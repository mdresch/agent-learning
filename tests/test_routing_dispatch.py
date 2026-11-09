"""Contract tests for Story 21.6: Dispatch and Gradient Exclusion.

Governing specifications:
- ADR-021 §4.1 (Contextual Authority Ensemble Routing)
- BRD-021 (BRU-021-14)
- FDD-021 §1 item 1, §2.3, §3.9, §3.11, §4 K2, K6, §7 item 2
- Story 21.6 (docs/user-stories/epic-21-contextual-authority-ensemble-routing.md)

Acceptance Criteria:
- AC_0 (Dispatch): policy_for_route(snapshot, LOW) returns a TaskPolicy whose authority is low
  and policy_for_route(snapshot, FULL) one whose authority is full, for the same stored snapshot;
  the stored snapshot is equal to its copy afterwards.
- AC_1 (Pinned Down-Route Refused): policy_for_route for a pinned task with LOW raises ValueError.
- AC_2 (Record): the episode metadata of FDD-021 §2.3 round-trips through json.dumps and json.loads,
  holds the route, entropy, margin, reason, thresholds and bucket, and a routing_anomaly string
  only after an anomaly.
- AC_3 (Full Skipped): ReinforceLearner.update over episodes with routed_authority "full" returns
  episodes_used of 0 for them, counts them as excluded, and leaves the logits unchanged, even
  when such an episode carries a log-probability.
- AC_4 (Untagged Still Trains): an untagged episode with a log-probability and a reward is still trained
  on, and the logits equal those of a run where the full-tagged episodes are absent; an untagged
  episode with no log-probability is skipped as before.
- AC_5 (Runner Unchanged): TrainingRunner (LearningRunner) is not modified, and a run_offline_batch
  over a mixed set uses only the low-tagged and untagged episodes with log-probabilities.

Contract Interpretations (Approved Pre-Flight Spec Gate):
- I1: Upstream Fork Purity (Invariant 6): Specification references upstream path 'src/agent_learning/routing.py'.
  Per Invariant 6, all custom classes, learners, and helpers must be created under 'src/agent_learning_ext/routing.py'
  and 'src/agent_learning_ext/learners/reinforce.py', leaving the upstream 'src/agent_learning/' tree completely pristine.
- I2: Defensive None-Safety for Dictionaries: When reading or updating dictionary attributes (such as policy.metadata
  or extra), implementations must defensively guard against None values to avoid AttributeError.
- I3: Empty Collection Base Case: When passed an empty collection or when no items produce valid pairs/deltas,
  the function/learner must return a clean, unmutated state with episodes_used=0 without raising.
- I4: Non-Finite Float Rejection: All floating point configuration and logit arguments must be validated using
  math.isfinite() and raise ValueError if NaN, Inf, or -Inf is encountered.
- I5: Numerical Precision Tolerances: Contract tests comparing floating-point outcomes must use pytest.approx
  with explicit absolute tolerance (1e-9).
"""

from __future__ import annotations

import ast
import json
import math
from pathlib import Path
from typing import Any

import pytest

from agent_learning.decision import DecisionAuthority
from agent_learning.policy.softmax_bandit import SoftmaxPolicy
from agent_learning.storage.memory import InMemoryStore
from agent_learning.types import Action, Episode, PolicySnapshot, Reward, RewardSource
from agent_learning_ext.decision import TaskPolicy
from agent_learning_ext.learners.reinforce import ReinforceLearner
from agent_learning_ext.routing import (
    PINNED_FULL,
    RouteDecision,
    RoutingConfig,
    policy_for_route,
    routed_episode_metadata,
)
from agent_learning_ext.training.runner import LearningRunner

ROOT = Path(__file__).resolve().parent.parent


def _sample_snapshot(
    task_id: str = "generic-task",
    authority: str = "low",
    actions: list[str] | None = None,
) -> PolicySnapshot:
    act_list = actions or ["opt_a", "opt_b"]
    return PolicySnapshot(
        id="policy-snap-1",
        agent_id="test-agent",
        task_id=task_id,
        version=1,
        actions=[Action(id=a, description=a) for a in act_list],
        logits={a: 0.0 for a in act_list},
        metadata={"decision_authority": authority},
    )


# --- AC_0: Dispatch -----------------------------------------------------------------


def test_ac0_policy_for_route_dispatch() -> None:
    snap = _sample_snapshot(task_id="unpinned-task", authority="low")
    snap_copy_dict = json.loads(json.dumps(snap.to_dict()))

    # Route with LOW authority
    policy_low = policy_for_route(snap, DecisionAuthority.LOW)
    assert isinstance(policy_low, TaskPolicy)
    assert policy_low.authority == DecisionAuthority.LOW

    # Route with FULL authority
    policy_full = policy_for_route(snap, DecisionAuthority.FULL)
    assert isinstance(policy_full, TaskPolicy)
    assert policy_full.authority == DecisionAuthority.FULL

    # Route using string values
    policy_low_str = policy_for_route(snap, "low")
    assert policy_low_str.authority == DecisionAuthority.LOW
    policy_full_str = policy_for_route(snap, "full")
    assert policy_full_str.authority == DecisionAuthority.FULL

    # Original snapshot must remain strictly unchanged
    assert snap.to_dict() == snap_copy_dict
    assert snap.metadata.get("decision_authority") == "low"


# --- AC_1: Pinned Down-Route Refused -------------------------------------------------


@pytest.mark.parametrize("pinned_task", PINNED_FULL)
def test_ac1_pinned_down_route_refused(pinned_task: str) -> None:
    snap = _sample_snapshot(task_id=pinned_task, authority="full")
    # DOWN-routing a pinned task to LOW must raise ValueError
    with pytest.raises(ValueError, match="pinned"):
        policy_for_route(snap, DecisionAuthority.LOW)

    with pytest.raises(ValueError, match="pinned"):
        policy_for_route(snap, "low")

    # Routing to FULL is permitted
    pol_full = policy_for_route(snap, DecisionAuthority.FULL)
    assert pol_full.authority == DecisionAuthority.FULL


# --- AC_2: Record & Serialization Round-Trip ----------------------------------------


def test_ac2_routed_episode_metadata_round_trip() -> None:
    cfg = RoutingConfig(tau_esc=1.0, tau_deesc=0.7, eps_margin=0.20)
    decision_normal = RouteDecision(
        authority=DecisionAuthority.FULL,
        entropy_bits=1.2955,
        margin=0.30,
        reason="entropy",
    )
    shadow = {"shadow_low_action": "approve_plan", "shadow_entropy_bits": 1.2955}

    meta = routed_episode_metadata(
        decision=decision_normal,
        bucket="ctx-17",
        config=cfg,
        shadow=shadow,
    )

    # Must match FDD-021 §2.3 structure
    assert meta["routed_authority"] == "full"
    assert meta["routing"]["bucket"] == "ctx-17"
    assert meta["routing"]["route"] == "full"
    assert meta["routing"]["entropy_bits"] == pytest.approx(1.2955, abs=1e-9)
    assert meta["routing"]["margin"] == pytest.approx(0.30, abs=1e-9)
    assert meta["routing"]["reason"] == "entropy"
    assert meta["routing"]["thresholds"]["tau_esc"] == 1.0
    assert meta["routing"]["thresholds"]["tau_deesc"] == 0.7
    assert meta["routing"]["thresholds"]["eps_margin"] == 0.20
    assert meta["routing_anomaly"] is None
    assert meta["shadow_low_action"] == "approve_plan"
    assert meta["shadow_entropy_bits"] == pytest.approx(1.2955, abs=1e-9)

    # Round-trip through JSON
    serialized = json.dumps(meta)
    deserialized = json.loads(serialized)
    assert deserialized == meta


def test_ac2_routed_episode_metadata_with_anomaly() -> None:
    decision_anomaly = RouteDecision(
        authority=DecisionAuthority.FULL,
        entropy_bits=None,
        margin=None,
        reason="anomaly",
        anomaly="probabilities do not sum to 1.0",
    )
    meta = routed_episode_metadata(
        decision=decision_anomaly,
        bucket="ctx-17",
        config=None,
    )
    assert meta["routed_authority"] == "full"
    assert meta["routing"]["reason"] == "anomaly"
    assert meta["routing_anomaly"] == "probabilities do not sum to 1.0"
    # Round-trip through JSON
    assert json.loads(json.dumps(meta)) == meta


# --- AC_3: Full Skipped in ReinforceLearner ------------------------------------------


def test_ac3_full_routed_episodes_skipped_in_reinforce() -> None:
    actions = ["opt_a", "opt_b"]
    policy = SoftmaxPolicy(_sample_snapshot(actions=actions))
    initial_probs = policy.probabilities()

    # Create full-routed episodes that carry an action_logprob
    episodes = [
        Episode(
            id=f"ep-{i}",
            agent_id="test-agent",
            user_input="test prompt",
            assistant_output="test output",
            action_id="opt_a",
            action_logprob=-0.6931,  # has logprob!
            metadata={
                "routed_authority": "full",
                "feedback_status": "accepted",
            },
        )
        for i in range(5)
    ]
    rewards = [
        Reward(episode_id=ep.id, value=1.0, source=RewardSource.AGGREGATE)
        for ep in episodes
    ]

    learner = ReinforceLearner()
    result = learner.update(policy, episodes, rewards)

    # episodes_used must be 0
    assert result.episodes_used == 0
    # extra must record full_authority_excluded count
    assert result.extra.get("full_authority_excluded") == 5
    # policy probabilities/logits must be completely unchanged (Interpretation I5)
    updated_probs = policy.probabilities()
    for idx in range(len(actions)):
        assert updated_probs[idx] == pytest.approx(initial_probs[idx], abs=1e-9)


# --- AC_4: Untagged Still Trains ----------------------------------------------------


def test_ac4_untagged_episodes_train_normally() -> None:
    actions = ["opt_a", "opt_b"]
    policy_mixed = SoftmaxPolicy(_sample_snapshot(actions=actions))
    policy_untagged_only = SoftmaxPolicy(_sample_snapshot(actions=actions))

    # 3 untagged valid episodes
    untagged_episodes = [
        Episode(
            id=f"untagged-{i}",
            agent_id="test-agent",
            user_input="prompt",
            assistant_output="output",
            action_id="opt_a" if i % 2 == 0 else "opt_b",
            action_logprob=-0.6931,
            metadata={"feedback_status": "accepted"},
        )
        for i in range(3)
    ]
    untagged_rewards = [
        Reward(episode_id=ep.id, value=0.8, source=RewardSource.AGGREGATE)
        for ep in untagged_episodes
    ]

    # 2 full-routed episodes (should be ignored)
    full_episodes = [
        Episode(
            id=f"full-{i}",
            agent_id="test-agent",
            user_input="prompt",
            assistant_output="output",
            action_id="opt_a",
            action_logprob=-0.6931,
            metadata={"routed_authority": "full", "feedback_status": "accepted"},
        )
        for i in range(2)
    ]
    full_rewards = [
        Reward(episode_id=ep.id, value=1.0, source=RewardSource.AGGREGATE)
        for ep in full_episodes
    ]

    # 1 untagged episode without log-prob (should be ignored as before)
    unlogged_episode = Episode(
        id="unlogged-1",
        agent_id="test-agent",
        user_input="prompt",
        assistant_output="output",
        action_id="opt_a",
        action_logprob=None,
    )
    unlogged_reward = Reward(episode_id="unlogged-1", value=0.5, source=RewardSource.AGGREGATE)

    mixed_episodes = untagged_episodes + full_episodes + [unlogged_episode]
    mixed_rewards = untagged_rewards + full_rewards + [unlogged_reward]

    learner = ReinforceLearner()

    # Train on mixed set
    res_mixed = learner.update(policy_mixed, mixed_episodes, mixed_rewards)
    # Train on untagged set only
    res_clean = learner.update(policy_untagged_only, untagged_episodes, untagged_rewards)

    # Both must use exactly 3 episodes
    assert res_mixed.episodes_used == 3
    assert res_clean.episodes_used == 3
    assert res_mixed.extra.get("full_authority_excluded") == 3  # 2 full + 1 unlogged

    # Resulting probabilities must match identically (Interpretation I5)
    probs_mixed = policy_mixed.probabilities()
    probs_clean = policy_untagged_only.probabilities()
    for idx in range(len(actions)):
        assert probs_mixed[idx] == pytest.approx(probs_clean[idx], abs=1e-9)


# --- AC_5: TrainingRunner Unchanged & Offline Batch Integration ---------------------


def test_ac5_training_runner_ast_unchanged() -> None:
    """AST check: runner.py has no references to routed_authority or routing."""
    runner_file = ROOT / "src" / "agent_learning_ext" / "training" / "runner.py"
    tree = ast.parse(runner_file.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            assert "routed_authority" not in node.value, "runner.py must not reference routed_authority"
            assert "shadow_low_action" not in node.value, "runner.py must not reference shadow_low_action"


def test_ac5_learning_runner_run_offline_batch_mixed_set() -> None:
    actions = ["opt_a", "opt_b"]
    snap = _sample_snapshot(task_id="default", authority="low", actions=actions)
    policy = SoftmaxPolicy(snap)
    store = InMemoryStore()

    # 2 low-routed episodes (should train)
    low_episodes = [
        Episode(
            id=f"low-{i}",
            agent_id="test-agent",
            task_id="default",
            user_input="prompt",
            assistant_output="output",
            intent_summary="intent",
            expected_outcome="outcome",
            execution_status="success",
            result_summary="result",
            action_id="opt_a",
            action_logprob=-0.6931,
            metadata={"routed_authority": "low", "feedback_status": "accepted"},
        )
        for i in range(2)
    ]
    # 2 full-routed episodes (should be excluded)
    full_episodes = [
        Episode(
            id=f"full-{i}",
            agent_id="test-agent",
            task_id="default",
            user_input="prompt",
            assistant_output="output",
            intent_summary="intent",
            expected_outcome="outcome",
            execution_status="success",
            result_summary="result",
            action_id="opt_b",
            action_logprob=-0.6931,
            metadata={"routed_authority": "full", "feedback_status": "accepted"},
        )
        for i in range(2)
    ]
    # 2 untagged episodes with logprob (should train)
    untagged_episodes = [
        Episode(
            id=f"untagged-{i}",
            agent_id="test-agent",
            task_id="default",
            user_input="prompt",
            assistant_output="output",
            intent_summary="intent",
            expected_outcome="outcome",
            execution_status="success",
            result_summary="result",
            action_id="opt_a",
            action_logprob=-0.6931,
            metadata={"feedback_status": "accepted"},
        )
        for i in range(2)
    ]

    all_episodes = low_episodes + full_episodes + untagged_episodes
    all_rewards = [
        Reward(episode_id=ep.id, value=1.0, source=RewardSource.AGGREGATE)
        for ep in all_episodes
    ]

    for ep in all_episodes:
        store.store_episode(ep)
    for r in all_rewards:
        store.store_reward(r)

    learner = ReinforceLearner()
    runner = LearningRunner(store=store, policy=policy, learner=learner)
    run = runner.run_offline_batch(agent_id="test-agent", task_id="default")

    # Exactly 4 episodes used (2 low + 2 untagged)
    assert run.metrics.get("episodes_used") == 4
    assert run.metrics.get("extra", {}).get("full_authority_excluded") == 2
