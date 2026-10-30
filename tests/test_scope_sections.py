"""Contract tests for Story 25.2: WBS and Definition of Done in Section 2.

Story: docs/user-stories/epic-25-scope-management-plan-standard-and-baseline-contract.md (Story 25.2)
ADR:   ADR-025
BRD:   BRD-025 (BRU-025-03)
FDD:   FDD-025 section 3.4
"""

from __future__ import annotations

from agent_learning.pmbok import lint_plan
from agent_learning.pmbok.scope import check_scope_sections
from tests.test_plan_content import H1, H2, H3, codes, make_body
from tests.test_scope_measure import SCOPE_FM, scope_doc, section1_four_items, section1_two_real


def s2(text: str) -> str:
    return f"{H2}\n\n{text}\n\n{H3}\n\nGovernance.\n"


class TestScopeSection2BothRoutes:
    """AC_0"""

    def test_missing_wbs_and_dod(self):
        doc = scope_doc(
            make_body(750, section1=section1_four_items(), h2=H2 + "\n\nGeneral mechanics without required keywords.\n", h3=H3),
            "full_plan",
        )
        msgs = [f.message for f in lint_plan(doc).flags if f.code == "MISSING_REQUIRED_SECTION"]
        assert any("WBS rules are missing" in m for m in msgs)
        assert any("Definition of Done is missing" in m for m in msgs)

    def test_wbs_and_dod_present_no_those_findings(self):
        s2text = (
            "Work breakdown structure lists phase, epic, story, and commit on each work package.\n"
            "Definition of Done requires acceptance criteria, owner, and parent fields.\n"
        )
        doc = scope_doc(make_body(750, section1=section1_four_items(), h2=H2 + "\n\n" + s2text, h3=H3), "full_plan")
        msgs = [f.message for f in lint_plan(doc).flags if f.code == "MISSING_REQUIRED_SECTION"]
        assert not any("WBS rules are missing" in m for m in msgs)
        assert not any("Definition of Done is missing" in m for m in msgs)


class TestEmbeddedHierarchy:
    """AC_1"""

    def test_one_term_fails_hierarchy(self):
        s2text = "Work breakdown structure mentions epic only.\nDefinition of Done applies.\n"
        doc = scope_doc(make_body(750, section1=section1_two_real(), h2=H2 + "\n\n" + s2text, h3=H3), "pmp_section")
        assert any(f.message == "WBS hierarchy is missing" for f in lint_plan(doc).flags)

    def test_two_terms_pass(self):
        s2text = "WBS covers phase and epic layers.\nDefinition of Done is documented.\n"
        doc = scope_doc(make_body(750, section1=section1_two_real(), h2=H2 + "\n\n" + s2text, h3=H3), "pmp_section")
        assert not any(f.message == "WBS hierarchy is missing" for f in lint_plan(doc).flags)

    def test_arrow_link_passes_with_one_term(self):
        s2text = "Work breakdown structure: phase → story.\nDefinition of Done listed.\n"
        doc = scope_doc(make_body(750, section1=section1_two_real(), h2=H2 + "\n\n" + s2text, h3=H3), "pmp_section")
        assert not any(f.message == "WBS hierarchy is missing" for f in lint_plan(doc).flags)

    def test_stray_arrow_does_not_satisfy_hierarchy(self):
        s2text = "Work breakdown structure: epic only. Review -> approve.\nDefinition of Done listed.\n"
        doc = scope_doc(make_body(750, section1=section1_two_real(), h2=H2 + "\n\n" + s2text, h3=H3), "pmp_section")
        assert any(f.message == "WBS hierarchy is missing" for f in lint_plan(doc).flags)

    def test_work_package_counts_without_commit_word(self):
        s2text = "WBS covers phase and work package layers.\nDefinition of Done is documented.\n"
        doc = scope_doc(make_body(750, section1=section1_two_real(), h2=H2 + "\n\n" + s2text, h3=H3), "pmp_section")
        assert not any(f.message == "WBS hierarchy is missing" for f in lint_plan(doc).flags)


class TestFullPlanDictionary:
    """AC_2"""

    def test_missing_hierarchy_labels(self):
        s2text = "WBS dictionary with epic and story only.\nDefinition of Done with acceptance criteria, owner, parent.\n"
        doc = scope_doc(make_body(750, section1=section1_four_items(), h2=H2 + "\n\n" + s2text, h3=H3), "full_plan")
        assert any("hierarchy is incomplete" in f.message and "phase" in f.message for f in lint_plan(doc).flags)

    def test_user_story_counts_as_story(self):
        s2text = (
            "Work breakdown structure: phase, epic, user story, work package.\n"
            "Definition of Done: acceptance criteria, owner, parent.\n"
        )
        doc = scope_doc(make_body(750, section1=section1_four_items(), h2=H2 + "\n\n" + s2text, h3=H3), "full_plan")
        assert not any("hierarchy is incomplete" in f.message for f in lint_plan(doc).flags)

    def test_missing_dictionary_fields(self):
        s2text = (
            "WBS with phase, epic, story, commit.\n"
            "Definition of Done mentions acceptance criteria only.\n"
        )
        doc = scope_doc(make_body(750, section1=section1_four_items(), h2=H2 + "\n\n" + s2text, h3=H3), "full_plan")
        assert any("fields are incomplete" in f.message for f in lint_plan(doc).flags)


class TestNoDoubleFinding:
    """AC_3"""

    def test_no_section2_heading_skips_scope_section_checks(self):
        body = make_body(750, section1=section1_four_items(), h2=None)
        assert check_scope_sections(body, "full_plan") == []
        doc = scope_doc(body, "full_plan")
        assert any("Section 2. Domain Mechanics & Standards is missing" in f.message for f in lint_plan(doc).flags)

    def test_non_scope_plan_no_section2_scope_findings(self):
        sched = scope_doc(make_body(800, section1=section1_four_items()), "full_plan").replace(
            "scope-management", "schedule-management"
        )
        sched = sched.replace("Scope Management Plan", "Schedule Management Plan")
        sched = sched.replace('primary_pmbok_domain: "Scope"', 'primary_pmbok_domain: "Schedule"')
        sched = sched.replace("5.1 Plan Scope Management", "6.1 Plan Schedule Management")
        sched = sched.replace('depends_on: []', 'depends_on: [scope-management]')
        assert not any("WBS rules are missing" in f.message for f in lint_plan(sched).flags)


class TestLintPlanOrder:
    """AC_4"""

    def test_heading_before_floor_before_section2(self):
        doc = scope_doc(
            make_body(
                100,
                section1=section1_two_real(),
                h1=None,
                h2=H2 + "\n\nEmpty section two.\n",
                h3=H3,
            ),
            "pmp_section",
        )
        ordered = [f.code if f.code != "MISSING_REQUIRED_SECTION" else f.message for f in lint_plan(doc).flags]
        # Find indices
        heading_idx = next(
            i for i, x in enumerate(ordered) if "Section 1" in str(x) or "Section 3" in str(x)
        )
        floor_idx = next(i for i, x in enumerate(ordered) if x == "BELOW_STANDARD_FLOOR")
        wbs_idx = next(i for i, x in enumerate(ordered) if x == "WBS rules are missing")
        assert heading_idx < floor_idx < wbs_idx
