---
artifact_id: resource-foundation-utilization-control-protocol
parent_plan_id: resource-management
baseline_id: PMP-BL-v1.1.0
route: foundation_artifact
governance_policy: approve-subsidiary-plan
substage: "6.C-5"
version: "2.0.0"
owner_role: "Project Manager"
depends_on:
  - scope-management
  - schedule-management
approval_status: approved
pmbok_process: "Monitor and Control Resourcing"
---

# Resource Foundation — Utilization & Control Protocol (`PMP-BL-v1.1.0`)

Operational protocols for tracking maintainer capacity utilization, monitoring tooling consumption, and resolving resource contentions during **Phase 2: Autonomous Feedback Loops & Extensible Architecture**.

**Historical Baseline Archive:** Frozen Phase 1 utilization protocol preserved in [`docs/project-docs/history/PMP-BL-v1.0.0/management-plans/resource-baseline/foundation/Resource-Utilization-and-Control-Protocol.md`](../../history/PMP-BL-v1.0.0/management-plans/resource-baseline/foundation/Resource-Utilization-and-Control-Protocol.md).

---

## 1. Capacity Utilization & Variance Monitoring (Phase 2)

* **Maintainer Burn Rate Tracking:** Actual engineering effort is audited against planned milestone allocations (30.0 pd total envelope across M6–M10).
* **Tolerance Thresholds:**
  - **Green (Nominal):** Cumulative milestone effort within $\pm 15\%$ of planned person-days.
  - **Amber (Strain):** Cumulative effort variance between $+15\%$ and $+25\%$. PM reviews story sequencing and leverages AI pair acceleration to eliminate toil.
  - **Red (Breach):** Effort variance $> +25\%$ or maintainer strain exceeding 36 hours/week. Triggers formal descope/reschedule review with Project Sponsor.

---

## 2. Resource Contention Priority Hierarchy (Phase 2)

When engineering trade-offs or capacity bottlenecks occur, tasks are prioritized in the following strict hierarchy:

$$\text{1. Fork Collision Guard} \succ \text{2. Contract Tests} \succ \text{3. Core Extension Math} \succ \text{4. Governance Rollups}$$

1. **Upstream Fork Collision Guard:** Maintaining `src/agent_learning` as 0 lines diff against upstream `microsoft/agent-learning` takes absolute precedence over all feature code.
2. **Contract-First Verification:** Authoring $AC_n$ unit/integration tests and observing RED failure before implementation.
3. **Core Extension Implementation:** Pure stdlib execution in `agent-training-ext/` for Epics 14, 18, 16, 21, 22, 38.
4. **Governance Automation & Rollups:** Zero status drift verification via `phase_rollup.py --check`.
