---
artifact_id: scope-foundation-project-scope-statement
parent_plan_id: scope-management
baseline_id: PMP-BL-v1.0.0
route: foundation_artifact
governance_policy: approve-subsidiary-plan
substage: "6.A-1"
version: "1.0.0"
owner_role: "Project Manager"
depends_on: []
approval_status: approved
pmbok_process: "Define Scope"
---

# Scope Foundation — Project Scope Statement (`PMP-BL-v1.0.0`)

PMBOK 8 **Scope Performance Domain** §2.2 — **Define Scope**. Approved scope statement for `PMP-BL-v1.0.0`, traced to [Project-Charter.md](../../../Project-Charter.md) Phase 1 *Warm-Start & Confidence-Interval Bandits*.

**Topic pillars:** See [Scope-Pillar-Overview-and-Trace.md](Scope-Pillar-Overview-and-Trace.md) for the nine pillars from [Project-Pillars.md](../../../Project-Pillars.md), mapped to WBS bands and milestones. Phase 1 executes **prior inheritance**, **repair-path bandits**, and **M0.5 hosted-layer research**; **critique becomes evidence** stays Band **C** until **M5**.

## Charter objectives (Phase 1)

1. **Unverified Dependency Resolution (M1):** `SoftmaxPolicy` structured state reusable as prior (Epic 20 path).
2. **Warm-Start Validation (M2, HYP-AL-008):** Prior warm-start vs cold uniform prior (Epics 19, 20).
3. **CI Bandit Autonomy (M3, HYP-AL-009):** UCB or Thompson under positive-only evidence (Epics 15–17).
4. **Phase 2 Gate (M5):** Empirical Option B decision (critique-to-evidence / DPO).
5. **End-User Value (M0.5):** 40-hour qualitative case analysis (Charter §5).

## In-scope deliverables (Phase 1 modules)

| Anchor | Deliverable |
| --- | --- |
| **M0.5** | Qualitative case studies; HYP-AL-011 in Research Log |
| **M1** | Softmax export/import serializers; inspection report |
| **M2** | Hierarchical prior seeding in `src/agent_learning/`; warm-start fixtures |
| **M3** | UCB-1 and Thompson resolvers under positive-only rewards |
| **M4** | 146-episode autonomy harness vs REINFORCE baseline |
| **M5** | Bayes factors for HYP-AL-008/009; Stage 18 decision frame |

## Mandatory out-of-scope (Phase 1)

* Option B implementation (DPO, critique parsers) — Phase 2 after M5.
* Multi-modal / OCR ingestion.
* New relational DB infrastructure (ADR-002, ADR-028).
* FastAPI / Uvicorn production hosting.
* Unbounded production RL without human gates.

## Program vs Phase 1 execution authorization

The [WBS dictionary](Scope-WBS-Dictionary.md) lists the **full program**. Bands below state **when work may start** without baseline change.

| Band | Epics (indicative) | Authorization |
| --- | --- | --- |
| **A** | 1–7, 9–13, 36 | Built or superseded; DoD applies |
| **B** | 15–17, 19–20; harness 9–10 | **Phase 1 authorized** (M2–M4) |
| **C** | 14, 18 | **Not authorized in Phase 1** (Level 3 to open) |
| **D** | 21, 22, 38 | Spec approved; schedule when planned |
| **E** | 25–35, 37, 34 | PMBOK / program parallel track |
| **F** | M0.5, M5 | Charter gates (not epic-decomposed) |

## Milestone to WBS trace

| Milestone | Primary WBS anchor |
| --- | --- |
| **M0.5** | Charter §5; HYP-AL-011 |
| **M1** | Epic 20; M1 report |
| **M2** | Epics 19, 20 |
| **M3** | Epics 15, 16 |
| **M4** | Stories 9.1, 10.1; synthetic fixture |
| **M5** | Story 9.1 / Stage 18; unlocks Band C if approved |

Listing a story in the WBS does **not** authorize implementation when its band is deferred (Band C).
