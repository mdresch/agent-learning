# Epic 10: Stage 15 Lessons Learned Crystallization and OPA Register

**Source ADR:** [ADR-010](../adr/ADR-010-lessons-learned-crystallization-and-register.md) — Accepted (2026-10-25)  
**Source BRD/FDD:** [BRD-010](../project-docs/Business-Requirements/BRD-010-lessons-learned-crystallization-and-register.md) / [FDD-010](../project-docs/Functional-Design/FDD-010-lessons-learned-crystallization-and-register.md)  

---

## Story 10.1 — Implement Lessons Learned Register Parser, Validation Contract, and Phase Close Readiness Bridge

**Status:** Completed (2026-10-25) — Implemented in feat/story-10.1 with contract tests in tests/test_lessons_learned.py.  
**As** an engineering team and governance auditor, **I want** an automated parser and schema validator for `docs/project-docs/Lessons-Learned-Register.md`, **so that** crystallized lessons are strictly verified, institutional memory is protected against decay, and PMBOK Phase Close readiness gates are deterministically satisfied.

### Acceptance Criteria:
- **$AC_0$ (Markdown Register Parsing):** `parse_lessons_learned_markdown()` extracts all `LL-###` sections from valid markdown text into typed `LessonsLearnedEntry` instances, capturing `id`, `date`, `phase`, `title`, `trap`, `root_cause`, `invariant`, `scope`, and `tier_targets`.
- **$AC_1$ (Strict Schema Validation):** The parser enforces that every entry conforms to the ADR-010 §4.2 schema. Malformed identifiers or missing required fields (`title`, `trap`, `root_cause`, `invariant`, `tier_targets`) raise `ValueError` with clear field diagnostic messages.
- **$AC_2$ (Filtering & Sign-Off Support):** `filter_crystallized_lessons()` filters entries by target Epic/Phase (case-insensitive substring) and supports explicit no-new-lessons phase sign-offs per ADR-010 §4.1.
- **$AC_3$ (Phase Close Readiness Integration):** Formatted dictionary payloads from `filter_crystallized_lessons()` cleanly pass PMBOK 4.7 `evaluate_phase_close_readiness()` validation without raising `ReadinessPreconditionError`, contributing accurately to `crystallized_lessons_count`.
- **$AC_4$ (Active Register Verification):** Contract test verifies that the active repository register `docs/project-docs/Lessons-Learned-Register.md` parses cleanly with 100% compliance, returning valid entries for `LL-001`, `LL-002`, `LL-003`, and `LL-004`.

---

## Out of Scope per ADR-010 & BRD-010

- Introducing a 6th record type in `LearningStore` (prohibited by ADR-002 Invariant #2).
- Hardcoding file I/O operations inside `pmbok/models/intent_refinement.py` (violates model purity boundary).
- Unvetted direct commits to `sidpa-template`.
