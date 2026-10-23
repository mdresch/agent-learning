# FDD-001: Enforce the REINFORCE Authority Boundary

**Source ADR:** [ADR-001](../../adr/ADR-001-decision-authority-model.md) — Accepted (2026-10-23), §4.5
**Source BRD:** [BRD-001](../Business-Requirements/BRD-001-reinforce-authority-boundary-enforcement.md)
**Status:** Approved (2026-10-23, Menno) — technical design derived from an Accepted ADR's disclosed gap. Not yet built.

One real, code-shaped design, matching BRD-001's single business rule cluster (BRU-001-01/02).

## Design 1: Exclude `full`-authority episodes inside `ReinforceLearner.update()`'s own loop, not at a caller

Current behavior (`src/agent_learning/learners/reinforce.py`, verified directly):

```python
for episode in episode_list:
    if episode.action_id is None or episode.action_id not in action_index:
        continue
    reward = aggregate_rewards.get(episode.id)
    if reward is None:
        continue
    reward_value = reward.value
    advantage = reward_value - baseline_before

    iw = self._importance_weight(episode, probs_now, action_index)   # returns 1.0 if action_logprob is None
    advantage *= iw
    ...
```

Proposed change — one additional condition on the existing skip check (line 76), not a new branch:

```python
for episode in episode_list:
    if (
        episode.action_id is None
        or episode.action_id not in action_index
        or episode.action_logprob is None   # NEW — full-authority episode, never sampled from this policy
    ):
        if episode.action_logprob is None and episode.action_id is not None:
            full_authority_excluded += 1
        continue
    ...
```

- **Fix location is the learner itself, not `training/runner.py`.** `ReinforceLearner.update()` has two other real callers besides `run_offline_batch()`: `audit.py:444` (direct replay) and `audit.py:503` (per-episode attribution replay). A filter placed only in `training/runner.py`'s episode query would leave both audit call sites still capable of training on `full`-authority episodes during replay — the same contamination BRD-001 names, just reachable from a different entry point. Putting the check inside `update()`'s own loop closes the gap for every caller at once, which is also why BRU-001-02 names "inside `ReinforceLearner` itself" as an acceptable location, not only "where the training batch is assembled."
- **No new field on `Episode`.** `action_logprob is None` already uniquely identifies a `full`-authority episode in every real path that constructs one (`DecisionResolver.resolve()` never sets it; the learned path always does) — confirmed against `decision.py`'s `DecisionResult` construction (ADR-001 §3). BRU-001-03's condition is met without a schema change.
- **`_importance_weight()` is left unmodified.** Its own `action_logprob is None → return 1.0` branch becomes unreachable through `update()`'s normal loop once the new exclusion lands (the episode never reaches the call), but the method stays correct in isolation and is not deleted — removing it would be an unrelated cleanup, not part of this fix.
- **Exclusion count surfaces in `LearnerResult.extra`**, not as a new dataclass field — consistent with the existing pattern already used for `extra={"reason": "no actionable episodes"}` and `extra={"entropy": entropy}`: `extra["full_authority_excluded"] = full_authority_excluded`. This makes the exclusion itself auditable (a caller or test can assert on the count), rather than a silent `continue`.

## Required follow-on: `audit.py`'s warning text goes stale

`audit.py:562-563` currently warns:

```python
if any(episode.action_logprob is None for episode in episodes):
    report.warnings.append("Missing behavior probability: importance weight uses the native fallback of 1.")
```

Once Design 1 lands, this condition no longer describes what actually happens — the episode is excluded before `_importance_weight()` is ever called, so there is no "fallback of 1" being applied to it anymore. This must be corrected in the same change, not left to drift into a misleading message:

```python
if any(episode.action_logprob is None for episode in episodes):
    report.warnings.append(
        "One or more full-authority episodes (action_logprob is None) were present in this "
        "batch and excluded from the REINFORCE update, not reweighted — see ADR-001 §4.5."
    )
```

## Error Handling / Compatibility

| Condition | Behavior |
|---|---|
| A `full`-authority episode (`action_logprob is None`) with a matching aggregate reward, in a batch passed to `ReinforceLearner.update()` | Excluded from the gradient step and from `episodes_used`; counted in `extra["full_authority_excluded"]`. Previously: included with `iw=1.0`. |
| A `low`-authority episode logged under an older policy version (the real case `_importance_weight()` exists to serve) | Unchanged — still reweighted by the existing importance-sampling ratio, not excluded. |
| A batch containing only `full`-authority episodes with matching rewards | `used == 0`, same `LearnerResult(episodes_used=0, extra={"reason": "no actionable episodes"})` path already returned today for an empty-after-filtering batch — no new code path, just a new way to reach the existing one. `full_authority_excluded` is still populated on this result. |
| `audit.py`'s replay/attribution call sites (`audit.py:444`, `audit.py:503`) | Same exclusion applies automatically — no separate fix needed there, since both call the same `ReinforceLearner.update()`. |

## Out of Scope

Same as BRD-001: no `Episode` schema change; no new mechanism for learning from `full`-authority evidence; no reopening of whether the exclusion should exist at all (ADR-001 §4.2 already decided that).
