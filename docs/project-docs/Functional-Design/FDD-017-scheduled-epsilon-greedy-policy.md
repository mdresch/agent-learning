# FDD-017: Scheduled Epsilon-Greedy Policy Baseline

**Source ADR:** [ADR-017](../../adr/ADR-017-scheduled-epsilon-greedy-policy.md) — Accepted (2026-10-28)  
**Source BRD:** [BRD-017](../Business-Requirements/BRD-017-scheduled-epsilon-greedy-policy.md)  
**Status:** Approved (2026-10-29, Menno) — derived from Accepted ADR-017 and BRD-017; adjudicated via `approve-fdd` (robust utility 0.714, episode `956b167a-de05-41d6-8844-b718d8806d53`). Section 4 lists where this design departs from ADR-017 §4.1 to §4.3. Menno confirmed the departures F1 to F7 on 2026-10-29 (F3, F5 and F6 as the options recommended in this FDD) and ADR-017 §4.1, §4.2 and §4.3 were amended to match.  

---

## 1. Architecture & Component Placement

1. **New modules** `src/agent_learning/policy/epsilon_greedy.py` (`EpsilonGreedyPolicy(Policy)`, `epsilon_at`) and `src/agent_learning/learners/epsilon_greedy.py` (`EpsilonGreedyLearner(Learner)`). A third module, `src/agent_learning/policy/action_statistics.py`, holds what this policy shares with the UCB policy of FDD-016: the `ActionStats` record, its validation, and the pure function that adds counted rewards to it (F6). The policy uses the standard library (`random`, `math`) only, imports `seed_for` from the Thompson module (Story 15.1 of Epic 15), and reads `PolicySnapshot` and `Action` from `agent_learning.types`. Nothing is imported from `agent_learning.storage`, and nothing does file I/O.
2. **Package export:** `EpsilonGreedyPolicy` and `EpsilonGreedyLearner` are re-exported from `agent_learning/__init__.py` and from the `policy` and `learners` packages.
3. **State in the snapshot** (BRU-017-09): `PolicySnapshot.metadata` holds `policy_type`, `epsilon_schedule`, `action_statistics` and `consumed_episode_ids`. `logits` stays at its zero default.
4. **Caller owns persistence.** The policy never touches the store; the caller persists the snapshot and attaches the decision record to `Episode.metadata`.
5. **Shared types.** `Decision.logprob` must be `Optional[float]` (F3), delivered by Story 15.3 of Epic 15.

---

## 2. Data Contract

### 2.1 Constants and the `reversible` flag
| Name | Value | Meaning |
|---|---|---|
| `SELECTION_BASIS` | `"epsilon_greedy"` | value of `Episode.metadata["selection_basis"]` |
| neutral mean | 0.5 | the mean of an action with no pulls, on [0, 1] (F1) |

The schedule arguments `eps0`, `delta` and `floor` have no default value (F5). The safe subset is the set of actions with `Action.parameters["reversible"] is True`; any other value of that key, including the string `"true"`, raises `ValueError` (BRU-017-04). An action without the key is not safe.

### 2.2 Snapshot metadata
```json
{
  "policy_type": "epsilon_greedy",
  "epsilon_schedule": {"eps0": 0.5, "delta": 0.05, "floor": 0.05},
  "action_statistics": {
    "action_id_1": {"pull_count": 42, "cumulative_reward": 37.5, "mean_reward": 0.8928},
    "action_id_2": {"pull_count": 15, "cumulative_reward": 10.0, "mean_reward": 0.6667}
  },
  "consumed_episode_ids": ["ep-0001", "ep-0002"]
}
```
`action_statistics` and `consumed_episode_ids` have exactly the shape and rules of FDD-016 §2.2, so one record serves both policies: `cumulative_reward` is the sum of the mapped rewards in `[0, pull_count]`, and `mean_reward` always equals `cumulative_reward / pull_count` (stored as 0.0 when there are no pulls). The schedule values in the example are placeholders, not defaults.

### 2.3 Decision record
`Episode.metadata["epsilon_greedy"]` holds:
```json
{
  "request_id": "req-001",
  "timestamp": "2026-10-29T08:00:00+00:00",
  "prng_seed": "8472910384719203841",
  "branch_taken": "exploration",
  "exploration_rate_applied": 0.142,
  "total_pulls": 57,
  "empirical_means": {"action_id_1": 0.8928, "action_id_2": 0.6667, "action_id_3": 0.5},
  "chosen": "action_id_2"
}
```
`prng_seed` is a decimal string (BRU-017-06). `empirical_means` is on [0, 1] and shows 0.5 for an action with no pulls (F1). `selection_basis` is stored beside the record, not inside it. The action ids above are placeholders.

---

## 3. Behavior

1. **`epsilon_at(t, eps0, delta, floor) -> float`** returns `max(floor, eps0 / (1 + delta * t))`. It raises `ValueError` unless `0 <= floor <= eps0 <= 1`, `delta >= 0` and `t >= 0`, and for a non-finite argument.
2. **`EpsilonGreedyPolicy.from_actions(actions, *, eps0, delta, floor, agent_id, task_id)`** builds a snapshot with every action at zero pulls and validates the schedule and every `reversible` flag (F7). **`from_snapshot(snapshot)`** reads and validates section 2.2.
3. **`choose(state=None, *, request_id=None, timestamp=None) -> Decision`.**
   1. A missing `request_id` or `timestamp` is supplied (a new UUID, the current UTC time) and recorded, so a no-argument `policy.choose()` keeps working (F2).
   2. `seed = seed_for(snapshot.id, request_id, timestamp)`; `rng = random.Random(seed)`.
   3. `t` is the sum of the pull counts. The safe subset is read and sorted by id. `eps = epsilon_at(t, ...)` when the subset is not empty, else `0.0` (BRU-017-03).
   4. The branch coin: `u = rng.random()` is always drawn first, so the seed is always used and always recorded (F4). The branch is `exploration` when `u < eps`, else `exploitation`. With `eps = 0.0` the branch is always exploitation.
   5. **Exploitation:** each action's mean is its `mean_reward` when `pull_count > 0`, else 0.5 (F1). The chosen action has the highest mean; a tie goes to the higher `pull_count`, then to the smaller `action.id` (BRU-017-07). No further random number is drawn.
   6. **Exploration:** `chosen = rng.choice(safe)`, where `safe` is the sorted list. The pick may be the greedy action. It is never an unflagged action (BRU-017-02).
   7. The returned `Decision` has `logprob=None` (F3). Its `probabilities` are the selection probabilities of this step, for display: with greedy action `g`, safe subset `S` and rate `eps`, `P(a) = (1 - eps) * [a = g] + eps / |S| * [a in S]`, and `P(a) = [a = g]` when `S` is empty.
4. **`last_decision_record()`** returns a deep copy of the record of section 2.3.
5. **`replay(record, snapshot) -> dict`** (module function). Re-derives the seed from the record's `request_id` and `timestamp` and the snapshot id, checks it equals `prng_seed`, redraws the coin and the pick from the recorded statistics, and returns `{"branch_taken", "chosen"}`. It raises `ValueError` when the seed differs.
6. **`apply_update(...)`** raises `TypeError("use EpsilonGreedyLearner")`: there are no logits to move.
7. **`EpsilonGreedyLearner.update(policy, episodes, rewards)`** requires an `EpsilonGreedyPolicy` (`TypeError` otherwise) and otherwise follows FDD-016 §3.6 with `selection_basis == "epsilon_greedy"`: the newest `RewardSource.AGGREGATE` reward per episode, `r = (value + 1) / 2`, a reward that is not finite or outside [-1, 1] raises `ValueError`, an episode whose id is already in `consumed_episode_ids` is skipped, and the shared function of section 1 adds the reward and recomputes the mean (F6).
8. **`ReinforceLearner` is unchanged.** It skips an episode whose `action_logprob` is `None`; Story 17.5 tests that.

**Worked checks (arithmetic, to be re-run when built).** With `eps0 = 0.5`, `delta = 0.05`, `floor = 0.05`: `t = 0` gives 0.5; `t = 20` gives 0.25; `t = 180` gives 0.05, the floor; `t = 1000` gives 0.05 (the harmonic term is 0.0098). With `eps = 0.2`, safe subset `{a, b}` and greedy action `a`: `P(a) = 0.9`, `P(b) = 0.1`, any other action 0. Three actions with no pulls have means 0.5 each, so the greedy pick is the smallest id.

---

## 4. Departures from ADR-017

Each is a place where ADR-017, as first accepted, did not fit the code that exists today or contradicted itself. Menno confirmed all seven on 2026-10-29 and ADR-017 was amended; the "ADR-017 says" column is the text before that amendment.

| # | ADR-017 says | This FDD does | Why |
|---|---|---|---|
| F1 | Means are over the shaped reward in [-1, 1], and an unpulled action has mean 0.0 | Statistics are kept on [0, 1] by `(value + 1) / 2`, and an unpulled action counts as 0.5 when choosing | The action statistics are shared with ADR-016, which keeps `[0, 1]` and the record of its FDD. A monotone map leaves the argmax unchanged, and 0.5 is exactly ADR-017's 0.0 on the new scale. Leaving 0.0 on [0, 1] would make an unpulled action the worst possible, changing the cold start |
| F2 | `choose(state=None, *, request_id, timestamp)` with both required | Both optional; supplied and recorded when absent | `decision.py` and `__init__.py` call `policy.choose()` with no arguments. Same as FDD-015 D2 |
| F3 | Not stated (the callers copy `decision.logprob` into the episode) | `logprob` is `None`; `probabilities` carry the real selection probabilities | The policy has a well-defined behaviour probability, so a real log-probability could be given. With one, `ReinforceLearner` would use these episodes as off-policy data. `None` keeps them out, as for Thompson and UCB. Needs Menno's choice |
| F4 | The exploitation branch never draws a random number | The branch coin `u` is drawn from the seeded PRNG on every decision; only the greedy pick itself draws none | Choosing the branch with probability `eps` needs a random number. The seed is therefore always used, which is what ADR-017 §4.2's example (a seed beside `"branch_taken": "exploitation"`) already shows |
| F5 | A fixed default schedule (§6), but no values | `eps0`, `delta` and `floor` are required arguments with no default | The ADR gives no numbers, and the only values in the repo are the synthetic sketch's. A default would be an invented tuning. Needs Menno's choice |
| F6 | The learner "shares the `action_statistics` update with ADR-016" | A shared module `policy/action_statistics.py`, and the counted-once rule of FDD-016 E6 (`consumed_episode_ids`) | The training runner re-queries recent episodes every run, and the two policies must not drift apart. FDD-016 holds `ActionStats` inside `ucb.py`; moving it is a follow-up amendment of FDD-016 (section 7 item 3). Needs Menno's choice |
| F7 | `reversible` must be a boolean, else `ValueError` (the check is described at choose time) | The check also runs when the policy is built and when a snapshot is read | A bad flag is reported once, at the point the action definitions are loaded, not on the first exploration step |

---

## 5. Error Handling

| Scenario | Behavior |
|---|---|
| `epsilon_at` with `delta < 0`, `eps0 < floor`, a value outside [0, 1], `t < 0`, or a non-finite value | `ValueError` naming the argument |
| `reversible` present and not a JSON boolean | `ValueError` naming the action |
| No action is safe | `eps` is 0.0; every decision is exploitation |
| `from_snapshot` with an invalid statistic, a duplicate in `consumed_episode_ids`, a `mean_reward` differing from `cumulative_reward / pull_count` by more than 1e-9, or an action outside the action space | `ValueError` naming it |
| Reward outside [-1, 1] or not finite | `ValueError` |
| `EpsilonGreedyLearner.update` given another policy type | `TypeError` |
| Episode with another `selection_basis`, an unknown `action_id`, no reward, or an id already consumed | skipped, not counted in `episodes_used` |
| `apply_update` on the policy | `TypeError("use EpsilonGreedyLearner")` |
| `replay` where the re-derived seed differs from `prng_seed` | `ValueError`; the record is not trusted |
| `choose` on a policy with no actions | `ValueError`, as `SoftmaxPolicy` |

---

## 6. Out of Scope

The benchmark against REINFORCE, UCB and Thompson sampling (BRD-017 Out of Scope); declaring `reversible` on a real action; contextual variants; any change to `ReinforceLearner` or the autonomy gates; wiring the policy into the CLI.

---

## 7. Decisions and Open Questions

1. **F1 to F7: decided (2026-10-29).** Menno confirmed them and ADR-017 was amended to match. F3 is `None`, F5 is required arguments with no default, F6 is the shared module.
2. **Walkthrough sketch aligned (2026-10-29).** `examples/methodologies/11-epsilon-greedy/sketch.py` gave an unpulled action the mean 1.0 and let the greedy branch consider only the safe actions. It now counts an unpulled action as the neutral mean and picks greedily over every action, with ties by higher pull count then smaller id, masking only exploration, as ADR-017 says. It is still a sketch, not evidence (ADR-036), and is rewritten against the real module once built.
3. **Done: amending FDD-016 and Epic 16 for the shared module.** FDD-016 kept `ActionStats` in `ucb.py`. FDD-016 (section 2.4, departure E7) and Epic 16 now import it from `action_statistics.py` and were re-approved (PR 48), so the two FDDs agree on where the code lives. The module is delivered by whichever epic is built first. This item was changed from open to done on 2026-10-29 as a wording correction; no design changed and the gates were not re-run.
4. **Open: `seed_for` location.** It is built in the Thompson module (Story 15.1). Importing it from there couples this policy to Thompson sampling; moving it to a neutral module is a follow-up.
5. **Open: replay across Python versions.** `random.Random.random` and `choice` are deterministic for one implementation, but CPython does not promise the same stream across versions. The recorded `chosen` and `branch_taken` are the ground truth; `replay` reports a mismatch as a version difference, not as tampering (the same as FDD-015 §7 item 4).
6. **Open: the size of `consumed_episode_ids`.** As FDD-016 §7 item 2.
7. **A consequence to expect, not a defect.** With no `reversible` flag on any action, which is every action today, the policy is purely greedy and locks onto the first action with a good mean (BRU-017-03). Story 17.6 shows this on the recorded history.

---

## 8. Test Data

*Real:* the recorded approval episodes (41 when ADR-017 was written, 58 committed files on 2026-10-29), replayed as `r = 1.0` for the action taken, the same replay as ADR-015 and ADR-016, so the three can be compared on identical history later. They carry no log-probability, so the REINFORCE side of any comparison assigns one from a softmax policy and says so. *Gap:* the `reversible` flag has never been declared on a real action; a human decision is needed first. *Oracle:* the schedule values and the selection probabilities of section 3, checked by hand, labelled as arithmetic checks, not as evidence.
