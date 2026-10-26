# Thompson sampling (methodology #9)

**Status:** proof_of_concept · **Code:** sketch · **Data:** SYNTHETIC · **Not evidence:** this run does not validate or invalidate the methodology.

## What it shows
A Beta posterior per action (alpha += r, beta += 1 - r) and probability matching: the better action is sampled more often as evidence accumulates.

## Run it
```
python examples/methodologies/09-thompson-sampling/sketch.py
```
Standard library only: no network, no credentials, no files written. All data in it is SYNTHETIC (invented for the demonstration). It is a sketch of the formulas in ADR-015 (Proposed); the methodology is not implemented in the SDK.

## What it does not show
That Thompson sampling crosses an autonomy gate under positive-only evidence; no gate is evaluated.

## Falsification
If a bandit trained purely on all-correct data for one action does cross the probability and margin gates given enough episodes, HYP-AL-002 is invalidated; HYP-AL-009 is invalidated if Thompson or UCB also fails the gate on the real 146-episode dataset.

## Real data needed
The real `validate-intent-foundation` episode set (146 episodes) with outcomes, run through the same autonomy gates.

## References
Ideation row #9; hypothesis: HYP-AL-002, see also HYP-AL-009; ADR-015. Catalog entry: `examples/methodologies/catalog.json`, id 9.
