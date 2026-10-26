# ADR 021: Contextual Authority Ensemble Routing

## 1. Executive Brief
ADR-001 established the foundational two-route decision authority model: high-frequency, automated decisions operate under `DecisionAuthority.LOW` (reinforcement learning bandits), while high-impact, strategic decisions operate under `DecisionAuthority.FULL` (Bayesian multi-criteria reasoning with mandatory human sign-off). Currently, the assignment of authority is statically fixed at policy initialization time. This creates a rigid operational dichotomy: routine, low-risk requests running on a `full` policy incur heavy LLM token and latency overhead, while unusual, edge-case requests hitting a `low` policy cannot escalate dynamically to reasoned evaluation.

This ADR introduces **Contextual Authority Ensemble Routing** (Methodology #17 from `Ideation-Document.md` §2.1). By evaluating request uncertainty, Shannon entropy, and declared ADR-003 complexity tiers at runtime, an ensemble router dynamically dispatches requests to either fast statistical bandits or thorough Bayesian reasoning, achieving optimal trade-offs between execution velocity and governance rigor.

## 2. Status
**Proposed (2026-10-25)** — Derived from `Ideation-Document.md` §2.1 (Methodology #17). Ready for multi-criteria evaluation under `approve-adr`.

## 3. Context & Problem Statement
- **The Static Authority Inefficiency:** A policy configured with `full` authority must evaluate a multi-criteria `DecisionFrame` for every single instance, even when an identical input has been processed hundreds of times with high confidence.
- **The Low-Authority Safety Hazard:** A policy configured with `low` authority samples actions based on learned logits. When faced with an out-of-distribution or adversarial input, it lacks an intrinsic mechanism to halt and invoke reasoned human oversight.
- **External Industry Precedent:** Microsoft's GitHub Copilot Auto mode (September 2026) and Azure AI Foundry Model Router dynamically evaluate prompt complexity and operational difficulty to route across multiple model tiers. ADR-021 implements this exact routing pattern within our decision governance framework.

## 4. Technical Decision

### 4.1 Routing Architecture & Dispatch Logic
Let a decision request contain context features $\mathbf{x}$ and belong to a configured complexity profile (ADR-003).

#### Hard Strategic Pinning:
Regardless of confidence or entropy, lifecycle baseline gates (`approve-charter`, `approve-adr`, `approve-brd`, `approve-fdd`, `approve-user-stories`, `approve-pmp`, `retrospective`) are hard-pinned by assertion to `DecisionAuthority.FULL` with `requires_human_approval: true`. Dynamic down-routing is prohibited.

#### Operational Dispatch Logic:
For operational tasks, the ensemble router evaluates two safety signals:
1. **Low-Authority Shannon Entropy:**
   $$H(\pi_{\text{low}}(\cdot \mid \mathbf{x})) = -\sum_{a \in A} \pi(a \mid \mathbf{x}) \log \pi(a \mid \mathbf{x})$$
2. **Complexity Tier Impact:** Whether the declared complexity tier is `critical` or high-impact.

To prevent high-frequency mode switching ("hunting" oscillation), routing employs a hysteresis band $\Delta H \ge 0.15 \text{ bits}$ between escalation ceiling $\tau_{\text{esc}}$ and de-escalation floor $\tau_{\text{deesc}}$:
$$R(\mathbf{x}) = \begin{cases} 
\text{DecisionAuthority.FULL} & \text{if } H(\pi) \ge \tau_{\text{esc}} \;\lor\; \text{Tier} = \text{Critical} \;\lor\; \text{Margin}(\pi) < \epsilon_{\text{margin}} \\
\text{DecisionAuthority.LOW} & \text{if } H(\pi) \le \tau_{\text{deesc}} \;\land\; \text{Tier} \ne \text{Critical} \;\land\; \text{Margin}(\pi) \ge \epsilon_{\text{margin}} \\
R_{\text{previous}}(\mathbf{x}) & \text{otherwise (hysteresis deadband)}
\end{cases}$$

### 4.2 Decoupled Execution Paths
- **Route = LOW:** Evaluated via `TaskPolicy.decide()` using local CPU bandit logits. Sub-millisecond latency, zero LLM calls.
- **Route = FULL:** Generates or consumes a `DecisionFrame`, invokes `DecisionResolver.resolve()`, enforces hard constraints, and triggers human adjudication if required.

### 4.3 Learner Gradient Exclusion Invariant
A critical architectural pitfall in ensemble systems is training contamination. Under ADR-001 §4.2, full-authority decisions must never enter REINFORCE policy-gradient batches.
- The router tags every episode: `Episode.metadata["routed_authority"] = "low" | "full"`.
- `LearningRunner` and `ReinforceLearner` filter training batches, strictly ignoring any episode where `routed_authority != "low"`.

## 5. Alternatives Considered

| Alternative | Rationale for Rejection |
|---|---|
| **Static Policy Configuration (Status Quo)** | Forces all-or-nothing trade-offs between performance and safety. |
| **Cascade Fallback on Failure** | Running `low` first and escalating only upon execution failure is unsafe for irreversible actions. Routing must occur *before* execution. |
| **LLM-Based Meta-Router** | Invoking an LLM to decide whether to invoke an LLM defeats the performance and cost benefits of fast bandit routing. Entropy and tier checks execute on CPU in $<0.1 \text{ ms}$. |

## 6. Consequences

### Positive
- Reduces LLM token costs and latency by $70\text{--}90\%$ for routine, low-uncertainty operational requests.
- Eliminates low-authority blind spots: high-entropy edge cases automatically escalate to full Bayesian review.
- Strictly adheres to ADR-001 and ADR-003 safety invariants.

### Negative
- Requires maintaining both a `SoftmaxPolicy` and a `DecisionFrame` schema for hybrid task definitions.
- The entropy threshold $\tau_{\text{entropy}}$ must be calibrated to balance escalation rates.

## 7. Architectural Invariants

1. **Mandatory Critical Escalation:** Any request with complexity tier `critical` must route to `full` authority regardless of entropy.
2. **Strict Gradient Exclusion:** Episodes executed under `routed_authority = "full"` are permanently barred from policy-gradient gradient updates.
3. **Audit Provenance:** `Episode.metadata` must record the routing decision, observed entropy $H(\pi)$, and the active routing threshold.
4. **Storage Boundary (ADR-002):** Zero new database entities; router state lives in `PolicySnapshot.metadata`.
5. **Strategic Baseline Pinned Authority Invariant:** Governance lifecycle baseline gates (`approve-charter`, `approve-adr`, `approve-brd`, `approve-fdd`, `approve-user-stories`, `approve-pmp`, `retrospective`) are permanently pinned to `DecisionAuthority.FULL` with `requires_human_approval: true`. Autonomous down-routing to `LOW` authority for these tasks is strictly prohibited by code assertion.
6. **Switching Hysteresis Invariant:** Dynamic transitions between `LOW` and `FULL` authority must enforce a hysteresis deadband $\Delta H \ge 0.15 \text{ bits}$ to prevent switching oscillation.

## 8. References
- `docs/project-docs/Ideation-Document.md` §2.1 (Methodology #17)
- `ADR-001`: Decision Authority Model
- `ADR-002`: Storage Backend Strategy
- `ADR-003`: Evidence-Gated Autonomy Thresholds

## 9. Amendment Log

| Date | Change | Why |
|---|---|---|
| 2026-10-25 | Initial Draft | Candidate derived from Ideation Document §2.1 (Methodology #17). |
| 2026-10-25 | Peer-Review Hardening | Added Invariant 5 (Strategic Baseline Pinned Authority) per PMBOK Auditor condition to protect core governance gates; added Invariant 6 (Switching Hysteresis Deadband $\Delta H \ge 0.15 \text{ bits}$) per Cybernetics Control Theorist to prevent limit-cycle hunting. |

