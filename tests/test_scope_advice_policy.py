"""Contract tests for Story 25.3: idle Scope advisory policy.

Story: docs/user-stories/epic-25-scope-management-plan-standard-and-baseline-contract.md (Story 25.3)
ADR:   ADR-025
BRD:   BRD-025 (BRU-025-05)
FDD:   FDD-025 sections 3.5; §5 item 1 confirmed 2026-10-30
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from agent_learning.policy.scope_advice import (
    ADVICE_TASK_ID,
    DECISION_KINDS,
    GATE_TASK_ID,
    baseline_snapshot,
    reset_recommendation_cache,
)
from agent_learning.types import Episode

POLICY_SHAPES = Path(__file__).resolve().parents[1] / "docs" / "policy-shapes"
ACTIONS_FILE = POLICY_SHAPES / "advise-scope-plan-decision.actions.json"


@pytest.fixture(autouse=True)
def _clear_advice_cache():
    reset_recommendation_cache()
    yield
    reset_recommendation_cache()


def _expected_action_ids() -> set[str]:
    assert ACTIONS_FILE.is_file(), f"missing policy shape: {ACTIONS_FILE}"
    rows = json.loads(ACTIONS_FILE.read_text(encoding="utf-8"))
    return {row["id"] for row in rows}


class TestBaselineIdentity:
    """AC_0"""

    def test_task_metadata_and_logits(self):
        snap = baseline_snapshot()
        assert snap.task_id == ADVICE_TASK_ID
        assert snap.metadata.get("decision_authority") == "low"
        assert snap.metadata.get("requires_human_approval") is False
        assert {a.id for a in snap.actions} == _expected_action_ids()
        assert set(snap.logits) == _expected_action_ids()
        assert all(snap.logits[a] == 0.0 for a in snap.logits)


class TestIdleSnapshot:
    """AC_1"""

    def test_baseline_snapshot_does_not_touch_store(self):
        store = MagicMock()
        baseline_snapshot()
        store.store_episode.assert_not_called()
        store.store_policy.assert_not_called()


class TestSeparateTask:
    """AC_2"""

    def test_task_id_differs_from_gate(self):
        assert baseline_snapshot().task_id != GATE_TASK_ID

    def test_gate_episode_task_id_is_not_advice_task(self):
        gate = Episode(
            id="ep_gate",
            agent_id="test",
            task_id=GATE_TASK_ID,
            action_type="decision",
            action_name="approve_plan",
        )
        assert gate.task_id != ADVICE_TASK_ID


class TestNoPrior:
    """AC_3"""

    def test_all_logits_zero(self):
        snap = baseline_snapshot()
        assert all(v == 0.0 for v in snap.logits.values())


class TestNoSelectionEpisode:
    """AC_4"""

    def test_module_does_not_reference_episode_construction(self):
        path = Path(__file__).resolve().parents[1] / "src" / "agent_learning" / "policy" / "scope_advice.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id == "Episode":
                    pytest.fail("scope_advice must not construct Episode (ADR-024 selection is human-only)")


class TestDecisionKindTable:
    """FDD-025 §2 DECISION_KINDS matches the declared policy shape."""

    def test_kinds_cover_every_action_once(self):
        from_shape = _expected_action_ids()
        from_table = {aid for ids in DECISION_KINDS.values() for aid in ids}
        assert from_table == from_shape


class TestScopeAdvicePurity:
    """BRU-025-08 / Story 25.4 AC_4 storage boundary for the policy module."""

    def test_no_storage_imports(self):
        path = Path(__file__).resolve().parents[1] / "src" / "agent_learning" / "policy" / "scope_advice.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "storage" not in alias.name
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                assert "storage" not in mod
