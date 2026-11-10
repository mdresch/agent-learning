# Epsilon-greedy (methodology #11)

**Status:** runnable · **Code:** SDK · **Data:** SYNTHETIC · **Not evidence:** this example does not validate or invalidate the methodology.

## What it shows
A decaying exploration rate `max(floor, eps0 / (1 + delta * t))` (`EpsilonGreedyPolicy`) with a safe-action mask and deterministic counting (`EpsilonGreedyLearner`).

## Run it
```
python examples/methodologies/11-epsilon-greedy/example.py
```
It needs the package installed and nothing else: no network, no credentials, no files written. All data in it is SYNTHETIC (invented for the demonstration).

## What it does not show
That decayed exploration beats a fixed policy on real data.

## Falsification
Proposed here, not in the Ideation Document: if epsilon-greedy with decay and a safe-action mask does not reach the same autonomy gate in fewer episodes than a fixed-temperature softmax on the same real data, it is not worth adopting.

## Real data needed
Episodes of a decision with a known set of unsafe actions, with outcomes for the actions that were tried.

## References
Ideation row #11; hypothesis: none; ADR: ADR-017. Catalog entry: `examples/methodologies/catalog.json`, id 11.
