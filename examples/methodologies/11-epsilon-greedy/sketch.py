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
    safe = sorted(k for k in true_p if k != "unsafe")
    count = {k: 0 for k in true_p}
    total = {k: 0.0 for k in true_p}
    e0, decay, floor = 0.5, 0.05, 0.05
    explored = 0
    explored_picks: set[str] = set()

    def mean(k: str) -> float:
        return total[k] / count[k] if count[k] else 0.5  # ADR-017 4.1: no pulls counts as the neutral mean

    for t in range(1, 301):
        eps = max(floor, e0 / (1 + decay * (t - 1)))
        if rng.random() < eps:
            pick = rng.choice(safe)  # only exploration is masked
            explored += 1
            explored_picks.add(pick)
        else:
            # greedy over every action; ties by higher pull count, then smaller id (ADR-017 4.1)
            pick = min(true_p, key=lambda k: (-mean(k), -count[k], k))
        count[pick] += 1
        total[pick] += 1.0 if rng.random() < true_p[pick] else 0.0
    print(f"  pulls: {count}, explored: {explored}")
    assert "unsafe" not in explored_picks and sum(count.values()) == 300


if __name__ == "__main__":
    main()
