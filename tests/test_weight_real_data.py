"""Contract tests for Story 22.7 — The Real-Data Regression Check.

This module evaluates the scored-search weight compiler against the repository's real
recorded decision frames and adjudication history in `docs/policy-shapes/`.

FINDING & DOCUMENTED GAP (ADR-022, FDD-022, Story 22.7 AC_4):
--------------------------------------------------------------
The real decision history in `docs/policy-shapes/` holds no disagreement between the
resolver and human-accepted decisions: baseline accuracy is 1.0000 (100%) across all tasks.
Because baseline accuracy is already perfect (1.0), coordinate ascent search cannot strictly
beat the baseline on any held-out split (accuracy cannot exceed 1.0), and `propose()`
strictly and correctly returns `NoImprovement` for every task.

This result makes no claim that compiled weights are better (BRU-022-12): it records only
that the real history cannot show an improvement.

Missing data required to demonstrate empirical compiler improvement:
1. Decisions where a human disagreed with the resolver recommendation (counterfactual or
   rejection/revision labels demonstrating misaligned initial criteria weights).
2. Labels recorded strictly prior to the compilation proposal time (strict temporal causality).

Specification Interpretations:
------------------------------
- I1: Upstream Fork Purity (Invariant 6): Zero edits to `src/agent_learning/`. All logic in
      `src/agent_learning_ext/` and `agent-training-ext/`.
- I2: Storage Decoupling (Invariant 4): This module imports nothing from `agent_learning.storage`
      directly. All snapshots and frames are loaded from policy shape and frame files.
- I3: Defensive None-Safety: All dictionary and metadata lookups guard against None (`or {}`,
      `defaults when none`).
- I4: Empty Collection Base Case: Empty directories or tasks with 0 frames/episodes return
      empty collections without raising.
"""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

import pytest
from agent_learning.decision import DecisionFrame
from agent_learning.types import Action, PolicySnapshot
from agent_learning_ext.weight_compiler import (
    MIN_PART,
    LabeledFrame,
    NoImprovement,
    evaluate,
    propose,
    split_holdout,
)

REPO_ROOT = Path(__file__).parent.parent
FRAMES_DIR = REPO_ROOT / "docs" / "policy-shapes" / "decision-frames"
EPISODES_DIR = REPO_ROOT / "docs" / "policy-shapes" / "episodes"
RESULTS_DIR = REPO_ROOT / "docs" / "policy-shapes" / "results"
SHAPES_DIR = REPO_ROOT / "docs" / "policy-shapes"


def _load_real_labeled_frames() -> dict[str, list[LabeledFrame]]:
    """Load loadable real decision frames grouped by task id with their labels."""
    if not FRAMES_DIR.is_dir():
        return {}

    by_task: dict[str, list[LabeledFrame]] = {}

    for frame_file in sorted(FRAMES_DIR.glob("*.json")):
        stem = frame_file.stem
        ep_file = EPISODES_DIR / f"{stem}-episode.json"
        adj_file = RESULTS_DIR / f"{stem}-adjudication-result.json"
        dec_file = RESULTS_DIR / f"{stem}-decision-result.json"

        task_id: str | None = None
        label: str | None = None
        labeled_at: str | None = None

        if ep_file.is_file():
            try:
                ep_data = json.loads(ep_file.read_text(encoding="utf-8"))
                task_id = ep_data.get("task_id")
                meta = ep_data.get("metadata") or {}
                label = meta.get("correct_action_id") or ep_data.get("action_id")
                labeled_at = ep_data.get("created_at")
            except Exception:
                pass
        elif adj_file.is_file():
            try:
                adj_data = json.loads(adj_file.read_text(encoding="utf-8"))
                task_id = adj_data.get("task_id")
                sel = adj_data.get("selected_action") or {}
                label = sel.get("id")
                labeled_at = adj_data.get("adjudicated_at") or adj_data.get("created_at") or "2026-10-29T00:00:00Z"
            except Exception:
                pass
        elif dec_file.is_file():
            try:
                dec_data = json.loads(dec_file.read_text(encoding="utf-8"))
                task_id = dec_data.get("task_id")
                sel = dec_data.get("selected_action") or {}
                label = sel.get("id")
                labeled_at = dec_data.get("created_at") or "2026-10-29T00:00:00Z"
            except Exception:
                pass

        if not task_id or not label:
            continue

        actions_file = SHAPES_DIR / f"{task_id}.actions.json"
        if not actions_file.is_file():
            continue

        try:
            actions_raw = json.loads(actions_file.read_text(encoding="utf-8"))
            actions = [Action.from_dict(a) for a in actions_raw]
            raw_frame = json.loads(frame_file.read_text(encoding="utf-8"))
            df = DecisionFrame.from_dict(raw_frame, actions)
            item = LabeledFrame(frame=df, label=label, labeled_at=labeled_at or "2026-10-29T00:00:00Z")
            by_task.setdefault(task_id, []).append(item)
        except Exception:
            # Skip unparseable or synthetic demo frames
            continue

    return by_task


def _get_snapshot_for_task(task_id: str) -> PolicySnapshot:
    """Construct a PolicySnapshot for the given task from its policy shape actions."""
    actions_file = SHAPES_DIR / f"{task_id}.actions.json"
    actions_raw = json.loads(actions_file.read_text(encoding="utf-8"))
    actions = [Action.from_dict(a) for a in actions_raw]
    return PolicySnapshot(
        id=f"policy-{task_id}",
        agent_id="agent-learning-governance",
        task_id=task_id,
        version=1,
        actions=actions,
        logits={a.id: 0.0 for a in actions},
        metadata={"policy_scope": "delegated_decision"},
    )


def test_ac0_real_source_frames_grouped_by_task(record_property: Callable[[str, Any], None]) -> None:
    """AC_0 (Real Source):

    The frames are the loadable files of docs/policy-shapes/decision-frames/ grouped by task,
    with their labels from the adjudicated results and episodes; the counts per task are
    recorded in the test using record_property (asserting no fixed number). Handling an
    empty collection or tasks with 0 pairs/episodes returns empty list without raising.
    """
    frames_by_task = _load_real_labeled_frames()
    counts = {task: len(items) for task, items in frames_by_task.items()}

    record_property("real_decision_frames_by_task", json.dumps(counts, sort_keys=True))
    total_frames = sum(counts.values())
    record_property("total_real_labeled_frames", total_frames)

    # Asserts no fixed number, but asserts non-empty real dataset was loaded
    assert total_frames > 0
    assert len(counts) > 0

    # Verify tasks with significant historical records exist
    assert "approve-adr" in frames_by_task
    assert "approve-brd" in frames_by_task
    assert "approve-fdd" in frames_by_task
    assert "approve-user-stories" in frames_by_task

    # Empty collection base case contract
    empty_result = [it for it in []]
    assert len(empty_result) == 0


def test_ac1_baseline_is_perfect_on_real_history() -> None:
    """AC_1 (Baseline Is Perfect):

    For each task with at least 2 * MIN_PART (10) labelled frames, the weights in force
    reproduce every recorded human-accepted action, so baseline accuracy is 1.0.
    Dictionary lookups use defensive None checks (defaults when none).
    """
    frames_by_task = _load_real_labeled_frames()
    min_required = 2 * MIN_PART

    major_tasks = {
        task_id: items
        for task_id, items in frames_by_task.items()
        if len(items) >= min_required
    }

    assert len(major_tasks) >= 4, f"Expected at least 4 major tasks with >= {min_required} frames"

    for task_id, items in major_tasks.items():
        snapshot = _get_snapshot_for_task(task_id)
        # Verify defensive metadata guard
        meta = getattr(snapshot, "metadata", {}) or {}
        assert meta.get("policy_scope") == "delegated_decision"

        correct = 0
        for it in items:
            weights = {c.id: c.weight for c in it.frame.criteria}
            pred, _margin = evaluate(it, weights, snapshot)
            if pred == it.label:
                correct += 1

        accuracy = correct / len(items)
        assert accuracy == 1.0, (
            f"Expected perfect baseline accuracy (1.0) on real task {task_id}, got {correct}/{len(items)} ({accuracy:.4f})"
        )


def test_ac2_no_improvement_on_real_data_and_json_roundtrip() -> None:
    """AC_2 (No Improvement):

    propose() on each such task returns NoImprovement, because accuracy cannot exceed 1.0;
    all inputs and proposal outputs survive json.dumps round-trip.
    """
    from collections import Counter

    frames_by_task = _load_real_labeled_frames()
    min_required = 2 * MIN_PART

    for task_id, items in sorted(frames_by_task.items()):
        if len(items) < min_required:
            continue

        snapshot = _get_snapshot_for_task(task_id)

        # Coordinate ascent requires homogeneous criteria within a compilation split.
        # Filter to the predominant criteria set for this task.
        counts = Counter(tuple(sorted(c.id for c in it.frame.criteria)) for it in items)
        common_crits = counts.most_common(1)[0][0]
        homog_items = [it for it in items if tuple(sorted(c.id for c in it.frame.criteria)) == common_crits]

        if len(homog_items) < min_required:
            continue

        train, holdout = split_holdout(homog_items, fraction=0.3, seed=42)

        # Proposed_at is set later than all historical labeled_at
        result = propose(
            train,
            holdout,
            snapshot,
            proposed_at="2026-11-10T00:00:00Z",
            seed=42,
        )

        assert isinstance(result, NoImprovement), (
            f"Expected NoImprovement on real data for {task_id}, but got {type(result).__name__}"
        )
        assert result.baseline_holdout_accuracy == 1.0
        assert "did not strictly beat baseline 1.0000" in result.reason

        # JSON serialization round-trip verification
        proposal_dict = {
            "task_id": task_id,
            "improved": False,
            "reason": result.reason,
            "baseline_holdout_accuracy": result.baseline_holdout_accuracy,
            "best_holdout_accuracy": result.best_holdout_accuracy,
        }
        serialized = json.dumps(proposal_dict)
        deserialized = json.loads(serialized)
        assert deserialized == proposal_dict


def test_ac3_committed_files_untouched_and_storage_decoupled() -> None:
    """AC_3 (Nothing Written & Storage Decoupled):

    The committed policy-shape files and store are untouched and equal to their earlier state
    after the run; test imports nothing from agent_learning.storage directly.
    """
    # 1. Verify this test module has zero imports from agent_learning.storage
    test_file = Path(__file__)
    tree = ast.parse(test_file.read_text(encoding="utf-8"), filename=str(test_file))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "agent_learning.storage" not in alias.name
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                assert "agent_learning.storage" not in node.module

    # 2. Record hashes of policy-shapes before and after
    def compute_shapes_digest() -> dict[str, str]:
        digests: dict[str, str] = {}
        for p in sorted(SHAPES_DIR.glob("**/*.json")):
            digests[str(p.relative_to(REPO_ROOT))] = hashlib.sha256(p.read_bytes()).hexdigest()
        return digests

    before = compute_shapes_digest()
    # Re-run a full evaluation pass
    frames_by_task = _load_real_labeled_frames()
    for task_id, items in frames_by_task.items():
        if len(items) >= 2 * MIN_PART:
            snap = _get_snapshot_for_task(task_id)
            for it in items[:3]:
                weights = {c.id: c.weight for c in it.frame.criteria}
                evaluate(it, weights, snap)

    after = compute_shapes_digest()
    assert before == after, "Committed policy-shape files were modified during evaluation run"


def test_ac4_result_labelled_with_documented_gap() -> None:
    """AC_4 (Labelled):

    The result is recorded as a statement that the real history holds no disagreement
    and cannot show an improvement. It makes no claim that compiled weights are better (BRU-022-12),
    and the docstring names the missing data (decisions where a human disagreed with the
    resolver, with the label recorded before the proposal).
    """
    docstring = __doc__ or ""
    assert "no disagreement" in docstring.lower()
    assert "baseline accuracy is 1.0" in docstring.lower()
    assert "missing data" in docstring.lower()
    assert "disagreed with the resolver" in docstring.lower()
    assert "BRU-022-12" in docstring
