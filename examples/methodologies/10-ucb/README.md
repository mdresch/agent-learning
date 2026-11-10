# UCB (methodology #10)

**Status:** runnable · **Code:** SDK · **Data:** SYNTHETIC · **Not evidence:** this example does not validate or invalidate the methodology.

## What it shows
Deterministic Upper Confidence Bound selection (`UCBPolicy`) and count-based updating (`UCBLearner`) with deterministic tie-breaking (pull count, then action id).

## Run it
```
python examples/methodologies/10-ucb/example.py
```
It needs the package installed and nothing else: no network, no credentials, no files written. All data in it is SYNTHETIC (invented for the demonstration).

## What it does not show
That UCB crosses the autonomy gate that defeated REINFORCE; no gate is evaluated.

## Falsification
If Thompson or UCB, run on the same real `validate-intent-foundation` 146-episode dataset that defeated REINFORCE, also fails to cross the gate, HYP-AL-009 is invalidated.

## Real data needed
The real `validate-intent-foundation` episodes with outcomes, scored against the declared autonomy gate.

## References
Ideation row #10; hypothesis: HYP-AL-009; ADR: ADR-016. Catalog entry: `examples/methodologies/catalog.json`, id 10.
