---
artifact_id: schedule-foundation-pillar-overview-trace
parent_plan_id: schedule-management
baseline_id: PMP-BL-v1.1.0
route: foundation_artifact
governance_policy: approve-subsidiary-plan
substage: "6.B-0P"
version: "2.0.0"
owner_role: "Project Manager"
depends_on:
  - scope-management
approval_status: approved
pmbok_process: "Develop Schedule"
---

# Schedule Foundation — Topic Pillars Overview & Trace (`PMP-BL-v1.1.0`)

Connects the **integrated schedule baseline** for Phase 2 to [Project-Pillars.md](../../../Project-Pillars.md) (**Approved**). Maps Phase 2 milestones (M6 through M10) directly to topic pillar realizations and planned effort.

**Historical Baseline Archive:** Frozen Phase 1 schedule pillar trace preserved in [`docs/project-docs/history/PMP-BL-v1.0.0/management-plans/schedule-baseline/foundation/Schedule-Pillar-Overview-and-Trace.md`](../../history/PMP-BL-v1.0.0/management-plans/schedule-baseline/foundation/Schedule-Pillar-Overview-and-Trace.md).

---

## 1. How Topic Pillars Sequence into Phase 2 Milestones

In Phase 2, each sequential milestone directly realizes and empirically proves one or more topic pillars:

```mermaid
flowchart LR
  M6["Milestone M6<br/><b>Pillar 6:</b> Critique becomes evidence<br/>(Epic 14: 7.5 pd)"]
  M7["Milestone M7<br/><b>Pillar 5:</b> Honest place vs SFT/DPO<br/>(Epic 18: 6.5 pd)"]
  M8["Milestone M8<br/><b>Pillar 3:</b> One TaskPolicy Contextual<br/>(Epics 16 & 21: 8.0 pd)"]
  M9["Milestone M9<br/><b>Pillars 1 & 4:</b> Frozen Learning & Packages<br/>(Epics 22 & 38: 5.5 pd)"]
  M10["Milestone M10<br/><b>Pillar 2:</b> Earned, Auditable Autonomy<br/>(Phase Close: 2.5 pd)"]

  M6 --> M7 --> M8 --> M9 --> M10
```

---

## 2. Milestone Sequence & Pillar Realization Matrix (Phase 2)

| Order | Milestone ID | Predecessor(s) | Primary Topic Pillar Realized | Planned Effort (M pd) | What the Gate Proves |
|---:|---|:---:|---|:---:|---|
| **1** | **M6** | Stage 8 Gate | **Pillar 6: Critique becomes evidence** | 7.5 | Qualitative review tags shift Bayesian pooled support exactly ($\le 10^{-9}$). |
| **2** | **M7** | M6 | **Pillar 5: Honest place against SFT/DPO** | 6.5 | Pairwise DPO loss achieves $\ge 30\%$ sample efficiency gain without GPU compute. |
| **3** | **M8** | M7 | **Pillar 3: One TaskPolicy Contextual Routing** | 8.0 | Contextual multi-armed router dispatches between `low` and `full` tiers with Wilson bounds. |
| **4** | **M9** | M8 | **Pillars 1 & 4: Frozen Learning & Packages** | 5.5 | Automated SIDPA loop operationalized; contextual policies exported for downstream SDKs. |
| **5** | **M10** | M9 | **Pillar 2: Earned, Auditable Autonomy** | 2.5 | 100% tests green; 0 upstream diff; `PCD-Phase2` formally approved. |

**Total Critical Path Planned Effort:** **30.0 person-days** (~180 engineering hours).
