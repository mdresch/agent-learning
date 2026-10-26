# Warm-start / prior transfer (methodology #15)

**Status:** proof_of_concept · **Code:** sketch · **Data:** SYNTHETIC · **Not evidence:** this run does not validate or invalidate the methodology.

## What it shows
Donor logits are mapped to a recipient through an explicit action mapping and damped by `tau` (default 0.70), which flattens the starting distribution.

## Run it
```
python examples/methodologies/15-warm-start/sketch.py
```
Standard library only: no network, no credentials, no files written. All data in it is SYNTHETIC (invented for the demonstration). It is a sketch of the formulas in ADR-020 (Proposed); the methodology is not implemented in the SDK.

## What it does not show
That a warm-started policy reaches the gate in fewer episodes than a cold start; no training is run.

## Falsification
If a policy warm-started from a converged source reaches its autonomy gate in the same or more episodes than an equivalent cold-started policy, HYP-AL-008 is invalidated.

## Real data needed
A converged real donor policy, a structurally similar new policy, and episode counts to the gate for warm and cold starts.

## References
Ideation row #15; hypothesis: HYP-AL-008; ADR-020. Catalog entry: `examples/methodologies/catalog.json`, id 15.
