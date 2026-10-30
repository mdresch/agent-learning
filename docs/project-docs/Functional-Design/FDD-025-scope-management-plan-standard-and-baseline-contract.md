# FDD-025: Scope Management Plan Standard and Baseline Contract

**Source ADR:** [ADR-025](../../adr/ADR-025-scope-management-plan-standard-and-baseline-contract.md) — Accepted (2026-10-26, Menno); re-approved 2026-10-29, episode `983c2b87-8309-4414-98fe-93337989b9b5`  
**Source BRD:** [BRD-025](../Business-Requirements/BRD-025-scope-management-plan-standard-and-baseline-contract.md)  
**Status:** Approved (2026-10-30, Menno) — derived from Accepted ADR-025 and BRD-025; adjudicated via `approve-fdd` (robust utility 0.735, episode `c59be18e-5b2c-4c4b-903a-cd8fa98848bd`). §5 interpretations are not confirmed; sections 2–3 implement the approved BRU rules.

---

## 1. Architecture and Component Placement

1. **Profile and section checks** live in `src/agent_learning/pmbok/scope.py`. `lint_plan` in `src/agent_learning/pmbok/lint.py` consults that profile when `plan_id` is `scope-management`. The universal constants in `standards.py` stay the ADR-012 baseline.
2. **Advisory policy** lives in `src/agent_learning/policy/scope_advice.py`. It builds a `PolicySnapshot` for the existing `SoftmaxPolicy` and a recommendation record. It does not import `LearningStore`. The caller writes any `Episode`.
3. **Purity:** standard library plus existing `agent_learning` types (`PolicySnapshot`, `SoftmaxPolicy`). No file I/O, no network, no sleep, no new record type.
4. **Reuse:** `count_words`, `check_content`, `TOKEN`, `HEADINGS`, `next_step`, and `PLAN_DAG` stay as they are. Scope passes a tighter floor, a tighter cap, and a higher item minimum into the content check. `check_content` gains an optional cap argument and an optional placeholder filter that apply only to the call that passes them.
5. **Already satisfied elsewhere:** `PLAN_DAG["scope-management"]` is empty, and every other plan reaches `scope-management` through its ancestors. Epic 13 owns staleness. This design adds no second graph.

---

## 2. Data Contract

```python
@dataclass(frozen=True)
class ScopeMeasure:
    floor: int
    cap: int
    min_out_of_scope_items: int

# Keyed by route. not_applicable has no row.
SCOPE_MEASURES: Mapping[str, ScopeMeasure] = MappingProxyType({
    "pmp_section": ScopeMeasure(floor=180, cap=750, min_out_of_scope_items=2),
    "full_plan": ScopeMeasure(floor=700, cap=4500, min_out_of_scope_items=4),
})

SCOPE_PLAN_ID = "scope-management"
ADVICE_TASK_ID = "advise-scope-plan-decision"

DECISION_KINDS: Mapping[str, tuple[str, ...]] = MappingProxyType({
    "route": ("recommend_full_plan", "recommend_pmp_section", "recommend_not_applicable"),
    "paragraph_sufficiency": ("recommend_sufficient", "recommend_insufficient"),
    "graduation": ("recommend_keep_section", "recommend_graduate"),
    "flagged_deviation": ("recommend_accept_deviation", "recommend_refuse_deviation"),
})

@dataclass(frozen=True)
class ScopeRecommendation:
    recommendation_id: str
    task_id: str                 # always ADVICE_TASK_ID
    decision_kind: str
    action_id: str
    recommended_at: str          # ISO 8601 UTC
    visible: bool                # False until the profile minimum is met
    logits: Mapping[str, float]  # the logits that produced the action
```

`min_shown_decisions` is an `int | None` on the policy profile. `None` means withhold. A set value is a positive integer chosen by the maintainer.

---

## 3. Behavior

### 3.1 `scope_measure(plan_id, route) -> ScopeMeasure | None` (BRU-025-01)

Returns the row when `plan_id == "scope-management"` and `route` is `pmp_section` or `full_plan`. Returns `None` otherwise, including `not_applicable` and every other plan.

### 3.2 Cap tightening and placeholder filtering in `check_content` (BRU-025-01, BRU-025-02)

Add `max_cap_words: int | None = None` and `exclude_placeholders: bool = False`.

The effective cap is `CAPS[route]` when `max_cap_words` is `None`. When it is an int, the effective cap is `min(CAPS[route], max_cap_words)`. A value above the universal cap leaves the universal cap in force. A bool or a non-int raises `TypeError`. A count equal to the effective cap is not a finding. The floor option already uses `max(FLOORS[route], min_floor_words or 0)` and is unchanged.

When `exclude_placeholders` is `False`, every distinct bullet counts, as today. When it is `True`, a bullet is dropped before the distinct count if, after strip, it matches `^(?:\[(?:TBD|TBC|FIXME|N/A)\]|(?:TBD|TBC|FIXME|N/A))[.!]?\s*$` with case ignored. The brackets are balanced: `[TBD]` and `TBD` are placeholders, while `[TBD` and `TBD]` count as real content. `N/A for mobile clients` still counts. The default call keeps today's count.

### 3.3 `lint_plan` applies the profile (BRU-025-01, BRU-025-02, BRU-025-04)

After a successful parse, when `scope_measure` returns a row, `lint_plan` calls `check_content` with:

- effective floor = `max(measure.floor, caller min_floor_words or 0)`
- effective cap = `measure.cap`
- effective item minimum = `max(measure.min_out_of_scope_items, caller min_out_of_scope_items or 0)`
- `exclude_placeholders=True`

It then appends `check_scope_sections`. Finding order stays parse, metadata, headings, floor, cap, boundary, then the Section 2 findings of §3.4. `next_step` is unchanged: Tier C Scope findings take `CARRY_TO_APPROVAL` unless an `EXCEEDS_SECTION_CAP` is present, which still takes `HUMAN_ROUTE_REVIEW`. A 751-word Scope section produces `EXCEEDS_SECTION_CAP`. A 4,501-word Scope plan produces `EXCEEDS_PLAN_CAP`.

When `scope_measure` returns `None`, `lint_plan` keeps the current call: no tighter cap, placeholders still count, and no Section 2 Scope findings.

### 3.4 `check_scope_sections(body, route) -> list[LintFlag]` (BRU-025-03)

Section 2 is the text from heading 2 to heading 3, using the same heading regexes as ADR-012. If heading 2 is absent, return `[]` because the missing-heading finding already exists. Otherwise, Tier B `MISSING_REQUIRED_SECTION`, one finding per missing statement, in this order:

1. No match for `work breakdown structure` or `\bWBS\b`. Message: `WBS rules are missing`.
2. No match for `definition of done` or `\bDoD\b`. Message: `Definition of Done is missing`.
3. For `pmp_section`: fewer than two of `phase`, `epic`, `story`, `commit`, or `work package` appear, and no line links two of them with `→` or `->`. Message: `WBS hierarchy is missing`.
4. For `full_plan`: any of `phase`, `epic`, `story` (a match of `user story` counts), and (`commit` or `work package`) is absent. One finding: `WBS dictionary hierarchy is incomplete`, naming the missing labels.
5. For `full_plan`: any of `acceptance criteria`, `owner`, and `parent` is absent. One finding: `WBS dictionary fields are incomplete`, naming the missing fields.

Matching is case-insensitive. `route == "not_applicable"` returns `[]`.

### 3.5 `baseline_snapshot() -> PolicySnapshot` (BRU-025-05)

`task_id` is `advise-scope-plan-decision`. `metadata["decision_authority"]` is `low`. `metadata["requires_human_approval"]` is `false` on this policy. Every action in §2 `DECISION_KINDS` has logit `0.0`. The snapshot carries no episodes. Calling this function does not write the store and does not create an ADR-024 selection episode.

### 3.6 `recommend(snapshot, decision_kind, *, recommendation_id, recommended_at, recorded_decisions, min_shown_decisions) -> ScopeRecommendation` (BRU-025-06)

`decision_kind` must be one of the four keys. The legal actions are that kind's tuple. `SoftmaxPolicy` chooses among those actions only; the other logits are not candidates on this call. The kind restricts the action set. It is not a learned context feature.

If `recommendation_id` was returned before, return that same record, including `action_id` and `recommended_at`. Do not draw again.

`visible` is `True` only when `min_shown_decisions` is an int and `recorded_decisions >= min_shown_decisions`. `min_shown_decisions is None` yields `visible=False`.

### 3.7 `advice_reward(followed: bool) -> float` (BRU-025-06)

`True` returns `1.0`. `False` returns `-1.0`. The action credited is the stored `action_id`. Gate actions are not an input.

---

## 4. Error Handling

| Situation | Behavior |
|---|---|
| `plan_id` other than `scope-management` | ADR-012 floors, caps, and item minimum; placeholder bullets still count; no Section 2 Scope findings |
| Scope route `not_applicable` | Content checks skipped, as today. Omission remains `omission_flags` |
| `max_cap_words` above the universal cap | Universal cap stands |
| `max_cap_words` or a floor option not an int | `TypeError` |
| Unknown `decision_kind` | `ValueError` naming the kind |
| `min_shown_decisions` of 0 or negative | `ValueError` |
| Same `recommendation_id` offered again | Original action and timestamp returned |

---

## 5. Interpretations to Confirm

These are not verbatim in ADR-025. Record confirmations here (LL-011).

1. **One policy, four kinds.** **Confirmed (2026-10-30, Menno):** one task id (`advise-scope-plan-decision`), four decision kinds in §2 `DECISION_KINDS`; each `recommend` call passes one kind and the bandit draws only among that kind's actions. The kinds are route, paragraph sufficiency, graduation of an over-cap section, and acceptance of a flagged deviation (ADR-025 §4.4.1). Stories 25.3 and 25.4 may proceed on this basis.
2. **Placeholder exclusion is Scope-only.** Other plans keep today's bullet count, so Epic 12 tests stay valid. The switch is `exclude_placeholders`, default `False`.
3. **A tighter cap is a profile, not a universal lowering.** `max_cap_words` can tighten one call. It cannot raise a cap above ADR-012, and the default call is unchanged.
4. **Section 2 presence is the whole structural check.** Charter traceability, in-scope exhaustiveness, testable wording, and the traceability matrix produce no flag.
5. **An unset show-minimum withholds every recommendation.** The ADR leaves the number unset on purpose.
6. **Follow is +1 and override is −1** on the recommendation action. That matches the existing reward interval of −1 to 1.

## 6. Out of Scope

Same boundary as BRD-025. `scope.py` and `scope_advice.py` do not import storage. They do not register the policy in a running store. They do not emit the ADR-024 selection episode.
