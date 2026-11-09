"""Story 17.2 — The Safety Mask (ADR-017, BRD-017, FDD-017).

Acceptance Criteria:
  AC_0 (Safe Subset): On the base policy the safe subset is {a, b}; an action without
       the key, or with "reversible": false, is not safe.
  AC_1 (Boolean Only): "reversible": "true", 1, null or a list raises ValueError
       naming the action, both when the policy is built and when a snapshot is read.
  AC_2 (Empty Subset): With no safe action the rate applied is 0.0 for every t,
       including t = 0.
  AC_3 (Existing Definitions): A policy built from the actions of
       docs/policy-shapes/approve-adr.actions.json has an empty safe subset and
       a rate applied of 0.0.

Contract Interpretations (derived via scripts/spec_gate.py):
  I1 (Upstream Fork Purity): All implementations reside in src/agent_learning_ext/,
      leaving upstream src/agent_learning/ pristine.
  I2 (Storage Decoupling & Serialization Round-Trip): All policy snapshots survive
      standard json.dumps() and json.loads() round-tripping.
  I3 (Non-Finite Float Rejection): Schedule arguments are strictly validated.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from agent_learning.types import Action, PolicySnapshot
from agent_learning_ext.policy.epsilon_greedy import EpsilonGreedyPolicy


def make_base_actions() -> list[Action]:
    """Base policy action fixture: a and b reversible, c has no flag."""
    return [
        Action(id="a", description="Action A", parameters={"reversible": True}),
        Action(id="b", description="Action B", parameters={"reversible": True}),
        Action(id="c", description="Action C", parameters={}),
    ]


def test_ac0_safe_subset_base_policy() -> None:
    """AC_0: Safe subset on base policy is {a, b}; no-flag or reversible=False are not safe."""
    actions = [
        Action(id="a", description="Action A", parameters={"reversible": True}),
        Action(id="b", description="Action B", parameters={"reversible": True}),
        Action(id="c", description="Action C", parameters={}),
        Action(id="d", description="Action D", parameters={"reversible": False}),
    ]
    policy = EpsilonGreedyPolicy.from_actions(
        actions,
        eps0=0.5,
        delta=0.05,
        floor=0.05,
    )

    assert policy.safe_subset == {"a", "b"}
    assert [a.id for a in policy.safe_actions] == ["a", "b"]
    assert "c" not in policy.safe_subset
    assert "d" not in policy.safe_subset


@pytest.mark.parametrize(
    "invalid_val",
    ["true", "false", 1, 0, None, [True], {"rev": True}],
)
def test_ac1_boolean_only_validation_from_actions(invalid_val: Any) -> None:
    """AC_1: Non-boolean reversible values raise ValueError naming the action in from_actions."""
    actions = [
        Action(id="action_bad", description="Bad", parameters={"reversible": invalid_val}),
    ]
    with pytest.raises(ValueError, match=r"(?i)\baction_bad\b"):
        EpsilonGreedyPolicy.from_actions(
            actions,
            eps0=0.5,
            delta=0.05,
            floor=0.05,
        )


@pytest.mark.parametrize(
    "invalid_val",
    ["true", "false", 1, 0, None, [True], {"rev": True}],
)
def test_ac1_boolean_only_validation_from_snapshot(invalid_val: Any) -> None:
    """AC_1: Non-boolean reversible values raise ValueError naming the action in from_snapshot."""
    snapshot = PolicySnapshot(
        agent_id="test",
        task_id="test",
        actions=[
            Action(id="action_bad_snap", description="Bad", parameters={"reversible": invalid_val}),
        ],
        logits={"action_bad_snap": 0.0},
        metadata={
            "policy_type": "epsilon_greedy",
            "epsilon_schedule": {"eps0": 0.5, "delta": 0.05, "floor": 0.05},
            "action_statistics": {
                "action_bad_snap": {"pull_count": 0, "cumulative_reward": 0.0, "mean_reward": 0.0},
            },
            "consumed_episode_ids": [],
        },
    )
    with pytest.raises(ValueError, match=r"(?i)\baction_bad_snap\b"):
        EpsilonGreedyPolicy.from_snapshot(snapshot)


def test_ac2_empty_safe_subset_rate_is_zero() -> None:
    """AC_2: With no safe action the rate applied is 0.0 for every t, including t = 0."""
    actions = [
        Action(id="c", description="Action C", parameters={}),
        Action(id="d", description="Action D", parameters={"reversible": False}),
    ]
    policy = EpsilonGreedyPolicy.from_actions(
        actions,
        eps0=0.5,
        delta=0.05,
        floor=0.05,
    )

    assert policy.safe_subset == set()
    assert policy.safe_actions == []

    for t in (0, 1, 10, 100, 1000):
        assert policy.exploration_rate_applied(t) == 0.0
        assert policy.rate_applied(t) == 0.0


def test_ac3_existing_definitions_approve_adr() -> None:
    """AC_3: Policy built from approve-adr.actions.json has empty safe subset and rate 0.0."""
    actions_path = Path("docs/policy-shapes/approve-adr.actions.json")
    assert actions_path.is_file(), f"Missing actions fixture at {actions_path}"

    with actions_path.open("r", encoding="utf-8") as f:
        raw_actions = json.load(f)

    actions = [Action.from_dict(d) for d in raw_actions]
    assert len(actions) == 3

    policy = EpsilonGreedyPolicy.from_actions(
        actions,
        eps0=0.5,
        delta=0.05,
        floor=0.05,
    )

    assert policy.safe_subset == set()
    assert policy.safe_actions == []
    for t in (0, 1, 20, 180, 1000):
        assert policy.exploration_rate_applied(t) == 0.0
        assert policy.rate_applied(t) == 0.0


def test_i2_snapshot_json_round_trip() -> None:
    """I2: Policy snapshot survives json.dumps and json.loads without loss."""
    actions = make_base_actions()
    policy = EpsilonGreedyPolicy.from_actions(
        actions,
        eps0=0.5,
        delta=0.05,
        floor=0.05,
    )

    snap_dict = policy.snapshot.to_dict()
    serialized = json.dumps(snap_dict)
    deserialized = json.loads(serialized)
    restored_snap = PolicySnapshot.from_dict(deserialized)
    restored_policy = EpsilonGreedyPolicy.from_snapshot(restored_snap)

    assert restored_policy.safe_subset == {"a", "b"}
    assert restored_policy.snapshot.metadata == policy.snapshot.metadata
