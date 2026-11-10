# Pairwise Preference Optimization Example — Summary

## Purpose
Demonstrates **Pairwise Preference Optimization** (ADR-018 / Epic 18). In production operations, human reviewers rarely assign continuous scalar rewards to agent actions. Instead, reviewers audit decisions and submit overrides—rejecting the agent's proposed action in favor of a preferred alternative. This example demonstrates fitting a `SoftmaxPolicy` directly to pairwise preference data using the **Bradley-Terry** model with convex $L_2$ regularization anchored to frozen reference logits.

File: [pairwise_preference_demo.py](pairwise_preference_demo.py)

## Problem Setup
An automated customer operations triage agent determines how to dispatch incoming incident reports.

| Element | Definition |
|---|---|
| **Actions** | `auto_resolve`, `queue_standard`, `escalate_incident` |
| **Feedback Signal** | Reviewer overrides with `feedback_status="rejected"` and `correct_action_id` |
| **Preference Pair** | Winner $w = \text{correct\_action\_id}$, Loser $l = \text{action\_id}$ |
| **Loss Function** | Regularized Bradley-Terry negative log-likelihood with anchor: $\mathcal{L}(\theta) = \sum_{(w,l)} W_{w,l} \log(1 + e^{-(\theta_w - \theta_l)}) + \frac{\lambda}{2} \|\theta - \theta_{\text{ref}}\|_2^2$ |

## Core Building Blocks
| Object | How the example uses it |
|---|---|
| **`pairs_from_episodes`** | Extracts deduplicated `PreferencePair(winner, loser, source_episode_id)` records from historical episodes. |
| **`bt_loss` & `bt_gradient`** | Evaluates exact loss and gradients with numerically stable `logaddexp` and vectorization. |
| **`PairwiseLearner`** | Projected gradient descent optimizer with stationarity stopping criteria (`tol=1e-7`), bounding box clamp ($[-6.0, +6.0]$), and frozen reference logits. |
| **`SoftmaxPolicy`** | Standard discrete policy whose logits update via `policy.apply_update(deltas)`. |

## Flow
1. **Initial Uniform Policy**: Creates a baseline `SoftmaxPolicy` with uniform prior (33.3% across all three actions).
2. **Reviewer Override Feedback**: Simulates episodes where human reviewers reject automated resolutions on critical incidents:
   - 3 overrides: `auto_resolve` rejected in favor of `escalate_incident`
   - 2 overrides: `queue_standard` rejected in favor of `escalate_incident`
   - 1 override: `auto_resolve` rejected in favor of `queue_standard`
3. **Reference Logit Freezing**: Captures and freezes $\theta_{\text{ref}}$ in snapshot metadata to anchor learning and prevent unbounded drift.
4. **Projected Gradient Descent**: `PairwiseLearner.update()` minimizes Bradley-Terry loss, outputting exact logit deltas and convergence diagnostics.
5. **Distribution Shift Inspection**: Verifies probability reallocation toward favored actions.

## Results (deterministic, seed-fixed)
```
Extracted 6 preference pairs from 7 episodes:
  [ep-001] Winner: 'escalate_incident' preferred over Loser: 'auto_resolve'
  [ep-002] Winner: 'escalate_incident' preferred over Loser: 'auto_resolve'
  [ep-003] Winner: 'escalate_incident' preferred over Loser: 'auto_resolve'
  [ep-004] Winner: 'escalate_incident' preferred over Loser: 'queue_standard'
  [ep-005] Winner: 'escalate_incident' preferred over Loser: 'queue_standard'
  [ep-006] Winner: 'queue_standard'    preferred over Loser: 'auto_resolve'

Optimization Diagnostics:
  - Converged:    True
  - Iterations:   219
  - Stationarity: 9.485e-08
  - Loss Before:  4.1589
  - Loss After:   0.8148

Logit Deltas:
  - auto_resolve:     -1.9587
  - queue_standard:   -0.2108
  - escalate_incident:+2.1695

Policy Probabilities Shift:
  - auto_resolve:      33.33% ->  1.45%
  - queue_standard:    33.33% ->  8.35%
  - escalate_incident: 33.33% -> 90.20%
```

## Key Learnings
1. **Direct preference learning without reward modeling:** Eliminates the intermediate step of calibrating arbitrary scalar reward numbers.
2. **Convex $L_2$ anchoring prevents runaway policy drift:** Without $\frac{\lambda}{2} \|\theta - \theta_{\text{ref}}\|^2$, separable preference data would push logits to $\pm \infty$.
3. **Auditability:** Every preference pair traces back to a specific `source_episode_id` and reviewer intervention.

## How It Differs From the Other Examples
| | [pairwise_preference_demo.py](pairwise_preference_demo.py) | [quickstart.py](quickstart.py) | [critique_evidence_demo.py](critique_evidence_demo.py) |
|---|---|---|---|
| Feedback Signal | Human action overrides | Continuous scalar reward | Markdown critique rubrics |
| Objective | Bradley-Terry preference loss | Policy gradient (REINFORCE) | Bayesian evidential pooling |
| Regularization | $L_2$ reference logit anchor | Entropy bonus | Doubt inflation ($\kappa$) |

## Run It
```powershell
uv run python examples/pairwise_preference_demo.py
```
