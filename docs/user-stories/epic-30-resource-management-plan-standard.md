# Epic 30: Resource Management Plan Standard

**Source ADR:** [ADR-030](../adr/ADR-030-resource-management-plan-standard.md) — Accepted (2026-10-29, Menno), episode `de095357-d927-4408-8311-181e158a2abf`  
**Source BRD/FDD:** [BRD-030](../project-docs/Business-Requirements/BRD-030-resource-management-plan-standard.md) / [FDD-030](../project-docs/Functional-Design/FDD-030-resource-management-plan-standard.md)  
**Status:** Approved (2026-10-30, Menno) — derived from Accepted ADR-030, BRD-030 and FDD-030 (Approved 2026-10-30); adjudicated via `approve-user-stories` (robust utility 0.735, episode `742976ba-7bd5-497f-9cc7-a3ba35bc4dc1`).

Four stories. Each rule sits in one story (LL-012). Contract tests: `tests/test_resource_measure.py` (30.1), `tests/test_resource_sections.py` (30.2), `tests/test_resource_advice_policy.py` (30.3), `tests/test_resource_advice_reward.py` (30.4). Stories 30.3 and 30.4 wait until FDD-030 §5 items 1 and 2 are confirmed. BRU-030-07 has no story: it is the text the plan author writes and the approver reads.

---

## Story 30.1 — Resource lengths and the full-plan exclusion minimum

**Status:** Ready
**As** a governance reviewer,  
**I want** a Resource plan measured at the ADR-012 floors and caps, with two out-of-scope items on a full plan,  
**so that** Tier 3 does not inherit a higher floor, and a full plan still states more than one exclusion.

### Acceptance Criteria

- **$AC_0$ (Profile):** `resource_measure("resource-management", "pmp_section")` is floor 150, cap 800, minimum 1 item. `full_plan` is 600, 5,000, and 2. `not_applicable`, `quality-management`, and `cost-management` return `None`.
- **$AC_1$ (Section lengths):** For a Resource `pmp_section`, word counts 149, 150, 159, 800, and 801 produce below-floor, no length finding, no length finding, no length finding, and `EXCEEDS_SECTION_CAP`. All length findings are Tier C. The call does not pass `min_floor_words` or `max_cap_words`.
- **$AC_2$ (Plan lengths):** For a Resource `full_plan`, word counts 599, 600, 5,000, and 5,001 produce below-floor, no length finding, no length finding, and `EXCEEDS_PLAN_CAP`.
- **$AC_3$ (Other plans):** `check_resource_sections` returns `[]` for a `quality-management` body. `lint_plan` on that plan does not append a Resource catalogue, allocation, or tooling finding. Its floor, when one is produced, is the universal floor.
- **$AC_4$ (Items):** A Resource `pmp_section` with one bullet does not raise `MISSING_BOUNDARY_DEF`, including when that bullet is only `TBD`. A Resource `full_plan` with one bullet does. Two bullets do not. A `None:` line of at least 10 tokens satisfies the boundary with zero bullets. A caller minimum below 2 leaves 2 in force for `full_plan`.
- **$AC_5$ (Omission and graph):** `lint_plan` on a `not_applicable` Resource plan adds no Resource content finding and no `OMISSION_OF_BASE_PLAN` finding. `PLAN_DAG["resource-management"]` is `("scope-management", "schedule-management")`. `PLAN_DAG["cost-management"]` does not contain `resource-management`. No `PLAN_DAG` value contains `resource-management`.
- **$AC_6$ (Purity):** `resource.py` imports no storage module and adds no package to `pyproject.toml`.

---

## Story 30.2 — Catalogue, allocation, and tooling

**Status:** Ready
**As** a governance reviewer,  
**I want** a Resource plan to name who is accountable, how capacity is allocated, and which tools the work needs,  
**so that** a plan cannot pass on word count alone while leaving the roles, the capacity, or the assets unnamed.

### Acceptance Criteria

- **$AC_0$ (Catalogue):** A Resource body whose Section 2 has no `role` produces one Tier B `MISSING_REQUIRED_SECTION` whose message says the role catalogue is missing. A Section 2 that has `role` and no `accountable` produces `role catalogue has no accountable owner`. The bare word `owner` does not satisfy that check.
- **$AC_1$ (Full catalogue):** A `full_plan` whose Section 2 has `role` and `accountable`, and lacks `responsib` or `decision`, produces one `role catalogue is incomplete` finding naming each gap. A `pmp_section` with `role` and `accountable` produces no responsibilities or decision-rights finding.
- **$AC_2$ (Agents):** A Section 2 that matches `agent` and lacks `accountable` or `human` produces `agent work has no accountable human`. A Section 2 with no `agent` produces no such finding. A Section 2 with `agent`, `accountable`, and `human` produces no such finding.
- **$AC_3$ (Allocation):** Both routes produce `allocation and capacity are missing` when Section 2 has neither `capacity` nor a word beginning `allocat`. A `full_plan` that has `capacity` and lacks `allocat`, a timebox (`timebox` or `time box`), or `basis` produces one `allocation and capacity are incomplete` finding naming each gap. A `pmp_section` that states `capacity` produces no timebox or basis finding.
- **$AC_4$ (Tooling):** Both routes produce `tooling assets are missing` when Section 2 has none of `asset`, `tooling`, `tool`, `licence`, `license`, and `environment`. A `full_plan` that lists a tool and lacks `owner` or a lead time (`lead time` or `lead-time`) produces one `tooling assets are incomplete` finding naming each gap. A `pmp_section` that lists a tool produces no owner or lead-time finding.
- **$AC_5$ (No double finding):** A body with no Section 2 heading produces the existing heading finding and no Resource section finding. A non-Resource plan and a `not_applicable` Resource plan receive no Resource section finding.
- **$AC_6$ (Order):** On a Resource plan that fails headings, floor, and the catalogue together, `lint_plan` returns heading findings, then the floor finding, then the Resource section findings.

---

## Story 30.3 — The idle Resource advisory policy

**Status:** Draft — blocked on confirmation of FDD-030 §5 items 1 and 2  
**As** a maintainer,  
**I want** `advise-resource-plan-decision` declared as its own low-authority policy with a separate logit map for Procurement and for HR,  
**so that** a later recommendation has a fixed task id and a materials decision cannot train a human-resources decision.

### Acceptance Criteria

- **$AC_0$ (Identity):** `baseline_snapshot()` has task id `advise-resource-plan-decision`, `decision_authority` `low`, and `requires_human_approval` false. `metadata["department_logits"]` has exactly `procurement` and `hr`. Each map has every action in the confirmed kind table at logit 0.0 and no other action. `PolicySnapshot.logits` is empty.
- **$AC_1$ (Separate maps):** The two department maps compare equal and are not the same object. Replacing a value in one map does not change the other.
- **$AC_2$ (Idle):** Constructing the snapshot creates no episode and writes nothing. A test double of the store receives no call.
- **$AC_3$ (Separate tasks):** The task id differs from `approve-subsidiary-plan`, `advise-scope-plan-decision`, `advise-schedule-plan-decision`, `advise-cost-plan-decision`, `advise-risk-plan-decision`, and `advise-quality-plan-decision`. A fixture episode whose task id is any of those is not a training input of this policy.
- **$AC_4$ (No prior and no selection episode):** Neither department's logits are copied from another plan's policy. The constructor does not build an ADR-024 methodology-selection episode.

---

## Story 30.4 — Record the recommendation, then show it

**Status:** Draft — blocked on Story 30.3  
**As** a maintainer reviewing a Resource recommendation,  
**I want** the recommendation stored with its department and its time before I see it, and left unchanged after I follow or override it,  
**so that** the learner's evidence is the gap between its advice and my decision, kept apart by department.

### Acceptance Criteria

- **$AC_0$ (Kind and department bound the draw):** For each confirmed kind and each department, the returned `action_id` is one of that kind's actions and `deciding_department` is the department that was passed. The draw reads that department's logits. An unknown kind or an unknown department raises `ValueError`.
- **$AC_1$ (Immutable):** Two calls with the same `recommendation_id` return the same `action_id`, the same `deciding_department`, and the same `recommended_at`, even if the second call passes the other department or the logits changed.
- **$AC_2$ (Withhold):** `min_shown_decisions is None` yields `visible=False`. The same for a count below a set minimum. A count equal to the minimum yields `visible=True`. A minimum of 0 or less raises `ValueError`.
- **$AC_3$ (Reward stays in the department):** `advice_reward(True)` is 1.0 and `advice_reward(False)` is −1.0. Applying it credits the stored action on the stored department's logit map and leaves the other department's map unchanged. The function has no parameter for a gate action.
- **$AC_4$ (No new record):** `resource_advice.py` imports no storage module. `ResourceRecommendation` is a frozen dataclass, not a `LearningStore` record type.

---

## Out of Scope for this epic

- Raising the Resource floor or tightening the Resource cap.
- Changing `PLAN_DAG`, including any edge between Cost and Resource.
- Staleness, approval, formalization, and `OMISSION_OF_BASE_PLAN` (Epics 11 and 13).
- The other plan profiles and their advisory policies.
- A team charter, a RACI chart, and a comparison of capacity units with the Schedule file.
- Encoding the human-only decisions of ADR-001 and ADR-008.
- Training on synthetic episodes or a shared prior.
- Writing the ADR-024 selection episode. That is a human record made when the policy is declared.
