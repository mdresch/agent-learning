# ADR 031: Stakeholder Engagement Plan Standard

## 1. Executive Brief
Under **ADR-012** (§4.6), the **Stakeholder Engagement Plan** is an Execution Support (Plan Tier 3) standard. In PMBOK 8 its primary domain is **Stakeholders** with **Governance** as secondary (ADR-012 §4.4), under the *Planning* Focus Area; its legacy process is `13.2`.

This ADR defines what a valid Stakeholder Engagement plan must contain: a stakeholder register contract, assessment of influence and interest, current and desired engagement levels, engagement actions with owners, and rules for keeping the register current. The register is also the source of the role names used in `owner_role` across all plans (ADR-012 §4.2).

It inherits the ADR-012 universal contract and specifies only what is Stakeholder-specific. As a Tier 3 plan it keeps the ADR-012 baseline floors and caps.

---

## 2. Status
**Proposed (2026-10-26)** — Plan Tier 3 standard, inheriting ADR-012. Ready for evaluation under `approve-adr`.

---

## 3. Context & Problem Statement
* **Roles reference the register:** `owner_role`, deliverable acceptance authority (ADR-025) and risk owners (ADR-028) all name roles "from the Stakeholder Register". The register's required fields must therefore be defined.
* **Engagement drift:** A stakeholder who is unsupportive or unaware of a baseline change becomes a late change request.
* **Personal data:** Registers can hold personal information; the plan must limit what is recorded.
* **Bounded invalidation:** A Stakeholder change does not invalidate other plans (ADR-013 §4.5); a Scope change makes it stale.
* **Zero Upfront Deliverable or Breakout Prerequisite:** Designing and baselining the Stakeholder Engagement Plan requires only the Project Charter and Scope baseline. It does **not** require pre-conducted stakeholder interview breakout sessions in advance; it establishes the stakeholder register contract and engagement mechanisms for the lifecycle.

---

## 4. Technical Decision

### 4.1 Frontmatter Specification (ADR-012 §4.2)

```yaml
---
plan_id: "stakeholder-engagement"
plan_name: "Stakeholder Engagement Plan"
pmbok_edition: "PMBOK 8"
pmbok_focus_area: "Planning"
primary_pmbok_domain: "Stakeholders"
secondary_pmbok_domains:
  - "Governance"
legacy_process: "13.2 Plan Stakeholder Engagement"
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
  - "docs/project-docs/management-plans/Stakeholder-Engagement-Plan.md" # if full_plan; .staging/pmp-sections/ if pmp_section
governance_policy: "approve-subsidiary-plan" # "approve-subsidiary-plan" (if full_plan) | "approve-pmp" (if pmp_section)
---
```

### 4.2 Required Content

#### Under `## 1. Intent, Alignment & Boundaries`
* **PMBOK Input, Process & Output (IPO) Specification:**
  * **Inputs:** `Project-Charter.md` (sponsor and approver roles), approved `Scope-Management-Plan.md` (affected deliverables). Zero stakeholder interviews or breakout sessions required prior to planning.
  * **Processes:** Stakeholder identification, influence/interest grid mapping, engagement level gap assessment, targeted engagement action planning, decision rights matrix formulation.
  * **Outputs:** `Stakeholder-Engagement-Plan.md` (or `.staging/pmp-sections/Stakeholder-Engagement-Plan.md`), Stakeholder Register schema contract, role source registry for `owner_role` values, and decision consultation protocols.
* **Charter and Scope Traceability:** Maps stakeholders to the Charter's sponsor and approver roles and to Scope deliverables they accept or are affected by.
* **Stakeholder Register Contract:** Location of the register and minimum fields: identifier, name or role, organization or team, project role, interest, influence, current engagement level, desired engagement level, and contact channel reference.
* **Out-of-Scope Engagement Boundaries:** Groups explicitly not engaged (for example end users outside the pilot). The ADR-012 §4.1 `None: [rationale]` form applies when there are none.

#### Under `## 2. Domain Mechanics & Standards`
* **Identification and Assessment:** How stakeholders are identified and how influence and interest are rated, using a stated scale.
* **Engagement Levels:** The level scale (for example unaware, resistant, neutral, supportive, leading) and the gap between current and desired level per stakeholder.
* **Engagement Actions:** For each gap, an action, an owner role, and a timing tied to a Schedule milestone or timebox.
* **Register Maintenance:** Triggers for update (new stakeholder, baseline change, role change).
* **Data Minimization:** The register records roles and work contact references; private personal data is excluded.

#### Under `## 3. Governance, Control & Decision Rights`
* **Accountability:** The Project Manager owns the plan and register. Sponsor and approver roles are fixed by the Charter.
* **Decision Rights:** The plan states who is consulted and who must approve for each class of baseline change (aligned with ADR-025, ADR-026, ADR-027), distinguishing approval from notification.
* **Review Cadence:** At each phase boundary and on any approved baseline change.
* **Downstream Invalidation:** Stakeholder Engagement has no dependent plans in the baseline DAG. An approved Scope baseline change marks it `STALE_DEPENDENCY`.

### 4.3 Floor and Cap Thresholds

Measurement follows ADR-012 §4.3.1. Tier 3 keeps the ADR-012 baseline defaults.

| Metric | Embedded `pmp_section` | Standalone `full_plan` | Flag Type | Trigger Condition |
|---|---|---|---|---|
| **Word Count Floor** | 150 words | 600 words | `FLAG: BELOW_STANDARD_FLOOR` | Content < floor |
| **Word Count Cap** | 800 words | 5,000 words | `FLAG: EXCEEDS_SECTION_CAP` / `FLAG: EXCEEDS_PLAN_CAP` | Content > cap |
| **Out-of-Scope Items** | $\ge 1$ item | $\ge 2$ distinct items | `FLAG: MISSING_BOUNDARY_DEF` | Items < minimum, unless a valid `None: [rationale]` is present |
| **Register Contract** | Location and key fields | Full field list | `FLAG: MISSING_REQUIRED_SECTION` | Missing contract |
| **Engagement Levels & Gaps** | Scale and current/desired for key stakeholders | Scale and current/desired for all registered stakeholders | `FLAG: MISSING_REQUIRED_SECTION` | Missing assessment |
| **Engagement Actions** | Actions for key gaps | Action, owner, timing for every gap | `FLAG: MISSING_REQUIRED_SECTION` | Missing actions |

### 4.4 Learning Methodology

**Now (implemented):** #3 reasoned resolution under `full` authority with permanent `requires_human_approval: true` through `approve-subsidiary-plan` (ADR-013 §4.2), and #6 durable human override. Methodology choice never grants autonomy, and no selection Episode exists yet (ADR-024 is Accepted).

**Possible later:** none identified for this plan. A candidate is reconsidered if decisions about this plan recur with scored outcomes.

### 4.4.1 Learner Decision

**Decision:** Build one advisory learner for the Stakeholder Engagement Management Plan, as the policy `advise-stakeholder-plan-decision`. The shape is declared with this standard and stays idle, with zero episodes and baseline logits, until real recommendation-versus-decision pairs exist. Synthetic episodes are not used. Building goes through BRD, FDD and a story; this ADR only decides that it is built and on which methodology. The methodology was chosen by hand from the `learning-methodology-selection` skill; when the policy is declared, the selection is recorded as an ADR-024 selection Episode with a human-declared profile. None exists yet and none is invented here.

**What it trains:** The decisions made in this area: the route (full plan, PMP section or N/A with reason), paragraph sufficiency against §4.3, graduation of an over-cap PMP section, and acceptance of a flagged deviation. These four decision types are the maintainer's working list and await confirmation.

**Selected methodology:** #2 softmax bandit with REINFORCE at `low` authority, over a small discrete recommendation set. It fits `learning-methodology-selection` step 3: the decision recurs, the action set is small, and outcomes are contrastive because the human either follows or overrides the recommendation. The reward comes from #5 reward shaping applied to the human decision recorded through #6 durable human override (followed is positive, overridden is negative). The learner trains on the recommendation, not on the approval decision itself.

**Boundaries:**
* Advisory only. The learner recommends and never approves; `approve-subsidiary-plan` stays `full` authority with permanent `requires_human_approval: true`, and its episodes are meant to stay outside REINFORCE (ADR-013 §4.2, ADR-001 §4.2). ADR-001 §4.5 records that this exclusion is not yet enforced in code, so the learner uses its own task id and never shares one with a gate policy.
* The recommendation and the human decision are both recorded; the gap between them is evidence.
* Methodology choice grants no autonomy. The complexity tier is declared by a human in the policy profile and its evidence gate in `autonomy-complexity.md` applies.
* No warm start is assumed. A shared prior across the nine learners (#15, ADR-020) is an untested hypothesis (HYP-AL-008) and is not built; each learner starts cold.
* Positive-only history would plateau REINFORCE (HYP-AL-002). Overrides must therefore be recorded as faithfully as agreements, or the learner is not trained.
* Anchoring and thin data: the learner's recommendation is persisted with a timestamp before the human sees it, so it cannot be altered after the decision. A minimum number of recorded decisions for this area is declared by the maintainer in the policy profile, above the tier minimum, and until it is reached the recommendation is stored but not shown. The number is not set here because no data exists to justify one.

**Plan-specific note:** No plan-specific later candidate is identified. The owner role is declared per knowledge area and defaults to the Project Manager.

Source: `learning-methodology-selection` skill and Ideation Document §2.1.

---

### 4.5 PMBOK 8 Alignment

**Source:** *A Guide to the Project Management Body of Knowledge*, Eighth Edition, Plan Stakeholder Engagement (Figure 2-34). The figure lists end with "Etc.", so the rows below are what the figure names, not an exhaustive set. This subsection records how the ADR relates to the guide; it does not change `depends_on`, `PLAN_DAG` or any threshold.

| | PMBOK 8 | This ADR |
|---|---|---|
| Inputs | Project charter; project management plan (resource, communications and risk management plans); project documents (assumption log, change log, issue log, project schedule, risk register, stakeholder register); agreements; enterprise environmental factors; organizational process assets. | Charter and approved Scope plan in; Stakeholder Engagement Plan out, with the register schema and consultation protocols (§4.2). |
| Tools and techniques | Expert judgment; data gathering (benchmarking); data analysis (assumption and constraint analysis, root cause analysis); decision-making (prioritization and ranking); data representation (mind mapping, stakeholder engagement assessment matrix); meetings. | Not prescribed; the standard sets structure and measured thresholds and leaves method to the generator and the human reviewer. |
| Outputs | Project management plan updates: stakeholder engagement plan. | See §4.1 `outputs` and §4.2. |

**Differences and decisions:**

* **Three plan inputs in the guide, one here.** The guide reads the resource, communications and risk plans. `PLAN_DAG` gives Stakeholder Engagement only `scope-management`. The earlier alignment review verified `depends_on: [scope-management]`, and keeping it avoids cascading re-approval (the reason ADR-032's review gave for its own). Decision: keep. Resource, Communications and Risk are optional reading with no staleness edge; the human reviewer checks consistency at approval.
* **Engagement assessment matrix** is a guide technique. The engagement-level gap assessment in §4.2 is the equivalent.
* **Agreements** are a guide input. They are created through Procurement (ADR-033); this ADR does not require them.

## 5. Architectural Invariants
1. **Register Is the Role Source:** `owner_role` values across plans must exist as roles in the register.
2. **Approval Is Distinct From Notification:** Decision rights state which stakeholders approve and which are only informed.
3. **Data Minimization:** Private personal data is not stored in the register or the plan.
4. **Flags, Not Blocks:** Findings other than Tier A integrity violations are flags resolved by recorded rationale (ADR-012 Invariant 8). Graduation and rejection follow ADR-012 §4.5.

---

## 6. Alternatives Considered
* **Alternative 1: Register only, no plan.** *Rejected:* Records who exists but not how engagement gaps are closed.
* **Alternative 2: Merge with Communications.** *Rejected:* Engagement strategy (why and how deeply) differs from communication logistics (what, when, how); separate plans keep credit assignment clear (LL-015).

---

## 7. Consequences

### Positive
* Role names across plans resolve to one register; approval versus notification is explicit.

### Negative
* Authoring burden; the register needs maintenance or it silently decays.

---

## 8. Open Questions & Future Extensions
1. **Register Location:** Whether the register is a Markdown artifact or structured data with a validator (deferred to tooling). *Resolved in practice:* In accordance with ADR-002 Invariant #2 and ADR-034 anti-sprawl, the register is maintained as a Markdown table within `Stakeholder-Engagement-Plan.md` (or companion `Stakeholder-Register.md`), validated by text linting rather than custom database entities.
2. **Role Cross-Check:** A linter check that every `owner_role` in plan frontmatter exists in the register (deferred to tooling). *Clarified:* Story 12.2 / FDD-012 enforces non-empty string format for `owner_role`; semantic consistency between frontmatter `owner_role` and register entries is verified during `approve-subsidiary-plan` human review.
3. **PMBOK 8 Domain Re-basing:** PMBOK 8 has seven performance domains, while the repo uses nine plan areas and one learner per area. The nine are kept; whether learners are regrouped by domain is decided in the plan standards ADR.

---

## 9. Amendment Log

| Date | Change | Why |
|---|---|---|
| 2026-10-26 | Proposed | Initial drafting of ADR-031 under the ADR-012 framework, using ADR-025 as the structural template. |
| 2026-10-26 | Learning Methodology Note | Added §4.4 recording the methodology that applies now and the candidates that apply only if their constraints are lifted. |
| 2026-10-28 | Daughter ADR Review & Alignment Draft | Resolved register location and role cross-check questions under ADR-002/034, verified `depends_on: [scope-management]`, and prepared for review. |
| 2026-10-28 | PMBOK 8 Edition Review | Added §4.5 comparing this standard with the guide's planning process: inputs, tools and techniques, outputs, and each difference with a decision. No change to `depends_on`, `PLAN_DAG`, thresholds or the plan files. Proposed, for maintainer confirmation. |
| 2026-10-28 | Learner Decision | Added §4.4.1 deciding to build the `advise-stakeholder-plan-decision` advisory learner on #2 softmax bandit with REINFORCE at `low` authority, fed by #5 and #6. Advisory only; no episodes created. |
| 2026-10-28 | Learner Safeguards and Re-basing Gap | Added to §4.4.1 the anchoring and thin-data safeguard, and to §8 the open question on regrouping learners by PMBOK 8 domain. |
