# Epic 5: Decision-Progress Comparison and Regression Healing

**Source ADR:** [ADR-005](../adr/ADR-005-decision-progress-comparison.md) — Accepted (2026-10-23)
**Source BRD/FDD:** [BRD-005](../project-docs/Business-Requirements/BRD-005-decision-progress-comparison.md) / [FDD-005](../project-docs/Functional-Design/FDD-005-decision-progress-comparison.md)

One story, matching FDD-005's three designs.

## Story 5.1 — Build `compare_decision_results()` and the `task-policy-compare` CLI

**Status:** Completed (2026-10-23) — implemented in `agent_learning.comparison` and `agent-learn task-policy-compare` CLI; contract tests verified ($AC_0$–$AC_5$).
**As** anyone running a revision pass on an ADR/BRD/FDD/Story through this repo's `agent-learning-governance` policies, **I want** a reusable comparison between two or more `DecisionResult`s, **so that** "did this revision help" is a measured number instead of a one-off script, with regression flagged and escalated rather than silently missed.

**Acceptance Criteria:**
- $AC_0$: `_validate_preconditions` raises `ValueError` naming the mismatched field when two `DecisionResult`s differ in `agent_id`, `task_id`, `decision_authority`, or action taxonomy — contract-test using the real `adr-001-decision-result.json` vs. `brd-001-decision-result.json` fixture (real `task_id` mismatch), asserting the raise.
- $AC_1$: `compare_decision_results()` reports a `robust_utility`/`expected_utility`/`uncertainty` delta for every action, not only the leader — contract-test against the real `adr-002-decision-result.json` → `adr-002-decision-result-v2.json` pair, asserting the exact deltas: `approve_adr +0.03421`, `reject_adr -0.02867`, `request_revision_before_decision -0.03815`.
- $AC_2$: `_classify` resolves the same real ADR-002 pair to `progression` (margin `0.74410` → `0.81646`), using ADR-005 §4.4's proven-exhaustive taxonomy verbatim, with `DEFAULT_EPSILON = 0.01`.
- $AC_3$: `agent-learn task-policy-compare --sequence <file1> <file2> ...` runs the real ADR-002 pair end-to-end and prints the per-action deltas and the `progression` classification — contract-test the CLI's actual stdout, not just the underlying function.
- $AC_4$: on a `regression` classification, the heal step prints per-criterion attribution, a running regression-streak count against `--retry-cap` (default `3`), and an `ESCALATE` line once the cap is reached, exiting `0` — contract-test against `adr-005-decision-result.json` (real, Accepted) → `adr-005-regressed-decision-result.json` (real declined-suggestion counterfactual: a scratch copy of ADR-005 with one review's actually-proposed but rejected "fix" applied — removing a valid ADR-002 §4.6 citation based on that review's false claim it didn't exist). Measured, not invented: `approve_adr` robust utility fell `-0.1784`, margin narrowed `0.8077 → 0.5483`. The live ADR-005 document itself was never edited — only a disposable scratch copy, deleted after use; the real fixture files (`adr-005-regressed-demo.json`, `adr-005-regressed-decision-result.json`) remain on disk as this AC's test input.
- $AC_5$: the heal step never writes to any ADR/BRD/FDD/Story file and never calls `LearningStore` — contract-test that `compare_decision_results()`/`task-policy-compare` make zero filesystem writes outside their own stdout and zero calls into `storage/*`.

## Not a story — out of scope per BRD-005/FDD-005

Persisting decision-result history as a new `LearningStore` record type, and the heal step generating its own corrective revision, are both already rejected in ADR-005 §5 — not drafted here as a future story, since they were explicitly decided against, not merely deferred.
