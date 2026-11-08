"""Contract test suite for Story 18.4 — The Learner.

Source ADR: ADR-018 (Pairwise Preference Optimization for Discrete Action Logits)
Source BRD: BRD-018 (BRU-018-01, BRU-018-04, BRU-018-07, BRU-018-08, BRU-018-10)
Source FDD: FDD-018 (§2.3, §3 item 3, G4, G6, G7)
Story: Story 18.4 (The Learner)

Acceptance Criteria:
- AC_0 (Type): update given a policy that is not a SoftmaxPolicy raises TypeError; given a SoftmaxPolicy
  with max_logit_abs below 8.0 raises ValueError.
- AC_1 (Reference Frozen): the first update with a pair writes the policy's logits to
  metadata["pairwise_reference_logits"]; a second update, after the logits changed, leaves the stored
  reference unchanged; a stored reference with a missing action or a non-finite value raises ValueError.
- AC_2 (Moves To The Fit): after an update with the pairs of the base set the policy's logits equal the
  fit_logits result from theta_ref within 1e-12, and the logit_deltas of the result equal fitted - before.
- AC_3 (No Pair, No Change): with episodes that give no pair, no reference is written, the logits and the
  snapshot version are unchanged, and episodes_used is 0.
- AC_4 (Idempotent): running update a second time on the same episodes leaves the logits unchanged and
  episodes_seen unchanged.
- AC_5 (Result): the LearnerResult has episodes_used equal to the number of pairs, mean_reward 0.0,
  baseline_after equal to baseline_before, consumed_inputs of None, and in extra the keys pairs,
  skipped_episodes, converged, iterations, stationarity, step_size, loss_before, loss_after and
  reference_logits; the rewards argument is ignored even when it holds invalid values.
- AC_6 (Storage Boundary): the snapshot survives json.dumps and json.loads unchanged and round-trips
  through an in-memory store with no new record type; pairwise.py imports nothing from agent_learning.storage.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import pytest

from agent_learning.decision import Action
from agent_learning.policy import SoftmaxPolicy
from agent_learning.types import Episode, PolicySnapshot
from agent_learning_ext.learners.pairwise import (
    PairwiseLearner,
    fit_logits,
    pairs_from_episodes,
)


def _make_episode(
    ep_id: str,
    action: str,
    feedback_status: str | None = None,
    correct_action: str | None = None,
) -> Episode:
    """Helper to build Episode instances for preference testing."""
    meta: dict[str, Any] = {}
    if feedback_status is not None:
        meta["feedback_status"] = feedback_status
    if correct_action is not None:
        meta["correct_action_id"] = correct_action

    return Episode(
        id=ep_id,
        agent_id="test-agent",
        task_id="test-task",
        task_name="Test Task",
        policy_id="test-policy",
        policy_version=1,
        action_id=action,
        intent_summary="Test intent",
        user_input="test input",
        assistant_output="test output",
        created_at=datetime.now(timezone.utc),
        metadata=meta,
    )


def _make_policy(actions: list[str], logits: dict[str, float] | None = None, max_logit_abs: float = 10.0) -> SoftmaxPolicy:
    """Helper to build a SoftmaxPolicy with optional initial logits."""
    action_objs = [Action(id=a, description=f"Action {a}") for a in actions]
    snap = PolicySnapshot(
        id="test-policy",
        agent_id="test-agent",
        task_id="test-task",
        version=1,
        actions=action_objs,
        logits=dict(logits) if logits is not None else {a: 0.0 for a in actions},
    )
    return SoftmaxPolicy(snap, max_logit_abs=max_logit_abs)


def test_ac0_type_and_clamp_validation():
    """AC_0: Non-SoftmaxPolicy raises TypeError; max_logit_abs < 8.0 raises ValueError."""
    learner = PairwiseLearner()
    ep = _make_episode("ep-1", "x", "rejected", "y")

    # Non-SoftmaxPolicy object
    class DummyPolicy:
        pass

    with pytest.raises(TypeError, match="SoftmaxPolicy"):
        learner.update(DummyPolicy(), [ep])

    # SoftmaxPolicy with max_logit_abs < 8.0
    actions = ["x", "y"]
    invalid_clamp_policy = _make_policy(actions, max_logit_abs=7.9)
    with pytest.raises(ValueError, match="max_logit_abs"):
        learner.update(invalid_clamp_policy, [ep])

    # Valid clamp policy >= 8.0 succeeds
    valid_policy = _make_policy(actions, max_logit_abs=8.0)
    res = learner.update(valid_policy, [ep])
    assert res.episodes_used == 1


def test_ac1_reference_frozen_and_validated():
    """AC_1: First update freezes reference logits; subsequent updates leave reference unchanged."""
    actions = ["x", "y", "z"]
    init_logits = {"x": 1.0, "y": -0.5, "z": 0.0}
    policy = _make_policy(actions, logits=init_logits, max_logit_abs=10.0)
    learner = PairwiseLearner()

    ep1 = _make_episode("ep-1", "x", "rejected", "y")
    learner.update(policy, [ep1])

    # Reference frozen in metadata
    stored_ref = policy.snapshot().metadata.get("pairwise_reference_logits")
    assert stored_ref is not None
    assert stored_ref == init_logits

    # Second update with different episode: stored reference must NOT change
    ep2 = _make_episode("ep-2", "y", "rejected", "z")
    learner.update(policy, [ep2])
    assert policy.snapshot().metadata.get("pairwise_reference_logits") == init_logits

    # Missing action in stored reference raises ValueError
    bad_ref_policy = _make_policy(actions, max_logit_abs=10.0)
    bad_ref_policy._snapshot.metadata["pairwise_reference_logits"] = {"x": 1.0, "y": 0.0}  # missing z
    with pytest.raises(ValueError, match="action"):
        learner.update(bad_ref_policy, [ep1])

    # Non-finite value in stored reference raises ValueError
    nan_ref_policy = _make_policy(actions, max_logit_abs=10.0)
    nan_ref_policy._snapshot.metadata["pairwise_reference_logits"] = {"x": float("nan"), "y": 0.0, "z": 0.0}
    with pytest.raises(ValueError, match="finite"):
        learner.update(nan_ref_policy, [ep1])


def test_ac2_moves_to_the_fit_exactly():
    """AC_2: After update with base set, policy logits equal fit_logits result within 1e-12."""
    actions = ["x", "y", "z"]
    init_logits = {"x": 0.3, "y": -0.2, "z": 0.1}
    policy = _make_policy(actions, logits=init_logits, max_logit_abs=10.0)
    learner = PairwiseLearner(lam=0.05, lr=0.1, steps=2000)

    # Base set: 2 x > y, 1 y > z
    episodes = [
        _make_episode("ep-1", "y", "rejected", "x"),
        _make_episode("ep-2", "y", "rejected", "x"),
        _make_episode("ep-3", "z", "rejected", "y"),
    ]
    pairs = pairs_from_episodes(episodes, actions)

    # Expected fit directly from fit_logits
    expected_fit = fit_logits(pairs, actions, init_logits, lam=0.05, lr=0.1, steps=2000)

    res = learner.update(policy, episodes)

    # Check policy logits equal fitted logits within 1e-12
    snap = policy.snapshot()
    for a in actions:
        assert abs(snap.logits[a] - expected_fit.logits[a]) < 1e-12

    # Check logit deltas equal fitted - before
    for a in actions:
        assert abs(res.logit_deltas[a] - (expected_fit.logits[a] - init_logits[a])) < 1e-12


def test_ac3_no_pairs_leaves_policy_untouched():
    """AC_3: Zero pairs leaves reference unwritten, logits unchanged, version unchanged, episodes_used=0."""
    actions = ["x", "y", "z"]
    init_logits = {"x": 1.0, "y": 2.0, "z": -1.0}
    policy = _make_policy(actions, logits=init_logits)
    learner = PairwiseLearner()

    # Accepted episodes give no preference pairs
    episodes = [
        _make_episode("ep-1", "x", "accepted"),
        _make_episode("ep-2", "y", "accepted"),
    ]

    res = learner.update(policy, episodes)
    snap = policy.snapshot()
    assert res.episodes_used == 0
    assert "pairwise_reference_logits" not in snap.metadata
    assert snap.version == 1
    assert snap.logits == init_logits
    assert res.logit_deltas == {}


def test_ac4_idempotent_repeated_update():
    """AC_4: Running update a second time on the same episodes leaves logits and episodes_seen unchanged."""
    actions = ["x", "y", "z"]
    policy = _make_policy(actions)
    learner = PairwiseLearner()

    episodes = [
        _make_episode("ep-1", "y", "rejected", "x"),
        _make_episode("ep-2", "z", "rejected", "y"),
    ]

    learner.update(policy, episodes)
    snap1 = policy.snapshot()
    logits_after_first = dict(snap1.logits)
    seen_after_first = snap1.episodes_seen

    # Second run on exact same episodes
    res2 = learner.update(policy, episodes)
    snap2 = policy.snapshot()
    assert snap2.logits == logits_after_first
    assert snap2.episodes_seen == seen_after_first
    for delta in res2.logit_deltas.values():
        assert abs(delta) < 1e-12


def test_ac5_learner_result_contract_and_rewards_ignored():
    """AC_5: LearnerResult has episodes_used, mean_reward=0, baseline unchanged, consumed_inputs=None, extra keys."""
    actions = ["x", "y"]
    policy = _make_policy(actions)
    learner = PairwiseLearner()

    episodes = [
        _make_episode("ep-1", "y", "rejected", "x"),
        _make_episode("ep-2", "x", "accepted"),
    ]
    # Pass invalid / negative / non-finite rewards: must be safely ignored
    bad_rewards = [-999.0, float("nan")]

    res = learner.update(policy, episodes, rewards=bad_rewards)
    assert res.episodes_used == 1  # only 1 rejected episode yielded a pair
    assert res.mean_reward == 0.0
    assert res.baseline_after == res.baseline_before
    assert res.consumed_inputs is None

    # Required extra metadata keys
    required_keys = {
        "pairs",
        "skipped_episodes",
        "converged",
        "iterations",
        "stationarity",
        "step_size",
        "loss_before",
        "loss_after",
        "reference_logits",
    }
    assert required_keys.issubset(res.extra.keys())
    assert res.extra["pairs"] == 1
    assert res.extra["skipped_episodes"] == 1
    assert isinstance(res.extra["converged"], bool)
    assert isinstance(res.extra["reference_logits"], dict)


def test_ac6_storage_boundary_and_purity():
    """AC_6: Snapshot survives JSON round-trip; pairwise.py imports nothing from agent_learning.storage."""
    import agent_learning_ext.learners.pairwise as pw_module

    # Must import nothing from storage
    assert "storage" not in pw_module.__dict__
    for attr in dir(pw_module):
        obj = getattr(pw_module, attr)
        if hasattr(obj, "__module__") and obj.__module__:
            assert not obj.__module__.startswith("agent_learning.storage")

    # Snapshot with reference metadata survives JSON round-trip
    actions = ["x", "y"]
    policy = _make_policy(actions)
    learner = PairwiseLearner()
    learner.update(policy, [_make_episode("ep-1", "y", "rejected", "x")])

    snap = policy.snapshot()
    serialized = json.dumps(snap.to_dict())
    deserialized = json.loads(serialized)
    restored_snap = PolicySnapshot.from_dict(deserialized)

    assert restored_snap.id == snap.id
    assert restored_snap.metadata["pairwise_reference_logits"] == snap.metadata["pairwise_reference_logits"]
    assert restored_snap.logits == snap.logits
