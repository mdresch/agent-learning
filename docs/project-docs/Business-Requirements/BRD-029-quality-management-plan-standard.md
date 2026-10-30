# BRD-029: Quality Management Plan Standard

**Source ADR:** [ADR-029](../../adr/ADR-029-quality-management-plan-standard.md) — Accepted (2026-10-29, Menno), episode `736036f7-40a1-441f-afc0-062501c46d57`  
**Governing Baseline:** none approved yet; cycle `CYC-001` (ADR-035, Accepted)  
**Status:** Approved (2026-10-30, Menno) — derived from Accepted ADR-029; adjudicated via `approve-brd` (robust utility 0.735, episode `009851b2-d860-4f06-b553-460e9f42fae8`).  
**Stakeholders:** Menno (Sponsor, Project Manager, maintainer); the Quality Assurance Lead named as plan owner

## Business Need

The Quality Management Plan is a Tier 2 governance plan. Scope holds the Definition of Done and the acceptance criteria. Quality says how conformance to them is verified. A gate that names no pass criterion cannot be audited, and a coverage number that does not say what it measures can be gamed. The first baseline's Quality plan has formatting errors and no normative standard. ADR-012 checks every plan with one contract. ADR-013 marks Quality stale when Scope changes, and no plan depends on Quality. Neither applies the Quality floors, nor checks that a Quality plan states gates, verification and coverage, and nonconformance handling.

A reviewer needs three things this requirement adds. A Quality plan is measured with the Tier 2 floors and the Tier 2 out-of-scope minimum, while the caps stay at the ADR-012 baseline. The plan states the gates, the verification criteria, and the nonconformance process, or the lint says which one is missing. An advisory policy, `advise-quality-plan-decision`, can later recommend a route, a sufficiency judgment, a graduation, or a treatment of a flagged deviation, and a human still decides. The policy is declared idle: no synthetic episodes, equal baseline logits, and no recommendation shown until the maintainer sets a minimum number of recorded decisions. The learner never waives a gate.

## Business Rules (BRU)

- **BRU-029-01 (Quality numbers apply only to Quality):** When `plan_id` is `quality-management` and the route is `pmp_section` or `full_plan`, the measured contract is ADR-029 §4.3. A `pmp_section` is 160 to 800 words and states at least 1 out-of-scope item. A `full_plan` is 650 to 5,000 words and states at least 2 distinct out-of-scope items. The caps are the ADR-012 caps. This profile does not tighten them. Word count uses the ADR-012 tokenizer. A count equal to the floor or the cap is acceptable. Every other `plan_id` keeps the numbers that already apply to it. A caller may raise the Quality floor or the item minimum. A caller cannot lower them.
- **BRU-029-02 (Omission is a tailoring choice):** A Quality route of `not_applicable` is allowed with the approved tailoring rationale (ADR-011). It does not raise `OMISSION_OF_BASE_PLAN`. That flag stays reserved for Scope, Schedule, and Cost. Content checks are skipped for `not_applicable`, as they are today.
- **BRU-029-03 (Gates, verification, and nonconformance are present):** Section 2 states the quality gates, the verification criteria, and the nonconformance process. A `pmp_section` lists gates with pass criteria, names the verification types and the minimum, and states the nonconformance process in one line. A `full_plan` states each gate's pass criteria, the evidence required, and the gate owner; it states the verification types, what a coverage figure measures, and the minimum; and it states triage, waiver, and rework. A missing statement is a Tier B `MISSING_REQUIRED_SECTION`. A gate with no pass criterion is that same flag (ADR-029 Invariant 2). Whether the criteria contradict the Scope Definition of Done, and whether a coverage figure is the right measure, stay with the human reviewer.
- **BRU-029-04 (Flags stay evidence):** Quality findings use the existing flag codes and the existing next-step table. A floor, cap, or boundary finding is Tier C and is carried to the human. A missing gate, verification statement, or nonconformance process is Tier B. No Quality finding blocks `approve_plan` by itself (ADR-029 Invariant 4).
- **BRU-029-05 (One idle advisory policy):** The policy id is `advise-quality-plan-decision`. It is a low-authority softmax bandit trained later with REINFORCE on its own recommendations. It has its own task id, equal baseline logits, and zero episodes at declaration. It never shares a task id with `approve-subsidiary-plan` or with `advise-scope-plan-decision`, `advise-schedule-plan-decision`, `advise-cost-plan-decision`, or `advise-risk-plan-decision`. It never approves a plan and it never waives a gate. `approve-subsidiary-plan` stays full authority with permanent `requires_human_approval: true`. No synthetic episodes are created. No shared prior with the other plan learners is created. The ADR-024 selection episode is recorded by a human when the policy is declared; this requirement does not invent one.
- **BRU-029-06 (The recommendation is fixed before it is shown):** The chosen action and a UTC timestamp are stored before a person sees them, and that record is not rewritten. Until the number of recorded decisions for this policy reaches the minimum in the policy profile, the recommendation is stored and not shown. The ADR does not set that minimum. While it is unset, nothing is shown. When a person later follows the recommendation, the reward on the recommendation is positive. When they override it, the reward is negative. The learner trains on the recommendation, not on `approve_plan`, `reject_plan`, or `request_revision_before_decision`.
- **BRU-029-07 (Quality control is a writing and review rule):** The plan maps quality objectives to Charter objectives and to the Scope acceptance criteria and Definition of Done. It references those criteria and does not replace them (ADR-029 Invariant 1). It states the quality metrics, their collection source, and the threshold that triggers action. It states where recurring defects are recorded for lessons learned (ADR-010). The Quality Assurance Lead owns the plan and the gate definitions. Deliverable acceptance stays with the authority named in the Scope standard. A waiver of a gate criterion requires a recorded rationale and the waiver authority named in the Charter, the Project Manager or the Sponsor (ADR-029 §8 item 2, Invariant 3). A waiver is never silent. Review is at each gate and at phase close. The lint does not check these sentences. No plan in `PLAN_DAG` lists `quality-management` as an ancestor, so a Quality change marks nothing else stale. A Scope change marks Quality `STALE_DEPENDENCY` through the existing graph. Resource, Cost, and Procurement may read the Quality plan and do not go stale when it changes (ADR-029 §4.5).
- **BRU-029-08 (Storage boundary):** The Quality checks and the recommendation record are plain data. No new `LearningStore` record type (ADR-002). No plan text is copied into learner metadata. The content hash stays out of the plan file. Gate results that Epic 13 already stores on `Episode.metadata` stay there. This requirement does not add a second store for them.

## Stakeholder Success Metrics

| Metric | Target |
|---|---|
| Quality floors and caps | A `quality-management` `pmp_section` of 159, 160, 800, and 801 words, and a `full_plan` of 649, 650, 5,000, and 5,001 words, yields the ADR-029 finding and only that finding |
| Caps stay universal | 751 words on a Quality `pmp_section` is not over cap |
| Other plans unchanged | The same lengths on `risk-management` are not judged by the Quality floor of 160 |
| Exclusions | A `full_plan` with one bullet raises the boundary finding; two bullets do not; a 10-token `None:` rationale satisfies the boundary |
| Omission | 0 `OMISSION_OF_BASE_PLAN` findings produced by this profile for a `not_applicable` Quality plan |
| Section 2 | Each missing gate, pass criterion, verification statement, or nonconformance process produces one Tier B finding; a present statement produces none |
| Flag strength | 0 Quality floor, cap, or boundary findings treated as a block |
| Idle policy | The declared snapshot has task id `advise-quality-plan-decision`, low authority, all logits 0, and 0 episodes |
| Separation | 0 recommendation episodes whose task id is a gate or another plan advisor, and 0 actions that waive a gate |
| Anchoring | A stored recommendation keeps its action and timestamp across a second call |
| Withholding | With the minimum unset, 0 recommendations are marked shown |
| Storage | 0 new record types; 0 imports of the store from the new Quality module |

## Out of Scope

- The universal grammar, the nine-plan metadata table, and the next-step table (ADR-012, Epic 12).
- Tier A detection, the content hash, `approve-subsidiary-plan`, lifecycle projection, and staleness (ADR-013, Epic 13). Orchestration commands (ADR-034).
- The Scope, Schedule, Cost, and Risk profiles and their advisory policies. Quality does not change their findings and does not tighten its cap.
- Restating or editing the Scope Definition of Done. Quality references it.
- Parsing test suites, coverage reports, or gate-result files. Registering gate results as episodes stays the Epic 13 record (ADR-029 §8 item 1).
- The later nonconformance-triage policy (rework or escalate). ADR-029 §4.4.1 keeps it separate from `advise-quality-plan-decision` and waits on two real cases. Waivers stay a human decision.
- A required external audit (ADR-029 §6).
- Regrouping the nine learners by PMBOK 8 domain (ADR-029 §8 item 3).
- A shared prior across the nine plan learners (HYP-AL-008).
- Showing that the learner recommends well. It has no episodes.
