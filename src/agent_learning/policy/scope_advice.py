"""Idle Scope plan advisory policy (ADR-025, FDD-025). No storage I/O."""

from __future__ import annotations

import hashlib
import random
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from ..types import Action, PolicySnapshot
from .softmax_bandit import SoftmaxPolicy

ADVICE_TASK_ID = "advise-scope-plan-decision"
GATE_TASK_ID = "approve-subsidiary-plan"

DECISION_KINDS: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "route": ("recommend_full_plan", "recommend_pmp_section", "recommend_not_applicable"),
        "paragraph_sufficiency": ("recommend_sufficient", "recommend_insufficient"),
        "graduation": ("recommend_keep_section", "recommend_graduate"),
        "flagged_deviation": ("recommend_accept_deviation", "recommend_refuse_deviation"),
    }
)

_ACTION_DESCRIPTIONS: Mapping[str, str] = MappingProxyType(
    {
        "recommend_full_plan": "Advisory (kind: route): full_plan subsidiary baseline",
        "recommend_pmp_section": "Advisory (kind: route): PMP section only",
        "recommend_not_applicable": "Advisory (kind: route): not_applicable with rationale",
        "recommend_sufficient": "Advisory (kind: paragraph_sufficiency): profile met",
        "recommend_insufficient": "Advisory (kind: paragraph_sufficiency): profile not met",
        "recommend_keep_section": "Advisory (kind: graduation): keep in PMP section",
        "recommend_graduate": "Advisory (kind: graduation): graduate to full_plan",
        "recommend_accept_deviation": "Advisory (kind: flagged_deviation): accept Tier C carry",
        "recommend_refuse_deviation": "Advisory (kind: flagged_deviation): refuse until remediated",
    }
)


@dataclass(frozen=True)
class ScopeRecommendation:
    recommendation_id: str
    task_id: str
    decision_kind: str
    action_id: str
    recommended_at: str
    visible: bool
    logits: Mapping[str, float]


_RECOMMENDATIONS: dict[str, ScopeRecommendation] = {}


def _all_action_ids() -> tuple[str, ...]:
    seen: list[str] = []
    for ids in DECISION_KINDS.values():
        for action_id in ids:
            if action_id not in seen:
                seen.append(action_id)
    return tuple(seen)


def baseline_snapshot(*, agent_id: str = "scope-advisory") -> PolicySnapshot:
    """Idle advisory snapshot (FDD-025 §3.5). Does not touch storage or create episodes."""
    action_ids = _all_action_ids()
    actions = [Action(id=aid, description=_ACTION_DESCRIPTIONS[aid]) for aid in action_ids]
    logits = {aid: 0.0 for aid in action_ids}
    return PolicySnapshot(
        agent_id=agent_id,
        task_id=ADVICE_TASK_ID,
        version=0,
        actions=actions,
        logits=logits,
        metadata={
            "decision_authority": "low",
            "requires_human_approval": False,
        },
    )


def _kind_actions(snapshot: PolicySnapshot, decision_kind: str) -> tuple[Action, ...]:
    if decision_kind not in DECISION_KINDS:
        raise ValueError(f"unknown decision_kind: {decision_kind!r}")
    allowed = DECISION_KINDS[decision_kind]
    by_id = {a.id: a for a in snapshot.actions}
    missing = [aid for aid in allowed if aid not in by_id]
    if missing:
        raise ValueError(f"snapshot missing actions for kind {decision_kind!r}: {missing}")
    return tuple(by_id[aid] for aid in allowed)


def _kind_snapshot(snapshot: PolicySnapshot, decision_kind: str) -> PolicySnapshot:
    actions = _kind_actions(snapshot, decision_kind)
    logits = {a.id: float(snapshot.logits.get(a.id, 0.0)) for a in actions}
    data = snapshot.to_dict()
    data["actions"] = [a.to_dict() for a in actions]
    data["logits"] = logits
    return PolicySnapshot.from_dict(data)


def _rng_for(recommendation_id: str) -> random.Random:
    digest = hashlib.sha256(recommendation_id.encode("utf-8")).hexdigest()
    seed = int(digest[:16], 16)
    return random.Random(seed)


def recommend(
    snapshot: PolicySnapshot,
    decision_kind: str,
    *,
    recommendation_id: str,
    recommended_at: str,
    recorded_decisions: int,
    min_shown_decisions: int | None,
) -> ScopeRecommendation:
    """Draw or return a cached Scope recommendation (FDD-025 §3.6)."""
    if recommendation_id in _RECOMMENDATIONS:
        return _RECOMMENDATIONS[recommendation_id]

    if min_shown_decisions is not None and min_shown_decisions <= 0:
        raise ValueError("min_shown_decisions must be a positive integer or None")

    kind_snap = _kind_snapshot(snapshot, decision_kind)
    policy = SoftmaxPolicy.from_snapshot(kind_snap, rng=_rng_for(recommendation_id))
    decision = policy.choose()
    action_id = decision.action.id
    allowed = DECISION_KINDS[decision_kind]
    if action_id not in allowed:
        raise ValueError(f"action {action_id!r} is outside kind {decision_kind!r}")

    if min_shown_decisions is None:
        visible = False
    else:
        visible = recorded_decisions >= min_shown_decisions

    record = ScopeRecommendation(
        recommendation_id=recommendation_id,
        task_id=ADVICE_TASK_ID,
        decision_kind=decision_kind,
        action_id=action_id,
        recommended_at=recommended_at,
        visible=visible,
        logits=dict(kind_snap.logits),
    )
    _RECOMMENDATIONS[recommendation_id] = record
    return record


def advice_reward(followed: bool) -> float:
    """Reward for following (+1) or overriding (−1) the stored recommendation (FDD-025 §3.7)."""
    return 1.0 if followed else -1.0


def reset_recommendation_cache() -> None:
    """Test helper: clear in-process recommendation memo (not part of the public contract)."""
    _RECOMMENDATIONS.clear()


__all__ = [
    "ADVICE_TASK_ID",
    "DECISION_KINDS",
    "GATE_TASK_ID",
    "ScopeRecommendation",
    "advice_reward",
    "baseline_snapshot",
    "recommend",
    "reset_recommendation_cache",
]
