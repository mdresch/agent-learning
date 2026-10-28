# ADR 027: Cost Management Plan Standard and Baseline Contract

## 1. Executive Brief
Under **ADR-012** (§4.6), the **Cost Management Plan** is the third Baseline-Substantiating (Plan Tier 1) standard: `5.1 Scope` $\to$ `6.1 Schedule` $\to$ `7.1 Cost`. In PMBOK 8 its primary domain is **Finance**, with **Governance** as secondary domain (ADR-012 §4.4), under the *Planning* Focus Area.

In baseline `PMP-BL-v1.0.0` the Cost plan has no normative standard. This ADR defines what a valid Cost plan must contain for a project funded in stages against a management envelope: the cost categories tracked, the estimating basis, a staged funding model, contingency and reserve rules, a burn-rate control method, and variance and change-control triggers.

It inherits the ADR-012 universal contract and specifies only what is Cost-specific.

---

## 2. Status
**Proposed (2026-10-26)** — Plan Tier 1 standard, inheriting ADR-012, ADR-025 and ADR-026. Ready for evaluation under `approve-adr`.

---

## 3. Context & Problem Statement
* **Derived baseline:** Cost is derived from Scope and Schedule (ADR-013 §4.5). A budget not traceable to WBS elements and timeboxes cannot be re-verified when either moves.
* **Hidden spend categories:** For a learning-systems project, material cost is not only staff time: compute, model/API usage and tooling can dominate and drift unnoticed unless categories are named.
* **Unbounded envelopes:** Without a stated envelope, funding stages and a contingency rule, overruns are discovered after the fact.
* **No casual omission:** ADR-011 §3.2 and Invariant #2 make Cost a baseline plan; `not_applicable` raises `FLAG: OMISSION_OF_BASE_PLAN`.
* **Zero Upfront Deliverable or Breakout Prerequisite:** Designing and baselining the Cost Management Plan requires only the Project Charter and the upstream Scope and Schedule baselines. It does **not** require detailed expenditure receipts, vendor contracts, or human breakout sessions in advance; the management envelope and funding stages govern progressive elaboration.

---

## 4. Technical Decision

### 4.1 Frontmatter Specification (ADR-012 §4.2)

```yaml
---
plan_id: "cost-management"
plan_name: "Cost Management Plan"
pmbok_edition: "PMBOK 8"
pmbok_focus_area: "Planning"
primary_pmbok_domain: "Finance"
secondary_pmbok_domains:
  - "Governance"
legacy_process: "7.1 Plan Cost Management"
route: "full_plan" # full_plan | pmp_section | not_applicable (validated against tailoring matrix)
generator: "llm"   # llm | human | stub | mock (ADR-013 §4.2 audit field)
version: "1.0.0"
baseline_id: "<target-baseline-id>"
owner_role: "Project Manager"
depends_on:
  - "scope-management"
  - "schedule-management"
inputs:
  - "Project-Charter.md"
  - "docs/project-docs/management-plans/Scope-Management-Plan.md"
  - "docs/project-docs/management-plans/Schedule-Management-Plan.md"
outputs:
  - "docs/project-docs/management-plans/Cost-Management-Plan.md" # if full_plan; .staging/pmp-sections/ if pmp_section
governance_policy: "approve-subsidiary-plan" # "approve-subsidiary-plan" (if full_plan) | "approve-pmp" (if pmp_section)
---
```

### 4.2 Required Content

#### Under `## 1. Intent, Alignment & Boundaries`
* **PMBOK Input, Process & Output (IPO) Specification:**
  * **Inputs:** `Project-Charter.md` (funding limits), approved `Scope-Management-Plan.md` (deliverable commitments), approved `Schedule-Management-Plan.md` (timeboxes/milestones). Zero invoices, receipts, or contracts required prior to planning.
  * **Processes:** Management envelope sizing, multi-category cost estimation (compute, token quotas, licences, effort), staged funding gates, contingency vs. reserve partitioning, burn-rate tracking.
  * **Outputs:** `Cost-Management-Plan.md` (or `.staging/pmp-sections/Cost-Management-Plan.md`), Management Envelope ceiling, Staged Budget allocations, and token/compute consumption caps.
* **Charter, Scope and Schedule Traceability:** Links the envelope and funding stages to Charter objectives, Scope epics and Schedule milestones.
* **Management Envelope:** The total spend ceiling and unit (currency or an explicitly defined effort unit), with the approving authority.
* **Out-of-Scope Cost Boundaries:** Explicit exclusions (e.g. costs borne by another budget, post-handover operating cost, sunk costs). The ADR-012 §4.1 `None: [rationale]` form applies when there are none.

#### Under `## 2. Domain Mechanics & Standards`
* **Cost Categories:** The categories tracked (for example people effort, compute, external model/API usage, tooling and licences), each with an owner and a measurement source.
* **Estimating Basis:** The method per category (analogous, parametric from observed usage, or bottom-up from the WBS) and its stated accuracy range.
* **Staged Funding Model:** Funding released per Schedule milestone or phase, with the release condition. Funding beyond the current stage is indicative only.
* **Contingency and Reserve:** Contingency (identified risk allowance, linked to the Risk plan) and any management reserve are held separately; the plan states who may release each.
* **Cost Baseline Definition:** The approved staged budget at the approval date, excluding management reserve.
* **Burn-Rate Control Method:** How actual spend is compared with plan (for example planned vs actual per stage, or earned-value-lite), and the reporting interval.

#### Under `## 3. Governance, Control & Decision Rights`
* **Accountability:** The Project Manager is accountable for cost baseline compliance. Envelope increases require the Sponsor / Charter Approver.
* **Variance Tolerances (baseline defaults; a stricter Charter tolerance takes precedence):**
  * Stage variance within $\pm 10\%$ of the stage budget and inside the stage's contingency: PM discretion, logged.
  * Variance beyond $\pm 10\%$, any envelope change, or any management-reserve release: Stage 17 Integrated Change Control (`approve-adaptation-plan`) or design-time baseline revision via ADR-037 (`BFI-NNN`).
* **Review Cadence:** At each stage boundary and at phase close.
* **Transitive Downstream Invalidation:** An approved Cost baseline change marks Risk (11.1) and Procurement (12.1) `STALE_DEPENDENCY` (ADR-013 §4.5).

### 4.3 Floor and Cap Thresholds

Measurement follows ADR-012 §4.3.1. Floors are raised and caps tightened for Tier 1 per ADR-012 §4.3.2.

| Metric | Embedded `pmp_section` | Standalone `full_plan` | Flag Type | Trigger Condition |
|---|---|---|---|---|
| **Word Count Floor** | 180 words | 700 words | `FLAG: BELOW_STANDARD_FLOOR` | Content < floor |
| **Word Count Cap** | 750 words | 4,500 words | `FLAG: EXCEEDS_SECTION_CAP` / `FLAG: EXCEEDS_PLAN_CAP` | Content > cap |
| **Out-of-Scope Items** | $\ge 2$ distinct items | $\ge 4$ distinct items | `FLAG: MISSING_BOUNDARY_DEF` | Items < minimum, unless a valid `None: [rationale]` is present |
| **Management Envelope** | Ceiling stated | Ceiling, unit, approver | `FLAG: MISSING_REQUIRED_SECTION` | Missing envelope |
| **Cost Categories & Estimating Basis** | Categories named | Categories, owners, sources, ranges | `FLAG: MISSING_REQUIRED_SECTION` | Missing categories |
| **Contingency / Reserve Rule** | One-line rule | Separate contingency and reserve with release authority | `FLAG: MISSING_REQUIRED_SECTION` | Missing rule |

### 4.4 Learning Methodology

**Now (implemented):** #3 reasoned resolution under `full` authority with permanent `requires_human_approval: true` through `approve-subsidiary-plan` (ADR-013 §4.2), and #6 durable human override. Methodology choice never grants autonomy, and no selection Episode exists yet (ADR-024 is Proposed).

**Possible later (only if its constraint is lifted):** #25 multi-stage credit assignment, to attribute a Cost deviation to Scope, Schedule or estimating basis. *Unblocked when:* Cryptographic parent plan lineage (`PlanApprovalRecord.parent_hashes`) implemented in Epic 13 provides the multi-stage dependency trace linking downstream cost deviations to upstream scope and schedule elements.

Source: `learning-methodology-selection` skill and Ideation Document §2.1.

---

## 5. Architectural Invariants
1. **Cost Follows Scope and Schedule:** Cost baseline finalization follows approval of both upstream plans.
2. **Budget Traces to Plan Elements:** Every funded stage names the Schedule milestone or Scope epic it funds.
3. **Contingency Is Linked to Risk:** Contingency amounts reference identified risks in the Risk plan (ADR-028) or state why none are identified.
4. **Tier 1 Omission Is Flagged:** `not_applicable` raises `FLAG: OMISSION_OF_BASE_PLAN` with recorded rationale and sponsor confirmation (ADR-011 §3.2).
5. **Flags, Not Blocks:** Findings other than Tier A integrity violations are flags resolved by recorded rationale (ADR-012 Invariant 8). Graduation and rejection follow ADR-012 §4.5.

---

## 6. Alternatives Considered
* **Alternative 1: Single upfront budget with no staging.** *Rejected:* Commits funds against work that is only elaborated progressively; no release conditions.
* **Alternative 2: Effort-only cost (ignore compute and API spend).** *Rejected:* Misses the largest uncontrolled spend categories for a learning-systems project.
* **Alternative 3: Merge Cost into Schedule.** *Rejected:* Violates LL-015; overrun cannot be separated from slippage.

---

## 7. Consequences

### Positive
* Spend overruns become escalated events with a defined threshold and approver.
* Contingency is traceable to risk rather than padded silently.

### Negative
* Authoring burden: categories, ranges and release rules must be defined early.
* A $\pm 10\%$ default is generic and needs tuning for very small envelopes.

---

## 8. Open Questions & Future Extensions
1. **Usage-Based Measurement:** Whether compute and API spend should be sourced from the repository cost model (`tests/test_cost_model.py` scope) rather than manual entry (deferred to tooling).
2. **Effort Unit:** Whether a project funded in effort rather than currency should use a standard unit across all plans. *Resolved in practice:* Person-hours or story points can serve as effort currency when declared in the management envelope.

---

## 9. Amendment Log

| Date | Change | Why |
|---|---|---|
| 2026-10-26 | Proposed | Initial drafting of ADR-027 under the ADR-012 framework, using ADR-025 as the structural template. |
| 2026-10-26 | Learning Methodology Note | Added §4.4 recording the methodology that applies now and the candidates that apply only if their constraints are lifted. |
| 2026-10-28 | Daughter ADR Review & Alignment Draft | Explicitly stated Governance secondary domain in §1, connected ADR-037 design-time feedback loop, noted Epic 13 cryptographic parent hashes unblocking #25 credit assignment, resolved effort unit open question, and prepared for review. |
