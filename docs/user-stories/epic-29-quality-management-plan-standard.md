# Epic 29: Quality Management Plan Standard

**Source ADR:** [ADR-029](../adr/ADR-029-quality-management-plan-standard.md) — Accepted (2026-10-29, Menno), episode `736036f7-40a1-441f-afc0-062501c46d57`  
**Source BRD/FDD:** [BRD-029](../project-docs/Business-Requirements/BRD-029-quality-management-plan-standard.md) / [FDD-029](../project-docs/Functional-Design/FDD-029-quality-management-plan-standard.md)  
**Status:** Draft (2026-10-29) — derived from Accepted ADR-029, BRD-029 and FDD-029; not yet adjudicated via `approve-user-stories`.

Four stories. Each rule sits in one story (LL-012). Contract tests: `tests/test_quality_measure.py` (29.1), `tests/test_quality_sections.py` (29.2), `tests/test_quality_advice_policy.py` (29.3), `tests/test_quality_advice_reward.py` (29.4). Stories 29.3 and 29.4 wait until FDD-029 §5 item 1 is confirmed. BRU-029-07 has no story: it is the text the plan author writes and the approver reads.

---

## Story 29.1 — Quality floors, caps, and exclusions

**Status:** Draft — blocked on acceptance of ADR-029  
**As** a governance reviewer,  
**I want** a Quality plan measured with the Tier 2 floors and the universal caps,  
**so that** a short Quality plan is flagged and a plan inside the universal cap is not pushed over a tighter cap that this standard does not set.

### Acceptance Criteria

- **$AC_0$ (Profile):** `quality_measure("quality-management", "pmp_section")` is floor 160, cap 800, minimum 1 item. `full_plan` is 650, 5,000, and 2. `not_applicable`, `risk-management`, and `scope-management` return `None`.
- **$AC_1$ (Section lengths):** For a Quality `pmp_section`, word counts 159, 160, 751, 800, and 801 produce below-floor, no length finding, no length finding, no length finding, and `EXCEEDS_SECTION_CAP`. All length findings are Tier C.
- **$AC_2$ (Plan lengths):** For a Quality `full_plan`, word counts 649, 650, 5,000, and 5,001 produce below-floor, no length finding, no length finding, and `EXCEEDS_PLAN_CAP`.
- **$AC_3$ (Other plans):** 159 words on a `risk-management` `pmp_section` is not a Quality floor finding. This profile does not pass `max_cap_words`.
- **$AC_4$ (Items):** A Quality `pmp_section` with one bullet does not raise `MISSING_BOUNDARY_DEF`, including when that bullet is only `TBD`. A Quality `full_plan` with one bullet does. Two bullets do not. A `None:` line of at least 10 tokens satisfies the boundary with zero bullets. A caller minimum below 2 leaves 2 in force for `full_plan`.
- **$AC_5$ (Omission):** `lint_plan` on a `not_applicable` Quality plan adds no Quality content finding and no `OMISSION_OF_BASE_PLAN` finding.
- **$AC_6$ (Purity):** `quality.py` imports no storage module and adds no package to `pyproject.toml`.

---

## Story 29.2 — Gates, verification, and nonconformance

**Status:** Draft — blocked on acceptance of ADR-029  
**As** a governance reviewer,  
**I want** a Quality plan to state how a gate is passed, what verification must show, and what happens when a gate fails,  
**so that** a plan cannot pass on word count alone while leaving the gate, the check, or the failure path unnamed.

### Acceptance Criteria

- **$AC_0$ (Gates):** A Quality body whose Section 2 has no `gate` produces one Tier B `MISSING_REQUIRED_SECTION` whose message says the quality gates are missing. The word `gate` only in Section 1 or Section 3 still produces that finding. A Section 2 that has `gate` and has neither `pass` nor a word beginning `criteri` produces `quality gates have no pass criteria` and no second gate finding.
- **$AC_1$ (Full gates):** A `full_plan` whose Section 2 has a gate and pass criteria, and lacks `evidence` or `owner`, produces one `quality gates are incomplete` finding naming each gap. A `pmp_section` with a gate and `pass` produces no evidence or owner finding.
- **$AC_2$ (Verification):** Both routes produce `verification criteria are missing`, naming `types`, `minimum`, or both, when Section 2 has none of `unit`, `contract`, `integration`, and `peer review`, or has no `minimum` and no `threshold`. One type and `minimum` produce no such finding on a `pmp_section`. A `full_plan` with a type and a minimum, and with neither `coverage` nor a word beginning `measur`, produces `verification criteria are incomplete` naming measurement scope. The bare word `scope` does not satisfy that check.
- **$AC_3$ (Nonconformance):** Both routes produce `nonconformance handling is missing` when Section 2 has none of `nonconformance`, `non-conformance`, and `rework`. A `full_plan` that has `nonconformance` and lacks `triage`, `waiver`, or `rework` produces one `nonconformance handling is incomplete` finding naming each gap. A `pmp_section` that has `rework` produces no triage or waiver finding.
- **$AC_4$ (No double finding):** A body with no Section 2 heading produces the existing heading finding and no Quality section finding. A non-Quality plan and a `not_applicable` Quality plan receive no Quality section finding. No numeric coverage value is required.
- **$AC_5$ (Order):** On a Quality plan that fails headings, floor, and the gates together, `lint_plan` returns heading findings, then the floor finding, then the Quality section findings.

---

## Story 29.3 — The idle Quality advisory policy

**Status:** Draft — blocked on confirmation of FDD-029 §5 item 1, and on acceptance of ADR-029  
**As** a maintainer,  
**I want** `advise-quality-plan-decision` declared as its own low-authority policy with equal logits and no episodes,  
**so that** a later recommendation has a fixed task id and cannot waive a gate or be trained as the approval gate.

### Acceptance Criteria

- **$AC_0$ (Identity):** `baseline_snapshot()` has task id `advise-quality-plan-decision`, `decision_authority` `low`, and `requires_human_approval` false. Every action in the confirmed kind table has logit 0.0. No other action is present. No action id waives a gate, and no action id is rework or escalate.
- **$AC_1$ (Idle):** Constructing the snapshot creates no episode and writes nothing. A test double of the store receives no call.
- **$AC_2$ (Separate tasks):** The task id differs from `approve-subsidiary-plan`, `advise-scope-plan-decision`, `advise-schedule-plan-decision`, `advise-cost-plan-decision`, and `advise-risk-plan-decision`. A fixture episode whose task id is any of those is not a training input of this policy.
- **$AC_3$ (No prior):** The snapshot logits are all 0.0 and carry no prior copied from another plan's policy.
- **$AC_4$ (No selection episode):** The constructor does not build an ADR-024 methodology-selection episode.

---

## Story 29.4 — Record the recommendation, then show it

**Status:** Draft — blocked on Story 29.3  
**As** a maintainer reviewing a Quality recommendation,  
**I want** the recommendation stored with its time before I see it, and left unchanged after I follow or override it,  
**so that** the learner's evidence is the gap between its advice and my decision.

### Acceptance Criteria

- **$AC_0$ (Kind bounds the draw):** For each confirmed kind, the returned `action_id` is one of that kind's actions. An unknown kind raises `ValueError`.
- **$AC_1$ (Immutable):** Two calls with the same `recommendation_id` return the same `action_id` and the same `recommended_at`, even if the snapshot logits changed between the calls.
- **$AC_2$ (Withhold):** `min_shown_decisions is None` yields `visible=False`. The same for a count below a set minimum. A count equal to the minimum yields `visible=True`. A minimum of 0 or less raises `ValueError`.
- **$AC_3$ (Reward):** `advice_reward(True)` is 1.0 and `advice_reward(False)` is −1.0. The credited action is the stored recommendation action. The function has no parameter for a gate action and no parameter for a waiver.
- **$AC_4$ (No new record):** `quality_advice.py` imports no storage module. `QualityRecommendation` is a frozen dataclass, not a `LearningStore` record type. A recommendation id from another plan advisor is not returned as a Quality recommendation.

---

## Out of Scope for this epic

- Rewriting universal floors or caps in `standards.py`.
- Tightening the Quality cap below 800 or 5,000.
- Staleness, approval, formalization, and `OMISSION_OF_BASE_PLAN` (Epics 11 and 13).
- The Scope, Schedule, Cost, and Risk profiles and their advisory policies.
- Editing the Scope Definition of Done, or reading test and coverage reports.
- The later nonconformance-triage policy, and any action that waives a gate.
- Training on synthetic episodes or a shared prior.
- Writing the ADR-024 selection episode. That is a human record made when the policy is declared.
