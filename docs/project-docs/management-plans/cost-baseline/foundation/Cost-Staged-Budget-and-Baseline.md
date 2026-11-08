---
artifact_id: cost-foundation-staged-budget-baseline
parent_plan_id: cost-management
baseline_id: PMP-BL-v1.1.0
route: foundation_artifact
governance_policy: approve-subsidiary-plan
substage: "6.D-3"
version: "2.0.0"
owner_role: "Project Manager"
depends_on:
  - scope-management
  - schedule-management
approval_status: approved
pmbok_process: "Develop Budget"
---

# Cost Foundation — Staged Budget & Cost Baseline (`PMP-BL-v1.1.0`)

Establishes the time-phased **Cost Baseline**, staged funding releases, and reserve boundaries for **Phase 2: Autonomous Feedback Loops & Extensible Architecture**.

**Historical Baseline Archive:** Frozen Phase 1 budget baseline preserved in [`docs/project-docs/history/PMP-BL-v1.0.0/management-plans/cost-baseline/foundation/Cost-Staged-Budget-and-Baseline.md`](../../history/PMP-BL-v1.0.0/management-plans/cost-baseline/foundation/Cost-Staged-Budget-and-Baseline.md).

---

## 1. Phase 2 Reserve Architecture & Budget Partitioning

In accordance with PMBOK 8 Figure 2-25:

```
+-----------------------------------------------------------------------------------+
|                        TOTAL PHASE 2 BUDGET: €21,725.00                           |
|  +-------------------------------------------------------------+  +--------------+|
|  |                 COST BASELINE: €19,175.00                   |  |  MANAGEMENT  ||
|  |  +-------------------------------------+  +-----------------+  |   RESERVE    ||
|  |  |    WORK PACKAGE ESTIMATES (M6-M10)   |  |   CONTINGENCY   |  |   (5.0 pd)   ||
|  |  |              €15,300.00             |  |     RESERVE     |  |  €2,550.00   ||
|  |  |    (180.0 hrs labor + €250 API cash)|  |   (12.5 pd)     |  |  (Sponsor    ||
|  |  |                                     |  |    €3,875.00    |  |   Controlled)||
|  |  +-------------------------------------+  +-----------------+  +--------------+|
|  +-------------------------------------------------------------+                  |
+-----------------------------------------------------------------------------------+
```

---

## 2. Staged Funding Release Schedule (Phase 2 Milestones)

| Milestone Stage | Planned Scope | Planned Labor Effort | Cash OpEx Envelope | Cumulative Cash Released | Cumulative Economic Valuation |
|---|---|:---:|:---:|:---:|:---:|
| **Stage 8 Authorization** | Baseline Formalization & Setup | — | €50.00 | €50.00 | €0.00 |
| **Milestone M6** | Critique Ingestion Engine (Epic 14) | 7.5 pd (45h) | €50.00 | €100.00 | €3,875.00 |
| **Milestone M7** | DPO Pairwise Optimization (Epic 18) | 6.5 pd (39h) | €50.00 | €150.00 | €7,240.00 |
| **Milestone M8** | Contextual Ensembles (Epics 16, 21) | 8.0 pd (48h) | €50.00 | €200.00 | €11,370.00 |
| **Milestone M9** | Continuous SIDPA & Packages (22, 38)| 5.5 pd (33h) | €50.00 | €250.00 | €14,225.00 |
| **Milestone M10** | Phase 2 Review & Close Gate | 2.5 pd (15h) | €0.00 | €250.00 | €15,550.00 |
| **Contingency Reserve**| Technical Risk Buffer (CR-P2-01..03)| 12.5 pd | €50.00 buffer | €300.00 max | €19,175.00 (Baseline) |

**Cost Baseline Rule:** Cash disbursement is capped strictly at **$\le €100.00/\text{month}$** and **$\le €300.00$** total Phase 2 outlay.
