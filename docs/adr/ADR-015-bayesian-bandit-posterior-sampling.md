# ADR 015: Bayesian Bandit Posterior Sampling (Thompson Sampling)

## 1. Executive Brief
In reinforcement learning systems applied to software engineering and governance, real-world deployment data is heavily skewed: successful executions vastly outnumber failures (the "survivorship bias" problem, identified in `Ideation-Document.md` as `HYP-AL-002`). When standard policy gradient algorithms (REINFORCE) are exposed solely to positive rewards ($r = +1.0$), baseline adaptation collapses policy variance, driving action probabilities to uniform distributions or causing numerical instability.

This ADR introduces **Bayesian Bandit Posterior Sampling (Thompson Sampling)** (Methodology #9 from `Ideation-Document.md` §2.1, addressing `HYP-AL-002` and `HYP-AL-009`). By modeling action value distributions using conjugate Beta posteriors, Thompson sampling dynamically balances exploration and exploitation through probability matching, maintaining explicit epistemic uncertainty and preventing policy collapse under positive-skewed telemetry.

## 2. Status
**Accepted (2026-10-28, Menno)** — Derived from `Ideation-Document.md` §2.1 (Methodology #9) and `HYP-AL-002`. Approved as a design through `approve-adr` (robust utility 0.680, expected utility 0.759; Episode `5a8c1d42-34d3-4d4e-8642-cd61091349b3`). Amazon Q reviewed this text in PR #37. Nothing is built; the gaps named in the code-design section stay open.

## 3. Context & Problem Statement
- **The Positive-Only Collapse (HYP-AL-002):** In production agent execution, bad actions are often filtered before persistence, or tasks simply succeed repeatedly. When $r_i \approx 1.0$ for all $i$, REINFORCE updates $\nabla \log \pi(a) (r - b)$ decay to zero as baseline $b \rightarrow 1.0$, freezing learning.
- **Epistemic Uncertainty Tracking:** Unlike gradient-based point estimates, Bayesian methods represent the full probability distribution over each action's true payoff rate $\theta_a$. Actions with few observations naturally maintain wide posterior distributions, driving targeted exploration.
- **The Audit Replay Challenge:** Thompson sampling requires random sampling from posterior distributions. In an audited repository, stochasticity must be reconciled with exact post-hoc replayability.

## 4. Technical Decision

### 4.1 Conjugate Beta-Bernoulli Formulation
For binary or unit-scaled rewards $r \in [0, 1]$, each action $a \in A$ maintains a conjugate Beta prior:
$$\theta_a \sim \text{Beta}(\alpha_a, \beta_a)$$
- Prior initialization: $\alpha_a = 1.0, \beta_a = 1.0$ (uniform prior).
- Update rule upon observing reward $r \in [0, 1]$. The SDK's `Reward.value` lies in $[-1, 1]$, so it is mapped by $r = (\text{value} + 1) / 2$ first. For binary $r$ this is the exact conjugate Beta-Bernoulli update; for fractional $r$ it is a pseudo-count approximation, not an exact posterior, and is documented as such:
  $$\alpha_a \leftarrow \alpha_a + r, \quad \beta_a \leftarrow \beta_a + (1 - r)$$
- **Counted once.** The training runner re-queries the latest episodes on every run, so a learner that adds to the posterior on each pass would count the same episode repeatedly. The snapshot keeps `metadata["consumed_episode_ids"]`, a list of unique episode ids, and the learner skips any episode whose id is in it (FDD-015 D7).
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
  $$\text{seed} = \text{int}(\text{HMAC-SHA256}(\text{key}=\text{policy\_id}, \text{msg}=\text{request\_id} \,\|\, \text{timestamp}).\text{hexdigest}()[:16], 16)$$
  (the first 16 hex digits, a 64-bit seed; the example below is a value of that width). It is stored as a decimal string, because a 64-bit integer above $2^{53} - 1$ loses its low bits in the double-precision JSON parsers used by Cosmos DB and common dashboards.
- The request id, the timestamp, the posterior used, the resulting seed and the sampled vector $\hat{\boldsymbol{\theta}}$ are saved in `Episode.metadata["thompson_sampling"]` (the request id and timestamp are needed to re-derive the seed). Posterior parameters are mappings keyed by action id, not lists:
  ```json
  {
    "request_id": "req-001",
    "timestamp": "2026-10-29T08:00:00+00:00",
    "prng_seed": "8472910384719203841",
    "posterior_parameters": {"alpha": {"action_1": 14.0, "action_2": 3.0}, "beta": {"action_1": 2.0, "action_2": 8.0}},
    "sampled_payoffs": {"action_1": 0.842, "action_2": 0.315}
  }
  ```
Any historical decision can be re-run deterministically by re-initializing the PRNG with the recorded seed.

### 4.4 Code design and test data
Design only: nothing below is built, and the signatures are the contract an FDD must confirm or change.
Module `src/agent_learning/policy/thompson.py`, implementing `Policy`, plus a `ThompsonLearner(Learner)`.

```python
def seed_for(policy_id: str, request_id: str, timestamp: str) -> int: ...   # §4.3, 64-bit
class ThompsonPolicy(Policy):
    @classmethod
    def from_snapshot(cls, snapshot: PolicySnapshot) -> ThompsonPolicy: ...  # reads metadata["posterior_parameters"]
    def choose(self, state=None, *, request_id: str | None = None, timestamp: str | None = None) -> Decision: ...  # absent values are supplied and recorded
class ThompsonLearner(Learner):
    def update(self, policy, episodes, rewards) -> LearnerResult: ...      # alpha += r, beta += 1 - r, ESS cap
```

`Policy.choose` returns a `Decision` with a log-probability, which probability matching does not define. `Decision.logprob` therefore becomes `Optional[float]` and is `None` for this policy, and the policy records the seed and sampled vector in `Episode.metadata["thompson_sampling"]` and sets `selection_basis="thompson_sampling"`. No guard is added to `ReinforceLearner`: it already skips an episode whose `action_logprob` is `None`, and a test locks that in (FDD-015 D6). `ThompsonPolicy.apply_update` raises, because a posterior has no logits.

Tests (`tests/test_thompson_seed.py`, `tests/test_thompson_policy.py`, `tests/test_thompson_learner.py`, `tests/test_thompson_reinforce_guard.py`, `tests/test_thompson_positive_only.py`, split by story in Epic 15): same seed gives the same draw, the replay in §4.3 reproduces a recorded episode, the update on Beta(1,1) with r=1 gives (2,1), the ESS cap holds at 5000, offering the same episodes twice counts them once, `ReinforceLearner` skips Thompson episodes, and an all-ones reward history keeps posteriors wide where REINFORCE's update goes to zero (the HYP-AL-002 check).

**Test data.** *Real:* the 41 recorded approval episodes, replayed as $r = 1.0$ for the action taken. This is a genuine positive-only history, the exact situation HYP-AL-002 describes, so it tests the failure mode of the baseline. *Gap:* every one of the 41 is accepted and the `approve-*` policies are full authority, so there is no real low-authority policy with failures and the data cannot show Thompson sampling is better. Needed: a low-authority policy with at least 100 scored episodes including failures. *Oracle tests:* closed-form Beta updates, labeled as arithmetic checks.

**Walkthrough.** [Methodology 9 in the walkthroughs](../learning-methodology-walkthroughs.md#9-thompson-sampling-adr-015-44). It runs the sketch today; it must be rewritten against the real module once this is built.

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
| 2026-10-28 | Review fix | Seed formula took 8 hex digits (32 bits) while the example showed a larger value; it now takes 16 (64 bits). Stated that the fractional-reward update is an approximation, not an exact conjugate posterior. |
| 2026-10-28 | Code design | Added §4.4: module layout, signatures, tests, and which real data exists and which is missing. |
| 2026-10-28 | Accepted | Approved by Menno through `approve-adr`: robust utility 0.680, expected utility 0.759; Episode `5a8c1d42-34d3-4d4e-8642-cd61091349b3`. Design only. |
| 2026-10-29 | FDD alignment | Menno confirmed FDD-015 D1 to D6: reward mapped from [-1, 1] to [0, 1]; `choose` arguments optional and `Decision.logprob` optional; posterior and record keyed by action id with `request_id` and `timestamp` added; no REINFORCE guard needed. §4.1, §4.3 and §4.4 amended to match. Re-approved 2026-10-29 under `approve-adr` (adjudicated accept, robust utility 0.729 vs. 0.044 reject and 0.110 revise, episode `4fd48886-3c8c-485e-8cb2-15bde70cdfe4`). |
| 2026-10-29 | Score progression | The `compare_decision_results` comparison (ADR-005) of the original approval and the re-approval classifies the change as **progression**, with no regression: approve robust utility 0.680 to 0.729 (+0.049), expected utility 0.759 to 0.801 (+0.042), uncertainty 0.795 to 0.720; margin over the next option 0.518 to 0.619 (+0.100); the leader stays `approve_adr`; reject is unchanged at 0.044; revise falls 0.161 to 0.110. Every approve criterion rose (+0.025 to +0.062). The inputs are the same reader's scoring both times, so this shows the amendment did not weaken the document in the scorer's judgement, not independent evidence. Result: `docs/policy-shapes/results/adr-015-reapproval-comparison.json`. |
| 2026-10-29 | Counted once | The training runner re-queries recent episodes on every run and marks none as consumed, so the Thompson learner would add the same episode to a posterior repeatedly. §4.1 adds `metadata["consumed_episode_ids"]` (unique ids, skipped on later passes; the same choice Menno made for ADR-016 E6) and §4.4 names the five Epic 15 test files and the counted-once test. Re-approved 2026-10-29 under `approve-adr` (adjudicated accept, robust utility 0.741 vs. 0.044 reject and 0.110 revise, episode `fb58342d-3d12-4301-8a12-979250cf9265`); the comparison with the previous approval (0.729) classifies as progression, margin 0.619 to 0.631, no criterion lower. |
