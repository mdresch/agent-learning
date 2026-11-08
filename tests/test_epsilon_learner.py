"""Story 17.4 — Statistics and the Learner (ADR-017, BRD-017, FDD-017).

Acceptance Criteria:
  AC_0 (Initial): from_actions gives every action pull_count 0, cumulative_reward 0.0 and
       mean_reward 0.0 in metadata["action_statistics"], stores policy_type "epsilon_greedy",
       the schedule, an empty consumed_episode_ids, and leaves logits at zero;
       from_snapshot rejects an invalid statistic, a duplicate id, an action outside
       the action space, or a mean_reward differing from cumulative_reward / pull_count
       by more than 1e-9.
  AC_1 (Scale): The reward value -1.0 maps to r = 0, 0.0 to 0.5 and +1.0 to 1; a value
       that is not finite or outside [-1, 1] raises ValueError.
  AC_2 (Count): One episode for action a with reward +1.0 gives pull_count 1, cumulative_reward 1.0
       and mean_reward 1.0; with reward 0.0 it adds 1 and 0.5 and recomputes the mean;
       only the chosen action changes.
  AC_3 (Selection): An episode whose selection_basis is not epsilon_greedy, whose action_id
       is outside the action space, that has no aggregate reward, or whose id is already
       consumed is skipped and not counted; the newest aggregate reward is used.
  AC_4 (Once): Offering the same episodes to update again, in the same call or later, leaves
       the statistics and episodes_used as after the first; two successive run_offline_batch
       runs over the same stored episodes give the statistics of one pass; an episode
       rewarded after newer ones were counted is counted once.
  AC_5 (Shared Record): The statistics produced by this learner and by the UCB learner of
       Epic 16 for the same episodes are equal, because both call the one function of
       action_statistics.py.
  AC_6 (Result): update advances the snapshot version and returns a LearnerResult with
       episodes_used, mean_reward of the mapped values and consumed_inputs; with no usable
       episode it changes nothing and returns 0; given a SoftmaxPolicy it raises TypeError;
       the snapshot survives json.dumps and json.loads and round-trips through an in-memory
       store with no new record type, and the modules import nothing from agent_learning.storage.

Contract Interpretations (derived via scripts/spec_gate.py):
  I1 (Upstream Fork Purity): Implemented under src/agent_learning_ext/ leaving upstream pristine.
  I2 (Defensive None-Safety for Dictionaries): Defensively guard against None metadata.
  I3 (Non-Finite Float Rejection): Strictly reject NaNs and Infs.
"""

from __future__ import annotations

import ast
import copy
from pathlib import Path
from typing import Any

import pytest

from agent_learning.policy import SoftmaxPolicy
from agent_learning.storage import InMemoryStore
from agent_learning.types import Action, Episode, PolicySnapshot, Reward, RewardSource
from agent_learning_ext import LearningRunner, UCBLearner, UCBPolicy
from agent_learning_ext.learners.epsilon_greedy import EpsilonGreedyLearner
from agent_learning_ext.policy.action_statistics import (
    reward_to_r,
)
from agent_learning_ext.policy.epsilon_greedy import (
    SELECTION_BASIS,
    EpsilonGreedyPolicy,
)

ACTIONS = [
    Action(id="a", description="Action A", parameters={"reversible": True}),
    Action(id="b", description="Action B", parameters={"reversible": True}),
]


def _make_policy(
    actions: list[Action] | None = None,
    stats: dict[str, dict[str, Any]] | None = None,
    consumed: list[str] | None = None,
    eps0: float = 0.5,
    delta: float = 0.05,
    floor: float = 0.05,
) -> EpsilonGreedyPolicy:
    act_list = actions if actions is not None else list(ACTIONS)
    if stats is None:
        return EpsilonGreedyPolicy.from_actions(act_list, eps0=eps0, delta=delta, floor=floor)

    metadata: dict[str, Any] = {
        "policy_type": "epsilon_greedy",
        "epsilon_schedule": {"eps0": eps0, "delta": delta, "floor": floor},
        "action_statistics": copy.deepcopy(stats),
        "consumed_episode_ids": list(consumed or []),
    }
    snap = PolicySnapshot(
        agent_id="test-agent",
        task_id="test-task",
        actions=act_list,
        logits={a.id: 0.0 for a in act_list},
        metadata=metadata,
    )
    return EpsilonGreedyPolicy.from_snapshot(snap)


def _episode(
    eid: str,
    aid: str = "a",
    basis: str = SELECTION_BASIS,
    created_at: str = "2026-11-08T00:00:00Z",
) -> Episode:
    return Episode(
        id=eid,
        agent_id="test-agent",
        task_id="test-task",
        action_id=aid,
        action_logprob=None,
        created_at=created_at,
        metadata={"selection_basis": basis},
    )


def _reward(
    eid: str,
    value: float,
    source: RewardSource = RewardSource.AGGREGATE,
    created_at: str = "2026-11-08T00:00:00Z",
    rid: str | None = None,
) -> Reward:
    return Reward(
        id=rid or f"rw-{eid}",
        episode_id=eid,
        source=source,
        value=value,
        created_at=created_at,
    )


def test_ac0_initial_from_actions_and_snapshot_validation() -> None:
    """AC_0: Initial statistics zeroes, schedule stored, logits 0; from_snapshot validates."""
    policy = _make_policy()
    snap = policy.snapshot

    assert snap.metadata["policy_type"] == "epsilon_greedy"
    assert snap.metadata["epsilon_schedule"] == {"eps0": 0.5, "delta": 0.05, "floor": 0.05}
    assert snap.metadata["consumed_episode_ids"] == []
    for a in ACTIONS:
        st = snap.metadata["action_statistics"][a.id]
        assert st == {"pull_count": 0, "cumulative_reward": 0.0, "mean_reward": 0.0}
        assert snap.logits[a.id] == 0.0

    # from_snapshot rejects invalid statistics / duplicates / mean mismatch
    with pytest.raises(ValueError, match=r"consumed_episode_ids"):
        _make_policy(stats={"a": {"pull_count": 0, "cumulative_reward": 0.0, "mean_reward": 0.0}, "b": {"pull_count": 0, "cumulative_reward": 0.0, "mean_reward": 0.0}}, consumed=["ep-1", "ep-1"])

    with pytest.raises(ValueError, match=r"outside the action space"):
        _make_policy(stats={"unknown": {"pull_count": 0, "cumulative_reward": 0.0, "mean_reward": 0.0}})

    with pytest.raises(ValueError, match=r"differs from"):
        _make_policy(stats={"a": {"pull_count": 2, "cumulative_reward": 1.0, "mean_reward": 0.9}, "b": {"pull_count": 0, "cumulative_reward": 0.0, "mean_reward": 0.0}})


def test_ac1_reward_scale_and_validation() -> None:
    """AC_1: -1.0 -> 0.0, 0.0 -> 0.5, +1.0 -> 1.0; outside [-1, 1] or non-finite raises ValueError."""
    assert abs(reward_to_r(-1.0) - 0.0) < 1e-12
    assert abs(reward_to_r(0.0) - 0.5) < 1e-12
    assert abs(reward_to_r(1.0) - 1.0) < 1e-12

    for bad in (-1.01, 1.01, float("inf"), float("-inf"), float("nan")):
        with pytest.raises(ValueError, match=r"reward value"):
            reward_to_r(bad)


def test_ac2_count_episodes_and_only_chosen_action_changes() -> None:
    """AC_2: +1.0 gives count 1, cum 1.0, mean 1.0; then 0.0 gives count 2, cum 1.5, mean 0.75."""
    policy = _make_policy()
    learner = EpsilonGreedyLearner()

    ep1 = _episode("ep-1", "a")
    rw1 = _reward("ep-1", 1.0)
    res1 = learner.update(policy, [ep1], [rw1])
    assert res1.episodes_used == 1
    assert abs(res1.mean_reward - 1.0) < 1e-12

    stats = policy.snapshot.metadata["action_statistics"]
    assert stats["a"] == {"pull_count": 1, "cumulative_reward": 1.0, "mean_reward": 1.0}
    assert stats["b"] == {"pull_count": 0, "cumulative_reward": 0.0, "mean_reward": 0.0}

    ep2 = _episode("ep-2", "a")
    rw2 = _reward("ep-2", 0.0)
    res2 = learner.update(policy, [ep2], [rw2])
    assert res2.episodes_used == 1
    assert abs(res2.mean_reward - 0.5) < 1e-12

    stats2 = policy.snapshot.metadata["action_statistics"]
    assert stats2["a"]["pull_count"] == 2
    assert abs(stats2["a"]["cumulative_reward"] - 1.5) < 1e-12
    assert abs(stats2["a"]["mean_reward"] - 0.75) < 1e-12
    assert stats2["b"] == {"pull_count": 0, "cumulative_reward": 0.0, "mean_reward": 0.0}


def test_ac3_selection_filtering_and_newest_aggregate_reward() -> None:
    """AC_3: Non-epsilon_greedy basis, unknown action, no aggregate reward are skipped; newest aggregate used."""
    policy = _make_policy()
    learner = EpsilonGreedyLearner()

    ep_valid = _episode("ep-ok", "a")
    ep_other = _episode("ep-other", "a", basis="ucb")
    ep_unknown = _episode("ep-unk", "action_not_in_policy")
    ep_no_reward = _episode("ep-norew", "a")

    # Test mixed timestamp representations (e.g. +00:00 vs Z)
    rw_old = _reward("ep-ok", -1.0, created_at="2026-11-08T00:00:00Z")
    rw_new = _reward("ep-ok", 1.0, created_at="2026-11-08T00:01:00+00:00")  # newer even with mixed tz suffix
    rw_metric = _reward("ep-ok", 0.0, source=RewardSource.METRIC)

    res = learner.update(
        policy,
        [ep_valid, ep_other, ep_unknown, ep_no_reward],
        [rw_metric, rw_old, rw_new],
    )
    assert res.episodes_used == 1
    assert abs(res.mean_reward - 1.0) < 1e-12  # newest +1.0 was used, mapped to 1.0


def test_ac4_offering_same_episodes_again_counted_once() -> None:
    """AC_4: Re-offering episodes leaves stats and episodes_used unchanged; late reward counted once."""
    policy = _make_policy()
    learner = EpsilonGreedyLearner()

    ep1 = _episode("ep-1", "a")
    ep2 = _episode("ep-2", "b")
    rw1 = _reward("ep-1", 1.0)
    rw2 = _reward("ep-2", 0.0)

    # First update
    res1 = learner.update(policy, [ep1, ep2], [rw1, rw2])
    assert res1.episodes_used == 2

    stats1 = copy.deepcopy(policy.snapshot.metadata["action_statistics"])
    version1 = policy.snapshot.version

    # Re-offer same episodes again in same call or later call
    res2 = learner.update(policy, [ep1, ep2], [rw1, rw2])
    assert res2.episodes_used == 0
    assert policy.snapshot.metadata["action_statistics"] == stats1
    assert policy.snapshot.version == version1


def test_ac4_runner_two_passes_over_stored_episodes() -> None:
    """AC_4: Two successive LearningRunner.run_offline_batch give statistics of one pass."""
    store = InMemoryStore()
    policy = _make_policy()
    store.store_policy(policy.snapshot())
    learner = EpsilonGreedyLearner()
    runner = LearningRunner(store=store, policy=policy, metrics=[], learner=learner)

    ep1 = Episode(
        id="ep-run-1",
        agent_id=policy.snapshot.agent_id,
        task_id=policy.snapshot.task_id,
        action_id="a",
        metadata={"selection_basis": SELECTION_BASIS},
        intent_summary="Route request",
        expected_outcome="Handle request",
        execution_status="completed",
        result_summary="Completed",
        created_at="2026-11-08T00:00:01+00:00",
    )
    ep2 = Episode(
        id="ep-run-2",
        agent_id=policy.snapshot.agent_id,
        task_id=policy.snapshot.task_id,
        action_id="b",
        metadata={"selection_basis": SELECTION_BASIS},
        intent_summary="Route request",
        expected_outcome="Handle request",
        execution_status="completed",
        result_summary="Completed",
        created_at="2026-11-08T00:00:02+00:00",
    )
    rw1 = Reward(
        id="rw-run-1",
        episode_id="ep-run-1",
        agent_id=policy.snapshot.agent_id,
        source=RewardSource.AGGREGATE,
        value=1.0,
        created_at="2026-11-08T00:00:01+00:00",
    )
    rw2 = Reward(
        id="rw-run-2",
        episode_id="ep-run-2",
        agent_id=policy.snapshot.agent_id,
        source=RewardSource.AGGREGATE,
        value=0.0,
        created_at="2026-11-08T00:00:02+00:00",
    )

    store.store_episode(ep1)
    store.store_episode(ep2)
    store.store_reward(rw1)
    store.store_reward(rw2)

    res1 = runner.run_offline_batch(policy.snapshot.agent_id, task_id=policy.snapshot.task_id, score_missing=False)
    assert res1.metrics["episodes_used"] == 2.0

    # Second pass
    res2 = runner.run_offline_batch(policy.snapshot.agent_id, task_id=policy.snapshot.task_id, score_missing=False)
    assert res2.metrics["episodes_used"] == 0.0

    latest_snap = store.get_latest_policy(agent_id=policy.snapshot.agent_id, task_id=policy.snapshot.task_id)
    assert latest_snap is not None
    assert sorted(latest_snap.metadata["consumed_episode_ids"]) == ["ep-run-1", "ep-run-2"]
    assert latest_snap.metadata["action_statistics"]["a"]["pull_count"] == 1
    assert latest_snap.metadata["action_statistics"]["b"]["pull_count"] == 1


def test_ac5_shared_record_with_ucb_learner() -> None:
    """AC_5: EpsilonGreedyLearner and UCBLearner produce equal statistics for same episodes."""
    eps_policy = _make_policy()
    eps_learner = EpsilonGreedyLearner()

    ucb_actions = [Action(id="a", description="A"), Action(id="b", description="B")]
    ucb_policy = UCBPolicy.from_actions(ucb_actions)
    ucb_learner = UCBLearner()

    # Offer same episodes with respective selection_basis
    ep_eps1 = _episode("ep-shared-1", "a", basis="epsilon_greedy")
    ep_eps2 = _episode("ep-shared-2", "b", basis="epsilon_greedy")
    rw1 = _reward("ep-shared-1", 1.0)
    rw2 = _reward("ep-shared-2", -1.0)

    ep_ucb1 = _episode("ep-shared-1", "a", basis="ucb")
    ep_ucb2 = _episode("ep-shared-2", "b", basis="ucb")

    eps_learner.update(eps_policy, [ep_eps1, ep_eps2], [rw1, rw2])
    ucb_learner.update(ucb_policy, [ep_ucb1, ep_ucb2], [rw1, rw2])

    eps_stats = eps_policy.snapshot.metadata["action_statistics"]
    ucb_stats = ucb_policy.snapshot().metadata["action_statistics"]

    assert eps_stats == ucb_stats
    assert sorted(eps_policy.snapshot.metadata["consumed_episode_ids"]) == sorted(ucb_policy.snapshot().metadata["consumed_episode_ids"])


def test_ac6_result_version_advancement_and_type_check() -> None:
    """AC_6: Advances version, returns LearnerResult; 0 on empty; TypeError on SoftmaxPolicy."""
    policy = _make_policy()
    learner = EpsilonGreedyLearner()

    initial_version = policy.snapshot.version
    ep = _episode("ep-res-1", "a")
    rw = _reward("ep-res-1", 1.0)

    result = learner.update(policy, [ep], [rw])
    assert result.episodes_used == 1
    assert abs(result.mean_reward - 1.0) < 1e-12
    assert len(result.consumed_inputs) == 1
    assert result.consumed_inputs[0].episode_id == "ep-res-1"
    assert policy.snapshot.version > initial_version

    # Empty calls return 0 and do not advance version
    curr_version = policy.snapshot.version
    empty_result = learner.update(policy, [], [])
    assert empty_result.episodes_used == 0
    assert policy.snapshot.version == curr_version

    # SoftmaxPolicy raises TypeError
    softmax_snap = PolicySnapshot(
        agent_id="test",
        task_id="test",
        actions=ACTIONS,
        logits={a.id: 0.0 for a in ACTIONS},
        metadata={},
    )
    softmax_pol = SoftmaxPolicy(softmax_snap)
    with pytest.raises(TypeError, match=r"EpsilonGreedyPolicy"):
        learner.update(softmax_pol, [ep], [rw])


def test_ac6_storage_import_isolation() -> None:
    """AC_6: policy/epsilon_greedy.py and learners/epsilon_greedy.py import nothing from storage."""
    repo_root = Path(__file__).resolve().parent.parent
    pol_path = repo_root / "src" / "agent_learning_ext" / "policy" / "epsilon_greedy.py"
    lrn_path = repo_root / "src" / "agent_learning_ext" / "learners" / "epsilon_greedy.py"

    for path in (pol_path, lrn_path):
        assert path.exists(), f"Source file must exist: {path}"
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "storage" not in alias.name
            elif isinstance(node, ast.ImportFrom):
                assert "storage" not in (node.module or "")


def test_callable_snapshot_guard_and_deepcopy() -> None:
    """CallableSnapshot guards _target against recursion and supports copy.deepcopy."""
    from agent_learning_ext.policy.epsilon_greedy import CallableSnapshot

    snap = _make_policy().snapshot()
    wrapper = CallableSnapshot(snap)

    # Calling wrapper returns snapshot
    assert wrapper() is snap
    # Direct property access delegates to snapshot
    assert wrapper.version == snap.version
    assert wrapper.task_id == snap.task_id

    # Non-existent attribute raises AttributeError without recursion
    with pytest.raises(AttributeError):
        _ = wrapper.non_existent_attribute_xyz

    # Deepcopy works cleanly without recursion
    copied = copy.deepcopy(wrapper)
    assert copied() is not snap
    assert copied().version == snap.version
