---
artifact_type: "methodology_guide"
stage: "3"
stage_name: "Benefit"
pmbok_process: "Business Documents: Benefits Realization Planning"
version: "1.3"
date: "2026-11-12"
owner: "Menno Drescher"
governance_policy: "approve-business-case (FULL authority); approve-benefits (FULL authority)"
---

# Stage 3: Benefit — Methodology Guide

> **Renumbered 2026-11-12** (Sponsor decision): this stage was **Stage 4** before. The Initiating group's stage numbers now match real execution order: old Stage 2 (Objective) is now Stage 4; old Stage 3 (Hypothesis) is now Stage 2. Stage 1 (Intent) and Stage 5 (Pillars) are unchanged. See [Intent-to-Outcome Chain Coverage](../../intent-to-outcome-chain-coverage.md) §0 for the full crosswalk. A document dated before 2026-11-12 that says "Stage 4" for Benefit means **this** stage under its old number.

> **Purpose:** Ground the project's value premise — why this investment, what benefit it realizes, at what risk — before the Charter formally authorizes chartering on top of it.

> **Alignment:** PMBOK 8 Business Documents, Benefits Realization Planning.

> **Authority:** two separate FULL-authority gates, one per document, not one shared gate: `approve-business-case` for `Business-Case.md` (3 actions: `approve_business_case`, `reject_business_case`, `request_revision_before_decision`) and `approve-benefits` for `Benefits-Management-Plan.md` (3 actions: `approve_benefits_plan`, `reject_benefits_plan`, `request_revision_before_decision`). The real `Benefits-Management-Plan.md` was approved via `approve-benefits`, episode `8cfdbf52-92bc-445f-aa0d-db729ca8667f` — not via `approve-business-case` as `docs/intent-to-outcome-chain-coverage.md`'s policy table implies by naming only one policy for this stage.

> **Authority in this repository:** these are hand-authored, Sponsor-approved documents, not output of the `pmbok-planning` tooling (unlike the Stage 7 subsidiary plans). An already-approved Business Case or Benefits Management Plan changes through a Sponsor-accepted amendment with its date and rationale recorded in the document, never a silent hand-edit.

---

## 1. Overview

### 1.1 Position in the Chain

```
Stage 1 (Intent) and Stage 2 (Hypothesis)
    ↓
Stage 3 (Benefit) — this stage — Business Case & Benefits Management Plan
    ↓
Stage 4 (Objective) — the Charter is authorized on top of this, not the reverse
```

The Benefits Management Plan is a **Charter input**. It is drafted and approved before the Charter, never written retroactively to justify a Charter already approved.

### 1.2 Inputs

| Input | Source | Mandatory |
|---|---|---|
| Ideation Document (strategic motivation) | `docs/project-docs/Ideation-Document.md` | Yes |
| Hypothesis Register (the evidence a value premise cites) | `docs/project-docs/Hypothesis-Register.md` | Yes |
| Prior phase's realized benefits (phase 2+) | `docs/project-docs/Status-Reports/Benefit-Realization-Review-Assessment.md` and the Stage 12 Actual Outcome assessments | If phase 2+ |

### 1.3 Outputs

| Output | Destination | Governed |
|---|---|---|
| Business Case | `docs/project-docs/Business-Case.md` | Yes (via `approve-business-case`) |
| Benefits Management Plan | `docs/project-docs/Benefits-Management-Plan.md` | Yes (via `approve-benefits`) |

### 1.4 Success Criteria

Stage 3 is complete when:
- [ ] The Business Case ties its value premise to specific hypotheses (Stage 2), not an unsubstantiated ROI claim
- [ ] The Benefits Management Plan states how and when each stated benefit will be measured
- [ ] Both `approve-business-case` and `approve-benefits` have run and the Sponsor's decisions are recorded
- [ ] The Charter (Stage 4) can now be drafted on top of these

---

## 2. Process

### Step 1: State the value premise

Draft or amend the Business Case: what problem, what hypothesis-backed value, what alternatives were considered, what risk is accepted. Link explicitly to the `HYP-AL-NNN` rows (Stage 2) the value premise depends on — a Business Case whose benefit claim has no hypothesis behind it is a red flag `approve-business-case` is built to catch.

### Step 2: State how benefit is measured

Draft or amend the Benefits Management Plan: the metric, the measurement window, and who owns tracking it. For a phase 2+ Benefits plan, reconcile against the prior phase's actual realized benefit (Stage 12's Benefit Realization Review) rather than restating the same target unchanged.

### Step 3: Submit each document for its own gate

Run `approve-business-case` for `Business-Case.md` and, separately, `approve-benefits` for `Benefits-Management-Plan.md` — two runs, not one. For each: show the Sponsor the recommendation, and on their explicit instruction run `task-policy-adjudicate` then `task-episode-register`, printing the store path and file count before and after (LL-040). The safe tool for this is `scripts/approve.py decide <scores.json>` (registers nothing) followed by `scripts/approve.py register <subject> --by "<name>" --disposition accept|reject --summary "..."` only once the Sponsor has actually decided.

### Step 4: Record and hand off to Stage 4

Record the decision in both documents and in Project-Status-Register.md. Stage 4 (Objective) may now draft or amend the Charter against this Benefits Management Plan.

---

## 3. Current Instance (as of 2026-11-12)

Phase 3's `GC-P2-05` reconciliation (replacing `agent-training-ext/` with `src/agent_learning_ext/` and repointing `HYP-AL-018` to `HYP-AL-028`) has been applied to both `Business-Case.md` v2.1 and `Benefits-Management-Plan.md` v2.1. Both are pending the Sponsor's re-approval via `approve-business-case` and `approve-benefits` respectively (both `decide` steps ran clean: `approve_business_case` 0.893 and `approve_benefits_plan` 0.893, nothing registered yet). The same `GC-P2-05` reconciliation on the Charter is still outstanding.

---

## 4. Validation

```bash
grep -n "^## \|HYP-AL-" docs/project-docs/Business-Case.md
grep -n "^## " docs/project-docs/Benefits-Management-Plan.md
```
No dedicated schema-validation script exists for these two files; review against `docs/policy-shapes/approve-business-case.actions.json` and `docs/policy-shapes/approve-benefits.actions.json`.

---

## 5. Common Pitfalls

| Pitfall | Mitigation |
|---|---|
| Restating a prior phase's benefit target unchanged | Reconcile against the prior phase's Benefit Realization Review (Stage 12) first |
| A Business Case whose ROI claim names no hypothesis | Every value-premise claim traces to a `HYP-AL-NNN` row |
| Hand-editing an approved Business Case or Benefits Plan without recording the amendment | Record the Sponsor's acceptance, its date, and the rationale in the document itself |
| Treating `approve-business-case` as covering `Benefits-Management-Plan.md` too | They are two separate policies; `Benefits-Management-Plan.md` is approved via `approve-benefits` |

---

## 6. References

- [Intent-to-Outcome Chain Coverage](../../intent-to-outcome-chain-coverage.md) — §0 renumbering crosswalk, §2 row 4 (old numbering), §4 `approve-business-case`
- [Business-Case.md](../Business-Case.md)
- [Benefits-Management-Plan.md](../Benefits-Management-Plan.md)
- [Benefit-Realization-Review-Assessment.md](../Status-Reports/Benefit-Realization-Review-Assessment.md)
- [Stage 2: Hypothesis Methodology](./Stage-2-Hypothesis-Methodology.md)
- [Stage 4: Objective Methodology](./Stage-4-Objective-Methodology.md)
- [Stage 12: Actual Outcome Methodology](./Stage-12-Actual-Outcome-Methodology.md)

---

## Change Log

| Date | Version | Change |
|---|---|---|
| 2026-11-12 | 1.0 | Initial version (as Stage 4), grounded in `docs/intent-to-outcome-chain-coverage.md` §2 row 4, `docs/policy-shapes/approve-business-case.actions.json`, and Project-Status-Register.md's record of the deferred Phase 3 `GC-P2-05` amendment. |
| 2026-11-12 | 1.1 | Corrected the governing policy: `Benefits-Management-Plan.md` is approved via its own `approve-benefits` gate, not `approve-business-case`. Step 3 now runs two separate gates, not one. |
| 2026-11-12 | 1.2 | **Renumbered** from Stage 4 to Stage 3 per the Sponsor's decision. File renamed from `Stage-4-Benefit-Methodology.md`. Recorded the applied `GC-P2-05` reconciliation and the two pending `decide` recommendations in §3. |
| 2026-11-12 | 1.3 | Fixed §1.2 Inputs: hypotheses no longer live in `Ideation-Document.md` (extracted to `Hypothesis-Register.md`, Stage 2's own document) — split into two input rows so the value-premise evidence check points at the right file. |
