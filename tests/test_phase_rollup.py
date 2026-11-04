"""Contract tests for the Phase Carry-Over Backlog roll-up (scripts/phase_rollup.py).

Governing specifications:
- Intent: the Phase 1 roll-up must separate stories that were implemented from stories that were approved
  but not implemented (the carry-over backlog for the next phase), and must be generated from the story
  files and implementation-log.md so it cannot drift from them (maintainer request, 2026-11-04).
- Related: IMP-011 (flag stories whose status disagrees with the log), LL-041.

Acceptance Criteria:
- AC_0 (Four Groups): each story is exactly one of implemented, ready, draft, superseded.
- AC_1 (Implemented By Evidence): a story in the log, or marked Completed/Done, is implemented.
- AC_2 (Drift Reported): logged but not marked Completed/Done, and marked Completed/Done with no log entry,
  are each reported; neither changes the group.
- AC_3 (Dependencies Kept): a Ready story's dependency or blocker note is carried into its row.
- AC_4 (Deterministic): the same inputs give the same text (no timestamps).
- AC_5 (Nothing Dropped): on the committed stories, every `## Story` heading is parsed and the groups add up.
- AC_6 (Check Exit Code): `--check` exits 1 when drift exists and 0 when none.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import phase_rollup

FIX = Path(__file__).parent / "fixtures" / "phase_rollup"


@pytest.fixture
def rollup():
    assert (FIX / "stories").is_dir(), f"missing fixture directory: {FIX / 'stories'}"
    assert (FIX / "implementation-log.md").is_file(), "missing fixture implementation-log.md"
    return phase_rollup.build(FIX / "stories", FIX / "implementation-log.md")


def _group(rollup, sid: str) -> str:
    return next(s.group for s in rollup.stories if s.sid == sid)


def test_ac0_four_groups(rollup) -> None:
    groups = {s.group for s in rollup.stories}
    assert groups == {"implemented", "ready", "draft", "superseded"}
    assert len(rollup.stories) == 7


def test_ac1_implemented_by_evidence(rollup) -> None:
    assert _group(rollup, "90.1") == "implemented"  # log + Completed
    assert _group(rollup, "90.2") == "implemented"  # log, status still Ready
    assert _group(rollup, "90.3") == "implemented"  # Done, no log entry
    assert _group(rollup, "91.1") == "ready"
    assert _group(rollup, "91.3") == "draft"
    assert _group(rollup, "91.4") == "superseded"


def test_ac2_drift_reported(rollup) -> None:
    kinds = {(d.sid, d.kind) for d in rollup.drift}
    assert kinds == {("90.2", "logged_but_not_marked_complete"), ("90.3", "marked_complete_without_log")}


def test_ac3_dependencies_kept(rollup) -> None:
    note = next(s.note for s in rollup.stories if s.sid == "91.2")
    assert "depends on Story 91.1" in note
    assert "blocked on confirmation of D1" in next(s.note for s in rollup.stories if s.sid == "91.3")


def test_ac4_deterministic(rollup) -> None:
    assert phase_rollup.render_markdown(rollup) == phase_rollup.render_markdown(
        phase_rollup.build(FIX / "stories", FIX / "implementation-log.md")
    )
    text = phase_rollup.render_markdown(rollup)
    assert "Carry-Over" in text and "91.1" in text and "90.2" in text


def test_ac5_nothing_dropped_on_committed_stories() -> None:
    stories_dir = REPO / "docs" / "user-stories"
    assert stories_dir.is_dir(), f"missing {stories_dir}"
    roll = phase_rollup.build(stories_dir, REPO / "implementation-log.md")
    headings = sum(len(re.findall(r"^## Story \d+\.\d+", p.read_text(encoding="utf-8"), re.MULTILINE)) for p in stories_dir.glob("epic-*.md"))
    assert headings > 0
    assert len(roll.stories) == headings
    assert sum(roll.counts.values()) == headings


def test_ac6_check_exit_code(tmp_path: Path) -> None:
    script = REPO / "scripts" / "phase_rollup.py"
    drifted = subprocess.run(
        [sys.executable, str(script), "--stories", str(FIX / "stories"), "--log", str(FIX / "implementation-log.md"), "--check"],
        capture_output=True, text=True, check=False,
    )
    assert drifted.returncode == 1, drifted.stderr
    clean = tmp_path / "stories"
    clean.mkdir()
    (clean / "epic-1-x.md").write_text("# E\n\n## Story 1.1 — A\n**Status:** Completed (x)\n", encoding="utf-8")
    log = tmp_path / "log.md"
    log.write_text("## Story 1.1 — A\n", encoding="utf-8")
    ok = subprocess.run(
        [sys.executable, str(script), "--stories", str(clean), "--log", str(log), "--check"], capture_output=True, text=True, check=False
    )
    assert ok.returncode == 0, ok.stderr
