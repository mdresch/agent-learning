---
artifact_type: "manual_change_request"
change_request_id: "CR-20261109-001"
stage: "16"
evidence_basis: "design_time"
current_baseline: "PMP-BL-v1.1.0"
status: "draft_pending_sponsor_decision"
date: "2026-11-09"
requested_by: "Menno Drescher"
---

# Manual Change Request: Add Epic 23 to Phase 2 Scope

> **Status:** Draft for sponsor decision. This request is a manual Stage 16 assessment outside the inactive automated design-time route. It does not approve the change, revise a baseline, or authorize implementation.

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
| Decision status | Pending; no approval or governance episode recorded |

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
| Project Sponsor | Pending | — |
| Steering Committee | Pending | — |

Until those decisions and the Stage 17 approval are recorded, `PMP-BL-v1.1.0` remains unchanged, Epic 23 remains outside authorized scope, and implementation remains blocked.
