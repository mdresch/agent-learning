---
name: contextual-learning
description: ContextualReinforceLearner, the exported learner for ContextualSoftmaxPolicy weight rows (ADR-038, Epic 38 Stories 38.1 to 38.3).
---

# Component: contextual-learning (`agent_learning_ext.learners.contextual_reinforce`)

**Governing:** ADR-038 (section 4.1, invariants 1 to 5), BRD-038 (BRU-038-01 to 06), FDD-038 (sections 1 to 3, D6), `docs/user-stories/epic-38-packaged-contextual-learning.md` Stories 38.1 to 38.3.
**Contract:** `tests/test_contextual_learner.py`. The CLI half of Epic 38 (Stories 38.4 to 38.6) is a separate component (`contextual-cli`).

## Load-bearing constraints

- **Placement (fork rule):** the module lives in `src/agent_learning_ext/learners/`. Nothing under `src/agent_learning/` is edited (`tests/test_upstream_untouched.py`). It is exported from `agent_learning_ext.learners` and, through `_EXPORTS`, from `agent_learning_ext`.
- **The update (ADR-038 4.1, FDD-038 3):** for each used episode, `c_a = (R - b) * (1[a == a_t] - pi(a | phi)) * phi`. The row handed to `apply_update` is `learning_rate` times the mean of `c_a` over used episodes. `b` is the snapshot baseline at the start of the call. Every episode is scored on the starting weights, with `policy.probabilities(phi)` per vector.
- **The learner never writes the snapshot.** It calls `policy.apply_update(rows, baseline=..., episodes_seen=...)` once. Clipping to `max_weight_abs` and the version bump stay in the policy. `extra["weight_deltas"]` holds the unclipped rows; `logit_deltas` is always `{}`.
- **Baseline:** `decay * baseline_before + (1 - decay) * mean_reward`. `entropy_bonus`, `importance_clip` and `min_train_episodes` are not read. No entropy term, no importance weight (D6).
- **Training vector:** `Episode.metadata["feature_vector"]`. `context_features` is never read (invariant 2, ADR-004).
- **Purity (Story 38.1 AC_4):** standard library plus existing learner and policy types. No `numpy` import and no `agent_learning.storage` import in the module (`policy.probabilities` uses numpy internally; that is the policy's business).
- **Skipped episodes are counted, never zero-filled (Story 38.2, invariants 3 and 4):** each episode increments exactly one `extra` key, the first matching row of FDD-038 2.1: `skipped_no_action`, `full_authority_excluded` (`action_logprob is None`), `skipped_no_reward`, `skipped_missing_vector` (absent or None), `skipped_not_list` (anything but a `list`), `skipped_wrong_length`, `skipped_non_finite` (bool, non-number, NaN or inf). All seven keys are present on every return. A caller-supplied zero vector of the right length is used.
- **Nothing to apply:** with no used episode `apply_update` is not called; weights, baseline and version are unchanged; `episodes_used` 0, `mean_reward` 0, `extra["weight_deltas"]` `{}`, `extra["reason"]` `"no actionable episodes"`.
- **Bad reward:** a non-finite aggregate reward, or one outside [-1, 1], raises `ValueError` while the rewards are indexed, before any episode is applied.
- **One learner, one policy class (Story 38.3, invariant 1):** `update` raises `TypeError("ContextualReinforceLearner requires a ContextualSoftmaxPolicy")` for any other policy, before reading an episode, leaving the policy untouched. `ReinforceLearner` (ours and Microsoft's) already raises `TypeError` for a `ContextualSoftmaxPolicy` and still updates a `SoftmaxPolicy` without reading `feature_vector`; this component never edits it.
- **Receipt:** `consumed_inputs` lists only used episodes with the aggregate reward id kept (newest `created_at` wins); `episodes_used == len(consumed_inputs)`.

## Call sites

- `src/agent_learning_ext/learners/contextual_reinforce.py`: `ContextualReinforceLearner.update()`.
- Not called by `LearningRunner` or `train` (BRD-038 out of scope; Story 38.6 makes `train` refuse a contextual snapshot).
