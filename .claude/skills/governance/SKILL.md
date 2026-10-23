---
name: governance
description: Automated governance change pipeline (Stage 16) for agent_learning paired diff classification and escalation.
---

# Component: governance (`agent_learning.governance`)

**Governing:** ADR-007, BRD-007, FDD-007, Story 7.1 (`docs/user-stories/epic-7-governance-change-paired-diff-classification-and-escalation.md`).
**Contract:** `tests/test_governance.py`; fixtures in `tests/fixtures/governance/` (DecisionFrame and diff JSONs, committed).

## Load-bearing constraints

- Two-stage decoupled pipeline: `classify-diff-type` runs under `DecisionAuthority.FULL` (Bayesian reasoning over DecisionFrame); `escalate-diff-response` runs under `DecisionAuthority.LOW` (Softmax bandit with REINFORCE).
- 7-Action taxonomy across 3 tiers:
  - Tier 1 (Substantive): `new_superseding_adr`, `amendment_log_entry`
  - Tier 2 (Documentation): `correction_note`, `clarification_section`, `provenance_note`
  - Tier 3 (Lifecycle): `pending_supersession_note`, `supersession_update`
- 4 Standard criteria weights: `semantic_scope_impact` (0.40), `architectural_intent_shift` (0.35), `downstream_contract_footprint` (0.15), `textual_cosmetic_ratio` (0.10).
- Native margin & ambiguity halting: `DecisionFrame.minimum_margin = 0.05`. If utility difference $\le 0.05$, resolver returns `DecisionStatus.NEEDS_USER_TIE_BREAK`. Pipeline halts immediately for human input without invoking escalation policy.
- Human approval gate: when `classify_policy` requires human approval, status `DecisionStatus.NEEDS_USER_FEEDBACK` immediately halts with `disposition="needs_user_feedback"` without bypassing human review.
- Permanent Lineage Freeze: `new_superseding_adr`, `pending_supersession_note`, `supersession_update` are permanently barred from autonomy; hard-overridden to `escalate_to_human`.
- Lightweight evidence transport (ADR-006): `audit_evidence` envelope passed to `escalate-diff-response.decide()`, transported without SDK domain interpretation.
- Deferred audit logging (audit integrity): `Episode` audit record is constructed and persisted strictly after progression verification, ensuring blocked regressions never leave false autonomous execution records in storage.
- Progression gating (ADR-005): candidate amendment verified via `compare_decision_results()`. Progression yields +1.0 reward; regression triggers healing/reversion, disposition override to `escalate_to_human`, and yields -1.5 penalty.
- Stage 16 scope boundary: pipeline terminates with a validated governance baseline; Stage 17 Execution Adaptation is strictly out of scope.
- Zero storage expansion: no new Cosmos containers or LearningStore record types (ADR-002 Invariant #2).

## Call sites

- `agent_learning/__init__.py`: re-exports `evaluate_governance_diff`, `GovernancePipelineResult`, `DIFF_ACTIONS`, `DIFF_TIERS`, `ESCALATION_ACTIONS`, etc.
- `agent_learning/governance.py`: core pipeline orchestration and taxonomy constants.
