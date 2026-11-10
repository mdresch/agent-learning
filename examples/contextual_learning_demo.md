# Contextual Learning Example — Summary

## Purpose
Demonstrates **Packaged Contextual Learning** (ADR-038 / Epic 38). Standard marginal bandits learn a single globally favored action across all users. In production environments, optimal decisions depend on request-specific context features. This example demonstrates `ContextualSoftmaxPolicy` parameterized by a weight matrix $W \in \mathbb{R}^{|A| \times d}$ and trained via `ContextualReinforceLearner`.

File: [contextual_learning_demo.py](contextual_learning_demo.py)

## Problem Setup
An automated developer platform support agent chooses guidance formats for incoming technical inquiries.

| Element | Definition |
|---|---|
| **Context Features ($\phi$)** | $\phi = [\text{is\_developer}, \text{system\_urgency}, \text{enterprise\_tier}] \in \mathbb{R}^3$ |
| **Actions** | `concise_cli` (direct command-line snippets) vs. `guided_gui` (visual step-by-step walkthrough) |
| **Reward Oracle** | Developers in outages reward concise CLI output (+1.0); non-technical business users reward step-by-step UI guidance (+1.0) |
| **Policy** | Action logits computed dynamically via $\theta(a, \phi) = W_a \cdot \phi$ |

## Core Building Blocks
| Object | How the example uses it |
|---|---|
| **`ContextualSoftmaxPolicy`** | Stores weight matrix $W \in \mathbb{R}^{2 \times 3}$; evaluates logits and action probabilities conditioned on state features $\phi$. |
| **`policy.choose(state=...)`** | Samples actions from the context-conditioned probability distribution $\pi(a \mid \phi) = \text{softmax}(W \phi)_a$. |
| **`ContextualReinforceLearner`** | Computes analytical policy gradients $\nabla_{W_a} \log \pi(a \mid \phi) = (\mathbf{1}_{a = a_t} - \pi(a \mid \phi)) \phi$ and updates $W$ across logged episodes with baseline tracking. |
| **`InMemoryStore`** | Persists policy snapshots and episode traces in-process without external databases. |

## Flow
1. **Initialize Contextual Policy**: Starts with zero weights $W = \mathbf{0}$, producing uniform 50%/50% distributions across all contexts.
2. **Episode Generation**: Simulates 60 historical support episodes across random user profiles; records the request feature vector in `episode.metadata["feature_vector"]`.
3. **Contextual REINFORCE Update**: Evaluates policy gradients using logged feature vectors and shaped rewards, updating $W$ over multiple training rounds.
4. **Specialization Verification**: Tests the trained policy against two contrasting user profiles:
   - **Profile A (Senior Engineer in Outage):** $\phi = [1.0, 1.0, 1.0]$
   - **Profile B (Business End-User):** $\phi = [0.0, 0.2, 0.5]$

## Results (deterministic, seed-fixed)
```
=== Policy Probabilities BEFORE Training (W = 0) ===
Profile A (Engineer):   concise_cli=50.0%  guided_gui=50.0%
Profile B (Business):   concise_cli=50.0%  guided_gui=50.0%

Training for 10 rounds x 60 episodes ...
  Round  1: Mean Reward = +0.033
  Round  3: Mean Reward = +0.467
  Round  6: Mean Reward = +0.767
  Round 10: Mean Reward = +0.867

=== Policy Probabilities AFTER Training ===
Profile A (Engineer [1.0, 1.0, 1.0]):
  - concise_cli: 97.7% (was 50.0%)
  - guided_gui:   2.3% (was 50.0%)
  -> Result: Strongly favors CLI commands for engineers!

Profile B (Business [0.0, 0.2, 0.5]):
  - concise_cli:  9.4% (was 50.0%)
  - guided_gui:  90.6% (was 50.0%)
  -> Result: Strongly favors step-by-step UI walkthrough for business users!
```

## Key Learnings
1. **Context eliminates policy conflict:** A marginal bandit forced to choose between CLI and GUI achieves mediocre rewards across mixed populations; contextual policies specialize per user segment.
2. **Zero external dependencies:** The weight matrix and gradient evaluations are implemented entirely in Python and NumPy without heavy ML frameworks.
3. **Metadata feature transport:** Context vectors serialize cleanly in `episode.metadata["feature_vector"]`, matching production telemetry pipelines.

## How It Differs From the Other Examples
| | [contextual_learning_demo.py](contextual_learning_demo.py) | [quickstart.py](quickstart.py) | [pairwise_preference_demo.py](pairwise_preference_demo.py) |
|---|---|---|---|
| Policy Type | Contextual Softmax ($W \phi$) | Marginal Softmax ($\theta$) | Marginal Softmax ($\theta$) |
| Context Sensitivity | Dynamic per feature vector | None (global distribution) | None (global distribution) |
| Learner | `ContextualReinforceLearner` | Built-in `ReinforceLearner` | `PairwiseLearner` (Bradley-Terry) |
| Input Data | Feature vector + scalar reward | Scalar reward only | Pairwise reviewer overrides |

## Run It
```powershell
uv run python examples/contextual_learning_demo.py
```
