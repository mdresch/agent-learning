---
artifact_id: resource-foundation-capacity-estimates
parent_plan_id: resource-management
baseline_id: PMP-BL-v1.1.0
route: foundation_artifact
governance_policy: approve-subsidiary-plan
substage: "6.C-2"
version: "2.0.0"
owner_role: "Project Manager"
depends_on:
  - scope-management
  - schedule-management
approval_status: approved
pmbok_process: "Estimate Resources"
---

# Resource Foundation — Capacity Estimates & Workload Modeling (`PMP-BL-v1.1.0`)

This artifact satisfies PMBOK 8 §2.6.2 *Estimate Resources* for the Phase 2 Resource Management Plan. It reconciles maintainer capacity against the Phase 2 Schedule Baseline ([Schedule-Gantt-Phase2.md](../../schedule-baseline/foundation/Schedule-Gantt-Phase2.md)) across Milestones M6 through M10.

**Historical Baseline Archive:** Frozen Phase 1 capacity estimates preserved in [`docs/project-docs/history/PMP-BL-v1.0.0/management-plans/resource-baseline/foundation/Resource-Capacity-Estimates.md`](../../history/PMP-BL-v1.0.0/management-plans/resource-baseline/foundation/Resource-Capacity-Estimates.md).

---

## 1. Capacity Modeling Basis (Phase 2)

### 1.1 Planning Units & Availability
* **Unit of Effort:** **Person-Day (pd)**, defined as approximately **6 focused engineering hours**.
* **Human Maintainer Commitment:** **120–160 engineering hours** (20.0–26.7 pd) across Milestones M6–M10 committed by Project Sponsor Menno Drescher (Charter v2.0 §4).
* **AI Pair Acceleration:** Lead Agent Engineer (Antigravity) provides high-throughput test authoring, pure stdlib implementation, and AST parsing, accelerating effective throughput by $\approx 2.5\times$.
* **Pacing Model:** Velocity-driven and milestone-gated; not bound to rigid calendar deadlines.

### 1.2 Phase 2 Workload vs. Maintainer Capacity Allocation

| Milestone ID | Target Epics / Work Packages | Maintainer Effort (pd) | Planned Hours | Feasibility & Sourcing Notes |
|:---:|---|:---:|:---:|---|
| **M6** | Epic 14 (Critique Ingestion Engine) | 7.5 | 45.0 | High feasibility; Stories 14.1–14.4 pre-verified in `temp/`. |
| **M7** | Epic 18 (DPO Pairwise Optimization) | 6.5 | 39.0 | Feasible; discrete policy formulation avoids GPU compute. |
| **M8** | Epics 16 & 21 (Contextual Authority Ensembles) | 8.0 | 48.0 | Multi-armed router with deterministic Wilson bounds. |
| **M9** | Epics 22 & 38 (Continuous SIDPA & Packaging) | 5.5 | 33.0 | Automated stage runners and self-contained exports. |
| **M10** | Formal Close Gate (`PCD-Phase2`) | 2.5 | 15.0 | Regression, upstream clean diff verification, close package. |
| **Reserve** | Milestone M10 Contingency Buffer | 5.0 | 30.0 | Management reserve `SR-P2-M10` for unanticipated integration friction. |

**Total Phase 2 Demand:** **30.0 person-days** (180 focused hours), perfectly aligning with maintainer capacity augmented by AI pair programming throughput.
