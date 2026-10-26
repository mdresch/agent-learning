# ADR 029: Quality Management Plan Standard

## 1. Executive Brief
Under **ADR-012** (§4.6), the **Quality Management Plan** is a Governance & Control (Plan Tier 2) standard. In PMBOK 8 its primary domain is **Governance** with **Scope** as secondary (ADR-012 §4.4), under the *Planning* Focus Area.

Baseline `PMP-BL-v1.0.0` records formatting errors in the Quality plan and no normative standard. This ADR defines what a valid Quality plan must contain: quality objectives traceable to Scope acceptance criteria, quality gates mapped to lifecycle stages, verification criteria and coverage expectations, nonconformance handling, and quality metrics with thresholds.

It inherits the ADR-012 universal contract and specifies only what is Quality-specific.

---

## 2. Status
**Proposed (2026-10-26)** — Plan Tier 2 standard, inheriting ADR-012 and ADR-025. Ready for evaluation under `approve-adr`.

---

## 3. Context & Problem Statement
* **Quality is defined by Scope:** The Scope plan (ADR-025) holds the Definition of Done and acceptance criteria. The Quality plan must say how conformance to them is verified, not restate them.
* **Gates without criteria:** A gate that names no pass criteria cannot be audited.
* **Coverage as a number only:** Coverage targets stated without what they measure invite gaming; the plan must state scope of measurement.
* **Bounded invalidation:** Per ADR-013 §4.5, a Quality change does not invalidate Scope, Schedule or Cost; a Scope change does make Quality stale.

---

## 4. Technical Decision

### 4.1 Frontmatter Specification (ADR-012 §4.2)

```yaml
---
plan_id: "quality-management"
plan_name: "Quality Management Plan"
pmbok_edition: "PMBOK 8"
pmbok_focus_area: "Planning"
primary_pmbok_domain: "Governance"
secondary_pmbok_domains:
  - "Scope"
legacy_process: "8.1 Plan Quality Management"
route: "full_plan" # full_plan | pmp_section | not_applicable (validated against tailoring matrix)
generator: "llm"   # llm | human | stub | mock (ADR-013 §4.2 audit field)
version: "1.0.0"
baseline_id: "<target-baseline-id>"
owner_role: "Quality Assurance Lead"
depends_on:
  - "scope-management"
inputs:
  - "Project-Charter.md"
  - "docs/project-docs/management-plans/Scope-Management-Plan.md"
outputs:
  - "docs/project-docs/management-plans/Quality-Management-Plan.md" # if full_plan; .staging/pmp-sections/ if pmp_section
governance_policy: "approve-subsidiary-plan" # "approve-subsidiary-plan" (if full_plan) | "approve-pmp" (if pmp_section)
---
```

### 4.2 Required Content

#### Under `## 1. Intent, Alignment & Boundaries`
* **Charter and Scope Traceability:** Maps quality objectives to Charter objectives and to the Scope acceptance criteria and DoD (ADR-025).
* **Quality Objectives:** Measurable objectives (for example defect escape limits, statistical confidence requirements, or contract-test pass rules appropriate to the project).
* **Out-of-Scope Quality Boundaries:** Verification activities explicitly not performed (for example formal third-party audit, load certification). The ADR-012 §4.1 `None: [rationale]` form applies when there are none.

#### Under `## 2. Domain Mechanics & Standards`
* **Quality Gates:** Each gate names the lifecycle point (for example before Stage 10 Verification Evidence), pass criteria, evidence required, and the gate owner.
* **Verification Criteria and Coverage:** The test or review types required (unit, contract, integration, peer review), what a coverage figure measures, and the minimum accepted value.
* **Nonconformance Handling:** How a failed gate is recorded, who triages it, and how it returns to work (rework, waiver, or escalate).
* **Quality Metrics:** Metrics, collection source, and the threshold that triggers action.
* **Continuous Improvement Link:** Where recurring defects are recorded for lessons learned (ADR-010).

#### Under `## 3. Governance, Control & Decision Rights`
* **Accountability:** The Quality Assurance Lead owns the plan and gate definitions; deliverable acceptance authority remains as in ADR-025.
* **Waivers:** A waiver of a gate criterion requires a recorded rationale and approval by the named waiver authority; waivers are never silent.
* **Review Cadence:** At each gate and at phase close.
* **Downstream Invalidation:** Quality has no dependent plans in the baseline DAG. An approved Scope baseline change marks Quality `STALE_DEPENDENCY`.

### 4.3 Floor and Cap Thresholds

Measurement follows ADR-012 §4.3.1. Tier 2 raises the floor; caps stay at the ADR-012 baseline.

| Metric | Embedded `pmp_section` | Standalone `full_plan` | Flag Type | Trigger Condition |
|---|---|---|---|---|
| **Word Count Floor** | 160 words | 650 words | `FLAG: BELOW_STANDARD_FLOOR` | Content < floor |
| **Word Count Cap** | 800 words | 5,000 words | `FLAG: EXCEEDS_SECTION_CAP` / `FLAG: EXCEEDS_PLAN_CAP` | Content > cap |
| **Out-of-Scope Items** | $\ge 1$ item | $\ge 2$ distinct items | `FLAG: MISSING_BOUNDARY_DEF` | Items < minimum, unless a valid `None: [rationale]` is present |
| **Quality Gates** | Gates listed with pass criteria | Gates with criteria, evidence, owner | `FLAG: MISSING_REQUIRED_SECTION` | Missing gates |
| **Verification & Coverage** | Types and minimum | Types, measurement scope, minimum | `FLAG: MISSING_REQUIRED_SECTION` | Missing criteria |
| **Nonconformance Handling** | One-line process | Triage, waiver and rework rules | `FLAG: MISSING_REQUIRED_SECTION` | Missing process |

### 4.4 Learning Methodology

**Now (implemented):** #3 reasoned resolution under `full` authority with permanent `requires_human_approval: true` through `approve-subsidiary-plan` (ADR-013 §4.2), and #6 durable human override. Methodology choice never grants autonomy, and no selection Episode exists yet (ADR-024 is Proposed).

**Possible later (only if its constraint is lifted):** #2 softmax bandit with REINFORCE, for nonconformance triage (rework or escalate), where pass and fail outcomes are contrastive. Waivers stay human-approved. *Unblocked when:* A `TaskPolicy` is declared once at least two real, converged cases exist, and the tier's scored-outcome gate is met. Synthetic episodes are not used.

Source: `learning-methodology-selection` skill and Ideation Document §2.1.

---

## 5. Architectural Invariants
1. **Quality Verifies Scope, Not Redefines It:** Acceptance criteria live in the Scope baseline; the Quality plan references them.
2. **Gates Have Pass Criteria:** A gate with no stated pass criterion raises `FLAG: MISSING_REQUIRED_SECTION`.
3. **Waivers Are Recorded:** A waived criterion requires a recorded rationale and named approver.
4. **Flags, Not Blocks:** Findings other than Tier A integrity violations are flags resolved by recorded rationale (ADR-012 Invariant 8). Graduation and rejection follow ADR-012 §4.5.

---

## 6. Alternatives Considered
* **Alternative 1: Keep quality criteria only inside Scope.** *Rejected:* Scope defines what is acceptable; it does not define gates, evidence and waiver control.
* **Alternative 2: A single global coverage number.** *Rejected:* Unrelated to deliverable risk and easy to game.
* **Alternative 3: External audit required for every project.** *Rejected:* Disproportionate; available as a tailored extension.

---

## 7. Consequences

### Positive
* Gates become auditable and waivers visible.

### Negative
* Authoring burden: gate criteria and evidence must be stated up front.
* Overlap with Scope's DoD needs discipline to avoid contradictory criteria.

---

## 8. Open Questions & Future Extensions
1. **Gate Automation:** Whether gate results should be registered as episodes by tooling (deferred).
2. **Waiver Authority:** Whether one waiver authority suffices across gates (deferred to the Charter).

---

## 9. Amendment Log

| Date | Change | Why |
|---|---|---|
| 2026-10-26 | Proposed | Initial drafting of ADR-029 under the ADR-012 framework, using ADR-025 as the structural template. |
| 2026-10-26 | Learning Methodology Note | Added §4.4 recording the methodology that applies now and the candidates that apply only if their constraints are lifted. |
