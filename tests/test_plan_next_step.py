"""Contract tests for Story 12.4: precedence and the next step.

Story: docs/user-stories/epic-12-subsidiary-management-plan-standards-and-content-contracts.md (Story 12.4)
ADR:   ADR-012 sections 4.3.4 and 4.5 (three-tier precedence; remedial breakout and graduation)
BRD:   BRD-012 (BRU-012-06, BRU-012-07, BRU-012-08)
FDD:   FDD-012 section 3.7 and the LintFlag contract in section 2

Interpretations not stated verbatim in the acceptance criteria (LL-011), recorded here and in the log:
  I1  ``next_step`` returns a ``NextStepDecision(step, reason, flags)``; ``flags`` is every flag passed in, in the
      order given, as a tuple (including flags that did not decide the step).
  I2  ``reason`` is "<deciding condition>; flags: <codes of every flag, deduplicated in order, or none>".
  I3  A generator that is ``None``, empty, or not one of llm/human/stub/mock is unreadable and escalates at once.
  I4  ``retries`` must be an int (bool rejected) and not negative: a bad value is a call error (TypeError or
      ValueError), not content. It is not changed by the call.
  I5  ``flags`` must be a sequence of ``LintFlag``; anything else is a TypeError. A tier outside A, B, C cannot
      reach ``next_step`` because ``LintFlag`` rejects it at construction.
  I6  A Tier C flag other than ``EXCEEDS_SECTION_CAP`` (including ``EXCEEDS_PLAN_CAP`` and
      ``OMISSION_OF_BASE_PLAN``) is carried to approval; only the section cap asks for a keep-or-graduate review.
  I7  A clean plan whose generator is ``stub`` or ``mock`` still escalates immediately: the generator itself is the
      Tier A condition.
  I8  ``LintFlag.label`` prints "FLAG: " followed by the code; the code itself is stored without the prefix.
"""

from __future__ import annotations

import ast
import dataclasses
import itertools
import sys
from pathlib import Path

import pytest

import agent_learning.pmbok as pmbok_pkg
from agent_learning.pmbok.lint import NextStep, NextStepDecision, next_step
from agent_learning.pmbok.standards import GENERATORS, MAX_AUTO_RETRIES, LintFlag

REPO = Path(__file__).resolve().parents[1]
PKG = REPO / "src" / "agent_learning" / "pmbok"


def flag(code: str, tier: str) -> LintFlag:
    return LintFlag(code=code, tier=tier, message=f"{code} message")  # type: ignore[arg-type]


A = flag("PLACEHOLDER_TOKEN", "A")
B = flag("MISSING_REQUIRED_SECTION", "B")
B2 = flag("INVALID_METADATA", "B")
C = flag("BELOW_STANDARD_FLOOR", "C")
C2 = flag("MISSING_BOUNDARY_DEF", "C")
SECTION_CAP = flag("EXCEEDS_SECTION_CAP", "C")
PLAN_CAP = flag("EXCEEDS_PLAN_CAP", "C")
OMISSION = flag("OMISSION_OF_BASE_PLAN", "C")


class TestPrecedence:
    """AC_0"""

    def test_tier_a_beats_tier_b_and_c_in_every_mix(self):
        for mix in ([A, B], [B, A], [A, C], [A, B, C], [C, B, A], [A, SECTION_CAP]):
            assert next_step(mix, generator="llm").step is NextStep.ESCALATE_IMMEDIATELY
            assert next_step(mix, generator="human").step is NextStep.ESCALATE_IMMEDIATELY

    def test_tier_b_beats_tier_c_in_every_mix(self):
        assert next_step([B, C], generator="llm").step is NextStep.AUTO_REMEDIATE
        assert next_step([C, B], generator="llm").step is NextStep.AUTO_REMEDIATE
        assert next_step([SECTION_CAP, B], generator="llm").step is NextStep.AUTO_REMEDIATE
        assert next_step([B, C], generator="human").step is NextStep.ESCALATE_KEEP_HUMAN_TEXT
        assert next_step([SECTION_CAP, B], generator="human").step is NextStep.ESCALATE_KEEP_HUMAN_TEXT
        assert next_step([B, C], generator="llm", retries=2).step is NextStep.ESCALATE_RETRIES_EXHAUSTED

    def test_a_section_cap_beats_other_tier_c_flags(self):
        assert next_step([C, SECTION_CAP, C2], generator="llm").step is NextStep.HUMAN_ROUTE_REVIEW

    def test_the_rules_apply_in_the_order_of_the_table(self):
        # Rule 1 before 2: a human plan with a Tier A flag is not "kept", it escalates at once.
        assert next_step([A, B], generator="human").step is NextStep.ESCALATE_IMMEDIATELY
        # Rule 2 before 5: a human plan with Tier B and a section cap keeps the human text.
        assert next_step([B, SECTION_CAP], generator="human").step is NextStep.ESCALATE_KEEP_HUMAN_TEXT

    def test_the_steps_are_the_seven_of_the_fdd(self):
        assert {s.value for s in NextStep} == {
            "ready_for_formalization", "carry_to_approval", "human_route_review", "auto_remediate",
            "escalate_immediately", "escalate_keep_human_text", "escalate_retries_exhausted",
        }
        assert issubclass(NextStep, str)


class TestImmediateEscalation:
    """AC_1"""

    @pytest.mark.parametrize("retries", [0, 1, 2, 3, 10])
    def test_a_tier_a_flag_whatever_the_retry_count(self, retries):
        assert next_step([A], generator="llm", retries=retries).step is NextStep.ESCALATE_IMMEDIATELY

    @pytest.mark.parametrize("generator", ["stub", "mock", None, "", "bot", "LLM", "Human"])
    @pytest.mark.parametrize("retries", [0, 1, 2, 10])
    def test_stub_mock_unreadable_and_unknown_generators(self, generator, retries):  # I3
        for flags in ([], [B], [C], [SECTION_CAP]):
            assert next_step(flags, generator=generator, retries=retries).step is NextStep.ESCALATE_IMMEDIATELY

    def test_a_clean_plan_from_a_stub_still_escalates(self):  # I7
        assert next_step([], generator="stub").step is NextStep.ESCALATE_IMMEDIATELY
        assert next_step([], generator="mock").step is NextStep.ESCALATE_IMMEDIATELY


class TestHumanTextIsKept:
    """AC_2"""

    def test_tier_b_with_a_human_generator(self):
        for retries in (0, 1, 2, 10):
            decision = next_step([B], generator="human", retries=retries)
            assert decision.step is NextStep.ESCALATE_KEEP_HUMAN_TEXT

    def test_a_human_plan_is_never_auto_remediated(self):
        for flags in ([], [B], [B, B2], [C], [B, C], [SECTION_CAP], [B, SECTION_CAP, C2]):
            for retries in range(5):
                assert next_step(flags, generator="human", retries=retries).step is not NextStep.AUTO_REMEDIATE


class TestBoundedRetries:
    """AC_3"""

    def test_the_limit_is_two(self):
        assert MAX_AUTO_RETRIES == 2

    @pytest.mark.parametrize("retries, expected", [
        (0, NextStep.AUTO_REMEDIATE), (1, NextStep.AUTO_REMEDIATE),
        (2, NextStep.ESCALATE_RETRIES_EXHAUSTED), (3, NextStep.ESCALATE_RETRIES_EXHAUSTED), (10, NextStep.ESCALATE_RETRIES_EXHAUSTED),
    ])
    def test_llm_with_a_tier_b_flag(self, retries, expected):
        assert next_step([B], generator="llm", retries=retries).step is expected

    def test_retries_default_to_zero(self):
        assert next_step([B], generator="llm").step is NextStep.AUTO_REMEDIATE

    def test_retries_are_not_changed_by_the_call(self):  # I4
        retries = 1
        next_step([B], generator="llm", retries=retries)
        assert retries == 1

    @pytest.mark.parametrize("bad", [-1, True, 1.0, "1", None])
    def test_a_bad_retry_count_is_a_call_error(self, bad):
        with pytest.raises((TypeError, ValueError)):
            next_step([B], generator="llm", retries=bad)  # type: ignore[arg-type]
        assert isinstance(bad, (int, float, str, type(None)))

    def test_the_bad_retry_kinds(self):
        with pytest.raises(ValueError):
            next_step([B], generator="llm", retries=-1)
        for bad in (True, 1.0, "1", None):
            with pytest.raises(TypeError):
                next_step([B], generator="llm", retries=bad)  # type: ignore[arg-type]


class TestContentFlagsAreEvidence:
    """AC_4"""

    def test_the_section_cap_asks_for_a_human_route_review(self):
        assert next_step([SECTION_CAP], generator="llm").step is NextStep.HUMAN_ROUTE_REVIEW
        assert next_step([SECTION_CAP], generator="human").step is NextStep.HUMAN_ROUTE_REVIEW

    @pytest.mark.parametrize("tier_c", [C, C2, PLAN_CAP, OMISSION, [C, C2], [PLAN_CAP, OMISSION, C]])
    def test_other_tier_c_flags_are_carried_to_approval(self, tier_c):  # I6
        flags = tier_c if isinstance(tier_c, list) else [tier_c]
        for generator in ("llm", "human"):
            assert next_step(flags, generator=generator).step is NextStep.CARRY_TO_APPROVAL

    def test_no_flags_is_ready_for_formalization(self):
        for generator in ("llm", "human"):
            assert next_step([], generator=generator).step is NextStep.READY_FOR_FORMALIZATION

    def test_tier_b_and_c_flags_never_produce_the_mechanical_stop(self):
        steps = set()
        for flags in ([B], [C], [SECTION_CAP], [B, C], [B, SECTION_CAP], [PLAN_CAP], [OMISSION]):
            for generator in ("llm", "human"):
                for retries in (0, 1, 2, 5):
                    steps.add(next_step(flags, generator=generator, retries=retries).step)
        assert NextStep.ESCALATE_IMMEDIATELY not in steps
        assert not [s for s in NextStep if "BLOCK" in s.name]


EXPECTED = {
    # flag set name -> generator kind -> expected step (retries matter only for Tier B with llm)
    "none": {"llm": NextStep.READY_FOR_FORMALIZATION, "human": NextStep.READY_FOR_FORMALIZATION},
    "tier_c": {"llm": NextStep.CARRY_TO_APPROVAL, "human": NextStep.CARRY_TO_APPROVAL},
    "section_cap": {"llm": NextStep.HUMAN_ROUTE_REVIEW, "human": NextStep.HUMAN_ROUTE_REVIEW},
    "cap_and_other": {"llm": NextStep.HUMAN_ROUTE_REVIEW, "human": NextStep.HUMAN_ROUTE_REVIEW},
    "tier_b": {"llm": None, "human": NextStep.ESCALATE_KEEP_HUMAN_TEXT},
    "tier_a": {"llm": NextStep.ESCALATE_IMMEDIATELY, "human": NextStep.ESCALATE_IMMEDIATELY},
}
FLAG_SETS = {
    "none": [],
    "tier_c": [C, C2],
    "section_cap": [SECTION_CAP],
    "cap_and_other": [C, SECTION_CAP],
    "tier_b": [B, C],
    "tier_a": [A, B, C],
}
CONDITION_WORDS = {
    NextStep.READY_FOR_FORMALIZATION: "no flags",
    NextStep.CARRY_TO_APPROVAL: "carried to approval",
    NextStep.HUMAN_ROUTE_REVIEW: "keep-or-graduate",
    NextStep.AUTO_REMEDIATE: "automatic retries",
    NextStep.ESCALATE_IMMEDIATELY: "escalate",
    NextStep.ESCALATE_KEEP_HUMAN_TEXT: "human",
    NextStep.ESCALATE_RETRIES_EXHAUSTED: "retries",
}


class TestTotalAndExplained:
    """AC_5"""

    @pytest.mark.parametrize("retries", [0, 1, 2, 3, 10])
    @pytest.mark.parametrize("generator", ["llm", "human", "stub", "mock", None])
    @pytest.mark.parametrize("name", sorted(FLAG_SETS))
    def test_every_combination_gives_one_step_with_a_reason(self, name, generator, retries):
        flags = FLAG_SETS[name]
        decision = next_step(flags, generator=generator, retries=retries)
        assert isinstance(decision, NextStepDecision) and isinstance(decision.step, NextStep)
        if generator not in ("llm", "human"):
            expected = NextStep.ESCALATE_IMMEDIATELY
        elif name == "tier_b" and generator == "llm":
            expected = NextStep.AUTO_REMEDIATE if retries < MAX_AUTO_RETRIES else NextStep.ESCALATE_RETRIES_EXHAUSTED
        else:
            expected = EXPECTED[name][generator]
        assert decision.step is expected
        assert decision.reason.strip()
        assert CONDITION_WORDS[expected] in decision.reason.lower()
        for f in flags:
            assert f.code in decision.reason
        if not flags:
            assert "flags: none" in decision.reason

    def test_the_decision_holds_every_flag_passed_in_in_order(self):  # I1
        flags = [C, SECTION_CAP, C2]
        decision = next_step(flags, generator="llm")
        assert decision.step is NextStep.HUMAN_ROUTE_REVIEW
        assert decision.flags == tuple(flags)
        assert isinstance(decision.flags, tuple)

    def test_a_non_deciding_flag_is_still_named_in_the_reason(self):
        decision = next_step([SECTION_CAP, C], generator="llm")
        assert "BELOW_STANDARD_FLOOR" in decision.reason and "EXCEEDS_SECTION_CAP" in decision.reason

    def test_codes_are_listed_once_and_in_order(self):  # I2
        reason = next_step([C, C, SECTION_CAP], generator="llm").reason
        assert reason.count("BELOW_STANDARD_FLOOR") == 1
        assert reason.index("BELOW_STANDARD_FLOOR") < reason.index("EXCEEDS_SECTION_CAP")

    def test_the_retry_count_above_the_limit_still_exhausts(self):
        assert next_step([B], generator="llm", retries=10**6).step is NextStep.ESCALATE_RETRIES_EXHAUSTED

    def test_the_full_matrix_is_total(self):
        seen = set()
        for name, generator, retries in itertools.product(FLAG_SETS, ["llm", "human", "stub", "mock", None], [0, 1, 2, 3, 10]):
            seen.add(next_step(FLAG_SETS[name], generator=generator, retries=retries).step)
        assert seen == set(NextStep)

    def test_deterministic_and_frozen(self):
        a = next_step([B, C], generator="llm", retries=1)
        assert a == next_step([B, C], generator="llm", retries=1)
        with pytest.raises(dataclasses.FrozenInstanceError):
            a.step = NextStep.CARRY_TO_APPROVAL  # type: ignore[misc]

    def test_input_validation(self):  # I5
        for bad in (None, "x", 3, [B, "x"], [object()]):
            with pytest.raises(TypeError):
                next_step(bad, generator="llm")  # type: ignore[arg-type]
        assert next_step((B,), generator="llm").step is NextStep.AUTO_REMEDIATE  # a tuple is a sequence

    def test_never_raises_for_any_valid_input(self):
        pool = [A, B, B2, C, C2, SECTION_CAP, PLAN_CAP, OMISSION]
        for size in range(4):
            for combo in itertools.product(pool, repeat=size):
                for generator in ("llm", "human", "stub", "mock", None, "x"):
                    for retries in (0, 1, 2, 5):
                        assert next_step(list(combo), generator=generator, retries=retries).reason


class TestClosedTiers:
    """AC_6"""

    @pytest.mark.parametrize("tier", ["D", "a", "b", "", "AB", " A", None, 1, "Tier A"])
    def test_a_tier_outside_a_b_c_raises_value_error(self, tier):
        with pytest.raises(ValueError):
            LintFlag(code="X", tier=tier, message="m")  # type: ignore[arg-type]

    @pytest.mark.parametrize("tier", ["A", "B", "C"])
    def test_the_three_tiers_are_accepted(self, tier):
        assert LintFlag(code="X", tier=tier, message="m").tier == tier  # type: ignore[arg-type]

    def test_label_is_flag_colon_code(self):  # I8
        assert flag("INVALID_METADATA", "B").label == "FLAG: INVALID_METADATA"
        assert flag("INVALID_METADATA", "B").code == "INVALID_METADATA"

    def test_every_finding_the_lint_produces_has_a_valid_tier(self):
        from agent_learning.pmbok import check_content, lint_plan, validate_metadata

        findings = list(validate_metadata({})) + list(check_content("", "full_plan")) + list(lint_plan("").flags)
        assert findings and all(f.tier in ("A", "B", "C") and f.label.startswith("FLAG: ") for f in findings)


class TestNoStorageNoNewDependency:
    """AC_7"""

    @staticmethod
    def imports(path: Path) -> list[tuple[int, str]]:
        found: list[tuple[int, str]] = []
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                found += [(0, alias.name) for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                found.append((node.level, node.module or ""))
        return found

    @pytest.mark.parametrize("name", ["lint.py", "standards.py", "parser.py"])
    def test_imports_are_standard_library_siblings_or_tailoring(self, name):
        for level, module in self.imports(PKG / name):
            if level == 0:
                assert module.split(".")[0] in sys.stdlib_module_names, (name, module)
            elif level == 1:
                assert module in ("standards", "parser", "lint", "scope", "body_visible"), (name, module)
            else:
                assert module == "tailoring", (name, module)
                assert name == "lint.py"

    @pytest.mark.parametrize("name", ["lint.py", "standards.py", "parser.py"])
    def test_nothing_reaches_storage_or_the_legacy_package(self, name):
        source = (PKG / name).read_text(encoding="utf-8")
        for needle in ("LearningStore", "agent_learning.storage", "import pmbok", "from pmbok", "import yaml"):
            assert needle not in source, (name, needle)

    def test_the_result_types_are_frozen_dataclasses(self):
        from agent_learning.pmbok.lint import LintResult
        from agent_learning.pmbok.parser import ParsedPlan
        from agent_learning.pmbok.standards import PlanStandard

        for cls in (LintFlag, ParsedPlan, LintResult, NextStepDecision, PlanStandard):
            assert dataclasses.is_dataclass(cls) and cls.__dataclass_params__.frozen, cls

    def test_no_record_type_is_added_to_the_store(self):
        from agent_learning import storage

        names = {n for n in dir(storage)}
        for added in ("LintFlag", "LintResult", "ParsedPlan", "NextStepDecision", "PlanStandard", "NextStep"):
            assert added not in names

    def test_the_package_exports_the_whole_lint(self):
        for name in ("LintFlag", "LintResult", "NextStep", "NextStepDecision", "next_step", "parse_frontmatter",
                     "validate_metadata", "check_content", "count_words", "lint_plan", "omission_flags"):
            assert hasattr(pmbok_pkg, name), name
            import agent_learning

            assert getattr(agent_learning, name) is getattr(pmbok_pkg, name), name
        assert set(GENERATORS) == {"llm", "human", "stub", "mock"}
