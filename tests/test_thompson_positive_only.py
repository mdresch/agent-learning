"""Contract tests for Epic 15, Story 15.6 (The Positive-Only Check, HYP-AL-002).

Story: docs/user-stories/epic-15-bayesian-bandit-posterior-sampling.md, Story 15.6.
ADR-015 §4.4 and Test Data; BRD-015 BRU-015-10; FDD-015 §8.

What this is: a consistency check on a real, positive-only history. The ``approve-*`` episodes of
``agent-learning-governance`` in ``docs/policy-shapes/episodes/`` were all accepted, so each is
replayed as ``r = 1.0`` (a reward value of 1.0) for the action taken, through the real
``ReinforceLearner`` and the real ``ThompsonLearner``. REINFORCE's baseline climbs to the reward and
its advantage, hence its logit change, goes to zero; the Thompson posterior of the action taken
stays a distribution with width and every untaken action keeps its prior.

What this is not: evidence that Thompson sampling decides better. Every episode here is accepted,
so there is no failure to learn from. That needs a low-authority policy with at least 100 scored
episodes including failures (BRD-015 BRU-015-10, FDD-015 §8 "Gap"), and that data does not exist
yet. Nothing below asserts a quality comparison.

Interpretation I1: one policy per ``task_id``, over that task's action file
``docs/policy-shapes/<task_id>.actions.json``, because the tasks have different action spaces.

Interpretation I2: the history carries no log-probability (full authority; Story 15.5 shows
REINFORCE would skip it). The REINFORCE replay therefore assigns each episode the log-probability
the ``SoftmaxPolicy`` being trained gives its action at that step, so the importance weight is 1.
This assignment is stated here and recorded with the result; it is not in the data.

Interpretation I3: one episode per ``update`` call (a batch of one), the finest grain the runner
allows, with the learner hyperparameters spelled out at the repository defaults so an environment
variable cannot change the result. ``approaches 1.0`` is a baseline above 0.95. With a decay of
0.9 the baseline after ``n`` all-ones episodes is ``1 - 0.9**n``, so a task needs about 30 episodes
to qualify; tasks with fewer are recorded but not asserted, because arithmetic, not data, decides
them.

Interpretation I4: the count and the file names are recorded (``record_property``) and never
asserted as a fixed number (41 when ADR-015 was written, 58 on 2026-10-29, more since).
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import pytest

from agent_learning.config import LearnerConfig
from agent_learning.learners.reinforce import ReinforceLearner
from agent_learning.learners.thompson import ThompsonLearner
from agent_learning.policy import SoftmaxPolicy
from agent_learning.policy.thompson import SELECTION_BASIS, ThompsonPolicy
from agent_learning.types import Action, Episode, Reward, RewardSource

SHAPES = Path(__file__).resolve().parent.parent / "docs" / "policy-shapes"
AGENT = "agent-learning-governance"
LABEL = "consistency check on a real positive-only history; no claim that Thompson sampling decides better"
MIN_EPISODES_FOR_STALL = 30
BASELINE_NEAR_ONE = 0.95
LOGIT_CHANGE_BOUND = 1e-3

# The repository defaults, spelled out so AGENT_LEARNING_* variables cannot move the result.
CONFIG = LearnerConfig(
    learning_rate=0.05,
    baseline_decay=0.9,
    entropy_bonus=0.01,
    max_logit_abs=10.0,
    importance_clip=5.0,
    min_train_episodes=0,
)


def _history(episodes_dir: Path = SHAPES / "episodes") -> dict[str, list[tuple[str, str]]]:
    """``{task_id: [(file name, action_id), ...]}`` for the approve-* episodes, in file-name order."""
    assert episodes_dir.is_dir(), f"missing {episodes_dir}"
    by_task: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for path in sorted(episodes_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("agent_id") == AGENT and str(data.get("task_id", "")).startswith("approve-"):
            action_id = data.get("action_id")
            assert action_id, f"{path.name}: an approve-* episode without an action_id"
            by_task[data["task_id"]].append((path.name, action_id))
    return dict(by_task)


def _actions(task_id: str) -> list[Action]:
    path = SHAPES / f"{task_id}.actions.json"
    assert path.is_file(), f"missing the action file {path}"
    return [Action(id=item["id"]) for item in json.loads(path.read_text(encoding="utf-8"))]


def _reward(name: str) -> Reward:
    return Reward(
        id=f"reward-{name}",
        episode_id=name,
        agent_id=AGENT,
        source=RewardSource.AGGREGATE,
        value=1.0,
        created_at="2026-10-29T00:00:00+00:00",
    )


def _replay_reinforce(task_id: str, history: list[tuple[str, str]]) -> tuple[float, float]:
    """Replay a task through REINFORCE; return the final baseline and the largest final logit change."""
    actions = _actions(task_id)
    index = {action.id: i for i, action in enumerate(actions)}
    policy = SoftmaxPolicy.from_actions(actions, agent_id=AGENT, task_id=task_id)
    learner = ReinforceLearner(CONFIG)
    result = None
    for name, action_id in history:
        logprob = math.log(policy.probabilities()[index[action_id]])  # I2: assigned, not recorded
        episode = Episode(id=name, agent_id=AGENT, task_id=task_id, action_id=action_id, action_logprob=logprob)
        result = learner.update(policy, [episode], [_reward(name)])
        assert result.episodes_used == 1
    assert result is not None
    return result.baseline_after, max(abs(v) for v in result.logit_deltas.values())


def _replay_thompson(task_id: str, history: list[tuple[str, str]]) -> ThompsonPolicy:
    policy = ThompsonPolicy.from_actions(_actions(task_id), agent_id=AGENT, task_id=task_id)
    learner = ThompsonLearner()
    for name, action_id in history:
        episode = Episode(
            id=name, agent_id=AGENT, task_id=task_id, action_id=action_id,
            metadata={"selection_basis": SELECTION_BASIS},
        )
        assert learner.update(policy, [episode], [_reward(name)]).episodes_used == 1
    return policy


def _std(alpha: float, beta: float) -> float:
    return math.sqrt(alpha * beta / ((alpha + beta) ** 2 * (alpha + beta + 1.0)))


def test_ac0_the_history_is_the_recorded_approve_episodes(record_property: pytest.RecordProperty) -> None:
    history = _history()
    total = sum(len(items) for items in history.values())
    assert total > 0, "no approve-* episodes of agent-learning-governance found"
    record_property("episode_count", total)
    record_property("files", ",".join(name for items in history.values() for name, _ in items))
    record_property("per_task", json.dumps({task: len(items) for task, items in sorted(history.items())}))
    for task_id, items in history.items():
        names = {a.id for a in _actions(task_id)}
        taken = {action_id for _, action_id in items}
        assert taken <= names, f"{task_id}: action(s) {taken - names} are not in the action file"


def test_ac1_reinforce_stalls_on_the_all_ones_history(record_property: pytest.RecordProperty) -> None:
    results = {task: _replay_reinforce(task, items) for task, items in _history().items()}
    record_property(
        "reinforce",
        json.dumps({t: {"baseline": round(b, 4), "max_logit_change": c} for t, (b, c) in sorted(results.items())}),
    )
    record_property("logprob_assignment", "log-probability of the SoftmaxPolicy being trained, at each step (I2)")

    history = _history()
    qualifying = {t: v for t, v in results.items() if len(history[t]) >= MIN_EPISODES_FOR_STALL}
    assert qualifying, "no task has enough episodes to show the stall; lower MIN_EPISODES_FOR_STALL only with a reason"
    for task_id, (baseline, change) in qualifying.items():
        assert baseline > BASELINE_NEAR_ONE, f"{task_id}: baseline {baseline}"
        assert change < LOGIT_CHANGE_BOUND, f"{task_id}: final logit change {change}"


def test_ac2_thompson_keeps_width_on_the_all_ones_history(record_property: pytest.RecordProperty) -> None:
    history = _history()
    summary = {}
    for task_id, items in history.items():
        policy = _replay_thompson(task_id, items)
        posterior = policy.posterior()
        taken = Counter(action_id for _, action_id in items)
        for action in policy.actions():
            alpha, beta = posterior["alpha"][action.id], posterior["beta"][action.id]
            if action.id in taken:
                assert _std(alpha, beta) > 0.0
                assert alpha == pytest.approx(1.0 + taken[action.id], abs=1e-9)
                assert beta == pytest.approx(1.0, abs=1e-9)
                summary[f"{task_id}/{action.id}"] = {"alpha": alpha, "beta": beta, "std": _std(alpha, beta)}
            else:
                assert (alpha, beta) == (1.0, 1.0), f"{task_id}/{action.id} moved without being taken"
    record_property("thompson", json.dumps(summary, sort_keys=True))


def test_ac3_the_result_is_labelled_a_consistency_check(record_property: pytest.RecordProperty) -> None:
    record_property("label", LABEL)
    assert "consistency check" in LABEL
    assert "no claim that Thompson sampling decides better" in LABEL
    docstring = " ".join((__doc__ or "").split())  # the docstring wraps lines
    assert "low-authority policy with at least 100 scored episodes including failures" in docstring


def test_a_history_file_without_an_action_id_fails_naming_the_file(tmp_path: Path) -> None:
    (tmp_path / "bad-episode.json").write_text(
        json.dumps({"agent_id": AGENT, "task_id": "approve-adr"}), encoding="utf-8"
    )
    with pytest.raises(AssertionError, match="bad-episode.json"):
        _history(tmp_path)
