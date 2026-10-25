"""Per-plan route records, flags and integration-section home for project tailoring.

Governed by ADR-011, BRD-011, FDD-011, and Epic 11 / Stories 11.1 and 11.2.
Pure functional module: standard library only, no storage and no PMBOK tooling.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional, Sequence

# The nine management plans, following the orchestrator's PLAN_MAPPING. Renaming to the
# PMBOK 8th-edition terms is deferred and would change this one mapping only.
PLAN_NAMES: Dict[str, str] = {
    "5.1": "Scope Management Plan",
    "6.1": "Schedule Management Plan",
    "7.1": "Cost Management Plan",
    "8.1": "Quality Management Plan",
    "9.1": "Resource Management Plan",
    "10.1": "Communications Management Plan",
    "11.1": "Risk Management Plan",
    "12.1": "Procurement Management Plan",
    "13.2": "Stakeholder Engagement Plan",
}
PLAN_IDS = tuple(PLAN_NAMES)

# The plans that substantiate the PMP's baselines (scope, schedule, cost). Provisional per ADR-011.
BASELINE_SUBSTANTIATING = frozenset({"5.1", "6.1", "7.1"})

# The elements of the integration section (ADR-011): project type, route per plan, owners.
INTEGRATION_ELEMENTS = ("type", "routes", "owners")


class Route(str, Enum):
    FULL_PLAN = "full_plan"
    PMP_SECTION = "pmp_section"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True)
class PlanRoute:
    """The route for one plan: the decided route, or the recommended one while undecided."""

    plan_id: str
    route: Route
    reason: str = ""
    recommended_route: Optional[Route] = None
    recommendation_basis: str = ""
    decided: bool = False
    decided_by_role: str = ""
    decided_by_human: bool = False
    rationale: str = ""

    def __post_init__(self) -> None:
        # Coerce strings to Route; an unknown value raises ValueError.
        object.__setattr__(self, "route", Route(self.route))
        if self.recommended_route is not None:
            object.__setattr__(self, "recommended_route", Route(self.recommended_route))


@dataclass(frozen=True)
class Flag:
    """Evidence put in front of a human. A flag never blocks a decision."""

    code: str
    plan_id: str
    message: str
    evidence: str


@dataclass(frozen=True)
class HomeResolution:
    element: str
    home: Optional[str]  # "charter", "pmp" or None
    value: Any
    conflict: bool


def validate_route_set(routes: Sequence[PlanRoute]) -> Sequence[PlanRoute]:
    """Check a set of routes and return it unchanged.

    Raises:
        ValueError: if a plan is missing, duplicated or unknown, a not-applicable route has no
            reason, or a decided route breaks the human-decision rules.
    """
    seen: Dict[str, int] = {}
    for route in routes:
        seen[route.plan_id] = seen.get(route.plan_id, 0) + 1

    unknown = sorted(pid for pid in seen if pid not in PLAN_NAMES)
    if unknown:
        raise ValueError(f"Unknown plan id(s): {', '.join(unknown)}")
    duplicated = sorted(pid for pid, count in seen.items() if count > 1)
    if duplicated:
        raise ValueError(f"Duplicate route for plan id(s): {', '.join(duplicated)}")
    missing = [pid for pid in PLAN_IDS if pid not in seen]
    if missing:
        raise ValueError(f"No route recorded for plan id(s): {', '.join(missing)}; omission is never silent")

    for route in routes:
        if route.route is Route.NOT_APPLICABLE and not route.reason.strip():
            raise ValueError(f"Plan {route.plan_id}: 'not_applicable' needs a stated reason")
        if route.decided:
            if not route.decided_by_human:
                raise ValueError(f"Plan {route.plan_id}: a route must be decided by a human")
            if not route.decided_by_role.strip():
                raise ValueError(f"Plan {route.plan_id}: a decided route needs the deciding role")
            if route.recommended_route is None:
                raise ValueError(f"Plan {route.plan_id}: a decided route must record the recommended route")
            if not route.recommendation_basis.strip():
                raise ValueError(f"Plan {route.plan_id}: a decided route must record the basis of the recommendation")
            if not route.rationale.strip():
                raise ValueError(f"Plan {route.plan_id}: a decided route must record its rationale")
    return routes


def to_episode_metadata(route: PlanRoute, flags: Sequence[Any] = ()) -> Dict[str, Any]:
    """Return a plain dict for ``Episode.metadata``; no new record type is introduced."""
    recommended = route.recommended_route
    return {
        "plan_id": route.plan_id,
        "recommended_route": recommended.value if recommended else None,
        "decided_route": route.route.value if route.decided else None,
        "rationale": route.rationale,
        "decided_by_role": route.decided_by_role,
        "diverged": bool(route.decided and recommended is not None and recommended != route.route),
        "flags": [getattr(flag, "code", flag) for flag in flags],
    }


def compute_flags(routes: Sequence[PlanRoute]) -> List[Flag]:
    """Return the flags a route set raises. Never raises for content and never blocks."""
    by_plan = {route.plan_id: route for route in routes}
    flags: List[Flag] = []
    for plan_id in PLAN_IDS:
        route = by_plan.get(plan_id)
        if plan_id in BASELINE_SUBSTANTIATING and route is not None and route.route is Route.NOT_APPLICABLE:
            name = PLAN_NAMES[plan_id]
            flags.append(
                Flag(
                    code="baseline_plan_omitted",
                    plan_id=plan_id,
                    message=f"{name} substantiates a PMP baseline but is routed not_applicable",
                    evidence=f"{name} is not_applicable; reason: {route.reason.strip() or 'none given'}",
                )
            )
    return flags


def _defined(value: Any) -> bool:
    return value is not None and value != "" and value != [] and value != {}


def resolve_home(
    charter: Mapping[str, Any],
    pmp: Mapping[str, Any],
    granularity: str = "element",
    elements: Sequence[str] = INTEGRATION_ELEMENTS,
) -> List[HomeResolution]:
    """Resolve where each integration-section element lives: the Charter if it defines it, else the PMP.

    With ``granularity="element"`` each element resolves on its own. With ``"section"`` the whole
    section sits in the Charter if the Charter defines any element, else in the PMP. In both modes the
    Charter prevails and a PMP value that disagrees with it is reported as a conflict.
    """
    if granularity not in ("element", "section"):
        raise ValueError(f"Unknown granularity '{granularity}'; expected 'element' or 'section'")

    names = list(dict.fromkeys([*elements, *charter, *pmp]))
    section_home: Optional[str] = None
    if granularity == "section":
        if any(_defined(charter.get(name)) for name in names):
            section_home = "charter"
        elif any(_defined(pmp.get(name)) for name in names):
            section_home = "pmp"

    resolutions: List[HomeResolution] = []
    for name in names:
        c_val, p_val = charter.get(name), pmp.get(name)
        if granularity == "element":
            if _defined(c_val):
                resolutions.append(HomeResolution(name, "charter", c_val, _defined(p_val) and p_val != c_val))
            elif _defined(p_val):
                resolutions.append(HomeResolution(name, "pmp", p_val, False))
            else:
                resolutions.append(HomeResolution(name, None, None, False))
        elif section_home == "charter":
            resolutions.append(
                HomeResolution(name, "charter", c_val if _defined(c_val) else None, _defined(p_val) and p_val != c_val)
            )
        elif section_home == "pmp":
            resolutions.append(HomeResolution(name, "pmp", p_val if _defined(p_val) else None, False))
        else:
            resolutions.append(HomeResolution(name, None, None, False))
    return resolutions

