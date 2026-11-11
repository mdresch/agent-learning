"""Tests for Active Evidence-Seeking via Information-Gain Prioritization (Methodology #12)."""

from __future__ import annotations

import json
from agent_learning.decision import (
    DecisionAuthority,
    DecisionCriterion,
    DecisionFrame,
    DecisionOption,
    DecisionResolver,
    DecisionStatus,
    EvidencePoint,
    TaskPolicy,
)
from agent_learning.types import Action, PolicySnapshot
from examples.active_evidence_seeking_demo import (
    AcquisitionStrategy,
    ActiveEvidenceSeeker,
    TelemetryOracle,
    build_initial_incomplete_frame,
    build_scenario_oracle,
    build_scenario_policy,
)


def test_initial_incomplete_frame_sorts_information_needs_by_gain():
    policy = build_scenario_policy()
    frame = build_initial_incomplete_frame()
    resolver = DecisionResolver()

    result = resolver.resolve(policy.snapshot(), frame)
    assert result.status is DecisionStatus.NEEDS_EVIDENCE
    assert len(result.information_needs) > 0

    # Ensure needs are sorted in descending order of information gain
    gains = [need.estimated_information_gain_bits for need in result.information_needs]
    assert gains == sorted(gains, reverse=True)

    # Constraints must have 1.0 bit
    constraint_needs = [n for n in result.information_needs if n.kind == "constraint"]
    assert all(n.estimated_information_gain_bits == 1.0 for n in constraint_needs)


def test_active_evidence_seeker_reaches_resolved_state():
    policy = build_scenario_policy()
    frame = build_initial_incomplete_frame()
    oracle = build_scenario_oracle()
    seeker = ActiveEvidenceSeeker(policy)

    final_result, final_frame, trace = seeker.run_loop(
        frame, oracle, strategy=AcquisitionStrategy.INFO_GAIN
    )

    assert final_result.status is DecisionStatus.RESOLVED
    assert final_result.selected_action is not None
    assert final_result.selected_action.id == "us_east_primary"
    assert trace.total_queries > 0
    assert trace.resolved_status is DecisionStatus.RESOLVED


def test_hard_constraint_failure_prunes_option_evaluations():
    policy = build_scenario_policy()
    frame = build_initial_incomplete_frame()
    oracle = build_scenario_oracle()
    seeker = ActiveEvidenceSeeker(policy)

    final_result, _, trace = seeker.run_loop(
        frame, oracle, strategy=AcquisitionStrategy.INFO_GAIN
    )

    # apac_singapore_edge fails data_sovereignty on step 1
    # Check that apac is ruled out in assessments
    apac_assessment = next(
        a for a in final_result.assessments if a.action.id == "apac_singapore_edge"
    )
    assert apac_assessment.feasible is False
    assert "constraint:data_sovereignty" in apac_assessment.ruled_out_by

    # Verify that NO criteria were ever probed for apac_singapore_edge
    apac_probes = [
        step
        for step in trace.steps
        if step.option_id == "apac_singapore_edge" and step.kind == "criterion"
    ]
    assert len(apac_probes) == 0


def test_episode_metadata_trace_is_json_serializable():
    policy = build_scenario_policy()
    frame = build_initial_incomplete_frame()
    oracle = build_scenario_oracle()
    seeker = ActiveEvidenceSeeker(policy)
    snap = policy.snapshot()

    final_result, _, trace = seeker.run_loop(
        frame, oracle, strategy=AcquisitionStrategy.INFO_GAIN
    )

    payload = {
        "task_id": snap.task_id,
        "policy_id": snap.id,
        "policy_version": snap.version,
        "methodology": "active_evidence_seeking",
        "methodology_id": 12,
        "acquisition_strategy": trace.strategy.value,
        "total_queries_executed": trace.total_queries,
        "final_decision_status": trace.resolved_status.value,
        "selected_action": trace.selected_action,
        "query_trace": [
            {
                "step": s.step_num,
                "option_id": s.option_id,
                "kind": s.kind,
                "field_id": s.field_id,
                "information_gain_bits": round(s.information_gain_bits, 3),
                "result": s.result_summary,
            }
            for s in trace.steps
        ],
        "final_assessments": trace.final_assessments,
    }

    serialized = json.dumps(payload)
    restored = json.loads(serialized)
    assert restored["methodology_id"] == 12
    assert restored["final_decision_status"] == "resolved"
    assert restored["selected_action"] == "us_east_primary"

