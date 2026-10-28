"""Contract tests for Story 13.3: The Approval Record and the Policy Shape.

Story: docs/user-stories/epic-13-subsidiary-plan-approval-gates-before-pmp-formalization.md (Story 13.3)
ADR:   ADR-013 section 4.2; ADR-034 sections 4.2.1, 4.3.1
BRD:   BRD-013 (BRU-013-03)
FDD:   FDD-013 section 3.3
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_learning.pmbok import (
    APPROVAL_ACTIONS,
    DISPOSITIONS,
    FEEDBACK_STATUSES,
    GATE_CRITERIA,
    PlanApprovalRecord,
    approval_record,
    build_approval_metadata,
    latest_approvals,
)

REPO = Path(__file__).resolve().parent.parent
POLICY_SHAPES_DIR = REPO / "docs" / "policy-shapes"

_VALID_HASH_A = "a" * 64
_VALID_HASH_B = "b" * 64


class TestPlanApprovalRecord:
    """Acceptance criteria tests for Story 13.3."""

    def test_ac0_producer_exact_keys(self) -> None:
        """$AC_0$: build_approval_metadata returns exactly the seven ADR-034 section 4.2.1 keys and no others."""
        meta = build_approval_metadata(
            plan_id="scope-management",
            canonical_content_hash=_VALID_HASH_A,
            upstream_hashes={"charter-input": _VALID_HASH_B},
            decision_disposition="accepted",
            feedback_status="accepted",
            run_id="run-12345",
            sequence_number=1,
        )

        expected_keys = {
            "plan_id",
            "canonical_content_hash",
            "upstream_hashes",
            "decision_disposition",
            "feedback_status",
            "run_id",
            "sequence_number",
        }
        assert set(meta.keys()) == expected_keys
        assert meta["plan_id"] == "scope-management"
        assert meta["canonical_content_hash"] == _VALID_HASH_A
        assert meta["upstream_hashes"] == {"charter-input": _VALID_HASH_B}
        assert meta["decision_disposition"] == "accepted"
        assert meta["feedback_status"] == "accepted"
        assert meta["run_id"] == "run-12345"
        assert meta["sequence_number"] == 1

    def test_ac1_round_trip_and_extra_keys_ignored(self) -> None:
        """$AC_1$: approval_record reads what build_approval_metadata wrote for all actions and dispositions; extra keys ignored."""
        for action in APPROVAL_ACTIONS:
            for disp in DISPOSITIONS:
                for feed in FEEDBACK_STATUSES:
                    meta = build_approval_metadata(
                        plan_id="schedule-management",
                        canonical_content_hash=_VALID_HASH_A,
                        upstream_hashes={"scope-management": _VALID_HASH_B},
                        decision_disposition=disp,
                        feedback_status=feed,
                        run_id="run-test",
                        sequence_number=2,
                    )
                    # Inject extra keys in stored metadata
                    stored_meta = dict(meta)
                    stored_meta["extra_audit_field"] = "ignored"
                    stored_meta["unrelated"] = 999

                    rec = approval_record(action, stored_meta, "2026-10-28T12:00:00Z")

                    assert isinstance(rec, PlanApprovalRecord)
                    assert rec.plan_id == "schedule-management"
                    assert rec.canonical_content_hash == _VALID_HASH_A
                    assert rec.action_id == action
                    assert rec.decision_disposition == disp
                    assert rec.feedback_status == feed
                    assert dict(rec.upstream_hashes) == {"scope-management": _VALID_HASH_B}
                    assert rec.sequence_number == 2
                    assert rec.created_at == "2026-10-28T12:00:00Z"

    def test_ac2_validation_invalid_inputs(self) -> None:
        """$AC_2$: raises ValueError naming the key on invalid values or missing contract keys."""
        valid_kwargs = {
            "plan_id": "scope-management",
            "canonical_content_hash": _VALID_HASH_A,
            "upstream_hashes": {"upstream-plan": _VALID_HASH_B},
            "decision_disposition": "accepted",
            "feedback_status": "accepted",
            "run_id": "run-001",
            "sequence_number": 0,
        }

        # 1. Non-kebab-case plan_id
        for bad_id in ("ScopeManagement", "scope_management", "scope--management", "-scope", ""):
            with pytest.raises(ValueError, match="plan_id"):
                build_approval_metadata(**{**valid_kwargs, "plan_id": bad_id})

        # 2. Hash not 64 lowercase hex (including raw: hash) in canonical_content_hash
        for bad_hash in (
            f"raw:{_VALID_HASH_A}",
            "a" * 63,
            "A" * 64,
            "g" * 64,
            "",
        ):
            with pytest.raises(ValueError, match="canonical_content_hash"):
                build_approval_metadata(**{**valid_kwargs, "canonical_content_hash": bad_hash})

        # 3. Bad hash in upstream_hashes
        with pytest.raises(ValueError, match="upstream_hashes"):
            build_approval_metadata(
                **{**valid_kwargs, "upstream_hashes": {"upstream": f"raw:{_VALID_HASH_B}"}}
            )
        # Bad plan_id in upstream_hashes key
        with pytest.raises(ValueError, match="upstream_hashes"):
            build_approval_metadata(
                **{**valid_kwargs, "upstream_hashes": {"bad_upstream_id": _VALID_HASH_B}}
            )

        # 4. Unknown action, disposition or feedback status
        meta = build_approval_metadata(**valid_kwargs)
        with pytest.raises(ValueError, match="action_id"):
            approval_record("unknown_action", meta, "2026-10-28T12:00:00Z")

        with pytest.raises(ValueError, match="decision_disposition"):
            build_approval_metadata(**{**valid_kwargs, "decision_disposition": "pending"})

        with pytest.raises(ValueError, match="feedback_status"):
            build_approval_metadata(**{**valid_kwargs, "feedback_status": "unknown"})

        # 5. Negative, boolean or non-integer sequence_number
        for bad_seq in (-1, -10, True, False, "1", 1.5):
            with pytest.raises(ValueError, match="sequence_number"):
                build_approval_metadata(**{**valid_kwargs, "sequence_number": bad_seq})

        # 6. Empty run_id
        for bad_run in ("", "   "):
            with pytest.raises(ValueError, match="run_id"):
                build_approval_metadata(**{**valid_kwargs, "run_id": bad_run})

        # 7. Missing contract keys in approval_record
        for key in valid_kwargs:
            incomplete = dict(meta)
            del incomplete[key]
            with pytest.raises(ValueError, match=key):
                approval_record("approve_plan", incomplete, "2026-10-28T12:00:00Z")

    def test_ac3_latest_wins(self) -> None:
        """$AC_3$: latest_approvals keeps record with highest (sequence_number, created_at); preserves input."""
        rec1 = approval_record(
            "approve_plan",
            build_approval_metadata(
                plan_id="scope-management",
                canonical_content_hash=_VALID_HASH_A,
                upstream_hashes={},
                decision_disposition="accepted",
                feedback_status="accepted",
                run_id="run-1",
                sequence_number=1,
            ),
            "2026-10-28T10:00:00Z",
        )
        rec2 = approval_record(
            "approve_plan",
            build_approval_metadata(
                plan_id="scope-management",
                canonical_content_hash=_VALID_HASH_B,
                upstream_hashes={},
                decision_disposition="accepted",
                feedback_status="accepted",
                run_id="run-2",
                sequence_number=2,
            ),
            "2026-10-28T09:00:00Z",
        )
        rec3 = approval_record(
            "approve_plan",
            build_approval_metadata(
                plan_id="cost-management",
                canonical_content_hash=_VALID_HASH_A,
                upstream_hashes={},
                decision_disposition="accepted",
                feedback_status="accepted",
                run_id="run-3",
                sequence_number=1,
            ),
            "2026-10-28T11:00:00Z",
        )

        input_records = [rec1, rec2, rec3]
        input_copy = list(input_records)

        result_forward = latest_approvals(input_records)
        result_reverse = latest_approvals(list(reversed(input_records)))

        # Sequence 2 wins over sequence 1 for scope-management
        assert result_forward["scope-management"] == rec2
        assert result_reverse["scope-management"] == rec2
        assert result_forward["cost-management"] == rec3

        # Input is not changed
        assert input_records == input_copy

        # Same sequence number: later created_at wins
        rec1_later = approval_record(
            "approve_plan",
            build_approval_metadata(
                plan_id="scope-management",
                canonical_content_hash=_VALID_HASH_A,
                upstream_hashes={},
                decision_disposition="accepted",
                feedback_status="accepted",
                run_id="run-1b",
                sequence_number=1,
            ),
            "2026-10-28T12:00:00Z",
        )
        tie_break = latest_approvals([rec1, rec1_later])
        assert tie_break["scope-management"] == rec1_later

    def test_ac4_audit_minimalism(self) -> None:
        """$AC_4$: any string above 256 characters is refused in producer and reader."""
        long_string = "a" * 257
        valid_kwargs = {
            "plan_id": "scope-management",
            "canonical_content_hash": _VALID_HASH_A,
            "upstream_hashes": {},
            "decision_disposition": "accepted",
            "feedback_status": "accepted",
            "run_id": "run-001",
            "sequence_number": 0,
        }

        # Long run_id
        with pytest.raises(ValueError, match="run_id"):
            build_approval_metadata(**{**valid_kwargs, "run_id": long_string})

        # Long created_at in reader
        meta = build_approval_metadata(**valid_kwargs)
        with pytest.raises(ValueError, match="created_at"):
            approval_record("approve_plan", meta, long_string)

    def test_ac5_policy_shape_and_gate_criteria(self) -> None:
        """$AC_5$: approve-subsidiary-plan.actions.json holds APPROVAL_ACTIONS; GATE_CRITERIA weights sum to 1.0."""
        actions_file = POLICY_SHAPES_DIR / "approve-subsidiary-plan.actions.json"
        assert actions_file.exists(), f"Policy shape file missing: {actions_file}"

        with open(actions_file, encoding="utf-8") as f:
            data = json.load(f)

        assert isinstance(data, list)
        action_ids = tuple(item["id"] for item in data)
        assert action_ids == APPROVAL_ACTIONS

        # Structure of each action conforms to approve-* shapes
        for item in data:
            assert "id" in item
            assert "description" in item
            assert "parameters" in item
            assert isinstance(item["parameters"], dict)

        # GATE_CRITERIA holds the four ADR-013 section 4.2 criteria with weights summing to 1.0
        expected_criteria = {
            "charter_alignment": 0.30,
            "substantive_content": 0.30,
            "internal_completeness": 0.25,
            "consistency_with_dependent_plans": 0.15,
        }
        assert dict(GATE_CRITERIA) == expected_criteria
        assert pytest.approx(sum(GATE_CRITERIA.values())) == 1.0

