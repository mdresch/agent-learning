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
version: "2.0.0"
baseline_id: "PMP-BL-v1.0.1"
target_baseline_id: "PMP-BL-v1.1.0"
owner_role: "Project Manager"
depends_on:
  - "scope-management"
  - "schedule-management"
foundation_pack: "docs/project-docs/management-plans/resource-baseline/Resource-Foundation-Pack-Manifest.md"
inputs:
  - "Project-Charter.md"
  - "docs/project-docs/Stakeholder-Register.md"
  - "docs/project-docs/management-plans/Scope-Management-Plan.md"
  - "docs/project-docs/management-plans/Schedule-Management-Plan.md"
outputs:
  - "docs/project-docs/management-plans/Resource-Management-Plan.md"
  - "docs/project-docs/management-plans/resource-baseline/Resource-Foundation-Pack-Manifest.md"
  - "docs/project-docs/management-plans/resource-baseline/foundation/"
governance_policy: "approve-subsidiary-plan"
---

# Resource Management Plan — agent-learning Phase 2: Autonomous Feedback Loops & Extensible Architecture

> **PMBOK 8 Domain:** `Resources` (Planning Focus Area) | **Legacy Process:** `9.1 Plan Resource Management`  
> **Governance Policy:** `approve-subsidiary-plan` | **Lifecycle Stage:** `Stage 6 (Planning: Resource Baseline)`  
> **Route:** `full_plan` | **Baseline Identifier:** `PMP-BL-v1.0.1` (targeting `PMP-BL-v1.1.0`)  
> **Foundation Pack:** [Resource-Foundation-Pack-Manifest.md](resource-baseline/Resource-Foundation-Pack-Manifest.md) (Stage **6.C**)  
> **Accountable Role:** Project Manager / PMBOK Steward | **Approving Sponsor:** Menno Drescher  
> **Normative Standard:** [ADR-012](../../adr/ADR-012-subsidiary-management-plan-standards-and-content-contracts.md) and [ADR-030](../../adr/ADR-030-resource-management-plan-standard.md)  
> **Upstream Baselines:** [Scope-Management-Plan.md](Scope-Management-Plan.md) v2.0.0 and [Schedule-Management-Plan.md](Schedule-Management-Plan.md) v2.0.0  
> **Master Stakeholder Register:** [Stakeholder-Register.md](../Stakeholder-Register.md) v2.0  
> **Historical Baseline Archive:** Frozen Phase 1 resource plan preserved in [`docs/project-docs/history/PMP-BL-v1.0.0/management-plans/Resource-Management-Plan.md`](../history/PMP-BL-v1.0.0/management-plans/Resource-Management-Plan.md)  

For `PMP-BL-v1.1.0`, the **integrated resource baseline** = approved **[Resource-Foundation-Pack-Manifest.md](resource-baseline/Resource-Foundation-Pack-Manifest.md)** + approved **this plan** (v2.0.0). Phase 2 operationalizes the maintainer human resource commitment (120–160 hours across Milestones M6–M10), AI pair programming throughput, and fork-isolated extension workspace provisioning.

---

## 1. Intent, Alignment & Boundaries

### 1.1 Core Mandate & Team Architecture
This Resource Management Plan establishes the team roles, physical and virtual workspaces, and allocation protocols for **Phase 2: Autonomous Feedback Loops & Extensible Architecture**.

In strict alignment with [Project-Charter.md](../Project-Charter.md) v2.0 §4 and [Stakeholder-Register.md](../Stakeholder-Register.md) v2.0:
* **Human Sovereign Authority (SH-01):** Menno Drescher acts as Project Sponsor, Maintainer, and MPN Microsoft Liaison.
* **PMBOK Process Steward (SH-02):** Project Manager accountable for baseline custody, phase rollups, and zero status drift.
* **AI Engineering Pair (SH-03):** Antigravity provides high-throughput test authoring, AST parsing, and stdlib implementations.
* **Upstream Microsoft Maintainers (SH-06):** External maintainer community (`MargoOs`, `adityasinha-aiplan`, `meiwa7`) engaged via clean fork boundaries and MPN channels.

### 1.2 Boundary Definitions (Phase 2)
* **In-Scope Resources:** Developer workstations (Python 3.10–3.14, uv, pytest); isolated `agent-training-ext/` package structure; local `LearningStore` file-based telemetry; GitHub PR workflows.
* **Out-of-Scope Resources (Zero Sprawl):** Strictly excludes external contractor spend, dedicated cloud GPU clusters, proprietary database infrastructure, and unmanaged microservices.

---

## 2. Domain Mechanics & Standards

### 2.1 RACI Assignment Matrix (Phase 2)

| Lifecycle Stage | Sponsor (SH-01) | PM (SH-02) | Lead Agent (SH-03) | Reviewers (SH-04) | Upstream (SH-06) | Auditor (SH-07) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Charter & Strategic Intent (Stages 1–4)** | **Accountable (A)** | Responsible (R) | Consulted (C) | Informed (I) | Informed (I) | Informed (I) |
| **Stakeholder & Subsidiary Baselines (Stages 5–6)** | **Accountable (A)** | Responsible (R) | Consulted (C) | Consulted (C) | Consulted (C) | Consulted (C) |
| **Integrated PMP Baseline `PMP-BL-v1.1.0` (Stage 7)** | **Accountable (A)** | Responsible (R) | Consulted (C) | Consulted (C) | Informed (I) | Consulted (C) |
| **Implementation Readiness Authorization (Stage 8)** | **Accountable (A)** | Responsible (R) | Consulted (C) | Consulted (C) | Informed (I) | Consulted (C) |
| **Story Code & Contract Tests (Stages 9–10)** | Informed (I) | Consulted (C) | **Responsible (R)** | **Accountable (A)** | Informed (I) | Responsible (R) |
| **Audit & Phase Close (Stages 11–18)** | **Accountable (A)** | Responsible (R) | Responsible (R) | Consulted (C) | Consulted (C) | **Responsible (R)** |

### 2.2 Capacity Allocation & Burnout Safeguards
* Human maintainer capacity commitment: **120–160 engineering hours** across Milestones M6–M10 (~5 person-days per week).
* AI pair programming acceleration reduces manual authoring toil by ~2.5x.
* Unrecorded maintainer overtime is strictly prohibited; capacity strain triggers formal descope/reschedule protocols.

---

## 3. Governance, Control & Decision Rights

* **Project Manager:** Accountable for capacity monitoring, tracking story velocity, and managing tooling allocations.
* **Project Sponsor (Menno Drescher):** Retains sovereign sign-off on resource baseline formalization and team operating agreements.

---

## 4. Amendment Log

| Date | Author | Description |
|---|---|---|
| 2026-10-25 | Menno Drescher / Antigravity | Initial full baseline Resource Management Plan replacing stub mock content per ADR-012 and ADR-030. |
| 2026-11-01 | Menno Drescher / Antigravity | **v1.1.0 — 6.C approved:** Integrated Resource foundation pack; approved under `approve-subsidiary-plan` (Episode `ebf812e6-d3c2-4773-918f-22a7b447cbe9`). |
| 2026-11-08 | Menno Drescher / Antigravity | **v2.0.0 — Phase 2 Resource Formalization:** Advanced to `v2.0.0` for Phase 2 under `PMP-BL-v1.0.1` targeting `PMP-BL-v1.1.0`. Aligned role taxonomy to 7 authoritative roles in Stakeholder Register v2.0, codified Upstream Microsoft Maintainer engagement, provisioned isolated `agent-training-ext/` workspace, and reconciled 120–160 hour maintainer capacity across M6–M10. |
