"""UCB (methodology #10) - proof-of-concept sketch.

STATUS: proof_of_concept
CODE: sketch
DATA: SYNTHETIC
IDEATION ROW: #10 UCB
ADR: ADR-016 (Accepted)
HYPOTHESIS: HYP-AL-009
NOT EVIDENCE: this run does not validate or invalidate the methodology

This is a sketch of the ADR formulas in plain Python (stdlib only), not SDK code:
the methodology is not implemented in agent_learning (ADR-036 section 4.2).
"""

from __future__ import annotations

import math
import random

SEED = 20261026


def main() -> None:
    print("SYNTHETIC data, NOT EVIDENCE: sketch of UCB (ADR-016, not implemented)")
    rng = random.Random(SEED)  # only generates the synthetic rewards; selection is deterministic
    true_p = {"a": 0.7, "b": 0.5, "c": 0.3}
    count = {k: 0 for k in true_p}
    total = {k: 0.0 for k in true_p}
    c = 1.0

    def score(k: str, t: int) -> float:
        if count[k] == 0:
            return math.inf
        return total[k] / count[k] + c * math.sqrt(2 * math.log(t) / count[k])

    for t in range(1, 301):
        # ADR-016 section 4.2: equal bounds go to the higher pull count, then the smaller id
        pick = min(true_p, key=lambda k: (-score(k, t), -count[k], k))
        count[pick] += 1
        total[pick] += 1.0 if rng.random() < true_p[pick] else 0.0
    print(f"  pulls: {count}")
    assert count["a"] > count["c"]


if __name__ == "__main__":
    main()
