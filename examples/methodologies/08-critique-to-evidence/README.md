# Critique-to-evidence (methodology #8)

**Status:** proof_of_concept · **Code:** sketch · **Data:** SYNTHETIC · **Not evidence:** this run does not validate or invalidate the methodology.

## What it shows
Critique tags of the form `- [criterion: id] -0.20: rationale` are parsed into evidence deltas, clipped by a support limit, and applied to criterion scores.

## Run it
```
python examples/methodologies/08-critique-to-evidence/sketch.py
```
Standard library only: no network, no credentials, no files written. All data in it is SYNTHETIC (invented for the demonstration). It is a sketch of the formulas in ADR-014 (Accepted); the methodology is not implemented in the SDK.

## What it does not show
That reflection converges faster than REINFORCE on real episodes; no REINFORCE comparison is run.

## Falsification
Implement a reflection-based update path; if it does not converge faster or more sample-efficiently than REINFORCE on the same real episode data, the hypothesis is invalidated (HYP-AL-005).

## Real data needed
Real episodes that carry textual critiques (for example Red Team critiques) together with their scored outcomes.

## References
Ideation row #8; hypothesis: HYP-AL-005 (reflection-style update converges faster than REINFORCE); ADR-014. Catalog entry: `examples/methodologies/catalog.json`, id 8.
