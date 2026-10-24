"""Automated Governance Change — Paired Diff Classification and Escalation Pipeline.

Governed by ADR-007, BRD-007, FDD-007, and Epic 7 / Story 7.1.
Implements Stage 16 of the 18-stage Intent-to-Outcome chain.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence

from .comparison import ClassificationType, PairwiseComparison, compare_decision_results
from .decision import (
    Action,
    DecisionAuthority,
    DecisionFrame,
    DecisionResult,
    DecisionStatus,
    TaskPolicy,
)
from .storage import LearningStore
from .types import Episode


class DiffActionTier(str, Enum):
    """Operational tier categorizing governance change diff types."""

    TIER_1_SUBSTANTIVE = "substantive"
    TIER_2_DOCUMENTATION = "documentation"
    TIER_3_LIFECYCLE = "lifecycle"


# 7-Action Taxonomy for classify-diff-type
DIFF_ACTIONS: tuple[str, ...] = (
    "new_superseding_adr",
    "amendment_log_entry",
    "correction_note",
    "clarification_section",
    "provenance_note",
    "pending_supersession_note",
    "supersession_update",
)

DIFF_TIERS: dict[str, DiffActionTier] = {
    "new_superseding_adr": DiffActionTier.TIER_1_SUBSTANTIVE,
    "amendment_log_entry": DiffActionTier.TIER_1_SUBSTANTIVE,
    "correction_note": DiffActionTier.TIER_2_DOCUMENTATION,
    "clarification_section": DiffActionTier.TIER_2_DOCUMENTATION,
    "provenance_note": DiffActionTier.TIER_2_DOCUMENTATION,
    "pending_supersession_note": DiffActionTier.TIER_3_LIFECYCLE,
    "supersession_update": DiffActionTier.TIER_3_LIFECYCLE,
}

# Invariant #4: Artifact lifecycle status mutations permanently frozen from autonomy
PERMANENTLY_FROZEN_DIFF_TYPES: frozenset[str] = frozenset(
    {
        "new_superseding_adr",
        "pending_supersession_note",
        "supersession_update",
    }
)

# 3-Action Escalation Taxonomy for escalate-diff-response
ESCALATE_TO_HUMAN: str = "escalate_to_human"
APPLY_WITH_NOTIFICATION: str = "apply_with_notification"
APPLY_AUTOMATICALLY: str = "apply_automatically"

ESCALATION_ACTIONS: tuple[str, ...] = (
    ESCALATE_TO_HUMAN,
    APPLY_WITH_NOTIFICATION,
    APPLY_AUTOMATICALLY,
)

# 4 Standard Weighted Criteria for classify-diff-type
GOVERNANCE_CRITERIA_WEIGHTS: dict[str, float] = {
    "semantic_scope_impact": 0.40,
    "architectural_intent_shift": 0.35,
    "downstream_contract_footprint": 0.15,
    "textual_cosmetic_ratio": 0.10,
}


@dataclass(frozen=True)
class GovernancePipelineResult:
    """End-to-end outcome of evaluating a candidate governance diff."""

    classification_result: DecisionResult
    escalation_result: DecisionResult | None
    disposition: str
    halted_for_tie_break: bool
    lineage_frozen: bool
    audit_evidence: dict[str, Any]
    audit_episode: Episode | None = None
    progression_comparison: PairwiseComparison | None = None
    reward: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "classification_result": self.classification_result.to_dict(),
            "escalation_result": (
                self.escalation_result.to_dict() if self.escalation_result else None
            ),
            "disposition": self.disposition,
            "halted_for_tie_break": self.halted_for_tie_break,
            "lineage_frozen": self.lineage_frozen,
            "audit_evidence": dict(self.audit_evidence),
            "audit_episode": self.audit_episode.to_dict() if self.audit_episode else None,
            "progression_comparison": (
                self.progression_comparison.to_dict()
                if self.progression_comparison
                else None
            ),
            "reward": self.reward,
        }


def evaluate_governance_diff(
    classify_policy: TaskPolicy,
    escalate_policy: TaskPolicy,
    frame: DecisionFrame,
    target_artifact: str,
    *,
    store: LearningStore | None = None,
    verification_before_result: DecisionResult | None = None,
    verification_after_result: DecisionResult | None = None,
) -> GovernancePipelineResult:
    """Execute the Stage 16 Governance Change paired classification & escalation pipeline.

    1. Classifies the semantic form of diff under FULL authority (Bayesian).
    2. Enforces native margin check; halts immediately on NEEDS_USER_TIE_BREAK or NEEDS_USER_FEEDBACK.
    3. Enforces permanent lineage freeze on lifecycle status mutations.
    4. Transports classification context as ADR-006 audit_evidence envelope to LOW authority.
    5. Verifies downstream progression via ADR-005 compare_decision_results().
    6. Mandates immutable Episode audit emission for autonomous updates (post-verification).
    """
    if classify_policy.authority is not DecisionAuthority.FULL:
        raise ValueError("classify_policy must operate under DecisionAuthority.FULL")
    if escalate_policy.authority is not DecisionAuthority.LOW:
        raise ValueError("escalate_policy must operate under DecisionAuthority.LOW")

    # Step 1: Execute semantic classification under FULL authority
    classification_result = classify_policy.decide(frame)

    # Step 2: Native margin & human approval gates (BRU-007-03, Invariant #3)
    if classification_result.status in {
        DecisionStatus.NEEDS_USER_TIE_BREAK,
        DecisionStatus.NEEDS_USER_FEEDBACK,
    }:
        disposition = (
            "needs_user_tie_break"
            if classification_result.status is DecisionStatus.NEEDS_USER_TIE_BREAK
            else "needs_user_feedback"
        )
        return GovernancePipelineResult(
            classification_result=classification_result,
            escalation_result=None,
            disposition=disposition,
            halted_for_tie_break=(
                classification_result.status is DecisionStatus.NEEDS_USER_TIE_BREAK
            ),
            lineage_frozen=False,
            audit_evidence={},
            audit_episode=None,
            progression_comparison=None,
            reward=None,
        )

    # Extract classified action
    selected_action = (
        classification_result.selected_action or classification_result.proposed_action
    )
    if selected_action is None:
        raise ValueError(
            f"classify-diff-type did not produce a selected or proposed action: {classification_result.status}"
        )
    action_id = selected_action.id

    # Step 3: Construct ADR-006 lightweight evidence transport envelope
    assessments = classification_result.assessments
    best_assessment = next((a for a in assessments if a.action.id == action_id), None)
    other_assessments = [
        a for a in assessments if a.action.id != action_id and a.robust_utility is not None
    ]
    runner_up_util = (
        max((a.robust_utility for a in other_assessments), default=0.0)
        if other_assessments
        else 0.0
    )
    robust_util = (
        best_assessment.robust_utility
        if best_assessment and best_assessment.robust_utility is not None
        else 0.0
    )
    runner_up_margin = float(robust_util) - float(runner_up_util)
    criteria_supports = {
        c.criterion_id: c.support
        for c in (best_assessment.criteria if best_assessment else ())
    }

    audit_evidence = {
        "source_task_id": "classify-diff-type",
        "classified_diff_type": action_id,
        "robust_utility": robust_util,
        "runner_up_margin": runner_up_margin,
        "criteria_supports": criteria_supports,
        "target_artifact": target_artifact,
    }

    # Step 4: Permanent Lineage Freeze check (BRU-007-04, Invariant #4)
    lineage_frozen = action_id in PERMANENTLY_FROZEN_DIFF_TYPES
    escalate_snapshot = escalate_policy.snapshot()

    if lineage_frozen:
        disposition = ESCALATE_TO_HUMAN
        # Bypass bandit exploration; hard-override escalation result
        escalation_result = DecisionResult(
            agent_id=escalate_snapshot.agent_id,
            task_id=escalate_snapshot.task_id,
            policy_id=escalate_snapshot.id,
            policy_version=escalate_snapshot.version,
            status=DecisionStatus.RESOLVED,
            reason=(
                f"Action '{action_id}' alters governance lineage and is permanently frozen "
                "from autonomous application (ADR-007 Invariant #4)."
            ),
            selection_basis="governance_invariants",
            selected_action=Action(
                id=ESCALATE_TO_HUMAN,
                description="Mandatory human escalation for lifecycle mutations",
                parameters={},
            ),
            candidate_actions=tuple(
                Action(id=a, description=f"Action {a}", parameters={})
                for a in ESCALATION_ACTIONS
            ),
            audit_evidence=audit_evidence,
        )
    else:
        # Step 5: Execute escalation decision under LOW authority
        escalation_result = escalate_policy.decide(audit_evidence=audit_evidence)
        chosen = escalation_result.selected_action or escalation_result.proposed_action
        disposition = chosen.id if chosen else ESCALATE_TO_HUMAN

    # Step 6: ADR-005 Progression Verification (BRU-007-07, Invariant #6)
    progression_comparison: PairwiseComparison | None = None
    reward: float | None = None
    if (
        verification_before_result is not None
        and verification_after_result is not None
    ):
        progression_comparison = compare_decision_results(
            verification_before_result, verification_after_result
        )
        if progression_comparison.classification is ClassificationType.PROGRESSION:
            reward = 1.0
        elif progression_comparison.classification is ClassificationType.FLAT:
            reward = 0.0
        else:  # REGRESSION
            reward = -1.5
            # Invariant: detected regression immediately halts & reverts to human escalation
            disposition = ESCALATE_TO_HUMAN

    # Step 7: Mandatory Episode Audit Emission (BRU-007-05, Invariant #5)
    # Strictly emitted if final disposition remains autonomous after progression verification
    audit_episode: Episode | None = None
    if disposition in {APPLY_AUTOMATICALLY, APPLY_WITH_NOTIFICATION}:
        audit_episode = Episode(
            agent_id=escalate_snapshot.agent_id,
            task_id=escalate_snapshot.task_id,
            policy_id=escalate_snapshot.id,
            policy_version=escalate_snapshot.version,
            action_id=disposition,
            metadata={"audit_evidence": audit_evidence},
            user_input=f"Governance change diff evaluation for {target_artifact}",
            assistant_output=f"Disposition: {disposition} for {action_id}",
        )
        if store is not None:
            store.store_episode(audit_episode)

    return GovernancePipelineResult(
        classification_result=classification_result,
        escalation_result=escalation_result,
        disposition=disposition,
        halted_for_tie_break=False,
        lineage_frozen=lineage_frozen,
        audit_evidence=audit_evidence,
        audit_episode=audit_episode,
        progression_comparison=progression_comparison,
        reward=reward,
    )
