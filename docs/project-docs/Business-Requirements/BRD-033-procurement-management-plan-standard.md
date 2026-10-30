# BRD-033: Procurement Management Plan Standard

**Source ADR:** [ADR-033](../../adr/ADR-033-procurement-management-plan-standard.md) — Accepted (2026-10-29, Menno), episode `7362459e-b596-4f85-8872-5b7063eef015`  
**Governing Baseline:** none approved yet; cycle `CYC-001` (ADR-035, Accepted)  
**Status:** Approved (2026-10-30, Menno) — derived from Accepted ADR-033; adjudicated via `approve-brd` (robust utility 0.735, episode `05e3d9be-4311-4138-a116-086702be87ef`).  
**Stakeholders:** Menno (Sponsor, Project Manager, maintainer)

## Business Need

The Procurement Management Plan is a Tier 3 execution-support plan. For this project, procurement is the acquisition of external services, models, libraries, and licences. A library chosen with no intake record, no make-or-buy factors, and no licence check becomes hidden cost and lock-in. The first baseline has no normative Procurement standard. ADR-012 already measures every plan at 150 and 600 words, with caps of 800 and 5,000. ADR-013 marks this plan stale when Scope or Cost changes, and no plan depends on it. Neither checks that the plan states make-or-buy criteria, a dependency intake rule, and contract and licence checks.

A reviewer needs three things this requirement adds. A full Procurement plan states at least two out-of-scope items. The floors and caps stay at the ADR-012 baseline. Inheriting ADR-027 means this plan follows Cost for staleness, and it does not adopt Cost's tighter floors or caps. The plan states the make-or-buy criteria, the intake rule, and the contract and licence checks, or the lint says which one is missing. An advisory policy, `advise-procurement-plan-decision`, can later recommend a route, a sufficiency judgment, a graduation, or a treatment of a flagged deviation, and a human still decides. The policy is declared idle: no synthetic episodes, equal baseline logits, and no recommendation shown until the maintainer sets a minimum number of recorded decisions. The deciding role on each pair is recorded. The policy keeps one logit map.

## Business Rules (BRU)

- **BRU-033-01 (Procurement keeps the baseline lengths):** When `plan_id` is `procurement-management` and the route is `pmp_section` or `full_plan`, length uses the ADR-012 baseline. A `pmp_section` is 150 to 800 words. A `full_plan` is 600 to 5,000 words. This standard does not raise those floors and does not tighten those caps. A count equal to the floor or the cap is acceptable. A `pmp_section` states at least 1 out-of-scope item, the baseline minimum. A `full_plan` states at least 2 distinct out-of-scope items. A caller may raise the item minimum. A caller cannot lower the full-plan minimum below 2. Every other `plan_id` keeps the numbers that already apply to it.
- **BRU-033-02 (Omission is a tailoring choice):** A Procurement route of `not_applicable` is allowed with the approved tailoring rationale (ADR-011). It does not raise `OMISSION_OF_BASE_PLAN`. That flag stays reserved for Scope, Schedule, and Cost. Content checks are skipped for `not_applicable`, as they are today.
- **BRU-033-03 (Criteria, intake rule, and licence checks are present):** Section 2 states the make-or-buy criteria, the dependency intake rule, and the contract and licence checks. A `pmp_section` names the make-or-buy factors. A `full_plan` also names how those factors are weighted. A `pmp_section` states the intake rule. A `full_plan` also states the justification fields: the need, the alternatives considered, the licence, the maintenance status, and the exit path. Both routes list the checks: licence compatibility, usage limits, data handling and retention, and change-of-terms rights. A `full_plan` also names the verification owner. A missing statement is a Tier B `MISSING_REQUIRED_SECTION`. The lint reads those three statements from Section 2 only. An incomplete finding is raised only when the statement is present and a required part of it is absent. It is not raised on a statement that is already missing.
- **BRU-033-04 (Flags stay evidence):** Procurement findings use the existing flag codes and the existing next-step table. A floor, cap, or boundary finding is Tier C and is carried to the human. A missing make-or-buy statement, intake rule, or contract and licence check is Tier B. No Procurement finding blocks `approve_plan` by itself (ADR-033 Invariant 4).
- **BRU-033-05 (One idle advisory policy):** The policy id is `advise-procurement-plan-decision`. It is a low-authority softmax bandit trained later with REINFORCE on its own recommendations. It has its own task id, one logit map, equal baseline logits, and zero episodes at declaration. It never shares a task id with `approve-subsidiary-plan` or with the Scope, Schedule, Cost, Risk, Quality, Resource, Stakeholder, or Communications advisors. It never approves a plan. The deciding role is recorded with each recommendation. That role selects no second map. `approve-subsidiary-plan` stays full authority with permanent `requires_human_approval: true`. No synthetic episodes are created. No shared prior with the other plan learners is created. The ADR-024 selection episode is recorded by a human when the policy is declared; this requirement does not invent one.
- **BRU-033-06 (The recommendation is fixed before it is shown):** The chosen action, the deciding role, and a UTC timestamp are stored before a person sees them, and that record is not rewritten. Until the number of recorded decisions for this policy reaches the minimum in the policy profile, the recommendation is stored and not shown. The ADR does not set that minimum. While it is unset, nothing is shown. When a person later follows the recommendation, the reward on the recommendation is positive. When they override it, the reward is negative. The learner trains on the recommendation, not on `approve_plan`, `reject_plan`, or `request_revision_before_decision`.
- **BRU-033-07 (Procurement control is a writing and review rule):** The plan maps acquisitions to Scope deliverables and to Cost categories and the Cost envelope. It names the acquisition classes in play. It states supplier selection criteria and how supplier performance is monitored, including the steps for replacing a supplier. The Project Manager owns the plan. An acquisition above the threshold the plan declares needs Sponsor or Charter Approver authorization. Below that threshold, Project Manager discretion is logged. ADR-033 §8 item 1 points at the Cost envelope for the default, including a single contract or annual service above 10% of stage contingency. The lint does not read that percentage and does not open the Cost plan. An acquisition that changes the Cost envelope or a stage budget is an integrated change-control event (ADR-033 Invariant 2). Adding an external dependency without the intake record is evidence in the approval or change episode, not a new stored entity (ADR-033 Invariant 1, ADR-002). Every external service dependency states how it would be replaced (ADR-033 Invariant 3). Review is at each acquisition decision and at phase close. The lint does not check these sentences beyond the Section 2 statements in BRU-033-03. `PLAN_DAG["procurement-management"]` is `("scope-management", "cost-management")` and does not list `resource-management`. No plan lists `procurement-management` as an ancestor. A Scope or Cost change marks this plan `STALE_DEPENDENCY` through the existing graph. A Procurement change marks no other plan stale. Schedule, Quality, and Resource may be read and do not make this plan stale (ADR-033 §4.5).
- **BRU-033-08 (Storage boundary):** The Procurement checks and the recommendation record are plain data. No new `LearningStore` record type (ADR-002). No plan text is copied into learner metadata. The content hash stays out of the plan file. This requirement does not open the Charter, the Scope plan, the Cost plan, or `pyproject.toml`, and it does not write into another plan.

## Stakeholder Success Metrics

| Metric | Target |
|---|---|
| Baseline lengths | A Procurement `pmp_section` of 149, 150, 159, 800, and 801 words, and a `full_plan` of 599, 600, 5,000, and 5,001 words, yields the ADR-012 finding and only that finding |
| No raised floor | 159 words on a Procurement `pmp_section` is not below floor |
| Full-plan exclusions | One bullet raises the boundary finding; two bullets do not; a 10-token `None:` rationale satisfies the boundary |
| Section minimum | A `pmp_section` with one bullet does not raise the boundary finding |
| Omission | 0 `OMISSION_OF_BASE_PLAN` findings produced by this profile for a `not_applicable` Procurement plan |
| Sections | Each missing make-or-buy statement, intake rule, or contract and licence check produces one Tier B finding; a present statement with its required parts produces none; a missing statement does not also produce the incomplete finding |
| Graph | The plan depends on Scope and Cost; that dependency tuple does not contain Resource; no plan lists Procurement as an ancestor |
| Flag strength | 0 Procurement floor, cap, or boundary findings treated as a block |
| Idle policy | The declared snapshot has task id `advise-procurement-plan-decision`, low authority, one logit map, all logits 0, and 0 episodes |
| Separation | 0 recommendation episodes whose task id is a gate or another plan advisor |
| Anchoring | A stored recommendation keeps its action, deciding role, and timestamp across a second call |
| Withholding | With the minimum unset, 0 recommendations are marked shown |
| Storage | 0 new record types; 0 imports of the store from the new Procurement module |

## Out of Scope

- The universal grammar, the nine-plan metadata table, and the next-step table (ADR-012, Epic 12). `owner_role` stays a non-empty string (Story 12.2).
- Raising the Procurement floor above 150 or 600, or tightening the cap below 800 or 5,000. Cost's tighter floors and caps stay on the Cost profile.
- Tier A detection, the content hash, `approve-subsidiary-plan`, lifecycle projection, and staleness (ADR-013, Epic 13). Orchestration commands (ADR-034).
- The other plan profiles and their advisory policies. This profile does not change their findings. The Resource policy's department id `procurement` is a different policy and a different logit map.
- Cross-checking `pyproject.toml` against intake records (ADR-033 §8 item 2).
- Opening the Cost plan to read the envelope, the 10% contingency sentence, or a stage budget.
- Adding a `PLAN_DAG` edge from Resource, Schedule, or Quality.
- Supplier selection scorecards, supplier performance monitoring, and the replacement steps, beyond the word `exit` on a full-plan intake rule.
- A second logit map, one per deciding role. The role is recorded. The logits stay one map.
- A shared prior across the nine plan learners (HYP-AL-008).
- Showing that the learner recommends well. It has no episodes.
