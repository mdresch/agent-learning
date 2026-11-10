# Scored-search decision compilation (methodology #22)

**Status:** runnable · **Code:** SDK · **Data:** SYNTHETIC · **Not evidence:** this example does not validate or invalidate the methodology.

## What it shows
Coordinate ascent over criteria weights on the simplex via `agent_learning_ext.weight_compiler`, maximizing accuracy + margin over historical `LabeledFrame` records with strict holdout safety validation.

## Run it
```
python examples/methodologies/22-scored-search/example.py
```
It needs the package installed and nothing else: no network, no credentials, no files written. All data in it is SYNTHETIC (invented for the demonstration).

## What it does not show
That search beats hand-set weights on real decisions; the labels here come from hidden weights and prove nothing.

## Falsification
If search over the same weight space, scored against the same labeled set, cannot find a configuration that outperforms the hand-set weights by a meaningful margin, HYP-AL-010 is invalidated.

## Real data needed
A labeled validation set of past `DecisionFrame` instances paired with the human adjudication, plus the current hand-set weights.

## References
Ideation row #22; hypothesis: HYP-AL-010; ADR: ADR-022. Catalog entry: `examples/methodologies/catalog.json`, id 22.
