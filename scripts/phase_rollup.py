"""Phase carry-over roll-up: which approved stories were implemented and which were not.

Generated from the story files (docs/user-stories/epic-*.md) and implementation-log.md every time it is
needed, never stored, so it cannot drift from them. Standard library only.

    python scripts/phase_rollup.py                      # markdown to stdout
    python scripts/phase_rollup.py --output FILE        # markdown to FILE
    python scripts/phase_rollup.py --check              # exit 1 if a story's status disagrees with the log
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GROUPS = ("implemented", "ready", "draft", "superseded")
GROUP_TITLES = {
    "implemented": "Implemented",
    "ready": "Approved and Ready, not implemented (carry-over)",
    "draft": "Epic approved, story still Draft or blocked, not implemented (needs a decision as well as the build)",
    "superseded": "Superseded",
}

_STORY = re.compile(r"^## Story (\d+)\.(\d+)\s*[—-]\s*(.+?)\s*\n+\*\*Status:\*\*\s*(.*?)\s*$", re.MULTILINE)
_HEADING = re.compile(r"^## Story \d+\.\d+", re.MULTILINE)
_LOGGED = re.compile(r"^## Story (\d+\.\d+)", re.MULTILINE)


@dataclass(frozen=True)
class Story:
    epic: int
    sid: str
    title: str
    status: str
    group: str
    note: str


@dataclass(frozen=True)
class Drift:
    sid: str
    kind: str
    status: str


@dataclass
class Rollup:
    stories: list[Story] = field(default_factory=list)
    drift: list[Drift] = field(default_factory=list)

    @property
    def counts(self) -> dict[str, int]:
        return {g: sum(1 for s in self.stories if s.group == g) for g in GROUPS}


def _is_complete(status: str) -> bool:
    return status.startswith(("Completed", "Done"))


def _group(status: str, logged: bool) -> str:
    if logged or _is_complete(status):
        return "implemented"
    if status.startswith("Superseded"):
        return "superseded"
    if status.startswith(("Ready", "Approved")):
        return "ready"
    return "draft"


def build(stories_dir: Path, log_path: Path) -> Rollup:
    stories_dir, log_path = Path(stories_dir), Path(log_path)
    assert stories_dir.is_dir(), f"missing stories directory: {stories_dir}"
    assert log_path.is_file(), f"missing implementation log: {log_path}"
    logged = set(_LOGGED.findall(log_path.read_text(encoding="utf-8")))
    rollup = Rollup()
    for path in sorted(stories_dir.glob("epic-*.md")):
        text = path.read_text(encoding="utf-8")
        for epic, num, title, status in _STORY.findall(text):
            sid = f"{epic}.{num}"
            status = " ".join(status.split())
            is_logged = sid in logged
            group = _group(status, is_logged)
            rollup.stories.append(Story(int(epic), sid, title, status, group, status[:140]))
            if is_logged and not _is_complete(status):
                rollup.drift.append(Drift(sid, "logged_but_not_marked_complete", status[:80]))
            elif _is_complete(status) and not is_logged:
                rollup.drift.append(Drift(sid, "marked_complete_without_log", status[:80]))
        headings = len(_HEADING.findall(text))
        parsed = len(_STORY.findall(text))
        assert headings == parsed, f"{path.name}: {headings} story headings but {parsed} parsed (a story has no Status line?)"
    key = lambda x: tuple(int(p) for p in x.sid.split("."))
    rollup.stories.sort(key=key)
    rollup.drift.sort(key=key)
    return rollup


def _table(rows: list[Story]) -> list[str]:
    lines = ["| Story | Title | Status note |", "|---|---|---|"]
    lines += [f"| {s.sid} | {s.title.replace('|', '/')} | {s.note.replace('|', '/')} |" for s in rows]
    return lines


def render_markdown(rollup: Rollup) -> str:
    counts = rollup.counts
    total = len(rollup.stories)
    out = [
        "# Phase Carry-Over Backlog",
        "",
        (
            "Generated from `docs/user-stories/epic-*.md` and `implementation-log.md`; never edited by hand. "
            "A story is implemented when it has a log entry or is marked Completed or Done."
        ),
        "",
        "| Group | Stories |",
        "|---|---|",
    ]
    out += [f"| {GROUP_TITLES[g]} | {counts[g]} |" for g in GROUPS]
    out += [f"| **Total** | **{total}** |", ""]
    for g in ("ready", "draft", "superseded"):
        rows = [s for s in rollup.stories if s.group == g]
        out += [f"## {GROUP_TITLES[g]}: {len(rows)}", ""]
        out += _table(rows) if rows else ["None."]
        out.append("")
    implemented = [s for s in rollup.stories if s.group == "implemented"]
    by_epic: dict[int, list[str]] = {}
    for s in implemented:
        by_epic.setdefault(s.epic, []).append(s.sid)
    out += [f"## Implemented: {len(implemented)}", "", "| Epic | Stories |", "|---|---|"]
    out += [f"| {e} | {', '.join(ids)} |" for e, ids in sorted(by_epic.items())]
    out += ["", f"## Status drift: {len(rollup.drift)}", ""]
    if rollup.drift:
        out += ["| Story | Kind | Status line |", "|---|---|---|"]
        out += [f"| {d.sid} | {d.kind} | {d.status.replace('|', '/')} |" for d in rollup.drift]
    else:
        out.append("None.")
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--stories", type=Path, default=REPO / "docs" / "user-stories")
    parser.add_argument("--log", type=Path, default=REPO / "implementation-log.md")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--check", action="store_true", help="exit 1 if any story's status disagrees with the log")
    args = parser.parse_args(argv)
    rollup = build(args.stories, args.log)
    if args.check:
        for d in rollup.drift:
            print(f"{d.sid}: {d.kind} ({d.status})", file=sys.stderr)
        return 1 if rollup.drift else 0
    text = render_markdown(rollup)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8", newline="\n")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
