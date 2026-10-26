# Scored-search decision compilation (methodology #22)

**Status:** proof_of_concept · **Code:** sketch · **Data:** SYNTHETIC · **Not evidence:** this run does not validate or invalidate the methodology.

## What it shows
Coordinate ascent over criteria weights on the simplex (steps of 0.05, renormalised) maximising agreement with labeled decisions.

## Run it
```
python examples/methodologies/22-scored-search/sketch.py
```
Standard library only: no network, no credentials, no files written. All data in it is SYNTHETIC (invented for the demonstration). It is a sketch of the formulas in ADR-022 (Proposed); the methodology is not implemented in the SDK.

## What it does not show
That search beats hand-set weights on real decisions; the labels here come from hidden weights and prove nothing.

## Falsification
If search over the same weight space, scored against the same labeled set, cannot find a configuration that outperforms the hand-set weights by a meaningful margin, HYP-AL-010 is invalidated.

## Real data needed
A labeled validation set of past `DecisionFrame` instances paired with the human adjudication, plus the current hand-set weights.

## References
Ideation row #22; hypothesis: HYP-AL-010; ADR-022. Catalog entry: `examples/methodologies/catalog.json`, id 22.
