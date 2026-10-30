# Epic 26: Schedule Management Plan Standard and Baseline Contract

**Source ADR:** [ADR-026](../adr/ADR-026-schedule-management-plan-standard-and-baseline-contract.md) — Accepted (2026-10-29, Menno), episode `8be53179-eb4e-4f1c-b71d-0efa79e0876d`  
**Source BRD/FDD:** [BRD-026](../project-docs/Business-Requirements/BRD-026-schedule-management-plan-standard-and-baseline-contract.md) / [FDD-026](../project-docs/Functional-Design/FDD-026-schedule-management-plan-standard-and-baseline-contract.md)  
**Status:** Approved (2026-10-30, Menno) — derived from Accepted ADR-026, BRD-026 and FDD-026 (Approved 2026-10-30); adjudicated via `approve-user-stories` (robust utility 0.735, episode `d95c487e-8fc2-40fe-96ce-daf338389be3`).

Four stories. Each rule sits in one story (LL-012). Contract tests: `tests/test_schedule_measure.py` (26.1), `tests/test_schedule_sections.py` (26.2), `tests/test_schedule_advice_policy.py` (26.3), `tests/test_schedule_advice_reward.py` (26.4). Story 26.1 waits on the shared lint arguments in FDD-026 §3.2. Stories 26.3 and 26.4 wait until FDD-026 §5 item 1 is confirmed. BRU-026-07 has no story: it is the text the plan author writes and the approver reads.

---

## Story 26.1 — Schedule floors, caps, and exclusions

**Status:** Draft — blocked on the `max_cap_words` and `exclude_placeholders` arguments of FDD-026 §3.2  
**As** a governance reviewer,  
**I want** a Schedule plan measured with the Schedule floors, caps, and out-of-scope minimum,  
**so that** a plan that would pass the universal lint still shows a Schedule gap, and every other plan keeps its own numbers.

### Acceptance Criteria

- **$AC_0$ (Profile):** `schedule_measure("schedule-management", "pmp_section")` is floor 180, cap 750, minimum 2 items. `full_plan` is 700, 4,500, and 4. `not_applicable`, `scope-management`, and `cost-management` return `None`.
- **$AC_1$ (Boundaries):** For a Schedule `pmp_section`, word counts 179, 180, 750, and 751 produce below-floor, no length finding, no length finding, and `EXCEEDS_SECTION_CAP`. For a Schedule `full_plan`, 699, 700, 4,500, and 4,501 produce below-floor, none, none, and `EXCEEDS_PLAN_CAP`. All four length findings are Tier C.
- **$AC_2$ (Other plans):** The same four `pmp_section` lengths on `cost-management` follow the universal 150 and 800. 751 words is not over cap. 179 words is not under floor. A `scope-management` body is not given a Schedule finding by this profile.
- **$AC_3$ (Items):** A Schedule section with one real bullet and one `TBD` bullet raises `MISSING_BOUNDARY_DEF`. Two real bullets do not. A bullet `N/A for vendor delivery dates` counts as real. A `None:` line of at least 10 tokens satisfies the boundary with zero bullets. The same one-bullet body on `cost-management` does not raise the boundary finding from this profile.
- **$AC_4$ (Cannot relax):** A caller `min_floor_words` below 180 leaves 180 in force. A caller `min_out_of_scope_items` below 2 leaves 2 in force. A caller value above the profile raises the bar. `max_cap_words` above 800 leaves the universal cap in force for a non-Schedule plan.
- **$AC_5$ (Purity):** `schedule.py` imports no storage module and adds no package to `pyproject.toml`.

---

## Story 26.2 — Milestone register, timebox, and estimation basis

**Status:** Ready
**As** a governance reviewer,  
**I want** Section 2 of a Schedule plan to state the milestone register, the timebox model, and the estimation basis,  
**so that** a plan cannot pass on word count alone while saying nothing about what finishes, in what order, or how duration was estimated.

### Acceptance Criteria

- **$AC_0$ (Register):** A Schedule body whose Section 2 lacks `milestone` produces one Tier B `MISSING_REQUIRED_SECTION` whose message says the milestone register is missing. A register that never says `epic` produces `milestone register has no parent epic`. Both phrases present produce neither finding.
- **$AC_1$ (Full register):** A `full_plan` missing `exit condition` and `exit criteria` produces `milestone exit conditions are missing`. Missing `window`, `date range`, and `range` produces `milestone target windows are missing`. A `pmp_section` with milestone and epic, and without those phrases, produces neither finding.
- **$AC_2$ (Timebox):** Both routes produce `timebox model is missing` when Section 2 has neither `timebox` nor `time box`. A `full_plan` that has a timebox and has neither `predecessor`, `critical path`, nor a word beginning `sequenc` produces `sequencing predecessors are missing`. A `pmp_section` does not produce that finding.
- **$AC_3$ (Estimation):** Both routes produce `estimation basis is missing` when Section 2 has no word beginning `estimat`. A `full_plan` that names an estimate and lacks both a unit phrase (`unit`, `story point`, `point`, `day`, or `hour`) and `confidence` produces one `estimation basis is incomplete` finding naming both gaps. Missing only one of them names that gap. A `pmp_section` that names an estimate produces no unit or confidence finding.
- **$AC_4$ (No double finding):** A body with no Section 2 heading produces the existing heading finding only, and `check_schedule_sections` adds nothing. A non-Schedule plan and a `not_applicable` Schedule plan receive no Section 2 Schedule finding. The labels `M0.5` and `M5` are not required.
- **$AC_5$ (Order):** On a Schedule plan that fails headings, floor, and Section 2 together, `lint_plan` returns heading findings, then the floor finding, then the Section 2 findings.

---

## Story 26.3 — The idle Schedule advisory policy

**Status:** Draft — blocked on confirmation of FDD-026 §5 item 1  
**As** a maintainer,  
**I want** `advise-schedule-plan-decision` declared as its own low-authority policy with equal logits and no episodes,  
**so that** a later recommendation has a fixed task id and cannot be trained as if it were the approval gate or the Scope advisor.

### Acceptance Criteria

- **$AC_0$ (Identity):** `baseline_snapshot()` has task id `advise-schedule-plan-decision`, `decision_authority` `low`, and `requires_human_approval` false. Every action in the confirmed kind table has logit 0.0. No other action is present.
- **$AC_1$ (Idle):** Constructing the snapshot creates no episode and writes nothing. A test double of the store receives no call.
- **$AC_2$ (Separate tasks):** The task id differs from `approve-subsidiary-plan` and from `advise-scope-plan-decision`. A fixture episode whose task id is either of those is not a training input of this policy.
- **$AC_3$ (No prior):** The snapshot logits are all 0.0 and carry no prior copied from another plan's policy.
- **$AC_4$ (No selection episode):** The constructor does not build an ADR-024 methodology-selection episode.

---

## Story 26.4 — Record the recommendation, then show it

**Status:** Draft — blocked on Story 26.3  
**As** a maintainer reviewing a Schedule recommendation,  
**I want** the recommendation stored with its time before I see it, and left unchanged after I follow or override it,  
**so that** the learner's evidence is the gap between its advice and my decision.

### Acceptance Criteria

- **$AC_0$ (Kind bounds the draw):** For each confirmed kind, the returned `action_id` is one of that kind's actions. An unknown kind raises `ValueError`.
- **$AC_1$ (Immutable):** Two calls with the same `recommendation_id` return the same `action_id` and the same `recommended_at`, even if the snapshot logits changed between the calls.
- **$AC_2$ (Withhold):** `min_shown_decisions is None` yields `visible=False`. The same for a count below a set minimum. A count equal to the minimum yields `visible=True`. A minimum of 0 or less raises `ValueError`.
- **$AC_3$ (Reward):** `advice_reward(True)` is 1.0 and `advice_reward(False)` is −1.0. The credited action is the stored recommendation action. The function has no parameter for `approve_plan`, `reject_plan`, or `request_revision_before_decision`.
- **$AC_4$ (No new record):** `schedule_advice.py` imports no storage module. `ScheduleRecommendation` is a frozen dataclass, not a `LearningStore` record type. A Scope recommendation id is not returned as a Schedule recommendation.

---

## Out of Scope for this epic

- Rewriting universal floors or caps in `standards.py`.
- Staleness, approval, formalization, and `PlanApprovalRecord.parent_hashes` (Epic 13).
- The Scope profile and the Scope advisory policy, beyond sharing the lint-option signature.
- Joining milestone rows to epics in the Scope plan, or judging exit conditions.
- Reading velocity from `LearningStore`.
- Training on synthetic episodes, a shared prior, contextual softmax, or multi-stage credit assignment.
- Writing the ADR-024 selection episode. That is a human record made when the policy is declared.
