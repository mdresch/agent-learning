---
name: comparison
description: Decision-progress comparison and regression healing component for agent_learning.
---

# Component: comparison (`agent_learning.comparison`)

**Governing:** ADR-005, BRD-005, FDD-005, Story 5.1 (`docs/user-stories/epic-5-decision-progress-comparison.md`).
**Contract:** `tests/test_comparison.py`; fixtures in `tests/fixtures/comparison/` (real DecisionResult JSONs, committed).

## Load-bearing constraints

- Pure and stateless: no filesystem writes, no `LearningStore` calls (AC5). The heal step never edits ADR/BRD/FDD/Story files.
- Classification taxonomy is ADR-005 §4.4 verbatim; `DEFAULT_EPSILON = 0.01`.
- `_validate_preconditions` raises `ValueError` naming the mismatched field (`agent_id`, `task_id`, `decision_authority`, or action taxonomy).
- Regression path prints per-criterion attribution and a streak against `--retry-cap` (default 3); at the cap it prints `ESCALATE` and exits 0.
- Persisting decision-result history and auto-generating corrective revisions are rejected in ADR-005 §5, not deferred.

## Call sites

- `agent_learning/__init__.py` re-exports the comparison symbols.
- `agent_learning/cli.py`: `agent-learn task-policy-compare --sequence <files...>`.
