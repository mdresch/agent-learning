---
plan_id: "procurement-management"
plan_name: "Procurement Management Plan"
pmbok_edition: "PMBOK 8"
pmbok_focus_area: "Planning"
primary_pmbok_domain: "Finance"
secondary_pmbok_domains:
  - "Resources"
  - "Governance"
legacy_process: "12.1 Plan Procurement Management"
route: "full_plan"
generator: "llm"
version: "2.0.0"
baseline_id: "PMP-BL-v1.1.0"
owner_role: "Project Manager"
depends_on:
  - "scope-management"
  - "cost-management"
inputs:
  - "Project-Charter.md"
  - "docs/project-docs/management-plans/Scope-Management-Plan.md"
  - "docs/project-docs/management-plans/Cost-Management-Plan.md"
outputs:
  - "docs/project-docs/management-plans/Procurement-Management-Plan.md"
governance_policy: "approve-subsidiary-plan"
---

# Procurement Management Plan — agent-learning Phase 2: Autonomous Feedback Loops & Extensible Architecture

> **PMBOK 8 Domain:** `Finance` (Planning Focus Area) | **Legacy Process:** `12.1 Plan Procurement Management`  
> **Governance Policy:** `approve-subsidiary-plan` | **Lifecycle Stage:** `Stage 6 (Planning)`  
> **Route:** `full_plan` | **Baseline Identifier:** `PMP-BL-v1.1.0`  
> **Accountable Role:** Project Manager | **Approving Sponsor:** Menno Drescher  
> **Normative Standard:** [ADR-012](../../adr/ADR-012-subsidiary-management-plan-standards-and-content-contracts.md), [ADR-033](../../adr/ADR-033-procurement-management-plan-standard.md)

---

## 1. Intent, Alignment & Boundaries

### 1.1 Core Mandate & Zero External Procurement Strategy
This Procurement Management Plan establishes the vendor, licensing, dependency intake, and supply chain governance for **Phase 2: Autonomous Feedback Loops & Extensible Architecture**. 

In strict alignment with [Project-Charter.md](../Project-Charter.md) v2.0 §4, [Cost-Management-Plan.md](Cost-Management-Plan.md) v2.0.0, and [Resource-Management-Plan.md](Resource-Management-Plan.md) v2.0.0, Phase 2 operates under an explicit **Zero External Procurement Strategy**:
1. **Complete Internal Self-Sufficiency:** All algorithmic design, AST critique parsing, DPO loss formulation, contextual bandit ensembling, and Continuous SIDPA orchestration are executed entirely by internal project resources (Sponsor/Maintainer Menno Drescher accelerated by Antigravity AI engineering assistants).
2. **Zero Paid Third-Party Consulting Contracts:** No external vendors, system integrators, staffing contractors, or specialized ML consultancies are engaged for Phase 2 delivery, saving over €32,000 in commercial contractor costs.
3. **Pure Standard Library Architecture (ADR-034):** The custom extensions in `agent-training-ext/` rely strictly on Python's built-in standard library (`ast`, `math`, `statistics`, `json`, `dataclasses`). This architectural decision eliminates heavy ML framework dependencies (such as PyTorch, Hugging Face, or CUDA) and bypasses expensive cloud GPU/accelerator compute rentals (saving >€5,000 in infrastructure costs).
4. **Open-Source Software (OSS) Permissive Licensing:** All toolchains and runtime components operate under permissive open-source licenses (MIT, Apache 2.0).

### 1.2 Boundary Definitions
* **In-Scope Governance:** Open-source dependency vetting; supply chain security analysis; software license compatibility (MIT/Apache 2.0 vs copyleft); developer toolchain licensing; model API quota monitoring (Anthropic, Google, Azure).
* **Out-of-Scope Procurement Activities:** The following procurement processes are strictly excluded:
  - Commercial cloud GPU server cluster leases (e.g. AWS EC2 p4de/p5, RunPod, Lambda Labs).
  - Requests for Proposals (RFPs) and formal bidding tenders.
  - Vendor bidding competitions and commercial procurement legal evaluations.
  - Commercial software licensing agreements and enterprise SaaS subscriptions.
  - Physical hardware procurement and datacenter co-location contracts.

### 1.3 Charter, Scope and Cost Traceability
Procurement controls directly operationalize Charter v2.0 commitments and align with the approved baselines:
* **Charter §4 Financial Envelope:** Adheres to the strict cash OpEx ceiling of $\le €100.00/\text{month}$ and $\le €300.00$ overall Phase 2 cash envelope.
* **Scope Baseline Deliverable Alignment (`PMP-BL-v1.1.0`):**
  - DEL-P2-01 through DEL-P2-08 are delivered 100% internally within `agent-training-ext/`.
  - Zero proprietary black-box APIs are embedded into the runtime decision engine.
* **Cost Baseline Alignment (`PMP-BL-v1.1.0`):**
  - Validates that zero procurement expenditure draws upon the €19,175.00 labor valuation (€15,300 base labor + €3,875 contingency buffer at €85.00/hr shadow rate; €0.00 cash outlay).
  - Confines cash disbursements exclusively to developer API token usage.

### 1.4 PMBOK Input, Process & Output (IPO) Specification
In accordance with PMBOK® Guide 8th Edition (Appendix X4 Procurement & Governance §2.1.6.3):
* **Inputs (PMBOK 8 Appendix X4 & §4):**
  - **Project Charter:** Strategic sourcing direction and budget constraints ([Project-Charter.md](../Project-Charter.md) v2.0).
  - **Project Management Plan:** Scope baseline ([Scope-Management-Plan.md](Scope-Management-Plan.md) v2.0.0) and cost envelope ([Cost-Management-Plan.md](Cost-Management-Plan.md) v2.0.0).
  - **Enterprise Environmental Factors (EEFs):** Open-source licensing ecosystem (MIT, Apache, GPL), cloud API pricing tiers, local workstation compute.
  - **Organizational Process Assets (OPAs):** ADR standards ([ADR-012](../../adr/ADR-012-subsidiary-management-plan-standards-and-content-contracts.md), [ADR-033](../../adr/ADR-033-procurement-management-plan-standard.md), [ADR-034](../../adr/ADR-034-pmbok-tooling-decommissioning-and-lightweight-learningstore-convergence.md) anti-sprawl).
* **Processes (PMBOK 8 Appendix X4 & §5):**
  - **Plan Sourcing Strategy:** Conducting make-or-buy analysis and establishing third-party dependency intake rules for Phase 2.
  - **Source Selection Analysis:** Evaluating candidate tools against capability, cost, and maintenance criteria.
  - **Contract & Licence Review:** Verifying copyleft/commercial licence compatibility and vendor data privacy terms.
  - **Monitor & Control Procurements:** Overseeing dependency health, API quotas, and supplier exit readiness.
* **Outputs (PMBOK 8 Appendix X4 & §4):**
  - **Procurement Management Plan:** `docs/project-docs/management-plans/Procurement-Management-Plan.md` v2.0.0.
  - **Dependency Intake Register:** Recorded justifications and exit paths for third-party development dependencies.
  - **Licence Compliance Checklists:** Verified terms for open-source libraries and cloud model subscriptions.

---

## 2. Domain Mechanics & Standards

### 2.1 Open-Source Licensing & Compatibility Governance
To protect the intellectual property and MIT licensing of the `agent-learning` SDK and its `agent-training-ext` extension package, all dependencies undergo strict licensing evaluation:

| License Category | Allowed in Production? | Evaluation Criteria & Action |
|---|---|---|
| **Permissive (MIT, Apache 2.0, BSD-2/3, ISC)** | **YES** | Pre-approved for core dependencies and development extras. Must be attributed in package metadata. |
| **Weak Copyleft (LGPL, MPL)** | **CONDITIONAL** | Allowed only as dynamically linked runtime dependencies; strictly prohibited from static embedding in `agent-training-ext/`. |
| **Strong Copyleft (GPL v2/v3, AGPL)** | **STRICTLY PROHIBITED** | Incompatible with permissive MIT distribution. Any component importing GPL code is rejected outright. |
| **Proprietary / Commercial** | **PROHIBITED (Phase 2)** | Prohibited unless explicit prior written authorization is granted by Project Sponsor Menno Drescher. |

### 2.2 Supply Chain Security & Pure Standard Library Dependency Intake
1. **Pure Standard Library Architecture for Phase 2:**
   - In accordance with **ADR-034** and Invariant 4, all core algorithmic modules in `agent-training-ext/` (`critique_evidence.py`, `dpo_generator.py`, `contextual_bandit.py`, `continuous_sidpa.py`) must use Python's built-in standard library exclusively.
   - External scientific dependencies (`torch`, `tensorflow`, `jax`, `transformers`) are strictly prohibited in `agent-training-ext/` production code.
2. **Deterministic Virtual Environments:** Development and testing environments utilize `pyproject.toml` dependency locking and deterministic virtual environment management via `uv`.
3. **Automated Vulnerability Monitoring:** All dependencies in the root development environment are monitored continuously via GitHub Dependabot and automated security advisories.

### 2.3 Make-or-Buy Analysis & Sourcing Strategy Decision

In accordance with PMBOK 8 Appendix X4 and ADR-033 §4.2, the project conducted a formal economic and strategic **Make-or-Buy Analysis** for Phase 2 deliverables using the labor rates established in [Resource-Capacity-Estimates.md](resource-baseline/foundation/Resource-Capacity-Estimates.md) §5:

#### 1. Sourcing Options Evaluated

1. **Option A (Make — Internal Maintainer + Antigravity AI Pair Engineering):**
   * Execute all Phase 2 deliverables (Epics 14, 18, 16, 21, 22, 38) internally in `agent-training-ext/`.
   * **Economic Labor Valuation:** 30.0 person-days (180 maintainer hours) + 5.0 pd reserve + 12.5 pd contingency at €85.00/hr = **€19,175.00** imputed economic value (**€0.00 cash disbursement**).
   * **Model API Outlay:** Capped at **≤ €100.00 / month** (total Phase 2 ceiling **≤ €300.00**).
   * **Total Cash Outlay:** **≤ €300.00**.

2. **Option B (Buy — External Specialized AI/ML Contractor):**
   * Procure external senior Python/ML reinforcement learning engineers to build AST critique engines, DPO generators, and bandit ensembling.
   * **Direct Contractor Outlay:** 30.0 days $\times$ 8 hrs/day $\times$ €135.00/hr = **€32,400.00 cash outlay**.
   * **Procurement & Onboarding Overhead (15%):** **€4,860.00** (contract drafting, technical onboarding, knowledge transfer).
   * **Total Cash Outlay:** **€37,260.00**.

3. **Option C (Buy — Commercial Off-the-Shelf SaaS & Cloud GPU Clusters):**
   * License commercial LLM evaluation / RLHF platforms (e.g., Scale AI, Weights & Biases Enterprise, commercial DPO SaaS) and lease cloud GPU instances (AWS EC2 p4de / RunPod) for model training.
   * **Platform & Cloud GPU Lease:** **€5,000.00 – €12,000.00**.
   * **Architectural Risk:** Violates standard-library purity, introduces vendor lock-in, and creates permanent operational cost burdens.

#### 2. Comparative Decision Matrix

| Evaluation Criterion | Weight | Option A (Internal Make) | Option B (External Contractor) | Option C (Commercial SaaS & Cloud GPU) |
| :--- | :---: | :---: | :---: | :---: |
| **Direct Cash Outlay (€)** | 0.35 | **5 / 5** (≤€300 cash) | 1 / 5 (€37.2k cash) | 2 / 5 (€10k+ cash) |
| **Standard-Library Purity (ADR-034)** | 0.25 | **5 / 5** (100% pure stdlib) | 3 / 5 (Dependency bloat risk) | 1 / 5 (Violates ADR-034) |
| **Upstream Fork Collision Protection** | 0.20 | **5 / 5** (Strictly isolated in ext/) | 2 / 5 (High bleed risk) | 1 / 5 (External SaaS mismatch) |
| **Delivery Velocity & Agility** | 0.20 | **4.6 / 5** (AI pair velocity) | 3 / 5 (Onboarding lag) | 4 / 5 (Pre-built components) |
| **Weighted Score** | **1.00** | **4.92 / 5.00** | **2.15 / 5.00** | **1.85 / 5.00** |

#### 3. Formal Sourcing Decision

* **Authoritative Decision:** **100% Internal "Make"**.
* **Contractor Procurement Ruling:** External contractor procurement is **strictly prohibited** for Phase 2. Zero contractor expense is authorized.
* **Direct Cost Avoidance:** Internal execution achieves **€36,960.00** in direct cash outlay avoidance compared to commercial contractor procurement.

---

### 2.4 Approved External Procurement Register

External acquisitions for Phase 2 are strictly limited to necessary developer model API quotas and local compute:

| Procurement Item | Category | Vendor / Source | Authorized Limit | Funding Basis | Justification |
| :--- | :--- | :--- | :---: | :--- | :--- |
| **AI Model APIs** | Cloud / SaaS | Anthropic, Google, Azure | **≤ €100.00 / mo** (max €300 total) | Monthly OpEx | Interactive pair engineering, AST critique analysis, and synthetic review benchmarks. |
| **Workstation Compute** | Hardware | Local Host System | **€0.00** | Sunk Capital | Zero CapEx local workstation execution; pure standard library execution requires no cloud GPU clusters. |
| **FOSS Development Toolchains** | Software | PyPI (MIT / Apache 2.0) | **€0.00** | Free OSS | Core development and static analysis toolchains (`pytest`, `ruff`, `mypy`). |
| **GitHub Repository & Actions** | DevOps | GitHub (Free Public OSS) | **€0.00** | Free OSS Tier | Public CI/CD workflows, automated testing, and release distribution. |

---

## 3. Governance, Control & Decision Rights

### 3.1 Accountabilities & Authority Levels
* **Tech Lead / Developer:** Responsible for auditing license types before introducing new dependencies, enforcing standard library purity in `agent-training-ext/`, and ensuring zero copyleft contamination.
* **Project Manager:** Accountable for enforcing the zero-procurement boundary, monitoring API monthly spend against the €100.00 cap, and reviewing Dependabot PR security advisories.
* **Project Sponsor (Menno Drescher):** Holds sole sovereign authority to authorize any commercial software expenditure, contract signing, or licensing exception.

### 3.2 Position in the Planning DAG & Baseline Approval (Stage 6.E)
In accordance with ADR-013 §4.1 and ADR-033 §4.1:
$$\begin{pmatrix}\text{Scope Management (5.1)} \\ \text{Cost Management (7.1)}\end{pmatrix} \longrightarrow \text{Procurement Management (12.1)}$$

* **Upstream Baselines:** Scope Management Plan v2.0.0 (hash `ee97d20993e90c88a5fe7619ed4329d47377e930a7a7cea5c3207e6d5b9c6270`) and Cost Management Plan v2.0.0 (hash `401f0d0fe8a3b7092ec76110946e1fe0bc628efd5a77dbf03300a3b5e7309ebc`).
* **Phase 2 Baseline Alignment:** Formally updated and baselined under `PMP-BL-v1.1.0`.

### 3.3 Procurement Deviation & Escalation Protocol
If technical execution identifies an unavoidable need for an external paid service or library:
1. **Business Justification:** Prepare an ROI rationale explaining why standard library or open-source alternatives are unviable.
2. **Sponsor Review:** Escalate directly to the Project Sponsor via Stage 17 Integrated Change Control (`approve-adaptation-plan`).
3. **Financial Release:** No financial commitment or subscription registration is permitted prior to formal Sponsor sign-off.

---

## 4. Amendment Log

| Date | Author | Description |
|---|---|---|
| 2026-10-25 | Menno Drescher / Antigravity | Initial full baseline Procurement Management Plan replacing stub mock content per ADR-012. |
| 2026-11-01 | Menno Drescher / Antigravity | **v1.1.0 — 6.E approved:** Make-or-Buy analysis completed selecting 100% internal 'Make' sourcing (€143.3k cost avoidance); external temp contractor procurement strictly prohibited; approved external procurement register established; approved under `approve-subsidiary-plan` (Episode `cb44cc0c-c923-4443-883e-6f0608273aa5`). |
| 2026-11-08 | Menno Drescher / Antigravity | **v2.0.0 — PMP-BL-v1.1.0 Phase 2 Formalization:** Updated for Phase 2: Autonomous Feedback Loops & Extensible Architecture; incorporated pure standard library architecture in `agent-training-ext/` eliminating cloud GPU rental needs (>€5,000 cost avoidance); updated Make-or-Buy analysis (€36,960 direct contractor avoidance); aligned financial limits to €19,175.00 baseline economic valuation and ≤€100/mo cash OpEx ceiling; updated upstream DAG links to Scope v2.0.0 and Cost v2.0.0. |
