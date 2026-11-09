# ext-source: src/agent_learning/learners/reinforce.py sha256:ec3bc489b4bcf75c9bc1aae543c787529b6b073c3167333206231ca4a51ae433
# ruff: noqa  (kept faithful to Microsoft's code and style so upstream changes merge in cleanly)
# Copy of Microsoft's module for agent_learning_ext (fork rule: Microsoft's file is never edited).
# EXT: ReinforceLearner.update() skips an episode whose action_logprob is None (Story 1.1, ADR-001 4.5) or whose routed_authority is 'full' (Story 21.6, ADR-021 4.3) and reports the count as extra['full_authority_excluded'].
# When the upstream pin moves and the source file changes, merge that change here and update the hash above.
"""REINFORCE-style policy gradient learner with an EMA value baseline.

The native learner consumes (episode, aggregate reward) pairs and
applies one batched gradient step per call. The gradient of a
softmax bandit's logit ``z_a`` w.r.t. the log-likelihood of action
``a`` is ``1_{action == a} - π(a)``, so the policy-gradient update
for one episode is:

    Δz_a = lr * (R - b) * (1_{action == a} - π(a))

We accumulate that delta over the batch, average by the batch size,
add a small entropy bonus to keep exploration alive, and update the
EMA baseline ``b`` afterwards. Importance sampling weights are
applied when the snapshot's policy version is older than the
in-memory policy version, to keep offline updates unbiased without
exploding gradients (the weight is clipped).
"""

from __future__ import annotations

import math
from typing import Dict, Iterable, List, Optional

from agent_learning.config import LearnerConfig
from agent_learning.policy.base import Policy
from agent_learning.policy.softmax_bandit import SoftmaxPolicy
from agent_learning.types import ConsumedInput, Episode, Reward, RewardSource
from agent_learning.learners.base import Learner, LearnerResult


class ReinforceLearner(Learner):
    """REINFORCE-with-baseline learner for :class:`SoftmaxPolicy`."""

    def __init__(self, config: Optional[LearnerConfig] = None) -> None:
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
        if not isinstance(policy, SoftmaxPolicy):
            raise TypeError("ReinforceLearner requires a SoftmaxPolicy")

        # Index rewards by episode id - we only consume aggregate rewards
        episode_list = list(episodes)
        aggregate_rewards: Dict[str, Reward] = {}
        for r in rewards:
            if r.source != RewardSource.AGGREGATE:
                continue
            if not math.isfinite(r.value) or not -1.0 <= r.value <= 1.0:
                raise ValueError("aggregate reward value must be finite and within [-1, 1]")
            # Rescoring may append a replacement aggregate. Keep the newest.
            current = aggregate_rewards.get(r.episode_id)
            if current is None or r.created_at > current.created_at:
                aggregate_rewards[r.episode_id] = r

        snapshot = policy.snapshot()
        baseline_before = snapshot.baseline
        probs_now = policy.probabilities()
        action_ids = [a.id for a in snapshot.actions]
        action_index = {aid: idx for idx, aid in enumerate(action_ids)}

        deltas: Dict[str, float] = {aid: 0.0 for aid in action_ids}
        consumed_inputs: list[ConsumedInput] = []
        used = 0
        reward_sum = 0.0
        entropy = -sum(p * math.log(max(p, 1e-12)) for p in probs_now)
        full_authority_excluded = 0

        for episode in episode_list:
            # Story 21.6 (AC_3): Full-routed decisions are reasoned, not sampled from policy.
            # They must be excluded from policy gradients even if they carry an action_logprob.
            meta = getattr(episode, "metadata", None) or {}
            routed_auth_raw = meta.get("routed_authority") if isinstance(meta, dict) else None
            if hasattr(routed_auth_raw, "value"):
                routed_auth = str(routed_auth_raw.value).strip().lower()
            elif routed_auth_raw is not None:
                routed_auth = str(routed_auth_raw).strip().lower()
            else:
                routed_auth = ""

            if routed_auth == "full":
                full_authority_excluded += 1
                continue

            if (
                episode.action_id is None
                or episode.action_id not in action_index
                or episode.action_logprob is None
            ):
                continue
            reward = aggregate_rewards.get(episode.id)
            if reward is None:
                continue
            reward_value = reward.value
            advantage = reward_value - baseline_before

            # Importance sampling weight when the episode was logged under a
            # behaviour policy that differs from the target policy.
            iw = self._importance_weight(episode, probs_now, action_index)
            advantage *= iw

            chosen_idx = action_index[episode.action_id]
            for idx, aid in enumerate(action_ids):
                indicator = 1.0 if idx == chosen_idx else 0.0
                grad = indicator - probs_now[idx]
                deltas[aid] += advantage * grad

            # Entropy regulariser pushes towards the maximum-entropy
            # distribution: its gradient w.r.t. logit i is -log p_i - H.
            for idx, aid in enumerate(action_ids):
                deltas[aid] += self._config.entropy_bonus * (-math.log(max(probs_now[idx], 1e-12)) - entropy)

            used += 1
            reward_sum += reward_value
            consumed_inputs.append(ConsumedInput(episode_id=episode.id, reward_id=reward.id))

        if used == 0:
            return LearnerResult(
                episodes_used=0,
                mean_reward=0.0,
                baseline_before=baseline_before,
                baseline_after=baseline_before,
                logit_deltas={aid: 0.0 for aid in action_ids},
                extra={
                    "reason": "no actionable episodes",
                    "full_authority_excluded": full_authority_excluded,
                },
                consumed_inputs=consumed_inputs,
            )

        # Average gradients across the batch and scale by learning rate
        for aid in deltas:
            deltas[aid] = self._config.learning_rate * deltas[aid] / used

        # Update EMA baseline using the mean batch reward
        mean_reward = reward_sum / used
        decay = self._config.baseline_decay
        baseline_after = decay * baseline_before + (1.0 - decay) * mean_reward

        policy.apply_update(
            deltas,
            baseline=baseline_after,
            episodes_seen=snapshot.episodes_seen + used,
        )

        return LearnerResult(
            episodes_used=used,
            mean_reward=mean_reward,
            baseline_before=baseline_before,
            baseline_after=baseline_after,
            logit_deltas=deltas,
            extra={
                "entropy": entropy,
                "full_authority_excluded": full_authority_excluded,
            },
            consumed_inputs=consumed_inputs,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _importance_weight(
        self,
        episode: Episode,
        probs_now: List[float],
        action_index: Dict[str, int],
    ) -> float:
        """Return clipped π_target / π_behaviour for an episode."""
        if episode.action_logprob is None or episode.action_id is None:
            return 1.0
        idx = action_index[episode.action_id]
        p_target = max(probs_now[idx], 1e-12)
        p_behaviour = max(math.exp(episode.action_logprob), 1e-12)
        ratio = p_target / p_behaviour
        return min(ratio, self._config.importance_clip)


__all__ = ["ReinforceLearner"]
