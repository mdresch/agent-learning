# ADR 027: Cost Management Plan Standard and Baseline Contract

## 1. Executive Brief
Under **ADR-012** (§4.6), the **Cost Management Plan** is the third Baseline-Substantiating (Plan Tier 1) standard: `5.1 Scope` $\to$ `6.1 Schedule` $\to$ `7.1 Cost`. In PMBOK 8 its primary domain is **Finance**, with **Governance** as secondary domain (ADR-012 §4.4), under the *Planning* Focus Area.

In baseline `PMP-BL-v1.0.0` the Cost plan has no normative standard. This ADR defines what a valid Cost plan must contain for a project funded in stages against a management envelope: the cost categories tracked, the estimating basis, a staged funding model, contingency and reserve rules, a burn-rate control method, and variance and change-control triggers.

It inherits the ADR-012 universal contract and specifies only what is Cost-specific.

---

## 2. Status
**Accepted (2026-10-29, Menno)** — Plan Tier 1 standard, inheriting ADR-012, ADR-025 and ADR-026. Episode: `0ae724ad-5309-4eb2-a333-749cde39c0c0`.

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

**Now (implemented):** #3 reasoned resolution under `full` authority with permanent `requires_human_approval: true` through `approve-subsidiary-plan` (ADR-013 §4.2), and #6 durable human override. Methodology choice never grants autonomy, and no selection Episode exists yet (ADR-024 is Accepted).

**Possible later (only if its constraint is lifted):** #25 multi-stage credit assignment, to attribute a Cost deviation to Scope, Schedule or estimating basis. *Unblocked when:* Cryptographic parent plan lineage (`PlanApprovalRecord.parent_hashes`) implemented in Epic 13 provides the multi-stage dependency trace linking downstream cost deviations to upstream scope and schedule elements.

### 4.4.1 Learner Decision

**Decision:** Build one advisory learner for the Cost Management Plan, as the policy `advise-cost-plan-decision`. The shape is declared with this standard and stays idle, with zero episodes and baseline logits, until real recommendation-versus-decision pairs exist. Synthetic episodes are not used. Building goes through BRD, FDD and a story; this ADR only decides that it is built and on which methodology. The methodology was chosen by hand from the `learning-methodology-selection` skill; when the policy is declared, the selection is recorded as an ADR-024 selection Episode with a human-declared profile. None exists yet and none is invented here.

**What it trains:** The decisions made in this area: the route (full plan, PMP section or N/A with reason), paragraph sufficiency against §4.3, graduation of an over-cap PMP section, and acceptance of a flagged deviation. These four decision types are the maintainer's working list and await confirmation.

**Selected methodology:** #2 softmax bandit with REINFORCE at `low` authority, over a small discrete recommendation set. It fits `learning-methodology-selection` step 3: the decision recurs, the action set is small, and outcomes are contrastive because the human either follows or overrides the recommendation. The reward comes from #5 reward shaping applied to the human decision recorded through #6 durable human override (followed is positive, overridden is negative). The learner trains on the recommendation, not on the approval decision itself.

**Boundaries:**
* Advisory only. The learner recommends and never approves; `approve-subsidiary-plan` stays `full` authority with permanent `requires_human_approval: true`, and its episodes are meant to stay outside REINFORCE (ADR-013 §4.2, ADR-001 §4.2). ADR-001 §4.5 records that this exclusion is not yet enforced in code, so the learner uses its own task id and never shares one with a gate policy.
* The recommendation and the human decision are both recorded; the gap between them is evidence.
* Methodology choice grants no autonomy. The complexity tier is declared by a human in the policy profile and its evidence gate in `autonomy-complexity.md` applies.
* No warm start is assumed. A shared prior across the nine learners (#15, ADR-020) is an untested hypothesis (HYP-AL-008) and is not built; each learner starts cold.
* Positive-only history would plateau REINFORCE (HYP-AL-002). Overrides must therefore be recorded as faithfully as agreements, or the learner is not trained.
* Anchoring and thin data: the learner's recommendation is persisted with a timestamp before the human sees it, so it cannot be altered after the decision. A minimum number of recorded decisions for this area is declared by the maintainer in the policy profile, above the tier minimum, and until it is reached the recommendation is stored but not shown. The number is not set here because no data exists to justify one.

**Plan-specific note:** The later candidate stays #25 multi-stage credit assignment, blocked until `PlanApprovalRecord.parent_hashes` lineage exists.

Source: `learning-methodology-selection` skill and Ideation Document §2.1.

---

### 4.5 PMBOK 8 Alignment

**Source:** *A Guide to the Project Management Body of Knowledge*, Eighth Edition, Plan Financial Management (Figure 2-27). The figure lists end with "Etc.", so the rows below are what the figure names, not an exhaustive set. This subsection records how the ADR relates to the guide; it does not change `depends_on`, `PLAN_DAG` or any threshold.

| | PMBOK 8 | This ADR |
|---|---|---|
| Inputs | Project charter; project management plan (schedule management plan, risk management plan); project documents; enterprise environmental factors; organizational process assets. | Charter, approved Scope and Schedule plans in; Cost Management Plan out, with the envelope, staged funding and contingency partition (§4.2). |
| Tools and techniques | Expert judgment; data analysis (alternative analysis); meetings. | Not prescribed; the standard sets structure and measured thresholds and leaves method to the generator and the human reviewer. |
| Outputs | Financial management plan; funding strategy. | See §4.1 `outputs` and §4.2. |

**Differences and decisions:**

* **Name and scope.** The guide's plan is a financial management plan covering project revenues and expenses. This ADR covers costs and funding of a project with no revenue line. Decision: keep the plan id `cost-management` (it is fixed in `PLAN_DAG` and in the plan file name) and record that revenue planning is out of scope. The guide's "funding strategy" output corresponds to the staged funding gates.
* **Risk management plan is a guide input; here Risk depends on Cost.** `PLAN_DAG` has `risk-management` depending on `cost-management`, the reverse of the guide. The guide itself has Plan Risk Management read all plan components, so its own ordering is circular. Decision: keep Cost before Risk, because a Risk plan needs the baseline exposure to score, and a DAG must not have a cycle (ADR-013 §4.5). Contingency sizing in this ADR is therefore set without an approved Risk plan and is reconciled when the Risk plan is approved. Open question for the maintainer: whether that reconciliation needs an explicit re-approval step.

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
3. **PMBOK 8 Domain Re-basing:** PMBOK 8 has seven performance domains, while the repo uses nine plan areas and one learner per area. The nine are kept; whether learners are regrouped by domain is decided in the plan standards ADR.

---

## 9. Amendment Log

| Date | Change | Why |
|---|---|---|
| 2026-10-26 | Proposed | Initial drafting of ADR-027 under the ADR-012 framework, using ADR-025 as the structural template. |
| 2026-10-26 | Learning Methodology Note | Added §4.4 recording the methodology that applies now and the candidates that apply only if their constraints are lifted. |
| 2026-10-28 | Daughter ADR Review & Alignment Draft | Explicitly stated Governance secondary domain in §1, connected ADR-037 design-time feedback loop, noted Epic 13 cryptographic parent hashes unblocking #25 credit assignment, resolved effort unit open question, and prepared for review. |
| 2026-10-28 | PMBOK 8 Edition Review | Added §4.5 comparing this standard with the guide's planning process: inputs, tools and techniques, outputs, and each difference with a decision. No change to `depends_on`, `PLAN_DAG`, thresholds or the plan files. Proposed, for maintainer confirmation. |
| 2026-10-28 | Learner Decision | Added §4.4.1 deciding to build the `advise-cost-plan-decision` advisory learner on #2 softmax bandit with REINFORCE at `low` authority, fed by #5 and #6. Advisory only; no episodes created. |
| 2026-10-28 | Learner Safeguards and Re-basing Gap | Added to §4.4.1 the anchoring and thin-data safeguard, and to §8 the open question on regrouping learners by PMBOK 8 domain. |
| 2026-10-29 | **Accepted by Menno** | Formally adjudicated and accepted through `approve-adr`; robust utility 0.712, expected utility 0.786; Episode `0ae724ad-5309-4eb2-a333-749cde39c0c0`. |
