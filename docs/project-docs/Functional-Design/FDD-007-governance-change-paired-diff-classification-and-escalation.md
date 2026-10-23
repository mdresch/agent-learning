# FDD-007: Automated Governance Change — Paired Diff Classification and Escalation Pipeline

**Source ADR:** [ADR-007](../../adr/ADR-007-governance-change-paired-diff-classification-and-escalation.md) — Accepted (2026-10-23)  
**Source BRD:** [BRD-007](../Business-Requirements/BRD-007-governance-change-paired-diff-classification-and-escalation.md)  
**Status:** Draft — technical design derived from an Accepted ADR  

This document specifies the technical design, data contracts, decision frames, validation guards, and verification protocols for the Stage 16 Governance Change paired pipeline.

---

## Design 1: Component Topology & End-to-End Workflow

The governance change pipeline coordinates two decoupled `TaskPolicy` instances and connects them with ADR-005 verification and ADR-006 evidence transport:

```
[Candidate Diff (Candidate vs. Frozen Baseline)]
                      │
                      ▼
 ┌─────────────────────────────────────────────────────────┐
 │ 1. classify-diff-type                                   │
 │    Authority: FULL (Bayesian DecisionResolver)          │
 │    Frame: 7 actions, 4 criteria, min_margin=0.05        │
 └─────────────────────────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │ Status ==                 │ Status ==
        │ NEEDS_USER_TIE_BREAK      │ RESOLVED
        ▼                           ▼
 ┌───────────────┐        Selected Diff Action
 │ HALT: Escalate│                  │ Transported via ADR-006
 │ to User for   │                  │ audit_evidence payload
 │ Manual Tie-   │                  ▼
 │ Break Decision│   ┌─────────────────────────────────────────────────────────┐
 └───────────────┘   │ 2. escalate-diff-response                               │
                     │    Authority: LOW (SoftmaxPolicy Bandit)                │
                     │    Candidate Actions: escalate, notify, apply           │
                     └─────────────────────────────────────────────────────────┘
                                    │
                      ┌─────────────┼─────────────┐
                      ▼             ▼             ▼
                 [escalate]     [notify]       [apply]
                (Human sign-   (Immutable    (Immutable
                  off req.)     Audit Log +   Audit Log +
                                Apply)        Auto-Commit)
                                    │             │
                                    └──────┬──────┘
                                           ▼
                     ┌─────────────────────────────────────────┐
                     │ 3. ADR-005 Progression Verification     │
                     │    Re-evaluate Approval Policy          │
                     │    compare_decision_results(bef, aft)   │
                     └─────────────────────────────────────────┘
                                           │
                            ┌──────────────┴──────────────┐
                            ▼                             ▼
                      [PROGRESSION]                 [REGRESSION]
                      Emit +1.0 Reward              Trigger ADR-005 Healing /
                      to escalate policy            Revert / Human Escalation
```

---

## Design 2: `classify-diff-type` Specification (FULL Authority)

### Policy Metadata & Identity
- `agent_id`: `socialengage-governance` (or configured governance agent)
- `task_id`: `classify-diff-type`
- `authority`: `DecisionAuthority.FULL`
- `requires_human_approval`: `true`

### 7-Action Grouped Taxonomy
```python
ACTIONS = [
    # Tier 1: Substantive Governance Change
    {"id": "new_superseding_adr", "description": "Alters core architecture, principles, or system topology"},
    {"id": "amendment_log_entry", "description": "Updates operational parameters/thresholds preserving intent"},
    
    # Tier 2: Documentation & Clarification
    {"id": "correction_note", "description": "Errata, typo fixes, broken links, non-semantic formatting"},
    {"id": "clarification_section", "description": "Explanatory prose or diagrams resolving ambiguity"},
    {"id": "provenance_note", "description": "Authorship, upstream spec links, or external references"},
    
    # Tier 3: Lifecycle Status Mutation
    {"id": "pending_supersession_note", "description": "Marks active artifact that replacement is drafted"},
    {"id": "supersession_update", "description": "Marks old artifact superseded once replacement is accepted"},
]
```

### Criteria & Weight Vector
- `semantic_scope_impact` (Weight: 0.40): Measures whether the diff alters the fundamental decision boundaries or just operational parameters.
- `architectural_intent_shift` (Weight: 0.35): Measures whether the diff alters the underlying "Why", principles, or trade-offs.
- `downstream_contract_footprint` (Weight: 0.15): Measures whether existing contract tests, interfaces, or consumer expectations are invalidated.
- `textual_cosmetic_ratio` (Weight: 0.10): Measures the ratio of substantive structural change to formatting/wording cleanup.

### Margin & Ambiguity Guard (BRU-007-03)
The frame configures `DecisionFrame.minimum_margin = 0.05`.
When `top_utility - runner_up_utility <= 0.05 + 1e-9`, `DecisionResolver` returns `DecisionStatus.NEEDS_USER_TIE_BREAK`.
The pipeline immediately short-circuits and prompts human maintainers without delegating to `escalate-diff-response`.

---

## Design 3: `escalate-diff-response` Specification (LOW Authority)

### Policy Metadata & Identity
- `agent_id`: `socialengage-governance`
- `task_id`: `escalate-diff-response`
- `authority`: `DecisionAuthority.LOW`
- `capture_decision_evidence`: `true` (ADR-006 opt-in evidence capture enabled)
- `complexity_tier`: `standard`

### 3-Action Candidate Set
1. `escalate_to_human`: Halts execution and requires human approval.
2. `apply_with_notification`: Applies change and emits notification + immutable audit event.
3. `apply_automatically`: Commits change directly + emits immutable audit event.

### Permanent Lineage Freeze Guard (BRU-007-04)
Prior to sampling the policy action, the execution harness evaluates the classified diff type:
```python
PERMANENTLY_FROZEN_ACTIONS = {
    "new_superseding_adr",
    "pending_supersession_note",
    "supersession_update",
}

if classified_action_id in PERMANENTLY_FROZEN_ACTIONS:
    # Hard-override: bypass bandit exploration, mandate human escalation
    return DecisionResult(
        selected_action={"id": "escalate_to_human"},
        reason=f"Action '{classified_action_id}' alters governance lineage and is permanently frozen from autonomous application (ADR-007 Invariant #4).",
        ...
    )
```

### Mandatory Audit Event Emission (BRU-007-05)
Whenever an action of `apply_automatically` or `apply_with_notification` is chosen, the engine immediately constructs and registers an `Episode` record into `LearningStore` before touching filesystem or repository state.

---

## Design 4: Lightweight Evidence Transport (ADR-006 Integration)

When calling `escalate-diff-response.decide()`, the output from `classify-diff-type` is supplied as `audit_evidence`:

```python
audit_evidence_payload = {
    "source_task_id": "classify-diff-type",
    "classified_diff_type": classification_result.selected_action["id"],
    "robust_utility": classification_assessment.robust_utility,
    "runner_up_margin": utility_margin,
    "criteria_supports": {
        c.criterion_id: c.support for c in classification_assessment.criteria
    },
    "diff_target": target_artifact_path,
}

escalation_result = escalate_policy.decide(
    audit_evidence=audit_evidence_payload
)
```

In accordance with ADR-006 §4.2, the SDK verifies non-empty presence of `audit_evidence` but does not interpret or featurize its contents.

---

## Design 5: Downstream Progression Verification (ADR-005 Integration)

Upon applying a governance change:
1. Re-evaluate the governing approval policy (e.g. `approve-adr` or `approve-brd`) against the candidate artifact to generate `after_result`.
2. Compare against the baseline decision:
   ```python
   comparison = compare_decision_results(before_result, after_result)
   ```
3. Evaluate outcome:
   - If `comparison.classification == ProgressionClassification.PROGRESSION`:
     Emit reward `+1.0` to `escalate-diff-response`.
   - If `comparison.classification == ProgressionClassification.FLAT`:
     Emit reward `0.0` (acceptable neutral maintenance).
   - If `comparison.classification == ProgressionClassification.REGRESSION`:
     Revert changes, trigger human escalation, and emit reward `-1.5` to `escalate-diff-response`.

---

## Design 6: Adversarial Diff Test Suite (Classification Safety Harness)

The contract test suite must assert correct behavior across 6 specific test archetypes:
1. `test_deleted_constraint_forces_superseding_adr`: Removing an architectural constraint clause must never classify as `amendment_log_entry` or `correction_note`.
2. `test_inverted_logic_forces_superseding_adr`: Inverting boolean conditions or changing inequality bounds forces `new_superseding_adr`.
3. `test_removed_guardrail_forces_superseding_adr`: Stripping validation or error handling preconditions forces `new_superseding_adr`.
4. `test_softened_modal_verb_forces_superseding_adr_or_tiebreak`: Altering `MUST` to `SHOULD` forces `new_superseding_adr` or `needs_user_tie_break`.
5. `test_legitimate_erratum_classifies_correction_note`: Fixing broken link or markdown typo classifies as `correction_note`.
6. `test_parameter_shift_classifies_amendment_log_entry`: Updating numeric retry cap or timeout while preserving intent classifies as `amendment_log_entry`.

