"""Contract tests for Story 26.1: Schedule floors, caps, and exclusions.

Story: docs/user-stories/epic-26-schedule-management-plan-standard-and-baseline-contract.md (Story 26.1)
ADR:   ADR-026 sections 4.3 and 5
BRD:   BRD-026 (BRU-026-01, BRU-026-02)
FDD:   FDD-026 sections 2 and 3.1 to 3.3
"""

from __future__ import annotations

import ast
from pathlib import Path

from agent_learning.pmbok import ScheduleMeasure, check_content, lint_plan, schedule_measure
from tests.test_plan_content import codes, make_body

ROOT = Path(__file__).resolve().parents[1]


def schedule_doc(body: str, route: str = "full_plan") -> str:
    policy = "approve-subsidiary-plan" if route == "full_plan" else "approve-pmp"
    return (
        "---\n"
        'plan_id: "schedule-management"\n'
        'plan_name: "Schedule Management Plan"\n'
        'pmbok_edition: "PMBOK 8"\n'
        'pmbok_focus_area: "Planning"\n'
        'primary_pmbok_domain: "Schedule"\n'
        'legacy_process: "6.1 Plan Schedule Management"\n'
        f'route: "{route}"\n'
        'generator: "human"\n'
        'version: "1.0.0"\n'
        'baseline_id: "PMP-BL-v1.0.0"\n'
        'owner_role: "Project Manager"\n'
        "depends_on:\n"
        "  - scope-management\n"
        "inputs:\n"
        "  - Project-Charter.md\n"
        "outputs:\n"
        "  - Schedule-Management-Plan.md\n"
        f'governance_policy: "{policy}"\n'
        "---\n"
        f"{body}"
    )


def plan_doc(plan_id: str, route: str, body: str) -> str:
    details = {
        "scope-management": ("Scope Management Plan", "Scope", "5.1 Plan Scope Management", "[]"),
        "cost-management": ("Cost Management Plan", "Finance", "7.1 Plan Cost Management", "[schedule-management]"),
    }
    name, domain, legacy, dependencies = details[plan_id]
    policy = "approve-subsidiary-plan" if route == "full_plan" else "approve-pmp"
    return (
        "---\n"
        f'plan_id: "{plan_id}"\n'
        f'plan_name: "{name}"\n'
        'pmbok_edition: "PMBOK 8"\n'
        'pmbok_focus_area: "Planning"\n'
        f'primary_pmbok_domain: "{domain}"\n'
        f'legacy_process: "{legacy}"\n'
        f'route: "{route}"\n'
        'generator: "human"\n'
        'version: "1.0.0"\n'
        'baseline_id: "PMP-BL-v1.0.0"\n'
        'owner_role: "Project Manager"\n'
        f"depends_on: {dependencies}\n"
        "inputs:\n"
        "  - Project-Charter.md\n"
        "outputs:\n"
        f"  - {name.replace(' ', '-')}.md\n"
        f'governance_policy: "{policy}"\n'
        "---\n"
        f"{body}"
    )


def exclusions(*items: str) -> str:
    return "Out-of-scope boundaries:\n" + "".join(f"- {item}\n" for item in items)


class TestScheduleMeasureProfile:
    """AC_0"""

    def test_schedule_profile_routes_and_other_plans(self):
        section = schedule_measure("schedule-management", "pmp_section")
        full = schedule_measure("schedule-management", "full_plan")
        assert section == ScheduleMeasure(floor=180, cap=750, min_out_of_scope_items=2)
        assert full == ScheduleMeasure(floor=700, cap=4500, min_out_of_scope_items=4)
        assert schedule_measure("schedule-management", "not_applicable") is None
        assert schedule_measure("scope-management", "pmp_section") is None
        assert schedule_measure("cost-management", "full_plan") is None


class TestScheduleLengths:
    """AC_1"""

    def test_schedule_route_length_boundaries_and_tiers(self):
        valid_boundaries = exclusions("Alpha exclusion.", "Beta exclusion.", "Gamma exclusion.", "Delta exclusion.")
        cases = (
            ("pmp_section", 179, "BELOW_STANDARD_FLOOR"),
            ("pmp_section", 180, None),
            ("pmp_section", 750, None),
            ("pmp_section", 751, "EXCEEDS_SECTION_CAP"),
            ("full_plan", 699, "BELOW_STANDARD_FLOOR"),
            ("full_plan", 700, None),
            ("full_plan", 4500, None),
            ("full_plan", 4501, "EXCEEDS_PLAN_CAP"),
        )
        for route, count, expected in cases:
            doc = schedule_doc(make_body(count, section1=valid_boundaries), route)
            flags = lint_plan(doc).flags
            length_flags = [flag for flag in flags if flag.code in {
                "BELOW_STANDARD_FLOOR",
                "EXCEEDS_SECTION_CAP",
                "EXCEEDS_PLAN_CAP",
            }]
            assert ([flag.code for flag in length_flags] == [expected]) if expected else not length_flags
            assert all(flag.tier == "C" for flag in length_flags)


class TestOtherPlans:
    """AC_2"""

    def test_cost_keeps_universal_thresholds_and_scope_is_not_schedule_profiled(self):
        body = make_body(179, section1=exclusions("One exclusion."))
        cost_short = plan_doc("cost-management", "pmp_section", body)
        assert "BELOW_STANDARD_FLOOR" not in codes(lint_plan(cost_short).flags)

        body = make_body(751, section1=exclusions("One exclusion."))
        cost_within_cap = plan_doc("cost-management", "pmp_section", body)
        assert "EXCEEDS_SECTION_CAP" not in codes(lint_plan(cost_within_cap).flags)

        scope = plan_doc("scope-management", "pmp_section", make_body(180))
        assert schedule_measure("scope-management", "pmp_section") is None
        assert lint_plan(scope).word_count == 180


class TestScheduleBoundaryItems:
    """AC_3"""

    def test_schedule_placeholder_exclusion_minimum_and_none_rationale(self):
        one_real_and_tbd = schedule_doc(
            make_body(750, section1=exclusions("Real exclusion.", "TBD")),
            "pmp_section",
        )
        assert "MISSING_BOUNDARY_DEF" in codes(lint_plan(one_real_and_tbd).flags)

        two_real = schedule_doc(
            make_body(750, section1=exclusions("First real exclusion.", "Second real exclusion.")),
            "pmp_section",
        )
        assert "MISSING_BOUNDARY_DEF" not in codes(lint_plan(two_real).flags)

        explanatory_na = schedule_doc(
            make_body(750, section1=exclusions("N/A for vendor delivery dates", "Second real exclusion.")),
            "pmp_section",
        )
        assert "MISSING_BOUNDARY_DEF" not in codes(lint_plan(explanatory_na).flags)

        none_rationale = schedule_doc(
            make_body(750, section1="None: " + " ".join(["reason"] * 10)),
            "pmp_section",
        )
        assert "MISSING_BOUNDARY_DEF" not in codes(lint_plan(none_rationale).flags)

        cost_one_item = plan_doc(
            "cost-management",
            "pmp_section",
            make_body(750, section1=exclusions("One real exclusion.")),
        )
        assert "MISSING_BOUNDARY_DEF" not in codes(lint_plan(cost_one_item).flags)


class TestScheduleCannotRelax:
    """AC_4"""

    def test_schedule_caller_options_cannot_relax_and_can_raise_profile(self):
        low_options = schedule_doc(
            make_body(179, section1=exclusions("One real exclusion.", "TBD")),
            "pmp_section",
        )
        found = codes(lint_plan(low_options, min_floor_words=10, min_out_of_scope_items=0).flags)
        assert "BELOW_STANDARD_FLOOR" in found
        assert "MISSING_BOUNDARY_DEF" in found

        raised_floor = schedule_doc(
            make_body(
                180,
                section1=exclusions("First real exclusion.", "Second real exclusion."),
            ),
            "pmp_section",
        )
        assert "BELOW_STANDARD_FLOOR" in codes(lint_plan(raised_floor, min_floor_words=181).flags)

        raised_items = schedule_doc(
            make_body(
                750,
                section1=exclusions("First real exclusion.", "Second real exclusion."),
            ),
            "pmp_section",
        )
        assert "MISSING_BOUNDARY_DEF" in codes(lint_plan(raised_items, min_out_of_scope_items=3).flags)
        assert check_content(make_body(801), "pmp_section", max_cap_words=900)[0].code == "EXCEEDS_SECTION_CAP"


class TestSchedulePurity:
    """AC_5"""

    def test_schedule_module_does_not_import_storage(self):
        path = ROOT / "src" / "agent_learning" / "pmbok" / "schedule.py"
        assert path.is_file(), "Schedule profile module is missing"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all("storage" not in alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                assert "storage" not in (node.module or "")
