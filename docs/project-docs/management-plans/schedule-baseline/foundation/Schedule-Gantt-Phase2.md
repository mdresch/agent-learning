---
artifact_id: schedule-foundation-gantt-phase2
parent_plan_id: schedule-management
baseline_id: PMP-BL-v1.1.0
route: foundation_artifact
governance_policy: approve-subsidiary-plan
substage: "6.B-2B"
version: "2.0.0"
owner_role: "Project Manager"
depends_on:
  - scope-management
approval_status: approved
pmbok_process: "Develop Schedule"
---

# Schedule Foundation — Phase 2 Gantt & CPM Schedule (`PMP-BL-v1.1.0`)

Bar chart schedule view for **Charter Phase 2: Autonomous Feedback Loops & Extensible Architecture** (Scope Bands **C** and **D**).

**Historical Baseline Archive:** Frozen Phase 1 Gantt preserved in [`docs/project-docs/history/PMP-BL-v1.0.0/management-plans/schedule-baseline/foundation/Schedule-Gantt-Phase1.md`](../../history/PMP-BL-v1.0.0/management-plans/schedule-baseline/foundation/Schedule-Gantt-Phase1.md).

---

## 1. Calendar Conventions (Phase 2 Planning Model)

| Parameter | Planning Value |
|---|---|
| **T0 (Planning Anchor)** | **2026-11-09** (Indicative dependency-sequenced anchor) |
| **Capacity Assumption** | **5 person-days (pd) / calendar week** (~6 hours per pd) |
| **Total Phase 2 Effort** | **25.0–30.0 person-days** (150–180 engineering hours) |
| **Critical Path Sequence** | **M6 (Critique) $\to$ M7 (DPO) $\to$ M8 (Contextual) $\to$ M9 (SIDPA) $\to$ M10 (Close)** |

---

## 2. CPM Forward Pass & Milestone Schedule Table

| Activity ID | Activity Title | Dur (M pd) | ES (pd) | EF (pd) | Critical? | Planned Start | Planned Finish |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **14.1** | Tag Grammar Parser | 1.5 | 0.0 | 1.5 | Yes | 2026-11-09 | 2026-11-10 |
| **14.2** | Delta Rubric & Exact Shift Engine | 1.5 | 1.5 | 3.0 | Yes | 2026-11-11 | 2026-11-12 |
| **14.3** | Doubt Calculation & Option Applicator | 1.0 | 3.0 | 4.0 | Yes | 2026-11-13 | 2026-11-13 |
| **14.4** | Critique Episode Metadata Serializer | 1.0 | 4.0 | 5.0 | Yes | 2026-11-16 | 2026-11-16 |
| **14.5** | Critique Tagging CLI Integration | 1.0 | 5.0 | 6.0 | Yes | 2026-11-17 | 2026-11-17 |
| **14.6** | Review Replay Benchmark & Harness | 1.5 | 6.0 | 7.5 | Yes | 2026-11-18 | 2026-11-19 |
| **M6** | **Milestone M6 Gate Join** | **0.0** | **7.5** | **7.5** | **Yes** | **2026-11-19** | **2026-11-19** |
| **18.1** | Pairwise Preference Dataset Pipeline | 1.5 | 7.5 | 9.0 | Yes | 2026-11-20 | 2026-11-23 |
| **18.2** | Discrete Policy DPO Loss Engine | 2.0 | 9.0 | 11.0 | Yes | 2026-11-24 | 2026-11-25 |
| **18.3** | Offline Policy Optimization Loop | 1.5 | 11.0 | 12.5 | Yes | 2026-11-26 | 2026-11-27 |
| **18.4** | Sample Efficiency Benchmark vs Exploration | 1.5 | 12.5 | 14.0 | Yes | 2026-11-30 | 2026-12-01 |
| **M7** | **Milestone M7 Gate Join** | **0.0** | **14.0** | **14.0** | **Yes** | **2026-12-01** | **2026-12-01** |
| **16.1** | Contextual Feature Extraction | 1.5 | 14.0 | 15.5 | Yes | 2026-12-02 | 2026-12-03 |
| **16.2** | Wilson Lower Bound Ensemble | 1.5 | 15.5 | 17.0 | Yes | 2026-12-04 | 2026-12-07 |
| **21.1** | Multi-Armed Authority Router Dispatcher | 2.0 | 17.0 | 19.0 | Yes | 2026-12-08 | 2026-12-09 |
| **21.2** | Boundary Fallback Engine | 1.5 | 19.0 | 20.5 | Yes | 2026-12-10 | 2026-12-11 |
| **21.5** | Contextual Authority Benchmark Harness | 1.5 | 20.5 | 22.0 | Yes | 2026-12-14 | 2026-12-15 |
| **M8** | **Milestone M8 Gate Join** | **0.0** | **22.0** | **22.0** | **Yes** | **2026-12-15** | **2026-12-15** |
| **22.1** | Automated Loop Pipeline Runner | 1.5 | 22.0 | 23.5 | Yes | 2026-12-16 | 2026-12-17 |
| **22.2** | Adaptation Trigger Integration | 1.5 | 23.5 | 25.0 | Yes | 2026-12-18 | 2026-12-21 |
| **38.1** | Packaged Contextual Policy Exporter | 1.5 | 22.0 | 23.5 | No | 2026-12-16 | 2026-12-17 |
| **38.2** | Self-Contained Runtime Importer | 1.0 | 23.5 | 24.5 | No | 2026-12-18 | 2026-12-18 |
| **22.4** | Governance Loop Replay Validation | 1.5 | 25.0 | 26.5 | Yes | 2026-12-22 | 2026-12-23 |
| **M9** | **Milestone M9 Gate Join** | **0.0** | **26.5** | **26.5** | **Yes** | **2026-12-23** | **2026-12-23** |
| **10.1** | Full Test Suite Regression & Drift Audit | 1.0 | 26.5 | 27.5 | Yes | 2026-12-24 | 2026-12-24 |
| **10.2** | Upstream Microsoft Fork Diff Verification | 0.5 | 27.5 | 28.0 | Yes | 2026-12-28 | 2026-12-28 |
| **10.3** | Phase 2 Close Decision Package (`PCD-Phase2`) | 1.0 | 28.0 | 29.0 | Yes | 2026-12-29 | 2026-12-30 |
| **M10** | **Milestone M10 Phase Close Gate** | **0.0** | **29.0** | **29.0** | **Yes** | **2026-12-30** | **2026-12-30** |

Total critical path duration: **29.0 person-days** (~5.8 calendar weeks).
