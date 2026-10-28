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
* **Zero Upfront Deliverable or Breakout Prerequisite:** Designing and baselining the Quality Management Plan requires only the Project Charter and Scope baseline. It does **not** require test suite code, verification evidence, or human breakout sessions in advance; it establishes the quality gates, verification rules, and DoD conformance criteria under which subsequent deliverables are audited.

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
* **PMBOK Input, Process & Output (IPO) Specification:**
  * **Inputs:** `Project-Charter.md` (quality standards), approved `Scope-Management-Plan.md` (acceptance criteria and DoD). Zero test suites or code deliverables required prior to planning.
  * **Processes:** Quality gate identification and lifecycle mapping, verification type categorization (contract, unit, integration), coverage scope measurement, nonconformance triage, waiver governance.
  * **Outputs:** `Quality-Management-Plan.md` (or `.staging/pmp-sections/Quality-Management-Plan.md`), Quality Gate Definitions, Verification Standards, and DoD audit checklists authorizing Stage 10 Verification Evidence.
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

**Now (implemented):** #3 reasoned resolution under `full` authority with permanent `requires_human_approval: true` through `approve-subsidiary-plan` (ADR-013 §4.2), and #6 durable human override. Methodology choice never grants autonomy, and no selection Episode exists yet (ADR-024 is Accepted).

**Possible later (only if its constraint is lifted):** #2 softmax bandit with REINFORCE, for nonconformance triage (rework or escalate), where pass and fail outcomes are contrastive. Waivers stay human-approved. *Unblocked when:* A `TaskPolicy` is declared once at least two real, converged cases exist, and the tier's scored-outcome gate is met. Synthetic episodes are not used.

### 4.4.1 Learner Decision

**Decision:** Build one advisory learner for the Quality Management Plan, as the policy `advise-quality-plan-decision`. The shape is declared with this standard and stays idle, with zero episodes and baseline logits, until real recommendation-versus-decision pairs exist. Synthetic episodes are not used. Building goes through BRD, FDD and a story; this ADR only decides that it is built and on which methodology. The methodology was chosen by hand from the `learning-methodology-selection` skill; when the policy is declared, the selection is recorded as an ADR-024 selection Episode with a human-declared profile. None exists yet and none is invented here.

**What it trains:** The decisions made in this area: the route (full plan, PMP section or N/A with reason), paragraph sufficiency against §4.3, graduation of an over-cap PMP section, and acceptance of a flagged deviation. These four decision types are the maintainer's working list and await confirmation.

**Selected methodology:** #2 softmax bandit with REINFORCE at `low` authority, over a small discrete recommendation set. It fits `learning-methodology-selection` step 3: the decision recurs, the action set is small, and outcomes are contrastive because the human either follows or overrides the recommendation. The reward comes from #5 reward shaping applied to the human decision recorded through #6 durable human override (followed is positive, overridden is negative). The learner trains on the recommendation, not on the approval decision itself.

**Boundaries:**
* Advisory only. The learner recommends and never approves; `approve-subsidiary-plan` stays `full` authority with permanent `requires_human_approval: true`, and its episodes are meant to stay outside REINFORCE (ADR-013 §4.2, ADR-001 §4.2). ADR-001 §4.5 records that this exclusion is not yet enforced in code, so the learner uses its own task id and never shares one with a gate policy.
* The recommendation and the human decision are both recorded; the gap between them is evidence.
* Methodology choice grants no autonomy. The complexity tier is declared by a human in the policy profile and its evidence gate in `autonomy-complexity.md` applies.
* No warm start is assumed. A shared prior across the nine learners (#15, ADR-020) is an untested hypothesis (HYP-AL-008) and is not built; each learner starts cold.
* Positive-only history would plateau REINFORCE (HYP-AL-002). Overrides must therefore be recorded as faithfully as agreements, or the learner is not trained.
* Anchoring and thin data: the learner's recommendation is persisted with a timestamp before the human sees it, so it cannot be altered after the decision. A minimum number of recorded decisions for this area is declared by the maintainer in the policy profile, above the tier minimum, and until it is reached the recommendation is stored but not shown. The number is not set here because no data exists to justify one.

**Plan-specific note:** Gate waivers stay human-approved. Nonconformance triage (rework or escalate) has contrastive pass/fail outcomes, but it is a separate decision from this learner's four types and stays the later policy already named above, declared once two real, converged cases exist.

Source: `learning-methodology-selection` skill and Ideation Document §2.1.

---

### 4.5 PMBOK 8 Alignment

**Source:** *A Guide to the Project Management Body of Knowledge*, Eighth Edition, Plan Scope Management (the guide has no separate Plan Quality Management process) (Figure 2-14). The figure lists end with "Etc.", so the rows below are what the figure names, not an exhaustive set. This subsection records how the ADR relates to the guide; it does not change `depends_on`, `PLAN_DAG` or any threshold.

| | PMBOK 8 | This ADR |
|---|---|---|
| Inputs | As for Plan Scope Management; the quality management plan is one of that process's outputs. | Charter and approved Scope plan (acceptance criteria and Definition of Done) in; Quality Management Plan out, with the gate definitions and verification standards (§4.2). |
| Tools and techniques | Includes test and inspection planning. | Not prescribed; the standard sets structure and measured thresholds and leaves method to the generator and the human reviewer. |
| Outputs | Project management plan updates: quality management plan. | See §4.1 `outputs` and §4.2. |

**Differences and decisions:**

* **No separate process in the guide.** The quality plan comes out of Plan Scope Management, and the guide treats it as a plan component. This repo gives it its own standard and its own approval. Decision: keep it; the dependency on Scope is consistent with the guide, since both are produced together.
* **Quality management plan is a guide input to other plans.** The guide takes it as input to Plan Resource Management, Estimate Costs and Plan Sourcing Strategy. `PLAN_DAG` has no edge from `quality-management` to Resource, Cost or Procurement. Decision: those plans may read it, without a staleness edge. A change to the Quality plan does not make them stale; the human reviewer checks consistency.

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
1. **Gate Automation:** Whether gate results should be registered as episodes by tooling (deferred). *Resolved in practice:* In Epic 13 (Story 13.3, `PlanApprovalRecord`), plan gate results and validation checks are recorded directly into `Episode.metadata` without bespoke database entities.
2. **Waiver Authority:** Whether one waiver authority suffices across gates (deferred to the Charter). *Clarified:* The Project Manager or Sponsor holds waiver authority as declared in the Project Charter; silent waivers remain strictly prohibited under Invariant 3.
3. **PMBOK 8 Domain Re-basing:** PMBOK 8 has seven performance domains, while the repo uses nine plan areas and one learner per area. The nine are kept; whether learners are regrouped by domain is decided in the plan standards ADR.

---

## 9. Amendment Log

| Date | Change | Why |
|---|---|---|
| 2026-10-26 | Proposed | Initial drafting of ADR-029 under the ADR-012 framework, using ADR-025 as the structural template. |
| 2026-10-26 | Learning Methodology Note | Added §4.4 recording the methodology that applies now and the candidates that apply only if their constraints are lifted. |
| 2026-10-28 | Daughter ADR Review & Alignment Draft | Resolved gate automation open question referencing Epic 13 `PlanApprovalRecord` episode persistence, clarified waiver authority, verified single upstream dependency on `scope-management`, and prepared for review. |
| 2026-10-28 | PMBOK 8 Edition Review | Added §4.5 comparing this standard with the guide's planning process: inputs, tools and techniques, outputs, and each difference with a decision. No change to `depends_on`, `PLAN_DAG`, thresholds or the plan files. Proposed, for maintainer confirmation. |
| 2026-10-28 | Learner Decision | Added §4.4.1 deciding to build the `advise-quality-plan-decision` advisory learner on #2 softmax bandit with REINFORCE at `low` authority, fed by #5 and #6. Advisory only; no episodes created. |
| 2026-10-28 | Learner Safeguards and Re-basing Gap | Added to §4.4.1 the anchoring and thin-data safeguard, and to §8 the open question on regrouping learners by PMBOK 8 domain. |
