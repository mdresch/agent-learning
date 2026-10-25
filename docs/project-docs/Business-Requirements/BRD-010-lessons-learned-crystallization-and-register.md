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

This Business Requirements Document establishes the operational requirements for the **Stage 15 Breakout & Recap Session**. It adds no new stage. It formalizes a light recap held once per epic, after the epic's last user story is implemented and reviewed, on how the code was created from the stories: unexpected traps, subtle defects and review findings (ADR-010 §4.1). Concrete, actionable invariants are recorded in a shared register. This recap is distinct from the formal Stage 15 review, which is separate work and not covered by this BRD.

---

## 2. Business Rules (BRU)

- **BRU-010-01 (Canonical Markdown Register):** The system must maintain a single, append-only, human-readable markdown register at `docs/project-docs/Lessons-Learned-Register.md` (ADR-010 §4.2).
- **BRU-010-02 (Standardized Schema Enforcement):** Every crystallized lesson entry must conform to the schema defined in ADR-010 §4.3. Required (enforced by the parser):
  1. `Identifier` (`LL-###`)
  2. `Title`
  3. `The Trap / Problem`
  4. `The Root Cause`
  5. `Actionable Invariant / Rule`
  6. `Tier 2/3 Propagation Target` (must be present; may read `Tier 1 only` or `Tier 1 register sign-off`).

  Recommended: `Epic / Phase` (required in practice for the Phase Close epic filter). Optional: `Date`, `Scope`, and a PR or commit reference.
- **BRU-010-06 (Recap Cadence):** The breakout recap is held once per epic, after the epic's last user story is implemented and reviewed. It is not a per-story gate and adds no approval gate or `TaskPolicy` (ADR-010 §4.1, §7 Invariant #1).
- **BRU-010-03 (Automated Parsing & Verification):** The SDK must provide a deterministic parser that extracts all `LL-###` entries from markdown into structured, validated representations, raising actionable errors on incomplete or malformed entries.
- **BRU-010-04 (Phase Close Readiness Gate Integration):** The parsed lessons learned must feed into `evaluate_phase_close_readiness()`. Phase close requires that all entries are `crystallized: True` and at least one entry references the closing Epic/Phase. When the review finds nothing new, a short no-new-lessons sign-off entry (Epic/Phase containing `no-new-lessons`) satisfies this (ADR-010 §4.2).
- **BRU-010-05 (Storage Invariant Preservation):** Lessons learned are project governance assets. Under no circumstances may lessons learned be persisted as a 6th record type in `LearningStore` (ADR-002 Invariant #2).

---

## 3. Stakeholder Success Metrics

| Metric | Current State | Target State |
|---|---|---|
| Institutional Memory Persistence | Transient PR comments and chat transcripts | Canonical, version-controlled markdown register at `docs/project-docs/Lessons-Learned-Register.md` |
| Automated Parsing & Schema Validation | 0% automated parsing of lessons learned | 100% automated parsing and validation via `parse_lessons_learned_markdown()` |
| Phase Close Stage 15 Gate Integration | Manual dictionary mock in unit tests | Automated extraction from markdown register directly validating Phase Close preconditions |
| Seed Lesson Coverage | 0 codified lessons in repository | At least 4 crystallized lessons (the seed set `LL-001` through `LL-004`) verified in the active register; later entries are appended as they are earned |

---

## 4. Out of Scope

- Storing lessons learned inside Cosmos DB, LocalFileStore, or `LearningStore` ABCs (rejected per ADR-002 Invariant #2).
- Automatic natural-language generation of lessons learned without human review or approved PR review triggers.
- External cloud synchronization services beyond standard git source control.
- Building the Autonomous Breakout Facilitator permitted by ADR-010 §4.7. If built, it only drafts and proposes: a human accepts register entries, and every cross-repo action needs explicit human approval. It requires its own story.
