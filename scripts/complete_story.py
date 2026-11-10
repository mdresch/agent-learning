#!/usr/bin/env python3
"""Automate the implement-story commit-and-log steps (Step 6 validate, Step 7 commit & log).

Replaces the manual two-commit routine, without amending (the log must cite a hash
that reaches ``main``):

    done     run contract tests + full suite, commit the implementation, append the
             ``implementation-log.md`` entry with that commit's hash, commit the entry
    triage   append Amazon Q triage lines (and review-fix commits) to a story's entry,
             commit the audit change

Usage:
    python scripts/complete_story.py worktree 20.3 [--dry-run]

    python scripts/complete_story.py done 20.3 \\
        --message "feat(warm-start): implement task-policy-warm-start (Story 20.3)" \\
        --note "Strict isolation: donor is never written" [--contract tests/test_x.py] [--dry-run]

    python scripts/complete_story.py triage 20.3 --round 1 --on 8bb9cc6 \\
        --finding "Q-83-1 | logic error | verified: yes | decision: accepted | <reason> | fix: 0820d05" \\
        --fix-commit 0820d05 --validation "7 passed; full suite 1,531 passed"

    python scripts/complete_story.py triage 20.3 --round 1 --on 8bb9cc6 --none [--verdict "no findings"]

Commits carry a ``Co-Authored-By`` trailer when ``--co-author "Name <email>"`` or the ``STORY_CO_AUTHOR`` variable is set.
"""

from __future__ import annotations

import argparse
import datetime
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "implementation-log.md"
STORY_DOCS = ROOT / "docs" / "user-stories"
STAGE_PATHS = ["src", "tests", ".claude/skills", "docs/user-stories"]
DEFAULT_IGNORES = ["tests/test_spark.py", "tests/pmbok"]  # optional deps, per LL-013


class Abort(Exception):
    """A gate failed; nothing further is done."""


def run(cmd: list[str], check: bool = True, capture: bool = True, cwd: Path | None = None) -> subprocess.CompletedProcess:
    proc = subprocess.run(cmd, cwd=cwd or ROOT, text=True, capture_output=capture, encoding="utf-8")
    if check and proc.returncode != 0:
        raise Abort(f"`{' '.join(cmd)}` failed:\n{proc.stdout}{proc.stderr}")
    return proc


def git(*args: str, check: bool = True) -> str:
    return run(["git", *args], check=check).stdout.strip()


def with_trailer(message: str, co_author: str | None) -> str:
    """Append a ``Co-Authored-By`` trailer once (IMP-001); no trailer when nobody is named."""
    if not co_author or f"Co-Authored-By: {co_author}" in message:
        return message
    return f"{message}\n\nCo-Authored-By: {co_author}"


def co_author_of(args: argparse.Namespace) -> str | None:
    return getattr(args, "co_author", None) or os.environ.get("STORY_CO_AUTHOR") or None


def cmd_worktree(args: argparse.Namespace) -> None:
    """Provision a story worktree: add it, sync every extra, drop the real azure-cosmos, check the import (LL-033)."""
    story = args.story
    branch = f"feat/story-{story}"
    path = ROOT.parent / f"{ROOT.name}-story-{story}"
    listed = [
        Path(ln[len("worktree ") :]).name
        for ln in git("worktree", "list", "--porcelain").splitlines()
        if ln.startswith("worktree ")
    ]
    if git("branch", "--list", branch) or path.name in listed:  # exact directory names: story 2.1 is not 2.10
        raise Abort(
            f"{branch} or {path.name} already exists: a run was already started (LL-042). Do not adopt it; inspect it read-only."
        )
    venv_python = path / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    steps = [
        (["git", "worktree", "add", str(path), "-b", branch, "main"], None),
        (["uv", "sync", "--all-extras"], path),
        (["uv", "pip", "uninstall", "--python", str(venv_python), "azure-cosmos"], path),
        ([str(venv_python), "-c", "import agent_learning"], path),
    ]
    if args.dry_run:
        print(f"[dry run] would provision {path} on {branch}:")
        for cmd, where in steps:
            print("  " + " ".join(cmd) + (f"   (in {where})" if where else ""))
        return
    for done, (cmd, where) in enumerate(steps):
        print("  " + " ".join(cmd))
        try:
            run(cmd, cwd=where)
        except Abort as exc:
            if done > 0:  # the worktree and branch exist only because this invocation just added them: take them back
                run(["git", "worktree", "remove", "--force", str(path)], check=False)
                run(["git", "branch", "-D", branch], check=False)
                raise Abort(f"{exc}\nRolled back {path.name} and {branch} so the command can be run again.") from exc
            raise
    print(f"Ready: {path} on {branch}. Read the RED before accepting it: it must name the symbol the story adds, not a missing package.")


def pytest_cmd() -> list[str]:
    return ["uv", "run", "pytest"] if shutil.which("uv") else [sys.executable, "-m", "pytest"]


def run_pytest(args: list[str]) -> str:
    """Run pytest streaming a short summary; return the final summary line."""
    proc = run([*pytest_cmd(), *args, "-q", "-p", "no:cacheprovider"], check=False)
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    summary = lines[-1] if lines else "no output"
    if proc.returncode != 0:
        raise Abort(f"pytest {' '.join(args)} failed:\n{proc.stdout[-3000:]}{proc.stderr[-1000:]}")
    return re.sub(r"^=+\s*|\s*=+$", "", summary)


def find_story(story: str) -> tuple[str, str]:
    """Return (title, 'ADR-nnn, BRD-nnn, FDD-nnn') for story id like '20.3'."""
    epic = story.split(".")[0]
    files = sorted(STORY_DOCS.glob(f"epic-{epic}-*.md"))
    if not files:
        raise Abort(f"No story file docs/user-stories/epic-{epic}-*.md")
    text = files[0].read_text(encoding="utf-8")
    m = re.search(rf"^## Story {re.escape(story)} — (.+)$", text, re.M)
    if not m:
        raise Abort(f"Story {story} not found in {files[0].name}")
    refs = []
    for kind in ("ADR", "BRD", "FDD"):
        found = re.search(rf"\b{kind}-\d+\b", text)
        if found:
            refs.append(found.group(0))
    return m.group(1).strip(), ", ".join(refs)


def read_log() -> tuple[str, str]:
    raw = LOG.read_bytes().decode("utf-8")
    nl = "\r\n" if "\r\n" in raw else "\n"
    return raw.replace("\r\n", "\n"), nl


def write_log(text: str, nl: str) -> None:
    LOG.write_bytes(text.replace("\n", nl).encode("utf-8"))


def changed_paths() -> list[str]:
    out = git("status", "--porcelain", "-uall")
    return [ln[3:].strip().strip('"') for ln in out.splitlines() if ln.strip()]


def current_branch() -> str:
    branch = git("branch", "--show-current")
    if branch in ("main", "master", ""):
        raise Abort(f"Refusing to commit on '{branch or 'detached HEAD'}'; use feat/story-<X.Y>.")
    return branch


def cmd_done(args: argparse.Namespace) -> None:
    story = args.story
    branch = current_branch()
    title, refs = find_story(story)
    if re.search(rf"^## Story {re.escape(story)} ", read_log()[0], re.M):
        raise Abort(f"implementation-log.md already has an entry for Story {story}.")

    paths = changed_paths()
    contracts = args.contract or sorted(
        {p for p in paths if re.fullmatch(r"tests/test_[\w]+\.py", p)}
    )
    if not contracts:
        raise Abort("No contract test found (no changed tests/test_*.py). Pass --contract.")

    print(f"Story {story} — {title}\nBranch: {branch}\nContracts: {', '.join(contracts)}")
    contract_summary = run_pytest(contracts)
    print(f"  contract: {contract_summary}")
    ignores = DEFAULT_IGNORES + (args.ignore or [])
    full_summary = run_pytest([f"--ignore={p}" for p in ignores])
    print(f"  full suite: {full_summary}")

    if args.dry_run:
        print("[dry run] gates passed; nothing committed.")
        return

    stage = [p for p in STAGE_PATHS if (ROOT / p).exists()]
    git("add", "-A", "--", *stage)
    if not git("diff", "--cached", "--name-only"):
        raise Abort("Nothing staged under " + ", ".join(stage))
    co_author = co_author_of(args)
    git("commit", "-m", with_trailer(args.message, co_author))
    impl = git("rev-parse", "--short", "HEAD")
    files = git("show", "--name-only", "--format=", impl).splitlines()

    entry = [
        f"## Story {story} — {title}",
        f"- **Commit:** `{impl}`",
        f"- **Date:** {datetime.date.today().isoformat()}",
        f"- **Branch:** `{branch}`",
        f"- **Source ADR / BRD / FDD:** {refs}",
        "- **Files Modified/Created:**",
        *[f"  - `{f}`" for f in files],
        "- **Contracts:**",
        *[f"  - `{c}`" for c in contracts],
        f"  - Contract run: {contract_summary}",
        f"  - Full suite: {full_summary} (excluding {', '.join(f'`{p}`' for p in ignores)}, per LL-013)",
    ]
    if args.note:
        entry += ["- **Notes:**", *[f"  - {n}" for n in args.note]]

    text, nl = read_log()
    write_log(text.rstrip("\n") + "\n\n" + "\n".join(entry) + "\n", nl)
    git("add", "implementation-log.md")
    git("commit", "-m", with_trailer(f"docs(audit): record implementation of Story {story} (commit {impl})", co_author))
    print(f"Done: implementation {impl}, audit {git('rev-parse', '--short', 'HEAD')}. Ready to push and open the PR.")


def cmd_triage(args: argparse.Namespace) -> None:
    story = args.story
    text, nl = read_log()
    m = re.search(rf"^## Story {re.escape(story)} .*$", text, re.M)
    if not m:
        raise Abort(f"No log entry for Story {story}; run `done` first.")
    end = re.search(r"^## ", text[m.end():], re.M)
    end_idx = m.end() + end.start() if end else len(text)
    block = text[m.start():end_idx].rstrip("\n")

    if args.none and args.finding:
        raise Abort("Pass --finding or --none, not both.")
    if not args.none and not args.finding:
        raise Abort("Pass --finding or --none.")

    add: list[str] = []
    if args.fix_commit:
        add.append(f"- **Review-fix commits:** `{args.fix_commit}`")
    if args.validation:
        add.append(f"- **Review validation:** {args.validation}")
    if args.none:
        # LL-034: a review with no findings is one prose bullet, never a Q-<PR>-<n> line (the claim types are fixed)
        verdict = args.verdict or "no findings"
        add.append(f"- **Amazon Q review (round {args.round} on `{args.on}`):** {verdict}.")
    else:
        add.append(f"- **Amazon Q triage (round {args.round} on `{args.on}`):**")
        add += [f"  - `{f}`" for f in args.finding]

    if args.dry_run:
        print("\n".join(add))
        return
    new_text = text[:m.start()] + block + "\n" + "\n".join(add) + "\n" + (
        "\n" + text[end_idx:] if end else ""
    )
    write_log(new_text, nl)
    git("add", "implementation-log.md")
    git("commit", "-m", with_trailer(f"docs(audit): record Amazon Q round {args.round} triage for Story {story}", co_author_of(args)))
    print(f"Recorded round {args.round} for Story {story}: {git('rev-parse', '--short', 'HEAD')}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("done", help="verify, commit implementation, log it")
    d.add_argument("story", help="story id, e.g. 20.3")
    d.add_argument("-m", "--message", required=True, help="implementation commit message")
    d.add_argument("--contract", action="append", help="contract test file (default: changed tests/test_*.py)")
    d.add_argument("--ignore", action="append", help="extra path to exclude from the full suite")
    d.add_argument("--note", action="append", help="note line for the log entry (repeatable)")
    d.add_argument("--co-author", help="'Name <email>' for a Co-Authored-By trailer (default: $STORY_CO_AUTHOR)")
    d.add_argument("--dry-run", action="store_true")
    d.set_defaults(fn=cmd_done)

    w = sub.add_parser("worktree", help="provision the story worktree (LL-033)")
    w.add_argument("story", help="story id, e.g. 20.3")
    w.add_argument("--dry-run", action="store_true")
    w.set_defaults(fn=cmd_worktree)

    t = sub.add_parser("triage", help="append Amazon Q triage to a story's log entry")
    t.add_argument("story")
    t.add_argument("--round", type=int, required=True)
    t.add_argument("--on", required=True, help="commit the review was on")
    t.add_argument("--finding", action="append",
                   help="'Q-<PR>-<n> | <claim type> | verified: ... | decision: ... | <reason> | fix: ...'")
    t.add_argument("--none", action="store_true", help="the review had no findings: log one prose bullet (LL-034)")
    t.add_argument("--verdict", help="with --none: the reviewer's verdict in a few words (default: no findings)")
    t.add_argument("--co-author", help="'Name <email>' for a Co-Authored-By trailer (default: $STORY_CO_AUTHOR)")
    t.add_argument("--fix-commit")
    t.add_argument("--validation")
    t.add_argument("--dry-run", action="store_true")
    t.set_defaults(fn=cmd_triage)

    args = ap.parse_args()
    try:
        args.fn(args)
    except Abort as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
