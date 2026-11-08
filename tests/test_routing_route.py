"""Contract test suite for Story 21.2 — The Route.

Source ADR: ADR-021 §4.1 (Contextual Authority Ensemble Routing)
Source BRD: BRD-021
Source FDD: FDD-021 §1, §2, §3
Story: Story 21.2 (The Route)

Acceptance Criteria:
- AC_0 (Config): RoutingConfig raises ValueError for a gap under 0.15 bits (including 0.149),
  for inverted thresholds (tau_esc < tau_deesc), for a non-finite value, for a negative
  tau_deesc, and for eps_margin of 0 or above 1; a gap of exactly 0.15 is accepted;
  tau_esc and tau_deesc have no default.
- AC_1 (Critical): tier 'critical' routes full with reason 'critical' for [0.99, 0.01]
  and an approved bucket.
- AC_2 (Escalate): on the base config entropy at or above 1.0 routes full with reason 'entropy',
  and a margin below 0.20 routes full with reason 'margin', even when entropy is below tau_deesc.
- AC_3 (Earn Low): with entropy at or below 0.7, margin at or above 0.20 and an approved bucket
  the route is low with reason 'low'; with the bucket not approved it is full with reason
  'not_approved', for every entropy.
- AC_4 (Hysteresis): [0.8, 0.2] (0.7219 bits, inside the deadband) keeps the previous route in both
  directions; a previous low route with the bucket no longer approved gives full with reason
  'not_approved'; previous of None inside the deadband gives full with reason 'no_previous'.
- AC_5 (No Hunting): over a sequence of entropies that oscillate inside the deadband the route
  changes at most once.
- AC_6 (Fail Safe): an empty list, a NaN, an infinite or negative probability, probabilities summing
  to 0.9 or 1.1, and an unknown tier each route full with reason 'anomaly' and an 'anomaly' text naming
  the cause, and entropy and margin are None.

Recommended Interpretations:
- I1: Upstream Fork Purity (Invariant 6): Specification references upstream path
  'src/agent_learning/routing.py'. Per Invariant 6, all custom classes, learners, and helpers
  must be created under 'src/agent_learning_ext/routing.py' (or 'agent-training-ext/'), leaving
  the upstream 'src/agent_learning/' tree completely pristine.
- I2: Storage Decoupling & Serialization Round-Trip: RouteDecision and RoutingConfig objects
  must survive standard serialization and deserialization patterns without custom decoders,
  and the routing module must import nothing from agent_learning.storage.
"""

from __future__ import annotations

import pytest

from agent_learning.decision import DecisionAuthority
from agent_learning_ext.routing import (
    EPS_MARGIN_DEFAULT,
    RoutingConfig,
    route,
)


@pytest.fixture
def base_config() -> RoutingConfig:
    """Base config specified in Epic 21 preamble: tau_esc=1.0, tau_deesc=0.7, eps_margin=0.20."""
    return RoutingConfig(tau_esc=1.0, tau_deesc=0.7, eps_margin=0.20)


def test_ac0_config_validation() -> None:
    """AC_0: RoutingConfig raises ValueError for invalid thresholds, non-finite values, and invalid margins."""
    # 1. Valid exact gap of 0.15 is accepted
    cfg_exact = RoutingConfig(tau_esc=0.85, tau_deesc=0.70)
    assert abs((cfg_exact.tau_esc - cfg_exact.tau_deesc) - 0.15) <= 1e-9
    assert cfg_exact.eps_margin == EPS_MARGIN_DEFAULT

    # 2. Gap under 0.15 bits (including 0.149) raises ValueError
    with pytest.raises(ValueError, match="gap"):
        RoutingConfig(tau_esc=0.849, tau_deesc=0.70)
    with pytest.raises(ValueError, match="gap"):
        RoutingConfig(tau_esc=0.70 + 0.149, tau_deesc=0.70)
    with pytest.raises(ValueError, match="gap"):
        RoutingConfig(tau_esc=0.75, tau_deesc=0.70)

    # 3. Inverted thresholds (tau_esc < tau_deesc) raise ValueError
    with pytest.raises(ValueError, match="inverted"):
        RoutingConfig(tau_esc=0.5, tau_deesc=0.8)

    # 4. Negative tau_deesc raises ValueError
    with pytest.raises(ValueError, match="negative"):
        RoutingConfig(tau_esc=0.5, tau_deesc=-0.1)

    # 5. Non-finite values or booleans raise ValueError
    with pytest.raises(ValueError, match="finite"):
        RoutingConfig(tau_esc=float("nan"), tau_deesc=0.7)
    with pytest.raises(ValueError, match="finite"):
        RoutingConfig(tau_esc=1.0, tau_deesc=float("inf"))
    with pytest.raises(ValueError, match="finite"):
        RoutingConfig(tau_esc=1.0, tau_deesc=0.7, eps_margin=float("nan"))
    with pytest.raises(ValueError, match="not bool"):
        RoutingConfig(tau_esc=True, tau_deesc=0.7)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="not bool"):
        RoutingConfig(tau_esc=1.0, tau_deesc=False)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="not bool"):
        RoutingConfig(tau_esc=1.0, tau_deesc=0.7, eps_margin=True)  # type: ignore[arg-type]

    # 6. eps_margin of 0 or above 1 raises ValueError
    with pytest.raises(ValueError, match="eps_margin"):
        RoutingConfig(tau_esc=1.0, tau_deesc=0.7, eps_margin=0.0)
    with pytest.raises(ValueError, match="eps_margin"):
        RoutingConfig(tau_esc=1.0, tau_deesc=0.7, eps_margin=-0.05)
    with pytest.raises(ValueError, match="eps_margin"):
        RoutingConfig(tau_esc=1.0, tau_deesc=0.7, eps_margin=1.01)

    # 7. eps_margin = 1.0 is valid boundary
    cfg_max_margin = RoutingConfig(tau_esc=1.0, tau_deesc=0.7, eps_margin=1.0)
    assert cfg_max_margin.eps_margin == 1.0


def test_ac1_critical_tier(base_config: RoutingConfig) -> None:
    """AC_1: tier 'critical' routes full with reason 'critical' for [0.99, 0.01] and an approved bucket."""
    decision = route(
        probs=[0.99, 0.01],
        tier="critical",
        task_id="classify-request",
        previous=DecisionAuthority.LOW,
        approved_for_low=True,
        requires_human_approval=False,
        cfg=base_config,
    )
    assert decision.authority == DecisionAuthority.FULL
    assert decision.reason == "critical"
    assert decision.entropy_bits is not None
    assert decision.margin is not None
    assert decision.anomaly is None


def test_ac2_escalate(base_config: RoutingConfig) -> None:
    """AC_2: entropy >= 1.0 routes full (reason 'entropy'), and margin < 0.20 routes full (reason 'margin')."""
    # 1. Entropy at or above 1.0 with margin >= 0.20 routes full with reason 'entropy'
    # [0.6, 0.3, 0.1]: entropy = 1.2955 >= 1.0, margin = 0.30 >= 0.20
    decision_ent = route(
        probs=[0.6, 0.3, 0.1],
        tier="standard",
        task_id="classify-request",
        previous=DecisionAuthority.LOW,
        approved_for_low=True,
        requires_human_approval=False,
        cfg=base_config,
    )
    assert decision_ent.authority == DecisionAuthority.FULL
    assert decision_ent.reason == "entropy"
    assert decision_ent.entropy_bits is not None and decision_ent.entropy_bits >= 1.0
    assert decision_ent.margin is not None and decision_ent.margin >= 0.20

    # 2. Margin below 0.20 routes full with reason 'margin'
    # E.g. [0.45, 0.40, 0.15] has margin 0.05 < 0.20 (and entropy ~1.46 >= 1.0), routes full by margin
    decision_margin1 = route(
        probs=[0.45, 0.40, 0.15],
        tier="standard",
        task_id="classify-request",
        previous=DecisionAuthority.LOW,
        approved_for_low=True,
        requires_human_approval=False,
        cfg=base_config,
    )
    assert decision_margin1.authority == DecisionAuthority.FULL
    assert decision_margin1.reason == "margin"

    # Distribution where entropy is below tau_deesc (0.7) but margin < 0.20:
    # Construct a distribution where top 2 probabilities are close:
    # Say [0.55, 0.45] has entropy 0.9928.
    # What if a distribution has low entropy and small margin?
    # Say we configure cfg with eps_margin=0.95:
    # [0.90, 0.10] has entropy 0.469 bits (< 0.7), and margin 0.80 (< 0.95)
    cfg_high_margin = RoutingConfig(tau_esc=1.0, tau_deesc=0.7, eps_margin=0.95)
    decision_margin2 = route(
        probs=[0.90, 0.10],
        tier="standard",
        task_id="classify-request",
        previous=DecisionAuthority.LOW,
        approved_for_low=True,
        requires_human_approval=False,
        cfg=cfg_high_margin,
    )
    assert decision_margin2.authority == DecisionAuthority.FULL
    assert decision_margin2.reason == "margin"
    assert decision_margin2.entropy_bits is not None and decision_margin2.entropy_bits <= 0.70


def test_ac3_earn_low(base_config: RoutingConfig) -> None:
    """AC_3: entropy <= 0.7 and margin >= 0.20 with approved bucket routes low ('low'), or full ('not_approved') if unapproved."""
    # [0.95, 0.05]: entropy 0.2864 <= 0.7, margin 0.90 >= 0.20
    # 1. Approved bucket -> routes low with reason 'low'
    decision_low = route(
        probs=[0.95, 0.05],
        tier="standard",
        task_id="classify-request",
        previous=DecisionAuthority.FULL,
        approved_for_low=True,
        requires_human_approval=False,
        cfg=base_config,
    )
    assert decision_low.authority == DecisionAuthority.LOW
    assert decision_low.reason == "low"

    # 2. Unapproved bucket with entropy <= tau_deesc -> routes full with reason 'not_approved'
    for probs in [[0.95, 0.05], [0.90, 0.10]]:
        decision_unapproved = route(
            probs=probs,
            tier="standard",
            task_id="classify-request",
            previous=DecisionAuthority.LOW,
            approved_for_low=False,
            requires_human_approval=False,
            cfg=base_config,
        )
        assert decision_unapproved.authority == DecisionAuthority.FULL
        assert decision_unapproved.reason == "not_approved"


def test_ac4_hysteresis(base_config: RoutingConfig) -> None:
    """AC_4: inside deadband, keeps previous route; previous low with unapproved bucket gives 'not_approved'; None gives 'no_previous'."""
    # [0.8, 0.2]: entropy 0.7219 bits (inside deadband [0.70, 1.0]), margin 0.60 >= 0.20
    # 1. Keeps previous LOW when approved
    decision_prev_low = route(
        probs=[0.8, 0.2],
        tier="standard",
        task_id="classify-request",
        previous=DecisionAuthority.LOW,
        approved_for_low=True,
        requires_human_approval=False,
        cfg=base_config,
    )
    assert decision_prev_low.authority == DecisionAuthority.LOW
    assert decision_prev_low.reason == "hysteresis"

    # 2. Keeps previous FULL
    decision_prev_full = route(
        probs=[0.8, 0.2],
        tier="standard",
        task_id="classify-request",
        previous=DecisionAuthority.FULL,
        approved_for_low=True,
        requires_human_approval=False,
        cfg=base_config,
    )
    assert decision_prev_full.authority == DecisionAuthority.FULL
    assert decision_prev_full.reason == "hysteresis"

    # 3. Previous LOW with bucket no longer approved gives FULL with reason 'not_approved'
    decision_revoked = route(
        probs=[0.8, 0.2],
        tier="standard",
        task_id="classify-request",
        previous=DecisionAuthority.LOW,
        approved_for_low=False,
        requires_human_approval=False,
        cfg=base_config,
    )
    assert decision_revoked.authority == DecisionAuthority.FULL
    assert decision_revoked.reason == "not_approved"

    # 4. Previous None inside deadband gives FULL with reason 'no_previous'
    decision_none = route(
        probs=[0.8, 0.2],
        tier="standard",
        task_id="classify-request",
        previous=None,
        approved_for_low=True,
        requires_human_approval=False,
        cfg=base_config,
    )
    assert decision_none.authority == DecisionAuthority.FULL
    assert decision_none.reason == "no_previous"

    # 5. Invalid previous string raises ValueError
    with pytest.raises(ValueError, match="unknown previous"):
        route(
            probs=[0.8, 0.2],
            tier="standard",
            task_id="classify-request",
            previous="unrecognized",
            approved_for_low=True,
            cfg=base_config,
        )


def test_ac5_no_hunting(base_config: RoutingConfig) -> None:
    """AC_5: over a sequence of entropies oscillating inside the deadband, route changes at most once."""
    # Sequence of probabilities all inside deadband [0.70, 1.0] with margin >= 0.20:
    oscillating_probs = [
        [0.80, 0.20],  # ~0.7219 bits (inside deadband [0.70, 1.0])
        [0.78, 0.22],  # ~0.760 bits
        [0.75, 0.25],  # ~0.811 bits
        [0.78, 0.22],  # ~0.760 bits
        [0.76, 0.24],  # ~0.795 bits
        [0.79, 0.21],  # ~0.742 bits
    ]

    # Test with initial route = LOW
    current_authority: DecisionAuthority | None = DecisionAuthority.LOW
    route_changes = 0

    for probs in oscillating_probs:
        decision = route(
            probs=probs,
            tier="standard",
            task_id="classify-request",
            previous=current_authority,
            approved_for_low=True,
            requires_human_approval=False,
            cfg=base_config,
        )
        if decision.authority != current_authority:
            route_changes += 1
            current_authority = decision.authority

    assert route_changes <= 1, f"Route changed {route_changes} times during deadband oscillation (max 1 allowed)"


def test_ac6_fail_safe(base_config: RoutingConfig) -> None:
    """AC_6: empty list, NaN, inf, negative prob, bad sum, unknown tier route FULL with reason 'anomaly' and text."""
    anomaly_cases = [
        ([], "empty probabilities"),
        ([float("nan"), 0.5], "non-finite probability: nan"),
        ([float("inf"), 0.0], "non-finite probability: inf"),
        ([-0.1, 1.1], "negative probability: -0.1"),
        ([0.45, 0.45], "probabilities sum to 0.9"),  # Sums to 0.9
        ([0.60, 0.50], "probabilities sum to 1.1"),  # Sums to 1.1
        ([True, False], "non-finite probability: true"),  # Booleans are rejected
    ]

    for probs, expected_anomaly_sub in anomaly_cases:
        decision = route(
            probs=probs,
            tier="standard",
            task_id="classify-request",
            previous=DecisionAuthority.LOW,
            approved_for_low=True,
            requires_human_approval=False,
            cfg=base_config,
        )
        assert decision.authority == DecisionAuthority.FULL
        assert decision.reason == "anomaly"
        assert decision.entropy_bits is None
        assert decision.margin is None
        assert decision.anomaly is not None
        assert expected_anomaly_sub.lower() in decision.anomaly.lower()

    # Unknown tier
    decision_unknown_tier = route(
        probs=[0.95, 0.05],
        tier="super-critical",
        task_id="classify-request",
        previous=DecisionAuthority.LOW,
        approved_for_low=True,
        requires_human_approval=False,
        cfg=base_config,
    )
    assert decision_unknown_tier.authority == DecisionAuthority.FULL
    assert decision_unknown_tier.reason == "anomaly"
    assert decision_unknown_tier.entropy_bits is None
    assert decision_unknown_tier.margin is None
    assert decision_unknown_tier.anomaly is not None
    assert "unknown tier" in decision_unknown_tier.anomaly.lower()

    # Missing routing config routes FULL with anomaly
    decision_no_cfg = route(
        probs=[0.8, 0.2],
        tier="standard",
        task_id="classify-request",
        cfg=None,
    )
    assert decision_no_cfg.authority == DecisionAuthority.FULL
    assert decision_no_cfg.reason == "anomaly"
    assert decision_no_cfg.anomaly is not None
    assert "missing routing config" in decision_no_cfg.anomaly.lower()
