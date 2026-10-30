# FDD-030: Resource Management Plan Standard

**Source ADR:** [ADR-030](../../adr/ADR-030-resource-management-plan-standard.md) — Accepted (2026-10-29, Menno), episode `de095357-d927-4408-8311-181e158a2abf`  
**Source BRD:** [BRD-030](../Business-Requirements/BRD-030-resource-management-plan-standard.md)  
**Status:** Draft (2026-10-29) — derived from Accepted ADR-030 and BRD-030; not yet adjudicated via `approve-fdd`. §5 interpretations are not confirmed.

---

## 1. Architecture and Component Placement

1. **Profile and section checks** live in `src/agent_learning/pmbok/resource.py`. `lint_plan` in `src/agent_learning/pmbok/lint.py` consults that profile when `plan_id` is `resource-management`. The universal constants in `standards.py` stay the ADR-012 baseline. This profile does not change them.
2. **Advisory policy** lives in `src/agent_learning/policy/resource_advice.py`. It builds a `PolicySnapshot` for the existing `SoftmaxPolicy` and a recommendation record. It does not import `LearningStore`. The caller writes any `Episode`.
3. **Purity:** standard library plus existing `agent_learning` types (`PolicySnapshot`, `SoftmaxPolicy`). No file I/O, no network, no sleep, no new record type. The checks do not open the Charter, the Scope plan, the Schedule plan, or the Stakeholder Register.
4. **Reuse:** `count_words`, `check_content`, `TOKEN`, `HEADINGS`, `next_step`, `omission_flags`, and `PLAN_DAG` stay as they are. For a Resource `full_plan`, `lint_plan` passes `min_out_of_scope_items=2`. It does not pass `min_floor_words`, `max_cap_words`, or `exclude_placeholders`. A `pmp_section` keeps the universal item minimum of 1. A Resource call does not change the findings of any other `plan_id`.
5. **Already satisfied elsewhere:** `PLAN_DAG["resource-management"]` is `("scope-management", "schedule-management")`. `PLAN_DAG["cost-management"]` does not include `resource-management`. No row lists `resource-management` as an ancestor. Epic 13 owns staleness. This design adds no edge.

---

## 2. Data Contract

```python
@dataclass(frozen=True)
class ResourceMeasure:
    floor: int
    cap: int
    min_out_of_scope_items: int

# These equal the ADR-012 baseline, except the full_plan item minimum.
RESOURCE_MEASURES: Mapping[str, ResourceMeasure] = MappingProxyType({
    "pmp_section": ResourceMeasure(floor=150, cap=800, min_out_of_scope_items=1),
    "full_plan": ResourceMeasure(floor=600, cap=5000, min_out_of_scope_items=2),
})

RESOURCE_PLAN_ID = "resource-management"
ADVICE_TASK_ID = "advise-resource-plan-decision"
DEPARTMENTS: tuple[str, ...] = ("procurement", "hr")

DECISION_KINDS: Mapping[str, tuple[str, ...]] = MappingProxyType({
    "route": ("recommend_full_plan", "recommend_pmp_section", "recommend_not_applicable"),
    "paragraph_sufficiency": ("recommend_sufficient", "recommend_insufficient"),
    "graduation": ("recommend_keep_section", "recommend_graduate"),
    "flagged_deviation": ("recommend_accept_deviation", "recommend_refuse_deviation"),
})

@dataclass(frozen=True)
class ResourceRecommendation:
    recommendation_id: str
    task_id: str                 # always ADVICE_TASK_ID
    deciding_department: str     # one of DEPARTMENTS
    decision_kind: str
    action_id: str
    recommended_at: str          # ISO 8601 UTC
    visible: bool                # False until the profile minimum is met
    logits: Mapping[str, float]  # the department's logits that produced the action
```

`min_shown_decisions` is an `int | None` on the policy profile. `None` means withhold. A set value is a positive integer chosen by the maintainer.

The snapshot's `metadata["department_logits"]` is a map from each department to that department's action logits. `PolicySnapshot.logits` stays an empty map. The bandit reads the department map for the call. The kind table is the same working list as ADR-030 §4.4.1.

---

## 3. Behavior

### 3.1 `resource_measure(plan_id, route) -> ResourceMeasure | None` (BRU-030-01)

Returns the row when `plan_id == "resource-management"` and `route` is `pmp_section` or `full_plan`. Returns `None` otherwise, including `not_applicable` and every other plan.

### 3.2 Options `lint_plan` passes (BRU-030-01, BRU-030-02)

When `resource_measure` returns a row, `lint_plan` calls `check_content` with:

- `min_floor_words` left unset, so the floor stays `FLOORS[route]`
- `max_cap_words` left unset, so the cap stays `CAPS[route]`
- `exclude_placeholders` left unset, so a `TBD` bullet still counts
- for `full_plan`, effective item minimum = `max(2, caller min_out_of_scope_items or 0)`
- for `pmp_section`, the universal item minimum of 1, raised only when the caller passes a higher value

A Resource `pmp_section` of 159 words is not under floor. A count of 149 is. A count of 801 or 5,001 is over cap. A count of 800 or 5,000 is not.

`not_applicable` skips content checks. This profile does not call `omission_flags` and does not emit `OMISSION_OF_BASE_PLAN`.

### 3.3 `lint_plan` applies the profile (BRU-030-01, BRU-030-04)

After the content checks, `lint_plan` appends `check_resource_sections`. Finding order is parse, metadata, headings, floor, cap, boundary, then the Resource section findings of §3.4. `next_step` is unchanged.

When `resource_measure` returns `None`, this profile adds nothing.

### 3.4 `check_resource_sections(body, route) -> list[LintFlag]` (BRU-030-03)

Section 2 is the text from heading 2 to heading 3. The heading regexes are the ADR-012 headings. If heading 2 is absent, return `[]`, because the missing-heading finding already exists. Findings are Tier B `MISSING_REQUIRED_SECTION`, in the order below. Matching is case-insensitive. The check is phrase presence in the section. It does not parse a role row, and a word that satisfies one check can satisfy another.

Catalogue:

1. No match for `role`. Message: `role catalogue is missing`.
2. When step 1 matched, and `accountable` does not match: message `role catalogue has no accountable owner`.
3. For `full_plan`, and only when steps 1 and 2 produced no finding: one finding if `responsib` or `decision` is absent. Message: `role catalogue is incomplete`, naming each gap.

Agent accountability, still in Section 2:

4. When `agent` matches, and `accountable` or `human` does not: message `agent work has no accountable human`. When `agent` does not match, this finding is not produced.

Allocation:

5. No match for `capacity` or `allocat`. Message: `allocation and capacity are missing`.
6. For `full_plan`, and only when step 5 produced no finding: one finding if `allocat`, a timebox (`timebox` or `time box`), or a basis (`basis`) is absent. Message: `allocation and capacity are incomplete`, naming each gap.

Tooling:

7. No match for `asset`, `tooling`, `tool`, `licence`, `license`, or `environment`. Message: `tooling assets are missing`.
8. For `full_plan`, and only when step 7 produced no finding: one finding if `owner` or a lead time (`lead time` or `lead-time`) is absent. Message: `tooling assets are incomplete`, naming each gap.

`route == "not_applicable"` returns `[]`. A `pmp_section` is not checked for responsibilities, decision rights, per-timebox allocation, basis, owners of assets, or lead times.

### 3.5 `baseline_snapshot() -> PolicySnapshot` (BRU-030-05)

`task_id` is `advise-resource-plan-decision`. `metadata["decision_authority"]` is `low`. `metadata["requires_human_approval"]` is `false` on this policy. `metadata["department_logits"]` has both `procurement` and `hr`. Each map has every action in §2 `DECISION_KINDS` at logit `0.0`, and no other action. The two maps are equal and are not the same object. `PolicySnapshot.logits` is empty. The snapshot carries no episodes. Calling this function does not write the store and does not create an ADR-024 selection episode. It does not read or copy another plan's advisory snapshot.

### 3.6 `recommend(..., deciding_department) -> ResourceRecommendation` (BRU-030-06)

The other arguments match the other plan advisors: `snapshot`, `decision_kind`, `recommendation_id`, `recommended_at`, `recorded_decisions`, and `min_shown_decisions`.

`deciding_department` must be `procurement` or `hr`. `decision_kind` must be one of the four keys. `SoftmaxPolicy` chooses among that department's logits for that kind only. It does not read the other department's logits. The kind restricts the action set. It is not a learned context feature. The department is not a learned feature. It selects which logit map is used.

If `recommendation_id` was returned before, return that same record, including `action_id`, `deciding_department`, and `recommended_at`. Do not draw again.

`visible` is `True` only when `min_shown_decisions` is an int and `recorded_decisions >= min_shown_decisions`. `min_shown_decisions is None` yields `visible=False`.

### 3.7 `advice_reward(followed: bool) -> float` (BRU-030-06)

`True` returns `1.0`. `False` returns `-1.0`. The action credited is the stored `action_id` on the stored department's logit map. Applying the reward does not write the other department's map. Gate actions are not an input.

---

## 4. Error Handling

| Situation | Behavior |
|---|---|
| `plan_id` other than `resource-management` | This profile adds no finding and does not change that plan's floor, cap, or item count |
| Resource route `not_applicable` | Content checks skipped. This profile emits no `OMISSION_OF_BASE_PLAN` |
| Resource `pmp_section` of 159 words | No floor finding |
| Resource `pmp_section` of 149 words | `BELOW_STANDARD_FLOOR` from the universal floor of 150 |
| Unknown `deciding_department` | `ValueError` naming the department |
| Unknown `decision_kind` | `ValueError` naming the kind |
| `min_shown_decisions` of 0 or negative | `ValueError` |
| Same `recommendation_id` offered again, including with another department | Original action, department, and timestamp returned |
| `agent` absent from Section 2 | No agent-accountability finding |

---

## 5. Interpretations to Confirm

These are not verbatim in ADR-030. Stories 30.3 and 30.4 wait on items 1 and 2.

1. **One policy, four kinds.** The action set is the table in §2. A call passes one kind and the bandit chooses only inside that kind. The four kinds are the working list in ADR-030 §4.4.1. Confirming this set for Resource confirms the same ids for the other plan advisors.
2. **Two departments, one task.** The department ids are `procurement` and `hr`. Materials map to `procurement` and human resources map to `hr`. There is no third department for the Project Manager. Each department has its own logit map inside one snapshot. The department selects the map. It is not a contextual feature.
3. **The Tier 1 placeholder filter stays off.** A bullet whose text is only `TBD` counts toward the Resource minimum. ADR-030 does not cite the ADR-025 placeholder sentence.
4. **Floors and caps are not passed in.** Recording 150, 600, 800, and 5,000 on `ResourceMeasure` documents the ADR-030 table. The call leaves `min_floor_words` and `max_cap_words` unset, so Resource follows the ADR-012 constants. The only raised number passed into the lint is the full-plan item minimum of 2.
5. **Phrase presence is the structural check.** Accountable owner matches `accountable`, not the bare word `owner`. Agent accountability is required only when Section 2 says `agent`. Invariants 2 and 3, beyond the timebox word on a full plan, stay review text (BRU-030-07).
6. **An unset show-minimum withholds every recommendation.** The ADR leaves the number unset on purpose.
7. **Follow is +1 and override is −1** on that department's recommendation action. That matches the existing reward interval of −1 to 1.

## 6. Out of Scope

Same boundary as BRD-030. `resource.py` and `resource_advice.py` do not import storage. They do not register the policy in a running store. They do not emit the ADR-024 selection episode. They do not add a `PLAN_DAG` edge.
