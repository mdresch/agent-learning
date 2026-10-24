# Epic 8: PMBOK 8 Lifecycle Orchestration and Closed-Loop Adaptation Feedback

**Source ADR:** [ADR-008](../adr/ADR-008-pmbok-lifecycle-orchestration-and-pmp-adaptation-loop.md) — Accepted (2026-10-24)  
**Source BRD/FDD:** [BRD-008](../project-docs/Business-Requirements/BRD-008-pmbok-lifecycle-orchestration-and-pmp-adaptation-loop.md) / [FDD-008](../project-docs/Functional-Design/FDD-008-pmbok-lifecycle-orchestration-and-pmp-adaptation-loop.md)  

---

## Story 8.1 — Native PMBOK 8 Orchestration Engine and PMP Decision Gate

**Status:** Ready (2026-10-24)  
**As** an autonomous project engineering and governance maintainer,  
**I want** the PMBOK 8 orchestration engine and `approve-pmp` decision gate operating natively in `agent-learning`,  
**So that** project baselines are rigorously synthesized and validated before technical specifications are authored, and adaptive feedback loops selectively update affected subsidiary plans upon governance changes.

### Acceptance Criteria:

- **$AC_0$ (Native Engine Integration):** The `pmbok/` package, CLI orchestrator (`scripts/orchestrate_pmbok.py`), and skill definition (`.claude/skills/pmbok-planning/SKILL.md`) run natively within `agent-learning` without external repository dependencies.
- **$AC_1$ (Full Subsidiary Plan Generation):** Running `orchestrate_pmbok.py --mode full` parses `Project-Charter.md`, generates all 9 subsidiary management plans in `docs/project-docs/management-plans/`, and compiles an integrated `Project-Management-Plan.md`.
- **$AC_2$ (Full-Authority PMP Gate):** `approve-pmp` is registered in `agent-learning-governance` under `DecisionAuthority.FULL`, enforcing Bayesian multi-criteria evaluation across completeness, coherence, responsiveness, and traceability, with `requires_human_approval: true`.
- **$AC_3$ (Selective Adaptation Execution):** Running `orchestrate_pmbok.py --mode adapt --adaptation-plan <path>` parses the modified subsidiary plans from the Adaptation Plan and executes *only* the affected process agents, updating `Project-Management-Plan.md` and leaving other plans unchanged.
- **$AC_4$ (Cascading Technical Updates):** Updates to quality, scope, or risk baselines in the PMP trigger re-evaluation of affected technical specifications (ADRs, BRDs, FDDs, Stories) prior to execution gate approval.
- **$AC_5$ (ADR-002 Storage Invariant):** All planning decision frames, evaluations, and human sign-offs are persisted as standard `Episode` records with zero new storage containers or record types.
- **$AC_6$ (Test Suite Verification):** All 49 PMBOK test cases and existing agent-learning unit/contract tests execute cleanly and pass.

---

## Out of Scope per BRD-008/FDD-008

- Bypassing human sign-off on PMP baselines.
- Introducing external database schemas.
- Re-executing unaffected subsidiary plans during adaptive cycles.
