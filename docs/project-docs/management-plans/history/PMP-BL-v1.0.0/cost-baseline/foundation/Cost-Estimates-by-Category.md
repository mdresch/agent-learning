---
artifact_id: cost-foundation-estimates-by-category
parent_plan_id: cost-management
baseline_id: PMP-BL-v1.0.0
route: foundation_artifact
governance_policy: approve-subsidiary-plan
substage: "6.D-2"
version: "1.0.0"
owner_role: "Project Manager"
depends_on:
  - scope-management
  - schedule-management
approval_status: approved
pmbok_process: "Estimate Costs"
---

# Cost Foundation — Cost Estimates by Category & Milestone (`PMP-BL-v1.0.0`)

This artifact satisfies PMBOK 8 §2.4.2 *Estimate Costs* (Figure 2-28) for the Cost Management Plan. It provides the detailed bottom-up cost estimates mapped across the **Charter Milestones** and **WBS Horizons**, reconciling human effort, AI pair assistance, and cloud/tooling consumption.

---

## 1. Milestone Cost Breakdown (Charter Horizon M0.5–M5)

The table below reconciles engineering hours, economic labor valuation (€85.00/hr), and operational tooling expenses across the core Phase 1 milestone delivery pipeline:

| Milestone | Deliverable Scope & Milestone Theme | Baseline Effort (hrs) | Economic Labor Valuation (€85/h) | External Cloud / API Quota (€) | Total Milestone Valuation (€) | Cash Outlay Required (€) |
| :---: | :--- | ---: | ---: | ---: | ---: | ---: |
| **M0.5** | End-User Value Research (HYP-AL-011) | 40.0 hrs | €3,400.00 | €0.00 | **€3,400.00** | **€0.00** |
| **M1** | Softmax Policy Inspection (Epic 20) | 15.0 hrs | €1,275.00 | €25.00 | **€1,300.00** | **€25.00** |
| **M2** | Warm-Start Prototype (Epics 19, 20) | 35.0 hrs | €2,975.00 | €50.00 | **€3,025.00** | **€50.00** |
| **M3** | Confidence-Interval Bandits (Epics 15–17) | 35.0 hrs | €2,975.00 | €50.00 | **€3,025.00** | **€50.00** |
| **M4** | Autonomy Benchmark Harness (Stories 9.1, 10.1)| 25.0 hrs | €2,125.00 | €50.00 | **€2,175.00** | **€50.00** |
| **M5** | Phase Close, Bayes Gate & Synthesis | 15.0 hrs | €1,275.00 | €25.00 | **€1,300.00** | **€25.00** |
| **Subtotal**| **Phase 1 Baseline Commitments** | **165.0 hrs** | **€14,025.00** | **€200.00** | **€14,225.00** | **€200.00** |
| **Cont.** | Contingency Reserve (15% Technical Buffer)| 25.0 hrs | €2,125.00 | €50.00 | **€2,175.00** | **€50.00** |
| **Total** | **Authorized Milestone Envelope** | **190.0 hrs** | **€16,150.00** | **€250.00** | **€16,400.00** | **€250.00** |

```
Milestone Cost Distribution (Economic Effort Valuation):
[ M0.5: €3,400 ] [ M1: €1.3k ] [ M2: €3.0k ] [ M3: €3.0k ] [ M4: €2.2k ] [ M5: €1.3k ] [ Reserve: €2.2k ]
```

---

## 2. Phase 1 Band B Total Scope Valuation (WBS Roll-Up)

Beyond the targeted serial milestone gates, the full scope of **Phase 1 Band B** comprises **31 user stories** across Epics 15–17, 19, and 20:

* **Total Band B Remaining Weighted Effort:** **115.4 person-days (692.4 focused hours)**.
* **Internal Economic Valuation:**
  $$\text{Band B Effort Value} = 692.4\text{ hours} \times €85.00/\text{hr} = \mathbf{€58,854.00}$$
* **Direct Cash Outlay:** **€0.00** payroll / **≤ €250.00** total API tooling.

---

## 3. Sourcing Justification & Cost Avoidance (Make-or-Buy Link)

In accordance with [Procurement-Management-Plan.md](../../Procurement-Management-Plan.md) §2.3, the project evaluated commercial external sourcing prior to locking these baseline estimates:

| Cost Element | Option A: Internal Sourcing (Baseline) | Option B: External Contractor Sourcing | Variance / Net Cost Avoidance |
| :--- | :---: | :---: | :---: |
| **Direct Engineering Labor** | **€0.00** cash (€58,854 shadow) | **€124,632.00** cash (115.4d $\times$ 8h $\times$ €135/h) | **+€124,632.00 savings** |
| **Contract & Vendor Management** | **€0.00** | **€18,695.00** cash (15% vendor overhead) | **+€18,695.00 savings** |
| **Developer Tooling & Cloud APIs** | **€250.00** cash | **€1,200.00** cash (contractor tool licenses) | **+€950.00 savings** |
| **Total Project Cash Outlay** | **€250.00** | **€144,527.00** | **+€144,277.00 Net Savings** |

**Conclusion:** The internal "Make" sourcing strategy is foundationally justified, eliminating over **€144,000.00** in commercial cash outlays while preserving 100% standard library purity and repo-internal knowledge retention.
