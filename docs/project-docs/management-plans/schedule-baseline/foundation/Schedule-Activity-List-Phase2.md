---
artifact_id: schedule-foundation-activity-list-phase2
parent_plan_id: schedule-management
baseline_id: PMP-BL-v1.1.0
route: foundation_artifact
governance_policy: approve-subsidiary-plan
substage: "6.B-2A"
version: "2.0.0"
owner_role: "Project Manager"
depends_on:
  - scope-management
approval_status: approved
pmbok_process: "Develop Schedule"
---

# Schedule Foundation — Phase 2 Activity List & Dependencies (`PMP-BL-v1.1.0`)

Story-level **activity list**, **predecessors**, and **durations** for Charter Phase 2 *Autonomous Feedback Loops & Extensible Architecture* (Scope Bands **C** and **D**). Governs execution across Milestones **M6 through M10**.

**Historical Baseline Archive:** Frozen Phase 1 activity list preserved in [`docs/project-docs/history/PMP-BL-v1.0.0/management-plans/schedule-baseline/foundation/Schedule-Activity-List-Phase1.md`](../../history/PMP-BL-v1.0.0/management-plans/schedule-baseline/foundation/Schedule-Activity-List-Phase1.md).

---

## 1. Charter Gate Activities (Phase 2 Milestones)

| Activity ID | Milestone / Gate Name | Band | Description | Predecessor(s) | Dur (M pd) | Critical Path? |
|---|---|:---:|---|---|:---:|:---:|
| **M6** | **Critique Ingestion Engine Gate** | C | Stories 14.1–14.6 complete; 32 review records replayed | 14.6 | 0 | Yes |
| **M7** | **DPO Pairwise Optimization Gate** | C | Stories 18.1–18.6 complete; DPO loss verified | M6, 18.6 | 0 | Yes |
| **M8** | **Contextual Authority Routing Gate** | D | Epics 16 & 21 complete (Stories 16.1–16.6, 21.1–21.7); multi-armed router operational | M7, 21.7 | 0 | Yes |
| **M9** | **Continuous SIDPA Automation Gate** | D | Epics 22 & 38 complete (Stories 22.1–22.7, 38.1–38.6); automated loop verified | M8, 22.7, 38.6 | 0 | Yes |
| **M10** | **Phase 2 Close & PCD Gate** | F | Full regression green; 0 upstream diff; `PCD-Phase2` approved | M9, 10.3 | 0 | Yes |

---

## 2. Story Activities — Epic 14 (Milestone M6: Critique Ingestion)

All modules deployed strictly inside `agent-training-ext/` under Upstream Fork Collision Protection constraints (Source: ADR-014, BRD-014, FDD-014):

| Activity | Title | Band | Predecessor(s) | Dur (M pd) | Target Module |
|---|---|:---:|---|:---:|---|
| **14.1** | Tag Grammar Specification & Parser | C | Stage 8 Gate | 1.5 | `agent-training-ext/critique_evidence.py` |
| **14.2** | Delta Rubric Table & Exact Pooled Shift Engine | C | 14.1 | 1.5 | `agent-training-ext/critique_evidence.py` |
| **14.3** | Doubt Calculation & Option Applicator | C | 14.2 | 1.0 | `agent-training-ext/critique_evidence.py` |
| **14.4** | Critique Episode Metadata Serializer | C | 14.3 | 1.0 | `agent-training-ext/critique_evidence.py` |
| **14.5** | Critique Tagging CLI & Pre-Calibrated Tags | C | 14.4 | 1.0 | `agent-training-ext/cli.py` |
| **14.6** | Review Replay Benchmark & Ingestion Harness | C | 14.5 | 1.5 | `agent-training-ext/tests/` |

---

## 3. Story Activities — Epic 18 (Milestone M7: DPO Preference Optimization)

Pairwise discrete preference optimization without GPU compute (Source: ADR-018, BRD-018, FDD-018):

| Activity | Title | Band | Predecessor(s) | Dur (M pd) | Target Module |
|---|---|:---:|---|:---:|---|
| **18.1** | Pairwise Preference Dataset Pipeline (Pairs From Episodes) | C | M6 | 1.5 | `agent-training-ext/dpo_preference.py` |
| **18.2** | Bradley-Terry Formulation & Discrete DPO Loss & Gradient | C | 18.1 | 1.5 | `agent-training-ext/dpo_preference.py` |
| **18.3** | Offline Policy Optimization Loop & Convergent Fit | C | 18.2 | 1.0 | `agent-training-ext/dpo_preference.py` |
| **18.4** | Discrete DPO Policy Learner Class | C | 18.3 | 1.0 | `agent-training-ext/dpo_preference.py` |
| **18.5** | Pipeline Execution Through Policy Runner | C | 18.4 | 0.5 | `agent-training-ext/dpo_preference.py` |
| **18.6** | Real-Data Check & Empirical Efficiency Benchmark | C | 18.5 | 1.0 | `agent-training-ext/tests/` |

---

## 4. Story Activities — Epics 16 & 21 (Milestone M8: Contextual Authority Routing)

Contextual ensemble routing and deterministic Wilson bound gating (Source: ADR-016, ADR-021, BRD-016, BRD-021, FDD-016, FDD-021):

| Activity | Title | Band | Predecessor(s) | Dur (M pd) | Target Module |
|---|---|:---:|---|:---:|---|
| **16.1** | Deterministic UCB Scoring Formulation | D | M7 | 0.5 | `agent-training-ext/ensemble_router.py` |
| **16.2** | Deterministic Action Selection Engine | D | 16.1 | 0.5 | `agent-training-ext/ensemble_router.py` |
| **16.3** | Contextual Statistics Snapshot Serialization | D | 16.2 | 0.5 | `agent-training-ext/ensemble_router.py` |
| **16.4** | Idempotent Episode Count Verification | D | 16.3 | 0.5 | `agent-training-ext/ensemble_router.py` |
| **16.5** | REINFORCE Isolation Boundary | D | 16.4 | 0.5 | `agent-training-ext/ensemble_router.py` |
| **16.6** | Deterministic Positive-Only Autonomy Check | D | 16.5 | 0.5 | `agent-training-ext/tests/` |
| **21.1** | Entropy and Margin Boundary Extraction | D | 16.6 | 1.0 | `agent-training-ext/ensemble_router.py` |
| **21.2** | Multi-Armed Authority Routing Dispatcher | D | 21.1 | 1.0 | `agent-training-ext/ensemble_router.py` |
| **21.3** | Pinned Autonomy Gate Evaluation | D | 21.2 | 0.5 | `agent-training-ext/ensemble_router.py` |
| **21.4** | Shadow Evaluation Record & Agreement Gate | D | 21.3 | 0.5 | `agent-training-ext/ensemble_router.py` |
| **21.5** | Human Promotion Seeding & Threshold Transition | D | 21.4 | 1.0 | `agent-training-ext/ensemble_router.py` |
| **21.6** | Dispatch Isolation & Gradient Exclusion | D | 21.5 | 0.5 | `agent-training-ext/ensemble_router.py` |
| **21.7** | Zero-Traffic Real-Data Fallback Verification | D | 21.6 | 0.5 | `agent-training-ext/tests/` |

---

## 5. Story Activities — Epics 22 & 38 (Milestone M9: Continuous SIDPA & Packages)

Continuous SIDPA loop automation and packaged contextual policy exports (Source: ADR-022, ADR-038, BRD-022, BRD-038, FDD-022, FDD-038):

| Activity | Title | Band | Predecessor(s) | Dur (M pd) | Target Module |
|---|---|:---:|---|:---:|---|
| **22.1** | Weight Vector Scoring With Real Resolver | D | M8 | 0.5 | `scripts/orchestrate_pmbok.py` |
| **22.2** | Dataset Split and Label Rules | D | 22.1 | 0.5 | `scripts/phase_rollup.py` |
| **22.3** | Coordinate Ascent Weight Optimization | D | 22.2 | 0.5 | `scripts/orchestrate_pmbok.py` |
| **22.4** | Monotonic Improvement Filter | D | 22.3 | 0.5 | `scripts/orchestrate_pmbok.py` |
| **22.5** | Frozen Weight Application Pipeline | D | 22.4 | 0.5 | `scripts/orchestrate_pmbok.py` |
| **22.6** | Human Decision Adoption Gate | D | 22.5 | 0.5 | `docs/governance/decisions/` |
| **22.7** | Real-Data Regression Harness | D | 22.6 | 0.5 | `tests/` |
| **38.1** | Weight-Row Contextual Feature Update | D | M8 | 0.5 | `agent-training-ext/packaging.py` |
| **38.2** | Contextual Skipped Episode Accounting | D | 38.1 | 0.25 | `agent-training-ext/packaging.py` |
| **38.3** | Unified Learner & Policy Class Structure | D | 38.2 | 0.5 | `agent-training-ext/packaging.py` |
| **38.4** | Initializer Dynamic Contextual Policy Creation | D | 38.3 | 0.25 | `agent-training-ext/packaging.py` |
| **38.5** | Decision Feature List Enforcement | D | 38.4 | 0.5 | `agent-training-ext/packaging.py` |
| **38.6** | Scalar Isolation & Weight-Row Immutability | D | 38.5 | 0.5 | `agent-training-ext/tests/` |

---

## 6. Milestone M10: Phase Close Activities

| Activity | Title | Band | Predecessor(s) | Dur (M pd) | Target Deliverable |
|---|---|:---:|---|:---:|---|
| **10.1** | Complete Test Suite Regression & Zero-Drift Audit | F | M9 | 1.0 | Full CI Green |
| **10.2** | Upstream Microsoft Pristine Fork Verification | F | 10.1 | 0.5 | `git diff upstream/main` = 0 |
| **10.3** | Phase 2 Close Decision Package Authoring (`PCD-Phase2`) | F | 10.2 | 1.0 | `docs/governance/decisions/` |
