---
name: intent-refinement
description: PMBOK 8 Stage 18 Intent Refinement, Phase Close readiness evaluation, and double-loop cognitive feedback.
---

# Component: intent-refinement (`pmbok.models.intent_refinement` & `scripts.orchestrate_pmbok`)

**Governing:** ADR-009, BRD-009, FDD-009, Epic 9 (Story 9.1).  
**Contract:** `tests/pmbok/test_intent_refinement.py`.  
**Baseline:** `PMP-BL-v1.0.0`.

## Load-bearing constraints

- **Readiness Audit Precondition ($AC_0$):** `evaluate_phase_close_readiness()` enforces that all Stage 9 deliverables are accepted, Stage 11 audit records are free of unresolved non-conformances, and Stage 15 lessons learned are crystallized before Stage 18 evaluation can proceed. Any violation raises `ReadinessPreconditionError`.
- **Full-Authority Refinement Gate ($AC_1$):** `approve-intent-refinement` is registered under `agent-learning-governance` with `DecisionAuthority.FULL`, multi-criteria Bayesian evaluation, and permanently locked `requires_human_approval: true`.
- **Machine-Readable Contract ($AC_2$):** The proposal artifact (`Intent-Refinement-Proposal.md`) strictly validates against `IntentRefinementProposalPayload`, enforcing structural completeness, SemVer baseline identifiers (`PMP-BL-vX.Y.Z`), and disposition constraints.
- **Administrative Decommissioning ($AC_3$):** Under `disposition_type: "project_termination"`, `scripts/orchestrate_pmbok.py --mode decommission` prunes ephemeral worktrees, revokes temporary runtime credentials, and releases test runners.
- **Phase $N+1$ Spark Seeding ($AC_4$):** Under `disposition_type: "phase_handoff"`, `scripts/orchestrate_pmbok.py --mode seed-next` generates Phase $N+1$ `Spark-Capture.md` and `Ideation-Document.md` populated with approved directives and incremented baseline.
- **Zero Storage Expansion ($AC_5$):** All refinement proposals, decision frames, evaluations, and human sign-off episodes are persisted using ADR-002's five record types as metadata-enriched `Episode` instances.

## Call sites

- `pmbok/models/intent_refinement.py`: Exports `IntentRefinementProposalPayload`, `ReadinessAuditResult`, `ReadinessPreconditionError`, `evaluate_phase_close_readiness`.
- `scripts/orchestrate_pmbok.py`: CLI `--mode seed-next`, `--mode decommission`, and `--mode rollback`.

