# FDD-016: Deterministic Upper Confidence Bound (UCB) Decision Policy

**Source ADR:** [ADR-016](../../adr/ADR-016-deterministic-ucb-decision-policy.md) — Accepted (2026-10-28)  
**Source BRD:** [BRD-016](../Business-Requirements/BRD-016-deterministic-ucb-decision-policy.md)  
**Status:** Approved (2026-10-29, Menno), amended 2026-10-29 with E7 (shared statistics module) and re-approved via `approve-fdd` (robust utility 0.732, episode `ea37755a-c23e-4f12-b11c-984bbae6ae3f`; comparison with the previous approval 0.720: progression, margin 0.612 to 0.624, no criterion lower) — derived from Accepted ADR-016 and BRD-016; adjudicated via `approve-fdd` (robust utility 0.720, episode `675a19db-33b2-4cf4-a954-6fd545e13d9f`). Section 4 lists where this design departs from ADR-016 §4.3 and §4.4. Menno confirmed the departures E1 to E6 on 2026-10-29 (E1, E2 and E4 follow his choices for ADR-015) and ADR-016 §4.3 and §4.4 are amended to match.  

---

## 1. Architecture & Component Placement

1. **New modules** `src/agent_learning/policy/ucb.py` (`UCBPolicy(Policy)`, `ucb_scores`), `src/agent_learning/learners/ucb.py` (`UCBLearner(Learner)`) and `src/agent_learning/policy/action_statistics.py` (`ActionStats`, `read_statistics`, `add_rewards`; section 2.4), the last shared with the epsilon-greedy policy of FDD-017 (E7). `ucb.py` and `learners/ucb.py` import it and hold no copy of its rules. All three use the standard library only; `ucb.py` imports `wilson_lower_bound` from `agent_learning.autonomy` and `PolicySnapshot`, `Action` from `agent_learning.types`. Neither imports `random` or anything from `agent_learning.storage`, and neither does file I/O.
2. **Package export:** `UCBPolicy` and `UCBLearner` are re-exported from `agent_learning/__init__.py` and from the `policy` and `learners` packages.
3. **State in the snapshot** (BRU-016-07): `PolicySnapshot.metadata` holds `policy_type`, `ucb_variant`, `exploration_constant`, `action_statistics` and `consumed_episode_ids` (E6). `logits` stays at its zero default.
4. **Caller owns persistence.** The policy never touches the store; the caller persists the snapshot and attaches the decision record to `Episode.metadata`.
5. **Shared types.** `Decision.logprob` must be `Optional[float]` so UCB can return `None` (E2). That change belongs to Story 15.3 of Epic 15; Epic 16's policy stories are built after it. `autonomy.wilson_lower_bound` keeps its behaviour; its parameter annotation widens from `int` to `float` (E3).

---

## 2. Data Contract

### 2.1 Constants
| Name | Value | Meaning |
|---|---|---|
| `WILSON_Z` | 1.96 | the interval width of the `wilson` variant (ADR-016 §4.1) |
| `C_DEFAULT` | `sqrt(2)` | exploration constant of the `standard` variant |
| `SELECTION_BASIS` | `"ucb"` | value of `Episode.metadata["selection_basis"]` for a UCB decision |

### 2.2 Snapshot metadata
```json
{
  "policy_type": "ucb",
  "ucb_variant": "wilson",
  "exploration_constant": 1.4142135623730951,
  "action_statistics": {
    "action_id_1": {"pull_count": 42, "cumulative_reward": 37.5, "mean_reward": 0.8928},
    "action_id_2": {"pull_count": 15, "cumulative_reward": 10.0, "mean_reward": 0.6667}
  },
  "consumed_episode_ids": ["ep-0001", "ep-0002"]
}
```
`mean_reward` is stored as in ADR-016 (E5) and always equals `cumulative_reward / pull_count` (0.0 when there are no pulls); the learner recomputes it on every update, and `from_snapshot` rejects a snapshot where the stored value differs from the derived one by more than 1e-9. `pull_count` is a non-negative integer; `cumulative_reward` is a finite float in `[0, pull_count]`. An action absent from `action_statistics` reads as zero pulls. `consumed_episode_ids` is the list of the ids of the episodes already counted; each id appears at most once, and the list is empty before the first update (E6).

### 2.3 Decision record
`Episode.metadata["ucb"]` holds `variant`, `exploration_constant`, `total_pulls`, `chosen`, and `scores`, a mapping from action id to the bound or to `null` when the bound is infinite (JSON has no infinity; E4). `selection_basis` is stored beside it. The record lets a reader check the choice without the snapshot.

### 2.4 The shared statistics module (E7)
`policy/action_statistics.py` owns the statistics record of section 2.2 for every policy that keeps pull counts and rewards (this one and FDD-017). It is pure: standard library only, no `random`, nothing from `agent_learning.storage`.
```python
@dataclass(frozen=True)
class ActionStats:
    pull_count: int
    cumulative_reward: float
    mean_reward: float
def read_statistics(metadata: Mapping[str, object], action_ids: Sequence[str]) -> dict[str, ActionStats]: ...
def add_rewards(metadata: dict[str, object], action_ids: Sequence[str],
                items: Iterable[tuple[str, str, float]]) -> tuple[str, ...]: ...
```
- `read_statistics` returns the statistics of every action in `action_ids` (an action absent from the record reads as zero pulls) and raises `ValueError` naming the action or the id for: an action outside `action_ids`, a negative or non-integer `pull_count`, a `cumulative_reward` outside `[0, pull_count]` or not finite, a `mean_reward` differing from `cumulative_reward / pull_count` by more than 1e-9, or a duplicate in `consumed_episode_ids`.
- `add_rewards` takes `(episode_id, action_id, value)` items with `value` in [-1, 1], raises `ValueError` for a value that is not finite or outside that range, and changes `metadata` in place: for each item whose episode id is not in `consumed_episode_ids` and not already counted in this call, it adds `r = (value + 1) / 2` (E1), increments `pull_count`, recomputes `mean_reward`, and appends the id. It returns the ids it counted, in order. It does not look at `selection_basis`; each learner selects its own episodes.

---

## 3. Behavior

1. **`ucb_scores(stats, total, *, variant="wilson", c=C_DEFAULT) -> dict[str, float]`.** For an action with `pull_count == 0` the score is `math.inf` in both variants. Otherwise:
   - `standard`: `mean + c * sqrt(2 * ln(total) / N)`, with `mean = cumulative_reward / N`. With `total == 1` the log is 0 and the bonus is 0.
   - `wilson`: `1 - wilson_lower_bound(N - k, N, WILSON_Z)` with `k = cumulative_reward` (E3). `c` and `total` are not used by this variant.
   It raises `ValueError` for an unknown variant, `c <= 0`, a `total` that is not the sum of the pull counts, or a statistic outside the ranges of section 2.2.
2. **`UCBPolicy.from_actions(actions, *, variant, c, agent_id, task_id)`** builds a snapshot with every action at zero. **`from_snapshot(snapshot)`** reads and validates section 2.2.
3. **`choose(state=None) -> Decision`.** Scores every action. The chosen action has the highest score; a tie goes first to the higher `pull_count`, then to the lexicographically smaller `action.id` (BRU-016-02). When several actions are unpulled they all score `inf`, tie on a pull count of 0, and the smallest id wins, which gives the round-robin of BRU-016-04. `Decision.logprob` is `None` (E2) and `probabilities` is one-hot on the chosen action. The call changes nothing on the policy.
4. **`last_decision_record()`** returns a deep copy of the record of section 2.3.
5. **`apply_update(...)`** raises `TypeError("use UCBLearner")`: there are no logits to move.
6. **`UCBLearner.update(policy, episodes, rewards)`** requires a `UCBPolicy` (`TypeError` otherwise). It indexes the newest `RewardSource.AGGREGATE` reward per episode, as `ReinforceLearner` does. An episode is offered when its `metadata["selection_basis"]` is `"ucb"`, its `action_id` is in the action space and it has a reward. The learner passes the offered `(episode_id, action_id, value)` items to `add_rewards` (section 2.4), which maps the reward, skips ids already in `consumed_episode_ids` (E6), adds the rest and recomputes the means (E1, E7). The snapshot version advances, and the result is a `LearnerResult` with `episodes_used`, `mean_reward` of the mapped `r`, the statistics before and after in `extra`, and `consumed_inputs`. A call with no usable episode changes nothing and returns `episodes_used=0`.
7. **`ReinforceLearner` is unchanged.** It skips an episode whose `action_logprob` is `None`, and `Decision.logprob=None` flows to `Episode.action_logprob=None`. Story 16.5 tests the existing behaviour.

**Worked checks (arithmetic, to be re-run when built).** `standard`, c = sqrt(2): action A with N = 10, mean 0.8 and action B with N = 5, mean 0.6, total 15: A = 0.8 + sqrt(2) * sqrt(2 ln 15 / 10) = 1.8408; B = 0.6 + sqrt(2) * sqrt(2 ln 15 / 5) = 2.0719; B is chosen. `wilson`: k = 10, N = 10 gives an upper bound of 1.0 exactly (its center plus spread is 1 + z squared over N); k = 0, N = 10 gives 0.2775.

---

## 4. Departures from ADR-016 §4.3 and §4.4

Each is a place where ADR-016, as first accepted, did not fit the code that exists today. Menno confirmed E1 to E6 on 2026-10-29 and ADR-016 is amended to match; E7 is added by the amendment that moves the shared statistics code; the "ADR-016 says" column is the text before that amendment.

| # | ADR-016 says | This FDD does | Why |
|---|---|---|---|
| E1 | The reward `r` is in [0, 1] | `r = (Reward.value + 1) / 2` | `Reward.value` is in [-1, 1] (`types.py`) and `ReinforceLearner` rejects anything else; a negative reward would corrupt `cumulative_reward` and break both bounds. The same mapping as FDD-015 D1 |
| E2 | `choose` returns one-hot probabilities and `logprob 0.0` | `logprob` is `None`; probabilities stay one-hot | A log-probability of 0.0 is a probability of 1. The callers copy `decision.logprob` into `Episode.action_logprob`, so `ReinforceLearner` would train on a UCB pick as a certain softmax sample. It needs `Decision.logprob` to be `Optional`, which Story 15.3 delivers |
| E3 | Reuse `wilson_lower_bound` by symmetry; "the FDD decides whether to generalise it or to round" | Generalise: the annotation of `successes` widens from `int` to `float`; no behaviour changes | The arithmetic already works on a float, and the symmetry identity holds exactly for it. Rounding would change the mean the policy scores |
| E4 | Unpulled actions have an infinite bound | Same, and the stored decision record uses `null` for an infinite score | JSON has no infinity |
| E5 | `action_statistics` stores `mean_reward` with the counts | Keeps it, as in the ADR, and enforces that it equals `cumulative_reward / pull_count` | Menno chose to keep the ADR's shape (2026-10-29). The risk is a stored copy that disagrees with its parts, so the learner recomputes it and the reader rejects a mismatch |
| E6 | Not stated | The snapshot keeps `consumed_episode_ids`, a list of unique episode ids, and the learner skips an episode whose id is already in it | `TrainingRunner.run_offline_batch` re-queries the latest `episode_limit` episodes on every run and marks none as consumed. REINFORCE tolerates a repeat; a counter does not. Menno chose unique consumed ids (2026-10-29), after first choosing a `created_at` watermark, which would skip a late-rewarded episode for good |
| E7 | Not stated (`ActionStats` was placed in `ucb.py`) | `ActionStats`, its validation and the counted-once update live in `policy/action_statistics.py`, shared with FDD-017 | ADR-017 shares the `action_statistics` record with this policy, and two copies of the validation and of the update can drift apart. Chosen by Menno for FDD-017 F6 (2026-10-29); this amendment applies it here. It changes where the code lives, not what it does |

---

## 5. Error Handling

| Scenario | Behavior |
|---|---|
| Unknown variant, or `c <= 0` | `ValueError` naming the argument |
| `from_snapshot` with a negative or non-integer `pull_count`, or a `cumulative_reward` outside `[0, pull_count]` or not finite | `ValueError` naming the action |
| Action id in the statistics that is not in the action space | `ValueError` |
| Reward outside [-1, 1] or not finite | `ValueError` |
| `UCBLearner.update` given another policy type | `TypeError` |
| Episode with another `selection_basis`, an unknown `action_id`, no reward, or an id already in `consumed_episode_ids` | skipped, not counted in `episodes_used` |
| `from_snapshot` where `consumed_episode_ids` holds a duplicate | `ValueError` naming the id |
| `from_snapshot` where `mean_reward` differs from `cumulative_reward / pull_count` by more than 1e-9 | `ValueError` naming the action |
| `apply_update` on a `UCBPolicy` | `TypeError("use UCBLearner")` |
| `choose` on a policy with no actions | `ValueError`, as `SoftmaxPolicy` |

---

## 6. Out of Scope

A study of decision quality against REINFORCE or Thompson sampling (data gap, BRD-016 Out of Scope); contextual variants; discounted statistics; any change to the autonomy gates; wiring UCB into the CLI.

---

## 7. Decisions and Open Questions

1. **E1 to E6: decided (2026-10-29).** Menno confirmed them and ADR-016 is amended to match.
2. **Open: the size of `consumed_episode_ids`.** It grows by one id per counted episode and is stored in the snapshot, so it is read and written with every update. It has no late-reward loss, which a `created_at` watermark would have. If the list becomes large, pruning ids older than the runner's `episode_limit` window is the next step; it is not built or decided here.
3. **Done: the same gap in ADR-015.** The Thompson learner of FDD-015 had the same repeat problem; ADR-015, BRD-015, FDD-015 and Epic 15 were amended and re-approved (PR 46).
4. **Walkthrough sketch aligned (2026-10-29).** `examples/methodologies/10-ucb/sketch.py` broke ties toward the lower pull count and the larger id, the opposite of ADR-016 §4.2; it now breaks them as the ADR does (higher pull count, then smaller id). It is still a sketch, not evidence (ADR-036), and is rewritten against the real module once built.
5. **Epic 17 repeats some criteria.** Story 17.4 of Epic 17 tests the epsilon-greedy learner against the same rules; both epics run against the one function of section 2.4, whose rules are owned by Stories 16.3 and 16.4. Whichever epic is built first delivers the module.
6. **`WILSON_Z = 1.96` and `C_DEFAULT = sqrt(2)`:** taken from ADR-016 §4.1. There is no data behind either.

---

## 8. Test Data

*Real:* the recorded approval episodes (41 when ADR-016 was written, 58 committed files on 2026-10-29), replayed as `r = 1.0` for the action taken, as in ADR-015. This is a real positive-only history and shows what the bound does when every reward is 1.0; they carry no log-probability, so the REINFORCE side of the replay assigns one from a softmax policy and says so (Story 16.6). *Gap:* a low-authority policy with at least 100 scored episodes including failures, so nothing real can show UCB is better. *Oracle:* published UCB1 worked examples and the section 3 checks, labelled as arithmetic checks, not as evidence.
