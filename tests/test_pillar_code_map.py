"""Pillar Code Map (draft): every mapped file exists and names an approved pillar.

Governance catch-up for the original microsoft/agent-learning code. See
docs/project-docs/Pillar-Code-Map.md and docs/project-docs/Project-Pillars.md.
This is a draft consistency check, not an approval gate.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAP = ROOT / "docs" / "project-docs" / "Pillar-Code-Map.md"
PILLARS = ROOT / "docs" / "project-docs" / "Project-Pillars.md"


def _rows() -> list[tuple[str, str]]:
    assert MAP.is_file(), f"missing pillar code map: {MAP}"
    rows = re.findall(r"^\| `([^`]+)` \| ([^|]+?) \|", MAP.read_text(encoding="utf-8"), re.MULTILINE)
    assert rows, "pillar code map has no rows"
    return rows


def test_every_mapped_file_exists() -> None:
    missing = [f for f, _ in _rows() if not (ROOT / f).is_file()]
    assert not missing, f"mapped files that no longer exist: {missing}"


def test_every_pillar_is_an_approved_pillar() -> None:
    names = set(re.findall(r"^### (.+)$", PILLARS.read_text(encoding="utf-8"), re.MULTILINE))
    unknown = sorted({p for _, p in _rows() if p not in names})
    assert not unknown, f"pillars not in Project-Pillars.md: {unknown}"


def test_no_file_is_mapped_twice() -> None:
    files = [f for f, _ in _rows()]
    assert len(files) == len(set(files)), "a file appears in the map more than once"
