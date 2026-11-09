---
name: weight-compiler
description: Guidance for Scored-Search Decision Configuration Compilation over criteria weights (ADR-022, Epic 22).
---

# Skill: weight-compiler (agent-learning)

## Overview
This skill governs Scored-Search Decision Configuration Compilation (`src/agent_learning_ext/weight_compiler.py`). Grounded in derivative-free black-box optimization, this offline utility optimizes Bayesian criteria weights against historical labeled decision frames using coordinate ascent and the real `DecisionResolver`, freezing compiled configurations for zero-overhead runtime deployment.

## Governing Specifications & Contracts
- **Architecture:** [`docs/adr/ADR-022-scored-search-decision-compilation.md`](../../docs/adr/ADR-022-scored-search-decision-compilation.md)
- **Business Requirements:** [`docs/project-docs/Business-Requirements/BRD-022-scored-search-decision-configuration-compilation.md`](../../docs/project-docs/Business-Requirements/BRD-022-scored-search-decision-configuration-compilation.md)
- **Functional Design:** [`docs/project-docs/Functional-Design/FDD-022-scored-search-decision-configuration-compilation.md`](../../docs/project-docs/Functional-Design/FDD-022-scored-search-decision-configuration-compilation.md)
- **User Stories:** [`docs/user-stories/epic-22-scored-search-decision-configuration-compilation.md`](../../docs/user-stories/epic-22-scored-search-decision-configuration-compilation.md)
- **Test Contracts:**
  - `tests/test_weight_objective.py` (Story 22.1 — Scoring a Weight Vector With the Real Resolver)
  - `tests/test_weight_split.py` (Story 22.2 — The Split and the Label Rule)
  - `tests/test_weight_search.py` (Story 22.3 — The Coordinate Ascent)
  - `tests/test_weight_propose.py` (Story 22.4 — Proposing Only a Real Improvement)
  - `tests/test_weight_apply.py` (Story 22.5 — Applying Frozen Weights)
  - `tests/test_weight_adopt.py` (Story 22.6 — Adopting a Proposal by a Human Decision)
  - `tests/test_weight_real_data.py` (Story 22.7 — The Real-Data Regression Check)

## Load-Bearing Constraints & Invariants
1. **Upstream Fork Collision Protection (Invariant 6):**
   - Resides in `src/agent_learning_ext/weight_compiler.py` and is re-exported via `src/agent_learning_ext`.
   - `src/agent_learning/` remains 100% byte-for-byte untouched upstream code (0 lines diff).
2. **Pure Module Boundary & Storage Decoupling (AC_6, BRU-022-10):**
   - Zero imports from `agent_learning.storage` or `agent_learning_ext.storage`.
   - Zero file I/O operations (no `open`, no `Path.read_*` or `Path.write_*`).
3. **Scored Exclusively via the Real Resolver (AC_5, BRU-022-02):**
   - Every candidate configuration is evaluated strictly through `DecisionResolver.resolve(snapshot, with_weights(frame, weights))`.
   - The module contains no alternate scoring path or heuristic shortcuts.
4. **Hard Constraint Inviolability (AC_4, BRU-022-04):**
   - Ruled-out options never win under any candidate weight vector.
   - Robust decision margin ignores ruled-out options and reflects separation between viable options only.
5. **Simplex Invariant & Step Floor (AC_1, BRU-022-03, FDD L2):**
   - Compiled weights must be strictly positive with a floor of one step (`STEP_DEFAULT = 0.05`), finite, and sum to 1.0 within 1e-9.
   - Non-positive, non-finite, `nan`, or key-mismatched weights raise `ValueError`.
6. **Multi-Objective Loss Formulation (AC_2, AC_3, ADR-022 §4.1):**
   - Objective: $\sum [\mathbb{I}[\hat{y} = y^*] + \beta \cdot \text{Margin}]$.
   - Default margin weight $\beta = 0.1$.
   - $\hat{y}$ awards credit for `resolved` and `needs_user_feedback` (reasoned recommendation awaiting human approval), returning `None` for ties or unevidenced states.
7. **Reproducible Disjoint Hold-Out (AC_0, AC_1, AC_2, BRU-022-05):**
   - `split_holdout(items, *, fraction=0.3, seed)` returns reproducible disjoint partitions that sum to the input collection.
   - Requires `0.3 <= fraction <= 0.5`, integer seed, and $\ge \text{MIN\_PART}$ (5) items in both partitions, raising `ValueError` otherwise.
   - Sorts items deterministically prior to shuffling (`random.Random(seed)`), ensuring permutation invariance.
8. **Label Timing Validation (AC_3, BRU-022-06):**
   - `validate_label_timing(items, proposed_at)` validates that every item's `labeled_at` is strictly earlier than `proposed_at`. If `labeled_at >= proposed_at`, it raises `ValueError` naming the item.
9. **Held-Out Partition Untouched (AC_4):**
   - Offline coordinate ascent runs exclusively on the training partition without invoking the resolver on held-out items during search.
10. **Coordinate Ascent Monotonicity & Bounded Search (AC_0, AC_1, AC_4):**
    - `coordinate_ascent(train, snapshot, *, step=0.05, restarts=5, max_sweeps=20, beta=0.1)` optimizes weights deterministically over start points (frames' mean, uniform, individual criterion spikes).
    - Every candidate weight vector floored at `step`, normalized to sum to 1.0; candidate rejected if any weight `< step`.
    - Every accepted candidate strictly raises objective by $> 10^{-12}$.
    - Search stops when a sweep accepts no candidate or reaches `max_sweeps`.
11. **Strict Hold-Out Improvement & Proposal Contracts (AC_0, AC_1, AC_2, AC_6, BRU-022-07):**
    - `propose(train, holdout, snapshot, *, proposed_at, ...)` returns `CompiledWeights` ONLY if `holdout_accuracy > baseline_holdout_accuracy` strictly; otherwise returns `NoImprovement`.
    - Baseline evaluates each frame's own criteria weights on held-out items.
    - `policy-compile-weights` writes proposal JSON without touching the policy store.
    - `CompiledWeights.weights` is immutable `MappingProxyType`.
12. **Runtime Weight Application & Zero Online Search (AC_0, AC_2, AC_3, AC_4, FDD L1):**
    - `apply_compiled_config(frame, snapshot)` replaces a frame's criteria weights with `snapshot.metadata["criteria_weights"]` via `with_weights()`.
    - Returns frame unchanged when snapshot lacks `criteria_weights`.
    - `task-policy-decide` applies weights transparently at runtime; zero search overhead online (`coordinate_ascent` calls = 0).
    - `DecisionResolver` remains 100% untouched without reference to `criteria_weights`.
13. **Human-Adjudicated Adoption (AC_0, AC_1, AC_2, AC_3, AC_4, FDD L6):**
    - `docs/policy-shapes/approve-compiled-weights.actions.json` defines `approve_compiled_weights`, `reject_compiled_weights`, `request_revision_before_decision`.
    - Profile declares `requires_human_approval: true`, ensuring router pins task to FULL.
    - `task-policy-weights-adopt` enforces an adjudicated and accepted episode belonging to `approve-compiled-weights`.
    - Stores new policy version with `criteria_weights` and `compiled_weights_provenance` (proposal hash, seed, accuracies, split sizes, label time range, approval episode id, adoption time).
    - Store gains no new record type; earlier policy versions remain unchanged.
14. **Real-Data Regression Check (Story 22.7 AC_0 to AC_4, BRU-022-12):**
    - `tests/test_weight_real_data.py` runs the compiler over the committed `docs/policy-shapes/decision-frames/` and the adjudicated results; it records the counts it ran on and asserts no fixed number.
    - On tasks with at least `2 * MIN_PART` labelled frames the baseline accuracy is 1.0, so `propose` returns `NoImprovement`. This is a statement that the history holds no disagreement, never evidence that compiled weights are better.
    - Missing data to show an improvement: decisions where a human disagreed with the resolver, with the label recorded before the proposal.
    - The check writes nothing (policy-shape files unchanged) and the test imports nothing from `agent_learning.storage`. Empty collections return empty results without raising.
    - `_resolve_label` initializes `labeled_at` for each candidate source before parsing, then replaces it for recognized source types. This is defensive clarity for the value returned on successful paths; an exception not caught by `_LOAD_ERRORS` still propagates and does not fall through to the return.
