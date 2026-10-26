# Contextual bandit (methodology #4)

**Status:** runnable · **Code:** SDK · **Data:** SYNTHETIC · **Not evidence:** this example does not validate or invalidate the methodology.

## What it shows
A contextual softmax policy learns a different best action for each of two invented contexts. The trainable learner is written out in the script because it is example-only in the SDK.

## Run it
```
python examples/methodologies/04-contextual-bandit/example.py
```
It needs the package installed and nothing else: no network, no credentials, no files written. All data in it is SYNTHETIC (invented for the demonstration).

## What it does not show
That a packaged contextual learner is needed. The policy class is exported; its learner is not.

## Falsification
If adopters repeatedly meet a per-instance-varying decision and route around the missing contextual path by hand-building full-authority frames, that is evidence against the hypothesis's second half (HYP-AL-004, status Testing).

## Real data needed
A recurring decision whose best action depends on logged context features, with scored outcomes per context.

## References
Ideation row #4; hypothesis HYP-AL-004; ADR: none (example-only: `ContextualSoftmaxPolicy`). Catalog entry: `examples/methodologies/catalog.json`, id 4.
