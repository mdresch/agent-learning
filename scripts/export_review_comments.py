#!/usr/bin/env python3
"""Export PR review comments into committed fixtures (IMP-015, Story 14.5 AC_0).

For each PR in the triage replay dataset, writes every comment by the chosen
reviewers (Amazon Q by default; inline, review summary and issue comment) to
`tests/fixtures/critique_evidence/review_comments/pr-<N>.json`, sorted and
idempotent. `index.json` lists each finding id with an empty `comment_ids`,
which the human tagger fills: a finding id is the order the maintainer triaged
in, not a GitHub id, so a script cannot join them. A re-run never erases it.

Usage:
    uv run python scripts/export_review_comments.py
    uv run python scripts/export_review_comments.py --pr 195 --reviewer cursor
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPO = "mdresch/agent-learning"
FIXTURES = ROOT / "tests" / "fixtures" / "critique_evidence"
DATASET = FIXTURES / "triage_replay_dataset.json"
OUT_DIR = FIXTURES / "review_comments"
DEFAULT_REVIEWERS = ("amazon-q",)


class NotFound(RuntimeError):
    """The PR (or its comments) no longer exists on GitHub."""


Runner = Callable[[str], list[dict[str, Any]]]


def gh_api(path: str) -> list[dict[str, Any]]:
    """GET a paginated GitHub list endpoint through `gh api`; a 404 raises NotFound."""
    run = subprocess.run(
        ["gh", "api", "--paginate", "--slurp", path],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )
    if run.returncode != 0:
        if "404" in run.stderr or "Not Found" in run.stderr:
            raise NotFound(path)
        raise RuntimeError(f"gh api {path} failed: {run.stderr.strip()}")
    pages = json.loads(run.stdout)
    return [item for page in pages for item in (page if isinstance(page, list) else [page])]


def _login(item: dict[str, Any]) -> str:
    return (item.get("user") or {}).get("login", "unknown")


def _wanted(login: str, reviewers: Sequence[str]) -> bool:
    return any(r.lower() in login.lower() for r in reviewers)


def _record(kind: str, item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item["id"],
        "kind": kind,
        "author": _login(item),
        "created_at": item.get("created_at") or item.get("submitted_at"),
        "commit": item.get("commit_id"),
        "path": item.get("path"),
        "line": item.get("line"),
        "body": item.get("body") or "",
        "url": item.get("html_url"),
    }


def export_pr(pr: int, run: Runner, reviewers: Sequence[str] = DEFAULT_REVIEWERS) -> dict[str, Any]:
    """Collect the chosen reviewers' comments of one PR, or mark the PR unavailable."""
    base = f"repos/{REPO}"
    sources = (
        ("inline", f"{base}/pulls/{pr}/comments"),
        ("review", f"{base}/pulls/{pr}/reviews"),
        ("issue", f"{base}/issues/{pr}/comments"),
    )
    comments: list[dict[str, Any]] = []
    try:
        for kind, path in sources:
            comments += [_record(kind, i) for i in run(path) if _wanted(_login(i), reviewers)]
    except NotFound:
        return {"pr": pr, "available": False, "comments": []}
    comments.sort(key=lambda c: (c["created_at"] or "", c["kind"], c["id"]))
    return {"pr": pr, "available": True, "comments": comments}


def _dump(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def write_pr(out_dir: Path, record: dict[str, Any]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"pr-{record['pr']}.json"
    path.write_text(_dump(record), encoding="utf-8", newline="\n")
    return path


def write_index(out_dir: Path, findings: Sequence[dict[str, Any]]) -> Path:
    """List each finding with empty `comment_ids`; keep ids a human already filled."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "index.json"
    old: dict[str, Any] = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    index = {
        f["finding_id"]: {"pr": f["pr"], "comment_ids": old.get(f["finding_id"], {}).get("comment_ids", [])}
        for f in findings
    }
    path.write_text(_dump(index), encoding="utf-8", newline="\n")
    return path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pr", type=int, action="append", help="only this PR (repeatable)")
    parser.add_argument("--reviewer", action="append", default=[], help="add a reviewer (e.g. cursor)")
    args = parser.parse_args(argv)

    findings = json.loads(DATASET.read_text(encoding="utf-8"))["findings"]
    prs = args.pr or sorted({f["pr"] for f in findings})
    reviewers = (*DEFAULT_REVIEWERS, *args.reviewer)
    for pr in prs:
        record = export_pr(pr, gh_api, reviewers)
        write_pr(OUT_DIR, record)
        print(f"PR #{pr}: {len(record['comments'])} comments" + ("" if record["available"] else " (unavailable)"))
    write_index(OUT_DIR, findings)
    return 0


if __name__ == "__main__":
    sys.exit(main())
