# ADR 026: Schedule Management Plan Standard and Baseline Contract

## 1. Executive Brief
Under **ADR-012** (§4.6), the **Schedule Management Plan** is the second Baseline-Substantiating (Plan Tier 1) standard, directly downstream of Scope (**ADR-025**): `5.1 Scope` $\to$ `6.1 Schedule` $\to$ `7.1 Cost`. In PMBOK 8 it belongs to the **Schedule Performance Domain** under the *Planning* Focus Area.

In baseline `PMP-BL-v1.0.0` the Schedule plan has no normative standard. This ADR defines what a valid Schedule plan must contain for a project that elaborates progressively through epics and timeboxed stories rather than a fixed Gantt: milestones traced to the WBS, a timebox and sequencing model, a duration estimation basis, a schedule baseline, buffers, and variance and change-control triggers.

It inherits the ADR-012 universal contract (frontmatter, three literal headings, tokenizer, Flag Tiers A/B/C) and specifies only what is Schedule-specific.

---

## 2. Status
**Proposed (2026-10-26)** — Plan Tier 1 standard, inheriting ADR-012 and ADR-025. Ready for evaluation under `approve-adr`.

---

## 3. Context & Problem Statement
* **Downstream of Scope, upstream of Cost:** Per ADR-013 §4.5, a Scope baseline change makes Schedule `STALE_DEPENDENCY`; a Schedule change in turn invalidates its dependents. Durations that cannot be traced to WBS elements cannot be re-verified when Scope moves.
* **False precision:** Fixed calendar dates for work that is elaborated progressively create commitments the project cannot keep. The standard must allow near-term detail and far-term milestones without becoming empty.
* **Silent slippage:** Without defined variance tolerances and an escalation trigger, schedule drift is absorbed informally and only surfaces at phase close.
* **No casual omission:** ADR-011 §3.2 and Invariant #2 make Schedule a baseline plan; `not_applicable` is a flagged deviation (`FLAG: OMISSION_OF_BASE_PLAN`).
* **Zero Upfront Deliverable or Breakout Prerequisite:** Designing and baselining the Schedule Management Plan requires only the Project Charter and the upstream Scope baseline. It does **not** require lower-level sprint tasks, code deliverables, or human breakout sessions in advance. Milestones and timeboxes are progressively elaborated from the Scope WBS.

---

## 4. Technical Decision

### 4.1 Frontmatter Specification (ADR-012 §4.2)

```yaml
---
plan_id: "schedule-management"
plan_name: "Schedule Management Plan"
pmbok_edition: "PMBOK 8"
pmbok_focus_area: "Planning"
primary_pmbok_domain: "Schedule"
secondary_pmbok_domains:
  - "Governance"
legacy_process: "6.1 Plan Schedule Management"
route: "full_plan" # full_plan | pmp_section | not_applicable (validated against tailoring matrix)
generator: "llm"   # llm | human | stub | mock (ADR-013 §4.2 audit field)
version: "1.0.0"
baseline_id: "<target-baseline-id>"
owner_role: "Project Manager"
depends_on:
  - "scope-management"
inputs:
  - "Project-Charter.md"
  - "docs/project-docs/management-plans/Scope-Management-Plan.md"
outputs:
  - "docs/project-docs/management-plans/Schedule-Management-Plan.md" # if full_plan; .staging/pmp-sections/ if pmp_section
governance_policy: "approve-subsidiary-plan" # "approve-subsidiary-plan" (if full_plan) | "approve-pmp" (if pmp_section)
---
```

`depends_on` lists direct plan dependencies only; transitive ancestors are resolved by the DAG (ADR-013 §4.5, ADR-034 §4.2.2).

### 4.2 Required Content

The plan body uses the three literal ADR-012 §4.3.1 headings. Schedule content is carried as subsections.

#### Under `## 1. Intent, Alignment & Boundaries`
* **PMBOK Input, Process & Output (IPO) Specification:**
  * **Inputs:** `Project-Charter.md` (target milestones), approved `Scope-Management-Plan.md` (WBS epics, boundaries, and DoD). Zero sprint tasks or code deliverables required prior to planning.
  * **Processes:** Progressive elaboration, timebox sequencing, critical path dependency analysis, duration estimation (story points/observed velocity), schedule buffer sizing and consumption control.
  * **Outputs:** `Schedule-Management-Plan.md` (or `.staging/pmp-sections/Schedule-Management-Plan.md`), Approved Milestone Register (M0.5–M5), timebox cadences, and critical path constraints.
* **Charter and Scope Traceability:** Maps the schedule horizon and milestones to Charter objectives and to the Scope baseline (ADR-025) epics.
* **Planning Horizon:** States what is scheduled in detail (the current timebox window) and what is held at milestone level only.
* **Out-of-Scope Scheduling Boundaries:** Explicit exclusions (e.g. calendar-date commitments beyond the detailed horizon, resource-levelled staffing calendars, external-vendor delivery dates). The ADR-012 §4.1 `None: [rationale]` form applies when there are none.

#### Under `## 2. Domain Mechanics & Standards`
* **Milestone Register:** Each milestone names its parent epic(s) from the Scope WBS, an exit condition that is objectively verifiable, and a target window (date range, not a single date, beyond the detailed horizon).
* **Timebox and Sequencing Model:** Timebox length and cadence; predecessor relationships between epics; the sequence that determines the earliest feasible completion (critical path or an equivalent stated method).
* **Duration Estimation Basis:** The estimation method (e.g. story points with observed velocity, or reference-class ranges), the unit, and whether estimates are ranges. Single-point estimates beyond the detailed horizon require a stated confidence.
* **Schedule Baseline Definition:** The approved milestone register plus timebox plan at the approval date. Later re-plans within tolerance do not alter the baseline.
* **Buffers:** Where schedule contingency is held (per milestone or per phase) and who may consume it.

#### Under `## 3. Governance, Control & Decision Rights`
* **Accountability:** The Project Manager is accountable for schedule baseline compliance. Milestone acceptance follows the Scope DoD (ADR-025).
* **Variance Tolerances (baseline defaults; a stricter Charter tolerance takes precedence):**
  * Milestone slip $\le 2$ working days, not on the critical path: PM discretion, logged.
  * Milestone slip $> 2$ working days, or any slip of a critical-path milestone, or a changed milestone exit condition: Stage 17 Integrated Change Control (`approve-adaptation-plan`) or design-time baseline revision via ADR-037 (`BFI-NNN`).
* **Review Cadence:** At each timebox boundary and at phase close.
* **Transitive Downstream Invalidation:** An approved Schedule baseline change marks Cost (7.1), Resource (9.1) and Risk (11.1) `STALE_DEPENDENCY`; Procurement (12.1) follows transitively through Cost (ADR-013 §4.5).

### 4.3 Floor and Cap Thresholds

Measurement follows ADR-012 §4.3.1. Floors are raised above the ADR-012 baseline defaults and caps tightened, as ADR-012 §4.3.2 permits for Tier 1 plans.

| Metric | Embedded `pmp_section` | Standalone `full_plan` | Flag Type | Trigger Condition |
|---|---|---|---|---|
| **Word Count Floor** | 180 words | 700 words | `FLAG: BELOW_STANDARD_FLOOR` | Content < floor |
| **Word Count Cap** | 750 words | 4,500 words | `FLAG: EXCEEDS_SECTION_CAP` / `FLAG: EXCEEDS_PLAN_CAP` | Content > cap |
| **Out-of-Scope Items** | $\ge 2$ distinct items | $\ge 4$ distinct items | `FLAG: MISSING_BOUNDARY_DEF` | Items < minimum, unless a valid `None: [rationale]` is present |
| **Milestone Register** | Milestone list with parent epic | Full register with exit conditions and windows | `FLAG: MISSING_REQUIRED_SECTION` | Missing register |
| **Timebox & Sequencing Model** | One-line model | Full model with predecessors | `FLAG: MISSING_REQUIRED_SECTION` | Missing model |
| **Estimation Basis** | Method named | Method, unit, confidence rule | `FLAG: MISSING_REQUIRED_SECTION` | Missing basis |

> [!NOTE]
> A distinct out-of-scope item is a Markdown list item with non-placeholder text (ADR-025 §4.3). Provisional unbracketed `TBD` dates are governance flags carried to the `DecisionFrame` (ADR-013 §4.2); bracketed tokens remain Tier A blocks.

### 4.4 Learning Methodology

**Now (implemented):** #3 reasoned resolution under `full` authority with permanent `requires_human_approval: true` through `approve-subsidiary-plan` (ADR-013 §4.2), and #6 durable human override. Methodology choice never grants autonomy, and no selection Episode exists yet (ADR-024 is Accepted).

**Possible later (only if its constraint is lifted):** #25 multi-stage credit assignment, to attribute a Schedule failure to Scope, estimation or sequencing along the DAG (LL-015). *Unblocked when:* Cryptographic parent plan lineage (`PlanApprovalRecord.parent_hashes`) implemented in Epic 13 provides the multi-stage dependency trace linking downstream schedule deviations to upstream scope elements.

### 4.4.1 Learner Decision

**Decision:** Build one advisory learner for the Schedule Management Plan, as the policy `advise-schedule-plan-decision`. The shape is declared with this standard and stays idle, with zero episodes and baseline logits, until real recommendation-versus-decision pairs exist. Synthetic episodes are not used. Building goes through BRD, FDD and a story; this ADR only decides that it is built and on which methodology. The methodology was chosen by hand from the `learning-methodology-selection` skill; when the policy is declared, the selection is recorded as an ADR-024 selection Episode with a human-declared profile. None exists yet and none is invented here.

**What it trains:** The decisions made in this area: the route (full plan, PMP section or N/A with reason), paragraph sufficiency against §4.3, graduation of an over-cap PMP section, and acceptance of a flagged deviation. These four decision types are the maintainer's working list and await confirmation.

**Selected methodology:** #2 softmax bandit with REINFORCE at `low` authority, over a small discrete recommendation set. It fits `learning-methodology-selection` step 3: the decision recurs, the action set is small, and outcomes are contrastive because the human either follows or overrides the recommendation. The reward comes from #5 reward shaping applied to the human decision recorded through #6 durable human override (followed is positive, overridden is negative). The learner trains on the recommendation, not on the approval decision itself.

**Boundaries:**
* Advisory only. The learner recommends and never approves; `approve-subsidiary-plan` stays `full` authority with permanent `requires_human_approval: true`, and its episodes are meant to stay outside REINFORCE (ADR-013 §4.2, ADR-001 §4.2). ADR-001 §4.5 records that this exclusion is not yet enforced in code, so the learner uses its own task id and never shares one with a gate policy.
* The recommendation and the human decision are both recorded; the gap between them is evidence.
* Methodology choice grants no autonomy. The complexity tier is declared by a human in the policy profile and its evidence gate in `autonomy-complexity.md` applies.
* No warm start is assumed. A shared prior across the nine learners (#15, ADR-020) is an untested hypothesis (HYP-AL-008) and is not built; each learner starts cold.
* Positive-only history would plateau REINFORCE (HYP-AL-002). Overrides must therefore be recorded as faithfully as agreements, or the learner is not trained.
* Anchoring and thin data: the learner's recommendation is persisted with a timestamp before the human sees it, so it cannot be altered after the decision. A minimum number of recorded decisions for this area is declared by the maintainer in the policy profile, above the tier minimum, and until it is reached the recommendation is stored but not shown. The number is not set here because no data exists to justify one.

**Plan-specific note:** Schedule is a baseline-substantiating plan. If recommendations turn out to depend on project features, #4 contextual softmax becomes relevant once it is packaged (HYP-AL-004); that is not yet evidenced. The later candidate stays #25 multi-stage credit assignment, blocked until `PlanApprovalRecord.parent_hashes` lineage exists.

Source: `learning-methodology-selection` skill and Ideation Document §2.1.

---

### 4.5 PMBOK 8 Alignment

**Source:** *A Guide to the Project Management Body of Knowledge*, Eighth Edition, Plan Schedule Management (Figure 2-21). The figure lists end with "Etc.", so the rows below are what the figure names, not an exhaustive set. This subsection records how the ADR relates to the guide; it does not change `depends_on`, `PLAN_DAG` or any threshold.

| | PMBOK 8 | This ADR |
|---|---|---|
| Inputs | Project charter; project management plan (scope management plan); development approach; enterprise environmental factors; organizational process assets. | Charter and approved Scope Management Plan in; Schedule Management Plan out (§4.2). Dependency matches: `schedule-management` depends on `scope-management`. |
| Tools and techniques | Expert judgment; data analysis (alternative analysis); meetings. | Not prescribed; the standard sets structure and measured thresholds and leaves method to the generator and the human reviewer. |
| Outputs | Project management plan updates: schedule management plan. | See §4.1 `outputs` and §4.2. |

**Differences and decisions:**

* **Dependency agrees with the guide.** Scope management plan is the guide's only plan input here, and it is the only dependency in `PLAN_DAG` besides the Charter.
* **Development approach is a named guide input.** This ADR has no field for it. Decision: the approach is taken from the Charter and the ADR-011 tailoring route. If a project's Charter does not state it, the Schedule plan must state it in Section 1. Proposed, for the maintainer to confirm.
* **Alternative analysis** (the guide's data-analysis technique) is not prescribed; no new requirement.

## 5. Architectural Invariants
1. **Schedule Follows Scope, Precedes Cost:** Schedule approval follows Scope and precedes Cost baseline finalization.
2. **Every Milestone Traces to the WBS:** A milestone with no parent epic in the Scope baseline raises `FLAG: MISSING_REQUIRED_SECTION`.
3. **Tier 1 Omission Is Flagged:** `not_applicable` raises `FLAG: OMISSION_OF_BASE_PLAN` and needs recorded rationale and sponsor confirmation (ADR-011 §3.2).
4. **Flags, Not Blocks:** Floor, cap, boundary and structure findings are Tier B/C flags resolved by recorded rationale in `Episode.metadata`; only Tier A integrity violations block (ADR-012 Invariant 8).
5. **Graduation and Rejection:** Over-cap `pmp_section` graduation and `approve-pmp` / `approve-subsidiary-plan` rejection follow ADR-012 §4.5; lifecycle states are projected from episodes (ADR-034 §4.2.2).

---

## 6. Alternatives Considered
* **Alternative 1: Fixed dated Gantt for the whole project.** *Rejected:* Contradicts progressive elaboration; produces unmaintainable far-term dates and constant spurious `STALE_DEPENDENCY` churn.
* **Alternative 2: Velocity-only schedule with no milestones.** *Rejected:* Gives no verifiable exit conditions and no basis for variance tolerances or Cost staging.
* **Alternative 3: Merge Schedule into Scope or Cost.** *Rejected:* Violates LL-015 component credit assignment; slippage cannot be separated from scope growth or spend.

---

## 7. Consequences

### Positive
* Slippage becomes a measured, escalated event rather than informal drift.
* Milestone-to-WBS traceability lets Scope changes invalidate exactly the affected schedule elements.

### Negative
* Authoring burden: teams must state estimation basis and milestone exit conditions early.
* Default tolerances are generic and need Charter-level tuning for very small or very large projects.

---

## 8. Open Questions & Future Extensions
1. **Tolerance Authority:** May the Charter alone tighten the default 2-working-day tolerance, or does that need an ADR-011 route-style decision? *Resolved in practice:* The Charter approver declares stricter tolerances in Charter success metrics; ADR-011 tailoring adopts Charter thresholds without requiring a separate route decision.
2. **Velocity Evidence:** Whether estimation basis should reference measured velocity from `LearningStore` episodes (deferred to tooling).
3. **PMBOK 8 Domain Re-basing:** PMBOK 8 has seven performance domains, while the repo uses nine plan areas and one learner per area. The nine are kept; whether learners are regrouped by domain is decided in the plan standards ADR.

---

## 9. Amendment Log

| Date | Change | Why |
|---|---|---|
| 2026-10-26 | Proposed | Initial drafting of ADR-026 under the ADR-012 framework, using ADR-025 as the structural template. |
| 2026-10-26 | Learning Methodology Note | Added §4.4 recording the methodology that applies now and the candidates that apply only if their constraints are lifted. |
| 2026-10-28 | Daughter ADR Review & Alignment Draft | Connected ADR-037 design-time feedback loop for pre-execution schedule adjustments, noted Epic 13 `PlanApprovalRecord.parent_hashes` cryptographic lineage unblocking #25 credit assignment, resolved tolerance authority open question, and prepared for review. |
| 2026-10-28 | PMBOK 8 Edition Review | Added §4.5 comparing this standard with the guide's planning process: inputs, tools and techniques, outputs, and each difference with a decision. No change to `depends_on`, `PLAN_DAG`, thresholds or the plan files. Proposed, for maintainer confirmation. |
| 2026-10-28 | Learner Decision | Added §4.4.1 deciding to build the `advise-schedule-plan-decision` advisory learner on #2 softmax bandit with REINFORCE at `low` authority, fed by #5 and #6. Advisory only; no episodes created. |
| 2026-10-28 | Learner Safeguards and Re-basing Gap | Added to §4.4.1 the anchoring and thin-data safeguard, and to §8 the open question on regrouping learners by PMBOK 8 domain. |
