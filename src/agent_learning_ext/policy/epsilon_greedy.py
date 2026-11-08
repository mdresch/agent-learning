"""Scheduled Epsilon-Greedy policy baseline (ADR-017, BRD-017, FDD-017).

Pure standard library exploration schedule and action selection under human safety masks.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from agent_learning.policy.base import Policy
from agent_learning.types import Action, PolicySnapshot
from agent_learning_ext.policy.action_statistics import read_statistics

# Constants per FDD-017 §2.1
SELECTION_BASIS: str = "epsilon_greedy"
NEUTRAL_MEAN: float = 0.5


def epsilon_at(t: float, eps0: float, delta: float, floor: float) -> float:
    """Compute the scheduled exploration rate epsilon at pull count t (ADR-017, FDD-017 §3.1).

    Formula:
        max(floor, eps0 / (1.0 + delta * t))

    Args:
        t: Non-negative pull count (int or finite float >= 0).
        eps0: Initial exploration rate in [0, 1].
        delta: Non-negative decay factor (delta >= 0).
        floor: Minimum exploration floor in [0, 1] where floor <= eps0.

    Returns:
        Exploration probability rate in [floor, eps0].

    Raises:
        ValueError: If any argument is non-finite, boolean, outside valid ranges,
            or if eps0 < floor.
    """
    # Validate t
    if isinstance(t, bool):
        raise ValueError("argument 't' must be numeric, not bool")  # noqa: TRY004
    if not isinstance(t, (int, float)) or not math.isfinite(t):
        raise ValueError(f"argument 't' must be finite, got {t!r}")
    if t < 0:
        raise ValueError(f"argument 't' must be non-negative, got {t!r}")

    # Validate delta
    if isinstance(delta, bool):
        raise ValueError("argument 'delta' must be numeric, not bool")  # noqa: TRY004
    if not isinstance(delta, (int, float)) or not math.isfinite(delta):
        raise ValueError(f"argument 'delta' must be finite, got {delta!r}")
    if delta < 0:
        raise ValueError(f"argument 'delta' must be non-negative, got {delta!r}")

    # Validate floor
    if isinstance(floor, bool):
        raise ValueError("argument 'floor' must be numeric, not bool")  # noqa: TRY004
    if not isinstance(floor, (int, float)) or not math.isfinite(floor):
        raise ValueError(f"argument 'floor' must be finite, got {floor!r}")
    if floor < 0.0 or floor > 1.0:
        raise ValueError(f"argument 'floor' must be in [0, 1], got {floor!r}")

    # Validate eps0
    if isinstance(eps0, bool):
        raise ValueError("argument 'eps0' must be numeric, not bool")  # noqa: TRY004
    if not isinstance(eps0, (int, float)) or not math.isfinite(eps0):
        raise ValueError(f"argument 'eps0' must be finite, got {eps0!r}")
    if eps0 < 0.0 or eps0 > 1.0:
        raise ValueError(f"argument 'eps0' must be in [0, 1], got {eps0!r}")

    # Validate ordering
    if eps0 < floor:
        raise ValueError(f"argument 'eps0' ({eps0}) cannot be less than argument 'floor' ({floor})")

    decayed = float(eps0) / (1.0 + float(delta) * float(t))
    return float(max(float(floor), decayed))


def _validate_reversible(action: Action) -> None:
    """Validate that action parameters['reversible'], if present, is strictly a boolean (FDD-017 §2.1)."""
    if action.parameters is not None and "reversible" in action.parameters:
        val = action.parameters["reversible"]
        if not isinstance(val, bool):
            raise ValueError(
                f"action {action.id!r}: 'reversible' parameter must be a boolean, got {val!r}"
            )


class EpsilonGreedyPolicy(Policy):
    """Scheduled Epsilon-Greedy policy baseline with safety mask (ADR-017, FDD-017)."""

    def __init__(self, snapshot: PolicySnapshot) -> None:
        self._snapshot = snapshot
        metadata = getattr(snapshot, "metadata", None) or {}
        policy_type = metadata.get("policy_type")
        if policy_type != "epsilon_greedy":
            raise ValueError(f"snapshot policy_type must be 'epsilon_greedy'; got {policy_type!r}")

        schedule = metadata.get("epsilon_schedule")
        if not isinstance(schedule, dict):
            raise ValueError("snapshot metadata must contain 'epsilon_schedule' dictionary")  # noqa: TRY004
        # Validate schedule parameters using epsilon_at
        epsilon_at(0, schedule["eps0"], schedule["delta"], schedule["floor"])

        # Validate all action reversible flags (FDD-017 F7)
        for action in snapshot.actions:
            _validate_reversible(action)

        # Validate statistics
        read_statistics(metadata, [a.id for a in snapshot.actions])

    @property
    def snapshot(self) -> PolicySnapshot:
        """Return the underlying PolicySnapshot."""
        return self._snapshot

    @property
    def actions(self) -> Sequence[Action]:
        """Sequence of actions available in the policy snapshot."""
        return self._snapshot.actions

    def choose(
        self,
        state: Any = None,
        *,
        request_id: str | None = None,
        timestamp: str | None = None,
    ) -> Any:
        """Choose an action (full implementation in Story 17.3)."""
        raise NotImplementedError("choose is implemented in Story 17.3")

    @property
    def safe_subset(self) -> set[str]:
        """Set of action IDs marked with reversible is True (FDD-017 §2.1)."""
        return {
            a.id
            for a in self._snapshot.actions
            if a.parameters is not None and a.parameters.get("reversible") is True
        }

    @property
    def safe_actions(self) -> list[Action]:
        """Sorted list of safe actions in lexicographical order by ID."""
        return sorted(
            [
                a
                for a in self._snapshot.actions
                if a.parameters is not None and a.parameters.get("reversible") is True
            ],
            key=lambda a: a.id,
        )

    def exploration_rate_applied(self, t: int | None = None) -> float:
        """Exploration rate applied given pull count t (or derived from statistics).

        If the safe subset is empty, returns 0.0 regardless of t (FDD-017 §3 item 3, BRU-017-03).
        """
        if not self.safe_subset:
            return 0.0

        metadata = self._snapshot.metadata or {}
        if t is None:
            stats = read_statistics(metadata, [a.id for a in self._snapshot.actions])
            t = sum(st.pull_count for st in stats.values())

        schedule = metadata.get("epsilon_schedule", {})
        return epsilon_at(t, schedule["eps0"], schedule["delta"], schedule["floor"])

    # Alias per convention
    rate_applied = exploration_rate_applied

    @classmethod
    def from_actions(
        cls,
        actions: Sequence[Action],
        *,
        eps0: float,
        delta: float,
        floor: float,
        agent_id: str = "default",
        task_id: str = "default",
    ) -> EpsilonGreedyPolicy:
        """Build an initial EpsilonGreedyPolicy from actions and schedule (FDD-017 §3 item 2)."""
        # Validate schedule
        epsilon_at(0, eps0, delta, floor)

        act_list = list(actions)
        for action in act_list:
            _validate_reversible(action)

        stats_dict = {
            a.id: {"pull_count": 0, "cumulative_reward": 0.0, "mean_reward": 0.0}
            for a in act_list
        }
        metadata: dict[str, Any] = {
            "policy_type": "epsilon_greedy",
            "epsilon_schedule": {
                "eps0": float(eps0),
                "delta": float(delta),
                "floor": float(floor),
            },
            "action_statistics": stats_dict,
            "consumed_episode_ids": [],
        }
        snapshot = PolicySnapshot(
            agent_id=agent_id,
            task_id=task_id,
            actions=act_list,
            logits={a.id: 0.0 for a in act_list},
            metadata=metadata,
        )
        return cls(snapshot)

    @classmethod
    def from_snapshot(cls, snapshot: PolicySnapshot) -> EpsilonGreedyPolicy:
        """Construct and validate an EpsilonGreedyPolicy from an existing PolicySnapshot."""
        return cls(snapshot)

    def apply_update(self, *args: Any, **kwargs: Any) -> Any:
        """Disallow direct logit updates on non-logit policy (FDD-017 §3 item 6)."""
        raise TypeError("use EpsilonGreedyLearner")


__all__ = ["NEUTRAL_MEAN", "SELECTION_BASIS", "EpsilonGreedyPolicy", "epsilon_at"]
