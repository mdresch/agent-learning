# Active dueling-bandit ranking (methodology #23)

**Status:** proof_of_concept · **Code:** sketch · **Data:** SYNTHETIC · **Not evidence:** this run does not validate or invalidate the methodology.

## What it shows
A regularised Bradley-Terry fit and an active query rule that asks about the pair whose outcome is closest to 50:50, with a minimum exposure of two comparisons per item.

## Run it
```
python examples/methodologies/23-dueling-bandit/sketch.py
```
Standard library only: no network, no credentials, no files written. All data in it is SYNTHETIC (invented for the demonstration). It is a sketch of the formulas in ADR-023 (Proposed); the methodology is not implemented in the SDK.

## What it does not show
That adaptive pair selection needs fewer comparisons than the exhaustive approach on real judgments; the ranking here is invented.

## Falsification
If an adaptive pair-selection strategy, tested against a real set of pairwise judgments, does not reduce the comparisons needed to reach the same ranking confidence as the exhaustive approach, HYP-AL-015 is invalidated. It is untestable until that judgment data is collected.

## Real data needed
Raw head-to-head judgments from a real portfolio prioritisation (not collected today, per the hypothesis).

## References
Ideation row #23; hypothesis: HYP-AL-015; ADR-023. Catalog entry: `examples/methodologies/catalog.json`, id 23.
