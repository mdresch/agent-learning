"""IMP-015: review comments are exported per PR into committed fixtures (Story 14.5 AC_0)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import scripts.export_review_comments as exp

FIXTURES = Path(__file__).parent / "fixtures" / "critique_evidence"
DATASET = FIXTURES / "triage_replay_dataset.json"
OUT = FIXTURES / "review_comments"

Q = {"login": "amazon-q-developer[bot]"}
CURSOR = {"login": "cursor[bot]"}
HUMAN = {"login": "mdresch"}


def _fake_gh(responses: dict[str, object]):
    """Return a runner that answers `gh api <path>` from a dict; a missing path is a 404."""

    calls: list[str] = []

    def run(path: str) -> list[dict]:
        calls.append(path)
        if path not in responses:
            raise exp.NotFound(path)
        return responses[path]  # type: ignore[return-value]

    run.calls = calls  # type: ignore[attr-defined]
    return run


def _pr_responses(n: int) -> dict[str, object]:
    base = "repos/mdresch/agent-learning"
    return {
        f"{base}/pulls/{n}/comments": [
            {"id": 22, "user": Q, "created_at": "2026-01-02T00:00:00Z", "commit_id": "abc", "path": "a.py",
             "line": 7, "body": "inline B", "html_url": "u22"},
            {"id": 11, "user": Q, "created_at": "2026-01-01T00:00:00Z", "commit_id": "abc", "path": "a.py",
             "line": 3, "body": "inline A", "html_url": "u11"},
            {"id": 33, "user": CURSOR, "created_at": "2026-01-03T00:00:00Z", "commit_id": "abc", "path": "b.py",
             "line": 1, "body": "cursor", "html_url": "u33"},
        ],
        f"{base}/pulls/{n}/reviews": [
            {"id": 44, "user": Q, "submitted_at": "2026-01-01T12:00:00Z", "commit_id": "abc", "body": "summary",
             "html_url": "u44"},
            {"id": 45, "user": HUMAN, "submitted_at": "2026-01-01T13:00:00Z", "commit_id": "abc", "body": "human",
             "html_url": "u45"},
        ],
        f"{base}/issues/{n}/comments": [
            {"id": 55, "user": Q, "created_at": "2026-01-04T00:00:00Z", "body": "issue comment", "html_url": "u55"},
        ],
    }


def test_exports_every_amazon_q_comment_of_all_three_kinds_sorted() -> None:
    record = exp.export_pr(9, _fake_gh(_pr_responses(9)))
    assert record["pr"] == 9 and record["available"] is True
    assert [(c["kind"], c["id"]) for c in record["comments"]] == [
        ("inline", 11), ("review", 44), ("inline", 22), ("issue", 55)
    ]
    first = record["comments"][0]
    assert set(first) == {"id", "kind", "author", "created_at", "commit", "path", "line", "body", "url"}
    assert first["body"] == "inline A" and first["path"] == "a.py" and first["line"] == 3


def test_reviewer_option_adds_cursor_and_never_the_human() -> None:
    record = exp.export_pr(9, _fake_gh(_pr_responses(9)), reviewers=("amazon-q", "cursor"))
    assert 33 in {c["id"] for c in record["comments"]}
    assert 45 not in {c["id"] for c in record["comments"]}


def test_a_pr_that_no_longer_exists_is_recorded_as_unavailable() -> None:
    record = exp.export_pr(404, _fake_gh({}))
    assert record == {"pr": 404, "available": False, "comments": []}


def test_other_gh_failures_are_not_swallowed() -> None:
    def broken(path: str) -> list[dict]:
        raise RuntimeError("gh exploded")

    with pytest.raises(RuntimeError, match="exploded"):
        exp.export_pr(9, broken)


def test_write_is_idempotent_and_ends_with_a_newline(tmp_path: Path) -> None:
    record = exp.export_pr(9, _fake_gh(_pr_responses(9)))
    path = exp.write_pr(tmp_path, record)
    first = path.read_bytes()
    exp.write_pr(tmp_path, exp.export_pr(9, _fake_gh(_pr_responses(9))))
    assert path.read_bytes() == first and first.endswith(b"\n")
    assert path.name == "pr-9.json"


def test_index_lists_each_finding_with_empty_comment_ids_and_keeps_filled_ones(tmp_path: Path) -> None:
    findings = [{"finding_id": "Q-9-1", "pr": 9}, {"finding_id": "Q-9-2", "pr": 9}]
    exp.write_index(tmp_path, findings)
    index = json.loads((tmp_path / "index.json").read_text(encoding="utf-8"))
    assert index == {"Q-9-1": {"pr": 9, "comment_ids": []}, "Q-9-2": {"pr": 9, "comment_ids": []}}
    index["Q-9-1"]["comment_ids"] = [11]
    (tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")
    exp.write_index(tmp_path, findings)  # a re-run must not erase the tagger's work
    again = json.loads((tmp_path / "index.json").read_text(encoding="utf-8"))
    assert again["Q-9-1"]["comment_ids"] == [11]


def test_every_pr_with_a_triage_line_has_a_committed_fixture() -> None:
    prs = {f["pr"] for f in json.loads(DATASET.read_text(encoding="utf-8"))["findings"]}
    missing = sorted(p for p in prs if not (OUT / f"pr-{p}.json").exists())
    assert not missing, f"run scripts/export_review_comments.py; no fixture for PRs {missing}"
    index = json.loads((OUT / "index.json").read_text(encoding="utf-8"))
    ids = {f["finding_id"] for f in json.loads(DATASET.read_text(encoding="utf-8"))["findings"]}
    assert set(index) == ids
