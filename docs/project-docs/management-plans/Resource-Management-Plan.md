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
version: "1.1.0"
baseline_id: "PMP-BL-v1.0.0"
owner_role: "Project Manager"
depends_on:
  - "scope-management"
  - "schedule-management"
foundation_pack: "docs/project-docs/management-plans/resource-baseline/Resource-Foundation-Pack-Manifest.md"
inputs:
  - "Project-Charter.md"
  - "docs/project-docs/management-plans/Scope-Management-Plan.md"
  - "docs/project-docs/management-plans/Schedule-Management-Plan.md"
outputs:
  - "docs/project-docs/management-plans/Resource-Management-Plan.md"
  - "docs/project-docs/management-plans/resource-baseline/Resource-Foundation-Pack-Manifest.md"
  - "docs/project-docs/management-plans/resource-baseline/foundation/"
governance_policy: "approve-subsidiary-plan"
---

# Resource Management Plan — agent-learning Phase 1: Warm-Start & Confidence-Interval Bandits

> **PMBOK 8 Domain:** `Resources` (Planning Focus Area) | **Legacy Process:** `9.1 Plan Resource Management`  
> **Governance Policy:** `approve-subsidiary-plan` | **Lifecycle Stage:** `Stage 6 (Planning)`  
> **Route:** `full_plan` | **Baseline Identifier:** `PMP-BL-v1.0.0`  
> **Foundation Pack:** [Resource-Foundation-Pack-Manifest.md](resource-baseline/Resource-Foundation-Pack-Manifest.md) (Stage **6.C**)  
> **Accountable Role:** Project Manager | **Approving Sponsor:** Menno Drescher  
> **Normative Standard:** [ADR-012](../../adr/ADR-012-subsidiary-management-plan-standards-and-content-contracts.md) and [ADR-030](../../adr/ADR-030-resource-management-plan-standard.md)  
> **Upstream Baselines:** [Scope-Management-Plan.md](Scope-Management-Plan.md) v1.2+ (**6.A-7**) and [Schedule-Management-Plan.md](Schedule-Management-Plan.md) v1.2+ (**6.B-7**)  
> **Topic Pillars:** [Project-Pillars.md](../Project-Pillars.md); resource trace [Resource-Pillar-Overview-and-Trace.md](resource-baseline/foundation/Resource-Pillar-Overview-and-Trace.md) (**6.C-0P**)

For `PMP-BL-v1.0.0`, the **integrated resource baseline** = approved **[Resource-Foundation-Pack-Manifest.md](resource-baseline/Resource-Foundation-Pack-Manifest.md)** + approved **this plan** (v1.1+). Core mandates, decision rights, and boundaries live here; detailed role catalogues, maintainer capacity models, tooling inventories, team operating charters, and utilization control protocols live under [resource-baseline/foundation/](resource-baseline/foundation/) and are gated per manifest **6.C** checklist before this plan’s first subsidiary approval.

---

## 1. Intent, Alignment & Boundaries

### 1.1 Core Mandate & Team Architecture
This Resource Management Plan establishes the resource identification, team roles, physical and virtual infrastructure, and allocation protocols for **Phase 1: Warm-Start & Confidence-Interval Bandits**. 

In strict alignment with [Project-Charter.md](../Project-Charter.md) §4 and §5, the project operates under an agile, high-velocity **human-agent pair engineering** model:
* **Human Sovereign Authority:** Menno Drescher acts as Project Sponsor, Initiator, and Principal Researcher.
* **Autonomous Engineering Pair:** Antigravity / AI Agent Assistants providing interactive coding, test contract synthesis, and governance drafting under human direction.

### 1.2 Boundary Definitions
* **In-Scope Resources:** Developer workstations; local Python 3.10–3.14 virtual environments managed via `uv`; GitHub repository infrastructure; Azure Cosmos DB emulator and development subscription.
* **Out-of-Scope Resources (Zero Sprawl):** The following resources are strictly excluded:
  - External contractor hiring during Phase 1.
  - Dedicated physical server provisioning.
  - Cloud GPU cluster procurement.
  - Multi-team organizational management scaffolding.

---

### 1.4 PMBOK Input, Process & Output (IPO) Specification
In accordance with PMBOK® Guide 8th Edition (Resources Performance Domain §2.6):
* **Inputs (PMBOK 8 §2.6.2.1, §2.6.2.2 & §4):**
  - **Project Charter:** Key roles, core sponsor limits, and project governance structure ([Project-Charter.md](../Project-Charter.md)).
  - **Project Management Plan:** Scope baseline ([Scope-Management-Plan.md](Scope-Management-Plan.md) v1.2+) and schedule baseline ([Schedule-Management-Plan.md](Schedule-Management-Plan.md) v1.2+).
  - **Enterprise Environmental Factors (EEFs):** Computational capacity, developer workstations, local emulators.
  - **Organizational Process Assets (OPAs):** ADR standards ([ADR-012](../../adr/ADR-012-subsidiary-management-plan-standards-and-content-contracts.md), [ADR-030](../../adr/ADR-030-resource-management-plan-standard.md)) and team charter norms.
* **Processes (PMBOK 8 §2.6.2 & §5):**
  - **Plan Resource Management:** Formulating the role catalogue and human accountability structure ([Resource-Role-Catalogue.md](resource-baseline/foundation/Resource-Role-Catalogue.md)).
  - **Estimate Resources:** Estimating required human effort and agent/tooling quotas per timebox ([Resource-Capacity-Estimates.md](resource-baseline/foundation/Resource-Capacity-Estimates.md)).
  - **Acquire Resources:** Staffing roles and provisioning tooling assets with lead times ([Resource-Tooling-and-Assignment-Register.md](resource-baseline/foundation/Resource-Tooling-and-Assignment-Register.md)).
  - **Lead the Team & Control Resourcing:** Managing autonomous agent boundaries ([Resource-Team-Operating-Charter.md](resource-baseline/foundation/Resource-Team-Operating-Charter.md)) and resolving capacity conflicts ([Resource-Utilization-and-Control-Protocol.md](resource-baseline/foundation/Resource-Utilization-and-Control-Protocol.md)).
* **Outputs (PMBOK 8 §2.6.2 & §4):**
  - This Resource Management Plan.
  - **Integrated Resource Baseline:** [Resource-Foundation-Pack-Manifest.md](resource-baseline/Resource-Foundation-Pack-Manifest.md) v1.1+ and seven approved foundation breakout artifacts.
  - Project Role Catalogue, RACI Matrix, and agent work boundaries.

---

## 2. Domain Mechanics & Standards

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

*Legend: **A** = Accountable (Sovereign Authority); **R** = Responsible (Doer); **C** = Consulted; **I** = Informed.* Detailed role catalogue in [Resource-Role-Catalogue.md](resource-baseline/foundation/Resource-Role-Catalogue.md) (**6.C-1**).

### 2.2 Physical, Virtual & Tooling Infrastructure
* **Execution Environment:** Windows and Linux developer environments utilizing standard Python toolchains (`uv`, `pytest`, `ruff`, `mypy`). Complete inventory in [Resource-Tooling-and-Assignment-Register.md](resource-baseline/foundation/Resource-Tooling-and-Assignment-Register.md) (**6.C-3**).
* **Storage Environment:** Strict compliance with ADR-002: persistence is mediated through `LearningStore` interfaces (in-memory for unit testing, file-based for local development, and Azure Cosmos DB for cloud telemetry). Zero custom relational database instances are permitted (ADR-028).
* **AI Tooling Protocol:** AI coding assistants operate via pull requests and task-directed CLI sessions, strictly adhering to the test-first (observed RED) invariant. Team norms defined in [Resource-Team-Operating-Charter.md](resource-baseline/foundation/Resource-Team-Operating-Charter.md) (**6.C-4**).

### 2.3 Integrated Resource Baseline & Readiness

The official **integrated resource baseline** for `PMP-BL-v1.0.0` comprises:

1. **[Resource-Foundation-Pack-Manifest.md](resource-baseline/Resource-Foundation-Pack-Manifest.md)** (Stage **6.C-7** roll-up; registry hashes for seven breakout artifacts).
2. **Resource Management Plan** (this document, **v1.1.0** — subsidiary approval at manifest **6.C-8**).
3. **6.C-0P — Pillar trace:** [Resource-Pillar-Overview-and-Trace.md](resource-baseline/foundation/Resource-Pillar-Overview-and-Trace.md).
4. **6.C-1 — Role catalogue:** [Resource-Role-Catalogue.md](resource-baseline/foundation/Resource-Role-Catalogue.md).
5. **6.C-2 — Capacity estimates:** [Resource-Capacity-Estimates.md](resource-baseline/foundation/Resource-Capacity-Estimates.md).
6. **6.C-3 — Tooling register:** [Resource-Tooling-and-Assignment-Register.md](resource-baseline/foundation/Resource-Tooling-and-Assignment-Register.md).
7. **6.C-4 — Team charter:** [Resource-Team-Operating-Charter.md](resource-baseline/foundation/Resource-Team-Operating-Charter.md).
8. **6.C-5 — Utilization protocol:** [Resource-Utilization-and-Control-Protocol.md](resource-baseline/foundation/Resource-Utilization-and-Control-Protocol.md).
9. **6.C-6 — Domain checklist:** [Resource-Domain-Checklist.md](resource-baseline/foundation/Resource-Domain-Checklist.md).

**6.C-8 Approved (2026-11-01):** Upstream Scope **6.A-7** and Schedule **6.B-7** are **approved** (**6.C-0** satisfied). Foundation breakouts **6.C-0P … 6.C-6** are **approved**; manifest **6.C-7** is complete (`pack_status: approved` on manifest **v1.1.0**). This plan **v1.1.0** is **approved** under **`approve-subsidiary-plan`** (**6.C-8**). BFI-003 closed as `applied`. Approval Episode `ebf812e6-d3c2-4773-918f-22a7b447cbe9`.

---

## 3. Governance, Control & Decision Rights

### 3.1 Resource Decision Rights & Escalation
* **Work Allocation Authority:** Project Manager assigns technical work packages and tracks velocity against the milestone schedule.
* **Sovereign Resource Ownership:** Menno Drescher holds sole authority over project time commitments, including releasing research hours for M0.5 or expanding Phase 1 allocations.
* **Resource Conflict Resolution:** If technical execution conflicts with qualitative research priorities, M0.5 value research takes precedence to protect the project's strategic ROI foundation. Complete protocols in [Resource-Utilization-and-Control-Protocol.md](resource-baseline/foundation/Resource-Utilization-and-Control-Protocol.md) (**6.C-5**).

### 3.2 Skill & Knowledge Management
* **Component Skills Registry:** Institutional knowledge and technical constraints are encapsulated in version-controlled skills (`.claude/skills/`).
* **Lessons Learned Bridge (ADR-010):** Post-coding breakout recaps are held once per epic to crystallize operational traps into actionable invariants, preventing generational amnesia across development handoffs.

### 3.3 Transitive Downstream Invalidation (ADR-013 §4.5)
In the planning directed acyclic graph (`PLAN_DAG`):
$$\text{Scope Management Plan} \longrightarrow \text{Schedule Management Plan} \longrightarrow \text{Resource Management Plan}$$

Resource Management has no dependent plans in `PLAN_DAG`. Upstream changes to Scope or Schedule that alter work breakdown or durations mark this Resource plan **`STALE_DEPENDENCY`** until re-verified before `approve-pmp`.

---

## Baseline Feedback (Stage 7-8 → 6)

| bfi_id | stage | document | citation | classification | evidence_basis | status |
| --- | ---: | --- | --- | --- | --- | --- |
| BFI-003 | 7 | Resource Management Plan / foundation pack | [ADR-030](../../adr/ADR-030-resource-management-plan-standard.md) §3; [Resource-Foundation-Pack-Manifest.md](resource-baseline/Resource-Foundation-Pack-Manifest.md) § Stage 6.C | *(empty — process interpretation)* | design_time | applied |

**BFI-003 (applied 2026-11-01):** ADR-030 §3 states Resource baselining has no upfront breakout prerequisite. For this repository, **Tier-1 Resource foundation pack** artifacts under Stage **6.C** (PMBOK §2.6 Plan / Estimate / Acquire / Lead / Control) are **normative** for the first `approve-subsidiary-plan` on `resource-management` v1.1+: integrated baseline = manifest + plan. Documented Path A without amending ADR-030. Applied when **6.C-8** completed; sponsor approval is recorded in Episode `ebf812e6-d3c2-4773-918f-22a7b447cbe9`.

---

## 4. Amendment Log

| Date | Author | Description |
|---|---|---|
| 2026-10-25 | Menno Drescher / Antigravity | Initial full baseline Resource Management Plan replacing stub mock content per ADR-012. |
| 2026-11-01 | Menno Drescher / Antigravity | **v1.1.0 — Foundation pack integration:** Linked `foundation_pack` manifest; §2.3 integrated baseline definition; 7 breakout artifacts under `resource-baseline/foundation/`; BFI-003 added; plan ready for **6.C-8** after Scope 6.A-7 and Schedule 6.B-7. |
| 2026-11-01 | Menno Drescher | **6.C-8 approved:** Resource Management Plan v1.1.0 approved under `approve-subsidiary-plan`; BFI-003 applied. Approval Episode `ebf812e6-d3c2-4773-918f-22a7b447cbe9`; canonical content hash recorded in the approval Episode. |
