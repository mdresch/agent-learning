# BRD-022: Scored-Search Decision Configuration Compilation

**Source ADR:** [ADR-022](../../adr/ADR-022-scored-search-decision-configuration-compilation.md) — Accepted (2026-10-28)  
**Governing Baseline:** none approved yet; cycle `CYC-001` (ADR-035, Proposed)  
**Status:** Draft (2026-10-29) — derived from Accepted ADR-022; not yet adjudicated through `approve-brd`.  
**Stakeholders:** Menno (Sponsor/PM/maintainer); authors of decision frames who set criteria weights by hand; reviewers who adjudicate full-authority decisions; auditors who must see why a weight is what it is  

## Business Need

The weights that decide a full-authority decision (how much "completeness" counts against "consistency") are chosen by hand and defended by intuition. ADR-022 decides an offline step that searches for better weights against a set of past decisions a human already settled, tests the result on decisions the search never saw, and offers it as a proposal only if it does better than the weights in force. Nothing runs during an online decision: the chosen weights are frozen, and a person adopts them by a recorded decision. The hard constraints of a decision are never touched. Nothing is built, and the recorded history cannot show an improvement, because every recorded label agrees with the resolver.

## Business Rules (BRU)

- **BRU-022-01 (Offline Only):** The search runs only as a batch step. An online decision reads frozen values and runs no search, exploration or optimisation (ADR-022 §4.3, Invariant 1).
- **BRU-022-02 (Real Resolver Scores It):** A candidate set of weights is scored by running the real `DecisionResolver` on each labelled frame with the weights replaced. The compiler has no second scoring function (ADR-022 §4.4).
- **BRU-022-03 (Weights Stay Valid):** Compiled weights are all positive, sum to 1.0 within 1e-9, and none is below the floor of one search step, because the resolver rejects a weight of zero or less (ADR-022 Invariant 2; FDD-022 L2).
- **BRU-022-04 (Constraints Untouched):** The search changes criteria weights only. It never changes a hard constraint, an option, evidence or a ruled-out result, so an option that is ruled out never wins (ADR-022 Invariant 3).
- **BRU-022-05 (Held-Out Honesty):** The labelled set is split before the search with a recorded seed. Reported accuracy is the accuracy on the held-out part only, and the weights in force are scored on the same held-out part as the baseline (ADR-022 §4.1).
- **BRU-022-06 (Labels Come First):** A label is usable only if it was recorded before the compiled weights were proposed. A label recorded at or after the proposal time makes the proposal invalid (ADR-022 §4.1 Label independence).
- **BRU-022-07 (Only A Real Improvement):** Compiled weights are proposed only when their held-out accuracy is strictly greater than that of the weights in force. Otherwise the compiler reports no improvement and changes nothing (ADR-022 Invariant 5; FDD-022 L4).
- **BRU-022-08 (Deterministic):** The same frames, labels, seed and parameters give the same weights and the same report. There is no random number apart from the seeded split (ADR-022 §4.4).
- **BRU-022-09 (A Proposal, Adopted By A Human):** A compiled result is a proposal file. It takes effect only through a recorded human decision that a command checks, which stores a new snapshot version (ADR-022 Invariant 6; FDD-022 L6).
- **BRU-022-10 (Storage Boundary):** The adopted weights and their provenance live in `PolicySnapshot.metadata`. Zero new `LearningStore` record types (ADR-022 Invariant 4; ADR-002).
- **BRU-022-11 (Run Time Disclosed):** The search time is measured and reported, not assumed, and the number of sweeps and restarts is bounded (FDD-022 L5).
- **BRU-022-12 (No Claim Of Improvement):** The recorded history holds only labels that agree with the resolver, so the baseline accuracy is 100% by construction. The first evidence is that the compiler reports no improvement there. Nothing is claimed about better weights (ADR-022 §4.4, test data).

## Stakeholder Success Metrics

| Metric | Target |
|---|---|
| Real resolver | every candidate is scored through `DecisionResolver.resolve`; 0 scoring paths outside it |
| Valid weights | 100% of compiled weights positive, summing to 1.0 within 1e-9, none below the step floor |
| Constraints | 0 options that were ruled out chosen under any candidate weights; 0 constraints, options or evidence changed |
| Held-out | 0 held-out items seen by the search; the split reproduces from its seed |
| Labels | 100% of proposals with a label time at or after the proposal time refused |
| Improvement | 0 proposals whose held-out accuracy is not strictly above the baseline |
| Deterministic | identical inputs give byte-identical weights and report across runs |
| Search | on a synthetic suite with known weights the search recovers weights within 0.05 of them and raises held-out accuracy |
| Adoption | 100% of adoptions cite an adjudicated accepted approval episode; 0 unreferenced changes of weights |
| Runtime | an online decision runs no search; the compile time is recorded with the proposal |
| Storage boundary | 0 new record types; 0 imports from `agent_learning.storage` in the compiler module |

## Out of Scope

- Searching the uncertainty penalty and the minimum margin. ADR-022 names them in the configuration but the search of its §4.2 steps the weights only; they stay at the frame's values and are recorded (FDD-022 L3).
- Nelder-Mead on the smoothed surrogate, the secondary engine of ADR-022 §4.2, and k-fold validation for small sets.
- Changing `DecisionResolver`, the frames' hard constraints, or the ADR-003 gate.
- A shown improvement on real data: it needs decisions where a human disagreed with the resolver, and none exist.
- Prompt compilation or LLM teleprompting (ADR-022 §5).
