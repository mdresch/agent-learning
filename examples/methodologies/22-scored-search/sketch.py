"""Scored-search decision compilation (methodology #22) - proof-of-concept sketch.

STATUS: proof_of_concept
CODE: sketch
DATA: SYNTHETIC
IDEATION ROW: #22 Scored-search decision compilation
ADR: ADR-022 (Proposed)
HYPOTHESIS: HYP-AL-010
NOT EVIDENCE: this run does not validate or invalidate the methodology

This is a sketch of the ADR formulas in plain Python (stdlib only), not SDK code:
the methodology is not implemented in agent_learning (ADR-036 section 4.2).
"""

from __future__ import annotations

import random

SEED = 20261026


def main() -> None:
    print("SYNTHETIC data, NOT EVIDENCE: sketch of Scored-search decision compilation (ADR-022, not implemented)")
    rng = random.Random(SEED)
    hidden = (0.6, 0.3, 0.1)
    frames = [(rng.random(), rng.random(), rng.random()) for _ in range(200)]
    labels = [sum(w * x for w, x in zip(hidden, f, strict=True)) > 0.5 for f in frames]

    def accuracy(w: list[float]) -> float:
        hits = sum(
            (sum(a * b for a, b in zip(w, f, strict=True)) > 0.5) == y
            for f, y in zip(frames, labels, strict=True)
        )
        return hits / len(frames)

    w = [1 / 3, 1 / 3, 1 / 3]
    start = accuracy(w)
    for _ in range(20):
        for i in range(3):
            for step in (0.05, -0.05):
                cand = list(w)
                cand[i] = max(0.0, cand[i] + step)
                total = sum(cand)
                cand = [x / total for x in cand]
                if accuracy(cand) > accuracy(w):
                    w = cand
    print(f"  accuracy {start:.2f} -> {accuracy(w):.2f}, weights {[round(x, 2) for x in w]}")
    assert accuracy(w) >= start and abs(sum(w) - 1.0) < 1e-9


if __name__ == "__main__":
    main()
