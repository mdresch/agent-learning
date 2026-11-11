---
artifact_type: "intent_refinement_proposal"
proposal_id: "IRP-20261111-001"
baseline_from: "PMP-BL-v1.1.0"
baseline_to: "set at the Phase Close Decision (PCD-20261111-001); no baseline content changes in this proposal"
version: "0.1"
date: "2026-11-11"
prepared_by: "Claude (draft for the Project Sponsor)"
status: "draft"
governance_policy: "approve-intent-refinement"
---

# Intent Refinement Proposal: IRP-20261111-001

## Phase 2 closure and Phase 3 seeding

> **Draft.** Nothing here is approved. Where the records do not hold the input a methodology step needs, the section says so instead of supplying a figure. Written to the Stage 18 methodology (`docs/project-docs/Methodology/Stage-18-Intent-Refinement-Methodology.md`, section 3.1).

## Executive summary

| Field | Value |
|---|---|
| Proposal ID | IRP-20261111-001 |
| From baseline | `PMP-BL-v1.1.0` |
| To baseline | Set at the Phase Close Decision. No plan or baseline content changes with this proposal |
| Status | Draft |
| Date | 2026-11-11 |

## 1. Phase closure readiness (Step 1)

Source: `Status-Reports/Stage-12-Actual-Outcome-Assessment-Phase2.md`, `Project-Status-Register.md` section 1, `Handover-2026-11-11.md`.

| Precondition | State | Evidence |
|---|---|---|
| Stage 9 deliverables | Every story of the six baseline epics (14, 16, 18, 21, 22, 38) is implemented; Epic 17 as well | `phase_rollup.py --check` exits 0 |
| Stage 10 verification | 2723 passed, 2 skipped, 0 failed | `Status-Reports/Stage-10-Verification-Evidence-Phase2.md` |
| Stage 11 audit | Approved twice: 2026-11-04 (AUDIT-001 to 006), 2026-11-10 (AUDIT-007 to 017, episode `198bfc09`) | `docs/registers/Audit-Register.md` |
| Stage 12 outcome | Report exists; certifies no gate | `Stage-12-Actual-Outcome-Assessment-Phase2.md` |
| Stages 13 and 14 | Notes with per-item files | `Status-Reports/Stage-13-*`, `Stage-14-Insights-Phase2.md` |
| Stage 15 lessons | Accepted (LL-001 to LL-067) | `Lessons-Learned-Register.md` |
| Stage 16 governance change | Approved by the Sponsor 2026-11-10 | `Status-Reports/Stage-16-Governance-Change-Phase2.md` |
| Stage 17 adaptation | Completed 2026-11-11: GC-P2-01 to 03 applied; GC-P2-04 to 07 deferred to Phase 3 | `ADP-20261110-002`, PR #203 |
| Open pull requests | None | `gh pr list` |

Charter criteria not met (from the Stage 12 report, section 2): criterion 2 (hypotheses HYP-AL-005, 018, 025, 026, 027 resolved with empirical evidence: HYP-AL-005 is Testing, 018 and 025 Formulated) and criterion 5 (`PCD-Phase2` approved, which is this decision).

Exceptions, in one line each:
- CI still runs `pytest --ignore=tests/pmbok` (IMP-056), so a green CI is not the whole suite.
- AUDIT-017: no failing-first (RED) evidence in `implementation-log.md` for most stories of Epics 14, 16, 17, 18 and 22.
- PR #195 and PR #198 were merged on dated Sponsor waivers of the PR gate (IMP-065).

## 2. Hypothesis adjudication (Steps 2 and 3)

Source: `Ideation-Document.md` section 2.2 status column. **Bayes factors are not computed.** The repository holds no evidence from which to compute one for the non-validated hypotheses, and an invented figure would be a fabricated result.

| State | Count | Hypotheses |
|---|---|---|
| Validated | 8 | HYP-AL-001, 002, 003, 006, 008, 009, 026, 027 |
| Testing | 2 | HYP-AL-004, 005 |
| Formulated | 17 | HYP-AL-007, 010 to 025 |

The full list of the 27 with type, status and claim is in the PCD (`docs/governance/decisions/PCD-20261111-001-Phase-2-Close-Decision.md`, section "Hypotheses at close").

HYP-AL-028 (DPO sample efficiency) is **not yet registered** in the Ideation Document; registering it is GC-P2-05, deferred to Phase 3.

**Exception to the methodology (Success Criteria: 100% terminal resolution):** 19 of 27 hypotheses are not in a terminal state. The methodology's collapse rule would score an inconclusive hypothesis as refuted. Proposed instead: carry the 19 forward unchanged to Phase 3, because the evidence they need (for example HYP-AL-009's and HYP-AL-013's external stores, LL-065) is outside the repository. **The Sponsor decides** whether to carry them forward or apply the collapse rule.

## 3. Low-pass damping (Step 4)

**Not computed.** The method needs a series of realized outcome deltas; the Stage 12 report gives met, partly met and not met per criterion, not a numeric series. The Sponsor decides whether a numeric outcome vector is wanted for Phase 2 or the step is recorded as not applicable.

## 4. Strategic pivot capacity (Step 5)

**Not computed.** The check is $P_{proposed} \le P_{max} = \lceil C_{adapt}/2 \rceil$. The pivot list and $C_{adapt}$ for Phase 2 are not recorded. The candidate pivots in this proposal are the items of section 5; the Sponsor confirms which count as pivots.

## 5. Refined intent for Phase 3 (Step 6)

Carried forward as the Stage 18 input. Nothing in this list is built by closing Phase 2.

| Group | Items | Source |
|---|---|---|
| Deferred Adaptation Plan changes | GC-P2-04 (Tier 2 backfill), GC-P2-05 (hand-authored documents), GC-P2-06 and 07 (regenerate the PMP and plans, with the Stage 7 artifact approvals), IMP-050 (Step 8 checklist), IMP-031 (Tier 2 check) | `ADP-20261110-002`, `CR-20261111-001` |
| Approved for fixes in Phase 3 | IMP-065, 066, 067 (PR gate: resolved fixes, Q headings, malformed bullets) | Sponsor, 2026-11-11, PR #204 |
| Epics | Epic 23 and Epic 24 (Phase 3), Epic 39 (next phase) | Status Register |
| Deferred designs | F3 and F4 (ADR-022, ADR-016) | Handover |
| Phase Next improvements | IMP-002, 006, 019, 025, 027, 028, 039; IMP-068 (actuals against the schedule plan) | Continuous Improvement Register |
| Ideation inputs | Story Execution Register hook-up; Task Ownership Register and the seven preparations before agents pick up WBS work packages | `CR-20261111-001` sections 4d to 4f |
| Open decision | Whether `complete_story.py done` drops `DEFAULT_IGNORES` | Handover |

## 6. Approval record (Step 7)

| Role | Decision | Date |
|---|---|---|
| Project Sponsor | Pending | |

Policy `approve-intent-refinement` (FULL authority, `requires_human_approval: true`). No episode has been registered for this draft.

## 7. Phase seeding (Step 8)

Not run. Seeding (Phase 3 Spark and Ideation, baseline increment, lineage kernel) follows the approved PCD. `scripts/execute_stage_18.py` is written for Phase 1 and is not used for Phase 2.
