# Active evidence-seeking (methodology #12)

**Status:** runnable · **Code:** SDK · **Data:** SYNTHETIC · **Not evidence:** this example does not validate or invalidate the methodology.

## What it shows
When evidence is missing, the resolver reports which constraint and criterion evidence would matter most, ranked by estimated information gain.

## Run it
```
python examples/methodologies/12-active-evidence-seeking/example.py
```
It needs the package installed and nothing else: no network, no credentials, no files written. All data in it is SYNTHETIC (invented for the demonstration).

## What it does not show
An automated loop that fetches the evidence. Only the report exists in the SDK; the methodology is partial.

## Falsification
A claim would be that supplying the highest-gain evidence changes the decision more often than supplying lower-gain evidence; it is falsified if it does not. This criterion is proposed here; no hypothesis is registered for this methodology in the Ideation Document.

## Real data needed
Real decisions that stopped for missing evidence, the evidence later supplied, and whether the decision changed.

## References
Ideation row #12; hypothesis: none; ADR: none (partial: `InformationNeed` on the `NEEDS_EVIDENCE` path). Catalog entry: `examples/methodologies/catalog.json`, id 12.
