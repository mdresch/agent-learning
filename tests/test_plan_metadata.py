"""Contract tests for Story 12.2: metadata validation and the nine-plan standards.

Story: docs/user-stories/epic-12-subsidiary-management-plan-standards-and-content-contracts.md (Story 12.2)
ADR:   ADR-012 sections 4.2 and 4.4 (daughter ADR-025 to ADR-033 frontmatter examples)
BRD:   BRD-012 (BRU-012-03)
FDD:   FDD-012 sections 2.1 and 3.2

Interpretations not stated verbatim in the acceptance criteria (LL-011), recorded here and in the log:
  I1  "Empty" means an empty or whitespace-only string, or an empty tuple.
  I2  A list key (depends_on, inputs, outputs, secondary_pmbok_domains) given a string, or a scalar key given a
      tuple, is a finding that names the key.
  I3  No cascade: a key that is missing, empty or of the wrong shape is reported once; later checks that depend
      on it (policy, table, route agreement) are skipped.
  I4  The route-agreement check is skipped when the frontmatter route is outside the closed list; the closed-list
      finding already covers it.
  I5  An empty mapping gives one finding whose message says "no metadata"; a non-mapping raises TypeError.
  I6  A finding names the key and shows the offending value (repr); its ``line`` is None (the input is a mapping).
  I7  A tailoring route is matched to a plan by ``plan_id`` equal to the legacy number at the start of
      ``legacy_process`` ("5.1"); routes are read by attribute (plan_id, route), so no import is needed.
  I8  Secondary domains are compared to the table as sets; their order does not matter.
  I9  The example in a daughter ADR is the first fenced ``yaml`` block whose first line is ``---`` (ADR 4.1).
  I10 The table row type is a frozen dataclass ``PlanStandard(primary, secondary, legacy, plan_tier)``.
  I11 The legacy number is the text of ``legacy_process`` before the first space.
"""

from __future__ import annotations

import dataclasses
import re
from pathlib import Path

import pytest

from agent_learning.pmbok.lint import validate_metadata
from agent_learning.pmbok.parser import parse_frontmatter
from agent_learning.pmbok.standards import (
    DOMAINS,
    GENERATORS,
    PLAN_STANDARDS,
    REQUIRED_KEYS,
    ROUTES,
    LintFlag,
    PlanStandard,
)
from agent_learning.tailoring import PlanRoute

REPO = Path(__file__).resolve().parents[1]
ADR_DIR = REPO / "docs" / "adr"

# A plan that is not one of the nine, so closed-list checks are not mixed with table checks.
BASE = {
    "plan_id": "custom-plan",
    "plan_name": "Custom Plan",
    "pmbok_edition": "PMBOK 8",
    "pmbok_focus_area": "Planning",
    "primary_pmbok_domain": "Scope",
    "secondary_pmbok_domains": ("Governance",),
    "legacy_process": "99.1 Plan Custom",
    "route": "full_plan",
    "generator": "llm",
    "version": "1.0.0",
    "baseline_id": "<target-baseline-id>",
    "owner_role": "Project Manager",
    "depends_on": (),
    "inputs": ("Project-Charter.md",),
    "outputs": ("docs/project-docs/management-plans/Custom-Plan.md",),
    "governance_policy": "approve-subsidiary-plan",
}

LIST_KEYS = ("depends_on", "inputs", "outputs", "secondary_pmbok_domains")
SCALAR_KEYS = tuple(k for k in REQUIRED_KEYS if k not in LIST_KEYS)


def meta(**changes):
    out = dict(BASE)
    for key, value in changes.items():
        if value is MISSING:
            out.pop(key, None)
        else:
            out[key] = value
    return out


MISSING = object()


def table_meta(plan_id: str, **changes):
    row = PLAN_STANDARDS[plan_id]
    fields = {
        "plan_id": plan_id,
        "primary_pmbok_domain": row.primary,
        "secondary_pmbok_domains": tuple(row.secondary),
        "legacy_process": f"{row.legacy} Plan Something",
    }
    fields.update(changes)
    return meta(**fields)


def one(findings: list[LintFlag], key: str, value: object | None = None) -> LintFlag:
    assert len(findings) == 1, findings
    flag = findings[0]
    assert flag.code == "INVALID_METADATA" and flag.tier == "B"
    assert flag.line is None
    assert key in flag.message, flag.message
    if value is not None:
        assert str(value) in flag.message, flag.message
    return flag


def adr_example(adr_number: int) -> str:
    matches = sorted(ADR_DIR.glob(f"ADR-{adr_number:03d}-*.md"))
    assert matches, f"ADR-{adr_number:03d} is missing from {ADR_DIR}"
    text = matches[0].read_text(encoding="utf-8")
    for block in re.finditer(r"```yaml\n(.*?)```", text, re.DOTALL):
        if block.group(1).startswith("---\n"):
            return block.group(1)
    raise AssertionError(f"ADR-{adr_number:03d} has no fenced yaml block that starts with ---")


class TestRequiredFields:
    """AC_0"""

    def test_a_complete_mapping_has_no_findings(self):
        assert validate_metadata(meta()) == []

    @pytest.mark.parametrize("key", REQUIRED_KEYS)
    def test_each_missing_required_key_is_one_finding(self, key):
        one(validate_metadata(meta(**{key: MISSING})), key)

    @pytest.mark.parametrize("key", SCALAR_KEYS)
    @pytest.mark.parametrize("empty", ["", "   "])
    def test_each_empty_scalar_is_one_finding(self, key, empty):  # I1
        one(validate_metadata(meta(**{key: empty})), key)

    @pytest.mark.parametrize("key", ["inputs", "outputs"])
    def test_inputs_and_outputs_may_not_be_empty(self, key):
        one(validate_metadata(meta(**{key: ()})), key)

    def test_depends_on_may_be_empty(self):
        assert validate_metadata(meta(depends_on=())) == []

    def test_secondary_domains_may_be_absent_or_empty(self):
        assert validate_metadata(meta(secondary_pmbok_domains=MISSING)) == []
        assert validate_metadata(meta(secondary_pmbok_domains=())) == []

    def test_empty_mapping_is_a_single_no_metadata_finding(self):  # I5
        findings = validate_metadata({})
        assert len(findings) == 1
        assert findings[0].code == "INVALID_METADATA" and findings[0].tier == "B"
        assert "no metadata" in findings[0].message.lower()

    @pytest.mark.parametrize("key", LIST_KEYS)
    def test_a_string_in_a_list_key_is_a_finding(self, key):  # I2
        one(validate_metadata(meta(**{key: "Governance"})), key)

    @pytest.mark.parametrize("key", SCALAR_KEYS)
    def test_a_tuple_in_a_scalar_key_is_a_finding(self, key):  # I2
        one(validate_metadata(meta(**{key: ("x",)})), key)

    @pytest.mark.parametrize("bad", [None, "---", ["a"], 3])
    def test_a_non_mapping_raises_type_error(self, bad):  # I5
        with pytest.raises(TypeError):
            validate_metadata(bad)  # type: ignore[arg-type]

    def test_findings_follow_the_order_of_the_required_keys(self):  # stable order
        findings = validate_metadata(meta(owner_role=MISSING, plan_name=MISSING, version=MISSING))
        keys = [next(k for k in REQUIRED_KEYS if k in f.message) for f in findings]
        assert keys == [k for k in REQUIRED_KEYS if k in ("plan_name", "version", "owner_role")]

    def test_the_result_does_not_change_the_input(self):
        original = meta(owner_role=MISSING)
        before = dict(original)
        validate_metadata(original)
        assert original == before


class TestClosedListsAndFormats:
    """AC_1"""

    @pytest.mark.parametrize("domain", ["Finances", "scope", "Quality", "Governance, Scope", "PMBOK"])
    def test_primary_domain_outside_the_seven(self, domain):
        one(validate_metadata(meta(primary_pmbok_domain=domain)), "primary_pmbok_domain", domain)

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_every_domain_is_accepted_as_primary(self, domain):
        assert validate_metadata(meta(primary_pmbok_domain=domain)) == []

    def test_secondary_domain_outside_the_seven(self):
        one(validate_metadata(meta(secondary_pmbok_domains=("Governance", "Money"))), "secondary_pmbok_domains", "Money")

    def test_each_bad_secondary_domain_gets_its_own_finding(self):
        assert len(validate_metadata(meta(secondary_pmbok_domains=("Money", "Time")))) == 2

    @pytest.mark.parametrize("route", ["weekly", "Full_Plan", "full-plan", "none"])
    def test_route_outside_its_list(self, route):
        one(validate_metadata(meta(route=route)), "route", route)

    @pytest.mark.parametrize("generator", ["bot", "LLM", "ai", "none"])
    def test_generator_outside_its_list(self, generator):
        one(validate_metadata(meta(generator=generator)), "generator", generator)

    @pytest.mark.parametrize("edition", ["PMBOK 7", "PMBOK8", "pmbok 8", "8"])
    def test_pmbok_edition_must_be_pmbok_8(self, edition):
        one(validate_metadata(meta(pmbok_edition=edition)), "pmbok_edition", edition)

    @pytest.mark.parametrize("area", ["Execution", "planning", "Plan"])
    def test_focus_area_must_be_planning(self, area):
        one(validate_metadata(meta(pmbok_focus_area=area)), "pmbok_focus_area", area)

    @pytest.mark.parametrize("version", ["1.0", "v1.0.0", "1.0.0-rc1", "1.0.0.0", "a.b.c", "1,0,0"])
    def test_malformed_version(self, version):
        one(validate_metadata(meta(version=version)), "version", version)

    @pytest.mark.parametrize("legacy", ["5.1", "5 Plan", "x.y Plan", "5.1Plan", " 5.1 Plan"])
    def test_malformed_legacy_process(self, legacy):
        one(validate_metadata(meta(legacy_process=legacy)), "legacy_process", legacy)

    @pytest.mark.parametrize("plan_id", ["Scope", "scope_management", "-scope", "1scope", "scope management", "scope!"])
    def test_malformed_plan_id(self, plan_id):
        one(validate_metadata(meta(plan_id=plan_id)), "plan_id", plan_id)

    @pytest.mark.parametrize("item", ["Bad Id", "UPPER", "a_b", "-x"])
    def test_malformed_depends_on_item(self, item):
        one(validate_metadata(meta(depends_on=("scope-management", item))), "depends_on", item)

    def test_a_valid_depends_on_list(self):
        assert validate_metadata(meta(depends_on=("scope-management", "schedule-management"))) == []

    def test_several_problems_give_several_findings_in_the_documented_order(self):
        findings = validate_metadata(meta(plan_id="Bad", version="x", primary_pmbok_domain="Nope", route="weekly", generator="bot"))
        keys = [next(k for k in ("plan_id", "version", "primary_pmbok_domain", "route", "generator") if k in f.message) for f in findings]
        assert keys == ["plan_id", "version", "primary_pmbok_domain", "route", "generator"]

    def test_the_closed_lists_are_the_adr_lists(self):
        assert DOMAINS == ("Governance", "Scope", "Schedule", "Finance", "Stakeholders", "Resources", "Risk")
        assert ROUTES == ("full_plan", "pmp_section", "not_applicable")
        assert GENERATORS == ("llm", "human", "stub", "mock")
        assert "secondary_pmbok_domains" not in REQUIRED_KEYS and len(REQUIRED_KEYS) == 15

    def test_no_cascade_when_a_dependent_key_is_invalid(self):  # I3
        findings = validate_metadata(meta(route="weekly", governance_policy="anything"))
        one(findings, "route", "weekly")


class TestGovernancePolicy:
    """AC_2"""

    def test_full_plan_needs_the_subsidiary_plan_gate(self):
        assert validate_metadata(meta(route="full_plan", governance_policy="approve-subsidiary-plan")) == []
        one(validate_metadata(meta(route="full_plan", governance_policy="approve-pmp")), "governance_policy", "approve-pmp")

    def test_pmp_section_needs_the_pmp_gate(self):
        assert validate_metadata(meta(route="pmp_section", governance_policy="approve-pmp")) == []
        one(
            validate_metadata(meta(route="pmp_section", governance_policy="approve-subsidiary-plan")),
            "governance_policy",
            "approve-subsidiary-plan",
        )

    @pytest.mark.parametrize("policy", ["approve-subsidiary-plan", "approve-pmp", "none", "banana"])
    def test_not_applicable_accepts_any_value(self, policy):
        assert validate_metadata(meta(route="not_applicable", governance_policy=policy)) == []

    def test_an_unknown_policy_name_is_a_finding_for_a_routed_plan(self):
        one(validate_metadata(meta(route="full_plan", governance_policy="approve")), "governance_policy", "approve")


class TestPlanStandards:
    """AC_3"""

    def adr_rows(self):
        text = next(ADR_DIR.glob("ADR-012-*.md")).read_text(encoding="utf-8")
        start = text.index("Primary Performance Domain")
        rows = {}
        for line in text[start : text.index("```", start)].splitlines()[2:]:
            parts = re.split(r"\s{2,}", line.strip())
            if len(parts) != 5:
                continue
            primary, secondary, legacy, name, tier = parts
            plan_id = re.sub(r"\s+", "-", name.lower().replace(" plan", "").strip())
            rows[plan_id] = (primary, tuple(s.strip() for s in secondary.split(",")), legacy, int(re.search(r"\d", tier).group()))
        return rows

    def test_the_table_equals_the_adr_012_table(self):
        rows = self.adr_rows()
        assert len(rows) == 9
        assert {k: (v.primary, v.secondary, v.legacy, v.plan_tier) for k, v in PLAN_STANDARDS.items()} == rows

    def test_the_nine_plans(self):
        assert set(PLAN_STANDARDS) == {
            "scope-management", "schedule-management", "cost-management", "quality-management", "resource-management",
            "communications-management", "risk-management", "procurement-management", "stakeholder-engagement",
        }

    def test_rows_use_the_closed_domain_list(self):  # I10
        for row in PLAN_STANDARDS.values():
            assert isinstance(row, PlanStandard)
            assert row.primary in DOMAINS and set(row.secondary) <= set(DOMAINS)
            assert row.plan_tier in (1, 2, 3)

    def test_plan_tiers_are_plan_tiers(self):
        tiers = {k: v.plan_tier for k, v in PLAN_STANDARDS.items()}
        assert [k for k, t in tiers.items() if t == 1] == ["scope-management", "schedule-management", "cost-management"]
        assert tiers["quality-management"] == 2 and tiers["risk-management"] == 2

    def test_rows_are_frozen(self):
        with pytest.raises(dataclasses.FrozenInstanceError):
            PLAN_STANDARDS["scope-management"].primary = "Risk"  # type: ignore[misc]

    @pytest.mark.parametrize("plan_id", sorted(PLAN_STANDARDS))
    def test_a_plan_that_follows_its_row_has_no_findings(self, plan_id):
        assert validate_metadata(table_meta(plan_id)) == []

    def test_a_different_primary_domain_is_a_finding(self):
        one(validate_metadata(table_meta("scope-management", primary_pmbok_domain="Risk")), "primary_pmbok_domain", "Risk")

    def test_a_different_secondary_set_is_a_finding(self):
        one(
            validate_metadata(table_meta("scope-management", secondary_pmbok_domains=("Governance", "Finance"))),
            "secondary_pmbok_domains",
        )
        one(validate_metadata(table_meta("scope-management", secondary_pmbok_domains=())), "secondary_pmbok_domains")

    def test_secondary_order_does_not_matter(self):  # I8
        assert validate_metadata(table_meta("risk-management", secondary_pmbok_domains=("Finance", "Governance"))) == []

    def test_a_different_legacy_number_is_a_finding(self):
        one(validate_metadata(table_meta("scope-management", legacy_process="6.1 Plan Scope Management")), "legacy_process", "6.1")

    def test_the_text_after_the_legacy_number_is_free(self):  # I11
        assert validate_metadata(table_meta("scope-management", legacy_process="5.1 Anything Goes Here")) == []

    def test_an_unknown_plan_is_checked_only_against_the_closed_lists(self):
        assert validate_metadata(meta(plan_id="my-own-plan", primary_pmbok_domain="Risk", legacy_process="1.1 Mine")) == []


class TestRouteAgreement:
    """AC_4"""

    def routes(self, **by_number):
        return [PlanRoute(plan_id=number, route=route) for number, route in by_number.items()]

    def scope(self, **changes):
        return table_meta("scope-management", **changes)

    def test_a_different_route_is_a_finding(self):  # I7
        routes = [PlanRoute(plan_id="5.1", route="pmp_section")]
        findings = validate_metadata(self.scope(), routes)
        flag = one(findings, "route", "pmp_section")
        assert "full_plan" in flag.message

    def test_the_same_route_is_not(self):
        routes = [PlanRoute(plan_id="5.1", route="full_plan")]
        assert validate_metadata(self.scope(), routes) == []

    def test_a_plan_absent_from_the_records_is_not_a_finding(self):
        routes = [PlanRoute(plan_id="6.1", route="pmp_section")]
        assert validate_metadata(self.scope(), routes) == []
        assert validate_metadata(self.scope(), []) == []
        assert validate_metadata(self.scope(), None) == []

    def test_a_pending_recommendation_counts_as_the_recorded_route(self):
        routes = [PlanRoute(plan_id="5.1", route="not_applicable", decided=False)]
        one(validate_metadata(self.scope(route="full_plan"), routes), "route", "not_applicable")

    def test_the_plan_is_found_by_its_legacy_number(self):
        routes = [PlanRoute(plan_id="5.1", route="pmp_section"), PlanRoute(plan_id="6.1", route="full_plan")]
        findings = validate_metadata(meta(legacy_process="6.1 Plan X", route="full_plan"), routes)
        assert findings == []

    def test_an_invalid_frontmatter_route_gives_only_the_closed_list_finding(self):  # I4
        routes = [PlanRoute(plan_id="5.1", route="full_plan")]
        one(validate_metadata(self.scope(route="weekly"), routes), "route", "weekly")

    def test_a_malformed_legacy_process_skips_the_agreement_check(self):  # I3
        routes = [PlanRoute(plan_id="5.1", route="pmp_section")]
        one(validate_metadata(self.scope(legacy_process="five"), routes), "legacy_process")

    def test_not_applicable_in_both_agrees(self):
        routes = [PlanRoute(plan_id="5.1", route="not_applicable")]
        assert validate_metadata(self.scope(route="not_applicable", governance_policy="none"), routes) == []


class TestConformance:
    """AC_5"""

    ADRS = range(25, 34)

    @pytest.mark.parametrize("number", ADRS)
    def test_each_daughter_adr_example_parses_and_validates(self, number):  # I9
        parsed = parse_frontmatter(adr_example(number))
        assert parsed.parsed, parsed.flags
        assert validate_metadata(parsed.metadata) == []

    def test_the_examples_cover_the_nine_plans_exactly(self):
        ids = {parse_frontmatter(adr_example(n)).metadata["plan_id"] for n in self.ADRS}
        assert ids == set(PLAN_STANDARDS)

    def test_the_example_matches_its_table_row(self):
        for number in self.ADRS:
            m = parse_frontmatter(adr_example(number)).metadata
            row = PLAN_STANDARDS[m["plan_id"]]
            assert m["primary_pmbok_domain"] == row.primary
            assert set(m["secondary_pmbok_domains"]) == set(row.secondary)
            assert m["legacy_process"].split(" ")[0] == row.legacy

    def test_a_missing_example_fails_the_test(self):
        with pytest.raises(AssertionError):
            adr_example(999)


class TestExtraKeys:
    """AC_6"""

    def test_unknown_keys_are_accepted(self):
        assert validate_metadata(meta(cycle_id="CYC-1", x_note="anything")) == []

    def test_extra_keys_do_not_hide_a_real_finding(self):
        one(validate_metadata(meta(cycle_id="CYC-1", route="weekly")), "route", "weekly")

    def test_validation_is_deterministic(self):
        bad = meta(version="x", owner_role=MISSING)
        assert validate_metadata(bad) == validate_metadata(bad)
