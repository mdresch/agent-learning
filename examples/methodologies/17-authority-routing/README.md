# Contextual authority-ensemble routing (methodology #17)

**Status:** runnable · **Code:** SDK · **Data:** SYNTHETIC · **Not evidence:** this example does not validate or invalidate the methodology.

## What it shows
Contextual authority routing via `agent_learning_ext.routing`: hard pinning of critical tasks to full authority, entropy and margin threshold escalation, and a hysteresis deadband preventing flapping.

## Run it
```
python examples/methodologies/17-authority-routing/example.py
```
It needs the package installed and nothing else: no network, no credentials, no files written. All data in it is SYNTHETIC (invented for the demonstration).

## What it does not show
That routing improves outcomes; it routes invented inputs. Lifecycle gates stay human-approved (ADR-003 Invariant 6).

## Falsification
Proposed here: if routed decisions are not escalated to a human more precisely (fewer unneeded and fewer missed escalations) than a fixed authority on real decisions, the methodology is not worth adopting.

## Real data needed
Real operational decisions with the policy's probabilities at decision time and whether a human later overrode it.

## References
Ideation row #17; hypothesis: none; ADR: ADR-021. Catalog entry: `examples/methodologies/catalog.json`, id 17.
