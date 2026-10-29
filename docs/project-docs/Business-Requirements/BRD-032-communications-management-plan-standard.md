# BRD-032: Communications Management Plan Standard

**Source ADR:** [ADR-032](../../adr/ADR-032-communications-management-plan-standard.md) — Proposed (2026-10-26); ready for `approve-adr`  
**Governing Baseline:** none approved yet; cycle `CYC-001` (ADR-035, Proposed)  
**Status:** Draft (2026-10-29) — derived from Proposed ADR-032; not yet adjudicated via `approve-brd`. Adjudication waits until ADR-032 is accepted.  
**Stakeholders:** Menno (Sponsor, Project Manager, maintainer)

## Business Need

The Communications Management Plan is a Tier 3 execution-support plan. It states which audience receives which information, on which cadence and channel, and who owns the flow. A notice with no owner and no cadence stops happening. A decision that lives only in a channel is not a governance record. The first baseline has no normative Communications standard. ADR-012 already measures every plan at 150 and 600 words, with caps of 800 and 5,000. ADR-013 marks this plan stale when Scope changes, and no plan depends on it. Neither checks that the plan states a communication matrix, a decision-recording rule, and an escalation path.

A reviewer needs three things this requirement adds. A full Communications plan states at least two out-of-scope items. The floors and caps stay at the ADR-012 baseline. The plan states the matrix, the recording rule, and the escalation path, or the lint says which one is missing. An advisory policy, `advise-communications-plan-decision`, can later recommend a route, a sufficiency judgment, a graduation, or a treatment of a flagged deviation, and a human still decides. The policy is declared idle: no synthetic episodes, equal baseline logits, and no recommendation shown until the maintainer sets a minimum number of recorded decisions. The deciding role on each pair is recorded. The policy keeps one logit map.

## Business Rules (BRU)

- **BRU-032-01 (Communications keeps the baseline lengths):** When `plan_id` is `communications-management` and the route is `pmp_section` or `full_plan`, length uses the ADR-012 baseline. A `pmp_section` is 150 to 800 words. A `full_plan` is 600 to 5,000 words. This standard does not raise those floors and does not tighten those caps. A count equal to the floor or the cap is acceptable. A `pmp_section` states at least 1 out-of-scope item, the baseline minimum. A `full_plan` states at least 2 distinct out-of-scope items. A caller may raise the item minimum. A caller cannot lower the full-plan minimum below 2. Every other `plan_id` keeps the numbers that already apply to it.
- **BRU-032-02 (Omission is a tailoring choice):** A Communications route of `not_applicable` is allowed with the approved tailoring rationale (ADR-011). It does not raise `OMISSION_OF_BASE_PLAN`. That flag stays reserved for Scope, Schedule, and Cost. Content checks are skipped for `not_applicable`, as they are today.
- **BRU-032-03 (Matrix, recording rule, and escalation path are present):** Section 2 states the communication matrix, the decision-recording rule, and the escalation path. A `pmp_section` matrix names the audience, the cadence or trigger, and the owner. A `full_plan` matrix also names the information, the purpose, and the channel. A flow with no owner, or with no cadence or trigger, is a Tier B `MISSING_REQUIRED_SECTION` (ADR-032 Invariant 1). A `pmp_section` states the recording rule. A `full_plan` also states where the record lives. Both routes name the escalation target. A `full_plan` also states the sequence and the time limit. A missing statement is a Tier B `MISSING_REQUIRED_SECTION`. The lint reads those three statements from Section 2 only.
- **BRU-032-04 (Flags stay evidence):** Communications findings use the existing flag codes and the existing next-step table. A floor, cap, or boundary finding is Tier C and is carried to the human. A missing matrix, recording rule, or escalation path is Tier B. No Communications finding blocks `approve_plan` by itself (ADR-032 Invariant 4).
- **BRU-032-05 (One idle advisory policy):** The policy id is `advise-communications-plan-decision`. It is a low-authority softmax bandit trained later with REINFORCE on its own recommendations. It has its own task id, one logit map, equal baseline logits, and zero episodes at declaration. It never shares a task id with `approve-subsidiary-plan` or with the Scope, Schedule, Cost, Risk, Quality, Resource, or Stakeholder advisors. It never approves a plan. The deciding role is recorded with each recommendation. That role selects no second map. `approve-subsidiary-plan` stays full authority with permanent `requires_human_approval: true`. No synthetic episodes are created. No shared prior with the other plan learners is created. The ADR-024 selection episode is recorded by a human when the policy is declared; this requirement does not invent one.
- **BRU-032-06 (The recommendation is fixed before it is shown):** The chosen action, the deciding role, and a UTC timestamp are stored before a person sees them, and that record is not rewritten. Until the number of recorded decisions for this policy reaches the minimum in the policy profile, the recommendation is stored and not shown. The ADR does not set that minimum. While it is unset, nothing is shown. When a person later follows the recommendation, the reward on the recommendation is positive. When they override it, the reward is negative. The learner trains on the recommendation, not on `approve_plan`, `reject_plan`, or `request_revision_before_decision`.
- **BRU-032-07 (Communications control is a writing and review rule):** The audience list names roles and points at the Stakeholder Register. Every audience is a role in that register (ADR-032 Invariant 3). The plan traces communication needs to Charter reporting obligations and to Scope deliverables that trigger notices. A status report names progress against Schedule milestones, spend against the Cost stage, the top risks, and the decisions needed. The plan states confidentiality classes, and which external or sponsor-facing messages need approval before release and by whom. The Project Manager owns the plan. Each flow has a named owner role. Review is at each phase boundary and when the Stakeholder Register changes materially. Governance decisions are recorded in episode metadata or a version-controlled artifact. The channel message is a pointer, not the record (ADR-032 Invariant 2). This plan does not write into the Stakeholder Engagement plan or the Schedule. An update needed there is a change request to that plan's owner (ADR-032 §4.5). The lint does not check these sentences beyond the Section 2 statements in BRU-032-03. `PLAN_DAG["communications-management"]` is `("scope-management",)` and does not list `stakeholder-engagement`. No plan lists `communications-management` as an ancestor. A Scope change marks this plan `STALE_DEPENDENCY` through the existing graph. A Communications change marks no other plan stale. The Resource plan may be read and does not make this plan stale (ADR-032 §4.5).
- **BRU-032-08 (Storage boundary):** The Communications checks and the recommendation record are plain data. No new `LearningStore` record type (ADR-002). No plan text is copied into learner metadata. The content hash stays out of the plan file. This requirement does not open `Stakeholder-Register.md`, the Scope plan, or the Charter, and it does not write into another plan.

## Stakeholder Success Metrics

| Metric | Target |
|---|---|
| Baseline lengths | A Communications `pmp_section` of 149, 150, 159, 800, and 801 words, and a `full_plan` of 599, 600, 5,000, and 5,001 words, yields the ADR-012 finding and only that finding |
| No raised floor | 159 words on a Communications `pmp_section` is not below floor |
| Full-plan exclusions | One bullet raises the boundary finding; two bullets do not; a 10-token `None:` rationale satisfies the boundary |
| Section minimum | A `pmp_section` with one bullet does not raise the boundary finding |
| Omission | 0 `OMISSION_OF_BASE_PLAN` findings produced by this profile for a `not_applicable` Communications plan |
| Sections | Each missing matrix, recording rule, or escalation path produces one Tier B finding; a present statement produces none |
| Graph | The plan depends only on Scope; that dependency tuple does not contain Stakeholder Engagement; no plan lists Communications as an ancestor |
| Flag strength | 0 Communications floor, cap, or boundary findings treated as a block |
| Idle policy | The declared snapshot has task id `advise-communications-plan-decision`, low authority, one logit map, all logits 0, and 0 episodes |
| Separation | 0 recommendation episodes whose task id is a gate or another plan advisor |
| Anchoring | A stored recommendation keeps its action, deciding role, and timestamp across a second call |
| Withholding | With the minimum unset, 0 recommendations are marked shown |
| Storage | 0 new record types; 0 imports of the store from the new Communications module |

## Out of Scope

- The universal grammar, the nine-plan metadata table, and the next-step table (ADR-012, Epic 12). `owner_role` stays a non-empty string (Story 12.2).
- Raising the Communications floor above 150 or 600, or tightening the cap below 800 or 5,000.
- Tier A detection, the content hash, `approve-subsidiary-plan`, lifecycle projection, and staleness (ADR-013, Epic 13). Orchestration commands (ADR-034).
- The other plan profiles and their advisory policies. This profile does not change their findings.
- Resolving each audience to a row in the Stakeholder Register. That check stays with the human reviewer (ADR-032 Invariant 3). Opening `Stakeholder-Register.md` is out of scope.
- Generating status reports from episodes and baselines (ADR-032 §8 item 2).
- Adding a `PLAN_DAG` edge between Communications and Stakeholder Engagement. That dependency stays a later ADR-013 amendment (ADR-032 §8 item 1).
- Writing into the Stakeholder Engagement plan or the Schedule (ADR-032 §4.5).
- A second logit map, one per deciding role. The role is recorded. The logits stay one map.
- A shared prior across the nine plan learners (HYP-AL-008).
- Showing that the learner recommends well. It has no episodes.
