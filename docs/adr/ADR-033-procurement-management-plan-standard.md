# ADR 033: Procurement Management Plan Standard

## 1. Executive Brief
Under **ADR-012** (§4.6), the **Procurement Management Plan** is an Execution Support (Plan Tier 3) standard. In PMBOK 8 its primary domain is **Finance** with **Resources** and **Governance** as secondary domains (ADR-012 §4.4), under the *Planning* Focus Area; its legacy process is `12.1`.

For this project, procurement is mostly the acquisition of external services, models, libraries and licences rather than contracted construction. This ADR defines what a valid Procurement plan must contain: what may be acquired from outside, make-or-buy and selection criteria, intake rules for third-party dependencies, contract and licence terms to check, supplier performance control, and exit conditions.

It inherits the ADR-012 universal contract and specifies only what is Procurement-specific. As a Tier 3 plan it keeps the ADR-012 baseline floors and caps.

---

## 2. Status
**Proposed (2026-10-26)** — Plan Tier 3 standard, inheriting ADR-012 and ADR-027. Ready for evaluation under `approve-adr`.

---

## 3. Context & Problem Statement
* **Dependency sprawl:** ADR-034 rejects tool and dependency sprawl for PMBOK tooling. Without an intake rule the same sprawl returns through ordinary library and service choices.
* **Hidden cost and lock-in:** External model/API usage and licences drive Cost (ADR-027) and create exit risk (ADR-028) that must be assessed before acquisition.
* **Licence and data exposure:** Terms covering licence compatibility and what data may be sent to a supplier must be checked before adoption.
* **Downstream of Cost:** Procurement depends on Scope and Cost in the baseline DAG; a Cost baseline change makes it stale.
* **Zero Upfront Deliverable or Breakout Prerequisite:** Designing and baselining the Procurement Management Plan requires only the Project Charter and Scope/Cost baselines. It does **not** require pre-signed vendor contracts, executed licences, or human breakout sessions in advance; it establishes make-or-buy criteria and third-party intake rules.

---

## 4. Technical Decision

### 4.1 Frontmatter Specification (ADR-012 §4.2)

```yaml
---
plan_id: "procurement-management"
plan_name: "Procurement Management Plan"
pmbok_edition: "PMBOK 8"
pmbok_focus_area: "Planning"
primary_pmbok_domain: "Finance"
secondary_pmbok_domains:
  - "Resources"
  - "Governance"
legacy_process: "12.1 Plan Procurement Management"
route: "full_plan" # full_plan | pmp_section | not_applicable (validated against tailoring matrix)
generator: "llm"   # llm | human | stub | mock (ADR-013 §4.2 audit field)
version: "1.0.0"
baseline_id: "<target-baseline-id>"
owner_role: "Project Manager"
depends_on:
  - "scope-management"
  - "cost-management"
inputs:
  - "Project-Charter.md"
  - "docs/project-docs/management-plans/Scope-Management-Plan.md"
  - "docs/project-docs/management-plans/Cost-Management-Plan.md"
outputs:
  - "docs/project-docs/management-plans/Procurement-Management-Plan.md" # if full_plan; .staging/pmp-sections/ if pmp_section
governance_policy: "approve-subsidiary-plan" # "approve-subsidiary-plan" (if full_plan) | "approve-pmp" (if pmp_section)
---
```

### 4.2 Required Content

#### Under `## 1. Intent, Alignment & Boundaries`
* **PMBOK Input, Process & Output (IPO) Specification:**
  * **Inputs:** `Project-Charter.md` (make-or-buy guidance), approved `Scope-Management-Plan.md` (acquisitions needed), approved `Cost-Management-Plan.md` (budget envelope). Zero pre-signed contracts, RFPs, or breakout sessions required prior to planning.
  * **Processes:** Make-or-buy analysis, source selection criteria weighting, third-party dependency intake justification (ADR-034 anti-sprawl), licence compatibility verification, supplier performance and exit control.
  * **Outputs:** `Procurement-Management-Plan.md` (or `.staging/pmp-sections/Procurement-Management-Plan.md`), Dependency Intake Register, source selection scorecards, and supplier exit plans.
* **Charter, Scope and Cost Traceability:** Maps planned acquisitions to Scope deliverables and to Cost categories and envelope.
* **Acquisition Classes:** The kinds of external acquisition in play (for example open-source libraries, hosted model/API services, tooling licences, contracted work).
* **Out-of-Scope Procurement Boundaries:** Acquisitions explicitly excluded (for example hardware purchasing, paid third-party review). The ADR-012 §4.1 `None: [rationale]` form applies when there are none.

#### Under `## 2. Domain Mechanics & Standards`
* **Make-or-Buy Criteria:** The factors used (capability fit, total cost, maintenance burden, lock-in, data exposure) and how they are weighed.
* **Dependency Intake Rule:** A new third-party runtime dependency or external service requires a recorded justification covering the need, alternatives considered including doing without, licence, maintenance status, and exit path. This applies ADR-034's anti-sprawl principle to all acquisitions.
* **Supplier Selection Criteria:** Criteria and evidence for choosing between candidates.
* **Contract and Licence Checks:** Terms to verify before adoption: licence compatibility, usage limits, data handling and retention, change-of-terms rights.
* **Supplier Performance and Exit:** How supplier performance is monitored and the conditions and steps for replacing a supplier.

#### Under `## 3. Governance, Control & Decision Rights`
* **Accountability:** The Project Manager owns the plan. Acquisitions above the threshold declared in the plan need Sponsor / Charter Approver authorization; below it, PM discretion, logged.
* **Cost Linkage:** An acquisition that changes the Cost envelope or a stage budget is a Stage 17 Integrated Change Control event (`approve-adaptation-plan`).
* **Review Cadence:** At each acquisition decision and at phase close.
* **Downstream Invalidation:** Procurement has no dependent plans in the baseline DAG. An approved Scope or Cost baseline change marks it `STALE_DEPENDENCY` (ADR-013 §4.5).

### 4.3 Floor and Cap Thresholds

Measurement follows ADR-012 §4.3.1. Tier 3 keeps the ADR-012 baseline defaults.

| Metric | Embedded `pmp_section` | Standalone `full_plan` | Flag Type | Trigger Condition |
|---|---|---|---|---|
| **Word Count Floor** | 150 words | 600 words | `FLAG: BELOW_STANDARD_FLOOR` | Content < floor |
| **Word Count Cap** | 800 words | 5,000 words | `FLAG: EXCEEDS_SECTION_CAP` / `FLAG: EXCEEDS_PLAN_CAP` | Content > cap |
| **Out-of-Scope Items** | $\ge 1$ item | $\ge 2$ distinct items | `FLAG: MISSING_BOUNDARY_DEF` | Items < minimum, unless a valid `None: [rationale]` is present |
| **Make-or-Buy Criteria** | Factors named | Factors and weighting | `FLAG: MISSING_REQUIRED_SECTION` | Missing criteria |
| **Dependency Intake Rule** | Rule stated | Rule with required justification fields | `FLAG: MISSING_REQUIRED_SECTION` | Missing rule |
| **Contract & Licence Checks** | Checks listed | Checks and verification owner | `FLAG: MISSING_REQUIRED_SECTION` | Missing checks |

### 4.4 Learning Methodology

**Now (implemented):** #3 reasoned resolution under `full` authority with permanent `requires_human_approval: true` through `approve-subsidiary-plan` (ADR-013 §4.2), and #6 durable human override. Methodology choice never grants autonomy, and no selection Episode exists yet (ADR-024 is Proposed).

**Possible later:** none identified for this plan. A candidate is reconsidered if decisions about this plan recur with scored outcomes.

Source: `learning-methodology-selection` skill and Ideation Document §2.1.

---

### 4.5 PMBOK 8 Alignment

**Source:** *A Guide to the Project Management Body of Knowledge*, Eighth Edition, Plan Sourcing Strategy (Figure 2-5). The figure lists end with "Etc.", so the rows below are what the figure names, not an exhaustive set. This subsection records how the ADR relates to the guide; it does not change `depends_on`, `PLAN_DAG` or any threshold.

| | PMBOK 8 | This ADR |
|---|---|---|
| Inputs | Project charter; project management plan (scope, quality, schedule, financial and resource management plans, scope baseline); project documents (among others milestone list, requirements documentation, requirements traceability matrix, quality metrics, resource requirements, project team assignments, risk register, stakeholder register); enterprise environmental factors; organizational process assets. | Charter, approved Scope and Cost plans in; Procurement Management Plan out, with the dependency intake register and selection scorecards (§4.2). |
| Tools and techniques | Expert judgment; market research; make-or-buy analysis; source selection analysis; document analysis. | Not prescribed; the standard sets structure and measured thresholds and leaves method to the generator and the human reviewer. |
| Outputs | Sourcing strategy plan, including insourcing or outsourcing decisions and source selection criteria. | See §4.1 `outputs` and §4.2. |

**Differences and decisions:**

* **Name.** The guide's process produces a sourcing strategy plan, and the guide's glossary also defines a procurement management plan as a plan component. Decision: keep the plan id `procurement-management`; this ADR covers the sourcing decisions and the third-party intake rules.
* **Five plan inputs in the guide, two here.** `PLAN_DAG` gives Procurement `scope-management` and `cost-management`. Schedule, Quality and Resource plans are not gating. Decision: Procurement may read them, without a staleness edge. The guide notes that sourcing differs from resource planning (it is for external sources), which supports keeping the two plans apart.
* **Make-or-buy and source selection analysis** are covered by §4.2. Market research is not required; the repo's anti-sprawl rule (ADR-034) prefers fewer third-party dependencies, so research is only needed when a dependency is proposed.

## 5. Architectural Invariants
1. **No Unrecorded Dependency:** Adding an external dependency or service without the intake record violates the plan; the record is evidence in the approval or change episode, not a new entity (ADR-002 Invariant #2).
2. **Acquisition Respects the Cost Envelope:** An acquisition that would exceed the envelope or a stage budget requires change control.
3. **Exit Path Required:** Every external service dependency states how it would be replaced.
4. **Flags, Not Blocks:** Findings other than Tier A integrity violations are flags resolved by recorded rationale (ADR-012 Invariant 8). Graduation and rejection follow ADR-012 §4.5.

---

## 6. Alternatives Considered
* **Alternative 1: No procurement plan; rely on ad hoc library choices.** *Rejected:* Allows the dependency and cost sprawl ADR-034 was written to prevent.
* **Alternative 2: Treat procurement as a section of Cost.** *Rejected:* Selection, licence and exit control are not budget topics (LL-015).
* **Alternative 3: Ban all external services.** *Rejected:* Unrealistic for a project built on external models.

---

## 7. Consequences

### Positive
* External dependencies are justified, costed and have exit paths.

### Negative
* Authoring burden; the intake record adds friction to adopting a library.

---

## 8. Open Questions & Future Extensions
1. **Threshold Value:** The plan declares its authorization threshold; whether a repository default is needed is open. *Clarified:* Default threshold is defined in the Cost Management Plan envelope (e.g. any single contract or annual service exceeding 10% of stage contingency requires Sponsor approval).
2. **Dependency Audit Tooling:** Cross-checking `pyproject.toml` dependencies against intake records (deferred to tooling).
3. **DAG Dependencies:** Whether Procurement should also depend on `resource-management`. *Resolved in PLAN_DAG:* In accordance with FDD-013 §2.1 and `standards.py`, `procurement-management` depends on `('scope-management', 'cost-management')`. External services, models, and third-party licences consume project budget (Cost) to fulfill deliverables (Scope); internal staffing allocations (Resource) do not constrain external acquisitions, preventing cross-Tier-3 invalidation churn.

---

## 9. Amendment Log

| Date | Change | Why |
|---|---|---|
| 2026-10-26 | Proposed | Initial drafting of ADR-033 under the ADR-012 framework, using ADR-025 as the structural template. |
| 2026-10-26 | Learning Methodology Note | Added §4.4 recording the methodology that applies now and the candidates that apply only if their constraints are lifted. |
| 2026-10-28 | Daughter ADR Review & Alignment Draft | Clarified authorization threshold and confirmed `PLAN_DAG` dependency edges (`scope-management`, `cost-management`) without coupling to `resource-management`, verified frontmatter, and prepared for review. |
| 2026-10-28 | PMBOK 8 Edition Review | Added §4.5 comparing this standard with the guide's planning process: inputs, tools and techniques, outputs, and each difference with a decision. No change to `depends_on`, `PLAN_DAG`, thresholds or the plan files. Proposed, for maintainer confirmation. |
