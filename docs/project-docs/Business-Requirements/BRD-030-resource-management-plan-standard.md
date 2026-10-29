# BRD-030: Resource Management Plan Standard

**Source ADR:** [ADR-030](../../adr/ADR-030-resource-management-plan-standard.md) — Proposed (2026-10-26); ready for `approve-adr`  
**Governing Baseline:** none approved yet; cycle `CYC-001` (ADR-035, Proposed)  
**Status:** Draft (2026-10-29) — derived from Proposed ADR-030; not yet adjudicated via `approve-brd`. Adjudication waits until ADR-030 is accepted.  
**Stakeholders:** Menno (Sponsor, Project Manager, maintainer)

## Business Need

The Resource Management Plan is a Tier 3 execution-support plan. Resource needs come from the Scope work and the Schedule timeboxes. A role with no accountable human hides who answers for agent work, an allocation that is not stated cannot be compared with the schedule, and an unlisted environment or licence shows up as a late blocker. The first baseline has no normative Resource standard. ADR-012 already measures every plan at 150 and 600 words, with caps of 800 and 5,000. ADR-013 marks Resource stale when Scope or Schedule changes, and no plan depends on Resource. Neither checks that a Resource plan states a role catalogue, an allocation, and the tooling it needs.

A reviewer needs three things this requirement adds. A full Resource plan states at least two out-of-scope items. The floors and caps stay at the ADR-012 baseline. The plan states the role catalogue, the allocation and capacity, and the tooling assets, or the lint says which one is missing. An advisory policy, `advise-resource-plan-decision`, can later recommend a route, a sufficiency judgment, a graduation, or a treatment of a flagged deviation, and a human still decides. The policy is declared idle. Procurement decisions and HR decisions are recorded separately so the two departments are not blended.

## Business Rules (BRU)

- **BRU-030-01 (Resource keeps the baseline lengths):** When `plan_id` is `resource-management` and the route is `pmp_section` or `full_plan`, length uses the ADR-012 baseline. A `pmp_section` is 150 to 800 words. A `full_plan` is 600 to 5,000 words. This standard does not raise those floors and does not tighten those caps. A count equal to the floor or the cap is acceptable. A `pmp_section` states at least 1 out-of-scope item, the baseline minimum. A `full_plan` states at least 2 distinct out-of-scope items. A caller may raise the item minimum. A caller cannot lower the full-plan minimum below 2. Every other `plan_id` keeps the numbers that already apply to it.
- **BRU-030-02 (Omission is a tailoring choice):** A Resource route of `not_applicable` is allowed with the approved tailoring rationale (ADR-011). It does not raise `OMISSION_OF_BASE_PLAN`. That flag stays reserved for Scope, Schedule, and Cost. Content checks are skipped for `not_applicable`, as they are today.
- **BRU-030-03 (Catalogue, allocation, and tooling are present):** Section 2 states a role catalogue, an allocation and capacity statement, and the tooling assets. A `pmp_section` names roles with an accountable owner, states capacity, and lists the assets. A `full_plan` states responsibilities and decision rights, a per-role per-timebox allocation with its basis, and asset owners and lead times. A missing statement is a Tier B `MISSING_REQUIRED_SECTION`. Where the plan gives work to an autonomous agent, it also names the accountable human (ADR-030 Invariant 1). Whether each named person exists in the Stakeholder Register, and whether the capacity unit matches the Schedule file, stay with the human reviewer.
- **BRU-030-04 (Flags stay evidence):** Resource findings use the existing flag codes and the existing next-step table. A floor, cap, or boundary finding is Tier C and is carried to the human. A missing catalogue, allocation, tooling list, or accountable human for agent work is Tier B. No Resource finding blocks `approve_plan` by itself (ADR-030 Invariant 4).
- **BRU-030-05 (One idle advisory policy, two departments):** The policy id is `advise-resource-plan-decision`. It is a low-authority softmax bandit trained later with REINFORCE on its own recommendations. It has one task id, equal baseline logits, and zero episodes at declaration. Each recommendation records the deciding department, `procurement` for materials or `hr` for human resources, and the logits for those departments are stored apart so an outcome in one does not move the other (ADR-030 §4.4.1). The policy never shares a task id with `approve-subsidiary-plan` or with the Scope, Schedule, Cost, Risk, or Quality advisors. It never approves a plan. `approve-subsidiary-plan` stays full authority with permanent `requires_human_approval: true`. No synthetic episodes are created. No shared prior with the other plan learners is created. The ADR-024 selection episode is recorded by a human when the policy is declared; this requirement does not invent one.
- **BRU-030-06 (The recommendation is fixed before it is shown):** The chosen action, the department, and a UTC timestamp are stored before a person sees them, and that record is not rewritten. Until the number of recorded decisions for this policy reaches the minimum in the policy profile, the recommendation is stored and not shown. The ADR does not set that minimum. While it is unset, nothing is shown. When a person later follows the recommendation, the reward on that department's recommendation is positive. When they override it, the reward is negative. The learner trains on the recommendation, not on `approve_plan`, `reject_plan`, or `request_revision_before_decision`.
- **BRU-030-07 (Resource control is a writing and review rule):** The plan maps resource needs to Scope epics and Schedule timeboxes. It declares human roles, autonomous agents, and tooling as in or out of the plan. For agents, it states the work classes they may perform. An agent does not receive a decision that ADR-001 or ADR-008 reserves for a human (ADR-030 Invariant 3). Allocation uses the Schedule timebox unit (ADR-030 Invariant 2). Agent capacity, when stated, may be an API token limit, a model context quota, or concurrent runner slots per timebox (ADR-030 §8 item 1). The plan states how a resource is acquired and released and who approves it. The Project Manager owns the plan. When demand exceeds capacity, the plan names who chooses between a Scope change and a Schedule change, and both go through `approve-adaptation-plan`. Review is at each timebox boundary. The lint does not check these sentences beyond the Section 2 presence rules. No plan in `PLAN_DAG` lists `resource-management` as an ancestor. Cost does not depend on Resource. A Scope or Schedule change marks Resource `STALE_DEPENDENCY` through the existing graph. Resource may read the Quality plan and does not go stale when Quality changes.
- **BRU-030-08 (Storage boundary):** The Resource checks and the recommendation record are plain data. No new `LearningStore` record type (ADR-002). No plan text is copied into learner metadata. The content hash stays out of the plan file. The two department logit maps live in the policy snapshot's metadata.

## Stakeholder Success Metrics

| Metric | Target |
|---|---|
| Baseline lengths | A Resource `pmp_section` of 149, 150, 159, 800, and 801 words, and a `full_plan` of 599, 600, 5,000, and 5,001 words, yields the ADR-012 finding and only that finding |
| No Tier 2 floor | 159 words on a Resource `pmp_section` is not below floor |
| Full-plan exclusions | One bullet raises the boundary finding; two bullets do not; a 10-token `None:` rationale satisfies the boundary |
| Section minimum | A `pmp_section` with one bullet does not raise the boundary finding |
| Omission | 0 `OMISSION_OF_BASE_PLAN` findings produced by this profile for a `not_applicable` Resource plan |
| Section 2 | Each missing catalogue, accountable owner, allocation, tooling list, or agent accountability produces one Tier B finding; a present statement produces none |
| Graph | Cost does not depend on Resource; no plan lists Resource as an ancestor |
| Flag strength | 0 Resource floor, cap, or boundary findings treated as a block |
| Idle policy | The declared snapshot has task id `advise-resource-plan-decision`, low authority, both departments at logit 0, and 0 episodes |
| Separation | An outcome recorded for one department leaves the other department's logits unchanged |
| Anchoring | A stored recommendation keeps its action, department, and timestamp across a second call |
| Withholding | With the minimum unset, 0 recommendations are marked shown |
| Storage | 0 new record types; 0 imports of the store from the new Resource module |

## Out of Scope

- The universal grammar, the nine-plan metadata table, and the next-step table (ADR-012, Epic 12).
- Raising the Resource floor above 150 or 600, or tightening the cap below 800 or 5,000.
- Tier A detection, the content hash, `approve-subsidiary-plan`, lifecycle projection, and staleness (ADR-013, Epic 13). Orchestration commands (ADR-034).
- The other plan profiles and their advisory policies. Resource does not change their findings.
- Adding a `PLAN_DAG` edge from Cost to Resource, or from Resource to any other plan (ADR-030 §8 item 2).
- A team charter, and a required RACI chart (ADR-030 §4.5). The catalogue does not have to use a matrix format.
- Checking the Stakeholder Register, opening the Schedule file to compare units, or listing the decisions ADR-001 and ADR-008 reserve for a human.
- A shared prior across the nine plan learners (HYP-AL-008).
- Showing that the learner recommends well. It has no episodes.
