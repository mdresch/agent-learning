"""Contextual authority-ensemble routing (methodology #17) using the real agent_learning_ext router.

STATUS: runnable
CODE: sdk
DATA: SYNTHETIC
IDEATION ROW: #17 Contextual authority-ensemble routing
ADR: ADR-021
HYPOTHESIS: none
NOT EVIDENCE: this run does not validate or invalidate the methodology. The distributions below are invented.
"""

from __future__ import annotations

from agent_learning_ext.routing import (
    RoutingConfig,
    route,
)


def main() -> None:
    print("DATA: SYNTHETIC. NOT EVIDENCE: this run does not validate or invalidate Contextual authority-ensemble routing.")

    cfg = RoutingConfig(tau_esc=1.00, tau_deesc=0.70, eps_margin=0.20)

    # 1. Pinned gates must always route to full authority
    for task in ["approve-charter", "approve-adr", "approve-brd"]:
        dec = route(probs=[0.99, 0.01], tier="standard", task_id=task, cfg=cfg)
        assert dec.authority.value == "full" and dec.reason == "pinned"

    # 2. Clear decisive operational request routes to low
    dec_low = route(probs=[0.95, 0.05], tier="standard", task_id="classify", approved_for_low=True, cfg=cfg)
    assert dec_low.authority.value == "low" and dec_low.reason == "low"

    # 3. Uncertain distribution routes to full
    dec_full = route(probs=[0.50, 0.50], tier="standard", task_id="classify", approved_for_low=True, cfg=cfg)
    assert dec_full.authority.value == "full"

    # High entropy with sufficient margin (margin=0.20 >= eps_margin, entropy=1.922 >= tau_esc)
    dec_entropy = route(probs=[0.40, 0.20, 0.20, 0.20], tier="standard", task_id="classify", approved_for_low=True, cfg=cfg)
    assert dec_entropy.authority.value == "full" and dec_entropy.reason == "entropy"

    # 4. Thin margin routes to full
    dec_margin = route(probs=[0.45, 0.40, 0.15], tier="standard", task_id="classify", approved_for_low=True, cfg=cfg)
    assert dec_margin.authority.value == "full" and dec_margin.reason == "margin"

    # 5. Hysteresis deadband preserves previous route
    deadband_probs = [0.80, 0.20]  # entropy ~0.722, between 0.70 and 1.00
    dec_hyst_low = route(probs=deadband_probs, tier="standard", task_id="classify", previous="low", approved_for_low=True, cfg=cfg)
    dec_hyst_full = route(probs=deadband_probs, tier="standard", task_id="classify", previous="full", approved_for_low=True, cfg=cfg)
    assert dec_hyst_low.authority.value == "low" and dec_hyst_low.reason == "hysteresis"
    assert dec_hyst_full.authority.value == "full" and dec_hyst_full.reason == "hysteresis"

    print("  routing checks passed (pinned, low, full, margin, entropy, hysteresis)")


if __name__ == "__main__":
    main()
