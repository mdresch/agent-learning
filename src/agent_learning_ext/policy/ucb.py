"""Deterministic Upper Confidence Bound (UCB) decision policy (ADR-016, FDD-016).

Implements deterministic action scoring via standard UCB1 and Wilson score upper bounds.
Guarantees 100% audit replayability with zero random numbers generated.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

from agent_learning_ext.autonomy import wilson_lower_bound
from agent_learning_ext.policy.action_statistics import ActionStats

# Constants per FDD-016 §2.1
WILSON_Z: float = 1.96
C_DEFAULT: float = math.sqrt(2)
SELECTION_BASIS: str = "ucb"


def ucb_scores(
    stats: Mapping[str, ActionStats],
    total: int,
    *,
    variant: str = "wilson",
    c: float = C_DEFAULT,
) -> dict[str, float]:
    """Compute deterministic upper confidence bounds for actions given their counts and rewards.

    Args:
        stats: Mapping of action_id to ActionStats.
        total: Total pulls across all actions in stats. Must equal sum(s.pull_count for s in stats.values()).
        variant: 'standard' (UCB1) or 'wilson' (Wilson score interval upper bound).
        c: Exploration parameter for 'standard' variant (default sqrt(2)).

    Returns:
        Mapping of action_id to computed score (float or math.inf).

    Raises:
        ValueError: For unknown variant, non-positive or non-finite c, total mismatch,
            invalid/negative/non-integer pull_count, or cumulative_reward outside [0, pull_count] or non-finite.
    """
    if variant not in ("standard", "wilson"):
        raise ValueError(f"unknown variant {variant!r}; must be 'standard' or 'wilson'")

    if not isinstance(c, (int, float)) or not math.isfinite(c) or c <= 0:
        raise ValueError(f"c must be a positive finite float; got {c!r}")

    sum_pulls = 0
    for action_id, stat in stats.items():
        if not isinstance(stat.pull_count, int) or isinstance(stat.pull_count, bool) or stat.pull_count < 0:
            raise ValueError(f"invalid pull_count for action {action_id!r}: {stat.pull_count!r}")
        if not isinstance(stat.cumulative_reward, (int, float)) or not math.isfinite(stat.cumulative_reward):
            raise ValueError(f"invalid non-finite cumulative_reward for action {action_id!r}: {stat.cumulative_reward!r}")
        if stat.cumulative_reward < 0.0 or stat.cumulative_reward > stat.pull_count:
            raise ValueError(
                f"cumulative_reward for action {action_id!r} ({stat.cumulative_reward}) "
                f"must be in [0, pull_count] (0..{stat.pull_count})"
            )
        sum_pulls += stat.pull_count

    if total != sum_pulls:
        raise ValueError(f"total ({total}) must equal sum of pull counts ({sum_pulls})")

    scores: dict[str, float] = {}
    for action_id, stat in stats.items():
        if stat.pull_count == 0:
            scores[action_id] = math.inf
        elif variant == "standard":
            mean = stat.cumulative_reward / stat.pull_count
            if total <= 1:
                bonus = 0.0
            else:
                bonus = c * math.sqrt(2.0 * math.log(total) / stat.pull_count)
            scores[action_id] = mean + bonus
        else:  # wilson
            k = stat.cumulative_reward
            n = stat.pull_count
            scores[action_id] = 1.0 - wilson_lower_bound(n - k, n, z=WILSON_Z)

    return scores
