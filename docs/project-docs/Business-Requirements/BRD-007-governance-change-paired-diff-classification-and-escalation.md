# BRD-007: Automated Governance Change — Paired Diff Classification and Escalation Pipeline

**Source ADR:** [ADR-007](../../adr/ADR-007-governance-change-paired-diff-classification-and-escalation.md) — Accepted (2026-10-23)  
**Status:** Draft — business requirements derived from an Accepted ADR  
**Stakeholders:** Menno (Sponsor/PM/maintainer)  

## Business Need

On the 18-stage Intent-to-Outcome Chain (`PROJECT-MANAGEMENT-ONTOLOGY.json`), Stage 16 (**Governance Change**) governs the formal amendment or evolution of governance policies and architectural baselines resulting from validated lessons (Stage 15) before downstream execution adapts (Stage 17). Today, evolving an already-accepted governance artifact (an ADR, BRD, FDD, or Story) presents a dangerous dilemma: a trivial erratum or parameter tweak requires manual human bureaucracy, while a disguised, consequential reversal of an architectural decision can slip through under the guise of a "minor clarification."

This BRD establishes an automated, evidence-driven **Governance Change** pipeline powered by two paired `TaskPolicy` instances:
1. **`classify-diff-type`** (`full` authority, Bayesian multi-criteria reasoning): Inspects the semantic diff between a candidate amendment and the frozen accepted baseline to categorize the exact structural *form* of change across a proven 7-action taxonomy grouped into three operational tiers.
2. **`escalate-diff-response`** (`low` authority, learned `SoftmaxPolicy` bandit): Decides whether that classified diff category warrants human escalation, notification, or autonomous application with mandatory audit logging, earning autonomy over time via REINFORCE from downstream outcome rewards.

This pipeline formally closes the development lifecycle loop between Lessons Learned and Workflow Adaptation. It integrates directly with **ADR-005** (verifying that the applied change yields measured decision `progression` rather than `regression`) and **ADR-006** (transporting diff classification context via lightweight `audit_evidence` into the low-authority escalation decision) while strictly preserving ADR-001's authority model and ADR-002's five-record-type storage boundary.

## Business Rules (BRU)

- **BRU-007-01 (Two-Stage Pipeline Decoupling):** Governance change evaluation must be split into two decoupled decisions:
  1. Semantic diff inspection (`classify-diff-type`) running under `full` authority via Bayesian reasoning.
  2. Operational escalation disposition (`escalate-diff-response`) running under `low` authority via a discrete `SoftmaxPolicy` bandit.
- **BRU-007-02 (7-Action Taxonomy Grouped into 3 Tiers):** `classify-diff-type` evaluates candidate diffs against 7 mutually exclusive actions grouped into 3 operational tiers:
  - *Tier 1 (Substantive Governance Change):* `new_superseding_adr`, `amendment_log_entry`
  - *Tier 2 (Documentation & Clarification):* `correction_note`, `clarification_section`, `provenance_note`
  - *Tier 3 (Lifecycle Status Mutation):* `pending_supersession_note`, `supersession_update`
- **BRU-007-03 (Native Margin & Ambiguity Halting):** `classify-diff-type` must enforce the SDK's native `DecisionFrame.minimum_margin` parameter (default `0.05`). If the utility difference between the top candidate and runner-up is $\le 0.05$, the system must return `DecisionStatus.NEEDS_USER_TIE_BREAK` and immediately halt for human input without invoking `escalate-diff-response`.
- **BRU-007-04 (Permanent Lineage Freeze):** Actions that mutate governance lineage or artifact lifecycle status (`new_superseding_adr`, `pending_supersession_note`, `supersession_update`) are permanently barred from autonomous application. Their escalation response must always be hard-constrained to `escalate_to_human`. Only Tier 2 documentation edits and `amendment_log_entry` may earn statistical autonomy.
- **BRU-007-05 (Mandatory Audit Emission for Autonomous Changes):** Autonomous governance application (`apply_automatically` or `apply_with_notification`) must never execute silently. Every automated change must emit an immutable `Episode` audit record before or upon applying the change.
- **BRU-007-06 (Lightweight Evidence Transport via ADR-006):** The selected classification, robust utility margin, and criteria assessment from `classify-diff-type` must be transported into `escalate-diff-response` strictly through the `audit_evidence` parameter of `decide()`. The SDK must not parse domain schemas or featurize the bandit.
- **BRU-007-07 (Downstream Progression Verification via ADR-005):** Once a governance change is applied, the governing requirement approval policy (e.g. `approve-adr`) must be re-evaluated. `compare_decision_results()` must verify that the new baseline produces `progression` or neutral tolerance (`flat`). Any detected `regression` must trigger ADR-005 regression healing and emit negative rewards to the escalation policy.
- **BRU-007-08 (Stage 16 Scope Boundary):** ADR-007 terminates with a formally validated, immutable governance baseline. Execution adaptation (code edits, test suite execution, prompt tuning) remains strictly the responsibility of Stage 17.
- **BRU-007-09 (Zero Storage Expansion):** The pipeline must introduce zero new Cosmos DB containers, zero new SQL tables, and zero new `LearningStore` record types (ADR-002 Invariant #2).

## Stakeholder Success Metrics

| Metric | Target |
|---|---|
| Red-Team Diff Detection | 100% of disguised decision reversals (deleted constraints, softened MUSTs) classified as `new_superseding_adr` or `needs_user_tie_break` |
| Lineage Preservation | 0 instances of autonomous status mutation for `new_superseding_adr`, `pending_supersession_note`, or `supersession_update` |
| Zero Silent Updates | 100% of autonomous updates accompanied by an immutable `Episode` audit record |
| Regression Protection | 100% of governance changes gated by ADR-005 progression comparison before final baseline adoption |
| Storage Boundary Compliance | 0 new record types or storage containers added to `LearningStore` |

## Out of Scope

- Automated execution of code refactoring, test fixes, or agent system-prompt rewrites (strictly Stage 17 Adaptation).
- Contextual bandit featurization of raw text diffs (prohibited by ADR-001 and ADR-007).
- Bypassing human review for artifact lifecycle mutations (permanently frozen by BRU-007-04).

