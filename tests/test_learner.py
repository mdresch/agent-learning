"""Tests for the REINFORCE learner.

We assert two important properties:

1. A consistently positive reward for one action shifts its
   logit upwards (and the other action's logit down).
2. Episodes without an aggregate reward or an unknown action are
   skipped without errors.
"""

from __future__ import annotations

import random

import pytest

from agent_learning.config import LearnerConfig
from agent_learning.learners import ReinforceLearner
from agent_learning.policy import SoftmaxPolicy
from agent_learning.types import Action, ConsumedInput, Episode, Reward, RewardSource


def _make_episode(agent_id: str, action_id: str, logprob: float = -0.693147) -> Episode:
    return Episode(agent_id=agent_id, user_input="x", assistant_output="y", action_id=action_id, action_logprob=logprob)


def test_positive_reward_shifts_logit_up() -> None:
    actions = [Action(id="a"), Action(id="b")]
    policy = SoftmaxPolicy.from_actions(actions, agent_id="nba", rng=random.Random(0))
    learner = ReinforceLearner(LearnerConfig(learning_rate=0.5, entropy_bonus=0.0))

    episodes = []
    rewards = []
    for _ in range(20):
        ep = _make_episode("nba", "a")
        episodes.append(ep)
        rewards.append(
            Reward(
                episode_id=ep.id,
                agent_id="nba",
                source=RewardSource.AGGREGATE,
                value=0.8,
            )
        )

    before = policy.snapshot()
    result = learner.update(policy, episodes, rewards)
    after = policy.snapshot()

    assert result.episodes_used == 20
    assert result.consumed_inputs == [
        ConsumedInput(ep.id, reward.id) for ep, reward in zip(episodes, rewards)
    ]
    assert after.logits["a"] > before.logits["a"]
    assert after.logits["b"] < before.logits["b"]
    assert after.version == before.version + 1
    assert after.episodes_seen == 20
    # Mean reward should be exactly 0.8 because every aggregate is identical.
    assert abs(result.mean_reward - 0.8) < 1e-9


def test_no_aggregate_reward_yields_noop() -> None:
    actions = [Action(id="a"), Action(id="b")]
    policy = SoftmaxPolicy.from_actions(actions, agent_id="nba")
    learner = ReinforceLearner(LearnerConfig())

    # Pass non-aggregate rewards only - learner must skip them.
    ep = _make_episode("nba", "a")
    rewards = [
        Reward(
            episode_id=ep.id,
            agent_id="nba",
            source=RewardSource.METRIC,
            value=0.9,
        )
    ]
    result = learner.update(policy, [ep], rewards)
    assert result.episodes_used == 0
    assert result.consumed_inputs == []


def test_unknown_action_is_skipped() -> None:
    actions = [Action(id="a")]
    policy = SoftmaxPolicy.from_actions(actions, agent_id="nba")
    learner = ReinforceLearner(LearnerConfig())

    ep = _make_episode("nba", "missing")
    rewards = [
        Reward(
            episode_id=ep.id,
            agent_id="nba",
            source=RewardSource.AGGREGATE,
            value=1.0,
        )
    ]
    result = learner.update(policy, [ep], rewards)
    assert result.episodes_used == 0
    assert result.consumed_inputs == []


def test_most_recent_aggregate_reward_wins() -> None:
    policy = SoftmaxPolicy.from_actions([Action(id="a"), Action(id="b")])
    learner = ReinforceLearner(LearnerConfig(learning_rate=0.5, entropy_bonus=0.0))
    episode = _make_episode("default", "a")
    rewards = [
        Reward(
            episode_id=episode.id,
            agent_id=episode.agent_id,
            source=RewardSource.AGGREGATE,
            value=0.0,
            created_at="2026-08-09T00:00:00+00:00",
        ),
        Reward(
            episode_id=episode.id,
            agent_id=episode.agent_id,
            source=RewardSource.AGGREGATE,
            value=0.8,
            created_at="2026-08-09T00:00:01+00:00",
        ),
    ]

    result = learner.update(policy, [episode], rewards)

    assert result.mean_reward == 0.8
    assert result.consumed_inputs == [ConsumedInput(episode.id, rewards[1].id)]
    assert policy.snapshot().logits["a"] > 0.0


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf"), 1.01, -1.01])
def test_invalid_aggregate_reward_is_rejected_without_policy_update(value: float) -> None:
    policy = SoftmaxPolicy.from_actions([Action(id="a"), Action(id="b")])
    learner = ReinforceLearner(LearnerConfig(learning_rate=0.5, entropy_bonus=0.0))
    episode = _make_episode("default", "a")
    reward = Reward(
        episode_id=episode.id,
        agent_id=episode.agent_id,
        source=RewardSource.AGGREGATE,
        value=value,
    )
    before = policy.snapshot()

    with pytest.raises(ValueError, match=r"finite and within \[-1, 1\]"):
        learner.update(policy, [episode], [reward])

    assert policy.snapshot() == before


def test_receipt_preserves_consumption_order_and_repeated_inputs() -> None:
    policy = SoftmaxPolicy.from_actions([Action(id="a"), Action(id="b")])
    first = Episode(id="first", action_id="a", action_logprob=-0.693147)
    second = Episode(id="second", action_id="b", action_logprob=-0.693147)
    unknown = Episode(id="unknown", action_id="outside", action_logprob=-0.693147)
    missing_action = Episode(id="missing-action", action_logprob=-0.693147)
    unrewarded = Episode(id="unrewarded", action_id="a", action_logprob=-0.693147)
    rewards = [
        Reward(id=f"reward-{ep.id}", episode_id=ep.id, source=RewardSource.AGGREGATE, value=0.5)
        for ep in (first, second, unknown, missing_action)
    ]

    result = ReinforceLearner().update(
        policy,
        iter([second, unknown, missing_action, unrewarded, first, second]),
        iter(rewards),
    )

    assert result.episodes_used == 3
    assert result.consumed_inputs == [
        ConsumedInput("second", "reward-second"),
        ConsumedInput("first", "reward-first"),
        ConsumedInput("second", "reward-second"),
    ]


@pytest.mark.parametrize("reverse", [False, True])
def test_equal_reward_timestamps_record_first_encountered_reward(reverse: bool) -> None:
    policy = SoftmaxPolicy.from_actions([Action(id="a"), Action(id="b")])
    episode = Episode(id="episode", action_id="a", action_logprob=-0.693147)
    rewards = [
        Reward(
            id="positive", episode_id=episode.id, source=RewardSource.AGGREGATE,
            value=0.8, created_at="2026-09-15T00:00:00+00:00",
        ),
        Reward(
            id="negative", episode_id=episode.id, source=RewardSource.AGGREGATE,
            value=-0.8, created_at="2026-09-15T00:00:00+00:00",
        ),
    ]
    if reverse:
        rewards.reverse()

    result = ReinforceLearner().update(policy, [episode], rewards)

    assert result.mean_reward == rewards[0].value
    assert result.consumed_inputs == [ConsumedInput(episode.id, rewards[0].id)]


def test_empty_batch_has_empty_receipt_and_leaves_snapshot_unchanged() -> None:
    policy = SoftmaxPolicy.from_actions([Action(id="a"), Action(id="b")])
    before = policy.snapshot()

    result = ReinforceLearner().update(policy, [], [])

    assert result.consumed_inputs == []
    assert result.episodes_used == 0
    assert policy.snapshot() == before


# ── Story 1.1: AC_0, AC_1, AC_2 Contract Tests ───────────────────────────────

def test_ac_0_full_authority_episode_excluded_from_update() -> None:
    """Story 1.1 AC0: Full-authority episodes (action_logprob is None) are excluded from gradient updates."""
    actions = [Action(id="a"), Action(id="b")]
    policy = SoftmaxPolicy.from_actions(actions, agent_id="gov")
    learner = ReinforceLearner(LearnerConfig(learning_rate=0.5, entropy_bonus=0.0))

    full_auth_ep = Episode(
        agent_id="gov",
        user_input="Approve ADR",
        assistant_output="Approved",
        action_id="a",
        action_logprob=None,  # Full authority: reasoned, never sampled from policy
    )
    reward = Reward(
        episode_id=full_auth_ep.id,
        agent_id="gov",
        source=RewardSource.AGGREGATE,
        value=0.8,
    )

    before = policy.snapshot()
    result = learner.update(policy, [full_auth_ep], [reward])
    after = policy.snapshot()

    assert result.episodes_used == 0
    assert result.extra.get("full_authority_excluded") == 1
    assert after.logits == before.logits


def test_ac_1_full_authority_excluded_count_in_extra() -> None:
    """Story 1.1 AC1: LearnerResult.extra['full_authority_excluded'] reports the exclusion count on every call, including 0."""
    actions = [Action(id="a"), Action(id="b")]
    policy = SoftmaxPolicy.from_actions(actions, agent_id="gov")
    learner = ReinforceLearner()

    # Case 1: Batch with 2 full-authority episodes
    ep1 = Episode(agent_id="gov", action_id="a", action_logprob=None)
    ep2 = Episode(agent_id="gov", action_id="b", action_logprob=None)
    rew1 = Reward(episode_id=ep1.id, agent_id="gov", source=RewardSource.AGGREGATE, value=0.5)
    rew2 = Reward(episode_id=ep2.id, agent_id="gov", source=RewardSource.AGGREGATE, value=-0.5)

    res1 = learner.update(policy, [ep1, ep2], [rew1, rew2])
    assert res1.extra.get("full_authority_excluded") == 2
    assert res1.episodes_used == 0

    # Case 2: Batch with 0 full-authority episodes
    ep3 = Episode(agent_id="gov", action_id="a", action_logprob=-0.693147)
    rew3 = Reward(episode_id=ep3.id, agent_id="gov", source=RewardSource.AGGREGATE, value=0.5)
    res2 = learner.update(policy, [ep3], [rew3])
    assert res2.extra.get("full_authority_excluded") == 0
    assert res2.episodes_used == 1


def test_ac_2_low_authority_importance_sampling_unchanged() -> None:
    """Story 1.1 AC2: Existing low-authority importance-sampling behavior is unchanged and not excluded."""
    actions = [Action(id="a"), Action(id="b")]
    policy = SoftmaxPolicy.from_actions(actions, agent_id="gov")
    learner = ReinforceLearner(LearnerConfig(learning_rate=0.5, entropy_bonus=0.0))

    # Older policy logged action 'a' with behaviour logprob -1.2 (prob ~0.301)
    # Current policy has uniform logits (prob 0.5)
    # Target / Behaviour ratio ~ 0.5 / 0.301 > 1.0 (reweighted)
    ep = Episode(agent_id="gov", action_id="a", action_logprob=-1.2)
    rew = Reward(episode_id=ep.id, agent_id="gov", source=RewardSource.AGGREGATE, value=0.8)

    before = policy.snapshot()
    result = learner.update(policy, [ep], [rew])
    after = policy.snapshot()

    assert result.episodes_used == 1
    assert result.extra.get("full_authority_excluded") == 0
    assert after.logits["a"] > before.logits["a"]

def test_ac_3_audit_warning_on_full_authority_presence() -> None:
    """Story 1.1 AC3: audit.py emits the updated ADR-001 §4.5 exclusion warning when full-authority episode is present."""
    from agent_learning.audit import AuditReport, _attribute, _projection
    actions = [Action(id="a"), Action(id="b")]
    policy = SoftmaxPolicy.from_actions(actions, agent_id="gov")
    snapshot = policy.snapshot()
    config = LearnerConfig(learning_rate=0.5, entropy_bonus=0.0)

    report = AuditReport(agent_id="gov", run_id="test-run")
    report.input_policy = _projection(snapshot)
    report.summary = {
        "proposed_deltas": {a.id: 0.0 for a in actions},
        "recorded_applied_deltas": {a.id: 0.0 for a in actions},
    }

    full_auth_ep = Episode(agent_id="gov", action_id="a", action_logprob=None)
    rew = Reward(episode_id=full_auth_ep.id, agent_id="gov", source=RewardSource.AGGREGATE, value=0.5)

    _attribute(report, snapshot, config, limit=3.0, episodes=[full_auth_ep], rewards=[rew])

    expected_msg = (
        "One or more full-authority episodes (action_logprob is None) were present in this "
        "batch and excluded from the REINFORCE update, not reweighted — see ADR-001 §4.5."
    )
    assert any(expected_msg in w for w in report.warnings)


def test_ac_4_audit_call_sites_exclude_full_authority_episodes() -> None:
    """Story 1.1 AC4: Both audit.py update call sites (:444 direct replay and :503 attribution) exclude full-authority episodes."""
    from dataclasses import replace
    actions = [Action(id="a"), Action(id="b")]
    policy = SoftmaxPolicy.from_actions(actions, agent_id="gov")
    snapshot = policy.snapshot()
    config = LearnerConfig(learning_rate=0.5, entropy_bonus=0.0)

    full_auth_ep = Episode(agent_id="gov", action_id="a", action_logprob=None)
    rew = Reward(episode_id=full_auth_ep.id, agent_id="gov", source=RewardSource.AGGREGATE, value=0.9)

    # Call site 1 (audit.py:444 equivalent): ReinforceLearner(config).update(...)
    res_direct = ReinforceLearner(config).update(policy, [full_auth_ep], [rew])
    assert res_direct.episodes_used == 0
    assert res_direct.extra["full_authority_excluded"] == 1
    assert res_direct.logit_deltas == {"a": 0.0, "b": 0.0}

    # Call site 2 (audit.py:503 equivalent): reward_only = ReinforceLearner(replace(config, entropy_bonus=0.0))
    reward_only = ReinforceLearner(replace(config, entropy_bonus=0.0))
    pol_attribution = SoftmaxPolicy.from_snapshot(snapshot)
    res_attr = reward_only.update(pol_attribution, [full_auth_ep], [rew])
    assert res_attr.episodes_used == 0
    assert res_attr.extra["full_authority_excluded"] == 1
    assert res_attr.logit_deltas == {"a": 0.0, "b": 0.0}

