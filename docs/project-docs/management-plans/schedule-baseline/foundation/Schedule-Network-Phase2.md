---
artifact_id: schedule-foundation-network-phase2
parent_plan_id: schedule-management
baseline_id: PMP-BL-v1.1.0
route: foundation_artifact
governance_policy: approve-subsidiary-plan
substage: "6.B-2"
version: "2.0.0"
owner_role: "Project Manager"
depends_on:
  - scope-management
approval_status: approved
pmbok_process: "Develop Schedule"
---

# Schedule Foundation — Phase 2 Logic Network (`PMP-BL-v1.1.0`)

Precedence diagram method (PDM) network for **Charter Phase 2: Autonomous Feedback Loops & Extensible Architecture** (Scope Bands **C** and **D**).

**Historical Baseline Archive:** Frozen Phase 1 logic network preserved in [`docs/project-docs/history/PMP-BL-v1.0.0/management-plans/schedule-baseline/foundation/Schedule-Network-Phase1.md`](../../history/PMP-BL-v1.0.0/management-plans/schedule-baseline/foundation/Schedule-Network-Phase1.md).

---

## 1. Milestone Critical Path (Phase 2)

Critical path executes sequentially across the 5 authorized Phase 2 milestones:
$$\text{Stage 8 Authorization} \longrightarrow \text{M6 (Critique Ingestion)} \longrightarrow \text{M7 (DPO Preference)} \longrightarrow \text{M8 (Contextual Ensembles)} \longrightarrow \text{M9 (SIDPA Loops)} \longrightarrow \text{M10 (Phase Close)}$$

---

## 2. Epic & Milestone Precedence Network

```mermaid
flowchart TD
  S8["Stage 8: Implementation Readiness Authorization<br/>(validate-intent-foundation)"]
  
  subgraph M6_BOX["Milestone M6: Critique Ingestion Engine (Epic 14)"]
    E14_1["14.1: Tag Grammar Parser"] --> E14_2["14.2: Delta Rubric & Exact Shift"]
    E14_2 --> E14_3["14.3: Doubt & Option Applicator"]
    E14_3 --> E14_4["14.4: Metadata Serializer"]
    E14_4 --> E14_5["14.5: Tagging CLI"]
    E14_5 --> E14_6["14.6: Review Replay Benchmark"]
    E14_6 --> M6["M6 Gate Join (0 pd)"]
  end

  subgraph M7_BOX["Milestone M7: DPO Preference Engine (Epic 18)"]
    E18_1["18.1: Pairwise Dataset Pipeline"] --> E18_2["18.2: Discrete DPO Loss Engine"]
    E18_2 --> E18_3["18.3: Offline Policy Loop"]
    E18_3 --> E18_4["18.4: Sample Efficiency Benchmark"]
    E18_4 --> M7["M7 Gate Join (0 pd)"]
  end

  subgraph M8_BOX["Milestone M8: Contextual Routing (Epics 16 & 21)"]
    E16_1["16.1: Feature Extraction"] --> E16_2["16.2: Wilson Bound Ensemble"]
    E16_2 --> E21_1["21.1: Multi-Armed Router"]
    E21_1 --> E21_2["21.2: Boundary Fallback"]
    E21_2 --> E21_5["21.5: Contextual Benchmark"]
    E21_5 --> M8["M8 Gate Join (0 pd)"]
  end

  subgraph M9_BOX["Milestone M9: Continuous SIDPA & Packages (Epics 22 & 38)"]
    E22_1["22.1: Automated Loop Runner"] --> E22_2["22.2: Adaptation Trigger"]
    E38_1["38.1: Packaged Exporter"] --> E38_2["38.2: SDK Importer"]
    E22_2 & E38_2 --> E22_4["22.4: Loop Replay Validation"]
    E22_4 --> M9["M9 Gate Join (0 pd)"]
  end

  subgraph M10_BOX["Milestone M10: Phase 2 Review & Close Gate"]
    REG["10.1: Full Regression Green"] --> FORK["10.2: Upstream Fork Diff = 0"]
    FORK --> PCD["10.3: PCD-Phase2 Close Package"]
    PCD --> M10["M10 Gate Join (0 pd)"]
  end

  S8 --> E14_1
  M6 --> E18_1
  M7 --> E16_1
  M8 --> E22_1 & E38_1
  M9 --> REG
```

All implementation activities occur strictly within `agent-training-ext/`, maintaining `src/agent_learning` diff = 0.
