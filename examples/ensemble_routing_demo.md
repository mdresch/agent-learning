# Ensemble Routing Example — Summary

## Purpose
Demonstrates the **Contextual Authority Ensemble Routing** framework (ADR-021 / Epic 21). When an agent operates in production or high-stakes environments, decisions with high uncertainty or thin margins must escalate from automated (`LOW`) authority to full reasoning or human oversight (`FULL`). This example demonstrates Shannon entropy, decision margin, hysteresis deadband routing, safety-critical task pinning, and gradient training exclusion.

File: [ensemble_routing_demo.py](ensemble_routing_demo.py)

## Problem Setup
| Element | Definition |
|---|---|
| **Signals** | Shannon Entropy (bits: $-\sum p \log_2 p$) and Decision Margin ($p_{(1)} - p_{(2)}$) |
| **Deadband** | Dual threshold $[\tau_{\text{deesc}}, \tau_{\text{esc}}] = [0.70, 1.00]$ bits with margin guard $\epsilon_{\text{margin}} = 0.20$ |
| **Tiers** | `LOW` (fast, automated policy execution) vs. `FULL` (high-tier reasoning or human approval) |
| **Safety Invariant** | High-risk approval tasks (e.g. financial authorization, compliance sign-offs) are hard-pinned to `FULL` |
| **Learning Rule** | Decisions made under `FULL` authority must be excluded from policy gradient training batches |

## Core Building Blocks
| Object | How the example uses it |
|---|---|
| **`compute_entropy_bits` & `compute_margin`** | Pure standard library functions computing decision uncertainty signals without external dependencies. |
| **`route` & `RoutingConfig`** | Evaluates uncertainty signals against deadband thresholds with hysteresis memory, preventing flapping near the boundary. |
| **`PINNED_FULL`** | Set of non-negotiable approval tasks that reject down-routing to `LOW` authority even when model confidence is 99.9%. |
| **`policy_for_route`** | Dynamic factory routing requests to either `LOW` authority (`TaskPolicy`) or `FULL` authority (`DecisionTaskPolicy`). |
| **`ReinforceLearner`** | Filters episodes by `metadata["route"] != "full"`, preserving learning gradient integrity. |

## Flow
1. **Uncertainty Signal Characterization**: Measures entropy and margin across decisive ($p=[0.95, 0.05]$), borderline ($p=[0.6, 0.3, 0.1]$), and uniform ($p=[0.25, 0.25, 0.25, 0.25]$) distributions.
2. **Hysteresis Deadband Streaming**: Processes a sequential stream of requests traversing the boundary; maintains the previous route when inside the deadband to avoid oscillation.
3. **Safety-Critical Pinning Verification**: Attempts down-routing on pinned tasks, proving that safety invariants override model confidence.
4. **Gradient Exclusion in Training**: Updates a `SoftmaxPolicy` over a mixed batch (2 `LOW` + 2 `FULL` episodes); verifies that only `LOW` episodes contribute to policy gradients.

## Results (deterministic, seed-fixed)
```
Routing Stream Trace:
Step 1: Clear request                | Entropy=0.286  Margin=0.900 -> Route: LOW   (reason: low)
Step 2: Slight drift into deadband   | Entropy=0.722  Margin=0.600 -> Route: LOW   (reason: hysteresis)
Step 3: Uncertain request            | Entropy=0.993  Margin=0.100 -> Route: FULL  (reason: margin)
Step 4: Borderline in deadband again | Entropy=0.722  Margin=0.600 -> Route: FULL  (reason: hysteresis)
Step 5: Decisive request             | Entropy=0.402  Margin=0.840 -> Route: LOW   (reason: low)

Safety-Critical Pinning Refusal:
  Attempting down-route on 'approve-adr' raised ValueError:
  "task 'approve-adr' is pinned to FULL and cannot be routed to LOW"

Reinforce Learner Update:
  - Total episodes in batch:      4
  - Episodes used in gradients:   2 (LOW episodes only)
  - Full-authority excluded:      2 (FULL episodes excluded)
  - Updated probabilities:        action_a=0.512, action_b=0.488
```

## Key Learnings
1. **Hysteresis is essential for streaming stability:** Single-threshold routers flap uncontrollably under noisy real-world confidence scores. Dual thresholds with hysteresis hold state cleanly.
2. **Safety invariants supersede machine confidence:** A high-confidence LLM output must never bypass constitutional approval gates.
3. **Gradient exclusion protects policy integrity:** Reasoning-tier decisions reflect external human or higher-model corrections, not the policy's own generative distribution; training on them corrupts policy gradients.
4. **Independent of internal governance:** While this repository dogfoods its own PMBOK approval tasks in `PINNED_FULL` (`approve-adr`, `approve-brd`, etc.), external adopters do not need our governance framework. Applications can simply pass `requires_human_approval=True` or supply their own high-risk operational tasks (e.g., `execute_wire_transfer`, `drop_database`, `deploy_production`) to enforce human escalation.

## How It Differs From the Other Examples
| | [ensemble_routing_demo.py](ensemble_routing_demo.py) | [contextual_learning_demo.py](contextual_learning_demo.py) | [quickstart.py](quickstart.py) |
|---|---|---|---|
| Core Focus | Uncertainty routing & safety escalation | Context-conditioned policy weights | Marginal baseline bandit |
| Signals | Shannon entropy & decision margin | Feature vector $\phi \in \mathbb{R}^d$ | Scalar reward $r \in [-1, 1]$ |
| Tiers | Automated `LOW` vs. Reasoned `FULL` | Uniform single-tier | Uniform single-tier |
| Invariants | Pinned gates & gradient exclusion | None | None |

## Run It
```powershell
uv run python examples/ensemble_routing_demo.py
```
