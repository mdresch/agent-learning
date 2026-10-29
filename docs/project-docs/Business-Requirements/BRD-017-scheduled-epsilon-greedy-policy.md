# BRD-017: Scheduled Epsilon-Greedy Policy Baseline

**Source ADR:** [ADR-017](../../adr/ADR-017-scheduled-epsilon-greedy-policy.md) — Accepted (2026-10-28)  
**Governing Baseline:** none approved yet; cycle `CYC-001` (ADR-035, Proposed)  
**Status:** Approved (2026-10-29, Menno) — derived from Accepted ADR-017; adjudicated via `approve-brd` (robust utility 0.732, episode `63a9fc4d-26c7-48ed-a084-6d641e01df98`).  
**Stakeholders:** Menno (Sponsor/PM/maintainer); SDK adopters who need a plain reference policy; auditors who must tell a deliberate exploration probe from a failed exploitation  

## Business Need

Whether REINFORCE, UCB (ADR-016) or Thompson sampling (ADR-015) is worth its extra machinery can only be judged against a simple reference. ADR-017 decides that reference: a low-authority policy that mostly picks the action with the best running mean and, with a probability that decays over time, picks a random action instead. Two things make it fit this repository. Every decision records whether it was a greedy pick or an exploration probe, and the exploration draw is seeded so it can be replayed. Exploration may only pick actions a human has declared reversible, so a random probe cannot run a destructive action. Nothing is built yet.

## Business Rules (BRU)

- **BRU-017-01 (Branch Transparency):** Every decision records `branch_taken` as `"exploitation"` or `"exploration"`, with the exploration rate applied (ADR-017 §4.2, Invariant 1).
- **BRU-017-02 (Safety Mask):** An exploration step selects only from the safe subset, the actions whose definition declares `"reversible": true`. An action without the flag is not safe (ADR-017 §4.1, Invariant 5).
- **BRU-017-03 (Empty Mask Forces Zero):** When no action is safe, the exploration rate is 0.0 and the policy is purely greedy. It can then stay on whichever action it pulled first; that is the stated price of the safety mask, not a defect to fix by exploring unflagged actions (ADR-017 §4.1).
- **BRU-017-04 (Flag Is A Boolean):** The `reversible` value must be a JSON boolean. Any other type raises `ValueError`, so a serialisation mistake is reported instead of silently turning exploration off (ADR-017 §4.3).
- **BRU-017-05 (Schedule):** The rate is `max(floor, eps0 / (1 + delta * t))` with `t` the total pull count. It never rises as `t` grows, never falls below the floor, and the arguments are validated: `0 <= floor <= eps0 <= 1`, `delta >= 0`, `t >= 0` (ADR-017 §4.1, §4.3, Invariant 2).
- **BRU-017-06 (Replayable Draw):** The random draw is seeded as in ADR-015 §4.3, a 64-bit seed from an HMAC over the request context, stored as a decimal string. The seed is recorded with every decision, and redrawing from it reproduces the same branch and the same exploration pick (ADR-017 §4.2, Invariant 6).
- **BRU-017-07 (Deterministic Greedy Pick):** The greedy branch picks the highest running mean with no random number. Ties go to the higher pull count, then to the lexicographically smaller `action.id` (ADR-017 §4.1; ADR-016 §4.2).
- **BRU-017-08 (Reward Scale And Cold Start):** The SDK's reward lies in [-1, 1]. Statistics are kept on [0, 1] as in ADR-016, mapped by `(value + 1) / 2`, so the two policies share one statistics record. An action with no pulls counts as the neutral reward when choosing, as ADR-017 §4.1 says (mean 0.0 on [-1, 1], which is 0.5 on [0, 1]) (FDD-017 F1).
- **BRU-017-09 (Storage Boundary):** Running means and pull counts live in `PolicySnapshot.metadata["action_statistics"]`. Zero new `LearningStore` record types (ADR-017 Invariant 3; ADR-002).
- **BRU-017-10 (Low Authority Only):** The policy operates under `DecisionAuthority.LOW`. It never grants autonomy (ADR-017 Invariant 4; ADR-001).
- **BRU-017-11 (Stays Out Of REINFORCE):** An epsilon-greedy episode never trains `ReinforceLearner` unless the maintainer decides otherwise in FDD-017 F3 (ADR-001 §4.5).
- **BRU-017-12 (Counted Once):** An episode adds to the statistics at most once, however many times it is offered to the learner. The training runner re-queries recent episodes on every run (FDD-016 E6).
- **BRU-017-13 (A Baseline, Not A Winner):** The first evidence is a run on the recorded positive-only history. It shows how the baseline behaves; it makes no claim that it is better or worse than the other policies. That needs a low-authority policy with failures, which does not exist (ADR-017 §4.3, test data).

## Stakeholder Success Metrics

| Metric | Target |
|---|---|
| Branch transparency | 100% of tested decisions record `branch_taken`, the rate applied and the seed |
| Schedule | `epsilon_at` matches hand-computed values to 1e-12; 0 increases as `t` grows; 0 values below the floor; every invalid argument rejected |
| Safety | 0 exploration picks outside the safe subset over 10,000 seeded decisions; `epsilon` is 0.0 whenever the safe subset is empty |
| Flag | 100% of non-boolean `reversible` values rejected with `ValueError` |
| Replay | 100% of tested decisions reproduce the recorded branch and pick from the recorded seed; 0 seeds lose bits through `json.dumps` and `json.loads` |
| Greedy pick | 100% of tested ties resolve by pull count then action id; an unpulled action counts as 0.5 on [0, 1] |
| Scale | 100% of rewards outside [-1, 1] or non-finite rejected; -1 maps to 0, 0 to 0.5, +1 to 1 |
| Counted once | feeding the same episodes to the learner twice leaves the statistics as after the first time |
| Stays out of REINFORCE | 0 epsilon-greedy episodes consumed by `ReinforceLearner` |
| Storage boundary | 0 new record types; 0 imports from `agent_learning.storage` in the module |

## Out of Scope

- The benchmark that compares this baseline with REINFORCE, UCB and Thompson sampling, and its metrics and report templates. ADR-017's review triage declined them: the benchmark is designed separately. It also needs a low-authority policy with failures.
- Declaring the `reversible` flag on a real action. That is a human decision about the action definition; no action carries it today, so exploration is off for every existing policy until a human sets it.
- Contextual variants (ADR-017 §6 Negative).
- Changing `ReinforceLearner`, the full-authority resolver, or the autonomy gates.
- Wiring the policy into the CLI's `task-policy-decide`.
