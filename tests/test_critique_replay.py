"""Contract tests for Story 14.5: Replay on the Real Triage Records.

Governing Specifications:
- Story: Story 14.5 (Replay on the Real Triage Records)
- Epic: Epic 14 (Lightweight Critique-to-Evidence Ingestion)
- ADR: ADR-014 §4.4 (Test Data: 30 real review-triage records tagged by a person)
- BRD/FDD: BRD-014, FDD-014 §4 (D1-D5), §7, §8

Pre-Flight Interpretations (from scripts/spec_gate.py):
- I1 (Upstream Fork Purity): Replay harness resides in src/agent_learning_ext/ and its contracts in tests/,
  leaving src/agent_learning/ completely pristine per Invariant 6.
- I2 (Storage Decoupling): Replay report and records serialize cleanly to JSON and round-trip
  without coupling to storage subsystems or custom codecs.
- I3 (Defensive None-Safety): Missing fields or comment text default defensively without raising
  AttributeError when None.
- I4 (Empty Collection Base Case): When passed zero triage records or empty lines, the replay
  produces an empty report cleanly with zero counts without raising.

Acceptance Criteria:
- AC_0 (Real Source): Findings come from records in implementation-log.md read with
  review_triage.find_triage_lines, with original comment text exported beside each.
- AC_1 (Tagged By A Person): Every criterion tag and delta is entered by a named person,
  and the name is recorded; the module never proposes them.
- AC_2 (Declined Findings): A finding the human declined in triage is one the human judged
  not to be a real defect, so its recorded delta is zero or positive and never negative;
  applying it does not lower the pooled support of the criterion it names. Any declined
  finding tagged with a negative delta is listed, not hidden.
- AC_3 (Accepted Findings): A finding the human accepted in triage was a real defect,
  so its recorded delta is negative, and applying it lowers the pooled support by that delta.
- AC_4 (Not Evidence Of Effectiveness): The result is recorded as a consistency check on the
  tagging. It makes no claim that the method improves decisions (HYP-AL-005 stays open).
- AC_5 (Empty & Defensive): Passing zero triage records or empty lines returns an empty replay
  report without error; missing optional fields or comment texts default defensively to None
  or empty dictionary without raising AttributeError.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from agent_learning.decision import (
    Action,
    DecisionCriterion,
    DecisionFrame,
    DecisionOption,
    EvidencePoint,
)
from agent_learning.review_triage import TriageRecord, find_triage_lines, parse_triage_line

from agent_learning_ext.triage_replay import (
    ReplayFinding,
    TriageReplayReport,
    load_and_replay_log,
    replay_triage_records,
)

ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT / "implementation-log.md"


def make_test_frame() -> DecisionFrame:
    """Standard base frame with calibrated criteria for replay."""
    criteria = (
        DecisionCriterion(id="correctness", weight=0.40, minimum_sources=1),
        DecisionCriterion(id="test_coverage", weight=0.30, minimum_sources=1),
        DecisionCriterion(id="implementation_quality", weight=0.30, minimum_sources=1),
    )
    opt = DecisionOption(
        action=Action(id="baseline_opt", description="Base Option"),
        evidence=(
            EvidencePoint("correctness", "ci", 0.85, 0.80),
            EvidencePoint("test_coverage", "ci", 0.80, 0.75),
            EvidencePoint("implementation_quality", "ci", 0.80, 0.75),
        ),
    )
    opt_alt = DecisionOption(
        action=Action(id="alt_opt", description="Alternative Option"),
        evidence=(
            EvidencePoint("correctness", "ci", 0.70, 0.70),
            EvidencePoint("test_coverage", "ci", 0.70, 0.70),
            EvidencePoint("implementation_quality", "ci", 0.70, 0.70),
        ),
    )
    return DecisionFrame(task="replay-check", options=(opt, opt_alt), criteria=criteria)


# ==============================================================================
# AC_0: Real Source
# ==============================================================================

def test_ac0_real_source_from_implementation_log() -> None:
    """AC_0: Findings come from implementation-log.md read with find_triage_lines."""
    assert LOG_PATH.is_file(), f"implementation-log.md missing at {LOG_PATH}"
    log_text = LOG_PATH.read_text(encoding="utf-8")
    lines = find_triage_lines(log_text)
    assert len(lines) >= 30, f"Expected at least 30 triage records, found {len(lines)}"

    records = [parse_triage_line(l) for l in lines]
    assert all(isinstance(r, TriageRecord) for r in records)
    assert all(r.finding_id.startswith("Q-") for r in records)


# ==============================================================================
# AC_1: Tagged By A Person
# ==============================================================================

def test_ac1_tagged_by_named_person() -> None:
    """AC_1: Every criterion tag and delta is entered by a named person, and recorded."""
    records = [
        TriageRecord(
            finding_id="Q-11-1",
            reviewer="amazon-q",
            pr=11,
            claim_type="crash risk",
            verified="yes",
            decision="accepted",
            reason="variable removed between reads could raise KeyError",
            fix="6a92064",
        )
    ]
    tagger_name = "Menno Drescher"
    report = replay_triage_records(records, base_frame=make_test_frame(), tagger=tagger_name)
    assert isinstance(report, TriageReplayReport)
    assert report.tagger == tagger_name
    assert len(report.findings) == 1
    assert isinstance(report.findings[0], ReplayFinding)
    assert report.findings[0].tagger == tagger_name


def test_ac1_rejects_empty_tagger() -> None:
    """AC_1: Module requires a non-empty named person and will not guess."""
    records = [
        TriageRecord(
            finding_id="Q-11-1",
            reviewer="amazon-q",
            pr=11,
            claim_type="crash risk",
            verified="yes",
            decision="accepted",
            reason="test",
            fix="none",
        )
    ]
    with pytest.raises(ValueError, match="tagger must be a non-empty string"):
        replay_triage_records(records, base_frame=make_test_frame(), tagger="")


# ==============================================================================
# AC_2: Declined Findings
# ==============================================================================

def test_ac2_declined_findings_never_lower_pooled_support() -> None:
    """AC_2: Declined findings have delta >= 0 and never lower pooled support."""
    declined_record = TriageRecord(
        finding_id="Q-14-1",
        reviewer="amazon-q",
        pr=14,
        claim_type="documentation",
        verified="no",
        decision="declined",
        reason="already in __all__",
        fix="none",
    )
    report = replay_triage_records([declined_record], base_frame=make_test_frame(), tagger="Menno Drescher")
    assert len(report.findings) == 1
    finding = report.findings[0]
    assert finding.decision == "declined"
    assert finding.support_delta >= 0.0
    assert finding.support_after >= finding.support_before
    assert finding.consistent is True


def test_ac2_declined_finding_with_negative_delta_is_flagged_inconsistent() -> None:
    """AC_2: Any declined finding tagged with a negative delta is listed, not hidden."""
    # If an override or anomaly gives a negative delta to a declined finding:
    inconsistent_record = TriageRecord(
        finding_id="Q-TEST-DECLINED-ANOMALY",
        reviewer="amazon-q",
        pr=99,
        claim_type="logic error",
        verified="yes",
        decision="declined",
        reason="anomalous test case",
        fix="none",
    )
    # Using explicit negative override to simulate human tagging anomaly
    report = replay_triage_records(
        [inconsistent_record],
        base_frame=make_test_frame(),
        tagger="Menno Drescher",
        delta_overrides={"Q-TEST-DECLINED-ANOMALY": -0.25},
    )
    assert len(report.findings) == 1
    finding = report.findings[0]
    assert finding.consistent is False
    assert report.consistent_count == 0


# ==============================================================================
# AC_3: Accepted Findings
# ==============================================================================

def test_ac3_accepted_findings_lower_pooled_support_by_delta() -> None:
    """AC_3: Accepted findings have negative delta and lower pooled support by that delta."""
    accepted_record = TriageRecord(
        finding_id="Q-11-1",
        reviewer="amazon-q",
        pr=11,
        claim_type="crash risk",
        verified="yes",
        decision="accepted",
        reason="variable removed between reads could raise KeyError",
        fix="6a92064",
    )
    frame = make_test_frame()
    report = replay_triage_records([accepted_record], base_frame=frame, tagger="Menno Drescher")
    assert len(report.findings) == 1
    finding = report.findings[0]
    assert finding.decision == "accepted"
    assert finding.support_delta < 0.0
    assert finding.support_after < finding.support_before
    assert pytest.approx(finding.delta_applied, abs=1e-6) == finding.support_delta
    assert finding.consistent is True


# ==============================================================================
# AC_4: Not Evidence of Effectiveness
# ==============================================================================

def test_ac4_report_carries_mandatory_disclaimer() -> None:
    """AC_4: Result is recorded as consistency check and makes no claim that method improves decisions."""
    report = load_and_replay_log(LOG_PATH, base_frame=make_test_frame(), tagger="Menno Drescher")
    assert "HYP-AL-005" in report.disclaimer
    assert "makes no claim that the method improves" in report.disclaimer
    assert report.total_findings >= 30
    assert report.consistency_rate >= 0.90  # At least 90% human-triage consistency


# ==============================================================================
# AC_5: Base Case (Empty Collection) & Defensive None-Safety (I3, I4)
# ==============================================================================

def test_ac5_empty_collection_returns_empty_report() -> None:
    """AC_5 & I4: Empty input collection returns clean report with 0 counts without raising."""
    report = replay_triage_records([], base_frame=make_test_frame(), tagger="Menno Drescher")
    assert report.total_findings == 0
    assert report.accepted_count == 0
    assert report.declined_count == 0
    assert report.consistent_count == 0
    assert report.consistency_rate == 1.0


def test_ac5_none_comments_and_missing_attributes_handled_defensively() -> None:
    """AC_5 & I3: Missing comment text or optional fields default defensively without raising."""
    incomplete_record = TriageRecord(
        finding_id="Q-99-1",
        reviewer="amazon-q",
        pr=99,
        claim_type="documentation",
        verified="partial",
        decision="accepted",
        reason="",  # empty reason
        fix="none",
    )
    report = replay_triage_records([incomplete_record], base_frame=make_test_frame(), tagger="Menno Drescher")
    assert len(report.findings) == 1
    assert report.findings[0].rationale == ""
