# ADR 016: Deterministic Upper Confidence Bound (UCB) Decision Policy

## 1. Executive Brief
In mission-critical autonomous governance, regulatory compliance and audit repeatability mandate that decision selection be **100% deterministic**. While reinforcement learning algorithms such as REINFORCE (ADR-001) and Thompson sampling (Methodology #9) rely on stochastic pseudo-random action sampling, stochasticity creates operational liability: re-evaluating the identical state with a different random seed can produce conflicting actions.

This ADR introduces the **Deterministic Upper Confidence Bound (UCB) Decision Policy** (Methodology #10 from `Ideation-Document.md` §2.1, addressing `HYP-AL-009`). By combining empirical mean rewards with deterministic confidence bounds (integrating with the repo's existing Wilson score calculator), UCB guarantees optimal balance of exploration and exploitation without gradient hyperparameters, entropy tuning, or stochastic seed dependencies.

## 2. Status
**Accepted (2026-10-28, Menno)** — Derived from `Ideation-Document.md` §2.1 (Methodology #10) and `HYP-AL-009`. Approved as a design through `approve-adr` (robust utility 0.697, expected utility 0.774; Episode `dcf700e1-6a3d-4e90-877b-0c2661b10878`). Amazon Q reviewed this text in PR #37. Nothing is built; the gaps named in the code-design section stay open.

## 3. Context & Problem Statement
- **The Audit Replay Liability of Stochastic Sampling:** In safety-critical agent systems, an auditor must be able to replay a historical decision and observe the exact same action chosen. When policies use softmax exploration ($\pi(a) \propto e^{\theta_a / \tau}$) or random draws, determinism requires preserving and restoring PRNG states across sessions.
- **The Hyperparameter Overhead of Policy Gradients:** REINFORCE requires careful tuning of learning rates ($\alpha$), baseline moving averages, and entropy regularization coefficients to prevent premature convergence or policy collapse.
- **The Wilson Score Precedent:** The repository already computes Wilson score confidence intervals for autonomy threshold gating (ADR-003). Extending this mathematics directly into action selection provides a unified, deterministic framework.

## 4. Technical Decision

### 4.1 Algorithmic Formulation
For each action $a \in A$, let:
- $N_a$ be the pull count of action $a$.
- $\bar{X}_a$ be the empirical mean reward of action $a$: $\bar{X}_a = \frac{1}{N_a} \sum_{i=1}^{N_a} r_{a, i}$, with each $r_{a,i} \in [0, 1]$. The SDK's `Reward.value` lies in $[-1, 1]$, so it is mapped by $r = (\text{value} + 1) / 2$ first.
- $t = \sum_{a \in A} N_a$ be the total decision count across all actions.

#### Standard UCB1 Variant:
$$a^* = \arg\max_{a \in A} \left[ \bar{X}_a + c \cdot \sqrt{\frac{2 \ln t}{N_a}} \right]$$
Where $c > 0$ is the exploration parameter (default $c = \sqrt{2}$). If $N_a = 0$, action $a$ is assigned an infinite upper bound, enforcing initial round-robin exploration.

#### Wilson-UCB Variant (Bounded Binary/Unit Rewards):
When rewards are bounded $r \in [0, 1]$, action selection leverages the upper bound of the Wilson score interval:
$$a^* = \arg\max_{a \in A} \text{WilsonUpper}(k_a, N_a, z = 1.96)$$
$$\text{WilsonUpper}(k_a, N_a, z) = \frac{\hat{p} + \frac{z^2}{2N_a} + z \sqrt{\frac{\hat{p}(1 - \hat{p})}{N_a} + \frac{z^2}{4N_a^2}}}{1 + \frac{z^2}{N_a}}$$
Where $\hat{p} = \bar{X}_a$.

### 4.2 Deterministic Tie-Breaking
When two actions yield identical upper bounds, ties are broken deterministically by:
1. Higher empirical pull count $N_a$.
2. Lexicographically smaller action identifier `action.id`.
Zero random numbers are generated at any stage of execution.

### 4.3 Policy Snapshot State Contract
The policy state is stored within standard `PolicySnapshot.metadata`:
```python
{
    "policy_type": "ucb",
    "ucb_variant": "wilson",  # "standard" | "wilson"
    "exploration_constant": 1.414,
    "action_statistics": {
        "action_id_1": {"pull_count": 42, "cumulative_reward": 37.5, "mean_reward": 0.8928},
        "action_id_2": {"pull_count": 15, "cumulative_reward": 10.0, "mean_reward": 0.6667}
    },
    "consumed_episode_ids": ["ep-0001", "ep-0002"]
}
```
`mean_reward` always equals `cumulative_reward / pull_count` and is recomputed on every update. `consumed_episode_ids` lists the unique ids of the episodes already counted; the learner skips any episode whose id is in it, because the training runner re-queries recent episodes on every run and a counter would otherwise count the same episode again (FDD-016 E6).

### 4.4 Code design and test data
Design only: nothing below is built, and the signatures are the contract an FDD must confirm or change.
Module `src/agent_learning/policy/ucb.py`, implementing `Policy`, plus `UCBLearner(Learner)`.

```python
def ucb_scores(stats: Mapping[str, ActionStats], total: int, *,
               variant: str = "wilson", c: float = 2 ** 0.5) -> dict[str, float]: ...
class UCBPolicy(Policy):
    def choose(self, state=None) -> Decision: ...   # no RNG; probabilities one-hot, logprob None
class UCBLearner(Learner):
    def update(self, policy, episodes, rewards) -> LearnerResult: ...   # pull_count, cumulative_reward
```

The Wilson upper bound reuses the existing code through symmetry: $\text{WilsonUpper}(k, N) = 1 - \text{WilsonLower}(N - k, N)$ with `autonomy.wilson_lower_bound`. Its annotation takes integer counts, but the arithmetic is exact on a float, so the annotation of `successes` widens to `float` and nothing else changes (FDD-016 E3). An action with no pulls has an infinite bound in both variants; the stored decision record writes it as `null`, because JSON has no infinity.

`Decision.logprob` becomes `Optional[float]` and is `None` for this policy (delivered by Story 15.3 of Epic 15). A log-probability of 0.0 is a probability of 1, and the callers copy it into `Episode.action_logprob`, so `ReinforceLearner` would train on a UCB pick as a certain softmax sample; with `None` it already skips the episode. `UCBPolicy.apply_update` raises, because there are no logits to move.

Tests (`tests/test_ucb.py`): round-robin on $N_a = 0$, tie-break by pull count then action id (§4.2), two `choose` calls on one snapshot return the same action, no `random` import (static check), the symmetry identity against `wilson_lower_bound`, scores match the UCB1 formula on hand-computed cases.

**Test data.** *Real:* the same 41-episode positive-only replay as ADR-015; it shows how a deterministic bound behaves when every reward is 1.0. *Gap:* as ADR-015; no real data can show UCB beats REINFORCE (HYP-AL-009) until a low-authority policy with failures exists. *Oracle tests:* published UCB1 worked examples, labeled as arithmetic checks.

**Walkthrough.** [Methodology 10 in the walkthroughs](../learning-methodology-walkthroughs.md#10-ucb-adr-016-44). It runs the sketch today; it must be rewritten against the real module once this is built.

## 5. Alternatives Considered

| Alternative | Rationale for Rejection |
|---|---|
| **Epsilon-Greedy Bandit** | Relies on uniform random action selection during exploration ($\epsilon$), violating strict audit replayability unless RNG seeds are tracked. |
| **Thompson Sampling** | Requires continuous posterior random sampling, requiring cryptographic HMAC seed logging to achieve replayability. |
| **Pure REINFORCE (Status Quo)** | Suffers from mathematical variance collapse under positive-only reward environments and requires hyperparameter tuning. |

## 6. Consequences

### Positive
- **100% Deterministic:** Replaying any historical snapshot state produces identical action choices with zero stochastic variance.
- **Zero Hyperparameter Drift:** Eliminates gradient step sizes, momentum damping, and baseline moving averages.
- **Seamless ADR-003 Compatibility:** As $N_a \rightarrow \infty$, the confidence bound shrinks, converging cleanly to the true mean and providing an exact match for Wilson lower-bound autonomy gates.

### Negative
- Initial exploration is strictly round-robin ($N_a = 0$ must be pulled once per action before exploitation begins).
- Does not easily incorporate continuous contextual feature vectors (unlike contextual bandits).

## 7. Architectural Invariants

1. **Absolute Determinism:** Action selection given a fixed `PolicySnapshot` must be mathematically deterministic with zero RNG calls.
2. **Deterministic Tie-Breaking:** All equal-bound conditions must resolve deterministically via pull counts or action ID ordering.
3. **Storage Boundary (ADR-002):** Action statistics must reside in `PolicySnapshot.metadata["action_statistics"]` with zero schema sprawl.
4. **Authority Boundary (ADR-001):** Operates under `DecisionAuthority.LOW`.

## 8. References
- `docs/project-docs/Ideation-Document.md` §2.1 (Methodology #10)
- `HYP-AL-009`: Deterministic confidence-bound exploration
- `ADR-001`: Decision Authority Model
- `ADR-003`: Evidence-Gated Autonomy Thresholds

## Amendment Log

| Date | Change | Why |
|---|---|---|
| 2026-10-28 | Code design | Added §4.4: module layout, signatures, tests, and which real data exists and which is missing. |
| 2026-10-28 | Accepted | Approved by Menno through `approve-adr`: robust utility 0.697, expected utility 0.774; Episode `dcf700e1-6a3d-4e90-877b-0c2661b10878`. Design only. |
| 2026-10-29 | FDD alignment | Menno confirmed FDD-016 E1 to E6: reward mapped from [-1, 1] to [0, 1]; `Decision.logprob` `None` instead of 0.0; `wilson_lower_bound` annotation widened to float; infinite bounds stored as `null`; `mean_reward` kept in the statistics and enforced equal to its parts; a list of unique `consumed_episode_ids` so an episode is counted once. §4.1, §4.3 and §4.4 amended to match. Re-approved 2026-10-29 under `approve-adr` (adjudicated accept, robust utility 0.729 vs. 0.044 reject and 0.110 revise, episode `d095096a-c9db-43d7-be70-4e079aeb4537`). |
| 2026-10-29 | Score progression | The `compare_decision_results` comparison (ADR-005) of the original approval and the re-approval classifies the change as **progression**: approve robust utility 0.697 to 0.729 (+0.031), expected utility 0.774 to 0.801 (+0.027), uncertainty 0.767 to 0.720; margin over the next option 0.548 to 0.619 (+0.071); the leader stays `approve_adr`; reject is unchanged at 0.044; revise falls 0.149 to 0.110. Three approve criteria rose (gap disclosure +0.062, consequences +0.025, alternatives +0.025); architectural soundness fell by 0.005, within the comparison's tolerance, so the overall result is not a regression. Both rounds are the same reader's scoring, so this is not independent evidence. Result: `docs/policy-shapes/results/adr-016-reapproval-comparison.json`. |
