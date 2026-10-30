# Epic 31: Stakeholder Engagement Plan Standard

**Source ADR:** [ADR-031](../adr/ADR-031-stakeholder-engagement-plan-standard.md) — Accepted (2026-10-29, Menno), episode `c6564adb-72de-4262-8309-4949e0745f51`  
**Source BRD/FDD:** [BRD-031](../project-docs/Business-Requirements/BRD-031-stakeholder-engagement-plan-standard.md) / [FDD-031](../project-docs/Functional-Design/FDD-031-stakeholder-engagement-plan-standard.md)  
**Status:** Draft (2026-10-29) — derived from Accepted ADR-031, BRD-031 and FDD-031; not yet adjudicated via `approve-user-stories`.

Four stories. Each rule sits in one story (LL-012). Contract tests: `tests/test_stakeholder_measure.py` (31.1), `tests/test_stakeholder_sections.py` (31.2), `tests/test_stakeholder_advice_policy.py` (31.3), `tests/test_stakeholder_advice_reward.py` (31.4). Stories 31.3 and 31.4 wait until FDD-031 §5 item 1 is confirmed. BRU-031-07 has no story: it is the text the plan author writes and the approver reads.

---

## Story 31.1 — Stakeholder lengths and the full-plan exclusion minimum

**Status:** Draft — blocked on acceptance of ADR-031  
**As** a governance reviewer,  
**I want** a Stakeholder plan measured at the ADR-012 floors and caps, with two out-of-scope items on a full plan,  
**so that** Tier 3 does not inherit a higher floor, and a full plan still states more than one exclusion.

### Acceptance Criteria

- **$AC_0$ (Profile):** `stakeholder_measure("stakeholder-engagement", "pmp_section")` is floor 150, cap 800, minimum 1 item. `full_plan` is 600, 5,000, and 2. `not_applicable`, `resource-management`, and `scope-management` return `None`.
- **$AC_1$ (Section lengths):** For a Stakeholder `pmp_section`, word counts 149, 150, 159, 800, and 801 produce below-floor, no length finding, no length finding, no length finding, and `EXCEEDS_SECTION_CAP`. All length findings are Tier C. The call does not pass `min_floor_words` or `max_cap_words`.
- **$AC_2$ (Plan lengths):** For a Stakeholder `full_plan`, word counts 599, 600, 5,000, and 5,001 produce below-floor, no length finding, no length finding, and `EXCEEDS_PLAN_CAP`.
- **$AC_3$ (Other plans):** `check_stakeholder_sections` returns `[]` for a `resource-management` body. `lint_plan` on that plan does not append a Stakeholder register, level, or action finding.
- **$AC_4$ (Items):** A Stakeholder `pmp_section` with one bullet does not raise `MISSING_BOUNDARY_DEF`, including when that bullet is only `TBD`. A Stakeholder `full_plan` with one bullet does. Two bullets do not. A `None:` line of at least 10 tokens satisfies the boundary with zero bullets. A caller minimum below 2 leaves 2 in force for `full_plan`.
- **$AC_5$ (Omission and graph):** `lint_plan` on a `not_applicable` Stakeholder plan adds no Stakeholder content finding and no `OMISSION_OF_BASE_PLAN` finding. `PLAN_DAG["stakeholder-engagement"]` is `("scope-management",)`. No `PLAN_DAG` value contains `stakeholder-engagement`.
- **$AC_6$ (Purity):** `stakeholder.py` imports no storage module and adds no package to `pyproject.toml`. It does not read `Stakeholder-Register.md`.

---

## Story 31.2 — Register, engagement levels, and actions

**Status:** Draft — blocked on acceptance of ADR-031  
**As** a governance reviewer,  
**I want** a Stakeholder plan to state the register fields, the engagement scale, and the action that closes a gap,  
**so that** a plan cannot pass on word count alone while leaving the role source, the levels, or the actions unnamed.

### Acceptance Criteria

- **$AC_0$ (Register):** A Stakeholder body whose Section 1 has no `register` produces one Tier B `MISSING_REQUIRED_SECTION` whose message says the stakeholder register contract is missing. The word `register` only in Section 2 still produces that finding.
- **$AC_1$ (Key fields):** A `pmp_section` whose Section 1 has `register` and lacks location, an identifier (`identifier` or the whole word `id`), `role`, `interest`, or `influence` produces one `stakeholder register contract is incomplete` finding naming each gap. All five present produce no register finding.
- **$AC_2$ (Full field list):** A `full_plan` whose Section 1 has `register` and lacks any field in `REGISTER_FIELDS` produces one incomplete finding naming each gap. `role` satisfies both "name or role" and "project role". `organi` or `team` satisfies organization or team. `current`, `desired`, and `contact` satisfy the last three fields. A `pmp_section` does not require organization, current, desired, or contact.
- **$AC_3$ (Levels):** Both routes produce `engagement levels are missing`, naming scale, current, desired, or the ones that are absent, when Section 2 lacks a scale and lacks `current` or `desired`. The word `scale`, or at least two of `unaware`, `resistant`, `neutral`, `supportive`, and `leading`, satisfies the scale. Those words only in Section 1 still produce the finding. A `full_plan` with a scale, `current`, and `desired`, and with none of `all`, `every`, and `each`, produces `engagement levels are incomplete`. A `pmp_section` does not produce that finding.
- **$AC_4$ (Actions):** Both routes produce `engagement actions are missing` when Section 2 has no `action`. A `full_plan` that has `action` and lacks `owner`, or lacks `timing`, `timebox`, `time box`, and `milestone`, produces one `engagement actions are incomplete` finding naming each gap. A `pmp_section` that has `action` produces no owner or timing finding.
- **$AC_5$ (No double finding):** A body with no Section 1 heading produces the existing heading finding and no register finding. A body with no Section 2 heading produces the existing heading finding and no level or action finding. A non-Stakeholder plan and a `not_applicable` Stakeholder plan receive no Stakeholder section finding. No register row is parsed.
- **$AC_6$ (Order):** On a Stakeholder plan that fails headings, floor, and the register together, `lint_plan` returns heading findings, then the floor finding, then the Stakeholder section findings.

---

## Story 31.3 — The idle Stakeholder advisory policy

**Status:** Draft — blocked on confirmation of FDD-031 §5 item 1, and on acceptance of ADR-031  
**As** a maintainer,  
**I want** `advise-stakeholder-plan-decision` declared as its own low-authority policy with equal logits and no episodes,  
**so that** a later recommendation has a fixed task id and cannot be trained as the approval gate or another plan advisor.

### Acceptance Criteria

- **$AC_0$ (Identity):** `baseline_snapshot()` has task id `advise-stakeholder-plan-decision`, `decision_authority` `low`, and `requires_human_approval` false. Every action in the confirmed kind table has logit 0.0. No other action is present. The snapshot has no department map.
- **$AC_1$ (Idle):** Constructing the snapshot creates no episode and writes nothing. A test double of the store receives no call.
- **$AC_2$ (Separate tasks):** The task id differs from `approve-subsidiary-plan`, `advise-scope-plan-decision`, `advise-schedule-plan-decision`, `advise-cost-plan-decision`, `advise-risk-plan-decision`, `advise-quality-plan-decision`, and `advise-resource-plan-decision`. A fixture episode whose task id is any of those is not a training input of this policy.
- **$AC_3$ (No prior):** The snapshot logits are all 0.0 and carry no prior copied from another plan's policy.
- **$AC_4$ (No selection episode):** The constructor does not build an ADR-024 methodology-selection episode.

---

## Story 31.4 — Record the recommendation, then show it

**Status:** Draft — blocked on Story 31.3  
**As** a maintainer reviewing a Stakeholder recommendation,  
**I want** the recommendation stored with its time before I see it, and left unchanged after I follow or override it,  
**so that** the learner's evidence is the gap between its advice and my decision.

### Acceptance Criteria

- **$AC_0$ (Kind bounds the draw):** For each confirmed kind, the returned `action_id` is one of that kind's actions. An unknown kind raises `ValueError`.
- **$AC_1$ (Immutable):** Two calls with the same `recommendation_id` return the same `action_id` and the same `recommended_at`, even if the snapshot logits changed between the calls.
- **$AC_2$ (Withhold):** `min_shown_decisions is None` yields `visible=False`. The same for a count below a set minimum. A count equal to the minimum yields `visible=True`. A minimum of 0 or less raises `ValueError`.
- **$AC_3$ (Reward):** `advice_reward(True)` is 1.0 and `advice_reward(False)` is −1.0. The credited action is the stored recommendation action. The function has no parameter for a gate action.
- **$AC_4$ (No new record):** `stakeholder_advice.py` imports no storage module. `StakeholderRecommendation` is a frozen dataclass, not a `LearningStore` record type. A recommendation id from another plan advisor is not returned as a Stakeholder recommendation.

---

## Out of Scope for this epic

- Raising the Stakeholder floor or tightening the Stakeholder cap.
- Changing `PLAN_DAG`.
- Staleness, approval, formalization, and `OMISSION_OF_BASE_PLAN` (Epics 11 and 13).
- The other plan profiles and their advisory policies.
- Joining `owner_role` values to register rows, parsing those rows, or opening `Stakeholder-Register.md`.
- Scanning the plan for private personal data.
- Training on synthetic episodes or a shared prior.
- Writing the ADR-024 selection episode. That is a human record made when the policy is declared.
