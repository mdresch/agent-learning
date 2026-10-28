"""Contract tests for Story 13.5 — Freshness and Transitive Staleness.

Story 13.5 (docs/user-stories/epic-13-subsidiary-plan-approval-gates-before-pmp-formalization.md)
ADR-013 section 4.5 and ADR-034 sections 4.2.3 and 6.1 (docs/adr/)
BRD-013 BRU-013-05 (docs/project-docs/Business-Requirements/)
FDD-013 sections 3.5 and 6 (docs/project-docs/Functional-Design/); ADR-034 Test 1, Test 2 and Test 6
"""

import pytest

from agent_learning.pmbok import (
    PLAN_DAG,
    CyclicDependencyError,
    Freshness,
    PlanApprovalRecord,
    build_approval_metadata,
    check_plan_freshness,
)

H_SCOPE = "a" * 64
H_SCOPE_2 = "b" * 64
H_SCHED = "c" * 64
H_SCHED_2 = "d" * 64
H_COST = "e" * 64


def make_record(
    plan_id: str,
    content_hash: str,
    upstream_hashes: dict[str, str],
    action_id: str = "approve_plan",
    disposition: str = "accepted",
    feedback: str = "accepted",
    seq: int = 1,
    created_at: str = "2026-10-28T12:00:00Z",
) -> PlanApprovalRecord:
    meta = build_approval_metadata(
        plan_id=plan_id,
        canonical_content_hash=content_hash,
        upstream_hashes=upstream_hashes,
        decision_disposition=disposition,
        feedback_status=feedback,
        run_id="run-001",
        sequence_number=seq,
    )
    return PlanApprovalRecord(
        plan_id=plan_id,
        canonical_content_hash=content_hash,
        action_id=action_id,
        decision_disposition=disposition,
        feedback_status=feedback,
        upstream_hashes=meta["upstream_hashes"],
        sequence_number=seq,
        created_at=created_at,
    )


def test_ac0_basic_outcomes():
    # 1. not_applicable
    dag = {"test-plan": ()}
    routes = {"test-plan": "not_applicable"}
    res = check_plan_freshness("test-plan", dag, routes, {}, {}, {})
    assert res == Freshness(True, "NOT_APPLICABLE", None)

    # 2. pmp_section fresh
    dag = {"scope-management": (), "schedule-management": ("scope-management",)}
    routes = {"scope-management": "full_plan", "schedule-management": "pmp_section"}
    rec_scope = make_record("scope-management", H_SCOPE, {})
    curr_hashes = {"scope-management": H_SCOPE, "schedule-management": H_SCHED}
    is_non_stub = {"scope-management": True, "schedule-management": True}
    approvals = {"scope-management": rec_scope}

    res_sched = check_plan_freshness("schedule-management", dag, routes, curr_hashes, is_non_stub, approvals)
    assert res_sched == Freshness(True, "SECTION_FRESH", None)

    # 3. full_plan fresh
    rec_sched = make_record("schedule-management", H_SCHED, {"scope-management": H_SCOPE})
    approvals["schedule-management"] = rec_sched
    routes["schedule-management"] = "full_plan"
    res_sched_fp = check_plan_freshness("schedule-management", dag, routes, curr_hashes, is_non_stub, approvals)
    assert res_sched_fp == Freshness(True, "APPROVED_AND_FRESH", None)


def test_ac1_approval_problems():
    dag = {"scope-management": ()}
    routes = {"scope-management": "full_plan"}
    curr_hashes = {"scope-management": H_SCOPE}
    is_non_stub = {"scope-management": True}

    # No record
    res = check_plan_freshness("scope-management", dag, routes, curr_hashes, is_non_stub, {})
    assert res == Freshness(False, "NO_APPROVAL_RECORD", "scope-management")

    # reject_plan
    rec_reject = make_record("scope-management", H_SCOPE, {}, action_id="reject_plan")
    res = check_plan_freshness("scope-management", dag, routes, curr_hashes, is_non_stub, {"scope-management": rec_reject})
    assert res == Freshness(False, "NOT_APPROVED_reject_plan", "scope-management")

    # request_revision_before_decision
    rec_rev = make_record("scope-management", H_SCOPE, {}, action_id="request_revision_before_decision")
    res = check_plan_freshness("scope-management", dag, routes, curr_hashes, is_non_stub, {"scope-management": rec_rev})
    assert res == Freshness(False, "NOT_APPROVED_request_revision_before_decision", "scope-management")

    # unaccepted disposition
    rec_disp = make_record("scope-management", H_SCOPE, {}, disposition="modify")
    res = check_plan_freshness("scope-management", dag, routes, curr_hashes, is_non_stub, {"scope-management": rec_disp})
    assert res == Freshness(False, "NOT_APPROVED_UNACCEPTED", "scope-management")

    # unaccepted feedback
    rec_feed = make_record("scope-management", H_SCOPE, {}, feedback="rejected")
    res = check_plan_freshness("scope-management", dag, routes, curr_hashes, is_non_stub, {"scope-management": rec_feed})
    assert res == Freshness(False, "NOT_APPROVED_UNACCEPTED", "scope-management")


def test_ac2_content_and_dependency_changes():
    dag = {"scope-management": (), "schedule-management": ("scope-management",)}
    routes = {"scope-management": "full_plan", "schedule-management": "full_plan"}
    rec_scope = make_record("scope-management", H_SCOPE, {})
    rec_sched = make_record("schedule-management", H_SCHED, {"scope-management": H_SCOPE})
    approvals = {"scope-management": rec_scope, "schedule-management": rec_sched}
    is_non_stub = {"scope-management": True, "schedule-management": True}

    # Hash changed
    curr_hashes_mod = {"scope-management": H_SCOPE, "schedule-management": H_SCHED_2}
    res = check_plan_freshness("schedule-management", dag, routes, curr_hashes_mod, is_non_stub, approvals)
    assert res == Freshness(False, "REAPPROVAL_REQUIRED_CONTENT_MODIFIED", "schedule-management")

    # Missing current hash
    curr_hashes_missing = {"scope-management": H_SCOPE}
    res = check_plan_freshness("schedule-management", dag, routes, curr_hashes_missing, is_non_stub, approvals)
    assert res == Freshness(False, "INVALID_METADATA_UNPARSEABLE", "schedule-management")

    # Raw hash
    curr_hashes_raw = {"scope-management": H_SCOPE, "schedule-management": "raw:12345"}
    res = check_plan_freshness("schedule-management", dag, routes, curr_hashes_raw, is_non_stub, approvals)
    assert res == Freshness(False, "INVALID_METADATA_UNPARSEABLE", "schedule-management")

    # Upstream recorded hash mismatch
    rec_sched_bad_up = make_record("schedule-management", H_SCHED, {"scope-management": "f" * 64})
    approvals_bad_up = {"scope-management": rec_scope, "schedule-management": rec_sched_bad_up}
    curr_hashes = {"scope-management": H_SCOPE, "schedule-management": H_SCHED}
    res = check_plan_freshness("schedule-management", dag, routes, curr_hashes, is_non_stub, approvals_bad_up)
    assert res == Freshness(False, "STALE_DEPENDENCY_scope-management", "scope-management")


def test_ac3_mixed_route_staleness_adr034_test1():
    # Scope (full_plan) -> Schedule (pmp_section) -> Cost (full_plan)
    dag = {
        "scope-management": (),
        "schedule-management": ("scope-management",),
        "cost-management": ("schedule-management",),
    }
    routes = {
        "scope-management": "full_plan",
        "schedule-management": "pmp_section",
        "cost-management": "full_plan",
    }
    rec_scope = make_record("scope-management", H_SCOPE, {})
    rec_cost = make_record("cost-management", H_COST, {"schedule-management": H_SCHED})
    approvals = {"scope-management": rec_scope, "cost-management": rec_cost}
    is_non_stub = {
        "scope-management": True,
        "schedule-management": True,
        "cost-management": True,
    }

    # Initial state: Scope is H_SCOPE, Schedule is H_SCHED, Cost is H_COST
    curr_hashes = {
        "scope-management": H_SCOPE,
        "schedule-management": H_SCHED,
        "cost-management": H_COST,
    }
    res_cost = check_plan_freshness("cost-management", dag, routes, curr_hashes, is_non_stub, approvals)
    assert res_cost == Freshness(True, "APPROVED_AND_FRESH", None)

    # Edit Scope's content: changes H_SCOPE to H_SCOPE_2
    curr_hashes_scope_edited = {
        "scope-management": H_SCOPE_2,
        "schedule-management": H_SCHED,  # Schedule unchanged
        "cost-management": H_COST,        # Cost unchanged
    }
    res_cost_stale = check_plan_freshness(
        "cost-management", dag, routes, curr_hashes_scope_edited, is_non_stub, approvals
    )
    assert res_cost_stale == Freshness(False, "TRANSITIVE_STALE_FROM_scope-management", "scope-management")


def test_ac4_omission_bypass_adr034_test2():
    # Scope (full_plan) -> Schedule (not_applicable) -> Cost (full_plan)
    dag = {
        "scope-management": (),
        "schedule-management": ("scope-management",),
        "cost-management": ("schedule-management",),
    }
    routes = {
        "scope-management": "full_plan",
        "schedule-management": "not_applicable",
        "cost-management": "full_plan",
    }
    rec_scope = make_record("scope-management", H_SCOPE, {})
    # Since Schedule is omitted, effective upstream for Cost is scope-management!
    rec_cost = make_record("cost-management", H_COST, {"scope-management": H_SCOPE})
    approvals = {"scope-management": rec_scope, "cost-management": rec_cost}
    is_non_stub = {
        "scope-management": True,
        "schedule-management": True,
        "cost-management": True,
    }

    curr_hashes = {
        "scope-management": H_SCOPE,
        "schedule-management": H_SCHED,
        "cost-management": H_COST,
    }
    res_cost = check_plan_freshness("cost-management", dag, routes, curr_hashes, is_non_stub, approvals)
    assert res_cost == Freshness(True, "APPROVED_AND_FRESH", None)

    # Editing nothing but Schedule's omission leaves Cost fresh
    curr_hashes_sched_mod = {
        "scope-management": H_SCOPE,
        "schedule-management": H_SCHED_2,
        "cost-management": H_COST,
    }
    res_cost_after_sched_edit = check_plan_freshness(
        "cost-management", dag, routes, curr_hashes_sched_mod, is_non_stub, approvals
    )
    assert res_cost_after_sched_edit == Freshness(True, "APPROVED_AND_FRESH", None)

    # Modifying Scope's hash invalidates Cost as transitively stale through bypass
    curr_hashes_scope_mod = {
        "scope-management": H_SCOPE_2,
        "schedule-management": H_SCHED,
        "cost-management": H_COST,
    }
    res_cost_after_scope_edit = check_plan_freshness(
        "cost-management", dag, routes, curr_hashes_scope_mod, is_non_stub, approvals
    )
    assert res_cost_after_scope_edit == Freshness(False, "STALE_DEPENDENCY_scope-management", "scope-management")


def test_ac5_bounded_scope():
    # Use real PLAN_DAG
    routes = {p: "full_plan" for p in PLAN_DAG}
    approvals = {}
    curr_hashes = {}
    is_non_stub = {}

    for p in PLAN_DAG:
        curr_hashes[p] = f"{hash(p) & 0xffffffffffffffff:016x}" * 4
        is_non_stub[p] = True

    # Build approvals in topological order
    for p in PLAN_DAG:
        upstreams = {up: curr_hashes[up] for up in PLAN_DAG[p]}
        approvals[p] = make_record(p, curr_hashes[p], upstreams)

    # Confirm scope, schedule, cost are fresh
    for p in ("scope-management", "schedule-management", "cost-management"):
        res = check_plan_freshness(p, PLAN_DAG, routes, curr_hashes, is_non_stub, approvals)
        assert res.fresh is True

    # Mutate communications-management (leaf/support plan)
    curr_hashes_mutated = dict(curr_hashes)
    curr_hashes_mutated["communications-management"] = "f" * 64

    # Scope, schedule, and cost must remain fresh!
    for p in ("scope-management", "schedule-management", "cost-management"):
        res = check_plan_freshness(p, PLAN_DAG, routes, curr_hashes_mutated, is_non_stub, approvals)
        assert res == Freshness(True, "APPROVED_AND_FRESH", None)


def test_ac6_technical_integrity_upstream_adr034_test6():
    dag = {
        "scope-management": (),
        "schedule-management": ("scope-management",),
        "cost-management": ("schedule-management",),
    }
    routes = {
        "scope-management": "full_plan",
        "schedule-management": "pmp_section",
        "cost-management": "full_plan",
    }
    rec_scope = make_record("scope-management", H_SCOPE, {})
    rec_cost = make_record("cost-management", H_COST, {"schedule-management": H_SCHED})
    approvals = {"scope-management": rec_scope, "cost-management": rec_cost}

    # 1. Section is a stub
    is_non_stub_stub = {
        "scope-management": True,
        "schedule-management": False,  # stub!
        "cost-management": True,
    }
    curr_hashes = {
        "scope-management": H_SCOPE,
        "schedule-management": H_SCHED,
        "cost-management": H_COST,
    }
    res_sched = check_plan_freshness(
        "schedule-management", dag, routes, curr_hashes, is_non_stub_stub, approvals
    )
    assert res_sched == Freshness(False, "INVALID_OR_STUB_SECTION", "schedule-management")

    res_cost = check_plan_freshness(
        "cost-management", dag, routes, curr_hashes, is_non_stub_stub, approvals
    )
    assert res_cost == Freshness(False, "TRANSITIVE_STALE_FROM_schedule-management", "schedule-management")

    # 2. Section has raw: hash
    is_non_stub_ok = {
        "scope-management": True,
        "schedule-management": True,
        "cost-management": True,
    }
    curr_hashes_raw = {
        "scope-management": H_SCOPE,
        "schedule-management": "raw:unparseable",
        "cost-management": H_COST,
    }
    res_sched_raw = check_plan_freshness(
        "schedule-management", dag, routes, curr_hashes_raw, is_non_stub_ok, approvals
    )
    assert res_sched_raw == Freshness(False, "INVALID_OR_STUB_SECTION", "schedule-management")


def test_ac7_pending_vs_stale():
    dag = {
        "scope-management": (),
        "schedule-management": ("scope-management",),
        "cost-management": ("schedule-management",),
    }
    routes = {
        "scope-management": "full_plan",
        "schedule-management": "full_plan",
        "cost-management": "full_plan",
    }
    is_non_stub = {p: True for p in dag}

    # Upstream has no approval record -> PENDING_UPSTREAM
    rec_sched = make_record("schedule-management", H_SCHED, {"scope-management": H_SCOPE})
    rec_cost = make_record("cost-management", H_COST, {"schedule-management": H_SCHED})
    curr_hashes = {
        "scope-management": H_SCOPE,
        "schedule-management": H_SCHED,
        "cost-management": H_COST,
    }
    approvals_pending = {
        # scope-management has NO record
        "schedule-management": rec_sched,
        "cost-management": rec_cost,
    }
    res_cost = check_plan_freshness("cost-management", dag, routes, curr_hashes, is_non_stub, approvals_pending)
    assert res_cost == Freshness(False, "PENDING_UPSTREAM_scope-management", "scope-management")

    # Upstream was modified -> TRANSITIVE_STALE_FROM_<offending>
    rec_scope = make_record("scope-management", H_SCOPE, {})
    approvals_stale = {
        "scope-management": rec_scope,
        "schedule-management": rec_sched,
        "cost-management": rec_cost,
    }
    curr_hashes_modified = {
        "scope-management": H_SCOPE_2,  # Scope modified!
        "schedule-management": H_SCHED,
        "cost-management": H_COST,
    }
    res_cost_stale = check_plan_freshness("cost-management", dag, routes, curr_hashes_modified, is_non_stub, approvals_stale)
    # Schedule recorded H_SCOPE, but current is H_SCOPE_2 -> Schedule gives STALE_DEPENDENCY_scope-management
    # Cost receives that and transforms to TRANSITIVE_STALE_FROM_scope-management!
    assert res_cost_stale == Freshness(False, "TRANSITIVE_STALE_FROM_scope-management", "scope-management")


def test_ac8_pure_and_safe_cycles_and_diamonds():
    # Diamond graph:
    # plan-a -> plan-b, plan-a -> plan-c, plan-b -> plan-d, plan-c -> plan-d
    dag_diamond = {
        "plan-a": (),
        "plan-b": ("plan-a",),
        "plan-c": ("plan-a",),
        "plan-d": ("plan-b", "plan-c"),
    }
    routes = {k: "full_plan" for k in dag_diamond}
    hashes = {k: f"{ord(k[-1]):02x}" * 32 for k in dag_diamond}
    is_non_stub = {k: True for k in dag_diamond}
    approvals = {
        "plan-a": make_record("plan-a", hashes["plan-a"], {}),
        "plan-b": make_record("plan-b", hashes["plan-b"], {"plan-a": hashes["plan-a"]}),
        "plan-c": make_record("plan-c", hashes["plan-c"], {"plan-a": hashes["plan-a"]}),
        "plan-d": make_record("plan-d", hashes["plan-d"], {"plan-b": hashes["plan-b"], "plan-c": hashes["plan-c"]}),
    }

    # Diamond evaluates cleanly without false cycle detection
    res = check_plan_freshness("plan-d", dag_diamond, routes, hashes, is_non_stub, approvals)
    assert res == Freshness(True, "APPROVED_AND_FRESH", None)

    # Repeated calls are equal (purity & idempotence)
    res2 = check_plan_freshness("plan-d", dag_diamond, routes, hashes, is_non_stub, approvals)
    assert res == res2

    # Cycle detection
    dag_cycle = {
        "plan-a": ("plan-b",),
        "plan-b": ("plan-a",),
    }
    routes_c = {"plan-a": "full_plan", "plan-b": "full_plan"}
    hashes_c = {"plan-a": hashes["plan-a"], "plan-b": hashes["plan-b"]}
    app_c = {
        "plan-a": make_record("plan-a", hashes["plan-a"], {"plan-b": hashes["plan-b"]}),
        "plan-b": make_record("plan-b", hashes["plan-b"], {"plan-a": hashes["plan-a"]}),
    }
    with pytest.raises(CyclicDependencyError, match="Cycle detected"):
        check_plan_freshness("plan-a", dag_cycle, routes_c, hashes_c, is_non_stub, app_c)
