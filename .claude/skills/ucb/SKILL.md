---
name: ucb
description: Guidance for the Deterministic Upper Confidence Bound (UCB) decision policy and learner in agent-learning (ADR-016, Epic 16).
---

# Skill: ucb (agent-learning)

## Overview
The Deterministic Upper Confidence Bound (UCB) decision policy guarantees 100% deterministic, audit-replayable action selection without stochastic sampling or PRNG seeds. It supports standard UCB1 and Wilson score upper-bound variants, maintaining action statistics within `PolicySnapshot.metadata` and sharing core statistics management with other count-based policies. This skill covers `src/agent_learning_ext/policy/ucb.py`, `src/agent_learning_ext/policy/action_statistics.py`, and `src/agent_learning_ext/learners/ucb.py`.

## Governing Specifications & Contracts
- **Architecture:** [`docs/adr/ADR-016-deterministic-ucb-decision-policy.md`](../../docs/adr/ADR-016-deterministic-ucb-decision-policy.md)
- **Business Requirements:** [`docs/project-docs/Business-Requirements/BRD-016-deterministic-ucb-decision-policy.md`](../../docs/project-docs/Business-Requirements/BRD-016-deterministic-ucb-decision-policy.md)
- **Functional Design:** [`docs/project-docs/Functional-Design/FDD-016-deterministic-ucb-decision-policy.md`](../../docs/project-docs/Functional-Design/FDD-016-deterministic-ucb-decision-policy.md)
- **User Stories:** [`docs/user-stories/epic-16-deterministic-ucb-decision-policy.md`](../../docs/user-stories/epic-16-deterministic-ucb-decision-policy.md)
- **Test Contracts:**
  - `tests/test_ucb_scores.py` (Story 16.1: The Scores)
  - `tests/test_ucb_policy.py` (Story 16.2: Choosing Deterministically; Story 16.3: Snapshot Integration)
  - `tests/test_action_statistics.py` (Story 16.3 & 16.4: Shared Statistics Module)
  - `tests/test_ucb_learner.py` (Story 16.4: Counting Each Episode Once)
  - `tests/test_ucb_reinforce_guard.py` (Story 16.5: Staying Out of REINFORCE)
  - `tests/test_ucb_positive_only.py` (Story 16.6: Positive-Only Check, HYP-AL-009)

## Load-Bearing Constraints & Invariants
1. **Absolute Determinism:** Zero random numbers are generated. Static checks enforce that `policy/ucb.py` and `learners/ucb.py` contain no `import random` or calls into `random`.
2. **Upstream Fork Purity (Invariant 6):** All custom classes, policies, and learners reside under `src/agent_learning_ext/`, leaving `src/agent_learning/` completely pristine (0 lines diff against upstream).
3. **Standard Library Purity (Invariant 4):** Standard library modules only (`math`, `dataclasses`, `typing`, `collections.abc`, `json`, `ast`). Zero imports from `agent_learning.storage` or external dependencies.
4. **Scoring Variants:**
   - `standard`: $\bar{X}_a + c \sqrt{\frac{2 \ln t}{N_a}}$ with $c = \sqrt{2}$ default (`C_DEFAULT`). Total $t=1$ gives bonus 0.
   - `wilson`: $1 - \text{wilson\_lower\_bound}(N_a - k_a, N_a, z=1.96)$ by symmetry where $k_a = \text{cumulative\_reward}$.
5. **Unexplored Actions:** Any action with $N_a = 0$ scores `math.inf` in both variants, enforcing initial round-robin exploration.
6. **Deterministic Tie-Breaking:** Two actions with equal bounds resolve to:
   - Higher empirical pull count $N_a$.
   - Lexicographically smaller `action.id`.
7. **Snapshot Metadata Contract:**
   ```json
   {
     "policy_type": "ucb",
     "ucb_variant": "wilson",
     "exploration_constant": 1.4142135623730951,
     "action_statistics": {
       "action_id": {"pull_count": 10, "cumulative_reward": 8.0, "mean_reward": 0.8}
     },
     "consumed_episode_ids": ["ep-001", "ep-002"]
   }
   ```
   `mean_reward` must equal `cumulative_reward / pull_count` within 1e-9.
8. **Counted-Once Semantics:** `consumed_episode_ids` tracks processed episodes so re-queried or batch episodes are counted exactly once.
9. **Decision Record:** `Episode.metadata["ucb"]` stores `variant`, `exploration_constant`, `total_pulls`, `chosen`, and `scores` (with `null` for `math.inf` to maintain JSON validity).
10. **REINFORCE Isolation:** `Decision.logprob` is strictly `None` so that `ReinforceLearner` skips deterministic UCB episodes.
11. **UCBPolicy Interface:** Subclasses `Policy`. `choose(state=None)` evaluates `ucb_scores` across all actions, selects the action with the maximum bound (tie-breaking by higher pull count, then lexicographically smaller `action.id`), returns `Decision` with `logprob=None` and one-hot probabilities. `last_decision_record()` returns a deep copy of the FDD-016 §2.3 record (`None` before first choose). `apply_update` raises `TypeError("use UCBLearner")`. `choose` leaves the snapshot unmodified.
12. **Snapshot Lifecycle & Delegation:** `UCBPolicy.from_actions` initializes an initial zeroed policy snapshot (`pull_count=0`, `cumulative_reward=0.0`, `mean_reward=0.0`, `consumed_episode_ids=[]`). `UCBPolicy.from_snapshot` delegates all statistics and episode ID validation to `policy/action_statistics.py:read_statistics` (AC_2); `ucb.py` holds no duplicate copy of statistics validation rules. A missing action in snapshot statistics reads as zero pulls (0, 0.0, 0.0). UCB modules import nothing from `agent_learning.storage`.
13. **Learner Lifecycle & Ingestion (Story 16.4):** `UCBLearner(Learner)` implements `update(policy, episodes, rewards)`. It indexes the newest `RewardSource.AGGREGATE` reward per episode and validates that reward values are finite and within $[-1.0, 1.0]$. It filters episodes for `selection_basis == "ucb"`, `action_id` within the action space, and matching aggregate reward. Offered items are passed directly to `policy/action_statistics.py:add_rewards`, mapping $r = (\\text{value} + 1) / 2$, which updates `pull_count`, `cumulative_reward`, and `mean_reward` in place, appends to `consumed_episode_ids`, and deduplicates across past and present calls. When usable episodes exist, `update` advances snapshot version (`policy.update_statistics`), records `episodes_seen`, and returns `LearnerResult` with `episodes_used`, `mean_reward`, `consumed_inputs`, and `extra` (`statistics_before`, `statistics_after`). When no usable episodes exist, it leaves policy state and version completely unchanged, returning `episodes_used=0`. Non-UCB policies raise `TypeError`.
