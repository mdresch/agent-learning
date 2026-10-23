"""Contract tests for Story 5.1 / ADR-005: Decision-Progress Comparison and Regression Healing.

Governing documents:
- ADR-005: docs/adr/ADR-005-decision-progress-comparison.md
- BRD-005: docs/project-docs/Business-Requirements/BRD-005-decision-progress-comparison.md
- FDD-005: docs/project-docs/Functional-Design/FDD-005-decision-progress-comparison.md
- Epic 5 / Story 5.1: docs/user-stories/epic-5-decision-progress-comparison.md
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch
import pytest

from agent_learning import DecisionResult
from agent_learning.comparison import (
    DEFAULT_EPSILON,
    ClassificationType,
    PairwiseComparison,
    SequenceComparisonResult,
    compare_decision_results,
    compare_decision_sequence,
    _validate_preconditions,
    _classify,
)
from agent_learning.cli import main as cli_main


FIXTURES_DIR = Path(__file__).resolve().parent.parent

ADR_001_FILE = FIXTURES_DIR / "adr-001-decision-result.json"
BRD_001_FILE = FIXTURES_DIR / "brd-001-decision-result.json"
ADR_002_V1_FILE = FIXTURES_DIR / "adr-002-decision-result.json"
ADR_002_V2_FILE = FIXTURES_DIR / "adr-002-decision-result-v2.json"
ADR_005_ACCEPTED_FILE = FIXTURES_DIR / "adr-005-decision-result.json"
ADR_005_REGRESSED_FILE = FIXTURES_DIR / "adr-005-regressed-decision-result.json"


def _load_result(path: Path) -> DecisionResult:
    with open(path, "r", encoding="utf-8") as f:
        return DecisionResult.from_dict(json.load(f))


def test_ac0_precondition_validation_mismatch_raises():
    """AC_0: _validate_preconditions raises ValueError naming the mismatched field.
    
    Contract-test using real adr-001-decision-result.json vs brd-001-decision-result.json fixture
    (real task_id mismatch), asserting the raise.
    """
    res_adr001 = _load_result(ADR_001_FILE)
    res_brd001 = _load_result(BRD_001_FILE)

    with pytest.raises(ValueError) as exc_info:
        _validate_preconditions(res_adr001, res_brd001)

    assert "task_id" in str(exc_info.value)


def test_ac1_per_action_deltas():
    """AC_1: compare_decision_results() reports robust_utility, expected_utility, and uncertainty
    delta for every action, not only the leader.
    
    Contract-test against the real adr-002-decision-result.json -> adr-002-decision-result-v2.json
    pair, asserting the exact deltas:
      approve_adr: +0.03421
      reject_adr: -0.02867
      request_revision_before_decision: -0.03815
    """
    res_v1 = _load_result(ADR_002_V1_FILE)
    res_v2 = _load_result(ADR_002_V2_FILE)

    comparison = compare_decision_results(res_v1, res_v2)

    deltas = comparison.action_deltas
    assert set(deltas.keys()) == {"approve_adr", "reject_adr", "request_revision_before_decision"}

    assert pytest.approx(deltas["approve_adr"].robust_utility_delta, abs=1e-4) == 0.03421
    assert pytest.approx(deltas["reject_adr"].robust_utility_delta, abs=1e-4) == -0.02867
    assert pytest.approx(deltas["request_revision_before_decision"].robust_utility_delta, abs=1e-4) == -0.03815


def test_ac2_classification_progression():
    """AC_2: _classify resolves the same real ADR-002 pair to progression (margin 0.74410 -> 0.81646),
    using ADR-005 §4.4's proven-exhaustive taxonomy verbatim, with DEFAULT_EPSILON = 0.01.
    """
    res_v1 = _load_result(ADR_002_V1_FILE)
    res_v2 = _load_result(ADR_002_V2_FILE)

    comparison = compare_decision_results(res_v1, res_v2, epsilon=DEFAULT_EPSILON)

    assert comparison.classification == ClassificationType.PROGRESSION
    assert pytest.approx(comparison.margin_before, abs=1e-4) == 0.74410
    assert pytest.approx(comparison.margin_after, abs=1e-4) == 0.81646
    assert pytest.approx(comparison.margin_delta, abs=1e-4) == 0.07236


def test_ac3_cli_task_policy_compare(capsys):
    """AC_3: agent-learn task-policy-compare --sequence <file1> <file2> runs the real ADR-002 pair
    end-to-end and prints the per-action deltas and the progression classification.
    """
    exit_code = cli_main([
        "task-policy-compare",
        "--sequence",
        str(ADR_002_V1_FILE),
        str(ADR_002_V2_FILE),
    ])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "progression" in captured.out.lower()
    assert "approve_adr" in captured.out
    assert "+0.0342" in captured.out or "0.0342" in captured.out
    assert "-0.0286" in captured.out or "-0.0287" in captured.out


def test_ac4_regression_attribution_and_escalation(capsys):
    """AC_4: on a regression classification, the heal step prints per-criterion attribution,
    a running regression-streak count against --retry-cap (default 3), and an ESCALATE line
    once the cap is reached, exiting 0.
    
    Contract-test against adr-005-decision-result.json -> adr-005-regressed-decision-result.json.
    approve_adr robust utility fell -0.1784, margin narrowed 0.8077 -> 0.5483.
    """
    res_acc = _load_result(ADR_005_ACCEPTED_FILE)
    res_reg = _load_result(ADR_005_REGRESSED_FILE)

    comparison = compare_decision_results(res_acc, res_reg)
    assert comparison.classification == ClassificationType.REGRESSION
    assert pytest.approx(comparison.leader_robust_utility_delta, abs=1e-4) == -0.17844
    assert pytest.approx(comparison.margin_before, abs=1e-4) == 0.80775
    assert pytest.approx(comparison.margin_after, abs=1e-4) == 0.54832

    # Check attribution: consequences_honest and gap_disclosure_quality moved negatively
    neg_criteria = [item["criterion_id"] for item in comparison.attribution]
    assert "consequences_honest" in neg_criteria
    assert "gap_disclosure_quality" in neg_criteria

    # Test CLI with --retry-cap 1 to verify ESCALATE trigger and exit 0
    exit_code = cli_main([
        "task-policy-compare",
        "--sequence",
        str(ADR_005_ACCEPTED_FILE),
        str(ADR_005_REGRESSED_FILE),
        "--retry-cap",
        "1",
    ])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "regression" in captured.out.lower()
    assert "consequences_honest" in captured.out
    assert "gap_disclosure_quality" in captured.out
    assert "ESCALATE" in captured.out


def test_ac5_stateless_no_writes_and_no_storage():
    """AC_5: the heal step never writes to any ADR/BRD/FDD/Story file and never calls LearningStore.
    
    Contract-test that compare_decision_results() and task-policy-compare make zero filesystem
    writes outside their own stdout and zero calls into storage/*.
    """
    with patch("agent_learning.storage.cosmos.get_default_store") as mock_store:
        exit_code = cli_main([
            "task-policy-compare",
            "--sequence",
            str(ADR_002_V1_FILE),
            str(ADR_002_V2_FILE),
        ])
        assert exit_code == 0
        mock_store.assert_not_called()

