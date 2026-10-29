# Epic 32: Communications Management Plan Standard

**Source ADR:** [ADR-032](../adr/ADR-032-communications-management-plan-standard.md) — Proposed (2026-10-26)  
**Source BRD/FDD:** [BRD-032](../project-docs/Business-Requirements/BRD-032-communications-management-plan-standard.md) / [FDD-032](../project-docs/Functional-Design/FDD-032-communications-management-plan-standard.md)  
**Status:** Draft (2026-10-29) — derived from Proposed ADR-032, BRD-032 and FDD-032; not yet adjudicated via `approve-user-stories`. Implementation waits until ADR-032 is accepted.

Four stories. Each rule sits in one story (LL-012). Contract tests: `tests/test_communications_measure.py` (32.1), `tests/test_communications_sections.py` (32.2), `tests/test_communications_advice_policy.py` (32.3), `tests/test_communications_advice_reward.py` (32.4). Stories 32.3 and 32.4 wait until FDD-032 §5 items 1 and 2 are confirmed. BRU-032-07 has no story: it is the text the plan author writes and the approver reads.

---

## Story 32.1 — Communications lengths and the full-plan exclusion minimum

**Status:** Draft — blocked on acceptance of ADR-032  
**As** a governance reviewer,  
**I want** a Communications plan measured at the ADR-012 floors and caps, with two out-of-scope items on a full plan,  
**so that** Tier 3 does not inherit a higher floor, and a full plan still states more than one exclusion.

### Acceptance Criteria

- **$AC_0$ (Profile):** `communications_measure("communications-management", "pmp_section")` is floor 150, cap 800, minimum 1 item. `full_plan` is 600, 5,000, and 2. `not_applicable`, `stakeholder-engagement`, and `scope-management` return `None`.
- **$AC_1$ (Section lengths):** For a Communications `pmp_section`, word counts 149, 150, 159, 800, and 801 produce below-floor, no length finding, no length finding, no length finding, and `EXCEEDS_SECTION_CAP`. All length findings are Tier C. The call does not pass `min_floor_words` or `max_cap_words`.
- **$AC_2$ (Plan lengths):** For a Communications `full_plan`, word counts 599, 600, 5,000, and 5,001 produce below-floor, no length finding, no length finding, and `EXCEEDS_PLAN_CAP`.
- **$AC_3$ (Other plans):** `check_communications_sections` returns `[]` for a `stakeholder-engagement` body. `lint_plan` on that plan does not append a Communications matrix, recording-rule, or escalation finding. Its floor, when one is produced, is the universal floor.
- **$AC_4$ (Items):** A Communications `pmp_section` with one bullet does not raise `MISSING_BOUNDARY_DEF`, including when that bullet is only `TBD`. A Communications `full_plan` with one bullet does. Two bullets do not. A `None:` line of at least 10 tokens satisfies the boundary with zero bullets. A caller minimum below 2 leaves 2 in force for `full_plan`.
- **$AC_5$ (Omission and graph):** `lint_plan` on a `not_applicable` Communications plan adds no Communications content finding and no `OMISSION_OF_BASE_PLAN` finding. `PLAN_DAG["communications-management"]` is `("scope-management",)` and does not contain `stakeholder-engagement`. No `PLAN_DAG` value contains `communications-management`.
- **$AC_6$ (Purity):** `communications.py` imports no storage module and adds no package to `pyproject.toml`. It does not read `Stakeholder-Register.md`.

---

## Story 32.2 — Matrix, decision-recording rule, and escalation path

**Status:** Draft — blocked on acceptance of ADR-032  
**As** a governance reviewer,  
**I want** a Communications plan to name each flow's audience, cadence, and owner, to state where a decision is recorded, and to name who an urgent issue reaches,  
**so that** a plan cannot pass on word count alone while leaving the flows, the record, or the escalation unnamed.

### Acceptance Criteria

- **$AC_0$ (Matrix):** A Communications body whose Section 2 has neither `matrix` nor `flow` produces one Tier B `MISSING_REQUIRED_SECTION` whose message says the communication matrix is missing. Those words only in Section 1 still produce that finding.
- **$AC_1$ (Key fields):** A `pmp_section` whose Section 2 has `matrix` or `flow`, and lacks `audience`, a cadence word (`cadence` or `trigger`), or `owner`, produces one `communication matrix is incomplete` finding naming each gap. All three present produce no matrix finding. The missing finding and the incomplete finding do not both fire.
- **$AC_2$ (Full fields):** A `full_plan` whose Section 2 has `matrix` or `flow`, and lacks `audience`, `information`, `purpose`, `channel`, a cadence word, or `owner`, produces one incomplete finding naming each gap. A `pmp_section` does not require information, purpose, or channel.
- **$AC_3$ (Recording rule):** Both routes produce `decision recording rule is missing` when Section 2 has no `record`. A `full_plan` that has `record` and has none of `episode`, `metadata`, `artifact`, `version-controlled`, and `version controlled` produces `decision recording rule is incomplete`, naming `record location`. A `pmp_section` that has `record` produces no location finding. The word `record` only in Section 3 still produces the missing finding.
- **$AC_4$ (Escalation):** Both routes produce `escalation path is missing` when Section 2 has no `escalat`. Both routes that have `escalat` and have none of `sponsor`, `approver`, `decision-maker`, and `decision maker` produce `escalation path is incomplete`, naming the target. A `full_plan` that has `escalat` and a target, and lacks `sequence` and `step`, or lacks `time limit`, `time-limit`, `within`, and `hour`, produces one incomplete finding naming each gap. The bare word `day` does not satisfy the time limit. A `pmp_section` that has `escalat` and a target produces no sequence or time-limit finding.
- **$AC_5$ (No double finding):** A body with no Section 2 heading produces the existing heading finding and no matrix, recording-rule, or escalation finding. A non-Communications plan and a `not_applicable` Communications plan receive no Communications section finding. No matrix row is parsed.
- **$AC_6$ (Order):** On a Communications plan that fails headings, floor, and the matrix together, `lint_plan` returns heading findings, then the floor finding, then the Communications section findings. When the matrix, the recording rule, and the escalation path are all missing, the findings are matrix, then recording rule, then escalation path.

---

## Story 32.3 — The idle Communications advisory policy

**Status:** Draft — blocked on confirmation of FDD-032 §5 items 1 and 2, and on acceptance of ADR-032  
**As** a maintainer,  
**I want** `advise-communications-plan-decision` declared as its own low-authority policy with one logit map,  
**so that** a later recommendation has a fixed task id and a recorded deciding role, and cannot be trained as the approval gate or another plan advisor.

### Acceptance Criteria

- **$AC_0$ (Identity):** `baseline_snapshot()` has task id `advise-communications-plan-decision`, `decision_authority` `low`, and `requires_human_approval` false. `PolicySnapshot.logits` has every action in the confirmed kind table at logit 0.0 and no other action. The snapshot has no department map and no per-role logit map.
- **$AC_1$ (Idle):** Constructing the snapshot creates no episode and writes nothing. A test double of the store receives no call.
- **$AC_2$ (Separate tasks):** The task id differs from `approve-subsidiary-plan`, `advise-scope-plan-decision`, `advise-schedule-plan-decision`, `advise-cost-plan-decision`, `advise-risk-plan-decision`, `advise-quality-plan-decision`, `advise-resource-plan-decision`, and `advise-stakeholder-plan-decision`. A fixture episode whose task id is any of those is not a training input of this policy.
- **$AC_3$ (No prior):** The snapshot logits are all 0.0 and carry no prior copied from another plan's policy.
- **$AC_4$ (No selection episode):** The constructor does not build an ADR-024 methodology-selection episode.

---

## Story 32.4 — Record the recommendation, then show it

**Status:** Draft — blocked on Story 32.3  
**As** a maintainer reviewing a Communications recommendation,  
**I want** the recommendation stored with its deciding role and its time before I see it, and left unchanged after I follow or override it,  
**so that** the learner's evidence is the gap between its advice and my decision, with the role that made the pair kept on the record.

### Acceptance Criteria

- **$AC_0$ (Kind bounds the draw):** For each confirmed kind and each confirmed role, the returned `action_id` is one of that kind's actions and `deciding_role` is the role that was passed. The draw reads `PolicySnapshot.logits`. An unknown kind or an unknown role raises `ValueError`.
- **$AC_1$ (Immutable):** Two calls with the same `recommendation_id` return the same `action_id`, the same `deciding_role`, and the same `recommended_at`, even if the second call passes the other role or the logits changed.
- **$AC_2$ (Withhold):** `min_shown_decisions is None` yields `visible=False`. The same for a count below a set minimum. A count equal to the minimum yields `visible=True`. A minimum of 0 or less raises `ValueError`.
- **$AC_3$ (Reward):** `advice_reward(True)` is 1.0 and `advice_reward(False)` is −1.0. The credited action is the stored recommendation action on the single logit map. The stored `deciding_role` is unchanged. The function has no parameter for a gate action and no parameter that selects a second map.
- **$AC_4$ (No new record):** `communications_advice.py` imports no storage module. `CommunicationsRecommendation` is a frozen dataclass, not a `LearningStore` record type. A recommendation id from another plan advisor is not returned as a Communications recommendation.

---

## Out of Scope for this epic

- Raising the Communications floor or tightening the Communications cap.
- Changing `PLAN_DAG`.
- Staleness, approval, formalization, and `OMISSION_OF_BASE_PLAN` (Epics 11 and 13).
- The other plan profiles and their advisory policies.
- Resolving audience names to Stakeholder Register rows, or opening `Stakeholder-Register.md`.
- Generating a status report, or writing into the Stakeholder Engagement plan or the Schedule.
- A second logit map for the deciding role.
- Training on synthetic episodes or a shared prior.
- Writing the ADR-024 selection episode. That is a human record made when the policy is declared.
