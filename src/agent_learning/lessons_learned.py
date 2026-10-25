"""Stage 15 Lessons Learned Register parser and schema validator.

Governed by ADR-010, BRD-010, FDD-010, and Epic 10 / Story 10.1.
Implements the Stage 15 Breakout & Recap Session retrospective notebook.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


@dataclass(frozen=True)
class LessonsLearnedEntry:
    """Structured representation of a crystallized Stage 15 Lesson Learned."""

    id: str
    date: str
    phase: str
    title: str
    trap: str
    root_cause: str
    invariant: str
    scope: str
    tier_targets: str
    crystallized: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "date": self.date,
            "phase": self.phase,
            "title": self.title,
            "trap": self.trap,
            "root_cause": self.root_cause,
            "invariant": self.invariant,
            "scope": self.scope,
            "tier_targets": self.tier_targets,
            "crystallized": self.crystallized,
        }


_ENTRY_HEADER_RE = re.compile(r"^###\s+(LL-[A-Za-z0-9_-]+)\s+[—-]\s+(.+)$")
_FIELD_LINE_RE = re.compile(r"^-\s+\*\*(.+?):\*\*\s*(.*)$")
_VALID_ID_RE = re.compile(r"^LL-\d{3,}$")


def parse_lessons_learned_markdown(content: str) -> List[LessonsLearnedEntry]:
    """Parse a Markdown Lessons Learned Register and extract crystallized entries.

    Raises:
        ValueError: If an entry has a malformed ID or is missing required fields.
    """
    entries: List[LessonsLearnedEntry] = []
    lines = content.splitlines()

    current_id: Optional[str] = None
    current_title: Optional[str] = None
    current_fields: Dict[str, List[str]] = {}
    current_field_key: Optional[str] = None

    def _flush_current_entry() -> None:
        nonlocal current_id, current_title, current_fields, current_field_key
        if not current_id or not current_title:
            return

        if not _VALID_ID_RE.match(current_id):
            raise ValueError(f"Malformed Lesson Learned ID '{current_id}'; must match 'LL-###' format")

        field_map = {k.lower(): "\n".join(v).strip() for k, v in current_fields.items()}

        date = field_map.get("date", "")
        phase = field_map.get("phase", field_map.get("epic / story", field_map.get("date & phase", "")))
        if not date and "date & phase" in field_map:
            date = field_map["date & phase"].split("·")[0].strip()

        trap = field_map.get("the trap / problem", field_map.get("the trap", field_map.get("trap", "")))
        root_cause = field_map.get("the root cause", field_map.get("root cause", ""))
        invariant = field_map.get(
            "actionable invariant / rule",
            field_map.get("actionable invariant", field_map.get("invariant", "")),
        )
        scope = field_map.get("scope", "Universal Cross-Project")
        tier_targets = field_map.get("tier 2/3 propagation target", field_map.get("tier targets", ""))

        # Required field validations
        if not current_title.strip():
            raise ValueError(f"Lesson Learned '{current_id}' missing required field: 'title'")
        if not trap.strip():
            raise ValueError(f"Lesson Learned '{current_id}' missing required field: 'trap'")
        if not root_cause.strip():
            raise ValueError(f"Lesson Learned '{current_id}' missing required field: 'root_cause'")
        if not invariant.strip():
            raise ValueError(f"Lesson Learned '{current_id}' missing required field: 'invariant'")
        if not tier_targets.strip():
            raise ValueError(f"Lesson Learned '{current_id}' missing required field: 'tier_targets'")

        entries.append(
            LessonsLearnedEntry(
                id=current_id,
                date=date,
                phase=phase,
                title=current_title,
                trap=trap,
                root_cause=root_cause,
                invariant=invariant,
                scope=scope,
                tier_targets=tier_targets,
                crystallized=True,
            )
        )

        current_id = None
        current_title = None
        current_fields = {}
        current_field_key = None

    for line in lines:
        header_match = _ENTRY_HEADER_RE.match(line.strip())
        if header_match:
            _flush_current_entry()
            current_id = header_match.group(1).strip()
            current_title = header_match.group(2).strip()
            current_fields = {}
            current_field_key = None
            continue

        if current_id is not None:
            field_match = _FIELD_LINE_RE.match(line.strip())
            if field_match:
                current_field_key = field_match.group(1).strip().lower()
                val = field_match.group(2).strip()
                current_fields[current_field_key] = [val] if val else []
            elif current_field_key is not None:
                # Continuation of multiline field (e.g. code blocks, multi-line prose)
                current_fields[current_field_key].append(line)

    _flush_current_entry()
    return entries


def load_lessons_learned_register(
    path: str | Path = "docs/project-docs/Lessons-Learned-Register.md",
) -> List[LessonsLearnedEntry]:
    """Load and parse the canonical Lessons Learned Register file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Lessons Learned Register not found at: {p}")
    content = p.read_text(encoding="utf-8")
    return parse_lessons_learned_markdown(content)


def filter_crystallized_lessons(
    entries: Sequence[LessonsLearnedEntry],
    epic_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Filter crystallized lessons matching an epic/phase tag, ready for Phase Close checks."""
    if not epic_filter:
        return [e.to_dict() for e in entries]

    target = epic_filter.lower()
    matched = [
        e.to_dict()
        for e in entries
        if target in e.phase.lower() or target in e.title.lower()
    ]
    return matched

