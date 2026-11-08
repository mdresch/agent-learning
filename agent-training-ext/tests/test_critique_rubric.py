"""Contract tests for Story 14.6: The Delta Rubric (AC0 - AC4).

Source: FDD-014 §2.4, ADR-014, epic-14-critique-to-evidence-ingestion.md.
"""

import pytest

try:
    from agent_training_ext.critique_evidence import (
        parse_critique,
        rubric_delta,
        RUBRIC_TABLE,
        RUBRIC_VERSION,
    )
except ImportError:
    try:
        from critique_evidence import (
            parse_critique,
            rubric_delta,
            RUBRIC_TABLE,
            RUBRIC_VERSION,
        )
    except ImportError:
        from agent_learning.critique_evidence import (
            parse_critique,
            rubric_delta,
            RUBRIC_TABLE,
            RUBRIC_VERSION,
        )


def test_ac0_rubric_table_all_18_pairs():
    expected_pairs = {
        ("crash risk", "yes"): -0.30,
        ("crash risk", "partial"): -0.15,
        ("crash risk", "no"): 0.00,
        ("logic error", "yes"): -0.25,
        ("logic error", "partial"): -0.13,
        ("logic error", "no"): 0.00,
        ("test gap", "yes"): -0.15,
        ("test gap", "partial"): -0.08,
        ("test gap", "no"): 0.00,
        ("documentation", "yes"): -0.10,
        ("documentation", "partial"): -0.05,
        ("documentation", "no"): 0.00,
        ("style", "yes"): -0.05,
        ("style", "partial"): -0.03,
        ("style", "no"): 0.00,
        ("confirmation", "yes"): 0.10,
        ("confirmation", "partial"): 0.05,
        ("confirmation", "no"): 0.00,
    }
    assert len(expected_pairs) == 18
    for (claim, ver), expected in expected_pairs.items():
        assert rubric_delta(claim, ver) == pytest.approx(expected, abs=1e-9)


def test_ac1_refuses_unknown_claim_or_verification():
    with pytest.raises(ValueError, match="claim_type"):
        rubric_delta("unknown_claim", "yes")

    with pytest.raises(ValueError, match="verified"):
        rubric_delta("crash risk", "invalid_ver")


def test_ac2_rubric_form_parsed_with_basis_rubric():
    text = "- [criterion: perf] [claim: crash risk] [verified: yes]: High memory footprint recursion"
    deltas = parse_critique(text, source_id="REV-01")
    assert len(deltas) == 1
    d = deltas[0]
    assert d.basis == "rubric"
    assert d.support_delta == pytest.approx(-0.30, abs=1e-9)
    assert d.rubric_delta == pytest.approx(-0.30, abs=1e-9)
    assert d.override is False


def test_ac3_override_logic():
    # Explicit number differing by > 0.005 from rubric value (-0.30)
    text_override = "- [criterion: perf] [claim: crash risk] [verified: yes] -0.10: Milder risk override"
    deltas = parse_critique(text_override, source_id="REV-01")
    assert len(deltas) == 1
    d = deltas[0]
    assert d.basis == "explicit"
    assert d.support_delta == pytest.approx(-0.10, abs=1e-9)
    assert d.rubric_delta == pytest.approx(-0.30, abs=1e-9)
    assert d.override is True

    # Explicit number matching rubric value within 0.005
    text_matching = "- [criterion: perf] [claim: crash risk] [verified: yes] -0.30: Matching value"
    d_matching = parse_critique(text_matching, source_id="REV-01")[0]
    assert d_matching.basis == "explicit"
    assert d_matching.override is False

    # Explicit number without rubric tags
    text_no_rubric = "- [criterion: perf] -0.20: Plain explicit delta"
    d_no_rubric = parse_critique(text_no_rubric, source_id="REV-01")[0]
    assert d_no_rubric.basis == "explicit"
    assert d_no_rubric.rubric_delta is None
    assert d_no_rubric.override is False


def test_ac4_rubric_version_is_one():
    assert RUBRIC_VERSION == "1"
    text = "- [criterion: perf] [claim: logic error] [verified: partial]: Incomplete condition"
    deltas = parse_critique(text, source_id="REV-01")
    assert len(deltas) == 1
    assert deltas[0].rubric_version == "1"
