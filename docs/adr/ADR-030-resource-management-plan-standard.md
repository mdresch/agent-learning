# ADR 030: Resource Management Plan Standard

## 1. Executive Brief
Under **ADR-012** (§4.6), the **Resource Management Plan** is an Execution Support (Plan Tier 3) standard. In PMBOK 8 its primary domain is **Resources** with **Governance** as secondary (ADR-012 §4.4), under the *Planning* Focus Area.

It is downstream of Scope and Schedule in the baseline DAG, because resource needs derive from the work and its timing. This ADR defines what a valid Resource plan must contain: the roles and their accountabilities, how people and agent capacity are allocated to work, tooling and environment assets, acquisition and release, and capacity-conflict resolution.

It inherits the ADR-012 universal contract and specifies only what is Resource-specific. As a Tier 3 plan it keeps the ADR-012 baseline floors and caps.

---

## 2. Status
**Accepted (2026-10-29, Menno)** — Plan Tier 3 standard, inheriting ADR-012. Episode: `de095357-d927-4408-8311-181e158a2abf`.

---

## 3. Context & Problem Statement
* **Accountability must be a human role:** Plans name `owner_role` from the Stakeholder Register (ADR-012 §4.2). Where autonomous agents perform work, the plan must still name the accountable human role.
* **Capacity is implicit:** Allocation that is not stated cannot be compared with Schedule durations, so over-allocation is invisible.
* **Tooling as a resource:** Environments, services and licences constrain delivery and cost; unlisted assets surface as late blockers.
* **Bounded invalidation:** A Resource change does not invalidate Scope, Schedule or Cost (ADR-013 §4.5); a Scope or Schedule change makes Resource stale.
* **Zero Upfront Deliverable or Breakout Prerequisite:** Designing and baselining the Resource Management Plan requires only the Project Charter and Scope/Schedule baselines. It does **not** require pre-executed staffing contracts, tooling procurement, or human breakout sessions in advance; it establishes the role catalogue and capacity-conflict mechanisms for project execution.

---

## 4. Technical Decision

### 4.1 Frontmatter Specification (ADR-012 §4.2)

```yaml
---
plan_id: "resource-management"
plan_name: "Resource Management Plan"
pmbok_edition: "PMBOK 8"
pmbok_focus_area: "Planning"
primary_pmbok_domain: "Resources"
secondary_pmbok_domains:
  - "Governance"
legacy_process: "9.1 Plan Resource Management"
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
  - "docs/project-docs/management-plans/Resource-Management-Plan.md" # if full_plan; .staging/pmp-sections/ if pmp_section
governance_policy: "approve-subsidiary-plan" # "approve-subsidiary-plan" (if full_plan) | "approve-pmp" (if pmp_section)
---
```

### 4.2 Required Content

#### Under `## 1. Intent, Alignment & Boundaries`
* **PMBOK Input, Process & Output (IPO) Specification:**
  * **Inputs:** `Project-Charter.md` (team roles and limits), approved `Scope-Management-Plan.md` (work decomposition), approved `Schedule-Management-Plan.md` (timebox cadence). Zero executed staffing contracts, vendor procurements, or breakout sessions required prior to planning.
  * **Processes:** Role cataloguing, accountable human assignment, agent work boundary restriction, timebox capacity and allocation modeling, tooling/environment tracking, capacity-conflict resolution.
  * **Outputs:** `Resource-Management-Plan.md` (or `.staging/pmp-sections/Resource-Management-Plan.md`), Role Catalogue, agent concurrency/token quotas, and resource onboarding/release schedules.
* **Charter, Scope and Schedule Traceability:** Maps resource needs to Scope epics and Schedule timeboxes.
* **Resource Classes:** Human roles, autonomous agents, and tooling/environment assets, each declared as in or out of this plan.
* **Out-of-Scope Resource Boundaries:** Resources explicitly not managed here (for example shared infrastructure owned by another team). The ADR-012 §4.1 `None: [rationale]` form applies when there are none.

#### Under `## 2. Domain Mechanics & Standards`
* **Role Catalogue:** Each role with responsibilities, accountable owner, and decision rights it holds.
* **Allocation and Capacity:** Planned allocation per role per timebox (or a stated capacity per period), with the basis for the capacity figure.
* **Agent Work Boundaries:** For autonomous agents, the work classes they may perform and the human role that remains accountable; no agent holds a decision that ADR-001 or ADR-008 reserves for a human.
* **Tooling and Environment Assets:** Required services, environments and licences, their owner, and acquisition lead time.
* **Acquisition and Release:** How a resource is added or released and who approves it.

#### Under `## 3. Governance, Control & Decision Rights`
* **Accountability:** The Project Manager owns the plan; role owners are named from the Stakeholder Register.
* **Capacity Conflict Resolution:** When demand exceeds capacity in a timebox, the plan states who decides between descoping (Scope change) and rescheduling (Schedule change); both are Stage 17 events (`approve-adaptation-plan`).
* **Review Cadence:** At each timebox boundary.
* **Downstream Invalidation:** Resource has no dependent plans in the baseline DAG. An approved Scope or Schedule baseline change marks Resource `STALE_DEPENDENCY`.

### 4.3 Floor and Cap Thresholds

Measurement follows ADR-012 §4.3.1. Tier 3 keeps the ADR-012 baseline defaults.

| Metric | Embedded `pmp_section` | Standalone `full_plan` | Flag Type | Trigger Condition |
|---|---|---|---|---|
| **Word Count Floor** | 150 words | 600 words | `FLAG: BELOW_STANDARD_FLOOR` | Content < floor |
| **Word Count Cap** | 800 words | 5,000 words | `FLAG: EXCEEDS_SECTION_CAP` / `FLAG: EXCEEDS_PLAN_CAP` | Content > cap |
| **Out-of-Scope Items** | $\ge 1$ item | $\ge 2$ distinct items | `FLAG: MISSING_BOUNDARY_DEF` | Items < minimum, unless a valid `None: [rationale]` is present |
| **Role Catalogue** | Roles with accountable owner | Roles, responsibilities, decision rights | `FLAG: MISSING_REQUIRED_SECTION` | Missing catalogue |
| **Allocation & Capacity** | Capacity statement | Per-role per-timebox allocation with basis | `FLAG: MISSING_REQUIRED_SECTION` | Missing allocation |
| **Tooling Assets** | Asset list | Assets, owners, lead times | `FLAG: MISSING_REQUIRED_SECTION` | Missing assets |

### 4.4 Learning Methodology

**Now (implemented):** #3 reasoned resolution under `full` authority with permanent `requires_human_approval: true` through `approve-subsidiary-plan` (ADR-013 §4.2), and #6 durable human override. Methodology choice never grants autonomy, and no selection Episode exists yet (ADR-024 is Accepted).

**Possible later:** none identified for this plan. A candidate is reconsidered if decisions about this plan recur with scored outcomes.

### 4.4.1 Learner Decision

**Decision:** Build one advisory learner for the Resource Management Plan, as the policy `advise-resource-plan-decision`. The shape is declared with this standard and stays idle, with zero episodes and baseline logits, until real recommendation-versus-decision pairs exist. Synthetic episodes are not used. Building goes through BRD, FDD and a story; this ADR only decides that it is built and on which methodology. The methodology was chosen by hand from the `learning-methodology-selection` skill; when the policy is declared, the selection is recorded as an ADR-024 selection Episode with a human-declared profile. None exists yet and none is invented here.

**What it trains:** The decisions made in this area: the route (full plan, PMP section or N/A with reason), paragraph sufficiency against §4.3, graduation of an over-cap PMP section, and acceptance of a flagged deviation. These four decision types are the maintainer's working list and await confirmation.

**Selected methodology:** #2 softmax bandit with REINFORCE at `low` authority, over a small discrete recommendation set. It fits `learning-methodology-selection` step 3: the decision recurs, the action set is small, and outcomes are contrastive because the human either follows or overrides the recommendation. The reward comes from #5 reward shaping applied to the human decision recorded through #6 durable human override (followed is positive, overridden is negative). The learner trains on the recommendation, not on the approval decision itself.

**Boundaries:**
* Advisory only. The learner recommends and never approves; `approve-subsidiary-plan` stays `full` authority with permanent `requires_human_approval: true`, and its episodes are meant to stay outside REINFORCE (ADR-013 §4.2, ADR-001 §4.2). ADR-001 §4.5 records that this exclusion is not yet enforced in code, so the learner uses its own task id and never shares one with a gate policy.
* The recommendation and the human decision are both recorded; the gap between them is evidence.
* Methodology choice grants no autonomy. The complexity tier is declared by a human in the policy profile and its evidence gate in `autonomy-complexity.md` applies.
* No warm start is assumed. A shared prior across the nine learners (#15, ADR-020) is an untested hypothesis (HYP-AL-008) and is not built; each learner starts cold.
* Positive-only history would plateau REINFORCE (HYP-AL-002). Overrides must therefore be recorded as faithfully as agreements, or the learner is not trained.
* Anchoring and thin data: the learner's recommendation is persisted with a timestamp before the human sees it, so it cannot be altered after the decision. A minimum number of recorded decisions for this area is declared by the maintainer in the policy profile, above the tier minimum, and until it is reached the recommendation is stored but not shown. The number is not set here because no data exists to justify one.

**Plan-specific note:** The plan has two possible owners (materials to Procurement, human resources to HR). Each recommendation-versus-decision pair records the deciding department, and the learner keeps them separate so departments are not blended. No plan-specific later candidate is identified.

Source: `learning-methodology-selection` skill and Ideation Document §2.1.

---

### 4.5 PMBOK 8 Alignment

**Source:** *A Guide to the Project Management Body of Knowledge*, Eighth Edition, Plan Resource Management (Figure 2-41). The figure lists end with "Etc.", so the rows below are what the figure names, not an exhaustive set. This subsection records how the ADR relates to the guide; it does not change `depends_on`, `PLAN_DAG` or any threshold.

| | PMBOK 8 | This ADR |
|---|---|---|
| Inputs | Project charter; project management plan (quality management plan, scope baseline); project documents (project schedule, requirements documentation, risk register, stakeholder register); enterprise environmental factors; organizational process assets. | Charter, approved Scope and Schedule plans in; Resource Management Plan out, with the role catalogue and agent quotas (§4.2). |
| Tools and techniques | Expert judgment; data gathering (interviews); data analysis (SWOT); data representation (hierarchical charts, responsibility assignment matrix, text-oriented formats); organizational theory; meetings; green human resource management; resource-based view. | Not prescribed; the standard sets structure and measured thresholds and leaves method to the generator and the human reviewer. |
| Outputs | Resource management plan; team charter; project document updates (assumption log, risk register). | See §4.1 `outputs` and §4.2. |

**Differences and decisions:**

* **Schedule input is stronger here.** The guide reads the project schedule (a document); `PLAN_DAG` makes Resource depend on the approved Schedule Management Plan. Decision: keep; the plan's capacity model needs the timebox cadence.
* **Quality management plan is a guide input; not a dependency here.** Decision: Resource may read it, without a staleness edge (see ADR-029).
* **Team charter** is a guide output. This ADR has none. Decision: whether a team charter is needed is an open question for the maintainer; the role catalogue and the Charter's approver roles cover part of it.
* **Responsibility assignment matrix** is a guide technique. The accountable-human assignment in §4.2 overlaps with it; the ADR does not require a RACI format.

## 5. Architectural Invariants
1. **Every Role Has an Accountable Human:** Agent work never lacks a named accountable human role.
2. **Allocation Is Comparable With Schedule:** Allocation uses the Schedule plan's timebox unit.
3. **No Agent Holds a Reserved Human Decision:** Agent work boundaries cannot grant authority reserved by ADR-001 or ADR-008.
4. **Flags, Not Blocks:** Findings other than Tier A integrity violations are flags resolved by recorded rationale (ADR-012 Invariant 8). Graduation and rejection follow ADR-012 §4.5.

---

## 6. Alternatives Considered
* **Alternative 1: Treat agents as unmanaged tooling.** *Rejected:* Hides the accountability chain.
* **Alternative 2: Fold resources into the Schedule plan.** *Rejected:* Violates LL-015; capacity shortfalls cannot be separated from estimation error.

---

## 7. Consequences

### Positive
* Over-allocation and unowned tooling become visible before they block delivery.

### Negative
* Authoring burden; capacity figures need an evidence basis that small teams may find heavy.

---

## 8. Open Questions & Future Extensions
1. **Agent Capacity Units:** How agent capacity (for example token or run budgets) should be expressed alongside human capacity. *Clarified:* Expressed as API token limits, model context quotas, or concurrent runner slots allocated per timebox.
2. **Cost Link:** Whether Resource should become a dependency of Cost (the baseline has no such edge). *Resolved in PLAN_DAG:* In accordance with FDD-013 §2.1 and `standards.py`, Cost does NOT depend on Resource (`PLAN_DAG['cost-management'] = ('scope-management', 'schedule-management')`). Resource Management remains a Tier 3 Execution Support plan downstream of Scope and Schedule. Fixed-stage envelopes govern costs rather than bottom-up rate rollups, avoiding cyclic dependencies and preserving Tier 1 baseline stability.
3. **PMBOK 8 Domain Re-basing:** PMBOK 8 has seven performance domains, while the repo uses nine plan areas and one learner per area. The nine are kept; whether learners are regrouped by domain is decided in the plan standards ADR.

---

## 9. Amendment Log

| Date | Change | Why |
|---|---|---|
| 2026-10-26 | Proposed | Initial drafting of ADR-030 under the ADR-012 framework, using ADR-025 as the structural template. |
| 2026-10-26 | Learning Methodology Note | Added §4.4 recording the methodology that applies now and the candidates that apply only if their constraints are lifted. |
| 2026-10-28 | Daughter ADR Review & Alignment Draft | Resolved Cost-Resource DAG dependency open question confirming Cost does not depend on Resource in `PLAN_DAG`, clarified agent capacity unit metrics, verified `depends_on`, and prepared for review. |
| 2026-10-28 | PMBOK 8 Edition Review | Added §4.5 comparing this standard with the guide's planning process: inputs, tools and techniques, outputs, and each difference with a decision. No change to `depends_on`, `PLAN_DAG`, thresholds or the plan files. Proposed, for maintainer confirmation. |
| 2026-10-28 | Learner Decision | Added §4.4.1 deciding to build the `advise-resource-plan-decision` advisory learner on #2 softmax bandit with REINFORCE at `low` authority, fed by #5 and #6. Advisory only; no episodes created. |
| 2026-10-28 | Learner Safeguards and Re-basing Gap | Added to §4.4.1 the anchoring and thin-data safeguard, and to §8 the open question on regrouping learners by PMBOK 8 domain. |
| 2026-10-29 | **Accepted by Menno** | Formally adjudicated and accepted through `approve-adr`; robust utility 0.706, expected utility 0.782; Episode `de095357-d927-4408-8311-181e158a2abf`. |
