"""Contract tests for Epic 15, Story 15.3 (Choosing by Probability Matching).

Story: docs/user-stories/epic-15-bayesian-bandit-posterior-sampling.md, Story 15.3.
ADR-015 Invariants and §4.3; BRD-015 BRU-015-02; FDD-015 §2.3, §3 item 3 and D2, D3, D5.

Interpretation I1: the story says the policy "supplies" a request id and a timestamp when they are
not given (FDD-015 §3 item 3.1: a new UUID, the current UTC time in ISO 8601). AC_2 asserts only
that both are non-empty strings that are recorded and that the record replays.

Interpretation I2: ``last_sampling_record()`` is ``None`` before the first ``choose``; the FDD does
not say. It is a deep copy on every call (FDD-015 §3 item 3.5).

Interpretation I3: ``Decision.probabilities`` is the draw-free posterior mean ``alpha / (alpha +
beta)`` normalised over the actions, for display only (FDD-015 §3 item 3.4). The story does not
assert it; this file pins it so the docstring's claim is tested.

Interpretation I4: an explicitly empty ``request_id`` or ``timestamp`` is not "missing"; it reaches
``seed_for`` and raises ``ValueError`` naming the argument (FDD-015 §3 item 1).

Interpretation I5: the policy id in the seed is ``snapshot.id`` (the story's AC_0 wording). A
learner update gives the snapshot a new id (``advance_version``), so a record made before the
update replays against the id the policy had then.
"""

from __future__ import annotations

import copy
import json
import random
import typing

import pytest

from agent_learning.policy.base import Decision
from agent_learning.policy.thompson import ThompsonPolicy, replay, seed_for
from agent_learning.types import Action, PolicySnapshot

ACTIONS = [Action(id="a"), Action(id="b"), Action(id="c")]
TS = "2026-10-29T08:00:00+00:00"


def _policy(alpha: dict | None = None, beta: dict | None = None) -> ThompsonPolicy:
    snapshot = PolicySnapshot(
        agent_id="agent",
        task_id="task",
        actions=list(ACTIONS),
        logits={a.id: 0.0 for a in ACTIONS},
        metadata={"posterior_parameters": {"alpha": alpha or {}, "beta": beta or {}}},
    )
    return ThompsonPolicy.from_snapshot(snapshot)


def _expected_draws(policy: ThompsonPolicy, request_id: str, timestamp: str) -> dict[str, float]:
    snap = policy.snapshot()
    post = snap.metadata["posterior_parameters"]
    rng = random.Random(seed_for(snap.id, request_id, timestamp))
    return {a.id: rng.betavariate(post["alpha"][a.id], post["beta"][a.id]) for a in snap.actions}


def test_ac0_chooses_the_highest_of_the_recomputed_draws() -> None:
    policy = _policy({"a": 4, "b": 3, "c": 3}, {"a": 3, "b": 3, "c": 3})
    seen = set()
    for i in range(40):
        request_id = f"req-{i}"
        decision = policy.choose(request_id=request_id, timestamp=TS)
        draws = _expected_draws(policy, request_id, TS)
        assert decision.action.id == max(draws, key=draws.get)
        seen.add(decision.action.id)
    assert len(seen) >= 2, "the fixture should make at least two actions win"


def test_ac0_a_tie_goes_to_the_earlier_action(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(random.Random, "betavariate", lambda self, alpha, beta: 0.5)
    policy = _policy()
    assert policy.choose(request_id="r", timestamp=TS).action.id == "a"


def test_ac0_the_same_request_gives_the_same_action_and_draws() -> None:
    policy = _policy({"a": 4, "b": 4, "c": 4}, {"a": 4, "b": 4, "c": 4})
    first = policy.choose(request_id="r", timestamp=TS)
    first_record = policy.last_sampling_record()
    second = policy.choose(request_id="r", timestamp=TS)
    assert first.action.id == second.action.id
    assert policy.last_sampling_record() == first_record


def test_ac1_the_record_has_the_fdd_shape() -> None:
    policy = _policy({"a": 14, "b": 3}, {"a": 2, "b": 8})
    assert policy.last_sampling_record() is None
    policy.choose(request_id="req-001", timestamp=TS)
    record = policy.last_sampling_record()

    snap = policy.snapshot()
    assert set(record) == {"request_id", "timestamp", "prng_seed", "posterior_parameters", "sampled_payoffs"}
    assert record["request_id"] == "req-001"
    assert record["timestamp"] == TS
    assert record["prng_seed"] == str(seed_for(snap.id, "req-001", TS))
    assert isinstance(record["prng_seed"], str)
    assert record["posterior_parameters"] == snap.metadata["posterior_parameters"]
    assert record["posterior_parameters"] == {
        "alpha": {"a": 14.0, "b": 3.0, "c": 1.0},
        "beta": {"a": 2.0, "b": 8.0, "c": 1.0},
    }
    assert list(record["sampled_payoffs"]) == ["a", "b", "c"]
    assert record["sampled_payoffs"] == _expected_draws(policy, "req-001", TS)
    assert json.loads(json.dumps(record)) == record


def test_ac1_mutating_the_returned_record_does_not_change_the_next_one() -> None:
    policy = _policy({"a": 14, "b": 3}, {"a": 2, "b": 8})
    policy.choose(request_id="r", timestamp=TS)
    record = policy.last_sampling_record()
    pristine = copy.deepcopy(record)

    record["sampled_payoffs"]["a"] = 99.0
    record["posterior_parameters"]["alpha"]["a"] = 99.0
    record["request_id"] = "tampered"

    assert policy.last_sampling_record() == pristine
    policy.choose(request_id="r", timestamp=TS)
    assert policy.last_sampling_record() == pristine
    assert policy.posterior()["alpha"]["a"] == 14.0


def test_ac1_the_record_replays() -> None:
    policy = _policy({"a": 14, "b": 3}, {"a": 2, "b": 8})
    policy.choose(request_id="req-001", timestamp=TS)
    record = policy.last_sampling_record()
    assert replay(record, policy.snapshot().id) == record["sampled_payoffs"]
    assert replay(json.loads(json.dumps(record)), policy.snapshot().id) == record["sampled_payoffs"]


def test_ac2_choose_with_no_arguments_supplies_and_records_both() -> None:
    policy = _policy({"a": 3, "b": 3}, {"a": 3, "b": 3})
    policy.choose()
    first = policy.last_sampling_record()
    policy.choose()
    second = policy.last_sampling_record()

    for record in (first, second):
        assert isinstance(record["request_id"], str) and record["request_id"]
        assert isinstance(record["timestamp"], str) and record["timestamp"]
        assert replay(record, policy.snapshot().id) == record["sampled_payoffs"]
    assert first["request_id"] != second["request_id"]


def test_ac2_only_the_missing_argument_is_supplied() -> None:
    policy = _policy()
    policy.choose(request_id="given")
    assert policy.last_sampling_record()["request_id"] == "given"
    assert policy.last_sampling_record()["timestamp"]

    policy.choose(timestamp=TS)
    assert policy.last_sampling_record()["timestamp"] == TS
    assert policy.last_sampling_record()["request_id"] != "given"


@pytest.mark.parametrize(("kwargs", "name"), [({"request_id": ""}, "request_id"), ({"timestamp": ""}, "timestamp")])
def test_i4_an_explicitly_empty_argument_is_refused_by_name(kwargs: dict, name: str) -> None:
    with pytest.raises(ValueError, match=name):
        _policy().choose(**kwargs)


def test_ac3_the_decision_has_no_log_probability() -> None:
    decision = _policy().choose(request_id="r", timestamp=TS)
    assert decision.logprob is None
    assert typing.get_type_hints(Decision)["logprob"] == (float | None)


def test_i3_probabilities_are_the_normalised_posterior_means() -> None:
    policy = _policy({"a": 14, "b": 3}, {"a": 2, "b": 8})
    decision = policy.choose(request_id="r", timestamp=TS)
    means = [14 / 16, 3 / 11, 0.5]
    expected = [m / sum(means) for m in means]
    assert decision.probabilities == pytest.approx(expected)
    assert sum(decision.probabilities) == pytest.approx(1.0)


def test_ac4_a_less_certain_action_is_still_tried() -> None:
    snapshot = PolicySnapshot(
        agent_id="agent",
        task_id="task",
        actions=[Action(id="a"), Action(id="b")],
        logits={"a": 0.0, "b": 0.0},
        metadata={"posterior_parameters": {"alpha": {"a": 2.0, "b": 1.0}, "beta": {"a": 1.0, "b": 1.0}}},
    )
    policy = ThompsonPolicy.from_snapshot(snapshot)
    counts = {"a": 0, "b": 0}
    for i in range(2000):
        counts[policy.choose(request_id=f"req-{i}", timestamp=TS).action.id] += 1
    assert counts["b"] >= 1
    assert counts["a"] > counts["b"]


def test_ac5_apply_update_points_at_the_learner() -> None:
    with pytest.raises(TypeError, match="ThompsonLearner"):
        _policy().apply_update({"a": 1.0}, baseline=0.0, episodes_seen=1)


def test_choose_does_not_change_the_snapshot() -> None:
    policy = _policy({"a": 14}, {"a": 2})
    before = policy.snapshot().to_dict()
    policy.choose(request_id="r", timestamp=TS)
    assert policy.snapshot().to_dict() == before
