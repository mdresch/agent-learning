"""Contract tests for Lessons Learned Register parsing, validation, and Phase Close integration.

Governed by:
- ADR-010: Lessons Learned Crystallization and the Organizational Process Assets Register
- BRD-010: Stage 15 Lessons Learned Crystallization and OPA Register
- FDD-010: Stage 15 Lessons Learned Crystallization and OPA Register
- Epic 10 / Story 10.1: Implement Lessons Learned Register Parser, Validation Contract, and Phase Close Readiness Bridge

Acceptance Criteria:
- AC-0: Markdown register parsing into typed LessonsLearnedEntry objects.
- AC-1: Strict schema validation raising ValueError on malformed or incomplete entries.
- AC-2: Filtering by Epic/Phase tag and support for no-new-lessons phase sign-off.
- AC-3: Seamless compatibility with PMBOK 4.7 evaluate_phase_close_readiness().
- AC-4: 100% compliance verification of the active docs/project-docs/Lessons-Learned-Register.md file.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from agent_learning.lessons_learned import (
    LessonsLearnedEntry,
    filter_crystallized_lessons,
    load_lessons_learned_register,
    parse_lessons_learned_markdown,
)
from pmbok.models.intent_refinement import (
    ReadinessPreconditionError,
    evaluate_phase_close_readiness,
)

SAMPLE_VALID_MARKDOWN = """# Lessons Learned Register

## Register

### LL-001 — Cosmos DB System Property Stripping
- **Date:** 2026-10-25
- **Epic / Story:** Epic 2 / Story 2.1
- **Scope:** Universal Storage
- **Tier 2/3 Propagation Target:** Tier 2: `.claude/skills/storage/SKILL.md`; Tier 3: `sidpa-template/storage/cosmos.py`
- **The Trap / Problem:** Passing `{**existing, ...}` into `replace_item` leaks system properties.
- **The Root Cause:** Cosmos DB includes `_etag`, `_rid` on read.
- **Actionable Invariant / Rule:** Strip all `_`-prefixed keys before updates:
  ```python
  clean = {k: v for k, v in existing.items() if not k.startswith('_')}
  ```

### LL-002 — Timezone Assertions
- **Date & Phase:** 2026-10-25 · Epic 2
- **Scope:** Universal Testing
- **Tier 2/3 Propagation Target:** Tier 2: `tests/test_storage_cosmos.py`
- **The Trap / Problem:** `assert dt is not None` is vacuous.
- **The Root Cause:** `fromisoformat` raises `ValueError` on bad input.
- **Actionable Invariant / Rule:** Assert explicit UTC offset:
  ```python
  assert dt.utcoffset() == timezone.utc.utcoffset(None)
  ```
"""

SAMPLE_SIGN_OFF_MARKDOWN = """# Lessons Learned Register

### LL-099 — Phase Close Sign-off
- **Date:** 2026-10-25
- **Phase:** Epic 99 (no-new-lessons)
- **Scope:** Repository-Wide
- **Tier 2/3 Propagation Target:** Tier 1 register sign-off
- **The Trap / Problem:** No new architectural defects or process traps occurred in this phase.
- **The Root Cause:** Well-specified requirements executed cleanly without deviations.
- **Actionable Invariant / Rule:** Explicit sign-off confirms Stage 15 review was performed.
"""


def test_ac0_parse_lessons_learned_markdown():
    """AC_0: parse_lessons_learned_markdown extracts typed LessonsLearnedEntry instances."""
    entries = parse_lessons_learned_markdown(SAMPLE_VALID_MARKDOWN)

    assert len(entries) == 2

    ll1 = entries[0]
    assert isinstance(ll1, LessonsLearnedEntry)
    assert ll1.id == "LL-001"
    assert ll1.title == "Cosmos DB System Property Stripping"
    assert ll1.date == "2026-10-25"
    assert "Epic 2" in ll1.phase
    assert ll1.scope == "Universal Storage"
    assert "SKILL.md" in ll1.tier_targets
    assert "Passing `{**existing, ...}`" in ll1.trap
    assert "Cosmos DB includes `_etag`" in ll1.root_cause
    assert "Strip all `_`-prefixed keys" in ll1.invariant
    assert ll1.crystallized is True

    # Dictionary serialization check
    d = ll1.to_dict()
    assert d["id"] == "LL-001"
    assert d["crystallized"] is True

    ll2 = entries[1]
    assert ll2.id == "LL-002"
    assert "Timezone Assertions" in ll2.title
    assert ll2.crystallized is True


def test_ac1_strict_schema_validation_failures():
    """AC_1: Missing required fields or malformed IDs raise ValueError."""
    # Malformed ID
    bad_id_md = """### LL-1 — Bad ID Format
- **Date:** 2026-10-25
- **The Trap / Problem:** Trap
- **The Root Cause:** Cause
- **Actionable Invariant / Rule:** Invariant
- **Tier 2/3 Propagation Target:** Target
"""
    with pytest.raises(ValueError, match="Malformed Lesson Learned ID"):
        parse_lessons_learned_markdown(bad_id_md)

    # Missing Actionable Invariant
    missing_invariant_md = """### LL-005 — Missing Invariant
- **Date:** 2026-10-25
- **The Trap / Problem:** Some trap
- **The Root Cause:** Some root cause
- **Tier 2/3 Propagation Target:** Target
"""
    with pytest.raises(ValueError, match="missing required field: 'invariant'"):
        parse_lessons_learned_markdown(missing_invariant_md)

    # Missing Tier Targets
    missing_tier_targets_md = """### LL-006 — Missing Tier Targets
- **Date:** 2026-10-25
- **The Trap / Problem:** Some trap
- **The Root Cause:** Some root cause
- **Actionable Invariant / Rule:** Some invariant
"""
    with pytest.raises(ValueError, match="missing required field: 'tier_targets'"):
        parse_lessons_learned_markdown(missing_tier_targets_md)


def test_ac2_filtering_by_epic_and_sign_off_support():
    """AC_2: filter_crystallized_lessons filters by epic and detects explicit sign-offs."""
    entries = parse_lessons_learned_markdown(SAMPLE_VALID_MARKDOWN)

    # Match Epic 2
    epic2_lessons = filter_crystallized_lessons(entries, epic_filter="Epic 2")
    assert len(epic2_lessons) == 2
    assert all(l["crystallized"] is True for l in epic2_lessons)

    # Non-matching epic returns empty
    epic3_lessons = filter_crystallized_lessons(entries, epic_filter="Epic 3")
    assert len(epic3_lessons) == 0

    # No filter returns all entries
    all_lessons = filter_crystallized_lessons(entries)
    assert len(all_lessons) == 2

    # Sign-off support
    signoff_entries = parse_lessons_learned_markdown(SAMPLE_SIGN_OFF_MARKDOWN)
    signoff_filtered = filter_crystallized_lessons(signoff_entries, epic_filter="Epic 99")
    assert len(signoff_filtered) == 1
    assert "no-new-lessons" in signoff_filtered[0]["phase"]


def test_ac3_phase_close_readiness_compatibility():
    """AC_3: filter_crystallized_lessons output satisfies evaluate_phase_close_readiness."""
    entries = parse_lessons_learned_markdown(SAMPLE_VALID_MARKDOWN)
    lessons_payload = filter_crystallized_lessons(entries, epic_filter="Epic 2")

    deliverables = [{"deliverable_id": "D-001", "status": "accepted"}]
    audit_records = [{"audit_id": "AUD-001", "status": "cleared", "non_conformance_count": 0}]

    result = evaluate_phase_close_readiness(deliverables, audit_records, lessons_payload)
    assert result.is_ready is True
    assert result.crystallized_lessons_count == 2
    assert result.open_findings_count == 0

    # Negative test: empty lessons payload raises ReadinessPreconditionError
    with pytest.raises(ReadinessPreconditionError, match="Stage 15 lessons learned uncrystallized"):
        evaluate_phase_close_readiness(deliverables, audit_records, [])


def test_ac4_active_repository_register_valid():
    """AC_4: The committed docs/project-docs/Lessons-Learned-Register.md parses cleanly."""
    register_path = Path("docs/project-docs/Lessons-Learned-Register.md")
    assert register_path.exists(), "Lessons-Learned-Register.md does not exist"

    entries = load_lessons_learned_register(register_path)
    assert len(entries) >= 4, f"Expected at least 4 crystallized lessons, found {len(entries)}"

    ids = [e.id for e in entries]
    assert "LL-001" in ids
    assert "LL-002" in ids
    assert "LL-003" in ids
    assert "LL-004" in ids

    for entry in entries:
        assert entry.id.startswith("LL-")
        assert entry.title
        assert entry.trap
        assert entry.root_cause
        assert entry.invariant
        assert entry.tier_targets
        assert entry.crystallized is True
