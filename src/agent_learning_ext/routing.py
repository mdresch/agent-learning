"""Contextual Authority Ensemble Routing signals and dispatch logic.

Source ADR: ADR-021 §4.1 (Contextual Authority Ensemble Routing)
Source BRD: BRD-021
Source FDD: FDD-021 §1, §2, §3
Stories: 21.1 to 21.7

This module provides the pure routing arithmetic, uncertainty signals (entropy and margin),
hysteresis routing logic, pinning tables, and dispatch helpers.

Purity invariant (Story 21.1 AC_2):
This module imports nothing from agent_learning.storage or agent_learning_ext.storage,
uses no random number generator (no random), and uses no numpy. All arithmetic is pure Python.
"""

from __future__ import annotations

import json
import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from agent_learning.autonomy import wilson_lower_bound
from agent_learning.config import AutonomyConfig
from agent_learning.decision import DecisionAuthority
from agent_learning.types import PolicySnapshot
from agent_learning_ext.decision import TaskPolicy

# Constants specified in FDD-021 §2.1
MIN_GAP_BITS: float = 0.15
EPS_MARGIN_DEFAULT: float = 0.20
SEED_DAMPING_DEFAULT: float = 0.70
VALID_TIERS: tuple[str, ...] = ("low", "standard", "high", "critical")
PINNED_FULL: tuple[str, ...] = (
    "approve-charter",
    "approve-adr",
    "approve-brd",
    "approve-fdd",
    "approve-user-stories",
    "approve-pmp",
    "approve-adaptation-plan",
    "approve-subsidiary-plan",
    "retrospective",
    "approve-routing-thresholds",
    "approve-routing-bucket",
    # IMP-046 (2026-11-10): gates found in the committed episodes that were not pinned by name
    "approve-audit-record",
    "approve-benefits",
    "approve-business-case",
    "approve-ideation",
    "approve-project-pillars",
    # IMP-046 follow-up (2026-11-10): the two gates that have a policy shape but no committed episode
    "approve-compiled-weights",
    "approve-intent-refinement",
)


@dataclass(frozen=True)
class RoutingConfig:
    """Threshold configuration for contextual authority ensemble routing."""

    tau_esc: float  # entropy at or above this routes full, in bits
    tau_deesc: float  # entropy at or below this may route low, in bits
    eps_margin: float = EPS_MARGIN_DEFAULT

    def __post_init__(self) -> None:
        """Validate threshold bounds, finite numbers, minimum gap, and margin range."""
        # Non-finite values check
        for name, val in [
            ("tau_esc", self.tau_esc),
            ("tau_deesc", self.tau_deesc),
            ("eps_margin", self.eps_margin),
        ]:
            if isinstance(val, bool) or not isinstance(val, (int, float)) or not math.isfinite(val):
                raise ValueError(f"{name} must be finite number (not bool): {val}")

        if self.tau_deesc < 0.0:
            raise ValueError(f"tau_deesc must be non-negative: {self.tau_deesc}")

        if self.tau_esc < self.tau_deesc:
            raise ValueError(
                f"inverted thresholds: tau_esc ({self.tau_esc}) < tau_deesc ({self.tau_deesc})"
            )

        gap = round(self.tau_esc - self.tau_deesc, 9)
        if gap < MIN_GAP_BITS:
            raise ValueError(
                f"gap under {MIN_GAP_BITS} bits: {self.tau_esc - self.tau_deesc}"
            )

        if not (0.0 < self.eps_margin <= 1.0):
            raise ValueError(f"eps_margin must be in (0, 1]: {self.eps_margin}")


@dataclass(frozen=True)
class RouteDecision:
    """Result of evaluating the ensemble router on an incoming decision request."""

    authority: DecisionAuthority
    entropy_bits: float | None  # None when the input was invalid
    margin: float | None
    reason: str  # pinned, critical, entropy, margin, low, not_approved, hysteresis, no_previous, anomaly
    anomaly: str | None = None


def entropy_bits(probabilities: Sequence[float]) -> float:
    """Compute Shannon entropy in bits (base-2 logarithm) over a discrete probability distribution.

    Formula:
        H(p) = - sum_{p_i > 0} p_i * log2(p_i)

    Boundary conditions:
        - 0.0 probability contributes 0.0 (limit p -> 0 of p * log2(p) = 0).
        - An empty sequence returns 0.0.
        - Single-action distribution [1.0] returns 0.0.
        - Input sequence is never mutated.

    Args:
        probabilities: Sequence of discrete action probabilities.

    Returns:
        Shannon entropy in bits (float >= 0.0).
    """
    total = 0.0
    for p in probabilities:
        if p > 0.0:
            total -= p * math.log2(p)
    return total


# Convenient alias matching standard terminology
entropy = entropy_bits


def margin(probabilities: Sequence[float]) -> float:
    """Compute decision margin: difference between highest and second-highest probabilities.

    Formula:
        Margin(p) = p_(1) - p_(2)

    Boundary conditions:
        - Single-action distribution [1.0] has p_(1) = 1.0 and p_(2) = 0.0, margin = 1.0.
        - Empty sequence returns 0.0.
        - Input sequence is never mutated (sorting is performed on a copy).

    Args:
        probabilities: Sequence of discrete action probabilities.

    Returns:
        Decision margin (float >= 0.0).
    """
    n = len(probabilities)
    if n == 0:
        return 0.0
    if n == 1:
        return float(probabilities[0])

    # Find two largest elements without mutating the input sequence
    first = float("-inf")
    second = float("-inf")
    for p in probabilities:
        p_val = float(p)
        if p_val > first:
            second = first
            first = p_val
        elif p_val > second:
            second = p_val

    return first - second


def route(
    probs: Sequence[float],
    tier: str,
    task_id: str = "classify-request",
    previous: DecisionAuthority | str | None = None,
    approved_for_low: bool = False,
    requires_human_approval: bool = False,
    cfg: RoutingConfig | None = None,
) -> RouteDecision:
    """Route a decision request by evaluating uncertainty signals, tier, and approval state.

    Evaluation precedence (FDD-021 §3 item 2):
        1. Pinned: PINNED_FULL tasks or requires_human_approval=True route FULL ('pinned').
        2. Invalid input: Empty, non-finite, negative, invalid sum, or unknown tier route FULL ('anomaly').
        3. Critical: Tier 'critical' routes FULL ('critical').
        4. Escalate: Margin below eps_margin routes FULL ('margin'); entropy >= tau_esc routes FULL ('entropy').
        5. De-escalate: Entropy <= tau_deesc (with margin >= eps_margin) routes LOW ('low') if approved,
           else FULL ('not_approved').
        6. Deadband: Inside deadband keeps previous route (LOW if approved, else FULL 'not_approved';
           None gives FULL 'no_previous'; FULL gives FULL 'hysteresis').

    Args:
        probs: Sequence of action probabilities.
        tier: Autonomy complexity tier ('low', 'standard', 'high', 'critical').
        task_id: Identifier of the task being routed.
        previous: Previous route authority (DecisionAuthority, str, or None).
        approved_for_low: True if the context bucket has an active human approval for fast-path routing.
        requires_human_approval: True if the task or complexity profile enforces human sign-off.
        cfg: RoutingConfig instance holding tau_esc, tau_deesc, and eps_margin.

    Returns:
        RouteDecision with target authority, entropy_bits, margin, reason, and optional anomaly.
    """
    # 1. Hard Pinned check (evaluated first, even before probability validation)
    if task_id in PINNED_FULL or requires_human_approval:
        ent_val = None
        margin_val = None
        if (
            probs
            and all(
                not isinstance(p, bool)
                and isinstance(p, (int, float))
                and math.isfinite(p)
                and p >= 0.0
                for p in probs
            )
            and abs(sum(probs) - 1.0) <= 1e-6
        ):
            ent_val = entropy_bits(probs)
            margin_val = margin(probs)
        return RouteDecision(
            authority=DecisionAuthority.FULL,
            entropy_bits=ent_val,
            margin=margin_val,
            reason="pinned",
            anomaly=None,
        )

    # 2. Input validation / Anomaly check (BRU-021-06)
    if len(probs) == 0:
        return RouteDecision(
            authority=DecisionAuthority.FULL,
            entropy_bits=None,
            margin=None,
            reason="anomaly",
            anomaly="empty probabilities",
        )

    for p in probs:
        if isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(p):
            return RouteDecision(
                authority=DecisionAuthority.FULL,
                entropy_bits=None,
                margin=None,
                reason="anomaly",
                anomaly=f"non-finite probability: {p}",
            )
        if p < 0.0:
            return RouteDecision(
                authority=DecisionAuthority.FULL,
                entropy_bits=None,
                margin=None,
                reason="anomaly",
                anomaly=f"negative probability: {p}",
            )

    sum_probs = sum(probs)
    if abs(sum_probs - 1.0) > 1e-6:
        return RouteDecision(
            authority=DecisionAuthority.FULL,
            entropy_bits=None,
            margin=None,
            reason="anomaly",
            anomaly=f"probabilities sum to {sum_probs}, expected 1.0",
        )

    if tier not in VALID_TIERS:
        return RouteDecision(
            authority=DecisionAuthority.FULL,
            entropy_bits=None,
            margin=None,
            reason="anomaly",
            anomaly=f"unknown tier: {tier}",
        )

    # Compute valid signals
    ent_val = entropy_bits(probs)
    margin_val = margin(probs)

    # 3. Critical tier check
    if tier == "critical":
        return RouteDecision(
            authority=DecisionAuthority.FULL,
            entropy_bits=ent_val,
            margin=margin_val,
            reason="critical",
            anomaly=None,
        )

    if cfg is None:
        return RouteDecision(
            authority=DecisionAuthority.FULL,
            entropy_bits=ent_val,
            margin=margin_val,
            reason="anomaly",
            anomaly="missing routing config",
        )

    # 4. Escalate check
    if margin_val < cfg.eps_margin:
        return RouteDecision(
            authority=DecisionAuthority.FULL,
            entropy_bits=ent_val,
            margin=margin_val,
            reason="margin",
            anomaly=None,
        )

    if ent_val >= cfg.tau_esc:
        return RouteDecision(
            authority=DecisionAuthority.FULL,
            entropy_bits=ent_val,
            margin=margin_val,
            reason="entropy",
            anomaly=None,
        )

    # 5. De-escalate check (Earn Low)
    if ent_val <= cfg.tau_deesc:
        if approved_for_low:
            return RouteDecision(
                authority=DecisionAuthority.LOW,
                entropy_bits=ent_val,
                margin=margin_val,
                reason="low",
                anomaly=None,
            )
        else:
            return RouteDecision(
                authority=DecisionAuthority.FULL,
                entropy_bits=ent_val,
                margin=margin_val,
                reason="not_approved",
                anomaly=None,
            )

    # 6. Hysteresis deadband (tau_deesc < ent_val < tau_esc and margin_val >= eps_margin)
    norm_prev: DecisionAuthority | None = None
    if isinstance(previous, DecisionAuthority):
        norm_prev = previous
    elif isinstance(previous, str):
        if previous.lower() == "low":
            norm_prev = DecisionAuthority.LOW
        elif previous.lower() == "full":
            norm_prev = DecisionAuthority.FULL
        else:
            return RouteDecision(
                authority=DecisionAuthority.FULL,
                entropy_bits=ent_val,
                margin=margin_val,
                reason="anomaly",
                anomaly=f"unknown previous route string: {previous}",
            )
    elif previous is not None:
        return RouteDecision(
            authority=DecisionAuthority.FULL,
            entropy_bits=ent_val,
            margin=margin_val,
            reason="anomaly",
            anomaly=f"unsupported previous route type: {type(previous)}",
        )

    if norm_prev is None:
        return RouteDecision(
            authority=DecisionAuthority.FULL,
            entropy_bits=ent_val,
            margin=margin_val,
            reason="no_previous",
            anomaly=None,
        )

    if norm_prev == DecisionAuthority.FULL:
        return RouteDecision(
            authority=DecisionAuthority.FULL,
            entropy_bits=ent_val,
            margin=margin_val,
            reason="hysteresis",
            anomaly=None,
        )

    if norm_prev == DecisionAuthority.LOW:
        if approved_for_low:
            return RouteDecision(
                authority=DecisionAuthority.LOW,
                entropy_bits=ent_val,
                margin=margin_val,
                reason="hysteresis",
                anomaly=None,
            )
        else:
            return RouteDecision(
                authority=DecisionAuthority.FULL,
                entropy_bits=ent_val,
                margin=margin_val,
                reason="not_approved",
                anomaly=None,
            )

    return RouteDecision(
        authority=DecisionAuthority.FULL,
        entropy_bits=ent_val,
        margin=margin_val,
        reason="anomaly",
        anomaly=f"unknown DecisionAuthority variant: {norm_prev}",
    )


def shadow_record(low_action_id: str, entropy_bits: float) -> dict[str, Any]:
    """Record shadow action and entropy for a full route (FDD-021 §1 item 4, §3.4).

    Returns a dict with 'shadow_low_action' and 'shadow_entropy_bits'.
    Raises ValueError for empty action id or non-finite entropy.
    Contains no reward key.
    """
    if not isinstance(low_action_id, str) or not low_action_id.strip():
        raise ValueError(f"action id must be a non-empty string: {low_action_id!r}")
    if isinstance(entropy_bits, bool) or not isinstance(entropy_bits, (int, float)) or not math.isfinite(entropy_bits):
        raise ValueError(f"entropy must be a finite number: {entropy_bits!r}")

    return {
        "shadow_low_action": low_action_id.strip(),
        "shadow_entropy_bits": float(entropy_bits),
    }


def previous_route(episodes: Sequence[Any], bucket: str) -> DecisionAuthority | None:
    """Return the route of the newest episode of the bucket by created_at (FDD-021 §3.5).

    Ignores other buckets and untagged episodes. Returns None if there is none.
    """
    if not episodes or not bucket:
        return None

    def _parse_created_at(ep: Any) -> datetime:
        raw = getattr(ep, "created_at", None)
        if raw is None and hasattr(ep, "metadata") and isinstance(ep.metadata, dict):
            raw = ep.metadata.get("created_at")
        if isinstance(raw, datetime):
            if raw.tzinfo is None:
                return raw.replace(tzinfo=timezone.utc)
            return raw
        if isinstance(raw, str):
            clean = raw.replace("Z", "+00:00")
            try:
                dt = datetime.fromisoformat(clean)
                if dt.tzinfo is None:
                    return dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                return datetime.min.replace(tzinfo=timezone.utc)
        return datetime.min.replace(tzinfo=timezone.utc)

    matching: list[tuple[datetime, Any]] = []
    for ep in episodes:
        meta = getattr(ep, "metadata", None)
        if not isinstance(meta, dict):
            continue
        ep_bucket = meta.get("routing_bucket")
        if not ep_bucket and isinstance(meta.get("routing"), dict):
            ep_bucket = meta["routing"].get("bucket")
        if ep_bucket != bucket:
            continue

        route_val = meta.get("routed_authority")
        if not route_val and isinstance(meta.get("routing"), dict):
            route_val = meta["routing"].get("route")
        if not route_val:
            continue

        dt = _parse_created_at(ep)
        matching.append((dt, route_val))

    if not matching:
        return None

    # Sort newest first by created_at
    matching.sort(key=lambda item: item[0], reverse=True)
    newest_route = matching[0][1]

    if isinstance(newest_route, DecisionAuthority):
        return newest_route
    if isinstance(newest_route, str):
        val = newest_route.strip().lower()
        if val == "low":
            return DecisionAuthority.LOW
        elif val == "full":
            return DecisionAuthority.FULL
    return None


def agreement(
    episodes: Sequence[Any],
    bucket: str,
    now: datetime | str,
    max_evidence_age_days: float | None,
) -> dict[str, Any]:
    """Count scored full-routed episodes of the bucket within the evidence window (FDD-021 §3.6).

    An episode counts when it has:
    1. bucket matching `bucket`
    2. full route (routed_authority == "full")
    3. shadow_low_action present
    4. feedback_status in ("accepted", "rejected")
    5. created_at inside [now - timedelta(days=max_evidence_age_days), now]

    The final action is correct_action_id when present, else action_id.
    Returns:
        n: total qualifying episodes
        k: count where shadow_low_action == final_action
        final_action_counts: mapping of action_id -> count of occurrences as final action
        modal_action: most frequent final action (None if n == 0)
        base_rate: share of the most frequent final action
        mean_shadow_entropy_bits: mean of shadow_entropy_bits across qualifying episodes
    """
    if max_evidence_age_days is None:
        raise ValueError("max_evidence_age_days must be set (fail closed)")
    if (
        isinstance(max_evidence_age_days, bool)
        or not isinstance(max_evidence_age_days, (int, float))
        or not math.isfinite(max_evidence_age_days)
        or max_evidence_age_days <= 0
    ):
        raise ValueError(f"max_evidence_age_days must be positive finite number: {max_evidence_age_days!r}")

    # Parse reference time `now`
    if isinstance(now, str):
        clean_now = now.replace("Z", "+00:00")
        ref_dt = datetime.fromisoformat(clean_now)
    elif isinstance(now, datetime):
        ref_dt = now
    else:
        raise TypeError(f"now must be datetime or ISO string: {now!r}")

    if ref_dt.tzinfo is None:
        ref_dt = ref_dt.replace(tzinfo=timezone.utc)

    window_start = ref_dt - timedelta(days=float(max_evidence_age_days))

    def _get_dt(ep: Any) -> datetime | None:
        raw = getattr(ep, "created_at", None)
        if raw is None and hasattr(ep, "metadata") and isinstance(ep.metadata, dict):
            raw = ep.metadata.get("created_at")
        if isinstance(raw, datetime):
            return raw if raw.tzinfo is not None else raw.replace(tzinfo=timezone.utc)
        if isinstance(raw, str):
            clean = raw.replace("Z", "+00:00")
            try:
                dt = datetime.fromisoformat(clean)
                return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)
            except ValueError:
                return None
        return None

    n = 0
    k = 0
    final_action_counts: dict[str, int] = {}
    entropy_sum = 0.0
    entropy_n = 0  # episodes carrying a finite shadow_entropy_bits (Q-146-1)

    for ep in episodes:
        meta = getattr(ep, "metadata", None)
        if not isinstance(meta, dict):
            continue

        # 1. Bucket check
        ep_bucket = meta.get("routing_bucket")
        if not ep_bucket and isinstance(meta.get("routing"), dict):
            ep_bucket = meta["routing"].get("bucket")
        if ep_bucket != bucket:
            continue

        # 2. Full route check
        route_val = meta.get("routed_authority")
        if not route_val and isinstance(meta.get("routing"), dict):
            route_val = meta["routing"].get("route")
        if isinstance(route_val, DecisionAuthority):
            is_full = route_val == DecisionAuthority.FULL
        elif isinstance(route_val, str):
            is_full = route_val.strip().lower() == "full"
        else:
            is_full = False
        if not is_full:
            continue

        # 3. Shadow action present
        shadow_action = meta.get("shadow_low_action")
        if not shadow_action or not isinstance(shadow_action, str):
            continue

        # 4. Scored feedback status in ("accepted", "rejected")
        feedback_status = getattr(ep, "feedback_status", None) or meta.get("feedback_status")
        if not feedback_status or str(feedback_status).strip().lower() not in ("accepted", "rejected"):
            continue

        # 5. Evidence window check
        ep_dt = _get_dt(ep)
        if ep_dt is None or ep_dt < window_start or ep_dt > ref_dt:
            continue

        # Determine final action
        correct_act = getattr(ep, "correct_action_id", None) or meta.get("correct_action_id")
        if correct_act and isinstance(correct_act, str) and correct_act.strip():
            final_act = correct_act.strip()
        else:
            final_act = getattr(ep, "action_id", None) or meta.get("action_id")
            if not isinstance(final_act, str) or not final_act.strip():
                # FDD-021 §3.6: an episode without a final action does not count.
                continue
            final_act = final_act.strip()

        n += 1
        if shadow_action == final_act:
            k += 1

        final_action_counts[final_act] = final_action_counts.get(final_act, 0) + 1

        ent = meta.get("shadow_entropy_bits")
        if isinstance(ent, (int, float)) and not isinstance(ent, bool) and math.isfinite(ent):
            entropy_sum += float(ent)
            entropy_n += 1

    if n > 0:
        # Determine modal action (sort ties deterministically)
        modal_action = max(sorted(final_action_counts.keys()), key=lambda a: final_action_counts[a])
        base_rate = round(final_action_counts[modal_action] / n, 9)
        mean_shadow_entropy_bits = round(entropy_sum / entropy_n, 9) if entropy_n > 0 else 0.0
    else:
        modal_action = None
        base_rate = 0.0
        mean_shadow_entropy_bits = 0.0

    return {
        "n": n,
        "k": k,
        "final_action_counts": final_action_counts,
        "modal_action": modal_action,
        "base_rate": base_rate,
        "mean_shadow_entropy_bits": mean_shadow_entropy_bits,
    }


def propose_bucket(
    agreement_result: dict[str, Any],
    cfg_gate: AutonomyConfig | Any = None,
) -> dict[str, Any]:
    """Propose bucket promotion based on agreement counts and standard tier autonomy gate (FDD-021 §3.7).

    Compares wilson_lower_bound(k, n) against the gate's lower bound (standard tier: 0.90)
    and n against the gate's minimum outcomes (standard tier: 20).
    Reports base_rate, modal_action, n, k, and mean_shadow_entropy_bits.
    """
    n = int(agreement_result.get("n", 0))
    k = int(agreement_result.get("k", 0))
    base_rate = float(agreement_result.get("base_rate", 0.0))
    modal_action = agreement_result.get("modal_action")
    mean_shadow_entropy_bits = float(agreement_result.get("mean_shadow_entropy_bits", 0.0))

    if cfg_gate is None:
        cfg_gate = AutonomyConfig()

    min_outcomes = getattr(cfg_gate, "min_outcomes", 20)
    lower_bound_req = getattr(cfg_gate, "min_correctness_lower_bound", 0.90)
    wilson_z = getattr(cfg_gate, "wilson_z", 1.96)

    # Unrounded: AC_4 "equals wilson_lower_bound(k, n)"; rounding first would admit a
    # bound just below the gate (e.g. 0.901096 rounded to 0.9011).
    w_lower = wilson_lower_bound(k, n, z=wilson_z)

    if n < min_outcomes:
        eligible = False
        reason = f"outcomes {n} below minimum required {min_outcomes}"
    elif w_lower < lower_bound_req:
        eligible = False
        reason = f"wilson lower bound {w_lower:.4f} below required {lower_bound_req:.4f}"
    else:
        eligible = True
        reason = "eligible: agreement meets standard tier autonomy gate"

    return {
        "eligible": eligible,
        "n": n,
        "k": k,
        "wilson_lower": w_lower,
        "base_rate": base_rate,
        "modal_action": modal_action,
        "mean_shadow_entropy_bits": mean_shadow_entropy_bits,
        "reason": reason,
    }


def seed_prior(
    counts: dict[str, int],
    action_ids: Sequence[str],
    *,
    damping: float = SEED_DAMPING_DEFAULT,
) -> dict[str, float]:
    """Seed a bucket's prior from its final action counts (FDD-021 §3 item 8, K5).

    With ``f_a = (n_a + 1) / (N + |A|)`` the logit is ``damping * (ln f_a - mean over b of ln f_b)``,
    so the logits sum to 0. The result follows the order of ``action_ids``. The Laplace smoothing
    gives an action never seen a finite logit. The seed is not scored outcomes (ADR-021 §4.4).

    Raises ValueError for damping outside (0, 1], a negative or non-integer count, a duplicate
    action id, or an action id missing from ``counts`` or from ``action_ids``. Empty input gives {}.
    """
    if (
        isinstance(damping, bool)
        or not isinstance(damping, (int, float))
        or not math.isfinite(damping)
        or not (0.0 < damping <= 1.0)
    ):
        raise ValueError(f"damping must be in (0, 1]: {damping!r}")

    ids = list(action_ids)
    if len(set(ids)) != len(ids):
        raise ValueError(f"duplicate action id in {ids!r}")
    missing_counts = [a for a in ids if a not in counts]
    if missing_counts:
        raise ValueError(f"action ids missing from counts: {missing_counts!r}")
    missing_ids = [a for a in counts if a not in ids]
    if missing_ids:
        raise ValueError(f"counts name actions missing from action_ids: {missing_ids!r}")
    for action, n_a in counts.items():
        if isinstance(n_a, bool) or not isinstance(n_a, int) or n_a < 0:
            raise ValueError(f"count for {action!r} must be a non-negative integer: {n_a!r}")

    if not ids:
        return {}

    total = sum(counts[a] for a in ids)
    size = len(ids)
    logs = [math.log((counts[a] + 1) / (total + size)) for a in ids]
    mean_log = sum(logs) / size
    return {a: damping * (lf - mean_log) for a, lf in zip(ids, logs)}


def is_routed(snapshot: Any) -> bool:
    """A task is routed only if its snapshot carries routing_state (FDD-021 §1 item 5)."""
    metadata = getattr(snapshot, "metadata", None)
    return isinstance(metadata, dict) and isinstance(metadata.get("routing_state"), dict)


def approved_for_low(snapshot: Any, bucket: str) -> bool:
    """The approved_for_low value the router receives for a bucket (FDD-021 §2.4, §3 item 10).

    True only when the snapshot is routed, the bucket is approved and it is not awaiting
    revalidation after a threshold change (BRU-021-13). Anything else is False (fail closed).
    """
    if not is_routed(snapshot):
        return False
    buckets = snapshot.metadata["routing_state"].get("buckets")
    if not isinstance(buckets, dict):
        return False
    entry = buckets.get(bucket)
    if not isinstance(entry, dict):
        return False
    return entry.get("approved") is True and entry.get("revalidate") is not True


def policy_for_route(
    snapshot: PolicySnapshot,
    authority: DecisionAuthority | str,
) -> TaskPolicy:
    """Return a TaskPolicy built from a copy of the snapshot with routed authority (FDD-021 §3.9).

    The stored snapshot is not changed (K2).
    For a pinned task (or requires_human_approval), raises ValueError if asked for LOW.
    """
    if isinstance(authority, DecisionAuthority):
        norm_auth = authority
    elif isinstance(authority, str):
        val = authority.strip().lower()
        if val == "low":
            norm_auth = DecisionAuthority.LOW
        elif val == "full":
            norm_auth = DecisionAuthority.FULL
        else:
            raise ValueError(f"Unknown authority string: {authority!r}")
    else:
        raise TypeError(f"authority must be DecisionAuthority or str, got {type(authority)}")

    # Check pinned tasks and human approval requirements
    task_id = getattr(snapshot, "task_id", "")
    metadata = getattr(snapshot, "metadata", None) or {}
    requires_human_approval = False
    if isinstance(metadata, dict):
        requires_human_approval = bool(metadata.get("requires_human_approval", False))

    if (task_id in PINNED_FULL or requires_human_approval) and norm_auth == DecisionAuthority.LOW:
        raise ValueError(f"task '{task_id}' is pinned to FULL and cannot be routed to LOW")

    # Deep copy the snapshot via json serialization to guarantee complete data isolation
    try:
        snap_dict = json.loads(json.dumps(snapshot.to_dict()))
    except (TypeError, ValueError) as exc:
        raise TypeError(f"snapshot contains non-serializable data: {exc}") from exc
    meta = snap_dict.get("metadata") or {}
    meta["decision_authority"] = norm_auth.value
    snap_dict["metadata"] = meta

    try:
        routed_snapshot = PolicySnapshot.from_dict(snap_dict)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"snapshot cannot be rebuilt for routing: {exc}") from exc
    return TaskPolicy(routed_snapshot)


def routed_episode_metadata(
    decision: RouteDecision,
    bucket: str,
    config: RoutingConfig | None = None,
    shadow: dict[str, Any] | None = None,
    tier: str | None = None,
) -> dict[str, Any]:
    """Format episode metadata for a routed decision per FDD-021 §2.3.

    Round-trips cleanly through json.dumps and json.loads.
    Holds route, entropy, margin, reason, thresholds, bucket, anomaly, and shadow info.

    The shadow record is a closed set (FDD-021 section 2.3): only ``shadow_low_action`` and
    ``shadow_entropy_bits`` are copied, and any other key in ``shadow`` is ignored.
    """
    thresholds_dict: dict[str, Any] | None = None
    if config is not None:
        thresholds_dict = {
            "tau_esc": config.tau_esc,
            "tau_deesc": config.tau_deesc,
            "eps_margin": config.eps_margin,
        }

    routing_dict: dict[str, Any] = {
        "bucket": bucket,
        "route": decision.authority.value,
        "entropy_bits": decision.entropy_bits,
        "margin": decision.margin,
        "reason": decision.reason,
        "thresholds": thresholds_dict,
    }
    if tier is not None:
        routing_dict["tier"] = tier

    meta: dict[str, Any] = {
        "routed_authority": decision.authority.value,
        "routing": routing_dict,
    }
    if decision.anomaly is not None:
        meta["routing_anomaly"] = decision.anomaly
    if shadow is not None:
        if "shadow_low_action" in shadow:
            meta["shadow_low_action"] = shadow["shadow_low_action"]
        if "shadow_entropy_bits" in shadow:
            meta["shadow_entropy_bits"] = shadow["shadow_entropy_bits"]
    return meta

