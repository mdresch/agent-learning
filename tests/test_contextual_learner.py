"""Contract for ContextualReinforceLearner (Epic 38, Stories 38.1 to 38.3).

Story 38.1 (The Weight-Row Update): AC_0 one episode, AC_1 batch mean, AC_2 clip stays in the policy, AC_3 receipt,
AC_4 purity.
Governing documents: ADR-038 (section 4.1, invariants 1 to 5), BRD-038 (BRU-038-02, BRU-038-06), FDD-038 (sections 1,
2.1 and 3, D6). Hierarchy: ADR > BRD/FDD > Story.

Interpretations from ``scripts/spec_gate.py 38.1`` (PASSED, robust margin +0.1774):
  I1 None-safety: ``Episode.metadata`` is read defensively; a missing or None metadata never raises (it is a skip, which
     Story 38.2 counts).
  I2 Empty base case: no usable episode leaves the policy unmutated and reports episodes_used 0 (Story 38.2 pins it).
  I3 Non-finite rejection: a non-finite aggregate reward raises ValueError (Story 38.2 AC_4).
Interpretations added for this contract:
  I4 AC_4 "imports from agent_learning and from agent_learning.learners": the module has at least one ``from
     agent_learning.learners import ...`` and at least one other ``from agent_learning... import`` statement. Checked on
     the parsed source, so an import hidden in a docstring does not count. ``from agent_learning import storage`` and
     ``import numpy`` are both detected.
  I5 The learner is exported from ``agent_learning_ext.learners`` and ``agent_learning_ext`` (FDD-038 section 1.2); no
     acceptance criterion states it, so it is pinned by its own test.
  I6 Batch rows are the plain mean over used episodes, each scored on the starting weights (FDD-038 section 3 items 3
     and 4); ``extra["weight_deltas"]`` holds the unclipped rows and ``logit_deltas`` is ``{}``.

Fixture ("the zero policy"): actions ``a`` then ``b``, feature_dim 2, both weight rows ``[0.0, 0.0]``, baseline 0.

Story 38.2 and 38.3 tests are appended below in their own sections.
"""

from __future__ import annotations

import ast
import math
from pathlib import Path

import pytest

from agent_learning.config import LearnerConfig
from agent_learning.policy import ContextualSoftmaxPolicy
from agent_learning.types import Action, Episode, Reward, RewardSource

LEARNER_FILE = Path(__file__).resolve().parents[1] / "src" / "agent_learning_ext" / "learners" / "contextual_reinforce.py"
HALF = math.log(0.5)


def _learner(learning_rate: float = 0.4, baseline_decay: float = 0.9):
    from agent_learning_ext.learners import ContextualReinforceLearner

    return ContextualReinforceLearner(LearnerConfig(learning_rate=learning_rate, baseline_decay=baseline_decay))


def _zero_policy() -> ContextualSoftmaxPolicy:
    return ContextualSoftmaxPolicy.from_actions([Action(id="a"), Action(id="b")], feature_dim=2)


def _episode(vector, action="a", logprob=HALF, **kwargs) -> Episode:
    metadata = {} if vector is None else {"feature_vector": vector}
    return Episode(metadata=metadata, action_id=action, action_logprob=logprob, **kwargs)


def _reward(episode: Episode, value: float = 1.0) -> Reward:
    return Reward(episode_id=episode.id, source=RewardSource.AGGREGATE, value=value)


def _rows(policy: ContextualSoftmaxPolicy) -> dict:
    return policy.snapshot().metadata["context_weights"]


def test_ac0_one_episode_matches_the_worked_update():
    policy = _zero_policy()
    start_version = policy.snapshot().version
    episode = _episode([1.0, 2.0])
    result = _learner(0.4, 0.9).update(policy, [episode], [_reward(episode, 1.0)])
    rows = _rows(policy)
    assert rows["a"] == pytest.approx([0.2, 0.4], abs=1e-9)
    assert rows["b"] == pytest.approx([-0.2, -0.4], abs=1e-9)
    snapshot = policy.snapshot()
    assert snapshot.baseline == pytest.approx(0.1, abs=1e-9)
    assert snapshot.version == start_version + 1
    assert result.episodes_used == 1


def test_ac1_batch_applies_the_mean_scored_on_the_starting_weights():
    policy = _zero_policy()
    first = _episode([1.0, 0.0], action="a")
    second = _episode([0.0, 1.0], action="b")
    result = _learner(1.0, 0.9).update(policy, [first, second], [_reward(first, 1.0), _reward(second, -1.0)])
    rows = _rows(policy)
    assert rows["a"] == pytest.approx([0.25, 0.25], abs=1e-9)
    assert rows["b"] == pytest.approx([-0.25, -0.25], abs=1e-9)
    assert policy.snapshot().baseline == pytest.approx(0.0, abs=1e-9)
    assert result.episodes_used == 2


def test_ac2_clip_stays_in_the_policy():
    policy = _zero_policy()
    episode = _episode([1.0, 0.0])
    result = _learner(100.0, 0.9).update(policy, [episode], [_reward(episode, 1.0)])
    assert result.extra["weight_deltas"]["a"] == pytest.approx([50.0, 0.0], abs=1e-9)
    assert result.extra["weight_deltas"]["b"] == pytest.approx([-50.0, 0.0], abs=1e-9)
    rows = _rows(policy)
    assert rows["a"] == pytest.approx([10.0, 0.0], abs=1e-9)
    assert rows["b"] == pytest.approx([-10.0, 0.0], abs=1e-9)
    assert result.logit_deltas == {}


def test_ac3_receipt_lists_only_used_episodes_with_the_kept_reward():
    policy = _zero_policy()
    used = _episode([1.0, 0.0])
    unrewarded = _episode([0.0, 1.0])
    old = Reward(
        episode_id=used.id, source=RewardSource.AGGREGATE, value=-1.0, created_at="2026-01-01T00:00:00+00:00"
    )
    kept = Reward(episode_id=used.id, source=RewardSource.AGGREGATE, value=1.0, created_at="2026-02-01T00:00:00+00:00")
    result = _learner().update(policy, [used, unrewarded], [old, kept])
    assert [(c.episode_id, c.reward_id) for c in result.consumed_inputs] == [(used.id, kept.id)]
    assert result.episodes_used == len(result.consumed_inputs) == 1


def _imports(path: Path) -> list[tuple[str, tuple[str, ...]]]:
    assert path.is_file(), f"{path} is missing"
    found: list[tuple[str, tuple[str, ...]]] = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            found.extend((alias.name, ()) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            found.append((node.module or "", tuple(alias.name for alias in node.names)))
    return found


def test_ac4_pure_imports():
    imports = _imports(LEARNER_FILE)
    for module, names in imports:
        root = module.split(".")[0]
        assert root != "numpy", "contextual_reinforce.py must not import numpy"
        assert module != "agent_learning.storage" and not module.startswith("agent_learning.storage."), (
            "contextual_reinforce.py must not import agent_learning.storage"
        )
        if module == "agent_learning":
            assert "storage" not in names, "contextual_reinforce.py must not import agent_learning.storage"
    from_agent_learning = [m for m, names in imports if m == "agent_learning" or m.startswith("agent_learning.")]
    assert from_agent_learning, "expected imports from agent_learning"
    assert any(m == "agent_learning.learners" for m, _ in imports), "expected an import from agent_learning.learners"


def test_exported_from_ext_learners_and_ext_root():
    import agent_learning_ext
    from agent_learning_ext import learners

    assert agent_learning_ext.ContextualReinforceLearner is learners.ContextualReinforceLearner
    assert learners.ContextualReinforceLearner.__module__ == "agent_learning_ext.learners.contextual_reinforce"
    assert "ContextualReinforceLearner" in learners.__all__
    assert "ContextualReinforceLearner" in agent_learning_ext.__all__
