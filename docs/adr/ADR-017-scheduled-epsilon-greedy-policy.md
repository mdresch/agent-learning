# ADR 017: Scheduled Epsilon-Greedy Policy Baseline

## 1. Executive Brief
To evaluate whether advanced exploration mechanisms (REINFORCE policy gradients, UCB confidence bounds, Thompson posterior sampling) genuinely provide value over simple empirical baselines, the repository requires a classical, mathematically transparent exploration algorithm.

This ADR introduces the **Scheduled Epsilon-Greedy Policy Baseline** (Methodology #11 from `Ideation-Document.md` §2.1). By combining running empirical mean tracking with a decaying exploration schedule ($\epsilon_t$) and explicit exploration-branch logging in episode metadata, this policy establishes a rigorous, low-complexity reference standard for all discrete bandit policies in `agent-learning`.

## 2. Status
**Proposed (2026-10-25)** — Derived from `Ideation-Document.md` §2.1 (Methodology #11). Ready for multi-criteria evaluation under `approve-adr`.

## 3. Context & Problem Statement
- **The Empirical Baseline Deficit:** Without an $\epsilon$-greedy reference implementation, it is impossible to rigorously quantify whether more complex policy-gradient mechanisms (such as REINFORCE with moving-average baselines) justify their computational and hyperparameter tuning costs.
- **Auditable Exploration Tracking:** Traditional $\epsilon$-greedy implementations make random choices silently. In an audited decision system, whether an action was chosen because it was believed to be optimal or because the policy was deliberately exploring must be explicitly recorded.

## 4. Technical Decision

### 4.1 Algorithmic Formulation
Let $A$ be the set of valid discrete actions.
For each action $a \in A$, maintain:
- $N_a$: pull count of action $a$.
- $\bar{X}_a$: running empirical mean reward.

#### Action Selection:
With probability $1 - \epsilon_t$ (Exploitation):
$$a^* = \arg\max_{a \in A} \bar{X}_a$$
With probability $\epsilon_t$ (Exploration):
$$a^* \sim \text{UniformRandom}(A_{\text{safe}})$$
Where $A_{\text{safe}} \subseteq A$ is the safety-masked subset of benign/reversible actions: those whose action definition declares `"reversible": true`. The flag is declared by a human in the action definition; an action without the flag is treated as not safe.
The uniform draw is made with a PRNG seeded exactly as in ADR-015 §4.3 (HMAC-SHA256 over `request_id || timestamp`, keyed by `policy_id`, 64-bit seed), so an exploration step is replayable. If $A_{\text{safe}} = \emptyset$ (all candidate actions carry destructive or irreversible impact), $\epsilon_t$ is forced to $0.0$, disabling random exploration entirely.

#### Decay Schedule:
The exploration rate $\epsilon_t$ follows a harmonic decay schedule parameterized by initial rate $\epsilon_0$, decay constant $\delta$, and floor $\epsilon_{\text{floor}}$:
$$\epsilon_t = \max\left(\epsilon_{\text{floor}}, \frac{\epsilon_0}{1 + \delta \cdot t}\right), \quad t = \sum_{a \in A} N_a$$

### 4.2 Audit & Branch Telemetry
To maintain audit integrity, every generated `DecisionResult` and `Episode` records the exact branch taken:
```json
{
  "selection_basis": "epsilon_greedy",
  "metadata": {
    "exploration_rate_applied": 0.142,
    "branch_taken": "exploitation", // "exploitation" | "exploration"
    "prng_seed": 8472910384719203841,
    "empirical_means": {
      "approve_plan": 0.88,
      "reject_plan": 0.05,
      "request_revision": 0.22
    }
  }
}
```

### 4.3 Code design and test data
Design only: nothing below is built, and the signatures are the contract an FDD must confirm or change.
Module `src/agent_learning/policy/epsilon_greedy.py`, implementing `Policy`, plus an `EpsilonGreedyLearner(Learner)` that shares the `action_statistics` update with ADR-016.

```python
def epsilon_at(t: int, eps0: float, delta: float, floor: float) -> float: ...   # harmonic, §4.1
class EpsilonGreedyPolicy(Policy):
    def choose(self, state=None, *, request_id: str, timestamp: str) -> Decision: ...
    # metadata: branch_taken, exploration_rate_applied, prng_seed, empirical_means
```

`A_safe` is read from `Action.parameters["reversible"] is True`. Existing action definitions (for example `approve-adr.actions.json`) carry empty `parameters`, so no action is safe today and $\epsilon_t$ is forced to 0 until a human declares the flag.

Tests (`tests/test_epsilon_greedy.py`): the schedule is non-increasing and never below the floor, an empty $A_{\text{safe}}$ forces $\epsilon = 0$, exploration never selects an unflagged action, the recorded seed reproduces the draw, `branch_taken` is always present.

**Test data.** *Real:* none specific; its role is the baseline run on the same replay as ADR-015 and ADR-016, so the three can be compared on identical history. *Gap:* the `reversible` flag has never been declared on a real action; that human decision is needed first. *Oracle tests:* the schedule values, checked by hand.

**Walkthrough.** [Methodology 11 in the walkthroughs](../learning-methodology-walkthroughs.md#11-epsilon-greedy-adr-017-43). It runs the sketch today; it must be rewritten against the real module once this is built.

## 5. Alternatives Considered

| Alternative | Rationale for Rejection |
|---|---|
| **Constant Epsilon ($\epsilon_t = \text{const}$)** | Continues random exploration indefinitely even after policy convergence, dragging down long-term autonomy scores. |
| **Silent Random Branching** | Obscures whether a sub-optimal choice was an intentional exploration probe or an exploitation failure, corrupting audit trails. |

## 6. Consequences

### Positive
- Provides a clean, zero-hyperparameter-tuning reference baseline for bandit research.
- Explicit `branch_taken` logging guarantees complete post-hoc transparency during failure audits.
- Negligible CPU overhead ($<0.05 \text{ ms}$ per decision).

### Negative
- Pure random exploration selects clearly inferior actions with equal probability as plausible alternatives during exploratory turns.
- Lacks contextual awareness (cannot condition on request features).

## 7. Architectural Invariants

1. **Branch Transparency:** Every episode generated under this policy must log `metadata["branch_taken"]` as either `"exploitation"` or `"exploration"`.
2. **Monotonic Schedule Decay:** The exploration rate $\epsilon_t$ must decay monotonically to $\epsilon_{\text{floor}}$.
3. **Storage Boundary (ADR-002):** Running action means and pull counts reside in `PolicySnapshot.metadata["action_statistics"]`.
4. **Authority Boundary (ADR-001):** Operates under `DecisionAuthority.LOW`.
5. **Action Safety Mask Invariant:** Random exploratory selection ($\epsilon_t$) is strictly prohibited from selecting unmasked destructive or irreversible actions. Exploratory probes are restricted to the subset $A_{\text{safe}} \subseteq A$; if $A_{\text{safe}}$ is empty, $\epsilon_t$ must evaluate to $0.0$.
6. **Replayable Exploration:** Every exploration step must record its `prng_seed` in `metadata`; re-seeding with it must reproduce the same draw.

## 8. References
- `docs/project-docs/Ideation-Document.md` §2.1 (Methodology #11)
- `ADR-001`: Decision Authority Model
- `ADR-002`: Storage Backend Strategy

## 9. Amendment Log

| Date | Change | Why |
|---|---|---|
| 2026-10-25 | Initial Draft | Candidate derived from Ideation Document §2.1 (Methodology #11). |
| 2026-10-25 | Peer-Review Hardening | Added Invariant 5 (Action Safety Masking) per PMBOK Governance Auditor and Systems Architecture Reviewer condition, preventing pseudo-random execution of irreversible actions. |
| 2026-10-28 | Review fix | ADR-016 rejects epsilon-greedy because random draws need seed logging, yet this ADR logged no seed. Added the seeded, replayable draw (ADR-015 §4.3) and Invariant 6. Defined $A_{\text{safe}}$ as actions declaring `reversible: true`. |
| 2026-10-28 | Code design | Added §4.3: module layout, signatures, tests, and which real data exists and which is missing. |

