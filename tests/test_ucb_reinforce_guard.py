"""Story 16.5 — Staying Out of REINFORCE (ADR-016, FDD-016 §3 item 7, E2).

Acceptance Criteria:
  AC_0 (Skipped): a UCB episode made through choose and the capture path has action_logprob of None;
       ReinforceLearner.update over only such episodes returns episodes_used of 0 and leaves logits unchanged.
  AC_1 (Mixed Set): over 3 softmax episodes and 3 UCB episodes with rewards, ReinforceLearner uses exactly
       the 3 softmax episodes, and logits equal those from 3 softmax episodes alone within 1e-12.
  AC_2 (Guard Is Existing Behaviour): the skip of AC_0 and AC_1 is provided by existing check on
       action_logprob is None in ReinforceLearner; this epic adds no condition to learners/reinforce.py.

Contract Interpretations (derived via scripts/spec_gate.py):
  I1 (Upstream Fork Purity): Implemented under src/agent_learning_ext/ leaving upstream pristine.
  I2 (Storage Decoupling & Serialization): No storage coupling in UCB modules.
  I3 (Empty Collection Base Case): Empty episodes return clean unmutated state with episodes_used=0.
  I4 (Non-Finite Float Rejection): Handled by existing numeric contracts.
"""

from __future__ import annotations

import random
from typing import Any

import pytest

from agent_learning.config import CaptureConfig
from agent_learning.policy import SoftmaxPolicy
from agent_learning.storage import InMemoryStore
from agent_learning.types import Action, Episode, PolicySnapshot, Reward, RewardSource
from agent_learning_ext.capture import EpisodeCapture
from agent_learning_ext.learners.reinforce import ReinforceLearner
from agent_learning_ext.policy.ucb import SELECTION_BASIS, UCBPolicy

ACTIONS = [Action(id="a", description="Action A"), Action(id="b", description="Action B"), Action(id="c", description="Action C")]
TS = "2026-10-29T08:00:00+00:00"


def _capture() -> EpisodeCapture:
    config = CaptureConfig(enabled=True, agent_id="agent", task_id="task")
    return EpisodeCapture(config, InMemoryStore())


def _captured(capture: EpisodeCapture, policy: Any, decision: Any, extra: dict[str, Any] | None = None) -> Episode:
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
        ctx,
        "Synthetic response",
        execution_status="completed",
        result_summary="Synthetic response",
    )
    assert episode is not None
    return episode


def _ucb_episodes(capture: EpisodeCapture, count: int) -> list[Episode]:
    policy = UCBPolicy.from_actions(ACTIONS, agent_id="agent", task_id="task")
    episodes: list[Episode] = []
    for _ in range(count):
        decision = policy.choose()
        record = policy.last_decision_record()
        episodes.append(
            _captured(capture, policy, decision, {"selection_basis": SELECTION_BASIS, "ucb": record})
        )
    return episodes


def _softmax_policy() -> SoftmaxPolicy:
    return SoftmaxPolicy.from_actions(ACTIONS, agent_id="agent", task_id="task", rng=random.Random(11))


def _softmax_episodes(capture: EpisodeCapture, policy: SoftmaxPolicy, count: int) -> list[Episode]:
    return [_captured(capture, policy, policy.choose()) for _ in range(count)]


def _reward(episode: Episode, value: float) -> Reward:
    return Reward(
        id=f"rew-{episode.id}",
        episode_id=episode.id,
        agent_id="agent",
        source=RewardSource.AGGREGATE,
        value=value,
        created_at="2026-10-29T09:00:00+00:00",
    )


def _copy_of(policy: SoftmaxPolicy) -> SoftmaxPolicy:
    return SoftmaxPolicy.from_snapshot(PolicySnapshot.from_dict(policy.snapshot().to_dict()))


# -----------------------------------------------------------------------------
# AC_0 (Skipped)
# -----------------------------------------------------------------------------


def test_ac0_a_captured_ucb_episode_has_no_log_probability() -> None:
    """AC_0: captured UCB episodes have action_logprob=None and selection_basis='ucb'."""
    episodes = _ucb_episodes(_capture(), 3)
    assert all(episode.action_logprob is None for episode in episodes)
    assert all(episode.metadata["selection_basis"] == SELECTION_BASIS for episode in episodes)
    assert all(episode.action_id in {"a", "b", "c"} for episode in episodes)


def test_ac0_reinforce_skips_a_set_of_only_ucb_episodes() -> None:
    """AC_0: ReinforceLearner.update over only UCB episodes returns episodes_used=0 and leaves logits unchanged."""
    episodes = _ucb_episodes(_capture(), 4)
    policy = _softmax_policy()
    before = policy.snapshot()

    result = ReinforceLearner().update(policy, episodes, [_reward(e, 1.0) for e in episodes])

    assert result.episodes_used == 0
    assert result.consumed_inputs == []
    after = policy.snapshot()
    assert after.logits == before.logits
    assert after.version == before.version
    assert after.episodes_seen == before.episodes_seen


# -----------------------------------------------------------------------------
# AC_1 (Mixed Set)
# -----------------------------------------------------------------------------


def test_ac1_reinforce_uses_exactly_the_softmax_episodes_of_a_mixed_set() -> None:
    """AC_1: ReinforceLearner uses exactly 3 softmax episodes and matches logits within 1e-12."""
    capture = _capture()
    mixed_policy = _softmax_policy()
    softmax = _softmax_episodes(capture, mixed_policy, 3)
    ucb = _ucb_episodes(capture, 3)
    alone_policy = _copy_of(mixed_policy)

    softmax_values = [0.8, -0.3, 0.5]
    ucb_values = [1.0, -1.0, 0.2]
    softmax_rewards = [_reward(e, v) for e, v in zip(softmax, softmax_values)]
    ucb_rewards = [_reward(e, v) for e, v in zip(ucb, ucb_values)]
    interleaved = [softmax[0], ucb[0], softmax[1], ucb[1], ucb[2], softmax[2]]

    mixed = ReinforceLearner().update(mixed_policy, interleaved, softmax_rewards + ucb_rewards)
    alone = ReinforceLearner().update(alone_policy, softmax, softmax_rewards)

    assert mixed.episodes_used == 3
    assert alone.episodes_used == 3
    assert {c.episode_id for c in (mixed.consumed_inputs or [])} == {e.id for e in softmax}

    mixed_logits = mixed_policy.snapshot().logits
    alone_logits = alone_policy.snapshot().logits
    assert alone_logits != {a.id: 0.0 for a in ACTIONS}, "the softmax episodes must move the logits"
    for action_id in mixed_logits:
        assert mixed_logits[action_id] == pytest.approx(alone_logits[action_id], abs=1e-12)
    assert mixed.baseline_after == pytest.approx(alone.baseline_after, abs=1e-12)
    assert mixed.mean_reward == pytest.approx(alone.mean_reward, abs=1e-12)
