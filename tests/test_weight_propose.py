"""Contract tests for Story 22.4 — Proposing Only a Real Improvement (ADR-022, Epic 22).

Source ADR: ADR-022 (Scored-Search Decision Configuration Compilation)
Source BRD: BRD-022 (BRU-022-07, BRU-022-08, BRU-022-09, BRU-022-10)
Source FDD: FDD-022 (§1 item 1, §1 item 2, §2.2, §2.3, §2.4, §3.6, §3.8, §4 L4, L6, L7, L8)

Contract Interpretations:
- [I1] Upstream Fork Purity (Invariant 6):
  Implemented strictly in src/agent_learning_ext/weight_compiler.py and cli.py.
  Upstream src/agent_learning/ remains 100% untouched.
- [I2] Storage Decoupling & Pure Functionality:
  weight_compiler.py imports nothing from agent_learning.storage or agent_learning_ext.storage,
  does not open dataset files, and does no file I/O operations.
- [I3] Defensive None-Safety:
  Defensively guards dictionary access and attributes against None values.
- [I4] Empty Collection Base Case:
  Passing an empty sequence of items raises ValueError cleanly with a descriptive message.
- [I5] Specific Exception Class Requirements:
  All negative test assertions specify exact exception classes (TypeError, ValueError).
"""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path
from types import MappingProxyType
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
    CompiledWeights,
    LabeledFrame,
    NoImprovement,
    propose,
    split_holdout,
)
from tests.test_weight_split import build_synthetic_suite


def build_misaligned_synthetic_suite() -> list[LabeledFrame]:
    """Synthetic suite where frames are authored with weights far from hidden weights (0.6, 0.3, 0.1).

    Authored weights: (0.1, 0.1, 0.8), leading to low baseline accuracy.
    """
    suite = build_synthetic_suite()
    misaligned: list[LabeledFrame] = []
    for it in suite:
        bad_criteria = [
            DecisionCriterion(id="c1", weight=0.1),
            DecisionCriterion(id="c2", weight=0.1),
            DecisionCriterion(id="c3", weight=0.8),
        ]
        bad_frame = DecisionFrame(
            task=it.frame.task,
            criteria=bad_criteria,
            options=it.frame.options,
            minimum_margin=it.frame.minimum_margin,
            uncertainty_penalty=it.frame.uncertainty_penalty,
        )
        misaligned.append(LabeledFrame(frame=bad_frame, label=it.label, labeled_at=it.labeled_at))
    return misaligned


@pytest.fixture
def snapshot() -> PolicySnapshot:
    actions = [Action(id="A"), Action(id="B")]
    return PolicySnapshot(
        id="policy-synth",
        agent_id="agent-synth",
        task_id="task-synth",
        version=1,
        actions=actions,
        logits={"A": 0.0, "B": 0.0},
    )


def test_ac0_propose_returns_compiled_weights_on_improvement(snapshot: PolicySnapshot) -> None:
    """AC_0 (Improvement):

    On a suite whose frames were authored with weights far from the hidden ones,
    propose returns CompiledWeights with holdout_accuracy strictly above baseline_holdout_accuracy,
    and the report holds the seed, split sizes, evaluations, sweeps and restarts.
    """
    suite = build_misaligned_synthetic_suite()
    train, holdout = split_holdout(suite, seed=7)
    proposed_at = "2026-10-27T00:00:00Z"

    result = propose(train, holdout, snapshot, proposed_at=proposed_at, seed=7)

    assert isinstance(result, CompiledWeights)
    assert result.holdout_accuracy > result.baseline_holdout_accuracy
    assert result.baseline_holdout_accuracy < 0.7  # Misaligned baseline is poor
    assert result.holdout_accuracy >= 0.8         # Compiled weights achieve high accuracy
    assert result.seed == 7
    assert result.evaluations > 0
    assert result.sweeps > 0
    assert result.restarts > 0
    assert result.proposed_at == proposed_at


def test_ac1_strictly_greater_rule_returns_no_improvement_on_tie(snapshot: PolicySnapshot) -> None:
    """AC_1 (Strictly Greater):

    When the compiled weights equal the baseline on the held-out part,
    propose returns NoImprovement with both accuracies, and the result has no weights.
    """
    suite = build_synthetic_suite()  # Authored with exact hidden weights, baseline is 1.0
    train, holdout = split_holdout(suite, seed=7)
    proposed_at = "2026-10-27T00:00:00Z"

    result = propose(train, holdout, snapshot, proposed_at=proposed_at, seed=7)

    assert isinstance(result, NoImprovement)
    assert result.best_holdout_accuracy == result.baseline_holdout_accuracy
    assert result.baseline_holdout_accuracy == 1.0
    assert not hasattr(result, "weights") or getattr(result, "weights", None) is None


def test_ac2_worse_accuracy_returns_no_improvement(snapshot: PolicySnapshot) -> None:
    """AC_2 (Worse):

    When compiled weights score lower on the held-out part than baseline,
    the result is NoImprovement.
    """
    suite = build_misaligned_synthetic_suite()
    train, holdout = split_holdout(suite, seed=7)
    proposed_at = "2026-10-27T00:00:00Z"

    # Mock coordinate_ascent returning an intentionally degraded weight vector
    from agent_learning_ext.weight_compiler import CoordinateAscentResult
    bad_ascent = CoordinateAscentResult(
        weights={"c1": 0.05, "c2": 0.05, "c3": 0.90},
        train_accuracy=0.2,
        train_objective=5.0,
        evaluations=10,
        sweeps=1,
        restarts=1,
    )

    with patch("agent_learning_ext.weight_compiler.coordinate_ascent", return_value=bad_ascent):
        result = propose(train, holdout, snapshot, proposed_at=proposed_at, seed=7)

    assert isinstance(result, NoImprovement)
    assert result.best_holdout_accuracy <= result.baseline_holdout_accuracy


def test_ac3_baseline_uses_stored_weights(snapshot: PolicySnapshot) -> None:
    """AC_3 (Baseline Is As Stored):

    The baseline uses each frame's own authored weights, unchanged, on the same held-out items.
    """
    suite = build_misaligned_synthetic_suite()
    train, holdout = split_holdout(suite, seed=7)
    proposed_at = "2026-10-27T00:00:00Z"

    # Manually compute baseline using frame's own criteria
    resolver = DecisionResolver()
    manual_baseline_hits = 0
    for item in holdout:
        res = resolver.resolve(snapshot, item.frame)
        predicted = res.selected_action.id if res.selected_action else None
        if predicted == item.label:
            manual_baseline_hits += 1
    expected_baseline_acc = manual_baseline_hits / len(holdout)

    result = propose(train, holdout, snapshot, proposed_at=proposed_at, seed=7)
    assert result.baseline_holdout_accuracy == expected_baseline_acc


def test_ac4_policy_compile_weights_cli(tmp_path: Path, snapshot: PolicySnapshot) -> None:
    """AC_4 (Proposal File):

    policy-compile-weights writes the proposal object of FDD-022 §2.3 for both outcomes,
    holds the policy id and version it compiled against, and writes nothing to the store.
    """
    suite = build_misaligned_synthetic_suite()
    dataset_file = tmp_path / "dataset.json"
    dataset_payload = [
        {"frame": it.frame.to_dict(), "label": it.label, "labeled_at": it.labeled_at}
        for it in suite
    ]
    dataset_file.write_text(json.dumps(dataset_payload), encoding="utf-8")

    proposal_improved_file = tmp_path / "proposal_improved.json"

    # Mock store to return our snapshot and ensure no write methods are called
    from agent_learning_ext.storage.cosmos import CosmosStore
    with patch("agent_learning_ext.cli.get_default_store") as mock_get_store:
        mock_store = mock_get_store.return_value
        mock_store.get_active_policy.return_value = snapshot

        # Run CLI policy-compile-weights
        from agent_learning_ext.cli import main
        ret = main([
            "policy-compile-weights",
            "--agent-id", snapshot.agent_id,
            "--task-id", snapshot.task_id,
            "--validation-dataset", str(dataset_file),
            "--seed", "7",
            "--proposed-at", "2026-10-27T00:00:00Z",
            "--output-proposal", str(proposal_improved_file),
        ])
        assert ret == 0

        # Verify nothing written to store
        mock_store.save_policy.assert_not_called()
        mock_store.register_episode.assert_not_called()

    # Read and inspect proposal file
    prop_data = json.loads(proposal_improved_file.read_text(encoding="utf-8"))
    assert prop_data["improved"] is True
    assert prop_data["task_id"] == snapshot.task_id
    assert prop_data["agent_id"] == snapshot.agent_id
    assert prop_data["policy_id"] == snapshot.id
    assert prop_data["policy_version"] == snapshot.version
    assert "weights" in prop_data
    assert prop_data["holdout_accuracy"] > prop_data["baseline_holdout_accuracy"]
    assert prop_data["dataset_size"] == len(suite)
    assert prop_data["train_size"] + prop_data["holdout_size"] == len(suite)
    assert "compile_duration_seconds" in prop_data


def test_ac5_dataset_checks_cli(tmp_path: Path, snapshot: PolicySnapshot) -> None:
    """AC_5 (Dataset Checks):

    A dataset item whose label is not an action id of the active policy,
    or that lacks frame, label or labeled_at, makes policy-compile-weights exit non-zero
    and name the item. weight_compiler.py does not open the dataset file.
    """
    # 1. Missing 'label'
    bad_ds1 = tmp_path / "bad1.json"
    bad_ds1.write_text(json.dumps([{"frame": {}, "labeled_at": "2026-10-26T10:00:00Z"}]), encoding="utf-8")

    # 2. Unknown action label
    bad_ds2 = tmp_path / "bad2.json"
    bad_ds2.write_text(json.dumps([{
        "frame": {"task": "bad-task", "criteria": [{"id": "c1", "weight": 1.0}], "options": []},
        "label": "UNKNOWN_ACTION",
        "labeled_at": "2026-10-26T10:00:00Z",
    }]), encoding="utf-8")

    from agent_learning_ext.cli import main
    with patch("agent_learning_ext.cli.get_default_store") as mock_get_store:
        mock_store = mock_get_store.return_value
        mock_store.get_active_policy.return_value = snapshot

        out_prop = tmp_path / "out.json"

        # Missing field
        ret1 = main([
            "policy-compile-weights",
            "--agent-id", snapshot.agent_id,
            "--task-id", snapshot.task_id,
            "--validation-dataset", str(bad_ds1),
            "--seed", "7",
            "--output-proposal", str(out_prop),
        ])
        assert ret1 != 0

        # Unknown action
        ret2 = main([
            "policy-compile-weights",
            "--agent-id", snapshot.agent_id,
            "--task-id", snapshot.task_id,
            "--validation-dataset", str(bad_ds2),
            "--seed", "7",
            "--output-proposal", str(out_prop),
        ])
        assert ret2 != 0

    # AST check: weight_compiler.py does not open files [I2]
    compiler_path = Path(__file__).resolve().parent.parent / "src" / "agent_learning_ext" / "weight_compiler.py"
    tree = ast.parse(compiler_path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "open":
                pytest.fail("weight_compiler.py must not call open()")


def test_ac6_frozen_weights_immutability() -> None:
    """AC_6 (Frozen Weights):

    CompiledWeights.weights is a MappingProxyType.
    Writing into it raises TypeError, and mutating the dict passed to the constructor
    leaves the stored weights unchanged.
    """
    raw_dict = {"c1": 0.6, "c2": 0.3, "c3": 0.1}
    cw = CompiledWeights(
        weights=raw_dict,
        train_accuracy=1.0,
        holdout_accuracy=1.0,
        baseline_holdout_accuracy=0.5,
        holdout_margin=0.2,
        seed=7,
        evaluations=100,
        sweeps=5,
        restarts=5,
        proposed_at="2026-10-27T00:00:00Z",
    )

    assert isinstance(cw.weights, MappingProxyType)

    # Writing into cw.weights raises TypeError
    with pytest.raises(TypeError):
        cw.weights["c1"] = 0.9  # type: ignore[index]

    # Mutating raw_dict leaves cw.weights unchanged
    raw_dict["c1"] = 0.999
    assert cw.weights["c1"] == 0.6
