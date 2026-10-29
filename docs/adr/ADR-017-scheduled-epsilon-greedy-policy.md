# ADR 017: Scheduled Epsilon-Greedy Policy Baseline

## 1. Executive Brief
To evaluate whether advanced exploration mechanisms (REINFORCE policy gradients, UCB confidence bounds, Thompson posterior sampling) genuinely provide value over simple empirical baselines, the repository requires a classical, mathematically transparent exploration algorithm.

This ADR introduces the **Scheduled Epsilon-Greedy Policy Baseline** (Methodology #11 from `Ideation-Document.md` §2.1). By combining running empirical mean tracking with a decaying exploration schedule ($\epsilon_t$) and explicit exploration-branch logging in episode metadata, this policy establishes a rigorous, low-complexity reference standard for all discrete bandit policies in `agent-learning`.

## 2. Status
**Accepted (2026-10-28, Menno)** — Derived from `Ideation-Document.md` §2.1 (Methodology #11). Approved as a design through `approve-adr` (robust utility 0.667, expected utility 0.747; Episode `dea2df98-8adb-49e2-9b7f-f690262756a7`). Amazon Q reviewed this text in PR #36. Nothing is built; the gaps named in the code-design section stay open.

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
Ties in $\arg\max_{a \in A} \bar{X}_a$ are broken deterministically as in ADR-016 §4.2: higher pull count first, then the lexicographically smaller `action.id`; the greedy pick itself draws no random number. The SDK's `Reward.value` lies in $[-1, 1]$. The statistics are kept on $[0, 1]$, mapped by $r = (\text{value} + 1)/2$, in the record ADR-016 uses (FDD-017 F1, F6), so the greedy argmax is unchanged. An action with $N_a = 0$ counts as the neutral mean $0.5$ when choosing, which is the $0.0$ of the $[-1, 1]$ scale.
With probability $1 - \epsilon_t$ (Exploitation):
$$a^* = \arg\max_{a \in A} \bar{X}_a$$
With probability $\epsilon_t$ (Exploration):
$$a^* \sim \text{UniformRandom}(A_{\text{safe}})$$
Where $A_{\text{safe}} \subseteq A$ is the safety-masked subset of benign/reversible actions: those whose action definition declares `"reversible": true`. The flag is declared by a human in the action definition, so setting or changing it is a reviewed change to that definition; an action without the flag is treated as not safe.
The branch itself is decided by a seeded draw $u$, the first number of the generator on every decision, with exploration when $u < \epsilon_t$ (FDD-017 F4). The uniform draw is made with a PRNG seeded exactly as in ADR-015 §4.3 (HMAC-SHA256 over `request_id || timestamp`, keyed by `policy_id`, 64-bit seed), so an exploration step is replayable. If $A_{\text{safe}} = \emptyset$ (all candidate actions carry destructive or irreversible impact), $\epsilon_t$ is forced to $0.0$, disabling random exploration entirely. With no safe action the policy is purely greedy and can stay on whichever action it pulled first; that is the stated price of the safety mask, not a defect to be fixed by exploring unflagged actions.

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
    "branch_taken": "exploitation",
    "prng_seed": "8472910384719203841",
    "empirical_means": {
      "action_a": 0.88,
      "action_b": 0.05,
      "action_c": 0.22
    }
  }
}
```
`branch_taken` is `"exploitation"` or `"exploration"`. `empirical_means` is on $[0, 1]$ and shows $0.5$ for an action with no pulls. The record also holds `request_id`, `timestamp`, `total_pulls` and `chosen`, so the seed can be re-derived and the decision replayed. The action ids above are generic placeholders, not those of any real policy. `prng_seed` is a decimal **string**: a 64-bit integer above $2^{53} - 1$ loses its low bits in the double-precision JSON parsers used by Cosmos DB and common dashboards, which would break replay.

### 4.3 Code design and test data
Design only: nothing below is built, and the signatures are the contract an FDD must confirm or change.
Module `src/agent_learning/policy/epsilon_greedy.py`, implementing `Policy`, plus an `EpsilonGreedyLearner(Learner)` that shares the `action_statistics` update with ADR-016.

```python
def epsilon_at(t: int, eps0: float, delta: float, floor: float) -> float: ...   # harmonic, §4.1
# raises ValueError unless 0 <= floor <= eps0 <= 1, delta >= 0 and t >= 0
class EpsilonGreedyPolicy(Policy):
    def choose(self, state=None, *, request_id: str | None = None, timestamp: str | None = None) -> Decision: ...   # absent values are supplied and recorded
    # metadata: branch_taken, exploration_rate_applied, prng_seed, empirical_means
```

`Decision.logprob` is `None` and `Decision.probabilities` hold the real selection probabilities; `EpsilonGreedyPolicy.apply_update` raises, because there are no logits. `eps0`, `delta` and `floor` are required arguments with no default, because the ADR names no values. The check of `reversible` runs when the policy is built and when a snapshot is read, as well as in `choose`. The learner and the UCB learner share one statistics record and one update function (`policy/action_statistics.py`), including the counted-once rule of ADR-016 (`consumed_episode_ids`).

`A_safe` is read from `Action.parameters["reversible"] is True`. The value must be a JSON boolean: any other type (for example the string `"true"`) raises `ValueError` rather than being read as "not safe", so a serialisation mistake is reported instead of silently forcing $\epsilon_t = 0$. Existing action definitions (for example `approve-adr.actions.json`) carry empty `parameters`, so no action is safe today and $\epsilon_t$ is forced to 0 until a human declares the flag.

Tests (`tests/test_epsilon_schedule.py`, `tests/test_epsilon_safety_mask.py`, `tests/test_epsilon_policy.py`, `tests/test_epsilon_learner.py`, `tests/test_epsilon_reinforce_guard.py`, `tests/test_epsilon_positive_only.py`, split by story in Epic 17): an unpulled action counts as the neutral mean, offering the same episodes twice counts them once, `epsilon_at` rejects `delta < 0`, `eps0 < floor` and values outside [0, 1], exploitation ties resolve by pull count then action id, an unpulled action has mean 0.0, a stored `prng_seed` round-trips through JSON as a string without loss, the schedule is non-increasing and never below the floor, an empty $A_{\text{safe}}$ forces $\epsilon = 0$, exploration never selects an unflagged action, the recorded seed reproduces the draw, `branch_taken` is always present.

**Test data.** *Real:* none specific; its role is the baseline run on the same replay as ADR-015 and ADR-016, so the three can be compared on identical history. *Gap:* the `reversible` flag has never been declared on a real action; that human decision is needed first. *Oracle tests:* the schedule values, checked by hand.

**Walkthrough.** [Methodology 11 in the walkthroughs](../learning-methodology-walkthroughs.md#11-epsilon-greedy-adr-017-43). It runs the sketch today; it must be rewritten against the real module once this is built.

## 5. Alternatives Considered

| Alternative | Rationale for Rejection |
|---|---|
| **Constant Epsilon ($\epsilon_t = \text{const}$)** | Continues random exploration indefinitely even after policy convergence, dragging down long-term autonomy scores. |
| **Silent Random Branching** | Obscures whether a sub-optimal choice was an intentional exploration probe or an exploitation failure, corrupting audit trails. |

## 6. Consequences

### Positive
- Provides a clean, gradient-free reference baseline for bandit research, with a fixed default schedule ($\epsilon_0$, $\delta$, $\epsilon_{\text{floor}}$) and no learning rate or baseline to tune.
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
| 2026-10-28 | External review triage | Cold start ($\bar{X}_a = 0$ when unpulled) and the exploitation tie-break (pull count, then action id, as ADR-016) specified; `epsilon_at` bounds; `prng_seed` stored as a string because 64-bit integers lose precision in Cosmos DB and browser JSON parsers; placeholder action ids and no comment inside the JSON; reward scale stated; "zero-hyperparameter" reworded. Declined: benchmark metrics and report templates (the benchmark is designed separately), an invented owner and cadence for the `reversible` flag, and a claimed missing minus sign (the formula is correct). |
| 2026-10-28 | Amazon Q review, round 2 | `reversible` must be a JSON boolean; any other type raises instead of silently reading as not safe. |
| 2026-10-28 | Accepted | Approved by Menno through `approve-adr`: robust utility 0.667, expected utility 0.747; Episode `dea2df98-8adb-49e2-9b7f-f690262756a7`. Design only. |
| 2026-10-29 | FDD alignment | Menno confirmed FDD-017 F1 to F7: statistics on [0, 1] shared with ADR-016 with an unpulled action at the neutral 0.5; `choose` arguments optional; `Decision.logprob` `None` with real selection probabilities in `probabilities`; the branch decided by a seeded draw (the greedy pick still draws none); schedule arguments required with no default; one shared statistics module with the counted-once rule; `reversible` validated at construction. §4.1, §4.2 and §4.3 amended to match. Re-approved 2026-10-29 under `approve-adr` (adjudicated accept, robust utility 0.678 vs. 0.044 reject and 0.110 revise, episode `a8a28c10-84e3-48cf-8067-70625688334a`). The ADR-005 comparison with the original approval (0.667) classifies as **progression**: margin 0.494 to 0.568, expected utility 0.747 to 0.757, uncertainty 0.803 to 0.785, no criterion lower (soundness +0.010, consequences +0.010, gap disclosure +0.019, alternatives 0.000; this ADR still lists two alternatives, so that criterion did not move). The inputs are the same reader's scoring both times, so this is not independent evidence. Result: `docs/policy-shapes/results/adr-017-reapproval-comparison.json`. |
