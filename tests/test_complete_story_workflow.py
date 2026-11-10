"""IMP-001 and IMP-043: complete_story.py provisions a worktree, logs a no-finding review, and signs its commits;
the append-only implementation log merges without conflicts at its tail."""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("complete_story", ROOT / "scripts" / "complete_story.py")
assert SPEC is not None and SPEC.loader is not None
cs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cs)


class Recorder:
    """Stands in for ``cs.run``: records commands and answers the git queries."""

    def __init__(self, branches: str = "", worktrees: str = "") -> None:
        self.calls: list[list[str]] = []
        self.branches, self.worktrees = branches, worktrees

    def __call__(self, cmd, check=True, capture=True, cwd=None):
        self.calls.append(list(cmd))
        out = ""
        if cmd[:3] == ["git", "branch", "--list"]:
            out = self.branches
        elif cmd[:3] == ["git", "worktree", "list"]:
            out = self.worktrees
        return subprocess.CompletedProcess(cmd, 0, stdout=out, stderr="")


def _args(**kw):
    return type("Args", (), kw)()


# --- IMP-001: worktree -----------------------------------------------------------------------------------------


def test_worktree_adds_syncs_removes_cosmos_and_checks_the_import(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    rec = Recorder()
    monkeypatch.setattr(cs, "run", rec)
    monkeypatch.setattr(cs, "ROOT", tmp_path / "agent-learning")
    cs.cmd_worktree(_args(story="20.3", dry_run=False))
    joined = [" ".join(c) for c in rec.calls]
    assert any(c.startswith("git worktree add") and "feat/story-20.3" in c and c.endswith("main") for c in joined)
    sync = next(i for i, c in enumerate(joined) if "uv sync --all-extras" in c)
    uninstall = next(i for i, c in enumerate(joined) if "uv pip uninstall" in c and "azure-cosmos" in c)
    check = next(i for i, c in enumerate(joined) if "import agent_learning" in c)
    assert sync < uninstall < check


def test_worktree_refuses_when_the_branch_or_worktree_already_exists(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """LL-042: an existing branch or worktree means a run was already started; do not adopt it."""
    monkeypatch.setattr(cs, "ROOT", tmp_path / "agent-learning")
    monkeypatch.setattr(cs, "run", Recorder(branches="  feat/story-20.3\n"))
    with pytest.raises(cs.Abort, match="already"):
        cs.cmd_worktree(_args(story="20.3", dry_run=False))
    rec = Recorder(worktrees="worktree C:/x/agent-learning-story-20.3\nHEAD abc\nbranch refs/heads/feat/story-20.3\n")
    monkeypatch.setattr(cs, "run", rec)
    with pytest.raises(cs.Abort, match="already"):
        cs.cmd_worktree(_args(story="20.3", dry_run=False))
    assert not any(c[:3] == ["git", "worktree", "add"] for c in rec.calls)


def test_a_longer_story_id_does_not_make_a_shorter_one_look_started(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Story 2.1 is not started because a worktree for 2.10 exists."""
    monkeypatch.setattr(cs, "ROOT", tmp_path / "agent-learning")
    rec = Recorder(worktrees="worktree C:/x/agent-learning-story-2.10\nHEAD abc\nbranch refs/heads/feat/story-2.10\n")
    monkeypatch.setattr(cs, "run", rec)
    cs.cmd_worktree(_args(story="2.1", dry_run=False))
    assert any(c[:3] == ["git", "worktree", "add"] for c in rec.calls)


def test_a_failed_provision_is_rolled_back_so_it_can_be_run_again(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(cs, "ROOT", tmp_path / "agent-learning")

    class FailingSync(Recorder):
        def __call__(self, cmd, check=True, capture=True, cwd=None):
            super().__call__(cmd, check, capture, cwd)
            if cmd[:2] == ["uv", "sync"]:
                raise cs.Abort("uv sync failed")
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    rec = FailingSync()
    monkeypatch.setattr(cs, "run", rec)
    with pytest.raises(cs.Abort, match="Rolled back"):
        cs.cmd_worktree(_args(story="20.3", dry_run=False))
    assert any(c[:4] == ["git", "worktree", "remove", "--force"] for c in rec.calls)
    assert ["git", "branch", "-D", "feat/story-20.3"] in rec.calls


def test_worktree_dry_run_changes_nothing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rec = Recorder()
    monkeypatch.setattr(cs, "run", rec)
    monkeypatch.setattr(cs, "ROOT", tmp_path / "agent-learning")
    cs.cmd_worktree(_args(story="20.3", dry_run=True))
    assert not any(c[:3] == ["git", "worktree", "add"] for c in rec.calls)
    assert "feat/story-20.3" in capsys.readouterr().out


# --- IMP-001: triage --none ------------------------------------------------------------------------------------


LOG = "# Log\n\n## Story 20.3 — Warm start\n- **Commit:** `abc1234`\n\n## Story 20.4 — Next\n- **Commit:** `def5678`\n"


def _triage_args(**kw):
    base = dict(story="20.3", round=1, on="abc1234", finding=None, none=True, verdict=None, fix_commit=None,
                validation=None, dry_run=False, co_author=None)
    base.update(kw)
    return _args(**base)


def test_triage_none_writes_one_prose_bullet_that_is_not_a_triage_line(monkeypatch: pytest.MonkeyPatch) -> None:
    from agent_learning.review_triage import find_triage_lines

    written: dict[str, str] = {}
    monkeypatch.setattr(cs, "read_log", lambda: (LOG, "\n"))
    monkeypatch.setattr(cs, "write_log", lambda text, nl: written.update(text=text))
    monkeypatch.setattr(cs, "git", lambda *a, check=True: "")
    cs.cmd_triage(_triage_args(verdict="no findings"))
    text = written["text"]
    entry = text.split("## Story 20.3", 1)[1].split("## Story 20.4", 1)[0]
    assert "round 1" in entry and "`abc1234`" in entry and "no findings" in entry
    assert find_triage_lines(text) == []  # LL-034: tests/test_review_triage.py parses every such line
    assert "## Story 20.4" in text


def test_triage_needs_findings_or_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cs, "read_log", lambda: (LOG, "\n"))
    with pytest.raises(cs.Abort, match="--finding or --none"):
        cs.cmd_triage(_triage_args(none=False))
    line = "Q-1-1 | style | verified: yes | decision: accepted | r | fix: none"
    with pytest.raises(cs.Abort, match="not both"):
        cs.cmd_triage(_triage_args(finding=[line]))


# --- IMP-001: trailer ------------------------------------------------------------------------------------------


def test_commit_message_gets_the_co_author_trailer_once() -> None:
    who = "Claude <noreply@anthropic.com>"
    assert cs.with_trailer("feat: x", who) == f"feat: x\n\nCo-Authored-By: {who}"
    assert cs.with_trailer(f"feat: x\n\nCo-Authored-By: {who}", who).count("Co-Authored-By") == 1
    assert cs.with_trailer("feat: x", None) == "feat: x"


# --- IMP-043: union merge --------------------------------------------------------------------------------------


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8", check=True
    ).stdout


def _merge_repo(tmp_path: Path, attributes: str) -> Path:
    repo = tmp_path / "r"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "t")
    _git(repo, "config", "core.autocrlf", "false")
    (repo / ".gitattributes").write_text(attributes, encoding="utf-8")
    (repo / "implementation-log.md").write_text("# Log\n\n## Story 1.1 — a\n- one\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    return repo


def _branch_append(repo: Path, name: str, text: str) -> None:
    _git(repo, "checkout", "-q", "-b", name, "main")
    with (repo / "implementation-log.md").open("a", encoding="utf-8") as fh:
        fh.write(text)
    _git(repo, "commit", "-q", "-am", name)


def test_the_repository_declares_union_merge_for_the_log() -> None:
    attrs = (ROOT / ".gitattributes").read_text(encoding="utf-8").splitlines()
    assert any(line.split() == ["implementation-log.md", "merge=union"] for line in attrs)


def test_two_stories_appending_at_the_tail_merge_without_a_conflict(tmp_path: Path) -> None:
    repo = _merge_repo(tmp_path, (ROOT / ".gitattributes").read_text(encoding="utf-8"))
    _branch_append(repo, "a", "\n## Story 2.1 — b\n- two\n")
    _branch_append(repo, "b", "\n## Story 3.1 — c\n- three\n")
    _git(repo, "checkout", "-q", "a")
    _git(repo, "merge", "-q", "--no-edit", "b")
    merged = (repo / "implementation-log.md").read_text(encoding="utf-8")
    assert merged.count("## Story 2.1") == 1 and merged.count("## Story 3.1") == 1


def test_without_the_attribute_the_same_merge_conflicts(tmp_path: Path) -> None:
    repo = _merge_repo(tmp_path, "")
    _branch_append(repo, "a", "\n## Story 2.1 — b\n- two\n")
    _branch_append(repo, "b", "\n## Story 3.1 — c\n- three\n")
    _git(repo, "checkout", "-q", "a")
    res = subprocess.run(["git", "-C", str(repo), "merge", "-q", "--no-edit", "b"], capture_output=True, text=True)
    assert res.returncode != 0


def test_a_contested_edit_to_an_older_entry_keeps_both_sides_instead_of_conflicting(tmp_path: Path) -> None:
    """Union merge never reports a conflict: both edits of one line survive, visible in review but not flagged.
    That is the cost of IMP-043, accepted and documented; a duplicated heading is caught by the test below."""
    repo = _merge_repo(tmp_path, (ROOT / ".gitattributes").read_text(encoding="utf-8"))
    for name, word in (("a", "alpha"), ("b", "beta")):
        _git(repo, "checkout", "-q", "-b", name, "main")
        (repo / "implementation-log.md").write_text(f"# Log\n\n## Story 1.1 — a\n- {word}\n", encoding="utf-8")
        _git(repo, "commit", "-q", "-am", name)
    _git(repo, "checkout", "-q", "a")
    _git(repo, "merge", "-q", "--no-edit", "b")
    merged = (repo / "implementation-log.md").read_text(encoding="utf-8")
    assert "- alpha" in merged and "- beta" in merged


def test_every_story_heading_in_the_real_log_is_unique() -> None:
    lines = (ROOT / "implementation-log.md").read_text(encoding="utf-8").splitlines()
    headings = [ln for ln in lines if ln.startswith("## Story ")]
    assert len(headings) == len(set(headings))
