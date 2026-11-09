---
artifact_id: scope-foundation-project-scope-statement
parent_plan_id: scope-management
baseline_id: PMP-BL-v1.1.0
route: foundation_artifact
governance_policy: approve-subsidiary-plan
substage: "6.A-1"
version: "2.0.0"
owner_role: "Project Manager"
depends_on: []
approval_status: approved
pmbok_process: "Define Scope"
---

# Scope Foundation — Project Scope Statement (`PMP-BL-v1.1.0`)

**PMBOK 8 Scope Performance Domain** §2.2 — **Define Scope**. Approved scope statement for `PMP-BL-v1.1.0`, traced to [Project-Charter.md](../../../Project-Charter.md) v2.0 Phase 2 *Autonomous Feedback Loops & Extensible Architecture*.

**Historical Baseline Archive:** Frozen Phase 1 scope statement preserved in [`docs/project-docs/history/PMP-BL-v1.0.0/management-plans/scope-baseline/foundation/Scope-Project-Scope-Statement.md`](../../history/PMP-BL-v1.0.0/management-plans/scope-baseline/foundation/Scope-Project-Scope-Statement.md).

**Topic pillars:** See [Scope-Pillar-Overview-and-Trace.md](Scope-Pillar-Overview-and-Trace.md) for the nine pillars from [Project-Pillars.md](../../../Project-Pillars.md) mapped to Phase 2 WBS bands and milestones. Phase 2 executes **critique-to-evidence conversion** (Pillar 2, Epic 14), **DPO pairwise preference optimization** (Pillars 3 & 5, Epic 18), **contextual authority ensemble routing** (Pillars 6 & 7, Epics 16 & 21), and **closed-loop SIDPA adaptation** (Pillar 1, Epics 22 & 38).

---

## 1. Charter Objectives (Phase 2)

1. **Critique Ingestion Engine (M6, HYP-AL-005):** Deterministic tag grammar and exact support shift engine converting qualitative code reviews into structured Bayesian evidence frames without guessing.
2. **DPO Pairwise Optimization (M7, HYP-AL-018):** Offline Bradley-Terry and DPO loss optimization for discrete policies without heavy GPU hardware.
3. **Contextual Authority Routing (M8, HYP-AL-016):** Contextual multi-armed bandit routing with deterministic Wilson lower bounds across authority tiers.
4. **Cognitive Feedback Automation (M9, HYP-AL-025):** Closed-loop intent refinement triggers and packaged contextual policy export.
5. **Upstream Fork Collision Protection Architecture (M6–M10, HYP-AL-026):** Complete isolation of all Phase 2 extensions in `agent-training-ext/`, maintaining `src/agent_learning` as 0 lines diff against upstream `microsoft/agent-learning` HEAD.

---

## 2. In-Scope Deliverables (Phase 2 Modules)

| Anchor / Milestone | Deliverable ID | Technical Deliverable Description | Acceptance Criteria |
|---|---|---|---|
| **M6** | **DEL-P2-01** | Tag Grammar Specification & Parser (`agent-training-ext/critique_evidence.py`) | Pure stdlib; parses valid tags; provides line-numbered syntax diagnostics. |
| **M6** | **DEL-P2-02** | Exact Pooled Support Shift Engine (`agent-training-ext/critique_evidence.py`) | Shift $|\Delta s_{\text{pooled}} - \delta| \le 10^{-9}$ measured via `DecisionResolver.resolve()`. |
| **M6** | **DEL-P2-03** | Critique Episode Metadata Serializer | Attaches adjustments to `Episode.metadata["critique_adjustments"]`; survives JSON round-trip. |
| **M7** | **DEL-P2-04** | Pairwise DPO Loss Engine (`agent-training-ext/dpo_preference.py`) | $\ge 30\%$ sample efficiency over uniform exploration on review corpora. |
| **M8** | **DEL-P2-05** | Contextual Authority Router (`agent-training-ext/ensemble_router.py`) | Deterministic Wilson lower bounds routing between `low` and `full` authority tiers. |
| **M9** | **DEL-P2-06** | Continuous SIDPA Loop Integration | Automated execution of Stages 12–18 maintaining 0 drift rows in `phase_rollup.py --check`. |
| **M6–M10** | **DEL-P2-07** | Fork-Isolated Extension Workspace (`agent-training-ext/`) | `src/agent_learning` diff against upstream Microsoft HEAD remains 0 lines. |
| **M10** | **DEL-P2-08** | Phase 2 Close Decision Package (`PCD-Phase2`) | Formal close package certifying M6–M10 completion and baselining `PMP-BL-v1.1.0`. |

---

## 3. Mandatory Out-of-Scope (Phase 2)

* **Direct Modification of `src/agent_learning/`:** Core upstream files are never modified for extension features.
* **Deep Neural Network Fine-Tuning & GPU Hardware:** No CUDA, PyTorch, TensorFlow, or GPU dependencies; strictly frozen-model, CPU-only, pure standard library algorithms.
* **Unconstrained Natural Language Processing:** Zero stochastic LLM parsing of review critiques; deterministic tag grammar required.
* **Modifying Phase 1 Historical Baseline Archives:** Historical files in `docs/project-docs/history/` are strictly immutable.
* **Standalone Web Servers or Relational Databases:** Zero FastAPI/Uvicorn hosting, zero SQLite/PostgreSQL schemas.

---

## 4. Execution Authorization Bands (Phase 2)

| Band | Epics (indicative) | Authorization Status | Phase 2 Execution Policy |
| --- | --- | --- | --- |
| **A — Foundation** | 1–7, 9–13, 36 | **Completed & Closed** | Maintained as frozen foundation. |
| **B — Phase 1 Product** | 15, 17, 19, 20 | **Completed & Closed** | Certified via `PCD-20261106-001`. |
| **C — Phase 2 Option B** | 14, 18 | **AUTHORIZED FOR PHASE 2** | Implement in `agent-training-ext/` (M6, M7). |
| **D — Learning Backlog** | 16, 21, 22, 38 | **AUTHORIZED FOR PHASE 2** | Implement in `agent-training-ext/` (M8, M9). |
| **E — PMBOK Machinery** | 25–35, 37 | **Active Governance** | Program scope; maintained continuously. |
| **F — Close & Governance** | M10, PCD-Phase2 | **Authorized Gate** | Formal phase close package. |

---

## 5. Milestone to WBS Trace (Phase 2)

| Milestone | Charter Intent | Primary WBS Anchor | Delivery Target |
|---|---|---|---|
| **M6** | Critique-to-Evidence Ingestion (Epic 14) | Stories 14.1–14.6 | `agent-training-ext/critique_evidence.py` |
| **M7** | DPO Preference Optimization (Epic 18) | Epic 18 Stories | `agent-training-ext/dpo_preference.py` |
| **M8** | Contextual Authority Routing (Epics 16, 21) | Epics 16, 21 Stories | `agent-training-ext/ensemble_router.py` |
| **M9** | Continuous SIDPA Automation (Epics 22, 38) | Epics 22, 38 Stories | Automated Stage 12–18 loop |
| **M10** | Phase 2 Review & Close Gate Adjudication | Formal Close Gate | `PCD-Phase2` package |
