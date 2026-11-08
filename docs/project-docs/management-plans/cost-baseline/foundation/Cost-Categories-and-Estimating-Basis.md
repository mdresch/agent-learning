---
artifact_id: cost-foundation-categories-estimating-basis
parent_plan_id: cost-management
baseline_id: PMP-BL-v1.1.0
route: foundation_artifact
governance_policy: approve-subsidiary-plan
substage: "6.D-1"
version: "2.0.0"
owner_role: "Project Manager"
depends_on:
  - scope-management
  - schedule-management
approval_status: approved
pmbok_process: "Plan Financial Management"
---

# Cost Foundation — Cost Categories & Estimating Basis (`PMP-BL-v1.1.0`)

Defines the units of measure, precision standards, and Cost Breakdown Structure (CBS) for **Phase 2: Autonomous Feedback Loops & Extensible Architecture**.

**Historical Baseline Archive:** Frozen Phase 1 estimating basis preserved in [`docs/project-docs/history/PMP-BL-v1.0.0/management-plans/cost-baseline/foundation/Cost-Categories-and-Estimating-Basis.md`](../../history/PMP-BL-v1.0.0/management-plans/cost-baseline/foundation/Cost-Categories-and-Estimating-Basis.md).

---

## 1. Units of Measure, Precision & Currency Standards (Phase 2)

* **Effort Units:** **Person-Day (pd)** (6 focused engineering hours) and **Hours (hrs)**.
* **Financial Currency:** **Euros (€)**. Model API billings incurred in USD converted at €1.00 = $1.08 USD.
* **Precision Levels:** Effort rounded to 0.1 pd (0.5 hrs); cash expenses reported to exact euro.

---

## 2. Phase 2 Cost Breakdown Structure (CBS)

| Category ID | Category Name | Scope Description | Measurement Basis | Phase 2 Cash Outlay | Phase 2 Economic Valuation |
|---|---|---|---|:---:|:---:|
| **CAT-LAB** | Internal Maintainer Labor | Engineering, testing, architecture, and governance by Menno Drescher. | 120–160 hrs (30.0 pd) $\times$ €85.00/hr shadow rate. | **€0.00**<br/>(Maintainer equity) | **€10,200.00–€13,600.00**<br/>(Economic value delivered) |
| **CAT-EXT** | External Contractors | Third-party consultants or temporary software contractors. | Invoiced contractor hours. | **€0.00**<br/>(Strictly prohibited) | **€0.00**<br/>(100% Make sourcing) |
| **CAT-CLD** | Cloud Services & AI APIs | Antigravity AI pair programming and regression evaluation API endpoints. | Monthly usage billing invoices (capped at €100/mo). | **≤ €250.00**<br/>(Hard cash ceiling) | **€250.00** |
| **CAT-HW** | Host Compute & Tooling | Workstation compute, local file-based telemetry storage. | Sunk hardware & local storage. | **€0.00** | **€0.00** |
| **CAT-CONT**| Contingency Reserve | Known-unknown risk buffers (CR-P2-01..03, 12.5 pd). | 12.5 pd $\times$ €85/hr + €50 API buffer. | **€50.00** | **€6,425.00** |
| **CAT-MGMT**| Management Reserve | Unknown-unknown risks & Sponsor close-out (SR-P2-M10, 5.0 pd). | 5.0 pd (30.0 hrs) $\times$ €85/hr. | **€0.00** | **€2,550.00** |

**Total Phase 2 Financial Envelope:** **Cash Outlay Ceiling: $\le €300.00$** | **Economic Value Valuation: €19,175.00–€22,575.00**.
