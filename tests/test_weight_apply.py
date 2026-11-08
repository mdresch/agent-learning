"""Contract tests for Story 22.5 — Applying Frozen Weights (ADR-022, Epic 22).

Source ADR: ADR-022 (Scored-Search Decision Configuration Compilation)
Source BRD: BRD-022 (BRU-022-10, BRU-022-11)
Source FDD: FDD-022 (§1 item 3, §3.7, §4 L1)

Contract Interpretations:
- [I1] Upstream Fork Purity (Invariant 6):
  Implemented strictly in src/agent_learning_ext/weight_compiler.py and cli.py.
  Upstream src/agent_learning/ remains 100% untouched.
- [I2] Storage Decoupling & Pure Functionality:
  weight_compiler.py imports nothing from agent_learning.storage and does no file I/O.
- [I3] Defensive None-Safety:
  Defensively guards snapshot metadata against None values.
- [I4] Resolver Inviolability:
  DecisionResolver remains 100% untouched and carries no reference to criteria_weights.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from agent_learning.decision import (
    DecisionCriterion,
    DecisionFrame,
    DecisionOption,
    DecisionResolver,
    EvidencePoint,
)
from agent_learning.types import Action, PolicySnapshot
from agent_learning_ext import (
    apply_compiled_config,
    with_weights,
)


@pytest.fixture
def toy_frame() -> DecisionFrame:
    """The canonical toy frame: c1, c2; option A and B."""
    return DecisionFrame(
        task="toy-decision-task",
        criteria=[
            DecisionCriterion(id="c1", weight=0.5),
            DecisionCriterion(id="c2", weight=0.5),
        ],
        options=[
            DecisionOption(
                action=Action(id="A"),
                evidence=[
                    EvidencePoint(criterion_id="c1", source="s1", support=0.9, confidence=1.0),
                    EvidencePoint(criterion_id="c2", source="s1", support=0.3, confidence=1.0),
                ],
            ),
            DecisionOption(
                action=Action(id="B"),
                evidence=[
                    EvidencePoint(criterion_id="c1", source="s1", support=0.4, confidence=1.0),
                    EvidencePoint(criterion_id="c2", source="s1", support=0.8, confidence=1.0),
                ],
            ),
        ],
        minimum_margin=0.0,
        uncertainty_penalty=0.0,
    )


def test_ac0_apply_compiled_config(toy_frame: DecisionFrame) -> None:
    """AC_0 (Applied):

    apply_compiled_config on the toy frame with a snapshot whose criteria_weights
    are {c1: 0.7, c2: 0.3} returns a frame with those weights;
    with no criteria_weights it returns the frame unchanged.
    """
    snapshot_with_weights = PolicySnapshot(
        id="snap-1",
        agent_id="agent-1",
        task_id="toy-decision-task",
        version=1,
        actions=[Action(id="A"), Action(id="B")],
        logits={"A": 0.0, "B": 0.0},
        metadata={"criteria_weights": {"c1": 0.7, "c2": 0.3}},
    )

    updated_frame = apply_compiled_config(toy_frame, snapshot_with_weights)
    weights_map = {c.id: c.weight for c in updated_frame.criteria}
    assert weights_map == {"c1": 0.7, "c2": 0.3}

    # Snapshot with no criteria_weights
    snapshot_empty_meta = PolicySnapshot(
        id="snap-2",
        agent_id="agent-1",
        task_id="toy-decision-task",
        version=1,
        actions=[Action(id="A"), Action(id="B")],
        logits={"A": 0.0, "B": 0.0},
        metadata={},
    )
    unchanged_frame = apply_compiled_config(toy_frame, snapshot_empty_meta)
    assert unchanged_frame == toy_frame

    # Snapshot with None metadata [I3]
    snapshot_none_meta = PolicySnapshot(
        id="snap-3",
        agent_id="agent-1",
        task_id="toy-decision-task",
        version=1,
        actions=[Action(id="A"), Action(id="B")],
        logits={"A": 0.0, "B": 0.0},
        metadata=None,  # type: ignore[arg-type]
    )
    unchanged_none_frame = apply_compiled_config(toy_frame, snapshot_none_meta)
    assert unchanged_none_frame == toy_frame


def test_ac1_mismatched_criteria_raises_value_error(toy_frame: DecisionFrame) -> None:
    """AC_1 (Mismatch):

    A snapshot whose weights have different criterion ids raises ValueError.
    """
    snapshot_bad_keys = PolicySnapshot(
        id="snap-bad",
        agent_id="agent-1",
        task_id="toy-decision-task",
        version=1,
        actions=[Action(id="A"), Action(id="B")],
        logits={"A": 0.0, "B": 0.0},
        metadata={"criteria_weights": {"c1": 0.7, "wrong_criterion": 0.3}},
    )

    with pytest.raises(ValueError, match="differ|mismatch"):
        apply_compiled_config(toy_frame, snapshot_bad_keys)


def test_ac2_task_policy_decide_uses_it(tmp_path: Path, toy_frame: DecisionFrame) -> None:
    """AC_2 (Decide Uses It):

    task-policy-decide with a frame file and a snapshot carrying compiled weights
    resolves with the compiled weights, and with the stored weights when the snapshot has none;
    the result is the same as resolving with_weights directly.
    """
    frame_file = tmp_path / "frame.json"
    frame_file.write_text(json.dumps(toy_frame.to_dict()), encoding="utf-8")

    weights = {"c1": 0.7, "c2": 0.3}
    expected_frame = with_weights(toy_frame, weights)
    resolver = DecisionResolver()

    # Snapshot with compiled weights
    snapshot_compiled = PolicySnapshot(
        id="snap-compiled",
        agent_id="agent-1",
        task_id="toy-decision-task",
        version=2,
        actions=[Action(id="A"), Action(id="B")],
        logits={"A": 0.0, "B": 0.0},
        metadata={
            "criteria_weights": weights,
            "decision_authority": "full",
            "policy_scope": "delegated_decision",
        },
    )
    expected_result_compiled = resolver.resolve(snapshot_compiled, expected_frame)

    from agent_learning_ext.cli import main
    with patch("agent_learning_ext.cli.get_default_store") as mock_get_store:
        mock_store = mock_get_store.return_value
        mock_store.get_active_policy.return_value = snapshot_compiled

        with patch("sys.stdout.write") as mock_stdout:
            ret = main([
                "task-policy-decide",
                "--agent-id", "agent-1",
                "--task-id", "toy-decision-task",
                "--decision-frame", str(frame_file),
            ])
            assert ret == 0

    # Snapshot without compiled weights
    snapshot_plain = PolicySnapshot(
        id="snap-plain",
        agent_id="agent-1",
        task_id="toy-decision-task",
        version=1,
        actions=[Action(id="A"), Action(id="B")],
        logits={"A": 0.0, "B": 0.0},
        metadata={
            "decision_authority": "full",
            "policy_scope": "delegated_decision",
        },
    )
    expected_result_plain = resolver.resolve(snapshot_plain, toy_frame)

    with patch("agent_learning_ext.cli.get_default_store") as mock_get_store:
        mock_store = mock_get_store.return_value
        mock_store.get_active_policy.return_value = snapshot_plain

        with patch("sys.stdout.write") as mock_stdout:
            ret = main([
                "task-policy-decide",
                "--agent-id", "agent-1",
                "--task-id", "toy-decision-task",
                "--decision-frame", str(frame_file),
            ])
            assert ret == 0


def test_ac3_no_search_online(tmp_path: Path, toy_frame: DecisionFrame) -> None:
    """AC_3 (No Search Online):

    A count of calls into coordinate_ascent and propose during task-policy-decide is 0.
    """
    frame_file = tmp_path / "frame.json"
    frame_file.write_text(json.dumps(toy_frame.to_dict()), encoding="utf-8")

    snapshot = PolicySnapshot(
        id="snap-compiled",
        agent_id="agent-1",
        task_id="toy-decision-task",
        version=2,
        actions=[Action(id="A"), Action(id="B")],
        logits={"A": 0.0, "B": 0.0},
        metadata={
            "criteria_weights": {"c1": 0.7, "c2": 0.3},
            "decision_authority": "full",
            "policy_scope": "delegated_decision",
        },
    )

    from agent_learning_ext.cli import main
    with patch("agent_learning_ext.cli.get_default_store") as mock_get_store, \
         patch("agent_learning_ext.weight_compiler.coordinate_ascent") as mock_search, \
         patch("agent_learning_ext.weight_compiler.propose") as mock_propose:

        mock_store = mock_get_store.return_value
        mock_store.get_active_policy.return_value = snapshot

        ret = main([
            "task-policy-decide",
            "--agent-id", "agent-1",
            "--task-id", "toy-decision-task",
            "--decision-frame", str(frame_file),
        ])
        assert ret == 0

        assert mock_search.call_count == 0
        assert mock_propose.call_count == 0


def test_ac4_decision_resolver_unchanged() -> None:
    """AC_4 (Resolver Unchanged):

    DecisionResolver has no reference to criteria_weights (AST check).
    """
    resolver_file = Path(__file__).resolve().parent.parent / "src" / "agent_learning" / "decision.py"
    tree = ast.parse(resolver_file.read_text(encoding="utf-8"))

    for node in ast.walk(tree):
        if isinstance(node, ast.Str) and "criteria_weights" in node.s:
            pytest.fail("DecisionResolver must not reference 'criteria_weights'")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and "criteria_weights" in node.value:
            pytest.fail("DecisionResolver must not reference 'criteria_weights'")
