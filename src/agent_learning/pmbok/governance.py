"""Plan governance models, approval records, freshness, and lifecycle state (ADR-013, ADR-034, FDD-013 section 3).

Pure: standard library only, no storage and no I/O.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, NamedTuple

from .standards import (
    APPROVAL_ACTIONS,
    DISPOSITIONS,
    DRAFT_ORDER,
    FEEDBACK_STATUSES,
    ROUTES,
)

_KEBAB = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_MAX_STRING_LEN = 256
_REQUIRED_METADATA_KEYS = (
    "plan_id",
    "canonical_content_hash",
    "upstream_hashes",
    "decision_disposition",
    "feedback_status",
    "run_id",
    "sequence_number",
)


@dataclass(frozen=True)
class PlanApprovalRecord:
    """The reader's view of one gate Episode (FDD-013 section 2)."""

    plan_id: str
    canonical_content_hash: str
    action_id: str
    decision_disposition: str
    feedback_status: str
    upstream_hashes: Mapping[str, str]
    sequence_number: int
    created_at: str


class CyclicDependencyError(Exception):
    """Raised when a dependency cycle is detected in a planning graph."""


class Freshness(NamedTuple):
    """Outcome of checking a plan's freshness against its dependencies (FDD-013 section 3.5)."""

    fresh: bool
    reason: str
    offending: str | None


class PlanState(str, Enum):
    """The governance lifecycle states of a subsidiary management plan (FDD-013 section 2)."""

    NOT_STARTED = "not_started"
    DRAFTED = "drafted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REVISION_REQUESTED = "revision_requested"
    REJECTED = "rejected"
    STALE_DEPENDENCY = "stale_dependency"
    PENDING_UPSTREAM = "pending_upstream"
    REAPPROVAL_REQUIRED = "reapproval_required"
    INVALID_METADATA = "invalid_metadata"


@dataclass(frozen=True)
class Blocker:
    """A condition blocking PMP formalization (FDD-013 section 2)."""

    plan_id: str
    route: str
    reason: str


@dataclass(frozen=True)
class FormalizationCheck:
    """The outcome of verifying preconditions for PMP formalization (FDD-013 section 2)."""

    ready: bool
    blockers: tuple[Blocker, ...]


def _validate_str(key: str, val: Any, *, allow_empty: bool = False) -> str:
    if not isinstance(val, str):
        raise ValueError(f"{key} must be a str, got {type(val).__name__}")
    if len(val) > _MAX_STRING_LEN:
        raise ValueError(f"{key} exceeds maximum length of {_MAX_STRING_LEN} characters")
    if not allow_empty and val.strip() == "":
        raise ValueError(f"{key} must not be empty")
    return val


def _validate_plan_id(plan_id: Any) -> str:
    s = _validate_str("plan_id", plan_id)
    if not _KEBAB.fullmatch(s):
        raise ValueError(f"plan_id {s!r} must be a kebab-case identifier")
    return s


def _validate_hash(key: str, hash_val: Any) -> str:
    s = _validate_str(key, hash_val)
    if not _HEX64.fullmatch(s):
        raise ValueError(f"{key} must be 64 lowercase hex characters, got {s!r}")
    return s


def _validate_sequence_number(val: Any) -> int:
    if isinstance(val, bool) or not isinstance(val, int):
        raise ValueError(f"sequence_number must be an integer, got {type(val).__name__}")
    if val < 0:
        raise ValueError(f"sequence_number must be non-negative, got {val}")
    return val


def _validate_upstream_hashes(val: Any) -> dict[str, str]:
    if not isinstance(val, Mapping):
        raise ValueError(f"upstream_hashes must be a mapping, got {type(val).__name__}")
    cleaned: dict[str, str] = {}
    for k, v in val.items():
        k_str = _validate_str("upstream_hashes key", k)
        if not _KEBAB.fullmatch(k_str):
            raise ValueError(f"upstream_hashes key {k_str!r} must be kebab-case")
        v_str = _validate_str(f"upstream_hashes[{k_str}]", v)
        if not _HEX64.fullmatch(v_str):
            raise ValueError(f"upstream_hashes value for {k_str!r} must be 64 lowercase hex characters")
        cleaned[k_str] = v_str
    return cleaned


def build_approval_metadata(
    *,
    plan_id: str,
    canonical_content_hash: str,
    upstream_hashes: Mapping[str, str],
    decision_disposition: str,
    feedback_status: str,
    run_id: str,
    sequence_number: int,
) -> dict[str, Any]:
    """Construct and validate metadata for an approval Episode (ADR-034 section 4.2.1; FDD-013 section 3.3).

    Returns exactly the 7 contract keys and no others.
    """
    v_plan_id = _validate_plan_id(plan_id)
    v_hash = _validate_hash("canonical_content_hash", canonical_content_hash)
    v_upstreams = _validate_upstream_hashes(upstream_hashes)

    _validate_str("decision_disposition", decision_disposition)
    if decision_disposition not in DISPOSITIONS:
        raise ValueError(f"decision_disposition must be one of {DISPOSITIONS}, got {decision_disposition!r}")

    _validate_str("feedback_status", feedback_status)
    if feedback_status not in FEEDBACK_STATUSES:
        raise ValueError(f"feedback_status must be one of {FEEDBACK_STATUSES}, got {feedback_status!r}")

    v_run_id = _validate_str("run_id", run_id)
    v_seq = _validate_sequence_number(sequence_number)

    return {
        "plan_id": v_plan_id,
        "canonical_content_hash": v_hash,
        "upstream_hashes": v_upstreams,
        "decision_disposition": decision_disposition,
        "feedback_status": feedback_status,
        "run_id": v_run_id,
        "sequence_number": v_seq,
    }


def approval_record(
    action_id: str,
    metadata: Mapping[str, Any],
    created_at: str,
) -> PlanApprovalRecord:
    """Read back and validate a PlanApprovalRecord from action_id, metadata, and created_at.

    Ignores extra keys in metadata; validates contract keys against the normative schema.
    """
    _validate_str("action_id", action_id)
    if action_id not in APPROVAL_ACTIONS:
        raise ValueError(f"action_id must be one of {APPROVAL_ACTIONS}, got {action_id!r}")

    v_created_at = _validate_str("created_at", created_at)

    if not isinstance(metadata, Mapping):
        raise ValueError(f"metadata must be a mapping, got {type(metadata).__name__}")

    for k in _REQUIRED_METADATA_KEYS:
        if k not in metadata:
            raise ValueError(f"missing required metadata key {k!r}")

    v_plan_id = _validate_plan_id(metadata["plan_id"])
    v_hash = _validate_hash("canonical_content_hash", metadata["canonical_content_hash"])
    v_upstreams = _validate_upstream_hashes(metadata["upstream_hashes"])

    disp = metadata["decision_disposition"]
    _validate_str("decision_disposition", disp)
    if disp not in DISPOSITIONS:
        raise ValueError(f"decision_disposition must be one of {DISPOSITIONS}, got {disp!r}")

    feed = metadata["feedback_status"]
    _validate_str("feedback_status", feed)
    if feed not in FEEDBACK_STATUSES:
        raise ValueError(f"feedback_status must be one of {FEEDBACK_STATUSES}, got {feed!r}")

    v_run_id = _validate_str("run_id", metadata["run_id"])
    v_seq = _validate_sequence_number(metadata["sequence_number"])

    return PlanApprovalRecord(
        plan_id=v_plan_id,
        canonical_content_hash=v_hash,
        action_id=action_id,
        decision_disposition=disp,
        feedback_status=feed,
        upstream_hashes=MappingProxyType(v_upstreams),
        sequence_number=v_seq,
        created_at=v_created_at,
    )


def latest_approvals(records: Sequence[PlanApprovalRecord]) -> dict[str, PlanApprovalRecord]:
    """Keep, per plan, the record with the highest (sequence_number, created_at).

    Pure: does not mutate the input sequence.
    """
    if not isinstance(records, (list, tuple)):
        raise TypeError(f"records must be a sequence of PlanApprovalRecord, got {type(records).__name__}")

    result: dict[str, PlanApprovalRecord] = {}
    for rec in records:
        if not isinstance(rec, PlanApprovalRecord):
            raise TypeError(f"item in records must be a PlanApprovalRecord, got {type(rec).__name__}")
        current = result.get(rec.plan_id)
        if current is None or (rec.sequence_number, rec.created_at) > (current.sequence_number, current.created_at):
            result[rec.plan_id] = rec

    return result



def effective_upstreams(
    plan_id: str,
    dag: Mapping[str, Sequence[str]],
    routes: Mapping[str, Any],
    active_stack: set[str] | None = None,
) -> list[str]:
    """Recursively resolves active ancestor dependencies by bypassing not_applicable nodes (ADR-034; FDD-013 section 3.4).

    A not_applicable upstream is replaced by its own effective upstreams, recursively;
    the result is sorted and without duplicates; a missing route means full_plan;
    a cycle on the active path raises CyclicDependencyError.
    """
    if active_stack is None:
        active_stack = set()

    if plan_id in active_stack:
        raise CyclicDependencyError(f"Cycle detected resolving effective upstreams at {plan_id}")

    active_stack.add(plan_id)
    try:
        effective: list[str] = []
        for upstream_id in dag.get(plan_id, ()):
            route_val = routes.get(upstream_id, "full_plan")
            route_str = getattr(route_val, "value", route_val)
            if route_str == "not_applicable":
                effective.extend(effective_upstreams(upstream_id, dag, routes, active_stack))
            else:
                effective.append(upstream_id)

        return sorted(set(effective))
    finally:
        active_stack.remove(plan_id)


def topological_order(dag: Mapping[str, Sequence[str]]) -> tuple[str, ...]:
    """Return a topological sort of the graph with dependencies first (FDD-013 section 3.4).

    Ties broken by position in DRAFT_ORDER, then by name;
    a cycle raises CyclicDependencyError;
    an edge to a plan that is not a key of dag raises ValueError.
    """
    if not isinstance(dag, Mapping):
        raise TypeError(f"dag must be a mapping, got {type(dag).__name__}")

    # Validate that every edge points to a key in dag
    for node, deps in dag.items():
        for dep in deps:
            if dep not in dag:
                raise ValueError(f"node {node!r} depends on {dep!r} which is not a key in dag")

    remaining_deps: dict[str, set[str]] = {node: set(deps) for node, deps in dag.items()}
    dependents: dict[str, list[str]] = {node: [] for node in dag}
    for node, deps in dag.items():
        for dep in deps:
            dependents[dep].append(node)

    def tie_key(plan_id: str) -> tuple[int, str]:
        try:
            return (DRAFT_ORDER.index(plan_id), plan_id)
        except ValueError:
            return (len(DRAFT_ORDER), plan_id)

    ready = [node for node, deps in remaining_deps.items() if not deps]
    ready.sort(key=tie_key)

    result: list[str] = []
    while ready:
        curr = ready.pop(0)
        result.append(curr)
        for dep in dependents[curr]:
            remaining_deps[dep].remove(curr)
            if not remaining_deps[dep]:
                ready.append(dep)
                ready.sort(key=tie_key)

    if len(result) < len(dag):
        raise CyclicDependencyError("cycle detected in graph")

    return tuple(result)



def check_plan_freshness(
    plan_id: str,
    dag: Mapping[str, Sequence[str]],
    routes: Mapping[str, Any],
    current_hashes: Mapping[str, str],
    is_non_stub: Mapping[str, bool],
    approvals: Mapping[str, PlanApprovalRecord],
    active_stack: set[str] | None = None,
) -> Freshness:
    """Pure DAG verification asserting that a plan and all its effective ancestors are fresh (FDD-013 section 3.5)."""
    if active_stack is None:
        active_stack = set()
    if plan_id in active_stack:
        raise CyclicDependencyError(f"Cycle detected in causal DAG at {plan_id}")

    active_stack.add(plan_id)
    try:
        route_val = routes.get(plan_id, "full_plan")
        route = getattr(route_val, "value", route_val)

        # 1. Route not_applicable
        if route == "not_applicable":
            return Freshness(True, "NOT_APPLICABLE", None)

        # 2. Route pmp_section
        if route == "pmp_section":
            curr_hash = current_hashes.get(plan_id)
            if not curr_hash or curr_hash.startswith("raw:") or not is_non_stub.get(plan_id, False):
                return Freshness(False, "INVALID_OR_STUB_SECTION", plan_id)

            for upstream_id in effective_upstreams(plan_id, dag, routes):
                up_fresh = check_plan_freshness(
                    upstream_id, dag, routes, current_hashes, is_non_stub, approvals, active_stack
                )
                if not up_fresh.fresh:
                    return up_fresh
            return Freshness(True, "SECTION_FRESH", None)

        # 3. Route full_plan (default for any other route)
        rec = approvals.get(plan_id)
        if rec is None:
            return Freshness(False, "NO_APPROVAL_RECORD", plan_id)

        if rec.action_id != "approve_plan":
            return Freshness(False, f"NOT_APPROVED_{rec.action_id}", plan_id)

        if rec.decision_disposition != "accepted" or rec.feedback_status != "accepted":
            return Freshness(False, "NOT_APPROVED_UNACCEPTED", plan_id)

        curr_hash = current_hashes.get(plan_id)
        if not curr_hash or curr_hash.startswith("raw:"):
            return Freshness(False, "INVALID_METADATA_UNPARSEABLE", plan_id)

        if rec.canonical_content_hash != curr_hash:
            return Freshness(False, "REAPPROVAL_REQUIRED_CONTENT_MODIFIED", plan_id)

        # 4. Check effective upstreams
        for upstream_id in effective_upstreams(plan_id, dag, routes):
            recorded_hash = rec.upstream_hashes.get(upstream_id)
            upstream_curr = current_hashes.get(upstream_id)
            if recorded_hash is None or recorded_hash != upstream_curr:
                return Freshness(False, f"STALE_DEPENDENCY_{upstream_id}", upstream_id)

            up_fresh = check_plan_freshness(
                upstream_id, dag, routes, current_hashes, is_non_stub, approvals, active_stack
            )
            if not up_fresh.fresh:
                offending_plan = up_fresh.offending or upstream_id
                if (
                    up_fresh.reason.startswith("NO_APPROVAL")
                    or up_fresh.reason.startswith("NOT_APPROVED")
                    or up_fresh.reason.startswith("PENDING_UPSTREAM")
                ):
                    return Freshness(False, f"PENDING_UPSTREAM_{offending_plan}", offending_plan)
                else:
                    return Freshness(False, f"TRANSITIVE_STALE_FROM_{offending_plan}", offending_plan)

        # 5. Otherwise fresh
        return Freshness(True, "APPROVED_AND_FRESH", None)
    finally:
        active_stack.remove(plan_id)


def derive_plan_state(
    *,
    exists: bool,
    current_hash: str | None,
    in_flight_hash: str | None = None,
    latest: PlanApprovalRecord | None = None,
    freshness: Freshness | None = None,
) -> PlanState:
    """Derive the governance lifecycle state of a subsidiary plan (FDD-013 section 3.6).

    Precedence order (first match wins):
    1. exists is false: NOT_STARTED
    2. current_hash is missing or raw: INVALID_METADATA
    3. in_flight_hash == current_hash: UNDER_REVIEW
    4. latest exists and its hash != current_hash:
       REAPPROVAL_REQUIRED if latest.action_id == 'approve_plan', else DRAFTED
    5. latest exists and its hash matches:
       If disposition or feedback is not 'accepted': DRAFTED
       If action_id == 'reject_plan': REJECTED
       If action_id == 'request_revision_before_decision': REVISION_REQUESTED
       If action_id == 'approve_plan':
           requires freshness, else ValueError
           fresh -> APPROVED
           reason starts with 'PENDING_UPSTREAM' -> PENDING_UPSTREAM
           else -> STALE_DEPENDENCY
    6. No latest record: DRAFTED
    """
    if not exists:
        return PlanState.NOT_STARTED

    if not current_hash or current_hash.startswith("raw:"):
        return PlanState.INVALID_METADATA

    if in_flight_hash is not None and in_flight_hash == current_hash:
        return PlanState.UNDER_REVIEW

    if latest is not None and latest.canonical_content_hash != current_hash:
        if latest.action_id == "approve_plan":
            return PlanState.REAPPROVAL_REQUIRED
        return PlanState.DRAFTED

    if latest is not None and latest.canonical_content_hash == current_hash:
        if latest.decision_disposition != "accepted" or latest.feedback_status != "accepted":
            return PlanState.DRAFTED
        if latest.action_id == "reject_plan":
            return PlanState.REJECTED
        if latest.action_id == "request_revision_before_decision":
            return PlanState.REVISION_REQUESTED
        if latest.action_id == "approve_plan":
            if freshness is None:
                raise ValueError("freshness is required when latest action is approve_plan matching current hash")
            if freshness.fresh:
                return PlanState.APPROVED
            if freshness.reason.startswith("PENDING_UPSTREAM"):
                return PlanState.PENDING_UPSTREAM
            return PlanState.STALE_DEPENDENCY

    return PlanState.DRAFTED


def check_formalization(
    routes: Mapping[str, Any],
    states: Mapping[str, Any],
    *,
    section_ok: Mapping[str, bool],
    rationale_recorded: Mapping[str, bool],
) -> FormalizationCheck:
    """Precondition check for PMP formalization (FDD-013 section 3.7; BRU-013-07)."""
    blockers: list[Blocker] = []
    for plan in DRAFT_ORDER:
        if plan not in routes or routes[plan] is None:
            blockers.append(Blocker(plan_id=plan, route="", reason="NO_ROUTE"))
            continue

        raw_route = routes[plan]
        route = getattr(raw_route, "value", raw_route)
        if route not in ROUTES:
            blockers.append(Blocker(plan_id=plan, route=str(route), reason="INVALID_ROUTE"))
            continue

        if route == "full_plan":
            state = states.get(plan)
            if state is None:
                blockers.append(Blocker(plan_id=plan, route=route, reason="NO_STATE"))
            else:
                st_val = getattr(state, "value", state)
                if st_val != PlanState.APPROVED.value:
                    st_name = getattr(state, "name", None) or str(st_val).upper()
                    blockers.append(Blocker(plan_id=plan, route=route, reason=f"PLAN_{st_name}"))
        elif route == "pmp_section":
            if not section_ok.get(plan, False):
                blockers.append(Blocker(plan_id=plan, route=route, reason="SECTION_MISSING_OR_STUB"))
        elif route == "not_applicable":
            if not rationale_recorded.get(plan, False):
                blockers.append(Blocker(plan_id=plan, route=route, reason="NO_OMISSION_RATIONALE"))

    return FormalizationCheck(ready=len(blockers) == 0, blockers=tuple(blockers))



