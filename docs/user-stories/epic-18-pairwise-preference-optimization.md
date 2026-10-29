# Epic 18: Pairwise Preference Optimization for Discrete Action Logits

**Source ADR:** [ADR-018](../adr/ADR-018-pairwise-preference-optimization.md) — Accepted (2026-10-28)  
**Source BRD/FDD:** [BRD-018](../project-docs/Business-Requirements/BRD-018-pairwise-preference-optimization.md) / [FDD-018](../project-docs/Functional-Design/FDD-018-pairwise-preference-optimization.md)  
**Status:** Approved (2026-10-29, Menno) — stories derived from Accepted ADR-018, BRD-018 and FDD-018; adjudicated via `approve-user-stories` (robust utility 0.735, episode `42460cf3-2d31-4aaa-911e-e6d3ac2c1467`). The epic number follows the source ADR number, as Epic 17 follows ADR-017.  

Six stories build `src/agent_learning/learners/pairwise.py`. Each rule sits in exactly one story's criteria (LL-012). Contract tests are `tests/test_pairwise_pairs.py` (18.1), `tests/test_pairwise_loss.py` (18.2), `tests/test_pairwise_fit.py` (18.3), `tests/test_pairwise_learner.py` (18.4), `tests/test_pairwise_runner.py` (18.5) and `tests/test_pairwise_real_data.py` (18.6). Showing that the learner improves decisions is a data gap, not a story (BRD-018 Out of Scope). The audit replay of this learner's runs is not a story (FDD-018 §7 item 2).

**Stories 18.1 to 18.6 are unblocked:** Menno confirmed FDD-018 §4 (G1 to G7) on 2026-10-29 and ADR-018 was amended to match. No story depends on another epic.

Fixture used by the criteria below ("the base set"): three actions `x`, `y` and `z`; `theta_ref` of zeros; `lambda = 0.05`. The pair sets are built in the tests and labelled synthetic.

---

## Story 18.1 — Pairs From Episodes

**Status:** Ready  
**As** a maintainer, **I want** a preference pair read from each episode in which a reviewer chose a different action, **so that** no label is written by hand and no preference becomes a reward.

### Acceptance Criteria:
- **$AC_0$ (Override):** an episode with `feedback_status` `"rejected"`, an `action_id` of `y` and a `correct_action_id` of `x` gives the pair (winner `x`, loser `y`) with its episode id; `" Rejected "` is read the same way.
- **$AC_1$ (No Pair):** an `accepted` episode, a `rejected` one with no `correct_action_id`, one whose `correct_action_id` equals `action_id`, one whose `correct_action_id` or `action_id` is outside `action_ids`, and one whose `correct_action_id` is not a string each give no pair and no error.
- **$AC_2$ (Not The ADR Field):** an episode with `decision_disposition` `"modify"` but no `feedback_status` of `rejected` gives no pair (the field ADR-018 names is not read; FDD-018 G3).
- **$AC_3$ (Once):** the same episode id offered twice gives one pair; the order of the pairs is the order of first appearance.
- **$AC_4$ (Inputs Untouched):** the episodes are equal to their deep copies after the call.

---

## Story 18.2 — The Loss and Its Gradient

**Status:** Ready  
**As** an auditor, **I want** the Bradley-Terry loss and its gradient written as plain arithmetic, **so that** a logit update can be checked by hand.

### Acceptance Criteria:
- **$AC_0$ (Loss):** on the base set with pairs `x > y` ×2 and `y > z` ×1 and `theta = (0.3, -0.2, 0.1)`, the loss equals the term-by-term sum of `log(1 + exp(-(theta_w - theta_l)))` plus `(lambda / 2) * ||theta - theta_ref||^2`, computed in the test, within 1e-12.
- **$AC_1$ (Gradient):** the analytic gradient equals a central finite difference of the loss within 1e-6 on at least five random `theta` and pair sets.
- **$AC_2$ (Aggregated):** the matrix form of FDD-018 §2.4 equals the sum over individual pairs within 1e-12, including a pair set with repeated pairs.
- **$AC_3$ (Single Pair):** for one pair `x > y`, `theta_ref = 0` and `lambda = 0.05`, the gradient at `theta = (0, 0)` is `(-0.5, +0.5, 0)` and at `theta = (1.3235, -1.3235, 0)` is zero within 1e-3.

---

## Story 18.3 — The Fit

**Status:** Ready  
**As** a maintainer, **I want** the fit to converge safely or say that it did not, **so that** a result is never taken for an optimum it is not.

### Acceptance Criteria:
- **$AC_0$ (Validation):** `lam` of 0.049 raises `ValueError`, and 0.05 is accepted; a non-finite argument, `lr <= 0`, `steps < 1`, `clamp <= 0`, an action missing from `theta_ref`, and a pair naming an unknown action each raise `ValueError` naming the argument.
- **$AC_1$ (No Pairs):** with no pair the returned logits equal `theta_ref` exactly and `converged` is true.
- **$AC_2$ (Clamp):** every returned logit lies in [-8.0, +8.0], including for a pair set that pushes a logit past 8 and for a `theta_ref` outside the box.
- **$AC_3$ (Step Size):** `step_size` equals `min(lr, 1 / (lam + 0.5 * max_degree))`, with `max_degree` the largest number of pairs that name one action; on the base set with 18 pairs it is 0.1, and with 3,000 pairs it is below 0.1.
- **$AC_4$ (Monotone):** over the iterations the regularised loss never increases for pair sets of 18, 100, 1,000 and 3,000 pairs; the test uses the loss of Story 18.2 and fails if a step raises it by more than 1e-12.
- **$AC_5$ (Order):** on a consistent set of 3,000 pairs (`x > y` 1,500, `x > z` 900, `y > z` 600) the returned logits keep `x > y > z`.
- **$AC_6$ (Honest Convergence):** a fit stopped by the cap has `converged` false and a `stationarity` above `tol`; a fit that stops early has `converged` true and `stationarity` below `tol`; `iterations` equals the number of steps taken.
- **$AC_7$ (Deterministic):** the same arguments give identical logits on repeated calls and in a fresh process, and `fit_logits` imports no random module.
- **$AC_8$ (Time):** the test records the time of a 2,000-step fit on three actions with 1,000 pairs and fails only if it exceeds 5 seconds; the recorded value is not claimed as a benchmark.

---

## Story 18.4 — The Learner

**Status:** Ready  
**As** a maintainer, **I want** the learner to move a `SoftmaxPolicy`'s logits to the fit, anchored to a reference, **so that** a few overrides cannot drag the policy far from where it started.

### Acceptance Criteria:
- **$AC_0$ (Type):** `update` given a policy that is not a `SoftmaxPolicy` raises `TypeError`; given a `SoftmaxPolicy` with `max_logit_abs` below 8.0 raises `ValueError`.
- **$AC_1$ (Reference Frozen):** the first update with a pair writes the policy's logits to `metadata["pairwise_reference_logits"]`; a second update, after the logits changed, leaves the stored reference unchanged; a stored reference with a missing action or a non-finite value raises `ValueError`.
- **$AC_2$ (Moves To The Fit):** after an update with the pairs of the base set the policy's logits equal the `fit_logits` result from `theta_ref` within 1e-12, and the `logit_deltas` of the result equal `fitted - before`.
- **$AC_3$ (No Pair, No Change):** with episodes that give no pair, no reference is written, the logits and the snapshot version are unchanged, and `episodes_used` is 0.
- **$AC_4$ (Idempotent):** running `update` a second time on the same episodes leaves the logits unchanged and `episodes_seen` unchanged.
- **$AC_5$ (Result):** the `LearnerResult` has `episodes_used` equal to the number of pairs, `mean_reward` 0.0, `baseline_after` equal to `baseline_before`, `consumed_inputs` of `None`, and in `extra` the keys `pairs`, `skipped_episodes`, `converged`, `iterations`, `stationarity`, `step_size`, `loss_before`, `loss_after` and `reference_logits`; the rewards argument is ignored even when it holds invalid values.
- **$AC_6$ (Storage Boundary):** the snapshot survives `json.dumps` and `json.loads` unchanged and round-trips through an in-memory store with no new record type; `pairwise.py` imports nothing from `agent_learning.storage`.

---

## Story 18.5 — Through the Runner

**Status:** Ready  
**As** an adopter, **I want** to train a policy with this learner through the training runner, **so that** it needs no special entry point.

### Acceptance Criteria:
- **$AC_0$ (Runs):** `TrainingRunner(learner=PairwiseLearner())` over a store that holds override episodes completes `run_offline_batch` with a `SUCCEEDED` run whose `algorithm` is `PairwiseLearner`.
- **$AC_1$ (Twice):** two successive `run_offline_batch` runs over the same stored episodes leave the logits as after the first.
- **$AC_2$ (Episodes Untouched):** the stored episodes are equal to their earlier copies after the run.
- **$AC_3$ (Audit Replay):** the audit replay of such a run reports insufficient lineage and does not raise; the test asserts this and its docstring names FDD-018 §7 item 2.

---

## Story 18.6 — The Real-Data Check (Zero Pairs)

**Status:** Ready  
**As** a maintainer, **I want** the learner run on the recorded history, **so that** the missing real data is shown, not assumed.

### Acceptance Criteria:
- **$AC_0$ (Real Source):** the episodes are the `approve-*` episodes of `agent-learning-governance` read from the committed files in `docs/policy-shapes/episodes/`; the count and the file names are recorded in the test (41 when ADR-018 was written, 76 files on 2026-10-29, so the test records the count it ran on and does not assert a fixed number).
- **$AC_1$ (Zero Pairs):** `pairs_from_episodes` over them returns no pair, because none carries a `rejected` feedback status with a different `correct_action_id`.
- **$AC_2$ (Logits Stay):** the learner run over them leaves a `SoftmaxPolicy`'s logits unchanged, writes no reference, and returns `episodes_used` of 0.
- **$AC_3$ (Labelled):** the result is recorded as a statement that real preference data does not exist yet. It makes no claim about the learner's quality (BRU-018-12), and the docstring names the missing data (real override adjudications) and the unbuilt Red Team pair set.
