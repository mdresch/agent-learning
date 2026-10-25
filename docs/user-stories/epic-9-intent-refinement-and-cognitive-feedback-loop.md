# Epic 9: Intent Refinement and Cognitive Feedback Loop

**Source ADR:** [ADR-009](../adr/ADR-009-intent-refinement-and-cognitive-feedback-loop.md) — Accepted (2026-10-25)  
**Governing Baseline:** `PMP-BL-v1.0.0`  
**Source BRD/FDD:** [BRD-009](../project-docs/Business-Requirements/BRD-009-intent-refinement-and-cognitive-feedback-loop.md) / [FDD-009](../project-docs/Functional-Design/FDD-009-intent-refinement-and-cognitive-feedback-loop.md)  

---

## Story 9.1 — Phase Close Readiness Gate and Intent Refinement Decision Policy

**Status:** Completed (2026-10-25)  
**As** an autonomous governance orchestrator and PM maintainer,  
**I want** a dedicated `approve-intent-refinement` full-authority decision gate and phase close readiness validator,  
**So that** project phases close with verified empirical evidence, administrative decommissioning occurs cleanly, and Phase $N+1$ Spark directives are authorized by project leadership.

### Acceptance Criteria:
- **$AC_0$ (Readiness Audit Gate):** The readiness evaluator validates that all Stage 9 deliverables are accepted, Stage 11 audit records are free of unresolved non-conformances, and Stage 15 lessons learned are crystallized before Stage 18 evaluation can proceed.
- **$AC_1$ (Full Authority Refinement Gate):** `approve-intent-refinement` is registered under `agent-learning-governance` with `DecisionAuthority.FULL`, multi-criteria Bayesian evaluation, and permanently locked `requires_human_approval: true`.
- **$AC_2$ (Machine-Readable Contract):** The proposal artifact (`Intent-Refinement-Proposal.md`) strictly validates against `IntentRefinementProposalPayload`, enforcing structural completeness, SemVer baseline identifiers, and disposition constraints.
- **$AC_3$ (Administrative Decommissioning):** Under `disposition_type: "project_termination"`, the orchestrator prunes ephemeral git worktrees, revokes temporary runtime credentials, and releases test runners.
- **$AC_4$ (Phase $N+1$ Spark Seeding):** Under `disposition_type: "phase_handoff"`, the orchestrator generates Phase $N+1$ `Spark-Capture.md` and `Ideation-Document.md` populated with approved directives.
- **$AC_5$ (Zero Storage Expansion):** All refinement proposals, decision frames, evaluations, and human sign-off episodes are persisted using ADR-002's five record types as metadata-enriched `Episode` instances.

---

## Story 9.2 — Bayesian Hypothesis Terminality and Recurrence Exhaustion ($d_{\max}=2$)

**Status:** Ready (2026-10-25)  
**As** a principal systems and research architect,  
**I want** hypothesis terminal states strictly bounded by empirical Bayes factors and maximum recurrence depth,  
**So that** defensive hypothesis drift and the "REFINED moral hazard" are eliminated.

### Acceptance Criteria:
- **$AC_6$ (Bayes Factor Adjudication):** Hypotheses with $BF_{10} \ge 10$ resolve to `VALIDATED` and graduate to permanent architectural invariants; hypotheses with $BF_{10} \le 0.1$ resolve to `REFUTED` and are archived with a negative reinforcement penalty.
- **$AC_7$ (Strict Recurrence Depth Guard):** Any hypothesis with `recurrence_depth >= 2` submitted as `REFINED` raises a validation error; it must collapse to `VALIDATED` ($BF_{10} \ge 10$) or default to `REFUTED` ($BF_{10} < 10$).
- **$AC_8$ (Hypothesis Terminality Verification):** No phase may close with lingering `TESTING` or `FORMULATED` hypotheses; 100% of Stage 3 hypotheses resolve to terminal states.

---

## Story 9.3 — Low-Pass Outcome Damping and Cumulative Lineage Kernel

**Status:** Ready (2026-10-25)  
**As** a cybernetics systems control engineer,  
**I want** outcome deltas filtered by an exponential moving average and preserved in a cumulative lineage kernel,  
**So that** the system prevents strategic whiplash and generational epistemic memory decay across project cycles.

### Acceptance Criteria:
- **$AC_9$ (Low-Pass Filter Damping):** Rolling outcome deltas apply exponential smoothing with momentum $\beta \in [0.6, 0.85]$ and bias-corrected warmup for generations $N < 3$.
- **$AC_{10}$ (S3–S4 Capacity Balance):** Strategic pivots are rate-limited such that $\text{Pivots}_{\max} \le \lceil C_{\text{adapt}} / 2 \rceil$.
- **$AC_{11}$ (Cumulative Lineage Kernel):** Every refinement payload carries an immutable lineage kernel preserving `root_spark_id`, `parent_refinement_id`, `immutable_core_invariants`, and `accumulated_knowledge_hash`.
