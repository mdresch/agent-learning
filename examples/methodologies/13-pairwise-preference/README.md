# Pairwise preference optimization (methodology #13)

**Status:** proof_of_concept · **Code:** sketch · **Data:** SYNTHETIC · **Not evidence:** this run does not validate or invalidate the methodology.

## What it shows
Bradley-Terry logits fitted by gradient descent on preference pairs, pulled toward a frozen reference (`lambda_reg >= 0.05`) and clamped to [-8, 8].

## Run it
```
python examples/methodologies/13-pairwise-preference/sketch.py
```
Standard library only: no network, no credentials, no files written. All data in it is SYNTHETIC (invented for the demonstration). It is a sketch of the formulas in ADR-018 (Proposed); the methodology is not implemented in the SDK.

## What it does not show
That override episodes yield useful preference pairs; the pairs here are invented.

## Falsification
Proposed here: if a policy fitted to real override pairs does not agree with later human adjudications more often than the unfitted reference policy, the methodology is not worth adopting.

## Real data needed
Real episodes with a recorded override (adjudicated action versus proposed action) in the learning store.

## References
Ideation row #13; hypothesis: none registered (a criterion is proposed in the README); ADR-018. Catalog entry: `examples/methodologies/catalog.json`, id 13.
