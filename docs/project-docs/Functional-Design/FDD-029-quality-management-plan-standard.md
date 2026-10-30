# FDD-029: Quality Management Plan Standard

**Source ADR:** [ADR-029](../../adr/ADR-029-quality-management-plan-standard.md) — Accepted (2026-10-29, Menno), episode `736036f7-40a1-441f-afc0-062501c46d57`  
**Source BRD:** [BRD-029](../Business-Requirements/BRD-029-quality-management-plan-standard.md)  
**Status:** Approved (2026-10-30, Menno) — derived from Accepted ADR-029 and BRD-029; adjudicated via `approve-fdd` (robust utility 0.735, episode `d191d9d0-5cb0-40fc-b2c7-34130e246ebf`). §5 interpretations are not confirmed; sections 2–3 implement the approved BRU rules.

---

## 1. Architecture and Component Placement

1. **Profile and section checks** live in `src/agent_learning/pmbok/quality.py`. `lint_plan` in `src/agent_learning/pmbok/lint.py` consults that profile when `plan_id` is `quality-management`. The universal constants in `standards.py` stay the ADR-012 baseline.
2. **Advisory policy** lives in `src/agent_learning/policy/quality_advice.py`. It builds a `PolicySnapshot` for the existing `SoftmaxPolicy` and a recommendation record. It does not import `LearningStore`. The caller writes any `Episode`.
3. **Purity:** standard library plus existing `agent_learning` types (`PolicySnapshot`, `SoftmaxPolicy`). No file I/O, no network, no sleep, no new record type. The checks do not open the Charter, the Scope plan, or a test report.
4. **Reuse:** `count_words`, `check_content`, `TOKEN`, `HEADINGS`, `next_step`, `omission_flags`, and `PLAN_DAG` stay as they are. Quality passes a raised floor and, for `full_plan`, a raised item minimum into `check_content`. It does not pass `max_cap_words`. The caps remain 800 and 5,000. It does not pass `exclude_placeholders`. Story 29.1 uses the floor and item options that already exist. A Quality call does not change the findings of any other `plan_id`.
5. **Already satisfied elsewhere:** `PLAN_DAG["quality-management"]` is `("scope-management",)`. No other row lists `quality-management`. Epic 13 owns staleness. This design adds no second graph and no omission flag.

---

## 2. Data Contract

```python
@dataclass(frozen=True)
class QualityMeasure:
    floor: int
    cap: int
    min_out_of_scope_items: int

# Caps equal the ADR-012 caps. They are recorded so a test can see that Quality does not tighten them.
QUALITY_MEASURES: Mapping[str, QualityMeasure] = MappingProxyType({
    "pmp_section": QualityMeasure(floor=160, cap=800, min_out_of_scope_items=1),
    "full_plan": QualityMeasure(floor=650, cap=5000, min_out_of_scope_items=2),
})

QUALITY_PLAN_ID = "quality-management"
ADVICE_TASK_ID = "advise-quality-plan-decision"

VERIFICATION_TYPES: tuple[str, ...] = ("unit", "contract", "integration", "peer review")

DECISION_KINDS: Mapping[str, tuple[str, ...]] = MappingProxyType({
    "route": ("recommend_full_plan", "recommend_pmp_section", "recommend_not_applicable"),
    "paragraph_sufficiency": ("recommend_sufficient", "recommend_insufficient"),
    "graduation": ("recommend_keep_section", "recommend_graduate"),
    "flagged_deviation": ("recommend_accept_deviation", "recommend_refuse_deviation"),
})

@dataclass(frozen=True)
class QualityRecommendation:
    recommendation_id: str
    task_id: str                 # always ADVICE_TASK_ID
    decision_kind: str
    action_id: str
    recommended_at: str          # ISO 8601 UTC
    visible: bool                # False until the profile minimum is met
    logits: Mapping[str, float]  # the logits that produced the action
```

`min_shown_decisions` is an `int | None` on the policy profile. `None` means withhold. A set value is a positive integer chosen by the maintainer.

The kind table is the same working list as ADR-029 §4.4.1. No action id waives a gate. No action id chooses rework or escalation. That triage decision is the later policy in ADR-029 §4.4, and this snapshot does not declare it.

---

## 3. Behavior

### 3.1 `quality_measure(plan_id, route) -> QualityMeasure | None` (BRU-029-01)

Returns the row when `plan_id == "quality-management"` and `route` is `pmp_section` or `full_plan`. Returns `None` otherwise, including `not_applicable` and every other plan.

### 3.2 Options `lint_plan` passes (BRU-029-01, BRU-029-02)

When `quality_measure` returns a row, `lint_plan` calls `check_content` with:

- effective floor = `max(measure.floor, caller min_floor_words or 0)`
- effective item minimum = `max(measure.min_out_of_scope_items, caller min_out_of_scope_items or 0)`
- `max_cap_words` left unset
- `exclude_placeholders` left unset

The effective cap is the universal cap. A count of 800 or 5,000 is not a finding. A count of 801 or 5,001 is. A `TBD` bullet still counts. ADR-029 does not cite the Tier 1 placeholder sentence.

`not_applicable` skips content checks. This profile does not call `omission_flags` and does not emit `OMISSION_OF_BASE_PLAN`.

### 3.3 `lint_plan` applies the profile (BRU-029-01, BRU-029-04)

After the content checks, `lint_plan` appends `check_quality_sections`. Finding order is parse, metadata, headings, floor, cap, boundary, then the Quality section findings of §3.4. `next_step` is unchanged. An 801-word Quality section produces `EXCEEDS_SECTION_CAP` and `HUMAN_ROUTE_REVIEW`. A 5,001-word Quality plan produces `EXCEEDS_PLAN_CAP` and `CARRY_TO_APPROVAL`.

When `quality_measure` returns `None`, this profile adds nothing.

### 3.4 `check_quality_sections(body, route) -> list[LintFlag]` (BRU-029-03)

Section 2 is the text from heading 2 to heading 3. The heading regexes are the ADR-012 headings. If heading 2 is absent, return `[]`, because the missing-heading finding already exists. Findings are Tier B `MISSING_REQUIRED_SECTION`, in the order below. Matching is case-insensitive. The check does not parse a gate table and does not require a numeric coverage value.

Gates:

1. No match for `gate`. Message: `quality gates are missing`.
2. When step 1 matched, and neither `pass` nor `criteri` matches: message `quality gates have no pass criteria`.
3. For `full_plan`, and only when steps 1 and 2 produced no finding: one finding if `evidence` or `owner` is absent. Message: `quality gates are incomplete`, naming each gap.

Verification, still in Section 2:

4. One finding if no verification type matches, or the minimum is absent. A type is any of `unit`, `contract`, `integration`, or `peer review`. The minimum matches `minimum` or `threshold`. Message: `verification criteria are missing`, naming `types`, `minimum`, or both.
5. For `full_plan`, and only when step 4 produced no finding: if neither `coverage` nor `measur` matches, message `verification criteria are incomplete`, naming `measurement scope`.

Nonconformance, still in Section 2:

6. No match for `nonconformance`, `non-conformance`, or `rework`. Message: `nonconformance handling is missing`.
7. For `full_plan`, and only when step 6 matched: one finding if `triage`, `waiver`, or `rework` is absent. Message: `nonconformance handling is incomplete`, naming each gap.

`route == "not_applicable"` returns `[]`. A `pmp_section` is not checked for evidence, owner, measurement scope, triage, waiver, or rework beyond the word that satisfied step 6.

### 3.5 `baseline_snapshot() -> PolicySnapshot` (BRU-029-05)

`task_id` is `advise-quality-plan-decision`. `metadata["decision_authority"]` is `low`. `metadata["requires_human_approval"]` is `false` on this policy. Every action in §2 `DECISION_KINDS` has logit `0.0`. The snapshot carries no episodes, no waive action, and no rework or escalate action. Calling this function does not write the store and does not create an ADR-024 selection episode. It does not read or copy another plan's advisory snapshot.

### 3.6 `recommend(...) -> QualityRecommendation` (BRU-029-06)

The signature matches the other plan advisors: `snapshot`, `decision_kind`, `recommendation_id`, `recommended_at`, `recorded_decisions`, and `min_shown_decisions`.

`decision_kind` must be one of the four keys. The legal actions are that kind's tuple. `SoftmaxPolicy` chooses among those actions only. The kind restricts the action set. It is not a learned context feature.

If `recommendation_id` was returned before, return that same record, including `action_id` and `recommended_at`. Do not draw again.

`visible` is `True` only when `min_shown_decisions` is an int and `recorded_decisions >= min_shown_decisions`. `min_shown_decisions is None` yields `visible=False`.

A recommendation id from another plan advisor is not a Quality recommendation id.

### 3.7 `advice_reward(followed: bool) -> float` (BRU-029-06)

`True` returns `1.0`. `False` returns `-1.0`. The action credited is the stored `action_id`. Gate actions are not an input, and a waiver decision is not an input.

---

## 4. Error Handling

| Situation | Behavior |
|---|---|
| `plan_id` other than `quality-management` | This profile adds no finding and does not change that plan's floor, cap, or item count |
| Quality route `not_applicable` | Content checks skipped. This profile emits no `OMISSION_OF_BASE_PLAN` |
| Quality `pmp_section` of 751 words | No cap finding |
| Quality `pmp_section` of 801 words | `EXCEEDS_SECTION_CAP` |
| Caller item minimum below the profile | Profile minimum stands |
| Gate word present, no pass criterion | `quality gates have no pass criteria`, and no second gate finding |
| Unknown `decision_kind` | `ValueError` naming the kind |
| `min_shown_decisions` of 0 or negative | `ValueError` |
| Same `recommendation_id` offered again | Original action and timestamp returned |
| Gate words only in Section 1 or Section 3 | Section 2 still raises `quality gates are missing` |

---

## 5. Interpretations to Confirm

These are not verbatim in ADR-029. Stories 29.3 and 29.4 wait on item 1.

1. **One policy, four kinds.** The action set is the table in §2. A call passes one kind and the bandit chooses only inside that kind. The four kinds are the working list in ADR-029 §4.4.1. Confirming this set for Quality confirms the same ids for the other plan advisors. This policy does not include rework or escalate.
2. **The Tier 1 placeholder filter stays off.** A bullet whose text is only `TBD` counts toward the Quality minimum. ADR-029 does not cite the ADR-025 placeholder sentence.
3. **The cap is not passed through `max_cap_words`.** Recording 800 and 5,000 on `QualityMeasure` documents the ADR-029 table. The call leaves the argument unset.
4. **All three structural checks read Section 2.** Pass criteria match `pass` or `criteri`. A verification type is one of `unit`, `contract`, `integration`, or `peer review`. Measurement scope matches `coverage` or `measur`, not the bare word `scope`. The lint does not decide whether the text restates the Scope Definition of Done.
5. **Waiver text in Section 3 is review text.** The full-plan nonconformance check looks for `waiver` in Section 2. Invariant 3, that an actual waiver carries a recorded rationale and a named approver, is BRU-029-07 and has no flag.
6. **An unset show-minimum withholds every recommendation.** The ADR leaves the number unset on purpose.
7. **Follow is +1 and override is −1** on the recommendation action. That matches the existing reward interval of −1 to 1.

## 6. Out of Scope

Same boundary as BRD-029. `quality.py` and `quality_advice.py` do not import storage. They do not register the policy in a running store. They do not emit the ADR-024 selection episode. They do not declare the later triage policy.
