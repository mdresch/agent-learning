# Epic 23: Active Dueling-Bandit Ranking Engine

**Source ADR:** [ADR-023](../adr/ADR-023-active-dueling-bandit-ranking-engine.md) — Accepted (2026-10-28, Menno)  
**Source BRD/FDD:** [BRD-023](../project-docs/Business-Requirements/BRD-023-active-dueling-bandit-ranking-engine.md) / [FDD-023](../project-docs/Functional-Design/FDD-023-active-dueling-bandit-ranking-engine.md)  
**Status:** Approved (2026-11-09, Menno) — derived from Accepted ADR-023, BRD-023 and FDD-023; adjudicated via `approve-user-stories` (robust utility 0.794, episode `774761c3-147a-4e23-9adf-f7a3f96c389c`). The epic number follows the source ADR number, as Epic 22 follows ADR-022.

Seven stories build `src/agent_learning_ext/dueling.py` (FDD-023 R1). The module reuses `bt_loss` and `bt_gradient` of `agent_learning_ext.learners.pairwise` (Epic 18). Each rule sits in exactly one story's criteria (LL-012). Contract tests are `tests/test_dueling_fit.py` (23.1), `tests/test_dueling_variance.py` (23.2), `tests/test_dueling_next_pair.py` (23.3), `tests/test_dueling_converged.py` (23.4), `tests/test_dueling_state.py` (23.5), `tests/test_dueling_synthetic.py` (23.6) and `tests/test_dueling_real_data.py` (23.7). Measuring HYP-AL-015, a command that presents pairs to a human, and rewriting the walkthrough sketch are not stories (BRD-023 Out of Scope; FDD-023 §7 items 3 and 7).

**FDD-023 decisions R1–R11 are confirmed, and all seven stories are approved.** Implementation remains blocked until Stage 16 change control authorizes Epic 23 in the project baseline (FDD-023 §7 item 1). The measured criteria below are to be verified against the implementation at Ingest; the prototype values are not golden expectations. No story depends on another epic. Epic 18's `pairwise.py` is reused unchanged.

Fixtures used by the criteria below. "The base items" are `a`, `b`, `c`, `d` in that order, with `lam` 0.01 and `k_min` 2. A comparison `(w, l)` means `w` beat `l`. "The N = 100 set": `random.Random(20261026)` draws 100 truths with `gauss(0, 1)` for items `x000` to `x099`. Then, 1,328 times, it picks `i, j = rng.sample(range(100), 2)`, and `i` wins when `rng.random() < sigma(t_i - t_j)`. "The N = 20 set" is the same, with truths `2.0 - 0.2 k` for items `y00` to `y19`, 172 comparisons, and no `gauss` draw. All are built in the tests and labelled synthetic. The worked numbers come from FDD-023 §3. They were recomputed on 2026-11-09 with the real `bt_loss` and `bt_gradient` and must be re-run through the real functions at Ingest (LL-036).

---

## Story 23.1 — The Bradley-Terry Fit

**Status:** Approved — implementation blocked pending Stage 16 baseline scope authorization; the 5 ms performance target is not met by the current prototype.
**As** an auditor, **I want** the utilities fitted by a monotone, regularized Bradley-Terry fit that says whether it converged, **so that** a ranking can be checked against the likelihood it maximizes.

### Acceptance Criteria:
- **$AC_0$ (Validation):** `fit_bradley_terry` raises `ValueError`, naming the argument, for one item, a blank or non-string item, a duplicate item, a comparison naming an unknown item, a comparison `(a, a)`, a comparison that is not a 2-tuple, `lam` of 0.0099 or NaN, `iters` of 0, and `tol` of 0. `lam` of 0.01 is accepted.
- **$AC_1$ (Two-Item Oracle):** one comparison `(a, b)` gives utilities `(1.9570, -1.9570)` within 1e-4, equal to the root of `sigma(-2t) = 0.01 t` found by bisection in the test. Three `(a, b)` and one `(b, a)` give `(0.5457, -0.5457)`. One of each gives `(0, 0)` within 1e-9.
- **$AC_2$ (Finite Without Losses):** an item that never lost and an item that never won get finite utilities. The chain `(a, b)`, `(b, c)`, `(a, c)` over `a`, `b`, `c` gives `(3.3865, 0.0, -3.3865)` within 1e-4.
- **$AC_3$ (Sum To Zero):** the utilities of every fit in this story sum to 0 within 1e-9, including the N = 100 set.
- **$AC_4$ (Monotone):** on the N = 20 set, `log_likelihood` of the fit with `iters = k` does not decrease from `k` to `k + 1` by more than 1e-12, for `k` from 1 to 50 (measured: 0 decreases).
- **$AC_5$ (Honest Convergence):** on the N = 100 set at `iters = 200` the result has `converged` false, `iterations` 200 and a `stationarity` above `tol` (measured: 6.3e-3). At `iters = 2000` it has `converged` true, `stationarity` at or below 1e-8, and fewer than 2,000 iterations (measured: 1,245). With no comparisons the utilities are all 0, `converged` is true and `iterations` is 0.
- **$AC_6$ (Reuses ADR-018 Code):** `log_likelihood` equals `-bt_loss(utilities, W, zeros, items, lam=lam)` within 1e-12. At a converged fit, `bt_gradient` there is at most `tol` in every entry. `dueling.py` imports `bt_loss` and `bt_gradient` from `agent_learning_ext.learners.pairwise` and defines no Bradley-Terry loss of its own.
- **$AC_7$ (Pure And Deterministic):** the same arguments give identical results on repeated calls. The inputs are equal to their copies after the call. `dueling.py` imports nothing from `agent_learning.storage` and no `random` module.
- **$AC_8$ (Time):** the test fits the N = 100 set at the default cap five times and records the median. It asserts a median below 5 ms, as selected in FDD-023 R4. The prototype measured 98 ms at the default cap on 2026-11-09 (920 ms at 2,000 steps), so the current method does not meet the criterion; optimization is required.

---

## Story 23.2 — The Laplace Variance

**Status:** Approved — implementation blocked pending Stage 16 baseline scope authorization.
**As** an approver, **I want** each utility's uncertainty computed from the curvature of the fit, without the part that no comparison can reduce, **so that** a stopping threshold can actually be reached.

### Acceptance Criteria:
- **$AC_0$ (Two Items):** at the fitted utilities, one `(a, b)` gives variance 10.3361 for both items, and three `(a, b)` with one `(b, a)` give 0.3299, within 1e-4.
- **$AC_1$ (Three Items):** the chain of Story 23.1 AC_2 gives `(12.9687, 6.3521, 12.9687)`. The tie `(a, b)`, `(b, a)`, `(a, c)`, `(b, c)` gives `(3.7033, 3.7033, 12.8601)`.
- **$AC_2$ (Never Compared):** over the base items with the single comparison `(a, b)`, `c` and `d` get 75.0 and `a` and `b` get 35.3361.
- **$AC_3$ (Floor Removed):** for every case of this story the test inverts the Hessian with `numpy` and checks that its diagonal minus the result equals `1 / (N * 0.01)` within 1e-9: 50 for two items, 33.3333 for three, 25 for four.
- **$AC_4$ (Validation):** `utilities` with a missing item, an extra item or a NaN, and `lam` of 0.0099, each raise `ValueError`.

---

## Story 23.3 — The Next Pair

**Status:** Approved — implementation blocked pending Stage 16 baseline scope authorization.
**As** an adjudicator, **I want** to be asked only the comparisons that can still change the ranking, after every item has been seen twice, **so that** my effort goes where the order is uncertain.

### Acceptance Criteria:
- **$AC_0$ (Closest To 50:50):** over the base items after `(a, b)`, with utilities `(1.9570, -1.9570, 0, 0)`, `next_pair` returns `(c, d)` (score 0, against 0.3762 for the pairs mixing the two groups and 0.6794 for `(a, b)`).
- **$AC_1$ (Cold Start And Tie-Break):** with no comparison and all utilities 0, `next_pair` returns `(a, b)` over the base items and `(d, c)` over the items in the order `d`, `c`, `b`, `a`.
- **$AC_2$ (Exposure First):** two items after one `(a, b)` give `(a, b)` although `P = 0.9804`. Over the base items after `(a, b)`, `(b, c)`, `(c, a)` and `(a, d)` (exposures 3, 2, 2, 1), the result contains `d` and is `(b, d)`. `(b, d)` and `(c, d)` tie at score 0.4723, and `b` comes first.
- **$AC_3$ (Obvious Pairs Skipped):** two items after two `(a, b)` (`P = 0.9888`, exposure 2 each) give `None`. The chain of Story 23.1 AC_2 (every `P` at least 0.9673, exposure 2 each) gives `None`.
- **$AC_4$ (A Tied Pair Stays First):** the tie of Story 23.2 AC_1 gives `(a, b)` at `P = 0.5` and `N_ab = 2`, ahead of `(a, c)` and `(b, c)`, which are asked once each.
- **$AC_5$ (k_min):** `k_min` of 1 raises `ValueError`. With `k_min` 3, two items after two `(a, b)` give `(a, b)`, not `None`.
- **$AC_6$ (Deterministic):** repeated calls on the same state return the same pair, and the inputs are equal to their copies afterwards.

---

## Story 23.4 — Termination and Budget

**Status:** Approved — implementation blocked pending Stage 16 baseline scope authorization.
**As** a maintainer, **I want** a tournament to stop on a declared confidence or a bounded budget, never before every item is exposed, **so that** the effort is capped and no item is ranked unseen.

### Acceptance Criteria:
- **$AC_0$ (Budget Range):** for a dict of five variances (as `laplace_variance` returns), budgets of 9 and 24 raise `ValueError` and 10 and 23 are accepted. For two, only 4 is accepted (3 and 5 raise). For three, 9 is accepted and 10 raises (`2 * 3 * log2 3 = 9.51`). For twenty, 39 and 173 raise and 40 and 172 are accepted.
- **$AC_1$ (Declared Threshold):** `tau` of 0, -1, NaN and infinity each raise `ValueError`, and `tau` has no default.
- **$AC_2$ (Variance Stop):** a dict of five variances whose largest value is 0.30, with `used` 12, budget 23 and `min_exposure` 2 give true at `tau` 0.30 and false at `tau` 0.2999.
- **$AC_3$ (Budget Stop):** a maximum variance of 5.0 at `tau` 0.30 with `used` 23, budget 23 and `min_exposure` 2 gives true. `used` 24 raises `ValueError`.
- **$AC_4$ (Exposure Before Any Stop):** `min_exposure` 1 with maximum variance 0.30 at `tau` 0.30 and `used` 12 gives false. `min_exposure` 1 with `used` equal to the budget (23) also gives false and raises nothing (R11 option B), because comparisons replayed from records need not have come from `next_pair`.
- **$AC_5$ (Other Validation):** fewer than two variances, a negative or NaN variance, a negative `used`, and `k_min` of 1 each raise `ValueError`.

---

## Story 23.5 — Tournament State and Answer Episodes

**Status:** Approved — implementation blocked pending Stage 16 baseline scope authorization.
**As** an auditor, **I want** the tournament state stored in the policy snapshot and every human answer kept as an ordinary episode, **so that** a ranking can be recomputed from what was asked and answered, with no new kind of record.

### Acceptance Criteria:
- **$AC_0$ (Fields):** `tournament_state` over `feat-auth`, `feat-storage`, `feat-caching` with three comparisons between `feat-auth` and `feat-storage` (two won by `feat-storage`) returns `item_ids`, `comparison_counts` of `{"feat-auth::feat-storage": 3}`, `latent_utilities`, `ranking_status`, `parameters` and `comparisons_used` 3. The key follows `item_ids` order, not the winner, and a pair never asked has no key.
- **$AC_1$ (Status):** the status is the first that holds, in this order: `converged` (every exposure at least 2 and the largest variance at or below `tau`), `exposure_unmet` (comparisons at the budget with an exposure below 2), `budget_exhausted` (comparisons at the budget), `no_informative_pair` (`exhausted` true), and `in_progress`. A state that reaches the budget with every exposure at least 2 and the largest variance at or below `tau` is `converged`. Over the three items above with budget 6, six comparisons between `feat-auth` and `feat-storage` leave `feat-caching` at exposure 0, and the status is `exposure_unmet`.
- **$AC_2$ (Separator Refused):** an item id `"x::y"` raises `ValueError`.
- **$AC_3$ (Storage Boundary):** the dict survives `json.dumps` and `json.loads` unchanged. A `PolicySnapshot` carrying it in `metadata["dueling_bandit"]` round-trips through an `InMemoryStore` with no new record type.
- **$AC_4$ (Answers From Episodes):** `comparisons_from_episodes` turns an episode whose `dueling_comparison` has this tournament, `pair` `[a, b]` and `winner` `b` into `(b, a)`. An episode of another tournament, with an unknown item, with a winner outside its pair, with a pair of one id twice, or with no `dueling_comparison` is skipped without error. An episode id offered twice gives one comparison. The order is first appearance, and the episodes are equal to their copies afterwards.
- **$AC_5$ (Human Answers Only):** answer episodes have `action_logprob` of `None`. A `ReinforceLearner.update` over them returns `episodes_used` 0 and leaves the logits unchanged. No function of `dueling.py` returns an `Episode` or a comparison it was not given.
- **$AC_6$ (Episode Identity And Adjudication):** a human answer recorded for task `rank-backlog` and tournament `rank-backlog-2026-11` has `task_id` `rank-backlog`, `metadata["dueling_comparison"]["tournament_id"]` set to the caller-supplied stable tournament id, and `metadata["feedback_status"]` set to `adjudicated` only after the human supplies the answer.

---

## Story 23.6 — The Synthetic Tournament (Maths Only)

**Status:** Approved — implementation blocked pending Stage 16 baseline scope authorization; measured results must be recorded from the implementation at Ingest.
**As** a maintainer, **I want** the whole loop run against known utilities, **so that** the parts are shown to work together, without any claim that the method saves effort.

### Acceptance Criteria:
- **$AC_0$ (Labelled):** the test module's docstring and its recorded output say `SYNTHETIC` and `NOT EVIDENCE`. They name HYP-AL-015 as untested (ADR-036; BRU-023-14).
- **$AC_1$ (The Loop):** the test repeats fit, variance, status and `next_pair` until the status is not `in_progress`. Answers come from `random.Random(20261026)`, one draw per comparison, and the first item of the pair wins when the draw is below `sigma` of its true utility minus the other's. Items `i1` to `i5` have true utilities `(1.5, 0.5, 0.0, -0.8, -1.2)`, with budget 23 and `tau` 1.0. The test asserts that the run ends in a status other than `in_progress` within 23 comparisons and that it never reaches `exposure_unmet`. It records the terminal status, the comparisons used and the fitted order; no prototype-specific terminal status or count is a golden expectation. For reference only, the FDD-023 prototype of the recommended options ended `no_informative_pair` after 11 comparisons in the order `i1` to `i5`.
- **$AC_2$ (Invariants Over Seeds):** for seeds 0 to 199 no run uses more than 23 comparisons, no run ends while an item has fewer than 2, and each run repeated gives the identical sequence of pairs. The test records, and does not assert, how often each status occurs and how often the fitted order equals the true order. The prototype recorded 181 `budget_exhausted`, 19 `no_informative_pair`, and the true order in 50 of 200 runs; these are not expected results for the implementation.
- **$AC_3$ (No Saving Claimed):** the recorded output shows the comparisons used beside `N(N-1)/2` (10 for five items) and `floor(2 N log2 N)` (23). It states that a run using more than 10 comparisons saved nothing against the exhaustive count.

---

## Story 23.7 — The Real-Data Check (No Recorded Judgments)

**Status:** Approved — implementation blocked pending Stage 16 baseline scope authorization.
**As** a maintainer, **I want** the engine pointed at the real backlog and the recorded episodes, **so that** the absence of real comparisons is shown, not assumed.

### Acceptance Criteria:
- **$AC_0$ (Real Source):** the items are the `## Story` headings of the epic files under `docs/user-stories/`, and the episodes are the committed files in `docs/policy-shapes/episodes/`. Both are listed with `git ls-files` (LL-037). The test records the counts it ran on and does not assert a fixed number (144 headings in 36 files and 187 episode files on 2026-11-09).
- **$AC_1$ (No Comparisons):** `comparisons_from_episodes` over those episodes returns no comparison for any tournament id.
- **$AC_2$ (What The Engine Would Ask):** with no comparison, the fit gives all-zero utilities, and `next_pair` returns the first two items in heading order. The budget range for the recorded `N` is printed (for 144 items: 288 to 2,064, against 10,296 exhaustive pairs).
- **$AC_3$ (Nothing Written):** no file under `docs/` and no store is changed by the test.
- **$AC_4$ (Labelled):** the result is recorded as a statement that no pairwise judgment exists yet. It makes no claim about the comparisons saved (BRU-023-14), and the docstring names the missing data: Menno's own comparisons of real items, each persisted as an answer episode.
