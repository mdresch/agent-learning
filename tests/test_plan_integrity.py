"""Contract tests for Story 13.2: Technical Integrity and the Gate Constraint.

Story: docs/user-stories/epic-13-subsidiary-plan-approval-gates-before-pmp-formalization.md (Story 13.2)
ADR:   ADR-013 section 4.2; ADR-034 sections 4.2.1, 4.3.1
BRD:   BRD-013 (BRU-013-02)
FDD:   FDD-013 section 3.2
"""

from __future__ import annotations

import pytest

from agent_learning.pmbok import (
    PLACEHOLDER_TOKENS,
    LintFlag,
    NextStep,
    gate_constraint_results,
    integrity_flags,
    next_step,
)


def _valid_plan_text(generator: str = "llm", body: str = "Clean body content here.\n") -> str:
    return (
        "---\n"
        'plan_id: "scope-management"\n'
        'plan_name: "Scope Management Plan"\n'
        'pmbok_edition: "PMBOK 8"\n'
        'pmbok_focus_area: "Planning"\n'
        'primary_pmbok_domain: "Scope"\n'
        'legacy_process: "5.1 Plan Scope Management"\n'
        'route: "full_plan"\n'
        f'generator: "{generator}"\n'
        'version: "1.0.0"\n'
        'baseline_id: "none"\n'
        'owner_role: "architect"\n'
        "depends_on: []\n"
        "inputs:\n"
        '  - "charter"\n'
        "outputs:\n"
        '  - "scope-management-plan"\n'
        'governance_policy: "approve-subsidiary-plan"\n'
        "---\n"
        "## 1. Intent, Alignment & Boundaries\n\n"
        f"{body}\n"
    )


class TestTechnicalIntegrity:
    """Acceptance criteria tests for Story 13.2."""

    def test_ac0_stub_generator(self) -> None:
        """$AC_0$: generator 'stub' or 'mock' gives one Tier A STUB_GENERATOR; 'llm' and 'human' give none."""
        stub_plan = _valid_plan_text(generator="stub")
        mock_plan = _valid_plan_text(generator="mock")
        llm_plan = _valid_plan_text(generator="llm")
        human_plan = _valid_plan_text(generator="human")

        stub_flags = integrity_flags(stub_plan)
        assert len(stub_flags) == 1
        assert stub_flags[0].code == "STUB_GENERATOR"
        assert stub_flags[0].tier == "A"
        assert stub_flags[0].evidence == "stub"

        mock_flags = integrity_flags(mock_plan)
        assert len(mock_flags) == 1
        assert mock_flags[0].code == "STUB_GENERATOR"
        assert mock_flags[0].tier == "A"
        assert mock_flags[0].evidence == "mock"

        assert integrity_flags(llm_plan) == []
        assert integrity_flags(human_plan) == []

    def test_ac1_placeholder_tokens(self) -> None:
        """$AC_1$: each placeholder token gives Tier A PLACEHOLDER_TOKEN; fenced code/HTML comments do not."""
        for token in PLACEHOLDER_TOKENS:
            text = _valid_plan_text(body=f"Some text with {token} inside.")
            flags = integrity_flags(text)
            assert len(flags) == 1
            assert flags[0].code == "PLACEHOLDER_TOKEN"
            assert flags[0].tier == "A"
            assert flags[0].evidence == token
            assert token in flags[0].message

        # Token inside fenced code
        fenced_text = _valid_plan_text(body="```python\n# [TBD]\n[TODO]\nStub content for Artifact\n```")
        assert integrity_flags(fenced_text) == []

        # Token inside HTML comment
        comment_text = _valid_plan_text(body="<!-- [Insert here] and [TBD] -->")
        assert integrity_flags(comment_text) == []

        # Multiple tokens appear in the order of PLACEHOLDER_TOKENS
        multi_text = _valid_plan_text(body="Content: [TODO] first, then Stub content for Artifact, then [TBD]")
        multi_flags = integrity_flags(multi_text)
        codes = [f.code for f in multi_flags]
        evidences = [f.evidence for f in multi_flags]

        assert codes == ["PLACEHOLDER_TOKEN", "PLACEHOLDER_TOKEN", "PLACEHOLDER_TOKEN"]
        # Expected order matches PLACEHOLDER_TOKENS:
        # ("Stub content for Artifact", "[Insert here]", "[TBD]", "[TODO]")
        assert evidences == ["Stub content for Artifact", "[TBD]", "[TODO]"]

    def test_ac2_process_failure(self) -> None:
        """$AC_2$: generation_error gives GENERATION_FAILED; text=None gives MISSING_ARTIFACT and returns."""
        # generation_error only
        flags_gen_err = integrity_flags(_valid_plan_text(), generation_error="API timeout after 30s")
        assert len(flags_gen_err) == 1
        assert flags_gen_err[0].code == "GENERATION_FAILED"
        assert flags_gen_err[0].tier == "A"
        assert flags_gen_err[0].evidence == "API timeout after 30s"

        # text is None only
        flags_missing = integrity_flags(None)
        assert len(flags_missing) == 1
        assert flags_missing[0].code == "MISSING_ARTIFACT"
        assert flags_missing[0].tier == "A"

        # Both: returns GENERATION_FAILED then MISSING_ARTIFACT, and nothing else
        flags_both = integrity_flags(None, generation_error="Failed to invoke model")
        assert len(flags_both) == 2
        assert flags_both[0].code == "GENERATION_FAILED"
        assert flags_both[0].tier == "A"
        assert flags_both[1].code == "MISSING_ARTIFACT"
        assert flags_both[1].tier == "A"

    def test_ac3_unparseable_frontmatter(self) -> None:
        """$AC_3$: unparseable frontmatter yields Tier A INVALID_METADATA; stub check is skipped."""
        # Frontmatter with bad syntax and generator: stub
        bad_text = (
            "---\n"
            'plan_id: "scope-management"\n'
            "generator: stub\n"
            "invalid: : syntax\n"
            "---\n"
            "Body\n"
        )
        flags = integrity_flags(bad_text)
        assert len(flags) > 0
        assert all(f.code == "INVALID_METADATA" for f in flags)
        assert all(f.tier == "A" for f in flags)
        # Stub check was skipped because frontmatter did not parse
        assert not any(f.code == "STUB_GENERATOR" for f in flags)

    def test_ac4_flags_not_blocks_provisional_tokens_and_floors_caps(self) -> None:
        """$AC_4$: unbracketed TBD or TODO gives Tier C PROVISIONAL_TOKEN; floors/caps give no integrity findings."""
        # Unbracketed TBD
        tbd_text = _valid_plan_text(body="Section details are TBD.")
        flags_tbd = integrity_flags(tbd_text)
        assert len(flags_tbd) == 1
        assert flags_tbd[0].code == "PROVISIONAL_TOKEN"
        assert flags_tbd[0].tier == "C"
        assert flags_tbd[0].evidence == "TBD"

        # Unbracketed TODO
        todo_text = _valid_plan_text(body="Section details are TODO.")
        flags_todo = integrity_flags(todo_text)
        assert len(flags_todo) == 1
        assert flags_todo[0].code == "PROVISIONAL_TOKEN"
        assert flags_todo[0].tier == "C"
        assert flags_todo[0].evidence == "TODO"

        # Bracketed [TBD] gives Tier A PLACEHOLDER_TOKEN, not Tier C PROVISIONAL_TOKEN
        bracketed_tbd = _valid_plan_text(body="Section details are [TBD].")
        flags_bracketed = integrity_flags(bracketed_tbd)
        assert len(flags_bracketed) == 1
        assert flags_bracketed[0].code == "PLACEHOLDER_TOKEN"
        assert flags_bracketed[0].tier == "A"

        # Below floor / above cap: no integrity findings
        short_plan = _valid_plan_text(body="Short.")
        assert integrity_flags(short_plan) == []

        long_plan = _valid_plan_text(body="Long text word " * 1000)
        assert integrity_flags(long_plan) == []

    def test_ac5_gate_constraint_results(self) -> None:
        """$AC_5$: gate_constraint_results is false for approve_plan iff any flag is Tier A; Tier B/C never change it."""
        # Clean flags: all true
        res_clean = gate_constraint_results([])
        assert res_clean["approve_plan"] == {"no_technical_integrity_block": True}
        assert res_clean["reject_plan"] == {"no_technical_integrity_block": True}
        assert res_clean["request_revision_before_decision"] == {"no_technical_integrity_block": True}

        # Tier C flag: approve_plan is still True
        c_flags = [LintFlag(code="PROVISIONAL_TOKEN", tier="C", message="provisional")]
        res_c = gate_constraint_results(c_flags)
        assert res_c["approve_plan"] == {"no_technical_integrity_block": True}
        assert res_c["reject_plan"] == {"no_technical_integrity_block": True}
        assert res_c["request_revision_before_decision"] == {"no_technical_integrity_block": True}

        # Tier B flag: approve_plan is still True
        b_flags = [LintFlag(code="INVALID_METADATA", tier="B", message="warning")]
        res_b = gate_constraint_results(b_flags)
        assert res_b["approve_plan"] == {"no_technical_integrity_block": True}
        assert res_b["reject_plan"] == {"no_technical_integrity_block": True}
        assert res_b["request_revision_before_decision"] == {"no_technical_integrity_block": True}

        # Tier A flag: approve_plan is False; others stay True
        a_flags = [LintFlag(code="STUB_GENERATOR", tier="A", message="stub generator")]
        res_a = gate_constraint_results(a_flags)
        assert res_a["approve_plan"] == {"no_technical_integrity_block": False}
        assert res_a["reject_plan"] == {"no_technical_integrity_block": True}
        assert res_a["request_revision_before_decision"] == {"no_technical_integrity_block": True}

        # Mixed flags containing Tier A: approve_plan is False
        mixed_flags = [
            LintFlag(code="PROVISIONAL_TOKEN", tier="C", message="provisional"),
            LintFlag(code="INVALID_METADATA", tier="B", message="warning"),
            LintFlag(code="PLACEHOLDER_TOKEN", tier="A", message="placeholder"),
        ]
        res_mixed = gate_constraint_results(mixed_flags)
        assert res_mixed["approve_plan"] == {"no_technical_integrity_block": False}

        # Bad sequence type raises TypeError
        with pytest.raises(TypeError):
            gate_constraint_results("not a sequence")  # type: ignore[arg-type]

    def test_ac6_feeds_next_step(self) -> None:
        """$AC_6$: passing Tier A findings of a stub plan to next_step gives ESCALATE_IMMEDIATELY; clean gives no flags."""
        stub_plan = _valid_plan_text(generator="stub")
        flags = integrity_flags(stub_plan)
        assert any(f.tier == "A" for f in flags)

        decision = next_step(flags, generator="stub")
        assert decision.step == NextStep.ESCALATE_IMMEDIATELY

        clean_plan = _valid_plan_text(generator="llm")
        clean_flags = integrity_flags(clean_plan)
        assert clean_flags == []

    def test_ac7_total_and_ordered_and_deterministic(self) -> None:
        """$AC_7$: findings come in FDD-013 section 3.2 order; no str or None raises; deterministic."""
        # Multiple deficiency plan: generation error, unparseable frontmatter, placeholder, provisional
        bad_text = (
            "---\n"
            "bad frontmatter\n"
            "---\n"
            "Body with Stub content for Artifact and TBD.\n"
        )
        flags = integrity_flags(bad_text, generation_error="Generation failed error")

        codes = [f.code for f in flags]
        # Expected order:
        # 1. GENERATION_FAILED
        # 2. MISSING_ARTIFACT (not present since text is not None)
        # 3. INVALID_METADATA
        # 4. STUB_GENERATOR (skipped since frontmatter unparseable)
        # 5. PLACEHOLDER_TOKEN
        # 6. PROVISIONAL_TOKEN
        assert codes[0] == "GENERATION_FAILED"
        assert "INVALID_METADATA" in codes
        assert "PLACEHOLDER_TOKEN" in codes
        assert codes[-1] == "PROVISIONAL_TOKEN"

        # Total on arbitrary string inputs
        for sample in ("", "plain text", "\ud800", "\n\n\n", "```\n[TBD]\n```"):
            res = integrity_flags(sample)
            assert isinstance(res, list)

        # Deterministic
        assert integrity_flags(bad_text) == integrity_flags(bad_text)

        # Non-str raises TypeError
        with pytest.raises(TypeError):
            integrity_flags(123)  # type: ignore[arg-type]
        with pytest.raises(TypeError):
            integrity_flags("text", generation_error=123)  # type: ignore[arg-type]
