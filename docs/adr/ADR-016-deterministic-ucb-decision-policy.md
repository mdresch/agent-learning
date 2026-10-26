# ADR 016: Deterministic Upper Confidence Bound (UCB) Decision Policy

## 1. Executive Brief
In mission-critical autonomous governance, regulatory compliance and audit repeatability mandate that decision selection be **100% deterministic**. While reinforcement learning algorithms such as REINFORCE (ADR-001) and Thompson sampling (Methodology #9) rely on stochastic pseudo-random action sampling, stochasticity creates operational liability: re-evaluating the identical state with a different random seed can produce conflicting actions.

This ADR introduces the **Deterministic Upper Confidence Bound (UCB) Decision Policy** (Methodology #10 from `Ideation-Document.md` §2.1, addressing `HYP-AL-009`). By combining empirical mean rewards with deterministic confidence bounds (integrating with the repo's existing Wilson score calculator), UCB guarantees optimal balance of exploration and exploitation without gradient hyperparameters, entropy tuning, or stochastic seed dependencies.

## 2. Status
**Proposed (2026-10-25)** — Derived from `Ideation-Document.md` §2.1 (Methodology #10) and `HYP-AL-009`. Ready for multi-criteria evaluation under `approve-adr`.

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

