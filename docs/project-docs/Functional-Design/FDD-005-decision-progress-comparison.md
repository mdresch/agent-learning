# FDD-005: Decision-Progress Comparison and Regression Healing

**Source ADR:** [ADR-005](../../adr/ADR-005-decision-progress-comparison.md) — Accepted (2026-10-23)
**Source BRD:** [BRD-005](../Business-Requirements/BRD-005-decision-progress-comparison.md)
**Status:** Draft — technical design derived from an Accepted ADR

Three real, code-shaped designs resolving ADR-005 §9's open implementation questions, plus the error-handling table BRU-005-01 requires.

## Design 1: `compare_decision_results(before, after)` — a pure function, new module `agent_learning/comparison.py`

```python
def compare_decision_results(before: DecisionResult, after: DecisionResult) -> ComparisonResult:
    _validate_preconditions(before, after)  # BRU-005-01
    action_deltas = {
        action_id: {
            "robust_utility_delta": after_assessment.robust_utility - before_assessment.robust_utility,
            "expected_utility_delta": after_assessment.expected_utility - before_assessment.expected_utility,
            "uncertainty_delta": after_assessment.uncertainty - before_assessment.uncertainty,
        }
        for action_id, before_assessment, after_assessment in _paired_assessments(before, after)
    }  # BRU-005-02 — every action, not just the leader
    classification = _classify(before, after, epsilon=DEFAULT_EPSILON)  # ADR-005 §4.4
    return ComparisonResult(action_deltas=action_deltas, classification=classification, ...)
```

- **`_validate_preconditions`** (BRU-005-01): raises `ValueError` naming exactly which field mismatched — `agent_id`, `task_id`, `decision_authority` (both must be `full`; `OptionAssessment` fields are only populated by the resolver, ADR-005 §4.1), or the action id set.
- **`_classify`** implements ADR-005 §4.4's proven-exhaustive four-disjunct `regression` / two-branch `progression` / residual `flat` definitions verbatim — no reinterpretation here, since the ADR already proved mutual exclusivity. `DEFAULT_EPSILON = 0.01` (a real, named default — ADR-005 §9 left this as a tuning parameter; this FDD sets one rather than leaving it unset, since an unset tolerance would make `flat` unreachable).

## Design 2: `task-policy-compare` — a new CLI subcommand, not a `task-policy-decide` flag

ADR-005 §9 left the CLI surface open between a new subcommand and a `--compare-to` flag on `task-policy-decide`. **Decided here: a new subcommand.** Reasoning: `task-policy-decide` already has seven flags: a 2+-file sequence comparison (not a single "compare to one prior" case, per ADR-005 §4.4) does not fit that command's existing single-decision shape without overloading it. A separate, discoverable subcommand matches the existing `task-policy-*` naming family.

```
agent-learn task-policy-compare --sequence <file1> <file2> [<file3> ...] [--epsilon 0.01] [--retry-cap 3]
```

- Requires at least 2 files; exits with a clear error otherwise.
- Prints, per consecutive pair: the action deltas (Design 1), the classification, and — only on `regression` — the heal-step output (Design 3).
- `--retry-cap` (default `3`, matching `heal-contract-failure`'s own small fixed cap — ADR-005 §4.5 point 2 named "e.g. 2-3" without committing; this FDD commits to `3`) is read but not enforced by this command itself — see Design 3's real division of labor.

## Design 3: The heal step is advisory output, not a loop the CLI runs for you

ADR-005 §4.5 point 4 is explicit: the SDK does not generate the corrective revision. Concretely, this means `task-policy-compare` does **not** re-invoke itself in a loop waiting for a new file to appear. On a `regression` classification, it prints:
- which action deltas moved against the leader (Design 1's per-action output already has this — no new computation needed, confirmed real via `OptionAssessment.criteria`, ADR-005 §4.5 point 1),
- a count of how many consecutive `regression` steps have now occurred for this leading action across the sequence so far, compared against `--retry-cap`,
- once that count reaches the cap: a distinct `ESCALATE` line, naming that human review is required — the command still exits `0` (it did its job: classify and report), it does not treat reaching the cap as the command's own failure.

The actual next revision — editing the ADR, re-running `task-policy-decide`, and feeding the new result back into `task-policy-compare` — is the calling agent's or human's job every time, identical to how `heal-contract-failure` hands retry back to the calling agent rather than looping internally.

## Error Handling / Compatibility

| Condition | Behavior |
|---|---|
| Fewer than 2 files passed to `--sequence` | CLI exits 2 with a usage error, no comparison attempted |
| Two `DecisionResult`s with different `task_id` (real fixture: any `approve-adr` result vs. `brd-001-decision-result.json`) | `_validate_preconditions` raises `ValueError` naming `task_id` as the mismatched field |
| A `low`-authority `DecisionResult` passed | Raises — `OptionAssessment.robust_utility` etc. are `None` for `low` authority (never populated by the resolver), so no delta is computable |
| A regression step where the leading action became infeasible (`feasible: false`) | Classified `regression` via ADR-005 §4.4's second disjunct; Design 3's output still runs normally |
| Retry-cap reached | `ESCALATE` line printed; command exits `0` (successful classification), not a command failure |

## Real Validation Fixtures (already on disk, not hypothetical)

- **Positive/progression case**: `adr-002-decision-result.json` → `adr-002-decision-result-v2.json`. Exact real numbers to assert against: `approve_adr` robust-utility delta `+0.03421`, `reject_adr` delta `-0.02867`, `request_revision_before_decision` delta `-0.03815`; margin `0.74410` → `0.81646`. Classification must resolve to `progression`.
- **Precondition-violation case**: `adr-001-decision-result.json` (task_id `approve-adr`) vs. `brd-001-decision-result.json` (task_id `approve-brd`) — must raise.
- **Per-criterion attribution case**: the same ADR-002 pair, asserting the reported per-criterion movement for `architectural_soundness`/`alternatives_considered`/`consequences_honest`/`gap_disclosure_quality` matches what was actually used to produce these two real decisions.
- **Real regression case (Design 3's test input)**: `adr-005-decision-result.json` (real, Accepted) → `adr-005-regressed-decision-result.json`. The latter is not invented — it is the real `approve-adr` decision against a disposable scratch copy of ADR-005 with one review's actually-proposed, actually-declined "fix" applied (removing a valid `ADR-002 §4.6` citation on that review's false claim it didn't exist). `approve_adr` robust utility fell `-0.1784`, margin narrowed `0.8077 → 0.5483`. The live ADR-005 document was never edited; the scratch copy was deleted after generating this fixture.

## Out of Scope

Same as BRD-005: no new `LearningStore` record type; no auto-generated corrective revision; no auto-revert of caller content.
