"""Contract tests for Story 14.1: The Tag Grammar and Parser.

Tests parse_critique() against the grammar defined in FDD-014 §2.1.
Pure function tests: standard library only, imports nothing from agent_learning.storage,
and performs no file or network I/O.
"""

import pytest

try:
    from agent_training_ext.critique_evidence import (
        CritiqueDelta,
        parse_critique,
        rubric_delta,
    )
except ImportError:
    try:
        from critique_evidence import (
            CritiqueDelta,
            parse_critique,
            rubric_delta,
        )
    except ImportError:
        from agent_learning.critique_evidence import (
            CritiqueDelta,
            parse_critique,
            rubric_delta,
        )


# ==============================================================================
# AC0 (Grammar): Returns one CritiqueDelta per bullet in line order,
# with verbatim rationale, ignoring non-bullet lines.
# ==============================================================================

def test_ac0_grammar_line_order_and_verbatim_rationale():
    text = """
# Review Findings Document
Some introductory prose here that should be completely ignored.

- [finding: Q-34-1] [criterion: architectural_soundness] -0.20: Unchecked concurrency race on active pointer replace
- [criterion: consequences_honest] +0.10: Explicit disclosure of negative performance trade-offs

A closing paragraph that is also ignored.
"""
    deltas = parse_critique(text, source_id="REV-001")
    assert len(deltas) == 2

    # First bullet
    assert deltas[0].finding_id == "Q-34-1"
    assert deltas[0].criterion_id == "architectural_soundness"
    assert deltas[0].support_delta == -0.20
    assert deltas[0].rationale == "Unchecked concurrency race on active pointer replace"
    assert deltas[0].basis == "explicit"
    assert deltas[0].rubric_delta is None
    assert deltas[0].override is False

    # Second bullet
    assert deltas[1].finding_id == "REV-001#2"
    assert deltas[1].criterion_id == "consequences_honest"
    assert deltas[1].support_delta == +0.10
    assert deltas[1].rationale == "Explicit disclosure of negative performance trade-offs"
    assert deltas[1].basis == "explicit"
    assert deltas[1].rubric_delta is None
    assert deltas[1].override is False


def test_ac0_ignores_headings_prose_and_blank_lines():
    text = """
# Heading 1
## Heading 2
Just a narrative description without any list items.

- [criterion: c1] +0.05: Valid bullet 1
1. Numbered item should be ignored
* [criterion: c2] -0.10: Asterisk bullet 2
"""
    deltas = parse_critique(text, source_id="SRC-1")
    assert len(deltas) == 2
    assert deltas[0].criterion_id == "c1"
    assert deltas[1].criterion_id == "c2"


# ==============================================================================
# AC1 (No Guessing): Missing criterion tag, or neither signed number nor both rubric tags.
# ==============================================================================

def test_ac1_missing_criterion_tag_raises_value_error():
    text = "- [finding: Q-1] -0.20: Rationale without criterion"
    with pytest.raises(ValueError, match=r"Line 1.*criterion"):
        parse_critique(text, source_id="SRC-1")


def test_ac1_unsigned_number_raises_value_error():
    text = "- [criterion: c1] 0.20: Missing sign on delta"
    with pytest.raises(ValueError, match=r"Line 1.*delta"):
        parse_critique(text, source_id="SRC-1")


def test_ac1_missing_delta_and_rubric_tags_raises_value_error():
    text = "- [criterion: c1]: Only rationale, no delta or rubric"
    with pytest.raises(ValueError, match=r"Line 1"):
        parse_critique(text, source_id="SRC-1")


def test_ac1_partial_rubric_tag_raises_value_error():
    text = "- [criterion: c1] [claim: logic error]: Missing verified tag"
    with pytest.raises(ValueError, match=r"Line 1"):
        parse_critique(text, source_id="SRC-1")


# ==============================================================================
# AC2 (Bounds): Delta outside [-1.0, 1.0] raises ValueError; -1.0 and +1.0 accepted.
# ==============================================================================

def test_ac2_bounds_outside_range_rejected():
    text_neg = "- [criterion: c1] -1.20: Too negative"
    with pytest.raises(ValueError, match=r"Line 1.*-1.0, 1.0"):
        parse_critique(text_neg, source_id="SRC-1")

    text_pos = "- [criterion: c1] +1.01: Too positive"
    with pytest.raises(ValueError, match=r"Line 1.*-1.0, 1.0"):
        parse_critique(text_pos, source_id="SRC-1")


def test_ac2_bounds_extremes_accepted():
    text = """
- [criterion: c1] -1.00: Lowest allowed
- [criterion: c2] +1.00: Highest allowed
"""
    deltas = parse_critique(text, source_id="SRC-1")
    assert len(deltas) == 2
    assert deltas[0].support_delta == -1.00
    assert deltas[1].support_delta == +1.00


# ==============================================================================
# AC3 (Fields): Empty rationale, invalid finding id, invalid source_id raises ValueError.
# ==============================================================================

def test_ac3_empty_rationale_raises_value_error():
    text = "- [criterion: c1] -0.10:"
    with pytest.raises(ValueError, match=r"Line 1.*rationale"):
        parse_critique(text, source_id="SRC-1")


def test_ac3_invalid_finding_id_raises_value_error():
    text = "- [finding: bad finding/id] [criterion: c1] -0.10: Rationale"
    with pytest.raises(ValueError, match=r"Line 1.*finding id"):
        parse_critique(text, source_id="SRC-1")


def test_ac3_invalid_source_id_raises_value_error():
    text = "- [criterion: c1] -0.10: Valid bullet"
    with pytest.raises(ValueError, match=r"source_id"):
        parse_critique(text, source_id="invalid source id with spaces")


# ==============================================================================
# AC4 (Finding Ids): Tagged finding keeps id; untagged gets <source_id>#<n>.
# ==============================================================================

def test_ac4_finding_id_retention_and_ordinal_generation():
    text = """
- [finding: Q-34-1] [criterion: c1] -0.10: Explicit id 1
- [criterion: c2] -0.05: Untagged finding
- [finding: custom.id_99] [criterion: c3] +0.05: Explicit id 2
- [criterion: c4] +0.10: Another untagged finding
"""
    deltas = parse_critique(text, source_id="REV-42")
    assert [d.finding_id for d in deltas] == [
        "Q-34-1",
        "REV-42#2",
        "custom.id_99",
        "REV-42#4",
    ]


# ==============================================================================
# AC5 (Pure): Module imports nothing from agent_learning.storage and performs no I/O.
# ==============================================================================

def test_ac5_module_is_pure_and_has_no_storage_dependency():
    try:
        import agent_training_ext.critique_evidence as ce
    except ImportError:
        try:
            import critique_evidence as ce
        except ImportError:
            import agent_learning.critique_evidence as ce
    import sys

    # Assert no storage modules imported by critique_evidence
    module_text = open(ce.__file__, encoding="utf-8").read()
    assert "agent_learning.storage" not in module_text
    assert "LearningStore" not in module_text
