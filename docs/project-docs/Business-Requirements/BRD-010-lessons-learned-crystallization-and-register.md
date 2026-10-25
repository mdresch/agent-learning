# BRD-010: Stage 15 Lessons Learned Crystallization and OPA Register

**Source ADR:** [ADR-010](../../adr/ADR-010-lessons-learned-crystallization-and-register.md) — Accepted (2026-10-25)  
**Status:** Approved (2026-10-25, Menno) — derived from Accepted ADR-010; adjudicated via `approve-brd`.  
**Stakeholders:** Menno Drescher (Sponsor/Maintainer/Architect).  

---

## 1. Business Need

During the implementation of Epics 1, 2, 5, 7, and 9, the engineering and automated review process surfaced subtle but catastrophic edge cases (e.g., Cosmos DB system-property leaking into replacement bodies causing HTTP 400s, vacuous datetime assertions giving false confidence, and optional cloud SDK import failures). Previously, these findings were scattered across ephemeral PR review comments, chat logs, or developer scratchpads.

Without a canonical, machine-verifiable Organizational Process Asset (OPA), these lessons:
1. Fade across development turns and agent context windows, guaranteeing repeated defects in subsequent epics.
2. Leave Stage 15 (Lessons Learned) of the 18-stage Intent-to-Outcome chain unfulfilled.
3. Block PMBOK 4.7 Phase Close validation (`pmbok/models/intent_refinement.py:evaluate_phase_close_readiness()`), which requires verified crystallized lessons learned prior to entering Stage 18 Intent Refinement.

This Business Requirements Document establishes the operational requirements for the **Stage 15 Breakout & Recap Session**. Rather than inventing a heavy new lifecycle stage, it formalizes the post-story retrospective pause—giving the team a chance to step back, recap the traps and review findings, and record concrete, actionable invariants in a shared register.

---

## 2. Business Rules (BRU)

- **BRU-010-01 (Canonical Markdown Register):** The system must maintain a single, append-only, human-readable markdown register at `docs/project-docs/Lessons-Learned-Register.md` (ADR-010 §4.1).
- **BRU-010-02 (Standardized Schema Enforcement):** Every crystallized lesson entry must strictly conform to the 8-field schema defined in ADR-010 §4.2:
  1. `Identifier` (`LL-###`)
  2. `Date`
  3. `Epic / Phase`
  4. `Title`
  5. `The Trap / Problem`
  6. `The Root Cause`
  7. `Actionable Invariant / Rule`
  8. `Scope & Traceability` (including explicit `Tier 2/3 Propagation Target`).
- **BRU-010-03 (Automated Parsing & Verification):** The SDK must provide a deterministic parser that extracts all `LL-###` entries from markdown into structured, validated representations, raising actionable errors on incomplete or malformed entries.
- **BRU-010-04 (Phase Close Readiness Gate Integration):** The parsed lessons learned must feed into `evaluate_phase_close_readiness()`. Phase close requires that all entries are `crystallized: True` and at least one entry (or an explicit no-new-lessons sign-off) references the closing Epic/Phase.
- **BRU-010-05 (Storage Invariant Preservation):** Lessons learned are project governance assets. Under no circumstances may lessons learned be persisted as a 6th record type in `LearningStore` (ADR-002 Invariant #2).

---

## 3. Stakeholder Success Metrics

| Metric | Current State | Target State |
|---|---|---|
| Institutional Memory Persistence | Transient PR comments and chat transcripts | Canonical, version-controlled markdown register at `docs/project-docs/Lessons-Learned-Register.md` |
| Automated Parsing & Schema Validation | 0% automated parsing of lessons learned | 100% automated parsing and validation via `parse_lessons_learned_markdown()` |
| Phase Close Stage 15 Gate Integration | Manual dictionary mock in unit tests | Automated extraction from markdown register directly validating Phase Close preconditions |
| Seed Lesson Coverage | 0 codified lessons in repository | 4 fully crystallized lessons (`LL-001` through `LL-004`) verified in active register |

---

## 4. Out of Scope

- Storing lessons learned inside Cosmos DB, LocalFileStore, or `LearningStore` ABCs (rejected per ADR-002 Invariant #2).
- Automatic natural-language generation of lessons learned without human review or approved PR review triggers.
- External cloud synchronization services beyond standard git source control.
