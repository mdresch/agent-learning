"""Per-plan route records and the human-decision invariants for project tailoring.

Governed by ADR-011, BRD-011, FDD-011, and Epic 11 / Story 11.1.
Pure functional module: standard library only, no storage and no PMBOK tooling.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Sequence

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
            if route.recommended_route is None or not route.recommendation_basis.strip():
                raise ValueError(f"Plan {route.plan_id}: a decided route must record the recommendation and its basis")
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
        "diverged": bool(route.decided and recommended is not None and recommended is not route.route),
        "flags": [getattr(flag, "code", flag) for flag in flags],
    }
