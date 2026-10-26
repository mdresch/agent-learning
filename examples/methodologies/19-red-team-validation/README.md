# Red-team validation (methodology #19)

**Status:** runnable · **Code:** SDK · **Data:** SYNTHETIC · **Not evidence:** this example does not validate or invalidate the methodology.

## What it shows
A persuasive but flawed proposal is run through the same policy as a sound one. The sound one is approved and the flawed one is not, because its critical-flaw constraint rules approval out.

## Run it
```
python examples/methodologies/19-red-team-validation/example.py
```
It needs the package installed and nothing else: no network, no credentials, no files written. All data in it is SYNTHETIC (invented for the demonstration).

## What it does not show
That the policy catches flaws it was not told about. The flaw is declared in the constraint results, which a reviewer must set.

## Falsification
A claim would be that a counterpart a human judges flawed is never approved by the policy; it is falsified if one is. This criterion is proposed here; no hypothesis is registered for this methodology in the Ideation Document.

## Real data needed
Real documents with deliberately flawed variants, a human judgment of which is flawed, and the policy's verdict on each.

## References
Ideation row #19; hypothesis: none; ADR: none (practiced as validation, not as a training signal). Catalog entry: `examples/methodologies/catalog.json`, id 19.
