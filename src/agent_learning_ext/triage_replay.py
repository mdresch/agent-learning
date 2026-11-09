"""Review-Triage Critique Replay Engine (Story 14.5 / ADR-014 §4.4).

Replays real Amazon Q, maintainer, and human review triage records from implementation-log.md
through Epic 14's lightweight critique-to-evidence engine. Validates that human acceptances
and rejections align with calibrated support shifts and doubt increments.

Pure module: standard library only, imports nothing from the storage subsystem,
and performs no file or network I/O except for log/fixture reading helpers.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

from agent_learning.decision import (
    Action,
    DecisionCriterion,
    DecisionFrame,
    DecisionOption,
    EvidencePoint,
)
from agent_learning.review_triage import TriageRecord, find_triage_lines, parse_triage_line

from agent_learning_ext.critique_evidence import (
    CritiqueDelta,
    apply_critique,
    rubric_delta,
)

DISCLAIMER_TEXT = (
    "This report is an internal consistency check on reviewer triage tagging "
    "and makes no claim that the method improves decision outcomes (HYP-AL-005 remains open)."
)

CLAIM_TO_CRITERION_MAP: Mapping[str, str] = {
    "crash risk": "correctness",
    "logic error": "correctness",
    "test gap": "test_coverage",
    "documentation": "implementation_quality",
    "style": "implementation_quality",
    "confirmation": "correctness",
}


@dataclass(frozen=True)
class ReplayFinding:
    """The result of replaying a single triaged finding through Epic 14."""

    finding_id: str
    pr: int
    claim_type: str
    verified: str
    decision: str
    criterion_id: str
    support_delta: float
    rationale: str
    tagger: str
    support_before: float
    support_after: float
    delta_applied: float
    consistent: bool
    override: bool = False


@dataclass(frozen=True)
class TriageReplayReport:
    """Summary report of replaying a batch of triage records through Epic 14."""

    tagger: str
    total_findings: int
    accepted_count: int
    declined_count: int
    consistent_count: int
    findings: tuple[ReplayFinding, ...]
    consistency_rate: float
    disclaimer: str = DISCLAIMER_TEXT


def map_claim_to_criterion(claim_type: str) -> str:
    """Map a finding claim type to a standardized DecisionFrame criterion."""
    clean = claim_type.strip().lower()
    return CLAIM_TO_CRITERION_MAP.get(clean, "correctness")


def _make_default_frame() -> DecisionFrame:
    """Construct default DecisionFrame covering all mapped criteria."""
    criteria = (
        DecisionCriterion(id="correctness", weight=0.40, minimum_sources=1),
        DecisionCriterion(id="test_coverage", weight=0.30, minimum_sources=1),
        DecisionCriterion(id="implementation_quality", weight=0.30, minimum_sources=1),
    )
    opt_a = DecisionOption(
        action=Action(id="baseline_opt", description="Target Option"),
        evidence=(
            EvidencePoint("correctness", "ci", 0.85, 0.80),
            EvidencePoint("test_coverage", "ci", 0.80, 0.75),
            EvidencePoint("implementation_quality", "ci", 0.80, 0.75),
        ),
    )
    opt_b = DecisionOption(
        action=Action(id="alt_opt", description="Alternative Option"),
        evidence=(
            EvidencePoint("correctness", "ci", 0.70, 0.70),
            EvidencePoint("test_coverage", "ci", 0.70, 0.70),
            EvidencePoint("implementation_quality", "ci", 0.70, 0.70),
        ),
    )
    return DecisionFrame(task="replay-check", options=(opt_a, opt_b), criteria=criteria)


def replay_triage_finding(
    record: TriageRecord,
    base_frame: DecisionFrame,
    tagger: str,
    delta_override: float | None = None,
    option_id: str = "baseline_opt",
) -> ReplayFinding:
    """Replay a single TriageRecord against a DecisionFrame using Epic 14."""
    if not tagger or not tagger.strip():
        raise ValueError("tagger must be a non-empty string naming the person who tagged the findings")

    criterion_id = map_claim_to_criterion(record.claim_type)
    override = delta_override is not None

    decision_norm = record.decision.strip().lower()

    if delta_override is not None:
        delta_val = delta_override
    elif "accepted" in decision_norm:
        # Accepted findings are real defects -> negative delta from rubric
        try:
            delta_val = rubric_delta(record.claim_type, record.verified)
        except ValueError:
            # Fallback calibrated default if claim_type is aliased
            delta_val = -0.25 if record.verified == "yes" else -0.13
    else:
        # Declined or deferred findings are not accepted as defects -> 0.0 delta (preserves support)
        delta_val = 0.0

    delta = CritiqueDelta(
        criterion_id=criterion_id,
        support_delta=delta_val,
        rationale=record.reason or "",
        finding_id=record.finding_id,
        basis="explicit" if override else "rubric",
        rubric_delta=delta_val if not override else None,
        override=override,
    )

    applied = apply_critique(base_frame, option_id=option_id, deltas=[delta])
    adj = applied.adjustments[0]
    s_before = float(adj["support_before"])
    s_after = float(adj["support_after"])
    applied_shift = s_after - s_before

    # Consistency assessment per AC_2 and AC_3:
    # - Accepted finding must have negative delta and reduce support
    # - Declined finding must have non-negative delta and not reduce support
    if "accepted" in decision_norm:
        is_consistent = (delta_val < 0.0) and (s_after < s_before)
    else:
        is_consistent = (delta_val >= 0.0) and (s_after >= s_before)

    return ReplayFinding(
        finding_id=record.finding_id,
        pr=record.pr,
        claim_type=record.claim_type,
        verified=record.verified,
        decision=record.decision,
        criterion_id=criterion_id,
        support_delta=delta_val,
        rationale=record.reason or "",
        tagger=tagger,
        support_before=s_before,
        support_after=s_after,
        delta_applied=applied_shift,
        consistent=is_consistent,
        override=override,
    )


def replay_triage_records(
    records: Sequence[TriageRecord],
    base_frame: DecisionFrame | None = None,
    tagger: str = "Menno Drescher",
    delta_overrides: Mapping[str, float] | None = None,
    option_id: str = "baseline_opt",
) -> TriageReplayReport:
    """Replay a sequence of TriageRecords through Epic 14 and summarize consistency."""
    if not tagger or not tagger.strip():
        raise ValueError("tagger must be a non-empty string naming the person who tagged the findings")

    if not records:
        return TriageReplayReport(
            tagger=tagger,
            total_findings=0,
            accepted_count=0,
            declined_count=0,
            consistent_count=0,
            findings=(),
            consistency_rate=1.0,
            disclaimer=DISCLAIMER_TEXT,
        )

    frame = base_frame if base_frame is not None else _make_default_frame()
    overrides = delta_overrides or {}

    replayed: list[ReplayFinding] = []
    accepted_n = 0
    declined_n = 0
    consistent_n = 0

    for rec in records:
        override_val = overrides.get(rec.finding_id)
        rf = replay_triage_finding(
            record=rec,
            base_frame=frame,
            tagger=tagger,
            delta_override=override_val,
            option_id=option_id,
        )
        replayed.append(rf)

        dec = rec.decision.strip().lower()
        if "accepted" in dec:
            accepted_n += 1
        else:
            declined_n += 1

        if rf.consistent:
            consistent_n += 1

    rate = consistent_n / len(replayed) if replayed else 1.0

    return TriageReplayReport(
        tagger=tagger,
        total_findings=len(replayed),
        accepted_count=accepted_n,
        declined_count=declined_n,
        consistent_count=consistent_n,
        findings=tuple(replayed),
        consistency_rate=round(rate, 4),
        disclaimer=DISCLAIMER_TEXT,
    )


def load_and_replay_log(
    log_path: Path | str,
    base_frame: DecisionFrame | None = None,
    tagger: str = "Menno Drescher",
    delta_overrides: Mapping[str, float] | None = None,
    option_id: str = "baseline_opt",
) -> TriageReplayReport:
    """Read triage records from an implementation-log.md file and replay them."""
    path = Path(log_path)
    if not path.is_file():
        raise FileNotFoundError(f"Implementation log file not found at {path}")

    text = path.read_text(encoding="utf-8")
    lines = find_triage_lines(text)
    records = [parse_triage_line(l) for l in lines]
    return replay_triage_records(
        records=records,
        base_frame=base_frame,
        tagger=tagger,
        delta_overrides=delta_overrides,
        option_id=option_id,
    )


def export_replay_dataset(
    records: Sequence[TriageRecord],
    output_path: Path | str,
    tagger: str = "Menno Drescher",
    delta_overrides: Mapping[str, float] | None = None,
) -> None:
    """Export triaged findings and their calibrated replay outcomes to a JSON fixture."""
    report = replay_triage_records(
        records=records,
        tagger=tagger,
        delta_overrides=delta_overrides,
    )
    data = {
        "tagger": report.tagger,
        "total_findings": report.total_findings,
        "accepted_count": report.accepted_count,
        "declined_count": report.declined_count,
        "consistent_count": report.consistent_count,
        "consistency_rate": report.consistency_rate,
        "disclaimer": report.disclaimer,
        "findings": [asdict(f) for f in report.findings],
    }
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=2), encoding="utf-8")
