# Reward shaping (methodology #5)

**Status:** runnable · **Code:** SDK · **Data:** SYNTHETIC · **Not evidence:** this example does not validate or invalidate the methodology.

## What it shows
Metric scores become one bounded reward in [-1, 1], with a penalty for slow responses.

## Run it
```
python examples/methodologies/05-reward-shaping/example.py
```
It needs the package installed and nothing else: no network, no credentials, no files written. All data in it is SYNTHETIC (invented for the demonstration).

## What it does not show
That the shaped reward ranks outcomes the way a human would. The scores and latencies are invented.

## Falsification
A claim would be that shaped rewards rank real outcomes in the same order as a human reviewer; it is falsified if the ranking disagrees on a labeled set. This criterion is proposed here; no hypothesis is registered for this methodology in the Ideation Document.

## Real data needed
Real metric outputs for real episodes, with human outcome labels to compare the ranking against.

## References
Ideation row #5; hypothesis: none; ADR: none (implemented: `RewardShaper`, `shape_episode_reward`). Catalog entry: `examples/methodologies/catalog.json`, id 5.
