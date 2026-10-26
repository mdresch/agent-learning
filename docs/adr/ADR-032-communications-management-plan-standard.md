# ADR 032: Communications Management Plan Standard

## 1. Executive Brief
Under **ADR-012** (§4.6), the **Communications Management Plan** is an Execution Support (Plan Tier 3) standard. In PMBOK 8 its primary domain is **Stakeholders** with **Governance** as secondary (ADR-012 §4.4), under the *Planning* Focus Area; its legacy process is `10.1`.

This ADR defines what a valid Communications plan must contain: the information each audience needs, cadence, channel and owner for each flow, escalation communication, and the rules for recording decisions communicated. It governs logistics (what, when, by which channel, by whom) while engagement strategy belongs to the Stakeholder Engagement plan (ADR-031).

It inherits the ADR-012 universal contract and specifies only what is Communications-specific. As a Tier 3 plan it keeps the ADR-012 baseline floors and caps.

---

## 2. Status
**Proposed (2026-10-26)** — Plan Tier 3 standard, inheriting ADR-012. Ready for evaluation under `approve-adr`.

---

## 3. Context & Problem Statement
* **Unowned flows:** Reports and notices that have no named owner and cadence stop happening.
* **Decisions lost in channels:** In a governance-driven project, approvals and rationales must land in the record (`Episode.metadata`, version-controlled artifacts), not only in chat or meetings.
* **Audience mismatch:** The same status text rarely suits a sponsor and a developer.
* **Bounded invalidation:** A Communications change does not invalidate other plans (ADR-013 §4.5); a Scope change makes it stale.

---

## 4. Technical Decision

### 4.1 Frontmatter Specification (ADR-012 §4.2)

```yaml
---
plan_id: "communications-management"
plan_name: "Communications Management Plan"
pmbok_edition: "PMBOK 8"
pmbok_focus_area: "Planning"
primary_pmbok_domain: "Stakeholders"
secondary_pmbok_domains:
  - "Governance"
legacy_process: "10.1 Plan Communications Management"
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
  - "docs/project-docs/management-plans/Communications-Management-Plan.md" # if full_plan; .staging/pmp-sections/ if pmp_section
governance_policy: "approve-subsidiary-plan" # "approve-subsidiary-plan" (if full_plan) | "approve-pmp" (if pmp_section)
---
```

### 4.2 Required Content

#### Under `## 1. Intent, Alignment & Boundaries`
* **Charter and Scope Traceability:** Links communication needs to Charter reporting obligations and to Scope deliverables that trigger notices.
* **Audience List:** Audiences by role, referencing the Stakeholder Register (ADR-031).
* **Out-of-Scope Communication Boundaries:** Communications explicitly not covered (for example public marketing, external press). The ADR-012 §4.1 `None: [rationale]` form applies when there are none.

#### Under `## 2. Domain Mechanics & Standards`
* **Communication Matrix:** For each flow: audience, information, purpose, channel, cadence or trigger, and owner role.
* **Decision Recording Rule:** Approvals and baseline-change decisions communicated are recorded in the governance record (episode metadata or a version-controlled artifact); the channel message is a pointer, not the record.
* **Status Reporting Format:** The standard fields in a status report (progress against Schedule milestones, spend against Cost stage, top risks, decisions needed).
* **Issue Escalation Path:** The sequence and time limits by which an urgent issue reaches the accountable decision-maker.
* **Confidentiality Classes:** What may be shared with which audience.

#### Under `## 3. Governance, Control & Decision Rights`
* **Accountability:** The Project Manager owns the plan; each flow has a named owner role.
* **Approval of External or Sponsor-Facing Messages:** The plan states which messages need approval before release and by whom.
* **Review Cadence:** At each phase boundary and when the Stakeholder Register changes materially.
* **Downstream Invalidation:** Communications has no dependent plans in the baseline DAG. An approved Scope baseline change marks it `STALE_DEPENDENCY`.

### 4.3 Floor and Cap Thresholds

Measurement follows ADR-012 §4.3.1. Tier 3 keeps the ADR-012 baseline defaults.

| Metric | Embedded `pmp_section` | Standalone `full_plan` | Flag Type | Trigger Condition |
|---|---|---|---|---|
| **Word Count Floor** | 150 words | 600 words | `FLAG: BELOW_STANDARD_FLOOR` | Content < floor |
| **Word Count Cap** | 800 words | 5,000 words | `FLAG: EXCEEDS_SECTION_CAP` / `FLAG: EXCEEDS_PLAN_CAP` | Content > cap |
| **Out-of-Scope Items** | $\ge 1$ item | $\ge 2$ distinct items | `FLAG: MISSING_BOUNDARY_DEF` | Items < minimum, unless a valid `None: [rationale]` is present |
| **Communication Matrix** | Key flows with audience, cadence, owner | All flows with all fields | `FLAG: MISSING_REQUIRED_SECTION` | Missing matrix |
| **Decision Recording Rule** | Rule stated | Rule with record locations | `FLAG: MISSING_REQUIRED_SECTION` | Missing rule |
| **Escalation Path** | Target named | Sequence and time limits | `FLAG: MISSING_REQUIRED_SECTION` | Missing path |

### 4.4 Learning Methodology

**Now (implemented):** #3 reasoned resolution under `full` authority with permanent `requires_human_approval: true` through `approve-subsidiary-plan` (ADR-013 §4.2), and #6 durable human override. Methodology choice never grants autonomy, and no selection Episode exists yet (ADR-024 is Proposed).

**Possible later:** none identified for this plan. A candidate is reconsidered if decisions about this plan recur with scored outcomes.

Source: `learning-methodology-selection` skill and Ideation Document §2.1.

---

## 5. Architectural Invariants
1. **Every Flow Has an Owner and a Cadence:** A flow without owner or cadence/trigger raises `FLAG: MISSING_REQUIRED_SECTION`.
2. **The Record Is Not the Channel:** Governance decisions are recorded per ADR-002 Invariant #2 and ADR-013; no decision exists only in a channel.
3. **Audiences Resolve to the Register:** Every audience is a role in the Stakeholder Register.
4. **Flags, Not Blocks:** Findings other than Tier A integrity violations are flags resolved by recorded rationale (ADR-012 Invariant 8). Graduation and rejection follow ADR-012 §4.5.

---

## 6. Alternatives Considered
* **Alternative 1: Ad hoc communication with no plan.** *Rejected:* Cadence and ownership decay; decisions are lost.
* **Alternative 2: One communication plan for the whole organization.** *Rejected:* Project-specific audiences and decisions cannot be standardized organization-wide.

---

## 7. Consequences

### Positive
* Reporting is predictable and every decision has a durable record.

### Negative
* Authoring burden for small projects; a lean `pmp_section` form is the intended mitigation.

---

## 8. Open Questions & Future Extensions
1. **Dependency on Stakeholder Engagement:** The baseline DAG makes Communications depend only on Scope. Whether it should also depend on `stakeholder-engagement` (audiences come from its register) is a DAG decision for a later ADR-013 amendment.
2. **Automated Status Reports:** Generating the status report from episodes and baselines (deferred to tooling).

---

## 9. Amendment Log

| Date | Change | Why |
|---|---|---|
| 2026-10-26 | Proposed | Initial drafting of ADR-032 under the ADR-012 framework, using ADR-025 as the structural template. |
| 2026-10-26 | Learning Methodology Note | Added §4.4 recording the methodology that applies now and the candidates that apply only if their constraints are lifted. |
