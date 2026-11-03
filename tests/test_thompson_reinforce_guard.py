"""Contract tests for Epic 15, Story 15.5 (Staying Out of REINFORCE).

Story: docs/user-stories/epic-15-bayesian-bandit-posterior-sampling.md, Story 15.5.
ADR-015 §4.4; BRD-015 BRU-015-08; FDD-015 §3 item 7 and D3, D6.

This story adds no production code. ``ReinforceLearner`` already skips an episode whose
``action_logprob`` is ``None``, and a Thompson ``Decision.logprob`` of ``None`` reaches
``Episode.action_logprob`` through the capture path (FDD-015 D3, D6). These tests pin that
behaviour so a later change to either side cannot silently let a draw be trained on as a
softmax sample.

Interpretation I1: AC_2 asks for behaviour only. These tests never read ``learners/reinforce.py``
and never assert on how the skip is counted (``full_authority_excluded`` is a name FDD-015 §7 item 3
leaves open), so a later epic may add a condition to that module or rename the counter.

Interpretation I2: "the capture path" is ``EpisodeCapture.start`` / ``end`` with
``action_logprob=decision.logprob``, as the package docstring and ``decision.py`` do it.

Interpretation I3: the RED for this story was observed by temporarily removing the
``action_logprob is None`` check from ``ReinforceLearner`` (restored before the commit); the
tests then fail because the Thompson episodes are trained on.
"""

from __future__ import annotations

import random

import pytest

from agent_learning.capture import EpisodeCapture
from agent_learning.config import CaptureConfig
from agent_learning.learners.reinforce import ReinforceLearner
from agent_learning.policy import SoftmaxPolicy
from agent_learning.policy.thompson import SELECTION_BASIS, ThompsonPolicy
from agent_learning.storage import InMemoryStore
from agent_learning.types import Action, Episode, PolicySnapshot, Reward, RewardSource

ACTIONS = [Action(id="a"), Action(id="b"), Action(id="c")]
TS = "2026-10-29T08:00:00+00:00"


def _capture() -> EpisodeCapture:
    config = CaptureConfig(enabled=True, agent_id="agent", task_id="task")
    return EpisodeCapture(config, InMemoryStore())


def _captured(capture: EpisodeCapture, policy, decision, extra: dict | None = None) -> Episode:
    snapshot = policy.snapshot()
    ctx = capture.start(
        "Route a synthetic request",
        task_id="task",
        intent_summary="Route a synthetic request",
        expected_outcome="Find a handler",
        policy_id=snapshot.id,
        policy_version=snapshot.version,
        action_id=decision.action.id,
        action_logprob=decision.logprob,
        metadata=extra,
    )
    episode = capture.end(
        ctx, "Synthetic response", execution_status="completed", result_summary="Synthetic response"
    )
    assert episode is not None
    return episode


def _thompson_episodes(capture: EpisodeCapture, count: int) -> list[Episode]:
    policy = ThompsonPolicy.from_actions(ACTIONS, agent_id="agent", task_id="task")
    episodes = []
    for i in range(count):
        decision = policy.choose(request_id=f"req-{i}", timestamp=TS)
        record = policy.last_sampling_record()
        episodes.append(
            _captured(capture, policy, decision, {"selection_basis": SELECTION_BASIS, "thompson_sampling": record})
        )
    return episodes


def _softmax_policy() -> SoftmaxPolicy:
    return SoftmaxPolicy.from_actions(ACTIONS, agent_id="agent", task_id="task", rng=random.Random(11))


def _softmax_episodes(capture: EpisodeCapture, policy: SoftmaxPolicy, count: int) -> list[Episode]:
    return [_captured(capture, policy, policy.choose()) for _ in range(count)]


def _reward(episode: Episode, value: float) -> Reward:
    return Reward(
        id=f"reward-{episode.id}",
        episode_id=episode.id,
        agent_id="agent",
        source=RewardSource.AGGREGATE,
        value=value,
        created_at="2026-10-29T09:00:00+00:00",
    )


def _copy_of(policy: SoftmaxPolicy) -> SoftmaxPolicy:
    return SoftmaxPolicy.from_snapshot(PolicySnapshot.from_dict(policy.snapshot().to_dict()))


def test_ac0_a_captured_thompson_episode_has_no_log_probability() -> None:
    episodes = _thompson_episodes(_capture(), 3)
    assert all(episode.action_logprob is None for episode in episodes)
    assert all(episode.metadata["selection_basis"] == SELECTION_BASIS for episode in episodes)
    assert all(episode.action_id in {"a", "b", "c"} for episode in episodes)


def test_ac0_reinforce_skips_a_set_of_only_thompson_episodes() -> None:
    episodes = _thompson_episodes(_capture(), 4)
    policy = _softmax_policy()
    before = policy.snapshot()

    result = ReinforceLearner().update(policy, episodes, [_reward(e, 1.0) for e in episodes])

    assert result.episodes_used == 0
    assert result.consumed_inputs == []
    after = policy.snapshot()
    assert after.logits == before.logits
    assert after.version == before.version
    assert after.episodes_seen == before.episodes_seen


def test_ac1_reinforce_uses_exactly_the_softmax_episodes_of_a_mixed_set() -> None:
    capture = _capture()
    mixed_policy = _softmax_policy()
    softmax = _softmax_episodes(capture, mixed_policy, 3)
    thompson = _thompson_episodes(capture, 3)
    alone_policy = _copy_of(mixed_policy)

    softmax_values = [0.8, -0.3, 0.5]
    thompson_values = [1.0, -1.0, 0.2]
    softmax_rewards = [_reward(e, v) for e, v in zip(softmax, softmax_values)]
    thompson_rewards = [_reward(e, v) for e, v in zip(thompson, thompson_values)]
    interleaved = [softmax[0], thompson[0], softmax[1], thompson[1], thompson[2], softmax[2]]

    mixed = ReinforceLearner().update(mixed_policy, interleaved, softmax_rewards + thompson_rewards)
    alone = ReinforceLearner().update(alone_policy, softmax, softmax_rewards)

    assert mixed.episodes_used == 3
    assert alone.episodes_used == 3
    assert {c.episode_id for c in mixed.consumed_inputs} == {e.id for e in softmax}
    mixed_logits = mixed_policy.snapshot().logits
    alone_logits = alone_policy.snapshot().logits
    assert alone_logits != {a.id: 0.0 for a in ACTIONS}, "the softmax episodes must move the logits"
    for action_id in mixed_logits:
        assert mixed_logits[action_id] == pytest.approx(alone_logits[action_id], abs=1e-12)
    assert mixed.baseline_after == pytest.approx(alone.baseline_after, abs=1e-12)
    assert mixed.mean_reward == pytest.approx(alone.mean_reward, abs=1e-12)


def test_ac2_the_guard_is_behaviour_not_source() -> None:
    """AC_2: nothing here reads ``learners/reinforce.py``; the two tests above are the evidence."""
    import agent_learning.learners.reinforce as reinforce

    assert reinforce.ReinforceLearner is ReinforceLearner
