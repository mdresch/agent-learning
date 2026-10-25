---
name: intent-refinement
description: PMBOK 8 Stage 18 Intent Refinement, Phase Close readiness evaluation, Bayesian hypothesis adjudication, and double-loop cognitive feedback.
---

# Component: intent-refinement (`pmbok.models.intent_refinement` & `scripts.orchestrate_pmbok`)

**Governing:** ADR-009, BRD-009, FDD-009, Epic 9 (Stories 9.1 & 9.2).  
**Contract:** `tests/pmbok/test_intent_refinement.py`.  
**Baseline:** `PMP-BL-v1.0.0`.

## Load-bearing constraints

- **Readiness Audit Precondition ($AC_0$):** `evaluate_phase_close_readiness()` enforces that all Stage 9 deliverables are accepted, Stage 11 audit records are free of unresolved non-conformances, and Stage 15 lessons learned are crystallized before Stage 18 evaluation can proceed. Any violation raises `ReadinessPreconditionError`.
- **Full-Authority Refinement Gate ($AC_1$):** `approve-intent-refinement` is registered under `agent-learning-governance` with `DecisionAuthority.FULL`, multi-criteria Bayesian evaluation, and permanently locked `requires_human_approval: true`.
- **Machine-Readable Contract ($AC_2$):** The proposal artifact (`Intent-Refinement-Proposal.md`) strictly validates against `IntentRefinementProposalPayload`, enforcing structural completeness, SemVer baseline identifiers (`PMP-BL-vX.Y.Z`), and disposition constraints.
- **Administrative Decommissioning ($AC_3$):** Under `disposition_type: "project_termination"`, `scripts/orchestrate_pmbok.py --mode decommission` prunes ephemeral worktrees, revokes temporary runtime credentials, and releases test runners.
- **Phase $N+1$ Spark Seeding ($AC_4$):** Under `disposition_type: "phase_handoff"`, `scripts/orchestrate_pmbok.py --mode seed-next` generates Phase $N+1$ `Spark-Capture.md` and `Ideation-Document.md` populated with approved directives and incremented baseline.
- **Zero Storage Expansion ($AC_5$):** All refinement proposals, decision frames, evaluations, and human sign-off episodes are persisted using ADR-002's five record types as metadata-enriched `Episode` instances.
- **Bayes Factor Adjudication ($AC_6$):** `resolve_hypothesis()` adjudicates empirical Bayes factors:
  - $BF_{10} \ge 10 \implies$ `VALIDATED` (graduated into permanent architectural invariant).
  - $BF_{10} \le 0.1 \implies$ `REFUTED` (archived with negative reinforcement learning penalty).
- **Strict Recurrence Depth Guard ($AC_7$):** On the 3rd cycle ($d=2$), `REFINED` is strictly prohibited. `resolve_hypothesis()` and `adjudicate_hypothesis_batch()` automatically collapse inconclusive hypotheses ($BF_{10} < 10$) at $d=2$ to `REFUTED` due to budget exhaustion.
- **Hypothesis Terminality Verification ($AC_8$):** `adjudicate_hypothesis_batch()` asserts that 100% of Stage 3 hypotheses resolve to terminal states. Any missing Bayes factor or lingering active state raises `HypothesisTerminalityError`.

## Call sites

- `pmbok/models/intent_refinement.py`: Exports `IntentRefinementProposalPayload`, `ReadinessAuditResult`, `ReadinessPreconditionError`, `evaluate_phase_close_readiness`, `HypothesisTerminalityError`, `resolve_hypothesis`, `adjudicate_hypothesis_batch`.
- `scripts/orchestrate_pmbok.py`: CLI `--mode seed-next`, `--mode decommission`, and `--mode rollback`.
