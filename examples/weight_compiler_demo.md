# Scored-Search Decision Weight Compilation Example — Summary

## Purpose
Demonstrates **Scored-Search Decision Configuration Compilation** (ADR-022 / Epic 22). When an agent makes decisions via multi-criteria utility scoring, hand-authored criteria weights often misalign with organizational priorities (e.g., over-weighting cost while human executives prioritize security). This example demonstrates learning optimal criteria weights by searching the simplex with coordinate ascent over historical adjudicated decisions, guarded by holdout partitioning and strict improvement safety gates.

File: [weight_compiler_demo.py](weight_compiler_demo.py)

## Problem Setup
An engineering council uses an agent to recommend microservices deployment architectures (`arch_a` vs. `arch_b`) based on three criteria: `security`, `latency`, and `cost`.

| Element | Definition |
|---|---|
| **Authored Weights (Baseline)** | Initial misaligned weights: `{"security": 0.15, "latency": 0.15, "cost": 0.70}` (excessive cost focus) |
| **True Consensus (Target)** | Expert priorities reflected in human decisions: `{"security": 0.60, "latency": 0.30, "cost": 0.10}` |
| **Historical Data** | 30 `LabeledFrame` records pairing `DecisionFrame` with expert-adjudicated action labels and timestamps |
| **Search Space** | Simplex coordinates: $w_k \ge 0.05$ and $\sum_k w_k = 1.0$ |
| **Multi-Objective** | $\text{Score}(w) = \sum_i (\mathbf{1}_{\hat{y}_i = y_i} + \beta \cdot \text{margin}_i)$ with $\beta = 0.10$ |
| **Safety Gate** | Candidate weights are proposed if and only if holdout accuracy strictly outperforms baseline |

## Core Building Blocks
| Object | How the example uses it |
|---|---|
| **`split_holdout`** | Partitions frames into training (70%) and holdout (30%) sets deterministically with sorting and minimum partition validation ($\ge 5$). |
| **`coordinate_ascent`** | Multi-restart coordinate ascent optimizer traversing simplex steps ($\pm 0.05$), projecting candidates, and tracking sweeps. |
| **`propose`** | Validates label timestamps strictly prior to `proposed_at`; scores baseline vs. candidate on holdout; emits `CompiledWeights` or `NoImprovement`. |
| **`apply_compiled_config`** | Injects compiled criteria weights carried in `PolicySnapshot.metadata["criteria_weights"]` into incoming production frames. |

## Flow
1. **Historical Dataset Generation**: Generates 30 realistic workload evaluations where human experts decide under true security priorities (0.60 security, 0.30 latency, 0.10 cost).
2. **Authored Baseline Measurement**: Evaluates accuracy under initial cost-biased weights (80.0% accuracy across all frames; 77.8% on holdout).
3. **Reproducible Holdout Split**: Partitions into 21 training frames and 9 held-out evaluation frames.
4. **Simplex Coordinate Ascent**: Runs 5 restarts and 4 sweeps; candidate weights converge to `security: 0.7039, latency: 0.1758, cost: 0.1203` with 100% training accuracy.
5. **Safety Gate Verification**: `propose()` checks holdout performance:
   - Baseline Holdout Accuracy: 77.8%
   - Compiled Holdout Accuracy: 100.0% (+22.2% strict improvement)
   - Emits immutable `CompiledWeights` (`mappingproxy`).
6. **Production Configuration Injection**: Updates active inference frame criteria via `apply_compiled_config`.

## Results (deterministic, seed-fixed)
```
Dataset Partitioning:
  - Total frames:   30
  - Training Set:   21 frames
  - Held-out Set:    9 frames

Coordinate Ascent Search:
  - Sweeps:         4
  - Restarts:       5
  - Evaluations:    4683
  - Train Accuracy: 100.0%

Compiled Weights on Simplex:
  - security: 0.7039 (was 0.1500)
  - latency:  0.1758 (was 0.1500)
  - cost:     0.1203 (was 0.7000)

Proposal Safety Gate:
  [PROPOSAL ACCEPTED] CompiledWeights meets all safety gates:
  - Baseline Holdout Accuracy: 77.8%
  - Compiled Holdout Accuracy: 100.0%
  - Holdout Margin:            0.1015
  - Strictly Outperformed?    YES (+22.2% improvement)
  - Immutable Proxy Type:      mappingproxy
```

## Key Learnings
1. **Coordinate ascent effectively discovers hidden priorities:** Even with small labeled samples ($N=30$), coordinate ascent accurately realigns weights to human expert judgment.
2. **Strict holdout safety protects production:** Weights that overfit or fail to beat authored baselines are cleanly rejected via `NoImprovement`.
3. **Immutable deployment:** `CompiledWeights.weights` is wrapped in Python's `MappingProxyType`, preventing runtime parameter tampering.

## How It Differs From the Other Examples
| | [weight_compiler_demo.py](weight_compiler_demo.py) | [critique_evidence_demo.py](critique_evidence_demo.py) | [quickstart.py](quickstart.py) |
|---|---|---|---|
| Target Parameter | Criteria weights $w \in \Delta^{K-1}$ | Option evidence points $p, c$ | Action logits $\theta \in \mathbb{R}^{|A|}$ |
| Algorithm | Coordinate ascent with restarts | Bayesian log-odds pooling | REINFORCE gradient ascent |
| Validation | Train/Holdout split & safety gate | None (instantaneous application) | None (single batch) |

## Run It
```powershell
uv run python examples/weight_compiler_demo.py
```
