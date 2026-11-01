---
artifact_id: cost-foundation-variance-control-protocol
parent_plan_id: cost-management
baseline_id: PMP-BL-v1.0.0
route: foundation_artifact
governance_policy: approve-subsidiary-plan
substage: "6.D-4"
version: "1.0.0"
owner_role: "Project Manager"
depends_on:
  - scope-management
  - schedule-management
approval_status: approved
pmbok_process: "Monitor and Control Finances"
---

# Cost Foundation — Cost Variance & Financial Control Protocol (`PMP-BL-v1.0.0`)

This artifact satisfies PMBOK 8 §2.4.2 *Monitor and Control Finances* (Figure 2-30) for the Cost Management Plan. It establishes the mathematical control rules, **Earned Value Management (EVM)** metrics, variance thresholds, and escalation pathways for **Phase 1: Warm-Start & Confidence-Interval Bandits**.

---

## 1. Earned Value Management (EVM) Metrics & Formulae

Financial performance and effort burn are evaluated weekly using standardized EVM equations:

$$CV = EV - AC \quad (\text{Cost Variance})$$
$$CPI = \frac{EV}{AC} \quad (\text{Cost Performance Index})$$
$$EAC = \frac{BAC}{CPI} \quad (\text{Estimate at Completion, assuming current performance})$$
$$VAC = BAC - EAC \quad (\text{Variance at Completion})$$

* **Budget at Completion ($BAC$):** **€16,150.00** economic labor valuation / **€250.00** cash envelope (190.0 authorized hours).
* **Earned Value ($EV$):** The planned economic value ($PV$) of closed, verified user stories (100% green contract tests, observed RED first).
* **Actual Cost ($AC$):** The actual hours spent recorded in `implementation-log.md` ($\times$ €85.00/hr) plus invoiced API/cloud expenses.

---

## 2. Variance Thresholds & Governance Action Matrix

To prevent unnoticed budget drift, project tracking enforces three strict variance tolerance bands:

| Status Tier | Metric Condition | Operational Impact | Governance Action Required | Authority |
| :---: | :--- | :--- | :--- | :--- |
| **GREEN (Nominal)** | $CPI \ge 0.90$ and $CV \ge -€1,000.00$ | Within authorized parameters. | Continue normal sprint execution. Log weekly EVM metrics. | Developer / Tech Lead |
| **AMBER (Warning)** | $0.80 \le CPI < 0.90$ or $-€2,000.00 \le CV < -€1,000.00$ | Effort burn rate exceeds deliverable completion rate. | **PM Rebalancing:** Project Manager adjusts backlog task depth, prunes optional edge cases, or draws from the 15% contingency reserve. | Project Manager |
| **RED (Critical Breach)** | $CPI < 0.80$ or $CV < -€2,000.00$, or contingency reserve fully exhausted | Authorized milestone envelope breached. | **Mandatory Work Halt:** Technical execution on the breached epic halts immediately. Submit formal Stage 17 `approve-adaptation-plan` for Sponsor sign-off. | Project Sponsor (Menno Drescher) |

```
EVM Tolerance Spectrum:
[ RED: CPI < 0.80 ] <--- [ AMBER: 0.80 <= CPI < 0.90 ] ---> [ GREEN: CPI >= 0.90 ]
  (Stop & Escalate)           (PM Scope Rebalance)             (Nominal Velocity)
```

---

## 3. Reserve Drawdown & Change Control Protocol

### 3.1 Contingency Reserve Drawdown (CAT-CONT)
* **Allocation Ceiling:** **25.0 hours (€2,125.00 economic value) + €50.00 API buffer**.
* **Eligible Triggers:**
  1. Statistical recalculation or Bayesian convergence delays requiring additional test runs.
  2. Unanticipated complexity in confidence interval edge cases (e.g. singular variance matrices).
  3. Upstream dependency security patches or breaking API changes.
* **Drawdown Process:** PM records the root cause, hours consumed, and remaining balance in `implementation-log.md`. Drawdown > 10 hours requires notification to the Sponsor.

### 3.2 Management Reserve Release (CAT-MGMT)
* **Allocation Ceiling:** **5.0 person-days (30.0 hours / €2,550.00 economic value)**.
* **Eligible Triggers:** Unforeseen strategic research explorations or major Sponsor-directed scope pivots.
* **Release Process:** The Management Reserve is strictly outside the Cost Baseline. It can **only** be released through formal written Sponsor authorization via an ADR-037 baseline feedback item or an approved Stage 17 adaptation decision (`approve-adaptation-plan`).
