"""
Pydantic data models for PMBOK 8 Stage 18: Intent Refinement.
Grounded in ADR-009, PMBOK Process 4.7 (Close Project or Phase), and double-loop cybernetic feedback.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


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
    pmp_baseline_id: str = Field(..., pattern=r"^PMP-BL-v\d+\.\d+\.\d+$")
    readiness_audit_ref: str
    disposition_type: str = Field(default="phase_handoff", pattern=r"^(phase_handoff|project_termination)$")
    lifecycle_stage: str = "Stage 18 (Intent Refinement)"
    governance_policy: str = "approve-intent-refinement"
    executive_summary: str
    outcome_deltas: List[OutcomeDeltaItem]
    hypothesis_resolutions: List[HypothesisResolutionItem]
    strategic_pivots: List[str]
    phase_next_spark_directives: List[SparkDirectiveItem] = Field(default_factory=list)
    lineage: CumulativeLineageKernel
    metadata: Dict[str, Any] = Field(default_factory=dict)

