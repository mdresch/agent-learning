# Epic 25: Scope Management Plan Standard and Baseline Contract

**Source ADR:** [ADR-025](../adr/ADR-025-scope-management-plan-standard-and-baseline-contract.md) — Accepted (2026-10-26, Menno); re-approved 2026-10-29, episode `983c2b87-8309-4414-98fe-93337989b9b5`  
**Source BRD/FDD:** [BRD-025](../project-docs/Business-Requirements/BRD-025-scope-management-plan-standard-and-baseline-contract.md) / [FDD-025](../project-docs/Functional-Design/FDD-025-scope-management-plan-standard-and-baseline-contract.md)  
**Status:** Approved (2026-10-30, Menno) — derived from Accepted ADR-025, BRD-025 and FDD-025 (Approved 2026-10-30); adjudicated via `approve-user-stories` (robust utility 0.735, episode `d33834f1-6ff5-4100-a08f-d2c2db66b0fb`).

Four stories. Each rule sits in one story (LL-012). Contract tests: `tests/test_scope_measure.py` (25.1), `tests/test_scope_sections.py` (25.2), `tests/test_scope_advice_policy.py` (25.3), `tests/test_scope_advice_reward.py` (25.4). FDD-025 §5 item 1 confirmed 2026-10-30 (one task id, four kinds, bandit scoped to the kind on each call). **Operating model (2026-10-30):** mandatory human `approve-subsidiary-plan` for baseline binding; `advise-scope-plan-decision` may recommend first (BRU-025-05–06, Scope plan §3.3). BRU-025-07 has no story: it is the text the plan author writes and the approver reads.

---

## Story 25.1 — Scope floors, caps, and exclusions

**Status:** Done (2026-10-30) — contract `tests/test_scope_measure.py` green  
**As** a governance reviewer,  
**I want** a Scope plan measured with the Scope floors, caps, and out-of-scope minimum,  
**so that** a plan that would pass the universal lint still shows a Scope gap, and every other plan keeps today's numbers.

### Acceptance Criteria

- **$AC_0$ (Profile):** `scope_measure("scope-management", "pmp_section")` is floor 180, cap 750, minimum 2 items. `full_plan` is 700, 4,500, and 4. `not_applicable` and any other `plan_id` return `None`.
- **$AC_1$ (Boundaries):** For a Scope `pmp_section`, word counts 179, 180, 750, and 751 produce below-floor, no length finding, no length finding, and `EXCEEDS_SECTION_CAP`. For a Scope `full_plan`, 699, 700, 4,500, and 4,501 produce below-floor, none, none, and `EXCEEDS_PLAN_CAP`. All four length findings are Tier C.
- **$AC_2$ (Other plans):** The same four `pmp_section` lengths on `schedule-management` follow the universal 150 and 800. 751 words is not over cap. 179 words is not under floor.
- **$AC_3$ (Items):** A Scope section with one real bullet and one `TBD` bullet raises `MISSING_BOUNDARY_DEF`. Two real bullets do not. A bullet `N/A for mobile clients` counts as real. A `None:` line of at least 10 tokens satisfies the boundary with zero bullets. The same one-bullet body on another plan does not raise the boundary finding.
- **$AC_4$ (Cannot relax):** A caller `min_floor_words` below 180 leaves 180 in force. A caller `min_out_of_scope_items` below 2 leaves 2 in force. A caller value above the profile raises the bar. `max_cap_words` above 800 leaves the universal cap in force for a non-Scope plan.
- **$AC_5$ (Purity):** `scope.py` imports no storage module and adds no package to `pyproject.toml`.

---

## Story 25.2 — WBS and Definition of Done

**Status:** Done (2026-10-30) — contract `tests/test_scope_sections.py` green  
**As** a governance reviewer,  
**I want** Section 2 of a Scope plan to state the breakdown rule and the Definition of Done,  
**so that** a plan cannot pass on word count alone while saying nothing about how work is decomposed or accepted.

### Acceptance Criteria

- **$AC_0$ (Both routes):** A Scope body whose Section 2 lacks a WBS phrase produces one Tier B `MISSING_REQUIRED_SECTION` whose message says the WBS rules are missing. The same for a missing Definition of Done or `DoD`. Both phrases present produce neither finding.
- **$AC_1$ (Embedded hierarchy):** A `pmp_section` whose Section 2 names only one of phase, epic, story, commit, or work package produces `WBS hierarchy is missing`. Naming two of them, or one line that links two with `→` or `->`, produces no hierarchy finding.
- **$AC_2$ (Full dictionary):** A `full_plan` missing any of phase, epic, story, or commit-or-work-package produces one finding naming the missing labels. `user story` counts as story. Missing any of `acceptance criteria`, `owner`, or `parent` produces one finding naming the missing fields. All of them present produce no dictionary finding.
- **$AC_3$ (No double finding):** A body with no Section 2 heading produces the existing heading finding only, and `check_scope_sections` adds nothing. A non-Scope plan and a `not_applicable` Scope plan receive no Section 2 Scope finding.
- **$AC_4$ (Order):** On a Scope plan that fails headings, floor, and Section 2 together, `lint_plan` returns heading findings, then the floor finding, then the Section 2 findings.

---

## Story 25.3 — The idle Scope advisory policy

**Status:** Ready  
**As** a maintainer,  
**I want** `advise-scope-plan-decision` declared as its own low-authority policy with equal logits and no episodes,  
**so that** a later recommendation has a fixed task id and cannot be trained as if it were the approval gate.

### Acceptance Criteria

- **$AC_0$ (Identity):** `baseline_snapshot()` has task id `advise-scope-plan-decision`, `decision_authority` `low`, and `requires_human_approval` false. Every action in the confirmed kind table has logit 0.0. No other action is present.
- **$AC_1$ (Idle):** Constructing the snapshot creates no episode and writes nothing. A test double of the store receives no call.
- **$AC_2$ (Separate task):** The task id differs from `approve-subsidiary-plan`. A fixture episode whose task id is the gate id is not a training input of this policy.
- **$AC_3$ (No prior):** The snapshot logits are all 0.0 and carry no prior copied from another plan's policy.
- **$AC_4$ (No selection episode):** The constructor does not build an ADR-024 methodology-selection episode.

---

## Story 25.4 — Record the recommendation, then show it

**Status:** Ready — depends on Story 25.3  
**As** a maintainer reviewing a Scope recommendation,  
**I want** the recommendation stored with its time before I see it, and left unchanged after I follow or override it,  
**so that** the learner's evidence is the gap between its advice and my decision.

### Acceptance Criteria

- **$AC_0$ (Kind bounds the draw):** For each confirmed kind, the returned `action_id` is one of that kind's actions. An unknown kind raises `ValueError`.
- **$AC_1$ (Immutable):** Two calls with the same `recommendation_id` return the same `action_id` and the same `recommended_at`, even if the snapshot logits changed between the calls.
- **$AC_2$ (Withhold):** `min_shown_decisions is None` yields `visible=False`. The same for a count below a set minimum. A count equal to the minimum yields `visible=True`. A minimum of 0 or less raises `ValueError`.
- **$AC_3$ (Reward):** `advice_reward(True)` is 1.0 and `advice_reward(False)` is −1.0. The credited action is the stored recommendation action. The function has no parameter for `approve_plan`, `reject_plan`, or `request_revision_before_decision`.
- **$AC_4$ (No new record):** `scope_advice.py` imports no storage module. `ScopeRecommendation` is a frozen dataclass, not a `LearningStore` record type.

---

## Out of Scope for this epic

- Rewriting universal floors or caps in `standards.py`.
- Staleness, approval, and formalization (Epic 13).
- Extracting a WBS from User Story files.
- Judging testability, Charter traceability, or a traceability matrix in the linter.
- Training on synthetic episodes, a shared prior, or pairwise WBS ranking.
- Writing the ADR-024 selection episode. That is a human record made when the policy is declared.
