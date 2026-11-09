"""Contract tests for the contextual-policy CLI changes in `agent_learning_ext.cli`.

Story 38.4 (docs/user-stories/epic-38-packaged-contextual-learning.md)
ADR-038 sections 4.3 and 7 (docs/adr/ADR-038-packaged-contextual-learning.md)
BRD-038 BRU-038-07, FDD-038 sections 2.2 and 3.1 (docs/project-docs/...)

Interpretations (LL-011; I1 to I4 come from `scripts/spec_gate.py 38.4 --no-persist`, verdict
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
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_learning.storage import InMemoryStore
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
