"""Contract tests for Story 25.4: record recommendation, then show it.

Story: docs/user-stories/epic-25-scope-management-plan-standard-and-baseline-contract.md (Story 25.4)
ADR:   ADR-025
BRD:   BRD-025 (BRU-025-06)
FDD:   FDD-025 sections 3.6–3.7; §5 item 1 confirmed 2026-10-30
"""

from __future__ import annotations

import ast
import inspect
from dataclasses import is_dataclass
from pathlib import Path

import pytest

from agent_learning.policy.scope_advice import (
    ADVICE_TASK_ID,
    DECISION_KINDS,
    ScopeRecommendation,
    advice_reward,
    baseline_snapshot,
    recommend,
    reset_recommendation_cache,
)

ISO = "2026-10-30T12:00:00+00:00"


@pytest.fixture(autouse=True)
def _clear_advice_cache():
    reset_recommendation_cache()
    yield
    reset_recommendation_cache()


class TestKindBoundsDraw:
    """AC_0"""

    @pytest.mark.parametrize("kind", list(DECISION_KINDS.keys()))
    def test_action_in_kind(self, kind: str):
        snap = baseline_snapshot()
        rec = recommend(
            snap,
            kind,
            recommendation_id=f"rec-{kind}",
            recommended_at=ISO,
            recorded_decisions=0,
            min_shown_decisions=None,
        )
        assert rec.action_id in DECISION_KINDS[kind]
        assert rec.task_id == ADVICE_TASK_ID
        assert rec.decision_kind == kind

    def test_unknown_kind_raises(self):
        with pytest.raises(ValueError, match="unknown decision_kind"):
            recommend(
                baseline_snapshot(),
                "not_a_kind",
                recommendation_id="rec-bad",
                recommended_at=ISO,
                recorded_decisions=0,
                min_shown_decisions=None,
            )


class TestImmutableRecommendation:
    """AC_1"""

    def test_same_id_returns_same_action_and_timestamp(self):
        snap = baseline_snapshot()
        first = recommend(
            snap,
            "route",
            recommendation_id="rec-stable",
            recommended_at=ISO,
            recorded_decisions=0,
            min_shown_decisions=None,
        )
        snap.logits["recommend_full_plan"] = 5.0
        snap.logits["recommend_pmp_section"] = -5.0
        second = recommend(
            snap,
            "route",
            recommendation_id="rec-stable",
            recommended_at="2026-10-30T99:99:99+00:00",
            recorded_decisions=99,
            min_shown_decisions=1,
        )
        assert second.action_id == first.action_id
        assert second.recommended_at == first.recommended_at
        assert second.visible == first.visible


    def test_invalid_minimum_raises_even_when_cached(self):
        snap = baseline_snapshot()
        recommend(
            snap,
            "route",
            recommendation_id="rec-cached-invalid",
            recommended_at=ISO,
            recorded_decisions=0,
            min_shown_decisions=None,
        )
        with pytest.raises(ValueError, match="min_shown_decisions"):
            recommend(
                snap,
                "route",
                recommendation_id="rec-cached-invalid",
                recommended_at=ISO,
                recorded_decisions=0,
                min_shown_decisions=0,
            )


class TestWithholdVisibility:
    """AC_2"""

    def test_none_minimum_withholds(self):
        rec = recommend(
            baseline_snapshot(),
            "graduation",
            recommendation_id="rec-hide",
            recommended_at=ISO,
            recorded_decisions=100,
            min_shown_decisions=None,
        )
        assert rec.visible is False

    def test_below_minimum_withholds(self):
        rec = recommend(
            baseline_snapshot(),
            "graduation",
            recommendation_id="rec-below",
            recommended_at=ISO,
            recorded_decisions=2,
            min_shown_decisions=5,
        )
        assert rec.visible is False

    def test_at_minimum_shows(self):
        rec = recommend(
            baseline_snapshot(),
            "graduation",
            recommendation_id="rec-show",
            recommended_at=ISO,
            recorded_decisions=5,
            min_shown_decisions=5,
        )
        assert rec.visible is True

    def test_non_positive_minimum_raises(self):
        with pytest.raises(ValueError, match="min_shown_decisions"):
            recommend(
                baseline_snapshot(),
                "route",
                recommendation_id="rec-min",
                recommended_at=ISO,
                recorded_decisions=0,
                min_shown_decisions=0,
            )


class TestAdviceReward:
    """AC_3"""

    def test_follow_and_override_values(self):
        assert advice_reward(True) == 1.0
        assert advice_reward(False) == -1.0

    def test_no_gate_action_parameters(self):
        sig = inspect.signature(advice_reward)
        assert list(sig.parameters) == ["followed"]


class TestNoStorageRecordType:
    """AC_4"""

    def test_scope_recommendation_is_frozen_dataclass_not_store_type(self):
        assert is_dataclass(ScopeRecommendation)
        rec = recommend(
            baseline_snapshot(),
            "flagged_deviation",
            recommendation_id="rec-type",
            recommended_at=ISO,
            recorded_decisions=0,
            min_shown_decisions=None,
        )
        assert type(rec).__name__ == "ScopeRecommendation"
        from agent_learning import types as al_types

        assert "ScopeRecommendation" not in al_types.__all__

    def test_module_has_no_storage_imports(self):
        path = Path(__file__).resolve().parents[1] / "src" / "agent_learning" / "policy" / "scope_advice.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                assert "storage" not in mod
