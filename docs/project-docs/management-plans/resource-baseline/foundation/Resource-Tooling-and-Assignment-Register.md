---
artifact_id: resource-foundation-tooling-assignment-register
parent_plan_id: resource-management
baseline_id: PMP-BL-v1.1.0
route: foundation_artifact
governance_policy: approve-subsidiary-plan
substage: "6.C-3"
version: "2.0.0"
owner_role: "Project Manager"
depends_on:
  - scope-management
  - schedule-management
approval_status: approved
pmbok_process: "Acquire Resources"
---

# Resource Foundation — Tooling & Assignment Register (`PMP-BL-v1.1.0`)

Catalogs the software toolchains, development environments, and isolated extension workspaces provisioned for **Phase 2: Autonomous Feedback Loops & Extensible Architecture**.

**Historical Baseline Archive:** Frozen Phase 1 tooling register preserved in [`docs/project-docs/history/PMP-BL-v1.0.0/management-plans/resource-baseline/foundation/Resource-Tooling-and-Assignment-Register.md`](../../history/PMP-BL-v1.0.0/management-plans/resource-baseline/foundation/Resource-Tooling-and-Assignment-Register.md).

---

## 1. Tooling & Workspace Inventory (Phase 2)

```mermaid
flowchart TD
    subgraph LocalDev["Developer Workstation Environment (Windows 11 / WSL2)"]
        PY["Python 3.10–3.14 Standard Library Toolchain<br/>(pytest, uv, ruff, mypy)"]
        EXT["Fork-Isolated Workspace: agent-training-ext/<br/>(Critique Ingestion, DPO Loss, Contextual Ensembles)"]
        CORE["Clean Upstream Mirror: src/agent_learning/<br/>(0 Diff vs microsoft/agent-learning HEAD)"]
        MEM["In-Memory & Local LearningStore<br/>(Episode Telemetry)"]
    end

    subgraph ExternalServices["External Channels & AI Endpoints"]
        GH["GitHub OSS Repository & PR Workflows"]
        MPN["Microsoft Partner Network (MPN) Liaison Channel"]
        AI["AI Development Endpoints (Google Antigravity SDK)"]
    end

    AI --> EXT
    EXT --> CORE
    EXT --> MEM
    LocalDev --> GH
    LocalDev --> MPN
```

---

## 2. Resource Assignment Matrix (Phase 2 Epics)

| Epic ID | Work Package Scope | Assigned Technical Lead | AI Pair Assistant | Target Workspace |
|---|---|---|---|---|
| **Epic 14** | Critique Ingestion Engine | Menno Drescher (SH-01) | Antigravity (SH-03) | `agent-training-ext/` |
| **Epic 18** | DPO Pairwise Optimization | Menno Drescher (SH-01) | Antigravity (SH-03) | `agent-training-ext/` |
| **Epic 16 & 21** | Contextual Authority Router | Menno Drescher (SH-01) | Antigravity (SH-03) | `agent-training-ext/` |
| **Epic 22 & 38** | Continuous SIDPA Automation | Menno Drescher (SH-01) | Antigravity (SH-03) | `agent-training-ext/` & `scripts/` |
| **Milestone M10** | Phase 2 Review & Close Gate | Menno Drescher (SH-01) | Quality Auditor (SH-07) | Governance Registry |
