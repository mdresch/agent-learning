# Epic 33: Procurement Management Plan Standard

**Source ADR:** [ADR-033](../adr/ADR-033-procurement-management-plan-standard.md) — Accepted (2026-10-29, Menno), episode `7362459e-b596-4f85-8872-5b7063eef015`  
**Source BRD/FDD:** [BRD-033](../project-docs/Business-Requirements/BRD-033-procurement-management-plan-standard.md) / [FDD-033](../project-docs/Functional-Design/FDD-033-procurement-management-plan-standard.md)  
**Status:** Approved (2026-10-30, Menno) — derived from Accepted ADR-033, BRD-033 and FDD-033 (Approved 2026-10-30); adjudicated via `approve-user-stories` (robust utility 0.735, episode `cb743658-ee2d-4e96-b796-434cfd466a06`).

Four stories. Each rule sits in one story (LL-012). Contract tests: `tests/test_procurement_measure.py` (33.1), `tests/test_procurement_sections.py` (33.2), `tests/test_procurement_advice_policy.py` (33.3), `tests/test_procurement_advice_reward.py` (33.4). Stories 33.3 and 33.4 wait until FDD-033 §5 items 1 and 2 are confirmed. BRU-033-07 has no story: it is the text the plan author writes and the approver reads.

---

## Story 33.1 — Procurement lengths and the full-plan exclusion minimum

**Status:** Ready
**As** a governance reviewer,  
**I want** a Procurement plan measured at the ADR-012 floors and caps, with two out-of-scope items on a full plan,  
**so that** Tier 3 does not inherit Cost's tighter floor, and a full plan still states more than one exclusion.

### Acceptance Criteria

- **$AC_0$ (Profile):** `procurement_measure("procurement-management", "pmp_section")` is floor 150, cap 800, minimum 1 item. `full_plan` is 600, 5,000, and 2. `not_applicable`, `cost-management`, and `resource-management` return `None`.
- **$AC_1$ (Section lengths):** For a Procurement `pmp_section`, word counts 149, 150, 159, 800, and 801 produce below-floor, no length finding, no length finding, no length finding, and `EXCEEDS_SECTION_CAP`. All length findings are Tier C. The call does not pass `min_floor_words` or `max_cap_words`.
- **$AC_2$ (Plan lengths):** For a Procurement `full_plan`, word counts 599, 600, 5,000, and 5,001 produce below-floor, no length finding, no length finding, and `EXCEEDS_PLAN_CAP`.
- **$AC_3$ (Other plans):** `check_procurement_sections` returns `[]` for a `cost-management` body. `lint_plan` on that plan does not append a Procurement make-or-buy, intake, or licence finding. Its floor, when one is produced, is the universal floor.
- **$AC_4$ (Items):** A Procurement `pmp_section` with one bullet does not raise `MISSING_BOUNDARY_DEF`, including when that bullet is only `TBD`. A Procurement `full_plan` with one bullet does. Two bullets do not. A `None:` line of at least 10 tokens satisfies the boundary with zero bullets. A caller minimum below 2 leaves 2 in force for `full_plan`.
- **$AC_5$ (Omission and graph):** `lint_plan` on a `not_applicable` Procurement plan adds no Procurement content finding and no `OMISSION_OF_BASE_PLAN` finding. `PLAN_DAG["procurement-management"]` is `("scope-management", "cost-management")` and does not contain `resource-management`. `PLAN_DAG["cost-management"]` does not contain `procurement-management`. No `PLAN_DAG` value contains `procurement-management`.
- **$AC_6$ (Purity):** `procurement.py` imports no storage module and adds no package to `pyproject.toml`. It does not read the Cost plan and it does not read `pyproject.toml` as an intake register.

---

## Story 33.2 — Make-or-buy criteria, intake rule, and licence checks

**Status:** Ready
**As** a governance reviewer,  
**I want** a Procurement plan to name the make-or-buy factors, the intake justification, and the licence checks,  
**so that** a plan cannot pass on word count alone while leaving the buy decision, the dependency record, or the licence terms unnamed.

### Acceptance Criteria

- **$AC_0$ (Make-or-buy missing):** A Procurement body whose Section 2 has neither `make-or-buy` nor `make or buy` produces one Tier B `MISSING_REQUIRED_SECTION` whose message says the make-or-buy criteria are missing. Those phrases only in Section 1 still produce that finding. `factor` and `weight` in that Section 2 do not add `make-or-buy criteria are incomplete`.
- **$AC_1$ (Make-or-buy parts):** When Section 2 has `make-or-buy` or `make or buy`, both routes that lack `factor` produce one `make-or-buy criteria are incomplete` finding naming factors. A `full_plan` that has `factor` and lacks `weight` names weighting in that same finding style, one finding for each missing part. A `pmp_section` that has the phrase and `factor` produces no weighting finding and no missing finding. The missing finding and the incomplete finding do not both fire.
- **$AC_2$ (Intake):** Both routes produce `dependency intake rule is missing` when Section 2 has no `intake`. A `full_plan` that has `intake` and lacks `need`, `alternative`, `licen`, `maintenance`, or `exit` produces one `dependency intake rule is incomplete` finding naming each gap. `licence` and `license` both satisfy `licen`. The word `maintainer` does not satisfy `maintenance`. A `pmp_section` that has `intake` produces no justification-field finding. Field words with no `intake` produce the missing finding and do not produce the incomplete finding.
- **$AC_3$ (Licence checks):** Both routes produce `contract and licence checks are missing` when Section 2 has neither `contract` nor `licen`. When either word is present, both routes that lack `compatib`, `usage`, both `data` and `retain`, or a change-of-terms phrase (`change-of-term` or `change of term`) produce one `contract and licence checks are incomplete` finding naming each gap. `retention` satisfies `retain`. A `full_plan` that lists the four checks and lacks `owner` names verification owner in that finding. A `pmp_section` that lists the four checks produces no owner finding. Check words with neither `contract` nor `licen` produce the missing finding and do not produce the incomplete finding.
- **$AC_4$ (No double finding):** A body with no Section 2 heading produces the existing heading finding and no make-or-buy, intake, or licence finding. A non-Procurement plan and a `not_applicable` Procurement plan receive no Procurement section finding. No intake row is parsed.
- **$AC_5$ (Order):** On a Procurement plan that fails headings, floor, and the make-or-buy statement together, `lint_plan` returns heading findings, then the floor finding, then the Procurement section findings. When make-or-buy, the intake rule, and the licence checks are all missing, the findings are make-or-buy, then intake, then contract and licence.

---

## Story 33.3 — The idle Procurement advisory policy

**Status:** Draft — blocked on confirmation of FDD-033 §5 items 1 and 2  
**As** a maintainer,  
**I want** `advise-procurement-plan-decision` declared as its own low-authority policy with one logit map,  
**so that** a later recommendation has a fixed task id and a recorded deciding role, and cannot be trained as the approval gate, the Resource department split, or another plan advisor.

### Acceptance Criteria

- **$AC_0$ (Identity):** `baseline_snapshot()` has task id `advise-procurement-plan-decision`, `decision_authority` `low`, and `requires_human_approval` false. `PolicySnapshot.logits` has every action in the confirmed kind table at logit 0.0 and no other action. The snapshot has no department map and no per-role logit map.
- **$AC_1$ (Idle):** Constructing the snapshot creates no episode and writes nothing. A test double of the store receives no call.
- **$AC_2$ (Separate tasks):** The task id differs from `approve-subsidiary-plan`, `advise-scope-plan-decision`, `advise-schedule-plan-decision`, `advise-cost-plan-decision`, `advise-risk-plan-decision`, `advise-quality-plan-decision`, `advise-resource-plan-decision`, `advise-stakeholder-plan-decision`, and `advise-communications-plan-decision`. A fixture episode whose task id is any of those is not a training input of this policy.
- **$AC_3$ (No prior):** The snapshot logits are all 0.0 and carry no prior copied from another plan's policy, including the Resource policy's `procurement` department map.
- **$AC_4$ (No selection episode):** The constructor does not build an ADR-024 methodology-selection episode.

---

## Story 33.4 — Record the recommendation, then show it

**Status:** Draft — blocked on Story 33.3  
**As** a maintainer reviewing a Procurement recommendation,  
**I want** the recommendation stored with its deciding role and its time before I see it, and left unchanged after I follow or override it,  
**so that** the learner's evidence is the gap between its advice and my decision, with the role that made the pair kept on the record.

### Acceptance Criteria

- **$AC_0$ (Kind bounds the draw):** For each confirmed kind and each confirmed role, the returned `action_id` is one of that kind's actions and `deciding_role` is the role that was passed. The draw reads `PolicySnapshot.logits`. An unknown kind or an unknown role raises `ValueError`.
- **$AC_1$ (Immutable):** Two calls with the same `recommendation_id` return the same `action_id`, the same `deciding_role`, and the same `recommended_at`, even if the second call passes the other role or the logits changed.
- **$AC_2$ (Withhold):** `min_shown_decisions is None` yields `visible=False`. The same for a count below a set minimum. A count equal to the minimum yields `visible=True`. A minimum of 0 or less raises `ValueError`.
- **$AC_3$ (Reward):** `advice_reward(True)` is 1.0 and `advice_reward(False)` is −1.0. The credited action is the stored recommendation action on the single logit map. The stored `deciding_role` is unchanged. The function has no parameter for a gate action and no parameter that selects a second map.
- **$AC_4$ (No new record):** `procurement_advice.py` imports no storage module. `ProcurementRecommendation` is a frozen dataclass, not a `LearningStore` record type. A recommendation id from another plan advisor is not returned as a Procurement recommendation.

---

## Out of Scope for this epic

- Raising the Procurement floor or tightening the Procurement cap.
- Copying Cost's 180, 700, 750, or 4,500 into this profile.
- Changing `PLAN_DAG`.
- Staleness, approval, formalization, and `OMISSION_OF_BASE_PLAN` (Epics 11 and 13).
- The other plan profiles and their advisory policies, including the Resource department maps.
- Reading `pyproject.toml` or the Cost plan.
- Supplier selection scorecards and supplier performance monitoring.
- A second logit map for the deciding role.
- Training on synthetic episodes or a shared prior.
- Writing the ADR-024 selection episode. That is a human record made when the policy is declared.
