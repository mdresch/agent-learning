# ADR 020: Explicit Policy Prior Warm-Starting

## 1. Executive Brief
When initializing a new delegated decision policy (`TaskPolicy`) under `DecisionAuthority.LOW`, starting from a cold, uniform prior distribution ($\theta_a = 0.0$ across all actions) forces the system to spend dozens or hundreds of episodes re-learning foundational trade-offs that have already been resolved by structurally similar policies. This cold-start penalty wastes computational resources, delays autonomy qualification (ADR-003), and imposes unnecessary human adjudication friction.

This ADR introduces **Explicit Policy Prior Warm-Starting** (Methodology #15 from `Ideation-Document.md` §2.1, addressing `HYP-AL-008`). It specifies an operational CLI and SDK mechanism allowing a new policy to transfer converged parameters from an existing donor policy, applying confidence damping to prevent premature convergence in order to reduce the supervision a new policy needs (the effect size is to be measured under HYP-AL-008, and the ADR-003 evidence gate is unchanged).

## 2. Status
**Proposed (2026-10-25)** — Derived from `Ideation-Document.md` §2.1 (Methodology #15) and `HYP-AL-008`. Ready for multi-criteria evaluation under `approve-adr`.

## 3. Context & Problem Statement
- **Cold-Start Latency:** A standard policy requires at least 20 scored outcomes and a Wilson lower bound $\ge 0.90$ to earn autonomous execution (ADR-003). Starting from zero knowledge requires substantial initial human supervision.
- **Family Similarity:** Many policies in `agent-learning` share identical action spaces and governing dynamics (e.g. the nine advisory knowledge-area learners planned in `docs/design-notes/planning-redesign-notes.md` §4.12 (`low` authority), sharing approve, reject and revise roles; document routing gates sharing `accept`, `escalate`, `defer`).
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

### 4.4 Code design and test data
Design only: nothing below is built, and the signatures are the contract an FDD must confirm or change.
Module `src/agent_learning/warm_start.py`, pure; `task-policy-warm-start` in `cli.py` does the reads and writes.

```python
def warm_start_logits(donor_logits: Mapping[str, float], action_map: Mapping[str, str],
                      target_actions: Sequence[str], *, damping: float = 0.70) -> dict[str, float]: ...
# ValueError: damping outside (0, 1], action_map not a complete bijection onto the target actions
def provenance(donor: PolicySnapshot, damping: float, now: str) -> dict[str, object]: ...   # §4.3 keys
```

Tests (`tests/test_warm_start.py`): $\tau \in (0, 1]$ enforced, an incomplete or non-injective map is rejected, damping at 1.0 reproduces donor logits, a smaller $\tau$ gives higher softmax entropy, the donor snapshot is unchanged, and the recipient gains no autonomy credit (gate unchanged).

**Test data.** *Real:* the `approve-*` action sets give real action-map cases (the same role mapping as ADR-019). *Gap:* no real converged donor logits exist (see ADR-019), so a real transfer cannot be run; the effect size under HYP-AL-008 stays unmeasured. Needed: one policy that has actually converged. *Oracle tests:* the damping arithmetic, as arithmetic.

**Walkthrough.** [Methodology 15 in the walkthroughs](../learning-methodology-walkthroughs.md#15-warm-start-adr-020-44). It runs the sketch today; it must be rewritten against the real module once this is built.

## 5. Alternatives Considered

| Alternative | Rationale for Rejection |
|---|---|
| **Uniform Cold-Start (Status Quo)** | Wastes human oversight bandwidth re-learning identical baselines across task families. |
| **Direct Weight Copying ($\tau = 1.0$)** | Causes overconfident exploitation, starving the new task of necessary local exploration. |
| **Shared Global Weight Vector** | Multiple policies sharing a single mutable weight vector creates race conditions and violates single-policy isolation. |

## 6. Consequences

### Positive
- Expected to reduce the human supervision a new policy needs before its decisions agree with the donor's; the size of the effect is unmeasured and is what HYP-AL-008 tests. It does not shorten the ADR-003 gate (Invariant 5).
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
5. **Evidence Gate Separation:** Warm-started logits are not scored outcomes. The recipient still needs its own at least 20 scored outcomes with a Wilson lower bound $\ge 0.90$ (ADR-003) before it can earn autonomy; transferred weights never count towards that gate.

## 8. References
- `docs/project-docs/Ideation-Document.md` §2.1 (Methodology #15)
- `HYP-AL-008`: Prior transfer across task policies
- `ADR-001`: Decision Authority Model
- `ADR-002`: Storage Backend Strategy
- `ADR-003`: Evidence-Gated Autonomy Thresholds


## 9. Amendment Log

| Date | Change | Why |
|---|---|---|
| 2026-10-25 | Initial Draft | Candidate derived from Ideation Document §2.1 (Methodology #15). |
| 2026-10-28 | Review fix | Added Invariant 5: transferred weights are not scored outcomes and never count towards the ADR-003 gate. Replaced the unsourced "60-80% faster" claim with a statement that HYP-AL-008 measures the effect. |
| 2026-10-28 | Code design | Added §4.4: module layout, signatures, tests, and which real data exists and which is missing. |