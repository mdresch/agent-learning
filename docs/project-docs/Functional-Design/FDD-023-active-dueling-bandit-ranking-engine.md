# FDD-023: Active Dueling-Bandit Ranking Engine

**Source ADR:** [ADR-023](../../adr/ADR-023-active-dueling-bandit-ranking-engine.md) — Accepted (2026-10-28, Menno)  
**Source BRD:** [BRD-023](../Business-Requirements/BRD-023-active-dueling-bandit-ranking-engine.md)  
**Status:** Draft (2026-11-09) — derived from Accepted ADR-023 and Draft BRD-023; not yet adjudicated through `approve-fdd`. Section 4 lists eleven places (R1 to R11) where this design departs from ADR-023 §4.1 to §4.5 or fills a gap the ADR leaves open. None is confirmed. Sections 2 and 3 are written with the option this FDD recommends for each, marked *provisional (R#)*, and every one needs Menno's choice before the stories that depend on it can be approved.  

---

## 1. Architecture & Component Placement

1. **Module** `src/agent_learning_ext/dueling.py` (R1), not the `src/agent_learning/dueling.py` of ADR-023 §4.5. It holds the constants of section 2.1, `BTFit`, and the functions `fit_bradley_terry`, `laplace_variance`, `next_pair`, `converged`, `tournament_state` and `comparisons_from_episodes`. It is pure in the sense of ADR-023 §4.5. It takes items, comparisons, utilities and episodes as arguments, and it returns values and dicts. It imports nothing from `agent_learning.storage`, uses no random number, and does no file I/O. The caller reads and writes the store.
2. **Reuse of the ADR-018 code** (BRU-023-13). The penalized loss and its gradient are `bt_loss` and `bt_gradient` of `agent_learning_ext.learners.pairwise`. Both accept a count matrix `W` as a `numpy` array and any `lam >= 0`. With `theta_ref` set to zeros, `bt_loss` is exactly the negative of ADR-023's `l(lambda)` in §4.1. This epic does not write a second Bradley-Terry loss. Three parts of that module are not reused, and the reasons are stated here:
   - `fit_logits` refuses `lam < 0.05` (`LAMBDA_MIN`), while ADR-023 requires the 0.01 floor and default. It also clips every logit to [-8, +8], which is a constraint ADR-023 does not have, and it is projected gradient descent rather than MM (R2).
   - `build_pair_matrix` and `PreferencePair` carry a `source_episode_id`, and `fit_logits` counts each episode id once. A tournament's comparisons are `(winner, loser)` tuples, and the same pair may legitimately be asked twice. `dueling.py` builds `W` itself.
   - `PairwiseLearner` changes a `SoftmaxPolicy`'s action logits. The dueling engine ranks items, not actions, and changes no policy.
3. **Dependencies.** `numpy` (already a dependency of `SoftmaxPolicy` and `pairwise.py`) and the standard library. The PMP's "standard library only" invariant for `agent-training-ext/` (PMP §6 Invariant 4) is not met by this choice, as it is not met by `pairwise.py` today. See section 7 item 2.
4. **Package export.** The public names are added to `_EXPORTS` in `src/agent_learning_ext/__init__.py`. They shadow no existing export, which was checked against `_EXPORTS` on 2026-11-09 (LL-017).
5. **No command, no policy shape, no CLI change.** ADR-023 names the module only. How a pair is presented to a human, and how the answer is written to the store, is section 7 item 3.
6. **State.** `PolicySnapshot.metadata["dueling_bandit"]` holds the dict of section 2.4, built by `tournament_state`. Each human answer is a standard `Episode` (section 2.5; R10). Shared types are unchanged, and `src/agent_learning/` gains no line (`tests/test_upstream_untouched.py` already enforces this).

---

## 2. Data Contract

### 2.1 Constants
| Name | Value | Meaning |
|---|---|---|
| `LAMBDA_REG_MIN` | 0.01 | the lowest allowed L2 weight (ADR-023 §4.1, Invariant 6) |
| `LAMBDA_REG_DEFAULT` | 0.01 | the default of `fit_bradley_terry` (ADR-023 §4.5) |
| `K_MIN` | 2 | the minimum comparisons per item (ADR-023 §4.2, Invariant 5); also the lowest allowed `k_min` |
| `OBVIOUS_P` | 0.95 | a pair with `P > 0.95` in either direction is obvious (ADR-023 §4.2) |
| `ITERS_DEFAULT` | 200 | the iteration cap of `fit_bradley_terry` (ADR-023 §4.5) |
| `TOL_DEFAULT` | 1e-8 | the stationarity tolerance, on the largest absolute gradient entry, *provisional (R3)* |
| `TIE_TOL` | 1e-12 | two selection scores closer than this are a tie, *provisional (R6)* |
| `PAIR_SEP` | `"::"` | the separator in a `comparison_counts` key (ADR-023 §4.4) |
| `RANKING_STATUSES` | `in_progress`, `converged`, `budget_exhausted`, `no_informative_pair`, `exposure_unmet` | the values of `ranking_status`, *provisional (R8, R11)*. ADR-023 §4.4 shows only `converged` |

There is no `TAU_DEFAULT`. ADR-023 §4.3 calls `tau_rank_confidence` "a declared threshold", and no calibrated value exists (BRU-023-09).

### 2.2 Comparisons
A comparison is a tuple `(winner, loser)` of two different item ids, as in ADR-023 §4.5. The tuple order is the outcome, not the order the pair was shown in. `N_ij` is the number of comparisons between `i` and `j` in either direction. The exposure of an item is the number of comparisons it appears in.

### 2.3 The fit result (*provisional, R3*)
```python
@dataclass(frozen=True)
class BTFit:
    utilities: dict[str, float]   # one per item, in item order, summing to 0 within 1e-9
    converged: bool               # True when the stationarity measure fell to tol before the cap
    iterations: int               # MM steps taken
    stationarity: float           # max_i |d bt_loss / d lambda_i| at the returned utilities
    log_likelihood: float         # the penalized log-likelihood l(lambda) of ADR-023 §4.1, equal to -bt_loss
```

### 2.4 Tournament state in the snapshot
```json
"dueling_bandit": {
  "item_ids": ["feat-auth", "feat-storage", "feat-caching"],
  "comparison_counts": {"feat-auth::feat-storage": 3},
  "latent_utilities": {"feat-auth": 1.42, "feat-storage": -0.15, "feat-caching": -1.27},
  "ranking_status": "converged",
  "parameters": {"lambda_reg": 0.01, "k_min": 2, "tau_rank_confidence": 0.5, "budget": 9},
  "comparisons_used": 3
}
```
The first four fields are ADR-023 §4.4, and the example values are the ADR's own, which sum to 0. `parameters` and `comparisons_used` are *provisional (R10)*. A key of `comparison_counts` is the two ids in `item_ids` order joined by `PAIR_SEP`, and only pairs asked at least once appear (R10). The snapshot is a derived view. The comparisons themselves live in the episodes of section 2.5, because the counts do not record who won and the fit cannot be recomputed from them (R10).

### 2.5 An answer episode (*provisional, R10*)
```json
{
  "task_id": "rank-backlog",
  "action_id": "feat-auth",
  "action_logprob": null,
  "metadata": {
    "dueling_comparison": {"tournament_id": "rank-backlog-2026-11", "pair": ["feat-auth", "feat-storage"], "winner": "feat-auth"},
    "feedback_status": "adjudicated"
  }
}
```
`pair` is the pair as shown, in the order `next_pair` returned it. `winner` is one of the two ids. `action_id` repeats the winner. `action_logprob` is `null`, so `ReinforceLearner`'s existing skip of an episode without a log-probability keeps it out of training (BRU-023-12). The task id, the tournament id and the `feedback_status` value are placeholders until R10 is decided.

---

## 3. Behavior

1. **`fit_bradley_terry(items, comparisons, *, lam=0.01, iters=200, tol=1e-8) -> BTFit`** (BRU-023-01 to 03; R2, R3 *provisional*).
   1. **Validation.** It raises `ValueError` when `items` has fewer than two entries, an entry that is not a non-empty string, or a duplicate. It also raises `ValueError` for a comparison that is not a 2-tuple of item ids, a comparison naming an id that is not in `items` (Q-149-12; §5 already lists it), a comparison whose winner equals its loser, a `lam` that is not finite or is below `LAMBDA_REG_MIN`, an `iters` below 1, or a `tol` that is not finite and positive. Each message names the argument.
   2. **Counts.** `W[w][l]` is the number of comparisons `(w, l)`. `n = W + W^T`, and `L = diag(n 1) - n` is the comparison-graph Laplacian.
   3. **Iteration (quadratic-bound MM, R2 option a).** `B = lam * I + L / 4` is fixed for the fit and inverted once. Start at `lambda = 0`. Each step is `lambda <- lambda - B^-1 g`, with `g = bt_gradient(lambda, W, zeros, items, lam=lam)`. Because `sigma(z)(1 - sigma(z)) <= 1/4`, the quadratic with curvature `B` bounds the negative penalized log-likelihood from above at every point, so each step cannot decrease `l(lambda)`. That is the minorization-maximization property of ADR-023 §4.1. Stop before a step when `max |g| <= tol` (`converged` true), or after `iters` steps (`converged` false unless the last gradient met `tol`).
   4. **Normalization.** The vector `1` is an eigenvector of `B` with eigenvalue `lam`, and `1^T g = lam * sum(lambda)`, so every step returns a vector whose entries sum to 0. The returned utilities are also centred by subtracting their mean, so the sum is 0 within 1e-9 whatever rounding occurred (BRU-023-01).
   5. **No clamp.** No box constraint is applied. The L2 term keeps the utilities finite (BRU-023-02).
   6. **No comparisons.** The utilities are all 0, `converged` is true, `iterations` is 0, and `log_likelihood` is 0.
2. **`laplace_variance(items, comparisons, utilities, *, lam) -> dict[str, float]`** (BRU-023-05; R5 *provisional*).
   1. `H = lam * I + sum over pairs {i, j} of n_ij * p_ij * (1 - p_ij) * (e_i - e_j)(e_i - e_j)^T`, with `p_ij = sigma(u_i - u_j)`. This is the Hessian of `bt_loss` at `utilities`.
   2. The result is the variance of the centred utilities, `diag(P H^-1 P)` with `P = I - 1 1^T / N` (R5 option b). Because `1` is an eigenvector of `H` with eigenvalue `lam`, this equals `diag(H^-1) - 1 / (N * lam)`.
   3. It raises `ValueError` for the input errors of item 1.1, for `utilities` whose keys differ from `items` or with a non-finite value, and for `lam` below `LAMBDA_REG_MIN`. It does not check that `utilities` is the fit for these comparisons and this `lam` (section 7 item 5).
3. **`next_pair(items, comparisons, utilities, *, k_min=2) -> tuple[str, str] | None`** (BRU-023-06 to 08; R6, R7, R8 *provisional*).
   1. It raises `ValueError` for `k_min < K_MIN`, or for the input errors of items 1.1 and 2.3.
   2. **Exposure first (R7 option a).** While any item has exposure below `k_min`, the candidates are the pairs that contain at least one such item, and no pair is skipped as obvious.
   3. **Then skip the obvious (R8).** Once every item has exposure of at least `k_min`, the candidates are the pairs with `|P(i > j) - 0.5| <= 0.45`. When there are none, the result is `None`.
   4. **Score.** For each candidate `{i, j}` with `i` before `j` in `items`, the score is `|sigma(u_i - u_j) - 0.5| * sqrt(N_ij + 1)` (ADR-023 §4.2).
   5. **Choice and tie-break (R6 option a).** The result is the candidate with the lowest score. Scores within `TIE_TOL` of the lowest are tied. Among tied candidates the one with the lower `N_ij` wins, then the one whose `(index of i, index of j)` in `items` comes first. The result is `(items[i], items[j])` with `i` before `j`.
4. **`converged(variances, tau, used, budget, *, min_exposure, k_min=2) -> bool`** (BRU-023-07, 09, 10; R9, R11 *provisional*). `variances` is the `dict[str, float]` that `laplace_variance` returns, and "the largest variance" below means `max(variances.values())`.
   1. `N = len(variances)`. It raises `ValueError` for `N < 2`, a non-finite or negative variance, a `tau` that is not finite and positive (there is no default), a negative `used`, `used > budget`, `k_min < K_MIN`, or a `budget` outside `[k_min * N, floor(2 * N * log2 N)]`.
   2. While `min_exposure < k_min` the result is false, whatever `used` is (R11 option B). When every pair comes from `next_pair`, this cannot happen with `used == budget`. A budget of at least `k_min * N` leaves room for the exposure rule, because each such comparison lowers the total exposure shortfall, which starts at `k_min * N`, by at least 1 (section 3 item 3.2). Comparisons chosen another way, such as replayed or manual records, carry no such guarantee. `converged` does not require that pairs came from `next_pair`. A spent budget with exposure short is reported by `tournament_state` as `exposure_unmet`.
   3. Otherwise the result is true when the largest variance is at or below `tau`, or when `used >= budget`.
5. **`tournament_state(items, comparisons, fit, variances, *, tau, budget, k_min=2, lam=0.01, exhausted=False) -> dict`** (BRU-023-11; R8, R10, R11 *provisional*). It returns the dict of section 2.4. `variances` is a `dict[str, float]`, as in item 4. It first calls `converged(variances, tau, len(comparisons), budget, min_exposure=<the smallest item exposure>, k_min=k_min)`, so it validates its inputs exactly as item 4.1 does and raises the same `ValueError` for the same inputs (Q-149-11). The `converged` status is narrower than a true result of that call: item 4.3 is also true when `used >= budget`, and that case is reported as `budget_exhausted`, not `converged`. `ranking_status` takes the first of these that holds, checked in this order: `converged` when the call is true by the variance test of item 4.3 (every item has exposure of at least `k_min` and `max(variances.values()) <= tau`); `exposure_unmet` when `len(comparisons) >= budget` and an item has exposure below `k_min`; `budget_exhausted` when `len(comparisons) >= budget`; `no_informative_pair` when `exhausted` is true (the caller got `None` from `next_pair`); `in_progress` otherwise. It raises `ValueError` for an item id containing `PAIR_SEP`, and for a `fit` whose `utilities` keys or `variances` keys are not exactly the ids in `items` (Q-149-14). The dict survives `json.dumps` and `json.loads` unchanged.
6. **`comparisons_from_episodes(episodes, tournament_id, items) -> list[tuple[str, str]]`** (BRU-023-11, 12; R10 *provisional*). An episode gives one comparison when its `metadata["dueling_comparison"]` has this `tournament_id`, a `pair` of two different ids in `items`, and a `winner` that is one of them. The comparison is `(winner, the other id)`. Duplicates are detected by the `Episode.id` field value, not by object identity or by the comparison tuple: two episode objects with the same `id` give one comparison (the first seen), while two different ids recording the same pair and winner give two comparisons, because they are two answers (Q-149-13). Any other episode is skipped, and no error is raised. The order is first appearance. The episodes are not changed.

**Worked checks (arithmetic, recomputed on 2026-11-09 with a throwaway script that called the real `bt_loss` and `bt_gradient`, solved the penalized fit by Newton's method to a gradient below 1e-12, and inverted `H` with `numpy`; to be re-run through the real functions when built, LL-036).** All use `lam = 0.01`.
- **Counts.** `N(N-1)/2` is 45, 190 and 435 for N = 10, 20 and 30. `floor(2 N log2 N)` is 4, 9, 23, 66, 172, 294 and 1,328 for N = 2, 3, 5, 10, 20, 30 and 100. `k_min * N` is 4, 6, 10, 20, 40, 60 and 200. The cap is below the exhaustive count only from N = 18 (150 against 153). At N = 17 it is 138 against 136 (BRU-023-14).
- **Two items.** One win of `a` over `b` gives `t = 1.9570`, `P(a > b) = 0.9804`, with `t` the root of `sigma(-2t) = 0.01 t`. Two wins give `t = 2.2402`, `P = 0.9888`. Three wins and one loss give `t = 0.5457`, `P = 0.7486`. One win each gives `t = 0`, `P = 0.5`. `bt_gradient` is 0 at each within 1e-10.
- **Variance.** For one win of `a` over `b`, the raw `[H^-1]_ii` is 60.3361 and the centred variance is 10.3361, which is `60.3361 - 1 / (2 * 0.01)`. For three wins and one loss they are 50.3299 and 0.3299. The raw diagonal can never fall below `1 / (N * lam)`, which is 50, 33.33, 20, 5 and 1 for N = 2, 3, 5, 20 and 100 (R5).
- **Three items, a chain** (`a > b`, `b > c`, `a > c`). The utilities are `(3.3865, 0, -3.3865)`. The raw variances are `(46.3020, 39.6854, 46.3020)` and the centred ones are `(12.9687, 6.3521, 12.9687)`. `P` is 0.9673 for `(a, b)` and `(b, c)` and 0.9989 for `(a, c)`. Every item has exposure 2 and every pair is above 0.95, so `next_pair` is `None`.
- **Three items, a tie** (`a > b`, `b > a`, `a > c`, `b > c`). The utilities are `(1.4147, 1.4147, -2.8293)`. `(a, b)` has `P = 0.5`, `N_ab = 2` and score 0. `(a, c)` and `(b, c)` have `P = 0.9859` and are obvious. `next_pair` is `(a, b)`. A pair at exactly 0.5 scores 0 however often it was asked (R6).
- **Four items, cold start.** With no comparison every score is 0 and every `N_ij` is 0, so the tie-break gives `(a, b)`. After `a > b` the utilities are `(1.9570, -1.9570, 0, 0)`. Every item is still under-exposed. The scores are 0.6794 for `(a, b)`, 0.3762 for each of `(a, c)`, `(a, d)`, `(b, c)` and `(b, d)`, and 0 for `(c, d)`, so `next_pair` is `(c, d)`. An item never compared has raw variance `1 / lam = 100` and centred variance 75.
- **Two items, exposure before skipping.** After one `a > b`, `P = 0.9804` is obvious, but both items have exposure 1, so `next_pair` is `(a, b)`. After a second `a > b`, both have exposure 2 and `P = 0.9888`, so `next_pair` is `None`.
- **Obvious threshold.** `P > 0.95` is `|u_i - u_j| > ln 19 = 2.9444`.
- **Budget range.** N = 5 accepts budgets 10 to 23. N = 2 accepts only 4. N = 20 accepts 40 to 172, and N = 100 accepts 200 to 1,328.

**Measured on 2026-11-09 with a throwaway prototype of the recommended options (not committed; this machine, `numpy` 2.5.3).**
- **Monotone, not converged at the cap.** For N = 100 and 1,328 seeded comparisons (`numpy.random.default_rng(20261026)`, truths drawn from a standard normal), the penalized log-likelihood never decreased over 200 steps. At step 200 the largest gradient entry was 3.8e-3, and the largest utility was 0.050 from the exact optimum. The gradient first fell to `tol = 1e-8` after 1,017 steps, and 2,000 steps reached 2e-15. On the epics' N = 100 set, built with `random.Random(20261026)` (Epic 23 fixtures), the largest gradient at step 200 was 6.3e-3, and `tol = 1e-8` was reached after 1,245 steps. The two sets are different draws, so their figures differ. Either way, the ADR's `iters=200` does not converge at that scale (R3).
- **Time.** The median of five runs was 98 ms for 200 steps and 920 ms for 2,000 steps. Ten exact Newton steps, which converge, took 218 ms. None met the 50 ms of Invariant 2 or the 5 ms of §4.1 on this machine (R4).
- **The skip ends tournaments early.** With five items of true utility `(1.5, 0.5, 0.0, -0.8, -1.2)`, `random.Random(20261026)`, one `rng.random()` per comparison (the first item named wins when the draw is below its true `P`), budget 23 and `tau` 1.0, the run ended `no_informative_pair` after 11 comparisons. The order was right, but the utilities were `(6.4651, 3.0409, 0, -3.0409, -6.4651)` and the largest centred variance was 12.83. Over seeds 0 to 199 the run spent the full budget of 23 in 181 cases and ended `no_informative_pair` in 19. The fitted order equalled the true order in 50 of 200. With ten items 0.4 apart, every one of 50 seeds spent the full budget of 66, more than the 45 exhaustive pairs, and none recovered the exact order (R8; BRU-023-14).

---

## 4. Departures from ADR-023 §4.1 to §4.5, and Gaps It Leaves

Each is a place where ADR-023 does not fit the code that exists today, contradicts itself, or leaves open something code needs closed. None is confirmed.

| # | ADR-023 says | This FDD does | Why |
|---|---|---|---|
| R1 | Module `src/agent_learning/dueling.py` (§4.5) | `src/agent_learning_ext/dueling.py`, exported through `agent_learning_ext/__init__.py` | The fork rule (PMP §4, Invariant 6; `tests/test_upstream_untouched.py`) forbids new code under `src/agent_learning/`. Epics 18, 21 and 22 were built the same way even though their FDDs named `src/agent_learning/`. Needs Menno's confirmation |
| R2 | "Minorization-Maximization (MM) algorithm (Hunter 2004), guaranteeing monotone convergence" (§4.1) | (a) Recommended: the quadratic-bound MM of section 3 item 1.3, on the stated penalized objective, using `bt_gradient`. (b) Hunter's closed-form MM. (c) Reuse `fit_logits`. (d) Newton's method with the Hessian of section 3 item 2 | Hunter's update maximizes the unpenalized likelihood in `gamma = e^lambda`. With the L2 term on `lambda` it has no closed form, and for a winless item it drives `gamma` to 0, so (b) does not solve the ADR's own objective. (c) refuses `lam < 0.05` and clips at ±8. (d) is faster but not monotone without a line search. (a) is an MM algorithm and is monotone, but it converges slowly (section 3, measured). Needs Menno's choice |
| R3 | `fit_bradley_terry(...) -> dict[str, float]`, `iters: int = 200` (§4.5) | Returns `BTFit` with `converged`, `iterations` and `stationarity`, and adds `tol` | At N = 100 and 1,328 comparisons, 200 steps of (a) did not converge (gradient 3.8e-3). A plain dict cannot say so. FDD-018 G1 made the same change for the same reason (BRU-023-03). Whether to keep 200 or raise the cap is part of the choice. Needs Menno's choice |
| R4 | "< 5 ms on CPU for N ≤ 100" (§4.1); "< 50 ms" (Invariant 2); "100 items fit well inside 50 ms" (§4.5 tests) | The test fits N = 100 with 1,328 comparisons (the full budget), records the median of five runs, and asserts the bound Menno chooses | The ADR states two bounds. The prototype took 98 ms for 200 steps on this machine, so neither holds as measured. Options: assert 50 ms and accept that Story 23.1 fails until a faster method is chosen; or record the time and bound it loosely (5 s, as Story 18.3 AC_8 does) and amend Invariant 2. Until R4 is decided, Story 23.1 AC_8 asserts the provisional 5 s, so the criterion stays testable. The prototype measured 98 ms at the default cap and 920 ms at 2,000 steps, both below 5 s. Needs Menno's choice |
| R5 | `Var(lambda_i) ~ [H^-1]_ii`; halt when `max Var <= tau` (§4.3) | (b) Recommended: the variance of the centred utilities, `[H^-1]_ii - 1 / (N * lam)`. (a) The raw diagonal as written, with `tau <= 1 / (N * lam)` refused because it can never be met | The likelihood does not change when every utility moves by the same amount, so along `1` the curvature is the penalty alone, `lam`. The raw diagonal then contains `1 / (N * lam)` whatever the data: 5 for N = 20, 1 for N = 100. With (a) a tournament with any `tau` below that floor can stop only on budget. (b) matches the sum-to-zero normalization of §4.1. Needs Menno's choice |
| R6 | `argmin` over pairs, no tie rule (§4.2) | Ties within 1e-12 are broken by lower `N_ij`, then by item order | At the start every utility is 0, so every pair scores 0. A pair at exactly `P = 0.5` scores 0 whatever its `N_ij`, so the `sqrt(N_ij + 1)` factor cannot demote it. In the worked tie case, `(a, b)` is asked a third time ahead of pairs asked once. A deterministic rule is needed for replay (BRU-023-06). Whether to also add a floor to `|P - 0.5|`, so that a tied pair loses priority as it is repeated, is part of the choice. The size of that floor has no data behind it. Needs Menno's choice |
| R7 | Under-exposed items are "prioritized for query pairing" (§4.2), partner unspecified | (a) Recommended: candidates are the pairs with at least one under-exposed item, scored as usual. (b) Prefer pairs where both items are under-exposed | The ADR does not say who an under-exposed item is paired with. (a) needs at most `k_min * N` comparisons to meet the rule, because each comparison lowers the total shortfall by at least 1. The walkthrough sketch pairs only the first under-exposed item. Needs Menno's choice |
| R8 | Obvious pairs (`P > 0.95`) "are bypassed once all items satisfy the minimum exposure constraint" (§4.2); `ranking_status` shows only `converged` (§4.4) | When every pair is obvious, `next_pair` returns `None` and the status is `no_informative_pair`. The statuses are `in_progress`, `converged`, `budget_exhausted` and `no_informative_pair` | `next_pair` may return `None` (§4.5 signature), but `converged` cannot see that, and a `None` is not convergence by the variance rule. With `lam = 0.01` two consistent answers already make a pair obvious (two items: `P = 0.9888`), so in the prototype a five-item run stopped after 11 comparisons with a largest centred variance of 12.83. Options: keep the skip as written; skip only when the pair's variance is also small; or drop the skip and rely on the score. Needs Menno's choice |
| R9 | `converged(variances, tau, used, budget)`; `B_max <= 2 N log2 N` (§4.3); Invariant 5 | Adds `min_exposure` and `k_min`; returns false while exposure is short; refuses a budget outside `[k_min * N, floor(2 N log2 N)]` | Invariant 5 forbids a final rank before every item has `k_min` comparisons, but the ADR's `converged` cannot see exposure. The ADR gives only an upper bound on the budget, and a budget below `k_min * N` can end before Invariant 5 is met. `floor` is needed because the bound is not an integer (9.51 for N = 3). Needs Menno's choice |
| R10 | State in `metadata["dueling_bandit"]` with four fields; "persist each answer as an episode" (§4.4, §4.5); Invariant 3 | Answers are episodes of the shape in section 2.5, and the snapshot dict is derived from them. Keys are canonical in `item_ids` order. Ids containing `::` are refused. `parameters` and `comparisons_used` are added | `comparison_counts` does not record who won, so the fit cannot be recomputed from the snapshot. The ADR says neither which order a key uses nor what happens to an id that contains the separator. Without the parameters in force, a stored status cannot be checked. FDD-021 K1 derived per-request state from episodes for the same reason. The task id, tournament id and `feedback_status` value of an answer episode are not decided. Needs Menno's choice |
| R11 | Invariant 5 (no final rank before `k_min` comparisons); `converged` as in §4.3; nothing on comparisons chosen outside the engine | (B) Proposed: `converged` returns false while exposure is short, whatever `used` is, and `tournament_state` reports `exposure_unmet` when the budget is spent with exposure short. (A) `converged` raises `ValueError` in that case, with the precondition stated that every comparison came from `next_pair` | The budget argument of R9 guarantees exposure only for pairs chosen by `next_pair`. Replayed or manual records, which `comparisons_from_episodes` accepts, can spend the budget first. (A) treats that as a programming error even though the data are legitimate. (B) keeps Invariant 5, because nothing is ranked as converged, and shows the case instead of raising. Needs Menno's choice |

---

## 5. Error Handling

| Scenario | Behavior |
|---|---|
| Fewer than two items, a blank or non-string id, or a duplicate id | `ValueError` naming the argument |
| A comparison with an unknown id, the same id twice, or the wrong shape | `ValueError` naming it |
| `lam` below 0.01 or not finite | `ValueError` |
| `iters < 1` or a bad `tol` | `ValueError` |
| The iteration cap is reached | `BTFit` with `converged` false and the stationarity (R3) |
| `utilities` with missing, extra or non-finite entries | `ValueError` |
| `k_min` below 2 | `ValueError` |
| Every pair obvious after exposure is met | `next_pair` returns `None` (R8) |
| `tau` missing, not finite or not positive | `ValueError`; there is no default |
| A budget above `floor(2 N log2 N)` or below `k_min * N`, or `used > budget` | `ValueError` (R9) |
| The budget is spent while an item is under-exposed (only possible when pairs did not come from `next_pair`) | `converged` returns false; `tournament_state` reports `exposure_unmet` (R11) |
| An item id containing `::` in `tournament_state` | `ValueError` (R10) |
| A `fit` or `variances` in `tournament_state` whose keys are not exactly `items` | `ValueError` naming the mismatched ids |
| An episode that is not an answer of this tournament, or names an unknown item | skipped by `comparisons_from_episodes` |

---

## 6. Out of Scope

Measuring HYP-AL-015; a command or interface that presents pairs and records answers; ADPA integration; calibrating `tau_rank_confidence`; non-transitive cycles beyond the L2 penalty; ties, multi-item rankings and contextual preferences; wiring into existing commands.

---

## 7. Decisions and Open Questions

1. **Open: scope authority.** `PMP-BL-v1.1.0` authorizes Epics 14, 16, 18, 21, 22 and 38 and does not name Epic 23. Approving these documents does not authorize building them. That needs a scope change through Stage 16 change control or the next baseline. This also decides which `pmp_baseline` the story headers cite (PMP §6 Invariant 2).
2. **Open: `numpy` and PMP §6 Invariant 4.** The PMP says modules in `agent-training-ext/` use the standard library only. `pairwise.py`, which this design reuses, already uses `numpy`, and that is under `src/agent_learning_ext/`, not `agent-training-ext/`. Whether the invariant covers `src/agent_learning_ext/` is not stated. If it does, both modules break it.
3. **Open: how an answer reaches the store.** No command presents a pair or records an answer, and ADR-023 names none. The first real run that §4.5 asks for needs one. That is a separate decision and is out of scope here.
4. **Open: presentation order.** `next_pair` returns the pair in item order. Whether to show it in that order, or to swap it to control for position bias, is not decided. Such a swap would need a seeded random number, which this module does not use.
5. **Open: variance of a stale fit.** `laplace_variance` trusts that `utilities` came from `fit_bradley_terry` on the same comparisons and `lam`. It could check that the gradient there is near 0. The design does not, because a fit stopped at the cap (R3) would then be refused.
6. **Open: the combined effect of R5, R8 and `lam = 0.01`.** In the prototype the variance rule never decided a run: with `tau` 1.0, five-item runs ended on the skip or the budget, and ten-item runs always on the budget. Whether ADR-023 §4.3's stopping rule can work at `lam = 0.01` depends on R5 and R8 together, and on a `tau` nobody has chosen.
7. **Walkthrough sketch.** `examples/methodologies/23-dueling-bandit/sketch.py` uses a fixed-step gradient fit with mean-centring, 60 steps per fit, pairs only the first under-exposed item, breaks ties by dictionary order, and has no skip, no variance and no budget check. ADR-023 §4.5 says it must be rewritten against the real module once built. No story does that here, and this is open. A rewrite changes the `CODE: sketch` header and the catalog's `proof_of_concept` class, and `tests/test_methodology_sketches.py` (BRD-036) enforces both. Epics 18, 21 and 22 were built without rewriting sketches 13, 17 and 22, which are still `candidate` and `proof_of_concept` in `examples/methodologies/catalog.json`. Whether Epic 23 adds a story for it, under ADR-036's rules, is Menno's choice. Until then it stays a sketch, not evidence.
8. **`LAMBDA_REG_MIN = 0.01`, `K_MIN = 2` and `OBVIOUS_P = 0.95`** are taken from ADR-023. There is no data behind any of them.

---

## 8. Test Data

*Real:* the backlog is real. The 36 epic files under `docs/user-stories/` held 144 `## Story` headings on 2026-11-09, and there are 38 ADR files. But the repository holds **no recorded pairwise judgment** about them. Checked on 2026-11-09: none of the 187 committed files in `docs/policy-shapes/episodes/` carries a comparison. The six that mention "pairwise" or "winner" are the approval episodes of ADR-018 (two), ADR-023, BRD-018, FDD-018 and Epic 18, and the words occur in their text. `data/agent-learning/store` is git-ignored and is not a test source (LL-037). Story 23.7 shows the gap. *Gap:* Menno's own comparisons of real items, each persisted as an answer episode (section 2.5). Until then HYP-AL-015 is untested. *Synthetic:* a seeded tournament against known utilities may check only the maths, labelled synthetic and not evidence (Story 23.6). *Oracle:* the two-item closed form and the worked checks of section 3.
