"""Shared types and constants of the subsidiary management plan lint (ADR-012, FDD-012 section 2).

Pure: standard library only, no I/O and no storage.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

DOMAINS = ("Governance", "Scope", "Schedule", "Finance", "Stakeholders", "Resources", "Risk")
ROUTES = ("full_plan", "pmp_section", "not_applicable")
GENERATORS = ("llm", "human", "stub", "mock")
# secondary_pmbok_domains is optional and is not listed here.
REQUIRED_KEYS = (
    "plan_id",
    "plan_name",
    "pmbok_edition",
    "pmbok_focus_area",
    "primary_pmbok_domain",
    "legacy_process",
    "route",
    "generator",
    "version",
    "baseline_id",
    "owner_role",
    "depends_on",
    "inputs",
    "outputs",
    "governance_policy",
)


@dataclass(frozen=True)
class LintFlag:
    """One finding of the plan lint.

    ``tier`` is a Flag Tier (A, B or C), never a Plan Tier. ``line`` is the 1-based line in the
    original text when known; ``evidence`` is the offending text.
    """

    code: str
    tier: Literal["A", "B", "C"]
    message: str
    line: int | None = None
    evidence: str = ""


@dataclass(frozen=True)
class PlanStandard:
    """One row of the ADR-012 section 4.4 table. ``plan_tier`` is a Plan Tier (1 to 3), never a Flag Tier."""

    primary: str
    secondary: tuple[str, ...]
    legacy: str
    plan_tier: int


PLAN_STANDARDS: Mapping[str, PlanStandard] = MappingProxyType(
    {
        "scope-management": PlanStandard("Scope", ("Governance",), "5.1", 1),
        "schedule-management": PlanStandard("Schedule", ("Governance",), "6.1", 1),
        "cost-management": PlanStandard("Finance", ("Governance",), "7.1", 1),
        "quality-management": PlanStandard("Governance", ("Scope",), "8.1", 2),
        "resource-management": PlanStandard("Resources", ("Governance",), "9.1", 3),
        "communications-management": PlanStandard("Stakeholders", ("Governance",), "10.1", 3),
        "risk-management": PlanStandard("Risk", ("Governance", "Finance"), "11.1", 2),
        "procurement-management": PlanStandard("Finance", ("Resources", "Governance"), "12.1", 3),
        "stakeholder-engagement": PlanStandard("Stakeholders", ("Governance",), "13.2", 3),
    }
)
