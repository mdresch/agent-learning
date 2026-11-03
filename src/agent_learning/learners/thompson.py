"""Beta-Bernoulli learner for :class:`ThompsonPolicy` (ADR-015 §4.4, FDD-015 §3 item 6).

Each counted reward moves the chosen action's posterior by the conjugate rule; a ceiling on
``alpha + beta`` keeps the posterior able to follow a change. Every episode is counted once: its id
is kept in the snapshot's ``consumed_episode_ids`` (D7).
"""

from __future__ import annotations

import math
from collections.abc import Iterable

from ..policy.base import Policy
from ..policy.thompson import N_MAX, SELECTION_BASIS, ThompsonPolicy
from ..types import ConsumedInput, Episode, Reward, RewardSource
from .base import Learner, LearnerResult


def reward_to_success(value: float) -> float:
    """Map a reward in [-1, 1] to the success probability ``r = (value + 1) / 2`` (D1)."""
    if not math.isfinite(value) or not -1.0 <= value <= 1.0:
        raise ValueError(f"reward value must be finite and within [-1, 1], got {value!r}")
    return (value + 1.0) / 2.0


class ThompsonLearner(Learner):
    """Conjugate Beta-Bernoulli update with a pseudo-count ceiling."""

    def update(
        self,
        policy: Policy,
        episodes: Iterable[Episode],
        rewards: Iterable[Reward],
    ) -> LearnerResult:
        if not isinstance(policy, ThompsonPolicy):
            raise TypeError("ThompsonLearner requires a ThompsonPolicy")

        # Newest aggregate reward per episode, as ReinforceLearner does; every one is validated.
        aggregate: dict[str, Reward] = {}
        for reward in rewards:
            if reward.source != RewardSource.AGGREGATE:
                continue
            reward_to_success(reward.value)
            current = aggregate.get(reward.episode_id)
            if current is None or reward.created_at > current.created_at:
                aggregate[reward.episode_id] = reward

        snapshot = policy.snapshot()
        posterior_before = policy.posterior()
        alpha = dict(posterior_before["alpha"])
        beta = dict(posterior_before["beta"])
        consumed = policy.consumed_episode_ids()
        seen = set(consumed)

        consumed_inputs: list[ConsumedInput] = []
        success_sum = 0.0
        for episode in episodes:
            if (
                episode.metadata.get("selection_basis") != SELECTION_BASIS
                or episode.action_id is None
                or episode.action_id not in alpha
                or episode.id in seen
            ):
                continue
            counted = aggregate.get(episode.id)
            if counted is None:
                continue
            r = reward_to_success(counted.value)
            alpha[episode.action_id] += r
            beta[episode.action_id] += 1.0 - r
            consumed.append(episode.id)
            seen.add(episode.id)
            success_sum += r
            consumed_inputs.append(ConsumedInput(episode_id=episode.id, reward_id=counted.id))

        if not consumed_inputs:
            return LearnerResult(
                episodes_used=0,
                mean_reward=0.0,
                baseline_before=snapshot.baseline,
                baseline_after=snapshot.baseline,
                logit_deltas={action.id: 0.0 for action in snapshot.actions},
                extra={"reason": "no actionable episodes"},
                consumed_inputs=[],
            )

        # The ceiling, once per call: both parameters keep their ratio while the total drops to N_MAX.
        for action_id, alpha_value in alpha.items():
            total = alpha_value + beta[action_id]
            if total > N_MAX:
                scale = N_MAX / total
                alpha[action_id] = alpha_value * scale
                beta[action_id] *= scale

        used = len(consumed_inputs)
        policy.update_posterior(alpha, beta, consumed, episodes_seen=snapshot.episodes_seen + used)
        return LearnerResult(
            episodes_used=used,
            mean_reward=success_sum / used,
            baseline_before=snapshot.baseline,
            baseline_after=snapshot.baseline,
            logit_deltas={action.id: 0.0 for action in snapshot.actions},
            extra={"posterior_before": posterior_before, "posterior_after": policy.posterior()},
            consumed_inputs=consumed_inputs,
        )


__all__ = ["ThompsonLearner", "reward_to_success"]
