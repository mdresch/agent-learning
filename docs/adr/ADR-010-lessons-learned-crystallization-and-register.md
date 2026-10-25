# ADR 010: Lessons Learned Crystallization and the Organizational Process Assets Register

## 1. Executive Brief
As `agent-learning` transitions from initial architecture to accelerated implementation across epics (Epics 1, 2, 5, 7, 9), critical engineering lessons, edge-case traps, and quality patterns emerge during development and automated review (e.g., Cosmos DB system-property stripping, non-vacuous timezone-aware assertion design, optional cloud SDK exception fallbacks, and automated PR review loops). Today, these insights reside only in transient PR comments or developer chat history, leaving future epics and related projects vulnerable to repeating identical mistakes.

This ADR establishes a formal, lightweight **Stage 15 Lessons Learned Register** (`docs/project-docs/Lessons-Learned-Register.md`) directly operationalizing the Stage 15 requirement formalized in **ADR-008** (§3 Stage 14-15) and **ADR-009** (§3.1 Phase Close Preconditions). It defines a 3-tier crystallization protocol ensuring that hard-won implementation lessons propagate into institutional memory across project boundaries without introducing storage overhead.

## 2. Status
**Accepted (2026-10-25)** — Formally approved by Menno Drescher (score: 96/100 across 5 architecture assessment methods) to operationalize Stage 15 Lessons Learned crystallization and OPA management.

## 3. Context
- **Stage 15 in the PMBOK Lifecycle:** On the 18-stage Intent-to-Outcome chain (`PROJECT-MANAGEMENT-ONTOLOGY.json`, ADR-008, ADR-009), Stage 15 (**Lessons Learned**) bridges execution outcomes (Stage 12) with Governance Evolution (Stage 16) and Intent Refinement (Stage 18).
- **Hard Gate in Code:** In `pmbok/models/intent_refinement.py` (`evaluate_phase_close_readiness()`), Phase Close readiness explicitly enforces that Stage 15 lessons learned must be crystallized before Stage 18 administrative closure or next-phase handoff can proceed.
- **Absence of Canonical Register:** Until now, `docs/project-docs/` contained `Business-Requirements/`, `Functional-Design/`, and `management-plans/`, but lacked a dedicated markdown register to record crystallized lessons learned.
- **Cross-Project Scope:** Findings from storage concurrency (Cosmos DB `_`-prefixed metadata) and test assertion rigor (verifying UTC offsets rather than truthiness of exception-raising parsers) are not isolated to `agent-learning`; they represent universal software engineering principles that apply to sibling repositories (e.g. `sidpa-template`).

## 4. Decision

### 4.1 Canonical Register Location
A single canonical markdown register is created at:
`docs/project-docs/Lessons-Learned-Register.md`

This file is append-only, human-readable, and version-controlled alongside repository code. Phase Close readiness in `intent_refinement.py` is satisfied when at least one `LL-###` entry (or an explicit no-new-lessons phase sign-off) referencing the closing Epic/Phase is committed to this register.

### 4.2 Standard Crystallization Schema
Each lesson learned entry must adhere to the following schema:
- **Identifier:** `LL-###` (sequentially numbered, e.g., `LL-001`).
- **Date & Phase:** Date crystallized and associated Epic / Story.
- **Title:** Descriptive summary of the finding.
- **The Trap / Problem:** Real-world manifestation or bug observed during development / review.
- **The Root Cause:** Underlying technical, architectural, or procedural mechanism.
- **Actionable Invariant / Rule:** Concrete engineering rule, invariant, or coding convention to prevent recurrence.
- **Scope & Traceability:** Classification (Component-Specific, Repository-Wide, or Universal Cross-Project), cross-reference to relevant PR/commit/issue, and **Tier 2/3 Propagation Target** (e.g., path to updated `SKILL.md` or `sidpa-template` issue).

### 4.3 3-Tier Propagation Protocol
To ensure lessons learned actively govern future execution rather than sitting inert in an archive, every crystallized lesson is evaluated across three propagation tiers:
1. **Tier 1 (Project Register):** Recorded in `docs/project-docs/Lessons-Learned-Register.md` for historical traceability, audit compliance, and PMBOK Phase Close verification.
2. **Tier 2 (In-Repo Component Skills):** Transferred into the appropriate component skill file (`.claude/skills/<component>/SKILL.md`) to actively steer coding agents and prevent regressions in this codebase.
3. **Tier 3 (Universal Cross-Project Memory):** Universal engineering principles are upstreamed into global developer rules (`RULE[user_global]`, Antigravity `/learn`), or codified into `sidpa-template` for automatic inheritance by all future initiatives.

### 4.4 ADR-002 Storage Invariant Preservation
In strict adherence to **ADR-002 Invariant #2**, lessons learned are maintained as repository governance assets in markdown and JSON audit logs. They are **never** introduced as a 6th record type in `LearningStore`.

## 5. Alternatives Considered

| Alternative | Reason for rejection |
|---|---|
| **Leave lessons in PR comments and chat logs** | Status quo. Unindexed, non-searchable across sessions, and lost when branches are pruned. Guarantees recurrence of subtle bugs across epics. |
| **Persist lessons inside `LearningStore` as a new record type** | Violates ADR-002 Invariant #2 (frozen 5-record-type storage model). Lessons learned belong to project governance/OPAs, not agent runtime state. |
| **Store lessons exclusively in personal scratchpads** | Siloed and inaccessible to automated audit pipelines, CI gates, and peer agents. |

## 6. Consequences

### Positive
- Closes the PMBOK Phase Close readiness requirement in `pmbok/models/intent_refinement.py` with an authoritative project asset.
- Prevents recurring regressions by translating retrospective findings into active component skills (`.claude/skills/`).
- Provides a structured pipeline to export universal engineering principles into `sidpa-template` and global agent rules.

### Negative
- Requires a small, disciplined documentation step (5–10 minutes) at the conclusion of each epic or major review cycle.

