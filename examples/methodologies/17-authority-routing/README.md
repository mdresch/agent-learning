# Contextual authority-ensemble routing (methodology #17)

**Status:** proof_of_concept · **Code:** sketch · **Data:** SYNTHETIC · **Not evidence:** this run does not validate or invalidate the methodology.

## What it shows
Hard pinning of lifecycle gates to full authority, entropy-based routing for operational tasks, and a hysteresis band that prevents flip-flopping.

## Run it
```
python examples/methodologies/17-authority-routing/sketch.py
```
Standard library only: no network, no credentials, no files written. All data in it is SYNTHETIC (invented for the demonstration). It is a sketch of the formulas in ADR-021 (Accepted); the methodology is not implemented in the SDK.

## What it does not show
That routing improves outcomes; it routes invented inputs. Lifecycle gates stay human-approved (ADR-003 Invariant 6).

## Falsification
Proposed here: if routed decisions are not escalated to a human more precisely (fewer unneeded and fewer missed escalations) than a fixed authority on real decisions, the methodology is not worth adopting.

## Real data needed
Real operational decisions with the policy's probabilities at decision time and whether a human later overrode it.

## References
Ideation row #17; hypothesis: none registered (a criterion is proposed in the README); ADR-021. Catalog entry: `examples/methodologies/catalog.json`, id 17.
