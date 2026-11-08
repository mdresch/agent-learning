"""Pairwise Preference Optimization for discrete action logits (ADR-018, Epic 18).

Fits a SoftmaxPolicy's action logits directly to preference pairs (winner, loser)
extracted from human reviewer overrides with the Bradley-Terry model and convex
L2 regularization anchored to frozen reference logits.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from agent_learning.types import Episode


@dataclass(frozen=True)
class PreferencePair:
    """An ordinal preference between two discrete actions derived from an episode override."""

    winner: str
    loser: str
    source_episode_id: str


def pairs_from_episodes(
    episodes: Sequence[Episode],
    action_ids: Sequence[str],
) -> list[PreferencePair]:
    """Extract preference pairs from reviewer override episodes (FDD-018 §3 item 1).

    An episode yields a pair (winner=correct_action_id, loser=action_id) when:
    - metadata["feedback_status"], stripped and lowercased, is "rejected"
    - metadata["correct_action_id"] is a string in action_ids
    - action_id is in action_ids
    - correct_action_id != action_id

    Episodes offered multiple times contribute at most one pair, preserving
    the order of first appearance (G5). Input episodes are never modified.
    """
    valid_actions = set(action_ids)
    pairs: list[PreferencePair] = []
    seen_episode_ids: set[str] = set()

    for ep in episodes:
        if ep.id in seen_episode_ids:
            continue

        meta: dict[str, Any] = getattr(ep, "metadata", {}) or {}

        # 1. Feedback status check
        status_raw = meta.get("feedback_status")
        if not isinstance(status_raw, str):
            continue
        if status_raw.strip().lower() != "rejected":
            continue

        # 2. Correct action check
        correct_action = meta.get("correct_action_id")
        if not isinstance(correct_action, str):
            continue
        if correct_action not in valid_actions:
            continue

        # 3. Proposed action check
        proposed_action = getattr(ep, "action_id", None)
        if not isinstance(proposed_action, str):
            continue
        if proposed_action not in valid_actions:
            continue

        # 4. Differing actions
        if correct_action == proposed_action:
            continue

        seen_episode_ids.add(ep.id)
        pairs.append(
            PreferencePair(
                winner=correct_action,
                loser=proposed_action,
                source_episode_id=ep.id,
            )
        )

    return pairs
