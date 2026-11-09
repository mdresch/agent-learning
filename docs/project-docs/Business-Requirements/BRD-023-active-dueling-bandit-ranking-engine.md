# BRD-023: Active Dueling-Bandit Ranking Engine

**Source ADR:** [ADR-023](../../adr/ADR-023-active-dueling-bandit-ranking-engine.md) — Accepted (2026-10-28, Menno); Episode `723b7f27-65bd-496f-ab86-130da1198f3b`  
**Governing Baseline:** `PMP-BL-v1.1.0` (approved 2026-11-08); cycle `CYC-001` (ADR-035, Accepted). Epic 23 is not among the epics that baseline authorizes (PMP §1 and §5 name Epics 14, 16, 18, 21, 22 and 38). Building it needs a scope change through change control (FDD-023 §7 item 1).  
**Status:** Draft (2026-11-09) — derived from Accepted ADR-023; not yet adjudicated through `approve-brd`.  
**Stakeholders:** Menno (Sponsor/PM/maintainer, and today the only adjudicator whose comparisons would be real data); SDK adopters who rank a backlog, a portfolio or a set of capabilities from head-to-head judgments; auditors who must see why one item ranks above another and how sure the ranking is  

## Business Need

To rank N items by head-to-head judgment, the exhaustive approach asks every unique pair: N(N-1)/2 questions, which is 45 for 10 items, 190 for 20 and 435 for 30. Asking pairs at random wastes many of those questions on pairs whose order is already obvious. ADR-023 decides an engine that fits a Bradley-Terry utility to the answers so far and then asks about the pair whose outcome is closest to 50:50 and that has been asked least often. It stops when a Laplace approximation of the utilities' variance is small enough, or when a budget of at most 2N log2 N questions is spent. The engine only chooses which pair to ask. A human gives every answer. The ADR builds on the Bradley-Terry learner of ADR-018, whose loss and gradient code already exists in `src/agent_learning_ext/learners/pairwise.py`. Nothing is built. The repository holds no recorded pairwise judgment, so HYP-AL-015 (the comparisons saved) is untested.

## Business Rules (BRU)

- **BRU-023-01 (Bradley-Terry Model):** The probability that item i beats item j is `sigma(lambda_i - lambda_j)`. The utilities are fitted by maximizing the L2-penalized log-likelihood of the recorded outcomes, and they are normalized to sum to 0 (ADR-023 §4.1).
- **BRU-023-02 (Regularization Floor):** The penalty weight `lambda_reg` is at least 0.01, and a smaller value is refused. With it, an item with no win or no loss still gets a finite utility (ADR-023 §4.1, Invariant 6).
- **BRU-023-03 (Monotone Fit, Honest Result):** The fit is a Minorization-Maximization iteration whose penalized log-likelihood never decreases. A fit that stops at its iteration cap says that it did not converge (ADR-023 §4.1; FDD-023 R2, R3).
- **BRU-023-04 (Computational Bound, Open):** For N ≤ 100 the fit time on CPU is measured, not assumed, and is held to a bound. ADR-023 states two bounds: under 5 ms in §4.1 and under 50 ms in Invariant 2. The FDD-023 prototype measured 98 ms, so neither holds today. Which bound applies is open until Menno decides FDD-023 R4. Until then the only bound is a provisional loose one (ADR-023 §4.1, Invariant 2; FDD-023 R4).
- **BRU-023-05 (Laplace Uncertainty):** The variance of each utility is the Laplace approximation `[H^-1]_ii`, with `H` the Hessian of the negative penalized log-likelihood at the fitted utilities. `H` is positive definite because `lambda_reg > 0`. Which variance the stopping rule reads is stated in FDD-023 (R5), because the raw diagonal can never fall below `1 / (N * lambda_reg)` (ADR-023 §4.3).
- **BRU-023-06 (Information-Gain Selection):** The next pair is the one that minimizes `|P(i > j) - 0.5| * sqrt(N_ij + 1)`, where `N_ij` counts how often the pair was already asked. Ties are broken by a fixed, stated rule, so the same state always gives the same pair (ADR-023 §4.2, Invariant 1; FDD-023 R6).
- **BRU-023-07 (Minimum Exposure):** Until every item has taken part in at least `k_min = 2` comparisons, only pairs that include an under-exposed item are asked. No item is given a final rank, and the tournament is not reported converged, before every item reaches `k_min`. A `k_min` below 2 is refused (ADR-023 §4.2, Invariant 5; FDD-023 R7, R11).
- **BRU-023-08 (Obvious Pairs Skipped):** Once every item meets the exposure rule, a pair whose predicted outcome is above 0.95 in either direction is not asked. When every pair is obvious, there is no next pair, and the tournament ends with a status that says so, which is not the same as converged (ADR-023 §4.2; FDD-023 R8).
- **BRU-023-09 (Declared Threshold):** The tournament halts when the largest variance is at or below a threshold `tau_rank_confidence` or when the budget is spent. The threshold has no default. A human declares it, because no calibrated value exists (ADR-023 §4.3).
- **BRU-023-10 (Budget Cap):** The budget is at most `floor(2 N log2 N)` comparisons. It is also at least `k_min * N`, the most comparisons the exposure rule can need when the engine chooses every pair, so in that case the exposure rule can always be met within it. A budget outside that range is refused. Comparisons chosen some other way, such as replayed or manual records, can spend the budget before every item is exposed. That case is reported, not hidden (ADR-023 §4.3, Invariant 5; FDD-023 R9, R11).
- **BRU-023-11 (Storage Boundary):** The tournament state lives in `PolicySnapshot.metadata["dueling_bandit"]` with the fields of ADR-023 §4.4. Each human answer is recorded as a standard `Episode`. No new `LearningStore` record type is added, and the module imports nothing from `agent_learning.storage` (ADR-023 §4.4, §4.5, Invariant 3; ADR-002; FDD-023 R10).
- **BRU-023-12 (Authority Boundary):** Pair selection is a `DecisionAuthority.LOW` act. The engine never supplies or guesses an outcome. Every outcome comes from a human adjudicator, and an answer episode is never used as a policy-gradient sample (ADR-023 Invariant 4; ADR-001).
- **BRU-023-13 (Upstream Untouched, Existing Code Reused):** The new code lives under `src/agent_learning_ext/`. It reuses the Bradley-Terry loss and gradient of `agent_learning_ext.learners.pairwise` rather than a second copy, and `src/agent_learning/` gains no line (PMP §4 and Invariant 6; ADR-023 §8 reference to ADR-018; FDD-023 R1).
- **BRU-023-14 (No Claim Of Effectiveness):** No pairwise judgment is recorded, so HYP-AL-015 stays untested. A synthetic tournament may check only the maths and is labelled synthetic, not evidence. For N ≤ 17 the budget cap is larger than the exhaustive count (66 against 45 for N = 10), so the cap alone saves nothing there. Any saving must come from stopping early (ADR-023 §4.5 test data, §6; ADR-036).

## Stakeholder Success Metrics

| Metric | Target |
|---|---|
| Two-item oracle | a fit of one win of `a` over `b` at `lambda_reg` 0.01 gives utilities `(1.9570, -1.9570)` within 1e-4, equal to the closed-form root of `sigma(-2t) = 0.01 t` |
| Finite and centred | 100% of fits finite for an unbeaten and a winless item; the utilities sum to 0 within 1e-9 |
| Monotone | 0 tested iterations in which the penalized log-likelihood decreases by more than 1e-12 |
| Regularization floor | 100% of `lambda_reg < 0.01` refused |
| Variance arithmetic | the Laplace variances of the worked cases in FDD-023 §3 equal the hand-computed values within 1e-4 |
| Selection | on every worked case of FDD-023 §3 `next_pair` returns the stated pair; 0 differences between repeated calls on the same state |
| Exposure | 0 tournaments reported converged, and 0 pairs skipped as obvious, while an item has fewer than 2 comparisons |
| Budget | 100% of budgets above `floor(2 N log2 N)` or below `k_min * N` refused; 0 tournaments that use more comparisons than their budget |
| Threshold | 0 tournaments started without a declared `tau_rank_confidence` |
| Time | the recorded fit time for N = 100 with 1,328 comparisons, held to the bound FDD-023 R4 settles; until then to a provisional 5 s |
| Storage boundary | 0 new record types; 0 imports from `agent_learning.storage` in the module; 0 lines changed under `src/agent_learning/` |
| Authority | 0 outcomes produced by the engine; 0 answer episodes consumed by `ReinforceLearner` |

## Out of Scope

- Measuring HYP-AL-015. It needs Menno's own comparisons of the real backlog, and none are recorded.
- A command, prompt or user interface that presents a pair to a human and records the answer. ADR-023 names the module only; how an answer reaches the store is FDD-023 R10 and §7 item 3.
- Integration with ADPA's `PairwiseComparisonMatrix.tsx` or its prioritization service (Ideation-Document HYP-AL-015).
- Calibrating `tau_rank_confidence`.
- Handling strong non-transitive cycles beyond the L2 penalty (ADR-023 §6).
- Ties or "no preference" answers, rankings of more than two items at once, and contextual preferences.
- Wiring the engine into `task-policy-decide` or any other existing command.
