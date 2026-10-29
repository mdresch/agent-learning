"""Active dueling-bandit ranking (methodology #23) - proof-of-concept sketch.

STATUS: proof_of_concept
CODE: sketch
DATA: SYNTHETIC
IDEATION ROW: #23 Active dueling-bandit ranking
ADR: ADR-023 (Accepted)
HYPOTHESIS: HYP-AL-015
NOT EVIDENCE: this run does not validate or invalidate the methodology

This is a sketch of the ADR formulas in plain Python (stdlib only), not SDK code:
the methodology is not implemented in agent_learning (ADR-036 section 4.2).
"""

from __future__ import annotations

import math
import random

SEED = 20261026


def main() -> None:
    print("SYNTHETIC data, NOT EVIDENCE: sketch of Active dueling-bandit ranking (ADR-023, not implemented)")
    rng = random.Random(SEED)
    truth = [1.5, 0.5, 0.0, -0.8, -1.2]
    n, reg = len(truth), 0.01
    lam = [0.0] * n
    results: list[tuple[int, int, int]] = []
    seen = {(i, j): 0 for i in range(n) for j in range(i + 1, n)}

    def sig(v: float) -> float:
        return 1.0 / (1.0 + math.exp(-v))

    def fit() -> None:
        for _ in range(60):
            grad = [-reg * v for v in lam]
            for i, j, y in results:
                p = sig(lam[i] - lam[j])
                grad[i] += y - p
                grad[j] -= y - p
            for k in range(n):
                lam[k] += 0.2 * grad[k]
            mean = sum(lam) / n
            for k in range(n):
                lam[k] -= mean

    for _ in range(25):
        exposure = [sum(c for pair, c in seen.items() if k in pair) for k in range(n)]
        low = [k for k in range(n) if exposure[k] < 2]
        pool = [p for p in seen if not low or low[0] in p]
        i, j = min(pool, key=lambda p: abs(sig(lam[p[0]] - lam[p[1]]) - 0.5) * math.sqrt(seen[p] + 1))
        y = 1 if rng.random() < sig(truth[i] - truth[j]) else 0
        results.append((i, j, y))
        seen[(i, j)] += 1
        fit()
    order = sorted(range(n), key=lambda k: -lam[k])
    print(f"  25 adaptive comparisons over {n * (n - 1) // 2} pairs: ranking {order}")
    assert order[0] == 0 and order[-1] in (3, 4)


if __name__ == "__main__":
    main()
