"""Contract tests for Epic 17, Story 17.6 (The Positive-Only Baseline Run, HYP-AL-009 / BRU-017-13).

Story: docs/user-stories/epic-17-scheduled-epsilon-greedy-policy.md, Story 17.6.
ADR-017 §4.3 and Test Data; BRD-017 BRU-017-03, BRU-017-13; FDD-017 §3 item 8.

What this is: a baseline run on a real, positive-only history. The approve-* episodes of
agent-learning-governance in docs/policy-shapes/episodes/ were all accepted, so each is
replayed as r = 1.0 (mapped to 1.0) for the action taken, through EpsilonGreedyLearner
and EpsilonGreedyPolicy. Because existing governance action definitions carry no reversible
flag (parameters are empty), the safe subset is empty (A_safe = {}) and the exploration rate
applied is 0.0 throughout every pull count t >= 0. Every decision is strictly exploitation.
The policy keeps choosing the action with the best mean (1.0 for the taken action, while
untaken actions remain at the neutral mean 0.5). Untaken actions are never chosen while a
taken action has mean > 0.5. This documents the stated price of the safety mask (BRU-017-03):
when actions are irreversible or unflagged, exploration is completely suppressed to protect
the system from random destructive actions.

What this is not: evidence that this policy decides better or worse than REINFORCE, UCB,
or Thompson sampling. Every episode here is accepted, so there is no failure to learn from.
Deciding whether any policy performs better requires a low-authority policy with failures
and a declared reversible flag (BRD-017 BRU-017-13), and that data does not exist yet.
Nothing below asserts a quality comparison.

Acceptance Criteria:
  AC_0 (Real Source): The history is the approve-* episodes of agent-learning-governance
       read from the committed files in docs/policy-shapes/episodes/, each replayed as
       r = 1.0 for the action taken; the count and the file names are recorded in the test.
  AC_1 (Locks In): With the existing action definitions, which carry no reversible flag,
       the rate applied is 0.0 throughout, every decision is exploitation, and the policy
       keeps choosing the action with the best mean; an untaken action stays at 0.5 and is
       not chosen while a taken action has a mean above 0.5. The test names this as the
       stated price of the safety mask (BRU-017-03).
  AC_2 (Repeatable): The replay run twice gives identical statistics, decisions and records.
  AC_3 (Labelled): The result is recorded as a baseline run on a real positive-only history.
       It makes no claim that this policy decides better or worse than REINFORCE, UCB or
       Thompson sampling (BRU-017-13), and the missing data (a low-authority policy with
       failures, and a declared reversible flag) is named in the test's docstring.

Contract Interpretations (derived via scripts/spec_gate.py):
  I1 (Upstream Fork Purity): Implemented under src/agent_learning_ext/ leaving upstream pristine.
  I2 (Storage Decoupling & Serialization): Policy snapshots survive JSON serialization without
      storage dependencies.
  I3 (Empty Collection Base Case): Handled cleanly without errors.
"""

from __future__ import annotations

import copy
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pytest

from agent_learning.types import Action, Episode, PolicySnapshot, Reward, RewardSource
from agent_learning_ext.learners.epsilon_greedy import EpsilonGreedyLearner
from agent_learning_ext.policy.action_statistics import read_statistics
from agent_learning_ext.policy.epsilon_greedy import (
    NEUTRAL_MEAN,
    SELECTION_BASIS,
    EpsilonGreedyPolicy,
)

SHAPES = Path(__file__).resolve().parent.parent / "docs" / "policy-shapes"
AGENT = "agent-learning-governance"
LABEL = "baseline run on a real positive-only history; no claim that epsilon-greedy decides better or worse"


def _history(episodes_dir: Path = SHAPES / "episodes") -> dict[str, list[tuple[str, str]]]:
    """Return {task_id: [(file_name, action_id), ...]} for the approve-* episodes in sorted order."""
    assert episodes_dir.is_dir(), f"missing episodes directory: {episodes_dir}"
    by_task: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for path in sorted(episodes_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("agent_id") == AGENT and str(data.get("task_id", "")).startswith("approve-"):
            action_id = data.get("action_id")
            assert action_id, f"{path.name}: an approve-* episode without an action_id"
            by_task[data["task_id"]].append((path.name, action_id))
    return dict(by_task)


def _actions(task_id: str) -> list[Action]:
    """Read the action file for task_id."""
    path = SHAPES / f"{task_id}.actions.json"
    assert path.is_file(), f"missing action file: {path}"
    return [
        Action(id=item["id"], description=item.get("description", ""), parameters=item.get("parameters", {}))
        for item in json.loads(path.read_text(encoding="utf-8"))
    ]


def _reward(name: str) -> Reward:
    """Create an aggregate reward of +1.0 for the given episode id."""
    return Reward(
        id=f"rew-{name}",
        episode_id=name,
        agent_id=AGENT,
        source=RewardSource.AGGREGATE,
        value=1.0,
        created_at="2026-10-29T00:00:00+00:00",
    )


def _replay_epsilon(
    task_id: str,
    history: list[tuple[str, str]],
    eps0: float = 0.5,
    delta: float = 0.05,
    floor: float = 0.05,
) -> EpsilonGreedyPolicy:
    """Replay task history through EpsilonGreedyPolicy and EpsilonGreedyLearner."""
    actions = _actions(task_id)
    policy = EpsilonGreedyPolicy.from_actions(
        actions,
        agent_id=AGENT,
        task_id=task_id,
        eps0=eps0,
        delta=delta,
        floor=floor,
    )
    learner = EpsilonGreedyLearner()
    for name, action_id in history:
        episode = Episode(
            id=name,
            agent_id=AGENT,
            task_id=task_id,
            action_id=action_id,
            metadata={"selection_basis": SELECTION_BASIS},
        )
        res = learner.update(policy, [episode], [_reward(name)])
        assert res.episodes_used == 1
    return policy


# -----------------------------------------------------------------------------
# AC_0 (Real Source)
# -----------------------------------------------------------------------------


def test_ac0_the_history_is_the_recorded_approve_episodes(record_property: pytest.RecordProperty) -> None:
    """AC_0: history is the approve-* episodes; count and filenames recorded without hardcoding fixed total."""
    history = _history()
    total = sum(len(items) for items in history.values())
    assert total > 0, "no approve-* episodes of agent-learning-governance found"

    record_property("episode_count", total)
    record_property("files", ",".join(name for items in history.values() for name, _ in items))
    record_property("per_task", json.dumps({task: len(items) for task, items in sorted(history.items())}))

    for task_id, items in history.items():
        valid_actions = {a.id for a in _actions(task_id)}
        taken_actions = {action_id for _, action_id in items}
        assert taken_actions <= valid_actions, f"{task_id}: action(s) {taken_actions - valid_actions} not in action space"


# -----------------------------------------------------------------------------
# AC_1 (Locks In — Stated Price of Safety Mask, BRU-017-03)
# -----------------------------------------------------------------------------


def test_ac1_locks_into_taken_action_due_to_safety_mask(record_property: pytest.RecordProperty) -> None:
    """AC_1: with existing actions lacking reversible flag, rate is 0.0, decisions are exploitation, locks onto best mean.

    Documents the stated price of the safety mask (BRU-017-03):
    Because no action in docs/policy-shapes/*.actions.json is flagged with 'reversible: true',
    the safe subset is empty, forcing the applied exploration rate to 0.0 throughout.
    Every decision is strictly exploitation. The policy locks onto the taken action whose mean
    is 1.0, while untaken actions stay at the neutral mean 0.5 and are never chosen.
    """
    history = _history()
    summary: dict[str, Any] = {}

    for task_id, items in history.items():
        policy = _replay_epsilon(task_id, items)
        actions = policy.actions()
        stats = read_statistics(policy.snapshot.metadata, [a.id for a in actions])
        taken_counts = Counter(action_id for _, action_id in items)

        # 1. Verify safe subset is empty and exploration rate applied is 0.0
        assert policy.safe_subset == set()
        assert policy.exploration_rate_applied() == 0.0

        for action in actions:
            aid = action.id
            if aid in taken_counts:
                n = stats[aid].pull_count
                k = stats[aid].cumulative_reward
                mean = stats[aid].mean_reward
                assert n == taken_counts[aid]
                assert k == pytest.approx(float(n), abs=1e-12)
                assert mean == pytest.approx(1.0, abs=1e-12)
                assert mean > NEUTRAL_MEAN  # 1.0 > 0.5
            else:
                # Untaken actions have pull_count 0, cumulative_reward 0.0, and mean_reward 0.0
                assert stats[aid].pull_count == 0
                assert stats[aid].cumulative_reward == 0.0
                assert stats[aid].mean_reward == 0.0

        # 2. Make a decision and verify that policy locks onto the taken action
        decision = policy.choose(request_id=f"req-check-{task_id}")
        record = policy.last_decision_record()

        assert record is not None
        assert record["branch_taken"] == "exploitation"
        assert record["exploration_rate_applied"] == 0.0
        assert record["chosen"] == decision.action.id

        # The chosen action MUST be one of the taken actions with mean 1.0 > 0.5
        assert decision.action.id in taken_counts
        # Untaken actions (with neutral mean 0.5) are NOT chosen
        untaken = {a.id for a in actions if a.id not in taken_counts}
        assert decision.action.id not in untaken

        summary[task_id] = {
            "total_episodes": len(items),
            "chosen_action": decision.action.id,
            "branch_taken": record["branch_taken"],
            "exploration_rate_applied": record["exploration_rate_applied"],
            "safe_subset_size": len(policy.safe_subset),
        }

    record_property("epsilon_positive_only_summary", json.dumps(summary, sort_keys=True))


# -----------------------------------------------------------------------------
# AC_2 (Repeatable)
# -----------------------------------------------------------------------------


def test_ac2_replay_run_twice_gives_identical_statistics_and_decisions() -> None:
    """AC_2: Running the replay twice yields identical statistics, decisions, and decision records."""
    history = _history()
    for task_id, items in history.items():
        run1 = _replay_epsilon(task_id, items)
        run2 = _replay_epsilon(task_id, items)

        # Standardize snapshot ID so PRNG seed derived from snapshot.id matches across separate runs
        run1._snapshot.id = f"snap-{task_id}"
        run2._snapshot.id = f"snap-{task_id}"

        # Guard: choose() must not mutate metadata
        meta_before1 = copy.deepcopy(run1.snapshot.metadata)
        meta_before2 = copy.deepcopy(run2.snapshot.metadata)

        # Statistics match identically
        stats1 = run1.snapshot.metadata["action_statistics"]
        stats2 = run2.snapshot.metadata["action_statistics"]
        assert stats1 == stats2

        # Decisions match identically with fixed request_id
        dec1 = run1.choose(request_id=f"req-repeat-{task_id}", timestamp="2026-11-08T00:00:00Z")
        dec2 = run2.choose(request_id=f"req-repeat-{task_id}", timestamp="2026-11-08T00:00:00Z")

        # Verify choose() left snapshot metadata strictly unmutated
        assert run1.snapshot.metadata == meta_before1
        assert run2.snapshot.metadata == meta_before2

        assert dec1.action.id == dec2.action.id
        assert dec1.probabilities == dec2.probabilities
        assert dec1.logprob is None and dec2.logprob is None

        rec1 = run1.last_decision_record()
        rec2 = run2.last_decision_record()
        assert rec1 == rec2

        # Snapshots serialize cleanly to JSON and back
        snap_dict1 = run1.snapshot.to_dict()
        snap_dict2 = run2.snapshot.to_dict()
        snap_dict1.pop("created_at", None)
        snap_dict2.pop("created_at", None)
        assert snap_dict1 == snap_dict2

        # Roundtrip survives json.dumps and json.loads
        roundtrip1 = json.loads(json.dumps(run1.snapshot.to_dict()))
        assert roundtrip1["metadata"] == run1.snapshot.metadata


# -----------------------------------------------------------------------------
# AC_3 (Labelled)
# -----------------------------------------------------------------------------


def test_ac3_the_result_is_labelled_a_baseline_run(record_property: pytest.RecordProperty) -> None:
    """AC_3: test and records explicitly label this as a baseline run without claims of superiority."""
    record_property("label", LABEL)
    assert "baseline run" in LABEL
    assert "no claim that epsilon-greedy decides better or worse" in LABEL

    docstring = " ".join((__doc__ or "").split())
    assert "low-authority policy with failures and a declared reversible flag" in docstring
    assert "stated price of the safety mask (BRU-017-03)" in docstring


def test_a_history_file_without_an_action_id_fails_naming_the_file(tmp_path: Path) -> None:
    """Defensive test: a history file lacking action_id raises AssertionError naming the file."""
    bad_file = tmp_path / "bad-episode.json"
    bad_file.write_text(json.dumps({"agent_id": AGENT, "task_id": "approve-adr"}), encoding="utf-8")
    with pytest.raises(AssertionError, match="bad-episode.json"):
        _history(tmp_path)
