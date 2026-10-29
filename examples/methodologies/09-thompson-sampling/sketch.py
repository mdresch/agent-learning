"""Thompson sampling (methodology #9) - proof-of-concept sketch.

STATUS: proof_of_concept
CODE: sketch
DATA: SYNTHETIC
IDEATION ROW: #9 Thompson sampling
ADR: ADR-015 (Accepted)
HYPOTHESIS: HYP-AL-002, see also HYP-AL-009
NOT EVIDENCE: this run does not validate or invalidate the methodology

This is a sketch of the ADR formulas in plain Python (stdlib only), not SDK code:
the methodology is not implemented in agent_learning (ADR-036 section 4.2).
"""

from __future__ import annotations

import random

SEED = 20261026


def main() -> None:
    print("SYNTHETIC data, NOT EVIDENCE: sketch of Thompson sampling (ADR-015, not implemented)")
    rng = random.Random(SEED)
    true_p = {"a": 0.8, "b": 0.4}
    post = {k: [1.0, 1.0] for k in true_p}
    for _ in range(300):
        pick = max(post, key=lambda k: rng.betavariate(*post[k]))
        r = 1.0 if rng.random() < true_p[pick] else 0.0
        post[pick][0] += r
        post[pick][1] += 1.0 - r
    pulls = {k: int(post[k][0] + post[k][1] - 2) for k in post}
    print(f"  pulls: {pulls}")
    assert pulls["a"] > pulls["b"]


if __name__ == "__main__":
    main()
