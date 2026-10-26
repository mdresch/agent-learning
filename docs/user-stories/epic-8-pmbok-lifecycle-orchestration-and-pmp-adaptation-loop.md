# Epic 8: PMBOK 8 Lifecycle Orchestration and Closed-Loop Adaptation Feedback

**Source ADR:** [ADR-008](../adr/ADR-008-pmbok-lifecycle-orchestration-and-pmp-adaptation-loop.md) — Accepted (2026-10-24)  
**Governing Baseline:** `PMP-BL-v1.0.0`  
**Source BRD/FDD:** [BRD-008](../project-docs/Business-Requirements/BRD-008-pmbok-lifecycle-orchestration-and-pmp-adaptation-loop.md) / [FDD-008](../project-docs/Functional-Design/FDD-008-pmbok-lifecycle-orchestration-and-pmp-adaptation-loop.md)  

---

## Story 8.1 — Native PMBOK 8 Orchestration Engine and PMP Decision Gate

**Status:** Superseded in part (2026-10-26) by ADR-034 and ADR-013; not to be implemented as written. Acceptance criteria AC_0, AC_1, AC_3 and AC_6 depend on the `pmbok/` package, `scripts/orchestrate_pmbok.py` and the 49 legacy PMBOK tests, which ADR-034 decommissions. The surviving intent (the `approve-pmp` gate, selective adaptation, baseline versioning and rollback) moves to the stories of the epic that implements ADR-034 and ADR-013. Was: Ready (2026-10-24).  
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
- **$AC_7$ (Baseline Versioning & Traceability):** Every approved PMP compiles with a unique SemVer identifier (`PMP-BL-vX.Y.Z`). Downstream requirements (ADRs, BRDs, FDDs, Stories) reference the active baseline. Prior baselines are archived in `management-plans/history/{baseline_id}/`.
- **$AC_8$ (Rollback & Negative Reinforcement):** If an adaptation results in detected regression, the orchestrator restores the prior approved baseline from archive and emits a negative reward to `escalate-diff-response`.
- **$AC_9$ (Configurable Approval Weighting Profiles):** `approve-pmp` decision frames support configurable weighting profiles for standard engineering, regulated, and rapid spike projects.

---

## Out of Scope per BRD-008/FDD-008

- Bypassing human sign-off on PMP baselines.
- Introducing external database schemas.
- Re-executing unaffected subsidiary plans during adaptive cycles.

