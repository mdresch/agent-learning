# Thompson sampling (methodology #9)

**Status:** runnable · **Code:** SDK · **Data:** SYNTHETIC · **Not evidence:** this run does not validate or invalidate the methodology.

## What it shows
Seeded Beta-Bernoulli Thompson sampling with the real `ThompsonPolicy` and `ThompsonLearner`: a Beta posterior per action, probability matching, each episode counted once, and the better action drawn more often as evidence accumulates.

## Run it
```
python examples/methodologies/09-thompson-sampling/example.py
```
It needs the package installed and nothing else: no network, no credentials, no files written. All data in it is SYNTHETIC (invented for the demonstration).

## What it does not show
That Thompson sampling crosses an autonomy gate under positive-only evidence; no gate is evaluated.

## Falsification
If a bandit trained purely on all-correct data for one action does cross the probability and margin gates given enough episodes, HYP-AL-002 is invalidated; HYP-AL-009 is invalidated if Thompson or UCB also fails the gate on the real 146-episode dataset.

## Real data needed
The real `validate-intent-foundation` episode set (146 episodes) with outcomes, run through the same autonomy gates.

## References
Ideation row #9; hypothesis: HYP-AL-002, see also HYP-AL-009; ADR-015. Catalog entry: `examples/methodologies/catalog.json`, id 9.
