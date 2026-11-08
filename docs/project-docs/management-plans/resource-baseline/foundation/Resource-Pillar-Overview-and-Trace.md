---
artifact_id: resource-foundation-pillar-overview-trace
parent_plan_id: resource-management
baseline_id: PMP-BL-v1.1.0
route: foundation_artifact
governance_policy: approve-subsidiary-plan
substage: "6.C-0P"
version: "2.0.0"
owner_role: "Project Manager"
depends_on:
  - scope-management
  - schedule-management
approval_status: approved
pmbok_process: "Plan Resource Management"
---

# Resource Foundation — Topic Pillars Overview & Trace (`PMP-BL-v1.1.0`)

Connects the **integrated resource baseline** for Phase 2 to [Project-Pillars.md](../../../Project-Pillars.md) (**Approved**). Specifies how human, virtual, tooling, and partner resources are mobilized across the strategic outcome threads of Phase 2.

**Historical Baseline Archive:** Frozen Phase 1 resource pillar trace preserved in [`docs/project-docs/history/PMP-BL-v1.0.0/management-plans/resource-baseline/foundation/Resource-Pillar-Overview-and-Trace.md`](../../history/PMP-BL-v1.0.0/management-plans/resource-baseline/foundation/Resource-Pillar-Overview-and-Trace.md).

---

## 1. Resource Allocations by Topic Pillar (Phase 2)

| Topic Pillar | Primary Resource Classes | Accountable Roles | Phase 2 Resource Allocation |
|---|---|---|---|
| **Critique becomes evidence** | Maintainer + AI Pair (`agent-training-ext/`) | Menno Drescher / Antigravity | **Milestone M6 (7.5 pd):** Parser, delta rubric, exact shift engine, replay harness. |
| **An honest place vs SFT/DPO** | Maintainer + AI Pair (`agent-training-ext/`) | Menno Drescher / Antigravity | **Milestone M7 (6.5 pd):** Pairwise DPO loss formulations, offline optimization. |
| **One TaskPolicy Contextual** | Maintainer + AI Pair (`agent-training-ext/`) | Menno Drescher / Antigravity | **Milestone M8 (8.0 pd):** Contextual multi-armed routing, deterministic Wilson bounds. |
| **Frozen Learning & Packages** | Maintainer + AI Pair (`agent-training-ext/`) | Menno Drescher / Antigravity | **Milestone M9 (5.5 pd):** Automated SIDPA runner, packaged contextual policy bundles. |
| **Earned, auditable autonomy** | Sponsor Adjudication + Auditor | Menno Drescher / Quality Auditor | **Milestone M10 (2.5 pd + 5.0 pd reserve):** Clean diff verification, `PCD-Phase2` sign-off. |
| **Fork Collision Protection** | Human Maintainer + MPN Liaison | Menno Drescher (SH-01) | **Continuous (M6–M10):** Microsoft Partner Network coordination, zero upstream diff. |

---

## 2. Resource Mobilization Summary

Phase 2 operates under a strictly **CPU-only, frozen-model** paradigm. Zero GPU compute or cloud cluster infrastructure is allocated or required. All custom code is developed inside `agent-training-ext/`, leveraging maintainer human capacity (120–160 hours) accelerated by Antigravity AI engineering throughput.
