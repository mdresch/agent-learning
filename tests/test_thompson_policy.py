"""Contract tests for Epic 15, Story 15.2 (Posterior State in the Snapshot).

Story: docs/user-stories/epic-15-bayesian-bandit-posterior-sampling.md, Story 15.2.
ADR-015 §4.1 and §4.3; BRD-015 BRU-015-06; FDD-015 §1 item 3, §2.2, §3 item 2, §5 and D4, D7.

Interpretation I1: the story names no accessor, so the policy exposes the posterior through
``posterior()`` (a copy shaped like FDD-015 §2.2, with every action present) and the consumed ids
through ``consumed_episode_ids()`` (a copy). AC_1 "exposes those values" is asserted through them.

Interpretation I2: ``choose`` is Story 15.3, so it raises ``NotImplementedError`` here; the
abstract ``Policy.choose`` must exist for the class to be built. ``apply_update`` raises
``TypeError("use ThompsonLearner")`` (FDD-015 §3 item 5, D6) because it is abstract too.

Interpretation I3: ``from_snapshot`` does not change the snapshot it is given; the policy keeps a
copy, and ``snapshot()`` returns the posterior with every action filled in, so an action that was
missing reads as the prior and is then stored as the prior.

Interpretation I4: a value that is a ``bool``, a string or any non-number is "not finite" in the
sense of AC_2 and is refused with ``ValueError`` naming the action.
"""

from __future__ import annotations

import ast
import copy
import json
import math
from pathlib import Path

import pytest

from agent_learning.policy.thompson import PRIOR_ALPHA, PRIOR_BETA, ThompsonPolicy
from agent_learning.storage import InMemoryStore
from agent_learning.types import Action, PolicySnapshot

ACTIONS = [Action(id="a"), Action(id="b")]
THOMPSON_SOURCE = Path(__file__).resolve().parent.parent / "src" / "agent_learning" / "policy" / "thompson.py"


def _snapshot(metadata: dict) -> PolicySnapshot:
    return PolicySnapshot(
        agent_id="agent",
        task_id="task",
        actions=list(ACTIONS),
        logits={"a": 0.0, "b": 0.0},
        metadata=metadata,
    )


def _posterior(alpha: dict, beta: dict) -> dict:
    return {"posterior_parameters": {"alpha": alpha, "beta": beta}}


def test_ac0_from_actions_starts_every_action_at_the_prior() -> None:
    policy = ThompsonPolicy.from_actions(ACTIONS, agent_id="agent", task_id="task")
    snap = policy.snapshot()
    assert (PRIOR_ALPHA, PRIOR_BETA) == (1.0, 1.0)
    assert snap.metadata["posterior_parameters"] == {
        "alpha": {"a": 1.0, "b": 1.0},
        "beta": {"a": 1.0, "b": 1.0},
    }
    assert snap.logits == {"a": 0.0, "b": 0.0}
    assert snap.agent_id == "agent"
    assert snap.task_id == "task"
    assert snap.version == 0
    assert policy.posterior() == snap.metadata["posterior_parameters"]


def test_ac0_from_actions_refuses_an_empty_action_space() -> None:
    with pytest.raises(ValueError, match="at least one action"):
        ThompsonPolicy.from_actions([], agent_id="agent", task_id="task")


def test_ac1_from_snapshot_exposes_the_stored_values() -> None:
    policy = ThompsonPolicy.from_snapshot(
        _snapshot(_posterior({"a": 14, "b": 3}, {"a": 2, "b": 8}))
    )
    assert policy.posterior() == {"alpha": {"a": 14.0, "b": 3.0}, "beta": {"a": 2.0, "b": 8.0}}


def test_ac1_an_action_missing_from_the_mapping_reads_as_the_prior() -> None:
    policy = ThompsonPolicy.from_snapshot(_snapshot(_posterior({"a": 14}, {"a": 2})))
    assert policy.posterior() == {"alpha": {"a": 14.0, "b": 1.0}, "beta": {"a": 2.0, "b": 1.0}}

    no_posterior = ThompsonPolicy.from_snapshot(_snapshot({}))
    assert no_posterior.posterior() == {"alpha": {"a": 1.0, "b": 1.0}, "beta": {"a": 1.0, "b": 1.0}}


def test_ac1_from_snapshot_does_not_change_the_snapshot_it_is_given() -> None:
    snap = _snapshot(_posterior({"a": 14}, {"a": 2}))
    before = copy.deepcopy(snap.to_dict())
    policy = ThompsonPolicy.from_snapshot(snap)
    policy.posterior()["alpha"]["a"] = 99.0  # a copy: writing to it must not reach the policy
    assert snap.to_dict() == before
    assert policy.posterior()["alpha"]["a"] == 14.0


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf, 0.0, -1.0, True, "3", None])
@pytest.mark.parametrize("part", ["alpha", "beta"])
def test_ac2_a_bad_value_is_refused_naming_the_action(part: str, bad: object) -> None:
    posterior = {"alpha": {"a": 2.0, "b": 2.0}, "beta": {"a": 2.0, "b": 2.0}}
    posterior[part]["b"] = bad
    with pytest.raises(ValueError, match="b"):
        ThompsonPolicy.from_snapshot(_snapshot({"posterior_parameters": posterior}))


def test_ac2_an_action_outside_the_action_space_is_refused_naming_it() -> None:
    for part in ("alpha", "beta"):
        posterior = {"alpha": {"a": 2.0}, "beta": {"a": 2.0}}
        posterior[part]["ghost"] = 2.0
        with pytest.raises(ValueError, match="ghost"):
            ThompsonPolicy.from_snapshot(_snapshot({"posterior_parameters": posterior}))


@pytest.mark.parametrize("shape", [[1.0, 2.0], {"alpha": [1.0], "beta": {}}, {"alpha": {}, "gamma": {}}, "x"])
def test_ac2_a_posterior_of_the_wrong_shape_is_refused(shape: object) -> None:
    with pytest.raises(ValueError, match="posterior_parameters"):
        ThompsonPolicy.from_snapshot(_snapshot({"posterior_parameters": shape}))


def test_ac3_consumed_ids_survive_a_json_round_trip_unchanged() -> None:
    snap = _snapshot({**_posterior({"a": 4}, {"a": 2}), "consumed_episode_ids": ["e1", "e2"]})
    policy = ThompsonPolicy.from_snapshot(snap)
    assert policy.consumed_episode_ids() == ["e1", "e2"]

    stored = policy.snapshot()
    again = PolicySnapshot.from_dict(json.loads(json.dumps(stored.to_dict())))
    assert again.to_dict() == stored.to_dict()
    assert again.metadata["consumed_episode_ids"] == ["e1", "e2"]
    assert ThompsonPolicy.from_snapshot(again).consumed_episode_ids() == ["e1", "e2"]


def test_ac3_a_duplicate_consumed_id_is_refused_naming_it() -> None:
    snap = _snapshot({"consumed_episode_ids": ["e1", "e2", "e1"]})
    with pytest.raises(ValueError, match="e1"):
        ThompsonPolicy.from_snapshot(snap)


def test_ac3_consumed_ids_must_be_a_list_of_strings() -> None:
    for bad in ("e1", [1], [None], {"e1": 1}):
        with pytest.raises(ValueError, match="consumed_episode_ids"):
            ThompsonPolicy.from_snapshot(_snapshot({"consumed_episode_ids": bad}))


def test_ac3_from_actions_starts_with_an_empty_list() -> None:
    policy = ThompsonPolicy.from_actions(ACTIONS, agent_id="agent", task_id="task")
    assert policy.consumed_episode_ids() == []
    assert policy.snapshot().metadata["consumed_episode_ids"] == []

    policy.consumed_episode_ids().append("x")  # a copy
    assert policy.consumed_episode_ids() == []


def test_ac4_a_posterior_snapshot_survives_json_and_an_in_memory_store() -> None:
    policy = ThompsonPolicy.from_snapshot(
        _snapshot({**_posterior({"a": 14, "b": 3}, {"a": 2, "b": 8}), "consumed_episode_ids": ["e1"]})
    )
    snap = policy.snapshot()

    assert PolicySnapshot.from_dict(json.loads(json.dumps(snap.to_dict()))).to_dict() == snap.to_dict()

    store = InMemoryStore()
    store.store_policy(snap)
    loaded = store.get_policy(snap.id, snap.agent_id)
    assert loaded is not None
    assert loaded.to_dict() == snap.to_dict()
    assert ThompsonPolicy.from_snapshot(loaded).posterior() == policy.posterior()


def test_ac4_thompson_imports_no_storage_and_does_no_file_io() -> None:
    assert THOMPSON_SOURCE.is_file(), f"missing {THOMPSON_SOURCE}"
    tree = ast.parse(THOMPSON_SOURCE.read_text(encoding="utf-8"))

    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            imported.append(("." * node.level) + (node.module or ""))
    assert not [m for m in imported if "storage" in m], imported
    assert not [m for m in imported if m.split(".")[0] in {"os", "pathlib", "io", "shutil", "tempfile"}]

    called = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "open" not in called


def test_apply_update_points_at_the_learner() -> None:
    policy = ThompsonPolicy.from_actions(ACTIONS, agent_id="agent", task_id="task")
    with pytest.raises(TypeError, match="use ThompsonLearner"):
        policy.apply_update({"a": 1.0}, baseline=0.0, episodes_seen=1)


def test_the_policy_is_a_policy_with_the_action_space_in_snapshot_order() -> None:
    from agent_learning.policy import Policy

    policy = ThompsonPolicy.from_actions(ACTIONS, agent_id="agent", task_id="task")
    assert isinstance(policy, Policy)
    assert [a.id for a in policy.actions()] == ["a", "b"]


def test_the_policy_is_exported_from_the_package_roots() -> None:
    import agent_learning
    import agent_learning.policy as policy_package

    assert agent_learning.ThompsonPolicy is ThompsonPolicy
    assert policy_package.ThompsonPolicy is ThompsonPolicy
    assert "ThompsonPolicy" in agent_learning.__all__
