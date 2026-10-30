"""Contract tests for Story 25.1: Scope floors, caps, and exclusions.

Story: docs/user-stories/epic-25-scope-management-plan-standard-and-baseline-contract.md (Story 25.1)
ADR:   ADR-025
BRD:   BRD-025 (BRU-025-01, BRU-025-02)
FDD:   FDD-025 sections 3.1 to 3.3
"""

from __future__ import annotations

import ast
from pathlib import Path

from agent_learning.pmbok import check_content, lint_plan
from agent_learning.pmbok.scope import scope_measure
from agent_learning.pmbok.standards import CAPS
from tests.test_plan_content import DECL, H1, H2, H3, codes, make_body

SCOPE_FM = (
    "---\n"
    'plan_id: "scope-management"\n'
    'plan_name: "Scope Management Plan"\n'
    'pmbok_edition: "PMBOK 8"\n'
    'pmbok_focus_area: "Planning"\n'
    'primary_pmbok_domain: "Scope"\n'
    'legacy_process: "5.1 Plan Scope Management"\n'
    'route: "{route}"\n'
    'generator: "human"\n'
    'version: "1.2.0"\n'
    'baseline_id: "PMP-BL-v1.0.0"\n'
    'owner_role: "Project Manager"\n'
    "depends_on: []\n"
    "inputs:\n"
    "  - Project-Charter.md\n"
    "outputs:\n"
    '  - "docs/project-docs/management-plans/Scope-Management-Plan.md"\n'
    'governance_policy: "{policy}"\n'
    "---\n"
)


def scope_doc(body: str, route: str = "full_plan") -> str:
    policy = "approve-subsidiary-plan" if route == "full_plan" else "approve-pmp"
    return SCOPE_FM.format(route=route, policy=policy) + body


def section1_two_real() -> str:
    return "Out-of-scope boundaries:\n- First excluded item here.\n- Second excluded item here.\n"


def section1_one_real_one_tbd() -> str:
    return "Out-of-scope boundaries:\n- Real exclusion for clients.\n- TBD\n"


def section2_wbs_dod_full() -> str:
    return (
        "Work breakdown structure: phase → epic → story → commit.\n"
        "Definition of Done covers acceptance criteria, owner, and parent on each work package.\n"
    )


class TestScopeMeasureProfile:
    """AC_0"""

    def test_scope_pmp_section_profile(self):
        m = scope_measure("scope-management", "pmp_section")
        assert m is not None
        assert m.floor == 180 and m.cap == 750 and m.min_out_of_scope_items == 2

    def test_scope_full_plan_profile(self):
        m = scope_measure("scope-management", "full_plan")
        assert m is not None
        assert m.floor == 700 and m.cap == 4500 and m.min_out_of_scope_items == 4

    def test_not_applicable_and_other_plans_return_none(self):
        assert scope_measure("scope-management", "not_applicable") is None
        assert scope_measure("schedule-management", "full_plan") is None
        assert scope_measure("cost-management", "pmp_section") is None


class TestScopeLengths:
    """AC_1, AC_2"""

    def test_pmp_section_length_thresholds(self):
        route = "pmp_section"
        s2 = section2_wbs_dod_full()
        short = scope_doc(make_body(179, section1=section1_two_real(), h2=s2, h3=None), route)
        assert "BELOW_STANDARD_FLOOR" in codes(lint_plan(short).flags)
        ok_low = scope_doc(make_body(180, section1=section1_two_real(), h2=s2, h3=None), route)
        assert "BELOW_STANDARD_FLOOR" not in codes(lint_plan(ok_low).flags)
        ok_mid = scope_doc(make_body(750, section1=section1_two_real(), h2=s2, h3=None), route)
        assert not [c for c in codes(lint_plan(ok_mid).flags) if c.startswith("EXCEEDS")]
        over = scope_doc(make_body(751, section1=section1_two_real(), h2=s2, h3=None), route)
        assert "EXCEEDS_SECTION_CAP" in codes(lint_plan(over).flags)
        for f in lint_plan(over).flags:
            if f.code == "EXCEEDS_SECTION_CAP":
                assert f.tier == "C"

    def test_full_plan_length_thresholds(self):
        route = "full_plan"
        s2 = section2_wbs_dod_full()
        under = scope_doc(make_body(699, section1=section1_four_items(), h2=s2), route)
        assert "BELOW_STANDARD_FLOOR" in codes(lint_plan(under).flags)
        at700 = scope_doc(make_body(700, section1=section1_four_items(), h2=s2), route)
        assert "BELOW_STANDARD_FLOOR" not in codes(lint_plan(at700).flags)
        at4500 = scope_doc(make_body(4500, section1=section1_four_items(), h2=s2), route)
        assert not [c for c in codes(lint_plan(at4500).flags) if c.startswith("EXCEEDS")]
        over = scope_doc(make_body(4501, section1=section1_four_items(), h2=s2), route)
        assert "EXCEEDS_PLAN_CAP" in codes(lint_plan(over).flags)

    def test_schedule_keeps_universal_caps(self):
        sched = (
            "---\nplan_id: schedule-management\nplan_name: x\npmbok_edition: PMBOK 8\n"
            "pmbok_focus_area: Planning\nprimary_pmbok_domain: Schedule\nlegacy_process: 6.1 Plan Schedule Management\n"
            'route: pmp_section\ngenerator: human\nversion: 1.0.0\nbaseline_id: PMP-BL-v1.0.0\n'
            'owner_role: PM\ndepends_on: [scope-management]\ninputs: [Project-Charter.md]\noutputs: [Schedule-Management-Plan.md]\n'
            'governance_policy: approve-pmp\n---\n'
            + make_body(751)
        )
        assert "EXCEEDS_SECTION_CAP" not in codes(lint_plan(sched).flags)
        short = make_body(179)
        assert "BELOW_STANDARD_FLOOR" not in codes(
            check_content(short, "pmp_section", min_floor_words=150)
        )


def section1_four_items() -> str:
    return (
        "Out-of-scope boundaries:\n"
        "- Alpha exclusion.\n"
        "- Beta exclusion.\n"
        "- Gamma exclusion.\n"
        "- Delta exclusion.\n"
    )


class TestScopeBoundaries:
    """AC_3"""

    def test_one_real_and_tbd_raises_boundary_on_scope(self):
        body = scope_doc(make_body(750, section1=section1_one_real_one_tbd(), h2=section2_wbs_dod_full()), "pmp_section")
        assert "MISSING_BOUNDARY_DEF" in codes(lint_plan(body).flags)

    def test_two_real_bullets_pass(self):
        body = scope_doc(make_body(750, section1=section1_two_real(), h2=section2_wbs_dod_full()), "pmp_section")
        assert "MISSING_BOUNDARY_DEF" not in codes(lint_plan(body).flags)

    def test_na_for_mobile_counts_as_real(self):
        s1 = "Out-of-scope boundaries:\n- N/A for mobile clients\n- Another real line here.\n"
        body = scope_doc(make_body(750, section1=s1, h2=section2_wbs_dod_full()), "pmp_section")
        assert "MISSING_BOUNDARY_DEF" not in codes(lint_plan(body).flags)

    def test_unbalanced_bracket_placeholder_counts_as_real(self):
        s1 = "Out-of-scope boundaries:\n- [TBD but scoped to clients\n- TBD]\n"
        body = scope_doc(make_body(750, section1=s1, h2=section2_wbs_dod_full()), "pmp_section")
        assert "MISSING_BOUNDARY_DEF" not in codes(lint_plan(body).flags)

    def test_bracketed_tbd_is_placeholder(self):
        s1 = "Out-of-scope boundaries:\n- Real exclusion for clients.\n- [TBD]\n"
        body = scope_doc(make_body(750, section1=s1, h2=section2_wbs_dod_full()), "pmp_section")
        assert "MISSING_BOUNDARY_DEF" in codes(lint_plan(body).flags)

    def test_none_line_satisfies_without_bullets(self):
        s1 = "None: " + " ".join(["reason"] * 10) + "\n"
        body = scope_doc(make_body(750, section1=s1, h2=section2_wbs_dod_full()), "pmp_section")
        assert "MISSING_BOUNDARY_DEF" not in codes(lint_plan(body).flags)

    def test_one_bullet_on_schedule_does_not_use_scope_boundary_rules(self):
        s1 = "Out-of-scope boundaries:\n- Only one item listed.\n"
        sched = (
            SCOPE_FM.format(route="full_plan", policy="approve-subsidiary-plan")
            .replace("scope-management", "schedule-management")
            .replace("Scope Management Plan", "Schedule Management Plan")
            .replace('primary_pmbok_domain: "Scope"', 'primary_pmbok_domain: "Schedule"')
            .replace("5.1 Plan Scope Management", "6.1 Plan Schedule Management")
            .replace("depends_on: []", "depends_on: [scope-management]")
            + make_body(800, section1=s1)
        )
        assert "MISSING_BOUNDARY_DEF" not in codes(lint_plan(sched).flags)


class TestScopeMeasureCannotRelax:
    """AC_4"""

    def test_caller_cannot_lower_scope_floor_or_items(self):
        doc = scope_doc(make_body(179, section1=section1_one_real_one_tbd(), h2=section2_wbs_dod_full()), "pmp_section")
        found = codes(lint_plan(doc, min_floor_words=10, min_out_of_scope_items=0).flags)
        assert "BELOW_STANDARD_FLOOR" in found
        assert "MISSING_BOUNDARY_DEF" in found

    def test_caller_can_raise_floor_and_items(self):
        body = make_body(750, section1=section1_two_real(), h2=section2_wbs_dod_full())
        assert "BELOW_STANDARD_FLOOR" in codes(
            check_content(body, "pmp_section", min_floor_words=800, max_cap_words=750, exclude_placeholders=True)
        )

    def test_max_cap_above_universal_leaves_universal_for_other_plan(self):
        assert check_content(make_body(801), "pmp_section", max_cap_words=900)[0].code == "EXCEEDS_SECTION_CAP"
        assert CAPS["pmp_section"] == 800


class TestScopePurity:
    """AC_5"""

    def test_scope_module_has_no_storage_imports(self):
        path = Path(__file__).resolve().parents[1] / "src" / "agent_learning" / "pmbok" / "scope.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "storage" not in alias.name
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                assert "storage" not in mod
