"""Shared action statistics primitives for count-based policies (FDD-016 §2.4, FDD-017).

Provides the ActionStats dataclass and shared validation/update routines.
Pure standard library only: no random, no storage imports.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ActionStats:
    """Action statistics for count-based exploration policies."""

    pull_count: int
    cumulative_reward: float
    mean_reward: float
