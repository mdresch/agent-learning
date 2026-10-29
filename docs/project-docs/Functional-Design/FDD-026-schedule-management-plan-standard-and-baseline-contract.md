# FDD-026: Schedule Management Plan Standard and Baseline Contract

**Source ADR:** [ADR-026](../../adr/ADR-026-schedule-management-plan-standard-and-baseline-contract.md) — Proposed (2026-10-26)  
**Source BRD:** [BRD-026](../Business-Requirements/BRD-026-schedule-management-plan-standard-and-baseline-contract.md)  
**Status:** Draft (2026-10-29) — derived from Proposed ADR-026 and BRD-026; not yet adjudicated via `approve-fdd`. §5 interpretations are not confirmed. Adjudication waits until ADR-026 is accepted.

---

## 1. Architecture and Component Placement

1. **Profile and section checks** live in `src/agent_learning/pmbok/schedule.py`. `lint_plan` in `src/agent_learning/pmbok/lint.py` consults that profile when `plan_id` is `schedule-management`. The universal constants in `standards.py` stay the ADR-012 baseline.
2. **Advisory policy** lives in `src/agent_learning/policy/schedule_advice.py`. It builds a `PolicySnapshot` for the existing `SoftmaxPolicy` and a recommendation record. It does not import `LearningStore`. The caller writes any `Episode`.
3. **Purity:** standard library plus existing `agent_learning` types (`PolicySnapshot`, `SoftmaxPolicy`). No file I/O, no network, no sleep, no new record type. The checks do not open the Scope plan.
4. **Reuse:** `count_words`, `check_content`, `TOKEN`, `HEADINGS`, `next_step`, and `PLAN_DAG` stay as they are. Schedule passes a tighter floor, a tighter cap, and a higher item minimum into the content check. The optional arguments are the ones the Scope profile also needs: `max_cap_words: int | None = None` and `exclude_placeholders: bool = False`. Schedule does not add a second pair. Story 26.1 is blocked until those arguments exist with this signature. A Schedule call does not change the findings of any other `plan_id`.
5. **Already satisfied elsewhere:** `PLAN_DAG["schedule-management"]` is `("scope-management",)`. Cost, Resource, and Risk list Schedule as a direct ancestor. Procurement lists Cost and reaches Schedule through it. `DRAFT_ORDER` places Schedule after Scope and before Cost. Epic 13 owns staleness. This design adds no second graph.

---

## 2. Data Contract

```python
@dataclass(frozen=True)
class ScheduleMeasure:
    floor: int
    cap: int
    min_out_of_scope_items: int

# Keyed by route. not_applicable has no row.
SCHEDULE_MEASURES: Mapping[str, ScheduleMeasure] = MappingProxyType({
    "pmp_section": ScheduleMeasure(floor=180, cap=750, min_out_of_scope_items=2),
    "full_plan": ScheduleMeasure(floor=700, cap=4500, min_out_of_scope_items=4),
})

SCHEDULE_PLAN_ID = "schedule-management"
ADVICE_TASK_ID = "advise-schedule-plan-decision"

DECISION_KINDS: Mapping[str, tuple[str, ...]] = MappingProxyType({
    "route": ("recommend_full_plan", "recommend_pmp_section", "recommend_not_applicable"),
    "paragraph_sufficiency": ("recommend_sufficient", "recommend_insufficient"),
    "graduation": ("recommend_keep_section", "recommend_graduate"),
    "flagged_deviation": ("recommend_accept_deviation", "recommend_refuse_deviation"),
})

@dataclass(frozen=True)
class ScheduleRecommendation:
    recommendation_id: str
    task_id: str                 # always ADVICE_TASK_ID
    decision_kind: str
    action_id: str
    recommended_at: str          # ISO 8601 UTC
    visible: bool                # False until the profile minimum is met
    logits: Mapping[str, float]  # the logits that produced the action
```

`min_shown_decisions` is an `int | None` on the policy profile. `None` means withhold. A set value is a positive integer chosen by the maintainer.

The kind table is the same working list as ADR-026 §4.4.1 and the Scope advisory policy. The two policies do not share a snapshot, logits, or episodes. Milestone identifiers such as `M0.5` to `M5` in ADR-026 §4.2 are an example of one project's register. They are not required labels.

---

## 3. Behavior

### 3.1 `schedule_measure(plan_id, route) -> ScheduleMeasure | None` (BRU-026-01)

Returns the row when `plan_id == "schedule-management"` and `route` is `pmp_section` or `full_plan`. Returns `None` otherwise, including `not_applicable` and every other plan.

### 3.2 Options `lint_plan` passes (BRU-026-01, BRU-026-02)

`check_content` accepts `max_cap_words: int | None = None` and `exclude_placeholders: bool = False`.

The effective cap is `CAPS[route]` when `max_cap_words` is `None`. When it is an int, the effective cap is `min(CAPS[route], max_cap_words)`. A value above the universal cap leaves the universal cap in force. A bool or a non-int raises `TypeError`. A count equal to the effective cap is not a finding. The floor option already uses `max(FLOORS[route], min_floor_words or 0)`.

When `exclude_placeholders` is `False`, every distinct bullet counts. When it is `True`, a bullet is dropped before the distinct count if, after strip, it matches `^(?:\[)?(?:TBD|TBC|FIXME|N/A)(?:\])?[.!]?\s*$` with case ignored. `N/A for vendor delivery dates` still counts. The default call keeps today's count. This is the same signature the Scope profile uses. Whichever story lands first adds the arguments; the other story only passes them.

### 3.3 `lint_plan` applies the profile (BRU-026-01, BRU-026-02, BRU-026-04)

After a successful parse, when `schedule_measure` returns a row, `lint_plan` calls `check_content` with:

- effective floor = `max(measure.floor, caller min_floor_words or 0)`
- effective cap = `measure.cap`
- effective item minimum = `max(measure.min_out_of_scope_items, caller min_out_of_scope_items or 0)`
- `exclude_placeholders=True`

It then appends `check_schedule_sections`. Finding order is parse, metadata, headings, floor, cap, boundary, then the Section 2 findings of §3.4. `next_step` is unchanged: Tier C Schedule findings take `CARRY_TO_APPROVAL` unless an `EXCEEDS_SECTION_CAP` is present, which still takes `HUMAN_ROUTE_REVIEW`. A 751-word Schedule section produces `EXCEEDS_SECTION_CAP`. A 4,501-word Schedule plan produces `EXCEEDS_PLAN_CAP`.

When `schedule_measure` returns `None`, this profile adds nothing. A Scope plan continues to follow the Scope profile when that profile is present, and the ADR-012 baseline when it is not.

### 3.4 `check_schedule_sections(body, route) -> list[LintFlag]` (BRU-026-03)

Section 2 is the text from heading 2 to heading 3, using the same heading regexes as ADR-012. If heading 2 is absent, return `[]` because the missing-heading finding already exists. Otherwise, Tier B `MISSING_REQUIRED_SECTION`, one finding per missing statement, in this order. Matching is case-insensitive.

1. No match for `milestone`. Message: `milestone register is missing`.
2. No match for `epic`. Message: `milestone register has no parent epic`.
3. For `full_plan`: no match for `exit condition` or `exit criteria`. Message: `milestone exit conditions are missing`.
4. For `full_plan`: no match for `window`, `date range`, or `range`. Message: `milestone target windows are missing`.
5. No match for `timebox` or `time box`. Message: `timebox model is missing`.
6. For `full_plan`: no match for `predecessor`, `critical path`, or `sequenc`. Message: `sequencing predecessors are missing`.
7. No match for `estimat`. Message: `estimation basis is missing`.
8. For `full_plan`, and only when step 7 matched: one finding if either the unit or the confidence rule is absent. The unit matches `\bunit\b`, `story point`, `point`, `day`, or `hour`. The confidence rule matches `confidence`. Message: `estimation basis is incomplete`, naming `unit`, `confidence`, or both.

`route == "not_applicable"` returns `[]`. A `pmp_section` is not checked for exit conditions, windows, predecessors, unit, or confidence. Its timebox statement is the word `timebox` or `time box`; the word cap already limits length, so the check does not count lines.

### 3.5 `baseline_snapshot() -> PolicySnapshot` (BRU-026-05)

`task_id` is `advise-schedule-plan-decision`. `metadata["decision_authority"]` is `low`. `metadata["requires_human_approval"]` is `false` on this policy. Every action in §2 `DECISION_KINDS` has logit `0.0`. The snapshot carries no episodes. Calling this function does not write the store and does not create an ADR-024 selection episode. It does not read or copy the Scope advisory snapshot.

### 3.6 `recommend(snapshot, decision_kind, *, recommendation_id, recommended_at, recorded_decisions, min_shown_decisions) -> ScheduleRecommendation` (BRU-026-06)

`decision_kind` must be one of the four keys. The legal actions are that kind's tuple. `SoftmaxPolicy` chooses among those actions only; the other logits are not candidates on this call. The kind restricts the action set. It is not a learned context feature.

If `recommendation_id` was returned before, return that same record, including `action_id` and `recommended_at`. Do not draw again.

`visible` is `True` only when `min_shown_decisions` is an int and `recorded_decisions >= min_shown_decisions`. `min_shown_decisions is None` yields `visible=False`.

The withhold and immutability rules match the Scope advisory policy. The records stay in separate modules so a Scope recommendation id is not a Schedule recommendation id.

### 3.7 `advice_reward(followed: bool) -> float` (BRU-026-06)

`True` returns `1.0`. `False` returns `-1.0`. The action credited is the stored `action_id`. Gate actions are not an input.

---

## 4. Error Handling

| Situation | Behavior |
|---|---|
| `plan_id` other than `schedule-management` | This profile adds no finding and does not change that plan's floor, cap, or item count |
| Schedule route `not_applicable` | Content checks skipped, as today. Omission remains `omission_flags` |
| `max_cap_words` above the universal cap | Universal cap stands |
| `max_cap_words` or a floor option not an int | `TypeError` |
| Unknown `decision_kind` | `ValueError` naming the kind |
| `min_shown_decisions` of 0 or negative | `ValueError` |
| Same `recommendation_id` offered again | Original action and timestamp returned |

---

## 5. Interpretations to Confirm

These are not verbatim in ADR-026. Stories 26.3 and 26.4 wait on item 1. Story 26.1 waits on item 2.

1. **One policy, four kinds.** The action set is the table in §2. A call passes one kind and the bandit chooses only inside that kind. The four kinds are the working list in ADR-026 §4.4.1: route, paragraph sufficiency, graduation of an over-cap section, and acceptance of a flagged deviation. Confirming this set for Schedule confirms the same ids for the Scope advisory policy, and the reverse.
2. **One lint signature for the tighter cap and the placeholder filter.** `max_cap_words` and `exclude_placeholders` are shared with the Scope profile. Schedule does not define a different regex or a different cap rule.
3. **Section 2 presence is the structural check.** The lint looks for the phrases in §3.4. It does not parse each milestone row, and it does not open the Scope plan to prove the parent epic exists. Charter traceability, the planning horizon, buffers, the baseline sentence, and the variance numbers are review text (BRU-026-07).
4. **`M0.5` to `M5` are an example, not a required register.** Any wording that meets §3.4 satisfies the structure check.
5. **Development approach stays a writing rule.** ADR-026 §4.5 says Section 1 states it when the Charter does not, and asks the maintainer to confirm. The lint does not read the Charter, so there is no flag.
6. **An unset show-minimum withholds every recommendation.** The ADR leaves the number unset on purpose.
7. **Follow is +1 and override is −1** on the recommendation action. That matches the existing reward interval of −1 to 1.

## 6. Out of Scope

Same boundary as BRD-026. `schedule.py` and `schedule_advice.py` do not import storage. They do not register the policy in a running store. They do not emit the ADR-024 selection episode. They do not implement #25 credit assignment or #4 contextual softmax.
