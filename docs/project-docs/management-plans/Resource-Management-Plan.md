---
plan_id: "resource-management"
plan_name: "Resource Management Plan"
pmbok_edition: "PMBOK 8"
pmbok_focus_area: "Planning"
primary_pmbok_domain: "Resources"
secondary_pmbok_domains:
  - "Governance"
legacy_process: "9.1 Plan Resource Management"
route: "full_plan"
generator: "llm"
version: "1.0.0"
baseline_id: "PMP-BL-v1.0.0"
owner_role: "Project Manager"
depends_on:
  - "scope-management"
  - "schedule-management"
inputs:
  - "Project-Charter.md"
  - "docs/project-docs/management-plans/Scope-Management-Plan.md"
  - "docs/project-docs/management-plans/Schedule-Management-Plan.md"
outputs:
  - "docs/project-docs/management-plans/Resource-Management-Plan.md"
governance_policy: "approve-subsidiary-plan"
---

# Resource Management Plan — agent-learning Phase 1: Warm-Start & Confidence-Interval Bandits

> **PMBOK 8 Domain:** `Resources` (Planning Focus Area) | **Legacy Process:** `9.1 Plan Resource Management`  
> **Governance Policy:** `approve-subsidiary-plan` | **Lifecycle Stage:** `Stage 6 (Planning)`  
> **Route:** `full_plan` | **Baseline Identifier:** `PMP-BL-v1.0.0`  
> **Accountable Role:** Project Manager | **Approving Sponsor:** Menno Drescher  
> **Normative Standard:** [ADR-012](../../adr/ADR-012-subsidiary-management-plan-standards-and-content-contracts.md)

---

## 1. Intent, Alignment & Resource Boundaries

### 1.1 Core Mandate & Team Architecture
This Resource Management Plan establishes the resource identification, team roles, physical and virtual infrastructure, and allocation protocols for **Phase 1: Warm-Start & Confidence-Interval Bandits**. 

In strict alignment with [Project-Charter.md](../Project-Charter.md) §4 and §5, the project operates under an agile, high-velocity **human-agent pair engineering** model:
* **Human Sovereign Authority:** Menno Drescher acts as Project Sponsor, Initiator, and Principal Researcher.
* **Autonomous Engineering Pair:** Antigravity / AI Agent Assistants providing interactive coding, test contract synthesis, and governance drafting under human direction.

### 1.2 Boundary Definitions
* **In-Scope Resources:** Developer workstations; local Python 3.10–3.12 virtual environments managed via `uv`; GitHub repository infrastructure; Azure Cosmos DB emulator and development subscription.
* **Out-of-Scope Resources (Zero Sprawl):** External contractor hiring; dedicated physical servers; cloud GPU cluster provisioning; multi-team organizational scaffolding.

---

## 2. Domain Mechanics & Resource Standards

### 2.1 RACI Assignment Matrix
Organizational accountabilities are mapped across the 18-stage lifecycle:

| Lifecycle Activity | Project Sponsor (Menno) | Project Manager | Tech Lead / Dev | AI Coding Assistant |
|---|---|---|---|---|
| **Strategic Intent & Chartering (Stages 1-4)** | **A / R** | C | C | C |
| **Planning & Plan Baselines (Stage 6)** | **A** | **R** | C | C |
| **Technical Specs: ADR / BRD / FDD (Stage 7)** | **A** | C | **R** | C |
| **Story Implementation & Code (Stages 8-9)** | I | C | **R** | **R** |
| **Verification & Testing (Stage 10)** | I | C | **A / R** | R |
| **Lessons Learned Crystallization (Stage 15)** | **A** | **R** | C | C |
| **Governance Change & Adaptation (Stages 16-17)** | **A** | **R** | C | C |
| **Intent Refinement & Bayes Factors (Stage 18)** | **A** | C | **R** | C |

*Legend: **A** = Accountable (Sovereign Authority); **R** = Responsible (Doer); **C** = Consulted; **I** = Informed.*

### 2.2 Physical, Virtual & Tooling Infrastructure
* **Execution Environment:** Windows and Linux developer environments utilizing standard Python toolchains (`uv`, `pytest`, `ruff`, `mypy`).
* **Storage Environment:** Strict compliance with ADR-002: persistence is mediated through `LearningStore` interfaces (in-memory for unit testing, file-based for local development, and Azure Cosmos DB for cloud telemetry). Zero custom relational database instances are permitted (ADR-028).
* **AI Tooling Protocol:** AI coding assistants operate via pull requests and task-directed CLI sessions, strictly adhering to the test-first (observed RED) invariant.

---

## 3. Governance, Control & Decision Rights

### 3.1 Resource Decision Rights & Escalation
* **Work Allocation Authority:** Project Manager assigns technical work packages and tracks velocity against the milestone schedule.
* **Sovereign Resource Ownership:** Menno Drescher holds sole authority over project time commitments, including releasing research hours for M0.5 or expanding Phase 1 allocations.
* **Resource Conflict Resolution:** If technical execution conflicts with qualitative research priorities, M0.5 value research takes precedence to protect the project's strategic ROI foundation.

### 3.2 Skill & Knowledge Management
* **Component Skills Registry:** Institutional knowledge and technical constraints are encapsulated in version-controlled skills (`.claude/skills/`).
* **Lessons Learned Bridge (ADR-010):** Post-coding breakout recaps are held once per epic to crystallize operational traps into actionable invariants, preventing generational amnesia across development handoffs.

---

## 4. Amendment Log

| Date | Author | Description |
|---|---|---|
| 2026-10-25 | Menno Drescher / Antigravity | Initial full baseline Resource Management Plan replacing stub mock content per ADR-012. |
