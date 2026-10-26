"""Contract tests for the learning methodology catalog.

Story 36.1 (docs/user-stories/epic-36-learning-methodology-examples-ledger-and-review-triage-loop.md)
ADR-036 section 4.1 and Invariants 1 to 3 (docs/adr/ADR-036-...)
BRD-036 BRU-036-01 and BRU-036-08, FDD-036 sections 1 and 2.1

Interpretations not stated verbatim in the acceptance criteria (LL-011):
- I1: the module does no file I/O (FDD-036 section 1), so AC_3's "every path exists" is checked
  against a set of existing paths the caller passes in (`existing_paths`). With `None` the
  existence check is skipped; the path-prefix check always runs. Stories 36.2 and 36.3 pass the
  real set, because the example directories do not exist yet.
- I2: the catalog `state` uses canonical tokens (implemented, example_only, partial, practiced,
  candidate, blocked, excluded, declined, not_applicable) rather than the free text in Ideation
  section 2.1. The expected states are the committed fixture
  tests/fixtures/methodology_catalog/ideation_states.json; a drift between that fixture and the
  Ideation table is not detected automatically (ADR-036 section 8, question 2).
- I3: a candidate with a Proposed ADR is a proof_of_concept even when the Ideation notes a data
  prerequisite (#23); the class follows the catalog state, which is the Ideation row.
"""

from __future__ import annotations

import ast
import copy
import json
from pathlib import Path

import pytest

from agent_learning.methodology_catalog import (
    CatalogEntry,
    ExampleClass,
    derive_class,
    parse_catalog,
    validate_catalog,
)

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "examples" / "methodologies" / "catalog.json"
STATES = ROOT / "tests" / "fixtures" / "methodology_catalog" / "ideation_states.json"


def _raw() -> list[dict]:
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def _states() -> dict[int, str]:
    return {int(k): v for k, v in json.loads(STATES.read_text(encoding="utf-8"))["states"].items()}


def _entries(raw: list[dict] | None = None) -> list[CatalogEntry]:
    return parse_catalog(raw if raw is not None else _raw())


def test_ac0_real_catalog_has_exactly_the_32_methodologies() -> None:
    """AC_0: the shipped catalog validates and covers ids 1 to 32 once each."""
    entries = _entries()
    validate_catalog(entries, _states())
    assert sorted(e.id for e in entries) == list(range(1, 33))


def test_ac0_missing_id_is_named() -> None:
    """AC_0: a missing id raises ValueError naming it."""
    raw = [e for e in _raw() if e["id"] != 7]
    with pytest.raises(ValueError, match=r"missing.*\b7\b"):
        validate_catalog(_entries(raw), _states())


def test_ac0_duplicate_id_is_named() -> None:
    """AC_0: a duplicate id raises ValueError naming it."""
    raw = _raw()
    raw.append(copy.deepcopy(raw[4]))
    with pytest.raises(ValueError, match=r"duplicate.*\b5\b"):
        validate_catalog(_entries(raw), _states())


@pytest.mark.parametrize("extra_id", [0, 33])
def test_ac0_id_outside_range_is_named(extra_id: int) -> None:
    """AC_0: an id outside 1 to 32 raises ValueError naming it."""
    raw = _raw()
    extra = copy.deepcopy(raw[0])
    extra["id"] = extra_id
    raw.append(extra)
    with pytest.raises(ValueError, match=rf"\b{extra_id}\b.*outside"):
        validate_catalog(_entries(raw), _states())


@pytest.mark.parametrize(
    ("state", "adr", "expected"),
    [
        ("implemented", None, ExampleClass.RUNNABLE),
        ("example_only", None, ExampleClass.RUNNABLE),
        ("partial", None, ExampleClass.RUNNABLE),
        ("practiced", None, ExampleClass.RUNNABLE),
        ("candidate", "ADR-014", ExampleClass.PROOF_OF_CONCEPT),
        ("candidate", None, ExampleClass.DOCUMENTED),
        ("blocked", None, ExampleClass.DOCUMENTED),
        ("blocked", "ADR-023", ExampleClass.DOCUMENTED),
        ("excluded", None, ExampleClass.DOCUMENTED),
        ("declined", None, ExampleClass.DOCUMENTED),
        ("not_applicable", None, ExampleClass.DOCUMENTED),
    ],
)
def test_ac1_derive_class_follows_the_state(state: str, adr: str | None, expected: ExampleClass) -> None:
    """AC_1: each state maps to its class per FDD-036 section 2.1."""
    assert derive_class(state, adr) is expected


def test_ac1_unknown_state_is_rejected() -> None:
    """AC_1 (interpretation I2): a state outside the canonical tokens raises."""
    with pytest.raises(ValueError, match="state"):
        derive_class("somewhat built", None)


def test_ac1_class_counts_match_adr_036() -> None:
    """AC_1: 9 runnable, 10 proof_of_concept and 13 documented (ADR-036 section 4.1, I3)."""
    counts: dict[str, int] = {}
    for entry in _entries():
        counts[entry.example_class.value] = counts.get(entry.example_class.value, 0) + 1
    assert counts == {"runnable": 9, "proof_of_concept": 10, "documented": 13}


def test_ac1_mismatched_class_is_rejected() -> None:
    """AC_1: an entry whose class differs from the derived class raises, naming the id."""
    raw = _raw()
    raw[1]["example_class"] = "documented"  # #2 is implemented, so runnable
    with pytest.raises(ValueError, match=r"#2.*runnable"):
        validate_catalog(_entries(raw), _states())


def test_ac1_state_that_differs_from_the_ideation_row_is_rejected() -> None:
    """AC_1: the catalog state must equal the Ideation state for that id (interpretation I2)."""
    states = _states()
    states[2] = "candidate"
    with pytest.raises(ValueError, match=r"#2.*state"):
        validate_catalog(_entries(), states)


@pytest.mark.parametrize("field", ["reason", "reopening_condition"])
def test_ac2_documented_entry_needs_a_reason_and_a_reopening_condition(field: str) -> None:
    """AC_2: a documented entry with an empty reason or reopening condition raises."""
    raw = _raw()
    documented = next(e for e in raw if e["example_class"] == "documented")
    documented[field] = "   "
    with pytest.raises(ValueError, match=rf"#{documented['id']}.*{field}"):
        validate_catalog(_entries(raw), _states())


def test_ac2_runnable_entry_does_not_need_a_reason() -> None:
    """AC_2: the reason and reopening condition are required only for documented entries."""
    validate_catalog(_entries(), _states())


def test_ac3_path_outside_the_examples_directory_is_rejected() -> None:
    """AC_3: a path outside examples/methodologies/ raises."""
    raw = _raw()
    raw[1]["path"] = "src/agent_learning/02-reinforce-bandit"
    with pytest.raises(ValueError, match=r"#2.*examples/methodologies"):
        validate_catalog(_entries(raw), _states())


def test_ac3_path_traversal_is_rejected() -> None:
    """AC_3: a path that climbs out of examples/methodologies/ raises."""
    raw = _raw()
    raw[1]["path"] = "examples/methodologies/../../src"
    with pytest.raises(ValueError, match=r"#2.*examples/methodologies"):
        validate_catalog(_entries(raw), _states())


def test_ac3_documented_entry_has_no_path_and_others_do() -> None:
    """AC_3: documented entries carry no path; runnable and proof_of_concept entries do."""
    raw = _raw()
    for entry in _entries(raw):
        if entry.example_class is ExampleClass.DOCUMENTED:
            assert entry.path is None, entry.id
        else:
            assert entry.path, entry.id
    raw[2]["path"] = None
    with pytest.raises(ValueError, match=r"#3.*path"):
        validate_catalog(_entries(raw), _states())


def test_ac3_existing_paths_are_checked_when_given() -> None:
    """AC_3 (interpretation I1): with existing_paths, a listed path that is absent raises."""
    entries = _entries()
    present = {e.path for e in entries if e.path}
    validate_catalog(entries, _states(), existing_paths=present)
    present.discard("examples/methodologies/03-reasoned-resolution")
    with pytest.raises(ValueError, match=r"#3.*does not exist"):
        validate_catalog(entries, _states(), existing_paths=present)


def test_ac3_existence_check_is_skipped_without_existing_paths() -> None:
    """AC_3 (interpretation I1): None skips the check, because the example directories come later."""
    validate_catalog(_entries(), _states(), existing_paths=None)


def test_parse_catalog_rejects_unknown_fields_and_values() -> None:
    """Strict parsing, as ComplexityProfile.from_dict does: an unknown field or class raises."""
    raw = _raw()
    raw[0]["colour"] = "red"
    with pytest.raises(ValueError, match="unknown"):
        parse_catalog(raw)
    raw = _raw()
    raw[0]["example_class"] = "demo"
    with pytest.raises(ValueError, match="example_class"):
        parse_catalog(raw)


def test_ac4_module_imports_nothing_from_storage() -> None:
    """AC_4: methodology_catalog.py imports nothing from agent_learning.storage and does no file I/O."""
    source = (ROOT / "src" / "agent_learning" / "methodology_catalog.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")
    assert not any("storage" in name for name in imported), imported
    assert not any(name in {"os", "pathlib", "io", "shutil"} for name in imported), imported


def test_package_exports_the_public_names() -> None:
    """FDD-036 section 1.4: the public names are re-exported from agent_learning."""
    import agent_learning

    for name in ("CatalogEntry", "ExampleClass", "derive_class", "parse_catalog", "validate_catalog"):
        assert hasattr(agent_learning, name), name
