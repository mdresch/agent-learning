# Epic 17: Scheduled Epsilon-Greedy Policy Baseline

**Source ADR:** [ADR-017](../adr/ADR-017-scheduled-epsilon-greedy-policy.md) — Accepted (2026-10-28)  
**Source BRD/FDD:** [BRD-017](../project-docs/Business-Requirements/BRD-017-scheduled-epsilon-greedy-policy.md) / [FDD-017](../project-docs/Functional-Design/FDD-017-scheduled-epsilon-greedy-policy.md)  
**Status:** Approved (2026-10-29, Menno) — stories derived from Accepted ADR-017, BRD-017 and FDD-017; adjudicated via `approve-user-stories` (robust utility 0.735, episode `4e6a04e1-48a0-4cee-be3c-d89c4df493a6`). The source-comparison criterion of Story 17.5 AC2 ("reinforce.py is unchanged") was made behavioural on 2026-10-29 and the stories were re-approved via `approve-user-stories` (robust utility 0.739, episode `1e0762b1-4c41-4440-af96-15b628946de3`; comparison with the previous approval: flat, within tolerance, no criterion lower). The epic number follows the source ADR number, as Epic 16 follows ADR-016.  

Six stories build `src/agent_learning/policy/epsilon_greedy.py`, `src/agent_learning/learners/epsilon_greedy.py` and `src/agent_learning/policy/action_statistics.py`. Each rule sits in exactly one story's criteria (LL-012). Contract tests are `tests/test_epsilon_schedule.py` (17.1), `tests/test_epsilon_safety_mask.py` (17.2), `tests/test_epsilon_policy.py` (17.3), `tests/test_epsilon_learner.py` (17.4), `tests/test_epsilon_reinforce_guard.py` (17.5) and `tests/test_epsilon_positive_only.py` (17.6). The benchmark against the other policies is not a story (BRD-017 Out of Scope).

**Stories 17.1 to 17.6 are unblocked except for dependencies:** Menno confirmed FDD-017 §4 (F1 to F7) on 2026-10-29. Stories 17.3 and 17.5 depend on Epic 15 Stories 15.1 (`seed_for`) and 15.3 (`Decision.logprob` optional); 17.1, 17.2, 17.4 and 17.6 do not. Story 17.4 also depends on the shared statistics module of FDD-017 F6, which FDD-016 and Epic 16 Stories 16.3 and 16.4 now import (PR 48; FDD-017 §7 item 3). This sentence was updated on 2026-10-29 as a wording correction; no criterion changed and the gate was not re-run.

Fixture used by the criteria below ("the base policy"): three actions `a`, `b` and `c`; `a` and `b` carry `"reversible": true` and `c` carries no flag; schedule `eps0 = 0.5`, `delta = 0.05`, `floor = 0.05`; no pulls. These schedule values are test values, not defaults.

---

## Story 17.1 — The Schedule

**Status:** Ready  
**As** an auditor, **I want** the exploration rate to be a pure, bounded function of the pull count, **so that** its decay can be checked by hand.

### Acceptance Criteria:
- **$AC_0$ (Values):** `epsilon_at(t, 0.5, 0.05, 0.05)` gives 0.5 for `t = 0`, 0.25 for `t = 20`, 0.05 for `t = 180` and 0.05 for `t = 1000`, each within 1e-12, and the test recomputes them from the formula itself.
- **$AC_1$ (Non-Increasing):** over `t` from 0 to 5000, the rate never rises from one `t` to the next and never falls below the floor.
- **$AC_2$ (Floor Equals Initial):** with `floor = eps0` the rate is constant at `eps0`; with `delta = 0` it is `eps0` for every `t`.
- **$AC_3$ (Validation):** `ValueError` naming the argument for `delta < 0`, `eps0 < floor`, a value outside [0, 1], `t < 0`, and any non-finite argument.

---

## Story 17.2 — The Safety Mask

**Status:** Ready  
**As** a maintainer, **I want** exploration restricted to actions a human has declared reversible, **so that** a random probe cannot run a destructive action.

### Acceptance Criteria:
- **$AC_0$ (Safe Subset):** on the base policy the safe subset is `{a, b}`; an action without the key, or with `"reversible": false`, is not safe.
- **$AC_1$ (Boolean Only):** `"reversible": "true"`, `1`, `null` or a list raises `ValueError` naming the action, both when the policy is built and when a snapshot is read.
- **$AC_2$ (Empty Subset):** with no safe action the rate applied is 0.0 for every `t`, including `t = 0`.
- **$AC_3$ (Existing Definitions):** a policy built from the actions of `docs/policy-shapes/approve-adr.actions.json` has an empty safe subset and a rate applied of 0.0.

---

## Story 17.3 — Choosing and Replaying

**Status:** Ready — depends on Stories 15.1 and 15.3 of Epic 15.  
**As** an auditor, **I want** every decision to say whether it was a greedy pick or an exploration probe and to be replayable, **so that** a sub-optimal choice can be explained.

### Acceptance Criteria:
- **$AC_0$ (Greedy Pick):** with the rate forced to 0.0 (no safe action) `choose` returns the action with the highest mean; an action with no pulls counts as 0.5; ties go to the higher pull count, then the smaller id; the same snapshot gives the same action on 100 calls and in a fresh process.
- **$AC_1$ (Branch Coin):** the branch is exploration exactly when the first `random.Random(seed).random()` is below the rate, where the seed is `seed_for(snapshot.id, request_id, timestamp)`; the test recomputes it, and over 10,000 distinct request ids on the base policy at `t = 0` the share of exploration lies within 0.5 ± 0.02.
- **$AC_2$ (Exploration Pick):** an exploration step picks `rng.choice` of the id-sorted safe list; over 10,000 seeded decisions on the base policy no exploration picks `c`.
- **$AC_3$ (Record):** `last_decision_record()` returns the record of FDD-017 §2.3 with `request_id`, `timestamp`, `prng_seed` as a decimal string, `branch_taken`, `exploration_rate_applied`, `total_pulls`, `empirical_means` on [0, 1] (0.5 for an unpulled action) and `chosen`; every decision has `branch_taken` and a seed; the record survives `json.dumps` and `json.loads` unchanged; mutating it does not change the policy.
- **$AC_4$ (Replay):** `replay(record, snapshot)` returns the recorded `branch_taken` and `chosen` for records of both branches; for a record whose `prng_seed` was changed by one it raises `ValueError`.
- **$AC_5$ (Defaults):** `choose()` with no arguments works, supplies a request id and a timestamp, records them, and is replayable from its own record.
- **$AC_6$ (Probabilities):** `Decision.probabilities` equal the formula of FDD-017 §3 (for rate 0.2, safe subset `{a, b}` and greedy `a`: 0.9, 0.1, 0.0), sum to 1 within 1e-12, and `Decision.logprob` is `None`.
- **$AC_7$ (Not A Logit Policy):** `apply_update` raises `TypeError` containing `EpsilonGreedyLearner`, and `choose` leaves the snapshot unchanged.

---

## Story 17.4 — Statistics and the Learner

**Status:** Ready  
**As** a maintainer, **I want** the means and counts kept in the policy snapshot in the record the UCB policy also uses, **so that** no new record type is needed and the two cannot drift apart.

### Acceptance Criteria:
- **$AC_0$ (Initial):** `from_actions` gives every action `pull_count` 0, `cumulative_reward` 0.0 and `mean_reward` 0.0 in `metadata["action_statistics"]`, stores `policy_type` `"epsilon_greedy"`, the schedule, an empty `consumed_episode_ids`, and leaves `logits` at zero; `from_snapshot` rejects an invalid statistic, a duplicate id, an action outside the action space, or a `mean_reward` differing from `cumulative_reward / pull_count` by more than 1e-9.
- **$AC_1$ (Scale):** the reward value -1.0 maps to `r = 0`, 0.0 to 0.5 and +1.0 to 1; a value that is not finite or outside [-1, 1] raises `ValueError`.
- **$AC_2$ (Count):** one episode for action `a` with reward +1.0 gives `pull_count` 1, `cumulative_reward` 1.0 and `mean_reward` 1.0; with reward 0.0 it adds 1 and 0.5 and recomputes the mean; only the chosen action changes.
- **$AC_3$ (Selection):** an episode whose `selection_basis` is not `epsilon_greedy`, whose `action_id` is outside the action space, that has no aggregate reward, or whose id is already consumed is skipped and not counted; the newest aggregate reward is used.
- **$AC_4$ (Once):** offering the same episodes to `update` again, in the same call or later, leaves the statistics and `episodes_used` as after the first; two successive `run_offline_batch` runs over the same stored episodes give the statistics of one pass; an episode rewarded after newer ones were counted is counted once.
- **$AC_5$ (Shared Record):** the statistics produced by this learner and by the UCB learner of Epic 16 for the same episodes are equal, because both call the one function of `action_statistics.py`.
- **$AC_6$ (Result):** `update` advances the snapshot version and returns a `LearnerResult` with `episodes_used`, `mean_reward` of the mapped values and `consumed_inputs`; with no usable episode it changes nothing and returns 0; given a `SoftmaxPolicy` it raises `TypeError`; the snapshot survives `json.dumps` and `json.loads` and round-trips through an in-memory store with no new record type, and the modules import nothing from `agent_learning.storage`.

---

## Story 17.5 — Staying Out of REINFORCE

**Status:** Ready — depends on Story 15.3 of Epic 15.  
**As** a maintainer, **I want** epsilon-greedy episodes to be invisible to `ReinforceLearner`, **so that** a baseline pick is never trained on as a softmax sample.

### Acceptance Criteria:
- **$AC_0$ (Skipped):** an episode made through `choose` and the capture path has `action_logprob` of `None`; `ReinforceLearner.update` over only such episodes returns `episodes_used` of 0 and leaves the logits unchanged.
- **$AC_1$ (Mixed Set):** over 3 softmax episodes and 3 epsilon-greedy episodes with rewards, `ReinforceLearner` uses exactly the 3 softmax episodes, and the logits equal those from the 3 softmax episodes alone within 1e-12.
- **$AC_2$ (Guard Is Existing Behaviour):** the skip of $AC_0$ and $AC_1$ is provided by the existing check on `action_logprob is None` in `ReinforceLearner`; this epic adds no condition to `learners/reinforce.py`. The test asserts behaviour only and does not compare the module's source, so a later epic may add a condition to that file without breaking it.

---

## Story 17.6 — The Positive-Only Baseline Run

**Status:** Ready  
**As** a maintainer, **I want** the recorded positive-only history replayed through the baseline, **so that** I can see how it behaves when every reward is 1.0 and no action is flagged reversible.

### Acceptance Criteria:
- **$AC_0$ (Real Source):** the history is the `approve-*` episodes of `agent-learning-governance` read from the committed files in `docs/policy-shapes/episodes/`, each replayed as `r = 1.0` for the action taken; the count and the file names are recorded in the test (41 when ADR-017 was written, 58 files on 2026-10-29, so the test records the count it ran on and does not assert a fixed number).
- **$AC_1$ (Locks In):** with the existing action definitions, which carry no `reversible` flag, the rate applied is 0.0 throughout, every decision is exploitation, and the policy keeps choosing the action with the best mean; an untaken action stays at 0.5 and is not chosen while a taken action has a mean above 0.5. The test names this as the stated price of the safety mask (BRU-017-03).
- **$AC_2$ (Repeatable):** the replay run twice gives identical statistics, decisions and records.
- **$AC_3$ (Labelled):** the result is recorded as a baseline run on a real positive-only history. It makes no claim that this policy decides better or worse than REINFORCE, UCB or Thompson sampling (BRU-017-13), and the missing data (a low-authority policy with failures, and a declared `reversible` flag) is named in the test's docstring.
