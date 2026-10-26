"""Contract tests for the methodology tailoring matrix.

Story 36.6 (docs/user-stories/epic-36-learning-methodology-examples-ledger-and-review-triage-loop.md)
ADR-036 section 4.4 and Invariant 4 (docs/adr/ADR-036-...)
BRD-036 BRU-036-09, FDD-036 section 1

Interpretations not stated verbatim in the acceptance criteria (LL-011):
- I1: the matrix is a Markdown table in docs/project-docs/Methodology-Tailoring-Matrix.md; this
  test parses it. No module is added, because the matrix is a register read by people.
- I2: "links to a ledger entry with status candidate" means the row's `Ledger` column names an
  entry that exists, is current (not superseded), has status `candidate`, and concerns one of the
  methodology ids named in the same row.
- I3: "a need for the store or lessons learned" is the `Applies to` column, which must be `store`
  or `lessons-learned`.
- I4: AC_2 (propagation to sidpa-template) spans two repositories; it cannot be a test here. It is
  checked by the template's own integrity tests, run when the template is changed, and recorded in
  the implementation log. This file checks only this repository's side.
- I5: AC_3 (the epic recap) is checked here by the register: a Lessons Learned entry whose Epic
  field names Epic 36 exists, and the index lists it.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from agent_learning.methodology_ledger import current_entries, parse_ledger

ROOT = Path(__file__).resolve().parent.parent
MATRIX = ROOT / "docs" / "project-docs" / "Methodology-Tailoring-Matrix.md"
LEDGER = ROOT / "docs" / "project-docs" / "Methodology-Best-Practice-Ledger.md"
CATALOG = ROOT / "examples" / "methodologies" / "catalog.json"
LL_REGISTER = ROOT / "docs" / "project-docs" / "Lessons-Learned-Register.md"
IDEATION = ROOT / "docs" / "project-docs" / "Ideation-Document.md"

COLUMNS = ["Need", "Applies to", "Methodology (catalog ids)", "Hypothesis", "Falsifiable by", "Ledger", "Status"]


def _rows() -> list[dict[str, str]]:
    lines = MATRIX.read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("| Need |"))
    header = [cell.strip() for cell in lines[start].strip().strip("|").split("|")]
    assert header == COLUMNS, header
    rows = []
    for line in lines[start + 2 :]:
        if not line.startswith("|"):
            break
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        assert len(cells) == len(COLUMNS), line
        rows.append(dict(zip(COLUMNS, cells, strict=True)))
    return rows


def _catalog_ids() -> set[int]:
    return {entry["id"] for entry in json.loads(CATALOG.read_text(encoding="utf-8"))}


def _ids(cell: str) -> list[int]:
    return [int(n) for n in re.findall(r"#(\d+)", cell)]


def test_ac0_the_matrix_has_the_six_adr_pairings() -> None:
    needs = [row["Need"] for row in _rows()]
    assert len(needs) == 6, needs
    assert len(set(needs)) == 6


def test_ac0_every_row_names_existing_catalog_ids() -> None:
    catalog = _catalog_ids()
    for row in _rows():
        ids = _ids(row["Methodology (catalog ids)"])
        assert ids, row["Need"]
        assert set(ids) <= catalog, (row["Need"], ids)


def test_ac0_every_row_has_a_need_for_the_store_or_lessons_learned_and_a_falsification_criterion() -> None:
    """Interpretation I3."""
    for row in _rows():
        assert row["Need"].strip(), row
        assert row["Applies to"] in {"store", "lessons-learned"}, row
        assert len(row["Falsifiable by"].strip()) > 10, row


def test_ac0_every_row_is_marked_hypothesis_never_finding() -> None:
    assert {row["Status"] for row in _rows()} == {"hypothesis"}
    assert "finding" not in {row["Status"] for row in _rows()}


def test_ac0_every_hypothesis_named_in_a_row_exists_in_the_ideation_document() -> None:
    known = set(re.findall(r"\*\*(HYP-AL-\d{3})\*\*", IDEATION.read_text(encoding="utf-8")))
    for row in _rows():
        named = re.findall(r"HYP-AL-\d{3}", row["Hypothesis"])
        assert named, row["Need"]
        assert set(named) <= known, (row["Need"], named)


def test_ac1_every_row_links_to_a_current_candidate_ledger_entry_of_one_of_its_methodologies() -> None:
    """Interpretation I2."""
    entries = parse_ledger(LEDGER.read_text(encoding="utf-8"))
    current = {entry.id: entry for entry in current_entries(entries)}
    for row in _rows():
        entry = current.get(row["Ledger"])
        assert entry is not None, f"{row['Need']}: {row['Ledger']} is not a current ledger entry"
        assert entry.status == "candidate", (row["Need"], entry.status)
        assert entry.methodology in _ids(row["Methodology (catalog ids)"]), (row["Need"], entry.methodology)


def test_ac1_no_ledger_entry_is_adopted_yet() -> None:
    """Invariant 4: no real episodes of a methodology exist, so nothing is adopted."""
    entries = parse_ledger(LEDGER.read_text(encoding="utf-8"))
    assert not [e for e in entries if e.status == "adopted"]


def test_ac3_the_epic_recap_is_recorded_in_the_lessons_learned_register() -> None:
    """Interpretation I5."""
    text = LL_REGISTER.read_text(encoding="utf-8")
    sections = re.split(r"^### (?=LL-\d{3} )", text, flags=re.MULTILINE)[1:]
    epic36 = [section[:6] for section in sections if re.search(r"\*\*Epic / Story:\*\*[^\n]*Epic 36", section)]
    assert epic36, "no Lessons Learned entry names Epic 36"
    for ll in epic36:
        assert re.search(rf"^\| \[{ll}\]", text, re.MULTILINE), f"{ll} is not in the index"
