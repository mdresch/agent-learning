"""Contract tests for Story 20.2: The Provenance Record.

Governing specifications:
- User Story: docs/user-stories/epic-20-explicit-policy-prior-warm-starting.md (Story 20.2)
- Architecture: docs/adr/ADR-020-explicit-policy-prior-warm-starting.md (§4.3)
- Business Requirements: docs/project-docs/Business-Requirements/BRD-020-explicit-policy-prior-warm-starting.md (BRU-020-07)
- Functional Design: docs/project-docs/Functional-Design/FDD-020-explicit-policy-prior-warm-starting.md (§1.1, §2.2, §3.2)

Acceptance Criteria:
- AC_0 (Keys): provenance returns warm_start_donor_policy_id, warm_start_donor_task_id,
  warm_start_donor_version, warm_start_damping_factor, warm_started_at, warm_start_action_map,
  warm_start_donor_kind and warm_start_donor_gate_met, with the donor's snapshot id, task id and version.
- AC_1 (Kind): kind defaults to "policy"; "meta_prior" is accepted; any other value raises ValueError;
  gate_met of None is stored as null (None).
- AC_2 (No Clock): the time is the now argument unchanged; the function reads no clock.
- AC_3 (JSON Safe): the result survives json.dumps and json.loads unchanged and the donor snapshot
  is equal to its copy afterwards.
"""

from __future__ import annotations

import ast
import copy
import importlib.util
import inspect
import json
from pathlib import Path
import types
import uuid
import pytest

import agent_learning.warm_start
from agent_learning_ext import VALID_DONOR_KINDS
from agent_learning.types import Action, PolicySnapshot
from agent_learning.warm_start import provenance


@pytest.fixture
def mock_donor_snapshot() -> PolicySnapshot:
    """A realistic low-authority donor policy snapshot."""
    return PolicySnapshot(
        id="9a7d3f12-0000-4000-8000-000000000001",
        agent_id="test-agent",
        task_id="approve-quality-plan",
        version=4,
        logits={"approve_plan": 2.5, "reject_plan": -1.5, "revise_plan": 0.0},
        actions=[Action(id="approve_plan"), Action(id="reject_plan"), Action(id="revise_plan")],
        metadata={"policy_scope": "decision", "decision_authority": "low"},
    )


@pytest.fixture
def sample_action_map() -> dict[str, str]:
    """Sample action mapping for provenance."""
    return {"accept": "approve_plan", "decline": "reject_plan", "ask": "revise_plan"}


def test_ac0_keys(
    mock_donor_snapshot: PolicySnapshot,
    sample_action_map: dict[str, str],
) -> None:
    """AC_0: provenance returns all 8 required keys with exact donor attributes."""
    now_str = "2026-10-29T08:00:00+00:00"
    damping = 0.75
    record = provenance(
        mock_donor_snapshot,
        damping,
        now_str,
        action_map=sample_action_map,
        kind="policy",
        gate_met=True,
    )

    expected_keys = {
        "warm_start_donor_policy_id",
        "warm_start_donor_task_id",
        "warm_start_donor_version",
        "warm_start_damping_factor",
        "warm_started_at",
        "warm_start_action_map",
        "warm_start_donor_kind",
        "warm_start_donor_gate_met",
    }
    assert set(record.keys()) == expected_keys

    assert record["warm_start_donor_policy_id"] == mock_donor_snapshot.id
    assert record["warm_start_donor_task_id"] == mock_donor_snapshot.task_id
    assert record["warm_start_donor_version"] == mock_donor_snapshot.version
    assert record["warm_start_damping_factor"] == 0.75
    assert record["warm_started_at"] == now_str
    assert record["warm_start_action_map"] == sample_action_map
    assert record["warm_start_donor_kind"] == "policy"
    assert record["warm_start_donor_gate_met"] is True


def test_ac1_kind(
    mock_donor_snapshot: PolicySnapshot,
    sample_action_map: dict[str, str],
) -> None:
    """AC_1: kind defaults to 'policy'; 'meta_prior' accepted; invalid kind raises ValueError; gate_met=None is None."""
    now_str = "2026-10-29T08:00:00+00:00"

    # Top-level export check
    assert VALID_DONOR_KINDS == frozenset({"policy", "meta_prior"})

    # Default kind is "policy"
    rec_default = provenance(mock_donor_snapshot, 0.70, now_str, action_map=sample_action_map)
    assert rec_default["warm_start_donor_kind"] == "policy"
    assert rec_default["warm_start_donor_gate_met"] is None

    # kind="meta_prior" is accepted
    rec_meta = provenance(
        mock_donor_snapshot, 1.0, now_str, action_map=sample_action_map, kind="meta_prior"
    )
    assert rec_meta["warm_start_donor_kind"] == "meta_prior"
    assert rec_meta["warm_start_donor_gate_met"] is None

    # gate_met explicitly None, True, False
    rec_none = provenance(
        mock_donor_snapshot, 0.70, now_str, action_map=sample_action_map, gate_met=None
    )
    assert rec_none["warm_start_donor_gate_met"] is None

    rec_false = provenance(
        mock_donor_snapshot, 0.70, now_str, action_map=sample_action_map, gate_met=False
    )
    assert rec_false["warm_start_donor_gate_met"] is False

    rec_true = provenance(
        mock_donor_snapshot, 0.70, now_str, action_map=sample_action_map, gate_met=True
    )
    assert rec_true["warm_start_donor_gate_met"] is True

    # Invalid kind raises ValueError
    for bad_kind in ["random", "model", "other", "", "POLICY"]:
        with pytest.raises(ValueError) as exc_info:
            provenance(mock_donor_snapshot, 0.70, now_str, action_map=sample_action_map, kind=bad_kind)
        assert "kind" in str(exc_info.value).lower()

    # Invalid gate_met type raises (TypeError, ValueError)
    for bad_gate in ["true", 1, 0, []]:
        with pytest.raises((TypeError, ValueError)):
            provenance(mock_donor_snapshot, 0.70, now_str, action_map=sample_action_map, gate_met=bad_gate)

    # Invalid now type raises TypeError; empty/whitespace string raises ValueError
    for bad_now in [123, True, None, object()]:
        with pytest.raises(TypeError):
            provenance(mock_donor_snapshot, 0.70, bad_now, action_map=sample_action_map)

    for empty_now in ["", "   ", " \t "]:
        with pytest.raises(ValueError):
            provenance(mock_donor_snapshot, 0.70, empty_now, action_map=sample_action_map)

    # Invalid donor: missing identity attributes raises ValueError
    class IncompleteDonor:
        pass

    with pytest.raises(ValueError):
        provenance(IncompleteDonor(), 0.70, now_str, action_map=sample_action_map)

    # Invalid donor identity attribute types raise TypeError or ValueError
    donor_bad_id_type = types.SimpleNamespace(id=uuid.uuid4(), task_id="task-1", version=1)
    with pytest.raises(TypeError):
        provenance(donor_bad_id_type, 0.70, now_str, action_map=sample_action_map)

    donor_empty_id = types.SimpleNamespace(id="   ", task_id="task-1", version=1)
    with pytest.raises(ValueError):
        provenance(donor_empty_id, 0.70, now_str, action_map=sample_action_map)

    donor_bad_task_type = types.SimpleNamespace(id="id-1", task_id=123, version=1)
    with pytest.raises(TypeError):
        provenance(donor_bad_task_type, 0.70, now_str, action_map=sample_action_map)

    donor_empty_task = types.SimpleNamespace(id="id-1", task_id="", version=1)
    with pytest.raises(ValueError):
        provenance(donor_empty_task, 0.70, now_str, action_map=sample_action_map)

    for bad_version_type in [True, False, "1", 1.5, object()]:
        donor_bad_ver = types.SimpleNamespace(id="id-1", task_id="task-1", version=bad_version_type)
        with pytest.raises(TypeError):
            provenance(donor_bad_ver, 0.70, now_str, action_map=sample_action_map)

    donor_neg_ver = types.SimpleNamespace(id="id-1", task_id="task-1", version=-1)
    with pytest.raises(ValueError):
        provenance(donor_neg_ver, 0.70, now_str, action_map=sample_action_map)

    # Invalid action_map raises TypeError or ValueError
    for bad_map_type in [123, "not-a-map", ["a", "b"], None]:
        with pytest.raises(TypeError):
            provenance(mock_donor_snapshot, 0.70, now_str, action_map=bad_map_type)

    # Empty action_map raises ValueError
    with pytest.raises(ValueError) as exc_info:
        provenance(mock_donor_snapshot, 0.70, now_str, action_map={})
    assert "action_map" in str(exc_info.value).lower() or "empty" in str(exc_info.value).lower()

    for bad_key_map in [{1: "a"}, {(1, 2): "a"}]:
        with pytest.raises(TypeError):
            provenance(mock_donor_snapshot, 0.70, now_str, action_map=bad_key_map)

    for empty_key_map in [{"": "a"}, {"   ": "a"}]:
        with pytest.raises(ValueError):
            provenance(mock_donor_snapshot, 0.70, now_str, action_map=empty_key_map)

    for bad_val_map in [{"a": 123}, {"a": object()}]:
        with pytest.raises(TypeError):
            provenance(mock_donor_snapshot, 0.70, now_str, action_map=bad_val_map)

    for empty_val_map in [{"a": ""}, {"a": "   "}]:
        with pytest.raises(ValueError):
            provenance(mock_donor_snapshot, 0.70, now_str, action_map=empty_val_map)


def test_ac2_no_clock(
    mock_donor_snapshot: PolicySnapshot,
    sample_action_map: dict[str, str],
) -> None:
    """AC_2: the time is the now argument unchanged; the function reads no clock."""
    frozen_now = "2026-11-01T23:59:59.123456+00:00"
    record = provenance(mock_donor_snapshot, 0.70, frozen_now, action_map=sample_action_map)
    assert record["warm_started_at"] == frozen_now

    # Module source must not import clock utilities (AST-checked)
    source_path = Path(inspect.getfile(agent_learning.warm_start))
    if source_path.suffix == ".pyc":
        source_path = Path(importlib.util.source_from_cache(str(source_path)))
    source_path = source_path.resolve()
    assert source_path.is_file() and source_path.suffix == ".py", f"Source not found: {source_path}"
    source_text = source_path.read_text(encoding="utf-8")

    tree = ast.parse(source_text)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)
                imported_modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_modules.add(node.module)
                imported_modules.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "__import__":
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    imported_modules.add(node.args[0].value)
                    imported_modules.add(node.args[0].value.split(".")[0])

    forbidden_clock = {"datetime", "time"}
    found_clock = imported_modules & forbidden_clock
    assert not found_clock, f"warm_start.py violates clock-isolation invariant: imports {found_clock}"


def test_ac3_json_safe_and_pure(
    mock_donor_snapshot: PolicySnapshot,
    sample_action_map: dict[str, str],
) -> None:
    """AC_3: The result survives json.dumps and json.loads; donor snapshot and map are unmutated."""
    donor_dict_before = mock_donor_snapshot.to_dict()
    map_copy = copy.deepcopy(sample_action_map)
    now_str = "2026-10-29T08:00:00+00:00"

    record = provenance(
        mock_donor_snapshot,
        0.70,
        now_str,
        action_map=sample_action_map,
        kind="policy",
        gate_met=True,
    )

    # JSON roundtrip
    serialized = json.dumps(record)
    deserialized = json.loads(serialized)
    assert deserialized == record

    # Donor snapshot untouched
    assert mock_donor_snapshot.to_dict() == donor_dict_before
    # Action map untouched
    assert sample_action_map == map_copy

    # Purity check on warm_start.py source code using AST
    source_path = Path(inspect.getfile(agent_learning.warm_start))
    if source_path.suffix == ".pyc":
        source_path = Path(importlib.util.source_from_cache(str(source_path)))
    source_path = source_path.resolve()
    assert source_path.is_file() and source_path.suffix == ".py", f"Source not found: {source_path}"
    source_text = source_path.read_text(encoding="utf-8")

    tree = ast.parse(source_text)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)
                imported_modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_modules.add(node.module)
                imported_modules.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "__import__":
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    imported_modules.add(node.args[0].value)
                    imported_modules.add(node.args[0].value.split(".")[0])

    for mod in imported_modules:
        assert mod not in {"random", "numpy"}, f"warm_start.py violates purity: imports {mod}"
        assert not mod.startswith("agent_learning.storage"), f"warm_start.py violates purity: imports {mod}"
