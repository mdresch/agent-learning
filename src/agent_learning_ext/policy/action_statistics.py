"""Shared action statistics primitives for count-based policies (FDD-016 §2.4, FDD-017).

Provides the ActionStats dataclass and shared validation/update routines.
Pure standard library only: no random, no storage imports.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ActionStats:
    """Action statistics for count-based exploration policies."""

    pull_count: int
    cumulative_reward: float
    mean_reward: float


def read_statistics(
    metadata: Mapping[str, Any] | None,
    action_ids: Sequence[str],
) -> dict[str, ActionStats]:
    """Read and validate action statistics from policy snapshot metadata (FDD-016 §2.4).

    Args:
        metadata: PolicySnapshot.metadata mapping, or None.
        action_ids: Sequence of allowed action IDs in the action space.

    Returns:
        Mapping of action_id to validated ActionStats (defaults to 0, 0.0, 0.0 if missing).

    Raises:
        ValueError: If metadata contains:
            - an action id outside action_ids
            - a negative or non-integer pull_count
            - cumulative_reward outside [0, pull_count] or not finite
            - mean_reward differing from cumulative_reward / pull_count by > 1e-9
            - duplicate episode IDs in consumed_episode_ids
    """
    if metadata is None:
        metadata = {}

    # Check consumed_episode_ids for duplicates
    consumed = metadata.get("consumed_episode_ids", [])
    if isinstance(consumed, (list, tuple)):
        seen: set[str] = set()
        for eid in consumed:
            if eid in seen:
                raise ValueError(f"duplicate id in consumed_episode_ids: {eid!r}")
            seen.add(eid)

    stats_dict = metadata.get("action_statistics", {})
    if not isinstance(stats_dict, dict):
        stats_dict = {}

    allowed_set = set(action_ids)
    for aid in stats_dict:
        if aid not in allowed_set:
            raise ValueError(f"action id {aid!r} in statistics is outside the action space")

    result: dict[str, ActionStats] = {}
    for aid in action_ids:
        raw = stats_dict.get(aid)
        if raw is None:
            result[aid] = ActionStats(pull_count=0, cumulative_reward=0.0, mean_reward=0.0)
            continue

        if isinstance(raw, ActionStats):
            pull_count = raw.pull_count
            cumulative_reward = raw.cumulative_reward
            mean_reward = raw.mean_reward
        elif isinstance(raw, dict):
            pull_count = raw.get("pull_count", 0)
            cumulative_reward = raw.get("cumulative_reward", 0.0)
            mean_reward = raw.get("mean_reward", 0.0)
        else:
            raise ValueError(f"invalid statistics entry for action {aid!r}: {raw!r}")  # noqa: TRY004

        # Validate pull_count
        if isinstance(pull_count, bool) or not isinstance(pull_count, int) or pull_count < 0:
            raise ValueError(f"invalid pull_count for action {aid!r}: {pull_count!r}")

        # Validate cumulative_reward
        if isinstance(cumulative_reward, bool) or not isinstance(cumulative_reward, (int, float)) or not math.isfinite(cumulative_reward):
            raise ValueError(f"invalid non-finite cumulative_reward for action {aid!r}: {cumulative_reward!r}")
        if cumulative_reward < 0.0 or cumulative_reward > pull_count:
            raise ValueError(
                f"cumulative_reward for action {aid!r} ({cumulative_reward}) "
                f"must be in [0, pull_count] (0..{pull_count})"
            )

        # Validate mean_reward
        if isinstance(mean_reward, bool) or not isinstance(mean_reward, (int, float)) or not math.isfinite(mean_reward):
            raise ValueError(f"invalid non-finite mean_reward for action {aid!r}: {mean_reward!r}")

        expected_mean = 0.0 if pull_count == 0 else (cumulative_reward / pull_count)
        if abs(mean_reward - expected_mean) > 1e-9:
            raise ValueError(
                f"mean_reward for action {aid!r} ({mean_reward}) differs from "
                f"cumulative_reward / pull_count ({expected_mean}) by more than 1e-9"
            )

        result[aid] = ActionStats(
            pull_count=pull_count,
            cumulative_reward=float(cumulative_reward),
            mean_reward=float(mean_reward),
        )

    return result
