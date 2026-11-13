---
artifact_type: "methodology_guide"
stage: "2"
stage_name: "Hypothesis"
pmbok_process: "Pre-Project: Design Assumption Formulation"
version: "1.2"
date: "2026-11-12"
owner: "Menno Drescher"
governance_policy: "classify-hypothesis-status (FULL authority)"
---

# Stage 2: Hypothesis — Methodology Guide

> **Renumbered 2026-11-12** (Sponsor decision): this stage was **Stage 3** before. The Initiating group's stage numbers now match real execution order: old Stage 2 (Objective) is now Stage 4; old Stage 4 (Benefit) is now Stage 3. Stage 1 (Intent) and Stage 5 (Pillars) are unchanged. See [Intent-to-Outcome Chain Coverage](../../intent-to-outcome-chain-coverage.md) §0 for the full crosswalk. A document dated before 2026-11-12 that says "Stage 3" for Hypothesis means **this** stage under its old number.

> **Purpose:** Track every design assumption this project is willing to be wrong about (`HYP-AL-NNN`) against real evidence, and move each one to a terminal state honestly rather than leaving it Formulated indefinitely.

> **Alignment:** PMBOK 8 Pre-Project, Design Assumption Formulation.

> **Authority:** FULL authority via `classify-hypothesis-status`. Six actions, not the seven some chain documents assume: `advance_to_testing`, `mark_validated`, `mark_invalidated`, `mark_inconclusive`, `remain_formulated_blocked`, `flag_for_human_review` (`docs/policy-shapes/classify-hypothesis-status.actions.json`).

> **Authority in this repository:** a hypothesis is classified by real evidence, not by schedule pressure. `flag_for_human_review` exists precisely so an ambiguous case goes to the Sponsor instead of being forced into a confident-looking bucket.

---

## 1. Overview

### 1.1 Position in the Chain

Hypotheses are not a separate register of per-id files; they are rows inside `Hypothesis-Register.md` (Stage 2's own document, extracted from `Ideation-Document.md` v1.15 on 2026-11-12), classified continuously through the phase and finally adjudicated at close.

```
Stage 1 (Intent) carries forward or introduces HYP-AL-NNN rows into Hypothesis-Register.md
    ↓
Stage 2 (Hypothesis) — this stage — classifies each row's status as evidence arrives
    ↓
Stage 3 (Benefit) reads the classified evidence as it drafts the Business Case
    ↓
Stage 18 (Intent Refinement) performs the final Bayes-factor adjudication to a terminal state at phase close
```

### 1.2 Inputs

| Input | Source | Mandatory |
|---|---|---|
| Hypothesis rows | `docs/project-docs/Hypothesis-Register.md` | Yes |
| Evidence for a given hypothesis | Episodes, test results, or research notes the hypothesis names as its test plan | Yes, before any action except `remain_formulated_blocked` or `flag_for_human_review` |
| Research grounding (where a methodology's feasibility is itself under test) | `docs/research/ideation/hypothesis-validation-and-governance-integration.md` | If applicable |

### 1.3 Outputs

| Output | Destination | Governed |
|---|---|---|
| Updated hypothesis status | `Hypothesis-Register.md`, the row's status column/cell | Yes (via `classify-hypothesis-status` per hypothesis) |
| New hypothesis id (if a new assumption is introduced) | Same document, a new `HYP-AL-NNN` row, never reusing or renumbering an existing id | Yes |

### 1.4 Success Criteria

Stage 2 is healthy when:
- [ ] Every `HYP-AL-NNN` row has a current status and, if not Formulated, the evidence it rests on
- [ ] No hypothesis sits at a non-terminal status past the point its own test plan says it should have resolved, without `remain_formulated_blocked` naming the blocker
- [ ] A hypothesis carried from the prior phase keeps its id and prior status unless new evidence changes it
- [ ] Each classification is recorded as an episode (`classify-hypothesis-status`, FULL authority)

---

## 2. Process

### Step 1: Locate the hypothesis

Find its row in `Hypothesis-Register.md` by `HYP-AL-NNN` id. Do not create a parallel per-id `HYP-*.md` file; this repository keeps hypotheses as table rows in that one register, not as standalone files.

### Step 2: Gather real evidence

A hypothesis moves off `Formulated` only on a real, actionable test plan or real evidence — never on a plausible-sounding argument. If the evidence lives outside the repository (a converged low-authority donor, a failure history) and the test environment cannot reach it, the hypothesis stays `Formulated/Blocked`: state the blocker, do not force a classification (this was the exact trap LL-044 records — see Stage 15).

### Step 3: Run `classify-hypothesis-status`

Choose the action that matches the evidence:
- `advance_to_testing` — a real test plan now exists.
- `mark_validated` / `mark_invalidated` — real evidence confirms or contradicts it.
- `mark_inconclusive` — real evidence exists but doesn't clearly decide it.
- `remain_formulated_blocked` — no test has happened, or a named prerequisite blocks it.
- `flag_for_human_review` — whether the evidence actually supports any of the above is itself ambiguous.

### Step 4: Update the row and record

Write the new status into `Hypothesis-Register.md` and record the classification episode. A validated hypothesis that graduates to a permanent architectural invariant, or a refuted one that is archived, happens at Stage 18's final adjudication, not here — Stage 2 tracks status continuously; Stage 18 closes the books once per phase.

---

## 3. Current Instance (as of 2026-11-12)

Phase 3 carries 19 non-terminal hypotheses forward unchanged from Phase 2's close, plus the newly registered `HYP-AL-028` (DPO sample efficiency, resolving Stage 16 Phase 2 finding F1 / `GC-P2-05`), now recorded in `Hypothesis-Register.md` v1.1 (extracted from `Ideation-Document.md` v1.15 on 2026-11-12). Six of those 19 (`HYP-AL-012`–`017`) were since withdrawn for referencing unrelated projects — 13 remain active. None of the active carried hypotheses were force-classified at Phase 2's close — they carry their Phase 2 status into Phase 3 for continued evidence-gathering.

---

## 4. Validation

```bash
grep -n "HYP-AL-" docs/project-docs/Hypothesis-Register.md | head -40
```
No dedicated hypothesis-registry test exists; classification evidence is reviewed against the `classify-hypothesis-status.actions.json` action descriptions, and terminal adjudication is reviewed at Stage 18 against the Bayes-factor rule stated there.

---

## 5. Common Pitfalls

| Pitfall | Mitigation |
|---|---|
| Forcing a status to look like progress | Only real evidence moves a hypothesis; `flag_for_human_review` exists for genuine ambiguity |
| Assuming production/external data will be available for testing | Document the dependency and use `remain_formulated_blocked`, per LL-044 |
| Renumbering or reusing a hypothesis id across phases | Ids are permanent; a carried hypothesis keeps its id and status |
| Treating Stage 2's running classification as the final adjudication | The terminal Bayes-factor decision is Stage 18's, once per phase |

---

## 6. References

- [Intent-to-Outcome Chain Coverage](../../intent-to-outcome-chain-coverage.md) — §0 renumbering crosswalk, §2 row 3 (old numbering), §4 `classify-hypothesis-status`
- [Hypothesis-Register.md](../Hypothesis-Register.md)
- [docs/research/ideation/hypothesis-validation-and-governance-integration.md](../../research/ideation/hypothesis-validation-and-governance-integration.md)
- [Stage 15: Lesson Learned Methodology](./Stage-15-Lesson-Learned-Methodology.md) — LL-044, the external-evidence-dependency lesson
- [Stage 18: Intent Refinement Methodology](./Stage-18-Intent-Refinement-Methodology.md) — §2 Steps 2-3, terminal Bayes-factor adjudication

---

## Change Log

| Date | Version | Change |
|---|---|---|
| 2026-11-12 | 1.0 | Initial version (as Stage 3), grounded in `docs/policy-shapes/classify-hypothesis-status.actions.json` (6 actions, correcting the 7-action figure in `docs/intent-to-outcome-chain-coverage.md` §2 row 3), and the real Phase 3 hypothesis carry-over recorded in `Ideation-Document.md` v1.15. |
| 2026-11-12 | 1.1 | **Renumbered** from Stage 3 to Stage 2 per the Sponsor's decision, so the Initiating group's numbers match real execution order. File renamed from `Stage-3-Hypothesis-Methodology.md`. No content other than stage numbers and cross-references changed. |
| 2026-11-12 | 1.2 | Fixed every stale `Ideation-Document.md` reference left over from the hypothesis extraction (§1.1, §1.2, §1.3, Step 1, Step 4, §3, §4's validation command, §6 References) to point at `Hypothesis-Register.md` instead — the §4 `grep` was checking the wrong file entirely. Also recorded the §2 withdrawal of `HYP-AL-012`–`017` in §3 (13 of the 19 carried hypotheses remain active, not 19). |
