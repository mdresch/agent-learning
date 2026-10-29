# BRD-018: Pairwise Preference Optimization for Discrete Action Logits

**Source ADR:** [ADR-018](../../adr/ADR-018-pairwise-preference-optimization.md) — Accepted (2026-10-28)  
**Governing Baseline:** none approved yet; cycle `CYC-001` (ADR-035, Proposed)  
**Status:** Approved (2026-10-29, Menno) — derived from Accepted ADR-018; adjudicated via `approve-brd` (robust utility 0.732, episode `1a8a82dc-d63e-4f5b-a651-1fa4299c1107`).  
**Stakeholders:** Menno (Sponsor/PM/maintainer); SDK adopters whose reviewers override a low-authority policy's proposal; auditors who must see why a logit moved  

## Business Need

When a human reviewer rejects the policy's proposal and names a different action, the signal is an ordering: the named action is better than the proposed one. Turning it into a number (+1 for one, -1 for the other) invents a scale, and the reward learner then trains on that invention. ADR-018 decides a learner that fits the policy's action logits directly to such orderings with the Bradley-Terry model, anchored to a frozen reference so a few overrides cannot drag the policy far from where it started. No reward is made up, and no foundation-model weights change. Nothing is built, and the recorded history holds no override at all.

## Business Rules (BRU)

- **BRU-018-01 (Ordinal Signal):** The learner trains on preference pairs (winner, loser). It never converts a preference into a scalar reward (ADR-018 §1, §3).
- **BRU-018-02 (Where A Pair Comes From):** A pair comes from one recorded episode in which a reviewer chose a different action from the one proposed: the chosen action wins and the proposed action loses. An accepted episode yields no pair. The exact fields that mark an override are stated in FDD-018 (G3), because the field ADR-018 names is not one the code reads (ADR-018 §4.3).
- **BRU-018-03 (Reference Anchor):** The loss includes `lambda / 2 * ||theta - theta_ref||^2`, with `lambda >= 0.05` enforced and `theta_ref` frozen at the first update. A `lambda` below 0.05 is rejected (ADR-018 §4.1, Invariant 3).
- **BRU-018-04 (Logit Clamp):** Every fitted logit lies in [-8.0, +8.0] (ADR-018 §4.1, Invariant 5).
- **BRU-018-05 (A Step That Converges):** The fit uses projected gradient descent with a step size that cannot overshoot, so the loss never increases, within a fixed iteration cap. The learner reports whether it converged and never states a result as converged when the cap was reached first (ADR-018 §4.2; FDD-018 G1).
- **BRU-018-06 (No Pairs, No Change):** With no pair, the fitted logits equal `theta_ref` (ADR-018 §4.4 tests).
- **BRU-018-07 (Deterministic, Counted Once):** The same pairs give the same logits, with no random number. An episode contributes at most one pair however many times it is offered (FDD-018 G5).
- **BRU-018-08 (Disclosed Bias):** Override pairs over-represent disagreement, because an accepted proposal yields none. The fitted logits are therefore only an adjustment relative to `theta_ref`, never an estimate of how often the policy is right (ADR-018 §4.3).
- **BRU-018-09 (Storage Boundary):** Pairs are derived from existing `Episode` records at training time, and `theta_ref` lives in `PolicySnapshot.metadata`. Zero new `LearningStore` record types (ADR-018 Invariant 2; ADR-002).
- **BRU-018-10 (Frozen Model, Low Authority):** Only discrete action logits change, and only under `DecisionAuthority.LOW` (ADR-018 Invariants 1 and 4; ADR-001).
- **BRU-018-11 (Inputs Untouched):** The learner never changes an `Episode` it reads (ADR-018 §4.4 tests).
- **BRU-018-12 (No Claim Of Effectiveness):** No real preference pair exists today: all committed approval episodes are accepted. The first evidence is that the learner leaves the logits at `theta_ref` on that history. Nothing is claimed about quality until real overrides exist. The Red Team fixtures are single adversarial frames, not pairs, and are not a source of pairs until a human labels a compliant counterpart for each (ADR-018 §3, §4.4).

## Stakeholder Success Metrics

| Metric | Target |
|---|---|
| Gradient | the analytic gradient matches a central finite difference to 1e-6 on every tested case, and the aggregated form equals the per-pair sum to 1e-12 |
| Monotone | 0 tested fits in which the loss rises from one iteration to the next, including a fit of 3,000 pairs |
| Ordering | on a consistent pair set of 3,000 pairs the fitted logits keep the order of the preferences |
| Clamp | 0 fitted logits outside [-8.0, +8.0] |
| Anchor | 100% of `lambda < 0.05` rejected; with no pairs the logits equal `theta_ref` exactly |
| Honest convergence | a fit that stops at the cap reports `converged: false` and the final gradient norm |
| Determinism | the same pairs, `theta_ref` and parameters give byte-identical logits across runs |
| Counted once | the same episodes offered twice give the same pair set and the same logits |
| Inputs | 0 episodes changed by a read |
| Storage boundary | 0 new record types; 0 imports from `agent_learning.storage` in the module |

## Out of Scope

- Showing that the learner improves decisions. It needs real overrides, none of which exist (BRU-018-12).
- Building the Red Team pair set: it needs a human to label a compliant counterpart for each adversarial frame.
- Contextual preferences or more than a pair at a time (rankings, listwise losses).
- Making the audit replay (`agent_learning.audit`) support this learner; the replay accepts only the REINFORCE run today (FDD-018 §7).
- Combining this learner with REINFORCE on one policy (FDD-018 §7, item 3).
- Wiring the learner into the CLI.
