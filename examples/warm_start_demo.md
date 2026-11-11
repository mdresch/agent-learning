# Explicit Policy Prior Warm-Starting — Summary

## Purpose
Demonstrates **Explicit Policy Prior Warm-Starting & Prior Transfer** (Methodology #15 / ADR-020 addressing Hypothesis `HYP-AL-008`). When an autonomous agent task policy or dynamic model router is initialized, starting from uniform uncalibrated weights ($\theta_a = 0.0$) forces the agent to waste dozens of episodes re-learning foundational trade-offs already mastered by structurally similar tasks. 

This example demonstrates how to transfer empirical knowledge from a converged donor policy to a new target policy across an explicit bijective action mapping, apply **confidence damping** ($\tau = 0.70$) to prevent premature policy lock-in, maintain strict snapshot isolation and provenance lineage, and measure the empirical speedup in policy gradient convergence.

File: [warm_start_demo.py](warm_start_demo.py)

---

## Architectural & Mathematical Formulation

### 1. The Cold-Start Dilemma
Under standard reinforcement learning or multi-armed bandits:
* A cold policy initializes with uniform zero logits: $\theta_{\text{cold}, a} = 0.0 \implies \pi(a) = \frac{1}{|A|}$.
* In an action space with $|A| = 3$, initial Shannon entropy is maximal ($H = \log_2(3) \approx 1.5850\text{ bits}$), meaning the agent explores completely blindly.
* In high-stakes production, this blind exploration causes degraded user responses, high human supervision costs, and slow qualification for autonomous execution (ADR-003).

### 2. Damped Logit Transfer
Instead of copying raw weights ($\tau = 1.0$), which transfers excessive confidence and chokes local exploration, ADR-020 specifies **Confidence Damping**:

$$\theta_{\text{target}, a} = \theta_{\text{donor}, m(a)} \cdot \tau_{\text{damping}}$$

Where:
* $m: A_{\text{target}} \to A_{\text{donor}}$ is an explicit bijective action mapping.
* $\tau_{\text{damping}} \in (0.0, 1.0]$ scales down logit spread (default $\tau = 0.70$).
* The resulting softmax distribution compresses the logit dynamic range and expands exploratory entropy:

$$\pi_{\text{target}}(a) \propto \exp\left( \tau_{\text{damping}} \cdot \theta_{\text{donor}, m(a)} \right)$$

$$H(\tau = 0.70) > H(\tau = 1.0)$$

---

## Comparison Table: Damping vs. Entropy

| Condition | Damping ($\tau$) | Shannon Entropy | Initial Probabilities (Approve / Revise / Reject) | Role in Learning |
|---|---|---|---|---|
| **Cold Start (Uniform)** | $0.00$ | $1.5850\text{ bits}$ | $33.3\% \ / \ 33.3\% \ / \ 33.3\%$ | Blind exploration; highest supervisory friction. |
| **Aggressive Damping** | $0.40$ | $1.3000\text{ bits}$ | $61.5\% \ / \ 27.1\% \ / \ 11.5\%$ | Broad exploration with slight prior bias. |
| **Standard Damping (ADR-020)** | **$0.70$** | **$0.9240\text{ bits}$** | **$77.5\% \ / \ 18.4\% \ / \ 4.1\%$** | **Optimal:** preserves ordinal ranking while allowing local adaptation. |
| **Raw Transfer (Undamped)** | $1.00$ | $0.6061\text{ bits}$ | $87.4\% \ / \ 11.3\% \ / \ 1.3\%$ | Overconfident; risks negative transfer if target differs. |

---

## Provenance & Snapshot Isolation Invariants

1. **Strict Snapshot Isolation (ADR-020 §7 Invariant 1):** The recipient policy is stored as a new version ($v_{\text{target}} = v_{\text{old}} + 1$). The donor policy snapshot and its stored episodes in `LearningStore` remain **100% immutable**. Subsequent gradient updates on the recipient never mutate the donor.
2. **Immutable Lineage Audit:** The recipient snapshot metadata records complete provenance:
   ```json
   {
     "warm_start_donor_policy_id": "policy-quality-v12-converged",
     "warm_start_donor_task_id": "approve-quality-plan",
     "warm_start_donor_version": 12,
     "warm_start_damping_factor": 0.7,
     "warm_started_at": "2026-11-11T00:00:00+00:00",
     "warm_start_action_map": {
       "approve_risk": "approve_plan",
       "request_risk_revision": "request_revision",
       "reject_risk": "reject_plan"
     },
     "warm_start_donor_kind": "policy",
     "warm_start_donor_gate_met": true
   }
   ```
3. **No Automatic Autonomy Credit:** Warm-starting accelerates learning, but does not bypass evidence gates. The recipient must still satisfy the ADR-003 autonomy gate independently.

---

## Simulation Results (HYP-AL-008 Confirmation)

We benchmarked a cold-start policy against a warm-started policy ($\tau = 0.70$) and an undamped policy ($\tau = 1.00$) over 12 training rounds (180 episodes total) using `ReinforceLearner`:

```
==============================================================================
  PHASE 3: COMPARATIVE LEARNING SIMULATION & HYPOTHESIS FALSIFICATION
==============================================================================

Simulating 12 training rounds (180 total episodes) across:
  1. Cold-Start Policy (Uniform logits, tau = 0.0)
  2. Warm-Started Policy (ADR-020, tau = 0.70)
  3. Undamped Policy (Raw transfer, tau = 1.00)

Benchmark Learning Results Summary:
  Condition                  Convergence Round    Cumulative Reward    Final Probabilities
  ------------------------   ------------------   ------------------   --------------------------------
  Cold-Start (tau = 0.00)    Round 12 (180 eps)   64.58                {'approve_risk': 0.629, 'request_risk_revision': 0.241, 'reject_risk': 0.131}
  Warm-Start (tau = 0.70)    Round 6 (90 eps)     133.31               {'approve_risk': 0.862, 'request_risk_revision': 0.108, 'reject_risk': 0.03}
  Undamped   (tau = 1.00)    Round 1 (15 eps)     142.80               {'approve_risk': 0.909, 'request_risk_revision': 0.079, 'reject_risk': 0.012}

Empirical Performance Gains:
  * Cumulative Reward Gain: +106.4% higher reward under warm-starting.
  * Training Time Saved:    90 fewer exploration episodes required to converge.

FALSIFICATION CONCLUSION (HYP-AL-008):
  Hypothesis: 'Explicit policy prior warm-starting with confidence damping reaches convergence
               and autonomy in significantly fewer episodes than uniform cold-starting.'
  Status: CONFIRMED (Warm-start reached threshold in Round 6 vs. Round 12 for cold-start).
```

---

## Architectural Takeaways

1. **Cold-Start Elimination:** Warm-starting doubles cumulative reward during initial rollout ($+106.4\%$) and halves the episodes required to achieve convergence.
2. **Entropy Preserves Adaptability:** Confidence damping at $\tau = 0.70$ provides the sweet spot: it gives the agent strong initial guidance while preserving sufficient entropy ($0.9240\text{ bits}$) to correct for target-task variations.
3. **Decoupled Lineage:** Enterprise audit trails maintain full provenance of which policy seeded which model router, guaranteeing traceability across model fleet versions.

