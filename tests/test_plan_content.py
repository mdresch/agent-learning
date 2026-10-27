"""Contract tests for Story 12.3: the content contract (headings, length and boundaries) and lint_plan.

Story: docs/user-stories/epic-12-subsidiary-management-plan-standards-and-content-contracts.md (Story 12.3)
ADR:   ADR-012 sections 4.3.1 to 4.3.3 and 4.4 (Plan Tier 1 omission)
BRD:   BRD-012 (BRU-012-04, BRU-012-05)
FDD:   FDD-012 sections 3.3 to 3.6

Interpretations not stated verbatim in the acceptance criteria (LL-011), recorded here and in the log:
  I1  A fence is a line that, after leading whitespace, starts with three backticks; fences toggle and an unclosed
      fence runs to the end. Only backtick fences count; ``~~~`` is ordinary text.
  I2  Fenced code is removed first, then HTML comments; an unclosed comment runs to the end of the text.
  I3  Headings and Section 1 are read from the text with fences and comments removed, so a heading or a
      boundary declaration inside code or a comment does not count.
  I4  ``check_content`` raises ValueError for a route outside the closed list and TypeError for a non-str body
      (call errors, not content); the options ``min_floor_words`` and ``min_out_of_scope_items`` must be int or
      None (bool is rejected) and a value below the baseline is ignored.
  I5  Section 1 runs from the end of its heading to the start of the Section 2 heading found after it, or to the
      end of the text.
  I6  After an out-of-scope marker line, scanning skips blank and prose lines until the first bullet, stops at a
      heading, and after the first bullet stops at a non-blank non-bullet line; bullets are distinct by their
      lower-cased text.
  I7  A qualifying ``None:`` line or a qualifying marker passes; otherwise there is exactly one finding and its
      message names the reason (rationale too short, too few items, or no declaration).
  I8  The marker is "out-of-scope" or "out of scope", matched case-insensitively anywhere in a line.
  I9  ``omission_flags`` keeps the tailoring order; the finding takes its message and evidence from the
      tailoring flag and has no line.
  I10 ``lint_plan`` gives ``word_count=None`` when parsing fails, when the route is not a valid string and when it
      is not_applicable; a content finding has no line.
  I11 A count equal to the floor or the cap is not a finding.
  I12 The ADR tokenizer counts nothing for a word that touches an underscore ("snake_case", "plan_id" give zero
      tokens), because the underscore is a word character for \b. The test pins this; it is reported to the
      maintainer, not changed here.
"""

from __future__ import annotations

import random
import re
from pathlib import Path

import pytest

from agent_learning.pmbok.lint import (
    LintResult,
    check_content,
    count_words,
    lint_plan,
    omission_flags,
)
from agent_learning.pmbok.parser import parse_frontmatter
from agent_learning.pmbok.standards import CAPS, FLOORS, HEADINGS, NONE_MIN_TOKENS, TOKEN
from agent_learning.tailoring import PLAN_IDS, PlanRoute

REPO = Path(__file__).resolve().parents[1]

H1 = "## 1. Intent, Alignment & Boundaries"
H2 = "## 2. Domain Mechanics & Standards"
H3 = "## 3. Governance, Control & Decision Rights"
DECL = "Out-of-scope boundaries:\n- Item one is excluded.\n"  # 8 + 0 tokens
NONE_OK = "None: " + " ".join(["reason"] * 10)


def words(n: int) -> str:
    return " ".join(["word"] * n)


def make_body(total: int | None = None, *, section1: str = DECL, h1: str | None = H1, h2: str | None = H2, h3: str | None = H3) -> str:
    """A body with the three headings and, when ``total`` is given, exactly that many words."""

    def build(pad: str) -> str:
        parts = [p for p in (h1, section1, h2, pad, h3, "Governance text.") if p]
        return "\n\n".join(parts) + "\n"

    base = count_words(build(""))
    if total is None:
        return build("")
    assert total >= base, (total, base)
    return build(words(total - base))


def codes(flags) -> list[str]:
    return [f.code for f in flags]


def adr_frontmatter() -> str:
    matches = sorted((REPO / "docs" / "adr").glob("ADR-025-*.md"))
    assert matches, "ADR-025 is missing from docs/adr; the frontmatter example cannot be read"
    adr = matches[0].read_text(encoding="utf-8")
    for block in re.finditer(r"```yaml\n(.*?)```", adr, re.DOTALL):
        if block.group(1).startswith("---\n"):
            return block.group(1)
    raise AssertionError("ADR-025 has no frontmatter example")


class TestWordCount:
    """AC_0"""

    def test_contraction_is_one_word_and_hyphenated_is_two(self):
        assert count_words("don't") == 1
        assert count_words("it’s") == 1
        assert count_words("well-known") == 2

    def test_markdown_punctuation_is_not_a_word(self):
        assert count_words("##\n---\n|\n-\n| a | b |\n- item") == 3

    def test_a_word_touching_an_underscore_is_not_counted_and_digits_count(self):  # I12
        # The ADR regex puts \b around [^\W_]+, and an underscore is a word character, so "snake_case" gives no
        # token at all (not two). Pinned as the normative behavior; changing it is an ADR amendment.
        assert count_words("snake_case") == 0
        assert count_words("plan_id is here") == 2
        assert count_words("2026") == 1

    def test_unicode_letters(self):
        assert count_words("café Überprüfung") == 2

    def test_empty_and_blank_bodies(self):
        assert count_words("") == 0
        assert count_words("  \n\t\n") == 0

    def test_html_comments_are_ignored_including_multi_line(self):
        assert count_words("one <!-- two --> three") == 2
        assert count_words("one <!--\ntwo\nthree\n--> four") == 2

    def test_an_unclosed_comment_runs_to_the_end(self):  # I2
        assert count_words("one two <!-- three four") == 2

    def test_fenced_code_is_ignored(self):
        assert count_words("one\n```\ntwo three\n```\nfour") == 2
        assert count_words("one\n  ```python\ntwo\n  ```\nthree") == 2

    def test_an_unclosed_fence_runs_to_the_end(self):  # I1
        assert count_words("one\n```\ntwo three\nfour") == 1

    def test_only_backtick_fences_count(self):  # I1
        assert count_words("one\n~~~\ntwo\n~~~\nthree") == 3

    def test_fences_are_removed_before_comments(self):  # I2
        assert count_words("```\n<!-- x\n```\nafter words") == 2

    def test_a_fixed_text_returns_a_known_count(self):
        text = (
            "# Title here\n\nIt's a well-known plan: 3 steps.\n\n"
            "<!-- hidden words -->\n```\ncode words\n```\n"
            "| col | col |\n|---|---|\n| a | b |\n"
        )
        # Title here (2) It's a well known plan 3 steps (7) col col a b (4)
        assert count_words(text) == 13

    def test_the_regex_is_the_adr_regex(self):
        assert TOKEN.pattern == r"\b[^\W_]+(?:['’][^\W_]+)?\b"

    def test_non_str_raises_type_error(self):
        for bad in (None, 3, b"x", ["a"]):
            with pytest.raises(TypeError):
                count_words(bad)  # type: ignore[arg-type]

    def test_deterministic(self):
        text = make_body(321)
        assert count_words(text) == count_words(text) == 321


class TestHeadings:
    """AC_1"""

    def test_all_three_present_gives_no_finding(self):
        assert [f for f in check_content(make_body(700), "full_plan") if f.code == "MISSING_REQUIRED_SECTION"] == []

    @pytest.mark.parametrize("which", [1, 2, 3])
    def test_each_missing_heading_is_one_tier_b_finding(self, which):
        body = make_body(700, **{f"h{which}": None})
        found = [f for f in check_content(body, "full_plan") if f.code == "MISSING_REQUIRED_SECTION"]
        assert len(found) == 1
        assert found[0].tier == "B"
        assert str(which) in found[0].message

    def test_all_missing_gives_three_in_section_order(self):
        body = "no headings here at all " * 200
        found = [f for f in check_content(body, "full_plan") if f.code == "MISSING_REQUIRED_SECTION"]
        assert len(found) == 3
        assert [re.search(r"\d", f.message).group() for f in found] == ["1", "2", "3"]

    def test_heading_order_is_not_checked(self):
        body = "\n\n".join([H3, H1, DECL, H2, words(600)])
        assert [f for f in check_content(body, "full_plan") if f.code == "MISSING_REQUIRED_SECTION"] == []

    def test_wrong_level_or_case_does_not_match(self):
        assert HEADINGS  # three compiled patterns
        for bad in ("### 1. Intent, Alignment & Boundaries", "## 1. intent, alignment & boundaries", "# 1. Intent, Alignment & Boundaries"):
            body = make_body(700, h1=bad)
            assert "MISSING_REQUIRED_SECTION" in codes(check_content(body, "full_plan")), bad

    def test_extra_whitespace_and_a_suffix_still_match(self):
        body = make_body(700, h1="##   1.  Intent,   Alignment  &  Boundaries (draft)")
        assert "MISSING_REQUIRED_SECTION" not in codes(check_content(body, "full_plan"))

    def test_a_heading_inside_code_or_a_comment_does_not_count(self):  # I3
        fenced = make_body(700, h2="```\n" + H2 + "\n```")
        commented = make_body(700, h3="<!-- " + H3 + " -->")
        assert "MISSING_REQUIRED_SECTION" in codes(check_content(fenced, "full_plan"))
        assert "MISSING_REQUIRED_SECTION" in codes(check_content(commented, "full_plan"))

    def test_the_patterns_are_the_adr_patterns(self):
        assert [p.pattern for p in HEADINGS] == [
            r"^##\s+1\.\s+Intent,\s+Alignment\s+&\s+Boundaries",
            r"^##\s+2\.\s+Domain\s+Mechanics\s+&\s+Standards",
            r"^##\s+3\.\s+Governance,\s+Control\s+&\s+Decision\s+Rights",
        ]
        assert all(p.flags & re.MULTILINE for p in HEADINGS)


class TestFloors:
    """AC_2"""

    @pytest.mark.parametrize("route, floor", [("pmp_section", 150), ("full_plan", 600)])
    def test_below_the_floor_is_a_tier_c_flag(self, route, floor):
        assert FLOORS[route] == floor
        found = [f for f in check_content(make_body(floor - 1), route) if f.code == "BELOW_STANDARD_FLOOR"]
        assert len(found) == 1 and found[0].tier == "C"
        assert str(floor - 1) in found[0].message and str(floor) in found[0].message

    @pytest.mark.parametrize("route, floor", [("pmp_section", 150), ("full_plan", 600)])
    def test_equal_to_the_floor_is_not_a_finding(self, route, floor):  # I11
        assert "BELOW_STANDARD_FLOOR" not in codes(check_content(make_body(floor), route))
        assert "BELOW_STANDARD_FLOOR" not in codes(check_content(make_body(floor + 1), route))

    def test_a_project_standard_can_raise_the_floor(self):
        assert "BELOW_STANDARD_FLOOR" in codes(check_content(make_body(700), "full_plan", min_floor_words=1000))
        assert "BELOW_STANDARD_FLOOR" not in codes(check_content(make_body(1000), "full_plan", min_floor_words=1000))
        assert "BELOW_STANDARD_FLOOR" in codes(check_content(make_body(160), "pmp_section", min_floor_words=200))

    def test_a_lower_value_is_ignored(self):
        assert "BELOW_STANDARD_FLOOR" in codes(check_content(make_body(599), "full_plan", min_floor_words=10))
        assert "BELOW_STANDARD_FLOOR" in codes(check_content(make_body(599), "full_plan", min_floor_words=0))
        assert "BELOW_STANDARD_FLOOR" in codes(check_content(make_body(599), "full_plan", min_floor_words=-5))
        assert "BELOW_STANDARD_FLOOR" in codes(check_content(make_body(599), "full_plan", min_floor_words=None))

    @pytest.mark.parametrize("bad", [True, 1.5, "100"])
    def test_a_non_int_option_raises_type_error(self, bad):  # I4
        with pytest.raises(TypeError):
            check_content(make_body(700), "full_plan", min_floor_words=bad)  # type: ignore[arg-type]
        with pytest.raises(TypeError):
            check_content(make_body(700), "full_plan", min_out_of_scope_items=bad)  # type: ignore[arg-type]


class TestCaps:
    """AC_3"""

    def test_a_section_above_800_words(self):
        assert CAPS == {"pmp_section": 800, "full_plan": 5000}
        found = [f for f in check_content(make_body(801), "pmp_section") if f.code.startswith("EXCEEDS")]
        assert [f.code for f in found] == ["EXCEEDS_SECTION_CAP"] and found[0].tier == "C"

    def test_a_full_plan_above_5000_words(self):
        found = [f for f in check_content(make_body(5001), "full_plan") if f.code.startswith("EXCEEDS")]
        assert [f.code for f in found] == ["EXCEEDS_PLAN_CAP"] and found[0].tier == "C"

    def test_equal_to_the_cap_is_not_a_finding(self):  # I11
        assert not [f for f in check_content(make_body(800), "pmp_section") if f.code.startswith("EXCEEDS")]
        assert not [f for f in check_content(make_body(5000), "full_plan") if f.code.startswith("EXCEEDS")]

    def test_a_section_cap_does_not_apply_to_a_full_plan_and_the_reverse(self):
        assert not [f for f in check_content(make_body(801), "full_plan") if f.code.startswith("EXCEEDS")]
        assert "EXCEEDS_PLAN_CAP" not in codes(check_content(make_body(5001), "pmp_section"))

    def test_an_over_cap_text_has_no_floor_finding(self):
        assert "BELOW_STANDARD_FLOOR" not in codes(check_content(make_body(801), "pmp_section"))


class TestBoundaryDeclaration:
    """AC_4"""

    def boundary(self, section1, route="pmp_section", **options):
        body = make_body(300, section1=section1)
        return [f for f in check_content(body, route, **options) if f.code == "MISSING_BOUNDARY_DEF"]

    def test_none_with_ten_tokens_passes_and_nine_fails(self):
        assert NONE_MIN_TOKENS == 10
        assert self.boundary("None: " + words(10)) == []
        short = self.boundary("None: " + words(9))
        assert len(short) == 1 and short[0].tier == "C"
        assert "rationale" in short[0].message.lower()

    @pytest.mark.parametrize("prefix", ["", "- ", "* ", "  - ", "   "])
    def test_none_line_forms(self, prefix):
        assert self.boundary(prefix + NONE_OK) == []

    def test_the_rationale_is_counted_with_the_adr_tokenizer(self):
        assert self.boundary("None: " + "well-known " * 5) == []  # 5 hyphenated words = 10 tokens
        assert self.boundary("None: " + "well-known " * 4) != []

    def test_none_needs_a_colon_and_a_space_and_the_exact_case(self):
        assert self.boundary("None " + words(12)) != []
        assert self.boundary("none: " + words(12)) != []
        assert self.boundary("None:" + words(12)) != []

    @pytest.mark.parametrize("marker", ["Out-of-scope:", "out-of-scope items", "Out of scope:", "OUT OF SCOPE", "The out-of-scope list"])
    def test_marker_with_one_bullet_passes(self, marker):  # I8
        assert self.boundary(f"{marker}\n- one thing\n") == []

    def test_marker_with_star_bullets_and_a_blank_line(self):
        assert self.boundary("Out of scope:\n\n* one thing\n") == []

    def test_marker_without_bullets_fails(self):
        found = self.boundary("Out-of-scope: nothing listed here.\n")
        assert len(found) == 1 and "item" in found[0].message.lower()

    def test_no_declaration_fails_with_one_finding(self):
        found = self.boundary("This section only describes the intent of the plan in some detail.")
        assert len(found) == 1

    def test_duplicate_bullets_count_once(self):  # I6
        assert self.boundary("Out-of-scope:\n- Same\n- same\n", min_out_of_scope_items=2) != []
        assert self.boundary("Out-of-scope:\n- One\n- Two\n", min_out_of_scope_items=2) == []

    def test_the_minimum_can_be_raised_and_never_lowered(self):
        assert self.boundary("Out-of-scope:\n- One\n", min_out_of_scope_items=2) != []
        assert self.boundary("Out-of-scope:\n- One\n- Two\n- Three\n", min_out_of_scope_items=3) == []
        assert self.boundary("Out-of-scope: none listed\n", min_out_of_scope_items=0) != []

    def test_bullets_stop_at_prose_after_the_first_bullet(self):  # I6
        text = "Out-of-scope:\n- One\nSome prose.\n- Two\n"
        assert self.boundary(text, min_out_of_scope_items=2) != []
        assert self.boundary(text) == []

    def test_prose_before_the_first_bullet_is_skipped(self):  # I6
        assert self.boundary("Out-of-scope items follow.\nThe following are excluded:\n- One\n") == []

    def test_a_heading_ends_the_scan(self):  # I6
        assert self.boundary("Out-of-scope:\n### Details\n- One\n") != []

    def test_a_qualifying_none_line_beats_a_marker_without_bullets(self):  # I7
        assert self.boundary("Out-of-scope: see below.\n" + NONE_OK) == []

    def test_a_declaration_outside_section_1_does_not_count(self):
        body = make_body(300, section1="Only intent here.", h2=H2 + "\nOut-of-scope:\n- One\n")
        assert "MISSING_BOUNDARY_DEF" in codes(check_content(body, "pmp_section"))

    def test_a_declaration_in_code_or_a_comment_does_not_count(self):  # I3
        assert self.boundary("```\nOut-of-scope:\n- One\n```\n") != []
        assert self.boundary("<!-- Out-of-scope:\n- One -->") != []

    def test_a_missing_section_1_heading_gives_no_boundary_finding(self):
        body = make_body(300, h1=None, section1="Nothing declared.")
        found = check_content(body, "pmp_section")
        assert "MISSING_REQUIRED_SECTION" in codes(found) and "MISSING_BOUNDARY_DEF" not in codes(found)

    def test_section_1_ends_at_the_next_section_2_heading(self):  # I5
        body = f"{H1}\n\nIntro only.\n\n{H2}\n\nOut-of-scope:\n- One\n\n{H3}\n\nx"
        assert "MISSING_BOUNDARY_DEF" in codes(check_content(body + "\n" + words(300), "pmp_section"))

    def test_section_1_runs_to_the_end_when_section_2_is_missing(self):  # I5
        body = "\n\n".join([H1, "Out-of-scope:\n- One", words(300)])
        assert "MISSING_BOUNDARY_DEF" not in codes(check_content(body, "pmp_section"))


class TestRouteNotApplicable:
    """AC_5"""

    @pytest.mark.parametrize("body", ["", "nothing at all", make_body(700)])
    def test_check_content_returns_nothing(self, body):
        assert check_content(body, "not_applicable") == []

    def test_lint_plan_still_validates_the_metadata(self):
        text = adr_frontmatter().replace('route: "full_plan"', 'route: "not_applicable"').replace('version: "1.0.0"', 'version: "x"')
        result = lint_plan(text + "short body")
        assert result.plan.parsed
        assert [f.code for f in result.flags] == ["INVALID_METADATA"]
        assert "version" in result.flags[0].message
        assert result.word_count is None  # I10

    def test_an_unknown_route_argument_is_a_call_error(self):  # I4
        with pytest.raises(ValueError):
            check_content("x", "weekly")
        with pytest.raises(TypeError):
            check_content(None, "full_plan")  # type: ignore[arg-type]


class TestOmissionFlags:
    """AC_6"""

    def route(self, number, route):
        return PlanRoute(plan_id=number, route=route, reason="because")

    def test_each_baseline_plan_routed_not_applicable_is_a_tier_c_flag(self):
        routes = [self.route(n, "not_applicable") for n in ("5.1", "6.1", "7.1")]
        found = omission_flags(routes)
        assert [f.code for f in found] == ["OMISSION_OF_BASE_PLAN"] * 3
        assert all(f.tier == "C" and f.line is None for f in found)
        assert all(f.message and f.evidence for f in found)  # I9

    def test_no_other_plan_can_raise_it(self):
        others = [n for n in PLAN_IDS if n not in ("5.1", "6.1", "7.1")]
        assert len(others) == 6
        assert omission_flags([self.route(n, "not_applicable") for n in others]) == []

    def test_a_routed_baseline_plan_is_not_flagged(self):
        assert omission_flags([self.route("5.1", "full_plan"), self.route("6.1", "pmp_section")]) == []

    def test_empty_input(self):
        assert omission_flags([]) == []

    def test_the_order_follows_tailoring(self):  # I9
        routes = [self.route("7.1", "not_applicable"), self.route("5.1", "not_applicable")]
        assert [f.message.split(" ")[0] for f in omission_flags(routes)] == ["Scope", "Cost"]


class TestLintPlan:
    """AC_7"""

    def good_plan(self, n=700, **kw):
        return adr_frontmatter() + make_body(n, **kw)

    def test_a_conformant_plan_has_no_findings_and_a_count(self):
        result = lint_plan(self.good_plan(700))
        assert isinstance(result, LintResult)
        assert result.plan.parsed and result.flags == () and result.word_count == 700

    def test_order_is_parse_metadata_headings_floor_cap_boundary(self):
        text = adr_frontmatter().replace('version: "1.0.0"', 'version: "x"') + make_body(100, section1="Prose only.", h2=None)
        assert codes(lint_plan(text).flags) == ["INVALID_METADATA", "MISSING_REQUIRED_SECTION", "BELOW_STANDARD_FLOOR", "MISSING_BOUNDARY_DEF"]

    def test_cap_comes_between_floor_and_boundary(self):
        text = adr_frontmatter().replace('route: "full_plan"', 'route: "pmp_section"').replace(
            'governance_policy: "approve-subsidiary-plan"', 'governance_policy: "approve-pmp"'
        ) + make_body(900, section1="Prose only.")
        assert codes(lint_plan(text).flags) == ["EXCEEDS_SECTION_CAP", "MISSING_BOUNDARY_DEF"]

    def test_a_parse_failure_returns_only_the_grammar_findings(self):
        result = lint_plan("---\nplan_id: two words\n---\n" + make_body())
        assert not result.plan.parsed
        assert result.flags == result.plan.flags and len(result.flags) == 1
        assert result.word_count is None

    def test_an_invalid_route_skips_the_content_checks(self):  # I10
        result = lint_plan(adr_frontmatter().replace('route: "full_plan"', 'route: "weekly"') + "tiny")
        assert codes(result.flags) == ["INVALID_METADATA"]
        assert result.word_count is None

    def test_a_missing_route_skips_the_content_checks(self):
        result = lint_plan(adr_frontmatter().replace('route: "full_plan"', "") + "tiny")
        assert set(codes(result.flags)) == {"INVALID_METADATA"} and result.word_count is None

    def test_routes_and_options_are_passed_through(self):
        text = self.good_plan(700)
        assert lint_plan(text, routes=[PlanRoute(plan_id="5.1", route="pmp_section")]).flags[0].code == "INVALID_METADATA"
        assert codes(lint_plan(text, min_floor_words=1000).flags) == ["BELOW_STANDARD_FLOOR"]
        two = self.good_plan(700, section1="Out-of-scope:\n- One\n")
        assert codes(lint_plan(two, min_out_of_scope_items=2).flags) == ["MISSING_BOUNDARY_DEF"]

    def test_the_frontmatter_is_not_counted(self):
        assert lint_plan(self.good_plan(650)).word_count == 650

    def test_deterministic(self):
        text = adr_frontmatter() + make_body(40, section1="Prose only.", h3=None)
        assert lint_plan(text) == lint_plan(text)

    def test_crlf_and_lf_give_equal_results(self):
        text = self.good_plan(700, section1="Prose only.")
        assert lint_plan(text) == lint_plan(text.replace("\n", "\r\n"))

    def test_the_result_is_frozen(self):
        import dataclasses

        with pytest.raises(dataclasses.FrozenInstanceError):
            lint_plan("").word_count = 1  # type: ignore[misc]

    def test_non_str_raises_type_error(self):
        with pytest.raises(TypeError):
            lint_plan(None)  # type: ignore[arg-type]

    def test_never_raises_for_any_text(self):
        alphabet = ["-", "\n", " ", "a", ":", "#", '"', "'", "[", "]", "`", "<!--", "-->", "## 1. Intent, Alignment & Boundaries", "None: ", "Out of scope", "\t", "\r", "é", "route: full_plan"]
        for seed in range(1500):
            rng = random.Random(seed)
            body = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 40)))
            lint_plan(body)
            lint_plan("---\nroute: full_plan\nplan_id: x\n---\n" + body)
            lint_plan(adr_frontmatter() + body)
        for text in ("", "---", "---\n---", "﻿", "\x00", "---\nroute: pmp_section\n---"):
            assert isinstance(lint_plan(text), LintResult)

    def test_parse_frontmatter_result_is_reused(self):
        text = self.good_plan(700)
        assert lint_plan(text).plan == parse_frontmatter(text)
