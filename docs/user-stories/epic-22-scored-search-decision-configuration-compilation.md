# Epic 22: Scored-Search Decision Configuration Compilation

**Source ADR:** [ADR-022](../adr/ADR-022-scored-search-decision-configuration-compilation.md) — Accepted (2026-10-28)  
**Source BRD/FDD:** [BRD-022](../project-docs/Business-Requirements/BRD-022-scored-search-decision-configuration-compilation.md) / [FDD-022](../project-docs/Functional-Design/FDD-022-scored-search-decision-configuration-compilation.md)  
**Status:** Approved (2026-10-30, Menno) — stories derived from Accepted ADR-022, BRD-022 and FDD-022; adjudicated via `approve-user-stories` (robust utility 0.731, episode `cc1804ea-6d96-4b82-8ce5-a3825680a03f`). Menno confirmed FDD-022 §4 (L1 to L8) on 2026-10-30. The epic number follows the source ADR number, as Epic 21 follows ADR-021.  

Seven stories build `src/agent_learning/weight_compiler.py`, the commands `policy-compile-weights` and `task-policy-weights-adopt`, the shape `approve-compiled-weights`, and the call in `task-policy-decide`. Each rule sits in exactly one story's criteria (LL-012). Contract tests are `tests/test_weight_objective.py` (22.1), `tests/test_weight_split.py` (22.2), `tests/test_weight_search.py` (22.3), `tests/test_weight_propose.py` (22.4), `tests/test_weight_apply.py` (22.5), `tests/test_weight_adopt.py` (22.6) and `tests/test_weight_real_data.py` (22.7). Searching the uncertainty penalty, the Nelder-Mead surrogate and k-fold validation are not stories (BRD-022 Out of Scope).

**Stories 22.1 to 22.7 follow the confirmed FDD.** Menno confirmed FDD-022 §4 (L1 to L8) on 2026-10-30, with L1 and L6 as the options that FDD states. ADR-022's body is not amended in this approval; FDD-022 §4 records the departures. No story depends on another epic.

Fixtures used by the criteria below. "The toy frame": criteria `c1`, `c2`, options `A` (supports 0.9 and 0.3) and `B` (0.4 and 0.8), one source per criterion at confidence 1.0, `uncertainty_penalty` 0. "The synthetic suite": 40 frames over criteria `c1`, `c2`, `c3` with supports drawn from `random.Random(20261026)`, each labelled by the real resolver under the hidden weights `(0.6, 0.3, 0.1)`, with `labeled_at` earlier than the proposal time. All are built in the tests and labelled synthetic. `evaluate`, `objective`, `coordinate_ascent` and `propose` take a snapshot whose actions are exactly the frame's options. The resolver rejects any other action space, and those functions do not read `criteria_weights` from the snapshot.

---

## Story 22.1 — Scoring a Weight Vector With the Real Resolver

**Status:** Ready  
**As** an auditor, **I want** a candidate scored by the real resolver and nothing else, **so that** a compiled weight is judged by the rule that will use it.

### Acceptance Criteria:
- **$AC_0$ (Weights Applied):** `with_weights` on the toy frame with `(0.7, 0.3)` returns a frame whose criteria weights are `0.7` and `0.3` in the original order; its constraints, options and evidence are equal to the original's; the original frame is equal to its copy afterwards.
- **$AC_1$ (Validation):** `with_weights` raises `ValueError` for a key set that differs from the criterion ids, a zero, negative, `nan` or infinite weight.
- **$AC_2$ (Predicted And Margin):** `evaluate` on the toy frame gives `predicted` `A` and margin 0.20 within 1e-9 for `(0.7, 0.3)`; `None` and margin 0.0 for `(0.5, 0.5)` (a tie that needs a person); `B` and margin 0.20 for `(0.3, 0.7)`.
- **$AC_3$ (Objective):** with label `A` and `beta` 0.1 the objective of the toy frame is 1.02 for `(0.7, 0.3)`, 0.0 for `(0.5, 0.5)` and 0.02 for `(0.3, 0.7)` within 1e-9; the objective of a set is the sum over its items.
- **$AC_4$ (Constraints Hold):** for a frame where option `B` is ruled out by a constraint, `evaluate` never returns `B` over a grid of weight vectors, and the margin ignores the ruled-out option.
- **$AC_5$ (Through The Resolver):** the test replaces `DecisionResolver.resolve` with a counting wrapper and finds one call per `evaluate`, as `resolve(snapshot, with_weights(...))`, where `snapshot` is the one passed to `evaluate`; the module has no other scoring path.
- **$AC_6$ (Pure):** `weight_compiler.py` imports nothing from `agent_learning.storage` and performs no file I/O.

---

## Story 22.2 — The Split and the Label Rule

**Status:** Ready  
**As** a maintainer, **I want** a reproducible hold-out and labels that predate the proposal, **so that** reported accuracy is honest.

### Acceptance Criteria:
- **$AC_0$ (Reproducible):** `split_holdout` on the synthetic suite with seed 7 returns the same two parts on every call and in a fresh process; a different seed returns a different split; the parts are disjoint and together equal the input.
- **$AC_1$ (Sizes):** a fraction of 0.3 on 40 items holds out 12; a fraction under 0.3 or over 0.5, a non-integer seed, and an input that would leave fewer than 5 items in either part each raise `ValueError`.
- **$AC_2$ (Order Independent):** shuffling the input list before the call does not change the parts.
- **$AC_3$ (Label Timing):** `propose` raises `ValueError` naming the item when any `labeled_at` equals or follows `proposed_at`, and accepts labels strictly earlier.
- **$AC_4$ (Held-Out Untouched):** a search run on the training part, with the held-out frames replaced by frames that raise on `resolve`, completes without calling the resolver on them.

---

## Story 22.3 — The Coordinate Ascent

**Status:** Ready  
**As** a maintainer, **I want** a deterministic search that keeps the weights valid, **so that** a result can be reproduced and trusted.

### Acceptance Criteria:
- **$AC_0$ (Valid Weights):** every weight vector the search evaluates, and the one it returns, is positive, at least the step 0.05, and sums to 1.0 within 1e-9; items whose frames have different criterion ids raise `ValueError`.
- **$AC_1$ (Not Worse):** the training objective of the returned weights is at least that of every start point, and never decreases from one accepted candidate to the next.
- **$AC_2$ (Recovers):** on the synthetic suite the returned weights are within 0.05 of `(0.6, 0.3, 0.1)` per criterion, and the training accuracy is 1.0.
- **$AC_3$ (Deterministic):** the same arguments give identical weights, counts and report on repeated calls and in a fresh process, and `weight_compiler.py` imports no random number source other than for the split.
- **$AC_4$ (Bounded):** the search stops after `max_sweeps` sweeps per start point or a sweep that accepts nothing, and the result reports `evaluations`, `sweeps` and `restarts`; `restarts` of 1 uses only the mean of the frames' own weights.
- **$AC_5$ (Time Recorded):** the test records the time of a default search on the synthetic suite and fails only if it exceeds 60 seconds; the recorded value is not claimed as a benchmark.

---

## Story 22.4 — Proposing Only a Real Improvement

**Status:** Ready  
**As** an approver, **I want** a proposal only when the held-out accuracy truly beats the weights in force, **so that** a frozen configuration is never changed for no gain.

### Acceptance Criteria:
- **$AC_0$ (Improvement):** on a suite whose frames were authored with weights far from the hidden ones, `propose` returns `CompiledWeights` with `holdout_accuracy` strictly above `baseline_holdout_accuracy`, and the report holds the seed, split sizes, evaluations, sweeps and restarts.
- **$AC_1$ (Strictly Greater):** when the compiled weights equal the baseline on the held-out part, `propose` returns `NoImprovement` with both accuracies, and the result has no weights.
- **$AC_2$ (Worse):** when the compiled weights score lower on the held-out part than the baseline, the result is `NoImprovement`.
- **$AC_3$ (Baseline Is As Stored):** the baseline uses each frame's own authored weights, unchanged, on the same held-out items.
- **$AC_4$ (Proposal File):** `policy-compile-weights` writes the proposal object of FDD-022 §2.3 for both outcomes, holds the policy id and version it compiled against, and writes nothing to the store.
- **$AC_5$ (Dataset Checks):** a dataset item whose label is not an action id of the active policy, or that lacks `frame`, `label` or `labeled_at`, makes `policy-compile-weights` exit non-zero and name the item. `weight_compiler.py` does not open the dataset file.
- **$AC_6$ (Frozen Weights):** `CompiledWeights.weights` is a `MappingProxyType`. Writing into it raises, and mutating the dict passed to the constructor leaves the stored weights unchanged.

---

## Story 22.5 — Applying Frozen Weights

**Status:** Ready  
**As** an operator, **I want** an online decision to use the adopted weights and run no search, **so that** a production decision stays deterministic and fast.

### Acceptance Criteria:
- **$AC_0$ (Applied):** `apply_compiled_config` on the toy frame with a snapshot whose `criteria_weights` are `{c1: 0.7, c2: 0.3}` returns a frame with those weights; with no `criteria_weights` it returns the frame unchanged.
- **$AC_1$ (Mismatch):** a snapshot whose weights have different criterion ids raises `ValueError`.
- **$AC_2$ (Decide Uses It):** `task-policy-decide` with a frame file and a snapshot carrying compiled weights resolves with the compiled weights, and with the stored weights when the snapshot has none; the result is the same as resolving `with_weights` directly.
- **$AC_3$ (No Search Online):** a count of calls into `coordinate_ascent` and `propose` during `task-policy-decide` is 0.
- **$AC_4$ (Resolver Unchanged):** `DecisionResolver` has no reference to `criteria_weights`.

---

## Story 22.6 — Adopting a Proposal by a Human Decision

**Status:** Ready  
**As** a maintainer, **I want** compiled weights to take effect only through a recorded human decision, **so that** a frozen configuration is never changed silently.

### Acceptance Criteria:
- **$AC_0$ (Shape):** `docs/policy-shapes/approve-compiled-weights.actions.json` holds `approve_compiled_weights`, `reject_compiled_weights` and `request_revision_before_decision`, and its complexity profile declares `requires_human_approval` true, so the router of FDD-021 pins it.
- **$AC_1$ (Needs An Approval Episode):** `task-policy-weights-adopt` without `--approval-episode`, or with an episode that does not exist, belongs to another task, or is not `adjudicated` and `accepted`, exits non-zero and writes nothing.
- **$AC_2$ (Adopts):** with a valid episode and an improved proposal for the active policy's id and version, it stores the next version of the policy with `criteria_weights` equal to the proposal's and `compiled_weights_provenance` holding the proposal hash, seed, accuracies, split sizes, label time range, approval episode id and adoption time; the earlier version is unchanged.
- **$AC_3$ (Refuses):** a proposal with `improved` false, a proposal for another policy id or version, or weights that fail `with_weights` validation exits non-zero and writes nothing.
- **$AC_4$ (Snapshot Only):** the store gains no record type, and the adoption changes nothing but the new snapshot.

---

## Story 22.7 — The Real-Data Regression Check

**Status:** Ready  
**As** a maintainer, **I want** the compiler run over the recorded decisions, **so that** the absence of any real disagreement is shown, not assumed.

### Acceptance Criteria:
- **$AC_0$ (Real Source):** the frames are the loadable files of `docs/policy-shapes/decision-frames/` grouped by task, with their labels from the adjudicated results and episodes; the counts per task are recorded in the test (48 frames and 97 results when ADR-022 was written, 106 frame files on 2026-10-29, so the test records what it ran on and asserts no fixed number).
- **$AC_1$ (Baseline Is Perfect):** for each task with at least `2 * MIN_PART` labelled frames the weights in force reproduce every recorded human-accepted action, so baseline accuracy is 1.0.
- **$AC_2$ (No Improvement):** `propose` on each such task returns `NoImprovement`, because accuracy cannot exceed 1.0.
- **$AC_3$ (Nothing Written):** the committed policy-shape files and store are equal to their earlier state after the run.
- **$AC_4$ (Labelled):** the result is recorded as a statement that the real history holds no disagreement and cannot show an improvement. It makes no claim that compiled weights are better (BRU-022-12), and the docstring names the missing data (decisions where a human disagreed with the resolver, with the label recorded before the proposal).
