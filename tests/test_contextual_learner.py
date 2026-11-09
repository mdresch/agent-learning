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

Story 38.2 (Skipped Episodes Are Counted): AC_0 one counter, AC_1 first match, AC_2 context is not the vector, AC_3
supplied zeros are used, AC_4 bad reward. Same governing documents (BRU-038-03, BRU-038-04, BRU-038-05; FDD-038 section
2.1 table and section 3 items 2 and 6; ADR-038 invariants 2 to 4).
Interpretations from ``scripts/spec_gate.py 38.2`` (PASSED, robust margin +0.1829); the gate numbers them I1 to I3 again,
they are renamed G1 to G3 here so that they do not collide with the Story 38.1 list above:
  G1 storage decoupling and JSON round-trip: the learner module imports nothing from agent_learning.storage (pinned by
     Story 38.1 AC_4); the returned ``extra`` holds only ints, strs and lists of floats, so json.dumps round-trips it.
  G2 None-safety: an episode whose ``metadata`` is None is a missing vector, not an AttributeError.
  G3 empty base case: an empty episode list returns episodes_used 0 and leaves weights, baseline and version unchanged.
Interpretations added for this contract:
  I7 Every one of the seven counter keys is present in ``extra`` on every return (value 0 when nothing was skipped
     under it), so "increments exactly the named counter to 1" can be checked against the others being 0.
  I8 ``[1.0, inf]`` is non-finite like NaN. A reward is validated only when its source is AGGREGATE (other sources are
     never consumed), and an invalid aggregate reward is rejected even when its episode is not in the call.
  I9 The "no aggregate reward" case is an episode with an otherwise usable vector and action and no reward at all.

Story 38.3 (One Learner, One Policy Class): AC_0 the contextual learner rejects a SoftmaxPolicy, AC_1 the scalar learner
rejects a ContextualSoftmaxPolicy and still updates a SoftmaxPolicy. Governing: ADR-038 invariant 1, BRU-038-01, FDD-038
section 3 item 1 and section 5.
Interpretations from ``scripts/spec_gate.py 38.3`` (PASSED, robust margin +0.1256), renamed H1 to H4 here:
  H1 storage decoupling and JSON round-trip: pinned by Story 38.1 AC_4; a rejected call leaves ``snapshot().to_dict()``
     equal to its value before the call.
  H2 empty base case: not relevant to the wall (the class check runs before any episode is read).
  H3 non-finite rejection: pinned by Story 38.2 AC_4.
  H4 tolerances: no floating-point comparison is made in this story; the one numeric check is a sign (the scalar
     update raises the logit of the rewarded action above 0).
Interpretations added for this contract:
  I10 "ReinforceLearner" means both ``agent_learning_ext.learners.ReinforceLearner`` and Microsoft's
      ``agent_learning.learners.ReinforceLearner``; both already raise TypeError for a ContextualSoftmaxPolicy, so those
      tests guard existing behaviour and are green before this story's code (recorded as such in the log).
  I11 "does not read feature_vector" is checked with an episode whose metadata fails the test on any key lookup.
  I12 The TypeError text is compared for equality, so the message in FDD-038 section 3 item 1 is the contract.
"""

from __future__ import annotations

import ast
import math
from pathlib import Path

import pytest

from agent_learning.config import LearnerConfig
from agent_learning.policy import ContextualSoftmaxPolicy, SoftmaxPolicy
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


# ----------------------------------------------------------------------------------------------------------------------
# Story 38.2 - Skipped Episodes Are Counted
# ----------------------------------------------------------------------------------------------------------------------

COUNTERS = (
    "skipped_no_action",
    "full_authority_excluded",
    "skipped_no_reward",
    "skipped_missing_vector",
    "skipped_not_list",
    "skipped_wrong_length",
    "skipped_non_finite",
)


def _skip_cases():
    def with_metadata(metadata):
        return Episode(metadata=metadata, action_id="a", action_logprob=HALF)

    return [
        ("missing_vector_absent", with_metadata({}), "skipped_missing_vector", True),
        ("missing_vector_null", with_metadata({"feature_vector": None}), "skipped_missing_vector", True),
        ("not_list_tuple", with_metadata({"feature_vector": (1.0, 0.0)}), "skipped_not_list", True),
        ("not_list_dict", with_metadata({"feature_vector": {"x": 1.0, "y": 0.0}}), "skipped_not_list", True),
        ("wrong_length", with_metadata({"feature_vector": [1.0]}), "skipped_wrong_length", True),
        ("non_finite_nan", with_metadata({"feature_vector": [1.0, math.nan]}), "skipped_non_finite", True),
        ("non_finite_inf", with_metadata({"feature_vector": [1.0, math.inf]}), "skipped_non_finite", True),
        ("non_finite_strings", with_metadata({"feature_vector": ["1", "0"]}), "skipped_non_finite", True),
        ("non_finite_bool", with_metadata({"feature_vector": [True, 0.0]}), "skipped_non_finite", True),
        (
            "full_authority",
            Episode(metadata={"feature_vector": [1.0, 0.0]}, action_id="a", action_logprob=None),
            "full_authority_excluded",
            True,
        ),
        (
            "no_action_null",
            Episode(metadata={"feature_vector": [1.0, 0.0]}, action_id=None, action_logprob=HALF),
            "skipped_no_action",
            True,
        ),
        (
            "no_action_unknown",
            Episode(metadata={"feature_vector": [1.0, 0.0]}, action_id="zzz", action_logprob=HALF),
            "skipped_no_action",
            True,
        ),
        ("no_reward", with_metadata({"feature_vector": [1.0, 0.0]}), "skipped_no_reward", False),
    ]


def _unchanged(policy: ContextualSoftmaxPolicy, before: dict) -> None:
    assert policy.snapshot().to_dict() == before


@pytest.mark.parametrize(("name", "episode", "counter", "rewarded"), _skip_cases(), ids=[c[0] for c in _skip_cases()])
def test_story382_ac0_each_skip_increments_exactly_its_counter(name, episode, counter, rewarded):
    policy = _zero_policy()
    before = policy.snapshot().to_dict()
    rewards = [_reward(episode, 1.0)] if rewarded else []
    result = _learner().update(policy, [episode], rewards)
    _unchanged(policy, before)
    assert result.episodes_used == 0
    assert result.extra["reason"] == "no actionable episodes"
    assert result.consumed_inputs == []
    assert {key: result.extra[key] for key in COUNTERS} == {key: int(key == counter) for key in COUNTERS}, name


def test_story382_ac1_first_match_wins():
    policy = _zero_policy()
    before = policy.snapshot().to_dict()
    episode = Episode(metadata={}, action_id="a", action_logprob=None)
    result = _learner().update(policy, [episode], [_reward(episode, 1.0)])
    _unchanged(policy, before)
    assert {key: result.extra[key] for key in COUNTERS} == {
        key: int(key == "full_authority_excluded") for key in COUNTERS
    }


def test_story382_ac2_context_features_is_not_the_vector():
    policy = _zero_policy()
    before = policy.snapshot().to_dict()
    episode = Episode(
        metadata={},
        action_id="a",
        action_logprob=HALF,
        context_features={"feature_vector": [1.0, 2.0], "x": [1.0, 2.0]},
    )
    result = _learner().update(policy, [episode], [_reward(episode, 1.0)])
    _unchanged(policy, before)
    assert result.extra["skipped_missing_vector"] == 1
    assert result.episodes_used == 0


def test_story382_ac3_supplied_zeros_are_used():
    policy = _zero_policy()
    start_version = policy.snapshot().version
    episode = _episode([0.0, 0.0])
    result = _learner(0.4, 0.9).update(policy, [episode], [_reward(episode, 1.0)])
    snapshot = policy.snapshot()
    assert result.episodes_used == 1
    assert snapshot.baseline == pytest.approx(0.1, abs=1e-9)
    assert snapshot.version == start_version + 1
    assert snapshot.metadata["context_weights"] == {"a": [0.0, 0.0], "b": [0.0, 0.0]}


@pytest.mark.parametrize("bad", [1.1, -1.1, math.nan, math.inf])
def test_story382_ac4_bad_reward_raises_before_any_weight_change(bad):
    policy = _zero_policy()
    before = policy.snapshot().to_dict()
    good = _episode([1.0, 0.0])
    other = _episode([0.0, 1.0], action="b")
    with pytest.raises(ValueError):
        _learner().update(policy, [good, other], [_reward(good, 1.0), _reward(other, bad)])
    _unchanged(policy, before)


def test_story382_g2_none_metadata_is_a_missing_vector():
    policy = _zero_policy()
    episode = Episode(metadata=None, action_id="a", action_logprob=HALF)  # type: ignore[arg-type]
    result = _learner().update(policy, [episode], [_reward(episode, 1.0)])
    assert result.extra["skipped_missing_vector"] == 1


def test_story382_g3_empty_episode_list_is_a_clean_no_op():
    policy = _zero_policy()
    before = policy.snapshot().to_dict()
    result = _learner().update(policy, [], [])
    _unchanged(policy, before)
    assert result.episodes_used == 0
    assert result.extra["weight_deltas"] == {}


# ----------------------------------------------------------------------------------------------------------------------
# Story 38.3 - One Learner, One Policy Class
# ----------------------------------------------------------------------------------------------------------------------


class _VectorGuard(dict):
    """Episode metadata that fails the test if anything reads ``feature_vector``."""

    def _blocked(self, *args, **kwargs):
        raise AssertionError("the scalar learner must not read feature_vector")

    __getitem__ = get = pop = setdefault = __contains__ = _blocked


def _scalar_policy() -> SoftmaxPolicy:
    return SoftmaxPolicy.from_actions([Action(id="a"), Action(id="b")])


def test_story383_ac0_contextual_learner_rejects_a_softmax_policy():
    policy = _scalar_policy()
    before = policy.snapshot().to_dict()
    episode = _episode([1.0, 0.0])
    with pytest.raises(TypeError) as raised:
        _learner().update(policy, [episode], [_reward(episode, 1.0)])
    assert str(raised.value) == "ContextualReinforceLearner requires a ContextualSoftmaxPolicy"
    assert policy.snapshot().to_dict() == before
    assert policy.snapshot().logits == {"a": 0.0, "b": 0.0}


def test_story383_ac1_scalar_learner_rejects_a_contextual_policy():
    from agent_learning.learners import ReinforceLearner as MicrosoftReinforceLearner
    from agent_learning_ext.learners import ReinforceLearner

    for learner_class in (ReinforceLearner, MicrosoftReinforceLearner):
        policy = _zero_policy()
        before = policy.snapshot().to_dict()
        episode = _episode([1.0, 0.0])
        with pytest.raises(TypeError):
            learner_class().update(policy, [episode], [_reward(episode, 1.0)])
        assert policy.snapshot().to_dict() == before
        assert policy.snapshot().metadata["context_weights"] == {"a": [0.0, 0.0], "b": [0.0, 0.0]}


def test_story383_ac1_scalar_learner_still_updates_a_softmax_policy_without_reading_the_vector():
    from agent_learning_ext.learners import ReinforceLearner

    policy = _scalar_policy()
    episode = Episode(metadata=_VectorGuard({"feature_vector": [1.0, 0.0]}), action_id="a", action_logprob=HALF)
    result = ReinforceLearner().update(policy, [episode], [_reward(episode, 1.0)])
    assert result.episodes_used == 1
    assert policy.snapshot().logits["a"] > 0.0
