# Epic 15: Bayesian Bandit Posterior Sampling (Thompson Sampling)

**Source ADR:** [ADR-015](../adr/ADR-015-bayesian-bandit-posterior-sampling.md) — Accepted (2026-10-28)  
**Source BRD/FDD:** [BRD-015](../project-docs/Business-Requirements/BRD-015-bayesian-bandit-posterior-sampling.md) / [FDD-015](../project-docs/Functional-Design/FDD-015-bayesian-bandit-posterior-sampling.md)  
**Status:** Approved (2026-10-29, Menno); amended 2026-10-29 with the counted-once criteria (FDD-015 D7), re-approval under `approve-user-stories` pending — stories derived from Accepted ADR-015, BRD-015 and FDD-015; adjudicated via `approve-user-stories` (robust utility 0.739, episode `8447f932-4002-43f5-9410-be732b8d5474`). The epic number follows the source ADR number, as Epic 14 follows ADR-014.  

Six stories build `src/agent_learning/policy/thompson.py` and `src/agent_learning/learners/thompson.py`. Each rule sits in exactly one story's criteria (LL-012). Contract tests are `tests/test_thompson_seed.py` (15.1), `tests/test_thompson_policy.py` (15.2 and 15.3), `tests/test_thompson_learner.py` (15.4), `tests/test_thompson_reinforce_guard.py` (15.5) and `tests/test_thompson_positive_only.py` (15.6). A study of decision quality against REINFORCE is a data gap, not a story (BRD-015 Out of Scope).

**Stories 15.1 to 15.6 are unblocked.** Menno confirmed FDD-015 §4 (D1 to D6) on 2026-10-29 and ADR-015 was amended to match.

Fixture used by the criteria below ("the base policy"): two actions, `a` and `b`, both at the prior Beta(1, 1), in a snapshot with id `policy-1`.

---

## Story 15.1 — The Seed and the Replay

**Status:** Ready  
**As** an auditor, **I want** every random draw to be re-derivable from the request that caused it, **so that** a stochastic decision can still be checked after the fact.

### Acceptance Criteria:
- **$AC_0$ (Seed):** `seed_for(policy_id, request_id, timestamp)` equals `int(HMAC-SHA256(key=policy_id, msg=request_id + "|" + timestamp).hexdigest()[:16], 16)`, computed in the test with `hmac` directly, and is below 2**64.
- **$AC_1$ (Deterministic):** the same three arguments give the same seed; changing any one gives a different seed for the test's three variations; `("ab", "c")` and `("a", "bc")` for `(request_id, timestamp)` give different seeds.
- **$AC_2$ (Refuses Empty):** an empty `policy_id`, `request_id` or `timestamp` raises `ValueError` naming the argument.
- **$AC_3$ (Replay):** `replay(record)` on a record made by `choose` returns the recorded `sampled_payoffs` exactly; on a record whose `prng_seed` was changed by one it raises `ValueError`.

---

## Story 15.2 — Posterior State in the Snapshot

**Status:** Ready  
**As** a maintainer, **I want** the posterior kept in the policy snapshot, **so that** no new record type is needed.

### Acceptance Criteria:
- **$AC_0$ (Prior):** `ThompsonPolicy.from_actions` gives every action `alpha = 1.0` and `beta = 1.0` in `snapshot.metadata["posterior_parameters"]`, keyed by action id, with `logits` left at zero.
- **$AC_1$ (Read):** `from_snapshot` reads a snapshot with `alpha {a: 14, b: 3}` and `beta {a: 2, b: 8}` and exposes those values; an action missing from the mapping reads as the prior.
- **$AC_2$ (Validation):** a non-finite or non-positive value, or an action id outside the action space, raises `ValueError` naming the action.
- **$AC_3$ (Consumed Ids):** a snapshot with `consumed_episode_ids` survives `json.dumps` and `json.loads` unchanged; one with a duplicate id raises `ValueError` naming it; `from_actions` starts with an empty list.
- **$AC_4$ (Storage Boundary):** a snapshot with a posterior survives `json.dumps` and `json.loads` unchanged and round-trips through an in-memory store with no new record type; `thompson.py` imports nothing from `agent_learning.storage` and performs no file I/O.

---

## Story 15.3 — Choosing by Probability Matching

**Status:** Ready  
**As** an adopter, **I want** the policy to pick the action with the highest posterior draw, **so that** an action with few observations is still tried.

### Acceptance Criteria:
- **$AC_0$ (Argmax):** `choose` draws one `betavariate` per action from `random.Random(seed)` in snapshot order, using the seed of `seed_for(snapshot.id, request_id, timestamp)`, and returns the action with the highest draw; the test recomputes the draws itself. A tie goes to the earlier action.
- **$AC_1$ (Record):** `last_sampling_record()` returns the record of FDD-015 §2.3 with `request_id`, `timestamp`, `prng_seed` as a decimal string, the posterior used and `sampled_payoffs` for every action; mutating the returned value does not change the policy's next record.
- **$AC_2$ (Defaults):** `choose()` with no arguments works, supplies a request id and a timestamp, and records them; two such calls are replayable from their own records.
- **$AC_3$ (No Log-Probability):** the returned `Decision` has `logprob` of `None`, and `Decision.logprob` is typed `Optional[float]`.
- **$AC_4$ (Exploration):** on the base policy with posteriors a: Beta(2, 1) and b: Beta(1, 1) over 2000 draws with distinct request ids, `b` is chosen at least once and `a` more often than `b`.
- **$AC_5$ (Not A Logit Policy):** `apply_update` raises `TypeError` containing `ThompsonLearner`.

---

## Story 15.4 — The Conjugate Update and the Ceiling

**Status:** Ready  
**As** a maintainer, **I want** each reward to move the chosen action's posterior by the Beta-Bernoulli rule, **so that** uncertainty shrinks only as evidence arrives.

### Acceptance Criteria:
- **$AC_0$ (Scale):** the reward value -1.0 maps to `r = 0`, 0.0 to 0.5 and +1.0 to 1; a value that is not finite or lies outside [-1, 1] raises `ValueError`.
- **$AC_1$ (Update):** from Beta(1, 1), `r = 1.0` gives (2, 1), and from Beta(14, 2), `r = 0.5` gives (14.5, 2.5), each to 1e-12; only the chosen action changes.
- **$AC_2$ (Ceiling):** from (4000, 1500), one reward `r = 1.0` ends at a total of 5000 within 1e-9 and keeps the ratio `alpha : beta` of (4001, 1500) within 1e-9; a total at or below 5000 is untouched.
- **$AC_3$ (Selection):** an episode whose `selection_basis` is not `thompson_sampling`, whose `action_id` is outside the action space, that has no aggregate reward, or whose id is already in `consumed_episode_ids` is skipped and not counted; when several aggregate rewards exist for an episode, the newest is used.
- **$AC_4$ (Result):** `update` advances the snapshot version, sets `episodes_seen` and `updates_applied`, and returns a `LearnerResult` with `episodes_used`, `mean_reward` of the mapped values and `consumed_inputs`; a call with no usable episode changes nothing and returns `episodes_used` of 0.
- **$AC_5$ (Type):** `update` given a `SoftmaxPolicy` raises `TypeError`.
- **$AC_6$ (Once):** offering the same episodes to `update` a second time, in the same call or in a later one, leaves the posteriors and `episodes_used` as after the first; each counted id appears once in `consumed_episode_ids`.
- **$AC_7$ (Through The Runner):** two successive `run_offline_batch` runs over the same stored episodes give the posteriors of one pass.
- **$AC_8$ (Late Reward):** an episode created before newer, already counted episodes, whose reward is recorded afterwards, is counted when it is first offered with its reward, and once only.

---

## Story 15.5 — Staying Out of REINFORCE

**Status:** Ready  
**As** a maintainer, **I want** Thompson episodes to be invisible to `ReinforceLearner`, **so that** a draw is never trained on as if it were a softmax sample.

### Acceptance Criteria:
- **$AC_0$ (Skipped):** a Thompson episode made through `choose` and the capture path has `action_logprob` of `None`; `ReinforceLearner.update` over a set of only such episodes returns `episodes_used` of 0 and leaves the logits unchanged.
- **$AC_1$ (Mixed Set):** over a set of 3 softmax episodes and 3 Thompson episodes with rewards, `ReinforceLearner` uses exactly the 3 softmax episodes, and the logits equal those from the 3 softmax episodes alone within 1e-12.
- **$AC_2$ (No Change To REINFORCE):** `learners/reinforce.py` is unchanged by this epic (FDD-015 D6); the test fails if the module's source differs from the one recorded when the story starts.

---

## Story 15.6 — The Positive-Only Check (HYP-AL-002)

**Status:** Ready  
**As** a maintainer, **I want** the recorded positive-only history replayed through both learners, **so that** I can see whether Thompson sampling keeps learning where REINFORCE stalls.

### Acceptance Criteria:
- **$AC_0$ (Real Source):** the history is the `approve-*` episodes of `agent-learning-governance` read from the committed files in `docs/policy-shapes/episodes/`, each replayed as `r = 1.0` for the action taken; the count and the file names are recorded in the test (41 when ADR-015 was written, 58 files on 2026-10-29, so the test records the count it ran on and does not assert a fixed number).
- **$AC_1$ (REINFORCE Stalls):** these episodes are full authority and carry no log-probability, which `ReinforceLearner` skips (Story 15.5), so the replay assigns each episode the log-probability a `SoftmaxPolicy` over the same actions gives its action, and states that it did. Over the all-ones history the baseline approaches 1.0 and the REINFORCE logit change on the final batch is below 1e-3 in absolute value.
- **$AC_2$ (Thompson Keeps Width):** over the same history the posterior of the action taken has a standard deviation above 0 and every untaken action keeps its prior Beta(1, 1).
- **$AC_3$ (Labelled):** the result is recorded as a consistency check on a real positive-only history. It makes no claim that Thompson sampling decides better; that needs a low-authority policy with failures (BRD-015 BRU-015-10), and the missing data is named in the test's docstring.
