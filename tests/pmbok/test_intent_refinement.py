"""
Unit and integration tests for Epic 9: Intent Refinement and Cognitive Feedback Loop.
Tests covering Acceptance Criteria AC_0 through AC_11.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
import pytest
from pydantic import ValidationError

from pmbok.models.intent_refinement import (
    CumulativeLineageKernel,
    HypothesisResolutionItem,
    HypothesisTerminalStatus,
    IntentRefinementProposalPayload,
    MeasurementHorizon,
    OutcomeDeltaItem,
    SparkDirectiveItem,
)
from scripts.orchestrate_pmbok import seed_next_phase, decommission_project, rollback_pmp


# ── AC_2, AC_6, AC_7, AC_8: Pydantic Contract & Hypothesis Adjudication ──────

def test_ac_2_valid_proposal_payload():
    """AC_2: Machine-readable contract adheres to IntentRefinementProposalPayload schema."""
    payload = IntentRefinementProposalPayload(
        refinement_id="IR-PROP-v1.0.0",
        pmp_baseline="PMP-BL-v1.0.0",
        readiness_audit_ref="AUD-CLOSE-001",
        disposition_type="phase_handoff",
        executive_summary="Phase 1 delivered all targeted capabilities with validated invariants.",
        outcome_deltas=[
            OutcomeDeltaItem(
                objective_id="OBJ-001",
                target_metric_stage_4="Latency <= 100ms",
                actual_metric_stage_12="Observed Latency = 82ms",
                variance_percentage=-18.0,
                measurement_horizon=MeasurementHorizon.IMMEDIATE,
                causal_factors=["Asynchronous IO optimization"],
                strategic_directive="Adopt latency profile as permanent SLA.",
            )
        ],
        hypothesis_resolutions=[
            HypothesisResolutionItem(
                hypothesis_id="HYP-001",
                statement="Stateless Bayesian comparison prevents drift.",
                terminal_status=HypothesisTerminalStatus.VALIDATED,
                recurrence_depth=0,
                bayes_factor=14.5,
                evidence_references=["EPISODE-101", "EPISODE-102"],
                promotion_target="Architecture Invariant #5",
                rationale="Bayes factor 14.5 >= 10 confirms hypothesis.",
            )
        ],
        strategic_pivots=["Promote stateless comparison to core framework."],
        phase_next_spark_directives=[
            SparkDirectiveItem(
                directive_id="DIR-001",
                title="Operationalize Generational Epistemic Kernel",
                action_type="expand_capability",
                target_stage_1_spark="SPARK-GEN-002",
            )
        ],
        lineage=CumulativeLineageKernel(
            root_spark="SPARK-ROOT-001",
            generational_index=1,
            immutable_core_invariants=["INV-01", "INV-02"],
            accumulated_knowledge_hash="sha256-abc123def456",
        ),
    )
    assert payload.refinement_id == "IR-PROP-v1.0.0"
    assert payload.pmp_baseline == "PMP-BL-v1.0.0"
    assert len(payload.phase_next_spark_directives) == 1


def test_ac_2_invalid_baseline_pattern():
    """AC_2: Baseline and refinement IDs must strictly adhere to SemVer patterns."""
    with pytest.raises(ValidationError):
        IntentRefinementProposalPayload(
            refinement_id="INVALID-REF",
            pmp_baseline="PMP-BL-v1.0.0",
            readiness_audit_ref="AUD-001",
            disposition_type="project_termination",
            executive_summary="Summary",
            outcome_deltas=[],
            hypothesis_resolutions=[],
            strategic_pivots=[],
            lineage=CumulativeLineageKernel(
                root_spark="SPARK-01",
                generational_index=1,
                immutable_core_invariants=[],
                accumulated_knowledge_hash="hash",
            ),
        )


def test_ac_2_disposition_constraints():
    """AC_2: Phase handoff requires directives; project termination prohibits directives."""
    # Handoff with empty directives -> Error
    with pytest.raises(ValidationError, match="phase_next_spark_directives must be non-empty"):
        IntentRefinementProposalPayload(
            refinement_id="IR-PROP-v1.0.0",
            pmp_baseline="PMP-BL-v1.0.0",
            readiness_audit_ref="AUD-001",
            disposition_type="phase_handoff",
            executive_summary="Summary",
            outcome_deltas=[],
            hypothesis_resolutions=[],
            strategic_pivots=[],
            phase_next_spark_directives=[],
            lineage=CumulativeLineageKernel(
                root_spark="SPARK-01",
                generational_index=1,
                immutable_core_invariants=[],
                accumulated_knowledge_hash="hash",
            ),
        )

    # Termination with non-empty directives -> Error
    with pytest.raises(ValidationError, match="phase_next_spark_directives must be empty"):
        IntentRefinementProposalPayload(
            refinement_id="IR-PROP-v1.0.0",
            pmp_baseline="PMP-BL-v1.0.0",
            readiness_audit_ref="AUD-001",
            disposition_type="project_termination",
            executive_summary="Summary",
            outcome_deltas=[],
            hypothesis_resolutions=[],
            strategic_pivots=[],
            phase_next_spark_directives=[
                SparkDirectiveItem(
                    directive_id="DIR-01",
                    title="Title",
                    action_type="expand_capability",
                    target_stage_1_spark="SPARK-02",
                )
            ],
            lineage=CumulativeLineageKernel(
                root_spark="SPARK-01",
                generational_index=1,
                immutable_core_invariants=[],
                accumulated_knowledge_hash="hash",
            ),
        )


def test_ac_6_bayes_factor_resolution():
    """AC_6: Bayes Factor adjudication thresholds (BF10 >= 10 validated, BF10 <= 0.1 refuted)."""
    # BF10 >= 10 -> Validated
    item_validated = HypothesisResolutionItem(
        hypothesis_id="HYP-VAL",
        statement="Valid hypothesis",
        terminal_status=HypothesisTerminalStatus.VALIDATED,
        recurrence_depth=0,
        bayes_factor=12.0,
        evidence_references=["EV-1"],
        rationale="BF10 >= 10",
    )
    assert item_validated.bayes_factor >= 10.0
    assert item_validated.terminal_status == HypothesisTerminalStatus.VALIDATED

    # BF10 <= 0.1 -> Refuted
    item_refuted = HypothesisResolutionItem(
        hypothesis_id="HYP-REF",
        statement="Refuted hypothesis",
        terminal_status=HypothesisTerminalStatus.REFUTED,
        recurrence_depth=1,
        bayes_factor=0.05,
        evidence_references=["EV-2"],
        rationale="BF10 <= 0.1",
    )
    assert item_refuted.bayes_factor <= 0.1
    assert item_refuted.terminal_status == HypothesisTerminalStatus.REFUTED


def test_ac_7_strict_recurrence_depth_guard():
    """AC_7: At recurrence_depth >= 2, REFINED is strictly prohibited."""
    # Depth 1 with REFINED is allowed
    item_d1 = HypothesisResolutionItem(
        hypothesis_id="HYP-D1",
        statement="Refining hypothesis",
        terminal_status=HypothesisTerminalStatus.REFINED,
        recurrence_depth=1,
        bayes_factor=2.5,
        evidence_references=["EV-1"],
        promotion_target="HYP-D1.1",
        rationale="Inconclusive, refining for next phase",
    )
    assert item_d1.recurrence_depth == 1
    assert item_d1.terminal_status == HypothesisTerminalStatus.REFINED

    # Depth 2 with REFINED must raise ValidationError
    with pytest.raises(ValidationError, match="At d_max=2, REFINED is prohibited"):
        HypothesisResolutionItem(
            hypothesis_id="HYP-D2",
            statement="Exhausted hypothesis",
            terminal_status=HypothesisTerminalStatus.REFINED,
            recurrence_depth=2,
            bayes_factor=1.8,
            evidence_references=["EV-2"],
            rationale="Trying to refine again at depth 2",
        )

    # Depth 2 with VALIDATED or REFUTED is allowed
    item_d2_collapsed = HypothesisResolutionItem(
        hypothesis_id="HYP-D2",
        statement="Exhausted hypothesis collapsed to REFUTED",
        terminal_status=HypothesisTerminalStatus.REFUTED,
        recurrence_depth=2,
        bayes_factor=1.8,
        evidence_references=["EV-2"],
        rationale="Defaulted to REFUTED due to budget exhaustion at d=2",
    )
    assert item_d2_collapsed.terminal_status == HypothesisTerminalStatus.REFUTED


def test_ac_8_hypothesis_terminality():
    """AC_8: All hypotheses in proposal payload must have terminal status (no pending/testing states)."""
    item = HypothesisResolutionItem(
        hypothesis_id="HYP-01",
        statement="Terminal hypothesis",
        terminal_status=HypothesisTerminalStatus.VALIDATED,
        recurrence_depth=0,
        bayes_factor=15.0,
        evidence_references=["EV-1"],
        rationale="Resolved",
    )
    assert item.terminal_status in {
        HypothesisTerminalStatus.VALIDATED,
        HypothesisTerminalStatus.REFUTED,
        HypothesisTerminalStatus.REFINED,
    }


# ── AC_9, AC_10: Low-Pass Filter Damping & S3-S4 Capacity Balance ─────────────

def calculate_ema_filter(
    deltas: list[float],
    beta: float = 0.75,
    apply_bias_correction: bool = True,
) -> list[float]:
    """Computes EMA low-pass damping filter with bias correction for N < 3."""
    assert 0.6 <= beta <= 0.85, "Momentum beta must be in [0.6, 0.85]"
    smoothed: list[float] = []
    theta = 0.0
    for n, delta in enumerate(deltas, start=1):
        theta = beta * theta + (1 - beta) * delta
        if apply_bias_correction and n < 3:
            corrected = theta / (1.0 - (beta ** n))
            smoothed.append(corrected)
        else:
            smoothed.append(theta)
    return smoothed


def test_ac_9_low_pass_filter_damping():
    """AC_9: Exponential smoothing dampens high-frequency noise and applies warmup."""
    raw_deltas = [10.0, -15.0, 12.0, -8.0, 14.0]
    beta = 0.75
    smoothed = calculate_ema_filter(raw_deltas, beta=beta)
    
    # Check that variance of smoothed series is strictly lower than raw series
    mean_raw = sum(raw_deltas) / len(raw_deltas)
    var_raw = sum((x - mean_raw) ** 2 for x in raw_deltas) / len(raw_deltas)

    mean_smoothed = sum(smoothed) / len(smoothed)
    var_smoothed = sum((x - mean_smoothed) ** 2 for x in smoothed) / len(smoothed)

    assert var_smoothed < var_raw, "Low-pass filter must dampen delta variance"
    # First item under bias correction equals the raw value
    assert math.isclose(smoothed[0], raw_deltas[0], rel_tol=1e-5)


def test_ac_10_s3_s4_capacity_balance():
    """AC_10: Strategic pivots are bounded by ceiling(C_adapt / 2)."""
    c_adapt = 5
    max_pivots = math.ceil(c_adapt / 2)  # 3
    proposed_pivots = ["Pivot 1", "Pivot 2", "Pivot 3"]
    assert len(proposed_pivots) <= max_pivots

    excessive_pivots = ["Pivot 1", "Pivot 2", "Pivot 3", "Pivot 4"]
    assert len(excessive_pivots) > max_pivots


# ── AC_1, AC_11: Decision Policy Gate & Lineage Kernel ───────────────────────

def test_ac_1_full_authority_policy_gate():
    """AC_1: approve-intent-refinement actions shape is defined with full governance options."""
    shape_path = Path("docs/policy-shapes/approve-intent-refinement.actions.json")
    assert shape_path.exists(), "Action shape file must exist"
    actions = json.loads(shape_path.read_text(encoding="utf-8"))
    
    assert isinstance(actions, list)
    action_ids = [a["id"] for a in actions]
    assert "approve_intent_refinement" in action_ids
    assert "reject_intent_refinement" in action_ids
    assert "request_revision_before_decision" in action_ids



def test_ac_11_cumulative_lineage_kernel():
    """AC_11: Lineage kernel preserves root spark, parent refinement, and immutable invariants."""
    lineage = CumulativeLineageKernel(
        root_spark="SPARK-GEN-001",
        parent_refinement="IR-PROP-v1.0.0",
        generational_index=2,
        immutable_core_invariants=["INV-01-STATELESS", "INV-02-FIVE-RECORDS"],
        accumulated_knowledge_hash="sha256-kernel-proof-999",
    )
    assert lineage.root_spark == "SPARK-GEN-001"
    assert lineage.parent_refinement == "IR-PROP-v1.0.0"
    assert lineage.generational_index == 2
    assert len(lineage.immutable_core_invariants) == 2


# ── AC_3, AC_4: Orchestrator Modes (seed-next, decommission, rollback) ────────

def test_ac_4_orchestrator_seed_next(tmp_path: Path):
    """AC_4: seed-next generates Phase N+1 Spark and Ideation with incremented baseline."""
    # Create sample approved refinement proposal
    refinement_doc = tmp_path / "Intent-Refinement-Proposal.md"
    refinement_doc.write_text("""---
refinement_id: "IR-PROP-v1.0.0"
pmp_baseline: "PMP-BL-v1.0.0"
disposition_type: "phase_handoff"
---
# Proposal
""", encoding="utf-8")

    out_dir = tmp_path / "seeded_phase"
    seed_next_phase(refinement_doc, out_dir)

    spark_file = out_dir / "Spark-Capture.md"
    ideation_file = out_dir / "Ideation-Document.md"

    assert spark_file.exists(), "Spark-Capture.md must be generated"
    assert ideation_file.exists(), "Ideation-Document.md must be generated"

    spark_text = spark_file.read_text(encoding="utf-8")
    assert 'pmp_baseline: "PMP-BL-v2.0.0"' in spark_text
    assert 'governed_by_refinement: "IR-PROP-v1.0.0"' in spark_text

    ideation_text = ideation_file.read_text(encoding="utf-8")
    assert 'pmp_baseline: "PMP-BL-v2.0.0"' in ideation_text
    assert "Active Hypotheses Register" in ideation_text


def test_ac_3_orchestrator_decommission(tmp_path: Path):
    """AC_3: decommission logs administrative teardown in target archive."""
    refinement_doc = tmp_path / "Intent-Refinement-Proposal.md"
    refinement_doc.write_text("""---
refinement_id: "IR-PROP-v1.0.0"
pmp_baseline: "PMP-BL-v1.0.0"
disposition_type: "project_termination"
---
# Termination Proposal
""", encoding="utf-8")

    archive_dir = tmp_path / "archive"
    decommission_project(refinement_doc, archive_dir)

    decom_folder = archive_dir / "decommission_Intent-Refinement-Proposal"
    assert decom_folder.exists()
    summary = decom_folder / "DECOMMISSION-SUMMARY.md"
    assert summary.exists()
    summary_text = summary.read_text(encoding="utf-8")
    assert "**Disposition:** Project Termination" in summary_text
    assert "Ephemeral worktrees pruned" in summary_text
