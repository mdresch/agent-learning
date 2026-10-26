# REINFORCE bandit (methodology #2)

**Status:** runnable · **Code:** SDK · **Data:** SYNTHETIC · **Not evidence:** this example does not validate or invalidate the methodology.

## What it shows
A two-action softmax policy is updated with REINFORCE and a baseline from rewards. The policy shifts toward the action that the invented rewards favor.

## Run it
```
python examples/methodologies/02-reinforce-bandit/example.py
```
It needs the package installed and nothing else: no network, no credentials, no files written. All data in it is SYNTHETIC (invented for the demonstration).

## What it does not show
That the policy would earn autonomy on real data. It does not use real outcomes, a complexity tier or an autonomy gate.

## Falsification
If well-behaved, contrastive (not positive-only) episode data cannot cross a `standard`-tier autonomy gate within a few hundred episodes, the hypothesis is invalidated (HYP-AL-001).

## Real data needed
Episodes of a recurring decision with both successes and failures, each with a scored reward, and enough of them to meet the declared tier's outcome gate.

## References
Ideation row #2; hypothesis HYP-AL-001; ADR: none (implemented: `SoftmaxPolicy`, `ReinforceLearner`). Catalog entry: `examples/methodologies/catalog.json`, id 2.
