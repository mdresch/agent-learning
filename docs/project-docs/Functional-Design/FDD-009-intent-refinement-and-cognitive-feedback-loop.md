# FDD-009: Intent Refinement and Cognitive Feedback Loop

**Source ADR:** [ADR-009](../../adr/ADR-009-intent-refinement-and-cognitive-feedback-loop.md) — Accepted (2026-10-25)  
**Governing Baseline:** `PMP-BL-v1.0.0`  
**Source BRD:** [BRD-009](../Business-Requirements/BRD-009-intent-refinement-and-cognitive-feedback-loop.md)  
**Status:** Accepted — functional design derived from an Accepted ADR and BRD  

---

## 1. System Architecture & Component Interactions

The Intent Refinement architecture closes the developmental feedback loop by synthesizing empirical observations, realized benefits, and crystallized lessons into Phase $N+1$ catalysts or project termination directives under PMBOK 8 Process 4.7 (*Close Project or Phase*):

```
       Stage 12: Actual Outcomes       Stage 15: Lessons Learned
                  │                                │
                  ▼                                ▼
       ┌────────────────────────────────────────────────────────┐
       │             Phase Close Readiness Evaluator            │
       │  (Audit checks: DEL=Accepted, AUD=Clear, KB=Merged)    │
       └──────────────────────────┬─────────────────────────────┘
                                  │
                                  ▼
       ┌────────────────────────────────────────────────────────┐
       │          Intent Refinement Synthesizer Engine          │
       │       (Low-pass filter, Bayes factor evaluator,        │
       │        d_max=2 recurrence depth guard, S3-S4 balance)   │
       └──────────────────────────┬─────────────────────────────┘
                                  │
                                  ▼
       ┌────────────────────────────────────────────────────────┐
       │             Intent-Refinement-Proposal.md              │
       │     (Pydantic: IntentRefinementProposalPayload)        │
       └──────────────────────────┬─────────────────────────────┘
                                  │
                                  ▼
       ┌────────────────────────────────────────────────────────┐
       │        approve-intent-refinement Decision Gate         │
       │         (agent-learning-governance / FULL)             │
       └──────────────────────────┬─────────────────────────────┘
                                  │
                 ┌────────────────┴────────────────┐
                 ▼ (Phase Handoff)                 ▼ (Project Termination)
       ┌────────────────────────┐        ┌────────────────────────┐
       │   scripts/orchestrate  │        │   Decommissioning      │
       │   --mode seed-next     │        │   • Prune worktrees    │
       │   (Phase N+1 Spark)    │        │   • Revoke credentials │
       │                        │        │   • Archive baselines  │
       └────────────────────────┘        └────────────────────────┘
```

---

## 2. Data Contracts & Pydantic Validation Schemas

All intent refinement payloads must adhere to the verified schema in `pmbok.models.intent_refinement`:

```python
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import AliasChoices, BaseModel, Field, model_validator

class HypothesisTerminalStatus(str, Enum):
    VALIDATED = "validated"
    REFUTED = "refuted"
    REFINED = "refined"

class MeasurementHorizon(str, Enum):
    IMMEDIATE = "immediate"
    LAGGING = "lagging"

class OutcomeDeltaItem(BaseModel):
    metric_id: str
    expected_value: float
    observed_value: float
    delta_percentage: float
    horizon: MeasurementHorizon = MeasurementHorizon.IMMEDIATE
    causal_factors: List[str]

class HypothesisResolutionItem(BaseModel):
    hypothesis_id: str
    bayes_factor: float
    recurrence_depth: int = 0
    terminal_status: HypothesisTerminalStatus
    promotion_target: Optional[str] = None
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
    hypothesis_references: List[str]
    proposed_priority: str
    operational_boundaries: List[str]

class CumulativeLineageKernel(BaseModel):
    root_spark_id: str
    parent_refinement_id: Optional[str] = None
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
```

---

## 3. Cybernetic Control & Damping Algorithms

### 3.1 Low-Pass Damping Filter for Outcome Deltas
To avoid erratic strategic pivots driven by transient sprint fluctuations, the synthesizer applies an exponential moving average (EMA) filter across rolling outcome deltas:

$$\mathbf{\Theta}_{N+1} = \beta \mathbf{\Theta}_{N} + (1 - \beta) \nabla_{\text{empirical}} \mathcal{L}(\text{Rolling Outcome Delta})$$

Where $\beta \in [0.6, 0.85]$. For initial generations ($N < 3$), a bias-corrected warmup is computed:

$$\hat{\mathbf{\Theta}}_N = \frac{\mathbf{\Theta}_N}{1 - \beta^N}$$

anchored against the original Stage 4 Business Case target.

### 3.2 Bayes Factor Hypothesis Resolution Protocol
The empirical Bayes factor ($BF_{10}$) compares the probability of observed evidence under hypothesis $H_1$ against the null $H_0$:

$$BF_{10} = \frac{P(\text{Evidence} \mid H_1)}{P(\text{Evidence} \mid H_0)}$$

- **$BF_{10} \ge 10$:** Mandatory resolution as `VALIDATED`. Graduated into an immutable architecture invariant in Phase $N+1$.
- **$BF_{10} \le 0.1$:** Mandatory resolution as `REFUTED`. Permanently retired with negative reinforcement feedback.
- **$0.1 < BF_{10} < 10$:** Inconclusive. Refinement is permitted only if recurrence depth $d < 2$. At $d = 2$, it defaults to `REFUTED` due to budget exhaustion.

---

## 4. Full-Authority Decision Gate: `approve-intent-refinement`

Registered under `agent-learning-governance` with `DecisionAuthority.FULL`:

| Criterion ID | Weight | Minimum Sources | Description |
|---|---|---|---|
| `empirical_grounding` | 0.30 | 1 | Outcome deltas cite verified Stage 12 metrics and Stage 11 audit records. |
| `hypothesis_resolution_completeness` | 0.30 | 1 | 100% of Stage 3 hypotheses resolve to terminal states under $d_{\max}=2$. |
| `strategic_alignment` | 0.20 | 1 | Strategic pivots are damped by the low-pass filter and respect S3–S4 capacity. |
| `spark_actionability` | 0.20 | 1 | Spark directives contain testable hypotheses and operational boundaries. |

**Governance Constraint:** `requires_human_approval: true` is permanently locked. No automated transition to `low` authority is permitted.

---

## 5. CLI Execution & Orchestrator Workflows

### 5.1 Seeding Phase $N+1$
```powershell
python scripts/orchestrate_pmbok.py --mode seed-next \
  --refinement-proposal docs/project-docs/Intent-Refinement-Proposal.md \
  --output-dir docs/phase-next/
```

### 5.2 Administrative Decommissioning
```powershell
python scripts/orchestrate_pmbok.py --mode decommission \
  --refinement-proposal docs/project-docs/Intent-Refinement-Proposal.md \
  --archive-root docs/archive/
```

---

## 6. Error Handling & Guardrails

| Exception | Trigger Condition | System Action |
|---|---|---|
| `ReadinessPreconditionError` | Incomplete deliverables or open non-conformances | Aborts Stage 18 evaluation; returns to Stage 11/17 |
| `HypothesisExhaustionError` | Hypothesis with $d \ge 2$ submitted as `REFINED` | Fails Pydantic validation; requires collapse to `VALIDATED` or `REFUTED` |
| `InvalidDispositionDirectivesError` | Directives present under termination or missing under handoff | Fails validation; requires structural alignment |
| `StrategicWhiplashError` | Proposed pivots exceed $\lceil C_{\text{adapt}} / 2 \rceil$ | Flags S3-S4 homeostatic violation in decision frame |
