"""Contract tests for the best-practice ledger parser.

Story 36.4 (docs/user-stories/epic-36-learning-methodology-examples-ledger-and-review-triage-loop.md)
ADR-036 section 4.3 and Invariants 4 and 5 (docs/adr/ADR-036-...)
BRD-036 BRU-036-04, FDD-036 sections 2.2 and 3 (item 2)

Interpretations not stated verbatim in the acceptance criteria (LL-011):
- I1: the module does no file I/O (FDD-036 section 1), so the identifiers that links must resolve
  to (`LL-###`, `HYP-AL-###`) are passed in as `known_links`. With `None` the resolution check is
  skipped; the format check always runs. The register test below passes the real sets, read from
  the Lessons Learned Register and the Ideation Document.
- I2: "the declared tier" is a `tier` field on the entry (low, standard, high, critical). It is
  required when the status is `adopted`, and the gate is `AutonomyConfig.for_tier(tier).min_outcomes`,
  so a tier-specific environment override applies as it does to autonomy (ADR-003).
- I3: an entry that supersedes another must come after it in the register, must concern the same
  methodology, and may be the only one to supersede it (no forks), so each chain is linear and the
  latest entry is current.
- I4: append-only is a maintenance rule on the register file (git history is the guard); the
  parser cannot see a past edit, so it is not tested here.
- I5: a register with no entries is valid (the register starts with candidates only).
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from agent_learning.methodology_ledger import LedgerEntry, current_entries, parse_ledger

ROOT = Path(__file__).resolve().parent.parent
REGISTER = ROOT / "docs" / "project-docs" / "Methodology-Best-Practice-Ledger.md"
LL_REGISTER = ROOT / "docs" / "project-docs" / "Lessons-Learned-Register.md"
IDEATION = ROOT / "docs" / "project-docs" / "Ideation-Document.md"
MODULE = ROOT / "src" / "agent_learning" / "methodology_ledger.py"


def _entry(
    bp: str = "BP-001",
    *,
    methodology: str = "2",
    applies_to: str = "store",
    evidence_class: str = "source-doc",
    evidence_count: str = "0",
    status: str = "candidate",
    tier: str | None = None,
    supersedes: str | None = None,
    links: str | None = None,
    extra: str = "",
) -> str:
    lines = [
        f"## {bp}",
        f"- methodology: {methodology}",
        "- practice: Use contrastive episodes, not positive-only ones.",
        "- preconditions: A recurring decision with both successes and failures.",
        f"- applies_to: {applies_to}",
        f"- evidence_class: {evidence_class}",
        "- evidence_ref: Ideation HYP-AL-002",
        f"- evidence_count: {evidence_count}",
        f"- status: {status}",
    ]
    if tier is not None:
        lines.append(f"- tier: {tier}")
    if supersedes is not None:
        lines.append(f"- supersedes: {supersedes}")
    if links is not None:
        lines.append(f"- links: {links}")
    if extra:
        lines.append(extra)
    return "\n".join(lines) + "\n"


def _text(*entries: str) -> str:
    return "# Ledger\n\nPreamble text that is not an entry.\n\n" + "\n".join(entries)


# --- AC_0: schema -----------------------------------------------------------------


def test_ac0_a_valid_candidate_parses_into_a_ledger_entry() -> None:
    [entry] = parse_ledger(_text(_entry(links="LL-004, HYP-AL-002")))
    assert isinstance(entry, LedgerEntry)
    assert entry.id == "BP-001" and entry.methodology == 2
    assert entry.status == "candidate" and entry.evidence_class == "source-doc"
    assert entry.evidence_count == 0 and entry.supersedes is None
    assert entry.links == ("LL-004", "HYP-AL-002")


def test_ac0_an_empty_register_is_valid() -> None:
    """Interpretation I5."""
    assert parse_ledger("# Ledger\n\nNo entries yet.\n") == []


@pytest.mark.parametrize(
    ("kwargs", "named"),
    [
        ({"applies_to": "everywhere"}, "applies_to"),
        ({"evidence_class": "vibes"}, "evidence_class"),
        ({"status": "done"}, "status"),
        ({"tier": "ultra", "status": "candidate"}, "tier"),
    ],
)
def test_ac0_an_unknown_enumeration_value_raises_naming_the_entry(kwargs: dict, named: str) -> None:
    with pytest.raises(ValueError, match=rf"BP-007.*{named}"):
        parse_ledger(_text(_entry("BP-007", **kwargs)))


@pytest.mark.parametrize("methodology", ["0", "33", "x"])
def test_ac0_an_unknown_methodology_id_raises_naming_the_entry(methodology: str) -> None:
    with pytest.raises(ValueError, match=r"BP-003.*methodology"):
        parse_ledger(_text(_entry("BP-003", methodology=methodology)))


def test_ac0_an_unknown_field_and_a_missing_field_raise_naming_the_entry() -> None:
    with pytest.raises(ValueError, match=r"BP-004.*mood"):
        parse_ledger(_text(_entry("BP-004", extra="- mood: hopeful")))
    broken = _entry("BP-005").replace("- practice: Use contrastive episodes, not positive-only ones.\n", "")
    with pytest.raises(ValueError, match=r"BP-005.*practice"):
        parse_ledger(_text(broken))


def test_ac0_a_duplicate_id_and_a_bad_evidence_count_raise() -> None:
    with pytest.raises(ValueError, match=r"duplicate.*BP-001"):
        parse_ledger(_text(_entry("BP-001"), _entry("BP-001")))
    with pytest.raises(ValueError, match=r"BP-001.*evidence_count"):
        parse_ledger(_text(_entry(evidence_count="-1")))
    with pytest.raises(ValueError, match=r"BP-001.*evidence_count"):
        parse_ledger(_text(_entry(evidence_count="many")))


# --- AC_1: adoption needs real episodes ---------------------------------------------


@pytest.mark.parametrize("evidence_class", ["source-doc", "synthetic-demo"])
def test_ac1_adopted_on_source_doc_or_synthetic_demo_raises(evidence_class: str) -> None:
    with pytest.raises(ValueError, match=r"BP-002.*real-episodes"):
        parse_ledger(_text(_entry("BP-002", evidence_class=evidence_class, evidence_count="500", status="adopted", tier="standard")))


def test_ac1_adopted_below_the_tier_gate_raises_and_at_the_gate_parses() -> None:
    with pytest.raises(ValueError, match=r"BP-002.*19.*20"):
        parse_ledger(_text(_entry("BP-002", evidence_class="real-episodes", evidence_count="19", status="adopted", tier="standard")))
    [entry] = parse_ledger(_text(_entry("BP-002", evidence_class="real-episodes", evidence_count="20", status="adopted", tier="standard")))
    assert entry.status == "adopted"


def test_ac1_the_gate_follows_the_declared_tier() -> None:
    """low needs 3 outcomes, so 3 real episodes adopt at low but not at standard (interpretation I2)."""
    [entry] = parse_ledger(_text(_entry(evidence_class="real-episodes", evidence_count="3", status="adopted", tier="low")))
    assert entry.tier == "low"
    with pytest.raises(ValueError, match=r"BP-001.*standard"):
        parse_ledger(_text(_entry(evidence_class="real-episodes", evidence_count="3", status="adopted", tier="standard")))


def test_ac1_adopted_without_a_tier_raises() -> None:
    with pytest.raises(ValueError, match=r"BP-001.*tier"):
        parse_ledger(_text(_entry(evidence_class="real-episodes", evidence_count="500", status="adopted")))


# --- AC_2: append-only chain ----------------------------------------------------------


def test_ac2_a_status_change_supersedes_and_the_latest_in_the_chain_is_current() -> None:
    first = _entry("BP-001")
    second = _entry("BP-002", supersedes="BP-001", status="retired")
    entries = parse_ledger(_text(first, second))
    assert [e.id for e in current_entries(entries)] == ["BP-002"]


def test_ac2_unrelated_entries_are_all_current() -> None:
    entries = parse_ledger(_text(_entry("BP-001"), _entry("BP-002", methodology="9")))
    assert [e.id for e in current_entries(entries)] == ["BP-001", "BP-002"]


def test_ac2_an_unknown_supersedes_raises_naming_the_entry() -> None:
    with pytest.raises(ValueError, match=r"BP-002.*BP-099"):
        parse_ledger(_text(_entry("BP-001"), _entry("BP-002", supersedes="BP-099")))


def test_ac2_supersedes_must_point_backward_at_the_same_methodology_without_forks() -> None:
    """Interpretation I3."""
    with pytest.raises(ValueError, match=r"BP-001.*BP-002"):  # forward reference
        parse_ledger(_text(_entry("BP-001", supersedes="BP-002"), _entry("BP-002")))
    with pytest.raises(ValueError, match=r"BP-002.*methodology"):
        parse_ledger(_text(_entry("BP-001"), _entry("BP-002", methodology="9", supersedes="BP-001")))
    with pytest.raises(ValueError, match=r"BP-003.*already superseded"):
        parse_ledger(_text(_entry("BP-001"), _entry("BP-002", supersedes="BP-001"), _entry("BP-003", supersedes="BP-001")))


def test_ac2_a_chain_of_three_has_only_its_tail_current() -> None:
    entries = parse_ledger(_text(_entry("BP-001"), _entry("BP-002", supersedes="BP-001"), _entry("BP-003", supersedes="BP-002")))
    assert [e.id for e in current_entries(entries)] == ["BP-003"]


# --- AC_3: links resolve --------------------------------------------------------------


def test_ac3_a_link_with_a_bad_format_raises_even_without_known_links() -> None:
    with pytest.raises(ValueError, match=r"BP-001.*LL-4"):
        parse_ledger(_text(_entry(links="LL-4")))


def test_ac3_a_link_that_does_not_resolve_raises_naming_the_entry_and_the_link() -> None:
    known = {"LL-004", "HYP-AL-002"}
    parse_ledger(_text(_entry(links="LL-004, HYP-AL-002")), known_links=known)
    with pytest.raises(ValueError, match=r"BP-001.*HYP-AL-099"):
        parse_ledger(_text(_entry(links="LL-004, HYP-AL-099")), known_links=known)


# --- AC_4: pure -----------------------------------------------------------------------


def test_ac4_the_module_imports_nothing_from_storage_and_does_no_file_io() -> None:
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


# --- the real register ----------------------------------------------------------------


def _known_links() -> set[str]:
    ll = set(re.findall(r"^\| \[(LL-\d{3})\]", LL_REGISTER.read_text(encoding="utf-8"), re.MULTILINE))
    hyp = set(re.findall(r"\*\*(HYP-AL-\d{3})\*\*", IDEATION.read_text(encoding="utf-8")))
    return ll | hyp


def test_the_real_register_parses_with_every_link_resolving_and_adopts_nothing_yet() -> None:
    known = _known_links()
    assert "LL-004" in known and "HYP-AL-002" in known, "link source patterns drifted"
    entries = parse_ledger(REGISTER.read_text(encoding="utf-8"), known_links=known)
    assert entries, "the register should start with candidate entries"
    assert all(e.evidence_class != "real-episodes" for e in entries), "no real episodes exist yet"
    assert not [e for e in entries if e.status == "adopted"]
