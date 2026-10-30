---
artifact_id: scope-foundation-pillar-overview-trace
parent_plan_id: scope-management
baseline_id: PMP-BL-v1.0.0
route: foundation_artifact
governance_policy: approve-subsidiary-plan
substage: "6.A-0P"
version: "1.0.0"
owner_role: "Project Manager"
depends_on: []
approval_status: approved
pmbok_process: "Define Scope"
---

# Scope Foundation — Topic Pillars Overview & Trace (`PMP-BL-v1.0.0`)

Connects the **integrated scope baseline** to the project **topic pillar** model in [Project-Pillars.md](../../../Project-Pillars.md) (**Approved** 2026-10-30; gate episode `8fe9fea9-6ef1-44be-82a9-e09677e47a4a`). That document is the sole source of pillar names and statements (Spark, Ideation, Business Case, Benefits). The four-layer doc stack (BRD, ADR, FDD, User Stories) and `docs/adr/README.md` manifesto are **not** topic pillars here.

## Pillar overview (statements)

| Topic pillar | One-line scope hook |
| --- | --- |
| **Frozen-model, in-process learning** | SDK policy layer; no GPU fine-tune job (Epics 12–13, 34, 36, 22). |
| **Earned, auditable autonomy** | Wilson gate, evidence trace, governance chain (Epics 1–7, 9–10, 25–37). |
| **One TaskPolicy for statistical and reasoned resolution** | Low vs full authority under one policy (Epics 1, 4, 7, 11, 21). |
| **Packaged contextual learning** | ContextualSoftmaxPolicy packaged path (Epic 38). |
| **An honest place against SFT, RLVR, and ERL** | Methodology catalog and positioning (Epic 36). |
| **Critique becomes evidence** | Scalar-only REINFORCE gap; Option B track (Epics 14, 18, 10). |
| **A new policy inherits a similar policy's prior** | Warm-start / meta-prior (Epics 19, 20; **M1–M2**). |
| **A repair path for a stuck low-authority decision** | UCB / Thompson / epsilon baseline (Epics 15–17; **M3**). |
| **A hosted layer someone would pay for** | HYP-AL-011 value research only (**M0.5**); not a delivery claim. |

Full statements, sources, and ADR primary assignment: [Project-Pillars.md](../../../Project-Pillars.md).

## Pillar → WBS band → Charter anchor

| Topic pillar | WBS band | Primary epics / anchors | Phase 1? |
| --- | --- | --- | --- |
| Frozen-model, in-process learning | A, E | 1–7, 12–13, 34, 36; 22 (D) | Built + program track |
| Earned, auditable autonomy | A, E | 3, 9–10, 25–37 | Harness **M4**; governance parallel |
| One TaskPolicy… | A, D | 1, 4, 7, 11, 21 | 21 when scheduled |
| Packaged contextual learning | D | 38 | Spec ready; not Charter-primary |
| An honest place against SFT, RLVR, and ERL | A | 36 | Catalog / examples built |
| Critique becomes evidence | C | 14, 18 (+ lessons 10) | **Deferred** until **M5** |
| A new policy inherits… | **B** | 19, 20 | **Authorized M1–M2** |
| A repair path for stuck low-authority… | **B** | 15, 16, 17 | **Authorized M3** |
| A hosted layer someone would pay for | **F** | M0.5, HYP-AL-011 | Charter time-box |

Phase 1 **product scope** (Band **B** + **F**) directly advances three pillar threads: **prior inheritance**, **repair-path bandits**, and **hosted-layer research**, under **earned autonomy** verification (**M4**) and **frozen-model** engineering constraints.

**Milestone sequence (schedule view):** Charter gates run **M1 → M2 → M3 → M4 → M5** on the critical path, with **M0.5** in parallel to **M5**. That order **sequences the primary pillar proofs** (prior at M1–M2, repair at M3, earned harness at M4, critique **decision** at M5). Detail: [Schedule-Pillar-Overview-and-Trace.md](../../schedule-baseline/foundation/Schedule-Pillar-Overview-and-Trace.md) § *How pillars relate to milestone sequence*.

## Pillar ↔ PMBOK §2.2 foundation artifacts

| Foundation artifact | Substage | Pillars primarily substantiated |
| --- | --- | --- |
| [Scope-Project-Scope-Statement.md](Scope-Project-Scope-Statement.md) | 6.A-1 | Prior inheritance, repair path, hosted layer, critique (out-of-scope Phase 1) |
| [Scope-WBS-Dictionary.md](Scope-WBS-Dictionary.md) | 6.A-2 | All nine (100% rule — every epic maps to ≥1 pillar via ADR assignment) |
| [Scope-Monitor-Control-Scope.md](Scope-Monitor-Control-Scope.md) | 6.A-3 | Earned, auditable autonomy |
| [Scope-Validate-Scope.md](Scope-Validate-Scope.md) | 6.A-4 | Earned, auditable autonomy; frozen-model (contract tests) |
| [Scope-Domain-Checklist.md](Scope-Domain-Checklist.md) | 6.A-5 | Cross-cutting |

## Trace rule (RTM extension)

When tracing a WBS row to strategy:

1. **Story** → parent **epic** → epic header **ADR** → [Project-Pillars.md](../../../Project-Pillars.md) **Primary assignment** table → **topic pillar**.
2. **Band** (§1.5 / scope statement) states whether that pillar thread may execute in Phase 1.
3. **Milestone** (§1.6) states which Charter gate consumes the pillar outcome.

At foundation approval, reviewers confirm Band **B** covers Charter **M1–M4** pillar threads and Band **C** holds **Critique becomes evidence** without silent Phase 1 implementation.

## Revision triggers

Reconcile this map when [Project-Pillars.md](../../../Project-Pillars.md) gains or renames a pillar, when the Primary assignment table changes for an in-scope ADR, or when §1.5 execution bands shift (Level 2+ scope change).

**Schedule counterpart:** milestone and weighted-effort view — [Schedule-Pillar-Overview-and-Trace.md](../../schedule-baseline/foundation/Schedule-Pillar-Overview-and-Trace.md) (**6.B-0P**).
