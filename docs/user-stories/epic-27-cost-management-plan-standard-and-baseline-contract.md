# Epic 27: Cost Management Plan Standard and Baseline Contract

**Source ADR:** [ADR-027](../adr/ADR-027-cost-management-plan-standard-and-baseline-contract.md) — Proposed (2026-10-26)  
**Source BRD/FDD:** [BRD-027](../project-docs/Business-Requirements/BRD-027-cost-management-plan-standard-and-baseline-contract.md) / [FDD-027](../project-docs/Functional-Design/FDD-027-cost-management-plan-standard-and-baseline-contract.md)  
**Status:** Draft (2026-10-29) — derived from Proposed ADR-027, BRD-027 and FDD-027; not yet adjudicated via `approve-user-stories`. Implementation waits until ADR-027 is accepted.

Four stories. Each rule sits in one story (LL-012). Contract tests: `tests/test_cost_measure.py` (27.1), `tests/test_cost_sections.py` (27.2), `tests/test_cost_advice_policy.py` (27.3), `tests/test_cost_advice_reward.py` (27.4). Story 27.1 waits on the shared lint arguments in FDD-027 §3.2. Stories 27.3 and 27.4 wait until FDD-027 §5 item 1 is confirmed. BRU-027-07 has no story: it is the text the plan author writes and the approver reads.

---

## Story 27.1 — Cost floors, caps, and exclusions

**Status:** Draft — blocked on the `max_cap_words` and `exclude_placeholders` arguments of FDD-027 §3.2, and on acceptance of ADR-027  
**As** a governance reviewer,  
**I want** a Cost plan measured with the Cost floors, caps, and out-of-scope minimum,  
**so that** a plan that would pass the universal lint still shows a Cost gap, and every other plan keeps its own numbers.

### Acceptance Criteria

- **$AC_0$ (Profile):** `cost_measure("cost-management", "pmp_section")` is floor 180, cap 750, minimum 2 items. `full_plan` is 700, 4,500, and 4. `not_applicable`, `schedule-management`, and `scope-management` return `None`.
- **$AC_1$ (Boundaries):** For a Cost `pmp_section`, word counts 179, 180, 750, and 751 produce below-floor, no length finding, no length finding, and `EXCEEDS_SECTION_CAP`. For a Cost `full_plan`, 699, 700, 4,500, and 4,501 produce below-floor, none, none, and `EXCEEDS_PLAN_CAP`. All four length findings are Tier C.
- **$AC_2$ (Other plans):** The same four `pmp_section` lengths on `schedule-management` are not judged by the Cost cap of 750. 751 words on `schedule-management` is not a Cost finding. A `scope-management` body receives no Cost finding from this profile.
- **$AC_3$ (Items):** A Cost section with one real bullet and one `TBD` bullet raises `MISSING_BOUNDARY_DEF`. Two real bullets do not. A bullet `N/A for post-handover operating cost` counts as real. A `None:` line of at least 10 tokens satisfies the boundary with zero bullets. The same one-bullet body on `schedule-management` does not raise the boundary finding from this profile.
- **$AC_4$ (Cannot relax):** A caller `min_floor_words` below 180 leaves 180 in force. A caller `min_out_of_scope_items` below 2 leaves 2 in force. A caller value above the profile raises the bar. `max_cap_words` above 800 leaves the universal cap in force for a non-Cost plan.
- **$AC_5$ (Purity):** `cost.py` imports no storage module, does not import `tests/test_cost_model.py`, and adds no package to `pyproject.toml`.

---

## Story 27.2 — Envelope, categories, and contingency

**Status:** Draft — blocked on acceptance of ADR-027  
**As** a governance reviewer,  
**I want** a Cost plan to state its spending ceiling, the categories it tracks, and who may release contingency,  
**so that** a plan cannot pass on word count alone while leaving the envelope, the spend types, or the reserve unnamed.

### Acceptance Criteria

- **$AC_0$ (Envelope):** A Cost body whose Section 1 has neither `envelope` nor `ceiling` produces one Tier B `MISSING_REQUIRED_SECTION` whose message says the management envelope is missing. The same words appearing only in Section 2 still produce that finding. A `pmp_section` whose Section 1 says `ceiling` produces no envelope finding, even with no unit and no approver.
- **$AC_1$ (Full envelope):** A `full_plan` whose Section 1 states a ceiling and lacks both a unit phrase (`unit`, `currency`, `euro`, `dollar`, `person-hour`, `person hour`, or `story point`) and an approver phrase (`approv` or `sponsor`) produces one `management envelope is incomplete` finding naming both gaps. Missing only one of them names that gap. `story point` alone satisfies the unit.
- **$AC_2$ (Categories):** Both routes produce `cost categories are missing` when Section 2 has no word beginning `categor`. A `full_plan` that names categories and lacks owner, source or measurement, range or accuracy, and a word beginning `estimat` produces one `cost categories and estimating basis are incomplete` finding naming each gap. A `pmp_section` that names categories produces no owner, source, range, or estimating finding.
- **$AC_3$ (Contingency):** Both routes produce `contingency rule is missing` when Section 2 has no word beginning `contingenc`. A `full_plan` that states contingency and lacks both `reserve` and `release` produces one `contingency and reserve rule is incomplete` finding naming both gaps. A `pmp_section` that states contingency produces no reserve or release finding.
- **$AC_4$ (No double finding):** A body with no Section 1 heading produces the existing heading finding and no envelope finding. A body with no Section 2 heading produces the existing heading finding and no category or contingency finding. A non-Cost plan and a `not_applicable` Cost plan receive no Cost section finding. No numeric amount is required.
- **$AC_5$ (Order):** On a Cost plan that fails headings, floor, and the envelope together, `lint_plan` returns heading findings, then the floor finding, then the Cost section findings.

---

## Story 27.3 — The idle Cost advisory policy

**Status:** Draft — blocked on confirmation of FDD-027 §5 item 1, and on acceptance of ADR-027  
**As** a maintainer,  
**I want** `advise-cost-plan-decision` declared as its own low-authority policy with equal logits and no episodes,  
**so that** a later recommendation has a fixed task id and cannot be trained as if it were the approval gate or another plan advisor.

### Acceptance Criteria

- **$AC_0$ (Identity):** `baseline_snapshot()` has task id `advise-cost-plan-decision`, `decision_authority` `low`, and `requires_human_approval` false. Every action in the confirmed kind table has logit 0.0. No other action is present.
- **$AC_1$ (Idle):** Constructing the snapshot creates no episode and writes nothing. A test double of the store receives no call.
- **$AC_2$ (Separate tasks):** The task id differs from `approve-subsidiary-plan`, `advise-scope-plan-decision`, and `advise-schedule-plan-decision`. A fixture episode whose task id is any of those is not a training input of this policy.
- **$AC_3$ (No prior):** The snapshot logits are all 0.0 and carry no prior copied from another plan's policy.
- **$AC_4$ (No selection episode):** The constructor does not build an ADR-024 methodology-selection episode.

---

## Story 27.4 — Record the recommendation, then show it

**Status:** Draft — blocked on Story 27.3  
**As** a maintainer reviewing a Cost recommendation,  
**I want** the recommendation stored with its time before I see it, and left unchanged after I follow or override it,  
**so that** the learner's evidence is the gap between its advice and my decision.

### Acceptance Criteria

- **$AC_0$ (Kind bounds the draw):** For each confirmed kind, the returned `action_id` is one of that kind's actions. An unknown kind raises `ValueError`.
- **$AC_1$ (Immutable):** Two calls with the same `recommendation_id` return the same `action_id` and the same `recommended_at`, even if the snapshot logits changed between the calls.
- **$AC_2$ (Withhold):** `min_shown_decisions is None` yields `visible=False`. The same for a count below a set minimum. A count equal to the minimum yields `visible=True`. A minimum of 0 or less raises `ValueError`.
- **$AC_3$ (Reward):** `advice_reward(True)` is 1.0 and `advice_reward(False)` is −1.0. The credited action is the stored recommendation action. The function has no parameter for `approve_plan`, `reject_plan`, or `request_revision_before_decision`.
- **$AC_4$ (No new record):** `cost_advice.py` imports no storage module. `CostRecommendation` is a frozen dataclass, not a `LearningStore` record type. A Scope or Schedule recommendation id is not returned as a Cost recommendation.

---

## Out of Scope for this epic

- Rewriting universal floors or caps in `standards.py`.
- Staleness, approval, formalization, and `PlanApprovalRecord.parent_hashes` (Epic 13).
- The Scope and Schedule profiles and their advisory policies, beyond sharing the lint-option signature.
- Revenue planning, and reading `tests/test_cost_model.py`.
- Joining stages to milestones or epics, or joining contingency amounts to risks.
- Deciding whether contingency reconciliation requires a fresh Cost approval.
- Training on synthetic episodes, a shared prior, or multi-stage credit assignment.
- Writing the ADR-024 selection episode. That is a human record made when the policy is declared.
