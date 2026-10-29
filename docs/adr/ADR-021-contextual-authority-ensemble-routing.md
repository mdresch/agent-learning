# ADR 021: Contextual Authority Ensemble Routing

## 1. Executive Brief
ADR-001 established the foundational two-route decision authority model: high-frequency, automated decisions operate under `DecisionAuthority.LOW` (reinforcement learning bandits), while high-impact, strategic decisions operate under `DecisionAuthority.FULL` (Bayesian multi-criteria reasoning with mandatory human sign-off). Currently, the assignment of authority is statically fixed at policy initialization time. This creates a rigid operational dichotomy: routine, low-risk requests running on a `full` policy incur heavy LLM token and latency overhead, while unusual, edge-case requests hitting a `low` policy cannot escalate dynamically to reasoned evaluation.

This ADR introduces **Contextual Authority Ensemble Routing** (Methodology #17 from `Ideation-Document.md` §2.1). By evaluating request uncertainty, Shannon entropy, and declared ADR-003 complexity tiers at runtime, an ensemble router dynamically dispatches requests to either fast statistical bandits or thorough Bayesian reasoning, achieving optimal trade-offs between execution velocity and governance rigor.

## 2. Status
**Accepted (2026-10-28, Menno)** — Derived from `Ideation-Document.md` §2.1 (Methodology #17). Approved as a design through `approve-adr` (robust utility 0.683, expected utility 0.762; Episode `a8e8fb11-e936-4cbd-9ce7-f872b1d0ee7a`). Amazon Q reviewed this text in PR #36. Nothing is built; the gaps named in the code-design section stay open.

## 3. Context & Problem Statement
- **The Static Authority Inefficiency:** A policy configured with `full` authority must evaluate a multi-criteria `DecisionFrame` for every single instance, even when an identical input has been processed hundreds of times with high confidence.
- **The Low-Authority Safety Hazard:** A policy configured with `low` authority samples actions based on learned logits. When faced with an out-of-distribution or adversarial input, it lacks an intrinsic mechanism to halt and invoke reasoned human oversight.
- **External Industry Precedent:** Microsoft's GitHub Copilot Auto mode (September 2026) and Azure AI Foundry Model Router dynamically evaluate prompt complexity and operational difficulty to route across multiple model tiers. ADR-021 implements this exact routing pattern within our decision governance framework.

## 4. Technical Decision

### 4.1 Routing Architecture & Dispatch Logic
Let a decision request contain context features $\mathbf{x}$ and belong to a configured complexity profile (ADR-003).

#### Hard Strategic Pinning:
Regardless of confidence or entropy, lifecycle baseline gates (`approve-charter`, `approve-adr`, `approve-brd`, `approve-fdd`, `approve-user-stories`, `approve-pmp`, `approve-adaptation-plan` (ADR-008 Invariant 4), `approve-subsidiary-plan` (ADR-013 Invariant 2), `retrospective`) are hard-pinned by assertion to `DecisionAuthority.FULL` with `requires_human_approval: true`. The router also pins any task whose complexity profile declares `requires_human_approval: true`, so a gate added later is protected without editing this list. Dynamic down-routing is prohibited.

#### Operational Dispatch Logic:
For operational tasks, the ensemble router evaluates three safety signals:
1. **Low-Authority Shannon Entropy**, in bits (base-2 logarithm, so that $\Delta H$ below is in bits):
   $$H(\pi_{\text{low}}(\cdot \mid \mathbf{x})) = -\sum_{a \in A} \pi(a \mid \mathbf{x}) \log_2 \pi(a \mid \mathbf{x})$$
2. **Decision Margin:** the gap between the two most probable actions, $\text{Margin}(\pi) = \pi_{(1)}(\mathbf{x}) - \pi_{(2)}(\mathbf{x})$, with default $\epsilon_{\text{margin}} = 0.20$.
3. **Complexity Tier Impact:** Whether the declared complexity tier is `critical`. Other tiers are decided by entropy and margin unless the task requires human approval, which pins it (FDD-021 K3).

$R_{\text{previous}}(\mathbf{x})$ is the route of the newest routed episode of the context bucket (the declared context key, not the raw input), read from `Episode.metadata["routing"]`. `PolicySnapshot.metadata["routing_state"]` holds only human-set configuration, because a per-request write would rewrite the snapshot on every decision (FDD-021 K1). A bucket with no previous route starts at `FULL`.

To prevent high-frequency mode switching ("hunting" oscillation), routing employs a hysteresis band $\Delta H \ge 0.15 \text{ bits}$ between escalation ceiling $\tau_{\text{esc}}$ and de-escalation floor $\tau_{\text{deesc}}$:
$$R(\mathbf{x}) = \begin{cases} 
\text{DecisionAuthority.FULL} & \text{if } H(\pi) \ge \tau_{\text{esc}} \;\lor\; \text{Tier} = \text{Critical} \;\lor\; \text{Margin}(\pi) < \epsilon_{\text{margin}} \\
\text{DecisionAuthority.LOW} & \text{if } H(\pi) \le \tau_{\text{deesc}} \;\land\; \text{Tier} \ne \text{Critical} \;\land\; \text{Margin}(\pi) \ge \epsilon_{\text{margin}} \;\land\; \text{ApprovedForLow}(\mathbf{x}) \\
R_{\text{previous}}(\mathbf{x}) & \text{otherwise (hysteresis deadband)}
\end{cases}$$

$\text{ApprovedForLow}(\mathbf{x})$ is true only for a bucket that passed the §4.4 gate and has a recorded human approval. A bucket that is not approved stays on `FULL` whatever its entropy.

**Fail-safe.** If any input cannot be computed or is invalid (a NaN or negative probability, probabilities that do not sum to 1 within tolerance, an empty action set, an unknown tier), the route is `FULL` and a routing anomaly is recorded in `Episode.metadata["routing_anomaly"]`. An unknown bucket also starts at `FULL`, which is the safe direction.

**Threshold ownership.** $\tau_{\text{esc}}$, $\tau_{\text{deesc}}$ and $\epsilon_{\text{margin}}$ are stored in `PolicySnapshot.metadata["routing_state"]["thresholds"]`. They have no calibrated values yet. Setting or changing them is a human decision recorded as an episode (the same `approve-*` pattern as other decisions), and a change triggers revalidation of every approved bucket (§4.4). The change is applied by `task-policy-routing-set`, which requires an adjudicated, accepted approval episode of `approve-routing-thresholds` or `approve-routing-bucket` (FDD-021 K4).

### 4.2 Decoupled Execution Paths
- **Route = LOW:** Evaluated via `TaskPolicy.decide()` using local CPU bandit logits. Sub-millisecond latency, zero LLM calls.
- **Route = FULL:** Generates or consumes a `DecisionFrame`, invokes `DecisionResolver.resolve()`, enforces hard constraints, and triggers human adjudication if required.
- **Dispatch** builds a `TaskPolicy` from an in-memory copy of the snapshot with the route as its authority, because `TaskPolicy` reads the authority when it is constructed. The stored policy is never changed, and only a snapshot that carries `routing_state` is routed (FDD-021 K2).

### 4.3 Learner Gradient Exclusion Invariant
A critical architectural pitfall in ensemble systems is training contamination. Under ADR-001 §4.2, full-authority decisions must never enter REINFORCE policy-gradient batches.
- The router tags every episode: `Episode.metadata["routed_authority"] = "low" | "full"`.
- `ReinforceLearner` skips an episode when `routed_authority == "full"`; `LearningRunner` hands it the episodes and is unchanged (FDD-021 K6). An episode with no `routed_authority` tag (a policy that never went through the router, or an episode recorded before this ADR) is not dropped by this rule: it falls back to the ADR-001 §4.5 enforcement (skip when `action_logprob is None`). Requiring `routed_authority == "low"` would silently discard every episode of an unrouted `low` policy.

### 4.4 Starvation Guard (No Gradient Path Required)
Excluding `full` episodes from training (§4.3) creates a loop: contexts the low policy is unsure about route to `full`, never train it, and so stay uncertain. The guard breaks the loop without letting any `full` episode into a gradient batch:
- For every `full`-routed instance the router also records, without acting on it, the low policy's argmax: `Episode.metadata["shadow_low_action"]`.
- Per context bucket, agreement between `shadow_low_action` and the final adjudicated action is counted from the bucket's episodes when a proposal is made, not stored per request (FDD-021 K1). The shadow action is the argmax of the policy state at decision time and is recorded together with that distribution's entropy, so a near-uniform (untrained) argmax is visible as such.
- Agreement from an untrained policy can come from the bucket's base rate alone (if one action is adjudicated 95% of the time, always picking it agrees 95% of the time). The promotion proposal therefore reports the bucket's base rate (share of its most frequent adjudicated action) beside the Wilson lower bound, so the approver can see whether agreement exceeds it. This is reported, not a second gate.
- A bucket may be proposed for `low` routing only when its agreements pass the ADR-003 gate (at least 20 outcomes, Wilson lower bound $\ge 0.90$). The 20-outcome floor is not binding: a Wilson lower bound of 0.90 needs at least 35 agreements without a miss (the bound for 20 of 20 is 0.839; FDD-021 K7). The proposal is a recommendation; a human approves it, and the entropy test in §4.1 still applies afterwards.
- Shadow actions are never rewards and never enter `LearningRunner` batches.
- **Promotion seeds the bucket without a gradient.** The low policy does not change while a bucket is on `FULL`, so its distribution for that bucket is still untrained and the §4.1 entropy test would send the bucket straight back to `FULL`. On approval, the bucket's prior is seeded from its observed agreement frequencies, damped as in ADR-020, and stored in `routing_state[bucket]["prior"]` with its provenance. The seed is `damping * (ln f_a - mean ln f)` with `f_a = (n_a + 1) / (N + |A|)` and damping 0.70 by default (FDD-021 K5). The router uses that prior for the entropy and margin tests and for the `LOW` choice until the bucket has its own `LOW` episodes, after which the learned distribution takes over. The seed is not scored outcomes and does not count towards any autonomy gate. If the seeded distribution still fails the §4.1 test, the bucket stays on `FULL`. FDD-021 K5 confirms this mechanism.
- **Evidence expires.** Agreement counts older than `max_evidence_age_days` are dropped. The parameter is required and has no default: until a human sets it, no bucket can be proposed for `low` routing (fail closed), so evidence cannot silently stay valid forever. and every approved bucket is revalidated when a threshold changes.

### 4.5 Code design and test data
Design only: nothing below is built, and the signatures are the contract an FDD must confirm or change.
Module `src/agent_learning/routing.py`, pure; the router returns a decision and the caller records it.

```python
@dataclass(frozen=True)
class RoutingConfig:
    tau_esc: float
    tau_deesc: float
    eps_margin: float = 0.20
    def __post_init__(self) -> None: ...   # ValueError if tau_esc - tau_deesc < 0.15 bits (Invariant 6)
def route(probs: Sequence[float], tier: str, task_id: str, previous: DecisionAuthority | None,
          approved_for_low: bool, requires_human_approval: bool,
          cfg: RoutingConfig) -> RouteDecision: ...      # authority, entropy_bits, margin, reason, anomaly
PINNED_FULL: frozenset[str]                              # the §7 baseline gates and approve-routing-thresholds, approve-routing-bucket; route() asserts on them
# route() also pins any task with requires_human_approval=True, and returns FULL with anomaly set on invalid input.
# previous=None is treated as FULL before the hysteresis comparison, so a first call inside the deadband routes FULL.
def shadow_record(low_action_id: str, entropy_bits: float) -> dict[str, object]: ...   # §4.4, recorded at decision time; the final action is not yet known; entropy stays a float
# previous_route, agreement, propose_bucket, seed_prior and policy_for_route are the other functions (FDD-021 §3)
```

Tests (`tests/test_routing_signals.py`, `tests/test_routing_route.py`, `tests/test_routing_pinning.py`, `tests/test_routing_guard.py`, `tests/test_routing_decisions.py`, `tests/test_routing_dispatch.py`, `tests/test_routing_real_data.py`, split by story in Epic 21): a `RoutingConfig` with a gap under 0.15 bits is rejected (including inverted thresholds, `tau_esc < tau_deesc`), a first call (`previous=None`) inside the deadband routes `FULL`, a pinned gate always routes `full`, a `critical` tier always routes `full`, no flip inside the hysteresis band, entropy is in bits (uniform over 4 actions = 2.0), the margin rule escalates, a bucket without `approved_for_low` never routes `LOW`, invalid input (NaN, empty, not summing to 1) routes `FULL` with an anomaly, `approve-adaptation-plan` and `approve-subsidiary-plan` are pinned, `shadow_record` output is never read by `LearningRunner`, a `full` episode is skipped by `ReinforceLearner`, and an untagged episode from an unrouted `low` policy is still trained on.

**Dependency.** `ReinforceLearner` already skips an episode with no log-probability, which every reasoned (full-authority) decision is, and counts it as excluded. The explicit `routed_authority` check of §4.3 is the one addition; it changes `learners/reinforce.py` (FDD-021 K6).

**Test data.** *Real:* none. No episode carries `routed_authority` or a low-policy distribution, because no policy has been run in both modes. The 14 `approve-adr` episodes do carry real `expected_utility` and `robust_utility`, which could inform where `eps_margin` sits, but they say nothing about entropy. *Gap:* real mixed-difficulty traffic through a hybrid policy; thresholds stay uncalibrated until then. *Oracle tests:* entropy and margin values on fixed distributions, as arithmetic.

**Walkthrough.** [Methodology 17 in the walkthroughs](../learning-methodology-walkthroughs.md#17-authority-routing-adr-021-45). It runs the sketch today; it must be rewritten against the real module once this is built.

## 5. Alternatives Considered

| Alternative | Rationale for Rejection |
|---|---|
| **Static Policy Configuration (Status Quo)** | Forces all-or-nothing trade-offs between performance and safety. |
| **Cascade Fallback on Failure** | Running `low` first and escalating only upon execution failure is unsafe for irreversible actions. Routing must occur *before* execution. |
| **LLM-Based Meta-Router** | Invoking an LLM to decide whether to invoke an LLM defeats the performance and cost benefits of fast bandit routing. Entropy and tier checks execute on CPU in $<0.1 \text{ ms}$. |

## 6. Consequences

### Positive
- Expected to reduce LLM token costs and latency for routine, low-uncertainty operational requests; the size of the saving is unmeasured and depends on the share of requests that reach `low`.
- Eliminates low-authority blind spots: high-entropy edge cases automatically escalate to full Bayesian review.
- Strictly adheres to ADR-001 and ADR-003 safety invariants.

### Negative
- Requires maintaining both a `SoftmaxPolicy` and a `DecisionFrame` schema for hybrid task definitions.
- The thresholds $(\tau_{\text{esc}}, \tau_{\text{deesc}}, \epsilon_{\text{margin}})$ must be calibrated to balance escalation rates.

## 7. Architectural Invariants

1. **Mandatory Critical Escalation:** Any request with complexity tier `critical` must route to `full` authority regardless of entropy.
2. **Strict Gradient Exclusion:** Episodes executed under `routed_authority = "full"` are permanently barred from policy-gradient gradient updates.
3. **Audit Provenance:** `Episode.metadata` must record the routing decision, observed entropy $H(\pi)$, and the active routing threshold.
4. **Storage Boundary (ADR-002):** Zero new database entities; router state lives in `PolicySnapshot.metadata`.
5. **Strategic Baseline Pinned Authority Invariant:** Governance lifecycle baseline gates (`approve-charter`, `approve-adr`, `approve-brd`, `approve-fdd`, `approve-user-stories`, `approve-pmp`, `approve-adaptation-plan`, `approve-subsidiary-plan`, `retrospective`, and any task declaring `requires_human_approval: true`) are permanently pinned to `DecisionAuthority.FULL` with `requires_human_approval: true`. Autonomous down-routing to `LOW` authority for these tasks is strictly prohibited by code assertion.
6. **Switching Hysteresis Invariant:** Dynamic transitions between `LOW` and `FULL` authority must enforce a hysteresis deadband $\Delta H \ge 0.15 \text{ bits}$ to prevent switching oscillation.

7. **Starvation Guard:** A context bucket moves from `full` to `low` only through the §4.4 evidence gate and a human approval; no `full` episode ever enters a gradient batch. The §4.1 routing rule and the `route()` signature both require `ApprovedForLow`.
8. **Fail-Safe Routing:** Any routing calculation failure or invalid input routes `FULL` and records a routing anomaly.
9. **Threshold Change Control:** Routing thresholds are changed only by a recorded human decision, and a change revalidates every approved bucket.

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
| 2026-10-28 | Review fix | Defined $\text{Margin}$ and $\epsilon_{\text{margin}}$, moved entropy to bits so $\Delta H$ is in bits, and bounded $R_{\text{previous}}$ per context bucket. Added §4.4 and Invariant 7: the gradient exclusion left `full`-routed contexts with no way to become `low`. Removed the unsourced "70-90%" saving. |
| 2026-10-28 | Code design | Added §4.5: module layout, signatures, tests, and which real data exists and which is missing. |
| 2026-10-28 | Amazon Q review (PR #36) | `RoutingConfig` enforces the 0.15-bit gap (`__post_init__`, dataclass fields on separate lines); `previous=None` is FULL before the hysteresis comparison; the starvation-guard proposal reports the bucket base rate and the entropy of the recorded shadow distribution. |
| 2026-10-28 | Amazon Q review, round 5 | `max_evidence_age_days` is required; unset means no bucket can be proposed for `low` (fail closed). |
| 2026-10-28 | Amazon Q review, round 4 | `shadow_record` takes `entropy_bits` and returns `dict[str, object]`, so the recorded entropy stays a number (§4.4 requires it beside the shadow action). |
| 2026-10-28 | External review triage | Accepted: promotion seeds the bucket prior without a gradient (the §4.4 guard could not otherwise lower entropy); `ApprovedForLow` added to §4.1 and `route()`; `approve-adaptation-plan`, `approve-subsidiary-plan` and any `requires_human_approval` task pinned; §4.3 filter skips `routed_authority == "full"` instead of requiring `"low"`; fail-safe routing and threshold change control (Invariants 8 and 9); evidence expiry parameter; wording fixes. Declined: invented roles, cadence and a 90-day figure, router KPIs (the benchmark is designed separately), and making the ADR-001 §4.5 story a condition of approval (it stays a build dependency). |
| 2026-10-28 | Amazon Q review, round 2 | Test list names inverted thresholds. |
| 2026-10-28 | Accepted | Approved by Menno through `approve-adr`: robust utility 0.683, expected utility 0.762; Episode `a8e8fb11-e936-4cbd-9ce7-f872b1d0ee7a`. Design only. |
| 2026-10-29 | FDD alignment | Menno confirmed FDD-021 K1 to K7: the previous route and the agreement counts are derived from episodes and the snapshot holds only human-set configuration (the per-request map and its eviction count are dropped); dispatch builds a `TaskPolicy` from a copy; only `critical` escalates by tier; thresholds and bucket approvals are applied by `task-policy-routing-set` citing an adjudicated approval episode, with two new pinned shapes; the bucket prior is seeded from Laplace-smoothed agreement frequencies damped by 0.70; only `ReinforceLearner` gains the `routed_authority` check and the stale dependency note is corrected; the 20-outcome floor of the agreement gate is stated not to be binding. §4.1 to §4.5 amended to match. Re-approved 2026-10-29 under `approve-adr` (adjudicated accept, robust utility 0.699 vs. 0.044 reject and 0.110 revise, episode `797f762c-b59f-4557-af49-f1d12641e676`). The ADR-005 comparison with the original approval (0.683) classifies as **progression**: margin 0.523 to 0.589, expected utility 0.762 to 0.776, uncertainty 0.791 to 0.766, no criterion lower (soundness +0.037, gap disclosure +0.010, consequences +0.010, alternatives 0.000; the alternatives section did not change). The largest rise is soundness because the amendment fixed real design problems (the per-request snapshot writes, the dispatch mechanism and the unreachable 20-outcome gate). The inputs are the same reader's scoring both times, so this is not independent evidence. Result: `docs/policy-shapes/results/adr-021-reapproval-comparison.json`. |
