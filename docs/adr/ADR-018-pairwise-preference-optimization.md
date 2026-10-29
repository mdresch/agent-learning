# ADR 018: Pairwise Preference Optimization for Discrete Action Logits

## 1. Executive Brief
In human-in-the-loop decision governance (ADR-001, ADR-003), human adjudications frequently take the form of explicit overrides: the autonomous system proposes action $a_{\text{proposed}}$, but the human reviewer selects a different action $a_{\text{selected}}$ (via `task-policy-adjudicate --disposition override`). Converting this qualitative human choice into a synthetic scalar reward (e.g., assigning $+1.0$ to the selected action and $-1.0$ to the proposed action) introduces arbitrary scale distortions, gradient explosion, and reward hacking.

This ADR introduces **Pairwise Preference Optimization for Discrete Action Logits** (Methodology #13 from `Ideation-Document.md` §2.1). Inspired by Direct Preference Optimization (DPO) and grounded in the classical Bradley-Terry preference model, this learner optimizes discrete action logits directly from observed human preference pairs $(a_w \succ a_l)$ without intermediate reward modeling, hyperparameter instability, or GPU infrastructure.

## 2. Status
**Accepted (2026-10-28, Menno)** — Derived from `Ideation-Document.md` §2.1 (Methodology #13). Approved as a design through `approve-adr` (robust utility 0.677, expected utility 0.757; Episode `63bf5225-a320-46d8-bc54-b26d84a1ea46`). Amazon Q reviewed this text in PR #37. Nothing is built; the gaps named in the code-design section stay open.

## 3. Context & Problem Statement
- **The Qualitative Preference Signal:** When a human adjudicator rejects an agent's proposal and selects an alternative, the true signal is ordinal ($a_{\text{selected}} \succ a_{\text{proposed}}$), not cardinal ($r = +1.0, r = -1.0$).
- **The Inherent Flaws of Scalar Reward Shaping:** Fitting a scalar reward function to ordinal preferences creates reward variance and calibration drift across different human reviewers.
- **Red Team Alignment (to be substantiated):** The Red Team fixtures (`tests/fixtures/governance/adversarial-*.json`) are single adversarial frames, not (compliant, non-compliant) pairs. They can become a pair set only after a human labels a compliant counterpart for each; until then this is a candidate source, not an existing one.

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
The regularized loss has no closed-form minimizer. It is minimized by projected gradient descent (gradient step, then clamp to $[-8.0, +8.0]$) with a fixed iteration cap. The loss is convex, and the clamp is a projection onto a convex box, so the iteration still converges to the global minimum of the constrained problem. The gradient is a sum over pairs, so the step must shrink as pairs grow: a fixed step of 0.1 diverged at 3,000 pairs in a prototype (the loss rose on 1,000 iterations and the logits ended in the wrong order). The pairs are therefore aggregated into an $|A| \times |A|$ count matrix, so one iteration costs $O(|A|^2)$ whatever the number of pairs, and the step is $\min(\text{lr}, 1/(\lambda_{\text{reg}} + 0.5 \cdot d_{\max}))$ with $d_{\max}$ the largest number of pairs naming one action, which keeps the loss from rising. The iteration stops early on a stationarity tolerance, and the result says whether it converged; at that step 3,000 pairs did not converge in 2,000 steps, and the result reports it instead of claiming an optimum. Measured on three actions, 2,000 steps took about 50 ms (FDD-018 G1, G2).

### 4.3 Training Pipeline & Data Sourcing
Training data is extracted directly from historical `Episode` records in `LearningStore`:
- An episode whose `metadata["feedback_status"]` is `rejected` and whose `correct_action_id` is in the policy's actions and differs from `action_id` yields pair $(a_{\text{adjudicated}} \succ a_{\text{proposed}})$, with $a_{\text{adjudicated}}$ = `correct_action_id`. These are the fields `autonomy.py` reads and episode registration validates; `decision_disposition` is not read, because no code reads or writes it (FDD-018 G3). There is no `"override"` value.
- A Red Team contrastive evaluation yields pair $(a_{\text{compliant}} \succ a_{\text{adversarial}})$.
Zero manual labeling or new database records are required.

**Prerequisites and bias.** `feedback_status` and `correct_action_id` are already present on recorded episodes, and all 41 recorded episodes are accepted, so no preference pair exists in real data today. The alternatives a human considered are not persisted beyond `correct_action_id`. Override pairs are also a biased sample: an accepted proposal yields no pair, so the data over-represents disagreements. The pairs are therefore used only to adjust logits relative to $\boldsymbol{\theta}_{\text{ref}}$ (the regularizer above), never as an estimate of the overall acceptance rate.

### 4.4 Code design and test data
Design only: nothing below is built, and the signatures are the contract an FDD must confirm or change.
Module `src/agent_learning/learners/pairwise.py`, with `PairwiseLearner(Learner)` acting on a `SoftmaxPolicy`.

```python
@dataclass(frozen=True)
class PreferencePair:
    winner: str; loser: str; source_episode_id: str
def pairs_from_episodes(episodes: Iterable[Episode], action_ids: Sequence[str]) -> list[PreferencePair]: ...   # §4.3 override rule; an episode id counts once
def fit_logits(pairs, action_ids, theta_ref, *, lam: float = 0.05, lr: float = 0.1,
               steps: int = 2000, clamp: float = 8.0, tol: float = 1e-8) -> FitResult: ...   # logits, converged, iterations, stationarity, step_size, loss
class PairwiseLearner(Learner):
    def update(self, policy, episodes, rewards) -> LearnerResult: ...
```

An override is an episode whose `metadata["feedback_status"]` is `rejected` and whose `correct_action_id` is in the policy's actions and differs from `action_id`. `theta_ref` is stored in `PolicySnapshot.metadata["pairwise_reference_logits"]` on the first update that has a pair and is never overwritten. Each update refits from `theta_ref` over the pairs offered, so it is idempotent for a fixed pair set; pairs that leave the training runner's episode window are forgotten (FDD-018 G4, G5). The learner refuses a policy whose `max_logit_abs` is below the 8.0 clamp, because `SoftmaxPolicy.apply_update` would cut the fitted values. There are no rewards to consume, so `consumed_inputs` is `None` and the audit replay reports insufficient lineage, as it does for every learner except REINFORCE (FDD-018 G6, G7).

Tests (`tests/test_pairwise_pairs.py`, `tests/test_pairwise_loss.py`, `tests/test_pairwise_fit.py`, `tests/test_pairwise_learner.py`, `tests/test_pairwise_runner.py`, `tests/test_pairwise_real_data.py`, split by story in Epic 18): the loss never increases for pair sets up to 3,000, the same episodes offered twice give the same pairs, the gradient matches a finite-difference check, the loss never increases, logits stay in $[-8, 8]$, with no pairs the logits stay at $\theta_{\text{ref}}$, $\lambda_{\text{reg}} < 0.05$ is rejected, the `Episode` input is not changed.

**Test data.** *Real:* all 41 recorded approval episodes when this ADR was written (76 committed files on 2026-10-29) carry `decision_disposition`, `correct_action_id` and `feedback_status`, and every one is `accepted` with the recommended action, so the real number of preference pairs is **zero**. The governance fixtures hold 3 adversarial and 6 diff frames; these are single classification frames, not (compliant, non-compliant) pairs, so the Red Team claim in §3 needs a labeled pair set built from them before it can be used. *Gap:* real override episodes. Needed: adjudications where a human chose differently from the proposal (the 30 review-triage records include `declined` and `accepted with modification` decisions, but the reviewer there is not a policy, so they do not qualify). *Oracle tests:* the finite-difference gradient check, as arithmetic.

**Walkthrough.** [Methodology 13 in the walkthroughs](../learning-methodology-walkthroughs.md#13-pairwise-preference-adr-018-44). It runs the sketch today; it must be rewritten against the real module once this is built.

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
- Operates entirely on CPU in tens of milliseconds (about 50 ms for 2,000 steps on three actions, measured), independent of the number of pairs.

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
| 2026-10-28 | Review fix | Removed the false closed-form claim (iterative projected gradient descent). Named the missing data prerequisites and the selection bias of override-only pairs. |
| 2026-10-28 | Code design | Added §4.4: module layout, signatures, tests, and which real data exists and which is missing. |
| 2026-10-28 | Amazon Q review (PR #37), round 2 | Section 4.3 said an override is `decision_disposition == "override"` while section 4.4 said `modify` or `rejected`. ADR-034 defines `accepted`, `rejected` and `modify`, so section 4.3 now uses that rule and says there is no `"override"` value. |
| 2026-10-28 | Accepted | Approved by Menno through `approve-adr`: robust utility 0.677, expected utility 0.757; Episode `63bf5225-a320-46d8-bc54-b26d84a1ea46`. Design only. |
| 2026-10-29 | FDD alignment | Menno confirmed FDD-018 G1 to G7: a step size that cannot overshoot with a matrix form and an honest convergence report (a fixed step of 0.1 diverged at 3,000 pairs); the timing claims replaced by a measurement; overrides read from `feedback_status` `rejected` and `correct_action_id`, not from the unused `decision_disposition`; `theta_ref` stored in the snapshot metadata and frozen; a refit from `theta_ref` that counts an episode once and forgets pairs outside the runner window; the 8.0 clamp checked against `max_logit_abs`; no consumed inputs. §4.2, §4.3, §4.4 and §6 amended to match. Re-approved 2026-10-29 under `approve-adr` (adjudicated accept, robust utility 0.705 vs. 0.044 reject and 0.110 revise, episode `e225dbbc-a0cc-4dbb-a39f-32d11293a753`). The ADR-005 comparison with the original approval (0.677) classifies as **progression**: margin 0.514 to 0.595, expected utility 0.757 to 0.781, uncertainty 0.797 to 0.757, no criterion lower (soundness +0.055, gap disclosure +0.020, consequences +0.019, alternatives 0.000; the alternatives section did not change). The largest rise is soundness because the amendment fixed real defects (the divergent step size, the unsupported timing claim and the unused override field). The inputs are the same reader's scoring both times, so this is not independent evidence. Result: `docs/policy-shapes/results/adr-018-reapproval-comparison.json`. |
