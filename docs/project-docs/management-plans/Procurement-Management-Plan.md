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
version: "1.0.0"
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

---

## 3. Governance, Control & Decision Rights

### 3.1 Accountabilities & Authority Levels
* **Tech Lead / Developer:** Responsible for auditing license types before introducing new dependencies and ensuring zero copyleft contamination.
* **Project Manager:** Accountable for enforcing the zero-procurement boundary and reviewing Dependabot PR security advisories.
* **Project Sponsor (Menno Drescher):** Holds sole sovereign authority to authorize any commercial software expenditure, contract signing, or licensing exception.

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
