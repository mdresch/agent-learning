"""Contract tests for per-plan route records and the human-decision invariants.

Governed by:
- ADR-011: Project Tailoring and Route Decision
- BRD-011: Project Tailoring and Route Decision
- FDD-011: Project Tailoring and Route Decision
- Epic 11 / Story 11.1: Route Records and the Human-Decision Invariants

Acceptance Criteria:
- AC-0: Route shape: only full_plan, pmp_section or not_applicable are accepted.
- AC-1: No silent omission: a missing, duplicate or unknown plan raises ValueError.
- AC-2: not_applicable needs a reason.
- AC-3: A human decides: a decided route needs a human decider and a deciding role.
- AC-4: Both recorded: a decided route carries recommendation, basis and rationale.
- AC-5: Storage boundary: no storage import and plain-dict episode metadata.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from agent_learning.tailoring import PLAN_IDS, PlanRoute, Route, to_episode_metadata, validate_route_set


def _all_pending(route: Route = Route.PMP_SECTION) -> list[PlanRoute]:
    """A complete, valid route set of pending recommendations."""
    return [PlanRoute(plan_id=pid, route=route) for pid in PLAN_IDS]


def _decided(plan_id: str, route: Route = Route.PMP_SECTION, **overrides) -> PlanRoute:
    base = dict(
        plan_id=plan_id,
        route=route,
        recommended_route=Route.PMP_SECTION,
        recommendation_basis="small project, no budget",
        decided=True,
        decided_by_human=True,
        decided_by_role="Project Manager",
        rationale="A section is enough for this cycle.",
    )
    base.update(overrides)
    return PlanRoute(**base)


def test_ac0_route_shape_accepts_only_the_three_routes() -> None:
    """AC_0: only the three defined routes are accepted."""
    assert {r.value for r in Route} == {"full_plan", "pmp_section", "not_applicable"}
    with pytest.raises(ValueError):
        Route("everything")
    with pytest.raises(ValueError):
        PlanRoute(plan_id=PLAN_IDS[0], route="everything")  # type: ignore[arg-type]


def test_ac1_no_silent_omission_names_missing_plans() -> None:
    """AC_1: a missing plan raises ValueError naming the missing plan ids."""
    routes = _all_pending()
    missing = routes.pop(0).plan_id
    with pytest.raises(ValueError) as exc:
        validate_route_set(routes)
    assert missing in str(exc.value)


def test_ac1_duplicate_and_unknown_plans_raise() -> None:
    """AC_1: a duplicate or unknown plan id raises ValueError."""
    duplicate = _all_pending() + [PlanRoute(plan_id=PLAN_IDS[0], route=Route.FULL_PLAN)]
    with pytest.raises(ValueError):
        validate_route_set(duplicate)
    unknown = _all_pending() + [PlanRoute(plan_id="99.9", route=Route.FULL_PLAN)]
    with pytest.raises(ValueError):
        validate_route_set(unknown)


def test_ac1_a_complete_set_is_returned_unchanged() -> None:
    """AC_1: a complete valid set passes and is returned unchanged."""
    routes = _all_pending()
    assert validate_route_set(routes) == routes


def test_ac2_not_applicable_needs_a_reason() -> None:
    """AC_2: not_applicable with an empty or blank reason raises ValueError."""
    routes = _all_pending()
    routes[3] = PlanRoute(plan_id=routes[3].plan_id, route=Route.NOT_APPLICABLE, reason="  ")
    with pytest.raises(ValueError) as exc:
        validate_route_set(routes)
    assert routes[3].plan_id in str(exc.value)

    routes[3] = PlanRoute(plan_id=routes[3].plan_id, route=Route.NOT_APPLICABLE, reason="No procurement is needed.")
    assert validate_route_set(routes) == routes


def test_ac3_a_decision_needs_a_human_and_a_role() -> None:
    """AC_3: a decided route needs decided_by_human and a non-empty deciding role."""
    routes = _all_pending()
    routes[0] = _decided(routes[0].plan_id, decided_by_human=False)
    with pytest.raises(ValueError):
        validate_route_set(routes)

    routes[0] = _decided(routes[0].plan_id, decided_by_role="")
    with pytest.raises(ValueError):
        validate_route_set(routes)

    routes[0] = _decided(routes[0].plan_id)
    assert validate_route_set(routes) == routes


def test_ac3_a_pending_recommendation_is_valid() -> None:
    """AC_3: an undecided recommendation is valid in a set."""
    assert validate_route_set(_all_pending(Route.FULL_PLAN))


def test_ac4_a_decision_records_both_sides() -> None:
    """AC_4: a decided route raises ValueError unless recommendation, basis and rationale are all set."""
    pid = PLAN_IDS[0]
    for missing in ("recommended_route", "recommendation_basis", "rationale"):
        routes = _all_pending()
        routes[0] = _decided(pid, **{missing: None if missing == "recommended_route" else ""})
        with pytest.raises(ValueError):
            validate_route_set(routes)


def test_ac4_error_names_the_part_that_is_missing() -> None:
    """AC_4 (review finding): a missing recommended route and a blank basis give distinct messages."""
    pid = PLAN_IDS[0]
    routes = _all_pending()
    routes[0] = _decided(pid, recommended_route=None)
    with pytest.raises(ValueError) as no_recommendation:
        validate_route_set(routes)
    assert "recommended route" in str(no_recommendation.value)
    assert "basis" not in str(no_recommendation.value)

    routes[0] = _decided(pid, recommendation_basis="")
    with pytest.raises(ValueError) as no_basis:
        validate_route_set(routes)
    assert "basis" in str(no_basis.value)
    assert "recommended route" not in str(no_basis.value)


def test_ac4_episode_metadata_records_the_pair_and_the_divergence() -> None:
    """AC_4: to_episode_metadata returns both routes, rationale, role and a diverged flag."""
    agreed = to_episode_metadata(_decided(PLAN_IDS[0], route=Route.PMP_SECTION))
    assert agreed["recommended_route"] == "pmp_section"
    assert agreed["decided_route"] == "pmp_section"
    assert agreed["rationale"] == "A section is enough for this cycle."
    assert agreed["decided_by_role"] == "Project Manager"
    assert agreed["diverged"] is False

    diverged = to_episode_metadata(_decided(PLAN_IDS[0], route=Route.FULL_PLAN))
    assert diverged["decided_route"] == "full_plan"
    assert diverged["diverged"] is True


def test_ac5_storage_boundary_no_storage_import_and_plain_metadata() -> None:
    """AC_5: tailoring.py imports nothing from storage and metadata is a plain dict."""
    source = (Path(__file__).resolve().parent.parent / "src" / "agent_learning" / "tailoring.py").read_text(
        encoding="utf-8"
    )
    imported = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
        elif isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
    assert not any("storage" in name for name in imported), imported

    meta = to_episode_metadata(_decided(PLAN_IDS[0]))
    assert type(meta) is dict
    assert all(isinstance(k, str) for k in meta)
