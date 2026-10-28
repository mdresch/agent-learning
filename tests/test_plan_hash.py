"""Contract tests for Story 13.1: The Canonical Content Hash.

Story: docs/user-stories/epic-13-subsidiary-plan-approval-gates-before-pmp-formalization.md (Story 13.1)
ADR:   ADR-013 section 4.3; ADR-034 sections 4.2.1, 4.3.1
BRD:   BRD-013 (BRU-013-01)
FDD:   FDD-013 section 3.1
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from pathlib import Path

import pytest

from agent_learning.pmbok import (
    VOLATILE_KEYS,
    compute_canonical_plan_hash,
    is_raw_hash,
    plan_hash,
    raw_change_hash,
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


class TestCanonicalPlanHash:
    """Acceptance criteria tests for Story 13.1."""

    def test_ac0_known_value(self) -> None:
        """$AC_0$: compute_canonical_plan_hash equals SHA-256 of expected normalized text."""
        raw_text = (
            "---\n"
            "plan_id: scope-management\n"
            'plan_name: "Scope Management Plan"\n'
            "last_modified: 2026-10-27\n"
            "---\n"
            "## 1. Intent\n"
            "\n"
            "Content with hard break  \n"
            "and second line.\n"
        )
        expected_normalized = (
            "---\n"
            "plan_id: scope-management\n"
            'plan_name: "Scope Management Plan"\n'
            "---\n"
            "## 1. Intent\n"
            "\n"
            "Content with hard break  \n"
            "and second line."
        )
        expected_hash = hashlib.sha256(expected_normalized.encode("utf-8")).hexdigest()
        computed = compute_canonical_plan_hash(raw_text)

        assert computed == expected_hash
        assert len(computed) == 64
        assert re.fullmatch(r"[0-9a-f]{64}", computed) is not None

    def test_ac1_invariance_line_endings(self) -> None:
        """$AC_1$: equal for LF, CRLF, and lone-CR forms."""
        base = (
            "---\n"
            "plan_id: scope-management\n"
            "---\n"
            "Line 1\n"
            "Line 2\n"
        )
        crlf = base.replace("\n", "\r\n")
        lone_cr = base.replace("\n", "\r")
        mixed = "---\r\nplan_id: scope-management\r---\nLine 1\r\nLine 2\n"

        h_base = compute_canonical_plan_hash(base)
        assert compute_canonical_plan_hash(crlf) == h_base
        assert compute_canonical_plan_hash(lone_cr) == h_base
        assert compute_canonical_plan_hash(mixed) == h_base

    def test_ac1_invariance_bom(self) -> None:
        """$AC_1$: equal with and without leading BOMs."""
        base = "---\nplan_id: scope-management\n---\nBody\n"
        with_single_bom = "\ufeff" + base
        with_double_bom = "\ufeff\ufeff" + base

        h_base = compute_canonical_plan_hash(base)
        assert compute_canonical_plan_hash(with_single_bom) == h_base
        assert compute_canonical_plan_hash(with_double_bom) == h_base

    def test_ac1_invariance_unicode_normalization(self) -> None:
        """$AC_1$: equal for NFC and NFD forms of the same characters."""
        base_nfc = (
            "---\n"
            "plan_id: scope-management\n"
            "---\n"
            "Le café et le résumé sont prêts.\n"
        )
        base_nfd = unicodedata.normalize("NFD", base_nfc)
        assert base_nfc != base_nfd

        h_nfc = compute_canonical_plan_hash(base_nfc)
        h_nfd = compute_canonical_plan_hash(base_nfd)
        assert h_nfc == h_nfd

    def test_ac1_invariance_trailing_whitespace_and_tabs(self) -> None:
        """$AC_1$: equal with added/removed trailing spaces/tabs except hard break."""
        base = (
            "---\n"
            "plan_id: scope-management\n"
            "---\n"
            "Heading  \n"  # Hard break: content followed by exactly 2 spaces
            "Body line 1\n"
            "Body line 2\n"
        )
        with_extra_spaces_and_tabs = (
            "---\t \n"
            "plan_id: scope-management   \n"
            "---\t\n"
            "Heading  \n"  # preserved hard break
            "Body line 1 \n"
            "Body line 2\t\t\n"
        )
        h_base = compute_canonical_plan_hash(base)
        assert compute_canonical_plan_hash(with_extra_spaces_and_tabs) == h_base

    def test_ac1_invariance_leading_and_trailing_blank_lines(self) -> None:
        """$AC_1$: equal with leading and trailing blank lines added."""
        base = "---\nplan_id: scope-management\n---\nBody content\n"
        padded = "\n\n   \n" + base + "\n\n\t  \n"

        h_base = compute_canonical_plan_hash(base)
        assert compute_canonical_plan_hash(padded) == h_base

    def test_ac1_invariance_volatile_keys(self) -> None:
        """$AC_1$: equal when volatile keys (scalar or list) are added, changed, or removed."""
        base = (
            "---\n"
            "plan_id: scope-management\n"
            "owner_role: lead\n"
            "---\n"
            "Body\n"
        )
        with_scalars = (
            "---\n"
            "plan_id: scope-management\n"
            "last_modified: 2026-10-27\n"
            "generated_at: 2026-10-27\n"
            "governance_hash: 0123456789abcdef\n"
            "owner_role: lead\n"
            "---\n"
            "Body\n"
        )
        with_different_values = (
            "---\n"
            "plan_id: scope-management\n"
            "last_modified: 2026-10-28\n"
            "generated_at: 2026-10-28\n"
            "governance_hash: fedcba9876543210\n"
            "owner_role: lead\n"
            "---\n"
            "Body\n"
        )
        with_list_items = (
            "---\n"
            "plan_id: scope-management\n"
            "approval_ref:\n"
            "  - apr-001\n"
            "  - apr-002\n"
            "owner_role: lead\n"
            "---\n"
            "Body\n"
        )
        with_empty_list = (
            "---\n"
            "plan_id: scope-management\n"
            "approval_ref: []\n"
            "owner_role: lead\n"
            "---\n"
            "Body\n"
        )

        h_base = compute_canonical_plan_hash(base)
        assert compute_canonical_plan_hash(with_scalars) == h_base
        assert compute_canonical_plan_hash(with_different_values) == h_base
        assert compute_canonical_plan_hash(with_list_items) == h_base
        assert compute_canonical_plan_hash(with_empty_list) == h_base

    def test_ac2_sensitivity_body_word(self) -> None:
        """$AC_2$: differs when a body word changes."""
        t1 = "---\nplan_id: scope-management\n---\nFirst version\n"
        t2 = "---\nplan_id: scope-management\n---\nSecond version\n"
        assert compute_canonical_plan_hash(t1) != compute_canonical_plan_hash(t2)

    def test_ac2_sensitivity_static_frontmatter_value(self) -> None:
        """$AC_2$: differs when a static frontmatter value changes."""
        t1 = "---\nplan_id: scope-management\nversion: 1.0.0\n---\nBody\n"
        t2 = "---\nplan_id: scope-management\nversion: 1.0.1\n---\nBody\n"
        assert compute_canonical_plan_hash(t1) != compute_canonical_plan_hash(t2)

    def test_ac2_sensitivity_static_key_added(self) -> None:
        """$AC_2$: differs when a static key is added."""
        t1 = "---\nplan_id: scope-management\n---\nBody\n"
        t2 = "---\nplan_id: scope-management\nowner_role: lead\n---\nBody\n"
        assert compute_canonical_plan_hash(t1) != compute_canonical_plan_hash(t2)

    def test_ac2_sensitivity_static_keys_reordered(self) -> None:
        """$AC_2$: differs when static keys are reordered."""
        t1 = "---\nplan_id: scope-management\nowner_role: lead\n---\nBody\n"
        t2 = "---\nowner_role: lead\nplan_id: scope-management\n---\nBody\n"
        assert compute_canonical_plan_hash(t1) != compute_canonical_plan_hash(t2)

    def test_ac2_sensitivity_hard_break_and_two_space_whitespace_line(self) -> None:
        """$AC_2$: differs when gaining/losing exactly 2 trailing spaces after content; '  ' is empty."""
        with_break = "---\nplan_id: scope-management\n---\nLine 1  \nLine 2\n"
        without_break = "---\nplan_id: scope-management\n---\nLine 1\nLine 2\n"
        assert compute_canonical_plan_hash(with_break) != compute_canonical_plan_hash(without_break)

        # A whitespace-only line of two spaces is the same as an empty line
        empty_line = "---\nplan_id: scope-management\n---\nLine 1\n\nLine 2\n"
        two_space_line = "---\nplan_id: scope-management\n---\nLine 1\n  \nLine 2\n"
        assert compute_canonical_plan_hash(empty_line) == compute_canonical_plan_hash(two_space_line)

    def test_ac3_raw_change_hash(self) -> None:
        """$AC_3$: raw_change_hash starts with 'raw:' and changes with any byte change."""
        t1 = "Hello world\n"
        t2 = "Hello world\r\n"
        t3 = "Hello world \n"

        h1 = raw_change_hash(t1)
        h2 = raw_change_hash(t2)
        h3 = raw_change_hash(t3)

        assert h1.startswith("raw:")
        assert len(h1) == 68
        assert h1 != h2
        assert h1 != h3

    def test_ac3_plan_hash_and_is_raw_hash(self) -> None:
        """$AC_3$: plan_hash returns canonical for parseable and raw for unparseable."""
        parseable = "---\nplan_id: scope-management\n---\nBody\n"
        unparseable = "Plain text without frontmatter"

        h_parseable = plan_hash(parseable)
        assert not is_raw_hash(h_parseable)
        assert h_parseable == compute_canonical_plan_hash(parseable)

        h_unparseable = plan_hash(unparseable)
        assert is_raw_hash(h_unparseable)
        assert h_unparseable == raw_change_hash(unparseable)

        with pytest.raises(ValueError, match="frontmatter"):
            compute_canonical_plan_hash(unparseable)

    def test_ac4_total_on_str(self) -> None:
        """$AC_4$: plan_hash does not raise for any str; non-str raises TypeError; repeated calls equal."""
        # Valid strings that would fail parsing or encoding
        surrogate_text = "Lone surrogate: \ud800"
        empty_text = ""
        no_closing_fm = "---\nplan_id: scope-management\n"

        for text in (surrogate_text, empty_text, no_closing_fm):
            res = plan_hash(text)
            assert isinstance(res, str)
            assert is_raw_hash(res)

        # Non-str raises TypeError across functions
        for bad_val in (None, 123, b"bytes", ["text"]):
            with pytest.raises(TypeError):
                plan_hash(bad_val)  # type: ignore[arg-type]
            with pytest.raises(TypeError):
                compute_canonical_plan_hash(bad_val)  # type: ignore[arg-type]
            with pytest.raises(TypeError):
                raw_change_hash(bad_val)  # type: ignore[arg-type]
            with pytest.raises(TypeError):
                is_raw_hash(bad_val)  # type: ignore[arg-type]

        # Repeated calls are equal (purity)
        assert plan_hash(surrogate_text) == plan_hash(surrogate_text)
        sample = "---\nplan_id: scope-management\n---\nDeterministic\n"
        assert plan_hash(sample) == plan_hash(sample)

    def test_ac5_real_plans_adr025(self) -> None:
        """$AC_5$: ADR-025 frontmatter example with body gives same hash in LF and CRLF."""
        adr_fm = adr_frontmatter_example(25)
        assert adr_fm.startswith("---\n")

        plan_lf = f"{adr_fm}\n## 1. Intent, Alignment & Boundaries\n\nReal body content here.\n"
        plan_crlf = plan_lf.replace("\n", "\r\n")

        h_lf = compute_canonical_plan_hash(plan_lf)
        h_crlf = compute_canonical_plan_hash(plan_crlf)

        assert h_lf == h_crlf
        assert len(h_lf) == 64
        assert not is_raw_hash(h_lf)
