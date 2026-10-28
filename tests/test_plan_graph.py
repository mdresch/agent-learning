"""Contract tests for Story 13.4: The Dependency Graph.

Story: docs/user-stories/epic-13-subsidiary-plan-approval-gates-before-pmp-formalization.md (Story 13.4)
ADR:   ADR-013 section 4.1; ADR-034 sections 4.2.2, ERR-034-06
BRD:   BRD-013 (BRU-013-04)
FDD:   FDD-013 sections 2.1, 3.4
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from agent_learning.pmbok import (
    DRAFT_ORDER,
    PLAN_DAG,
    CyclicDependencyError,
    effective_upstreams,
    parse_frontmatter,
    topological_order,
    validate_dependencies,
)

REPO = Path(__file__).resolve().parent.parent
ADR_DIR = REPO / "docs" / "adr"


def adr_frontmatter_example(adr_number: int) -> str:
    matches = sorted(ADR_DIR.glob(f"ADR-{adr_number:03d}-*.md"))
    assert matches, f"ADR-{adr_number:03d} is missing from {ADR_DIR}; the frontmatter example cannot be read"
    text = matches[0].read_text(encoding="utf-8")
    for block in re.finditer(r"```yaml\n(.*?)```", text, re.DOTALL):
        if block.group(1).startswith("---\n"):
            return block.group(1)
    raise AssertionError(f"ADR-{adr_number:03d} has no frontmatter example starting with '---'")


class TestPlanGraph:
    """Acceptance criteria tests for Story 13.4."""

    def test_ac0_authoritative_graph(self) -> None:
        """$AC_0$: PLAN_DAG has 9 plans and FDD-013 section 2.1 edges; each daughter ADR frontmatter matches."""
        expected_dag = {
            "scope-management": (),
            "schedule-management": ("scope-management",),
            "cost-management": ("scope-management", "schedule-management"),
            "quality-management": ("scope-management",),
            "resource-management": ("scope-management", "schedule-management"),
            "communications-management": ("scope-management",),
            "risk-management": ("scope-management", "schedule-management", "cost-management"),
            "procurement-management": ("scope-management", "cost-management"),
            "stakeholder-engagement": ("scope-management",),
        }
        assert dict(PLAN_DAG) == expected_dag

        # For each of ADR-025 to ADR-033, depends_on equals graph edges
        for adr_num in range(25, 34):
            fm_text = adr_frontmatter_example(adr_num)
            parsed = parse_frontmatter(fm_text)
            assert parsed.parsed, f"ADR-{adr_num:03d} frontmatter failed to parse"
            plan_id = parsed.metadata["plan_id"]
            assert plan_id in PLAN_DAG, f"ADR-{adr_num:03d} plan_id {plan_id!r} not in PLAN_DAG"
            assert parsed.metadata["depends_on"] == PLAN_DAG[plan_id]

    def test_ac1_topological_order(self) -> None:
        """$AC_1$: topological_order(PLAN_DAG) puts dependencies first, breaks ties by DRAFT_ORDER; DRAFT_ORDER is valid order."""
        order = topological_order(PLAN_DAG)
        assert len(order) == 9
        assert set(order) == set(PLAN_DAG.keys())

        # Every plan appears after its dependencies
        pos = {plan: idx for idx, plan in enumerate(order)}
        for plan, deps in PLAN_DAG.items():
            for dep in deps:
                assert pos[dep] < pos[plan], f"dependency {dep} appears after {plan}"

        # DRAFT_ORDER is itself a valid topological order
        draft_pos = {plan: idx for idx, plan in enumerate(DRAFT_ORDER)}
        for plan, deps in PLAN_DAG.items():
            for dep in deps:
                assert draft_pos[dep] < draft_pos[plan], f"dependency {dep} appears after {plan} in DRAFT_ORDER"

        # Ties broken by DRAFT_ORDER yields DRAFT_ORDER itself
        assert order == DRAFT_ORDER

    def test_ac2_effective_upstreams(self) -> None:
        """$AC_2$: effective_upstreams returns direct deps, replaces not_applicable deps recursively, sorts without duplicates."""
        # When all upstreams are full_plan (or missing route -> full_plan)
        routes_all_full = {"scope-management": "full_plan", "schedule-management": "full_plan"}
        assert effective_upstreams("cost-management", PLAN_DAG, routes_all_full) == [
            "schedule-management",
            "scope-management",
        ]

        # Missing route defaults to full_plan
        assert effective_upstreams("cost-management", PLAN_DAG, {}) == [
            "schedule-management",
            "scope-management",
        ]

        # Single not_applicable bypass:
        # Schedule is not_applicable -> Cost's effective upstreams are Scope (from Scope direct + Schedule's Scope)
        routes_schedule_na = {"schedule-management": "not_applicable"}
        assert effective_upstreams("cost-management", PLAN_DAG, routes_schedule_na) == ["scope-management"]

        # Recursive bypass through multi-node chain:
        # A -> B -> C -> D where B and C are not_applicable
        chain_dag = {
            "root": (),
            "node_b": ("root",),
            "node_c": ("node_b",),
            "node_d": ("node_c",),
        }
        routes_chain = {"node_b": "not_applicable", "node_c": "not_applicable"}
        assert effective_upstreams("node_d", chain_dag, routes_chain) == ["root"]

    def test_ac3_cycles_and_diamonds_and_bad_edges(self) -> None:
        """$AC_3$: cycle raises CyclicDependencyError in both; diamond succeeds; bad edge raises ValueError in topological_order."""
        # Cycle A -> B -> A
        cycle_dag = {
            "A": ("B",),
            "B": ("A",),
        }
        with pytest.raises(CyclicDependencyError):
            topological_order(cycle_dag)

        routes_na = {"A": "not_applicable", "B": "not_applicable"}
        with pytest.raises(CyclicDependencyError):
            effective_upstreams("A", cycle_dag, routes_na)

        # Longer cycle A -> B -> C -> A
        ring_dag = {
            "A": ("C",),
            "B": ("A",),
            "C": ("B",),
        }
        with pytest.raises(CyclicDependencyError):
            topological_order(ring_dag)
        routes_ring_na = {"A": "not_applicable", "B": "not_applicable", "C": "not_applicable"}
        with pytest.raises(CyclicDependencyError):
            effective_upstreams("A", ring_dag, routes_ring_na)

        # Diamond DAG: D -> (B, C) -> A
        diamond_dag = {
            "A": (),
            "B": ("A",),
            "C": ("A",),
            "D": ("B", "C"),
        }
        order = topological_order(diamond_dag)
        assert order[0] == "A"
        assert order[-1] == "D"
        assert set(order[1:3]) == {"B", "C"}

        # Diamond effective upstreams with both B and C not_applicable -> evaluates without error
        routes_diamond_na = {"B": "not_applicable", "C": "not_applicable"}
        assert effective_upstreams("D", diamond_dag, routes_diamond_na) == ["A"]

        # Edge to a plan not in dag raises ValueError in topological_order
        bad_edge_dag = {
            "A": ("NON_EXISTENT",),
        }
        with pytest.raises(ValueError, match="NON_EXISTENT"):
            topological_order(bad_edge_dag)

    def test_ac4_validate_dependencies(self) -> None:
        """$AC_4$: validate_dependencies gives 1 Tier B INVALID_METADATA naming depends_on on mismatch; none on match/unknown/missing."""
        # Exact match in order
        meta_ok = {"plan_id": "cost-management", "depends_on": ("scope-management", "schedule-management")}
        assert validate_dependencies(meta_ok) == []

        # Match in different order
        meta_reordered = {"plan_id": "cost-management", "depends_on": ("schedule-management", "scope-management")}
        assert validate_dependencies(meta_reordered) == []

        # Extra dependency
        meta_extra = {
            "plan_id": "schedule-management",
            "depends_on": ("scope-management", "cost-management"),
        }
        flags_extra = validate_dependencies(meta_extra)
        assert len(flags_extra) == 1
        assert flags_extra[0].code == "INVALID_METADATA"
        assert flags_extra[0].tier == "B"
        assert "depends_on" in flags_extra[0].message
        assert "['scope-management']" in flags_extra[0].message

        # Missing dependency
        meta_missing = {"plan_id": "cost-management", "depends_on": ("scope-management",)}
        flags_missing = validate_dependencies(meta_missing)
        assert len(flags_missing) == 1
        assert flags_missing[0].code == "INVALID_METADATA"
        assert flags_missing[0].tier == "B"

        # Wrong dependency
        meta_wrong = {"plan_id": "schedule-management", "depends_on": ("risk-management",)}
        flags_wrong = validate_dependencies(meta_wrong)
        assert len(flags_wrong) == 1

        # Unknown plan gives nothing
        assert validate_dependencies({"plan_id": "custom-plan", "depends_on": ("scope-management",)}) == []

        # Missing or malformed depends_on gives nothing (handled by validate_metadata)
        assert validate_dependencies({"plan_id": "scope-management"}) == []
        assert validate_dependencies({"plan_id": "scope-management", "depends_on": None}) == []
        assert validate_dependencies({"plan_id": "scope-management", "depends_on": "not-a-list"}) == []
        assert validate_dependencies({"plan_id": "scope-management", "depends_on": [123]}) == []
        assert validate_dependencies("not a mapping") == []  # type: ignore[arg-type]

    def test_ac5_real_plans_adr025_to_033(self) -> None:
        """$AC_5$: validate_dependencies gives no finding for the frontmatter example of each of ADR-025 to ADR-033."""
        for adr_num in range(25, 34):
            fm_text = adr_frontmatter_example(adr_num)
            parsed = parse_frontmatter(fm_text)
            assert parsed.parsed
            flags = validate_dependencies(parsed.metadata)
            assert flags == [], f"ADR-{adr_num:03d} frontmatter produced dependency flags: {flags}"

