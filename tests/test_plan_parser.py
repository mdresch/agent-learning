"""Contract tests for Story 12.1: the frontmatter grammar parser.

Story: docs/user-stories/epic-12-subsidiary-management-plan-standards-and-content-contracts.md (Story 12.1)
ADR:   ADR-012 section 4.2 and 4.2.1 (normative text: ADR-034 section 4.3.1)
BRD:   BRD-012 (BRU-012-02)
FDD:   FDD-012 sections 2 and 3.1

Interpretations not stated verbatim in the acceptance criteria (LL-011), recorded here and in the log:
  I1  A "#" starts a comment only after whitespace; a bare token such as ``val#x`` is a finding.
  I2  An escape other than \\" \\\\ \\n inside a double-quoted string is a finding.
  I3  ``key:value`` (no space after the colon) is a finding.
  I4  A list item after a key that already has a scalar or ``[]``, or before any key, is a finding.
  I5  A non-empty flow list such as ``[a]`` is a finding; only ``[]`` is supported.
  I6  A missing closing delimiter reports the last line; empty text reports line 1.
  I7  A key with no items is ``()``.
  I8  Blank lines are dropped; a tab, or any indent other than the two spaces of a list item, is a finding.
  I9  A delimiter with trailing whitespace is not a delimiter.
  I10 ``metadata`` is a read-only mapping that compares equal to a dict; the keys stay in file order.
  I11 ``LintFlag`` exists here with its fields only; the closed tier check and ``label`` belong to Story 12.4.
  I12 Line numbers are 1-based and identical in the original and the CRLF-normalized text.
"""

from __future__ import annotations

import ast
import dataclasses
import re
import sys
from pathlib import Path

import pytest

from agent_learning.pmbok.parser import ParsedPlan, parse_frontmatter
from agent_learning.pmbok.standards import LintFlag

REPO = Path(__file__).resolve().parents[1]
ADR_012 = next((REPO / "docs" / "adr").glob("ADR-012-*.md"))


def adr_012_example() -> str:
    """The canonical frontmatter of ADR-012 section 4.2, taken from the real file."""
    text = ADR_012.read_text(encoding="utf-8")
    start = text.index("### 4.2 Universal Frontmatter Metadata Schema")
    fence = text.index("```yaml\n", start) + len("```yaml\n")
    return text[fence : text.index("```", fence)]


def make(*lines: str) -> str:
    return "\n".join(["---", *lines, "---", ""])


def only_flag(result: ParsedPlan) -> LintFlag:
    assert not result.parsed
    assert len(result.flags) == 1, result.flags
    return result.flags[0]


class TestCanonicalExample:
    """AC_0"""

    def test_parses_and_every_field_matches_the_documented_value(self):
        example = adr_012_example()
        body = "## 1. Intent, Alignment & Boundaries\n\nText.\n"
        result = parse_frontmatter(example + body)
        assert result.parsed and result.flags == ()
        assert result.metadata == {
            "plan_id": "scope-management",
            "plan_name": "Scope Management Plan",
            "pmbok_edition": "PMBOK 8",
            "pmbok_focus_area": "Planning",
            "primary_pmbok_domain": "Scope",
            "secondary_pmbok_domains": ("Governance",),
            "legacy_process": "5.1 Plan Scope Management",
            "route": "full_plan",
            "generator": "llm",
            "version": "1.0.0",
            "baseline_id": "<target-baseline-id>",
            "owner_role": "Project Manager",
            "depends_on": (),
            "inputs": ("Project-Charter.md", "docs/project-docs/Ideation-Document.md"),
            "outputs": ("docs/project-docs/management-plans/Scope-Management-Plan.md",),
            "governance_policy": "approve-subsidiary-plan",
        }

    def test_scalars_are_str_and_lists_are_tuples(self):
        meta = parse_frontmatter(adr_012_example()).metadata
        assert type(meta["plan_id"]) is str
        assert type(meta["inputs"]) is tuple and type(meta["depends_on"]) is tuple
        assert meta["depends_on"] == ()

    def test_body_and_its_start_line(self):
        example = adr_012_example()
        closing_line = example.rstrip("\n").count("\n") + 1
        result = parse_frontmatter(example + "## Heading\ntext\n")
        assert result.body == "## Heading\ntext\n"
        assert result.body_start_line == closing_line + 1

    def test_body_may_be_empty(self):
        result = parse_frontmatter("---\nplan_id: x\n---")
        assert result.parsed and result.body == "" and result.body_start_line == 4


class TestGrammarRules:
    """AC_1"""

    def test_crlf_and_bom_are_normalized(self):
        text = "\ufeff---\r\nplan_id: x\r\n---\r\nbody\r\n"
        result = parse_frontmatter(text)
        assert result.parsed
        assert result.metadata == {"plan_id": "x"}
        assert result.body == "body\n"

    def test_opening_delimiter_must_stand_alone(self):
        for first in ("--- ", " ---", "----", "--- # note"):
            assert not parse_frontmatter(f"{first}\nplan_id: x\n---\n").parsed

    def test_closing_delimiter_must_stand_alone(self):
        for closing in ("--- ", " ---", "----"):
            assert not parse_frontmatter(f"---\nplan_id: x\n{closing}\n").parsed

    def test_frontmatter_ends_at_the_first_closing_delimiter(self):
        result = parse_frontmatter("---\na: 1\n---\nbody\n---\nnot: metadata\n")
        assert result.metadata == {"a": "1"}
        assert result.body == "body\n---\nnot: metadata\n"

    @pytest.mark.parametrize("key", ["plan_id", "a", "x_y_z", "_"])
    def test_valid_keys(self, key):
        assert parse_frontmatter(make(f"{key}: v")).metadata == {key: "v"}

    @pytest.mark.parametrize("key", ["Plan", "plan-id", "plan1", "1plan", "plan id", ""])
    def test_invalid_keys(self, key):
        assert not parse_frontmatter(make(f"{key}: v")).parsed

    def test_double_quoted_escapes(self):
        meta = parse_frontmatter(make(r'k: "a\"b\\c\nd"')).metadata
        assert meta["k"] == 'a"b\\c\nd'

    def test_unknown_escape_is_a_finding(self):  # I2
        assert not parse_frontmatter(make(r'k: "a\tb"')).parsed

    def test_single_quoted_text_is_literal(self):
        meta = parse_frontmatter(make(r"k: 'a\nb\\'")).metadata
        assert meta["k"] == r"a\nb\\"

    def test_quoted_scalars_may_contain_spaces_and_symbols(self):
        meta = parse_frontmatter(make('k: "PMBOK 8: {x} [y] | z"', "j: 'a b'")).metadata
        assert meta == {"k": "PMBOK 8: {x} [y] | z", "j": "a b"}

    @pytest.mark.parametrize("token", ["1.0.0", "full_plan", "Scope", "a-b", "A_1.2-x"])
    def test_bare_tokens(self, token):
        assert parse_frontmatter(make(f"k: {token}")).metadata == {"k": token}

    @pytest.mark.parametrize("value", ["two words", "a/b", "a,b", "a:b", "a=b", "a@b", "val#x"])
    def test_bare_values_outside_the_token_class_are_findings(self, value):  # I1
        assert not parse_frontmatter(make(f"k: {value}")).parsed

    def test_colon_needs_a_space_before_a_value(self):  # I3
        assert not parse_frontmatter(make("k:v")).parsed

    def test_list_items_use_exactly_two_spaces(self):
        ok = parse_frontmatter(make("k:", '  - "a"', "  - b"))
        assert ok.metadata == {"k": ("a", "b")}
        for item in (' - "a"', '   - "a"', '    - "a"', '\t- "a"'):
            assert not parse_frontmatter(make("k:", item)).parsed, item

    def test_list_item_forms(self):
        meta = parse_frontmatter(make("k:", "  - 'a b'", '  - "c d"', "  - e.f")).metadata
        assert meta["k"] == ("a b", "c d", "e.f")

    def test_list_item_without_an_owner_is_a_finding(self):  # I4
        assert not parse_frontmatter(make('  - "a"')).parsed
        assert not parse_frontmatter(make("k: v", '  - "a"')).parsed
        assert not parse_frontmatter(make("k: []", '  - "a"')).parsed

    def test_empty_list_forms(self):
        meta = parse_frontmatter(make("a: []", "b:", "c:  # note", "d: x")).metadata
        assert meta == {"a": (), "b": (), "c": (), "d": "x"}  # I7

    def test_non_empty_flow_list_is_a_finding(self):  # I5
        assert not parse_frontmatter(make("k: [a, b]")).parsed
        assert not parse_frontmatter(make("k: [ ]")).parsed

    def test_comments_after_every_allowed_position(self):
        text = make(
            "# whole-line comment",
            "",
            "a: v  # after a bare scalar",
            'b: "q"  # after a quoted scalar',
            "c: 'q' # after a single-quoted scalar",
            "d: []  # after an empty list",
            "e:  # after a bare key",
            '  - "x"  # after a list item',
            "  # comment between items",
            "  - y # another",
        )
        result = parse_frontmatter(text)
        assert result.parsed, result.flags
        assert result.metadata == {"a": "v", "b": "q", "c": "q", "d": (), "e": ("x", "y")}

    def test_hash_inside_quotes_is_text(self):
        meta = parse_frontmatter(make('a: "x # y"', "b: 'p # q'", "c:", '  - "m # n"')).metadata
        assert meta == {"a": "x # y", "b": "p # q", "c": ("m # n",)}

    def test_comment_after_a_quoted_scalar_needs_whitespace(self):
        assert not parse_frontmatter(make('a: "x"#y')).parsed

    def test_text_after_a_quoted_scalar_is_a_finding(self):
        assert not parse_frontmatter(make('a: "x" y')).parsed
        assert not parse_frontmatter(make("a: 'x' y")).parsed

    def test_unterminated_quote_is_a_finding(self):
        assert not parse_frontmatter(make('a: "x')).parsed
        assert not parse_frontmatter(make("a: 'x")).parsed

    def test_blank_lines_are_dropped_and_tabs_are_findings(self):  # I8
        assert parse_frontmatter(make("a: v", "", "   ", "b: w")).metadata == {"a": "v", "b": "w"}
        assert not parse_frontmatter(make("a:\tv")).parsed
        assert not parse_frontmatter(make("\ta: v")).parsed


class TestFindingsNeverExceptions:
    """AC_2"""

    @pytest.mark.parametrize(
        "lines, line_no, evidence",
        [
            (["a: 1", "a: 2"], 3, "a: 2"),  # duplicate key
            (["a: two words"], 2, "a: two words"),  # unquoted value with spaces
            (["a:", "  b: 1"], 3, "  b: 1"),  # nested mapping
            (["a: |"], 2, "a: |"),  # block scalar
            (["a: >"], 2, "a: >"),
            (["a: &anchor x"], 2, "a: &anchor x"),  # anchor
            (["a: *alias"], 2, "a: *alias"),  # alias
            (["a: {b: 1}"], 2, "a: {b: 1}"),  # flow mapping
            (["a: !!str x"], 2, "a: !!str x"),  # type tag
        ],
    )
    def test_each_prohibited_or_malformed_construct(self, lines, line_no, evidence):
        flag = only_flag(parse_frontmatter(make(*lines)))
        assert flag.code == "INVALID_METADATA"
        assert flag.tier == "B"
        assert flag.line == line_no
        assert flag.evidence == evidence
        assert flag.message

    def test_missing_opening_delimiter(self):
        flag = only_flag(parse_frontmatter("plan_id: x\n---\nbody\n"))
        assert (flag.code, flag.tier, flag.line, flag.evidence) == ("INVALID_METADATA", "B", 1, "plan_id: x")

    def test_missing_closing_delimiter(self):  # I6
        flag = only_flag(parse_frontmatter("---\nplan_id: x\nroute: y\n"))
        assert (flag.code, flag.tier) == ("INVALID_METADATA", "B")
        assert flag.line == 3
        assert flag.evidence == "route: y"

    def test_empty_text_and_bom_only_text(self):
        for text in ("", "\ufeff", "\n", "\r\n"):
            flag = only_flag(parse_frontmatter(text))
            assert (flag.code, flag.tier, flag.line) == ("INVALID_METADATA", "B", 1)

    def test_every_violating_line_gets_its_own_finding(self):
        result = parse_frontmatter(make("a: 1", "a: 2", "b: two words", "c: |"))
        assert not result.parsed
        assert [f.line for f in result.flags] == [3, 4, 5]

    def test_line_numbers_count_from_the_original_first_line(self):  # I12
        text = "\ufeff---\r\n# c\r\na: 1\r\nb: two words\r\n---\r\n"
        assert only_flag(parse_frontmatter(text)).line == 4

    @pytest.mark.parametrize(
        "text",
        [
            "", "---", "---\n", "---\n---", "---\n---\n", "\x00", "---\n\x00\n---\n", "---\n:\n---\n",
            "---\n: v\n---\n", "---\n- x\n---\n", "---\n\"\n---\n", "---\n'\n---\n", "---\n[\n---\n",
            "---\n]\n---\n", "---\n\\\n---\n", "\ufeff\ufeff---\n---\n", "é: v", "---\nk: é\n---\n",
            "---\nk: \"\\\n---\n", "---\n  \n---\n", "---\r\r\n---\n",
        ],
    )
    def test_no_input_raises(self, text):
        result = parse_frontmatter(text)
        assert isinstance(result, ParsedPlan)

    def test_generated_inputs_never_raise(self):
        import itertools

        alphabet = ["-", "-", "-", "\n", " ", "a", ":", "#", '"', "'", "[", "]", "{", "|", ">", "&", "*", "!", "\\", "\t", "\r", "é"]
        for length in range(6):
            for combo in itertools.product(alphabet, repeat=length) if length <= 3 else []:
                parse_frontmatter("".join(combo))
        for seed in range(2000):
            import random

            rng = random.Random(seed)
            parse_frontmatter("---\n" + "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 60))) + "\n---\n")

    @pytest.mark.parametrize("bad", [None, 1, b"---\n---\n", ["---"], 1.5])
    def test_non_str_raises_type_error(self, bad):
        with pytest.raises(TypeError):
            parse_frontmatter(bad)  # type: ignore[arg-type]


class TestFailClosed:
    """AC_3"""

    @pytest.mark.parametrize(
        "text",
        ["", "no frontmatter", "---\na: 1\na: 2\n---\nbody\n", "---\na: 1\n", "---\nok: v\nbad: two words\n---\nbody\n"],
    )
    def test_nothing_half_read_is_returned(self, text):
        result = parse_frontmatter(text)
        assert result.parsed is False
        assert result.metadata == {}
        assert result.body == ""
        assert result.body_start_line is None
        assert len(result.flags) >= 1

    def test_success_has_no_flags_and_a_start_line(self):
        result = parse_frontmatter("---\na: 1\n---\nbody\n")
        assert result.parsed is True and result.flags == () and result.body_start_line == 4

    def test_flag_fields_default_sensibly(self):  # I11
        flag = LintFlag(code="X", tier="B", message="m")
        assert flag.line is None and flag.evidence == ""


class TestDeterminism:
    """AC_4"""

    TEXT = "---\nplan_id: x\nz_key: 1\na_key: 2\nlist:\n  - b\n  - a\n---\nBody line\nSecond\n"

    def test_same_text_twice_is_equal(self):
        assert parse_frontmatter(self.TEXT) == parse_frontmatter(self.TEXT)

    def test_lf_and_crlf_forms_are_equal(self):
        assert parse_frontmatter(self.TEXT) == parse_frontmatter(self.TEXT.replace("\n", "\r\n"))

    def test_failures_are_equal_across_line_endings(self):
        bad = "---\na: 1\na: 2\n---\n"
        assert parse_frontmatter(bad) == parse_frontmatter(bad.replace("\n", "\r\n"))

    def test_keys_keep_file_order(self):
        assert list(parse_frontmatter(self.TEXT).metadata) == ["plan_id", "z_key", "a_key", "list"]

    def test_list_items_keep_file_order(self):
        assert parse_frontmatter(self.TEXT).metadata["list"] == ("b", "a")

    def test_metadata_is_read_only(self):  # I10
        meta = parse_frontmatter(self.TEXT).metadata
        with pytest.raises(TypeError):
            meta["new"] = "x"  # type: ignore[index]

    def test_result_is_frozen(self):
        result = parse_frontmatter(self.TEXT)
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.parsed = False  # type: ignore[misc]


class TestPurity:
    """AC_5"""

    def test_public_names_are_exported_from_the_package_and_the_root(self):
        import agent_learning
        from agent_learning import pmbok

        for name in ("LintFlag", "ParsedPlan", "parse_frontmatter"):
            assert getattr(agent_learning, name) is getattr(pmbok, name)

    @staticmethod
    def imports(path: Path) -> list[tuple[int, str]]:
        found: list[tuple[int, str]] = []
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                found += [(0, alias.name) for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                found.append((node.level, node.module or ""))
        return found

    def test_parser_imports_only_the_standard_library_and_its_sibling(self):
        from agent_learning.pmbok import parser

        for level, module in self.imports(Path(parser.__file__)):
            if level:
                assert module == "standards", (level, module)
            else:
                assert module.split(".")[0] in sys.stdlib_module_names, module

    def test_parser_does_not_reach_storage_tailoring_or_the_legacy_package(self):
        from agent_learning.pmbok import parser

        source = Path(parser.__file__).read_text(encoding="utf-8")
        for name in ("agent_learning.storage", "agent_learning.tailoring", "LearningStore", "import pmbok", "from pmbok"):
            assert name not in source, name

    def test_standards_imports_only_the_standard_library(self):
        from agent_learning.pmbok import standards

        for level, module in self.imports(Path(standards.__file__)):
            assert level == 0 and module.split(".")[0] in sys.stdlib_module_names, module

    def test_the_package_does_not_import_a_yaml_library(self):
        # pyproject.toml already lists pyyaml for the legacy stack that ADR-034 decommissions; the new
        # package must not use it.
        package = REPO / "src" / "agent_learning" / "pmbok"
        for path in package.glob("*.py"):
            assert not re.search(r"(?m)^\s*(import|from)\s+yaml\b", path.read_text(encoding="utf-8")), path.name
