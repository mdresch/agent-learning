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

import math
from collections.abc import Sequence
from dataclasses import dataclass

from agent_learning.decision import DecisionAuthority

# Constants specified in FDD-021 §2.1
MIN_GAP_BITS: float = 0.15
EPS_MARGIN_DEFAULT: float = 0.20
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
)
SEED_DAMPING_DEFAULT: float = 0.70


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

    # Normalize previous authority
    norm_prev: DecisionAuthority | None = None
    if isinstance(previous, DecisionAuthority):
        norm_prev = previous
    elif isinstance(previous, str):
        if previous.lower() == "low":
            norm_prev = DecisionAuthority.LOW
        elif previous.lower() == "full":
            norm_prev = DecisionAuthority.FULL
        else:
            raise ValueError(f"unknown previous route string: {previous}")
    elif previous is not None:
        raise ValueError(f"unsupported previous route type: {type(previous)}")

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

    raise ValueError(f"unknown DecisionAuthority variant: {norm_prev}")
