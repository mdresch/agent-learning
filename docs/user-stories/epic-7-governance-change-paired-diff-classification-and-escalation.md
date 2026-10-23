# Epic 7: Automated Governance Change — Paired Diff Classification and Escalation Pipeline

**Source ADR:** [ADR-007](../adr/ADR-007-governance-change-paired-diff-classification-and-escalation.md) — Accepted (2026-10-23)  
**Source BRD/FDD:** [BRD-007](../project-docs/Business-Requirements/BRD-007-governance-change-paired-diff-classification-and-escalation.md) / [FDD-007](../project-docs/Functional-Design/FDD-007-governance-change-paired-diff-classification-and-escalation.md)  

---

## Story 7.1 — Implement Paired Diff Classification & Escalation Pipeline

**Status:** Ready (2026-10-23)  
**As** an architectural governance maintainer on the Intent-to-Outcome chain,  
**I want** candidate changes to accepted artifacts evaluated by a paired pipeline of full-authority semantic classification and low-authority escalation learning,  
**So that** low-risk amendments and errata can be maintained autonomously while disguised decision reversals are caught and gated by human escalation.

### Acceptance Criteria:

- **$AC_0$ (Two-Stage Decoupled Execution):** The pipeline executes in two distinct stages: semantic diff classification under `DecisionAuthority.FULL`, followed by operational escalation disposition under `DecisionAuthority.LOW`.
- **$AC_1$ (7-Action Grouped Taxonomy):** `classify-diff-type` evaluates candidate diffs against 7 mutually exclusive actions grouped across 3 operational tiers:
  - *Tier 1 (Substantive):* `new_superseding_adr`, `amendment_log_entry`
  - *Tier 2 (Documentation):* `correction_note`, `clarification_section`, `provenance_note`
  - *Tier 3 (Lifecycle):* `pending_supersession_note`, `supersession_update`
  using the 4 weighted criteria (`semantic_scope_impact` [0.40], `architectural_intent_shift` [0.35], `downstream_contract_footprint` [0.15], `textual_cosmetic_ratio` [0.10]).
- **$AC_2$ (Native Margin & Ambiguity Halting):** When `classify-diff-type` evaluates a diff where the difference in robust utility between top candidate and runner-up is $\le 0.05$ (via native `DecisionFrame.minimum_margin`), the resolver returns `DecisionStatus.NEEDS_USER_TIE_BREAK`. The pipeline immediately halts and escalates to human maintainers without invoking `escalate-diff-response`.
- **$AC_3$ (Permanent Lineage Freeze Guard):** If `classify-diff-type` resolves to any of the 3 lifecycle status mutations (`new_superseding_adr`, `pending_supersession_note`, `supersession_update`), the escalation harness hard-overrides the disposition to `escalate_to_human`, barring bandit exploration or autonomous application.
- **$AC_4$ (Lightweight Evidence Transport via ADR-006):** The classification outcome (action ID, robust utility, runner-up margin, criteria support summary) is passed as `audit_evidence` to `escalate-diff-response.decide()`. The SDK verifies presence and transports the envelope without interpreting or parsing domain contents.
- **$AC_5$ (Mandatory Audit Emission for Autonomous Updates):** Any execution of `apply_automatically` or `apply_with_notification` constructs and registers an immutable `Episode` audit record before or upon applying changes to the repository. No governance update executes silently.
- **$AC_6$ (Progression Gating via ADR-005):** Upon application of an amendment, the governing requirement approval policy is re-evaluated, and `compare_decision_results(before, after)` compares the baseline. Progression emits positive reward (+1.0); detected regression triggers ADR-005 regression healing and human escalation with negative reward (-1.5).
- **$AC_7$ (Adversarial Diff Safety Harness):** Contract test suite verifies classification against adversarial test cases: deleted constraints, inverted logic, removed guardrails, softened `MUST` to `SHOULD`, legitimate errata, and parameter tweaks.

---

## Out of Scope per BRD-007/FDD-007

- Automating Stage 17 Execution Adaptation (refactoring source code, re-running build pipelines, rewriting agent instructions).
- Non-contextual bandit featurization of raw text diffs.
- Autonomous application of artifact lifecycle or lineage changes.
- Introduction of any new `LearningStore` record types or database containers.

