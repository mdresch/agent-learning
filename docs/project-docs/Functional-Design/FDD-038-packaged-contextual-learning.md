# FDD-038: Packaged Contextual Learning

**Source ADR:** [ADR-038](../../adr/ADR-038-packaged-contextual-learning.md) — Accepted (2026-10-30, Menno); Episode `f745c77b-0a2c-4e97-82d4-6f6936b2acd9`  
**Source BRD:** [BRD-038](../Business-Requirements/BRD-038-packaged-contextual-learning.md)  
**Status:** Approved (2026-10-30, Menno) — derived from Accepted ADR-038 and BRD-038; adjudicated via `approve-fdd` (robust utility 0.745, episode `3e68b518-9bf7-4107-873b-9bfdc59b2711`). Menno confirmed D1–D6 and the three ADR open questions on 2026-10-30. Each confirmation is option A in §4 and §7.

---

## 1. Architecture and Component Placement

1. **New module** `src/agent_learning/learners/contextual_reinforce.py`. It defines `ContextualReinforceLearner(Learner)`. It uses the standard library (`math`) and the existing learner and policy types. It imports `numpy` from nowhere, and it imports nothing from `agent_learning.storage`. No new package is added.
2. **Export.** `ContextualReinforceLearner` is re-exported from `agent_learning.learners` and from `agent_learning`.
3. **Policy class stays.** `ContextualSoftmaxPolicy` already stores `metadata["feature_dim"]`, `metadata["context_weights"]`, `metadata["policy_kind"] = "contextual_softmax"`, and a zero `logits` map. This design adds no snapshot key.
4. **CLI.** `task-policy-init` gains `--feature-dim`. `task-policy-decide` gains `--features`. `train` and `task-policy-authority-set` gain a refusal for this policy kind. `ReinforceLearner`, `LearningRunner`, and ADR-003 are not edited.
5. **Caller owns the episode.** The learner reads episodes. It does not construct them. `task-policy-decide` does not store one (D1).

---

## 2. Data Contract

### 2.1 Learner

```python
class ContextualReinforceLearner(Learner):
    def __init__(self, config: LearnerConfig | None = None) -> None: ...

    def update(
        self,
        policy: Policy,
        episodes: Iterable[Episode],
        rewards: Iterable[Reward],
    ) -> LearnerResult: ...
    # TypeError unless policy is ContextualSoftmaxPolicy
```

`LearnerConfig.learning_rate` is \(\eta\). `LearnerConfig.baseline_decay` is the baseline EMA weight. `entropy_bonus`, `importance_clip`, and `min_train_episodes` are not read.

`LearnerResult.logit_deltas` is `{}` on every return. The rows passed to `apply_update` are `extra["weight_deltas"]`, a dict from action id to `list[float]`, before clipping. Skip counts live in `extra` under these keys, each an `int`:

| Key | Episode that increments it |
|---|---|
| `skipped_no_action` | `action_id` is missing or not in the policy |
| `full_authority_excluded` | `action_logprob is None` |
| `skipped_no_reward` | no `RewardSource.AGGREGATE` reward for that episode |
| `skipped_missing_vector` | `metadata` has no `feature_vector`, or the value is `None` |
| `skipped_not_list` | the value is not a `list` |
| `skipped_wrong_length` | the list length is not `feature_dim` |
| `skipped_non_finite` | an element is a `bool`, is not an `int` or `float`, or is not finite |

One episode increments one key. The first matching row in the table wins. A list of the right length whose elements are finite `int` or `float` values is used. A caller-supplied list of zeros is used.

### 2.2 Snapshot the CLI creates

`task-policy-init --feature-dim N` stores a snapshot from `ContextualSoftmaxPolicy.from_actions`. After the usual decision-metadata update, these hold:

| Field | Value |
|---|---|
| `metadata["policy_kind"]` | `"contextual_softmax"` |
| `metadata["feature_dim"]` | `N`, an int `>= 1` |
| `metadata["context_weights"]` | one `[0.0] * N` row per action id |
| `logits` | `{action_id: 0.0}` for every action, unused |
| `metadata["decision_authority"]` | `"low"` |

The decision fields already written today (`policy_scope`, `decision_context`, `decision_authority_source`, `complexity_profile`) are written the same way. The update must leave `policy_kind`, `feature_dim`, and `context_weights` in place.

### 2.3 Decide payload

`--features` is an inline JSON list, for example `--features "[1.0, 0.0, 1.0]"`. It is not a file path.

On success the printed object includes `feature_vector`: the same length, each element `float(x)` of the parsed list. It also includes `selection_mode` (`"sampled"` or `"greedy"`), `selected_action` with `probability` and `logprob`, and `action_probabilities` from `ContextualSoftmaxPolicy.probabilities(phi)`. It does not include an autonomy block.

### 2.4 Episode the caller records

The caller copies the payload's `feature_vector` into `Episode.metadata["feature_vector"]`. `context_features` stays whatever the caller uses for reward shaping. The learner never reads it.

---

## 3. Behavior

1. **`update` rejects the wrong class.** Anything other than a `ContextualSoftmaxPolicy` raises `TypeError("ContextualReinforceLearner requires a ContextualSoftmaxPolicy")`. No weight changes.
2. **Rewards are indexed first.** Keep the newest `RewardSource.AGGREGATE` per episode id (`created_at` strictly greater replaces). A non-finite value, or a value outside [-1, 1], raises `ValueError` before any episode is applied, and the snapshot is unchanged.
3. **Each episode is classified** by the table in §2.1. The advantage of a used episode is `R - baseline_before`, where `baseline_before` is the snapshot baseline at the start of the call. \(\pi(\cdot \mid \phi)\) is `policy.probabilities(feature_vector)` on those same starting weights. One shared distribution is not reused across different vectors.
4. **One apply at the end.** For each used episode and each action \(a\),

\[
c_a = (R - b) \, \bigl(\mathbf{1}_{a = a_t} - \pi(a \mid \phi)\bigr) \, \phi
\]

The row passed for \(a\) is \(\eta\) times the mean of \(c_a\) over the used episodes. `apply_update` receives those rows, `baseline_after`, and `episodes_seen + used`. The policy clips each coordinate to `[-max_weight_abs, max_weight_abs]` (default 10) and bumps the version once. The learner does not write `context_weights` itself.

5. **Baseline.** `baseline_after = decay * baseline_before + (1 - decay) * mean_reward`, with `mean_reward` the mean of the used aggregate rewards and `decay` from `LearnerConfig.baseline_decay`.
6. **Nothing to apply.** When `used == 0`, `apply_update` is not called. Weights, baseline, and version stay as they were. `episodes_used` is 0, `mean_reward` is 0, `weight_deltas` is `{}`, and `extra["reason"]` is `"no actionable episodes"`. The skip counts are still returned.
7. **`consumed_inputs`** lists only the used episodes, each with the aggregate reward id that was kept.

**Worked checks (arithmetic, to be re-run when built).** Two actions, `a` then `b`. Weights start at zero, so \(\pi = [0.5, 0.5]\) for every vector. Baseline starts at 0. Decay is 0.9.

- One episode. \(\phi = [1, 2]\), action `a`, \(R = 1\), \(\eta = 0.4\). Applied rows before clipping: `a` is `[0.2, 0.4]`, `b` is `[-0.2, -0.4]`. `baseline_after` is 0.1. Version increases by 1.
- Two episodes, one call, \(\eta = 1\). First: \(\phi = [1, 0]\), action `a`, \(R = 1\). Second: \(\phi = [0, 1]\), action `b`, \(R = -1\). Both see the starting weights. Applied rows: `a` is `[0.25, 0.25]`, `b` is `[-0.25, -0.25]`. Mean reward is 0, so the baseline stays 0.
- Clip. One episode, \(\phi = [1, 0]\), action `a`, \(R = 1\), \(\eta = 100\). The rows passed in `weight_deltas` are `a: [50, 0]` and `b: [-50, 0]`. The stored rows are `a: [10, 0]` and `b: [-10, 0]`.

A one-episode call with \(\eta\) equal to the learning rate is the formula in ADR-038 §4.1. The example's loop is that call, repeated by the caller. This module does not add the example's per-step baseline rewrite, and it does not add the entropy term or the importance weight from `ReinforceLearner`.

### 3.1 `task-policy-init`

- `--feature-dim` omitted: today's `SoftmaxPolicy.from_actions` path, including a full-authority init. The stored metadata has no `context_weights` and no `feature_dim`.
- `--feature-dim` present and `--decision-authority full`: exit 2, stderr names `feature-dim` and `full`, and the store gains no policy.
- `--feature-dim` is not an integer `>= 1` (`0` or negative): exit 2, nothing stored. A non-integer is an argparse failure, exit 2, nothing stored.
- Otherwise: build the snapshot in §2.2 with authority `low`. If the flag `--decision-authority low` was passed, `decision_authority_source` is `configured`; if authority was omitted, the source is `default`. Print the payload from §3.4.

### 3.2 `task-policy-decide`

Branch on `metadata["policy_kind"] == "contextual_softmax"`.

Contextual snapshot:

1. A missing `--features`, a value that is not a JSON list, a `bool` element, a non-numeric element, a non-finite element, or the wrong length: exit 2, stderr names `--features`, and the store is unchanged.
2. `--decision-frame` is refused, as it is for every low-authority policy.
3. If `capture_decision_evidence` is set, exit 2 with the message the command already prints, and write nothing. The features check in step 1 runs first.
4. `--greedy` selects the action with the highest `probabilities(phi)`. A tie keeps the earlier action in `snapshot.actions`. Otherwise call `choose(phi)`. `--seed` seeds that draw. Both paths set `action_logprob` from the contextual probability.
5. Print the payload in §2.3. Store no episode and no new policy version.

A scalar snapshot:

- `--features` present: exit 2, stderr names `--features`, store unchanged. The flag is not ignored.
- `--features` absent: today's path, including the autonomy branch.

A contextual snapshot whose authority is `full`: exit 2, write nothing. Init cannot create that pair (D4 covers the later authority command).

### 3.3 `train` and `task-policy-authority-set`

- `train` sees `policy_kind == "contextual_softmax"`: append a skipped entry whose reason names `ContextualReinforceLearner`, write no run that updates that snapshot, and do not construct a `SoftmaxPolicy` from it. If every task is skipped, the command stays exit 2, as it does today when nothing was trained.
- `task-policy-authority-set --authority full` on that kind: exit 2, stderr names `full` and `contextual`, and the snapshot is unchanged, including `migration_records`.
- Any other snapshot keeps today's `train` and authority-set behavior.

### 3.4 Printed policy payload

`_policy_payload` on a contextual snapshot returns `snapshot.to_dict()` and does not add `action_probabilities`. A distribution needs \(\phi\). The scalar path still adds `action_probabilities` from `SoftmaxPolicy`.

---

## 4. Points ADR-038 left open

ADR-038 §4.5 says an FDD may confirm the signatures. Menno confirmed each row on 2026-10-30, option A.

| # | This draft does | Why |
|---|---|---|
| D1 | `task-policy-decide` returns `feature_vector` and stores no episode | The command has never stored an episode. A decide-time episode has no outcome, so `train`'s full-episode filter would drop it. The caller copies the list when the episode is registered. Refusal still writes nothing |
| D2 | `train` refuses a contextual snapshot | The ADR names init and decide. Today's `train` would wrap the snapshot as a `SoftmaxPolicy` and move the unused logits |
| D3 | Contextual decide samples or takes the argmax of \(\pi(\cdot \mid \phi)\). It does not call `assess_autonomy` | That helper reads the unused logits. ADR-003 is not edited. `--greedy` still sets `action_logprob`, so the episode can train |
| D4 | `task-policy-authority-set` to `full` is refused for this kind | The ADR refuses the pair at init. A later authority command would create it |
| D5 | The printed contextual payload has no `action_probabilities` | `probabilities(None)` is uniform for every weight matrix. Printing it would describe a distribution the policy does not use |
| D6 | A batch applies \(\eta\) times the mean of the one-episode rows, with the sibling learner's baseline EMA, and with no entropy term and no importance weight | A one-episode call matches ADR-038 §4.1. The example's `0.3` and `0.05` stay in the example. `LearnerConfig` supplies \(\eta\) and the decay |

---

## 5. Error Handling

| Scenario | Behavior |
|---|---|
| `update` on a `SoftmaxPolicy` | `TypeError`; snapshot unchanged |
| `ReinforceLearner.update` on a `ContextualSoftmaxPolicy` | `TypeError`, as today |
| Aggregate reward `1.1`, `-1.1`, or `NaN` | `ValueError`; snapshot unchanged |
| Every episode skipped | No `apply_update`; version unchanged |
| `feature_vector` only inside `context_features` | `skipped_missing_vector`; weights unchanged |
| `--feature-dim` with full authority | Exit 2; no policy stored |
| `--features` missing or unusable on a contextual snapshot | Exit 2; store unchanged |
| `--features` on a scalar snapshot | Exit 2; store unchanged |
| `train` on a contextual snapshot | Skipped; weights and logits unchanged |
| Authority set to `full` on a contextual snapshot | Exit 2; snapshot unchanged |

---

## 6. Out of Scope

The same boundary as BRD-038. In particular: no feature schema, no LinUCB, no warm-start of weight rows, no change to `ReinforceLearner` or `LearningRunner`, no catalog edit, and no episode insert inside `task-policy-decide`.

---

## 7. Confirmed bounds

Menno confirmed these on 2026-10-30. They stay outside this design.

1. **Coordinates of \(\phi\).** The caller names them. This package fixes the length only (Q1 A).
2. **ADR-020.** A new contextual policy starts at zero rows. A later ADR can add a weight-row donor map (Q2 A).
3. **HYP-AL-018.** LinUCB / LinTS is a separate ADR, after this learner and these CLI flags exist (Q3 A).
