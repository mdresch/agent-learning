"""REINFORCE-with-baseline learner for :class:`ContextualSoftmaxPolicy` (ADR-038, FDD-038).

For one used episode with reward ``R``, baseline ``b``, feature vector ``phi`` and probabilities ``pi(. | phi)``:

    c_a = (R - b) * (1_{a == a_t} - pi(a | phi)) * phi

The row passed to ``apply_update`` for action ``a`` is ``learning_rate`` times the mean of ``c_a`` over the used episodes.
Every episode is scored on the weights the call started with. Clipping and the version bump stay inside ``apply_update``.
"""

from __future__ import annotations

from collections.abc import Iterable

from agent_learning.config import LearnerConfig
from agent_learning.learners import Learner, LearnerResult
from agent_learning.policy.base import Policy
from agent_learning.types import ConsumedInput, Episode, Reward, RewardSource


class ContextualReinforceLearner(Learner):
    """Updates the weight rows of a :class:`ContextualSoftmaxPolicy` from episodes that carry ``feature_vector``."""

    def __init__(self, config: LearnerConfig | None = None) -> None:
        self._config = config or LearnerConfig()

    @property
    def config(self) -> LearnerConfig:
        return self._config

    def update(
        self,
        policy: Policy,
        episodes: Iterable[Episode],
        rewards: Iterable[Reward],
    ) -> LearnerResult:
        aggregate_rewards: dict[str, Reward] = {}
        for r in rewards:
            if r.source != RewardSource.AGGREGATE:
                continue
            current = aggregate_rewards.get(r.episode_id)
            if current is None or r.created_at > current.created_at:
                aggregate_rewards[r.episode_id] = r

        snapshot = policy.snapshot()
        baseline_before = snapshot.baseline
        action_ids = [a.id for a in snapshot.actions]
        feature_dim = int(snapshot.metadata["feature_dim"])
        sums: dict[str, list[float]] = {aid: [0.0] * feature_dim for aid in action_ids}
        consumed_inputs: list[ConsumedInput] = []
        reward_sum = 0.0

        for episode in episodes:
            reward = aggregate_rewards.get(episode.id)
            if reward is None or episode.action_id not in sums:
                continue
            if not episode.metadata or "feature_vector" not in episode.metadata:
                continue
            phi = [float(x) for x in episode.metadata["feature_vector"]]
            probs = policy.probabilities(phi)
            advantage = reward.value - baseline_before
            for aid, p in zip(action_ids, probs):
                scale = advantage * ((1.0 if aid == episode.action_id else 0.0) - p)
                sums[aid] = [s + scale * x for s, x in zip(sums[aid], phi)]
            reward_sum += reward.value
            consumed_inputs.append(ConsumedInput(episode_id=episode.id, reward_id=reward.id))

        used = len(consumed_inputs)
        if used == 0:
            return LearnerResult(
                episodes_used=0,
                mean_reward=0.0,
                baseline_before=baseline_before,
                baseline_after=baseline_before,
                logit_deltas={},
                extra={"weight_deltas": {}},
                consumed_inputs=[],
            )
        weight_deltas = {
            aid: [self._config.learning_rate * s / used for s in row] for aid, row in sums.items()
        }
        mean_reward = reward_sum / used
        decay = self._config.baseline_decay
        baseline_after = decay * baseline_before + (1.0 - decay) * mean_reward

        policy.apply_update(weight_deltas, baseline=baseline_after, episodes_seen=snapshot.episodes_seen + used)

        return LearnerResult(
            episodes_used=used,
            mean_reward=mean_reward,
            baseline_before=baseline_before,
            baseline_after=baseline_after,
            logit_deltas={},
            extra={"weight_deltas": weight_deltas},
            consumed_inputs=consumed_inputs,
        )


__all__ = ["ContextualReinforceLearner"]
