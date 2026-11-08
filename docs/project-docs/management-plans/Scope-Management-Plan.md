---
plan_id: "scope-management"
plan_name: "Scope Management Plan"
pmbok_edition: "PMBOK 8"
pmbok_focus_area: "Planning"
primary_pmbok_domain: "Scope"
secondary_pmbok_domains:
  - "Governance"
legacy_process: "5.1 Plan Scope Management"
route: "full_plan"
generator: "llm"
version: "2.0.0"
baseline_id: "PMP-BL-v1.0.1"
target_baseline_id: "PMP-BL-v1.1.0"
owner_role: "Project Manager"
depends_on: []
foundation_pack: "docs/project-docs/management-plans/scope-baseline/Scope-Foundation-Pack-Manifest.md"
inputs:
  - "Project-Charter.md"
  - "docs/project-docs/Ideation-Document.md"
  - "docs/project-docs/Business-Case.md"
  - "docs/project-docs/Benefits-Management-Plan.md"
outputs:
  - "docs/project-docs/management-plans/Scope-Management-Plan.md"
  - "docs/project-docs/management-plans/scope-baseline/Scope-Foundation-Pack-Manifest.md"
  - "docs/project-docs/management-plans/scope-baseline/foundation/"
governance_policy: "approve-subsidiary-plan"
---

# Scope Management Plan — agent-learning Phase 2: Autonomous Feedback Loops & Extensible Architecture

> **PMBOK 8 Domain:** `Scope` (Planning Focus Area) | **Legacy Process:** `5.1 Plan Scope Management`  
> **Governance Policy:** `approve-subsidiary-plan` | **Lifecycle Stage:** `Stage 6 (Planning: Scope Baseline & Requirements)`  
> **Route:** `full_plan` | **Baseline Identifier:** `PMP-BL-v1.0.1` (targeting `PMP-BL-v1.1.0`)  
> **Foundation pack:** [Scope-Foundation-Pack-Manifest.md](scope-baseline/Scope-Foundation-Pack-Manifest.md) (Stage **6.A**, PMBOK §2.2)  
> **Accountable Role:** Project Manager / PMBOK Steward | **Approving Sponsor:** Menno Drescher  
> **Normative Standard:** [ADR-012](../../adr/ADR-012-subsidiary-management-plan-standards-and-content-contracts.md) and [ADR-025](../../adr/ADR-025-scope-management-plan-standard-and-baseline-contract.md)  
> **Charter alignment:** [Project-Charter.md](../Project-Charter.md) v2.0 — Phase 2 *Autonomous Feedback Loops & Extensible Architecture*  
> **Historical Baseline Archive:** Frozen Phase 1 snapshot preserved in [`docs/project-docs/history/PMP-BL-v1.0.0/management-plans/Scope-Management-Plan.md`](../history/PMP-BL-v1.0.0/management-plans/Scope-Management-Plan.md)  

For `PMP-BL-v1.1.0`, the **integrated scope baseline** = approved **[Scope-Foundation-Pack-Manifest.md](scope-baseline/Scope-Foundation-Pack-Manifest.md)** + approved **this plan** (v2.0.0). Phase 1 is formally **Closed** via `PCD-20261106-001`. Phase 2 scope operationalizes the transition from `PMP-BL-v1.0.1` to minor baseline `PMP-BL-v1.1.0`, covering **Option B (Epics 14, 18)**, **Contextual Routing & Ensembles (Epics 16, 21)**, and **Cognitive Feedback Loops (Epics 22, 38)** packaged cleanly inside `agent-training-ext/`.

---

## 1. Intent, Alignment & Boundaries

### 1.1 Core Mandate & Charter Traceability
This plan establishes scope mechanisms, verification gates, and boundaries for **Phase 2: Autonomous Feedback Loops & Extensible Architecture**.

Phase 2 objectives operationalize [Project-Charter.md](../Project-Charter.md) v2.0 §2, §3, and §6:
1. **Critique-to-Evidence Ingestion Engine (Epic 14):** Build a deterministic tag grammar and parser converting qualitative review feedback into Bayesian evidence frames, guaranteeing exact support shifts without guessing (`DEL-P2-01` through `DEL-P2-03`, `HYP-AL-005`, `BEN-P2-001`).
2. **DPO Pairwise Preference Optimization Engine (Epic 18):** Construct pairwise preference dataset pipelines and train discrete policy logits directly from preference comparisons offline without heavy GPU fine-tuning (`DEL-P2-04`, `HYP-AL-018`, `BEN-P2-002`).
3. **Contextual Authority Ensemble Routing & Deterministic UCB (Epics 16, 21):** Deploy multi-armed contextual routing with deterministic lower bounds across authority tiers (`DEL-P2-05`, `HYP-AL-016`, `BEN-P2-005`).
4. **Cognitive Feedback Loops & Packaged Contextual Learning (Epics 22, 38):** Establish closed-loop intent refinement triggers and export packaged contextual policies (`DEL-P2-06`, `HYP-AL-025`, `BEN-P2-003`).
5. **Upstream Fork Collision Protection Architecture:** Enforce strict isolation of custom extensions into `agent-training-ext/`, keeping core `src/agent_learning` untouched to guarantee conflict-free synchronization with upstream `microsoft/agent-learning` (`DEL-P2-07`, `HYP-AL-026`, `BEN-P2-004`).
6. **Decoupled Research Library (`LL-044`):** Ensure deep exploratory research remains housed in `docs/research/ideation/` without bloating governed lifecycle documents.

### 1.2 In-Scope Deliverables & Key Work Packages (Phase 2)
The authorized deliverables for Phase 2 are strictly bounded to:
* **DEL-P2-01 (Tag Grammar Specification & Deterministic Parser):** Pure stdlib parser (`agent-training-ext/critique_evidence.py`) for reviewer critique tags with line-numbered error diagnostics (Epic 14, Story 14.1).
* **DEL-P2-02 (Exact Pooled Support Shift & Doubt Applicator):** Mathematical applicator guaranteeing $|\Delta s_{\text{pooled}} - \delta| \le 10^{-9}$ measured via `DecisionResolver.resolve()` (Epic 14, Stories 14.2, 14.3).
* **DEL-P2-03 (Critique Episode Metadata Formatter):** Standard metadata serializer attaching critique adjustments to `Episode.metadata["critique_adjustments"]` (Epic 14, Story 14.4).
* **DEL-P2-04 (Pairwise DPO Loss Engine for Discrete Policies):** Bradley-Terry / DPO loss formulations for discrete policies achieving $\ge 30\%$ sample efficiency over online exploration (Epic 18).
* **DEL-P2-05 (Contextual Authority Ensemble Router):** Deterministic Wilson lower bounds routing between `low` and `full` authority tiers (Epics 16, 21).
* **DEL-P2-06 (Continuous SIDPA Automation Pipeline):** Automated execution of Stages 12–18 maintaining 0 drift rows in `phase_rollup.py --check` (Epics 22, 38).
* **DEL-P2-07 (Isolated `agent-training-ext` Package Structure):** Dedicated package workspace ensuring `src/agent_learning` diff against upstream Microsoft HEAD remains 0 lines.
* **DEL-P2-08 (Phase 2 Close Decision Package `PCD-Phase2`):** Formal close package certifying M6–M10 milestone completion.

### 1.3 Mandatory Out-of-Scope Boundaries (Phase 2)
To preserve architectural integrity and prevent scope creep:
* **Direct Modification of `src/agent_learning/`:** Zero custom model logic or non-upstream code in `src/agent_learning/`. Upstream files remain a pristine mirror of `microsoft/agent-learning`.
* **Deep Neural Network Fine-Tuning & GPU Dependencies:** Zero PyTorch, TensorFlow, CUDA, or GPU hardware requirements. All learning algorithms remain CPU-only, frozen-model, standard library only.
* **Unconstrained Natural Language Processing:** Zero stochastic, unconstrained LLM parsing. All critique ingestion requires deterministic grammar validation.
* **Modifying Phase 1 Historical Baseline Archives:** `docs/project-docs/history/PMP-BL-v1.0.0/` remains strictly immutable.
* **Standalone Database or Web Server Deployments:** Zero SQLite/PostgreSQL schemas or FastAPI/Uvicorn server hosting. The codebase remains an embeddable SDK and CLI tool.

---

### 1.4 PMBOK Input, Process & Output (IPO) Specification
In accordance with PMBOK® Guide 8th Edition (Scope Performance Domain §2.2):
* **Inputs (PMBOK 8 §2.2.2.1 & §4):**
  - **Project Charter (v2.0):** Phase 2 objectives, scope boundaries, fork protection directive, and milestones M6–M10 ([Project-Charter.md](../Project-Charter.md)).
  - **Business Documents:** Business Case v2.0 ([Business-Case.md](../Business-Case.md)), Benefits Management Plan v2.0 ([Benefits-Management-Plan.md](../Benefits-Management-Plan.md)), and Ideation Document v1.14 ([Ideation-Document.md](../Ideation-Document.md)).
  - **Master Stakeholder Register (v2.0):** Authoritative roles SH-01 through SH-07 ([Stakeholder-Register.md](../Stakeholder-Register.md)).
  - **Enterprise Environmental Factors (EEFs):** Microsoft Partner Network channel, upstream open-source synchronization constraints.
  - **Organizational Process Assets (OPAs):** ADR standards ([ADR-012](../../adr/ADR-012-subsidiary-management-plan-standards-and-content-contracts.md), [ADR-025](../../adr/ADR-025-scope-management-plan-standard-and-baseline-contract.md)) and historical Phase 1 archive.
* **Processes (PMBOK 8 §2.2.2 & §5):**
  - **Plan Scope Management:** Defining how Phase 2 scope is structured, bounded, and verified.
  - **Elicit & Analyze Requirements:** Translating hypotheses (`HYP-AL-005`, `018`, `025`–`027`) into concrete contract-first stories.
  - **Define Scope:** Delineating `agent-training-ext/` package isolation and out-of-scope exclusions.
  - **Develop Scope Structure (WBS):** Decomposing Phase 2 across Milestones M6 through M10 with 100% rule.
  - **Validate & Control Scope:** Enforcing Definition of Done (DoD) verification gates and zero status drift.
* **Outputs (PMBOK 8 §2.2.2 & §4):**
  - **Scope Management Plan:** this document (v2.0.0).
  - **Phase 2 Scope Baseline:** Integrated baseline combining Charter v2.0, this plan, and WBS dictionary.
  - **Requirements Traceability Matrix (RTM):** Convention in §1.7.

---

### 1.5 WBS Execution Authorization (Phase 1 vs Phase 2)

| Band | Epics (indicative) | Authorization Status | Phase 2 Execution Policy |
| --- | --- | --- | --- |
| **A — Foundation** | 1–7, 9–13, 36 | **Completed & Closed** | Retained as operational foundation. |
| **B — Phase 1 Product** | 15, 17, 19, 20 | **Completed & Closed** | Validated via `PCD-20261106-001`. |
| **C — Phase 2 Option B** | 14, 18 | **AUTHORIZED FOR PHASE 2** | Execute inside `agent-training-ext/` (M6, M7). |
| **D — Learning Backlog** | 16, 21, 22, 38 | **AUTHORIZED FOR PHASE 2** | Execute inside `agent-training-ext/` (M8, M9). |
| **E — PMBOK Machinery** | 25–35, 37 | **Active Governance** | Program scope; maintained continuously. |
| **F — Close & Governance** | M10, PCD-Phase2 | **Authorized Gate** | Formal phase close-out package. |

---

### 1.6 Charter Milestone to WBS Trace (Phase 2)

| Milestone | Charter Intent | Primary WBS Anchor | Delivery Target |
|---|---|---|---|
| **M6** | Critique-to-Evidence Ingestion Engine (Epic 14) | Stories 14.1–14.6 | `agent-training-ext/critique_evidence.py` |
| **M7** | DPO Pairwise Preference Optimization (Epic 18) | Epic 18 Stories | `agent-training-ext/dpo_preference.py` |
| **M8** | Contextual Authority Ensemble Routing (Epics 16, 21) | Epics 16, 21 Stories | `agent-training-ext/ensemble_router.py` |
| **M9** | Continuous SIDPA Automation (Epics 22, 38) | Epics 22, 38 Stories | Automated Stage 12–18 loop |
| **M10** | Phase 2 Review & Close Gate Adjudication | Formal Close Gate | `PCD-Phase2` package |

---

### 1.7 Requirements Traceability (RTM Convention)
Traceability remains strictly structural:
1. **Epic** — `docs/user-stories/epic-NN-*.md` header links ADR, BRD, FDD, and `PMP-BL-v1.1.0`.
2. **Story** — Each `## Story N.M` holds acceptance criteria $AC_n$; contract tests live in `agent-training-ext/tests/test_*.py`.
3. **Work package** — Closing commit recorded in `implementation-log.md` under story ID.
4. **Governance** — Continuous zero status drift enforced by `python scripts/phase_rollup.py --check`.

---

## 2. Domain Mechanics & Standards

### 2.1 Work Breakdown Structure (WBS) & Decomposition Hierarchy
Decomposition adheres to the 4-tier hierarchy:
$$\text{Project Phase} \longrightarrow \text{Epic} \longrightarrow \text{User Story} \longrightarrow \text{Work Package / Commit}$$

### 2.2 WBS 100% Rule & Assignment Invariant
Every deliverable maps to one parent epic and one user story. Each story names an accountable owner role from the Master Stakeholder Register ([`Stakeholder-Register.md`](../Stakeholder-Register.md)). All development work, tests, and documentation must trace directly to approved acceptance criteria ($AC_n$).

### 2.3 Deliverable Acceptance Protocol (Definition of Done)
In accordance with the Definition of Done:
1. **Contract-First:** Tests ($AC_n$) written and verified failing before implementation.
2. **Standard Library Purity:** Zero external dependencies for algorithmic logic; pure Python standard library only.
3. **Upstream Immunity:** All code placed in `agent-training-ext/`; `src/agent_learning` untouched.
4. **Full Test Suite Green:** 100% pass rate across active unit and contract test suites.
5. **Zero Governance Drift:** `python scripts/phase_rollup.py --check` exits with code 0.
6. **Audit Registration:** Implementation commit and verification evidence recorded in `implementation-log.md`.

---

## 3. Governance, Control & Decision Rights

### 3.1 Accountabilities & Escalation Thresholds
* **Project Manager:** Accountable for enforcing scope boundaries, monitoring backlog drift, and rejecting unauthorized feature requests.
* **Project Sponsor (Menno Drescher):** Holds sovereign authority over project scope, milestone gates, and budget authorization.

| Variance Level | Definition | Authority | Action Required |
|---|---|---|---|
| **Level 0 (Operational)** | Minor refactoring or doc clarification within an approved Story | Lead Agent Engineer | Immediate commit; log in `implementation-log.md`. |
| **Level 1 (Story Scope)** | Adding or adjusting an Acceptance Criterion within an Epic | Project Manager | Update Story spec; notify Sponsor. |
| **Level 2 (Milestone Scope)** | Adding a new User Story or altering an Epic boundary | Project Sponsor | Formal review via Stage 16 Governance Change. |
| **Level 3 (Baseline Breach)** | Adding an Epic, modifying Charter boundaries, or Phase 3 work | Project Sponsor | Stage 17 Integrated Change (`approve-adaptation-plan`). |

### 3.2 Transitive Downstream Invalidation (ADR-013 §4.5)
$$\text{Scope Management Plan} \longrightarrow \text{Schedule Management Plan} \longrightarrow \text{Cost Management Plan}$$

A Level 2 or Level 3 change to this Scope Management Plan automatically marks downstream schedule and cost plans as `STALE_DEPENDENCY` until re-baselined.

---

## 4. Amendment Log

| Date | Author | Description |
|---|---|---|
| 2026-10-25 | Menno Drescher / Antigravity | Initial full baseline Scope Management Plan replacing stub mock content per ADR-012 and ADR-025. |
| 2026-10-30 | Menno Drescher / Cursor | **v1.1.0 — First presentation pass:** unified program WBS and Phase 1 boundaries; 143-row dictionary. |
| 2026-10-30 | Menno Drescher / Cursor | **v1.2.0 — Foundation pack:** Stage 6.A manifest; foundation artifacts per PMBOK §2.2 processes. Approved under `approve-subsidiary-plan` (Episode `d68772b0-d831-4a86-90a9-a891747b9007`). |
| 2026-11-08 | Menno Drescher / Antigravity | **v2.0.0 — Phase 2 Scope Formalization:** Advanced to `v2.0.0` for Phase 2 under `PMP-BL-v1.0.1` targeting `PMP-BL-v1.1.0`. Fully authorized Band C (Epics 14, 18) and Band D (Epics 16, 21, 22, 38) for execution in `agent-training-ext/`. Codified upstream Microsoft fork collision protection boundaries, mapped Milestones M6–M10 deliverables (DEL-P2-01..08), and updated traceability to Project Charter v2.0. |
