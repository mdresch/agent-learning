# ADR 028: Risk Management Plan Standard

## 1. Executive Brief
Under **ADR-012** (§4.6), the **Risk Management Plan** is a Governance & Control (Plan Tier 2) standard. In PMBOK 8 its primary domain is **Risk**, with **Governance** and **Finance** as secondary domains (ADR-012 §4.4), under the *Planning* Focus Area.

It is downstream of Scope, Schedule and Cost in the baseline DAG, because risk exposure is assessed against the scope, the schedule and the budget. This ADR defines what a valid Risk plan must contain: a risk taxonomy, a probability-impact scale with defined bands, risk appetite and thresholds, a register contract, response strategies, review cadence and escalation.

It inherits the ADR-012 universal contract and specifies only what is Risk-specific.

---

## 2. Status
**Proposed (2026-10-26)** — Plan Tier 2 standard, inheriting ADR-012. Ready for evaluation under `approve-adr`.

---

## 3. Context & Problem Statement
* **Unanchored ratings:** "High" or "medium" without defined bands makes ratings unrepeatable between authors and between generator runs.
* **Risk without thresholds:** A register that never triggers escalation is a list, not a control. Thresholds must say when a risk moves a decision to a human.
* **Link to baselines:** Contingency in the Cost plan (ADR-027) and buffers in the Schedule plan (ADR-026) should be justified by identified risks.
* **Omission is allowed but recorded:** Tier 2 plans may be `not_applicable` with an approved tailoring rationale (ADR-011); it is not a Tier 1 `OMISSION_OF_BASE_PLAN` case.
* **Zero Upfront Deliverable or Breakout Prerequisite:** Designing and baselining the Risk Management Plan requires only the Project Charter and upstream Scope, Schedule, and Cost baselines. It does **not** require an exhaustive pre-populated risk register, quantified exposure models, or human breakout sessions in advance; the plan establishes the taxonomy, scales, and register contract under which risks are progressively identified.

---

## 4. Technical Decision

### 4.1 Frontmatter Specification (ADR-012 §4.2)

```yaml
---
plan_id: "risk-management"
plan_name: "Risk Management Plan"
pmbok_edition: "PMBOK 8"
pmbok_focus_area: "Planning"
primary_pmbok_domain: "Risk"
secondary_pmbok_domains:
  - "Governance"
  - "Finance"
legacy_process: "11.1 Plan Risk Management"
route: "full_plan" # full_plan | pmp_section | not_applicable (validated against tailoring matrix)
generator: "llm"   # llm | human | stub | mock (ADR-013 §4.2 audit field)
version: "1.0.0"
baseline_id: "<target-baseline-id>"
owner_role: "Risk Lead"
depends_on:
  - "scope-management"
  - "schedule-management"
  - "cost-management"
inputs:
  - "Project-Charter.md"
  - "docs/project-docs/management-plans/Scope-Management-Plan.md"
  - "docs/project-docs/management-plans/Schedule-Management-Plan.md"
  - "docs/project-docs/management-plans/Cost-Management-Plan.md"
outputs:
  - "docs/project-docs/management-plans/Risk-Management-Plan.md" # if full_plan; .staging/pmp-sections/ if pmp_section
governance_policy: "approve-subsidiary-plan" # "approve-subsidiary-plan" (if full_plan) | "approve-pmp" (if pmp_section)
---
```

### 4.2 Required Content

#### Under `## 1. Intent, Alignment & Boundaries`
* **PMBOK Input, Process & Output (IPO) Specification:**
  * **Inputs:** `Project-Charter.md` (risk appetite), approved `Scope-Management-Plan.md`, `Schedule-Management-Plan.md`, `Cost-Management-Plan.md` (baseline exposures). Zero populated risk registers or breakout sessions required prior to planning.
  * **Processes:** Risk taxonomy classification, reproducible probability-impact banded scoring, response strategy selection (avoid, mitigate, transfer, accept, escalate), contingency linking, escalation threshold enforcement.
  * **Outputs:** `Risk-Management-Plan.md` (or `.staging/pmp-sections/Risk-Management-Plan.md`), Risk Register schema contract, escalation criteria reaching human authority, and contingency drawdown triggers.
* **Charter and Baseline Traceability:** Maps risk objectives to Charter objectives and states which Scope, Schedule and Cost baseline elements are in the assessed exposure.
* **Risk Appetite:** A short statement per objective area (scope, schedule, cost, quality, governance integrity) of what level of exposure is acceptable.
* **Out-of-Scope Risk Boundaries:** Risk categories explicitly not managed by this plan (for example, risks owned by an external party). The ADR-012 §4.1 `None: [rationale]` form applies when there are none.

#### Under `## 2. Domain Mechanics & Standards`
* **Risk Taxonomy:** The categories used to classify risks (for example technical, mathematical/statistical, governance and integrity, dependency, schedule, cost).
* **Probability-Impact Scale:** Defined numeric or banded scales for probability and for impact per objective area, and the rule that combines them into a rating (for example a score and a rating band). Ratings must be reproducible from the scale.
* **Risk Register Contract:** The register's location and the minimum fields per risk: identifier, description, category, probability, impact, rating, owner, response strategy, status, and trigger.
* **Response Strategies:** The allowed strategies (avoid, mitigate, transfer, accept, escalate) and when each applies.
* **Contingency Link:** How rated risks translate into contingency in the Cost plan and buffers in the Schedule plan.

#### Under `## 3. Governance, Control & Decision Rights`
* **Accountability:** The Risk Lead owns the register and the plan. Risk owners are named roles from the Stakeholder Register.
* **Escalation Thresholds (baseline defaults):** A risk rated at or above the plan's *high* band, or any risk threatening a baseline tolerance (ADR-026, ADR-027), is escalated to the Sponsor / Charter Approver; acceptance of such a risk is a recorded decision.
* **Review Cadence:** At each timebox boundary and when any upstream baseline changes.
* **Downstream Invalidation:** Risk has no dependent plans in the baseline DAG. When an upstream baseline changes the Risk plan becomes `STALE_DEPENDENCY` and the register is re-assessed (ADR-013 §4.5).

### 4.3 Floor and Cap Thresholds

Measurement follows ADR-012 §4.3.1. Tier 2 raises the floor above the ADR-012 baseline defaults; caps stay at the baseline.

| Metric | Embedded `pmp_section` | Standalone `full_plan` | Flag Type | Trigger Condition |
|---|---|---|---|---|
| **Word Count Floor** | 160 words | 650 words | `FLAG: BELOW_STANDARD_FLOOR` | Content < floor |
| **Word Count Cap** | 800 words | 5,000 words | `FLAG: EXCEEDS_SECTION_CAP` / `FLAG: EXCEEDS_PLAN_CAP` | Content > cap |
| **Out-of-Scope Items** | $\ge 1$ item | $\ge 2$ distinct items | `FLAG: MISSING_BOUNDARY_DEF` | Items < minimum, unless a valid `None: [rationale]` is present |
| **Probability-Impact Scale** | Bands defined | Scales per objective area with combination rule | `FLAG: MISSING_REQUIRED_SECTION` | Missing scale |
| **Register Contract** | Location and key fields | Full field list | `FLAG: MISSING_REQUIRED_SECTION` | Missing contract |
| **Escalation Thresholds** | Threshold stated | Threshold, escalation target, acceptance record | `FLAG: MISSING_REQUIRED_SECTION` | Missing thresholds |

### 4.4 Learning Methodology

**Now (implemented):** #3 reasoned resolution under `full` authority with permanent `requires_human_approval: true` through `approve-subsidiary-plan` (ADR-013 §4.2), and #6 durable human override. Methodology choice never grants autonomy, and no selection Episode exists yet (ADR-024 is Proposed).

**Possible later (only if its constraint is lifted):** #31 safe bandits with action masking, for choosing a risk response while masking responses the escalation thresholds forbid (HYP-AL-022). *Unblocked when:* The method is built, risk responses recur with scored outcomes, and the tier's evidence gate in `autonomy-complexity.md` is met.

Source: `learning-methodology-selection` skill and Ideation Document §2.1.

---

## 5. Architectural Invariants
1. **Ratings Are Reproducible:** Every rating can be recomputed from the declared scale; unanchored qualitative ratings raise `FLAG: MISSING_REQUIRED_SECTION`.
2. **Thresholds Reach a Human:** A risk at or above the escalation threshold cannot be accepted without a recorded human decision.
3. **Register Is Not a New Entity:** The register is a version-controlled artifact; any approval evidence is persisted as `Episode.metadata` (ADR-002 Invariant #2).
4. **Flags, Not Blocks:** Findings other than Tier A integrity violations are flags resolved by recorded rationale (ADR-012 Invariant 8). Graduation and rejection follow ADR-012 §4.5.

---

## 6. Alternatives Considered
* **Alternative 1: Free-text risk list with qualitative ratings.** *Rejected:* Not reproducible and not lintable.
* **Alternative 2: Full quantitative Monte Carlo analysis as a requirement.** *Rejected:* Disproportionate for most projects and not justified by the baseline's size; available as an optional extension.
* **Alternative 3: Fold risk into the Cost plan's contingency section.** *Rejected:* Risk spans scope, schedule, quality and governance, not only cost.

---

## 7. Consequences

### Positive
* Risk ratings are repeatable and tied to escalation, and contingency can be traced to risks.

### Negative
* Authoring burden: scales and register fields must be defined before risks are recorded.
* Scale design is judgement-based; a poor scale yields consistently poor ratings.

---

## 8. Open Questions & Future Extensions
1. **Risk and Learning Evidence:** Whether recorded risk outcomes should feed an advisory learner (deferred to learner ADRs).
2. **Register Format:** Whether the register should be a Markdown table or structured data with a parser (deferred to tooling). *Resolved in practice:* Per ADR-002 Invariant #2 and ADR-034 anti-sprawl, the register is formatted as a standardized Markdown table within `Risk-Management-Plan.md`, parsed and checked by text linter rules rather than requiring a dedicated database entity.

---

## 9. Amendment Log

| Date | Change | Why |
|---|---|---|
| 2026-10-26 | Proposed | Initial drafting of ADR-028 under the ADR-012 framework, using ADR-025 as the structural template. |
| 2026-10-26 | Learning Methodology Note | Added §4.4 recording the methodology that applies now and the candidates that apply only if their constraints are lifted. |
| 2026-10-28 | Daughter ADR Review & Alignment Draft | Resolved register format open question confirming Markdown table format under ADR-002/034, verified DAG dependencies (`scope-management`, `schedule-management`, `cost-management`), and prepared for review. |
