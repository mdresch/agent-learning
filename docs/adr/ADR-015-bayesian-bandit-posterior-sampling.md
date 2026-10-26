# ADR 015: Bayesian Bandit Posterior Sampling (Thompson Sampling)

## 1. Executive Brief
In reinforcement learning systems applied to software engineering and governance, real-world deployment data is heavily skewed: successful executions vastly outnumber failures (the "survivorship bias" problem, identified in `Ideation-Document.md` as `HYP-AL-002`). When standard policy gradient algorithms (REINFORCE) are exposed solely to positive rewards ($r = +1.0$), baseline adaptation collapses policy variance, driving action probabilities to uniform distributions or causing numerical instability.

This ADR introduces **Bayesian Bandit Posterior Sampling (Thompson Sampling)** (Methodology #9 from `Ideation-Document.md` §2.1, addressing `HYP-AL-002` and `HYP-AL-009`). By modeling action value distributions using conjugate Beta posteriors, Thompson sampling dynamically balances exploration and exploitation through probability matching, maintaining explicit epistemic uncertainty and preventing policy collapse under positive-skewed telemetry.

## 2. Status
**Proposed (2026-10-25)** — Derived from `Ideation-Document.md` §2.1 (Methodology #9) and `HYP-AL-002`. Ready for multi-criteria evaluation under `approve-adr`.

## 3. Context & Problem Statement
- **The Positive-Only Collapse (HYP-AL-002):** In production agent execution, bad actions are often filtered before persistence, or tasks simply succeed repeatedly. When $r_i \approx 1.0$ for all $i$, REINFORCE updates $\nabla \log \pi(a) (r - b)$ decay to zero as baseline $b \rightarrow 1.0$, freezing learning.
- **Epistemic Uncertainty Tracking:** Unlike gradient-based point estimates, Bayesian methods represent the full probability distribution over each action's true payoff rate $\theta_a$. Actions with few observations naturally maintain wide posterior distributions, driving targeted exploration.
- **The Audit Replay Challenge:** Thompson sampling requires random sampling from posterior distributions. In an audited repository, stochasticity must be reconciled with exact post-hoc replayability.

## 4. Technical Decision

### 4.1 Conjugate Beta-Bernoulli Formulation
For binary or unit-scaled rewards $r \in [0, 1]$, each action $a \in A$ maintains a conjugate Beta prior:
$$\theta_a \sim \text{Beta}(\alpha_a, \beta_a)$$
- Prior initialization: $\alpha_a = 1.0, \beta_a = 1.0$ (uniform prior).
- Update rule upon observing reward $r \in [0, 1]$:
  $$\alpha_a \leftarrow \alpha_a + r, \quad \beta_a \leftarrow \beta_a + (1 - r)$$
- **Effective Sample Size (ESS) Cap & Discounting:** To prevent parameter lock-in under non-stationary conditions, total pseudo-counts are capped at $N_{\max} = 5000$:
  $$\text{If } (\alpha_a + \beta_a) > N_{\max}, \quad \alpha_a \leftarrow \alpha_a \cdot \frac{N_{\max}}{\alpha_a + \beta_a}, \quad \beta_a \leftarrow \beta_a \cdot \frac{N_{\max}}{\alpha_a + \beta_a}$$
  Alternatively, an exponential discounting factor $\gamma \in [0.99, 1.0]$ may be applied per batch update ($\alpha_a \leftarrow 1.0 + \gamma (\alpha_a - 1.0)$).

### 4.2 Action Selection (Probability Matching)
At each decision point:
1. Draw a sample $\hat{\theta}_a$ from the posterior distribution of each action:
   $$\hat{\theta}_a \sim \text{Beta}(\alpha_a, \beta_a), \quad \forall a \in A$$
2. Select the action with the highest sampled value:
   $$a^* = \arg\max_{a \in A} \hat{\theta}_a$$

### 4.3 Deterministic Audit & Cryptographic Replayability
To satisfy repository auditability without compromising the mathematical properties of Thompson sampling:
- The pseudo-random number generator (PRNG) is seeded via an HMAC-SHA256 hash of the immutable request context:
  $$\text{seed} = \text{int}(\text{HMAC-SHA256}(\text{key}=\text{policy\_id}, \text{msg}=\text{request\_id} \,\|\, \text{timestamp})[:8], 16)$$
- The resulting seed and the sampled vector $\hat{\boldsymbol{\theta}}$ are saved in `Episode.metadata["thompson_sampling"]`:
  ```json
  {
    "prng_seed": 847291038471,
    "posterior_parameters": {"alpha": [14.0, 3.0], "beta": [2.0, 8.0]},
    "sampled_payoffs": {"action_1": 0.842, "action_2": 0.315}
  }
  ```
Any historical decision can be re-run deterministically by re-initializing the PRNG with the recorded seed.

## 5. Alternatives Considered

| Alternative | Rationale for Rejection |
|---|---|
| **REINFORCE Gradient Ascent (Status Quo)** | Fails under positive-only reward environments due to baseline convergence ($r - b \approx 0$). |
| **Deterministic UCB1 (ADR-016)** | Lacks a full probabilistic posterior representation, preventing seamless integration with prior transfers (ADR-020). |
| **Gaussian Process Bandits** | Requires matrix inversions scaling as $\mathcal{O}(t^3)$, violating the CPU-bound, low-latency requirement. |

## 6. Consequences

### Positive
- Robust to positive-only reward distributions; epistemic uncertainty naturally guides exploration without artificial entropy bonuses.
- Zero gradient step-size or learning-rate hyperparameters to tune.
- Deterministic auditability preserved via cryptographically seeded PRNG tracking.

### Negative
- Requires closed-form conjugate assumptions (Beta-Bernoulli for bounded rewards); extending to complex multi-dimensional continuous rewards requires discretization.

## 7. Architectural Invariants

1. **Deterministic Replay Guarantee:** Every decision episode generated under Thompson sampling must record its PRNG seed and sampled values in `Episode.metadata`.
2. **Conjugate Storage (ADR-002):** Action posterior parameters ($\alpha_a, \beta_a$) must be stored in `PolicySnapshot.metadata["posterior_parameters"]` without introducing new tables.
3. **Authority Model (ADR-001):** Operates under `DecisionAuthority.LOW`.
4. **Effective Sample Size Ceiling & Discounting:** To prevent epistemic lock-in in non-stationary environments, total pseudo-counts per action must not exceed $N_{\max} = 5000$; updates exceeding this ceiling are dynamically normalized or discounted.

## 8. References
- `docs/project-docs/Ideation-Document.md` §2.1 (Methodology #9)
- `HYP-AL-002`: Positive-skewed telemetry convergence
- `ADR-001`: Decision Authority Model
- `ADR-002`: Storage Backend Strategy

## 9. Amendment Log

| Date | Change | Why |
|---|---|---|
| 2026-10-25 | Initial Draft | Candidate derived from Ideation Document §2.1 (Methodology #9). |
| 2026-10-25 | Peer-Review Hardening | Added Invariant 4 (Effective Sample Size Ceiling $N_{\max} \le 5000$ and exponential discounting) per Cybernetics Control Theorist and Systems Architect recommendations to prevent posterior lock-in. |

