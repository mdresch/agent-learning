# BRD-008: PMBOK 8 Lifecycle Orchestration and Closed-Loop Adaptation Feedback

**Source ADR:** [ADR-008](../../adr/ADR-008-pmbok-lifecycle-orchestration-and-pmp-adaptation-loop.md) — Accepted (2026-10-24)  
**Status:** Draft — business requirements derived from an Accepted ADR  
**Stakeholders:** Menno (Sponsor/PM/maintainer)  

## Business Need

On the 18-stage Intent-to-Outcome Chain (`PROJECT-MANAGEMENT-ONTOLOGY.json`), Stage 16 (**Governance Change**) mechanics were formalized by ADR-007 via paired diff classification and escalation. However, once a governance amendment is validated, an operational disconnect arises if that amendment remains an isolated text diff: how does that amendment adapt the project's living governance baselines, and how do those adaptations cascade into subsequent development cycles?

In enterprise project management standards (PMBOK 8 / Process Groups Practice Guide), project artifacts follow strict dependency ordering:
- Initiating documents (Business Case, Benefits Statement, Ideation) are mandatory inputs to the **Project Charter** (Process 4.1).
- The Project Charter is a mandatory input to the **Project Management Plan (PMP)** (Process 4.2), which synthesizes the 9 subsidiary management plans (Scope, Schedule, Cost, Quality, Resource, Communications, Risk, Procurement, Stakeholder).
- The PMP establishes the approved baselines that govern technical requirement authoring (ADR, BRD, FDD, User Stories; Processes 5.2, 5.3, 5.4).

This BRD establishes native **PMBOK 8 Lifecycle Orchestration** and a **Closed-Loop Adaptation Cycle** within `agent-learning`:
1. **Native PMBOK 8 Planning Orchestration:** Direct integration of the 9 PMBOK subsidiary management plans into an integrated `Project-Management-Plan.md`.
2. **Dedicated Full-Authority Decision Gate (`approve-pmp`):** Bayesian multi-criteria evaluation of the integrated PMP baselines before technical requirements are authorized for drafting.
3. **Closed-Loop Adaptation Feedback (Stage 17 $\rightarrow$ Stage 6 $\rightarrow$ Stage 7):** When a Stage 16 Governance Change is accepted, the Stage 17 `Adaptation-Plan.md` itemizes affected subsidiary plans. The orchestrator re-executes only those process agents, updates `Project-Management-Plan.md`, re-evaluates `approve-pmp`, and cascades amendments into technical specifications.

## Business Rules (BRU)

- **BRU-008-01 (Strict Authoring Sequence):** The document build order must follow the PMBOK 8 Input-Process-Output (IPO) dependency flow:
  `Spark (Intent) → Ideation (Hypothesis) → Business Case & Benefits (Benefit) → Project Charter (Objective) → Subsidiary Plans & PMP (Project) → ADR/BRD/FDD/Stories (Requirements)`.
- **BRU-008-02 (Full Authority for PMP Gate):** `approve-pmp` must operate under `DecisionAuthority.FULL` using Bayesian multi-criteria decision reasoning, with `requires_human_approval: true`.
- **BRU-008-03 (Selective Adaptation Re-Execution):** When running in adaptive mode (`--mode adapt`), the orchestrator must parse the Stage 17 `Adaptation-Plan.md`, determine the exact subset of affected PMBOK processes, and execute only those corresponding process agents, leaving unaffected subsidiary plans untouched.
- **BRU-008-04 (PMP Synthesis Invariant):** After any subsidiary plan update (initial or adaptive), the orchestrator must re-synthesize `Project-Management-Plan.md` to ensure global baseline consistency across Scope, Schedule, Cost, Quality, and Risk.
- **BRU-008-05 (Cascading Technical Updates):** When a subsidiary plan affecting technical execution (such as Quality, Scope, or Risk) is amended via the adaptation loop, the orchestrator or maintainer must trigger re-evaluation of affected technical requirements (ADRs, BRDs, FDDs, Stories) before entering the execution gate (Stage 8).
- **BRU-008-06 (Zero Storage Expansion):** The orchestration engine, PMP gate, and adaptation records must introduce zero new Cosmos DB containers, zero new SQL tables, and zero new `LearningStore` record types (preserving ADR-002 Invariant #2). All operational records must be captured as standard `Episode` instances.

## Stakeholder Success Metrics

| Metric | Target |
|---|---|
| PMBOK Subsidiary Plan Coverage | 100% of 9 subsidiary plans (Scope, Schedule, Cost, Quality, Resource, Comms, Risk, Procurement, Stakeholder) generated and synthesized into PMP |
| Adaptive Re-Execution Precision | 100% selective execution in `--mode adapt` (only modified subsidiary plans re-run) |
| Governance Sign-Off Enforcement | 0 autonomous bypasses of `approve-pmp` (`requires_human_approval: true` permanently enforced) |
| Feedback Loop Closure | 100% of accepted Stage 16 changes linked to Stage 17 adaptation and PMP baseline revision |
| Storage Boundary Compliance | 0 new record types or storage containers added to `LearningStore` |

## Out of Scope

- Bypassing human sign-off for baseline plan approvals.
- Creating custom database schemas or non-`Episode` persistence layers.
- Direct code execution without prior technical requirement sign-off.
