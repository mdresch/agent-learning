# ADR 010: Lessons Learned Crystallization and the Organizational Process Assets Register

## 1. Executive Brief
As `agent-learning` moves through its epics, engineering lessons, edge-case traps, and quality patterns emerge while user stories are turned into code and reviewed (e.g., Cosmos DB system-property stripping, non-vacuous timezone-aware assertion design, optional cloud SDK exception fallbacks, and automated PR review loops). Today these insights reside only in transient PR comments or developer chat history, leaving future epics and related projects vulnerable to repeating identical mistakes.

This ADR establishes the **Breakout & Recap Session** and its companion register (`docs/project-docs/Lessons-Learned-Register.md`). It is a **light breakout held once per epic, after the last user story of that epic has been implemented and reviewed**: a short recap of how the code was created from the user stories, covering unexpected traps, subtle defects and review findings. It is not a new stage and not a heavy ceremony. Anything worth keeping is written down as a short register entry, and may optionally be propagated into component skills or universal memory without introducing storage overhead.

**Scope boundary:** this ADR does **not** define or represent Stage 15 of the Intent-to-Outcome chain. A formal Stage 15 review is separate work, to be decided on its own. This ADR defines only the light recap and the register it produces.

## 2. Status
**Accepted (2026-10-25)** — Formally approved by Menno Drescher (score: 96/100 across 5 architecture assessment methods) to operationalize Stage 15 Lessons Learned crystallization and OPA management.

**Amended and closed (2026-10-25)** — The trigger, the position in the story loop, the entry schema and an optional facilitator extension were approved by Menno directly ("close ADR 010"; see §9). The amendment was not run through the `classify-diff-type` pipeline (ADR-007), so no classification result exists, and the earlier manual "Tier 2 clarification" label is withdrawn. Status remains Accepted. BRD-010 and FDD-010 were edited for consistency and were not re-adjudicated through `approve-brd` / `approve-fdd`.

## 3. Context
- **A Light Recap, Not a Stage:** The breakout is an agile retrospective moment after coding, not a bureaucratic phase: *What unexpected trap did we hit turning the stories into code? What was the root cause? What rule prevents recurrence?* It is distinct from the formal Stage 15 review on the 18-stage Intent-to-Outcome chain (`PROJECT-MANAGEMENT-ONTOLOGY.json`, ADR-008, ADR-009), which this ADR does not define.
- **Trigger is the last story of an epic.** The recap happens after the final user story of an epic has been implemented and its PR review findings are known, because review findings are part of what is worth recapping. It does not run per story.
- **Existing Gate in Code:** `pmbok/models/intent_refinement.py` (`evaluate_phase_close_readiness()`) already requires crystallized lessons before Stage 18 closure or next-phase handoff, and refers to them as "Stage 15 lessons learned". The register produced by this recap is the artifact that gate consumes. That existing "Stage 15" label in code and in some documents is not changed by this ADR. How a separate formal Stage 15 review relates to the gate is left to that separate work.
- **Absence of Canonical Register:** Until now, `docs/project-docs/` contained `Business-Requirements/`, `Functional-Design/`, and `management-plans/`, but lacked a dedicated markdown register to record crystallized lessons learned.
- **Cross-Project Scope:** Findings from storage concurrency (Cosmos DB `_`-prefixed metadata) and test assertion rigor (verifying UTC offsets rather than truthiness of exception-raising parsers) are not isolated to `agent-learning`; they can be universal software engineering principles that apply to sibling repositories (e.g. `sidpa-template`).

## 4. Decision

### 4.1 Trigger and Scope of the Breakout
- **Position in the story loop:** inside `implement-story`, after the contracts are verified (Step 6, story contract and full suite passing) and after the reviewer (Q Developer) has approved the PR (Step 8). At that point the coding is verified and reviewed, and the question is whether it produced any lessons worth keeping.
- **When:** Once per epic, at that position for the last user story of the epic. Earlier stories only leave the optional one-line note below.
- **Focus:** How code was created from the user stories: unexpected traps, subtle defects, and PR review findings encountered along the way. It is a recap of the coding work, not a formal review of the epic and not a general project retrospective.
- **Optional per-story note:** During any story, a one-line note of a surprising trap may be jotted down for the epic-end recap. This is optional, never a gate, and creates no register entry on its own.
- **Duration:** A brief session (roughly 5–10 minutes). If nothing noteworthy happened, the session ends with the sign-off in §4.2.

### 4.2 Canonical Register and Sign-Off
A single canonical markdown register is created at:
`docs/project-docs/Lessons-Learned-Register.md`

This file is append-only, human-readable, and version-controlled alongside repository code. Phase Close readiness in `intent_refinement.py` is satisfied when the closing Epic/Phase has at least one `LL-###` entry referencing it. When the recap finds nothing new, a **no-new-lessons sign-off** is recorded as a short `LL-###` entry whose Epic/Phase contains the marker `no-new-lessons` and whose required fields (§4.3) carry brief text, with the propagation target `Tier 1 register sign-off`. A sign-off is therefore a short entry, not a separate file format, because the parser (`parse_lessons_learned_markdown()`) and the Phase Close gate consume `LL-###` entries only.

### 4.3 Lightweight Entry Schema
Each lesson learned entry is headed `### LL-### — <Title>` and requires only these fields, which the parser enforces:
- **Identifier:** `LL-###` (sequentially numbered, e.g., `LL-001`).
- **Title:** Descriptive summary of the finding (the entry heading).
- **The Trap:** What was observed during development or review.
- **The Root Cause:** The underlying technical, architectural, or procedural mechanism.
- **The Rule:** The concrete invariant or convention that prevents recurrence (`Actionable Invariant / Rule`).
- **Tier 2/3 Propagation Target:** Where the lesson is propagated (§4.4). Required to be present, but it may simply read `Tier 1 register sign-off` or `Tier 1 only` when the lesson is not propagated further.

Recommended: **Epic / Story** (or `Date & Phase`), because the Phase Close filter matches entries by Epic/Phase. Optional: **date**, **scope** (Component-Specific, Repository-Wide, or Universal; defaults to Universal Cross-Project), and a PR or commit reference.

### 4.4 Optional 3-Tier Propagation
Every crystallized lesson is **considered** for propagation; none is required to be propagated:
1. **Tier 1 (Project Register):** Recorded in `docs/project-docs/Lessons-Learned-Register.md` for historical traceability and Phase Close verification. This is the only tier every lesson receives.
2. **Tier 2 (In-Repo Component Skills):** Where the lesson is component-specific, transfer it into the relevant `.claude/skills/<component>/SKILL.md` to steer coding agents and prevent regressions in this codebase.
3. **Tier 3 (Universal Cross-Project Memory):** Where the lesson is a universal engineering principle, upstream it into global developer rules or codify it in `sidpa-template` for inheritance by future initiatives.

### 4.5 ADR-002 Storage Invariant Preservation
In strict adherence to **ADR-002 Invariant #2**, lessons learned are maintained as repository governance assets in markdown and JSON audit logs. They are **never** introduced as a 6th record type in `LearningStore`.

### 4.6 Downstream Alignment
The following documents are aligned to §4.1–§4.4 and §4.7 and must stay consistent with this ADR: `docs/adr/README.md`, `.claude/skills/implement-story/SKILL.md` (Step 7, Step 9, Definition of Done; Step 9 is currently worded as a "Stage 15 formal epic review" and must be reworded to the light recap), `.claude/skills/governance/SKILL.md` (§2), `docs/project-docs/Business-Requirements/BRD-010-*.md`, `docs/project-docs/Functional-Design/FDD-010-*.md`, `docs/user-stories/epic-10-*.md`, `docs/project-docs/Lessons-Learned-Register.md` (header), and `docs/intent-to-outcome-chain-coverage.md` (Stage 15 row, which currently describes this recap as the Stage 15 process and must not). Where any of them differs from this ADR, this ADR governs. Existing "Stage 15" labels in titles and in `lessons_learned.py` are out of scope here and listed for a separate renaming decision.

### 4.7 Permitted Extension: Autonomous Breakout Facilitator
The breakout recap may be facilitated by an **Autonomous Breakout Facilitator**: an agent-driven retrospective assistant that automates the mechanics of the breakout (§4.1) and the optional cross-repo propagation (§4.4). This section records that the extension is **permitted**, and the guardrails it must respect. It does not commit the project to building it; building it is separate, scoped work.

What the facilitator may do:
- **Prepare the recap:** gather the epic's stories, PR review findings, optional per-story trap notes, and implementation-log entries, and draft candidate traps and root causes (§4.1).
- **Draft register entries:** propose `LL-###` entries in the §4.3 schema, or a no-new-lessons sign-off, for the human to accept, edit or reject.
- **Propose propagation:** draft Tier 2 changes to `.claude/skills/<component>/SKILL.md` and Tier 3 changes to `sidpa-template` or other sibling repositories (e.g., as a diff, issue or pull request), including detecting when a lesson already exists elsewhere.

Guardrails:
- **Human authority stays final.** Consistent with ADR-001 §4.4 and ADR-009 Invariant #3, the facilitator recommends and drafts; a human accepts the register entry and the sign-off. It never closes the Phase Close gate on its own.
- **Cross-repo actions are outward-facing.** Any change to another repository (pull request, issue, push) requires explicit human approval for that action. The facilitator never merges or pushes to a sibling repository autonomously.
- **No new storage.** Drafts, session transcripts and propagation records live in markdown or JSON repository assets, never as a sixth `LearningStore` record type (ADR-002 §7 Invariant #2).
- **No self-modifying governance.** The facilitator does not edit Accepted ADRs, and does not change its own instructions or skills without review.
- **Learning requires its own decision.** If the facilitator is ever to learn from which proposed lessons humans accept (e.g., via a `TaskPolicy`), that is a new decision requiring its own ADR under ADR-001 and ADR-003; this ADR does not grant it.

## 5. Alternatives Considered

| Alternative | Reason for rejection |
|---|---|
| **Leave lessons in PR comments and chat logs** | Status quo. Unindexed, non-searchable across sessions, and lost when branches are pruned. Guarantees recurrence of subtle bugs across epics. |
| **Persist lessons inside `LearningStore` as a new record type** | Violates ADR-002 Invariant #2 (frozen 5-record-type storage model). Lessons learned belong to project governance/OPAs, not agent runtime state. |
| **Store lessons exclusively in personal scratchpads** | Siloed and inaccessible to automated audit pipelines, CI gates, and peer agents. |
| **Mandatory recap and register entry for every story** | Turns a light recap into a per-story gate and encourages filler entries. Review findings, which are part of the lesson, are only known once the epic's last PR is reviewed. |
| **Full seven-field schema with mandatory Tier 2/3 propagation per lesson** | Too heavy for a 5–10 minute breakout; discourages recording lessons at all. Core fields suffice, with the rest optional. |

## 6. Consequences

### Positive
- Closes the PMBOK Phase Close readiness requirement in `pmbok/models/intent_refinement.py` with an authoritative project asset.
- Prevents recurring regressions by letting retrospective findings flow into active component skills (`.claude/skills/`) where they apply.
- Provides an optional pipeline to export universal engineering principles into `sidpa-template` and global agent rules.
- Cost is one short session per epic, not one per story.

### Negative
- An Autonomous Breakout Facilitator (§4.7) is permitted but not built; until it is, the recap and propagation remain manual.
- A lesson from an early story in an epic can be forgotten before the epic-end recap if nobody jots the optional one-line note (§4.1).
- Requires a small, disciplined documentation step at the end of each epic.
- Until `implement-story` and the ADR README are aligned (§4.6), they describe a different cadence than this ADR.

## 7. Architectural Invariants

1. This ADR defines a light recap, adds no new stage, no additional approval gate and no `TaskPolicy`, and does not define or represent Stage 15 of the Intent-to-Outcome chain (§1, §3).
2. The recap is held once per epic, after the epic's last story is implemented and reviewed, and focuses on how code was created from the stories (§4.1).
3. The Phase Close gate is always satisfiable: a register entry or a short no-new-lessons sign-off entry is sufficient, so the gate never forces fabricated lessons (§4.2).
4. A register entry requires only the fields in §4.3; the propagation target must be present but may be `Tier 1 only`, and propagation to Tier 2/3 is considered, never mandated (§4.4).
5. The register is append-only markdown and is never a `LearningStore` record type (§4.5; ADR-002 §7 Invariant #2).
6. An Autonomous Breakout Facilitator, if built, only drafts and proposes: a human accepts register entries and sign-offs, and every cross-repo change needs explicit human approval (§4.7).

## 8. References
- [`pmbok/models/intent_refinement.py`](../../pmbok/models/intent_refinement.py) — `evaluate_phase_close_readiness()`, the Phase Close gate cited in §3/§4.2
- [`docs/project-docs/Lessons-Learned-Register.md`](../project-docs/Lessons-Learned-Register.md) — the canonical register
- [`.claude/skills/implement-story/SKILL.md`](../../.claude/skills/implement-story/SKILL.md) — story loop whose Step 7/8 and Definition of Done must be aligned (§4.6)
- Related: [ADR-002](./ADR-002-storage-backend-strategy.md) §7 Invariant #2 — the five-record-type boundary preserved by §4.5
- Related: [ADR-007](./ADR-007-governance-change-paired-diff-classification-and-escalation.md) — the `classify-diff-type` pipeline, which this amendment was not run through
- Related: [ADR-009](./ADR-009-intent-refinement-and-cognitive-feedback-loop.md) — Phase Close readiness, which consumes the register

## 9. Amendment Log

| Date | Change | Why |
|---|---|---|
| 2026-10-25 | Accepted | Formally approved by Menno Drescher (score: 96/100 across 5 architecture assessment methods). |
| 2026-10-25 | Proposed amendment (classification pending): trigger set to once per epic after the last user story is implemented and reviewed, instead of a vague "post-delivery" trigger and a per-story recap in `implement-story` (§4.1); entry schema reduced to the fields the parser enforces, with date, scope and PR reference optional (§4.3); Tier 2/3 propagation changed from mandatory evaluation to "consider" (§4.4); added a scope boundary stating this ADR does not define or represent Stage 15 (§1, §3, §7 Invariant #1); added §4.6 downstream alignment, §7 Architectural Invariants, §8 References and this log | The intent (a light breakout recapping how code was created from the stories) was in §1/§3, but the trigger, schema weight and `implement-story` cadence contradicted it. A first draft of this amendment widened the ADR into a formal four-lens Stage 15 review; Menno clarified that the Stage 15 formal review is separate work, so that widening was removed. The trigger, propagation and cadence changes change how the process runs, so the earlier manual "Tier 2 clarification" label is withdrawn. Approved directly by Menno on 2026-10-25 ("close ADR 010") without a `classify-diff-type` run; recorded here rather than implied (ADR-007 Risk A). |
| 2026-10-25 | Aligned §4.2/§4.3/§7 to the implemented parser: the propagation target is a required field (it may read `Tier 1 only`), and a no-new-lessons sign-off is a short `LL-###` entry | `lessons_learned.py` rejects entries without a propagation target, and the contract tests model the sign-off as a full `LL-099` entry. The ADR was aligned to the code, avoiding an unscoped code change. |
| 2026-10-25 | Proposed §4.7 (Permitted Extension: Autonomous Breakout Facilitator) and §7 Invariant #6 | Menno asked that the ADR state the recap and cross-repo skill propagation can be automated by an agent-driven retrospective assistant. Recorded as a permitted, not-yet-built extension with guardrails: draft-and-propose only, human approval for register entries and every cross-repo action, no new `LearningStore` record type, and a separate ADR if it ever learns. Approved with the rest of this amendment. |
| 2026-10-25 | Fixed the position of the recap in the story loop: after contracts are verified (Step 6) and after the reviewer (Q Developer) has approved the PR (Step 8) (§4.1) | Menno specified where the recap sits, to ask whether the verified and approved coding produced any lessons. Cadence kept at the epic's last story, with the optional per-story note; if the recap should run after every story's approval instead, that is a one-line change to §4.1 and `implement-story` Step 9. |
