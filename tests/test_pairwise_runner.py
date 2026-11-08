"""Contract tests for Story 18.5: Pairwise Preference Optimization Through the Runner (ADR-018, Epic 18).

Interpretations from Pre-Flight Spec Gate (spec-18_5-f26b87c5):
- [I1] Upstream Fork Purity (Invariant 6): Specification references upstream path
  'src/agent_learning/learners/pairwise.py'. Per Invariant 6, all custom classes,
  learners, and helpers must be created under 'src/agent_learning_ext/learners/pairwise.py'
  (or 'agent-training-ext/'), leaving the upstream 'src/agent_learning/' tree completely pristine.
- [I2] Storage Decoupling & Serialization Round-Trip: All policy snapshots and episode
  metadata modifications must survive standard json.dumps() and json.loads() round-tripping
  without custom decoders, and the learner module must not import anything from agent_learning.storage.

Acceptance Criteria covered:
- AC_0 (Runs): TrainingRunner(learner=PairwiseLearner()) over a store that holds override
  episodes completes run_offline_batch with a SUCCEEDED run whose algorithm is PairwiseLearner.
- AC_1 (Twice): two successive run_offline_batch runs over the same stored episodes leave
  the logits as after the first within 1e-12 tolerance.
- AC_2 (Episodes Untouched): the stored episodes are equal to their earlier copies after the run.
- AC_3 (Audit Replay): the audit replay of such a run reports insufficient lineage and does not raise;
  the test asserts this and its docstring names FDD-018 §7 item 2.
- AC_4 (Empty Store & Non-Finite Guard): running over a store with 0 pairs or an empty batch
  returns a SUCCEEDED run with 0 episodes used, leaving policy logits unchanged; non-finite
  float parameters (NaN / Inf) raise ValueError.
"""

from __future__ import annotations

import copy
import math
from collections.abc import Sequence

import pytest

from agent_learning.policy import SoftmaxPolicy
from agent_learning.storage.memory import InMemoryStore
from agent_learning.types import Action, Episode, PolicySnapshot, TrainingStatus
from agent_learning_ext import PairwiseLearner, TrainingRunner
from agent_learning_ext.audit import AuditStatus, audit_run


def _make_policy(
    actions: Sequence[str],
    logits: dict[str, float] | None = None,
    max_logit_abs: float = 10.0,
    agent_id: str = "agent",
    task_id: str = "task",
) -> SoftmaxPolicy:
    action_objs = [Action(id=a, description=f"Action {a}") for a in actions]
    init_logits = dict(logits) if logits is not None else {a: 0.0 for a in actions}
    snap = PolicySnapshot(
        agent_id=agent_id,
        task_id=task_id,
        version=1,
        actions=action_objs,
        logits=init_logits,
    )
    return SoftmaxPolicy(snap, max_logit_abs=max_logit_abs)


def _make_episode(
    ep_id: str,
    action_id: str,
    feedback_status: str,
    correct_action_id: str | None = None,
    agent_id: str = "agent",
    task_id: str = "task",
) -> Episode:
    metadata: dict[str, object] = {"feedback_status": feedback_status}
    if correct_action_id is not None:
        metadata["correct_action_id"] = correct_action_id
    return Episode(
        id=ep_id,
        agent_id=agent_id,
        task_id=task_id,
        action_id=action_id,
        user_input="test prompt",
        assistant_output="test output",
        intent_summary="Test intent",
        expected_outcome="Test expected outcome",
        execution_status="completed",
        result_summary="Test result summary",
        metadata=metadata,
    )


def test_ac0_runner_completes_succeeded_run_with_algorithm_name():
    """AC_0: TrainingRunner(learner=PairwiseLearner()) runs run_offline_batch with SUCCEEDED status and PairwiseLearner algorithm."""
    actions = ["x", "y", "z"]
    store = InMemoryStore()
    policy = _make_policy(actions)
    store.store_policy(policy.snapshot())

    # Store override episodes
    ep1 = _make_episode("ep-1", "y", "rejected", "x")
    ep2 = _make_episode("ep-2", "z", "rejected", "y")
    store.store_episode(ep1)
    store.store_episode(ep2)

    runner = TrainingRunner(store=store, policy=policy, metrics=[], learner=PairwiseLearner())
    run = runner.run_offline_batch("agent", task_id="task", score_missing=False)

    assert run.status == TrainingStatus.SUCCEEDED
    assert run.algorithm == "PairwiseLearner"
    assert run.metrics["episodes_used"] == 2
    assert run.metrics["extra"]["pairs"] == 2
    assert run.output_policy_id is not None
    assert run.consumed_inputs is None


def test_ac1_two_successive_runs_leave_logits_as_after_the_first():
    """AC_1: Two successive run_offline_batch runs over the same stored episodes leave logits as after the first within 1e-12."""
    actions = ["x", "y", "z"]
    store = InMemoryStore()
    policy = _make_policy(actions, logits={"x": 0.0, "y": 0.0, "z": 0.0})
    store.store_policy(policy.snapshot())

    ep1 = _make_episode("ep-1", "y", "rejected", "x")
    ep2 = _make_episode("ep-2", "z", "rejected", "y")
    store.store_episode(ep1)
    store.store_episode(ep2)

    runner = TrainingRunner(store=store, policy=policy, metrics=[], learner=PairwiseLearner())

    run1 = runner.run_offline_batch("agent", task_id="task", score_missing=False)
    assert run1.status == TrainingStatus.SUCCEEDED
    logits_after_first = dict(policy.snapshot().logits)

    run2 = runner.run_offline_batch("agent", task_id="task", score_missing=False)
    assert run2.status == TrainingStatus.SUCCEEDED
    logits_after_second = dict(policy.snapshot().logits)

    for a in actions:
        assert abs(logits_after_second[a] - logits_after_first[a]) <= 1e-12
        assert math.isclose(logits_after_second[a], logits_after_first[a], rel_tol=0.0, abs_tol=1e-12)


def test_ac2_stored_episodes_are_untouched_after_run():
    """AC_2: Stored episodes are equal to their earlier copies after the run."""
    actions = ["x", "y", "z"]
    store = InMemoryStore()
    policy = _make_policy(actions)
    store.store_policy(policy.snapshot())

    ep1 = _make_episode("ep-1", "y", "rejected", "x")
    ep2 = _make_episode("ep-2", "z", "rejected", "y")

    store.store_episode(ep1)
    store.store_episode(ep2)
    ep1_copy = copy.deepcopy(store.get_episode("ep-1", "agent"))
    ep2_copy = copy.deepcopy(store.get_episode("ep-2", "agent"))

    runner = TrainingRunner(store=store, policy=policy, metrics=[], learner=PairwiseLearner())
    runner.run_offline_batch("agent", task_id="task", score_missing=False)

    stored_ep1 = store.get_episode("ep-1", "agent")
    stored_ep2 = store.get_episode("ep-2", "agent")

    assert stored_ep1 == ep1_copy
    assert stored_ep2 == ep2_copy


def test_ac3_audit_replay_reports_insufficient_lineage_and_does_not_raise():
    """AC_3: The audit replay of such a run reports insufficient lineage and does not raise (FDD-018 §7 item 2)."""
    actions = ["x", "y", "z"]
    store = InMemoryStore()
    policy = _make_policy(actions)
    store.store_policy(policy.snapshot())

    ep1 = _make_episode("ep-1", "y", "rejected", "x")
    store.store_episode(ep1)

    runner = TrainingRunner(store=store, policy=policy, metrics=[], learner=PairwiseLearner())
    run = runner.run_offline_batch("agent", task_id="task", score_missing=False)

    # audit_run must NOT raise an exception and must report INSUFFICIENT_LINEAGE
    report = audit_run(store, "agent", run.id)
    assert report.status == AuditStatus.INSUFFICIENT_LINEAGE
    assert report.reason_code in ("unsupported_run", "missing_lineage", "missing_configuration")


def test_ac4_empty_store_and_non_finite_parameter_guards():
    """AC_4: Empty store returns SUCCEEDED with 0 episodes used; non-finite floats raise ValueError."""
    actions = ["x", "y", "z"]
    store = InMemoryStore()
    init_logits = {"x": 1.0, "y": 0.0, "z": -1.0}
    policy = _make_policy(actions, logits=init_logits)
    store.store_policy(policy.snapshot())

    runner = TrainingRunner(store=store, policy=policy, metrics=[], learner=PairwiseLearner())
    run = runner.run_offline_batch("agent", task_id="task", score_missing=False)

    assert run.status == TrainingStatus.SUCCEEDED
    assert run.metrics["episodes_used"] == 0
    assert policy.snapshot().logits == init_logits

    # Non-finite float parameters to PairwiseLearner raise ValueError
    with pytest.raises(ValueError, match="lam"):
        PairwiseLearner(lam=float("nan"))
    with pytest.raises(ValueError, match="lr"):
        PairwiseLearner(lr=float("inf"))
    with pytest.raises(ValueError, match="clamp"):
        PairwiseLearner(clamp=float("nan"))
    with pytest.raises(ValueError, match="tol"):
        PairwiseLearner(tol=float("-inf"))
