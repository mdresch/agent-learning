# BRD-028: Risk Management Plan Standard

**Source ADR:** [ADR-028](../../adr/ADR-028-risk-management-plan-standard.md) — Accepted (2026-10-29, Menno), episode `8bad2024-ef80-4cbf-8497-8ffb92c8b564`  
**Governing Baseline:** none approved yet; cycle `CYC-001` (ADR-035, Accepted)  
**Status:** Approved (2026-10-30, Menno) — derived from Accepted ADR-028; adjudicated via `approve-brd` (robust utility 0.735, episode `fcb319f9-e4eb-4a05-80aa-6b61723dfd07`).  
**Stakeholders:** Menno (Sponsor, Project Manager, maintainer); the Risk Lead named as plan owner

## Business Need

The Risk Management Plan is a Tier 2 governance plan. It sits downstream of Scope, Schedule, and Cost, because exposure is read from those baselines. A rating of "high" with no bands cannot be repeated by the next author, and a register with no escalation threshold never moves a decision to a person. The first baseline has no normative Risk standard. ADR-012 checks every plan with one contract. ADR-013 marks Risk stale when Scope, Schedule, or Cost changes, and no plan depends on Risk. Neither applies the Risk floors, nor checks that a Risk plan states a probability-impact scale, a register contract, and an escalation threshold.

A reviewer needs three things this requirement adds. A Risk plan is measured with the Tier 2 floors and the Tier 2 out-of-scope minimum, while the caps stay at the ADR-012 baseline. The plan states the scale, the register contract, and the escalation threshold, or the lint says which one is missing. An advisory policy, `advise-risk-plan-decision`, can later recommend a route, a sufficiency judgment, a graduation, or a treatment of a flagged deviation, and a human still decides. The policy is declared idle: no synthetic episodes, equal baseline logits, and no recommendation shown until the maintainer sets a minimum number of recorded decisions. The learner may recommend. It never accepts a risk.

## Business Rules (BRU)

- **BRU-028-01 (Risk numbers apply only to Risk):** When `plan_id` is `risk-management` and the route is `pmp_section` or `full_plan`, the measured contract is ADR-028 §4.3. A `pmp_section` is 160 to 800 words and states at least 1 out-of-scope item. A `full_plan` is 650 to 5,000 words and states at least 2 distinct out-of-scope items. The caps are the ADR-012 caps. This profile does not tighten them. Word count uses the ADR-012 tokenizer. A count equal to the floor or the cap is acceptable. Every other `plan_id` keeps the numbers that already apply to it. A caller may raise the Risk floor or the item minimum. A caller cannot lower them.
- **BRU-028-02 (Omission is a tailoring choice):** A Risk route of `not_applicable` is allowed with the approved tailoring rationale (ADR-011). It does not raise `OMISSION_OF_BASE_PLAN`. That flag stays reserved for Scope, Schedule, and Cost. Content checks are skipped for `not_applicable`, as they are today.
- **BRU-028-03 (Scale, register contract, and escalation are present):** Section 2 states a probability-impact scale and a register contract. A `pmp_section` defines the bands and states the register location and its key fields. A `full_plan` states scales per objective area with the rule that combines them, and it names the full field list: identifier, description, category, probability, impact, rating, owner, response strategy, status, and trigger. Section 3 states the escalation threshold. A `pmp_section` states the threshold. A `full_plan` states the threshold, the escalation target, and that acceptance is a recorded decision. A missing statement is a Tier B `MISSING_REQUIRED_SECTION`. Whether a rating on a particular risk can be recomputed from the scale, and whether each field is present on each register row, stay with the human reviewer.
- **BRU-028-04 (Flags stay evidence):** Risk findings use the existing flag codes and the existing next-step table. A floor, cap, or boundary finding is Tier C and is carried to the human. A missing scale, register contract, or escalation threshold is Tier B. No Risk finding blocks `approve_plan` by itself (ADR-028 Invariant 4).
- **BRU-028-05 (One idle advisory policy):** The policy id is `advise-risk-plan-decision`. It is a low-authority softmax bandit trained later with REINFORCE on its own recommendations. It has its own task id, equal baseline logits, and zero episodes at declaration. It never shares a task id with `approve-subsidiary-plan`, `advise-scope-plan-decision`, `advise-schedule-plan-decision`, or `advise-cost-plan-decision`. It never approves a plan and it never accepts a risk. A recommendation to accept a flagged plan deviation is not an acceptance of a risk at or above the escalation threshold (ADR-028 §4.4.1, Invariant 2). `approve-subsidiary-plan` stays full authority with permanent `requires_human_approval: true`. No synthetic episodes are created. No shared prior with the other plan learners is created. The ADR-024 selection episode is recorded by a human when the policy is declared; this requirement does not invent one.
- **BRU-028-06 (The recommendation is fixed before it is shown):** The chosen action and a UTC timestamp are stored before a person sees them, and that record is not rewritten. Until the number of recorded decisions for this policy reaches the minimum in the policy profile, the recommendation is stored and not shown. The ADR does not set that minimum. While it is unset, nothing is shown. When a person later follows the recommendation, the reward on the recommendation is positive. When they override it, the reward is negative. The learner trains on the recommendation, not on `approve_plan`, `reject_plan`, or `request_revision_before_decision`.
- **BRU-028-07 (Risk control is a writing and review rule):** The plan states risk appetite for scope, schedule, cost, quality, and governance integrity. It states the taxonomy, the allowed response strategies (avoid, mitigate, transfer, accept, escalate), and how rated risks become Cost contingency and Schedule buffers. The Risk Lead owns the register. Risk owners are roles from the Stakeholder Register. A risk at or above the high band, or any risk that threatens a Schedule or Cost baseline tolerance, is escalated to the Sponsor or Charter Approver, and accepting it is a recorded human decision. The review cadence is each timebox boundary and any upstream baseline change. The register is a Markdown artifact in the plan file, not a new stored entity (ADR-028 §8 item 2, ADR-002). The lint does not check these sentences and does not parse register rows. No plan in `PLAN_DAG` lists `risk-management` as an ancestor, so a Risk change marks nothing else stale. An upstream change marks Risk `STALE_DEPENDENCY` through the existing graph.
- **BRU-028-08 (Storage boundary):** The Risk checks and the recommendation record are plain data. No new `LearningStore` record type (ADR-002). No plan text is copied into learner metadata. The content hash stays out of the plan file. Approval evidence for a risk acceptance stays `Episode.metadata` written by the caller.

## Stakeholder Success Metrics

| Metric | Target |
|---|---|
| Risk floors and caps | A `risk-management` `pmp_section` of 159, 160, 800, and 801 words, and a `full_plan` of 649, 650, 5,000, and 5,001 words, yields the ADR-028 finding and only that finding |
| Caps stay universal | 751 words on a Risk `pmp_section` is not over cap |
| Other plans unchanged | The same lengths on `cost-management` are not judged by the Risk floor of 160 |
| Exclusions | A `full_plan` with one bullet raises the boundary finding; two bullets do not; a 10-token `None:` rationale satisfies the boundary |
| Omission | 0 `OMISSION_OF_BASE_PLAN` findings produced by this profile for a `not_applicable` Risk plan |
| Section checks | Each missing scale, register contract, or escalation threshold produces one Tier B finding; a present statement produces none |
| Flag strength | 0 Risk floor, cap, or boundary findings treated as a block |
| Idle policy | The declared snapshot has task id `advise-risk-plan-decision`, low authority, all logits 0, and 0 episodes |
| Separation | 0 recommendation episodes whose task id is a gate or another plan advisor, and 0 actions that accept a risk |
| Anchoring | A stored recommendation keeps its action and timestamp across a second call |
| Withholding | With the minimum unset, 0 recommendations are marked shown |
| Storage | 0 new record types; 0 imports of the store from the new Risk module |

## Out of Scope

- The universal grammar, the nine-plan metadata table, and the next-step table (ADR-012, Epic 12).
- Tier A detection, the content hash, `approve-subsidiary-plan`, lifecycle projection, and staleness (ADR-013, Epic 13). Orchestration commands (ADR-034).
- The Scope, Schedule, and Cost profiles and their advisory policies. Risk does not change their findings and does not tighten its cap through their `max_cap_words` option.
- Parsing register rows, whether the register is a Markdown table or another layout (ADR-028 §8 item 2). This requirement checks that the contract names the fields.
- Recomputing a rating from a scale, and proving that a named risk owner exists in the Stakeholder Register. The stakeholder register is not a gating input (ADR-028 §4.5).
- Monte Carlo or any quantitative model as a required method (ADR-028 §6).
- Safe bandits with action masking (#31, HYP-AL-022).
- Regrouping the nine learners by PMBOK 8 domain (ADR-028 §8 item 3).
- A shared prior across the nine plan learners (HYP-AL-008).
- Showing that the learner recommends well. It has no episodes.
