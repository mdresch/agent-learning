# Epic 28: Risk Management Plan Standard

**Source ADR:** [ADR-028](../adr/ADR-028-risk-management-plan-standard.md) — Accepted (2026-10-29, Menno), episode `8bad2024-ef80-4cbf-8497-8ffb92c8b564`  
**Source BRD/FDD:** [BRD-028](../project-docs/Business-Requirements/BRD-028-risk-management-plan-standard.md) / [FDD-028](../project-docs/Functional-Design/FDD-028-risk-management-plan-standard.md)  
**Status:** Approved (2026-10-30, Menno) — derived from Accepted ADR-028, BRD-028 and FDD-028 (Approved 2026-10-30); adjudicated via `approve-user-stories` (robust utility 0.735, episode `3ae2aa80-db44-442c-984f-506e8d7ad816`).

Four stories. Each rule sits in one story (LL-012). Contract tests: `tests/test_risk_measure.py` (28.1), `tests/test_risk_sections.py` (28.2), `tests/test_risk_advice_policy.py` (28.3), `tests/test_risk_advice_reward.py` (28.4). Stories 28.3 and 28.4 wait until FDD-028 §5 item 1 is confirmed. BRU-028-07 has no story: it is the text the plan author writes and the approver reads.

---

## Story 28.1 — Risk floors, caps, and exclusions

**Status:** Ready
**As** a governance reviewer,  
**I want** a Risk plan measured with the Tier 2 floors and the universal caps,  
**so that** a short Risk plan is flagged and a plan inside the universal cap is not pushed over a tighter cap that this standard does not set.

### Acceptance Criteria

- **$AC_0$ (Profile):** `risk_measure("risk-management", "pmp_section")` is floor 160, cap 800, minimum 1 item. `full_plan` is 650, 5,000, and 2. `not_applicable`, `cost-management`, and `scope-management` return `None`.
- **$AC_1$ (Section lengths):** For a Risk `pmp_section`, word counts 159, 160, 751, 800, and 801 produce below-floor, no length finding, no length finding, no length finding, and `EXCEEDS_SECTION_CAP`. All length findings are Tier C.
- **$AC_2$ (Plan lengths):** For a Risk `full_plan`, word counts 649, 650, 5,000, and 5,001 produce below-floor, no length finding, no length finding, and `EXCEEDS_PLAN_CAP`.
- **$AC_3$ (Other plans):** 159 words on a `cost-management` `pmp_section` is not a Risk floor finding. This profile does not pass `max_cap_words`.
- **$AC_4$ (Items):** A Risk `pmp_section` with one bullet does not raise `MISSING_BOUNDARY_DEF`, including when that bullet is only `TBD`. A Risk `full_plan` with one bullet does. Two bullets do not. A `None:` line of at least 10 tokens satisfies the boundary with zero bullets. A caller minimum below 2 leaves 2 in force for `full_plan`.
- **$AC_5$ (Omission):** `lint_plan` on a `not_applicable` Risk plan adds no Risk content finding and no `OMISSION_OF_BASE_PLAN` finding.
- **$AC_6$ (Purity):** `risk.py` imports no storage module and adds no package to `pyproject.toml`.

---

## Story 28.2 — Scale, register contract, and escalation

**Status:** Ready
**As** a governance reviewer,  
**I want** a Risk plan to state how a rating is produced, which fields a register row carries, and when a risk reaches a person,  
**so that** a plan cannot pass on word count alone while leaving the scale, the register, or the threshold unnamed.

### Acceptance Criteria

- **$AC_0$ (Scale):** A Risk body whose Section 2 lacks probability, impact, or both `band` and `scale` produces one Tier B `MISSING_REQUIRED_SECTION` naming each missing part. The same words appearing only in Section 3 still produce that finding. A `pmp_section` whose Section 2 contains probability, impact, and `band` produces no scale finding.
- **$AC_1$ (Full scale):** A `full_plan` whose scale words are present and that lacks both `objective` and `combin` produces one `probability-impact scale is incomplete` finding naming both gaps. Missing only one of them names that gap. A `pmp_section` does not produce that finding.
- **$AC_2$ (Register):** Both routes produce `risk register contract is missing` when Section 2 has no `register`. A `pmp_section` that has `register` and lacks `location`, an identifier (`identifier` or the whole word `id`), and `owner` produces one incomplete finding naming those gaps. `rating` or `status` satisfies the remaining key field. A `full_plan` that has `register` and lacks any field in `REGISTER_FIELDS` produces one incomplete finding naming each missing field.
- **$AC_3$ (Escalation):** Both routes produce `escalation threshold is missing` when Section 3 has neither `threshold` nor `escalat`. Those words in Section 2 do not satisfy the check. A `full_plan` whose Section 3 has a threshold and lacks `sponsor` or `approver`, and lacks `recorded` or `acceptance`, produces one `escalation threshold is incomplete` finding naming both gaps. A `pmp_section` that states `threshold` produces no target or acceptance finding.
- **$AC_4$ (No double finding):** A body with no Section 2 heading produces the existing heading finding and no scale or register finding. A body with no Section 3 heading produces the existing heading finding and no escalation finding. A non-Risk plan and a `not_applicable` Risk plan receive no Risk section finding. No numeric score is required.
- **$AC_5$ (Order):** On a Risk plan that fails headings, floor, and the scale together, `lint_plan` returns heading findings, then the floor finding, then the Risk section findings.

---

## Story 28.3 — The idle Risk advisory policy

**Status:** Draft — blocked on confirmation of FDD-028 §5 item 1  
**As** a maintainer,  
**I want** `advise-risk-plan-decision` declared as its own low-authority policy with equal logits and no episodes,  
**so that** a later recommendation has a fixed task id and cannot accept a risk or be trained as the approval gate.

### Acceptance Criteria

- **$AC_0$ (Identity):** `baseline_snapshot()` has task id `advise-risk-plan-decision`, `decision_authority` `low`, and `requires_human_approval` false. Every action in the confirmed kind table has logit 0.0. No other action is present. No action id accepts a risk.
- **$AC_1$ (Idle):** Constructing the snapshot creates no episode and writes nothing. A test double of the store receives no call.
- **$AC_2$ (Separate tasks):** The task id differs from `approve-subsidiary-plan`, `advise-scope-plan-decision`, `advise-schedule-plan-decision`, and `advise-cost-plan-decision`. A fixture episode whose task id is any of those is not a training input of this policy.
- **$AC_3$ (No prior):** The snapshot logits are all 0.0 and carry no prior copied from another plan's policy.
- **$AC_4$ (No selection episode):** The constructor does not build an ADR-024 methodology-selection episode.

---

## Story 28.4 — Record the recommendation, then show it

**Status:** Draft — blocked on Story 28.3  
**As** a maintainer reviewing a Risk recommendation,  
**I want** the recommendation stored with its time before I see it, and left unchanged after I follow or override it,  
**so that** the learner's evidence is the gap between its advice and my decision.

### Acceptance Criteria

- **$AC_0$ (Kind bounds the draw):** For each confirmed kind, the returned `action_id` is one of that kind's actions. An unknown kind raises `ValueError`.
- **$AC_1$ (Immutable):** Two calls with the same `recommendation_id` return the same `action_id` and the same `recommended_at`, even if the snapshot logits changed between the calls.
- **$AC_2$ (Withhold):** `min_shown_decisions is None` yields `visible=False`. The same for a count below a set minimum. A count equal to the minimum yields `visible=True`. A minimum of 0 or less raises `ValueError`.
- **$AC_3$ (Reward):** `advice_reward(True)` is 1.0 and `advice_reward(False)` is −1.0. The credited action is the stored recommendation action. The function has no parameter for a gate action and no parameter for accepting a risk.
- **$AC_4$ (No new record):** `risk_advice.py` imports no storage module. `RiskRecommendation` is a frozen dataclass, not a `LearningStore` record type. A recommendation id from another plan advisor is not returned as a Risk recommendation.

---

## Out of Scope for this epic

- Rewriting universal floors or caps in `standards.py`.
- Tightening the Risk cap below 800 or 5,000.
- Staleness, approval, formalization, and `OMISSION_OF_BASE_PLAN` (Epics 11 and 13).
- The Scope, Schedule, and Cost profiles and their advisory policies.
- Parsing register rows, recomputing ratings, or reading the Stakeholder Register.
- Monte Carlo, and safe bandits with action masking.
- Training on synthetic episodes or a shared prior.
- Writing the ADR-024 selection episode. That is a human record made when the policy is declared.
