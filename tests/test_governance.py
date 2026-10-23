"""Contract tests for Story 7.1 / ADR-007: Automated Governance Change — Paired Diff Classification and Escalation Pipeline.

Governing documents:
- ADR-007: docs/adr/ADR-007-governance-change-paired-diff-classification-and-escalation.md
- BRD-007: docs/project-docs/Business-Requirements/BRD-007-governance-change-paired-diff-classification-and-escalation.md
- FDD-007: docs/project-docs/Functional-Design/FDD-007-governance-change-paired-diff-classification-and-escalation.md
- Epic 7 / Story 7.1: docs/user-stories/epic-7-governance-change-paired-diff-classification-and-escalation.md
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from agent_learning import DecisionResult
from agent_learning.comparison import ClassificationType, PairwiseComparison
from agent_learning.decision import (
    Action,
    DecisionAuthority,
    DecisionFrame,
    DecisionStatus,
    PolicySnapshot,
    TaskPolicy,
)
from agent_learning.governance import (
    DIFF_ACTIONS,
    DIFF_TIERS,
    DiffActionTier,
    GOVERNANCE_CRITERIA_WEIGHTS,
    PERMANENTLY_FROZEN_DIFF_TYPES,
    ESCALATION_ACTIONS,
    ESCALATE_TO_HUMAN,
    APPLY_WITH_NOTIFICATION,
    APPLY_AUTOMATICALLY,
    GovernancePipelineResult,
    evaluate_governance_diff,
)
from agent_learning.storage import InMemoryStore


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "governance"

ERRATUM_FRAME_FILE = FIXTURES_DIR / "diff-frame-erratum.json"
PARAMETER_FRAME_FILE = FIXTURES_DIR / "diff-frame-parameter.json"
SUPERSEDING_FRAME_FILE = FIXTURES_DIR / "diff-frame-superseding.json"
PENDING_SUPER_FRAME_FILE = FIXTURES_DIR / "diff-frame-pending-supersession.json"
SUPER_UPDATE_FRAME_FILE = FIXTURES_DIR / "diff-frame-supersession-update.json"
TIEBREAK_FRAME_FILE = FIXTURES_DIR / "diff-frame-tiebreak.json"

ADV_DELETED_CONSTRAINT_FILE = FIXTURES_DIR / "adversarial-deleted-constraint.json"
ADV_INVERTED_LOGIC_FILE = FIXTURES_DIR / "adversarial-inverted-logic.json"
ADV_SOFTENED_MUST_FILE = FIXTURES_DIR / "adversarial-softened-must.json"


def _make_classify_policy(requires_human_approval: bool = False) -> TaskPolicy:
    """Create classify-diff-type task policy under FULL authority."""
    snapshot = PolicySnapshot(
        id="policy-classify-diff-type-v0",
        agent_id="socialengage-governance",
        task_id="classify-diff-type",
        version=0,
        actions=[Action(id=a, description=f"Action {a}", parameters={}) for a in DIFF_ACTIONS],
        logits={a: 0.0 for a in DIFF_ACTIONS},
        metadata={
            "decision_authority": DecisionAuthority.FULL.value,
            "requires_human_approval": requires_human_approval,
        },
    )
    return TaskPolicy(snapshot)


def _make_escalate_policy(logits: tuple[float, ...] | None = None) -> TaskPolicy:
    """Create escalate-diff-response task policy under LOW authority."""
    if logits is None:
        logits_dict = {a: 0.0 for a in ESCALATION_ACTIONS}
    else:
        logits_dict = {a: float(v) for a, v in zip(ESCALATION_ACTIONS, logits)}
    snapshot = PolicySnapshot(
        id="policy-escalate-diff-response-v0",
        agent_id="socialengage-governance",
        task_id="escalate-diff-response",
        version=0,
        actions=[Action(id=a, description=f"Action {a}", parameters={}) for a in ESCALATION_ACTIONS],
        logits=logits_dict,
        metadata={
            "decision_authority": DecisionAuthority.LOW.value,
            "capture_decision_evidence": True,
        },
    )
    return TaskPolicy(snapshot)


def _load_frame(path: Path) -> DecisionFrame:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    actions = tuple(Action(id=a, description=f"Action {a}", parameters={}) for a in DIFF_ACTIONS)
    return DecisionFrame.from_dict(data, actions)


def test_ac0_two_stage_decoupled_execution():
    """AC_0: The pipeline executes in two distinct stages: FULL classification then LOW escalation."""
    classify_policy = _make_classify_policy()
    escalate_policy = _make_escalate_policy()
    frame = _load_frame(ERRATUM_FRAME_FILE)

    result = evaluate_governance_diff(
        classify_policy=classify_policy,
        escalate_policy=escalate_policy,
        frame=frame,
        target_artifact="docs/adr/ADR-001.md",
    )

    assert isinstance(result, GovernancePipelineResult)
    assert result.classification_result is not None
    assert result.classification_result.selection_basis == "bayesian_decision"
    assert classify_policy.authority is DecisionAuthority.FULL

    assert result.escalation_result is not None
    assert result.escalation_result.selection_basis == "learned_policy"
    assert escalate_policy.authority is DecisionAuthority.LOW


def test_ac1_seven_action_grouped_taxonomy_and_criteria():
    """AC_1: 7-action taxonomy grouped into 3 tiers with 4 weighted criteria."""
    assert len(DIFF_ACTIONS) == 7
    assert set(DIFF_ACTIONS) == {
        "new_superseding_adr",
        "amendment_log_entry",
        "correction_note",
        "clarification_section",
        "provenance_note",
        "pending_supersession_note",
        "supersession_update",
    }

    # Verify 3 tiers
    assert DIFF_TIERS["new_superseding_adr"] == DiffActionTier.TIER_1_SUBSTANTIVE
    assert DIFF_TIERS["amendment_log_entry"] == DiffActionTier.TIER_1_SUBSTANTIVE
    assert DIFF_TIERS["correction_note"] == DiffActionTier.TIER_2_DOCUMENTATION
    assert DIFF_TIERS["clarification_section"] == DiffActionTier.TIER_2_DOCUMENTATION
    assert DIFF_TIERS["provenance_note"] == DiffActionTier.TIER_2_DOCUMENTATION
    assert DIFF_TIERS["pending_supersession_note"] == DiffActionTier.TIER_3_LIFECYCLE
    assert DIFF_TIERS["supersession_update"] == DiffActionTier.TIER_3_LIFECYCLE

    # Verify 4 criteria weights sum to 1.0
    assert GOVERNANCE_CRITERIA_WEIGHTS == {
        "semantic_scope_impact": 0.40,
        "architectural_intent_shift": 0.35,
        "downstream_contract_footprint": 0.15,
        "textual_cosmetic_ratio": 0.10,
    }
    assert sum(GOVERNANCE_CRITERIA_WEIGHTS.values()) == pytest.approx(1.0)


def test_ac2_native_margin_and_ambiguity_halting():
    """AC_2: When diff utility margin <= 0.05, immediately halts with NEEDS_USER_TIE_BREAK."""
    classify_policy = _make_classify_policy()
    escalate_policy = _make_escalate_policy()
    frame = _load_frame(TIEBREAK_FRAME_FILE)

    result = evaluate_governance_diff(
        classify_policy=classify_policy,
        escalate_policy=escalate_policy,
        frame=frame,
        target_artifact="docs/adr/ADR-0145.md",
    )

    assert result.halted_for_tie_break is True
    assert result.disposition == "needs_user_tie_break"
    assert result.classification_result.status is DecisionStatus.NEEDS_USER_TIE_BREAK
    # Escalation policy MUST NOT have been invoked
    assert result.escalation_result is None


def test_ac3_permanent_lineage_freeze_guard():
    """AC_3: Lifecycle status mutations hard-override to escalate_to_human without autonomy."""
    classify_policy = _make_classify_policy()
    # Configure escalate policy with high logits for apply_automatically to attempt autonomy
    escalate_policy = _make_escalate_policy(logits=(-10.0, -10.0, 10.0))

    # Test all 3 frozen lifecycle actions
    for path, expected_action in [
        (SUPERSEDING_FRAME_FILE, "new_superseding_adr"),
        (PENDING_SUPER_FRAME_FILE, "pending_supersession_note"),
        (SUPER_UPDATE_FRAME_FILE, "supersession_update"),
    ]:
        frame = _load_frame(path)
        result = evaluate_governance_diff(
            classify_policy=classify_policy,
            escalate_policy=escalate_policy,
            frame=frame,
            target_artifact="docs/adr/ADR-002.md",
        )

        assert result.classification_result.selected_action is not None
        assert result.classification_result.selected_action.id == expected_action
        assert expected_action in PERMANENTLY_FROZEN_DIFF_TYPES
        assert result.lineage_frozen is True
        # Must be hard-overridden to escalate_to_human regardless of bandit logits
        assert result.disposition == ESCALATE_TO_HUMAN


def test_ac4_lightweight_evidence_transport_via_adr006():
    """AC_4: Classification context transported to escalate policy via audit_evidence envelope."""
    classify_policy = _make_classify_policy()
    escalate_policy = _make_escalate_policy()
    frame = _load_frame(ERRATUM_FRAME_FILE)

    result = evaluate_governance_diff(
        classify_policy=classify_policy,
        escalate_policy=escalate_policy,
        frame=frame,
        target_artifact="docs/adr/ADR-001.md",
    )

    assert isinstance(result.audit_evidence, dict)
    assert result.audit_evidence["source_task_id"] == "classify-diff-type"
    assert result.audit_evidence["classified_diff_type"] == "correction_note"
    assert "robust_utility" in result.audit_evidence
    assert "runner_up_margin" in result.audit_evidence
    assert "criteria_supports" in result.audit_evidence
    assert result.audit_evidence["target_artifact"] == "docs/adr/ADR-001.md"


def test_ac5_mandatory_audit_emission_for_autonomous_updates():
    """AC_5: Autonomous updates emit an immutable audit Episode record into storage."""
    classify_policy = _make_classify_policy()
    # Force apply_automatically via logits
    escalate_policy = _make_escalate_policy(logits=(-10.0, -10.0, 10.0))
    frame = _load_frame(ERRATUM_FRAME_FILE)
    store = InMemoryStore()

    result = evaluate_governance_diff(
        classify_policy=classify_policy,
        escalate_policy=escalate_policy,
        frame=frame,
        target_artifact="docs/adr/ADR-001.md",
        store=store,
    )

    assert result.disposition == APPLY_AUTOMATICALLY
    assert result.audit_episode is not None
    assert result.audit_episode.task_id == "escalate-diff-response"
    assert result.audit_episode.action_id == APPLY_AUTOMATICALLY
    assert result.audit_episode.metadata.get("audit_evidence") is not None

    # Verify persisted in store
    episodes = store.query_episodes(agent_id="socialengage-governance", task_id="escalate-diff-response")
    assert len(episodes) == 1
    assert episodes[0].id == result.audit_episode.id


def test_ac6_progression_gating_via_adr005():
    """AC_6: ADR-005 compare_decision_results gates baseline update and shapes outcome reward."""
    classify_policy = _make_classify_policy()
    escalate_policy = _make_escalate_policy(logits=(-10.0, -10.0, 10.0))
    frame = _load_frame(PARAMETER_FRAME_FILE)

    # 1. Progression case
    from agent_learning.comparison import compare_decision_results
    fixtures_comp = Path(__file__).resolve().parent / "fixtures" / "comparison"
    before = DecisionResult.from_dict(json.loads((fixtures_comp / "adr-002-decision-result.json").read_text()))
    after_prog = DecisionResult.from_dict(json.loads((fixtures_comp / "adr-002-decision-result-v2.json").read_text()))

    result_prog = evaluate_governance_diff(
        classify_policy=classify_policy,
        escalate_policy=escalate_policy,
        frame=frame,
        target_artifact="docs/adr/ADR-002.md",
        verification_before_result=before,
        verification_after_result=after_prog,
    )
    assert result_prog.progression_comparison is not None
    assert result_prog.progression_comparison.classification == ClassificationType.PROGRESSION
    assert result_prog.reward == 1.0

    # 2. Regression case
    after_reg = DecisionResult.from_dict(json.loads((fixtures_comp / "adr-005-regressed-decision-result.json").read_text()))
    # Same task_id and policy_id for comparison precondition
    before_reg = DecisionResult.from_dict(json.loads((fixtures_comp / "adr-005-decision-result.json").read_text()))

    result_reg = evaluate_governance_diff(
        classify_policy=classify_policy,
        escalate_policy=escalate_policy,
        frame=frame,
        target_artifact="docs/adr/ADR-005.md",
        verification_before_result=before_reg,
        verification_after_result=after_reg,
    )
    assert result_reg.progression_comparison is not None
    assert result_reg.progression_comparison.classification == ClassificationType.REGRESSION
    assert result_reg.reward == -1.5
    # Detected regression must revert/escalate to human
    assert result_reg.disposition == ESCALATE_TO_HUMAN


def test_ac7_adversarial_diff_safety_harness():
    """AC_7: Adversarial test suite verifies classification across red-team diff archetypes."""
    classify_policy = _make_classify_policy()
    escalate_policy = _make_escalate_policy()

    # 1. Deleted constraint -> MUST classify as new_superseding_adr
    frame_del = _load_frame(ADV_DELETED_CONSTRAINT_FILE)
    res_del = evaluate_governance_diff(classify_policy, escalate_policy, frame_del, "docs/adr/ADR-002.md")
    assert res_del.classification_result.selected_action.id == "new_superseding_adr"
    assert res_del.disposition == ESCALATE_TO_HUMAN

    # 2. Inverted logic -> MUST classify as new_superseding_adr
    frame_inv = _load_frame(ADV_INVERTED_LOGIC_FILE)
    res_inv = evaluate_governance_diff(classify_policy, escalate_policy, frame_inv, "docs/adr/ADR-003.md")
    assert res_inv.classification_result.selected_action.id == "new_superseding_adr"
    assert res_inv.disposition == ESCALATE_TO_HUMAN

    # 3. Softened MUST -> MUST classify as new_superseding_adr or trigger tie-break
    frame_soft = _load_frame(ADV_SOFTENED_MUST_FILE)
    res_soft = evaluate_governance_diff(classify_policy, escalate_policy, frame_soft, "docs/adr/ADR-001.md")
    assert res_soft.classification_result.selected_action.id == "new_superseding_adr" or res_soft.halted_for_tie_break
    assert res_soft.disposition in {ESCALATE_TO_HUMAN, "needs_user_tie_break"}

    # 4. Legitimate erratum -> classifies as correction_note
    frame_err = _load_frame(ERRATUM_FRAME_FILE)
    res_err = evaluate_governance_diff(classify_policy, escalate_policy, frame_err, "docs/adr/ADR-001.md")
    assert res_err.classification_result.selected_action.id == "correction_note"

    # 5. Parameter shift -> classifies as amendment_log_entry
    frame_param = _load_frame(PARAMETER_FRAME_FILE)
    res_param = evaluate_governance_diff(classify_policy, escalate_policy, frame_param, "docs/adr/ADR-005.md")
    assert res_param.classification_result.selected_action.id == "amendment_log_entry"


def test_ac0_requires_human_approval_halts_for_user_feedback():
    """AC_0 (PR Review Finding): When classify_policy requires human approval, halt for feedback."""
    classify_policy = _make_classify_policy(requires_human_approval=True)
    escalate_policy = _make_escalate_policy()
    frame = _load_frame(ERRATUM_FRAME_FILE)

    result = evaluate_governance_diff(
        classify_policy=classify_policy,
        escalate_policy=escalate_policy,
        frame=frame,
        target_artifact="docs/adr/ADR-001.md",
    )

    assert result.disposition == "needs_user_feedback"
    assert result.classification_result.status is DecisionStatus.NEEDS_USER_FEEDBACK
    assert result.escalation_result is None


def test_ac5_regression_does_not_persist_autonomous_audit_episode():
    """AC_5 (PR Review Finding): Regression must NOT persist autonomous update episode to store."""
    classify_policy = _make_classify_policy()
    escalate_policy = _make_escalate_policy(logits=(-10.0, -10.0, 10.0))
    frame = _load_frame(PARAMETER_FRAME_FILE)
    store = InMemoryStore()

    fixtures_comp = Path(__file__).resolve().parent / "fixtures" / "comparison"
    before_reg = DecisionResult.from_dict(__import__("json").loads((fixtures_comp / "adr-005-decision-result.json").read_text()))
    after_reg = DecisionResult.from_dict(__import__("json").loads((fixtures_comp / "adr-005-regressed-decision-result.json").read_text()))

    result = evaluate_governance_diff(
        classify_policy=classify_policy,
        escalate_policy=escalate_policy,
        frame=frame,
        target_artifact="docs/adr/ADR-005.md",
        store=store,
        verification_before_result=before_reg,
        verification_after_result=after_reg,
    )

    assert result.disposition == ESCALATE_TO_HUMAN
    assert result.audit_episode is None
    # Storage MUST contain ZERO episodes
    episodes = store.query_episodes(agent_id="socialengage-governance", task_id="escalate-diff-response")
    assert len(episodes) == 0
