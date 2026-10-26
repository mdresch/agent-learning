"""Epsilon-greedy (methodology #11) - proof-of-concept sketch.

STATUS: proof_of_concept
CODE: sketch
DATA: SYNTHETIC
IDEATION ROW: #11 Epsilon-greedy
ADR: ADR-017 (Proposed)
HYPOTHESIS: none registered (a criterion is proposed in the README)
NOT EVIDENCE: this run does not validate or invalidate the methodology

This is a sketch of the ADR formulas in plain Python (stdlib only), not SDK code:
the methodology is not implemented in agent_learning (ADR-036 section 4.2).
"""

from __future__ import annotations

import random

SEED = 20261026


def main() -> None:
    print("SYNTHETIC data, NOT EVIDENCE: sketch of Epsilon-greedy (ADR-017, not implemented)")
    rng = random.Random(SEED)
    true_p = {"a": 0.7, "b": 0.5, "unsafe": 0.9}
    safe = [k for k in true_p if k != "unsafe"]
    count = {k: 0 for k in safe}
    total = {k: 0.0 for k in safe}
    e0, decay, floor = 0.5, 0.05, 0.05
    explored = 0
    for t in range(1, 301):
        eps = max(floor, e0 / (1 + decay * t))
        if rng.random() < eps:
            pick = rng.choice(safe)
            explored += 1
        else:
            pick = max(safe, key=lambda k: (total[k] / count[k] if count[k] else 1.0, k))
        count[pick] += 1
        total[pick] += 1.0 if rng.random() < true_p[pick] else 0.0
    print(f"  pulls: {count}, explored: {explored}")
    assert "unsafe" not in count and count["a"] > count["b"]


if __name__ == "__main__":
    main()
