# BRD-025: Scope Management Plan Standard and Baseline Contract

**Source ADR:** [ADR-025](../../adr/ADR-025-scope-management-plan-standard-and-baseline-contract.md) — Accepted (2026-10-26, Menno); re-approved 2026-10-29, episode `983c2b87-8309-4414-98fe-93337989b9b5`  
**Governing Baseline:** none approved yet; cycle `CYC-001` (ADR-035, Accepted)  
**Status:** Approved (2026-10-30, Menno) — derived from Accepted ADR-025; adjudicated via `approve-brd` (robust utility 0.735, episode `78ec7505-784c-4cdc-8014-4f77771f7351`).  
**Stakeholders:** Menno (Sponsor, Project Manager, maintainer); the Product Owner named in the Stakeholder Register as deliverable-acceptance authority

## Business Need

The Scope Management Plan is the root of the planning graph. Schedule, Cost, and the other six subsidiary plans take their boundaries from it. The first baseline's Scope plan was generic stub text: no out-of-scope list, no work breakdown, and no Definition of Done. ADR-012 now checks every plan the same way. ADR-013 now binds approval to content and marks downstream plans stale. Neither applies the Scope numbers or the Scope section rules, and neither recommends a Scope decision.

A reviewer needs three things this requirement adds. A Scope plan is measured with the Scope floors, caps, and out-of-scope minimum, including the rule that a placeholder bullet is not an exclusion. Section 2 states a work-breakdown rule and a Definition of Done, or the lint says which one is missing. An advisory policy, `advise-scope-plan-decision`, can later recommend a route, a sufficiency judgment, a graduation, or a treatment of a flagged deviation, and a human still decides. The policy is declared idle: no synthetic episodes, equal baseline logits, and no recommendation shown until the maintainer sets a minimum number of recorded decisions.

## Business Rules (BRU)

- **BRU-025-01 (Scope numbers apply only to Scope):** When `plan_id` is `scope-management` and the route is `pmp_section` or `full_plan`, the measured contract is ADR-025 §4.3. A `pmp_section` is 180 to 750 words and states at least 2 distinct out-of-scope items. A `full_plan` is 700 to 4,500 words and states at least 4. Word count uses the ADR-012 tokenizer. A count equal to the floor or the cap is acceptable. Every other `plan_id` keeps the ADR-012 numbers (150/800, 600/5,000, minimum 1). A caller may raise the Scope floor or the item minimum. A caller cannot lower them and cannot relax the Scope cap.
- **BRU-025-02 (A placeholder is not an exclusion):** Under the Scope profile, a bullet whose whole text is `TBD`, `TBC`, `FIXME`, or `N/A` (optionally in brackets, any case) does not count toward the minimum. A valid `None: [rationale]` of at least 10 tokens still satisfies the boundary, as in ADR-012. Bracketed tokens such as `[TBD]` remain Tier A integrity blocks under ADR-013; this rule only changes the Scope item count.
- **BRU-025-03 (WBS and Definition of Done are present):** Under the three ADR-012 headings, Section 2 states the work-breakdown rule and a Definition of Done. A `pmp_section` states a hierarchy. A `full_plan` states the four-level hierarchy (Phase, Epic, Story, Commit or work package) and the dictionary fields acceptance criteria, owner, and parent. A missing statement is a Tier B `MISSING_REQUIRED_SECTION`. Quality of the criteria, Charter traceability, the in-scope list, and the requirements traceability matrix stay with the human reviewer (ADR-025 §4.2, §4.3 note).
- **BRU-025-04 (Flags stay evidence):** Scope findings use the existing flag codes and the existing next-step table. A floor, cap, or boundary finding is Tier C and is carried to the human. A missing WBS or Definition of Done is Tier B. No Scope finding blocks `approve_plan` by itself.
- **BRU-025-05 (One idle advisory policy):** The policy id is `advise-scope-plan-decision`. It is a low-authority softmax bandit trained later with REINFORCE on its own recommendations. It has its own task id, equal baseline logits, and zero episodes at declaration. It never shares a task id with `approve-subsidiary-plan`. It never approves a plan. `approve-subsidiary-plan` stays full authority with permanent `requires_human_approval: true`. No synthetic episodes are created. No shared prior with the other eight plan learners is created. The ADR-024 selection episode is recorded by a human when the policy is declared; this requirement does not invent one.
- **BRU-025-06 (The recommendation is fixed before it is shown):** The chosen action and a UTC timestamp are stored before a person sees them, and that record is not rewritten. Until the number of recorded decisions for this policy reaches the minimum in the policy profile, the recommendation is stored and not shown. The ADR does not set that minimum. While it is unset, nothing is shown. When a person later follows the recommendation, the reward on the recommendation is positive. When they override it, the reward is negative. The learner trains on the recommendation, not on `approve_plan`, `reject_plan`, or `request_revision_before_decision`.
- **BRU-025-07 (Scope change control is a writing and review rule):** The plan states that the Project Manager is accountable for the baseline; that a change of at most one story point, or a localized refactor that touches no public interface, approved deliverable, architectural decision, or acceptance criterion, stays at the Project Manager's discretion; and that a structural boundary change or a new feature epic goes through `approve-adaptation-plan` and the Charter. Deliverable acceptance sits with the Product Owner or Project Manager named in the Stakeholder Register. This rule has no lint flag. Downstream staleness after an approved Scope change stays the ADR-013 graph: Scope is the root, and the other eight plans are downstream.
- **BRU-025-08 (Storage boundary):** The Scope checks and the recommendation record are plain data. No new `LearningStore` record type (ADR-002). No plan text is copied into learner metadata. The content hash stays out of the plan file.

## Stakeholder Success Metrics

| Metric | Target |
|---|---|
| Scope floors and caps | A `scope-management` body of 179, 180, 750, and 751 words, and of 699, 700, 4,500, and 4,501 words, yields the ADR-025 finding and only that finding |
| Other plans unchanged | The same lengths on any other `plan_id` still follow 150/800 and 600/5,000 |
| Exclusions | Placeholder-only bullets do not meet the Scope minimum; a 10-token `None:` rationale does |
| Section 2 | Each missing WBS or Definition of Done statement produces one Tier B finding; a present statement produces none |
| Flag strength | 0 Scope floor, cap, or boundary findings treated as a block |
| Idle policy | The declared snapshot has task id `advise-scope-plan-decision`, low authority, all logits 0, and 0 episodes |
| Separation | 0 recommendation episodes whose task id is `approve-subsidiary-plan` |
| Anchoring | A stored recommendation keeps its action and timestamp across a second call |
| Withholding | With the minimum unset, 0 recommendations are marked shown |
| Storage | 0 new record types; 0 imports of the store from the new Scope module |

## Out of Scope

- The universal grammar, the nine-plan metadata table, and the next-step table (ADR-012, Epic 12).
- Tier A detection, the content hash, `approve-subsidiary-plan`, lifecycle projection, and staleness (ADR-013, Epic 13). Orchestration commands (ADR-034).
- Parsing User Story files to fill a WBS dictionary (ADR-025 §8 item 1).
- Scoring whether an acceptance criterion is testable, whether Charter mapping is adequate, or whether a traceability matrix is complete. Those stay in peer review.
- A requirements management plan (ADR-025 §4.5 leaves this open).
- Regrouping the nine learners by PMBOK 8 domain (ADR-025 §8 item 2).
- Pairwise ranking of WBS candidates (#13). That waits on paired accept and reject episodes.
- A shared prior across the nine plan learners (HYP-AL-008).
- Showing that the learner recommends well. It has no episodes.
