# Epic 16: Deterministic Upper Confidence Bound (UCB) Decision Policy

**Source ADR:** [ADR-016](../adr/ADR-016-deterministic-ucb-decision-policy.md) — Accepted (2026-10-28)  
**Source BRD/FDD:** [BRD-016](../project-docs/Business-Requirements/BRD-016-deterministic-ucb-decision-policy.md) / [FDD-016](../project-docs/Functional-Design/FDD-016-deterministic-ucb-decision-policy.md)  
**Status:** Approved (2026-10-29, Menno) — stories derived from Accepted ADR-016, BRD-016 and FDD-016; adjudicated via `approve-user-stories` (robust utility 0.739, episode `3d00424a-a01d-4bca-8623-a5953d3347d5`). The epic number follows the source ADR number, as Epic 15 follows ADR-015.  

Six stories build `src/agent_learning/policy/ucb.py` and `src/agent_learning/learners/ucb.py`. Each rule sits in exactly one story's criteria (LL-012). Contract tests are `tests/test_ucb_scores.py` (16.1), `tests/test_ucb_policy.py` (16.2 and 16.3), `tests/test_ucb_learner.py` (16.4), `tests/test_ucb_reinforce_guard.py` (16.5) and `tests/test_ucb_positive_only.py` (16.6). A study of decision quality against REINFORCE or Thompson sampling is a data gap, not a story (BRD-016 Out of Scope).

**Stories 16.1 to 16.6 are unblocked except for one dependency:** Menno confirmed FDD-016 §4 (E1 to E6) on 2026-10-29. Stories 16.2 and 16.5 depend on Story 15.3 of Epic 15, which makes `Decision.logprob` optional; 16.1, 16.3, 16.4 and 16.6 do not.

Fixture used by the criteria below ("the base statistics"): action `a` with 10 pulls and cumulative reward 8.0, action `b` with 5 pulls and cumulative reward 3.0, total 15.

---

## Story 16.1 — The Scores

**Status:** Ready  
**As** an auditor, **I want** each action's bound computed by a pure function of its counts, **so that** a choice can be checked by hand.

### Acceptance Criteria:
- **$AC_0$ (Standard):** on the base statistics with `variant="standard"` and the default `c`, the scores are 1.8408 for `a` and 2.0719 for `b` within 1e-4, and the test recomputes them from the UCB1 formula itself.
- **$AC_1$ (Wilson):** with `variant="wilson"`, an action with 10 pulls and cumulative reward 10.0 scores 1.0 and one with 10 pulls and 0.0 scores 0.2775 within 1e-4; the scores on the base statistics match the closed form of ADR-016 §4.1 within 1e-9.
- **$AC_2$ (Unexplored):** an action with no pulls scores `math.inf` in both variants, and in the `standard` variant `total == 1` gives a bonus of 0.
- **$AC_3$ (Reuse):** over a grid of `N` from 1 to 50 and `k` from 0 to `N` in steps of 0.5, `1 - wilson_lower_bound(N - k, N)` equals the `wilson` score within 1e-12, and `wilson_lower_bound` returns the same values as before for integer arguments.
- **$AC_4$ (Validation):** `ValueError` for an unknown variant, `c <= 0`, a `total` that is not the sum of the pull counts, a negative or non-integer pull count, and a cumulative reward outside `[0, pull_count]` or not finite.
- **$AC_5$ (No RNG):** a static check finds no import of `random` and no call into it in `policy/ucb.py` and `learners/ucb.py`.

---

## Story 16.2 — Choosing Deterministically

**Status:** Ready — depends on Story 15.3 (`Decision.logprob` optional).  
**As** an auditor, **I want** the same snapshot to give the same action every time, **so that** a replayed decision is identical.

### Acceptance Criteria:
- **$AC_0$ (Argmax):** on the base statistics `choose` returns the action with the highest score of Story 16.1.
- **$AC_1$ (Repeatable):** 100 calls on one snapshot, and one call in a fresh process on the same snapshot, return the same action.
- **$AC_2$ (Tie-Break):** two actions with equal scores resolve to the one with the higher pull count; if the pull counts are also equal, to the lexicographically smaller `action.id`.
- **$AC_3$ (Round-Robin):** with three actions and no pulls, `choose` returns the smallest id; after that action is given one pull, the next smallest; after all three have one pull, no action scores `inf`.
- **$AC_4$ (No Log-Probability):** the returned `Decision` has `logprob` of `None` and one-hot `probabilities` on the chosen action.
- **$AC_5$ (Record):** `last_decision_record()` returns the record of FDD-016 §2.3, with `null` for an infinite score; it survives `json.dumps` and `json.loads` unchanged, and mutating it does not change the policy.
- **$AC_6$ (Not A Logit Policy):** `apply_update` raises `TypeError` containing `UCBLearner`, and `choose` leaves the snapshot unchanged.

---

## Story 16.3 — Statistics in the Snapshot

**Status:** Ready  
**As** a maintainer, **I want** the statistics kept in the policy snapshot, **so that** no new record type is needed.

### Acceptance Criteria:
- **$AC_0$ (Initial):** `UCBPolicy.from_actions` gives every action `pull_count` 0, `cumulative_reward` 0.0 and `mean_reward` 0.0 in `metadata["action_statistics"]`, stores `policy_type` `"ucb"`, the variant and the exploration constant, an empty `consumed_episode_ids`, and leaves `logits` at zero.
- **$AC_1$ (Read):** `from_snapshot` reads the example of FDD-016 §2.2, including `mean_reward` and `consumed_episode_ids`; an action missing from the statistics reads as zero pulls.
- **$AC_2$ (Validation):** an action id outside the action space, an invalid statistic, an unknown variant, a duplicate id in `consumed_episode_ids`, or a `mean_reward` that differs from `cumulative_reward / pull_count` by more than 1e-9 in a snapshot raises `ValueError` naming it.
- **$AC_3$ (Storage Boundary):** a snapshot survives `json.dumps` and `json.loads` unchanged and round-trips through an in-memory store with no new record type; `ucb.py` imports nothing from `agent_learning.storage`.

---

## Story 16.4 — Counting Each Episode Once

**Status:** Ready  
**As** a maintainer, **I want** each reward to add to the statistics exactly once, **so that** retraining on recent episodes cannot inflate a count.

### Acceptance Criteria:
- **$AC_0$ (Scale):** the reward value -1.0 maps to `r = 0`, 0.0 to 0.5 and +1.0 to 1; a value that is not finite or lies outside [-1, 1] raises `ValueError`.
- **$AC_1$ (Count):** one episode for action `a` with reward +1.0 gives `pull_count` 1, `cumulative_reward` 1.0 and `mean_reward` 1.0; with reward 0.0 it adds 1 and 0.5 and the mean is recomputed; only the chosen action changes.
- **$AC_2$ (Selection):** an episode whose `selection_basis` is not `ucb`, whose `action_id` is outside the action space, or that has no aggregate reward is skipped and not counted; when several aggregate rewards exist for an episode, the newest is used.
- **$AC_3$ (Once):** offering the same episodes to `update` a second time, in the same call or in a later one, leaves the statistics and `episodes_used` as after the first; each counted id appears once in `consumed_episode_ids`, and an episode whose id is already there is skipped.
- **$AC_4$ (Through The Runner):** two successive `run_offline_batch` runs over the same stored episodes give the statistics of one pass.
- **$AC_5$ (Late Reward):** an episode created before newer, already counted episodes, whose reward is recorded afterwards, is counted when it is first offered with its reward, and once only.
- **$AC_6$ (Result):** `update` advances the snapshot version and returns a `LearnerResult` with `episodes_used`, `mean_reward` of the mapped values and `consumed_inputs`; a call with no usable episode changes nothing and returns `episodes_used` of 0; given a `SoftmaxPolicy` it raises `TypeError`.

---

## Story 16.5 — Staying Out of REINFORCE

**Status:** Ready — depends on Story 15.3 (`Decision.logprob` optional).  
**As** a maintainer, **I want** UCB episodes to be invisible to `ReinforceLearner`, **so that** a deterministic pick is never trained on as a softmax sample.

### Acceptance Criteria:
- **$AC_0$ (Skipped):** a UCB episode made through `choose` and the capture path has `action_logprob` of `None`; `ReinforceLearner.update` over only such episodes returns `episodes_used` of 0 and leaves the logits unchanged.
- **$AC_1$ (Mixed Set):** over 3 softmax episodes and 3 UCB episodes with rewards, `ReinforceLearner` uses exactly the 3 softmax episodes, and the logits equal those from the 3 softmax episodes alone within 1e-12.
- **$AC_2$ (No Change To REINFORCE):** `learners/reinforce.py` is unchanged by this epic; the test fails if the module's source differs from the one recorded when the story starts.

---

## Story 16.6 — The Positive-Only Check (HYP-AL-009)

**Status:** Ready  
**As** a maintainer, **I want** the recorded positive-only history replayed through the policy, **so that** I can see how a deterministic bound behaves when every reward is 1.0.

### Acceptance Criteria:
- **$AC_0$ (Real Source):** the history is the `approve-*` episodes of `agent-learning-governance` read from the committed files in `docs/policy-shapes/episodes/`, each replayed as `r = 1.0` for the action taken; the count and the file names are recorded in the test (41 when ADR-016 was written, 58 files on 2026-10-29, so the test records the count it ran on and does not assert a fixed number).
- **$AC_1$ (Keeps Exploring):** after the replay, every untaken action still scores `inf` and is chosen before any taken action; the taken action's `wilson` score is 1.0 and its `wilson` lower bound rises with the count, matching `wilson_lower_bound` (ADR-003).
- **$AC_2$ (Repeatable):** the replay run twice gives identical statistics and identical choices.
- **$AC_3$ (Labelled):** the result is recorded as a consistency check on a real positive-only history. It makes no claim that UCB decides better; that needs a low-authority policy with failures (BRU-016-11), and the missing data is named in the test's docstring.
