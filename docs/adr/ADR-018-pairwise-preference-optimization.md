# ADR 018: Pairwise Preference Optimization for Discrete Action Logits

## 1. Executive Brief
In human-in-the-loop decision governance (ADR-001, ADR-003), human adjudications frequently take the form of explicit overrides: the autonomous system proposes action $a_{\text{proposed}}$, but the human reviewer selects a different action $a_{\text{selected}}$ (via `task-policy-adjudicate --disposition override`). Converting this qualitative human choice into a synthetic scalar reward (e.g., assigning $+1.0$ to the selected action and $-1.0$ to the proposed action) introduces arbitrary scale distortions, gradient explosion, and reward hacking.

This ADR introduces **Pairwise Preference Optimization for Discrete Action Logits** (Methodology #13 from `Ideation-Document.md` §2.1). Inspired by Direct Preference Optimization (DPO) and grounded in the classical Bradley-Terry preference model, this learner optimizes discrete action logits directly from observed human preference pairs $(a_w \succ a_l)$ without intermediate reward modeling, hyperparameter instability, or GPU infrastructure.

## 2. Status
**Proposed (2026-10-25)** — Derived from `Ideation-Document.md` §2.1 (Methodology #13). Ready for multi-criteria evaluation under `approve-adr`.

## 3. Context & Problem Statement
- **The Qualitative Preference Signal:** When a human adjudicator rejects an agent's proposal and selects an alternative, the true signal is ordinal ($a_{\text{selected}} \succ a_{\text{proposed}}$), not cardinal ($r = +1.0, r = -1.0$).
- **The Inherent Flaws of Scalar Reward Shaping:** Fitting a scalar reward function to ordinal preferences creates reward variance and calibration drift across different human reviewers.
- **Red Team Alignment:** The repository's Red Team evaluation suite systematically generates paired comparisons (compliant vs. non-compliant governance diffs). DPO provides a native training framework to consume this paired dataset directly.

## 4. Technical Decision

### 4.1 Bradley-Terry Optimization Formulation
Let $A$ be a finite discrete action set. Let $\boldsymbol{\theta} \in \mathbb{R}^{|A|}$ be the logit vector of a `SoftmaxPolicy`.
Given a preference dataset $\mathcal{D} = \{(a_{w, i}, a_{l, i})\}_{i=1}^M$ where action $a_w$ was preferred over action $a_l$, the probability that $a_w$ is chosen over $a_l$ under the Bradley-Terry model is:
$$P(a_w \succ a_l \mid \boldsymbol{\theta}) = \sigma(\theta_{a_w} - \theta_{a_l}) = \frac{1}{1 + e^{-(\theta_{a_w} - \theta_{a_l})}}$$

The negative log-likelihood loss is:
$$\mathcal{L}(\boldsymbol{\theta}) = -\sum_{i=1}^M \log \sigma(\theta_{a_{w, i}} - \theta_{a_{l, i}}) + \frac{\lambda_{\text{reg}}}{2} \|\boldsymbol{\theta} - \boldsymbol{\theta}_{\text{ref}}\|^2$$
Where $\boldsymbol{\theta}_{\text{ref}}$ is a frozen reference policy snapshot (preventing drift from initial safety bounds), and $\lambda_{\text{reg}} \ge 0.05$ is an explicit regularization lower bound. Furthermore, action logits $\theta_a$ are clamped to $[-8.0, +8.0]$ to prevent sigmoid saturation and numerical gradient vanishing.

### 4.2 Exact CPU-Bound Gradient Updates
The gradient with respect to logit $\theta_a$ is:
$$\nabla_{\theta_a} \mathcal{L} = -\sum_{i=1}^M \sigma(\theta_{a_{l, i}} - \theta_{a_{w, i}}) \cdot \left( \mathbb{I}[a = a_{w, i}] - \mathbb{I}[a = a_{l, i}] \right) + \lambda_{\text{reg}}(\theta_a - \theta_{\text{ref}, a})$$
This update has a closed-form solution that executes on a single CPU core in $< 1 \text{ ms}$ for discrete action spaces ($|A| \le 20$).

### 4.3 Training Pipeline & Data Sourcing
Training data is extracted directly from historical `Episode` records in `LearningStore`:
- An episode where `metadata["decision_disposition"] == "override"` yields pair $(a_{\text{adjudicated}} \succ a_{\text{proposed}})$.
- A Red Team contrastive evaluation yields pair $(a_{\text{compliant}} \succ a_{\text{adversarial}})$.
Zero manual labeling or new database records are required.

## 5. Alternatives Considered

| Alternative | Rationale for Rejection |
|---|---|
| **Synthetic Scalar Rewards with REINFORCE** | Forcing scalar numbers onto pairwise choices creates baseline drift and gradient instability. |
| **Full LLM-DPO with LoRA** | Fine-tuning generative weights violates the frozen foundation model invariant and requires GPU hardware. |
| **RankNet / Multi-Layer Perceptrons** | Over-parameterizes small discrete action spaces; Bradley-Terry provides exact convex convergence. |

## 6. Consequences

### Positive
- Directly aligns action logits with human adjudication choices without scalar reward distortion.
- Convex loss function guarantees global convergence without local minima traps.
- Operates entirely on CPU in sub-millisecond execution times.

### Negative
- Requires paired comparison data; cannot learn from solitary execution traces where no alternative action was considered.

## 7. Architectural Invariants

1. **Frozen Model Invariance:** Updates apply strictly to discrete action logits $\boldsymbol{\theta} \in \mathbb{R}^{|A|}$; foundation model weights remain untouched.
2. **Zero Storage Sprawl (ADR-002):** Training pairs are derived dynamically from existing `Episode` override records; no new storage tables are created.
3. **Reference Anchor Regularization:** Updates must retain a reference regularization term ($\lambda_{\text{reg}} \ge 0.05$) against the initial baseline snapshot.
4. **Authority Boundary (ADR-001):** Operates under `DecisionAuthority.LOW`.
5. **Logit Clamping Invariant:** All updated logits must be clamped to $[-8.0, +8.0]$ during gradient optimization to prevent numerical instability and probability polarization.

## 8. References
- `docs/project-docs/Ideation-Document.md` §2.1 (Methodology #13)
- `ADR-001`: Decision Authority Model
- `ADR-002`: Storage Backend Strategy
- `ADR-005`: Decision Progress Comparison

## 9. Amendment Log

| Date | Change | Why |
|---|---|---|
| 2026-10-25 | Initial Draft | Candidate derived from Ideation Document §2.1 (Methodology #13). |
| 2026-10-25 | Peer-Review Hardening | Added Invariant 5 (Logit Clamping to $[-8.0, +8.0]$) and bound $\lambda_{\text{reg}} \ge 0.05$ per Control Theorist and Systems Architect recommendations. |

