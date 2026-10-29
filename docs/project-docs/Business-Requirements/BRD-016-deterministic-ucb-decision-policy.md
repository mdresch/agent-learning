# BRD-016: Deterministic Upper Confidence Bound (UCB) Decision Policy

**Source ADR:** [ADR-016](../../adr/ADR-016-deterministic-ucb-decision-policy.md) — Accepted (2026-10-28)  
**Governing Baseline:** none approved yet; cycle `CYC-001` (ADR-035, Accepted)  
**Status:** Approved (2026-10-29, Menno) — derived from Accepted ADR-016; adjudicated via `approve-brd` (robust utility 0.741, episode `fac58260-2fff-4b3d-9709-ab56c2774e6c`).  
**Stakeholders:** Menno (Sponsor/PM/maintainer); SDK adopters who run low-authority policies; auditors who must replay a decision and get the same action  

## Business Need

An auditor who replays a historical decision must see the same action chosen. A softmax or Thompson policy draws random numbers, so replay needs the seed kept and restored (ADR-015). A policy gradient learner also needs a learning rate, a baseline and an entropy weight tuned. ADR-016 decides a second low-authority policy that selects by an upper confidence bound on each action's reward: a function of the stored counts only, with no random number at any step. The repository already computes a Wilson interval for autonomy gating (ADR-003); the same mathematics is reused for selection. Nothing is built yet.

## Business Rules (BRU)

- **BRU-016-01 (Absolute Determinism):** Given a fixed `PolicySnapshot`, `choose` returns the same action every time. The module generates no random number and does not import `random` (ADR-016 §4.2, Invariant 1).
- **BRU-016-02 (Deterministic Tie-Break):** Equal upper bounds are resolved first by the higher pull count, then by the lexicographically smaller `action.id` (ADR-016 §4.2, Invariant 2).
- **BRU-016-03 (Two Variants):** The `standard` variant scores `mean + c * sqrt(2 ln t / N)` with `c = sqrt(2)` by default. The `wilson` variant scores the upper bound of the Wilson interval at `z = 1.96`. The variant is stored in the snapshot (ADR-016 §4.1, §4.3).
- **BRU-016-04 (Unexplored First):** An action with no pulls has an infinite upper bound in both variants, so every action is pulled once before any is pulled twice (ADR-016 §4.1, §6 Negative).
- **BRU-016-05 (Reward Scale):** The SDK's `Reward.value` lies in [-1, 1]. It is mapped to [0, 1] by `(value + 1) / 2` before it is counted, in one place, because both bounds assume a [0, 1] reward (FDD-016 E1; the same mapping as BRU-015-04).
- **BRU-016-06 (Wilson Reuse):** The Wilson upper bound is computed from the existing `autonomy.wilson_lower_bound` through `WilsonUpper(k, N) = 1 - WilsonLower(N - k, N)`, so the policy and the autonomy gates cannot drift apart (ADR-016 §4.4).
- **BRU-016-07 (Storage Boundary):** Per-action statistics live in `PolicySnapshot.metadata["action_statistics"]`. Zero new `LearningStore` record types (ADR-016 Invariant 3; ADR-002).
- **BRU-016-08 (Low Authority Only):** The policy operates under `DecisionAuthority.LOW`. It never grants autonomy (ADR-016 Invariant 4; ADR-001).
- **BRU-016-09 (Stays Out Of REINFORCE):** A UCB episode never trains `ReinforceLearner`. It carries no behaviour probability, and a log-probability of 0.0 would present it to REINFORCE as a softmax pick with probability 1 (FDD-016 E2; ADR-001 §4.5).
- **BRU-016-10 (Counted Once):** An episode adds to the statistics at most once, however many times it is offered to the learner. The training runner re-queries recent episodes on every run, so a counter that adds on each pass would count the same episode repeatedly. The snapshot keeps the unique ids of the episodes already counted, and the learner skips any episode whose id is in it (FDD-016 E6).
- **BRU-016-11 (No Claim Of Effectiveness):** The first evidence is a consistency check on the recorded positive-only history. It does not claim UCB decides better than REINFORCE. That needs a low-authority policy with failures, which does not exist (HYP-AL-009; ADR-016 §4.4).

## Stakeholder Success Metrics

| Metric | Target |
|---|---|
| Determinism | 100% of tested snapshots give the same action across repeated calls and across fresh processes; 0 imports of `random` in the module (static check) |
| Formula | `standard` scores match hand-computed UCB1 values to 1e-9; `wilson` scores match the closed form to 1e-9 on every tested case |
| Reuse | the identity `WilsonUpper(k, N) = 1 - wilson_lower_bound(N - k, N)` holds to 1e-12 on a grid of counts, including fractional `k` |
| Tie-break | 100% of tested ties resolve by pull count then action id |
| Exploration | an unpulled action is always chosen before any pulled one |
| Scale | 100% of rewards outside [-1, 1] or non-finite rejected; -1 maps to 0, 0 to 0.5, +1 to 1 |
| Counted once | feeding the same episodes to the learner twice leaves the statistics as after the first time; an episode whose reward arrives after newer episodes were counted is still counted exactly once |
| Mean consistent | `mean_reward` equals `cumulative_reward / pull_count` within 1e-9 for every stored action; a snapshot where it differs is rejected |
| Stays out of REINFORCE | 0 UCB episodes consumed by `ReinforceLearner` |
| Storage boundary | 0 new record types; 0 imports from `agent_learning.storage` in the module |

## Out of Scope

- Showing that UCB decides better than REINFORCE or Thompson sampling. It needs a low-authority policy with at least 100 scored episodes that include failures; none exists. Recorded as a data gap, not as a story.
- Contextual or continuous-feature variants (ADR-016 §6 Negative).
- Sliding-window or discounted statistics for non-stationary rewards.
- Changing `ReinforceLearner`, the full-authority resolver, or the meaning of the autonomy gates.
- Wiring UCB into the CLI's `task-policy-decide`.
