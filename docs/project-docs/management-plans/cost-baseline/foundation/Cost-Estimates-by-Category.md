---
artifact_id: cost-foundation-estimates-by-category
parent_plan_id: cost-management
baseline_id: PMP-BL-v1.1.0
route: foundation_artifact
governance_policy: approve-subsidiary-plan
substage: "6.D-2"
version: "2.0.0"
owner_role: "Project Manager"
depends_on:
  - scope-management
  - schedule-management
approval_status: approved
pmbok_process: "Estimate Costs"
---

# Cost Foundation — Cost Estimates by Category & Milestone (`PMP-BL-v1.1.0`)

Provides bottom-up cost estimates mapped across **Phase 2 Milestones M6 through M10**, reconciling maintainer labor, AI pair programming endpoints, and tooling cash envelopes.

**Historical Baseline Archive:** Frozen Phase 1 estimates preserved in [`docs/project-docs/history/PMP-BL-v1.0.0/management-plans/cost-baseline/foundation/Cost-Estimates-by-Category.md`](../../history/PMP-BL-v1.0.0/management-plans/cost-baseline/foundation/Cost-Estimates-by-Category.md).

---

## 1. Milestone Cost Breakdown (Phase 2 Milestones M6–M10)

| Milestone ID | Deliverable Scope & Milestone Theme | Baseline Effort (hrs) | Labor Valuation (€85/h) | External AI API Quota (€) | Total Economic Valuation (€) | Cash Outlay Required (€) |
|:---:|---|:---:|:---:|:---:|:---:|:---:|
| **M6** | Critique Ingestion Engine (Epic 14) | 45.0 hrs (7.5 pd) | €3,825.00 | €50.00 | **€3,875.00** | **€50.00** |
| **M7** | DPO Preference Optimization (Epic 18) | 39.0 hrs (6.5 pd) | €3,315.00 | €50.00 | **€3,365.00** | **€50.00** |
| **M8** | Contextual Ensembles (Epics 16, 21) | 48.0 hrs (8.0 pd) | €4,080.00 | €50.00 | **€4,130.00** | **€50.00** |
| **M9** | Continuous SIDPA & Packages (22, 38) | 33.0 hrs (5.5 pd) | €2,805.00 | €50.00 | **€2,855.00** | **€50.00** |
| **M10** | Phase 2 Review & Close Gate | 15.0 hrs (2.5 pd) | €1,275.00 | €50.00 | **€1,325.00** | **€50.00** |
| **Subtotal** | **Work Package Baseline Commitments** | **180.0 hrs (30.0 pd)** | **€15,300.00** | **€250.00** | **€15,550.00** | **€250.00** |
| **Contingency**| Technical Risk Buffer (CR-P2-01..03) | 75.0 hrs (12.5 pd) | €6,375.00 | €50.00 | **€6,425.00** | **€50.00** |
| **Total** | **Authorized Milestone Baseline Envelope**| **255.0 hrs (42.5 pd)** | **€21,675.00** | **€300.00** | **€21,975.00** | **€300.00** |

All custom code developed strictly within `agent-training-ext/` under 100% internal Make sourcing.
