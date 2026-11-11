"""Tests for Methodology #21: Category-Level Escalation Learning (ADR-007 / HYP-AL-007)."""

from __future__ import annotations

import random
from agent_learning.config import LearnerConfig
from agent_learning.learners import ReinforceLearner
from agent_learning.policy import SoftmaxPolicy
from agent_learning.types import Episode, Reward, RewardSource
from examples.category_escalation_demo import (
    ACT_SILENTLY,
    CATEGORIES,
    ESCALATE_TO_EXECUTIVE,
    ESCALATE_TO_MANAGER,
    NOTIFY,
    build_initial_policy,
    simulate_environment_reward,
)


def test_initial_policy_has_uniform_distribution():
    cat = CATEGORIES[0]
    snapshot = build_initial_policy(cat.id)
    policy = SoftmaxPolicy(snapshot)

    probs = policy.probabilities()
    assert len(probs) == 4
    # All 4 actions must have equal 25% probability
    assert all(abs(p - 0.25) < 1e-4 for p in probs)


def test_category_escalation_learns_manager_for_schema_changes():
    cat = next(c for c in CATEGORIES if c.id == "cat_schema_business_logic")
    snapshot = build_initial_policy(cat.id)
    policy = SoftmaxPolicy(snapshot)
    learner = ReinforceLearner(LearnerConfig(learning_rate=0.45, entropy_bonus=0.01))
    actions = policy.actions()
    rng = random.Random(42)

    for _ in range(8):
        episodes: list[Episode] = []
        rewards: list[Reward] = []
        for e_idx in range(20):
            probs = policy.probabilities()
            chosen_idx = rng.choices(range(len(actions)), weights=probs)[0]
            action = actions[chosen_idx]
            r_val = simulate_environment_reward(cat, action.id, rng)

            ep_id = f"test-{e_idx}"
            episodes.append(
                Episode(
                    id=ep_id,
                    agent_id=policy.snapshot().agent_id,
                    task_id=policy.snapshot().task_id,
                    intent_summary="Test schema escalation",
                    action_id=action.id,
                    expected_outcome="Test",
                    execution_status="completed",
                    result_summary="Test",
                    created_at="2026-11-11T00:00:00+00:00",
                )
            )
            rewards.append(
                Reward(
                    id=f"rw-{ep_id}",
                    episode_id=ep_id,
                    source=RewardSource.AGGREGATE,
                    value=r_val,
                    created_at="2026-11-11T00:00:00+00:00",
                )
            )
        learner.update(policy, episodes, rewards)

    final_probs = {a.id: p for a, p in zip(actions, policy.probabilities())}
    # escalate_to_manager must be the top learned tier
    assert max(final_probs, key=final_probs.get) == ESCALATE_TO_MANAGER
    # act_silently must be heavily penalized
    assert final_probs[ACT_SILENTLY] < 0.15


def test_category_escalation_learns_executive_for_security_keys():
    cat = next(c for c in CATEGORIES if c.id == "cat_security_sovereignty")
    snapshot = build_initial_policy(cat.id)
    policy = SoftmaxPolicy(snapshot)
    learner = ReinforceLearner(LearnerConfig(learning_rate=0.45, entropy_bonus=0.01))
    actions = policy.actions()
    rng = random.Random(42)

    for _ in range(8):
        episodes: list[Episode] = []
        rewards: list[Reward] = []
        for e_idx in range(20):
            probs = policy.probabilities()
            chosen_idx = rng.choices(range(len(actions)), weights=probs)[0]
            action = actions[chosen_idx]
            r_val = simulate_environment_reward(cat, action.id, rng)

            ep_id = f"test-sec-{e_idx}"
            episodes.append(
                Episode(
                    id=ep_id,
                    agent_id=policy.snapshot().agent_id,
                    task_id=policy.snapshot().task_id,
                    intent_summary="Test security escalation",
                    action_id=action.id,
                    expected_outcome="Test",
                    execution_status="completed",
                    result_summary="Test",
                    created_at="2026-11-11T00:00:00+00:00",
                )
            )
            rewards.append(
                Reward(
                    id=f"rw-{ep_id}",
                    episode_id=ep_id,
                    source=RewardSource.AGGREGATE,
                    value=r_val,
                    created_at="2026-11-11T00:00:00+00:00",
                )
            )
        learner.update(policy, episodes, rewards)

    final_probs = {a.id: p for a, p in zip(actions, policy.probabilities())}
    assert max(final_probs, key=final_probs.get) == ESCALATE_TO_EXECUTIVE

