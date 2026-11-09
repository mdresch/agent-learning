---
artifact_id: schedule-foundation-reserve-register
parent_plan_id: schedule-management
baseline_id: PMP-BL-v1.1.0
route: foundation_artifact
governance_policy: approve-subsidiary-plan
substage: "6.B-3"
version: "2.0.0"
owner_role: "Project Manager"
depends_on:
  - scope-management
approval_status: approved
---

# Schedule Foundation — Reserve Register (`PMP-BL-v1.1.0`)

Schedule buffers and contingency allocations for Phase 2 known-unknowns (PMBOK 8 §2.3.5 Table 2-7). Durations in person-days (**pd**).

**Historical Baseline Archive:** Frozen Phase 1 reserve register preserved in [`docs/project-docs/history/PMP-BL-v1.0.0/management-plans/schedule-baseline/foundation/Schedule-Reserve-Register.md`](../../history/PMP-BL-v1.0.0/management-plans/schedule-baseline/foundation/Schedule-Reserve-Register.md).

---

## 1. Management Reserves (Phase 2 Milestones)

| Reserve ID | Amount (pd) | Accountable Holder | Purpose / Allocation Scope | Consumption & Drawdown Rule |
|---|:---:|---|---|---|
| **SR-P2-M10** | 5.0 | Project Manager | Close-out synthesis, regression reconciliation, and `PCD-Phase2` preparation. | Log in `implementation-log.md`; Sponsor approval required for drawdown $> 5$ pd. |

---

## 2. Schedule Contingency Buffers (Risk Triggers)

| Trigger ID | Associated Risk | Epic / Milestone | Buffer (pd) | Trigger Condition |
|---|---|---|:---:|---|
| **CR-P2-01** | Upstream Breaking Refactor | Epics 14, 18 | 3.0 | Upstream Microsoft modifies dataclass signatures, requiring adapter layer. |
| **CR-P2-02** | Tag Grammar Syntax Edge Cases | Epic 14 (Stories 14.1..14.3) | 2.0 | Complex nested markdown tags in review corpora require parser expansion. |
| **CR-P2-03** | Contextual Optimization Non-Convergence | Epic 18 (DPO Loss) | 2.5 | DPO loss optimization fails to achieve $>30\%$ sample efficiency threshold. |

Total Phase 2 Buffer Envelope: **12.5 person-days** (accommodated within overall project schedule float).
