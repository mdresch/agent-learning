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
version: "1.1.0"
baseline_id: "PMP-BL-v1.0.0"
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

# Procurement Management Plan — agent-learning Phase 1: Warm-Start & Confidence-Interval Bandits

> **PMBOK 8 Domain:** `Finance` (Planning Focus Area) | **Legacy Process:** `12.1 Plan Procurement Management`  
> **Governance Policy:** `approve-subsidiary-plan` | **Lifecycle Stage:** `Stage 6 (Planning)`  
> **Route:** `full_plan` | **Baseline Identifier:** `PMP-BL-v1.0.0`  
> **Accountable Role:** Project Manager | **Approving Sponsor:** Menno Drescher  
> **Normative Standard:** [ADR-012](../../adr/ADR-012-subsidiary-management-plan-standards-and-content-contracts.md)

---

## 1. Intent, Alignment & Boundaries

### 1.1 Core Mandate & Zero External Procurement Strategy
This Procurement Management Plan establishes the vendor, licensing, and supply chain governance for **Phase 1: Warm-Start & Confidence-Interval Bandits**. 

In strict alignment with [Project-Charter.md](../Project-Charter.md) §4 and [Cost-Management-Plan.md](Cost-Management-Plan.md), Phase 1 operates under an explicit **Zero External Procurement Strategy**:
1. **Complete Internal Self-Sufficiency:** All algorithmic design, research analysis, software engineering, and verification are conducted entirely by internal project resources (Sponsor, Project Manager, and AI engineering assistants).
2. **Zero Paid Third-Party Contracts:** No external vendors, system integrators, staffing contractors, or consulting firms are engaged for Phase 1 delivery.
3. **Open-Source Software (OSS) Exclusivity:** Software development relies strictly on free, open-source software (FOSS) operating under permissive licensing models.

### 1.2 Boundary Definitions
* **In-Scope Governance:** Open-source dependency vetting; supply chain security analysis; software license compatibility; cloud free-tier quota monitoring.
* **Out-of-Scope Procurement Activities:** The following procurement processes are strictly excluded:
  - Requests for Proposals (RFPs) and formal bidding tenders.
  - Vendor bidding competitions and procurement evaluations.
  - Commercial procurement contracts and enterprise software leasing agreements.

---

### 1.4 PMBOK Input, Process & Output (IPO) Specification
In accordance with PMBOK® Guide 8th Edition (Appendix X4 Procurement & Governance §2.1.6.3):
* **Inputs (PMBOK 8 Appendix X4 & §4):**
  - **Project Charter:** Strategic sourcing direction and budget constraints ([Project-Charter.md](../Project-Charter.md)).
  - **Project Management Plan:** Scope baseline ([Scope-Management-Plan.md](Scope-Management-Plan.md)) and cost envelope ([Cost-Management-Plan.md](Cost-Management-Plan.md)).
  - **Enterprise Environmental Factors (EEFs):** Open-source licensing ecosystem (MIT, Apache, GPL), cloud API pricing, vendor terms.
  - **Organizational Process Assets (OPAs):** ADR standards ([ADR-012](../../adr/ADR-012-subsidiary-management-plan-standards-and-content-contracts.md), [ADR-033](../../adr/ADR-033-procurement-management-plan-standard.md), [ADR-034](../../adr/ADR-034-pmbok-tooling-decommissioning-and-lightweight-learningstore-convergence.md) anti-sprawl).
* **Processes (PMBOK 8 Appendix X4 & §5):**
  - **Plan Sourcing Strategy:** Conducting make-or-buy analysis and establishing third-party dependency intake rules.
  - **Source Selection Analysis:** Evaluating candidate packages and services against capability, cost, and maintenance criteria.
  - **Contract & Licence Review:** Verifying copyleft/commercial licence compatibility and vendor data privacy terms.
  - **Monitor & Control Procurements:** Overseeing dependency health, API quotas, and supplier exit readiness.
* **Outputs (PMBOK 8 Appendix X4 & §4):**
  - **Procurement Management Plan:** `docs/project-docs/management-plans/Procurement-Management-Plan.md`.
  - **Dependency Intake Register:** Recorded justifications and exit paths for third-party runtime dependencies.
  - **Licence Compliance Checklists:** Verified terms for open-source libraries and cloud model subscriptions.

---

## 2. Domain Mechanics & Standards

### 2.1 Open-Source Licensing & Compatibility Governance
To protect the intellectual property and MIT licensing of the `agent-learning` SDK, all third-party software libraries must undergo licensing evaluation prior to inclusion in `pyproject.toml`:

| License Category | Allowed in Production? | Evaluation Criteria & Action |
|---|---|---|
| **Permissive (MIT, Apache 2.0, BSD-2/3, ISC)** | **YES** | Pre-approved for core dependencies and optional extras. Must be attributed in package metadata. |
| **Weak Copyleft (LGPL, MPL)** | **CONDITIONAL** | Allowed only as dynamically linked runtime dependencies; strictly prohibited from static embedding. |
| **Strong Copyleft (GPL v2/v3, AGPL)** | **STRICTLY PROHIBITED** | Incompatible with commercial MIT distribution. Any component importing GPL code is rejected outright. |
| **Proprietary / Commercial** | **PROHIBITED (Phase 1)** | Prohibited unless explicit prior written authorization is granted by the Project Sponsor. |

### 2.2 Supply Chain Security & Dependency Vetting
1. **Automated Vulnerability Ingestion:** All dependencies are continuously monitored via GitHub Dependabot and automated advisory checks.
2. **Deterministic Locking:** Environment builds utilize pinned dependency ranges in `pyproject.toml` and deterministic virtual environment isolation via `uv`.
3. **No Heavyweight System Binaries:** In accordance with **ADR-028**, packages requiring external system-level C-binaries (e.g. `tesseract-ocr`, `poppler`, SQLite C-extensions) are barred from core dependencies.


### 2.3 Make-or-Buy Analysis & Sourcing Strategy Decision

In accordance with PMBOK 8 Appendix X4 and ADR-033 §4.2, the project conducted a formal economic and strategic **Make-or-Buy Analysis** using the labor rates established in [Resource-Capacity-Estimates.md](resource-baseline/foundation/Resource-Capacity-Estimates.md) §5:

#### 1. Sourcing Options Evaluated

1. **Option A (Make — Internal Employees / Maintainer + AI Pair):**
   * Execute all Phase 1 WBS deliverables using internal project resources (Menno Drescher as Principal Researcher/Lead Developer) accelerated by interactive AI engineering assistants (Antigravity/Cursor/Claude).
   * **Economic Valuation:** 115.4 pd $\times$ 6 hrs/pd $\times$ €85.00/hr = **€58,854.00** imputed economic value (**€0.00 cash outlay**).
   * **Tooling / API Outlay:** Capped at **≤ €100.00 / month** (total Phase 1 ~€200.00).
   * **Total Cash Outlay:** **€200.00**.

2. **Option B (Buy — External AI/ML Consultancy / Temp Contractors):**
   * Procure external senior Python / ML contractors to build the multi-armed bandit modules and test suites.
   * **Direct Contractor Outlay:** 115.4 days $\times$ 8 hrs/day $\times$ €135.00/hr = **€124,632.00 cash outlay**.
   * **Procurement & Onboarding Overhead (15%):** **€18,695.00** (vendor selection, contract drafting, knowledge transfer).
   * **Total Cash Outlay:** **€143,327.00**.

3. **Option C (Buy — Commercial Off-the-Shelf SaaS / Proprietary Bandits):**
   * License proprietary commercial experimentation platforms (e.g., Statsig, LaunchDarkly, proprietary contextual bandit engines).
   * **Annual Licensing & Platform Fees:** **€15,000.00 – €30,000.00 / year**.
   * **Architectural Risk:** Violates ADR-002, ADR-028, and ADR-034 standard-library purity and creates unrecoverable external vendor lock-in.

#### 2. Comparative Decision Matrix

| Evaluation Criterion | Weight | Option A (Internal Make) | Option B (External Contractor) | Option C (Commercial SaaS) |
| :--- | :---: | :---: | :---: | :---: |
| **Direct Cash Outlay (€)** | 0.35 | **5 / 5** (€200) | 1 / 5 (€143k) | 2 / 5 (€25k/yr) |
| **Standard-Library Purity (ADR-034)** | 0.25 | **5 / 5** (100% stdlib core) | 3 / 5 (Dependency sprawl risk) | 1 / 5 (Violates ADR-034) |
| **Domain Knowledge Retention** | 0.20 | **5 / 5** (Retained in repo) | 2 / 5 (Exits with contractor) | 1 / 5 (Opaque black box) |
| **Delivery Velocity (AI Pair Multiplier)** | 0.20 | **4.5 / 5** (1.6x–1.8x velocity) | 3 / 5 (Onboarding lag) | 4 / 5 (Immediate API) |
| **Weighted Score** | **1.00** | **4.90 / 5.00** | **2.20 / 5.00** | **1.95 / 5.00** |

#### 3. Formal Sourcing Decision

* **Authoritative Decision:** **100% Internal "Make"**.
* **Contractor Procurement Ruling:** External consultancy and temp contractor procurement is **strictly prohibited** for Phase 1. Zero contractor expense is authorized.
* **Direct Cost Avoidance:** Internal execution achieves **€143,327.00** in direct cash outlay avoidance compared to commercial contractor procurement.

---

### 2.4 Approved External Procurement Register

External acquisitions for Phase 1 are strictly limited to necessary developer toolchains and model API quotas:

| Procurement Item | Category | Vendor / Source | Authorized Limit | Funding Basis | Justification |
| :--- | :--- | :--- | :---: | :--- | :--- |
| **AI Model APIs** | Cloud / SaaS | Anthropic, Google, Azure | **≤ €100.00 / mo** (max €250 total) | Monthly OpEx | Pair engineering generation, reasoning lookups, and `azure-ai-evaluation` benchmarking. |
| **Azure Cosmos DB** | Cloud Hosting | Microsoft Azure | **€0.00** (Local Emulator / Free Tier) | Free Tier | Compliance audit telemetry validation without cloud infrastructure cost. |
| **FOSS Libraries** | Software | PyPI (MIT / Apache 2.0) | **€0.00** | Free OSS | Core scientific and testing toolchains (`numpy`, `pytest`, `ruff`, `mypy`). |
| **Workstation Compute** | Hardware | Local Host System | **€0.00** | Sunk Capital | Zero CapEx workstation execution; saves ~€0.65/hr cloud VM hosting fees. |

---

## 3. Governance, Control & Decision Rights

### 3.1 Accountabilities & Authority Levels
* **Tech Lead / Developer:** Responsible for auditing license types before introducing new dependencies and ensuring zero copyleft contamination.
* **Project Manager:** Accountable for enforcing the zero-procurement boundary and reviewing Dependabot PR security advisories.
* **Project Sponsor (Menno Drescher):** Holds sole sovereign authority to authorize any commercial software expenditure, contract signing, or licensing exception.

### 3.3 Position in the Planning DAG & Baseline Approval (Stage 6.E)
In accordance with ADR-013 §4.1 and ADR-033 §4.1:
$$\text{Scope Management (5.1)} \longrightarrow \text{Cost Management (7.1)} \longrightarrow \text{Procurement Management (12.1)}$$

* **Upstream Baselines:** Scope Management Plan v1.2+ (approved at 6.A-7, hash `3febf6edd1dbed564df2a8618176d32c42ec19a5d02dcf3ea45b594b70cb33a8`) and Cost Management Plan v1.1+ (approved at 6.D-7, hash `4abc8f43b5a49cd1b968df4138992ae3900fd77d4168354c5d63218f6e16489b`).
* **Stage 6.E Approval (2026-11-01):** Approved under `approve-subsidiary-plan` by Project Sponsor Menno Drescher. Episode: `cb44cc0c-c923-4443-883e-6f0608273aa5`.

### 3.2 Procurement Deviation & Escalation Protocol
If technical execution identifies an unavoidable need for an external paid service or dataset:
1. **Business Justification:** Prepare an ROI rationale explaining why open-source alternatives are unviable.
2. **Sponsor Review:** Escalate directly to the Project Sponsor via Stage 17 Integrated Change Control (`approve-adaptation-plan`).
3. **Financial Release:** No financial commitment or subscription registration is permitted prior to formal Sponsor sign-off.

---

## 4. Amendment Log

| Date | Author | Description |
|---|---|---|
| 2026-10-25 | Menno Drescher / Antigravity | Initial full baseline Procurement Management Plan replacing stub mock content per ADR-012. |

| 2026-11-01 | Menno Drescher / Antigravity | **v1.1.0 — 6.E approved:** Make-or-Buy analysis completed selecting 100% internal 'Make' sourcing (€143.3k cost avoidance); external temp contractor procurement strictly prohibited; approved external procurement register established; approved under `approve-subsidiary-plan` (Episode `cb44cc0c-c923-4443-883e-6f0608273aa5`). |
