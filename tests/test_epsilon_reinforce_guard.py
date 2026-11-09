"""Story 17.5 — Staying Out of REINFORCE (ADR-017, BRD-017, FDD-017).

Acceptance Criteria:
  AC_0 (Skipped): An episode made through choose and the capture path has action_logprob
       of None; ReinforceLearner.update over only such episodes returns episodes_used
       of 0 and leaves the logits unchanged.
  AC_1 (Mixed Set): Over 3 softmax episodes and 3 epsilon-greedy episodes with rewards,
       ReinforceLearner uses exactly the 3 softmax episodes, and the logits equal those
       from the 3 softmax episodes alone within 1e-12.
  AC_2 (Guard Is Existing Behaviour): The skip of AC_0 and AC_1 is provided by the
       existing check on action_logprob is None in ReinforceLearner; this epic adds no
       condition to learners/reinforce.py. The test asserts behaviour only and does not
       compare the module's source, so a later epic may add a condition to that file
       without breaking it.

Contract Interpretations (derived via scripts/spec_gate.py):
  I1 (Upstream Fork Purity): Zero changes in src/agent_learning/. All logic isolated under
      src/agent_learning_ext/.
  I2 (Storage Decoupling & Serialization): Policy snapshots and episode records survive
      JSON serialization without storage dependencies.
  I3 (Empty Collection Base Case): When passed an empty collection or when all episodes are
      excluded, ReinforceLearner returns episodes_used=0 and leaves logits unmutated.
  I4 (Non-Finite Float Rejection): Aggregate rewards must be finite and within [-1, 1],
      strictly raising ValueError on NaN or Inf.
"""

from __future__ import annotations

import copy
import math
import random
import uuid
from typing import Any

import pytest

from agent_learning.config import CaptureConfig
from agent_learning.policy.softmax_bandit import SoftmaxPolicy
from agent_learning.types import Action, Episode, PolicySnapshot, Reward, RewardSource
from agent_learning_ext.capture import EpisodeCapture
from agent_learning_ext.learners.reinforce import ReinforceLearner
from agent_learning_ext.policy.epsilon_greedy import (
    SELECTION_BASIS,
    EpsilonGreedyPolicy,
)

ACTIONS = [
    Action(id="a", description="Action A", parameters={"reversible": True}),
    Action(id="b", description="Action B", parameters={"reversible": True}),
    Action(id="c", description="Action C"),
]


def _make_epsilon_policy() -> EpsilonGreedyPolicy:
    """Create a standard base EpsilonGreedyPolicy for testing."""
    return EpsilonGreedyPolicy.from_actions(
        actions=ACTIONS,
        eps0=0.5,
        delta=0.05,
        floor=0.05,
    )


def _make_softmax_policy(
    initial_logits: dict[str, float] | None = None,
    baseline: float = 0.0,
) -> SoftmaxPolicy:
    """Create a SoftmaxPolicy with known actions and initial logits."""
    snap = PolicySnapshot(
        agent_id="test-agent",
        task_id="test-task",
        actions=list(ACTIONS),
        logits=dict(initial_logits or {a.id: 0.0 for a in ACTIONS}),
        baseline=baseline,
        metadata={},
    )
    return SoftmaxPolicy(snap)


def test_ac0_epsilon_episodes_skipped_by_reinforce_learner() -> None:
    """AC_0: Episode via choose and capture path has action_logprob=None; ReinforceLearner skips them."""
    eps_policy = _make_epsilon_policy()
    config = CaptureConfig(enabled=True, agent_id="test-agent", task_id="test-task")
    capture = EpisodeCapture(config=config)

    episodes: list[Episode] = []
    rewards: list[Reward] = []

    for i in range(3):
        req_id = f"req-ac0-{i}"
        dec = eps_policy.choose(request_id=req_id)

        # Verify that EpsilonGreedyPolicy decision logprob is strictly None
        assert dec.logprob is None

        # Build episode via capture start/end simulating orchestrator path
        ctx = capture.start(
            user_input=f"query {i}",
            action_id=dec.action.id,
            action_logprob=dec.logprob,
            metadata={"selection_basis": SELECTION_BASIS},
        )
        ep = capture.end(ctx, assistant_output=f"result {i}")

        assert ep.action_logprob is None
        assert ep.action_id == dec.action.id
        episodes.append(ep)

        rewards.append(
            Reward(
                id=str(uuid.uuid4()),
                episode_id=ep.id,
                value=0.5,
                source=RewardSource.AGGREGATE,
                created_at="2026-11-08T12:00:00Z",
            )
        )

    softmax_policy = _make_softmax_policy()
    initial_logits = copy.deepcopy(softmax_policy.snapshot().logits)
    initial_version = softmax_policy.snapshot().version

    learner = ReinforceLearner()
    result = learner.update(softmax_policy, episodes, rewards)

    # Assert ReinforceLearner used 0 episodes and excluded all 3
    assert result.episodes_used == 0
    assert result.extra.get("full_authority_excluded") == 3
    assert softmax_policy.snapshot().logits == initial_logits
    assert softmax_policy.snapshot().version == initial_version


def test_ac1_mixed_set_uses_only_softmax_episodes_with_identical_logits() -> None:
    """AC_1: Over 3 softmax + 3 epsilon episodes, ReinforceLearner uses exactly 3 softmax episodes."""
    eps_policy = _make_epsilon_policy()
    initial_logits = {"a": 0.2, "b": -0.1, "c": 0.5}

    softmax_solo = _make_softmax_policy(initial_logits=initial_logits, baseline=0.1)
    softmax_mixed = _make_softmax_policy(initial_logits=initial_logits, baseline=0.1)

    # 1. Generate 3 softmax episodes (with action_logprob)
    softmax_episodes: list[Episode] = []
    softmax_rewards: list[Reward] = []
    reward_values = [0.8, -0.4, 0.6]

    for i in range(3):
        dec = softmax_solo.choose()
        assert dec.logprob is not None
        ep_id = f"ep-sm-{i}"
        ep = Episode(
            id=ep_id,
            agent_id="test-agent",
            task_id="test-task",
            action_id=dec.action.id,
            action_logprob=dec.logprob,
            policy_version=softmax_solo.snapshot().version,
            intent_summary="Softmax intent",
        )
        softmax_episodes.append(ep)
        softmax_rewards.append(
            Reward(
                id=str(uuid.uuid4()),
                episode_id=ep_id,
                value=reward_values[i],
                source=RewardSource.AGGREGATE,
                created_at=f"2026-11-08T12:0{i}:00Z",
            )
        )

    # 2. Generate 3 epsilon-greedy episodes (with action_logprob=None)
    eps_episodes: list[Episode] = []
    eps_rewards: list[Reward] = []
    for i in range(3):
        dec = eps_policy.choose(request_id=f"req-mixed-eps-{i}")
        assert dec.logprob is None
        ep_id = f"ep-eps-{i}"
        ep = Episode(
            id=ep_id,
            agent_id="test-agent",
            task_id="test-task",
            action_id=dec.action.id,
            action_logprob=dec.logprob,
            metadata={"selection_basis": SELECTION_BASIS},
            intent_summary="Epsilon intent",
        )
        eps_episodes.append(ep)
        eps_rewards.append(
            Reward(
                id=str(uuid.uuid4()),
                episode_id=ep_id,
                value=1.0,  # Even high reward must be ignored because logprob is None
                source=RewardSource.AGGREGATE,
                created_at=f"2026-11-08T12:1{i}:00Z",
            )
        )

    learner = ReinforceLearner()

    # Train on softmax episodes alone
    solo_result = learner.update(softmax_solo, softmax_episodes, softmax_rewards)
    assert solo_result.episodes_used == 3
    assert solo_result.extra.get("full_authority_excluded", 0) == 0

    # Train on mixed set (interleaved or concatenated)
    mixed_episodes = [
        softmax_episodes[0],
        eps_episodes[0],
        softmax_episodes[1],
        eps_episodes[1],
        softmax_episodes[2],
        eps_episodes[2],
    ]
    mixed_rewards = softmax_rewards + eps_rewards

    mixed_result = learner.update(softmax_mixed, mixed_episodes, mixed_rewards)
    assert mixed_result.episodes_used == 3
    assert mixed_result.extra.get("full_authority_excluded") == 3

    # Assert logits match within 1e-12
    solo_logits = softmax_solo.snapshot().logits
    mixed_logits = softmax_mixed.snapshot().logits

    for a in ACTIONS:
        assert math.isclose(
            solo_logits[a.id],
            mixed_logits[a.id],
            abs_tol=1e-12,
        ), f"Logit mismatch for action {a.id}: solo={solo_logits[a.id]}, mixed={mixed_logits[a.id]}"

    # Assert baseline updates match within 1e-12
    assert math.isclose(
        softmax_solo.snapshot().baseline,
        softmax_mixed.snapshot().baseline,
        abs_tol=1e-12,
    )


def test_ac2_guard_is_existing_behaviour_and_spec_interpretations() -> None:
    """AC_2: Behavioral verification that existing guard in ReinforceLearner handles skipping cleanly."""
    policy = _make_softmax_policy()
    learner = ReinforceLearner()

    # I3: Empty collection base case
    empty_result = learner.update(policy, [], [])
    assert empty_result.episodes_used == 0
    assert empty_result.extra.get("full_authority_excluded", 0) == 0

    # I4: Non-finite float rejection
    nan_reward = Reward(
        id="rw-nan",
        episode_id="ep-nan",
        value=float("nan"),
        source=RewardSource.AGGREGATE,
    )
    with pytest.raises(ValueError, match=r"finite and within"):
        learner.update(policy, [], [nan_reward])

    inf_reward = Reward(
        id="rw-inf",
        episode_id="ep-inf",
        value=float("inf"),
        source=RewardSource.AGGREGATE,
    )
    with pytest.raises(ValueError, match=r"finite and within"):
        learner.update(policy, [], [inf_reward])

    out_of_bounds_reward = Reward(
        id="rw-oob",
        episode_id="ep-oob",
        value=1.5,
        source=RewardSource.AGGREGATE,
    )
    with pytest.raises(ValueError, match=r"finite and within"):
        learner.update(policy, [], [out_of_bounds_reward])
