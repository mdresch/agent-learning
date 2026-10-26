# Category-level escalation (methodology #21)

**Status:** runnable · **Code:** SDK · **Data:** SYNTHETIC · **Not evidence:** this example does not validate or invalidate the methodology.

## What it shows
For one invented category of change, a low-authority policy learns to apply silently more often than to escalate, from invented outcomes.

## Run it
```
python examples/methodologies/21-category-escalation/example.py
```
It needs the package installed and nothing else: no network, no credentials, no files written. All data in it is SYNTHETIC (invented for the demonstration).

## What it does not show
That the policy has learned anything real: the escalation policy is implemented but has no real training episodes.

## Falsification
If the escalation policy, given real training episodes, cannot cross a `standard`-tier autonomy gate despite well-behaved contrastive data, the hypothesis is invalidated (HYP-AL-007).

## Real data needed
Real governance-change episodes with the change category, the action taken, and the outcome (accepted, regressed or reverted).

## References
Ideation row #21; hypothesis HYP-AL-007; ADR-007 (implemented, untrained: `escalate-diff-response`). Catalog entry: `examples/methodologies/catalog.json`, id 21.
