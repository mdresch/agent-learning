# Durable human override (methodology #6)

**Status:** runnable · **Code:** SDK · **Data:** SYNTHETIC · **Not evidence:** this example does not validate or invalidate the methodology.

## What it shows
With no learned preference and no outcomes, one human acceptance makes a choice eligible and bypasses the statistical gates. A rejection withholds it.

## Run it
```
python examples/methodologies/06-human-override/example.py
```
It needs the package installed and nothing else: no network, no credentials, no files written. All data in it is SYNTHETIC (invented for the demonstration).

## What it does not show
That a human acceptance is a good signal. It is granted trust, and `requires_human_approval` still outranks it.

## Falsification
A claim would be that accepted choices are rarely overturned later; it is falsified if accepted choices are reversed at a high rate. This criterion is proposed here; no hypothesis is registered for this methodology in the Ideation Document.

## Real data needed
Real acceptances and rejections with later outcomes, to measure how often accepted choices were later overturned.

## References
Ideation row #6; hypothesis: none; ADR-003 (implemented: explicit feedback in `assess_autonomy`). Catalog entry: `examples/methodologies/catalog.json`, id 6.
