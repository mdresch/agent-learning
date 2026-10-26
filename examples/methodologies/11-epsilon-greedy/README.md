# Epsilon-greedy (methodology #11)

**Status:** proof_of_concept · **Code:** sketch · **Data:** SYNTHETIC · **Not evidence:** this run does not validate or invalidate the methodology.

## What it shows
A decaying exploration rate `max(floor, e0 / (1 + d t))` with a safe-action mask: masked actions are never explored.

## Run it
```
python examples/methodologies/11-epsilon-greedy/sketch.py
```
Standard library only: no network, no credentials, no files written. All data in it is SYNTHETIC (invented for the demonstration). It is a sketch of the formulas in ADR-017 (Proposed); the methodology is not implemented in the SDK.

## What it does not show
That decayed exploration beats a fixed policy on real data.

## Falsification
Proposed here, not in the Ideation Document: if epsilon-greedy with decay and a safe-action mask does not reach the same autonomy gate in fewer episodes than a fixed-temperature softmax on the same real data, it is not worth adopting.

## Real data needed
Episodes of a decision with a known set of unsafe actions, with outcomes for the actions that were tried.

## References
Ideation row #11; hypothesis: none registered (a criterion is proposed in the README); ADR-017. Catalog entry: `examples/methodologies/catalog.json`, id 11.
