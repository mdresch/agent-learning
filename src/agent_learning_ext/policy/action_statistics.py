"""Shared action statistics primitives for count-based policies (FDD-016 §2.4, FDD-017).

Provides the ActionStats dataclass and shared validation/update routines.
Pure standard library only: no random, no storage imports.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
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


def reward_to_r(value: float) -> float:
    """Map a reward in [-1, 1] to r in [0, 1] via (value + 1) / 2 (FDD-016 §2.4, E1)."""
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value < -1.0
        or value > 1.0
    ):
        raise ValueError(f"reward value must be finite and within [-1, 1], got {value!r}")
    return (float(value) + 1.0) / 2.0


def add_rewards(
    metadata: dict[str, Any],
    action_ids: Sequence[str],
    items: Iterable[tuple[str, str, float]],
) -> tuple[str, ...]:
    """In-place update of action statistics and consumed episode ids (FDD-016 §2.4, E1, E6, E7).

    Parameters:
        metadata: policy snapshot metadata dictionary modified in place.
        action_ids: collection of valid action ids.
        items: iterable of (episode_id, action_id, value) tuples where value in [-1, 1].

    Returns:
        tuple of episode ids counted, in order.
    """
    if not isinstance(metadata, dict):
        raise TypeError("metadata must be a dictionary")

    action_set = set(action_ids)

    consumed_raw = metadata.setdefault("consumed_episode_ids", [])
    if not isinstance(consumed_raw, list):
        raise TypeError("consumed_episode_ids in metadata must be a list")
    seen = set(consumed_raw)

    action_stats = metadata.setdefault("action_statistics", {})
    if not isinstance(action_stats, dict):
        raise TypeError("action_statistics in metadata must be a dictionary")

    counted_ids: list[str] = []

    for episode_id, action_id, value in items:
        # Skip if already counted in consumed_episode_ids or previously in this call
        if episode_id in seen:
            continue

        # Validate value and map to r
        r = reward_to_r(value)

        if action_id not in action_set:
            raise ValueError(f"action {action_id!r} not in action space")

        seen.add(episode_id)
        consumed_raw.append(episode_id)
        counted_ids.append(episode_id)

        raw = action_stats.get(action_id)
        if raw is None:
            pull_count = 0
            cumulative_reward = 0.0
        elif isinstance(raw, dict):
            pull_count = raw.get("pull_count", 0)
            cumulative_reward = raw.get("cumulative_reward", 0.0)
        elif isinstance(raw, ActionStats):
            pull_count = raw.pull_count
            cumulative_reward = raw.cumulative_reward
        else:
            raise ValueError(f"invalid statistics entry for action {action_id!r}: {raw!r}")

        new_pulls = pull_count + 1
        new_cum = cumulative_reward + r
        new_mean = new_cum / new_pulls

        action_stats[action_id] = {
            "pull_count": new_pulls,
            "cumulative_reward": new_cum,
            "mean_reward": new_mean,
        }

    return tuple(counted_ids)


__all__ = ["ActionStats", "add_rewards", "read_statistics", "reward_to_r"]
