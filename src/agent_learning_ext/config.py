"""Amended configuration for agent_learning_ext (fork rule: Microsoft's ``config.py`` is not edited).

``AutonomyConfig`` here subclasses Microsoft's, so it is accepted wherever Microsoft's is. It resolves each metric from its tier
variable, then the global variable, then the tier default (FDD-003 Design 1), and adds the cross-tier monotonicity check
(ADR-003 Invariant 5).
"""

from __future__ import annotations

import logging
import os

from agent_learning.config import (
    _AUTONOMY_TIER_DEFAULTS,
    AutonomyConfig as _MicrosoftAutonomyConfig,
    AutonomyTier,
    _env_float,
    _env_int,
)

logger = logging.getLogger(__name__)


def _tier_override_keys(metric: str, tier: str) -> tuple[str, str]:
    global_key = f"AGENT_LEARNING_AUTONOMY_{metric}"
    return f"{global_key}_{tier.upper()}", global_key


def _note_global_override(metric: str, tier: str) -> None:
    tier_key, global_key = _tier_override_keys(metric, tier)
    global_value = os.getenv(global_key)
    if global_value and not os.getenv(tier_key):
        logger.info(
            "Using global autonomy override %s=%s for tier %s",
            global_key,
            global_value,
            tier,
        )


def _env_tier_int(metric: str, tier: str, default: int) -> int:
    """Tier variable, then global variable, then default (FDD-003 Design 1)."""
    tier_key, global_key = _tier_override_keys(metric, tier)
    _note_global_override(metric, tier)
    return _env_int(tier_key, _env_int(global_key, default))


def _env_tier_float(metric: str, tier: str, default: float) -> float:
    """Tier variable, then global variable, then default (FDD-003 Design 1)."""
    tier_key, global_key = _tier_override_keys(metric, tier)
    _note_global_override(metric, tier)
    return _env_float(tier_key, _env_float(global_key, default))


class AutonomyConfig(_MicrosoftAutonomyConfig):
    """Microsoft's AutonomyConfig with per-tier environment overrides."""

    @classmethod
    def for_tier(cls, tier: AutonomyTier) -> "AutonomyConfig":
        """Resolve each metric from its tier variable, then the global variable, then the tier default."""
        defaults = _AUTONOMY_TIER_DEFAULTS[tier]
        return cls(
            min_outcomes=_env_tier_int(
                "MIN_OUTCOMES", tier, int(defaults["min_outcomes"])
            ),
            min_correctness_lower_bound=_env_tier_float(
                "MIN_CORRECTNESS_LOWER_BOUND", tier, float(defaults["min_correctness_lower_bound"])
            ),
            min_mean_reward=_env_tier_float(
                "MIN_MEAN_REWARD", tier, float(defaults["min_mean_reward"])
            ),
            min_action_probability=_env_tier_float(
                "MIN_ACTION_PROBABILITY", tier, float(defaults["min_action_probability"])
            ),
            min_probability_margin=_env_tier_float(
                "MIN_PROBABILITY_MARGIN", tier, float(defaults["min_probability_margin"])
            ),
            stable_snapshots=_env_tier_int(
                "STABLE_SNAPSHOTS", tier, int(defaults["stable_snapshots"])
            ),
            audit_rate=_env_tier_float(
                "AUDIT_RATE", tier, float(defaults["audit_rate"])
            ),
            wilson_z=_env_float("AGENT_LEARNING_AUTONOMY_WILSON_Z", 1.96),
        )


_MONOTONIC_GATES: tuple[str, ...] = (
    "min_outcomes",
    "min_correctness_lower_bound",
    "min_mean_reward",
    "min_action_probability",
    "min_probability_margin",
    "stable_snapshots",
)
_AUTONOMY_TIERS: tuple[AutonomyTier, ...] = ("low", "standard", "high", "critical")


def validate_autonomy_monotonicity() -> None:
    """Reject configurations where a higher tier is easier to enter than a lower one.

    Covers the six statistical entry gates (ADR-003 Invariant 5). Drift-audit rate
    is a post-autonomy sampling parameter and is not one of them (ADR-003 4.3).
    """
    configs = [AutonomyConfig.for_tier(tier) for tier in _AUTONOMY_TIERS]
    for index in range(len(configs) - 1):
        lower, upper = configs[index], configs[index + 1]
        for gate in _MONOTONIC_GATES:
            lower_value, upper_value = getattr(lower, gate), getattr(upper, gate)
            if lower_value > upper_value:
                raise ValueError(
                    f"Autonomy monotonicity violation: {gate} for "
                    f"{_AUTONOMY_TIERS[index]} ({lower_value}) exceeds "
                    f"{_AUTONOMY_TIERS[index + 1]} ({upper_value})"
                )


__all__ = ["AutonomyConfig", "validate_autonomy_monotonicity"]
