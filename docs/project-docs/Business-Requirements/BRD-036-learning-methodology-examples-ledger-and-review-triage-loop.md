# BRD-036: Learning Methodology Examples, Best-Practice Ledger and the Review-Triage Learning Loop

**Source ADR:** [ADR-036](../../adr/ADR-036-learning-methodology-examples-ledger-and-review-triage-loop.md) — Accepted (2026-10-26)  
**Governing Baseline:** `baseline_id` none approved yet; cycle `CYC-001` (ADR-035, Proposed)  
**Status:** Approved (2026-10-26, Menno) — derived from Accepted ADR-036; adjudicated via `approve-brd` (robust utility 0.770, episode `d3e5e596-322c-4784-a6c4-7347ca6ab0cc`).  
**Stakeholders:** Menno (Sponsor/PM/maintainer); SDK adopters who need to see how each methodology behaves  

## Business Need

The project lists 32 learning methodologies but cannot show an adopter how most of them behave, cannot say which practices have worked, and does not learn from its own build loop. ADR-036 decides an example catalog, a best-practice ledger and a review-triage learning loop. This BRD states the smallest set of business rules that make those three trustworthy.

## Business Rules (BRU)

- **BRU-036-01 (Complete Catalog):** The catalog has exactly one entry for each methodology 1 to 32. A methodology's class (`runnable`, `proof_of_concept`, `documented`) follows from its state in Ideation §2.1; a mismatch is invalid (ADR-036 §4.1, Invariant 2).
- **BRU-036-02 (Examples Are Not Evidence):** Every example and sketch is labeled synthetic and not evidence, states the falsification criterion and the real data needed, and never changes a methodology's state or a hypothesis status (ADR-036 §4.2, Invariant 1).
- **BRU-036-03 (Isolation):** Examples run offline against an in-memory or temporary store and are never imported by the SDK (ADR-036 Invariant 3).
- **BRU-036-04 (Ledger Honesty):** A best-practice entry is `adopted` only on real episodes that meet the declared tier's outcome gate. Synthetic or source-document evidence can never be adopted. The ledger is append-only (ADR-036 §4.3, Invariants 4 and 5).
- **BRU-036-05 (Human Triage):** Every accept, decline or defer decision on a review finding is made by a human. The system may recommend and record (ADR-036 Invariant 6).
- **BRU-036-06 (No Invented Outcomes):** A triage record never guesses a field; unknown is valid. A record rebuilt from history is marked `reconstructed` (ADR-036 Invariant 7).
- **BRU-036-07 (Learning Stays Within Its Authority):** A learned policy may order and route verification work. It never accepts or declines a finding, because the triage policy keeps permanent human approval (ADR-036 §4.5, Invariant 9; ADR-003 Invariant 6).
- **BRU-036-08 (Storage Boundary):** All of this is stored as documents or `Episode` metadata. Zero new `LearningStore` record types (ADR-002 Invariant #2).

## Stakeholder Success Metrics

| Metric | Target |
|---|---|
| Catalog coverage | 32 of 32 methodologies have an entry; 0 class/state mismatches |
| Labeling | 100% of examples and sketches carry the synthetic, not-evidence header and a falsification note |
| Isolation | 0 imports from `examples/` into `src/`; 0 example runs that touch a real store |
| State integrity | 0 changes to a methodology state or hypothesis status caused by an example run |
| Ledger honesty | 0 `adopted` entries without `real-episodes` evidence meeting the tier gate |
| Human triage | 0 triage decisions recorded without a human decider |
| Invented data | 0 triage records with a guessed field; 100% of rebuilt records marked `reconstructed` |
| Storage boundary | 0 new record types added to `LearningStore` |

## Out of Scope

- Any claim about a methodology's effectiveness, and any change to a methodology's state (that goes through ADR-024).
- Building the unbuilt methodologies as SDK features.
- Autonomy for accepting or declining review findings.
- A `trace_id` on `Episode` (methodology #25).
- Runnable code for methodologies that are blocked, excluded, declined or have no ADR.
