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
- $\bar{X}_a$ be the empirical mean reward of action $a$: $\bar{X}_a = \frac{1}{N_a} \sum_{i=1}^{N_a} r_{a, i}$.
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
    }
}
```

### 4.4 Code design and test data
Design only: nothing below is built, and the signatures are the contract an FDD must confirm or change.
Module `src/agent_learning/policy/ucb.py`, implementing `Policy`, plus `UCBLearner(Learner)`.

```python
def ucb_scores(stats: Mapping[str, ActionStats], total: int, *,
               variant: str = "wilson", c: float = 2 ** 0.5) -> dict[str, float]: ...
class UCBPolicy(Policy):
    def choose(self, state=None) -> Decision: ...   # no RNG; probabilities one-hot, logprob 0.0
class UCBLearner(Learner):
    def update(self, policy, episodes, rewards) -> LearnerResult: ...   # pull_count, cumulative_reward
```

The Wilson upper bound reuses the existing code through symmetry: $\text{WilsonUpper}(k, N) = 1 - \text{WilsonLower}(N - k, N)$ with `autonomy.wilson_lower_bound`. That function takes integer counts, so fractional rewards need a float-count variant; the FDD decides whether to generalise it or to round (a stated approximation).

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
