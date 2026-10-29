# FDD-015: Bayesian Bandit Posterior Sampling (Thompson Sampling)

**Source ADR:** [ADR-015](../../adr/ADR-015-bayesian-bandit-posterior-sampling.md) — Accepted (2026-10-28)  
**Source BRD:** [BRD-015](../Business-Requirements/BRD-015-bayesian-bandit-posterior-sampling.md)  
**Status:** Approved (2026-10-29, Menno) — derived from Accepted ADR-015 and BRD-015; adjudicated via `approve-fdd` (robust utility 0.720, episode `c3801042-49c4-407e-823d-282071b3d05f`). Section 4 lists where this design departs from ADR-015 §4.4. Menno confirmed the departures D1 to D6 on 2026-10-29 and ADR-015 §4.1, §4.3 and §4.4 were amended to match.  

---

## 1. Architecture & Component Placement

1. **New module** `src/agent_learning/policy/thompson.py` with `ThompsonPolicy(Policy)` and the pure function `seed_for`. A second module `src/agent_learning/learners/thompson.py` holds `ThompsonLearner(Learner)`. The policy imports `random`, `hmac`, `hashlib` and `math` from the standard library; it reads `PolicySnapshot` and `Action` from `agent_learning.types`. Nothing is imported from `agent_learning.storage`, and nothing does file I/O. No numpy is needed: `random.Random.betavariate` draws a Beta sample.
2. **Package export:** `ThompsonPolicy` and `ThompsonLearner` are re-exported from `agent_learning/__init__.py` and from the `policy` and `learners` packages, as `SoftmaxPolicy` and `ReinforceLearner` are.
3. **State in the snapshot.** The posterior lives in `PolicySnapshot.metadata["posterior_parameters"]` (BRU-015-06). `logits` stays at its zero default, because `PolicySnapshot` has no field for a posterior and ADR-002 forbids a new record type.
4. **Caller owns persistence.** As for `SoftmaxPolicy`, the policy never touches the store. The caller persists the snapshot and attaches the sampling record to `Episode.metadata`.
5. **Shared types change in one place:** `Decision.logprob` becomes `Optional[float]` (D3). Everything else in `policy/base.py` and `learners/base.py` is unchanged.

---

## 2. Data Contract

### 2.1 Constants
| Name | Value | Meaning |
|---|---|---|
| `PRIOR_ALPHA`, `PRIOR_BETA` | 1.0, 1.0 | uniform prior for every action (ADR-015 §4.1) |
| `N_MAX` | 5000.0 | ceiling on `alpha + beta` per action (BRU-015-05) |
| `SELECTION_BASIS` | `"thompson_sampling"` | value of `Episode.metadata["selection_basis"]` for a Thompson decision |

### 2.2 Posterior parameters
```json
"posterior_parameters": {"alpha": {"action_1": 14.0, "action_2": 3.0}, "beta": {"action_1": 2.0, "action_2": 8.0}}
```
Keyed by action id (D4). An action absent from the mapping is read as the prior. A value that is not finite or not positive is rejected when the snapshot is read.

### 2.3 Sampling record
`Episode.metadata["thompson_sampling"]` holds:
```json
{
  "request_id": "req-001",
  "timestamp": "2026-10-29T08:00:00+00:00",
  "prng_seed": "8472910384719203841",
  "posterior_parameters": {"alpha": {"action_1": 14.0, "action_2": 3.0}, "beta": {"action_1": 2.0, "action_2": 8.0}},
  "sampled_payoffs": {"action_1": 0.842, "action_2": 0.315}
}
```
`prng_seed` is a decimal string (BRU-015-02). The record adds `request_id`, `timestamp` and the posterior used for the draw to the fields ADR-015 §4.3 lists, because the seed cannot be re-derived, and the draw cannot be re-run, without them (D5). `selection_basis` is stored beside it, not inside it.

---

## 3. Behavior

1. **`seed_for(policy_id, request_id, timestamp) -> int`.** `int(HMAC-SHA256(key=policy_id, msg=request_id + "|" + timestamp).hexdigest()[:16], 16)`. The separator `"|"` is fixed here so two different pairs cannot concatenate to the same message. It raises `ValueError` for an empty `policy_id`, `request_id` or `timestamp`.
2. **`ThompsonPolicy.from_actions(actions, *, agent_id, task_id)`** builds a snapshot with every action at the prior. **`from_snapshot(snapshot)`** reads `metadata["posterior_parameters"]` (section 2.2) and validates it. Both mirror `SoftmaxPolicy`.
3. **`choose(state=None, *, request_id=None, timestamp=None) -> Decision`.**
   1. If `request_id` or `timestamp` is missing the policy supplies it (a new UUID, the current UTC time in ISO 8601), so `policy.choose()` keeps working for the callers in `decision.py` and `__init__.py` (D2). Whatever is used is recorded.
   2. `seed = seed_for(snapshot.id, request_id, timestamp)`; a `random.Random(seed)` draws `betavariate(alpha_a, beta_a)` for each action in snapshot order.
   3. The action with the highest draw is chosen; a tie goes to the earlier action in snapshot order.
   4. The returned `Decision` has `logprob=None` (D3) and `probabilities` equal to the draw-free posterior mean `alpha / (alpha + beta)` normalised over the actions, for display only. It is not the selection probability, and the docstring says so.
   5. The sampling record of section 2.3 is made available as `policy.last_sampling_record()`, a deep copy, for the caller to attach to the episode. The policy does not hold a reference the caller can mutate.
4. **`replay(record) -> dict`** (module function). Re-derives the seed from the record's `request_id` and `timestamp` and the snapshot id, checks it equals `prng_seed`, redraws from the recorded `posterior_parameters`, and returns the redrawn vector. It does not read the store.
5. **`apply_update(...)`** raises `TypeError("use ThompsonLearner")`: a Thompson policy has no logits to move (D6).
6. **`ThompsonLearner.update(policy, episodes, rewards)`** requires a `ThompsonPolicy` (`TypeError` otherwise). It indexes the newest `RewardSource.AGGREGATE` reward per episode, as `ReinforceLearner` does; it raises `ValueError` for a reward that is not finite or lies outside [-1, 1]. For each episode whose `metadata["selection_basis"]` is `"thompson_sampling"`, whose `action_id` is in the action space, and that has a reward:
   1. `r = (value + 1) / 2` (D1).
   2. `alpha_a += r`, `beta_a += 1 - r` for the chosen action.
   Then, once per call and per action, the ceiling: with `total = alpha + beta` computed first, if `total > N_MAX`, both parameters are multiplied by `N_MAX / total`. The snapshot version advances (`advance_version`) and `episodes_seen` and `updates_applied` are updated. The result is a `LearnerResult` with `episodes_used`, `mean_reward` (of the mapped `r`), the posterior before and after in `extra`, and `consumed_inputs`. A call with no usable episode changes nothing and returns `episodes_used=0`.
7. **`ReinforceLearner` is unchanged.** It already skips an episode whose `action_logprob` is `None` (`reinforce.py`, the check on `action_logprob is None`), and `Decision.logprob=None` flows to `Episode.action_logprob=None` through `decision.py` and `__init__.py`. The code design of ADR-015 §4.4 asked the FDD to add a guard; none is needed, and Story 15.5 tests the existing behaviour (D6 also covers the counter name).

**Worked check (arithmetic, to be re-run when built).** Beta(1, 1) with r = 1.0 gives (2, 1). Beta(14, 2) with r = 0.5 gives (14.5, 2.5). A posterior (4000, 1500) with r = 1 first becomes (4001, 1500), total 5501, and is rescaled by 5000 / 5501 to (3636.6..., 1363.4...), total 5000.

---

## 4. Departures from ADR-015 §4.4

Each is a place where the code design of ADR-015 §4.4, as first accepted, did not fit the code that exists today. Menno confirmed all six on 2026-10-29 and ADR-015 was amended; the "ADR-015 §4.4 says" column is the text before that amendment.

| # | ADR-015 §4.4 says | This FDD does | Why |
|---|---|---|---|
| D1 | The update takes a reward `r ∈ [0, 1]` | `r = (Reward.value + 1) / 2` | `Reward.value` is in [-1, 1] (`types.py`), and `ReinforceLearner` rejects anything else. A learner fed `-1.0` would otherwise give `beta` a negative increment |
| D2 | `choose(state=None, *, request_id, timestamp)` with both required | Both optional; the policy supplies and records them when absent | `decision.py` and `__init__.py` call `policy.choose()` with no arguments. A required keyword would break the `Policy` contract |
| D3 | A `Decision` with a log-probability | `Decision.logprob` becomes `Optional[float]`, `None` for Thompson | Probability matching has no selection probability. The callers copy `decision.logprob` into `Episode.action_logprob`; a made-up number would let `ReinforceLearner` treat the draw as a softmax sample |
| D4 | `{"alpha": [14.0, 3.0], "beta": [2.0, 8.0]}` as lists | Mappings keyed by action id | A list is correct only while the action order never changes; the sampled payoffs in the same example are already keyed by id |
| D5 | The record holds `prng_seed`, `posterior_parameters`, `sampled_payoffs` | Adds `request_id` and `timestamp` | The seed is an HMAC of the request id and timestamp; without them a reader can store the seed but not check it |
| D6 | `ReinforceLearner` needs a guard that skips Thompson episodes; `ThompsonPolicy` implements `Policy` | No guard is added (the `None` log-probability already skips it); `apply_update` raises | `Policy.apply_update` takes logit deltas, which a posterior does not have. The existing skip counts these episodes as `full_authority_excluded`, a name that is wrong for them; renaming it is out of scope (section 7, item 3) |

---

## 5. Error Handling

| Scenario | Behavior |
|---|---|
| `seed_for` with an empty argument | `ValueError` naming the argument |
| `from_snapshot` with a non-finite or non-positive `alpha` or `beta` | `ValueError` naming the action |
| `from_snapshot` with an action id in the posterior that is not in the action space | `ValueError` |
| `choose` on a policy with no actions | `ValueError`, as `SoftmaxPolicy` |
| Reward outside [-1, 1] or not finite | `ValueError` |
| `ThompsonLearner.update` given a `SoftmaxPolicy` | `TypeError` |
| Episode with another `selection_basis`, an unknown `action_id`, or no reward | skipped, not counted in `episodes_used` |
| `apply_update` on a `ThompsonPolicy` | `TypeError("use ThompsonLearner")` |
| `replay` where the re-derived seed differs from `prng_seed` | `ValueError`; the record is not trusted |
| Total pseudo-count above `N_MAX` | rescaled, ratio kept within 1e-9 |

---

## 6. Out of Scope

A study of decision quality against REINFORCE (data gap, BRD-015 Out of Scope); exponential discounting; contextual posteriors; transferred priors; any change to `ReinforceLearner`'s arithmetic; wiring Thompson sampling into the CLI's `task-policy-decide`.

---

## 7. Decisions and Open Questions

1. **D1 to D6: decided (2026-10-29).** Menno confirmed them and ADR-015 was amended to match.
2. **Open: discounting.** ADR-015 §4.1 allows an exponential factor as an alternative to the ceiling. Only the ceiling is built; the maintainer says if the factor is wanted.
3. **Open: the REINFORCE counter name.** Thompson episodes are counted under `full_authority_excluded`. Either the name widens to "no behaviour probability" or a second counter is added. A change touches `reinforce.py` and its tests, so it is a separate decision.
4. **Open: replay across Python versions.** `random.Random.betavariate` is deterministic for one implementation, but CPython does not promise the same stream across versions. The recorded `sampled_payoffs` is the ground truth; `replay` checks the redraw against it and reports a mismatch as a version difference, not as tampering. Whether to record the interpreter version in the record is open.
5. **`N_MAX = 5000`:** taken from ADR-015 Invariant 4. There is no data on non-stationarity behind it.

---

## 8. Test Data

*Real:* the recorded approval episodes (41 when ADR-015 was written, 58 committed files on 2026-10-29), replayed as `r = 1.0` for the action taken (ADR-015 §4.4). Every one is accepted and the `approve-*` policies are full authority, so this is a real positive-only history; they carry no log-probability, so the REINFORCE side of the replay assigns one from a softmax policy and says so (Story 15.6) and it exercises the failure mode HYP-AL-002 names. It cannot show that Thompson sampling is better. *Gap:* a low-authority policy with at least 100 scored episodes including failures. *Oracle:* closed-form Beta updates, labelled as arithmetic checks, not as evidence.
