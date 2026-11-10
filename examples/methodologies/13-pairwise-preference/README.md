# Pairwise preference optimization (methodology #13)

**Status:** runnable · **Code:** SDK · **Data:** SYNTHETIC · **Not evidence:** this example does not validate or invalidate the methodology.

## What it shows
Bradley-Terry logit optimization via `PairwiseLearner` directly on human override pairs extracted from episodes, anchored to frozen reference logits with $L_2$ regularization.

## Run it
```
python examples/methodologies/13-pairwise-preference/example.py
```
It needs the package installed and nothing else: no network, no credentials, no files written. All data in it is SYNTHETIC (invented for the demonstration).

## What it does not show
That override episodes yield useful preference pairs; the pairs here are invented.

## Falsification
Proposed here: if a policy fitted to real override pairs does not agree with later human adjudications more often than the unfitted reference policy, the methodology is not worth adopting.

## Real data needed
Real episodes with a recorded override (adjudicated action versus proposed action) in the learning store.

## References
Ideation row #13; hypothesis: none; ADR: ADR-018. Catalog entry: `examples/methodologies/catalog.json`, id 13.
