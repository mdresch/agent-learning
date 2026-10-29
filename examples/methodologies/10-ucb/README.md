# UCB (methodology #10)

**Status:** proof_of_concept · **Code:** sketch · **Data:** SYNTHETIC · **Not evidence:** this run does not validate or invalidate the methodology.

## What it shows
UCB1 selection `mean + c * sqrt(2 ln t / N)` with a deterministic tie-break (count, then id); selection uses no random numbers.

## Run it
```
python examples/methodologies/10-ucb/sketch.py
```
Standard library only: no network, no credentials, no files written. All data in it is SYNTHETIC (invented for the demonstration). It is a sketch of the formulas in ADR-016 (Accepted); the methodology is not implemented in the SDK.

## What it does not show
That UCB crosses the autonomy gate that defeated REINFORCE; no gate is evaluated.

## Falsification
If Thompson or UCB, run on the same real `validate-intent-foundation` 146-episode dataset that defeated REINFORCE, also fails to cross the gate, HYP-AL-009 is invalidated.

## Real data needed
The real `validate-intent-foundation` episodes with outcomes, scored against the declared autonomy gate.

## References
Ideation row #10; hypothesis: HYP-AL-009; ADR-016. Catalog entry: `examples/methodologies/catalog.json`, id 10.
