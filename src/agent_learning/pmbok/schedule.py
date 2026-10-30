"""Schedule Management Plan measurement profile (ADR-026, FDD-026). Pure: no I/O, no storage."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

SCHEDULE_PLAN_ID = "schedule-management"


@dataclass(frozen=True)
class ScheduleMeasure:
    floor: int
    cap: int
    min_out_of_scope_items: int


SCHEDULE_MEASURES: Mapping[str, ScheduleMeasure] = MappingProxyType(
    {
        "pmp_section": ScheduleMeasure(floor=180, cap=750, min_out_of_scope_items=2),
        "full_plan": ScheduleMeasure(floor=700, cap=4500, min_out_of_scope_items=4),
    }
)


def schedule_measure(plan_id: str, route: str) -> ScheduleMeasure | None:
    """Return Schedule thresholds for this plan and route, or None for all others."""
    if plan_id != SCHEDULE_PLAN_ID or route not in SCHEDULE_MEASURES:
        return None
    return SCHEDULE_MEASURES[route]
