"""Contract tests for Story 13.6 — The Lifecycle State.

Story 13.6 (docs/user-stories/epic-13-subsidiary-plan-approval-gates-before-pmp-formalization.md)
ADR-013 section 4.6 and ADR-034 sections 4.2.4 and 6.1 (docs/adr/); ADR-034 Test 4
BRD-013 BRU-013-06 (docs/project-docs/Business-Requirements/)
FDD-013 sections 3.6 and 6 (docs/project-docs/Functional-Design/)
"""

import pytest

from agent_learning.pmbok import (
    Freshness,
    PlanApprovalRecord,
    PlanState,
    build_approval_metadata,
    derive_plan_state,
)

H1 = "1" * 64
H2 = "2" * 64


def make_record(
    plan_id: str = "scope-management",
    content_hash: str = H1,
    action_id: str = "approve_plan",
    disposition: str = "accepted",
    feedback: str = "accepted",
    upstream_hashes: dict[str, str] | None = None,
) -> PlanApprovalRecord:
    meta = build_approval_metadata(
        plan_id=plan_id,
        canonical_content_hash=content_hash,
        upstream_hashes=upstream_hashes or {},
        decision_disposition=disposition,
        feedback_status=feedback,
        run_id="run-001",
        sequence_number=1,
    )
    return PlanApprovalRecord(
        plan_id=plan_id,
        canonical_content_hash=content_hash,
        action_id=action_id,
        decision_disposition=disposition,
        feedback_status=feedback,
        upstream_hashes=meta["upstream_hashes"],
        sequence_number=1,
        created_at="2026-10-28T12:00:00Z",
    )


def test_ac0_precedence_order():
    rec_app = make_record(action_id="approve_plan", content_hash=H1)
    fresh = Freshness(True, "APPROVED_AND_FRESH", None)

    # 1. Missing file -> NOT_STARTED regardless of any other argument
    st = derive_plan_state(
        exists=False,
        current_hash=H1,
        in_flight_hash=H1,
        latest=rec_app,
        freshness=fresh,
    )
    assert st == PlanState.NOT_STARTED

    # 2. Missing or raw: hash -> INVALID_METADATA
    st = derive_plan_state(
        exists=True,
        current_hash=None,
        in_flight_hash=H1,
        latest=rec_app,
        freshness=fresh,
    )
    assert st == PlanState.INVALID_METADATA

    st = derive_plan_state(
        exists=True,
        current_hash="raw:something",
        in_flight_hash=H1,
        latest=rec_app,
        freshness=fresh,
    )
    assert st == PlanState.INVALID_METADATA

    # 3. in_flight_hash == current_hash -> UNDER_REVIEW
    st = derive_plan_state(
        exists=True,
        current_hash=H1,
        in_flight_hash=H1,
        latest=rec_app,
        freshness=fresh,
    )
    assert st == PlanState.UNDER_REVIEW

    # 4. Local edit outranks past adjudication (different hash)
    st = derive_plan_state(
        exists=True,
        current_hash=H2,
        in_flight_hash=None,
        latest=rec_app,
        freshness=fresh,
    )
    assert st == PlanState.REAPPROVAL_REQUIRED

    # 5. Verdict when matching hash
    st = derive_plan_state(
        exists=True,
        current_hash=H1,
        in_flight_hash=None,
        latest=rec_app,
        freshness=fresh,
    )
    assert st == PlanState.APPROVED

    # 6. No record -> DRAFTED
    st = derive_plan_state(
        exists=True,
        current_hash=H1,
        in_flight_hash=None,
        latest=None,
        freshness=None,
    )
    assert st == PlanState.DRAFTED


def test_ac1_local_edit_adr034_test4():
    # 1. Approved plan edited on disk -> REAPPROVAL_REQUIRED
    rec_approved = make_record(action_id="approve_plan", content_hash=H1)
    st = derive_plan_state(
        exists=True,
        current_hash=H2,  # edited
        in_flight_hash=None,
        latest=rec_approved,
    )
    assert st == PlanState.REAPPROVAL_REQUIRED

    # 2. Rejected plan edited on disk -> DRAFTED
    rec_rejected = make_record(action_id="reject_plan", content_hash=H1)
    st = derive_plan_state(
        exists=True,
        current_hash=H2,  # edited
        in_flight_hash=None,
        latest=rec_rejected,
    )
    assert st == PlanState.DRAFTED

    # 3. Revision-requested plan edited on disk -> DRAFTED
    rec_rev = make_record(action_id="request_revision_before_decision", content_hash=H1)
    st = derive_plan_state(
        exists=True,
        current_hash=H2,  # edited
        in_flight_hash=None,
        latest=rec_rev,
    )
    assert st == PlanState.DRAFTED

    # 4. Submitting edited plan for review -> UNDER_REVIEW
    st = derive_plan_state(
        exists=True,
        current_hash=H2,
        in_flight_hash=H2,  # submitted for review
        latest=rec_approved,
    )
    assert st == PlanState.UNDER_REVIEW


def test_ac2_verdicts_matching_hash():
    # reject_plan
    rec_rej = make_record(action_id="reject_plan", content_hash=H1)
    st = derive_plan_state(
        exists=True,
        current_hash=H1,
        latest=rec_rej,
    )
    assert st == PlanState.REJECTED

    # request_revision_before_decision
    rec_rev = make_record(action_id="request_revision_before_decision", content_hash=H1)
    st = derive_plan_state(
        exists=True,
        current_hash=H1,
        latest=rec_rev,
    )
    assert st == PlanState.REVISION_REQUESTED

    # approve_plan with fresh -> APPROVED
    rec_app = make_record(action_id="approve_plan", content_hash=H1)
    st = derive_plan_state(
        exists=True,
        current_hash=H1,
        latest=rec_app,
        freshness=Freshness(True, "APPROVED_AND_FRESH", None),
    )
    assert st == PlanState.APPROVED

    # approve_plan with PENDING_UPSTREAM -> PENDING_UPSTREAM
    st = derive_plan_state(
        exists=True,
        current_hash=H1,
        latest=rec_app,
        freshness=Freshness(False, "PENDING_UPSTREAM_scope-management", "scope-management"),
    )
    assert st == PlanState.PENDING_UPSTREAM

    # approve_plan with other reason -> STALE_DEPENDENCY
    st = derive_plan_state(
        exists=True,
        current_hash=H1,
        latest=rec_app,
        freshness=Freshness(False, "TRANSITIVE_STALE_FROM_scope-management", "scope-management"),
    )
    assert st == PlanState.STALE_DEPENDENCY

    st = derive_plan_state(
        exists=True,
        current_hash=H1,
        latest=rec_app,
        freshness=Freshness(False, "STALE_DEPENDENCY_scope-management", "scope-management"),
    )
    assert st == PlanState.STALE_DEPENDENCY


def test_ac3_not_a_verdict():
    # modify disposition -> DRAFTED
    rec_mod = make_record(action_id="approve_plan", content_hash=H1, disposition="modify")
    st = derive_plan_state(
        exists=True,
        current_hash=H1,
        latest=rec_mod,
    )
    assert st == PlanState.DRAFTED

    # rejected disposition on approve_plan -> DRAFTED
    rec_rej_disp = make_record(action_id="approve_plan", content_hash=H1, disposition="rejected")
    st = derive_plan_state(
        exists=True,
        current_hash=H1,
        latest=rec_rej_disp,
    )
    assert st == PlanState.DRAFTED

    # rejected feedback -> DRAFTED
    rec_feed_rej = make_record(action_id="approve_plan", content_hash=H1, feedback="rejected")
    st = derive_plan_state(
        exists=True,
        current_hash=H1,
        latest=rec_feed_rej,
    )
    assert st == PlanState.DRAFTED

    # No record and no review -> DRAFTED
    st = derive_plan_state(
        exists=True,
        current_hash=H1,
        latest=None,
    )
    assert st == PlanState.DRAFTED


def test_ac4_needs_freshness():
    rec_app = make_record(action_id="approve_plan", content_hash=H1)

    # Missing freshness when accepted approve_plan matches current_hash -> ValueError
    with pytest.raises(ValueError, match="freshness is required"):
        derive_plan_state(
            exists=True,
            current_hash=H1,
            latest=rec_app,
            freshness=None,
        )

    # Other cases do not need freshness:
    # 1. reject_plan
    rec_rej = make_record(action_id="reject_plan", content_hash=H1)
    assert derive_plan_state(exists=True, current_hash=H1, latest=rec_rej) == PlanState.REJECTED

    # 2. edited plan (hash mismatch)
    assert derive_plan_state(exists=True, current_hash=H2, latest=rec_app) == PlanState.REAPPROVAL_REQUIRED

    # 3. no record
    assert derive_plan_state(exists=True, current_hash=H1, latest=None) == PlanState.DRAFTED

    # 4. in-flight review
    assert derive_plan_state(exists=True, current_hash=H1, in_flight_hash=H1, latest=rec_app) == PlanState.UNDER_REVIEW


def test_ac5_all_ten_states_reachable():
    rec_app = make_record(action_id="approve_plan", content_hash=H1)
    rec_rej = make_record(action_id="reject_plan", content_hash=H1)
    rec_rev = make_record(action_id="request_revision_before_decision", content_hash=H1)
    fresh_ok = Freshness(True, "APPROVED_AND_FRESH", None)
    fresh_pend = Freshness(False, "PENDING_UPSTREAM_x", "x")
    fresh_stale = Freshness(False, "STALE_DEPENDENCY_x", "x")

    reached_states = {
        derive_plan_state(exists=False, current_hash=None): "NOT_STARTED",
        derive_plan_state(exists=True, current_hash="raw:foo"): "INVALID_METADATA",
        derive_plan_state(exists=True, current_hash=H1, in_flight_hash=H1): "UNDER_REVIEW",
        derive_plan_state(exists=True, current_hash=H2, latest=rec_app): "REAPPROVAL_REQUIRED",
        derive_plan_state(exists=True, current_hash=H1, latest=None): "DRAFTED",
        derive_plan_state(exists=True, current_hash=H1, latest=rec_rej): "REJECTED",
        derive_plan_state(exists=True, current_hash=H1, latest=rec_rev): "REVISION_REQUESTED",
        derive_plan_state(exists=True, current_hash=H1, latest=rec_app, freshness=fresh_ok): "APPROVED",
        derive_plan_state(exists=True, current_hash=H1, latest=rec_app, freshness=fresh_pend): "PENDING_UPSTREAM",
        derive_plan_state(exists=True, current_hash=H1, latest=rec_app, freshness=fresh_stale): "STALE_DEPENDENCY",
    }

    assert len(reached_states) == 10
    for st in PlanState:
        assert st in reached_states



def test_unrecognised_action_is_refused():
    """Q-42-1 (Amazon Q, PR 42): a record whose action id is not an approval action is refused, not read as DRAFTED.

    Interpretation (LL-011, FDD-013 section 6 item 10): the story criteria do not say what a record with an
    unknown action id means. The record is built by hand here, bypassing `approval_record()`, which validates
    the id. The function fails closed with `ValueError`, whether the recorded hash matches the current hash or not.
    """
    fresh = Freshness(True, "APPROVED_AND_FRESH", None)
    for recorded in (H1, H2):
        rec = make_record(action_id="approve_everything", content_hash=recorded)
        with pytest.raises(ValueError, match="approve_everything"):
            derive_plan_state(exists=True, current_hash=H1, in_flight_hash=None, latest=rec, freshness=fresh)
    # a known action still behaves as before
    ok = make_record(action_id="approve_plan", content_hash=H1)
    assert derive_plan_state(exists=True, current_hash=H1, in_flight_hash=None, latest=ok, freshness=fresh) == PlanState.APPROVED
