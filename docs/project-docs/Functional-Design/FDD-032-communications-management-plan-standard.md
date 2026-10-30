# FDD-032: Communications Management Plan Standard

**Source ADR:** [ADR-032](../../adr/ADR-032-communications-management-plan-standard.md) — Accepted (2026-10-29, Menno), episode `5ee60bbe-b680-4c14-887c-aae515e1379c`  
**Source BRD:** [BRD-032](../Business-Requirements/BRD-032-communications-management-plan-standard.md)  
**Status:** Draft (2026-10-29) — derived from Accepted ADR-032 and BRD-032; not yet adjudicated via `approve-fdd`. §5 interpretations are not confirmed.

---

## 1. Architecture and Component Placement

1. **Profile and section checks** live in `src/agent_learning/pmbok/communications.py`. `lint_plan` in `src/agent_learning/pmbok/lint.py` consults that profile when `plan_id` is `communications-management`. The universal constants in `standards.py` stay the ADR-012 baseline. This profile does not change them.
2. **Advisory policy** lives in `src/agent_learning/policy/communications_advice.py`. It builds a `PolicySnapshot` for the existing `SoftmaxPolicy` and a recommendation record. It does not import `LearningStore`. The caller writes any `Episode`.
3. **Purity:** standard library plus existing `agent_learning` types (`PolicySnapshot`, `SoftmaxPolicy`). No file I/O, no network, no sleep, no new record type. The checks do not open the Charter, the Scope plan, the Stakeholder Engagement plan, or `Stakeholder-Register.md`.
4. **Reuse:** `count_words`, `check_content`, `TOKEN`, `HEADINGS`, `next_step`, `omission_flags`, and `PLAN_DAG` stay as they are. For a Communications `full_plan`, `lint_plan` passes `min_out_of_scope_items=2`. It does not pass `min_floor_words`, `max_cap_words`, or `exclude_placeholders`. A `pmp_section` keeps the universal item minimum of 1. A Communications call does not change the findings of any other `plan_id`.
5. **Already satisfied elsewhere:** `PLAN_DAG["communications-management"]` is `("scope-management",)`. That tuple does not contain `stakeholder-engagement`. No row lists `communications-management` as an ancestor. Epic 13 owns staleness. This design adds no edge.

---

## 2. Data Contract

```python
@dataclass(frozen=True)
class CommunicationsMeasure:
    floor: int
    cap: int
    min_out_of_scope_items: int

# Lengths equal the ADR-012 baseline. The full_plan item minimum is the raised number.
COMMUNICATIONS_MEASURES: Mapping[str, CommunicationsMeasure] = MappingProxyType({
    "pmp_section": CommunicationsMeasure(floor=150, cap=800, min_out_of_scope_items=1),
    "full_plan": CommunicationsMeasure(floor=600, cap=5000, min_out_of_scope_items=2),
})

COMMUNICATIONS_PLAN_ID = "communications-management"
ADVICE_TASK_ID = "advise-communications-plan-decision"

# Closed set from ADR-032 §4.4.1. Recorded on the pair. Not a second logit map.
DECIDING_ROLES: tuple[str, ...] = ("internal_communications", "marketing")

# Full matrix fields from ADR-032 §4.2 and §4.3.
MATRIX_FIELDS: tuple[str, ...] = (
    "audience",
    "information",
    "purpose",
    "channel",
    "cadence or trigger",
    "owner",
)

DECISION_KINDS: Mapping[str, tuple[str, ...]] = MappingProxyType({
    "route": ("recommend_full_plan", "recommend_pmp_section", "recommend_not_applicable"),
    "paragraph_sufficiency": ("recommend_sufficient", "recommend_insufficient"),
    "graduation": ("recommend_keep_section", "recommend_graduate"),
    "flagged_deviation": ("recommend_accept_deviation", "recommend_refuse_deviation"),
})

@dataclass(frozen=True)
class CommunicationsRecommendation:
    recommendation_id: str
    task_id: str                 # always ADVICE_TASK_ID
    decision_kind: str
    action_id: str
    deciding_role: str           # one of DECIDING_ROLES
    recommended_at: str          # ISO 8601 UTC
    visible: bool                # False until the profile minimum is met
    logits: Mapping[str, float]  # the single map that produced the action
```

`min_shown_decisions` is an `int | None` on the policy profile. `None` means withhold. A set value is a positive integer chosen by the maintainer.

The kind table is the same working list as ADR-032 §4.4.1. `PolicySnapshot.logits` holds the one map. There is no `metadata["department_logits"]` and no per-role map. The deciding role is stored on the recommendation. It does not select which logits are read. The plan `owner_role` stays Project Manager and is not an action.

---

## 3. Behavior

### 3.1 `communications_measure(plan_id, route) -> CommunicationsMeasure | None` (BRU-032-01)

Returns the row when `plan_id == "communications-management"` and `route` is `pmp_section` or `full_plan`. Returns `None` otherwise, including `not_applicable` and every other plan.

### 3.2 Options `lint_plan` passes (BRU-032-01, BRU-032-02)

When `communications_measure` returns a row, `lint_plan` calls `check_content` with:

- `min_floor_words` left unset, so the floor stays `FLOORS[route]`
- `max_cap_words` left unset, so the cap stays `CAPS[route]`
- `exclude_placeholders` left unset, so a `TBD` bullet still counts
- for `full_plan`, effective item minimum = `max(2, caller min_out_of_scope_items or 0)`
- for `pmp_section`, the universal item minimum of 1, raised only when the caller passes a higher value

A Communications `pmp_section` of 159 words is not under floor. A count of 149 is. A count of 801 or 5,001 is over cap. A count of 800 or 5,000 is not.

`not_applicable` skips content checks. This profile does not call `omission_flags` and does not emit `OMISSION_OF_BASE_PLAN`.

### 3.3 `lint_plan` applies the profile (BRU-032-01, BRU-032-04)

After the content checks, `lint_plan` appends `check_communications_sections`. Finding order is parse, metadata, headings, floor, cap, boundary, then the Communications section findings of §3.4. `next_step` is unchanged.

When `communications_measure` returns `None`, this profile adds nothing. A floor finding on another plan, when one is produced, is that plan's universal floor.

### 3.4 `check_communications_sections(body, route) -> list[LintFlag]` (BRU-032-03)

Section 2 is the text from heading 2 to heading 3. The heading regexes are the ADR-012 headings. If heading 2 is absent, this function returns nothing, because the missing-heading finding already exists. Findings are Tier B `MISSING_REQUIRED_SECTION`, in the order below. Matching is case-insensitive substring presence on Section 2. The check does not parse a matrix row, does not open a companion file, and does not read Section 1 or Section 3.

Communication matrix:

1. No match for `matrix` and no match for `flow`. Message: `communication matrix is missing`.
2. When step 1 matched, one finding naming each missing field. A `pmp_section` requires audience (`audience`), cadence or trigger (`cadence` or `trigger`), and owner (`owner`). A `full_plan` also requires information (`information`), purpose (`purpose`), and channel (`channel`). Message: `communication matrix is incomplete`. A present matrix with every required field produces no matrix finding. Steps 1 and 2 do not both fire.

Decision recording rule:

3. No match for `record`. Message: `decision recording rule is missing`.
4. For `full_plan`, and only when step 3 matched: if none of `episode`, `metadata`, `artifact`, `version-controlled`, and `version controlled` match, message `decision recording rule is incomplete`, naming `record location`. A `pmp_section` that has `record` produces no location finding. Steps 3 and 4 do not both fire.

Escalation path:

5. No match for `escalat`. Message: `escalation path is missing`.
6. When step 5 matched, one finding naming each missing part. Both routes require a target: `sponsor`, `approver`, `decision-maker`, or `decision maker`. A `full_plan` also requires a sequence (`sequence` or `step`) and a time limit (`time limit`, `time-limit`, `within`, or `hour`). The bare word `day` does not satisfy the time limit. Message: `escalation path is incomplete`. Steps 5 and 6 do not both fire.

`route == "not_applicable"` returns `[]`. Words in Section 1 or Section 3 do not satisfy the check.

### 3.5 `baseline_snapshot() -> PolicySnapshot` (BRU-032-05)

`task_id` is `advise-communications-plan-decision`. `metadata["decision_authority"]` is `low`. `metadata["requires_human_approval"]` is `false` on this policy. `PolicySnapshot.logits` has every action in §2 `DECISION_KINDS` at logit `0.0`, and no other action. The snapshot has no `department_logits` and no per-role logit map. It carries no episodes. Calling this function does not write the store and does not create an ADR-024 selection episode. It does not read or copy another plan's advisory snapshot.

### 3.6 `recommend(..., deciding_role) -> CommunicationsRecommendation` (BRU-032-06)

The other arguments match the Scope, Schedule, Cost, Risk, Quality, and Stakeholder advisors: `snapshot`, `decision_kind`, `recommendation_id`, `recommended_at`, `recorded_decisions`, and `min_shown_decisions`.

`deciding_role` must be `internal_communications` or `marketing`. `decision_kind` must be one of the four keys. The legal actions are that kind's tuple. `SoftmaxPolicy` chooses among `PolicySnapshot.logits` for those actions only. The kind restricts the action set. It is not a learned context feature. The role is stored on the recommendation. It is not a learned feature and it does not select a logit map.

If `recommendation_id` was returned before, return that same record, including `action_id`, `deciding_role`, and `recommended_at`. Do not draw again.

`visible` is `True` only when `min_shown_decisions` is an int and `recorded_decisions >= min_shown_decisions`. `min_shown_decisions is None` yields `visible=False`.

A recommendation id from another plan advisor is not a Communications recommendation id.

### 3.7 `advice_reward(followed: bool) -> float` (BRU-032-06)

`True` returns `1.0`. `False` returns `-1.0`. The action credited is the stored `action_id` on the single logit map. The stored `deciding_role` is left unchanged. Gate actions are not an input.

---

## 4. Error Handling

| Situation | Behavior |
|---|---|
| `plan_id` other than `communications-management` | This profile adds no finding and does not change that plan's floor, cap, or item count |
| Communications route `not_applicable` | Content checks skipped. This profile emits no `OMISSION_OF_BASE_PLAN` |
| Communications `pmp_section` of 159 words | No floor finding |
| Communications `pmp_section` of 149 words | `BELOW_STANDARD_FLOOR` from the universal floor of 150 |
| Matrix, record, or escalation words only in Section 1 or Section 3 | Section 2 still raises the matching missing finding |
| Unknown `decision_kind` | `ValueError` naming the kind |
| Unknown `deciding_role` | `ValueError` naming the role |
| `min_shown_decisions` of 0 or negative | `ValueError` |
| Same `recommendation_id` offered again, including with the other role | Original action, role, and timestamp returned |

---

## 5. Interpretations to Confirm

These are not verbatim in ADR-032. Stories 32.3 and 32.4 wait on items 1 and 2.

1. **One policy, four kinds.** The action set is the table in §2. A call passes one kind and the bandit chooses only inside that kind. The four kinds are the working list in ADR-032 §4.4.1. Confirming this set for Communications confirms the same ids for the other plan advisors.
2. **The deciding role is recorded. The logits stay one map.** The role ids are `internal_communications` and `marketing`. ADR-032 §4.4.1 says the owner is organization-dependent and that the deciding role is recorded with each pair. It does not say the logits are kept apart by role. The role is stored on the recommendation and is immutable with it. It does not select a second map, and it is not a contextual feature. An unknown role raises `ValueError`. There is no third role id for the Project Manager. The plan `owner_role` stays Project Manager.
3. **The Tier 1 placeholder filter stays off.** A bullet whose text is only `TBD` counts toward the Communications minimum. ADR-032 does not cite the ADR-025 placeholder sentence.
4. **Floors and caps are not passed in.** Recording 150, 600, 800, and 5,000 on `CommunicationsMeasure` documents the ADR-032 table. The call leaves `min_floor_words` and `max_cap_words` unset. The only raised number passed into the lint is the full-plan item minimum of 2.
5. **All three structural checks are read from Section 2.** Presence of the matrix is the word `matrix` or the word `flow`. A `pmp_section` then requires audience, cadence or trigger, and owner. A `full_plan` also requires information, purpose, and channel. The recording rule is the substring `record`. A `full_plan` also requires one location phrase: `episode`, `metadata`, `artifact`, `version-controlled`, or `version controlled`. The escalation path is the substring `escalat`. Both routes then require a target (`sponsor`, `approver`, `decision-maker`, or `decision maker`). A `full_plan` also requires `sequence` or `step`, and a time-limit phrase (`time limit`, `time-limit`, `within`, or `hour`). The bare word `day` does not satisfy the time limit. The lint does not parse matrix rows.
6. **Invariants 2 and 3, beyond the recording-location phrase and the cadence words, stay review text.** Audience names resolving to the Stakeholder Register, Charter and Scope traceability, status-report fields, confidentiality classes, approval of external messages, and the rule that this plan does not write into another plan stay with the human reviewer (BRU-032-07). The lint does not open `Stakeholder-Register.md`.
7. **An unset show-minimum withholds every recommendation.** The ADR leaves the number unset on purpose.
8. **Follow is +1 and override is −1** on the recommendation action of the single logit map. That matches the existing reward interval of −1 to 1.

## 6. Out of Scope

Same boundary as BRD-032. `communications.py` and `communications_advice.py` do not import storage. They do not register the policy in a running store. They do not emit the ADR-024 selection episode. They do not add a `PLAN_DAG` edge, they do not open a companion register file, and they do not write into another plan.
