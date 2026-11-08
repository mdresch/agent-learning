"""Deterministic Upper Confidence Bound (UCB) decision policy (ADR-016, FDD-016).

Implements deterministic action scoring via standard UCB1 and Wilson score upper bounds.
Guarantees 100% audit replayability with zero random numbers generated.
"""

from __future__ import annotations

import copy
import math
from collections.abc import Mapping, Sequence
from typing import Any

from agent_learning.policy.base import Decision, Policy
from agent_learning.types import Action, PolicySnapshot
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
        ValueError: For unknown variant, non-positive or non-finite c, total mismatch or non-integer total,
            invalid/negative/non-integer pull_count, or cumulative_reward outside [0, pull_count] or non-finite.
    """
    if variant not in ("standard", "wilson"):
        raise ValueError(f"unknown variant {variant!r}; must be 'standard' or 'wilson'")

    if isinstance(total, bool) or not isinstance(total, int) or total < 0:
        raise ValueError(f"total must be a non-negative integer; got {total!r}")

    if isinstance(c, bool) or not isinstance(c, (int, float)) or not math.isfinite(c) or c <= 0:
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


class UCBPolicy(Policy):
    """Deterministic Upper Confidence Bound decision policy (ADR-016, FDD-016)."""

    def __init__(self, snapshot: PolicySnapshot) -> None:
        self._snapshot = copy.deepcopy(snapshot)
        self._last_decision_record: dict[str, Any] | None = None

    def choose(self, state: Any = None) -> Decision:
        """Deterministically choose an action using Upper Confidence Bound scoring."""
        if not self._snapshot.actions:
            raise ValueError("policy has no actions")

        stats_meta = self._snapshot.metadata.get("action_statistics", {})
        variant = self._snapshot.metadata.get("ucb_variant", "wilson")
        c = self._snapshot.metadata.get("exploration_constant", C_DEFAULT)

        # Ingest statistics for every action in action space
        stats: dict[str, ActionStats] = {}
        total = 0
        for action in self._snapshot.actions:
            raw = stats_meta.get(action.id)
            if raw is None:
                st = ActionStats(pull_count=0, cumulative_reward=0.0, mean_reward=0.0)
            elif isinstance(raw, ActionStats):
                st = raw
            elif isinstance(raw, dict):
                st = ActionStats(
                    pull_count=raw.get("pull_count", 0),
                    cumulative_reward=float(raw.get("cumulative_reward", 0.0)),
                    mean_reward=float(raw.get("mean_reward", 0.0)),
                )
            else:
                st = ActionStats(pull_count=0, cumulative_reward=0.0, mean_reward=0.0)
            stats[action.id] = st
            total += st.pull_count

        scores = ucb_scores(stats, total, variant=variant, c=c)

        # Deterministic selection with tie-breaking:
        # 1. Highest score (math.inf is largest float)
        # 2. Higher pull_count
        # 3. Lexicographically smaller action.id
        best_action: Action | None = None
        best_score = -math.inf
        best_pulls = -1

        for action in self._snapshot.actions:
            sc = scores[action.id]
            pc = stats[action.id].pull_count
            if best_action is None or sc > best_score:
                best_action = action
                best_score = sc
                best_pulls = pc
            elif sc == best_score:
                if pc > best_pulls:
                    best_action = action
                    best_score = sc
                    best_pulls = pc
                elif pc == best_pulls:
                    if action.id < best_action.id:
                        best_action = action
                        best_score = sc
                        best_pulls = pc

        assert best_action is not None

        # Build one-hot probabilities
        probabilities = [1.0 if a.id == best_action.id else 0.0 for a in self._snapshot.actions]

        # Record decision
        self._last_decision_record = {
            "variant": variant,
            "exploration_constant": c,
            "total_pulls": total,
            "chosen": best_action.id,
            "scores": {aid: (None if s == math.inf else s) for aid, s in scores.items()},
        }

        return Decision(
            action=best_action,
            logprob=None,
            probabilities=probabilities,
        )

    def actions(self) -> Sequence[Action]:
        """Return the action space."""
        return self._snapshot.actions

    def snapshot(self) -> PolicySnapshot:
        """Return a copy of the policy snapshot."""
        return copy.deepcopy(self._snapshot)

    def last_decision_record(self) -> dict[str, Any] | None:
        """Return a deep copy of the last decision record or None."""
        if self._last_decision_record is None:
            return None
        return copy.deepcopy(self._last_decision_record)

    def apply_update(self, *args: Any, **kwargs: Any) -> None:
        """Raise TypeError: UCBPolicy does not support direct logit updates."""
        raise TypeError("use UCBLearner: UCBPolicy is not a logit-based policy")
