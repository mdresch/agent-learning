# Diff classification (methodology #20)

**Status:** runnable · **Code:** SDK · **Data:** SYNTHETIC · **Not evidence:** this example does not validate or invalidate the methodology.

## What it shows
Two invented changes are classified. A cosmetic correction is applied with a notice; a decision reversal wearing a minor-tweak label is classified as superseding and held for a human.

## Run it
```
python examples/methodologies/20-diff-classification/example.py
```
It needs the package installed and nothing else: no network, no credentials, no files written. All data in it is SYNTHETIC (invented for the demonstration).

## What it does not show
That real diffs would be classified this way. The criterion scores that drive the result are written into the script.

## Falsification
If the classifier assigns a genuine decision change to a cosmetic class (or the reverse) on a well-evidenced real case, the hypothesis is invalidated (HYP-AL-006).

## Real data needed
Real before-and-after documents with a human classification of each change and the evidence scores a reviewer would assign.

## References
Ideation row #20; hypothesis HYP-AL-006; ADR-007 (implemented: `evaluate_governance_diff`). Catalog entry: `examples/methodologies/catalog.json`, id 20.
