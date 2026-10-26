"""Contract tests for the review-triage record, its episode metadata and reliability evidence.

Story 36.5 (docs/user-stories/epic-36-learning-methodology-examples-ledger-and-review-triage-loop.md)
ADR-036 section 4.5 and Invariants 6 and 7 (docs/adr/ADR-036-...)
BRD-036 BRU-036-05 to BRU-036-07, FDD-036 sections 2.3, 2.4 and 3 (items 3 to 5)

Interpretations not stated verbatim in the acceptance criteria (LL-011):
- I1: the reviewer and the PR number come from the finding id ("Q-12-3": initial Q, PR 12, ordinal
  3). The initial maps to a reviewer name through a table (Q is amazon-q); an unknown initial raises.
- I2: the vocabulary is the FDD's. The implementation log already uses two spellings the FDD does
  not: the claim type "logic" (read as "logic error") and the decision "accepted with modification"
  (read as "accepted", with "(with modification)" put in front of the reason so nothing is lost).
- I3: "backfilled" is a record built with `reconstruct_record`: only the fields the caller can show
  from repository history are given; every other field reads "unknown", and `reconstructed` is True.
- I4: `review_triage.py` imports nothing from a storage module directly. It does import
  `wilson_lower_bound` from `agent_learning.autonomy`, as FDD-036 section 1 item 5 says, and that
  module imports storage; the test checks the module's own imports, as the story states.
- I5: "no account of the decision" (AC_6) is tested by value: records are frozen dataclasses, and the
  decision of every record is compared before and after the two functions run.
- I6: the profile for `route-review-finding` is a low-impact, reversible decision with direct
  outcome observability and no human-approval flag; the profile for `triage-review-finding`
  is medium impact and reversible, with `requires_human_approval` true (ADR-003 Invariant 6).
- I7: `to_episode_metadata` keeps the FDD's name inside `agent_learning.review_triage`, but the
  package root already exports a different `to_episode_metadata` (tailoring), so this one is not
  re-exported from `agent_learning`; callers import it from the module. The other names are exported.
"""

from __future__ import annotations

import ast
import dataclasses
import json
from pathlib import Path

import pytest

from agent_learning.autonomy import ComplexityProfile, wilson_lower_bound
from agent_learning.review_triage import (
    Reliability,
    TriageRecord,
    find_triage_lines,
    parse_triage_line,
    reconstruct_record,
    reliability,
    to_episode_metadata,
)

ROOT = Path(__file__).resolve().parent.parent
SHAPES = ROOT / "docs" / "policy-shapes"
LOG = ROOT / "implementation-log.md"
MODULE = ROOT / "src" / "agent_learning" / "review_triage.py"

LINE = "Q-15-1 | test gap | verified: yes | decision: accepted | check=True raised before the hash assertion | fix: 5048fe2"


def _line(
    finding: str = "Q-12-3",
    claim: str = "logic error",
    verified: str = "yes",
    decision: str = "accepted",
    reason: str = "a reason",
    fix: str = "abc1234",
) -> str:
    return f"{finding} | {claim} | verified: {verified} | decision: {decision} | {reason} | fix: {fix}"


def _record(
    verified: str = "yes",
    claim: str = "logic error",
    reviewer: str = "amazon-q",
    decision: str = "accepted",
    n: int = 1,
) -> TriageRecord:
    return TriageRecord(
        finding_id=f"Q-1-{n}",
        reviewer=reviewer,
        pr=1,
        claim_type=claim,
        verified=verified,
        decision=decision,
        reason="r",
        fix=None,
    )


# --- AC_0: record shape -----------------------------------------------------------------


def test_ac0_a_triage_line_parses_into_a_record() -> None:
    record = parse_triage_line(LINE)
    assert isinstance(record, TriageRecord)
    assert record.finding_id == "Q-15-1" and record.reviewer == "amazon-q" and record.pr == 15
    assert record.claim_type == "test gap" and record.verified == "yes" and record.decision == "accepted"
    assert record.reason == "check=True raised before the hash assertion"
    assert record.fix == "5048fe2" and record.reconstructed is False


def test_ac0_fix_none_reads_as_none_and_a_reason_may_contain_a_bar() -> None:
    record = parse_triage_line(_line(reason="a | b", fix="none"))
    assert record.fix is None and record.reason == "a | b"


@pytest.mark.parametrize(
    ("kwargs", "named"),
    [
        ({"claim": "vibes"}, "claim type"),
        ({"verified": "maybe"}, "verified"),
        ({"decision": "shrugged"}, "decision"),
    ],
)
def test_ac0_a_field_outside_its_vocabulary_raises_naming_the_field_and_value(kwargs: dict, named: str) -> None:
    value = next(iter(kwargs.values()))
    with pytest.raises(ValueError, match=rf"(?s){named}.*{value}"):
        parse_triage_line(_line(**kwargs))


@pytest.mark.parametrize("bad", ["Q-15 | style | verified: yes | decision: accepted | r | fix: none", "nonsense", ""])
def test_ac0_a_malformed_line_raises(bad: str) -> None:
    with pytest.raises(ValueError):
        parse_triage_line(bad)


def test_ac0_an_unknown_reviewer_initial_raises() -> None:
    """Interpretation I1."""
    with pytest.raises(ValueError, match=r"reviewer.*Z"):
        parse_triage_line(_line(finding="Z-1-1"))


def test_ac0_unknown_is_accepted_in_every_vocabulary_field() -> None:
    record = parse_triage_line(_line(claim="unknown", verified="unknown", decision="unknown"))
    assert (record.claim_type, record.verified, record.decision) == ("unknown", "unknown", "unknown")


def test_ac0_the_two_log_spellings_are_read_as_the_fdd_vocabulary() -> None:
    """Interpretation I2."""
    record = parse_triage_line(_line(claim="logic", decision="accepted with modification", reason="why"))
    assert record.claim_type == "logic error"
    assert record.decision == "accepted" and record.reason == "(with modification) why"


def test_ac0_every_recorded_line_in_the_implementation_log_parses() -> None:
    lines = find_triage_lines(LOG.read_text(encoding="utf-8"))
    assert len(lines) >= 10, "the log should carry the Q review records of the earlier stories"
    records = [parse_triage_line(line) for line in lines]
    assert all(r.reviewer == "amazon-q" for r in records)
    assert all(r.reconstructed is False for r in records)


# --- AC_1: episode metadata, no new record type -----------------------------------------------


def test_ac1_episode_metadata_is_a_plain_dict_of_the_record_fields() -> None:
    metadata = to_episode_metadata(parse_triage_line(LINE))
    assert type(metadata) is dict
    assert metadata == {
        "finding_id": "Q-15-1",
        "reviewer": "amazon-q",
        "pr": 15,
        "claim_type": "test gap",
        "verified": "yes",
        "decision": "accepted",
        "reason": "check=True raised before the hash assertion",
        "fix": "5048fe2",
        "reconstructed": False,
    }
    json.dumps(metadata)  # plain data only


def test_ac1_the_module_imports_nothing_from_storage() -> None:
    """Interpretation I4."""
    tree = ast.parse(MODULE.read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            imported.append(("." * node.level) + (node.module or ""))
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
    assert not [name for name in imported if "storage" in name], imported
    assert not [name for name in imported if name.split(".")[0] in {"pathlib", "os", "io", "shutil"}], imported


# --- AC_2: reliability evidence -----------------------------------------------------------------


def test_ac2_reliability_is_the_wilson_lower_bound_over_verified_cases() -> None:
    records = [_record("yes", n=i) for i in range(6)] + [_record("no", n=7), _record("no", n=8)]
    result = reliability(records, "amazon-q", "logic error")
    assert isinstance(result, Reliability)
    assert (result.cases, result.verified) == (8, 6)
    assert result.lower_bound == pytest.approx(wilson_lower_bound(6, 8, 1.96))


def test_ac2_unknown_records_are_excluded_and_partial_counts_as_not_verified() -> None:
    records = [_record("yes", n=i) for i in range(3)] + [_record("partial", n=4), _record("no", n=5), _record("unknown", n=6)]
    result = reliability(records, "amazon-q", "logic error")
    assert (result.cases, result.verified) == (5, 3)


def test_ac2_only_the_named_reviewer_and_claim_type_are_counted() -> None:
    records = [
        _record("yes", n=1),
        _record("yes", claim="style", n=2),
        _record("yes", reviewer="other", n=3),
    ]
    result = reliability(records, "amazon-q", "logic error", min_cases=1)
    assert (result.cases, result.verified) == (1, 1)


def test_ac2_below_min_cases_the_lower_bound_is_none_not_zero() -> None:
    records = [_record("yes", n=i) for i in range(4)]
    result = reliability(records, "amazon-q", "logic error")
    assert result.cases == 4 and result.lower_bound is None
    assert reliability(records, "amazon-q", "logic error", min_cases=4).lower_bound is not None


def test_ac2_no_cases_gives_none() -> None:
    result = reliability([], "amazon-q", "logic error")
    assert (result.cases, result.verified, result.lower_bound) == (0, 0, None)


def test_ac2_the_z_value_is_passed_through() -> None:
    records = [_record("yes", n=i) for i in range(10)]
    result = reliability(records, "amazon-q", "logic error", z=1.0)
    assert result.lower_bound == pytest.approx(wilson_lower_bound(10, 10, 1.0))


# --- AC_3: no guessing on backfill ------------------------------------------------------------------


def test_ac3_a_reconstructed_record_reads_unknown_for_every_field_it_was_not_given() -> None:
    record = reconstruct_record("Q-9-2", claim_type="test gap", decision="declined")
    assert record.reconstructed is True
    assert (record.finding_id, record.reviewer, record.pr) == ("Q-9-2", "amazon-q", 9)
    assert record.claim_type == "test gap" and record.decision == "declined"
    assert record.verified == "unknown" and record.reason == "unknown" and record.fix is None


def test_ac3_a_reconstructed_record_with_nothing_given_is_all_unknown() -> None:
    record = reconstruct_record("Q-9-1")
    assert (record.claim_type, record.verified, record.decision) == ("unknown", "unknown", "unknown")
    assert record.reconstructed is True


def test_ac3_reconstruct_still_rejects_a_value_outside_the_vocabulary() -> None:
    with pytest.raises(ValueError, match=r"verified.*perhaps"):
        reconstruct_record("Q-9-1", verified="perhaps")


def test_ac3_a_reconstructed_unknown_record_adds_no_case_to_the_reliability() -> None:
    records = [reconstruct_record("Q-9-1", claim_type="logic error")]
    assert reliability(records, "amazon-q", "logic error", min_cases=1).cases == 0


# --- AC_4 and AC_5: the declared policy shapes --------------------------------------------------------


def _ids(name: str) -> list[str]:
    return [action["id"] for action in json.loads((SHAPES / name).read_text(encoding="utf-8"))]


def test_ac4_the_triage_shape_lists_exactly_three_actions_and_keeps_the_human() -> None:
    assert sorted(_ids("triage-review-finding.actions.json")) == [
        "accept_and_amend",
        "decline_with_reason",
        "defer_to_human",
    ]
    profile = ComplexityProfile.from_dict(json.loads((SHAPES / "triage-review-finding.profile.json").read_text(encoding="utf-8")))
    assert profile.requires_human_approval is True


def test_ac5_the_routing_shape_orders_verification_and_never_decides() -> None:
    ids = _ids("route-review-finding.actions.json")
    assert sorted(ids) == [
        "verify_documentation_claims_first",
        "verify_logic_claims_first",
        "verify_test_claims_first",
    ]
    assert not [i for i in ids if "accept" in i or "decline" in i]
    profile = ComplexityProfile.from_dict(json.loads((SHAPES / "route-review-finding.profile.json").read_text(encoding="utf-8")))
    assert profile.requires_human_approval is False


def test_ac5_the_two_shapes_do_not_share_actions() -> None:
    assert not set(_ids("triage-review-finding.actions.json")) & set(_ids("route-review-finding.actions.json"))


# --- AC_6: nothing sets the decision -------------------------------------------------------------------


def test_ac6_reliability_and_episode_metadata_leave_every_decision_unchanged() -> None:
    records = [
        _record("yes", decision="accepted", n=1),
        _record("no", decision="declined", n=2),
        _record("partial", decision="deferred", n=3),
        _record("unknown", decision="unknown", n=4),
        reconstruct_record("Q-9-1"),
    ]
    before = [(r.finding_id, r.decision) for r in records]
    reliability(records, "amazon-q", "logic error", min_cases=1)
    for record in records:
        to_episode_metadata(record)
    assert [(r.finding_id, r.decision) for r in records] == before


def test_ac6_records_are_frozen_so_nothing_can_set_a_decision() -> None:
    """Interpretation I5."""
    record = _record()
    with pytest.raises(dataclasses.FrozenInstanceError):
        record.decision = "declined"  # type: ignore[misc]
