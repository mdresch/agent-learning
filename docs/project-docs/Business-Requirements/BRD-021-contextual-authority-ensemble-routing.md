# BRD-021: Contextual Authority Ensemble Routing

**Source ADR:** [ADR-021](../../adr/ADR-021-contextual-authority-ensemble-routing.md) — Accepted (2026-10-28)  
**Governing Baseline:** none approved yet; cycle `CYC-001` (ADR-035, Proposed)  
**Status:** Draft (2026-10-29) — derived from Accepted ADR-021; not yet adjudicated through `approve-brd`.  
**Stakeholders:** Menno (Sponsor/PM/maintainer); SDK adopters who run a mix of routine and unusual requests through one decision task; auditors who must see why a request was handled by a learned policy or by full reasoned review  

## Business Need

Today a decision task has one fixed authority. A full-authority task reasons through a multi-criteria frame for every request, even a routine one it has decided a hundred times. A low-authority task picks from learned logits, even for an unusual request it is unsure about, and has no way to stop and ask. ADR-021 decides a router that looks at each request before anything runs: when the learned policy is confident and the context has earned trust, it takes the fast path; when the policy is unsure, the margin is thin, the complexity tier is critical, or the task is one of the governance gates, it takes the full reasoned path with a human. Routing never goes the other way for the gates. Because full-path decisions never train the learned policy, the ADR adds a guard that lets a context earn its way to the fast path through recorded agreement and a human approval. Nothing is built, and no thresholds have been calibrated.

## Business Rules (BRU)

- **BRU-021-01 (Critical Always Full):** A request with complexity tier `critical` routes to full authority whatever its entropy or margin (ADR-021 §4.1, Invariant 1).
- **BRU-021-02 (Pinned Gates):** The lifecycle baseline gates (`approve-charter`, `approve-adr`, `approve-brd`, `approve-fdd`, `approve-user-stories`, `approve-pmp`, `approve-adaptation-plan`, `approve-subsidiary-plan`, `retrospective`) and any task whose complexity profile requires human approval are pinned to full authority by an assertion. They are never routed down (ADR-021 §4.1, Invariant 5).
- **BRU-021-03 (Entropy And Margin):** The policy's Shannon entropy is measured in bits (base 2), and the margin is the gap between the two most probable actions (default threshold 0.20). A request escalates when entropy is at or above the escalation threshold or the margin is below the threshold (ADR-021 §4.1).
- **BRU-021-04 (No Hunting):** Between the escalation threshold and the de-escalation threshold, which are at least 0.15 bits apart, the route stays as it was. A request with no previous route starts at full. A configuration with a smaller gap, or with the thresholds inverted, is refused (ADR-021 §4.1, Invariant 6).
- **BRU-021-05 (Earned Fast Path):** A context bucket routes to low authority only if it has passed the agreement gate and a human has approved it. Otherwise it stays on full whatever its entropy (ADR-021 §4.1, §4.4, Invariant 7).
- **BRU-021-06 (Fail Safe):** Any input the router cannot compute or trust (a NaN or negative probability, probabilities that do not sum to 1, an empty action set, an unknown tier) routes to full and records a routing anomaly (ADR-021 §4.1, Invariant 8).
- **BRU-021-07 (Audit Provenance):** Every routed episode records the route, the entropy, the margin, the reason and the thresholds in force (ADR-021 §4.3, Invariant 3).
- **BRU-021-08 (Full Never Trains):** An episode routed to full authority is barred from policy-gradient training. An episode that never went through the router is not dropped by this rule, and an unrouted low-authority policy keeps training (ADR-021 §4.3, Invariant 2).
- **BRU-021-09 (Shadow, Not Reward):** For every full-routed request the router also records, without acting on it, what the low policy would have chosen and how uncertain it was. That record is never a reward and never enters a training batch (ADR-021 §4.4).
- **BRU-021-10 (Agreement Gate):** A bucket may be proposed for the fast path only when the agreement between the shadow action and the final adjudicated action passes the ADR-003 threshold, with the bucket's base rate reported beside it. The proposal is a recommendation; a human decides (ADR-021 §4.4; FDD-021 K4).
- **BRU-021-11 (Evidence Expires, Closed By Default):** Agreement older than `max_evidence_age_days` is dropped. The parameter has no default: until a human sets it, no bucket can be proposed (ADR-021 §4.4).
- **BRU-021-12 (Promotion Seeds Without A Gradient):** On approval a bucket's starting distribution is seeded from its observed agreement frequencies, damped as in ADR-020, with its provenance. The seed is not scored outcomes. If the seeded distribution still fails the entropy or margin test, the bucket stays on full (ADR-021 §4.4).
- **BRU-021-13 (Human Control Of Thresholds And Approvals):** Routing thresholds and bucket approvals change only through a recorded human decision, and a threshold change re-checks every approved bucket (ADR-021 §4.1, Invariant 9; FDD-021 K4).
- **BRU-021-14 (Stored Policy Unchanged):** Routing decides which authority handles a request; it never rewrites the stored policy's authority. Per-request state is derived from episodes, and the snapshot holds only human-set routing configuration (ADR-021 Invariant 4; FDD-021 K1, K2).
- **BRU-021-15 (No Claim Of Effectiveness):** No thresholds are calibrated and no request has been routed. The first evidence is arithmetic and refusals; nothing is claimed about saved cost or latency (ADR-021 §4.5, test data).

## Stakeholder Success Metrics

| Metric | Target |
|---|---|
| Entropy and margin | entropy of the uniform distribution over 4 actions is 2.0 bits; entropy and margin equal hand-computed values to 1e-4 on tested distributions |
| Critical and pinned | 0 routes to low for a `critical` request or a pinned task across every tested input; every listed gate and every `requires_human_approval` profile is pinned |
| Hysteresis | 0 route changes inside the deadband; a first call inside the deadband routes full; 100% of configs with a gap under 0.15 bits or inverted thresholds refused |
| Earned fast path | 0 routes to low for a bucket that is not approved, whatever its entropy |
| Fail safe | 100% of invalid inputs route full with a routing anomaly recorded |
| Audit | 100% of routed episodes carry the route, entropy, margin, reason and thresholds |
| Gradient exclusion | 0 full-tagged episodes consumed by `ReinforceLearner`; 100% of untagged episodes with a log-probability still consumed |
| Shadow | 0 shadow records read by a learner or counted as a reward |
| Gate arithmetic | the agreement proposal equals the `wilson_lower_bound` of the agreements; the bucket base rate is reported with it; with `max_evidence_age_days` unset 0 buckets are proposed |
| Stored policy | 0 stored snapshots changed by routing; the dispatched policy is a copy |
| Storage boundary | 0 new record types; 0 imports from `agent_learning.storage` in the routing module |

## Out of Scope

- Calibrating `tau_esc`, `tau_deesc` and the margin threshold. That needs real mixed-difficulty traffic through a hybrid policy; none exists.
- Router KPIs, a benchmark, a re-validation cadence and named owners: ADR-021's review triage declined them.
- Measuring the saving in LLM tokens or latency (ADR-021 §6).
- An LLM-based router, cascade fallback after failure, and static configuration as the only option (ADR-021 §5).
- Wiring the router into the `task-policy-decide` command, which dispatches a stored policy's authority today.
- Changing the full-authority resolver or the ADR-003 gate.
