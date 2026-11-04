"""Contract tests for Story 20.4: No Borrowed Evidence.

Governing specifications:
- User Story: docs/user-stories/epic-20-explicit-policy-prior-warm-starting.md (Story 20.4)
- Architecture: docs/adr/ADR-020-explicit-policy-prior-warm-starting.md
- Business Requirements: docs/project-docs/Business-Requirements/BRD-020-explicit-policy-prior-warm-starting.md
- Functional Design: docs/project-docs/Functional-Design/FDD-020-explicit-policy-prior-warm-starting.md

Acceptance Criteria:
- AC_0 (Gate Unchanged): after a warm start the target, with no episodes, is not eligible under
  assess_autonomy with the thresholds of its own tier, and its episodes_seen is 0.
- AC_1 (Donor Gate Recorded): warm_start_donor_gate_met is true when the donor meets the standard tier
  gate in the test and false when it does not, and in both cases the copy proceeds.
- AC_2 (Decoupled): after the target's logits are changed by a later update, which stores a further
  version of the target, the donor snapshot and its episodes are equal to their copies from before
  the warm start.

Interpretation I1: "the thresholds of its own tier" is read for every tier (low, standard, high, critical),
because the target carries no tier of its own; the check holds for all of them.
Interpretation I2: the donor that meets the gate is built the way tests/test_meta_prior_store.py builds a
member (three stable snapshots and 40 scored outcomes); the donor that does not has five outcomes.
Everything here is synthetic.
"""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path

import pytest

from agent_learning import cli
from agent_learning.autonomy import assess_autonomy
from agent_learning.config import AutonomyConfig
from agent_learning.storage.local import LocalFileStore
from agent_learning.types import Action, Episode, PolicySnapshot, Reward, RewardSource

AGENT = "test-agent"
TIERS = ("low", "standard", "high", "critical")
ACTION_MAP = json.dumps({"accept": "approve", "decline": "reject", "ask": "escalate"})


@pytest.fixture(autouse=True)
def _clear_autonomy_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in list(os.environ):
        if name.startswith("AGENT_LEARNING_AUTONOMY_"):
            monkeypatch.delenv(name)


@pytest.fixture
def store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> LocalFileStore:
    local = LocalFileStore(tmp_path / "store")
    monkeypatch.setattr(cli, "get_default_store", lambda: local)
    return local


def _donor(store: LocalFileStore, outcomes: int) -> PolicySnapshot:
    """The base donor with three stable snapshots and `outcomes` scored outcomes (I2)."""
    last = None
    for version in range(1, 4):
        last = PolicySnapshot(
            id=f"donor-v{version}",
            agent_id=AGENT,
            task_id="donor-task",
            version=version,
            actions=[Action(id="approve"), Action(id="reject"), Action(id="escalate")],
            logits={"approve": 2.0, "reject": -1.0, "escalate": 0.0},
            episodes_seen=version * 20,
            updates_applied=version,
            metadata={"policy_scope": "delegated_decision", "decision_authority": "low"},
        )
        store.store_policy(last)
    for index in range(outcomes):
        episode = Episode(
            id=f"donor-episode-{index}",
            agent_id=AGENT,
            task_id="donor-task",
            intent_summary="Decide",
            action_id="approve",
            expected_outcome="Correct decision",
            execution_status="completed",
            result_summary="The outcome supported the decision",
            metadata={"correct_action_id": "approve", "task_completed": True},
        )
        store.store_episode(episode)
        store.store_reward(Reward(episode_id=episode.id, agent_id=AGENT, source=RewardSource.AGGREGATE, value=0.7))
    assert last is not None
    return last


def _target(store: LocalFileStore) -> PolicySnapshot:
    snapshot = PolicySnapshot(
        id="target-v0",
        agent_id=AGENT,
        task_id="target-task",
        version=0,
        actions=[Action(id="accept"), Action(id="decline"), Action(id="ask")],
        logits={"accept": 0.0, "decline": 0.0, "ask": 0.0},
        metadata={"policy_scope": "delegated_decision", "decision_authority": "low"},
    )
    store.store_policy(snapshot)
    return snapshot


def _warm_start() -> int:
    return cli.main(
        ["task-policy-warm-start", "--agent-id", AGENT, "--target-task-id", "target-task",
         "--donor-task-id", "donor-task", "--action-map", ACTION_MAP]
    )


def test_ac0_the_warm_started_target_is_not_eligible_under_any_tier(store: LocalFileStore) -> None:
    _donor(store, outcomes=40)
    _target(store)
    assert _warm_start() == 0

    target = store.get_active_policy(AGENT, "target-task")
    assert target is not None and target.version == 1
    assert target.logits == pytest.approx({"accept": 1.4, "decline": -0.7, "ask": 0.0})
    assert target.episodes_seen == 0
    for tier in TIERS:
        assessment = assess_autonomy(store, target, config=AutonomyConfig.for_tier(tier))
        assert assessment.eligible is False, f"borrowed logits made the target eligible on tier {tier}"


def test_ac1_the_donor_gate_is_recorded_true_when_the_donor_meets_it(store: LocalFileStore) -> None:
    donor = _donor(store, outcomes=40)
    _target(store)
    assert assess_autonomy(store, donor, config=AutonomyConfig.for_tier("standard")).eligible is True

    assert _warm_start() == 0
    target = store.get_active_policy(AGENT, "target-task")
    assert target is not None
    assert target.metadata["warm_start_donor_gate_met"] is True


def test_ac1_the_donor_gate_is_recorded_false_and_the_copy_proceeds(store: LocalFileStore) -> None:
    donor = _donor(store, outcomes=5)
    _target(store)
    assert assess_autonomy(store, donor, config=AutonomyConfig.for_tier("standard")).eligible is False

    assert _warm_start() == 0
    target = store.get_active_policy(AGENT, "target-task")
    assert target is not None
    assert target.metadata["warm_start_donor_gate_met"] is False
    assert target.logits == pytest.approx({"accept": 1.4, "decline": -0.7, "ask": 0.0})


def test_ac2_a_later_update_of_the_target_leaves_the_donor_alone(store: LocalFileStore) -> None:
    donor = _donor(store, outcomes=40)
    _target(store)
    donor_before = donor.to_dict()
    episodes_before = [e.to_dict() for e in store.query_episodes(AGENT, task_id="donor-task", limit=10_000)]
    assert len(episodes_before) == 40

    assert _warm_start() == 0
    target = store.get_active_policy(AGENT, "target-task")
    assert target is not None

    later = PolicySnapshot.from_dict(copy.deepcopy(target.to_dict()))
    later.logits = {"accept": 0.2, "decline": 0.9, "ask": -0.1}
    later.episodes_seen = 3
    later.updates_applied = 1
    later.advance_version()
    store.store_policy(later)

    active = store.get_active_policy(AGENT, "target-task")
    assert active is not None and active.version == 2
    assert active.logits == {"accept": 0.2, "decline": 0.9, "ask": -0.1}

    donor_after = store.get_active_policy(AGENT, "donor-task")
    assert donor_after is not None and donor_after.to_dict() == donor_before
    episodes_after = [e.to_dict() for e in store.query_episodes(AGENT, task_id="donor-task", limit=10_000)]
    assert episodes_after == episodes_before
