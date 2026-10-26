# Reasoned resolution (methodology #3)

**Status:** runnable · **Code:** SDK · **Data:** SYNTHETIC · **Not evidence:** this example does not validate or invalidate the methodology.

## What it shows
A full-authority decision is resolved from weighed, multi-source evidence with no training. With a human-approval requirement the same result is held for a human instead.

## Run it
```
python examples/methodologies/03-reasoned-resolution/example.py
```
It needs the package installed and nothing else: no network, no credentials, no files written. All data in it is SYNTHETIC (invented for the demonstration).

## What it does not show
That the verdict is correct. The evidence scores are invented, and the resolver only aggregates what it is given.

## Falsification
If full-authority resolution produces an incorrect verdict on a well-evidenced real-versus-red-team contrastive pair, the hypothesis is invalidated (HYP-AL-003).

## Real data needed
Real artifacts with reviewer-supplied evidence scores and a known correct verdict, including deliberately flawed counterparts.

## References
Ideation row #3; hypothesis HYP-AL-003; ADR: none (implemented: `DecisionResolver`, `TaskPolicy`). Catalog entry: `examples/methodologies/catalog.json`, id 3.
