"""Scheduled Epsilon-Greedy policy baseline (ADR-017, BRD-017, FDD-017).

Pure standard library exploration schedule and action selection under human safety masks.
"""

from __future__ import annotations

import copy
import datetime
import math
import random
import uuid
from collections.abc import Mapping, Sequence
from typing import Any

from agent_learning.policy.base import Decision, Policy
from agent_learning.policy.thompson import seed_for
from agent_learning.types import Action, PolicySnapshot
from agent_learning_ext.policy.action_statistics import ActionStats, read_statistics

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


def _find_greedy_action(
    actions: Sequence[Action],
    stats: Mapping[str, ActionStats],
) -> tuple[Action, dict[str, float]]:
    """Determine the greedy action and empirical means mapping (FDD-017 §3 item 3.5).

    Each action's mean is mean_reward when pull_count > 0, else 0.5 (neutral mean).
    Tie breaking:
        1. Highest mean
        2. Higher pull_count
        3. Lexicographically smaller action.id
    """
    empirical_means: dict[str, float] = {}
    best_action: Action | None = None
    best_mean = -math.inf
    best_pulls = -1

    for a in actions:
        st = stats[a.id]
        mean = st.mean_reward if st.pull_count > 0 else NEUTRAL_MEAN
        empirical_means[a.id] = mean

        if best_action is None or mean > best_mean:
            best_action = a
            best_mean = mean
            best_pulls = st.pull_count
        elif mean == best_mean:
            if st.pull_count > best_pulls or (
                st.pull_count == best_pulls and a.id < best_action.id
            ):
                best_action = a
                best_mean = mean
                best_pulls = st.pull_count

    if best_action is None:
        raise ValueError("policy has no actions")

    return best_action, empirical_means


class CallableSnapshot:
    """Wrapper allowing policy.snapshot to be accessed as both a PolicySnapshot and a callable method."""

    def __init__(self, target: PolicySnapshot) -> None:
        object.__setattr__(self, "_target", target)

    def __call__(self) -> PolicySnapshot:
        return self._target

    def __getattr__(self, name: str) -> Any:
        if name == "_target":
            raise AttributeError(name)
        target = self.__dict__.get("_target")
        if target is None:
            raise AttributeError(name)
        return getattr(target, name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "_target":
            object.__setattr__(self, name, value)
        else:
            setattr(self._target, name, value)

    def __deepcopy__(self, memo: dict[int, Any]) -> CallableSnapshot:
        return CallableSnapshot(copy.deepcopy(self._target, memo))

    def to_dict(self) -> dict[str, Any]:
        return self._target.to_dict()


class EpsilonGreedyPolicy(Policy):
    """Scheduled Epsilon-Greedy policy baseline with safety mask (ADR-017, FDD-017)."""

    def __init__(self, snapshot: PolicySnapshot) -> None:
        self._snapshot = snapshot
        self._last_record: dict[str, Any] | None = None

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
    def snapshot(self) -> CallableSnapshot:
        """Return the underlying PolicySnapshot (supports both property access and method call)."""
        return CallableSnapshot(self._snapshot)

    @property
    def actions(self) -> Sequence[Action]:
        """Sequence of actions available in the policy snapshot."""
        return self._snapshot.actions

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

    def choose(
        self,
        state: Any = None,
        *,
        request_id: str | None = None,
        timestamp: str | None = None,
    ) -> Decision:
        """Choose an action under the exploration schedule and safety mask (FDD-017 §3 item 3)."""
        if not self._snapshot.actions:
            raise ValueError("policy has no actions")

        if request_id is None:
            request_id = str(uuid.uuid4())
        if timestamp is None:
            timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Seed PRNG via HMAC-SHA256 (Story 15.1, ADR-015 §4.3)
        seed = seed_for(self._snapshot.id, request_id, timestamp)
        rng = random.Random(seed)

        metadata = self._snapshot.metadata or {}
        stats = read_statistics(metadata, [a.id for a in self._snapshot.actions])
        total_pulls = sum(st.pull_count for st in stats.values())

        safe = self.safe_actions
        safe_ids = {a.id for a in safe}

        if not safe:
            eps = 0.0
        else:
            schedule = metadata.get("epsilon_schedule", {})
            eps = epsilon_at(total_pulls, schedule["eps0"], schedule["delta"], schedule["floor"])

        # The branch coin u is drawn first from the seeded PRNG on every decision (FDD-017 F4)
        u = rng.random()
        branch_taken = "exploration" if (bool(safe) and u < eps) else "exploitation"

        greedy_action, empirical_means = _find_greedy_action(self._snapshot.actions, stats)

        if branch_taken == "exploration":
            chosen = rng.choice(safe)
        else:
            chosen = greedy_action

        # Calculate display selection probabilities (FDD-017 §3 item 3.7)
        # P(a) = (1 - eps) * [a == g] + (eps / |S|) * [a in S]
        probabilities: list[float] = []
        num_safe = len(safe)
        for a in self._snapshot.actions:
            prob = 0.0
            if a.id == greedy_action.id:
                prob += 1.0 - eps
            if num_safe > 0 and a.id in safe_ids:
                prob += eps / num_safe
            probabilities.append(prob)

        self._last_record = {
            "request_id": request_id,
            "timestamp": timestamp,
            "prng_seed": str(seed),
            "branch_taken": branch_taken,
            "exploration_rate_applied": float(eps),
            "total_pulls": total_pulls,
            "empirical_means": empirical_means,
            "chosen": chosen.id,
        }

        return Decision(action=chosen, logprob=None, probabilities=probabilities)

    def last_decision_record(self) -> dict[str, Any]:
        """Return a deep copy of the last decision record (FDD-017 §2.3, §3 item 4)."""
        if self._last_record is None:
            raise RuntimeError("no decision has been made yet")
        return copy.deepcopy(self._last_record)

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

    def consumed_episode_ids(self) -> list[str]:
        """Return a copy of the ids of the episodes already counted."""
        metadata = self._snapshot.metadata or {}
        return list(metadata.get("consumed_episode_ids", []))

    def update_statistics(
        self,
        metadata: dict[str, Any],
        *,
        episodes_seen: int,
    ) -> None:
        """Update action statistics and advance snapshot version (used by EpsilonGreedyLearner)."""
        action_ids = [action.id for action in self._snapshot.actions]
        read_statistics(metadata, action_ids)
        self._snapshot.metadata = copy.deepcopy(metadata)
        self._snapshot.episodes_seen = int(episodes_seen)
        self._snapshot.updates_applied += 1
        self._snapshot.advance_version()

    def apply_update(self, *args: Any, **kwargs: Any) -> Any:
        """Disallow direct logit updates on non-logit policy (FDD-017 §3 item 6)."""
        raise TypeError("use EpsilonGreedyLearner")


def replay(record: Mapping[str, Any], snapshot: PolicySnapshot) -> dict[str, str]:
    """Replay an epsilon-greedy decision from its audit record (FDD-017 §3 item 5).

    Re-derives the seed, checks equality with prng_seed, redraws the branch coin and
    pick, and returns {'branch_taken': ..., 'chosen': ...}.

    Raises:
        ValueError: If prng_seed does not match the re-derived seed.
    """
    req_id = record.get("request_id")
    ts = record.get("timestamp")
    recorded_seed = record.get("prng_seed")

    expected_seed = seed_for(snapshot.id, str(req_id), str(ts))
    if str(expected_seed) != str(recorded_seed):
        raise ValueError(
            f"prng_seed mismatch: recorded {recorded_seed!r} != expected {expected_seed}"
        )

    rng = random.Random(expected_seed)
    metadata = snapshot.metadata or {}
    stats = read_statistics(metadata, [a.id for a in snapshot.actions])
    total_pulls = sum(st.pull_count for st in stats.values())

    safe = sorted(
        [
            a
            for a in snapshot.actions
            if a.parameters is not None and a.parameters.get("reversible") is True
        ],
        key=lambda a: a.id,
    )

    if not safe:
        eps = 0.0
    else:
        schedule = metadata.get("epsilon_schedule", {})
        eps = epsilon_at(total_pulls, schedule["eps0"], schedule["delta"], schedule["floor"])

    u = rng.random()
    branch_taken = "exploration" if (bool(safe) and u < eps) else "exploitation"

    if branch_taken == "exploration":
        chosen_id = rng.choice(safe).id
    else:
        greedy_action, _ = _find_greedy_action(snapshot.actions, stats)
        chosen_id = greedy_action.id

    return {
        "branch_taken": branch_taken,
        "chosen": chosen_id,
    }


__all__ = [
    "NEUTRAL_MEAN",
    "SELECTION_BASIS",
    "EpsilonGreedyPolicy",
    "epsilon_at",
    "replay",
]
