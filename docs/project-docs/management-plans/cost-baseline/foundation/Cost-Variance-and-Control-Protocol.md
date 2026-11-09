---
artifact_id: cost-foundation-variance-control-protocol
parent_plan_id: cost-management
baseline_id: PMP-BL-v1.1.0
route: foundation_artifact
governance_policy: approve-subsidiary-plan
substage: "6.D-4"
version: "2.0.0"
owner_role: "Project Manager"
depends_on:
  - scope-management
  - schedule-management
approval_status: approved
pmbok_process: "Monitor and Control Finances"
---

# Cost Foundation — Cost Variance & Financial Control Protocol (`PMP-BL-v1.1.0`)

Defines EVM formulas, financial variance thresholds, and escalation pathways for **Phase 2: Autonomous Feedback Loops & Extensible Architecture**.

**Historical Baseline Archive:** Frozen Phase 1 variance protocol preserved in [`docs/project-docs/history/PMP-BL-v1.0.0/management-plans/cost-baseline/foundation/Cost-Variance-and-Control-Protocol.md`](../../history/PMP-BL-v1.0.0/management-plans/cost-baseline/foundation/Cost-Variance-and-Control-Protocol.md).

---

## 1. Earned Value Management (EVM) Baseline Parameters (Phase 2)

* **Budget at Completion ($BAC$):** **€19,175.00** economic valuation / **€300.00** maximum cash OpEx ceiling.
* **Earned Value ($EV$):** Planned economic value ($PV$) of verified stories completed inside `agent-training-ext/`.
* **Actual Cost ($AC$):** Actual maintainer hours recorded in `implementation-log.md` ($\times$ €85.00/hr) + API cash billings.

---

## 2. Variance Tolerance Bands & Escalation Thresholds

| Status Tier | Metric Condition | Operational Impact | Governance Action Required |
|:---:|---|---|---|
| **GREEN (Nominal)** | $CPI \ge 0.90$ and $CV \ge -€1,000.00$ | Within baseline parameters. | Continue sprint execution; log EVM metrics. |
| **AMBER (Warning)** | $0.80 \le CPI < 0.90$ or $-€2,000.00 \le CV < -€1,000.00$ | Burn rate exceeds deliverable pace. | Project Manager reallocates tasks; draws from contingency reserve. |
| **RED (Breach)** | $CPI < 0.80$, or cash spend $> €100.00/\text{mo}$ | Milestone envelope breached. | **Mandatory Work Halt:** Submit Stage 16/17 change request for Sponsor sign-off. |
