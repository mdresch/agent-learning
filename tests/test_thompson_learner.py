"""Contract tests for Epic 15, Story 15.4 (The Conjugate Update and the Ceiling).

Story: docs/user-stories/epic-15-bayesian-bandit-posterior-sampling.md, Story 15.4.
ADR-015 §4.1, §4.4 and Invariant 4; BRD-015 BRU-015-05; FDD-015 §2.1, §3 item 6, §5 and D1, D7.

Interpretation I1: the story names no function for AC_0's scale, so it is
``reward_to_success(value)`` in ``agent_learning.learners.thompson``.

Interpretation I2: the learner needs to write the posterior into the policy, but
``ThompsonPolicy.apply_update`` is a ``TypeError`` (D6). The policy gets one more method,
``update_posterior(alpha, beta, consumed_episode_ids, *, episodes_seen)``, that validates the new
state as ``from_snapshot`` does, keeps ``logits`` at zero, bumps ``updates_applied`` and advances the
version. These tests reach it only through ``ThompsonLearner.update``.

Interpretation I3: as in ``ReinforceLearner``, every aggregate reward offered is validated (finite and
within [-1, 1]), including one for an episode the update then skips.

Interpretation I4: a call with no usable episode returns ``mean_reward`` 0.0, an empty
``consumed_inputs`` list and does not touch the policy, not even its version.

Interpretation I5: ``baseline_before`` and ``baseline_after`` both equal the snapshot's baseline; a
posterior has no baseline. ``extra`` carries ``posterior_before`` and ``posterior_after``.

Interpretation I6: the ceiling is applied to every action once at the end of the call, to the totals
that are over ``N_MAX``; a total at or below ``N_MAX`` is left untouched.

Interpretation I7: AC_7 and AC_8 run through ``LearningRunner`` with the same ``ThompsonPolicy``
object across runs, as the runner is built to be used. The runner is not changed.
"""

from __future__ import annotations

import copy
import json
import math

import pytest

from agent_learning import LearningRunner
from agent_learning.learners.base import Learner
from agent_learning.learners.thompson import ThompsonLearner, reward_to_success
from agent_learning.policy import SoftmaxPolicy
from agent_learning.policy.thompson import N_MAX, SELECTION_BASIS, ThompsonPolicy
from agent_learning.storage import InMemoryStore
from agent_learning.types import Action, Episode, PolicySnapshot, Reward, RewardSource

ACTIONS = [Action(id="a"), Action(id="b")]


def _policy(alpha: dict | None = None, beta: dict | None = None, consumed: list | None = None) -> ThompsonPolicy:
    metadata: dict = {"posterior_parameters": {"alpha": alpha or {}, "beta": beta or {}}}
    if consumed is not None:
        metadata["consumed_episode_ids"] = consumed
    return ThompsonPolicy.from_snapshot(
        PolicySnapshot(
            agent_id="agent",
            task_id="task",
            actions=list(ACTIONS),
            logits={"a": 0.0, "b": 0.0},
            metadata=metadata,
        )
    )


def _episode(episode_id: str, action_id: str | None = "a", *, basis: str | None = SELECTION_BASIS, **kw) -> Episode:
    metadata = {"selection_basis": basis} if basis is not None else {}
    return Episode(id=episode_id, agent_id="agent", task_id="task", action_id=action_id, metadata=metadata, **kw)


def _reward(episode_id: str, value: float, created_at: str = "2026-10-29T00:00:00+00:00", rid: str | None = None) -> Reward:
    return Reward(
        id=rid or f"reward-{episode_id}-{created_at}",
        episode_id=episode_id,
        agent_id="agent",
        source=RewardSource.AGGREGATE,
        value=value,
        created_at=created_at,
    )


def _update(policy: ThompsonPolicy, episodes: list, rewards: list):
    return ThompsonLearner().update(policy, episodes, rewards)


def test_ac0_the_reward_scale_maps_minus_one_zero_one() -> None:
    assert reward_to_success(-1.0) == 0.0
    assert reward_to_success(0.0) == 0.5
    assert reward_to_success(1.0) == 1.0
    assert reward_to_success(0.25) == pytest.approx(0.625, abs=1e-12)


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf, 1.0000001, -1.5, 7.0])
def test_ac0_a_bad_reward_value_is_refused(bad: float) -> None:
    with pytest.raises(ValueError, match="reward"):
        reward_to_success(bad)


def test_ac0_a_bad_aggregate_reward_is_refused_by_update_even_for_a_skipped_episode() -> None:
    policy = _policy()
    before = policy.snapshot().to_dict()
    with pytest.raises(ValueError, match="reward"):
        _update(policy, [_episode("e1")], [_reward("e1", 0.5), _reward("other", 1.5)])
    assert policy.snapshot().to_dict() == before


def test_ac1_a_success_from_the_uniform_prior_gives_two_one() -> None:
    policy = _policy()
    _update(policy, [_episode("e1", "a")], [_reward("e1", 1.0)])
    post = policy.posterior()
    assert post["alpha"]["a"] == pytest.approx(2.0, abs=1e-12)
    assert post["beta"]["a"] == pytest.approx(1.0, abs=1e-12)


def test_ac1_a_neutral_reward_from_14_2_gives_14_5_2_5_and_only_the_chosen_action_changes() -> None:
    policy = _policy({"a": 14, "b": 3}, {"a": 2, "b": 8})
    _update(policy, [_episode("e1", "a")], [_reward("e1", 0.0)])
    post = policy.posterior()
    assert post["alpha"]["a"] == pytest.approx(14.5, abs=1e-12)
    assert post["beta"]["a"] == pytest.approx(2.5, abs=1e-12)
    assert post["alpha"]["b"] == 3.0
    assert post["beta"]["b"] == 8.0


def test_ac1_a_failure_adds_to_beta_only() -> None:
    policy = _policy()
    _update(policy, [_episode("e1", "b")], [_reward("e1", -1.0)])
    post = policy.posterior()
    assert post["alpha"]["b"] == pytest.approx(1.0, abs=1e-12)
    assert post["beta"]["b"] == pytest.approx(2.0, abs=1e-12)


def test_ac2_the_ceiling_rescales_to_n_max_and_keeps_the_ratio() -> None:
    assert N_MAX == 5000.0
    policy = _policy({"a": 4000}, {"a": 1500})
    _update(policy, [_episode("e1", "a")], [_reward("e1", 1.0)])
    post = policy.posterior()
    alpha, beta = post["alpha"]["a"], post["beta"]["a"]
    assert alpha + beta == pytest.approx(5000.0, abs=1e-9)
    assert alpha / beta == pytest.approx(4001.0 / 1500.0, rel=1e-9)
    assert alpha == pytest.approx(4001.0 * 5000.0 / 5501.0, rel=1e-9)


def test_ac2_a_total_at_or_below_the_ceiling_is_untouched() -> None:
    policy = _policy({"a": 3999.0, "b": 2000.0}, {"a": 1000.0, "b": 1000.0})
    _update(policy, [_episode("e1", "a")], [_reward("e1", 1.0)])  # a ends at exactly 4000 + 1000
    post = policy.posterior()
    assert post["alpha"]["a"] == 4000.0
    assert post["beta"]["a"] == 1000.0
    assert post["alpha"]["b"] == 2000.0
    assert post["beta"]["b"] == 1000.0


def test_ac2_the_ceiling_applies_once_per_call_after_all_episodes() -> None:
    policy = _policy({"a": 4000}, {"a": 999})  # total 4999
    episodes = [_episode(f"e{i}", "a") for i in range(3)]
    _update(policy, episodes, [_reward(e.id, 1.0) for e in episodes])
    post = policy.posterior()
    assert post["alpha"]["a"] + post["beta"]["a"] == pytest.approx(5000.0, abs=1e-9)
    assert post["alpha"]["a"] / post["beta"]["a"] == pytest.approx(4003.0 / 999.0, rel=1e-9)


@pytest.mark.parametrize(
    "episode",
    [
        _episode("e1", basis="bayesian_decision"),
        _episode("e1", basis=None),
        _episode("e1", action_id="ghost"),
        _episode("e1", action_id=None),
    ],
    ids=["other-basis", "no-basis", "unknown-action", "no-action"],
)
def test_ac3_an_unusable_episode_is_skipped_and_not_counted(episode: Episode) -> None:
    policy = _policy()
    before = policy.snapshot().to_dict()
    result = _update(policy, [episode], [_reward("e1", 1.0)])
    assert result.episodes_used == 0
    assert policy.snapshot().to_dict() == before


def test_ac3_an_episode_without_an_aggregate_reward_is_skipped() -> None:
    policy = _policy()
    metric_reward = Reward(id="m", episode_id="e1", agent_id="agent", source=RewardSource.METRIC, value=1.0)
    result = _update(policy, [_episode("e1"), _episode("e2")], [metric_reward, _reward("e2", 1.0)])
    assert result.episodes_used == 1
    assert policy.consumed_episode_ids() == ["e2"]


def test_ac3_an_already_consumed_episode_is_skipped() -> None:
    policy = _policy(consumed=["e1"])
    result = _update(policy, [_episode("e1"), _episode("e2")], [_reward("e1", 1.0), _reward("e2", 1.0)])
    assert result.episodes_used == 1
    assert policy.consumed_episode_ids() == ["e1", "e2"]


def test_ac3_the_newest_aggregate_reward_is_used() -> None:
    policy = _policy()
    rewards = [
        _reward("e1", -1.0, "2026-10-29T10:00:00+00:00", rid="new"),
        _reward("e1", 1.0, "2026-10-29T09:00:00+00:00", rid="old"),
    ]
    result = _update(policy, [_episode("e1", "a")], rewards)
    assert result.consumed_inputs[0].reward_id == "new"
    assert policy.posterior()["beta"]["a"] == pytest.approx(2.0, abs=1e-12)  # r = 0 from the newest


def test_ac4_the_result_and_the_snapshot_bookkeeping() -> None:
    policy = _policy()
    before = policy.snapshot()
    episodes = [_episode("e1", "a"), _episode("e2", "b")]
    result = _update(policy, episodes, [_reward("e1", 1.0), _reward("e2", 0.0)])
    after = policy.snapshot()

    assert result.episodes_used == 2
    assert result.mean_reward == pytest.approx((1.0 + 0.5) / 2, abs=1e-12)
    assert [(c.episode_id, c.reward_id) for c in result.consumed_inputs] == [
        ("e1", result.consumed_inputs[0].reward_id),
        ("e2", result.consumed_inputs[1].reward_id),
    ]
    assert after.version == before.version + 1
    assert after.id != before.id
    assert after.episodes_seen == before.episodes_seen + 2
    assert after.updates_applied == before.updates_applied + 1
    assert after.logits == {"a": 0.0, "b": 0.0}
    assert after.metadata["consumed_episode_ids"] == ["e1", "e2"]
    assert result.baseline_before == result.baseline_after == before.baseline
    assert result.extra["posterior_before"]["alpha"]["a"] == 1.0
    assert result.extra["posterior_after"]["alpha"]["a"] == pytest.approx(2.0)
    assert json.loads(json.dumps(after.to_dict())) == after.to_dict()


def test_ac4_a_call_with_no_usable_episode_changes_nothing() -> None:
    policy = _policy({"a": 3}, {"a": 2})
    before = policy.snapshot().to_dict()
    result = _update(policy, [], [])
    assert result.episodes_used == 0
    assert result.mean_reward == 0.0
    assert result.consumed_inputs == []
    assert policy.snapshot().to_dict() == before


def test_ac5_a_softmax_policy_is_refused() -> None:
    softmax = SoftmaxPolicy.from_actions(ACTIONS, agent_id="agent")
    with pytest.raises(TypeError):
        ThompsonLearner().update(softmax, [], [])


def test_ac6_the_same_episodes_in_the_same_call_count_once() -> None:
    policy = _policy()
    episode = _episode("e1", "a")
    result = _update(policy, [episode, episode, copy.deepcopy(episode)], [_reward("e1", 1.0)])
    assert result.episodes_used == 1
    assert policy.posterior()["alpha"]["a"] == pytest.approx(2.0, abs=1e-12)
    assert policy.consumed_episode_ids() == ["e1"]


def test_ac6_the_same_episodes_in_a_later_call_count_once() -> None:
    policy = _policy()
    episodes = [_episode("e1", "a"), _episode("e2", "b")]
    rewards = [_reward("e1", 1.0), _reward("e2", -1.0)]
    _update(policy, episodes, rewards)
    after_first = policy.snapshot().to_dict()

    second = _update(policy, episodes, rewards)
    assert second.episodes_used == 0
    assert policy.snapshot().to_dict() == after_first
    assert sorted(policy.consumed_episode_ids()) == ["e1", "e2"]


def _stored_episode(store: InMemoryStore, episode_id: str, action_id: str, created_at: str) -> None:
    store.store_episode(
        Episode(
            id=episode_id,
            agent_id="agent",
            task_id="task",
            action_id=action_id,
            metadata={"selection_basis": SELECTION_BASIS},
            intent_summary="Route a synthetic request",
            expected_outcome="Find a handler",
            execution_status="completed",
            result_summary="Synthetic response",
            created_at=created_at,
        )
    )


def _runner() -> tuple[LearningRunner, InMemoryStore, ThompsonPolicy]:
    store = InMemoryStore()
    policy = ThompsonPolicy.from_actions(ACTIONS, agent_id="agent", task_id="task")
    store.store_policy(policy.snapshot())
    runner = LearningRunner(store=store, policy=policy, metrics=[], learner=ThompsonLearner())
    return runner, store, policy


def test_ac7_two_runner_batches_over_the_same_episodes_give_one_pass() -> None:
    runner, store, policy = _runner()
    _stored_episode(store, "e1", "a", "2026-10-29T00:00:01+00:00")
    _stored_episode(store, "e2", "b", "2026-10-29T00:00:02+00:00")
    store.store_reward(_reward("e1", 1.0))
    store.store_reward(_reward("e2", -1.0))

    first = runner.run_offline_batch("agent", task_id="task", score_missing=False)
    once = policy.posterior()
    second = runner.run_offline_batch("agent", task_id="task", score_missing=False)

    assert once == {"alpha": {"a": 2.0, "b": 1.0}, "beta": {"a": 1.0, "b": 2.0}}
    assert policy.posterior() == once
    assert first.metrics["episodes_used"] == 2
    assert second.metrics["episodes_used"] == 0
    assert sorted(policy.consumed_episode_ids()) == ["e1", "e2"]


def test_ac8_a_late_reward_is_counted_once_when_first_offered_with_it() -> None:
    runner, store, policy = _runner()
    _stored_episode(store, "early", "b", "2026-10-29T00:00:01+00:00")  # created first, scored last
    _stored_episode(store, "later", "a", "2026-10-29T00:00:02+00:00")
    store.store_reward(_reward("later", 1.0))

    first = runner.run_offline_batch("agent", task_id="task", score_missing=False)
    assert first.metrics["episodes_used"] == 1
    assert policy.consumed_episode_ids() == ["later"]

    store.store_reward(_reward("early", 1.0))
    second = runner.run_offline_batch("agent", task_id="task", score_missing=False)
    assert second.metrics["episodes_used"] == 1
    assert policy.posterior()["alpha"]["b"] == pytest.approx(2.0, abs=1e-12)

    third = runner.run_offline_batch("agent", task_id="task", score_missing=False)
    assert third.metrics["episodes_used"] == 0
    assert sorted(policy.consumed_episode_ids()) == ["early", "later"]
    assert policy.posterior()["alpha"]["b"] == pytest.approx(2.0, abs=1e-12)


def test_the_learner_is_a_learner_and_is_exported() -> None:
    import agent_learning
    import agent_learning.learners as learners_package

    assert issubclass(ThompsonLearner, Learner)
    assert agent_learning.ThompsonLearner is ThompsonLearner
    assert learners_package.ThompsonLearner is ThompsonLearner
    assert "ThompsonLearner" in agent_learning.__all__
