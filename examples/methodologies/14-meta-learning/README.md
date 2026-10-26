# Hierarchical meta-prior (methodology #14)

**Status:** proof_of_concept · **Code:** sketch · **Data:** SYNTHETIC · **Not evidence:** this run does not validate or invalidate the methodology.

## What it shows
Empirical-Bayes mean and variance (with a floor) across a family of converged policies, and a new policy initialised at the mean.

## Run it
```
python examples/methodologies/14-meta-learning/sketch.py
```
Standard library only: no network, no credentials, no files written. All data in it is SYNTHETIC (invented for the demonstration). It is a sketch of the formulas in ADR-019 (Proposed); the methodology is not implemented in the SDK.

## What it does not show
That a family-level prior speeds up a new policy; no learning on the new policy is run.

## Falsification
Proposed here: if a policy initialised from the family mean does not reach its autonomy gate in fewer episodes than a uniform start, on real converged policies of one family, the methodology is not worth adopting.

## Real data needed
At least three converged real policies that share one action space (a policy family).

## References
Ideation row #14; hypothesis: none registered (a criterion is proposed in the README); ADR-019. Catalog entry: `examples/methodologies/catalog.json`, id 14.
