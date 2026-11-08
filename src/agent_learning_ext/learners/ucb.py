"""Deterministic Upper Confidence Bound (UCB) learner (ADR-016, FDD-016).

Implements count-based episode updates for UCBPolicy.
Pure standard library only: zero random numbers, zero storage imports, zero file I/O.
"""

from __future__ import annotations

import copy
from collections.abc import Iterable

from agent_learning.learners.base import Learner, LearnerResult
from agent_learning.policy.base import Policy
from agent_learning.types import ConsumedInput, Episode, Reward, RewardSource
from agent_learning_ext.policy.action_statistics import add_rewards, reward_to_r
from agent_learning_ext.policy.ucb import SELECTION_BASIS, UCBPolicy


class UCBLearner(Learner):
    """Deterministic count-based learner for UCBPolicy (ADR-016, FDD-016).

    Counts aggregate episode rewards into action statistics exactly once.
    Delegates all statistic counting to policy/action_statistics.py:add_rewards (AC_6).
    """

    def update(
        self,
        policy: Policy,
        episodes: Iterable[Episode],
        rewards: Iterable[Reward],
    ) -> LearnerResult:
        """Apply one update to UCBPolicy using the supplied data (FDD-016 §3 item 6)."""
        if not isinstance(policy, UCBPolicy):
            raise TypeError("UCBLearner requires a UCBPolicy")

        snapshot = policy.snapshot()
        action_ids = [action.id for action in snapshot.actions]
        action_set = set(action_ids)

        # 1. Index newest aggregate reward per episode and validate values upfront
        aggregate: dict[str, Reward] = {}
        for reward in rewards:
            if reward.source != RewardSource.AGGREGATE:
                continue
            # Validate reward value upfront (reject non-finite, out-of-range, bool)
            reward_to_r(reward.value)
            current = aggregate.get(reward.episode_id)
            if current is None or reward.created_at > current.created_at:
                aggregate[reward.episode_id] = reward

        # 2. Collect eligible episodes (selection_basis="ucb", valid action, aggregate reward)
        offered_items: list[tuple[str, str, float]] = []
        episode_reward_map: dict[str, str] = {}
        for episode in episodes:
            if (
                episode.metadata.get("selection_basis") != SELECTION_BASIS
                or episode.action_id is None
                or episode.action_id not in action_set
            ):
                continue
            reward = aggregate.get(episode.id)
            if reward is None:
                continue

            offered_items.append((episode.id, episode.action_id, reward.value))
            episode_reward_map[episode.id] = reward.id

        if not offered_items:
            return LearnerResult(
                episodes_used=0,
                mean_reward=0.0,
                baseline_before=snapshot.baseline,
                baseline_after=snapshot.baseline,
                logit_deltas={action.id: 0.0 for action in snapshot.actions},
                extra={"reason": "no usable episodes"},
                consumed_inputs=[],
            )

        metadata_copy = copy.deepcopy(snapshot.metadata)
        stats_before = copy.deepcopy(metadata_copy.get("action_statistics", {}))

        # 3. Add rewards via shared function add_rewards (AC_6)
        counted_ids = add_rewards(metadata_copy, action_ids, offered_items)

        if not counted_ids:
            return LearnerResult(
                episodes_used=0,
                mean_reward=0.0,
                baseline_before=snapshot.baseline,
                baseline_after=snapshot.baseline,
                logit_deltas={action.id: 0.0 for action in snapshot.actions},
                extra={"reason": "no newly counted episodes"},
                consumed_inputs=[],
            )

        # 4. Advance snapshot version and record stats
        policy.update_statistics(
            metadata_copy,
            episodes_seen=snapshot.episodes_seen + len(counted_ids),
        )

        stats_after = copy.deepcopy(metadata_copy.get("action_statistics", {}))
        mapped_rewards = [reward_to_r(aggregate[eid].value) for eid in counted_ids]
        mean_mapped = sum(mapped_rewards) / len(counted_ids)

        consumed_inputs = [
            ConsumedInput(episode_id=eid, reward_id=episode_reward_map[eid])
            for eid in counted_ids
        ]

        return LearnerResult(
            episodes_used=len(counted_ids),
            mean_reward=mean_mapped,
            baseline_before=snapshot.baseline,
            baseline_after=snapshot.baseline,
            logit_deltas={action.id: 0.0 for action in snapshot.actions},
            extra={
                "statistics_before": stats_before,
                "statistics_after": stats_after,
            },
            consumed_inputs=consumed_inputs,
        )


__all__ = ["UCBLearner"]
