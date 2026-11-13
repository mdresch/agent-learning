---
artifact_type: "methodology_guide"
stage: "4"
stage_name: "Objective"
pmbok_process: "4.1 Develop Project Charter"
version: "1.1"
date: "2026-11-12"
owner: "Menno Drescher"
governance_policy: "approve-charter (FULL authority)"
---

# Stage 4: Objective — Methodology Guide

> **Renumbered 2026-11-12** (Sponsor decision): this stage was **Stage 2** before. The Initiating group's stage numbers now match real execution order: old Stage 3 (Hypothesis) is now Stage 2; old Stage 4 (Benefit) is now Stage 3. Stage 1 (Intent) and Stage 5 (Pillars) are unchanged. See [Intent-to-Outcome Chain Coverage](../../intent-to-outcome-chain-coverage.md) §0 for the full crosswalk. A document dated before 2026-11-12 that says "Stage 2" for Objective means **this** stage under its old number — this was the exact numbering that made it look like the Charter could be drafted right after Stage 1, which it cannot.

> **Purpose:** Turn the Business Case and Benefits plan (Stage 3) into a Project Charter that names the Sponsor's authority, measurable objectives, and scope boundaries, so execution has one document the Project Manager's authority traces to.

> **Alignment:** PMBOK 8 Process 4.1 Develop Project Charter.

> **Authority:** FULL authority via `approve-charter` (3 actions: `approve_charter`, `reject_charter`, `request_revision_before_decision`).

> **Authority in this repository:** the Sponsor is both the chartering authority and the sole decision-maker; there is no separate Steering Committee. The Charter's purpose here is to formally designate the Project Manager's authority to operate the project to completion — without a Stakeholder Register naming both the Sponsor and the Project Manager, there is no one for the Charter to designate, so it is not drafted (Sponsor, 2026-11-11).

---

## 1. Overview

### 1.1 Position in the Chain

```
Stage 1 (Intent) and Stage 3 (Benefit)
    ↓  (Business Case + Benefits plan are Charter inputs, not a follow-on)
Stage 4 (Objective) — this stage
    ↓
Stage 5 (Pillars & Architecture), Stage 6 (Requirement), Stage 7 (Project/PMP)
```

Stage 3's Benefits plan is a **Charter input**, drafted before the Charter, not written retroactively to justify one already approved. This stage now correctly sits fourth, after Stage 2 (Hypothesis) and Stage 3 (Benefit) — not second, which is what its old number implied.

### 1.2 Inputs

| Input | Source | Mandatory |
|---|---|---|
| Business Case | `docs/project-docs/Business-Case.md` | Yes |
| Benefits Management Plan | `docs/project-docs/Benefits-Management-Plan.md` | Yes |
| Stakeholder Register (names the Sponsor and the Project Manager) | `docs/project-docs/Stakeholder-Register.md` | Yes — sufficient as long as it names those two; it is not itself a full Stakeholder Engagement Plan |
| Ideation Document | `docs/project-docs/Ideation-Document.md` | Yes |

### 1.3 Outputs

| Output | Destination | Governed |
|---|---|---|
| Project Charter | `docs/project-docs/Project-Charter.md` | Yes (via `approve-charter`) |

### 1.4 Success Criteria

Stage 4 is complete when:
- [ ] The Stakeholder Register names the Sponsor and the Project Manager
- [ ] The Charter states measurable objectives aligned with the Benefits Management Plan
- [ ] The Charter states the Sponsor's authority and the scope boundary it sets for Stage 5-7
- [ ] `approve-charter` has run and the decision is recorded
- [ ] Project-Status-Register.md names the Charter's version and the episode id

---

## 2. Process

### Step 1: Confirm the prerequisites exist

Before drafting, confirm the Stakeholder Register names the Sponsor and Project Manager, and that the Business Case and Benefits Management Plan are current for this phase (amended, if the phase changed them — Stage 3's own methodology covers that amendment route). A Charter drafted before these exist has nothing to formally designate.

### Step 2: Draft or amend the Charter

State: strategic purpose (from the Spark/Ideation, Stage 1), Sponsor authority and the Project Manager's designated authority, measurable objectives tied to the Benefits Management Plan, and scope boundaries this phase operates within. If this is an amendment to an already-approved Charter, route it the same way any hand-authored approved document is amended (Sponsor-accepted amendment, recorded with its date and rationale), not a silent hand-edit.

### Step 3: Submit for `approve-charter`

Run the policy's recommendation, show it to the Sponsor, and wait. On the Sponsor's explicit instruction, run `task-policy-adjudicate` then `task-episode-register`, printing the store path and file count before and after (LL-040).

### Step 4: Record and hand off

Record the decision in the Charter itself and in Project-Status-Register.md. The Charter now bounds Stage 5 (Pillars decompose it), Stage 6 (Requirement specifications trace to it), and Stage 7 (the PMP formalizes within it).

---

## 3. Current Instance (as of 2026-11-12)

Phase 3's Charter has **not been drafted**. Project-Status-Register.md §1 lists it among the Phase 3 Planning items, downstream of the Stakeholder Register and the `GC-P2-05` hand-authored amendments to the Business Case and Benefits Management Plan (now applied to those two documents, pending re-approval; the Charter's own `GC-P2-05` text fix is still outstanding). Do not draft a Phase 3 Charter ahead of those.

---

## 4. Validation

```bash
grep -n "^## \|Sponsor\|Project Manager" docs/project-docs/Project-Charter.md
grep -n "Sponsor\|Project Manager" docs/project-docs/Stakeholder-Register.md
```
No dedicated schema-validation script exists for the Charter in this repository; review against `docs/policy-shapes/approve-charter.actions.json`.

---

## 5. Common Pitfalls

| Pitfall | Mitigation |
|---|---|
| Drafting the Charter to justify scope, then back-filling the Benefits plan | Benefits Management Plan is a Charter input; draft it first |
| Drafting a Charter before the Stakeholder Register names a Sponsor and PM | Confirm the register first; the Charter exists to designate authority to a named person |
| Treating the Charter as PM-authority to change at will | Only the Sponsor approves it (`approve-charter`); the PM operates within it, does not amend it unilaterally |
| Assuming this stage runs right after Stage 1 because its (old) number was low | It runs fourth, after Stage 2 (Hypothesis) and Stage 3 (Benefit) — this exact confusion is why the stage was renumbered |

---

## 6. References

- [Intent-to-Outcome Chain Coverage](../../intent-to-outcome-chain-coverage.md) — §0 renumbering crosswalk, §2 row 2 (old numbering), §4 `approve-charter`
- [Project-Charter.md](../Project-Charter.md)
- [Business-Case.md](../Business-Case.md)
- [Benefits-Management-Plan.md](../Benefits-Management-Plan.md)
- [Stage 3: Benefit Methodology](./Stage-3-Benefit-Methodology.md)
- [Stage 18: Intent Refinement Methodology](./Stage-18-Intent-Refinement-Methodology.md) — §2 Step 8's roll-up order names the Stakeholder Register as the Charter's prerequisite

---

## Change Log

| Date | Version | Change |
|---|---|---|
| 2026-11-12 | 1.0 | Initial version (as Stage 2), grounded in `docs/intent-to-outcome-chain-coverage.md` §2 row 2, `docs/policy-shapes/approve-charter.actions.json`, and the Sponsor's 2026-11-11 note (recorded in the Stage 18 methodology) that the Stakeholder Register is a Charter prerequisite. |
| 2026-11-12 | 1.1 | **Renumbered** from Stage 2 to Stage 4 per the Sponsor's decision: its old number made it look like this stage could run right after Stage 1, in parallel with Hypothesis — it cannot; it is fourth. File renamed from `Stage-2-Objective-Methodology.md`. |
