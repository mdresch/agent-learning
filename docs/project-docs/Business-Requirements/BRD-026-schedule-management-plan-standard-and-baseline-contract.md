# BRD-026: Schedule Management Plan Standard and Baseline Contract

**Source ADR:** [ADR-026](../../adr/ADR-026-schedule-management-plan-standard-and-baseline-contract.md) — Accepted (2026-10-29, Menno), episode `8be53179-eb4e-4f1c-b71d-0efa79e0876d`  
**Governing Baseline:** none approved yet; cycle `CYC-001` (ADR-035, Accepted)  
**Status:** Approved (2026-10-30, Menno) — derived from Accepted ADR-026; adjudicated via `approve-brd` (robust utility 0.718, episode `6f500ffb-054a-49f6-a3a7-323cecdc19a9`).  
**Stakeholders:** Menno (Sponsor, Project Manager, maintainer)

## Business Need

The Schedule Management Plan sits between Scope and Cost. A duration that does not name its parent epic cannot be checked again when Scope moves, and a schedule with no variance rule absorbs slippage until phase close. The first baseline has no normative Schedule standard. ADR-012 checks every plan with one contract. ADR-013 marks Cost, Resource, and Risk stale when Schedule changes, and Procurement through Cost. Neither applies the Schedule numbers, nor checks that a Schedule plan states a milestone register, a timebox model, and an estimation basis.

A reviewer needs three things this requirement adds. A Schedule plan is measured with the Schedule floors, caps, and out-of-scope minimum, and a placeholder bullet does not count as an exclusion. Section 2 states the milestone register, the timebox and sequencing model, and the estimation basis, or the lint says which one is missing. An advisory policy, `advise-schedule-plan-decision`, can later recommend a route, a sufficiency judgment, a graduation, or a treatment of a flagged deviation, and a human still decides. The policy is declared idle: no synthetic episodes, equal baseline logits, and no recommendation shown until the maintainer sets a minimum number of recorded decisions.

## Business Rules (BRU)

- **BRU-026-01 (Schedule numbers apply only to Schedule):** When `plan_id` is `schedule-management` and the route is `pmp_section` or `full_plan`, the measured contract is ADR-026 §4.3. A `pmp_section` is 180 to 750 words and states at least 2 distinct out-of-scope items. A `full_plan` is 700 to 4,500 words and states at least 4. Word count uses the ADR-012 tokenizer. A count equal to the floor or the cap is acceptable. Every other `plan_id` keeps the numbers that already apply to it. A caller may raise the Schedule floor or the item minimum. A caller cannot lower them and cannot relax the Schedule cap.
- **BRU-026-02 (A placeholder is not an exclusion):** Under the Schedule profile, a bullet whose whole text is `TBD`, `TBC`, `FIXME`, or `N/A` (optionally in brackets, any case) does not count toward the minimum, the same rule ADR-026 §4.3 takes from ADR-025 §4.3. A valid `None: [rationale]` of at least 10 tokens still satisfies the boundary, as in ADR-012. An unbracketed `TBD` date stays the existing provisional-token flag carried to the decision frame (ADR-013 §4.2). A bracketed token such as `[TBD]` stays a Tier A integrity block. This rule only changes the Schedule item count.
- **BRU-026-03 (Milestone register, timebox, and estimation basis are present):** Under the three ADR-012 headings, Section 2 states a milestone register that names a parent epic, a timebox and sequencing model, and an estimation basis. A `pmp_section` states the milestone list with its parent epic, a one-line timebox model, and the estimation method. A `full_plan` states exit conditions and target windows, predecessors (or a critical path, or an equivalent sequence), and the estimation method, unit, and confidence rule. A missing statement is a Tier B `MISSING_REQUIRED_SECTION`. Whether each milestone's exit condition is objectively verifiable, whether each parent epic exists in the Scope baseline, and whether a far-horizon estimate is a range, stay with the human reviewer.
- **BRU-026-04 (Flags stay evidence):** Schedule findings use the existing flag codes and the existing next-step table. A floor, cap, or boundary finding is Tier C and is carried to the human. A missing register, model, or estimation basis is Tier B. No Schedule finding blocks `approve_plan` by itself (ADR-026 Invariant 4).
- **BRU-026-05 (One idle advisory policy):** The policy id is `advise-schedule-plan-decision`. It is a low-authority softmax bandit trained later with REINFORCE on its own recommendations. It has its own task id, equal baseline logits, and zero episodes at declaration. It never shares a task id with `approve-subsidiary-plan` or with `advise-scope-plan-decision`. It never approves a plan. `approve-subsidiary-plan` stays full authority with permanent `requires_human_approval: true`. No synthetic episodes are created. No shared prior with the other plan learners is created. The ADR-024 selection episode is recorded by a human when the policy is declared; this requirement does not invent one.
- **BRU-026-06 (The recommendation is fixed before it is shown):** The chosen action and a UTC timestamp are stored before a person sees them, and that record is not rewritten. Until the number of recorded decisions for this policy reaches the minimum in the policy profile, the recommendation is stored and not shown. The ADR does not set that minimum. While it is unset, nothing is shown. When a person later follows the recommendation, the reward on the recommendation is positive. When they override it, the reward is negative. The learner trains on the recommendation, not on `approve_plan`, `reject_plan`, or `request_revision_before_decision`.
- **BRU-026-07 (Schedule change control is a writing and review rule):** The plan states that the Project Manager is accountable for the schedule baseline, and that milestone acceptance follows the Scope Definition of Done. A milestone slip of at most 2 working days that is not on the critical path stays at the Project Manager's discretion and is logged. A slip of more than 2 working days, any slip of a critical-path milestone, or a changed milestone exit condition goes through `approve-adaptation-plan` or a design-time baseline revision (`BFI-NNN`, ADR-037). A stricter tolerance written in the Charter takes precedence over these defaults (ADR-026 §8 item 1). The plan states the planning horizon, the schedule baseline, where contingency is held, who may consume it, and a review at each timebox boundary and at phase close. Section 1 states the development approach when the Charter does not (ADR-026 §4.5, still marked for maintainer confirmation). This rule has no lint flag. Downstream staleness stays the ADR-013 graph: an approved Schedule change marks Cost, Resource, and Risk stale, and Procurement through Cost.
- **BRU-026-08 (Storage boundary):** The Schedule checks and the recommendation record are plain data. No new `LearningStore` record type (ADR-002). No plan text is copied into learner metadata. The content hash stays out of the plan file. Estimation does not read velocity from the store (ADR-026 §8 item 2).

## Stakeholder Success Metrics

| Metric | Target |
|---|---|
| Schedule floors and caps | A `schedule-management` body of 179, 180, 750, and 751 words, and of 699, 700, 4,500, and 4,501 words, yields the ADR-026 finding and only that finding |
| Other plans unchanged | The same lengths on `cost-management` still follow 150/800 and 600/5,000 |
| Exclusions | Placeholder-only bullets do not meet the Schedule minimum; a 10-token `None:` rationale does |
| Section 2 | Each missing milestone register, parent epic, timebox model, or estimation basis produces one Tier B finding; a present statement produces none |
| Flag strength | 0 Schedule floor, cap, or boundary findings treated as a block |
| Idle policy | The declared snapshot has task id `advise-schedule-plan-decision`, low authority, all logits 0, and 0 episodes |
| Separation | 0 recommendation episodes whose task id is `approve-subsidiary-plan` or `advise-scope-plan-decision` |
| Anchoring | A stored recommendation keeps its action and timestamp across a second call |
| Withholding | With the minimum unset, 0 recommendations are marked shown |
| Storage | 0 new record types; 0 imports of the store from the new Schedule module |

## Out of Scope

- The universal grammar, the nine-plan metadata table, and the next-step table (ADR-012, Epic 12).
- Tier A detection, provisional-token handling, the content hash, `approve-subsidiary-plan`, lifecycle projection, and staleness (ADR-013, Epic 13). Orchestration commands (ADR-034).
- The Scope profile and `advise-scope-plan-decision` (ADR-025). Schedule uses the same lint options for a tighter cap and placeholder exclusion, and does not change Scope findings.
- Joining each milestone to a named epic in the Scope plan file, and judging whether an exit condition is objectively verifiable.
- Reading velocity or any other evidence from `LearningStore` (ADR-026 §8 item 2).
- Multi-stage credit assignment (#25). It waits on `PlanApprovalRecord.parent_hashes` (Epic 13).
- Contextual softmax (#4, HYP-AL-004). ADR-026 records it as unevidenced.
- Regrouping the nine learners by PMBOK 8 domain (ADR-026 §8 item 3).
- A shared prior across the nine plan learners (HYP-AL-008).
- Showing that the learner recommends well. It has no episodes.
