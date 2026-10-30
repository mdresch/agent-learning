# BRD-031: Stakeholder Engagement Plan Standard

**Source ADR:** [ADR-031](../../adr/ADR-031-stakeholder-engagement-plan-standard.md) — Accepted (2026-10-29, Menno), episode `c6564adb-72de-4262-8309-4949e0745f51`  
**Governing Baseline:** none approved yet; cycle `CYC-001` (ADR-035, Accepted)  
**Status:** Draft (2026-10-29) — derived from Accepted ADR-031; not yet adjudicated via `approve-brd`.  
**Stakeholders:** Menno (Sponsor, Project Manager, maintainer)

## Business Need

The Stakeholder Engagement Plan is a Tier 3 execution-support plan. It is the source of the role names that other plans put in `owner_role`. A register with no required fields cannot be that source, and an engagement gap with no action becomes a late change request. The first baseline has no normative Stakeholder standard. ADR-012 already measures every plan at 150 and 600 words, with caps of 800 and 5,000. ADR-013 marks this plan stale when Scope changes, and no plan depends on it. Neither checks that the plan states a register contract, an engagement scale with current and desired levels, and an action for the gaps.

A reviewer needs three things this requirement adds. A full Stakeholder plan states at least two out-of-scope items. The floors and caps stay at the ADR-012 baseline. The plan states the register contract, the engagement levels, and the engagement actions, or the lint says which one is missing. An advisory policy, `advise-stakeholder-plan-decision`, can later recommend a route, a sufficiency judgment, a graduation, or a treatment of a flagged deviation, and a human still decides. The policy is declared idle: no synthetic episodes, equal baseline logits, and no recommendation shown until the maintainer sets a minimum number of recorded decisions.

## Business Rules (BRU)

- **BRU-031-01 (Stakeholder keeps the baseline lengths):** When `plan_id` is `stakeholder-engagement` and the route is `pmp_section` or `full_plan`, length uses the ADR-012 baseline. A `pmp_section` is 150 to 800 words. A `full_plan` is 600 to 5,000 words. This standard does not raise those floors and does not tighten those caps. A count equal to the floor or the cap is acceptable. A `pmp_section` states at least 1 out-of-scope item, the baseline minimum. A `full_plan` states at least 2 distinct out-of-scope items. A caller may raise the item minimum. A caller cannot lower the full-plan minimum below 2. Every other `plan_id` keeps the numbers that already apply to it.
- **BRU-031-02 (Omission is a tailoring choice):** A Stakeholder route of `not_applicable` is allowed with the approved tailoring rationale (ADR-011). It does not raise `OMISSION_OF_BASE_PLAN`. That flag stays reserved for Scope, Schedule, and Cost. Content checks are skipped for `not_applicable`, as they are today.
- **BRU-031-03 (Register, levels, and actions are present):** Section 1 states the stakeholder register contract. A `pmp_section` states the location and the key fields: identifier, role, interest, and influence. A `full_plan` states the full field list: identifier, name or role, organization or team, project role, interest, influence, current engagement level, desired engagement level, and contact channel reference. Section 2 states the engagement scale and the current and desired levels. A `full_plan` also states that the assessment covers the registered stakeholders, and it states an action, an owner, and a timing for the gaps. A `pmp_section` states the actions. A missing statement is a Tier B `MISSING_REQUIRED_SECTION`. Whether every registered person has a row, and whether each `owner_role` in another plan exists in the register, stay with the human reviewer.
- **BRU-031-04 (Flags stay evidence):** Stakeholder findings use the existing flag codes and the existing next-step table. A floor, cap, or boundary finding is Tier C and is carried to the human. A missing register contract, engagement assessment, or engagement action is Tier B. No Stakeholder finding blocks `approve_plan` by itself (ADR-031 Invariant 4).
- **BRU-031-05 (One idle advisory policy):** The policy id is `advise-stakeholder-plan-decision`. It is a low-authority softmax bandit trained later with REINFORCE on its own recommendations. It has its own task id, equal baseline logits, and zero episodes at declaration. It never shares a task id with `approve-subsidiary-plan` or with the Scope, Schedule, Cost, Risk, Quality, or Resource advisors. It never approves a plan. The owner role defaults to the Project Manager (ADR-031 §4.4.1). `approve-subsidiary-plan` stays full authority with permanent `requires_human_approval: true`. No synthetic episodes are created. No shared prior with the other plan learners is created. The ADR-024 selection episode is recorded by a human when the policy is declared; this requirement does not invent one.
- **BRU-031-06 (The recommendation is fixed before it is shown):** The chosen action and a UTC timestamp are stored before a person sees them, and that record is not rewritten. Until the number of recorded decisions for this policy reaches the minimum in the policy profile, the recommendation is stored and not shown. The ADR does not set that minimum. While it is unset, nothing is shown. When a person later follows the recommendation, the reward on the recommendation is positive. When they override it, the reward is negative. The learner trains on the recommendation, not on `approve_plan`, `reject_plan`, or `request_revision_before_decision`.
- **BRU-031-07 (Engagement control is a writing and review rule):** The plan maps stakeholders to the Charter's sponsor and approver roles and to the Scope deliverables they accept or are affected by. It states how stakeholders are identified and how influence and interest are rated. It states when the register is updated: a new stakeholder, a baseline change, or a role change. The register records roles and work contact references. Private personal data is excluded (ADR-031 Invariant 3). The Project Manager owns the plan and the register. Sponsor and approver roles stay the Charter's. The plan states who approves a baseline change and who is only informed, for Scope, Schedule, and Cost changes (ADR-031 Invariant 2). Review is at each phase boundary and on any approved baseline change. The lint does not check these sentences. No plan in `PLAN_DAG` lists `stakeholder-engagement` as an ancestor. A Scope change marks this plan `STALE_DEPENDENCY` through the existing graph. Resource, Communications, and Risk may be read and do not make this plan stale (ADR-031 §4.5).
- **BRU-031-08 (Storage boundary):** The Stakeholder checks and the recommendation record are plain data. No new `LearningStore` record type (ADR-002). No plan text is copied into learner metadata. The content hash stays out of the plan file. The register is Markdown in the plan, or named there as a companion `Stakeholder-Register.md`. This requirement does not open that companion and does not store the register as its own entity (ADR-031 §8 item 1).

## Stakeholder Success Metrics

| Metric | Target |
|---|---|
| Baseline lengths | A Stakeholder `pmp_section` of 149, 150, 159, 800, and 801 words, and a `full_plan` of 599, 600, 5,000, and 5,001 words, yields the ADR-012 finding and only that finding |
| No raised floor | 159 words on a Stakeholder `pmp_section` is not below floor |
| Full-plan exclusions | One bullet raises the boundary finding; two bullets do not; a 10-token `None:` rationale satisfies the boundary |
| Section minimum | A `pmp_section` with one bullet does not raise the boundary finding |
| Omission | 0 `OMISSION_OF_BASE_PLAN` findings produced by this profile for a `not_applicable` Stakeholder plan |
| Sections | Each missing register contract, engagement assessment, or engagement action produces one Tier B finding; a present statement produces none |
| Graph | The plan depends only on Scope; no plan lists it as an ancestor |
| Flag strength | 0 Stakeholder floor, cap, or boundary findings treated as a block |
| Idle policy | The declared snapshot has task id `advise-stakeholder-plan-decision`, low authority, all logits 0, and 0 episodes |
| Separation | 0 recommendation episodes whose task id is a gate or another plan advisor |
| Anchoring | A stored recommendation keeps its action and timestamp across a second call |
| Withholding | With the minimum unset, 0 recommendations are marked shown |
| Storage | 0 new record types; 0 imports of the store from the new Stakeholder module |

## Out of Scope

- The universal grammar, the nine-plan metadata table, and the next-step table (ADR-012, Epic 12). `owner_role` stays a non-empty string (Story 12.2).
- Raising the Stakeholder floor above 150 or 600, or tightening the cap below 800 or 5,000.
- Tier A detection, the content hash, `approve-subsidiary-plan`, lifecycle projection, and staleness (ADR-013, Epic 13). Orchestration commands (ADR-034).
- The other plan profiles and their advisory policies. This profile does not change their findings.
- Joining `owner_role` values in other plans to register rows. That check stays with the human at `approve-subsidiary-plan` (ADR-031 §8 item 2).
- Opening `Stakeholder-Register.md`, parsing register rows, or scanning the plan for private personal data.
- Adding `PLAN_DAG` edges from Resource, Communications, or Risk. Agreements from Procurement are not a required input (ADR-031 §4.5).
- Merging this plan with Communications (ADR-031 §6).
- A shared prior across the nine plan learners (HYP-AL-008).
- Showing that the learner recommends well. It has no episodes.
