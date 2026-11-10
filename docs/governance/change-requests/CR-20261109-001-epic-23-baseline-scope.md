---
artifact_type: "manual_change_request"
change_request_id: "CR-20261109-001"
stage: "16"
evidence_basis: "design_time"
current_baseline: "PMP-BL-v1.1.0"
status: "rescoped_to_phase_3_2026-11-10"
date: "2026-11-09"
requested_by: "Menno Drescher"
---

# Manual Change Request: Add Epic 23 to Phase 2 Scope

> **Status (2026-11-10): rescoped to Phase 3.** The Sponsor decided on 2026-11-10 that Epic 23 is not built in Phase 2 and that Phase 2 closes once, so the baseline change is carried by the Phase 2 close adaptation as a Phase 3 input (see section 7). The text below is the record as it stood before that decision and is not rewritten.
>
> **Earlier status:** Approved by the Project Sponsor on 2026-11-09 and by the Steering Committee on 2026-11-10 (see section 6). This request is a manual Stage 16 assessment outside the inactive automated design-time route. The approvals decide that Epic 23 is in Phase 2 scope and permit the Stage 17 change package; they do not themselves revise `PMP-BL-v1.1.0`, and Epic 23 implementation stays blocked until the revised baseline is approved.

## 1. Request

Add the approved seven-story Epic 23, Active Dueling-Bandit Ranking Engine, to the authorized Phase 2 scope. The requested implementation is described in the approved [BRD-023](../../project-docs/Business-Requirements/BRD-023-active-dueling-bandit-ranking-engine.md), [FDD-023](../../project-docs/Functional-Design/FDD-023-active-dueling-bandit-ranking-engine.md), and [Epic 23 stories](../../user-stories/epic-23-active-dueling-bandit-ranking-engine.md).

The request is limited to authorizing Epic 23 through a formal baseline change. It does not add the currently out-of-scope human-facing command, empirical effectiveness claim, or other FDD-023 §7 items unless separately approved.

## 2. Baseline and authority

The approved [PMP](../../project-docs/Project-Management-Plan.md) `PMP-BL-v1.1.0` includes Epics 14, 16, 18, 21, 22, and 38; it does not include Epic 23. The [Scope-Management Plan](../../project-docs/management-plans/Scope-Management-Plan.md) classifies adding an Epic as a Level 3 baseline breach requiring Stage 17 integrated change control. It also makes downstream schedule and cost plans stale if the scope baseline changes, until they are re-baselined. The [Risk-Management Plan](../../project-docs/management-plans/Risk-Management-Plan.md) requires baseline changes to go through Stage 17.

The approved stories explicitly block implementation pending baseline authorization. Approval of the BRD, FDD, and stories is not that authorization. No code work under Epic 23 is authorized by this request.

## 3. Manual Stage 16 assessment

| Assessment field | Proposed assessment |
|---|---|
| Trigger | Sponsor-directed manual request after design approval; not a Stage 15 lesson |
| Evidence basis | `design_time` |
| Primary diff type | `scope` |
| Related impact | `structural` — adds a new engine/module to the Phase 2 product scope |
| Overall impact | High — changes the approved scope baseline and affects critical-path schedule, cost/capacity, architecture constraints, and quality gates |
| Proposed escalation | Steering Committee and Project Sponsor |
| Stage 16 recommendation | Permit preparation of a complete Stage 17 change package, subject to the unresolved decisions and estimates below |
| Decision status | Sponsor approved 2026-11-09; Steering Committee approved 2026-11-10; Stage 17 approval pending; no governance episode recorded for the two approvals |

This is a manual assessment, not an output from `classify-diff-type` or `escalate-diff-response`. No automated governance decision is represented as having occurred.

## 4. Impact assessment

### Scope and architecture

- The change adds seven approved stories and a ranking engine that selects item pairs and fits Bradley-Terry utilities from human-provided outcomes.
- FDD-023 places the module at `src/agent_learning_ext/dueling.py`, while the PMP and Charter define the custom package boundary as `agent-training-ext/`. The scope standard's exact applicability to `src/agent_learning_ext/` is unresolved.
- FDD-023 reuses `numpy` through Epic 18's `pairwise.py`; the PMP and Charter state a standard-library-only constraint. The scope change must explicitly resolve this conflict rather than silently waive the constraint.
- Epic 23 has an existing dependency on Epic 18's implementation. Its fit, variance, pair selection, state, and data stories otherwise define their own contracts.

### Schedule

- The approved Phase 2 critical path is M6–M10, totaling 30.0 person-days. M8 covers Epics 16 and 21; M9 covers Epics 22 and 38.
- The current approved schedule does not estimate Epic 23 or place it in a milestone. The added effort, sequencing, critical-path effect, and any change to the phase completion forecast are unknown.
- The schedule plan's 5.0 person-day management reserve and 12.5 person-day risk contingency are not presumed available for this work. A schedule impact analysis and updated estimate are required.

### Cost and resources

- The approved Phase 2 economic labor baseline is €19,175; the total budget including sponsor management reserve is €21,725. The Charter commits 120–160 maintainer engineering hours across the existing Phase 2 scope.
- No incremental effort, cost, or available capacity has been established for Epic 23. No reserve drawdown or budget increase is requested or authorized here.
- Stage 17 preparation must estimate engineering, verification, review, and documentation effort and reconcile it with remaining capacity and the cost baseline.

### Quality, performance, and risk

- BRU-023-04 and Story 23.1 AC_8 retain the median fit-time target of less than 5 ms for N ≤ 100. The prototype measured 98 ms at the default iteration cap, so it currently misses the requirement. The target must not be weakened implicitly; a viable implementation or a separately approved requirement change is needed.
- The seven-story test plan includes numerical contracts, synthetic-only checks, real-data validation, and upstream-untouched checks. Epic 23 currently has no recorded real pairwise judgments, so synthetic results cannot establish HYP-AL-015.
- Principal risks are schedule/capacity overrun, failure to meet the performance target, and unresolved package/dependency constraints. The Stage 17 package should add owners, responses, and measurable verification evidence.
- Open design questions in FDD-023 §7 beyond scope and dependency policy should be dispositioned as in-scope decisions or explicitly retained non-goals before readiness authorization.

## 5. Conditions for Stage 17 package and decision

Before any revised baseline is approved:

1. Decide whether Epic 23 belongs in the current Phase 2 scope or should be deferred to a later baseline.
2. Resolve the `src/agent_learning_ext/` versus `agent-training-ext/` boundary and the `numpy` versus standard-library-only constraint.
3. Produce an effort, sequencing, critical-path, capacity, and cost analysis; identify any proposed reserve use or budget change for explicit approval.
4. Preserve the less-than-5-ms target unless a separately reviewed and approved requirement change is made; provide a credible verification plan.
5. Prepare the required Stage 17 integrated change package, including revised scope, schedule, and cost plans; update the integrated PMP and related traceability only after approval.

## 6. Decision record

| Role | Decision | Date |
|---|---|---|
| Project Sponsor | Approved: prepare the Stage 17 change package for adding Epic 23 to Phase 2 | 2026-11-09 |
| Steering Committee | Approved: Epic 23 is in Phase 2 scope; prepare the Stage 17 change package | 2026-11-10 |

The Project Sponsor's decision was given by Menno Drescher in the working session of 2026-11-09 and is recorded here from that statement; no governance episode was registered for it. It permits the work in section 5 (conditions 1 to 5). Until the Steering Committee decision and the Stage 17 approval are recorded, `PMP-BL-v1.1.0` remains unchanged, Epic 23 remains outside authorized scope, and implementation remains blocked.

The Steering Committee decision was given by Menno Drescher in the working session of 2026-11-10 ("the CR is approved and Epic 23 can be amended") and is recorded here from that statement; the Sponsor, Project Manager and maintainer are one person in this repository (BRD-008), and the request lists the Steering Committee separately. No governance episode was registered for either approval.

**Where the five conditions of section 5 stand (2026-11-10):**

| Condition | State |
|---|---|
| 1. In Phase 2 scope or deferred | Decided: in Phase 2 scope (the two approvals above) |
| 2. Package boundary and `numpy` | Resolved in the documents by two Stage 16 correction notes: ADR-023 now names `src/agent_learning_ext/dueling.py`, and FDD-023 section 7 item 2 records that the "standard library only" invariant named a folder that no longer exists and that `numpy` is accepted in `src/agent_learning_ext/`; the PMP and Charter wording is revised in the Stage 17 package |
| 3. Effort, sequencing, capacity and cost analysis | Open: not yet prepared |
| 4. The less-than-5-ms target | Open: preserved; the prototype measured 98 ms; a viable implementation or a separately approved requirement change is still needed |
| 5. The Stage 17 change package | Open: not yet prepared; the stories stay blocked until it is approved |

Condition 2 (the custom package boundary) has moved since this request was drafted: the Epic 14 engine now lives in `src/agent_learning_ext/` (PR #162, merged), so the boundary the PMP and Charter call `agent-training-ext/` is `src/agent_learning_ext/` in the code. The PMP, Charter and generated plans still name the old folder and must be revised in the Stage 17 package.

## 7. Rescoping decision (2026-11-10)

The Project Sponsor decided on 2026-11-10 ("we will push these to Phase 3 and close Phase 2 once instead of multiple times"), given by Menno Drescher in the working session and recorded here from that statement; no governance episode was registered for it. It supersedes the Steering Committee's 2026-11-10 "in Phase 2 scope" decision in section 6, which stays above as the record of what was decided at the time.

| Item | Result |
|---|---|
| Epic 23 | Moves from Phase 2 scope to Phase 3 scope. Not built in Phase 2. |
| `PMP-BL-v1.1.0` | Unchanged by this request. Phase 2 closes under it. |
| Separate Stage 17 package for this request | Not pursued. The draft [ADP-20261110-001](../../project-docs/Adaptation-Plans/ADP-20261110-001-Epic-23-Scope-Change-Package.md) is kept as an input to the Phase 2 close adaptation and to the Phase 3 baseline. |
| Epics 24 and 39 | Already waiting on the next phase; carried by the same close. |
| Conditions 3 and 4 (section 5) | Not closed. The estimate, cost option and 5 ms plan in the draft are inputs for the Phase 3 baseline decision, which still needs the Sponsor's choices. |
| Condition 5 | Replaced: the baseline change is made once, at Phase 2 close. |

