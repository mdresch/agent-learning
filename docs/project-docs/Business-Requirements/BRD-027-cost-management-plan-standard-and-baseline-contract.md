# BRD-027: Cost Management Plan Standard and Baseline Contract

**Source ADR:** [ADR-027](../../adr/ADR-027-cost-management-plan-standard-and-baseline-contract.md) — Accepted (2026-10-29, Menno), episode `0ae724ad-5309-4eb2-a333-749cde39c0c0`  
**Governing Baseline:** none approved yet; cycle `CYC-001` (ADR-035, Accepted)  
**Status:** Approved (2026-10-30, Menno) — derived from Accepted ADR-027; adjudicated via `approve-brd` (robust utility 0.722, episode `e870c2c1-a214-4d9f-9c88-b33b637c1cf3`).  
**Stakeholders:** Menno (Sponsor, Project Manager, maintainer)

## Business Need

The Cost Management Plan is the third baseline plan. It takes its envelope from the Charter and its stages from Scope and Schedule. A budget that does not name its categories can hide compute, model, and licence spend inside a staff-time figure, and a budget with no contingency rule discovers an overrun after the money is gone. The first baseline has no normative Cost standard. ADR-012 checks every plan with one contract. ADR-013 marks Risk and Procurement stale when Cost changes. Neither applies the Cost numbers, nor checks that a Cost plan states a management envelope, cost categories with an estimating basis, and a contingency and reserve rule.

A reviewer needs three things this requirement adds. A Cost plan is measured with the Cost floors, caps, and out-of-scope minimum, and a placeholder bullet does not count as an exclusion. The plan states the envelope, the categories and estimating basis, and the contingency rule, or the lint says which one is missing. An advisory policy, `advise-cost-plan-decision`, can later recommend a route, a sufficiency judgment, a graduation, or a treatment of a flagged deviation, and a human still decides. The policy is declared idle: no synthetic episodes, equal baseline logits, and no recommendation shown until the maintainer sets a minimum number of recorded decisions.

## Business Rules (BRU)

- **BRU-027-01 (Cost numbers apply only to Cost):** When `plan_id` is `cost-management` and the route is `pmp_section` or `full_plan`, the measured contract is ADR-027 §4.3. A `pmp_section` is 180 to 750 words and states at least 2 distinct out-of-scope items. A `full_plan` is 700 to 4,500 words and states at least 4. Word count uses the ADR-012 tokenizer. A count equal to the floor or the cap is acceptable. Every other `plan_id` keeps the numbers that already apply to it. A caller may raise the Cost floor or the item minimum. A caller cannot lower them and cannot relax the Cost cap.
- **BRU-027-02 (A placeholder is not an exclusion):** Under the Cost profile, a bullet whose whole text is `TBD`, `TBC`, `FIXME`, or `N/A` (optionally in brackets, any case) does not count toward the minimum. ADR-027 uses the same distinct-item minimum as the other Tier 1 plans, and this requirement uses the distinct-item rule those plans take from ADR-025 §4.3. A valid `None: [rationale]` of at least 10 tokens still satisfies the boundary, as in ADR-012. A bracketed token such as `[TBD]` stays a Tier A integrity block under ADR-013. This rule only changes the Cost item count.
- **BRU-027-03 (Envelope, categories, and contingency are present):** Section 1 states the management envelope. A `pmp_section` states the ceiling. A `full_plan` states the ceiling, the unit, and the approving authority. Section 2 states the cost categories and the contingency rule. A `pmp_section` names the categories and states the contingency rule in one line. A `full_plan` states categories with owners, measurement sources, and accuracy ranges, and it states contingency and management reserve separately, with who may release each. A missing statement is a Tier B `MISSING_REQUIRED_SECTION`. Whether each funded stage names a real Schedule milestone or Scope epic, whether each category's range is a true accuracy band, and whether each contingency amount names a risk, stay with the human reviewer.
- **BRU-027-04 (Flags stay evidence):** Cost findings use the existing flag codes and the existing next-step table. A floor, cap, or boundary finding is Tier C and is carried to the human. A missing envelope, category statement, or contingency rule is Tier B. No Cost finding blocks `approve_plan` by itself (ADR-027 Invariant 5).
- **BRU-027-05 (One idle advisory policy):** The policy id is `advise-cost-plan-decision`. It is a low-authority softmax bandit trained later with REINFORCE on its own recommendations. It has its own task id, equal baseline logits, and zero episodes at declaration. It never shares a task id with `approve-subsidiary-plan`, `advise-scope-plan-decision`, or `advise-schedule-plan-decision`. It never approves a plan. `approve-subsidiary-plan` stays full authority with permanent `requires_human_approval: true`. No synthetic episodes are created. No shared prior with the other plan learners is created. The ADR-024 selection episode is recorded by a human when the policy is declared; this requirement does not invent one.
- **BRU-027-06 (The recommendation is fixed before it is shown):** The chosen action and a UTC timestamp are stored before a person sees them, and that record is not rewritten. Until the number of recorded decisions for this policy reaches the minimum in the policy profile, the recommendation is stored and not shown. The ADR does not set that minimum. While it is unset, nothing is shown. When a person later follows the recommendation, the reward on the recommendation is positive. When they override it, the reward is negative. The learner trains on the recommendation, not on `approve_plan`, `reject_plan`, or `request_revision_before_decision`.
- **BRU-027-07 (Cost change control is a writing and review rule):** The plan states that the Project Manager is accountable for the cost baseline, and that an envelope increase requires the Sponsor or Charter Approver. A stage variance within ±10% of that stage's budget, and inside that stage's contingency, stays at the Project Manager's discretion and is logged. A variance beyond ±10%, any envelope change, or any management-reserve release goes through `approve-adaptation-plan` or a design-time baseline revision (`BFI-NNN`, ADR-037). A stricter tolerance written in the Charter takes precedence. The plan states the staged funding model, including that funding beyond the current stage is indicative, the cost baseline as the approved staged budget excluding management reserve, the burn-rate comparison and its reporting interval, and a review at each stage boundary and at phase close. Each funded stage names the Schedule milestone or Scope epic it funds (ADR-027 Invariant 2). Contingency references identified risks or states why none are identified (ADR-027 Invariant 3). The lint does not check these sentences. Downstream staleness stays the ADR-013 graph: an approved Cost change marks Risk and Procurement stale.
- **BRU-027-08 (Storage boundary):** The Cost checks and the recommendation record are plain data. No new `LearningStore` record type (ADR-002). No plan text is copied into learner metadata. The content hash stays out of the plan file. Compute and API spend are not read from `tests/test_cost_model.py` or from any store (ADR-027 §8 item 1).

## Stakeholder Success Metrics

| Metric | Target |
|---|---|
| Cost floors and caps | A `cost-management` body of 179, 180, 750, and 751 words, and of 699, 700, 4,500, and 4,501 words, yields the ADR-027 finding and only that finding |
| Other plans unchanged | The same lengths on `schedule-management` still follow that plan's own profile, or the universal 150/800 when no Schedule profile is applied |
| Exclusions | Placeholder-only bullets do not meet the Cost minimum; a 10-token `None:` rationale does |
| Envelope and Section 2 | Each missing envelope, category statement, or contingency rule produces one Tier B finding; a present statement produces none |
| Flag strength | 0 Cost floor, cap, or boundary findings treated as a block |
| Idle policy | The declared snapshot has task id `advise-cost-plan-decision`, low authority, all logits 0, and 0 episodes |
| Separation | 0 recommendation episodes whose task id is `approve-subsidiary-plan`, `advise-scope-plan-decision`, or `advise-schedule-plan-decision` |
| Anchoring | A stored recommendation keeps its action and timestamp across a second call |
| Withholding | With the minimum unset, 0 recommendations are marked shown |
| Storage | 0 new record types; 0 imports of the store from the new Cost module |

## Out of Scope

- The universal grammar, the nine-plan metadata table, and the next-step table (ADR-012, Epic 12).
- Tier A detection, the content hash, `approve-subsidiary-plan`, lifecycle projection, and staleness (ADR-013, Epic 13). Orchestration commands (ADR-034).
- The Scope and Schedule profiles and their advisory policies. Cost uses the same lint options for a tighter cap and placeholder exclusion, and it does not change their findings.
- Revenue planning. The plan id stays `cost-management` (ADR-027 §4.5).
- Joining a funded stage to a named milestone or epic in another plan file, and joining a contingency amount to a named risk. Reconciliation of contingency when the Risk plan is later approved, including whether that needs a fresh Cost approval, stays the open question in ADR-027 §4.5.
- Reading compute or API spend from `tests/test_cost_model.py` or from `LearningStore` (ADR-027 §8 item 1).
- Multi-stage credit assignment (#25). It waits on `PlanApprovalRecord.parent_hashes` (Epic 13).
- Regrouping the nine learners by PMBOK 8 domain (ADR-027 §8 item 3).
- A shared prior across the nine plan learners (HYP-AL-008).
- Showing that the learner recommends well. It has no episodes.
