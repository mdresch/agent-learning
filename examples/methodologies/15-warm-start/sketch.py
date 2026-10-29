"""Warm-start / prior transfer (methodology #15) - proof-of-concept sketch.

STATUS: proof_of_concept
CODE: sketch
DATA: SYNTHETIC
IDEATION ROW: #15 Warm-start / prior transfer
ADR: ADR-020 (Accepted)
HYPOTHESIS: HYP-AL-008
NOT EVIDENCE: this run does not validate or invalidate the methodology

This is a sketch of the ADR formulas in plain Python (stdlib only), not SDK code:
the methodology is not implemented in agent_learning (ADR-036 section 4.2).
"""

from __future__ import annotations

import math

SEED = 20261026


def main() -> None:
    print("SYNTHETIC data, NOT EVIDENCE: sketch of Warm-start / prior transfer (ADR-020, not implemented)")
    donor = {"approve": 2.0, "reject": -1.0, "escalate": 0.0}
    mapping = {"accept": "approve", "decline": "reject", "ask": "escalate"}
    tau = 0.70

    def softmax(d: dict[str, float]) -> dict[str, float]:
        z = sum(math.exp(v) for v in d.values())
        return {k: math.exp(v) / z for k, v in d.items()}

    full = softmax({a: donor[m] for a, m in mapping.items()})
    damped = softmax({a: donor[m] * tau for a, m in mapping.items()})
    print("  full:", {k: round(v, 2) for k, v in full.items()}, "damped:", {k: round(v, 2) for k, v in damped.items()})
    assert max(damped.values()) < max(full.values())


if __name__ == "__main__":
    main()
