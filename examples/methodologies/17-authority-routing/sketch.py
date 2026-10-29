"""Contextual authority-ensemble routing (methodology #17) - proof-of-concept sketch.

STATUS: proof_of_concept
CODE: sketch
DATA: SYNTHETIC
IDEATION ROW: #17 Contextual authority-ensemble routing
ADR: ADR-021 (Accepted)
HYPOTHESIS: none registered (a criterion is proposed in the README)
NOT EVIDENCE: this run does not validate or invalidate the methodology

This is a sketch of the ADR formulas in plain Python (stdlib only), not SDK code:
the methodology is not implemented in agent_learning (ADR-036 section 4.2).
"""

from __future__ import annotations

import math

SEED = 20261026


def main() -> None:
    print("SYNTHETIC data, NOT EVIDENCE: sketch of Contextual authority-ensemble routing (ADR-021, not implemented)")
    # ADR-021 4.1 baseline gates, plus the two decisions FDD-021 adds; none may ever route low.
    pinned = {
        "approve-charter", "approve-adr", "approve-brd", "approve-fdd", "approve-user-stories", "approve-pmp",
        "approve-adaptation-plan", "approve-subsidiary-plan", "retrospective",
        "approve-routing-thresholds", "approve-routing-bucket",
    }
    esc, deesc, eps_margin = 1.0, 0.7, 0.20  # entropy in bits; the band is wider than the 0.15-bit minimum
    assert esc - deesc >= 0.15

    def entropy(p: list[float]) -> float:
        return -sum(x * math.log2(x) for x in p if x > 0)

    def margin(p: list[float]) -> float:
        top = sorted(p, reverse=True)
        return top[0] - (top[1] if len(top) > 1 else 0.0)

    def route(task: str, p: list[float], tier: str, previous: str | None, approved: bool) -> str:
        if task in pinned:
            return "full"
        if not p or any(x < 0 or math.isnan(x) for x in p) or abs(sum(p) - 1.0) > 1e-6:
            return "full"  # fail safe: invalid input routes full
        h = entropy(p)
        if h >= esc or tier == "critical" or margin(p) < eps_margin:
            return "full"
        if h <= deesc:
            return "low" if approved else "full"  # only an approved bucket may route low
        # deadband: keep the previous route; a first call, or a bucket no longer approved, is full
        return previous if previous == "low" and approved else "full"

    assert route("approve-adr", [0.99, 0.01], "standard", "low", True) == "full"
    assert route("classify", [0.95, 0.05], "standard", "full", True) == "low"
    assert route("classify", [0.95, 0.05], "standard", "full", False) == "full"  # not approved
    assert route("classify", [0.5, 0.5], "standard", "low", True) == "full"
    assert route("classify", [0.8, 0.2], "standard", "low", True) == "low"  # inside the band: unchanged
    assert route("classify", [0.8, 0.2], "standard", "full", True) == "full"
    assert route("classify", [0.8, 0.2], "standard", None, True) == "full"  # no previous route starts full
    assert route("classify", [0.45, 0.40, 0.15], "standard", "low", True) == "full"  # thin margin
    assert route("classify", [0.95, 0.05], "critical", "low", True) == "full"
    assert route("classify", [0.7, 0.4], "standard", "low", True) == "full"  # invalid sum
    print("  routing checks passed (pinned, low, full, hysteresis, margin, approval, critical, fail safe)")


if __name__ == "__main__":
    main()
