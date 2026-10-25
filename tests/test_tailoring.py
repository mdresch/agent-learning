"""Contract tests for per-plan route records and the human-decision invariants.

Governed by:
- ADR-011: Project Tailoring and Route Decision
- BRD-011: Project Tailoring and Route Decision
- FDD-011: Project Tailoring and Route Decision
- Epic 11 / Story 11.1: Route Records and the Human-Decision Invariants
- Epic 11 / Story 11.2: Flags That Never Block, and Integration-Section Home

Acceptance Criteria:
- AC-0: Route shape: only full_plan, pmp_section or not_applicable are accepted.
- AC-1: No silent omission: a missing, duplicate or unknown plan raises ValueError.
- AC-2: not_applicable needs a reason.
- AC-3: A human decides: a decided route needs a human decider and a deciding role.
- AC-4: Both recorded: a decided route carries recommendation, basis and rationale.
- AC-5: Storage boundary: no storage import and plain-dict episode metadata.

Story 11.2 (tests prefixed s112_):
- AC-0: baseline_plan_omitted flag for cost, scope or schedule routed not_applicable.
- AC-1: flags never raise for content and never make a route set invalid.
- AC-2: an accepted flagged route needs a rationale.
- AC-3: the Charter prevails; per-element home resolution and conflict reporting.
- AC-4: granularity stays open: element and section modes both behave per contract.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from agent_learning.tailoring import (
    BASELINE_SUBSTANTIATING,
    INTEGRATION_ELEMENTS,
    PLAN_IDS,
    PlanRoute,
    Route,
    compute_flags,
    resolve_home,
    to_episode_metadata,
    validate_route_set,
)


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


# ---------------------------------------------------------------------------
# Story 11.2: flags that never block, and integration-section home
# ---------------------------------------------------------------------------


def _routes_with(plan_id: str, route: Route, **kwargs) -> list[PlanRoute]:
    routes = _all_pending()
    routes[PLAN_IDS.index(plan_id)] = PlanRoute(plan_id=plan_id, route=route, **kwargs)
    return routes


def _by_element(resolutions) -> dict:
    return {r.element: r for r in resolutions}


def test_s112_ac0_each_omitted_baseline_plan_is_flagged_with_evidence() -> None:
    """AC_0: cost, scope and schedule routed not_applicable each raise baseline_plan_omitted."""
    assert set(BASELINE_SUBSTANTIATING) == {"5.1", "6.1", "7.1"}
    for plan_id in sorted(BASELINE_SUBSTANTIATING):
        flags = compute_flags(_routes_with(plan_id, Route.NOT_APPLICABLE, reason="Not needed this cycle."))
        assert [f.code for f in flags] == ["baseline_plan_omitted"]
        assert flags[0].plan_id == plan_id
        assert flags[0].message and flags[0].evidence


def test_s112_ac0_no_flag_when_baseline_plans_are_at_least_sections() -> None:
    """AC_0: no baseline_plan_omitted flag when cost, scope and schedule are at least a section."""
    assert compute_flags(_all_pending(Route.PMP_SECTION)) == []
    assert compute_flags(_all_pending(Route.FULL_PLAN)) == []


def test_s112_ac0_other_plans_may_be_not_applicable_without_a_flag() -> None:
    """AC_0: omitting a plan outside the baseline set raises no flag."""
    routes = _routes_with("12.1", Route.NOT_APPLICABLE, reason="No external sourcing is needed.")
    assert compute_flags(routes) == []


def test_s112_ac1_flags_never_raise_and_never_make_a_set_invalid() -> None:
    """AC_1: compute_flags does not raise for content, and a flagged complete set still validates."""
    assert compute_flags([]) == []
    partial = [PlanRoute(plan_id="5.1", route=Route.NOT_APPLICABLE, reason="x")]
    assert [f.plan_id for f in compute_flags(partial)] == ["5.1"]

    routes = _routes_with("7.1", Route.NOT_APPLICABLE, reason="Funding is research only.")
    assert compute_flags(routes)
    assert validate_route_set(routes) == routes


def test_s112_ac2_an_accepted_flagged_route_needs_a_rationale() -> None:
    """AC_2: a decided route that raises a flag needs a rationale; with one it is accepted."""
    pid = "7.1"
    blank = _routes_with(pid, Route.NOT_APPLICABLE)
    blank[PLAN_IDS.index(pid)] = _decided(pid, route=Route.NOT_APPLICABLE, reason="Research only.", rationale="")
    with pytest.raises(ValueError):
        validate_route_set(blank)

    accepted = _routes_with(pid, Route.NOT_APPLICABLE)
    accepted[PLAN_IDS.index(pid)] = _decided(
        pid, route=Route.NOT_APPLICABLE, reason="Research only.", rationale="Funding is research only this cycle."
    )
    assert compute_flags(accepted)
    assert validate_route_set(accepted) == accepted


def test_s112_ac2_episode_metadata_carries_the_flag_codes() -> None:
    """AC_2: to_episode_metadata records the flag codes that were raised."""
    routes = _routes_with("5.1", Route.NOT_APPLICABLE, reason="Not needed.")
    flags = compute_flags(routes)
    meta = to_episode_metadata(routes[PLAN_IDS.index("5.1")], flags)
    assert meta["flags"] == ["baseline_plan_omitted"]


def test_s112_ac3_charter_prevails_per_element() -> None:
    """AC_3: the Charter's value prevails; PMP-only elements resolve to the PMP; a differing value is a conflict."""
    res = _by_element(resolve_home({"type": "sdk", "routes": {"5.1": "full_plan"}}, {"routes": {"5.1": "pmp_section"}, "owners": "PM"}))
    assert res["type"].home == "charter" and res["type"].conflict is False
    assert res["routes"].home == "charter" and res["routes"].conflict is True
    assert res["routes"].value == {"5.1": "full_plan"}
    assert res["owners"].home == "pmp" and res["owners"].value == "PM" and res["owners"].conflict is False


def test_s112_ac3_neither_defines_an_element_gives_none() -> None:
    """AC_3: an element that neither side defines resolves to no home."""
    res = _by_element(resolve_home({}, {}))
    assert set(res) == set(INTEGRATION_ELEMENTS)
    assert all(r.home is None and r.conflict is False for r in res.values())


def test_s112_ac3_equal_values_are_not_a_conflict_and_blank_is_not_defined() -> None:
    """AC_3: the same value in both is not a conflict, and a blank value does not count as defined."""
    same = _by_element(resolve_home({"type": "sdk"}, {"type": "sdk"}))
    assert same["type"].home == "charter" and same["type"].conflict is False
    blank = _by_element(resolve_home({"type": ""}, {"type": "sdk"}))
    assert blank["type"].home == "pmp"


def test_s112_ac4_section_granularity_puts_the_whole_section_in_one_home() -> None:
    """AC_4: in section mode the Charter holds the whole section if it defines any element, else the PMP."""
    charter_holds = _by_element(resolve_home({"type": "sdk"}, {"owners": "PM"}, granularity="section"))
    assert all(r.home == "charter" for r in charter_holds.values())
    assert charter_holds["owners"].conflict is True  # the PMP version is flagged
    assert charter_holds["type"].conflict is False

    pmp_holds = _by_element(resolve_home({}, {"owners": "PM"}, granularity="section"))
    assert pmp_holds["owners"].home == "pmp" and pmp_holds["owners"].value == "PM"
    assert pmp_holds["type"].home == "pmp"

    nobody = _by_element(resolve_home({}, {}, granularity="section"))
    assert all(r.home is None for r in nobody.values())


def test_s112_ac4_element_granularity_resolves_each_element_independently() -> None:
    """AC_4: in element mode the same input splits across homes, so the open question is not pre-decided."""
    res = _by_element(resolve_home({"type": "sdk"}, {"owners": "PM"}))
    assert res["type"].home == "charter"
    assert res["owners"].home == "pmp"


def test_s112_ac4_unknown_granularity_raises() -> None:
    """AC_4: an unknown granularity raises ValueError."""
    with pytest.raises(ValueError):
        resolve_home({}, {}, granularity="paragraph")


def test_s112_ac3_blank_strings_and_every_empty_container_are_not_defined() -> None:
    """AC_3 (review finding): blank strings and empty list, tuple, dict, set and frozenset are not defined."""
    for blank in ("", "   ", [], (), {}, set(), frozenset(), None):
        res = _by_element(resolve_home({"type": blank}, {"type": "sdk"}))
        assert res["type"].home == "pmp", repr(blank)


def test_s112_ac4_section_mode_flags_a_second_home_but_not_agreement() -> None:
    """AC_4: in section mode, equal values are no conflict; a PMP value for an element the Charter section lacks is flagged."""
    agree = _by_element(resolve_home({"type": "sdk"}, {"type": "sdk"}, granularity="section"))
    assert agree["type"].conflict is False
    stray = _by_element(resolve_home({"type": "sdk"}, {"owners": "PM"}, granularity="section"))
    assert stray["owners"].conflict is True  # the PMP holds part of a section the Charter holds

