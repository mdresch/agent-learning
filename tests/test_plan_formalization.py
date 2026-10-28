"""Contract tests for Story 13.7 — Formalization and the Package Contract.

Story 13.7 (docs/user-stories/epic-13-subsidiary-plan-approval-gates-before-pmp-formalization.md)
ADR-013 section 4.7 and ADR-034 sections 4.2.5 and 4.3 (docs/adr/)
BRD-013 BRU-013-07 (docs/project-docs/Business-Requirements/)
FDD-013 sections 3.7 and 6 (docs/project-docs/Functional-Design/)
"""

import ast
from pathlib import Path
import pytest

from agent_learning.pmbok import (
    APPROVAL_ACTIONS,
    Blocker,
    CyclicDependencyError,
    DISPOSITIONS,
    DRAFT_ORDER,
    FEEDBACK_STATUSES,
    FormalizationCheck,
    Freshness,
    GATE_CRITERIA,
    PLACEHOLDER_TOKENS,
    PLAN_DAG,
    PlanApprovalRecord,
    PlanState,
    PROVISIONAL_TOKENS,
    VOLATILE_KEYS,
    approval_record,
    build_approval_metadata,
    check_formalization,
    check_plan_freshness,
    compute_canonical_plan_hash,
    derive_plan_state,
    effective_upstreams,
    gate_constraint_results,
    integrity_flags,
    is_raw_hash,
    latest_approvals,
    plan_hash,
    raw_change_hash,
    topological_order,
    validate_dependencies,
)
import agent_learning


def test_ac0_ready_all_approved_and_satisfied():
    # Setup all 9 plans in DRAFT_ORDER:
    # 3 full_plan (APPROVED), 3 pmp_section (ok=True), 3 not_applicable (rationale=True)
    routes = {
        "scope-management": "full_plan",
        "schedule-management": "full_plan",
        "cost-management": "full_plan",
        "quality-management": "pmp_section",
        "resource-management": "pmp_section",
        "communications-management": "pmp_section",
        "risk-management": "not_applicable",
        "procurement-management": "not_applicable",
        "stakeholder-engagement": "not_applicable",
    }
    states = {
        "scope-management": PlanState.APPROVED,
        "schedule-management": PlanState.APPROVED,
        "cost-management": PlanState.APPROVED,
    }
    section_ok = {
        "quality-management": True,
        "resource-management": True,
        "communications-management": True,
    }
    rationale_recorded = {
        "risk-management": True,
        "procurement-management": True,
        "stakeholder-engagement": True,
    }

    res = check_formalization(
        routes,
        states,
        section_ok=section_ok,
        rationale_recorded=rationale_recorded,
    )
    assert res == FormalizationCheck(ready=True, blockers=())


def test_ac1_route_conditions_blockers():
    routes = {
        "scope-management": "full_plan",
        "schedule-management": "full_plan",
        "cost-management": "pmp_section",
        "quality-management": "not_applicable",
    }
    # Remaining 5 plans will be tested under AC2 / NO_ROUTE
    # But let's fill remaining as valid so we test AC1 conditions specifically:
    for p in DRAFT_ORDER[4:]:
        routes[p] = "not_applicable"
    rationale_recorded = {p: True for p in DRAFT_ORDER[4:]}

    # 1. full_plan in any state but APPROVED -> PLAN_<STATE>
    states = {
        "scope-management": PlanState.STALE_DEPENDENCY,
        # schedule-management is omitted from states -> NO_STATE
    }
    section_ok = {"cost-management": False}  # section not ok -> SECTION_MISSING_OR_STUB
    rationale_recorded["quality-management"] = False  # unrationalized omission -> NO_OMISSION_RATIONALE

    res = check_formalization(
        routes,
        states,
        section_ok=section_ok,
        rationale_recorded=rationale_recorded,
    )
    assert res.ready is False
    assert len(res.blockers) == 4
    assert res.blockers[0] == Blocker("scope-management", "full_plan", "PLAN_STALE_DEPENDENCY")
    assert res.blockers[1] == Blocker("schedule-management", "full_plan", "NO_STATE")
    assert res.blockers[2] == Blocker("cost-management", "pmp_section", "SECTION_MISSING_OR_STUB")
    assert res.blockers[3] == Blocker("quality-management", "not_applicable", "NO_OMISSION_RATIONALE")


def test_ac2_routes_validation():
    routes = {
        # scope-management is missing -> NO_ROUTE
        "schedule-management": "custom_unsupported_route",  # INVALID_ROUTE
        "cost-management": "full_plan",
        "unknown-extra-plan": "full_plan",  # Outside DRAFT_ORDER -> IGNORED
    }
    for p in DRAFT_ORDER[3:]:
        routes[p] = "not_applicable"

    states = {"cost-management": PlanState.APPROVED}
    section_ok = {}
    rationale_recorded = {p: True for p in DRAFT_ORDER[3:]}

    res = check_formalization(
        routes,
        states,
        section_ok=section_ok,
        rationale_recorded=rationale_recorded,
    )
    assert res.ready is False
    assert len(res.blockers) == 2
    assert res.blockers[0] == Blocker("scope-management", "", "NO_ROUTE")
    assert res.blockers[1] == Blocker("schedule-management", "custom_unsupported_route", "INVALID_ROUTE")


def test_ac3_attribution_and_draft_order():
    # Make every plan have a blocker, and verify they come in exact DRAFT_ORDER
    routes = {p: "full_plan" for p in DRAFT_ORDER}
    states = {p: PlanState.DRAFTED for p in DRAFT_ORDER}

    res = check_formalization(routes, states, section_ok={}, rationale_recorded={})
    assert res.ready is False
    assert len(res.blockers) == len(DRAFT_ORDER)
    for blocker, expected_plan in zip(res.blockers, DRAFT_ORDER):
        assert blocker.plan_id == expected_plan
        assert blocker.route == "full_plan"
        assert blocker.reason == "PLAN_DRAFTED"


def test_ac4_end_to_end_scenario():
    # End-to-end scenario over 3 core plans:
    # scope-management, schedule-management, cost-management
    # Other 6 plans set to not_applicable with rationale_recorded=True
    core_dag = {
        "scope-management": (),
        "schedule-management": ("scope-management",),
        "cost-management": ("schedule-management",),
    }
    routes = {p: "not_applicable" for p in DRAFT_ORDER}
    routes["scope-management"] = "full_plan"
    routes["schedule-management"] = "full_plan"
    routes["cost-management"] = "full_plan"

    rationale_recorded = {p: True for p in DRAFT_ORDER if routes[p] == "not_applicable"}
    section_ok = {}

    # Initial plan texts
    scope_text = (
        "---\n"
        "plan_id: scope-management\n"
        "plan_name: \"Scope Management Plan\"\n"
        "version: \"1.0.0\"\n"
        "---\n"
        "# Scope Management Plan\n"
        "Scope description v1.\n"
    )
    sched_text = (
        "---\n"
        "plan_id: schedule-management\n"
        "plan_name: \"Schedule Management Plan\"\n"
        "version: \"1.0.0\"\n"
        "---\n"
        "# Schedule Management Plan\n"
        "Schedule description v1.\n"
    )
    cost_text = (
        "---\n"
        "plan_id: cost-management\n"
        "plan_name: \"Cost Management Plan\"\n"
        "version: \"1.0.0\"\n"
        "---\n"
        "# Cost Management Plan\n"
        "Cost description v1.\n"
    )

    h_scope_1 = compute_canonical_plan_hash(scope_text)
    h_sched_1 = compute_canonical_plan_hash(sched_text)
    h_cost_1 = compute_canonical_plan_hash(cost_text)

    # 1. Build approvals for all 3
    rec_scope_1 = approval_record("approve_plan", build_approval_metadata(
        plan_id="scope-management",
        canonical_content_hash=h_scope_1,
        upstream_hashes={},
        decision_disposition="accepted",
        feedback_status="accepted",
        run_id="run-001",
        sequence_number=1,
    ), "2026-10-28T12:00:00Z")

    rec_sched_1 = approval_record("approve_plan", build_approval_metadata(
        plan_id="schedule-management",
        canonical_content_hash=h_sched_1,
        upstream_hashes={"scope-management": h_scope_1},
        decision_disposition="accepted",
        feedback_status="accepted",
        run_id="run-001",
        sequence_number=1,
    ), "2026-10-28T12:01:00Z")

    rec_cost_1 = approval_record("approve_plan", build_approval_metadata(
        plan_id="cost-management",
        canonical_content_hash=h_cost_1,
        upstream_hashes={"schedule-management": h_sched_1},
        decision_disposition="accepted",
        feedback_status="accepted",
        run_id="run-001",
        sequence_number=1,
    ), "2026-10-28T12:02:00Z")

    approvals = latest_approvals([rec_scope_1, rec_sched_1, rec_cost_1])
    current_hashes = {
        "scope-management": h_scope_1,
        "schedule-management": h_sched_1,
        "cost-management": h_cost_1,
    }
    is_non_stub = {p: True for p in core_dag}

    # Freshness
    fresh_scope = check_plan_freshness("scope-management", core_dag, routes, current_hashes, is_non_stub, approvals)
    fresh_sched = check_plan_freshness("schedule-management", core_dag, routes, current_hashes, is_non_stub, approvals)
    fresh_cost = check_plan_freshness("cost-management", core_dag, routes, current_hashes, is_non_stub, approvals)

    assert fresh_scope.fresh and fresh_sched.fresh and fresh_cost.fresh

    # States
    states = {
        "scope-management": derive_plan_state(exists=True, current_hash=h_scope_1, latest=approvals["scope-management"], freshness=fresh_scope),
        "schedule-management": derive_plan_state(exists=True, current_hash=h_sched_1, latest=approvals["schedule-management"], freshness=fresh_sched),
        "cost-management": derive_plan_state(exists=True, current_hash=h_cost_1, latest=approvals["cost-management"], freshness=fresh_cost),
    }

    # Check formalization: ready!
    f_check = check_formalization(routes, states, section_ok=section_ok, rationale_recorded=rationale_recorded)
    assert f_check.ready is True
    assert f_check.blockers == ()

    # 2. Scope is edited on disk
    scope_text_v2 = scope_text + "\nAdditional Scope requirements.\n"
    h_scope_2 = compute_canonical_plan_hash(scope_text_v2)
    current_hashes["scope-management"] = h_scope_2

    # Re-evaluate freshness & states
    fresh_scope_2 = check_plan_freshness("scope-management", core_dag, routes, current_hashes, is_non_stub, approvals)
    fresh_sched_2 = check_plan_freshness("schedule-management", core_dag, routes, current_hashes, is_non_stub, approvals)
    fresh_cost_2 = check_plan_freshness("cost-management", core_dag, routes, current_hashes, is_non_stub, approvals)

    states_2 = {
        "scope-management": derive_plan_state(exists=True, current_hash=h_scope_2, latest=approvals["scope-management"], freshness=fresh_scope_2),
        "schedule-management": derive_plan_state(exists=True, current_hash=h_sched_1, latest=approvals["schedule-management"], freshness=fresh_sched_2),
        "cost-management": derive_plan_state(exists=True, current_hash=h_cost_1, latest=approvals["cost-management"], freshness=fresh_cost_2),
    }

    assert states_2["scope-management"] == PlanState.REAPPROVAL_REQUIRED
    assert states_2["schedule-management"] == PlanState.STALE_DEPENDENCY
    assert states_2["cost-management"] == PlanState.STALE_DEPENDENCY

    f_check_2 = check_formalization(routes, states_2, section_ok=section_ok, rationale_recorded=rationale_recorded)
    assert f_check_2.ready is False
    assert len(f_check_2.blockers) == 3
    assert f_check_2.blockers[0] == Blocker("scope-management", "full_plan", "PLAN_REAPPROVAL_REQUIRED")
    assert f_check_2.blockers[1] == Blocker("schedule-management", "full_plan", "PLAN_STALE_DEPENDENCY")
    assert f_check_2.blockers[2] == Blocker("cost-management", "full_plan", "PLAN_STALE_DEPENDENCY")

    # 3. Re-approve Scope, Schedule, Cost in topological order
    rec_scope_2 = approval_record("approve_plan", build_approval_metadata(
        plan_id="scope-management",
        canonical_content_hash=h_scope_2,
        upstream_hashes={},
        decision_disposition="accepted",
        feedback_status="accepted",
        run_id="run-002",
        sequence_number=2,
    ), "2026-10-28T14:00:00Z")

    rec_sched_2 = approval_record("approve_plan", build_approval_metadata(
        plan_id="schedule-management",
        canonical_content_hash=h_sched_1,
        upstream_hashes={"scope-management": h_scope_2},
        decision_disposition="accepted",
        feedback_status="accepted",
        run_id="run-002",
        sequence_number=2,
    ), "2026-10-28T14:01:00Z")

    rec_cost_2 = approval_record("approve_plan", build_approval_metadata(
        plan_id="cost-management",
        canonical_content_hash=h_cost_1,
        upstream_hashes={"schedule-management": h_sched_1},
        decision_disposition="accepted",
        feedback_status="accepted",
        run_id="run-002",
        sequence_number=2,
    ), "2026-10-28T14:02:00Z")

    approvals_3 = latest_approvals([
        rec_scope_1, rec_sched_1, rec_cost_1,
        rec_scope_2, rec_sched_2, rec_cost_2,
    ])

    fresh_scope_3 = check_plan_freshness("scope-management", core_dag, routes, current_hashes, is_non_stub, approvals_3)
    fresh_sched_3 = check_plan_freshness("schedule-management", core_dag, routes, current_hashes, is_non_stub, approvals_3)
    fresh_cost_3 = check_plan_freshness("cost-management", core_dag, routes, current_hashes, is_non_stub, approvals_3)

    states_3 = {
        "scope-management": derive_plan_state(exists=True, current_hash=h_scope_2, latest=approvals_3["scope-management"], freshness=fresh_scope_3),
        "schedule-management": derive_plan_state(exists=True, current_hash=h_sched_1, latest=approvals_3["schedule-management"], freshness=fresh_sched_3),
        "cost-management": derive_plan_state(exists=True, current_hash=h_cost_1, latest=approvals_3["cost-management"], freshness=fresh_cost_3),
    }

    f_check_3 = check_formalization(routes, states_3, section_ok=section_ok, rationale_recorded=rationale_recorded)
    assert f_check_3.ready is True
    assert f_check_3.blockers == ()


def test_ac5_purity_and_package_exports():
    # AST inspection of pure modules
    pmbok_dir = Path("src/agent_learning/pmbok")
    allowed_internal = {"parser", "standards", "tailoring", "hashing", "integrity", "governance", "lint"}

    for filename in ("hashing.py", "integrity.py", "governance.py"):
        filepath = pmbok_dir / filename
        tree = ast.parse(filepath.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod = alias.name.split(".")[0]
                    # Must be stdlib: not storage, not legacy pmbok, not 3rd party
                    assert mod not in ("storage", "pmbok", "requests", "pydantic", "fastapi")
            elif isinstance(node, ast.ImportFrom):
                if node.level > 0:
                    # relative import to sibling
                    if node.module:
                        assert node.module in allowed_internal
                else:
                    if node.module:
                        mod = node.module.split(".")[0]
                        assert mod not in ("storage", "pmbok", "agent_learning.storage")

    # Verify every public symbol of Epic 13 is exported at both package and root level
    epic_13_symbols = [
        "compute_canonical_plan_hash",
        "raw_change_hash",
        "is_raw_hash",
        "plan_hash",
        "VOLATILE_KEYS",
        "PLACEHOLDER_TOKENS",
        "PROVISIONAL_TOKENS",
        "APPROVAL_ACTIONS",
        "DISPOSITIONS",
        "FEEDBACK_STATUSES",
        "GATE_CRITERIA",
        "DRAFT_ORDER",
        "PLAN_DAG",
        "integrity_flags",
        "gate_constraint_results",
        "PlanApprovalRecord",
        "build_approval_metadata",
        "approval_record",
        "latest_approvals",
        "CyclicDependencyError",
        "Freshness",
        "PlanState",
        "Blocker",
        "FormalizationCheck",
        "effective_upstreams",
        "topological_order",
        "validate_dependencies",
        "check_plan_freshness",
        "derive_plan_state",
        "check_formalization",
    ]

    for sym in epic_13_symbols:
        assert hasattr(agent_learning.pmbok, sym), f"agent_learning.pmbok missing {sym}"
        assert sym in agent_learning.pmbok.__all__, f"agent_learning.pmbok.__all__ missing {sym}"
        assert hasattr(agent_learning, sym), f"agent_learning root missing {sym}"
        assert sym in agent_learning.__all__, f"agent_learning.__all__ missing {sym}"
