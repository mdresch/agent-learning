"""Scope Management Plan profile and Section 2 checks (ADR-025, FDD-025). Pure: no I/O, no storage."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from .body_visible import visible_for_measurement
from .standards import HEADINGS, LintFlag

SCOPE_PLAN_ID = "scope-management"
_WBS = re.compile(r"work breakdown structure|\bWBS\b", re.IGNORECASE)
_DOD = re.compile(r"definition of done|\bDoD\b", re.IGNORECASE)
_ARROW_LINK = re.compile(r"→|->")
_PHASE = re.compile(r"\bphase\b", re.IGNORECASE)
_EPIC = re.compile(r"\bepic\b", re.IGNORECASE)
_STORY = re.compile(r"\bstory\b|\buser story\b", re.IGNORECASE)
_COMMIT_OR_WP = re.compile(r"\bcommit\b|work package", re.IGNORECASE)
_AC = re.compile(r"acceptance criteria", re.IGNORECASE)
_OWNER = re.compile(r"\bowner\b", re.IGNORECASE)
_PARENT = re.compile(r"\bparent\b", re.IGNORECASE)


@dataclass(frozen=True)
class ScopeMeasure:
    floor: int
    cap: int
    min_out_of_scope_items: int


SCOPE_MEASURES: Mapping[str, ScopeMeasure] = MappingProxyType(
    {
        "pmp_section": ScopeMeasure(floor=180, cap=750, min_out_of_scope_items=2),
        "full_plan": ScopeMeasure(floor=700, cap=4500, min_out_of_scope_items=4),
    }
)


def scope_measure(plan_id: str, route: str) -> ScopeMeasure | None:
    """Return Scope floors, cap and boundary minimum for scope-management; else None (FDD-025 §3.1)."""
    if plan_id != SCOPE_PLAN_ID or route not in SCOPE_MEASURES:
        return None
    return SCOPE_MEASURES[route]


def _content_flag(message: str) -> LintFlag:
    return LintFlag(code="MISSING_REQUIRED_SECTION", tier="B", message=message)


def _section_two(visible: str) -> str | None:
    first = HEADINGS[1].search(visible)
    if first is None:
        return None
    newline = visible.find("\n", first.end())
    start = len(visible) if newline == -1 else newline + 1
    third = HEADINGS[2].search(visible, first.end())
    return visible[start : third.start() if third else len(visible)]


def _hierarchy_terms(section: str) -> set[str]:
    found: set[str] = set()
    if _PHASE.search(section):
        found.add("phase")
    if _EPIC.search(section):
        found.add("epic")
    if _STORY.search(section):
        found.add("story")
    if re.search(r"\bcommit\b", section, re.IGNORECASE):
        found.add("commit")
    if re.search(r"work package", section, re.IGNORECASE):
        found.add("work package")
    return found


def _has_linked_hierarchy(section: str) -> bool:
    """True when one line links two hierarchy terms with an arrow (FDD-025 §3.4)."""
    return any(_ARROW_LINK.search(line) and len(_hierarchy_terms(line)) >= 2 for line in section.splitlines())


def check_scope_sections(body: str, route: str) -> list[LintFlag]:
    """Tier B Section 2 Scope findings (FDD-025 §3.4). Returns [] when Section 2 heading is absent."""
    if route == "not_applicable":
        return []

    visible = visible_for_measurement(body)
    section = _section_two(visible)
    if section is None:
        return []

    flags: list[LintFlag] = []
    if _WBS.search(section) is None:
        flags.append(_content_flag("WBS rules are missing"))
    if _DOD.search(section) is None:
        flags.append(_content_flag("Definition of Done is missing"))

    if route == "pmp_section":
        terms = _hierarchy_terms(section)
        if len(terms) < 2 and not _has_linked_hierarchy(section):
            flags.append(_content_flag("WBS hierarchy is missing"))
    elif route == "full_plan":
        missing_h: list[str] = []
        if not _PHASE.search(section):
            missing_h.append("phase")
        if not _EPIC.search(section):
            missing_h.append("epic")
        if not _STORY.search(section):
            missing_h.append("story")
        if not _COMMIT_OR_WP.search(section):
            missing_h.append("commit or work package")
        if missing_h:
            flags.append(_content_flag(f"WBS dictionary hierarchy is incomplete: missing {', '.join(missing_h)}"))
        missing_f: list[str] = []
        if not _AC.search(section):
            missing_f.append("acceptance criteria")
        if not _OWNER.search(section):
            missing_f.append("owner")
        if not _PARENT.search(section):
            missing_f.append("parent")
        if missing_f:
            flags.append(_content_flag(f"WBS dictionary fields are incomplete: missing {', '.join(missing_f)}"))
    return flags
