"""Contract tests for the proof-of-concept methodology sketches.

Story 36.3 (docs/user-stories/epic-36-learning-methodology-examples-ledger-and-review-triage-loop.md)
ADR-036 section 4.2 and Invariants 1 and 3 (docs/adr/ADR-036-...)
BRD-036 BRU-036-02 and BRU-036-03 (sketches: ADR-036 section 4.2, CODE: sketch), FDD-036 sections 1 and 3 (item 6)

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

# Methodology id -> directory, for the ten proof-of-concept entries (ADR-036 section 4.1).
RUNNABLE = {
    8: "08-critique-to-evidence",
    9: "09-thompson-sampling",
    10: "10-ucb",
    11: "11-epsilon-greedy",
    13: "13-pairwise-preference",
    14: "14-meta-learning",
    15: "15-warm-start",
    17: "17-authority-routing",
    22: "22-scored-search",
    23: "23-dueling-bandit",
}
RUN_TIMEOUT_SECONDS = 60  # each sketch takes about two seconds
FORBIDDEN_NAMES = {"LocalFileStore", "CosmosStore", "get_default_store"}
FORBIDDEN_IMPORTS = {"requests", "urllib", "http", "socket", "azure", "aiohttp", "httpx"}


def _script(methodology_id: int) -> Path:
    return EXAMPLES / RUNNABLE[methodology_id] / "sketch.py"


def _parse(path: Path) -> ast.Module:
    """Parse a source file, failing the test with the path and error if it is not valid Python."""
    try:
        return ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        pytest.fail(f"cannot parse {path}: {exc}")


def _docstring(path: Path) -> str:
    return ast.get_docstring(_parse(path)) or ""


def _catalog() -> dict[int, dict]:
    return {entry["id"]: entry for entry in json.loads(CATALOG.read_text(encoding="utf-8"))}


@pytest.mark.parametrize("methodology_id", sorted(RUNNABLE))
def test_ac0_each_poc_methodology_has_a_readme_and_a_script(methodology_id: int) -> None:
    """AC_0: the directory exists with README.md and sketch.py, and the catalog calls it proof_of_concept."""
    entry = _catalog()[methodology_id]
    assert entry["example_class"] == "proof_of_concept"
    assert entry["path"] == f"examples/methodologies/{RUNNABLE[methodology_id]}"
    directory = ROOT / entry["path"]
    assert (directory / "README.md").is_file()
    assert (directory / "sketch.py").is_file()


def test_ac0_the_ten_proof_of_concept_entries_are_exactly_these_ids() -> None:
    """AC_0: no proof_of_concept catalog entry lacks a sketch, and no sketch lacks an entry."""
    poc_ids = {i for i, e in _catalog().items() if e["example_class"] == "proof_of_concept"}
    assert poc_ids == set(RUNNABLE)


@pytest.mark.parametrize("methodology_id", sorted(RUNNABLE))
def test_ac1_header_carries_the_labeling_lines(methodology_id: int) -> None:
    """AC_1: STATUS, CODE, DATA: SYNTHETIC, the Ideation row and NOT EVIDENCE are in the header."""
    header = _docstring(_script(methodology_id))
    assert re.search(r"^STATUS: proof_of_concept$", header, re.MULTILINE), header
    assert re.search(r"^CODE: sketch$", header, re.MULTILINE), header
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
def test_ac2_sketch_runs_offline_and_exits_zero(methodology_id: int, tmp_path: Path) -> None:
    """AC_2 (interpretation I1): the script exits 0 in an empty temporary directory within the limit."""
    result = subprocess.run(
        [sys.executable, str(_script(methodology_id))],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=RUN_TIMEOUT_SECONDS,
        check=False,
    )
    assert result.returncode == 0, result.stderr[-1500:]
    assert "SYNTHETIC" in result.stdout
    assert "NOT EVIDENCE" in result.stdout
    assert list(tmp_path.iterdir()) == [], "the run must not write files"


@pytest.mark.parametrize("methodology_id", sorted(RUNNABLE))
def test_ac3_sketch_uses_no_real_store_and_no_network(methodology_id: int) -> None:
    """AC_3 (interpretation I2): the script names no durable store and imports no network or cloud client."""
    tree = _parse(_script(methodology_id))
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
        tree = _parse(path)
        for node in ast.walk(tree):
            modules = []
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                modules = [node.module or ""]
            if any(m.split(".")[0] == "examples" for m in modules):
                offenders.append(str(path))
    assert offenders == []


def test_ac3_running_the_sketches_leaves_the_catalog_unchanged(tmp_path: Path) -> None:
    """AC_3 (ADR-036 Invariant 1): running every sketch does not change the catalog file."""
    before = hashlib.sha256(CATALOG.read_bytes()).hexdigest()
    for methodology_id in sorted(RUNNABLE):
        proc = subprocess.run(
            [sys.executable, str(_script(methodology_id))],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=RUN_TIMEOUT_SECONDS,
            check=False,
        )
        assert proc.returncode == 0, f"#{methodology_id}: {proc.stderr[-1500:]}"
    assert hashlib.sha256(CATALOG.read_bytes()).hexdigest() == before
