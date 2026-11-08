---
artifact_id: scope-foundation-pillar-overview-trace
parent_plan_id: scope-management
baseline_id: PMP-BL-v1.1.0
route: foundation_artifact
governance_policy: approve-subsidiary-plan
substage: "6.A-0P"
version: "2.0.0"
owner_role: "Project Manager"
depends_on: []
approval_status: approved
pmbok_process: "Define Scope"
---

# Scope Foundation — Topic Pillars Overview & Trace (`PMP-BL-v1.1.0`)

Connects the **integrated scope baseline** for Phase 2 to the project **topic pillar** model in [Project-Pillars.md](../../../Project-Pillars.md) (**Approved**; gate episode `8fe9fea9-6ef1-44be-82a9-e09677e47a4a`).

**Historical Baseline Archive:** Frozen Phase 1 pillar trace preserved in [`docs/project-docs/history/PMP-BL-v1.0.0/management-plans/scope-baseline/foundation/Scope-Pillar-Overview-and-Trace.md`](../../history/PMP-BL-v1.0.0/management-plans/scope-baseline/foundation/Scope-Pillar-Overview-and-Trace.md).

---

## 1. Pillar Overview (Phase 2 Focus)

| Topic Pillar | Phase 2 Scope & WBS Implementation Hook |
|---|---|
| **Frozen-model, in-process learning** | Pure standard library extensions in `agent-training-ext/`; zero GPU fine-tuning; frozen-model Bayesian updates (Epics 14, 18, 22). |
| **Earned, auditable autonomy** | Deterministic Wilson lower bounds; Bayesian gate episodes; zero status drift across registers (Epics 16, 21, 22). |
| **One TaskPolicy for statistical and reasoned resolution** | Unified contextual routing between `low` and `full` authority tiers (Epics 16, 21). |
| **Packaged contextual learning** | Exportable, self-contained contextual policy bundles deployed into downstream agents (Epic 38). |
| **An honest place against SFT, RLVR, and ERL** | Pairwise DPO loss formulations for discrete policies achieving sample efficiency without GPU compute (Epic 18). |
| **Critique becomes evidence** | Tag grammar and exact support shift engine converting reviewer feedback into Bayesian evidence frames (Epic 14, `DEL-P2-01`..`03`). |
| **A new policy inherits a similar policy's prior** | Phase 1 foundation (Warm-start / meta-priors) leveraged across Phase 2 contextual bandits. |
| **A repair path for a stuck low-authority decision** | Phase 1 foundation (UCB / Thompson) extended into multi-armed contextual ensemble routing. |
| **A hosted layer someone would pay for** | Open-source foundation with enterprise-grade governance traceability. |

---

## 2. Pillar → WBS Band → Charter Anchor (Phase 2)

| Topic Pillar | WBS Band | Primary Epics / Anchors | Phase 2 Status |
|---|---|---|---|
| **Critique becomes evidence** | **C** | Epic 14 (Stories 14.1–14.6) | **Authorized (Milestone M6)** |
| **An honest place against SFT...** | **C** | Epic 18 (DPO Loss Engine) | **Authorized (Milestone M7)** |
| **One TaskPolicy…** | **D** | Epics 16, 21 (Contextual Ensembles) | **Authorized (Milestone M8)** |
| **Frozen-model learning** | **D** | Epic 22 (SIDPA Adaptation Loops) | **Authorized (Milestone M9)** |
| **Packaged contextual learning** | **D** | Epic 38 (Packaged Contextual Exports) | **Authorized (Milestone M9)** |
| **Earned, auditable autonomy** | **E / F** | PMBOK Continuous Verification / M10 Close | **Active Governance** |

Phase 2 **product scope** (Bands **C** and **D**) operationalizes the authorized Option B capabilities within `agent-training-ext/` under complete upstream Microsoft fork immunity.

---

## 3. Pillar ↔ PMBOK §2.2 Foundation Artifacts

| Foundation Artifact | Substage | Pillars Primarily Substantiated |
|---|---|---|
| [Scope-Project-Scope-Statement.md](Scope-Project-Scope-Statement.md) | 6.A-1 | Critique becomes evidence, DPO, Contextual Ensembles, Upstream Fork Immunity. |
| [Scope-WBS-Dictionary.md](Scope-WBS-Dictionary.md) | 6.A-2 | All nine (100% rule: every active story maps to a pillar via ADR). |
| [Scope-Monitor-Control-Scope.md](Scope-Monitor-Control-Scope.md) | 6.A-3 | Earned, auditable autonomy; fork cleanliness verification. |
| [Scope-Validate-Scope.md](Scope-Validate-Scope.md) | 6.A-4 | Earned autonomy; pure stdlib and contract test verification. |
| [Scope-Domain-Checklist.md](Scope-Domain-Checklist.md) | 6.A-5 | Cross-cutting PMBOK 8 scope domain outcomes. |

---

## 4. Milestone Sequence Trace (Phase 2)

Charter milestone gates execute sequentially:
$$\text{M6 (Critique Ingestion)} \longrightarrow \text{M7 (DPO Preference)} \longrightarrow \text{M8 (Contextual Ensembles)} \longrightarrow \text{M9 (SIDPA Loops)} \longrightarrow \text{M10 (Phase Close)}$$

Each milestone represents the empirical verification of its governing topic pillars and hypotheses.
