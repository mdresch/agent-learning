---
artifact_type: "adaptation_plan"
plan_id: "ADP-20261110-002"
baseline_from: "PMP-BL-v1.1.0"
baseline_to: "PMP-BL-v1.2.0 (proposed; the Sponsor decides, section 9)"
version: "0.1 (draft)"
date: "2026-11-10"
prepared_by: "Claude (draft for the Project Sponsor)"
status: "draft"
related_stage_16: "Status-Reports/Stage-16-Governance-Change-Phase2.md (approved 2026-11-10)"
related_change_requests:
  - "CR-20261109-001"
  - "CR-20261109-002"
  - "CR-20261110-001"
  - "CR-20261110-002"
governance_policy: "approve-adaptation-plan (FULL authority; the Sponsor's words decide)"
---

# Phase 2 Close Adaptation Plan (ADP-20261110-002)

> **Draft. Not approved. Nothing in sections 4 to 6 is applied by this document.** It is the single Stage 17 adaptation for Phase 2 (Sponsor, 2026-11-10: close Phase 2 once). It follows `Stage-17-Adaptation-Plan-Methodology.md` v1.1. `PMP-BL-v1.1.0` is unchanged until the plan is approved through `approve-adaptation-plan`.
>
> Effort figures anywhere in this plan are human-engineering person-days. Agentic effort is a shadow record for learning only and is not used here.

## 1. Executive summary

| Field | Value |
|---|---|
| Plan ID | ADP-20261110-002 |
| From baseline | `PMP-BL-v1.1.0` |
| To baseline | `PMP-BL-v1.2.0` (proposed) |
| Source | The approved Stage 16 assessment: 67 lessons and 62 improvements triaged, 5 baseline findings (F1 to F5), 3 change requests |
| Already done (recorded, not repeated) | skill edits (PR #187), register reconciliation (LL-065 to LL-067, crosswalk, IMP dispositions), governance store merge, Stage 16 and 17 methodology v1.1 |
| To do under this plan | 5 pending changes (GC-P2-03 to GC-P2-07) of 7, in 4 steps (section 6) |
| Status | draft |

## 2. Scope

**In scope:** the changes Stage 16 approved or left for Stage 17: the hand-authored approved documents that disagree with the code or each other (F1, F2), the regenerated PMP and plans, the tooling change set, and the Tier 2 backfill.

**Out of scope:** Epic 23 and Epic 24 (Phase 3), Epic 39 and the seven improvements rolled into Phase Next, F3 and F4 (ADR-022 and ADR-016, deferred to the next phase on 2026-11-10), and any change to Phase 2 scope, schedule or cost. The estimate and cost option in `ADP-20261110-001` stay an input to the Phase 3 baseline, not part of this plan.

## 3. Change inventory

| ID | Change | Source | Route | State |
|---|---|---|---|---|
| GC-P2-01 | `implement-story` and `heal-contract-failure` skills carry LL-027 to 036, 038, 039 and the whole-suite rule | CR-20261110-001 | Change request, one PR | **Done** (PR #187) |
| GC-P2-02 | LL-065 to LL-067, id crosswalk, index to LL-067, IMP dispositions, correction note on the Stage 17 assessment | Stage 16 proposals A and B | Register edits | **Done** (cf460ed) |
| GC-P2-03 | The tooling change set: IMP-062, 063, 045, 052, 030, 017, 015, 021, 024, 001, 007, 043, 044, 050, 031 | CR-20261110-002 | One PR (or story) each; IMP-044 delivered by #187, IMP-050 and IMP-031 edit skills and need the Sponsor's text | Pending |
| GC-P2-04 | Tier 2 backfill for lessons whose rule is not in the named target: LL-014 (`tailoring`), LL-015 (`learning-methodology-selection`), LL-046 (`ucb`, `spec_gate.py`), LL-047 (`pairwise-preference`, `spec_gate.py`), LL-065 and LL-066 (`implement-story`), LL-067 (`governance`) | Stage 16 Step 2d | Change request with the exact text, then one PR | Pending |
| GC-P2-05 | Hand-authored approved documents: register HYP-AL-028 (DPO sample efficiency) in the Ideation Document and repoint HYP-AL-018 to HYP-AL-028 in the Charter, Business Case and Benefits Management Plan; replace `agent-training-ext/` with `src/agent_learning_ext/` in the Charter, Business Case and Benefits Management Plan | Stage 16 F1 (approved) and F2 | Each document amended and accepted by the Sponsor; the exact lines are listed in section 5 | Pending |
| GC-P2-06 | Regenerate the PMP (`PMP-BL-v1.2.0`) and the nine subsidiary plans, which clears the remaining `agent-training-ext` mentions and carries HYP-AL-028 | GC-P2-05, CR-20261109-001 section 6 and 7, `ADP-20261110-001` section 7 | `scripts/orchestrate_pmbok.py --mode adapt`; never by hand | Pending, after GC-P2-05 |
| GC-P2-07 | State the unit of every effort figure in the PMP (human-engineering person-days) | LL-063 | Regeneration, with the unit in the template | Pending; the Sponsor first confirms whether the PMP already states it |

## 4. Impact mapping

| Change | Skills | Workflow or tooling | Documents | Tests |
|---|---|---|---|---|
| GC-P2-03 | `implement-story` (IMP-044 done, IMP-050, IMP-031) | `pr_gate.py`, `spec_gate.py`, `complete_story.py`, `stage16_amend.py`, `publish.yaml`, `.gitattributes`, new `approve.py` | none | one contract test per change, seen failing first |
| GC-P2-04 | six skills | `spec_gate.py` (LL-046, LL-047, with IMP-021 and IMP-024) | none | the existing skill-reading tests |
| GC-P2-05 | none | none | Ideation Document, Charter, Business Case, Benefits Management Plan | `tests/test_governance_baseline.py` unaffected (these are not in the ADR-007 manifest); hypothesis references checked by search |
| GC-P2-06 | `pmbok-planning`, `plan-lint`, `plan-approval-gate` | `orchestrate_pmbok.py` | PMP, nine subsidiary plans, foundation packs | plan-lint |
| GC-P2-07 | none | PMP template | PMP | plan-lint |

## 5. The lines GC-P2-05 touches (counted 2026-11-10)

- **HYP-AL-018 to HYP-AL-028 (DPO meaning):** Charter lines 46 and 158; Business Case lines 51, 95 and 166; Benefits Management Plan lines 31, 44 and 92; the generated Scope plans (regenerated, not edited). The Ideation Document gets a new HYP-AL-028 row in section 2.2.4 with the DPO sample-efficiency statement now in the Business Case (row for HYP-AL-018); its HYP-AL-018 row (LinUCB) stays. ADR-038 and FDD-024 already use the LinUCB meaning.
- **`agent-training-ext/`:** Charter lines 49, 57, 62, 95 and 109; Business Case (11 mentions); Benefits Management Plan (5 mentions). FDD-023 (2 mentions) stays with Epic 23 and Phase 3. About 157 mentions in current documents remain until GC-P2-05 and GC-P2-06 run; history copies under `history/` are not edited.

## 6. Implementation plan

1. **Safe store first.** Build IMP-062 and IMP-063 (GC-P2-03), so no governance run can write to the wrong store and the suite stops adding episodes. Until then, point the store variable at this repository and run the suite against a temporary store.
2. **Unblock the gate and release.** IMP-045, IMP-052; then the gate and spec-gate checks (030, 017, 021, 024); then the helper scripts (001, 007, 015, 043).
3. **Text decisions.** Draft the Tier 2 backfill text (GC-P2-04) and the IMP-050 and IMP-031 skill text as a change request; the Sponsor decides the wording; one PR applies it.
4. **Baseline.** Amend the four documents of GC-P2-05, accepted by the Sponsor one at a time; then regenerate the PMP and plans (GC-P2-06, 07) with the tooling and run plan-lint.

Each PR is merged through `scripts/pr_gate.py` only after every required workflow has concluded (LL-060) and the whole suite has passed.

## 7. Validation plan

- Whole suite, plain `uv run pytest`, against a temporary store; `tests/test_governance_baseline.py`, `tests/test_stage16_amend.py`, `tests/test_lessons_learned.py` pass.
- A search finds no `agent-training-ext` outside `history/`, ADR-023/FDD-023/Epic 23 and dated records; HYP-AL-018 appears only with the LinUCB meaning outside dated records.
- plan-lint and the plan approval gate pass on the regenerated PMP and plans; the PMP states its effort unit.
- The Stage 16 deferrals (F3, F4, the seven Phase Next improvements) are listed in the Stage 18 input, not dropped.

## 8. Rollback plan

- A merged PR is reverted by a revert commit; no history is rewritten.
- A baseline problem after regeneration: `python scripts/orchestrate_pmbok.py --mode rollback --to-baseline PMP-BL-v1.1.0`, then revert the document amendments of GC-P2-05.
- A wrong approval episode is not deleted; a dated correction entry and a new decision replace it.

## 9. Decisions for the Sponsor

1. Approve this plan as the Phase 2 adaptation (`approve-adaptation-plan`), or ask for changes.
2. Whether the adaptation bumps the baseline to `PMP-BL-v1.2.0`. CR-20261109-001 section 7 says `PMP-BL-v1.1.0` is unchanged by that request and the baseline change is made once at Phase 2 close; a minor increment follows ADR-008 section 4.6.1 for an execution adaptation. If the Sponsor prefers to keep `PMP-BL-v1.1.0`, GC-P2-05 and GC-P2-06 still change the documents but not the baseline id.
3. Whether the PMP already states its effort unit (GC-P2-07).

## 10. Approval

| Role | Decision | Date | Episode |
|---|---|---|---|
| Project Sponsor | Pending | | |

No `task-policy-decide` run, adjudication or episode exists for this plan.
