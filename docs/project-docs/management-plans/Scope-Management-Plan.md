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
version: "1.0.2"
baseline_id: "PMP-BL-v1.0.0"
owner_role: "Project Manager"
depends_on: []
inputs:
  - "Project-Charter.md"
  - "docs/project-docs/Ideation-Document.md"
  - "docs/project-docs/Business-Case.md"
outputs:
  - "docs/project-docs/management-plans/Scope-Management-Plan.md"
governance_policy: "approve-subsidiary-plan"
---

# Scope Management Plan — agent-learning Phase 1: Warm-Start & Confidence-Interval Bandits

> **PMBOK 8 Domain:** `Scope` (Planning Focus Area) | **Legacy Process:** `5.1 Plan Scope Management`  
> **Governance Policy:** `approve-subsidiary-plan` | **Lifecycle Stage:** `Stage 6 (Planning)`  
> **Route:** `full_plan` | **Baseline Identifier:** `PMP-BL-v1.0.0`  
> **Accountable Role:** Project Manager | **Approving Sponsor:** Menno Drescher  
> **Normative Standard:** [ADR-012](../../adr/ADR-012-subsidiary-management-plan-standards-and-content-contracts.md) and [ADR-025](../../adr/ADR-025-scope-management-plan-standard-and-baseline-contract.md)

---

## 1. Intent, Alignment & Boundaries

### 1.1 Core Mandate & Charter Traceability
This Scope Management Plan establishes the formal mechanisms, verification gates, and boundary definitions for **Phase 1: Warm-Start & Confidence-Interval Bandits** of the `agent-learning` project. It directly operationalizes the strategic objectives authorized in [Project-Charter.md](../Project-Charter.md) §2 and §3:
1. **Unverified Dependency Resolution:** Resolve whether `SoftmaxPolicy` exposes its converged internal state in a structured format reusable as an initial prior distribution for successor policies (Milestone M1).
2. **Warm-Start Empirical Validation (HYP-AL-008):** Validate whether prior-distribution warm-starting reduces the number of interaction episodes required to achieve statistical autonomy eligibility compared to a cold uniform prior (Milestone M2).
3. **Confidence-Interval Bandit Autonomy (HYP-AL-009):** Validate whether an upper confidence bound (UCB) or Thompson sampling bandit can cross the Wilson lower-bound autonomy threshold when operating under positive-only (survivorship-biased) empirical evidence (Milestone M3).
4. **Phase 2 Resourcing Gate:** Formulate a rigorous, empirical decision on whether Option B (critique-to-evidence ingestion and Direct Preference Optimization) warrants development (Milestone M5).
5. **End-User Value Research (M0.5):** Conduct a time-boxed 40-hour qualitative case analysis to assess willingness-to-pay and end-user value drivers before committing to downstream production deployment.

### 1.2 In-Scope Deliverables & Architectural Modules
The authorized deliverables for Phase 1 are strictly bounded to the following components:
* **M0.5 (End-User Value Analysis):** Qualitative case studies extending beyond the SocialEngage example; preliminary empirical testing of HYP-AL-011 recorded in the Research Log.
* **M1 (State Inspection & Serialization):** Technical verification report and export/import serializers for `SoftmaxPolicy` parameters, preserving numerical stability and policy integrity.
* **M2 (Warm-Start Prior Module):** Concrete implementation of hierarchical prior seeding for discrete bandit policies in `src/agent_learning/`, accompanied by automated warm-start benchmarking fixtures.
* **M3 (Confidence-Interval Bandit Engine):** Mathematical implementation of deterministic UCB-1 and Bayesian Thompson sampling policy resolvers capable of maintaining exploration under positive-only reward feedback.
* **M4 (Autonomy Verification Harness):** Automated synthetic evaluation environment reproducing the 146-episode `validate-intent-foundation` dataset to benchmark autonomy gate crossing against baseline REINFORCE.
* **M5 (Phase 1 Synthesis & Decision Frame):** Comprehensive evaluation episode registering empirical Bayes factors for HYP-AL-008 and HYP-AL-009, feeding the formal Stage 18 Intent Refinement gate.

### 1.3 Mandatory Out-of-Scope Boundary
To prevent silent scope creep and maintain architectural focus, the following capabilities are explicitly **excluded** from Phase 1 scope:
* **Option B Implementation (Critique-to-Evidence & DPO):** No implementation of Direct Preference Optimization (DPO), pairwise reward preference fine-tuning, or offline critique parsers (deferred to Phase 2 per Business Case §6).
* **Multi-Modal / OCR Ingestion:** No image processing, scanned PDF extraction, or integration with external OCR engines (`pytesseract`, `pdf2image`, `pillow`).
* **Relational Database Infrastructure:** Zero new database engines, SQLite tables, or SQLAlchemy schemas, strictly adhering to ADR-002 Invariant #2 and ADR-028.
* **Microservice Web Server Deployment:** No FastAPI or Uvicorn server hosting; the repository remains an embedded Python SDK and CLI tool.
* **Continuous Reinforcement Learning in Production:** No unbounded autonomous policy adaptation without explicit human sign-off gates.

---

### 1.4 PMBOK Input, Process & Output (IPO) Specification
In accordance with PMBOK® Guide 8th Edition (Scope Performance Domain §2.2):
* **Inputs (PMBOK 8 §2.2.2.1 & §4):**
  - **Project Charter:** High-level scope, strategic intent, and approval requirements ([Project-Charter.md](../Project-Charter.md)).
  - **Business Documents:** Business Case ([Business-Case.md](../Business-Case.md)) and Ideation Document ([Ideation-Document.md](../Ideation-Document.md)).
  - **Enterprise Environmental Factors (EEFs):** Organizational governance frameworks, technology constraints (CPU-only execution, frozen models).
  - **Organizational Process Assets (OPAs):** ADR standards ([ADR-012](../../adr/ADR-012-subsidiary-management-plan-standards-and-content-contracts.md), [ADR-025](../../adr/ADR-025-scope-management-plan-standard-and-baseline-contract.md)) and lessons learned.
* **Processes (PMBOK 8 §2.2.2 & §5):**
  - **Plan Scope Management:** Defining how scope is identified, structured, and validated.
  - **Elicit & Analyze Requirements:** Eliciting stakeholder requirements without gold plating.
  - **Define Scope:** Delineating in-scope capabilities and non-negotiable out-of-scope exclusions.
  - **Develop Scope Structure (WBS):** Decomposing scope across 4 tiers (`Phase` $\to$ `Epic` $\to$ `Story` $\to$ `Commit`) with 100% rule.
  - **Validate & Control Scope:** Enforcing Definition of Done (DoD) verification gates and managing scope variance.
* **Outputs (PMBOK 8 §2.2.2 & §4):**
  - **Scope Management Plan:** `docs/project-docs/management-plans/Scope-Management-Plan.md`.
  - **Scope Baseline:** Approved Scope Statement, WBS architecture, and progressive User Story acceptance criteria.
  - **Requirements Traceability Matrix (RTM):** Linking high-level goals (BRD) to functional specs (FDD) and Pytest contract suites.

---

## 2. Domain Mechanics & Standards

### 2.1 Work Breakdown Structure (WBS) & Decomposition Hierarchy
Project scope is decomposed across four hierarchical tiers:

$$\text{Project Phase} \longrightarrow \text{Epic} \longrightarrow \text{User Story} \longrightarrow \text{Work Package / Commit}$$

The dictionary in §2.2 is the user-story tier. It lists every `## Story` heading under `docs/user-stories/` on 2026-10-30: 35 epic files and 137 stories. No epic file exists for Epic 23 or Epic 24.

The diagram this section used before that date is withdrawn. It named Story 0.1, and it assigned Epics 12–15 to tooling, warm-start serialization, confidence-interval bandits, and phase close. Those headings are not the written stories. The written work for those themes is:

* **Tooling convergence:** Epic 34.
* **Warm-start:** Epics 19 and 20.
* **Confidence-interval bandits:** Epics 15, 16, and 17.
* **Phase close:** Stories 9.1 and 10.1.

A work package is the commit that closes one story, recorded in `implementation-log.md`. This dictionary does not list commits.

### 2.2 WBS Dictionary & 100% Rule
Every deliverable maps to one parent epic and one user story. Unassigned work packages are prohibited. The 100% rule requires development work, documentation updates, and test suites to trace to an approved story acceptance criterion ($AC_n$).

Each row below uses these dictionary fields:

* **Parent epic:** the epic named in the row. The story file is the child of that epic.
* **Owner role:** Project Manager.
* **Acceptance criteria:** the $AC_n$ items in that story file. This dictionary records the story id and title. It does not copy the criteria.

Epic 14 and Epic 18 are written. §1.3 still excludes Option B (critique parsers and pairwise preference) from Phase 1. The rows record that the files exist. They do not authorize that work.

| Story | Title | Parent epic |
| --- | --- | --- |
| 1.1 | Exclude full-authority episodes from ReinforceLearner's training batch | Epic 1: Decision Authority Enforcement |
| 2.1 | Implement Optimistic Concurrency and Monotonicity Guard for Cosmos Active Pointer | Epic 2: Cosmos Active-Policy Pointer Concurrency Protection |
| 3.1 | Build Tier-Specific Environment Overrides and Authority-Aware Autonomy Reporting | Epic 3: Tier-Specific Autonomy Overrides and Authority-Aware Reporting |
| 4.1 | Capture Diagnostic Migration Snapshot and Correct Replay Docstring | Epic 4: Authority-Migration Diagnostic Snapshot and Docstring Alignment |
| 5.1 | Build compare_decision_results() and the task-policy-compare CLI | Epic 5: Decision-Progress Comparison and Regression Healing |
| 6.1 | Implement Opt-In Policy Configuration and Lightweight Evidence Capture | Epic 6: Opt-In Lightweight Evidence Capture for Low-Authority Decisions |
| 7.1 | Implement Paired Diff Classification & Escalation Pipeline | Epic 7: Automated Governance Change — Paired Diff Classification and Escalation Pipeline |
| 8.1 | Native PMBOK 8 Orchestration Engine and PMP Decision Gate | Epic 8: PMBOK 8 Lifecycle Orchestration and Closed-Loop Adaptation Feedback |
| 9.1 | Phase Close Readiness Gate and Intent Refinement Decision Policy | Epic 9: Intent Refinement and Cognitive Feedback Loop |
| 9.2 | Bayesian Hypothesis Terminality and Recurrence Exhaustion ($d_{\max}=2$) | Epic 9: Intent Refinement and Cognitive Feedback Loop |
| 9.3 | Low-Pass Outcome Damping and Cumulative Lineage Kernel | Epic 9: Intent Refinement and Cognitive Feedback Loop |
| 10.1 | Implement Lessons Learned Register Parser, Validation Contract, and Phase Close Readiness Bridge | Epic 10: Stage 15 Lessons Learned Crystallization and OPA Register |
| 11.1 | Route Records and the Human-Decision Invariants | Epic 11: Project Tailoring and Route Decision |
| 11.2 | Flags That Never Block, and Integration-Section Home | Epic 11: Project Tailoring and Route Decision |
| 12.1 | The Frontmatter Grammar Parser | Epic 12: Subsidiary Management Plan Standards and Content Contracts |
| 12.2 | Metadata Validation and the Nine-Plan Standards | Epic 12: Subsidiary Management Plan Standards and Content Contracts |
| 12.3 | The Content Contract: Headings, Length and Boundaries | Epic 12: Subsidiary Management Plan Standards and Content Contracts |
| 12.4 | Precedence and the Next Step | Epic 12: Subsidiary Management Plan Standards and Content Contracts |
| 13.1 | The Canonical Content Hash | Epic 13: Subsidiary Plan Approval Gates Before PMP Formalization |
| 13.2 | Technical Integrity and the Gate Constraint | Epic 13: Subsidiary Plan Approval Gates Before PMP Formalization |
| 13.3 | The Approval Record and the Policy Shape | Epic 13: Subsidiary Plan Approval Gates Before PMP Formalization |
| 13.4 | The Dependency Graph | Epic 13: Subsidiary Plan Approval Gates Before PMP Formalization |
| 13.5 | Freshness and Transitive Staleness | Epic 13: Subsidiary Plan Approval Gates Before PMP Formalization |
| 13.6 | The Lifecycle State | Epic 13: Subsidiary Plan Approval Gates Before PMP Formalization |
| 13.7 | Formalization and the Package Contract | Epic 13: Subsidiary Plan Approval Gates Before PMP Formalization |
| 14.1 | The Tag Grammar and Parser | Epic 14: Lightweight Critique-to-Evidence Ingestion |
| 14.2 | Moving the Pooled Support by the Delta | Epic 14: Lightweight Critique-to-Evidence Ingestion |
| 14.3 | Doubt, Traceability and Validation | Epic 14: Lightweight Critique-to-Evidence Ingestion |
| 14.4 | Episode Metadata | Epic 14: Lightweight Critique-to-Evidence Ingestion |
| 14.5 | Replay on the Real Triage Records | Epic 14: Lightweight Critique-to-Evidence Ingestion |
| 14.6 | The Delta Rubric | Epic 14: Lightweight Critique-to-Evidence Ingestion |
| 15.1 | The Seed and the Replay | Epic 15: Bayesian Bandit Posterior Sampling (Thompson Sampling) |
| 15.2 | Posterior State in the Snapshot | Epic 15: Bayesian Bandit Posterior Sampling (Thompson Sampling) |
| 15.3 | Choosing by Probability Matching | Epic 15: Bayesian Bandit Posterior Sampling (Thompson Sampling) |
| 15.4 | The Conjugate Update and the Ceiling | Epic 15: Bayesian Bandit Posterior Sampling (Thompson Sampling) |
| 15.5 | Staying Out of REINFORCE | Epic 15: Bayesian Bandit Posterior Sampling (Thompson Sampling) |
| 15.6 | The Positive-Only Check (HYP-AL-002) | Epic 15: Bayesian Bandit Posterior Sampling (Thompson Sampling) |
| 16.1 | The Scores | Epic 16: Deterministic Upper Confidence Bound (UCB) Decision Policy |
| 16.2 | Choosing Deterministically | Epic 16: Deterministic Upper Confidence Bound (UCB) Decision Policy |
| 16.3 | Statistics in the Snapshot | Epic 16: Deterministic Upper Confidence Bound (UCB) Decision Policy |
| 16.4 | Counting Each Episode Once | Epic 16: Deterministic Upper Confidence Bound (UCB) Decision Policy |
| 16.5 | Staying Out of REINFORCE | Epic 16: Deterministic Upper Confidence Bound (UCB) Decision Policy |
| 16.6 | The Positive-Only Check (HYP-AL-009) | Epic 16: Deterministic Upper Confidence Bound (UCB) Decision Policy |
| 17.1 | The Schedule | Epic 17: Scheduled Epsilon-Greedy Policy Baseline |
| 17.2 | The Safety Mask | Epic 17: Scheduled Epsilon-Greedy Policy Baseline |
| 17.3 | Choosing and Replaying | Epic 17: Scheduled Epsilon-Greedy Policy Baseline |
| 17.4 | Statistics and the Learner | Epic 17: Scheduled Epsilon-Greedy Policy Baseline |
| 17.5 | Staying Out of REINFORCE | Epic 17: Scheduled Epsilon-Greedy Policy Baseline |
| 17.6 | The Positive-Only Baseline Run | Epic 17: Scheduled Epsilon-Greedy Policy Baseline |
| 18.1 | Pairs From Episodes | Epic 18: Pairwise Preference Optimization for Discrete Action Logits |
| 18.2 | The Loss and Its Gradient | Epic 18: Pairwise Preference Optimization for Discrete Action Logits |
| 18.3 | The Fit | Epic 18: Pairwise Preference Optimization for Discrete Action Logits |
| 18.4 | The Learner | Epic 18: Pairwise Preference Optimization for Discrete Action Logits |
| 18.5 | Through the Runner | Epic 18: Pairwise Preference Optimization for Discrete Action Logits |
| 18.6 | The Real-Data Check (Zero Pairs) | Epic 18: Pairwise Preference Optimization for Discrete Action Logits |
| 19.1 | Pooling Logits | Epic 19: Hierarchical Meta-Prior Compilation Across Task Families |
| 19.2 | Pooling Beta Counts | Epic 19: Hierarchical Meta-Prior Compilation Across Task Families |
| 19.3 | Refusing a Bad Family | Epic 19: Hierarchical Meta-Prior Compilation Across Task Families |
| 19.4 | Declaring and Finding Members | Epic 19: Hierarchical Meta-Prior Compilation Across Task Families |
| 19.5 | Storing the Prior | Epic 19: Hierarchical Meta-Prior Compilation Across Task Families |
| 19.6 | Seeding a New Policy | Epic 19: Hierarchical Meta-Prior Compilation Across Task Families |
| 19.7 | The Real-Data Check (No Family) | Epic 19: Hierarchical Meta-Prior Compilation Across Task Families |
| 20.1 | The Damped Copy | Epic 20: Explicit Policy Prior Warm-Starting |
| 20.2 | The Provenance Record | Epic 20: Explicit Policy Prior Warm-Starting |
| 20.3 | The Command for a Policy Donor | Epic 20: Explicit Policy Prior Warm-Starting |
| 20.4 | No Borrowed Evidence | Epic 20: Explicit Policy Prior Warm-Starting |
| 20.5 | Seeding From a Family Meta-Prior | Epic 20: Explicit Policy Prior Warm-Starting |
| 20.6 | The Real-Data Check (No Donor) | Epic 20: Explicit Policy Prior Warm-Starting |
| 21.1 | Entropy and Margin | Epic 21: Contextual Authority Ensemble Routing |
| 21.2 | The Route | Epic 21: Contextual Authority Ensemble Routing |
| 21.3 | Pinned Gates | Epic 21: Contextual Authority Ensemble Routing |
| 21.4 | The Shadow Record and the Agreement Gate | Epic 21: Contextual Authority Ensemble Routing |
| 21.5 | Human Decisions and the Promotion Seed | Epic 21: Contextual Authority Ensemble Routing |
| 21.6 | Dispatch and Gradient Exclusion | Epic 21: Contextual Authority Ensemble Routing |
| 21.7 | The Real-Data Check (No Routed Traffic) | Epic 21: Contextual Authority Ensemble Routing |
| 22.1 | Scoring a Weight Vector With the Real Resolver | Epic 22: Scored-Search Decision Configuration Compilation |
| 22.2 | The Split and the Label Rule | Epic 22: Scored-Search Decision Configuration Compilation |
| 22.3 | The Coordinate Ascent | Epic 22: Scored-Search Decision Configuration Compilation |
| 22.4 | Proposing Only a Real Improvement | Epic 22: Scored-Search Decision Configuration Compilation |
| 22.5 | Applying Frozen Weights | Epic 22: Scored-Search Decision Configuration Compilation |
| 22.6 | Adopting a Proposal by a Human Decision | Epic 22: Scored-Search Decision Configuration Compilation |
| 22.7 | The Real-Data Regression Check | Epic 22: Scored-Search Decision Configuration Compilation |
| 25.1 | Scope floors, caps, and exclusions | Epic 25: Scope Management Plan Standard and Baseline Contract |
| 25.2 | WBS and Definition of Done | Epic 25: Scope Management Plan Standard and Baseline Contract |
| 25.3 | The idle Scope advisory policy | Epic 25: Scope Management Plan Standard and Baseline Contract |
| 25.4 | Record the recommendation, then show it | Epic 25: Scope Management Plan Standard and Baseline Contract |
| 26.1 | Schedule floors, caps, and exclusions | Epic 26: Schedule Management Plan Standard and Baseline Contract |
| 26.2 | Milestone register, timebox, and estimation basis | Epic 26: Schedule Management Plan Standard and Baseline Contract |
| 26.3 | The idle Schedule advisory policy | Epic 26: Schedule Management Plan Standard and Baseline Contract |
| 26.4 | Record the recommendation, then show it | Epic 26: Schedule Management Plan Standard and Baseline Contract |
| 27.1 | Cost floors, caps, and exclusions | Epic 27: Cost Management Plan Standard and Baseline Contract |
| 27.2 | Envelope, categories, and contingency | Epic 27: Cost Management Plan Standard and Baseline Contract |
| 27.3 | The idle Cost advisory policy | Epic 27: Cost Management Plan Standard and Baseline Contract |
| 27.4 | Record the recommendation, then show it | Epic 27: Cost Management Plan Standard and Baseline Contract |
| 28.1 | Risk floors, caps, and exclusions | Epic 28: Risk Management Plan Standard |
| 28.2 | Scale, register contract, and escalation | Epic 28: Risk Management Plan Standard |
| 28.3 | The idle Risk advisory policy | Epic 28: Risk Management Plan Standard |
| 28.4 | Record the recommendation, then show it | Epic 28: Risk Management Plan Standard |
| 29.1 | Quality floors, caps, and exclusions | Epic 29: Quality Management Plan Standard |
| 29.2 | Gates, verification, and nonconformance | Epic 29: Quality Management Plan Standard |
| 29.3 | The idle Quality advisory policy | Epic 29: Quality Management Plan Standard |
| 29.4 | Record the recommendation, then show it | Epic 29: Quality Management Plan Standard |
| 30.1 | Resource lengths and the full-plan exclusion minimum | Epic 30: Resource Management Plan Standard |
| 30.2 | Catalogue, allocation, and tooling | Epic 30: Resource Management Plan Standard |
| 30.3 | The idle Resource advisory policy | Epic 30: Resource Management Plan Standard |
| 30.4 | Record the recommendation, then show it | Epic 30: Resource Management Plan Standard |
| 31.1 | Stakeholder lengths and the full-plan exclusion minimum | Epic 31: Stakeholder Engagement Plan Standard |
| 31.2 | Register, engagement levels, and actions | Epic 31: Stakeholder Engagement Plan Standard |
| 31.3 | The idle Stakeholder advisory policy | Epic 31: Stakeholder Engagement Plan Standard |
| 31.4 | Record the recommendation, then show it | Epic 31: Stakeholder Engagement Plan Standard |
| 32.1 | Communications lengths and the full-plan exclusion minimum | Epic 32: Communications Management Plan Standard |
| 32.2 | Matrix, decision-recording rule, and escalation path | Epic 32: Communications Management Plan Standard |
| 32.3 | The idle Communications advisory policy | Epic 32: Communications Management Plan Standard |
| 32.4 | Record the recommendation, then show it | Epic 32: Communications Management Plan Standard |
| 33.1 | Procurement lengths and the full-plan exclusion minimum | Epic 33: Procurement Management Plan Standard |
| 33.2 | Make-or-buy criteria, intake rule, and licence checks | Epic 33: Procurement Management Plan Standard |
| 33.3 | The idle Procurement advisory policy | Epic 33: Procurement Management Plan Standard |
| 33.4 | Record the recommendation, then show it | Epic 33: Procurement Management Plan Standard |
| 34.1 | The 49-process registry is pure data | Epic 34: PMBOK Tooling Decommissioning and Lightweight LearningStore Convergence |
| 34.2 | A project run is an Episode, and the latest one wins | Epic 34: PMBOK Tooling Decommissioning and Lightweight LearningStore Convergence |
| 34.3 | The client is the standard library, and secrets stay out of the record | Epic 34: PMBOK Tooling Decommissioning and Lightweight LearningStore Convergence |
| 34.4 | One CLI dispatches draft, approve, formalize, and adapt | Epic 34: PMBOK Tooling Decommissioning and Lightweight LearningStore Convergence |
| 34.5 | The legacy tree is gone and the suite collects | Epic 34: PMBOK Tooling Decommissioning and Lightweight LearningStore Convergence |
| 35.1 | Cycle and baseline ids, and a hash that ignores them | Epic 35: Cycle Identification and Cross-Cycle Artifact Traceability |
| 35.2 | The register is an event log with one open cycle | Epic 35: Cycle Identification and Cross-Cycle Artifact Traceability |
| 35.3 | Lookup stops at the first source that hits | Epic 35: Cycle Identification and Cross-Cycle Artifact Traceability |
| 35.4 | Frontmatter is checked, and a clash refuses closure | Epic 35: Cycle Identification and Cross-Cycle Artifact Traceability |
| 36.1 | The Catalog and Its Integrity Check | Epic 36: Learning Methodology Examples, Best-Practice Ledger and the Review-Triage Learning Loop |
| 36.2 | Runnable Examples for What Exists | Epic 36: Learning Methodology Examples, Best-Practice Ledger and the Review-Triage Learning Loop |
| 36.3 | Proof-of-Concept Sketches for the ADR-Backed Candidates | Epic 36: Learning Methodology Examples, Best-Practice Ledger and the Review-Triage Learning Loop |
| 36.4 | The Best-Practice Ledger | Epic 36: Learning Methodology Examples, Best-Practice Ledger and the Review-Triage Learning Loop |
| 36.5 | The Review-Triage Learning Loop | Epic 36: Learning Methodology Examples, Best-Practice Ledger and the Review-Triage Learning Loop |
| 36.6 | Tailoring for the Store and Lessons Learned, and Template Propagation | Epic 36: Learning Methodology Examples, Best-Practice Ledger and the Review-Triage Learning Loop |
| 37.1 | Record design-time evidence on the existing governance call | Epic 37: Design-Time Baseline Feedback Loop |
| 37.2 | A baseline feedback item cites documents and carries no numbers | Epic 37: Design-Time Baseline Feedback Loop |
| 37.3 | Design-time bumps the patch, execution bumps the minor | Epic 37: Design-Time Baseline Feedback Loop |
| 37.4 | The pending-feedback section names both loops | Epic 37: Design-Time Baseline Feedback Loop |

### 2.3 Scope Baseline Definition
The official Scope Baseline for Phase 1 comprises:
1. **The Approved Scope Statement:** As set forth in this document.
2. **The WBS & Milestone Schedule:** Anchored in [Project-Charter.md](../Project-Charter.md) §7.
3. **The User Story Contracts:** Individual Acceptance Criteria specified in approved User Story specifications (`docs/user-stories/`).

### 2.4 Deliverable Acceptance Protocol (Definition of Done)
No work package or deliverable is accepted into the repository baseline until it satisfies the canonical **Definition of Done (DoD)**:
- **Contract Specification:** User story acceptance criteria are formalized in executable contract tests (`tests/test_*.py`).
- **Observed RED First:** Contract tests are verified failing prior to functional implementation.
- **Pure Implementation:** Production code adheres to stdlib-first constraints with zero undeclared dependencies.
- **Full Suite Green:** Complete repository test suite passes without collection errors.
- **Audit Logging:** Story commit hash and acceptance verification are documented in `implementation-log.md`.
- **Peer Review:** Pull request passes automated and human review with all findings resolved.

---

## 3. Governance, Control & Decision Rights

### 3.1 Accountabilities & Escalation Thresholds
* **Project Manager:** Accountable for enforcing scope boundaries, monitoring backlog drift, and rejecting unauthorized feature requests.
* **Project Sponsor (Menno Drescher):** Holds sovereign authority over project scope, milestone gates, and budget authorization.

| Variance Level | Definition | Authority | Action Required |
|---|---|---|---|
| **Level 0 (Operational)** | Minor refactoring or doc clarification within an approved Story | Developer / Tech Lead | Immediate commit; log in `implementation-log.md`. |
| **Level 1 (Story Scope)** | Adding or adjusting an Acceptance Criterion within an Epic | Project Manager | Update Story spec; notify Sponsor. |
| **Level 2 (Milestone Scope)** | Adding a new User Story or altering an Epic boundary | Project Sponsor | Formal review via Stage 16 Governance Change. |
| **Level 3 (Baseline Breach)** | Adding an Epic, modifying Charter boundaries, or Phase 2 work | Project Sponsor | Stage 17 Integrated Change (`approve-adaptation-plan`). |

### 3.2 Transitive Downstream Invalidation (ADR-013 §4.5)
Per ADR-013 §4.5, Scope forms the foundational root node of the planning directed acyclic graph:
$$\text{Scope Management Plan} \longrightarrow \text{Schedule Management Plan} \longrightarrow \text{Cost Management Plan}$$

Any Level 2 or Level 3 change to this Scope Management Plan automatically marks:
1. `Schedule-Management-Plan.md` as **`STALE_DEPENDENCY`** (requiring schedule recalculation).
2. `Cost-Management-Plan.md` as **`STALE_DEPENDENCY`** (requiring budget re-estimation).

Re-validation of downstream plans must occur before composite formalization under `approve-pmp` is permitted.

### 3.3 Subsidiary approval with scope advisory recommendations (ADR-025 §4.4.1, BRU-025-05–06)

Scope baseline authorization uses **two task ids**. They are sequential in intent but **not** merged into one policy.

| Step | Task id | Authority | Outcome |
| --- | --- | --- | --- |
| 1 — Measure | *(lint only)* | — | `lint_plan` on this file applies ADR-012 plus the Scope profile (ADR-025 / Epic 25). Findings are evidence for the human; they do not approve the plan. |
| 2 — Advise *(optional, when implemented)* | `advise-scope-plan-decision` | **Low** — advisory only | For each maintainer question, the caller passes **one** decision kind (`route`, `paragraph_sufficiency`, `graduation`, `flagged_deviation`). The bandit draws **only** among that kind's actions ([FDD-025](../../project-docs/Functional-Design/FDD-025-scope-management-plan-standard-and-baseline-contract.md) §2 `DECISION_KINDS`, confirmed 2026-10-30). The recommendation and `recommended_at` are **stored before display**; follow or override is recorded for later REINFORCE on the **recommendation action**, not on gate actions. |
| 3 — Decide | `approve-subsidiary-plan` | **Full** — human required | The Project Manager / Sponsor adjudicates `approve_plan`, `reject_plan`, or `request_revision_before_decision`. **Only this step** binds the integrated Scope baseline (manifest **6.A-7**, BFI-002). |

**Operating rule (2026-10-30, Menno):** Human approval is mandatory for subsidiary scope baseline; **`advise-scope-plan-decision` may recommend** route, sufficiency, graduation, or deviation handling **before** that decision. Recommendations never substitute for `approve_plan`. Idle policy shape: [advise-scope-plan-decision.actions.json](../../policy-shapes/advise-scope-plan-decision.actions.json). Implementation: Epic 25 Stories 25.3–25.4; methodology selection episode (ADR-024) is recorded separately when the policy is declared.

---

## 4. Amendment Log

| Date | Author | Description |
|---|---|---|
| 2026-10-25 | Menno Drescher / Antigravity | Initial full baseline Scope Management Plan replacing stub mock content per ADR-012 and ADR-025. |
| 2026-10-30 | Menno Drescher / Cursor | Replaced the WBS diagram with the dictionary of 137 written stories in 35 epics. The previous diagram named stories those files do not contain. |
| 2026-10-30 | Menno Drescher | **v1.0.2:** §3.3 — human `approve-subsidiary-plan` with optional `advise-scope-plan-decision` recommendations (FDD-025 §5 item 1 confirmed). |
