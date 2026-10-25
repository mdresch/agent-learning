"""
Pydantic data models for PMBOK 8 Stage 18: Intent Refinement.
Grounded in ADR-009, PMBOK Process 4.7 (Close Project or Phase), and double-loop cybernetic feedback.
"""

from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import AliasChoices, BaseModel, Field, model_validator


class HypothesisTerminalStatus(str, Enum):
    VALIDATED = "validated"
    REFUTED = "refuted"
    REFINED = "refined"


class MeasurementHorizon(str, Enum):
    IMMEDIATE = "immediate"       # Observed directly via telemetry at phase cutoff
    PROVISIONAL = "provisional"   # Early directional signal; final outcome pending
    DEFERRED = "deferred"         # Long-term lagging indicator (requires operational soak)


class OutcomeDeltaItem(BaseModel):
    objective_id: str
    target_metric_stage_4: str
    actual_metric_stage_12: str
    variance_percentage: float
    measurement_horizon: MeasurementHorizon
    deferred_audit_due_date: Optional[str] = None
    causal_factors: List[str]
    strategic_directive: str


class HypothesisResolutionItem(BaseModel):
    hypothesis_id: str
    statement: str
    terminal_status: HypothesisTerminalStatus
    recurrence_depth: int = Field(default=0, ge=0, le=2)
    bayes_factor: Optional[float] = None
    evidence_references: List[str]
    promotion_target: Optional[str] = None  # e.g., "Architecture Invariant #7" or "HYP-001.1"
    rationale: str

    @model_validator(mode="after")
    def validate_exhaustion_collapse(self) -> "HypothesisResolutionItem":
        # Invariant 11: on the 3rd cycle (d=2), REFINED is prohibited
        if self.recurrence_depth >= 2 and self.terminal_status == HypothesisTerminalStatus.REFINED:
            raise ValueError(
                f"Hypothesis '{self.hypothesis_id}' reached recurrence depth {self.recurrence_depth}. "
                "At d_max=2, REFINED is prohibited: must collapse to VALIDATED (BF10 >= 10) "
                "or default to REFUTED (BF10 < 10)."
            )
        return self


class SparkDirectiveItem(BaseModel):
    directive_id: str
    title: str
    action_type: str  # "expand_capability" | "retire_component" | "pivot_architecture"
    target_stage_1_spark: str


class CumulativeLineageKernel(BaseModel):
    root_spark: str
    parent_refinement: Optional[str] = None
    generational_index: int = Field(..., ge=1)
    immutable_core_invariants: List[str]
    accumulated_knowledge_hash: str


class IntentRefinementProposalPayload(BaseModel):
    refinement_id: str = Field(..., pattern=r"^IR-PROP-v\d+\.\d+\.\d+$")
    pmp_baseline: str = Field(
        ...,
        pattern=r"^PMP-BL-v\d+\.\d+\.\d+$",
        validation_alias=AliasChoices("pmp_baseline", "pmp_baseline_id"),
    )
    readiness_audit_ref: str
    disposition_type: Literal["phase_handoff", "project_termination"] = "phase_handoff"
    lifecycle_stage: str = "Stage 18 (Intent Refinement)"
    governance_policy: str = "approve-intent-refinement"
    executive_summary: str
    outcome_deltas: List[OutcomeDeltaItem]
    hypothesis_resolutions: List[HypothesisResolutionItem]
    strategic_pivots: List[str]
    phase_next_spark_directives: List[SparkDirectiveItem] = Field(default_factory=list)
    lineage: CumulativeLineageKernel
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_disposition_directives(self) -> "IntentRefinementProposalPayload":
        if self.disposition_type == "phase_handoff" and not self.phase_next_spark_directives:
            raise ValueError(
                "phase_next_spark_directives must be non-empty when disposition_type is 'phase_handoff'."
            )
        if self.disposition_type == "project_termination" and self.phase_next_spark_directives:
            raise ValueError(
                "phase_next_spark_directives must be empty when disposition_type is 'project_termination'."
            )
        return self


class ReadinessPreconditionError(Exception):
    """Raised when Stage 18 Intent Refinement entry preconditions fail."""
    pass


class ReadinessAuditResult(BaseModel):
    audit_ref: str
    is_ready: bool
    verified_at: str
    deliverables_accepted: int
    open_findings_count: int
    crystallized_lessons_count: int


def evaluate_phase_close_readiness(
    deliverables: List[Dict[str, Any]],
    audit_records: List[Dict[str, Any]],
    lessons_learned: List[Dict[str, Any]],
) -> ReadinessAuditResult:
    """
    Validates preconditions for entering Stage 18 Intent Refinement under PMBOK 8 Process 4.7.
    - All Stage 9 deliverables must be accepted.
    - Stage 11 audit records must have zero unresolved non-conformances.
    - Stage 15 lessons learned must be crystallized.
    """
    import hashlib
    from datetime import datetime, timezone

    unaccepted = [
        d.get("deliverable_id", d.get("name", "unknown"))
        for d in deliverables
        if d.get("status") != "accepted"
    ]
    if unaccepted:
        raise ReadinessPreconditionError(
            f"Stage 9 deliverables incomplete: {', '.join(unaccepted)} are not accepted."
        )

    open_findings = sum(
        rec.get("non_conformance_count", 0)
        for rec in audit_records
        if rec.get("status") != "cleared" or rec.get("non_conformance_count", 0) > 0
    )
    if open_findings > 0:
        raise ReadinessPreconditionError(
            f"Stage 11 audit has unresolved non-conformances: {open_findings} finding(s) pending."
        )

    if not lessons_learned or any(not l.get("crystallized", False) for l in lessons_learned):
        raise ReadinessPreconditionError(
            "Stage 15 lessons learned uncrystallized: all lessons must be marked crystallized before phase close."
        )

    now_iso = datetime.now(timezone.utc).isoformat()
    audit_hash = hashlib.sha256(f"{now_iso}-{len(deliverables)}".encode()).hexdigest()[:8]
    audit_ref = f"AUD-CLOSE-{audit_hash.upper()}"

    return ReadinessAuditResult(
        audit_ref=audit_ref,
        is_ready=True,
        verified_at=now_iso,
        deliverables_accepted=len(deliverables),
        open_findings_count=0,
        crystallized_lessons_count=len(lessons_learned),
    )

