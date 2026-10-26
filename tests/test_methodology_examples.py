"""Contract tests for the runnable methodology examples.

Story 36.2 (docs/user-stories/epic-36-learning-methodology-examples-ledger-and-review-triage-loop.md)
ADR-036 section 4.2 and Invariants 1 and 3 (docs/adr/ADR-036-...)
BRD-036 BRU-036-02 and BRU-036-03, FDD-036 sections 1 and 3 (item 6)

Interpretations not stated verbatim in the acceptance criteria (LL-011):
- I1: "runs offline" is tested by running each script as a subprocess with an empty temporary
  working directory and a time limit; the test cannot prove the absence of network access, so
  each script is also scanned for network and cloud imports.
- I2: "leaves the real store unchanged" is tested statically (no LocalFileStore, CosmosStore or
  get_default_store in the script) plus a check that the run created nothing in its working
  directory; the scripts use InMemoryStore only.
- I3: every script's header carries the labeling lines of ADR-036 section 4.2; the falsification
  criterion and the real data needed are tested in the README, where the ADR places them.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples" / "methodologies"
CATALOG = EXAMPLES / "catalog.json"

# Methodology id -> directory, for the nine runnable entries (ADR-036 section 4.1).
RUNNABLE = {
    2: "02-reinforce-bandit",
    3: "03-reasoned-resolution",
    4: "04-contextual-bandit",
    5: "05-reward-shaping",
    6: "06-human-override",
    12: "12-active-evidence-seeking",
    19: "19-red-team-validation",
    20: "20-diff-classification",
    21: "21-category-escalation",
}
FORBIDDEN_NAMES = {"LocalFileStore", "CosmosStore", "get_default_store"}
FORBIDDEN_IMPORTS = {"requests", "urllib", "http", "socket", "azure", "aiohttp", "httpx"}


def _script(methodology_id: int) -> Path:
    return EXAMPLES / RUNNABLE[methodology_id] / "example.py"


def _docstring(path: Path) -> str:
    return ast.get_docstring(ast.parse(path.read_text(encoding="utf-8"))) or ""


def _catalog() -> dict[int, dict]:
    return {entry["id"]: entry for entry in json.loads(CATALOG.read_text(encoding="utf-8"))}


@pytest.mark.parametrize("methodology_id", sorted(RUNNABLE))
def test_ac0_each_runnable_methodology_has_a_readme_and_a_script(methodology_id: int) -> None:
    """AC_0: the directory exists with README.md and example.py, and the catalog calls it runnable."""
    entry = _catalog()[methodology_id]
    assert entry["example_class"] == "runnable"
    assert entry["path"] == f"examples/methodologies/{RUNNABLE[methodology_id]}"
    directory = ROOT / entry["path"]
    assert (directory / "README.md").is_file()
    assert (directory / "example.py").is_file()


def test_ac0_the_nine_runnable_entries_are_exactly_these_ids() -> None:
    """AC_0: no runnable catalog entry lacks an example, and no example lacks a runnable entry."""
    runnable_ids = {i for i, e in _catalog().items() if e["example_class"] == "runnable"}
    assert runnable_ids == set(RUNNABLE)


@pytest.mark.parametrize("methodology_id", sorted(RUNNABLE))
def test_ac1_header_carries_the_labeling_lines(methodology_id: int) -> None:
    """AC_1: STATUS, CODE, DATA: SYNTHETIC, the Ideation row and NOT EVIDENCE are in the header."""
    header = _docstring(_script(methodology_id))
    assert re.search(r"^STATUS: runnable$", header, re.MULTILINE), header
    assert re.search(r"^CODE: sdk$", header, re.MULTILINE), header
    assert re.search(r"^DATA: SYNTHETIC$", header, re.MULTILINE), header
    assert re.search(rf"^IDEATION ROW: #{methodology_id}\b", header, re.MULTILINE), header
    assert re.search(r"^ADR: \S+", header, re.MULTILINE), header
    assert re.search(r"^HYPOTHESIS: \S+", header, re.MULTILINE), header
    assert re.search(r"^NOT EVIDENCE: this run does not validate or invalidate the methodology", header, re.MULTILINE), header


@pytest.mark.parametrize("methodology_id", sorted(RUNNABLE))
def test_ac1_readme_states_the_falsification_criterion_and_the_data_needed(methodology_id: int) -> None:
    """AC_1 (interpretation I3): the README names the falsification criterion and the real data needed."""
    readme = (EXAMPLES / RUNNABLE[methodology_id] / "README.md").read_text(encoding="utf-8")
    assert re.search(r"^#+ Falsification", readme, re.MULTILINE), readme[:200]
    assert re.search(r"^#+ Real data needed", readme, re.MULTILINE), readme[:200]
    assert "SYNTHETIC" in readme


@pytest.mark.parametrize("methodology_id", sorted(RUNNABLE))
def test_ac2_example_runs_offline_and_exits_zero(methodology_id: int, tmp_path: Path) -> None:
    """AC_2 (interpretation I1): the script exits 0 in an empty temporary directory within the limit."""
    result = subprocess.run(
        [sys.executable, str(_script(methodology_id))],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stderr[-1500:]
    assert "SYNTHETIC" in result.stdout
    assert "NOT EVIDENCE" in result.stdout
    assert list(tmp_path.iterdir()) == [], "the run must not write files"


@pytest.mark.parametrize("methodology_id", sorted(RUNNABLE))
def test_ac3_example_uses_no_real_store_and_no_network(methodology_id: int) -> None:
    """AC_3 (interpretation I2): the script names no durable store and imports no network or cloud client."""
    tree = ast.parse(_script(methodology_id).read_text(encoding="utf-8"))
    names: set[str] = set()
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add((node.module or "").split(".")[0])
            names.update(alias.name for alias in node.names)
    assert not (names & FORBIDDEN_NAMES), names & FORBIDDEN_NAMES
    assert not (imports & FORBIDDEN_IMPORTS), imports & FORBIDDEN_IMPORTS


def test_ac3_nothing_under_src_imports_from_examples() -> None:
    """AC_3 (ADR-036 Invariant 3): no module under src/ imports from examples/."""
    offenders = []
    for path in (ROOT / "src").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            modules = []
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                modules = [node.module or ""]
            if any(m.split(".")[0] == "examples" for m in modules):
                offenders.append(str(path))
    assert offenders == []


def test_ac3_running_the_examples_leaves_the_catalog_unchanged(tmp_path: Path) -> None:
    """AC_3 (ADR-036 Invariant 1): running every example does not change the catalog file."""
    before = hashlib.sha256(CATALOG.read_bytes()).hexdigest()
    for methodology_id in sorted(RUNNABLE):
        subprocess.run(
            [sys.executable, str(_script(methodology_id))],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=120,
            check=True,
        )
    assert hashlib.sha256(CATALOG.read_bytes()).hexdigest() == before
