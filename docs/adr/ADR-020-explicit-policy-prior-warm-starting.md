# ADR 020: Explicit Policy Prior Warm-Starting

## 1. Executive Brief
When initializing a new delegated decision policy (`TaskPolicy`) under `DecisionAuthority.LOW`, starting from a cold, uniform prior distribution ($\theta_a = 0.0$ across all actions) forces the system to spend dozens or hundreds of episodes re-learning foundational trade-offs that have already been resolved by structurally similar policies. This cold-start penalty wastes computational resources, delays autonomy qualification (ADR-003), and imposes unnecessary human adjudication friction.

This ADR introduces **Explicit Policy Prior Warm-Starting** (Methodology #15 from `Ideation-Document.md` §2.1, addressing `HYP-AL-008`). It specifies an operational CLI and SDK mechanism allowing a new policy to transfer converged parameters from an existing donor policy, applying confidence damping to prevent premature convergence while accelerating time-to-autonomy by $60\text{--}80\%$.

## 2. Status
**Proposed (2026-10-25)** — Derived from `Ideation-Document.md` §2.1 (Methodology #15) and `HYP-AL-008`. Ready for multi-criteria evaluation under `approve-adr`.

## 3. Context & Problem Statement
- **Cold-Start Latency:** A standard policy requires at least 20 scored outcomes and a Wilson lower bound $\ge 0.90$ to earn autonomous execution (ADR-003). Starting from zero knowledge requires substantial initial human supervision.
- **Family Similarity:** Many policies in `agent-learning` share identical action spaces and governing dynamics (e.g. 9 PMBOK subsidiary approval gates sharing `approve`, `reject`, `request_revision`; document routing gates sharing `accept`, `escalate`, `defer`).
- **The Overconfidence Trap:** Directly copying raw converged weights from a donor policy can transfer excessive confidence, extinguishing necessary local exploration in the target task's unique context.

## 4. Technical Decision

### 4.1 Warm-Start Transfer Formulation
Let $P_{\text{donor}}$ be a converged donor policy snapshot with action parameter vector $\boldsymbol{\theta}_{\text{donor}}$.
Let $P_{\text{target}}$ be a new recipient policy with action set $A_{\text{target}}$.
An explicit action mapping function $m: A_{\text{target}} \rightarrow A_{\text{donor}}$ maps recipient actions to donor actions.

The recipient policy's initial parameters $\boldsymbol{\theta}_{\text{target}}$ are initialized via:
$$\theta_{\text{target}, a} = \theta_{\text{donor}, m(a)} \cdot \tau_{\text{damping}}$$
Where:
- $\tau_{\text{damping}} \in (0.0, 1.0]$ is the **Confidence Damping Factor** (default $\tau = 0.70$).
- Damping compresses the logit dynamic range, flattening the initial softmax distribution to guarantee that the recipient policy retains adequate exploratory entropy:
  $$\pi_{\text{target}}(a) \propto \exp\left( \tau_{\text{damping}} \cdot \theta_{\text{donor}, m(a)} \right)$$

### 4.2 CLI Ergonomics & Provenance Lineage
Warm-starting is executed via the `agent-learn` CLI:
```powershell
python -m agent_learning.cli task-policy-warm-start \
  --agent-id agent-learning-governance \
  --target-task-id approve-risk-plan \
  --donor-task-id approve-quality-plan \
  --damping 0.75 \
  --action-map '{"approve_plan": "approve_plan", "reject_plan": "reject_plan", "request_revision_before_decision": "request_revision_before_decision"}'
```

### 4.3 Storage & Invariant Boundary
- The recipient snapshot records the transfer in `PolicySnapshot.metadata`:
  ```json
  {
    "warm_start_donor_policy_id": "9a7d3f12-...",
    "warm_start_donor_task_id": "approve-quality-plan",
    "warm_start_donor_version": 4,
    "warm_start_damping_factor": 0.75,
    "warm_started_at": "2026-10-25T20:15:00Z"
  }
  ```
- **Strict Isolation:** Donor and recipient snapshots remain entirely decoupled in `LearningStore`. Subsequent episodes and gradient updates to the recipient never mutate the donor snapshot.

## 5. Alternatives Considered

| Alternative | Rationale for Rejection |
|---|---|
| **Uniform Cold-Start (Status Quo)** | Wastes human oversight bandwidth re-learning identical baselines across task families. |
| **Direct Weight Copying ($\tau = 1.0$)** | Causes overconfident exploitation, starving the new task of necessary local exploration. |
| **Shared Global Weight Vector** | Multiple policies sharing a single mutable weight vector creates race conditions and violates single-policy isolation. |

## 6. Consequences

### Positive
- Reduces time-to-autonomy for new policy instances by an estimated $60\text{--}80\%$.
- Damping factor guarantees bounded entropy and prevents premature policy lock-in.
- Unbroken provenance lineage tracks which policies seeded which downstream learners.

### Negative
- Requires human operator to select a valid, structurally comparable donor policy.
- An inappropriate donor policy can introduce negative transfer bias, requiring corrective episodes to un-learn.

## 7. Architectural Invariants

1. **Strict Snapshot Isolation:** Updating a warm-started recipient policy must never mutate the donor policy snapshot or its stored episodes.
2. **Mandatory Damping:** $\tau_{\text{damping}}$ must be bounded in $(0.0, 1.0]$; raw undamped transfer ($\tau > 1.0$) is prohibited.
3. **Action Space Compatibility:** The transfer requires an exact action-set match or an explicit complete bijection mapping across all recipient actions.
4. **Storage Law (ADR-002):** Transfer metadata is stored exclusively in `PolicySnapshot.metadata` with zero schema modifications.

## 8. References
- `docs/project-docs/Ideation-Document.md` §2.1 (Methodology #15)
- `HYP-AL-008`: Prior transfer across task policies
- `ADR-001`: Decision Authority Model
- `ADR-002`: Storage Backend Strategy
- `ADR-003`: Evidence-Gated Autonomy Thresholds

