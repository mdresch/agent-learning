"""Decision-progress comparison and regression healing for reasoned TaskPolicy decisions.

Governed by ADR-005, BRD-005, FDD-005, and Epic 5 / Story 5.1.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence

from .decision import DecisionResult, OptionAssessment

DEFAULT_EPSILON: float = 0.01


class ClassificationType(str, Enum):
    """Exhaustive, mutually exclusive classification of a pairwise decision delta."""

    REGRESSION = "regression"
    PROGRESSION = "progression"
    FLAT = "flat"


@dataclass(frozen=True)
class ActionDelta:
    """Differences in utility metrics for a single action between two decisions."""

    robust_utility_delta: float
    expected_utility_delta: float
    uncertainty_delta: float
    criteria_deltas: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "robust_utility_delta": self.robust_utility_delta,
            "expected_utility_delta": self.expected_utility_delta,
            "uncertainty_delta": self.uncertainty_delta,
            "criteria_deltas": dict(self.criteria_deltas),
        }


@dataclass(frozen=True)
class PairwiseComparison:
    """Comparison of two consecutive DecisionResult instances."""

    before_policy_id: str
    after_policy_id: str
    before_version: int
    after_version: int
    leader_before: str
    leader_after: str
    leader_changed: bool
    leader_feasible: bool
    margin_before: float
    margin_after: float
    margin_delta: float
    leader_robust_utility_delta: float
    action_deltas: dict[str, ActionDelta]
    classification: ClassificationType
    classification_reason: str
    attribution: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "before_policy_id": self.before_policy_id,
            "after_policy_id": self.after_policy_id,
            "before_version": self.before_version,
            "after_version": self.after_version,
            "leader_before": self.leader_before,
            "leader_after": self.leader_after,
            "leader_changed": self.leader_changed,
            "leader_feasible": self.leader_feasible,
            "margin_before": self.margin_before,
            "margin_after": self.margin_after,
            "margin_delta": self.margin_delta,
            "leader_robust_utility_delta": self.leader_robust_utility_delta,
            "action_deltas": {k: v.to_dict() for k, v in self.action_deltas.items()},
            "classification": self.classification.value,
            "classification_reason": self.classification_reason,
            "attribution": list(self.attribution),
        }


@dataclass(frozen=True)
class SequenceComparisonResult:
    """Step-by-step pairwise comparison across an ordered sequence of DecisionResults."""

    comparisons: list[PairwiseComparison]
    consecutive_regression_count: int
    escalation_required: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "comparisons": [c.to_dict() for c in self.comparisons],
            "consecutive_regression_count": self.consecutive_regression_count,
            "escalation_required": self.escalation_required,
        }


def _validate_preconditions(before: DecisionResult, after: DecisionResult) -> None:
    """Ensure both results are from full authority and share taxonomy and task context.
    
    Raises:
        ValueError: Naming the exact field that mismatched.
    """
    if before.agent_id != after.agent_id:
        raise ValueError(f"agent_id mismatch: {before.agent_id!r} != {after.agent_id!r}")
    if before.task_id != after.task_id:
        raise ValueError(f"task_id mismatch: {before.task_id!r} != {after.task_id!r}")

    # Decision authority validation: must be full authority (OptionAssessments populated with robust_utility)
    if before.selection_basis != "bayesian_decision" or after.selection_basis != "bayesian_decision":
        raise ValueError("decision_authority must be 'full' to compare decision results")

    if not before.assessments or not after.assessments:
        raise ValueError("decision_authority must be 'full' (assessments required) to compare decision results")

    for assessment in (*before.assessments, *after.assessments):
        if assessment.robust_utility is None:
            raise ValueError("decision_authority must be 'full' (robust_utility required) to compare decision results")

    before_actions = {a.id for a in before.candidate_actions}
    after_actions = {a.id for a in after.candidate_actions}
    if before_actions != after_actions:
        raise ValueError(
            f"action taxonomy mismatch: {sorted(before_actions)} != {sorted(after_actions)}"
        )


def _classify(
    before: DecisionResult,
    after: DecisionResult,
    epsilon: float = DEFAULT_EPSILON,
) -> tuple[ClassificationType, str, dict[str, Any]]:
    """Classify the delta between two decision results using ADR-005 §4.4's proven-exhaustive taxonomy.
    
    Returns:
        tuple of (ClassificationType, reason_string, metrics_dict)
    """
    assessments_before = {a.action.id: a for a in before.assessments}
    assessments_after = {a.action.id: a for a in after.assessments}

    sorted_before = sorted(before.assessments, key=lambda a: (a.robust_utility or 0.0), reverse=True)
    sorted_after = sorted(after.assessments, key=lambda a: (a.robust_utility or 0.0), reverse=True)

    leader_before_id = sorted_before[0].action.id
    leader_after_id = sorted_after[0].action.id

    leader_before_ru = sorted_before[0].robust_utility or 0.0
    runner_up_before_ru = sorted_before[1].robust_utility or 0.0 if len(sorted_before) > 1 else 0.0
    margin_before = leader_before_ru - runner_up_before_ru

    leader_after_ru = sorted_after[0].robust_utility or 0.0
    runner_up_after_ru = sorted_after[1].robust_utility or 0.0 if len(sorted_after) > 1 else 0.0
    margin_after = leader_after_ru - runner_up_after_ru

    margin_delta = margin_after - margin_before

    # Metrics for the initial leader in the after decision
    after_lead_assessment = assessments_after[leader_before_id]
    leader_feasible = bool(after_lead_assessment.feasible)
    leader_ru_after = after_lead_assessment.robust_utility or 0.0
    leader_ru_delta = leader_ru_after - leader_before_ru
    leader_changed = (leader_before_id != leader_after_id)

    metrics = {
        "leader_before": leader_before_id,
        "leader_after": leader_after_id,
        "leader_changed": leader_changed,
        "leader_feasible": leader_feasible,
        "margin_before": margin_before,
        "margin_after": margin_after,
        "margin_delta": margin_delta,
        "leader_robust_utility_delta": leader_ru_delta,
    }

    # 1. Regression (four disjuncts per ADR-005 §4.4)
    if leader_changed:
        return ClassificationType.REGRESSION, f"Leader changed from {leader_before_id} to {leader_after_id}", metrics
    if not leader_feasible:
        return ClassificationType.REGRESSION, f"Leading action {leader_before_id} became infeasible", metrics
    if margin_delta < -epsilon:
        return ClassificationType.REGRESSION, f"Decision margin narrowed by {abs(margin_delta):.4f} (> epsilon {epsilon})", metrics
    if leader_ru_delta < -epsilon:
        return ClassificationType.REGRESSION, f"Leader robust utility fell by {abs(leader_ru_delta):.4f} (> epsilon {epsilon})", metrics

    # 2. Progression (two branches per ADR-005 §4.4)
    # Leading action unchanged and feasible (guaranteed by passing regression checks)
    margin_widened = margin_delta > epsilon
    ru_rose = leader_ru_delta > epsilon
    ru_not_fell = leader_ru_delta >= -epsilon
    margin_not_narrowed = margin_delta >= -epsilon

    if (margin_widened and ru_not_fell) or (ru_rose and margin_not_narrowed):
        reasons = []
        if margin_widened:
            reasons.append(f"margin widened by {margin_delta:+.4f}")
        if ru_rose:
            reasons.append(f"robust utility rose by {leader_ru_delta:+.4f}")
        return ClassificationType.PROGRESSION, "; ".join(reasons), metrics

    # 3. Flat (residual within tolerance [-epsilon, +epsilon])
    return ClassificationType.FLAT, f"Deltas within tolerance [-{epsilon}, +{epsilon}]", metrics


def compare_decision_results(
    before: DecisionResult,
    after: DecisionResult,
    epsilon: float = DEFAULT_EPSILON,
) -> PairwiseComparison:
    """Compare two full-authority DecisionResults and compute per-action and sequence deltas."""
    _validate_preconditions(before, after)

    assessments_before = {a.action.id: a for a in before.assessments}
    assessments_after = {a.action.id: a for a in after.assessments}

    action_deltas: dict[str, ActionDelta] = {}
    for action_id, a_before in assessments_before.items():
        a_after = assessments_after[action_id]
        
        # Criteria deltas
        cb = {c.criterion_id: c.support for c in a_before.criteria}
        ca = {c.criterion_id: c.support for c in a_after.criteria}
        crit_deltas = {cid: (ca[cid] - cb.get(cid, 0.0)) for cid in ca if cid in cb}

        action_deltas[action_id] = ActionDelta(
            robust_utility_delta=(a_after.robust_utility or 0.0) - (a_before.robust_utility or 0.0),
            expected_utility_delta=(a_after.expected_utility or 0.0) - (a_before.expected_utility or 0.0),
            uncertainty_delta=(a_after.uncertainty or 0.0) - (a_before.uncertainty or 0.0),
            criteria_deltas=crit_deltas,
        )

    classification, reason, metrics = _classify(before, after, epsilon=epsilon)

    # On regression, compute per-criterion attribution for the leader
    attribution: list[dict[str, Any]] = []
    if classification == ClassificationType.REGRESSION:
        lead_id = metrics["leader_before"]
        lead_before_criteria = {c.criterion_id: c.support for c in assessments_before[lead_id].criteria}
        lead_after_criteria = {c.criterion_id: c.support for c in assessments_after[lead_id].criteria}
        
        for cid, sup_before in lead_before_criteria.items():
            if cid in lead_after_criteria:
                sup_after = lead_after_criteria[cid]
                delta = sup_after - sup_before
                if delta < 0.0:
                    attribution.append({
                        "criterion_id": cid,
                        "before_support": sup_before,
                        "after_support": sup_after,
                        "support_delta": delta,
                    })
        attribution.sort(key=lambda x: x["support_delta"])

    return PairwiseComparison(
        before_policy_id=before.policy_id,
        after_policy_id=after.policy_id,
        before_version=before.policy_version,
        after_version=after.policy_version,
        leader_before=metrics["leader_before"],
        leader_after=metrics["leader_after"],
        leader_changed=metrics["leader_changed"],
        leader_feasible=metrics["leader_feasible"],
        margin_before=metrics["margin_before"],
        margin_after=metrics["margin_after"],
        margin_delta=metrics["margin_delta"],
        leader_robust_utility_delta=metrics["leader_robust_utility_delta"],
        action_deltas=action_deltas,
        classification=classification,
        classification_reason=reason,
        attribution=attribution,
    )


def compare_decision_sequence(
    results: Sequence[DecisionResult],
    epsilon: float = DEFAULT_EPSILON,
    retry_cap: int = 3,
) -> SequenceComparisonResult:
    """Compare an ordered sequence of 2 or more DecisionResults."""
    if len(results) < 2:
        raise ValueError("At least two DecisionResults are required for a sequence comparison")

    comparisons: list[PairwiseComparison] = []
    consecutive_regressions = 0

    for i in range(len(results) - 1):
        pair_comp = compare_decision_results(results[i], results[i + 1], epsilon=epsilon)
        comparisons.append(pair_comp)
        if pair_comp.classification == ClassificationType.REGRESSION:
            consecutive_regressions += 1
        else:
            consecutive_regressions = 0

    escalation_required = consecutive_regressions >= retry_cap

    return SequenceComparisonResult(
        comparisons=comparisons,
        consecutive_regression_count=consecutive_regressions,
        escalation_required=escalation_required,
    )

