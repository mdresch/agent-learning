# Critique-to-evidence (methodology #8)

**Status:** runnable · **Code:** SDK · **Data:** SYNTHETIC · **Not evidence:** this example does not validate or invalidate the methodology.

## What it shows
Critique tags of the form `- [criterion: id] [claim: claim] [verified: yes]: rationale` are parsed into structured evidence deltas, applied to existing decision frame evidence via Bayesian log-odds pooling, and doubt is updated via multiplier $\kappa$.

## Run it
```
python examples/methodologies/08-critique-to-evidence/example.py
```
It needs the package installed and nothing else: no network, no credentials, no files written. All data in it is SYNTHETIC (invented for the demonstration).

## What it does not show
That reflection converges faster than REINFORCE on real episodes; no REINFORCE comparison is run.

## Falsification
Implement a reflection-based update path; if it does not converge faster or more sample-efficiently than REINFORCE on the same real episode data, the hypothesis is invalidated (HYP-AL-005).

## Real data needed
Real episodes that carry textual critiques (for example Red Team critiques) together with their scored outcomes.

## References
Ideation row #8; hypothesis: HYP-AL-005; ADR: ADR-014. Catalog entry: `examples/methodologies/catalog.json`, id 8.
