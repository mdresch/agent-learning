"""Contract tests for the contextual-policy CLI changes in `agent_learning_ext.cli`.

Stories 38.4, 38.5 and 38.6 share this file; each story's interpretations are labelled with its number.

Story 38.4 (docs/user-stories/epic-38-packaged-contextual-learning.md)
ADR-038 sections 4.3 and 7 (docs/adr/ADR-038-packaged-contextual-learning.md)
BRD-038 BRU-038-07, FDD-038 sections 2.2 and 3.1 (docs/project-docs/...)

Interpretations for 38.4 (LL-011; I1 to I4 come from `scripts/spec_gate.py 38.4 --no-persist`, verdict
PASSED, robust margin +0.0975; I5 to I8 are this story's own):
- I1 (gate): the stored snapshot survives json.dumps / json.loads without a custom decoder.
- I2 (gate): empty-collection case. Not applicable to the init command (no episodes); the nearest
  case is a refused init, which must leave the store empty.
- I3 (gate): non-finite floats. Not applicable to `--feature-dim` (an int); a non-integer value is an
  argparse failure (FDD-038 3.1), tested as exit 2 with nothing stored.
- I4 (gate): float comparisons use `pytest.approx`; the weight rows here are exact zeros.
- I5: "exits 2" is observed as either `main` returning 2 or argparse raising `SystemExit(2)`, so the
  non-integer case (argparse) and the `0` / `-1` cases (command body) share one helper.
- I6: "stores no policy" is `store.get_active_policy(agent, task) is None` on a fresh store.
- I7: AC_4 compares against an init without the flag: it must lack `feature_dim`, `context_weights`
  and `policy_kind`, with `low` and `full` authority.
- I8: the printed payload of a contextual init is not specified by 38.4 (Story 38.6 AC_2 owns its
  `action_probabilities` rule), so nothing here asserts it beyond the command exiting 0 with JSON.
- Stores are `InMemoryStore` objects patched in through `cli.get_default_store`; the real
  LearningStore is never touched.

Story 38.5 (same documents; ADR-038 4.3, BRD-038 BRU-038-08 and BRU-038-09, FDD-038 2.3, 3.2, D1, D3).
Interpretations (LL-011; 38.5-I1 to 38.5-I3 come from `scripts/spec_gate.py 38.5 --no-persist`, verdict
PASSED, robust margin +0.1963; 38.5-I4 onward are this story's own):
- 38.5-I1 (gate): the printed payload survives json.loads (it is parsed from stdout in every test).
- 38.5-I2 (gate): empty-collection case. The nearest case is the empty list `[]`, which has the wrong
  length for any `feature_dim` >= 1 and is refused.
- 38.5-I3 (gate): probabilities are compared with `pytest.approx(abs=1e-9)`.
- 38.5-I4: "unchanged store" means the stored policy list (every version, as JSON) is identical before and
  after and `query_episodes` still returns nothing. A refusal and a successful decide both write nothing.
- 38.5-I5: "a JSON object" is `{"a": 1.0}`; other refused inputs are non-JSON text, a JSON scalar, a string
  element, `true`, `NaN`, `Infinity`, `-Infinity`, an overflowing literal, and a list of the wrong length
  (`[]`, 1 and 3 elements).
- 38.5-I6: `selection_mode` is `greedy` with `--greedy` and `sampled` without it; `--seed` makes the sampled draw
  repeatable and changes nothing under `--greedy` (FDD-038 3.2 step 4).
- 38.5-I7: "the command's existing evidence message" is the text containing `capture_decision_evidence` and
  `audit_evidence` that the scalar path prints today.
- 38.5-I8: a contextual snapshot whose stored authority is `full` exits 2 and writes nothing (FDD-038 3.2, last
  paragraph; init cannot create the pair). Its stderr names `full` and `contextual`.
- 38.5-I9: `--decision-frame` on a contextual snapshot is refused as it is for any low-authority policy, after
  the `--features` check (FDD-038 3.2 steps 1 and 2).
- 38.5-I10: "no autonomy block" is the absence of the key `autonomy` in the payload.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from agent_learning.policy import ContextualSoftmaxPolicy, SoftmaxPolicy
from agent_learning.storage import InMemoryStore
from agent_learning.types import Action
from agent_learning_ext import cli

AGENT = "agent-1"
TASK = "choose-region"


@pytest.fixture()
def store(monkeypatch: pytest.MonkeyPatch) -> InMemoryStore:
    in_memory = InMemoryStore()
    monkeypatch.setattr(cli, "get_default_store", lambda: in_memory)
    return in_memory


@pytest.fixture()
def actions_file(tmp_path: Path) -> Path:
    path = tmp_path / "actions.json"
    path.write_text(
        json.dumps([{"id": "a", "description": "first"}, {"id": "b", "description": "second"}]),
        encoding="utf-8",
    )
    return path


def _run(argv: list[str]) -> int:
    try:
        return cli.main(argv)
    except SystemExit as exc:  # argparse failures
        return int(exc.code) if isinstance(exc.code, int) else 1


def _init(actions_file: Path, *extra: str) -> int:
    return _run(
        [
            "task-policy-init", "--agent-id", AGENT, "--task-id", TASK,
            "--decision-context", "Choose a region", "--actions", str(actions_file), *extra,
        ]
    )


def _stored(store: InMemoryStore):
    snapshot = store.get_active_policy(AGENT, TASK)
    assert snapshot is not None, "no active policy for agent-1 / choose-region"
    return snapshot


# --- Story 38.4 -------------------------------------------------------------------------------------


def test_38_4_ac0_shape(store: InMemoryStore, actions_file: Path, capsys) -> None:
    assert _init(actions_file, "--feature-dim", "3") == 0
    capsys.readouterr()
    snapshot = _stored(store)
    meta = snapshot.metadata
    assert meta["policy_kind"] == "contextual_softmax"
    assert meta["feature_dim"] == 3
    assert meta["context_weights"] == {"a": [0.0, 0.0, 0.0], "b": [0.0, 0.0, 0.0]}
    assert snapshot.logits == {"a": 0.0, "b": 0.0}
    assert meta["decision_authority"] == "low"
    # The decision fields written today are still written.
    assert meta["policy_scope"] == cli._DECISION_POLICY_SCOPE
    assert meta["decision_context"] == "Choose a region"
    assert "complexity_profile" in meta
    assert meta["complexity_profile_source"] == "default"
    # I1: JSON round trip.
    assert json.loads(json.dumps(snapshot.to_dict()))["metadata"]["feature_dim"] == 3


def test_38_4_ac1_source_default_when_authority_omitted(store, actions_file: Path) -> None:
    assert _init(actions_file, "--feature-dim", "2") == 0
    meta = _stored(store).metadata
    assert meta["decision_authority_source"] == "default"
    assert meta["decision_authority"] == "low"


def test_38_4_ac1_source_configured_when_authority_low(store, actions_file: Path) -> None:
    assert _init(actions_file, "--feature-dim", "2", "--decision-authority", "low") == 0
    meta = _stored(store).metadata
    assert meta["decision_authority_source"] == "configured"
    assert meta["decision_authority"] == "low"


def test_38_4_ac2_full_authority_is_refused(store, actions_file: Path, capsys) -> None:
    capsys.readouterr()
    code = _init(actions_file, "--feature-dim", "3", "--decision-authority", "full")
    err = capsys.readouterr().err
    assert code == 2
    assert "feature-dim" in err and "full" in err
    assert store.get_active_policy(AGENT, TASK) is None


@pytest.mark.parametrize("value", ["0", "-1"])
def test_38_4_ac3_bad_dimension_is_refused(store, actions_file: Path, value: str, capsys) -> None:
    capsys.readouterr()
    assert _init(actions_file, "--feature-dim", value) == 2
    # The flag must exist: an "unrecognized arguments" exit 2 would pass this test for the wrong reason.
    assert "unrecognized" not in capsys.readouterr().err
    assert store.get_active_policy(AGENT, TASK) is None


def test_38_4_ac3_non_integer_dimension_is_refused(store, actions_file: Path, capsys) -> None:
    capsys.readouterr()
    assert _init(actions_file, "--feature-dim", "2.5") == 2
    assert "unrecognized" not in capsys.readouterr().err
    assert store.get_active_policy(AGENT, TASK) is None


@pytest.mark.parametrize("authority", [None, "low", "full"])
def test_38_4_ac4_omitted_flag_stores_no_contextual_keys(
    store, actions_file: Path, authority: str | None
) -> None:
    extra = ["--decision-authority", authority] if authority else []
    assert _init(actions_file, *extra) == 0
    meta = _stored(store).metadata
    assert "context_weights" not in meta
    assert "feature_dim" not in meta
    assert "policy_kind" not in meta


# --- Story 38.5 -------------------------------------------------------------------------------------


def _decision_meta(snapshot, *, authority: str = "low", evidence: bool = False):
    snapshot.metadata.update(
        {
            "policy_scope": cli._DECISION_POLICY_SCOPE,
            "decision_context": "Choose a region",
            "decision_authority": authority,
            "decision_authority_source": "configured",
        }
    )
    if evidence:
        snapshot.metadata["capture_decision_evidence"] = True
    return snapshot


def _contextual(
    store: InMemoryStore,
    *,
    weights: dict[str, list[float]] | None = None,
    logits: dict[str, float] | None = None,
    authority: str = "low",
    evidence: bool = False,
):
    policy = ContextualSoftmaxPolicy.from_actions(
        [Action(id="a"), Action(id="b")],
        feature_dim=2,
        agent_id=AGENT,
        task_id=TASK,
        initial_weights=weights,
    )
    snapshot = _decision_meta(policy.snapshot(), authority=authority, evidence=evidence)
    if logits is not None:
        snapshot.logits = dict(logits)
    store.store_policy(snapshot)
    return snapshot


def _scalar(store: InMemoryStore):
    snapshot = SoftmaxPolicy.from_actions(
        [Action(id="a"), Action(id="b")], agent_id=AGENT, task_id=TASK
    ).snapshot()
    store.store_policy(_decision_meta(snapshot))
    return snapshot


def _fingerprint(store: InMemoryStore) -> str:
    policies = [p.to_dict() for p in store.list_policies(AGENT, TASK)]
    episodes = store.query_episodes(AGENT, task_id=TASK, limit=50)
    return json.dumps(
        {"policies": policies, "episodes": [e.to_dict() for e in episodes]}, sort_keys=True
    )


def _decide(*extra: str) -> int:
    return _run(["task-policy-decide", "--agent-id", AGENT, "--task-id", TASK, *extra])


def _decide_ok(capsys, *extra: str) -> dict:
    capsys.readouterr()
    assert _decide(*extra) == 0
    return json.loads(capsys.readouterr().out)


REFUSED_FEATURES = [
    pytest.param('{"a": 1.0}', id="object"),
    pytest.param("[1.0]", id="too-short"),
    pytest.param("[1.0, 0.0, 2.0]", id="too-long"),
    pytest.param("[]", id="empty"),
    pytest.param("[true, 0.0]", id="bool-element"),
    pytest.param('["1", "0"]', id="string-elements"),
    pytest.param("[NaN, 0.0]", id="nan"),
    pytest.param("[Infinity, 0.0]", id="inf"),
    pytest.param("[1.0, -Infinity]", id="neg-inf"),
    pytest.param("[1e999, 0.0]", id="overflow-float"),
    pytest.param("1.0", id="scalar"),
    pytest.param("not json", id="not-json"),
]


def test_38_5_ac0_missing_features_is_refused(store, capsys) -> None:
    _contextual(store)
    before = _fingerprint(store)
    capsys.readouterr()
    assert _decide() == 2
    assert "--features" in capsys.readouterr().err
    assert _fingerprint(store) == before


@pytest.mark.parametrize("text", REFUSED_FEATURES)
def test_38_5_ac0_unusable_features_are_refused(store, capsys, text: str) -> None:
    _contextual(store)
    before = _fingerprint(store)
    capsys.readouterr()
    assert _decide("--features", text) == 2
    err = capsys.readouterr().err
    assert "--features" in err and "unrecognized" not in err
    assert _fingerprint(store) == before


def test_38_5_ac0_features_on_a_scalar_snapshot_is_refused(store, capsys) -> None:
    _scalar(store)
    before = _fingerprint(store)
    capsys.readouterr()
    assert _decide("--features", "[1.0, 0.0]") == 2
    err = capsys.readouterr().err
    assert "--features" in err and "unrecognized" not in err
    assert _fingerprint(store) == before


def test_38_5_ac1_payload(store, capsys) -> None:
    snapshot = _contextual(store)
    before = _fingerprint(store)
    payload = _decide_ok(capsys, "--features", "[1.0, 0.0]")
    assert payload["feature_vector"] == [1.0, 0.0]
    assert payload["selection_mode"] in {"sampled", "greedy"}
    expected = ContextualSoftmaxPolicy.from_snapshot(snapshot).probabilities([1.0, 0.0])
    assert payload["action_probabilities"] == pytest.approx(dict(zip(["a", "b"], expected)), abs=1e-9)
    assert payload["selected_action"]["id"] in {"a", "b"}
    assert _fingerprint(store) == before  # no episode, no new policy version


def test_38_5_ac1_integer_elements_are_printed_as_floats(store, capsys) -> None:
    _contextual(store)
    payload = _decide_ok(capsys, "--features", "[1, 0]")
    assert payload["feature_vector"] == [1.0, 0.0]
    assert all(isinstance(x, float) for x in payload["feature_vector"])


def test_38_5_ac2_greedy_takes_the_unique_maximum(store, capsys) -> None:
    snapshot = _contextual(store, weights={"a": [0.0, 0.0], "b": [2.0, 0.0]})
    payload = _decide_ok(capsys, "--features", "[1.0, 0.0]", "--greedy")
    probs = ContextualSoftmaxPolicy.from_snapshot(snapshot).probabilities([1.0, 0.0])
    assert payload["selection_mode"] == "greedy"
    assert payload["selected_action"]["id"] == "b"
    assert payload["selected_action"]["probability"] == pytest.approx(probs[1], abs=1e-9)
    assert payload["selected_action"]["logprob"] == pytest.approx(math.log(probs[1]), abs=1e-9)


def test_38_5_ac2_greedy_tie_keeps_the_earlier_action(store, capsys) -> None:
    _contextual(store)
    payload = _decide_ok(capsys, "--features", "[1.0, 0.0]", "--greedy")
    assert payload["selected_action"]["id"] == "a"
    assert payload["selected_action"]["logprob"] == pytest.approx(math.log(0.5), abs=1e-9)


def test_38_5_ac3_greedy_ignores_the_scalar_logits(store, capsys) -> None:
    _contextual(store, weights={"a": [0.0, 0.0], "b": [2.0, 0.0]}, logits={"a": 5.0, "b": 0.0})
    payload = _decide_ok(capsys, "--features", "[1.0, 0.0]", "--greedy")
    assert payload["selected_action"]["id"] == "b"
    assert "autonomy" not in payload


def test_38_5_ac3_seed_changes_only_the_sampled_draw(store, capsys) -> None:
    _contextual(store, weights={"a": [0.0, 0.0], "b": [0.3, 0.0]})
    greedy = [
        _decide_ok(capsys, "--features", "[1.0, 0.0]", "--greedy", "--seed", str(seed))
        for seed in (1, 2, 3)
    ]
    assert all(p == greedy[0] for p in greedy)
    draws = {
        seed: _decide_ok(capsys, "--features", "[1.0, 0.0]", "--seed", str(seed))
        for seed in range(40)
    }
    repeat = _decide_ok(capsys, "--features", "[1.0, 0.0]", "--seed", "7")
    assert repeat == draws[7]
    assert {p["selected_action"]["id"] for p in draws.values()} == {"a", "b"}
    for payload in draws.values():
        assert payload["selection_mode"] == "sampled"
        assert payload["action_probabilities"] == draws[0]["action_probabilities"]
        assert payload["feature_vector"] == [1.0, 0.0]


def test_38_5_ac4_evidence_opt_in_is_refused(store, capsys) -> None:
    _contextual(store, evidence=True)
    before = _fingerprint(store)
    capsys.readouterr()
    assert _decide("--features", "[1.0, 0.0]") == 2
    err = capsys.readouterr().err
    assert "capture_decision_evidence" in err and "audit_evidence" in err
    assert _fingerprint(store) == before


def test_38_5_features_check_runs_before_the_evidence_refusal(store, capsys) -> None:
    _contextual(store, evidence=True)
    capsys.readouterr()
    assert _decide("--features", "[1.0]") == 2
    err = capsys.readouterr().err
    assert "--features" in err and "unrecognized" not in err
    assert "audit_evidence" not in err


def test_38_5_decision_frame_is_refused_on_a_contextual_snapshot(
    store, capsys, tmp_path: Path
) -> None:
    _contextual(store)
    before = _fingerprint(store)
    frame = tmp_path / "frame.json"
    frame.write_text("{}", encoding="utf-8")
    capsys.readouterr()
    assert _decide("--features", "[1.0, 0.0]", "--decision-frame", str(frame)) == 2
    assert "--decision-frame" in capsys.readouterr().err
    assert _fingerprint(store) == before


def test_38_5_full_authority_contextual_snapshot_is_refused(store, capsys) -> None:
    _contextual(store, authority="full")
    before = _fingerprint(store)
    capsys.readouterr()
    assert _decide("--features", "[1.0, 0.0]") == 2
    err = capsys.readouterr().err
    assert "full" in err and "contextual" in err
    assert _fingerprint(store) == before


def test_38_5_scalar_decide_without_features_still_runs(store, capsys) -> None:
    _scalar(store)
    payload = _decide_ok(capsys, "--greedy")
    assert "autonomy" in payload and "feature_vector" not in payload
