"""Story 16.4 — Counting Each Episode Once (ADR-016, FDD-016 §2.4, §3 item 6, E1, E6, E7).

Acceptance Criteria:
  AC_0 (Scale): -1.0 maps to r = 0, 0.0 to 0.5, +1.0 to 1; values outside [-1, 1] or non-finite raise ValueError.
  AC_1 (Count): one episode for action a with reward +1.0 gives pull_count 1, cumulative 1.0, mean 1.0;
       with 0.0 it adds 1 and 0.5; only the chosen action changes.
  AC_2 (Selection): an episode whose selection_basis is not ucb, whose action_id is outside the action space,
       or that has no aggregate reward is skipped; when several aggregate rewards exist, newest is used.
  AC_3 (Once): offering same episodes a second time (same call or later call) leaves stats and episodes_used unchanged;
       each counted id appears once in consumed_episode_ids.
  AC_4 (Through The Runner): two successive run_offline_batch runs over the same stored episodes give the
       statistics of one pass.
  AC_5 (Late Reward): an episode created before newer already-counted episodes, whose reward is recorded afterwards,
       is counted when first offered with its reward, and once only.
  AC_6 (Shared Function): UCBLearner.update counts through add_rewards of policy/action_statistics.py;
       for same items, stats equal direct add_rewards; source check finds no second implementation in learners/ucb.py.
  AC_7 (Result): update advances snapshot version and returns LearnerResult with episodes_used, mean_reward of
       mapped values, consumed_inputs, and extra; call with no usable episodes changes nothing and returns
       episodes_used of 0; given SoftmaxPolicy it raises TypeError.

Contract Interpretations (derived via scripts/spec_gate.py):
  I1 (Upstream Fork Purity): Implemented under src/agent_learning_ext/ leaving upstream pristine.
  I2 (Storage Decoupling & Serialization): learners/ucb.py imports nothing from storage; snapshot round-trips via JSON.
  I3 (Empty Collection Base Case): Empty episodes or rewards returns unmutated snapshot with episodes_used=0.
  I4 (Non-Finite Float Rejection): NaNs/Infs rejected with ValueError.
"""

from __future__ import annotations

import ast
import copy
import json
import math
from pathlib import Path
from typing import Any

import pytest

from agent_learning.learners.base import Learner
from agent_learning.policy import SoftmaxPolicy
from agent_learning.storage import InMemoryStore
from agent_learning.types import Action, Episode, PolicySnapshot, Reward, RewardSource
from agent_learning_ext import LearningRunner, UCBLearner, UCBPolicy
from agent_learning_ext.policy.action_statistics import (
    ActionStats,
    add_rewards,
    read_statistics,
    reward_to_r,
)
from agent_learning_ext.policy.ucb import SELECTION_BASIS

ACTIONS = [Action(id="a", description="Action A"), Action(id="b", description="Action B")]


def _policy(
    stats: dict[str, dict[str, Any]] | None = None,
    consumed: list[str] | None = None,
    variant: str = "wilson",
    c: float = 1.4142135623730951,
) -> UCBPolicy:
    """Build a test UCBPolicy instance with optional preloaded statistics."""
    metadata: dict[str, Any] = {
        "policy_type": "ucb",
        "ucb_variant": variant,
        "exploration_constant": c,
        "action_statistics": stats or {a.id: {"pull_count": 0, "cumulative_reward": 0.0, "mean_reward": 0.0} for a in ACTIONS},
        "consumed_episode_ids": list(consumed or []),
    }
    snap = PolicySnapshot(
        agent_id="agent",
        task_id="task",
        actions=list(ACTIONS),
        logits={"a": 0.0, "b": 0.0},
        metadata=metadata,
    )
    return UCBPolicy.from_snapshot(snap)


def _episode(
    episode_id: str,
    action_id: str | None = "a",
    *,
    basis: str | None = SELECTION_BASIS,
    created_at: str = "2026-10-29T00:00:00+00:00",
) -> Episode:
    metadata = {"selection_basis": basis} if basis is not None else {}
    return Episode(
        id=episode_id,
        agent_id="agent",
        task_id="task",
        action_id=action_id,
        metadata=metadata,
        created_at=created_at,
    )


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


def _reward(
    episode_id: str,
    value: float,
    created_at: str = "2026-10-29T00:00:00+00:00",
    rid: str | None = None,
    source: RewardSource = RewardSource.AGGREGATE,
) -> Reward:
    return Reward(
        id=rid or f"rew-{episode_id}-{created_at}",
        episode_id=episode_id,
        agent_id="agent",
        source=source,
        value=value,
        created_at=created_at,
    )


def _runner() -> tuple[LearningRunner, InMemoryStore, UCBPolicy]:
    store = InMemoryStore()
    policy = UCBPolicy.from_actions(ACTIONS, agent_id="agent", task_id="task")
    store.store_policy(policy.snapshot())
    runner = LearningRunner(store=store, policy=policy, metrics=[], learner=UCBLearner())
    return runner, store, policy


# -----------------------------------------------------------------------------
# AC_0 (Scale)
# -----------------------------------------------------------------------------


def test_ac0_the_reward_scale_maps_minus_one_zero_one() -> None:
    """AC_0: -1.0 maps to r = 0, 0.0 to 0.5, +1.0 to 1; 0.25 to 0.625."""
    assert reward_to_r(-1.0) == 0.0
    assert reward_to_r(0.0) == 0.5
    assert reward_to_r(1.0) == 1.0
    assert reward_to_r(0.25) == pytest.approx(0.625, abs=1e-12)


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf, 1.0000001, -1.0000001, 2.0, -5.0, True, False])
def test_ac0_a_bad_reward_value_is_refused(bad: Any) -> None:
    """AC_0 & I4: bad reward values outside [-1, 1], non-finite floats, or booleans raise ValueError."""
    with pytest.raises(ValueError, match="reward"):
        reward_to_r(bad)


def test_ac0_a_bad_aggregate_reward_is_refused_by_update_even_for_a_skipped_episode() -> None:
    """AC_0: UCBLearner.update validates aggregate rewards upfront and rejects invalid values."""
    policy = _policy()
    before = policy.snapshot().to_dict()
    with pytest.raises(ValueError, match="reward"):
        UCBLearner().update(policy, [_episode("e1")], [_reward("e1", 0.5), _reward("other", 1.5)])
    assert policy.snapshot().to_dict() == before


# -----------------------------------------------------------------------------
# AC_1 (Count)
# -----------------------------------------------------------------------------


def test_ac1_one_episode_reward_plus_one_gives_pull_1_cum_1_mean_1() -> None:
    """AC_1: one episode for action a with reward +1.0 gives pull_count 1, cumulative 1.0, mean 1.0."""
    policy = _policy()
    result = UCBLearner().update(policy, [_episode("e1", "a")], [_reward("e1", 1.0)])
    assert result.episodes_used == 1

    stats = read_statistics(policy.snapshot().metadata, [a.id for a in ACTIONS])
    assert stats["a"] == ActionStats(pull_count=1, cumulative_reward=1.0, mean_reward=1.0)
    assert stats["b"] == ActionStats(pull_count=0, cumulative_reward=0.0, mean_reward=0.0)


def test_ac1_second_episode_reward_zero_adds_1_and_half_mean_recomputed_only_chosen_changes() -> None:
    """AC_1: subsequent reward 0.0 adds 1 pull and 0.5 cumulative; mean recomputed (0.75); only a changes."""
    policy = _policy()
    learner = UCBLearner()
    learner.update(policy, [_episode("e1", "a")], [_reward("e1", 1.0)])
    learner.update(policy, [_episode("e2", "a")], [_reward("e2", 0.0)])

    stats = read_statistics(policy.snapshot().metadata, [a.id for a in ACTIONS])
    assert stats["a"] == ActionStats(pull_count=2, cumulative_reward=1.5, mean_reward=0.75)
    assert stats["b"] == ActionStats(pull_count=0, cumulative_reward=0.0, mean_reward=0.0)


# -----------------------------------------------------------------------------
# AC_2 (Selection)
# -----------------------------------------------------------------------------


def test_ac2_an_unusable_episode_is_skipped_and_not_counted() -> None:
    """AC_2: episodes with non-ucb basis, unknown action, or missing reward are skipped."""
    policy = _policy()
    before = policy.snapshot().to_dict()

    episodes = [
        _episode("e-softmax", "a", basis="softmax"),
        _episode("e-no-basis", "a", basis=None),
        _episode("e-foreign-action", "foreign_action"),
        _episode("e-no-action", None),
        _episode("e-no-reward", "a"),
    ]
    rewards = [
        _reward("e-softmax", 1.0),
        _reward("e-no-basis", 1.0),
        _reward("e-foreign-action", 1.0),
        _reward("e-no-action", 1.0),
    ]

    result = UCBLearner().update(policy, episodes, rewards)
    assert result.episodes_used == 0
    assert result.consumed_inputs == []
    assert policy.snapshot().to_dict() == before


def test_ac2_non_aggregate_rewards_are_skipped() -> None:
    """AC_2: rewards whose source is not AGGREGATE are skipped."""
    policy = _policy()
    before = policy.snapshot().to_dict()

    reward = _reward("e1", 1.0, source=RewardSource.METRIC)
    result = UCBLearner().update(policy, [_episode("e1", "a")], [reward])
    assert result.episodes_used == 0
    assert policy.snapshot().to_dict() == before


def test_ac2_the_newest_aggregate_reward_is_used() -> None:
    """AC_2: when several aggregate rewards exist for an episode, the newest is used."""
    policy = _policy()
    older = _reward("e1", -1.0, created_at="2026-10-29T00:00:01+00:00", rid="r-old")
    newer = _reward("e1", 1.0, created_at="2026-10-29T00:00:02+00:00", rid="r-new")

    result = UCBLearner().update(policy, [_episode("e1", "a")], [older, newer])
    assert result.episodes_used == 1
    assert result.consumed_inputs is not None
    assert result.consumed_inputs[0].reward_id == "r-new"
    stats = read_statistics(policy.snapshot().metadata, [a.id for a in ACTIONS])
    assert stats["a"] == ActionStats(pull_count=1, cumulative_reward=1.0, mean_reward=1.0)


# -----------------------------------------------------------------------------
# AC_3 (Once)
# -----------------------------------------------------------------------------


def test_ac3_same_episodes_in_same_call_counted_once() -> None:
    """AC_3: duplicate episodes offered in the same update call count once."""
    policy = _policy()
    ep = _episode("e1", "a")
    result = UCBLearner().update(policy, [ep, ep, copy.deepcopy(ep)], [_reward("e1", 1.0)])

    assert result.episodes_used == 1
    stats = read_statistics(policy.snapshot().metadata, [a.id for a in ACTIONS])
    assert stats["a"] == ActionStats(pull_count=1, cumulative_reward=1.0, mean_reward=1.0)
    assert policy.consumed_episode_ids() == ["e1"]


def test_ac3_same_episodes_in_later_call_count_once() -> None:
    """AC_3: episodes offered in a later call that are already in consumed_episode_ids are skipped."""
    policy = _policy()
    learner = UCBLearner()
    episodes = [_episode("e1", "a"), _episode("e2", "b")]
    rewards = [_reward("e1", 1.0), _reward("e2", -1.0)]

    res1 = learner.update(policy, episodes, rewards)
    assert res1.episodes_used == 2
    after_first = policy.snapshot().to_dict()

    res2 = learner.update(policy, episodes, rewards)
    assert res2.episodes_used == 0
    assert policy.snapshot().to_dict() == after_first
    assert sorted(policy.consumed_episode_ids()) == ["e1", "e2"]


# -----------------------------------------------------------------------------
# AC_4 (Through The Runner)
# -----------------------------------------------------------------------------


def test_ac4_two_runner_batches_over_same_episodes_give_one_pass() -> None:
    """AC_4: two successive run_offline_batch runs over the same stored episodes give the stats of one pass."""
    runner, store, policy = _runner()
    _stored_episode(store, "e1", "a", "2026-10-29T00:00:01+00:00")
    _stored_episode(store, "e2", "b", "2026-10-29T00:00:02+00:00")
    store.store_reward(_reward("e1", 1.0))
    store.store_reward(_reward("e2", -1.0))

    first_run = runner.run_offline_batch("agent", task_id="task", score_missing=False)
    assert first_run.status.value.lower() == "succeeded"
    assert first_run.metrics["episodes_used"] == 2.0

    stats_once = read_statistics(policy.snapshot().metadata, [a.id for a in ACTIONS])
    assert stats_once["a"] == ActionStats(pull_count=1, cumulative_reward=1.0, mean_reward=1.0)
    assert stats_once["b"] == ActionStats(pull_count=1, cumulative_reward=0.0, mean_reward=0.0)

    second_run = runner.run_offline_batch("agent", task_id="task", score_missing=False)
    assert second_run.status.value.lower() == "succeeded"
    assert second_run.metrics["episodes_used"] == 0.0

    stats_twice = read_statistics(policy.snapshot().metadata, [a.id for a in ACTIONS])
    assert stats_twice == stats_once
    assert sorted(policy.consumed_episode_ids()) == ["e1", "e2"]


# -----------------------------------------------------------------------------
# AC_5 (Late Reward)
# -----------------------------------------------------------------------------


def test_ac5_late_reward_counted_once_when_first_offered() -> None:
    """AC_5: an early episode whose reward is recorded later is counted when first offered with reward."""
    runner, store, policy = _runner()
    _stored_episode(store, "early", "b", "2026-10-29T00:00:01+00:00")
    _stored_episode(store, "later", "a", "2026-10-29T00:00:02+00:00")
    store.store_reward(_reward("later", 1.0))

    run1 = runner.run_offline_batch("agent", task_id="task", score_missing=False)
    assert run1.metrics["episodes_used"] == 1.0
    assert policy.consumed_episode_ids() == ["later"]

    # Now early episode gets its reward recorded
    store.store_reward(_reward("early", 1.0))
    run2 = runner.run_offline_batch("agent", task_id="task", score_missing=False)
    assert run2.metrics["episodes_used"] == 1.0
    assert sorted(policy.consumed_episode_ids()) == ["early", "later"]

    stats = read_statistics(policy.snapshot().metadata, [a.id for a in ACTIONS])
    assert stats["a"] == ActionStats(pull_count=1, cumulative_reward=1.0, mean_reward=1.0)
    assert stats["b"] == ActionStats(pull_count=1, cumulative_reward=1.0, mean_reward=1.0)

    # Third pass without new data changes nothing
    run3 = runner.run_offline_batch("agent", task_id="task", score_missing=False)
    assert run3.metrics["episodes_used"] == 0.0


# -----------------------------------------------------------------------------
# AC_6 (Shared Function)
# -----------------------------------------------------------------------------


def test_ac6_ucb_learner_parity_with_direct_add_rewards() -> None:
    """AC_6: UCBLearner produces identical statistics to direct call to add_rewards."""
    policy = _policy()
    episodes = [_episode("e1", "a"), _episode("e2", "b"), _episode("e3", "a")]
    rewards = [_reward("e1", 1.0), _reward("e2", 0.0), _reward("e3", -1.0)]

    UCBLearner().update(policy, episodes, rewards)
    policy_stats = read_statistics(policy.snapshot().metadata, [a.id for a in ACTIONS])

    # Direct call on fresh initial metadata
    direct_metadata: dict[str, Any] = {
        "action_statistics": {a.id: {"pull_count": 0, "cumulative_reward": 0.0, "mean_reward": 0.0} for a in ACTIONS},
        "consumed_episode_ids": [],
    }
    items = [("e1", "a", 1.0), ("e2", "b", 0.0), ("e3", "a", -1.0)]
    counted = add_rewards(direct_metadata, [a.id for a in ACTIONS], items)
    assert counted == ("e1", "e2", "e3")

    direct_stats = read_statistics(direct_metadata, [a.id for a in ACTIONS])
    assert policy_stats == direct_stats
    assert policy.consumed_episode_ids() == list(direct_metadata["consumed_episode_ids"])


def test_ac6_source_check_finds_no_second_implementation_in_learners_ucb() -> None:
    """AC_6: Static AST analysis confirms learners/ucb.py delegates counting to add_rewards."""
    root = Path(__file__).resolve().parents[1]
    learner_path = root / "src" / "agent_learning_ext" / "learners" / "ucb.py"
    tree = ast.parse(learner_path.read_text(encoding="utf-8"), filename=str(learner_path))

    # Must import add_rewards
    imports_add_rewards = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and "action_statistics" in node.module:
            for alias in node.names:
                if alias.name == "add_rewards":
                    imports_add_rewards = True
    assert imports_add_rewards, "learners/ucb.py must import add_rewards from action_statistics"

    # Must not contain cumulative_reward / pull_count arithmetic or math updates
    for node in ast.walk(tree):
        if isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name):
            assert node.target.id not in ("pull_count", "cumulative_reward"), (
                f"learners/ucb.py contains inline update to {node.target.id}"
            )


# -----------------------------------------------------------------------------
# AC_7 (Result) & Interpretations
# -----------------------------------------------------------------------------


def test_ac7_the_result_and_snapshot_bookkeeping() -> None:
    """AC_7: update advances version, returns LearnerResult with mean_reward, consumed_inputs, and extra."""
    policy = _policy()
    before = policy.snapshot()
    episodes = [_episode("e1", "a"), _episode("e2", "b")]
    rewards = [_reward("e1", 1.0), _reward("e2", 0.0)]

    result = UCBLearner().update(policy, episodes, rewards)
    after = policy.snapshot()

    assert result.episodes_used == 2
    assert result.mean_reward == pytest.approx((1.0 + 0.5) / 2, abs=1e-12)
    assert [(c.episode_id, c.reward_id) for c in (result.consumed_inputs or [])] == [
        ("e1", result.consumed_inputs[0].reward_id),  # type: ignore[index]
        ("e2", result.consumed_inputs[1].reward_id),  # type: ignore[index]
    ]
    assert after.version == before.version + 1
    assert after.id != before.id
    assert after.episodes_seen == before.episodes_seen + 2
    assert after.updates_applied == before.updates_applied + 1
    assert after.logits == {"a": 0.0, "b": 0.0}
    assert after.metadata["consumed_episode_ids"] == ["e1", "e2"]
    assert result.baseline_before == result.baseline_after == before.baseline
    assert result.extra["statistics_before"]["a"]["pull_count"] == 0
    assert result.extra["statistics_after"]["a"]["pull_count"] == 1


def test_ac7_a_call_with_no_usable_episodes_changes_nothing() -> None:
    """AC_7: a call with no usable episodes leaves snapshot version and policy untouched, episodes_used=0."""
    policy = _policy()
    before = policy.snapshot().to_dict()
    result = UCBLearner().update(policy, [], [])

    assert result.episodes_used == 0
    assert result.mean_reward == 0.0
    assert result.consumed_inputs == []
    assert policy.snapshot().to_dict() == before


def test_ac7_softmax_policy_raises_type_error() -> None:
    """AC_7: passing SoftmaxPolicy to UCBLearner.update raises TypeError."""
    softmax = SoftmaxPolicy.from_actions(ACTIONS, agent_id="agent")
    with pytest.raises(TypeError, match="UCBPolicy"):
        UCBLearner().update(softmax, [], [])


def test_i2_storage_decoupling_and_json_roundtrip() -> None:
    """I2: learners/ucb.py imports nothing from storage; updated snapshot roundtrips through JSON."""
    root = Path(__file__).resolve().parents[1]
    learner_path = root / "src" / "agent_learning_ext" / "learners" / "ucb.py"
    tree = ast.parse(learner_path.read_text(encoding="utf-8"), filename=str(learner_path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "storage" not in alias.name, f"learners/ucb.py imports {alias.name}"
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert "storage" not in node.module, f"learners/ucb.py imports from {node.module}"

    policy = _policy()
    UCBLearner().update(policy, [_episode("e1", "a")], [_reward("e1", 1.0)])
    snap = policy.snapshot()
    serialized = json.dumps(snap.to_dict())
    deserialized = PolicySnapshot.from_dict(json.loads(serialized))
    assert deserialized == snap


def test_learner_is_subclass_and_exported() -> None:
    """Verify UCBLearner is a Learner subclass and exported from public extension surfaces."""
    import agent_learning_ext
    import agent_learning_ext.learners as ext_learners

    assert issubclass(UCBLearner, Learner)
    assert agent_learning_ext.UCBLearner is UCBLearner
    assert ext_learners.UCBLearner is UCBLearner
    assert "UCBLearner" in agent_learning_ext.__all__
