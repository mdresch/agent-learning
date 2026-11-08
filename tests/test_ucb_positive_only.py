"""Contract tests for Epic 16, Story 16.6 (The Positive-Only Check, HYP-AL-009).

Story: docs/user-stories/epic-16-deterministic-ucb-decision-policy.md, Story 16.6.
ADR-016 §4.4 and Test Data; BRD-016 BRU-016-11; FDD-016 §3, §8.

What this is: a consistency check on a real, positive-only history. The ``approve-*`` episodes of
``agent-learning-governance`` in ``docs/policy-shapes/episodes/`` were all accepted, so each is
replayed as ``r = 1.0`` (a reward value of 1.0) for the action taken, through the real
``UCBLearner`` and ``UCBPolicy``. Because unpulled actions score ``inf``, every untaken action
still scores ``inf`` and is chosen before any taken action, preserving exploration; the taken
action's Wilson score is 1.0 and its Wilson lower bound rises monotonically with the count,
matching ``wilson_lower_bound`` (ADR-003).

What this is not: evidence that UCB decides better. Every episode here is accepted, so there is
no failure to learn from. Deciding whether UCB performs better requires a low-authority policy
with at least 100 scored episodes including failures (BRD-016 BRU-016-11, FDD-016 §8 "Gap"),
and that data does not exist yet. Nothing below asserts a quality comparison.

Acceptance Criteria:
  AC_0 (Real Source): The history is the approve-* episodes read from committed files in
       docs/policy-shapes/episodes/, replayed as r = 1.0 for action taken; count and file names recorded.
  AC_1 (Keeps Exploring): Every untaken action still scores inf and is chosen before any taken action;
       the taken action's Wilson score is 1.0 and its lower bound rises with the count, matching wilson_lower_bound.
  AC_2 (Repeatable): Replay run twice gives identical statistics and identical choices.
  AC_3 (Labelled): Result recorded as consistency check on real positive-only history with no claim of
       superiority without low-authority failure data (BRU-016-11).

Contract Interpretations (derived via scripts/spec_gate.py):
  I1 (Upstream Fork Purity): Implemented under src/agent_learning_ext/ leaving upstream pristine.
  I2 (Storage Decoupling & Serialization): No storage coupling; snapshot roundtrips cleanly via JSON.
  I3 (Empty Collection Base Case): Handled cleanly without errors.
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pytest

from agent_learning.types import Action, Episode, Reward, RewardSource
from agent_learning_ext.autonomy import wilson_lower_bound
from agent_learning_ext.learners.ucb import UCBLearner
from agent_learning_ext.policy.action_statistics import read_statistics
from agent_learning_ext.policy.ucb import SELECTION_BASIS, WILSON_Z, UCBPolicy, ucb_scores

SHAPES = Path(__file__).resolve().parent.parent / "docs" / "policy-shapes"
AGENT = "agent-learning-governance"
LABEL = "consistency check on a real positive-only history; no claim that UCB decides better"


def _history(episodes_dir: Path = SHAPES / "episodes") -> dict[str, list[tuple[str, str]]]:
    """Return ``{task_id: [(file_name, action_id), ...]}`` for the approve-* episodes in sorted order."""
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
    return [Action(id=item["id"], description=item.get("description", "")) for item in json.loads(path.read_text(encoding="utf-8"))]


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


def _replay_ucb(task_id: str, history: list[tuple[str, str]], variant: str = "wilson") -> UCBPolicy:
    """Replay task history through UCBPolicy and UCBLearner."""
    actions = _actions(task_id)
    policy = UCBPolicy.from_actions(actions, agent_id=AGENT, task_id=task_id, variant=variant)
    learner = UCBLearner()
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
# AC_1 (Keeps Exploring)
# -----------------------------------------------------------------------------


def test_ac1_untaken_actions_score_inf_and_chosen_before_taken(record_property: pytest.RecordProperty) -> None:
    """AC_1: untaken actions still score inf and are chosen before taken actions; taken action Wilson score is 1.0."""
    history = _history()
    summary: dict[str, Any] = {}

    for task_id, items in history.items():
        policy = _replay_ucb(task_id, items, variant="wilson")
        actions = policy.actions()
        stats = read_statistics(policy.snapshot().metadata, [a.id for a in actions])
        total_pulls = sum(s.pull_count for s in stats.values())
        scores = ucb_scores(stats, total_pulls, variant="wilson")

        taken_counts = Counter(action_id for _, action_id in items)

        for action in actions:
            aid = action.id
            if aid in taken_counts:
                # Taken action: all rewards were 1.0, so k == N
                n = stats[aid].pull_count
                k = stats[aid].cumulative_reward
                assert n == taken_counts[aid]
                assert k == float(n)
                # Wilson score for perfect action is 1.0
                assert scores[aid] == pytest.approx(1.0, abs=1e-12)

                # Wilson lower bound rises monotonically with N
                lower_bound = wilson_lower_bound(k, n, WILSON_Z)
                assert lower_bound is not None
                assert 0.0 < lower_bound <= 1.0

                summary[f"{task_id}/{aid}"] = {
                    "pull_count": n,
                    "cumulative_reward": k,
                    "score": scores[aid],
                    "lower_bound": lower_bound,
                }
            else:
                # Untaken action: pull count 0, score math.inf
                assert stats[aid].pull_count == 0
                assert stats[aid].cumulative_reward == 0.0
                assert scores[aid] == math.inf

        # If there are untaken actions, choose() MUST choose an untaken action (scoring inf)
        untaken = [a for a in actions if a.id not in taken_counts]
        if untaken:
            decision = policy.choose()
            assert decision.action.id in {a.id for a in untaken}, (
                f"For task {task_id}, policy chose taken action {decision.action.id} instead of untaken actions"
            )

    record_property("ucb_wilson_summary", json.dumps(summary, sort_keys=True))


def test_ac1_wilson_lower_bound_rises_with_count_on_perfect_records() -> None:
    """AC_1: Wilson lower bound monotonically increases as pull count rises with perfect rewards (r=1.0)."""
    bounds: list[float] = []
    for n in range(1, 60):
        lb = wilson_lower_bound(float(n), n, WILSON_Z)
        assert lb is not None
        bounds.append(lb)

    # Strictly monotonically increasing
    for i in range(len(bounds) - 1):
        assert bounds[i] < bounds[i + 1], f"Bound failed to rise at N={i + 1}: {bounds[i]} >= {bounds[i + 1]}"


# -----------------------------------------------------------------------------
# AC_2 (Repeatable)
# -----------------------------------------------------------------------------


def test_ac2_replay_run_twice_gives_identical_statistics_and_choices() -> None:
    """AC_2: Running the replay twice yields identical statistics and deterministic choices."""
    history = _history()
    for task_id, items in history.items():
        run1_policy = _replay_ucb(task_id, items, variant="wilson")
        run2_policy = _replay_ucb(task_id, items, variant="wilson")

        stats1 = run1_policy.snapshot().metadata["action_statistics"]
        stats2 = run2_policy.snapshot().metadata["action_statistics"]
        assert stats1 == stats2

        choice1 = run1_policy.choose()
        choice2 = run2_policy.choose()
        assert choice1.action.id == choice2.action.id
        assert choice1.probabilities == choice2.probabilities


# -----------------------------------------------------------------------------
# AC_3 (Labelled)
# -----------------------------------------------------------------------------


def test_ac3_the_result_is_labelled_a_consistency_check(record_property: pytest.RecordProperty) -> None:
    """AC_3: test and records explicitly label this as a consistency check without claims of superiority."""
    record_property("label", LABEL)
    assert "consistency check" in LABEL
    assert "no claim that UCB decides better" in LABEL

    docstring = " ".join((__doc__ or "").split())
    assert "low-authority policy with at least 100 scored episodes including failures" in docstring


def test_a_history_file_without_an_action_id_fails_naming_the_file(tmp_path: Path) -> None:
    """Defensive test: a history file lacking action_id raises AssertionError naming the file."""
    bad_file = tmp_path / "bad-episode.json"
    bad_file.write_text(json.dumps({"agent_id": AGENT, "task_id": "approve-adr"}), encoding="utf-8")
    with pytest.raises(AssertionError, match="bad-episode.json"):
        _history(tmp_path)
