# FDD-018: Pairwise Preference Optimization for Discrete Action Logits

**Source ADR:** [ADR-018](../../adr/ADR-018-pairwise-preference-optimization.md) — Accepted (2026-10-28)  
**Source BRD:** [BRD-018](../Business-Requirements/BRD-018-pairwise-preference-optimization.md)  
**Status:** Approved (2026-10-29, Menno) — derived from Accepted ADR-018 and BRD-018; adjudicated via `approve-fdd` (robust utility 0.726, episode `4c3037cb-336b-4811-8cf9-f6917cce00bd`). Section 4 lists where this design departs from ADR-018 §4.2 to §4.4. Menno confirmed the departures G1 to G7 on 2026-10-29 (G1 keeping the 2,000-step cap, G3 as `feedback_status`, G5 accepted with its forgetting disclosed) and ADR-018 §4.2, §4.3, §4.4 and §6 were amended to match.  

---

## 1. Architecture & Component Placement

1. **New module** `src/agent_learning/learners/pairwise.py` holding `PreferencePair`, `FitResult`, `pairs_from_episodes`, `fit_logits` and `PairwiseLearner(Learner)`. It uses `numpy` (already a dependency of `SoftmaxPolicy`) and the standard library, reads `Episode` and `PolicySnapshot` from `agent_learning.types` and `SoftmaxPolicy` from `agent_learning.policy`. It imports nothing from `agent_learning.storage`, uses no random number and does no file I/O.
2. **Package export:** `PairwiseLearner`, `PreferencePair`, `FitResult`, `pairs_from_episodes` and `fit_logits` are re-exported from `agent_learning/__init__.py` and from the `learners` package.
3. **The policy is the existing `SoftmaxPolicy`.** No new policy class: this learner changes only its logits, through `SoftmaxPolicy.apply_update`.
4. **State in the snapshot** (BRU-018-09): `PolicySnapshot.metadata["pairwise_reference_logits"]` holds `theta_ref` (G4). Nothing else is stored; pairs are derived from episodes at training time.
5. **Shared types are unchanged.**

---

## 2. Data Contract

### 2.1 Constants
| Name | Value | Meaning |
|---|---|---|
| `LAMBDA_MIN` | 0.05 | the lowest allowed regularisation weight (ADR-018 Invariant 3) |
| `CLAMP` | 8.0 | the logit box [-8, +8] (ADR-018 Invariant 5) |
| `LR_DEFAULT` | 0.1 | the largest step the fit may take (G1) |
| `STEPS_DEFAULT` | 2000 | the iteration cap |
| `TOL_DEFAULT` | 1e-8 | the stationarity tolerance (G1) |

### 2.2 Dataclasses
```python
@dataclass(frozen=True)
class PreferencePair:
    winner: str
    loser: str
    source_episode_id: str

@dataclass(frozen=True)
class FitResult:
    logits: dict[str, float]    # one per action id, inside [-clamp, +clamp]
    converged: bool             # True when the stationarity measure fell below tol before the cap
    iterations: int
    stationarity: float         # the measure at the last iterate
    step_size: float            # the step actually used
    loss: float                 # the regularised loss at the returned logits
```

### 2.3 Reference logits
`metadata["pairwise_reference_logits"]` is a mapping from action id to a finite float, written once on the first update that has at least one pair and never overwritten (G4). It equals the policy's logits at that moment.

### 2.4 The loss and its gradient
With `W[w][l]` the number of pairs that prefer `w` to `l`:

`loss(theta) = sum over (w, l) of W[w][l] * log(1 + exp(-(theta_w - theta_l))) + (lambda / 2) * sum over a of (theta_a - theta_ref_a)^2`

`grad_a = -sum over l of W[a][l] * s(a, l) + sum over w of W[w][a] * s(w, a) + lambda * (theta_a - theta_ref_a)`, with `s(w, l) = 1 / (1 + exp(theta_w - theta_l))`, which is ADR-018 §4.2. The matrix form makes one iteration cost `O(|A|^2)` whatever the number of pairs (G1).

---

## 3. Behavior

1. **`pairs_from_episodes(episodes, action_ids) -> list[PreferencePair]`.** An episode gives a pair when all of these hold (G3): its `metadata["feedback_status"]`, stripped and lowercased, is `"rejected"`; `metadata["correct_action_id"]` is a string in `action_ids`; `action_id` is in `action_ids`; and the two differ. The winner is `correct_action_id`, the loser is `action_id`. An accepted episode, an episode with no `correct_action_id`, or one whose ids are outside `action_ids` gives no pair. An episode id seen twice gives one pair (G5). The order is that of first appearance. The episodes are not changed (BRU-018-11).
2. **`fit_logits(pairs, action_ids, theta_ref, *, lam=0.05, lr=0.1, steps=2000, clamp=8.0, tol=1e-8) -> FitResult`.** It raises `ValueError` for `lam < LAMBDA_MIN`, a non-finite argument, `lr <= 0`, `steps < 1`, `clamp <= 0`, an action id missing from `theta_ref`, or a pair naming an action outside `action_ids`. Then:
   1. Build `W` from the pairs (duplicates by `source_episode_id` counted once).
   2. `max_degree` is the largest, over actions, of the number of pairs that name the action. The step is `min(lr, 1 / (lam + 0.5 * max_degree))` (G1), which is below the inverse of the largest curvature of the loss, so the loss does not rise.
   3. Start at `theta_ref` clipped to the box. Repeat up to `steps` times: take a gradient step, then clip to the box (projected gradient descent, ADR-018 §4.2). Stop early when the stationarity measure `max_a |theta_a - clip(theta_a - step * grad_a)| / step` is below `tol`.
   4. Return the `FitResult`. With no pair the gradient at the start is the regulariser alone, which is zero at `theta_ref`, so the logits equal `theta_ref` (BRU-018-06).
3. **`PairwiseLearner.update(policy, episodes, rewards) -> LearnerResult`.** It requires a `SoftmaxPolicy` (`TypeError` otherwise) whose `max_logit_abs` is at least `CLAMP` (`ValueError` otherwise, G6). The `rewards` argument is not used: preferences are not rewards (BRU-018-01).
   1. The pairs come from `pairs_from_episodes` with the policy's action ids.
   2. With no pair, nothing changes: no reference is written, the snapshot version does not advance, and the result has `episodes_used` of 0.
   3. Otherwise `theta_ref` is read from the snapshot, or written from the current logits if absent (G4), and `fit_logits` runs from `theta_ref` over all pairs offered, not from the current logits (G5).
   4. The deltas are `fitted - current` for each action, applied with `policy.apply_update(deltas, baseline=snapshot.baseline, episodes_seen=snapshot.episodes_seen)`. `episodes_seen` is left unchanged because the fit is a refit over the pairs supplied, not an accumulation; `updates_applied` and the version advance as usual.
   5. The `LearnerResult` has `episodes_used` equal to the number of pairs, `mean_reward` 0.0, the baseline unchanged, the `logit_deltas`, `consumed_inputs` of `None` (G7), and in `extra`: `pairs`, `skipped_episodes`, `converged`, `iterations`, `stationarity`, `step_size`, `loss_before`, `loss_after` and `reference_logits`.
4. **Running again on the same episodes** gives the same pairs, the same `theta_ref` and so the same fit; the deltas are zero (BRU-018-07).

**Worked checks (arithmetic, to be re-run when built).** One pair `x > y`, `lambda = 0.05`, `theta_ref = 0`: at `theta = (0, 0)` the gradient is `(-0.5, +0.5)`. The stationary point is `theta_x = -theta_y = t` with `0.05 * t = 1 / (1 + exp(2t))`, which gives `t = 1.3235`. A pair set of 3,000 pairs with preferences `x > y` (1,500), `x > z` (900), `y > z` (600) keeps the order `theta_x > theta_y > theta_z` at the returned logits.

**Measured on 2026-10-29 with a throwaway prototype of ADR-018 §4.2 (not committed).** With three actions and the ADR's step of 0.1 and 2,000 steps, the loss never rose for 18, 40, 100 and 1,000 pairs, but for 3,000 pairs it rose on 1,000 iterations and ended at 1074.8 with the logits (7.96, 8.0, -8.0), the wrong order. With the step `1 / (lam + 0.5 * max_degree)` the loss never rose, but at 3,000 pairs 2,000 steps had not converged (loss 4.255 against 3.823 after 20,000 steps), which is why the result reports `converged` (G1). The 2,000 steps took about 50 ms with the matrix form, including a loss trace.

---

## 4. Departures from ADR-018 §4.2 to §4.4

Each is a place where ADR-018, as first accepted, did not fit the code that exists today or failed when run. Menno confirmed all seven on 2026-10-29 and ADR-018 was amended; the "ADR-018 says" column is the text before that amendment.

| # | ADR-018 says | This FDD does | Why |
|---|---|---|---|
| G1 | `fit_logits` takes `lr=0.1`, `steps=2000` and returns a dict; "the iteration still converges" | Matrix form (cost independent of the number of pairs), a step capped at `1 / (lam + 0.5 * max_degree)`, an early stop on a stationarity tolerance, and a `FitResult` that says whether it converged | The gradient is a sum over pairs, so a fixed step of 0.1 stops being safe as pairs grow: in the prototype it diverged at 3,000 pairs, the scale the ADR names ("a few thousand pairs"). With the safe step the cap can still be reached first, and a result must not claim convergence it did not reach (BRU-018-05) |
| G2 | Milliseconds, and "sub-millisecond execution times" in §6 | Measured, not assumed: about 50 ms for 2,000 steps on three actions in the prototype; the test records the time and bounds it loosely | The ADR itself says the timing "is to be measured, not assumed"; §6's sub-millisecond claim was not supported by the measurement |
| G3 | An override is `metadata["decision_disposition"]` of `modify` or `rejected` with `correct_action_id` differing from `action_id` | `feedback_status == "rejected"` with `correct_action_id` in the action space and differing from `action_id` | ADR-018 itself notes that no code reads `decision_disposition`. `feedback_status` and `correct_action_id` are what `autonomy.py` reads and what episode registration validates (`correct_action_id` must be in the policy's actions). Chosen by Menno on 2026-10-29 |
| G4 | `theta_ref` is "a frozen reference policy snapshot" | `theta_ref` is stored in `metadata["pairwise_reference_logits"]` on the first update that has a pair, and never overwritten | The ADR does not say where it lives or when it is frozen; the snapshot metadata keeps it within ADR-002 |
| G5 | Pairs are "derived dynamically" from episodes | The fit restarts from `theta_ref` over every pair offered; an episode id counts once | The runner re-queries recent episodes on every run. A refit is idempotent for a fixed pair set, so the counted-once record of FDD-015 to FDD-017 is not needed. The cost is that pairs which leave the runner's window are forgotten (section 7 item 4) |
| G6 | Logits are clamped to [-8, +8] | The fit clamps to 8.0 and the learner refuses a policy whose `max_logit_abs` is below 8.0 | `SoftmaxPolicy.apply_update` clips to its own `max_logit_abs` (default 10.0); a smaller one would silently cut the fitted values |
| G7 | `LearnerResult` as for other learners | `mean_reward` 0.0, the baseline unchanged, `consumed_inputs` `None` | There is no reward to consume, and `ConsumedInput` needs a reward id. The audit replay then reports insufficient lineage (section 7 item 2) |

---

## 5. Error Handling

| Scenario | Behavior |
|---|---|
| `lam < 0.05`, or any non-finite argument | `ValueError` naming the argument |
| `lr <= 0`, `steps < 1` or `clamp <= 0` | `ValueError` naming the argument |
| An action id missing from `theta_ref`, or a pair naming an action outside `action_ids` | `ValueError` naming it |
| `update` given another policy type | `TypeError` |
| `update` on a policy with `max_logit_abs` below `CLAMP` | `ValueError` |
| A stored `pairwise_reference_logits` with a missing action or a non-finite value | `ValueError` naming it |
| An episode that is not an override, or whose ids are outside the action space | skipped; counted in `skipped_episodes`, not in `episodes_used` |
| The iteration cap is reached | the result is returned with `converged` false and the stationarity measure |
| No pair | nothing changes; `episodes_used` is 0 |

---

## 6. Out of Scope

Showing the learner improves decisions; the Red Team pair set; listwise or contextual preferences; making the audit replay support this learner; combining it with REINFORCE on one policy; wiring it into the CLI.

---

## 7. Decisions and Open Questions

1. **G1 to G7: decided (2026-10-29).** Menno confirmed them and ADR-018 was amended to match. G1 keeps the 2,000-step cap, G3 reads `feedback_status`, and G5 is accepted with the forgetting of item 4.
2. **Open, and wider than this ADR: the audit replay supports only REINFORCE.** `agent_learning.audit` accepts a run only when `run.algorithm` is `ReinforceLearner` and `replay_implementation` is `reinforce_softmax_v1`; every other run reports insufficient lineage. That is true of the Thompson, UCB and epsilon-greedy learners of Epics 15 to 17 too. Whether a run of these learners should be replayable is a decision for ADR-005's comparison and the audit module, not for this FDD.
3. **Open: this learner and REINFORCE on one policy.** A refit from `theta_ref` replaces the logits, so a policy that REINFORCE has also trained would lose that training at the next pairwise update. The FDD does not combine them; nothing enforces it.
4. **Open: forgetting.** Pairs outside the runner's `episode_limit` window drop out of the next fit. Keeping them would need a stored record of the pairs, which ADR-002 forbids, or a different design (accumulating deltas, which needs a counted-once record).
5. **Decided: the iteration cap stays 2,000 (2026-10-29).** At the safe step, 3,000 pairs did not converge in 2,000 steps; `converged` makes the shortfall visible, and no real pair exists today. A larger cap or a better-conditioned method is revisited when real pairs reach that scale.
6. **Open: the Red Team pair set** (ADR-018 §3, §4.4): a human has to label a compliant counterpart for each adversarial frame.
7. **`LAMBDA_MIN = 0.05` and the clamp 8.0:** taken from ADR-018. There is no data behind either.

---

## 8. Test Data

*Real:* the recorded approval episodes (41 when ADR-018 was written, 76 committed files on 2026-10-29). Every one is accepted, so the real number of preference pairs is **zero**; the learner must leave the logits at `theta_ref` on them (Story 18.6). The governance fixtures hold 3 adversarial and 6 diff frames: single frames, not pairs. The 30 review-triage records do not qualify, because their reviewer is not a policy. *Gap:* real override episodes; adjudications where a human chose differently from a proposal. *Oracle:* the finite-difference gradient check, the single-pair stationary point of section 3, and synthetic pair sets built in the test, all labelled as arithmetic checks, not as evidence.
