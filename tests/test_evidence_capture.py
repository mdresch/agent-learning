"""Contract tests for opt-in lightweight evidence capture on low-authority decisions.

Story 6.1 (docs/user-stories/epic-6-opt-in-lightweight-evidence-capture-for-low-authority.md)
ADR-006 sections 4.1 to 4.4 and 5 (docs/adr/ADR-006-...)
BRD-006 BRU-006-01 to BRU-006-07, FDD-006 designs 1 to 4 and the error-handling table

Interpretations not stated verbatim in the acceptance criteria (LL-011):
- I1: the flag is read as absent-or-None means False (FDD design 1). `TaskPolicy(snapshot,
  capture_decision_evidence=None)` leaves the snapshot's value alone; an explicit True or False
  sets it. FDD-006 sketches the default as False, which would silently switch off a flag already
  stored on the snapshot, so the default is None here.
- I2: "settable only at initialization or configuration time" (BRU-006-01) means `decide()` never
  writes the flag; the snapshot returned by `TaskPolicy.snapshot()` carries it unchanged.
- I3: `task-policy-init` writes the key (`true`) only when `--capture-decision-evidence` is passed. Without
  the flag the key is absent, which reads as False, so the metadata of a default policy is unchanged
  (an existing contract test in tests/test_cli.py pins that metadata exactly).
- I4: a forced action (`selected_action_id`) goes through the same enforcement as a sampled one.
- I5: the enforcement applies only to the low-authority path (FDD design 2). A full-authority
  decision does not read the flag.
- I6: "verbatim" means equal in value, not the same object; the result holds what the caller passed
  and `to_dict()` returns a plain copy.
- I7: the write-once rule: `EpisodeCapture.start(decision_result=...)` and
  `task-episode-register --decision-result` set `metadata["audit_evidence"]`; a different value
  already present fails (`ValueError`, or exit code 2 with nothing stored); a re-registration
  without the key carries the stored value over; `EpisodeCapture.end()` rejects a different
  `audit_evidence` in `extra_metadata`.
- I8: "no performance overhead" (AC_3) is tested as behavior, not time: with the flag off the
  decision needs no evidence and the learned-policy path is the same as before.
- I10: `task-policy-decide` has no option to pass `audit_evidence`, so on an opted-in low-authority policy
  it exits 2 with a message pointing to the SDK instead of failing inside `decide()`. A CLI way to
  supply the evidence is not part of this story (FDD-006 does not specify one).
- I9: AC_6 is tested by running one REINFORCE update with and without `audit_evidence` in the
  episode metadata and comparing the logits, plus a source scan that no learner, metric, reward or
  policy module mentions `audit_evidence`.
"""

from __future__ import annotations

import copy
import dataclasses
import json
import random
from pathlib import Path

import pytest

from agent_learning import cli
from agent_learning.capture import EpisodeCapture
from agent_learning.config import CaptureConfig, LearnerConfig
from agent_learning.decision import DecisionResult, TaskPolicy, capture_decision_evidence_enabled
from agent_learning.learners import ReinforceLearner
from agent_learning.policy import SoftmaxPolicy
from agent_learning.storage import InMemoryStore
from agent_learning.types import Action, Episode, PolicySnapshot, Reward, RewardSource

ROOT = Path(__file__).resolve().parent.parent
MESSAGE = "TaskPolicy requires non-empty audit_evidence when capture_decision_evidence is enabled"
EVIDENCE = {"source": "reviewer", "inputs": {"files": ["a.py", "b.py"], "score": 0.4}, "free_form": [1, "two", None]}
EPISODE_FIELDS = {
    "action_id", "action_logprob", "action_name", "action_type", "agent_id", "agent_name", "assistant_output",
    "context_features", "conversation_history", "correlation_id", "created_at", "execution_status",
    "expected_outcome", "id", "input_summary", "intent_summary", "metadata", "model_deployment", "policy_id",
    "policy_version", "request_latency_ms", "result_summary", "session_id", "system_message", "target",
    "task_id", "task_name", "token_usage", "tool_calls", "user_input",
}
SNAPSHOT_FIELDS = {
    "id", "agent_id", "version", "actions", "logits", "baseline", "episodes_seen",
    "updates_applied", "metadata", "created_at", "task_id",
}


def _snapshot(*, capture: object = "unset") -> PolicySnapshot:
    snapshot = SoftmaxPolicy.from_actions(
        [Action(id="east"), Action(id="west")], agent_id="agent-1", task_id="choose-region"
    ).snapshot()
    snapshot.metadata = {"policy_scope": "delegated_decision", "decision_context": "Choose a region"}
    if capture != "unset":
        snapshot.metadata["capture_decision_evidence"] = capture
    return snapshot


def _policy(*, capture: object = "unset", **kwargs) -> TaskPolicy:
    return TaskPolicy(_snapshot(capture=capture), rng=random.Random(0), **kwargs)


@pytest.fixture()
def store(monkeypatch: pytest.MonkeyPatch) -> InMemoryStore:
    in_memory = InMemoryStore()
    monkeypatch.setattr(cli, "get_default_store", lambda: in_memory)
    return in_memory


# --- AC_0: the opt-in flag -------------------------------------------------------------------------


def test_ac0_the_flag_defaults_to_false_when_absent() -> None:
    policy = _policy()
    assert "capture_decision_evidence" not in policy.snapshot().metadata
    assert policy.decide().audit_evidence is None  # nothing required


@pytest.mark.parametrize(("argument", "expected"), [(True, True), (False, False)])
def test_ac0_task_policy_initialization_can_set_the_flag(argument: bool, expected: bool) -> None:
    policy = _policy(capture_decision_evidence=argument)
    assert policy.snapshot().metadata["capture_decision_evidence"] is expected


def test_ac0_none_leaves_a_stored_flag_alone() -> None:
    """Interpretation I1."""
    assert _policy(capture=True).snapshot().metadata["capture_decision_evidence"] is True
    assert _policy(capture=True, capture_decision_evidence=None).snapshot().metadata["capture_decision_evidence"] is True
    assert _policy(capture=True, capture_decision_evidence=False).snapshot().metadata["capture_decision_evidence"] is False


def test_ac0_deciding_never_changes_the_flag() -> None:
    """Interpretation I2."""
    policy = _policy(capture=True)
    policy.decide(audit_evidence=EVIDENCE)
    assert policy.snapshot().metadata["capture_decision_evidence"] is True


def _init_policy(store: InMemoryStore, tmp_path: Path, *extra: str) -> PolicySnapshot:
    actions = tmp_path / "actions.json"
    actions.write_text(json.dumps([{"id": "east"}, {"id": "west"}]), encoding="utf-8")
    code = cli.main(
        ["task-policy-init", "--agent-id", "agent-1", "--task-id", "choose-region", "--decision-context",
         "Choose a region", "--actions", str(actions), *extra]
    )
    assert code == 0
    snapshot = store.get_active_policy("agent-1", "choose-region")
    assert snapshot is not None
    return snapshot


def test_ac0_the_cli_init_flag_enables_capture(store: InMemoryStore, tmp_path: Path, capsys) -> None:
    snapshot = _init_policy(store, tmp_path, "--capture-decision-evidence")
    capsys.readouterr()
    assert snapshot.metadata["capture_decision_evidence"] is True


def test_ac0_the_cli_init_without_the_flag_leaves_the_key_absent_which_reads_as_false(
    store: InMemoryStore, tmp_path: Path, capsys
) -> None:
    """Interpretation I3."""
    snapshot = _init_policy(store, tmp_path)
    capsys.readouterr()
    assert "capture_decision_evidence" not in snapshot.metadata
    assert capture_decision_evidence_enabled(snapshot) is False


def test_ac1_the_cli_decide_on_an_opted_in_policy_exits_2_with_a_clear_message(
    store: InMemoryStore, tmp_path: Path, capsys
) -> None:
    """Interpretation I10."""
    _init_policy(store, tmp_path, "--capture-decision-evidence")
    capsys.readouterr()
    code = cli.main(["task-policy-decide", "--agent-id", "agent-1", "--task-id", "choose-region"])
    captured = capsys.readouterr()
    assert code == 2
    assert "audit_evidence" in captured.err and "SDK" in captured.err
    assert captured.out == ""


def test_ac3_the_cli_decide_on_a_default_policy_is_unchanged(store: InMemoryStore, tmp_path: Path, capsys) -> None:
    _init_policy(store, tmp_path)
    capsys.readouterr()
    code = cli.main(["task-policy-decide", "--agent-id", "agent-1", "--task-id", "choose-region", "--seed", "1"])
    out = capsys.readouterr().out
    assert code == 0 and json.loads(out)["decision_authority"] == "low"


def test_ac0_there_is_no_separate_toggle_subcommand() -> None:
    parser_source = (ROOT / "src" / "agent_learning" / "cli.py").read_text(encoding="utf-8")
    assert "task-policy-evidence-capture-set" not in parser_source


# --- AC_1: presence enforced on an opted policy -------------------------------------------------------


@pytest.mark.parametrize("bad", [None, {}, "text", ["a", "b"], 5, [("a", 1)]])
def test_ac1_an_opted_low_policy_rejects_missing_empty_or_non_mapping_evidence(bad: object) -> None:
    policy = _policy(capture=True)
    with pytest.raises(ValueError, match=MESSAGE):
        policy.decide(audit_evidence=bad)  # type: ignore[arg-type]


def test_ac1_a_forced_action_goes_through_the_same_check() -> None:
    """Interpretation I4."""
    policy = _policy(capture=True)
    with pytest.raises(ValueError, match=MESSAGE):
        policy.decide(selected_action_id="east")
    assert policy.decide(selected_action_id="east", audit_evidence={"why": "operator"}).proposed_action.id == "east"


def test_ac1_a_failed_check_does_not_change_the_policy() -> None:
    policy = _policy(capture=True)
    before = policy.snapshot().to_dict()
    with pytest.raises(ValueError):
        policy.decide()
    assert policy.snapshot().to_dict() == before


def test_ac1_the_check_reads_the_stored_flag_not_a_default() -> None:
    policy = _policy(capture=False)
    assert policy.decide().audit_evidence is None  # no error: the flag is off


# --- AC_2: verbatim attachment ------------------------------------------------------------------------------


def test_ac2_a_valid_mapping_is_attached_verbatim() -> None:
    evidence = copy.deepcopy(EVIDENCE)
    result = _policy(capture=True).decide(audit_evidence=evidence)
    assert isinstance(result, DecisionResult)
    assert result.audit_evidence == EVIDENCE  # interpretation I6: equal in value
    assert evidence == EVIDENCE  # the caller's mapping was not changed


def test_ac2_the_sdk_does_no_schema_filtering_or_reasoning() -> None:
    odd = {"": 1, "nested": {"a": {"b": {"c": [{"d": None}]}}}, "weights": {"x": 99.0}, "decision": "approve"}
    result = _policy(capture=True).decide(audit_evidence=odd)
    assert result.audit_evidence == odd
    assert result.proposed_action is not None  # selection did not read the evidence


# --- AC_3: the default low-authority path is unchanged ---------------------------------------------------------


def test_ac3_with_the_flag_off_no_evidence_is_needed() -> None:
    """Interpretation I8."""
    for capture in ("unset", False, None):
        result = _policy(capture=capture).decide()
        assert result.audit_evidence is None
        assert result.selection_basis == "learned_policy"


def test_ac3_with_the_flag_off_optional_evidence_is_still_attached() -> None:
    result = _policy(capture=False).decide(audit_evidence={"note": "optional"})
    assert result.audit_evidence == {"note": "optional"}


def test_ac3_the_chosen_action_does_not_depend_on_the_evidence() -> None:
    seq_without = [_policy().decide().proposed_action.id for _ in range(1)]
    left = TaskPolicy(_snapshot(), rng=random.Random(7))
    right = TaskPolicy(_snapshot(capture=True), rng=random.Random(7))
    chosen_left = [left.decide().proposed_action.id for _ in range(20)]
    chosen_right = [right.decide(audit_evidence={"k": i}).proposed_action.id for i in range(20)]
    assert chosen_left == chosen_right
    assert seq_without


# --- AC_4: serialization -----------------------------------------------------------------------------------------


@pytest.mark.parametrize("evidence", [None, {}, EVIDENCE, {"a": {"b": [1, 2, {"c": None}]}}])
def test_ac4_round_trip_keeps_the_evidence_exactly(evidence: object) -> None:
    result = _policy(capture=False).decide(audit_evidence=evidence)  # type: ignore[arg-type]
    payload = json.loads(json.dumps(result.to_dict()))
    restored = DecisionResult.from_dict(payload)
    assert restored.audit_evidence == evidence
    assert restored.to_dict()["audit_evidence"] == evidence


def test_ac4_an_empty_mapping_is_kept_as_empty_not_turned_into_none() -> None:
    result = _policy(capture=False).decide(audit_evidence={})
    assert result.to_dict()["audit_evidence"] == {}


# --- AC_5: propagation and write-once --------------------------------------------------------------------------------


def _capture(store: InMemoryStore) -> EpisodeCapture:
    return EpisodeCapture(CaptureConfig(enabled=True, agent_id="agent-1", task_id="choose-region"), store)


def _result(evidence: object = EVIDENCE) -> DecisionResult:
    return _policy(capture=False).decide(audit_evidence=evidence)  # type: ignore[arg-type]


def test_ac5_capture_start_copies_the_evidence_into_the_episode_metadata() -> None:
    store = InMemoryStore()
    capture = _capture(store)
    context = capture.start("choose", decision_result=_result())
    assert context.metadata["audit_evidence"] == EVIDENCE
    episode = capture.end(context, "done", execution_status="completed", result_summary="ok")
    assert episode is not None and episode.metadata["audit_evidence"] == EVIDENCE


def test_ac5_capture_start_without_evidence_adds_no_key() -> None:
    capture = _capture(InMemoryStore())
    context = capture.start("choose", decision_result=_result(None))
    assert "audit_evidence" not in context.metadata
    assert "audit_evidence" not in capture.start("choose").metadata


def test_ac5_capture_start_copies_rather_than_aliases_the_evidence() -> None:
    result = _result(copy.deepcopy(EVIDENCE))
    context = _capture(InMemoryStore()).start("choose", decision_result=result)
    context.metadata["audit_evidence"]["source"] = "changed"
    assert result.audit_evidence["source"] == "reviewer"


def test_ac5_capture_start_rejects_a_different_value_already_in_the_metadata() -> None:
    """Interpretation I7: write-once."""
    capture = _capture(InMemoryStore())
    with pytest.raises(ValueError, match="audit_evidence"):
        capture.start("choose", decision_result=_result(), metadata={"audit_evidence": {"other": 1}})
    same = capture.start("choose", decision_result=_result(), metadata={"audit_evidence": EVIDENCE})
    assert same.metadata["audit_evidence"] == EVIDENCE


def test_ac5_capture_end_keeps_the_value_and_rejects_a_different_one_in_extra_metadata() -> None:
    store = InMemoryStore()
    capture = _capture(store)
    context = capture.start("choose", decision_result=_result())
    episode = capture.end(context, "done", extra_metadata={"feedback_status": "accepted"})
    assert episode.metadata["audit_evidence"] == EVIDENCE and episode.metadata["feedback_status"] == "accepted"
    with pytest.raises(ValueError, match="audit_evidence"):
        capture.end(context, "done", extra_metadata={"audit_evidence": {"other": 1}})


def _episode_file(tmp_path: Path, name: str, **fields: object) -> Path:
    payload = {"id": "ep-1", "agent_id": "agent-1", "task_id": "choose-region", "user_input": "x", "assistant_output": ""}
    payload.update(fields)
    path = tmp_path / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _result_file(tmp_path: Path, evidence: object = EVIDENCE, name: str = "result.json") -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(_result(evidence).to_dict()), encoding="utf-8")
    return path


def _register(episode: Path, *extra: str) -> int:
    return cli.main(["task-episode-register", "--agent-id", "agent-1", "--task-id", "choose-region",
                     "--episode", str(episode), *extra])


def _stored(store: InMemoryStore) -> Episode:
    episode = store.get_episode("ep-1", "agent-1")
    assert episode is not None
    return episode


def test_ac5_the_cli_copies_the_evidence_from_a_decision_result(store: InMemoryStore, tmp_path: Path, capsys) -> None:
    code = _register(_episode_file(tmp_path, "e.json"), "--decision-result", str(_result_file(tmp_path)))
    capsys.readouterr()
    assert code == 0
    assert _stored(store).metadata["audit_evidence"] == EVIDENCE


def test_ac5_the_cli_with_a_result_that_has_no_evidence_adds_no_key(store: InMemoryStore, tmp_path: Path, capsys) -> None:
    code = _register(_episode_file(tmp_path, "e.json"), "--decision-result", str(_result_file(tmp_path, None)))
    capsys.readouterr()
    assert code == 0 and "audit_evidence" not in _stored(store).metadata


def test_ac5_the_cli_rejects_an_episode_file_with_a_different_value(store: InMemoryStore, tmp_path: Path, capsys) -> None:
    episode = _episode_file(tmp_path, "e.json", metadata={"audit_evidence": {"other": 1}})
    code = _register(episode, "--decision-result", str(_result_file(tmp_path)))
    assert code == 2 and "audit_evidence" in capsys.readouterr().err
    assert store.get_episode("ep-1", "agent-1") is None


def test_ac5_a_completion_without_the_key_carries_the_stored_value_over(store: InMemoryStore, tmp_path: Path, capsys) -> None:
    assert _register(_episode_file(tmp_path, "e1.json"), "--decision-result", str(_result_file(tmp_path))) == 0
    completion = _episode_file(
        tmp_path, "e2.json", assistant_output="done", execution_status="completed",
        intent_summary="i", expected_outcome="o", result_summary="r", metadata={"feedback_status": "accepted"},
    )
    assert _register(completion) == 0
    capsys.readouterr()
    stored = _stored(store)
    assert stored.metadata["audit_evidence"] == EVIDENCE
    assert stored.metadata["feedback_status"] == "accepted"
    assert stored.assistant_output == "done"


def test_ac5_re_registering_the_same_value_changes_nothing(store: InMemoryStore, tmp_path: Path, capsys) -> None:
    assert _register(_episode_file(tmp_path, "e1.json"), "--decision-result", str(_result_file(tmp_path))) == 0
    assert _register(_episode_file(tmp_path, "e2.json", metadata={"audit_evidence": EVIDENCE})) == 0
    capsys.readouterr()
    assert _stored(store).metadata["audit_evidence"] == EVIDENCE


def test_ac5_re_registering_a_different_value_fails_and_stores_nothing(store: InMemoryStore, tmp_path: Path, capsys) -> None:
    assert _register(_episode_file(tmp_path, "e1.json"), "--decision-result", str(_result_file(tmp_path))) == 0
    before = _stored(store).to_dict()
    code = _register(_episode_file(tmp_path, "e2.json", assistant_output="changed", metadata={"audit_evidence": {"other": 1}}))
    assert code == 2 and "audit_evidence" in capsys.readouterr().err
    assert _stored(store).to_dict() == before


def test_ac5_an_unreadable_decision_result_exits_2(store: InMemoryStore, tmp_path: Path, capsys) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("not json", encoding="utf-8")
    assert _register(_episode_file(tmp_path, "e.json"), "--decision-result", str(bad)) == 2
    assert store.get_episode("ep-1", "agent-1") is None


def test_ac5_no_new_record_type_or_field(store: InMemoryStore) -> None:
    assert {f.name for f in dataclasses.fields(Episode)} == EPISODE_FIELDS
    assert {f.name for f in dataclasses.fields(PolicySnapshot)} == SNAPSHOT_FIELDS


# --- AC_6: learner and storage decoupling ----------------------------------------------------------------------------


def _train(evidence: object) -> dict[str, float]:
    policy = SoftmaxPolicy.from_actions(
        [Action(id="a"), Action(id="b")], agent_id="nba", rng=random.Random(0)
    )
    learner = ReinforceLearner(LearnerConfig(learning_rate=0.5, entropy_bonus=0.0))
    episodes, rewards = [], []
    for index in range(12):
        metadata = {"audit_evidence": evidence} if evidence is not None else {}
        episode = Episode(
            agent_id="nba", user_input="x", assistant_output="y",
            action_id="a" if index % 3 else "b", action_logprob=-0.693147, metadata=metadata,
        )
        episodes.append(episode)
        rewards.append(Reward(episode_id=episode.id, agent_id="nba", source=RewardSource.AGGREGATE, value=0.9 if index % 3 else 0.1))
    learner.update(policy, episodes, rewards)
    return dict(policy.snapshot().logits)


def test_ac6_training_gives_the_same_logits_with_and_without_evidence() -> None:
    assert _train(None) == _train({"huge": ["x"] * 50, "score": 123.0})


def test_ac6_episodes_with_evidence_store_and_reload_without_a_schema_error() -> None:
    store = InMemoryStore()
    episode = Episode(agent_id="nba", user_input="x", assistant_output="y", metadata={"audit_evidence": EVIDENCE})
    store.store_episode(episode)
    loaded = store.get_episode(episode.id, "nba")
    assert loaded is not None and loaded.metadata["audit_evidence"] == EVIDENCE
    assert Episode.from_dict(loaded.to_dict()).metadata["audit_evidence"] == EVIDENCE


@pytest.mark.parametrize("package", ["learners", "metrics", "rewards", "policy"])
def test_ac6_no_learner_metric_reward_or_policy_module_mentions_audit_evidence(package: str) -> None:
    """Interpretation I9 (BRU-006-06)."""
    offenders = [
        str(path.relative_to(ROOT))
        for path in (ROOT / "src" / "agent_learning" / package).rglob("*.py")
        if "audit_evidence" in path.read_text(encoding="utf-8")
    ]
    assert offenders == []
