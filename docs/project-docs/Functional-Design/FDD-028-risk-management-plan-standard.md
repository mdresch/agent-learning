# FDD-028: Risk Management Plan Standard

**Source ADR:** [ADR-028](../../adr/ADR-028-risk-management-plan-standard.md) — Proposed (2026-10-26)  
**Source BRD:** [BRD-028](../Business-Requirements/BRD-028-risk-management-plan-standard.md)  
**Status:** Draft (2026-10-29) — derived from Proposed ADR-028 and BRD-028; not yet adjudicated via `approve-fdd`. §5 interpretations are not confirmed. Adjudication waits until ADR-028 is accepted.

---

## 1. Architecture and Component Placement

1. **Profile and section checks** live in `src/agent_learning/pmbok/risk.py`. `lint_plan` in `src/agent_learning/pmbok/lint.py` consults that profile when `plan_id` is `risk-management`. The universal constants in `standards.py` stay the ADR-012 baseline.
2. **Advisory policy** lives in `src/agent_learning/policy/risk_advice.py`. It builds a `PolicySnapshot` for the existing `SoftmaxPolicy` and a recommendation record. It does not import `LearningStore`. The caller writes any `Episode`.
3. **Purity:** standard library plus existing `agent_learning` types (`PolicySnapshot`, `SoftmaxPolicy`). No file I/O, no network, no sleep, no new record type. The checks do not open the Charter, the upstream plans, or the Stakeholder Register.
4. **Reuse:** `count_words`, `check_content`, `TOKEN`, `HEADINGS`, `next_step`, `omission_flags`, and `PLAN_DAG` stay as they are. Risk passes a raised floor and, for `full_plan`, a raised item minimum into `check_content`. It does not pass `max_cap_words`. The caps remain `CAPS["pmp_section"]` of 800 and `CAPS["full_plan"]` of 5,000. It does not pass `exclude_placeholders`. Story 28.1 uses the floor and item options that already exist. A Risk call does not change the findings of any other `plan_id`.
5. **Already satisfied elsewhere:** `PLAN_DAG["risk-management"]` is `("scope-management", "schedule-management", "cost-management")`. No other row lists `risk-management`. Epic 13 owns staleness. This design adds no second graph and no omission flag.

---

## 2. Data Contract

```python
@dataclass(frozen=True)
class RiskMeasure:
    floor: int
    cap: int
    min_out_of_scope_items: int

# Caps equal the ADR-012 caps. They are recorded so a test can see that Risk does not tighten them.
RISK_MEASURES: Mapping[str, RiskMeasure] = MappingProxyType({
    "pmp_section": RiskMeasure(floor=160, cap=800, min_out_of_scope_items=1),
    "full_plan": RiskMeasure(floor=650, cap=5000, min_out_of_scope_items=2),
})

RISK_PLAN_ID = "risk-management"
ADVICE_TASK_ID = "advise-risk-plan-decision"

REGISTER_FIELDS: tuple[str, ...] = (
    "identifier",
    "description",
    "category",
    "probability",
    "impact",
    "rating",
    "owner",
    "response strategy",
    "status",
    "trigger",
)

DECISION_KINDS: Mapping[str, tuple[str, ...]] = MappingProxyType({
    "route": ("recommend_full_plan", "recommend_pmp_section", "recommend_not_applicable"),
    "paragraph_sufficiency": ("recommend_sufficient", "recommend_insufficient"),
    "graduation": ("recommend_keep_section", "recommend_graduate"),
    "flagged_deviation": ("recommend_accept_deviation", "recommend_refuse_deviation"),
})

@dataclass(frozen=True)
class RiskRecommendation:
    recommendation_id: str
    task_id: str                 # always ADVICE_TASK_ID
    decision_kind: str
    action_id: str
    recommended_at: str          # ISO 8601 UTC
    visible: bool                # False until the profile minimum is met
    logits: Mapping[str, float]  # the logits that produced the action
```

`min_shown_decisions` is an `int | None` on the policy profile. `None` means withhold. A set value is a positive integer chosen by the maintainer.

The kind table is the same working list as ADR-028 §4.4.1. `recommend_accept_deviation` recommends a treatment of a flagged plan deviation. It is not an acceptance of a risk. No action id accepts a risk.

---

## 3. Behavior

### 3.1 `risk_measure(plan_id, route) -> RiskMeasure | None` (BRU-028-01)

Returns the row when `plan_id == "risk-management"` and `route` is `pmp_section` or `full_plan`. Returns `None` otherwise, including `not_applicable` and every other plan.

### 3.2 Options `lint_plan` passes (BRU-028-01, BRU-028-02)

When `risk_measure` returns a row, `lint_plan` calls `check_content` with:

- effective floor = `max(measure.floor, caller min_floor_words or 0)`
- effective item minimum = `max(measure.min_out_of_scope_items, caller min_out_of_scope_items or 0)`
- `max_cap_words` left unset
- `exclude_placeholders` left unset

The effective cap is therefore the universal cap. A count of 800 or 5,000 is not a finding. A count of 801 or 5,001 is. A `TBD` bullet still counts, because the placeholder filter is a Tier 1 rule and this profile does not turn it on.

`not_applicable` skips content checks. This profile does not call `omission_flags` and does not emit `OMISSION_OF_BASE_PLAN`.

### 3.3 `lint_plan` applies the profile (BRU-028-01, BRU-028-04)

After the content checks, `lint_plan` appends `check_risk_sections`. Finding order is parse, metadata, headings, floor, cap, boundary, then the Risk section findings of §3.4. `next_step` is unchanged. A 801-word Risk section produces `EXCEEDS_SECTION_CAP` and `HUMAN_ROUTE_REVIEW`. A 5,001-word Risk plan produces `EXCEEDS_PLAN_CAP` and `CARRY_TO_APPROVAL`.

When `risk_measure` returns `None`, this profile adds nothing.

### 3.4 `check_risk_sections(body, route) -> list[LintFlag]` (BRU-028-03)

Section 2 is the text from heading 2 to heading 3. Section 3 is the text from heading 3 to the end. The heading regexes are the ADR-012 headings. If a heading is absent, the checks that read that section return nothing, because the missing-heading finding already exists. Findings are Tier B `MISSING_REQUIRED_SECTION`, in the order below. Matching is case-insensitive. The check does not parse a table and does not require a numeric score.

Scale, read from Section 2:

1. One finding if probability, impact, or a band is absent. Probability matches `probabilit`. Impact matches `impact`. A band matches `band` or `scale`. Message: `probability-impact scale is missing`, naming each missing part.
2. For `full_plan`, and only when step 1 produced no finding: one finding if objective areas or the combination rule is absent. Objective areas match `objective`. The combination rule matches `combin`. Message: `probability-impact scale is incomplete`, naming `objective areas`, `combination rule`, or both.

Register contract, read from Section 2:

3. No match for `register`. Message: `risk register contract is missing`.
4. For `pmp_section`, and only when step 3 matched: one finding if location or a key field is absent. Location matches `location`. Key fields are identifier (`identifier` or the whole word `id`), `owner`, and either `rating` or `status`. Message: `risk register contract is incomplete`, naming each gap.
5. For `full_plan`, and only when step 3 matched: one finding naming every missing field from `REGISTER_FIELDS`. Identifier matches `identifier` or the whole word `id`. Description matches `descript`. Category matches `categor`. Probability matches `probabilit`. Impact matches `impact`. Rating matches `rating`. Owner matches `owner`. Response strategy matches `response` or `strateg`. Status matches `status`. Trigger matches `trigger`.

Escalation, read from Section 3:

6. No match for `threshold` or `escalat`. Message: `escalation threshold is missing`.
7. For `full_plan`, and only when step 6 produced no finding: one finding if the threshold word, the escalation target, or the acceptance record is absent. The threshold word matches `threshold`. The target matches `sponsor` or `approver`. The acceptance record matches `recorded` or `acceptance`. Message: `escalation threshold is incomplete`, naming each gap.

`route == "not_applicable"` returns `[]`. A `pmp_section` is not checked for objective areas, the combination rule, the full field list, the escalation target, or the acceptance record.

### 3.5 `baseline_snapshot() -> PolicySnapshot` (BRU-028-05)

`task_id` is `advise-risk-plan-decision`. `metadata["decision_authority"]` is `low`. `metadata["requires_human_approval"]` is `false` on this policy. Every action in §2 `DECISION_KINDS` has logit `0.0`. The snapshot carries no episodes and no action whose id accepts a risk. Calling this function does not write the store and does not create an ADR-024 selection episode. It does not read or copy another plan's advisory snapshot.

### 3.6 `recommend(...) -> RiskRecommendation` (BRU-028-06)

The signature matches the other plan advisors: `snapshot`, `decision_kind`, `recommendation_id`, `recommended_at`, `recorded_decisions`, and `min_shown_decisions`.

`decision_kind` must be one of the four keys. The legal actions are that kind's tuple. `SoftmaxPolicy` chooses among those actions only. The kind restricts the action set. It is not a learned context feature.

If `recommendation_id` was returned before, return that same record, including `action_id` and `recommended_at`. Do not draw again.

`visible` is `True` only when `min_shown_decisions` is an int and `recorded_decisions >= min_shown_decisions`. `min_shown_decisions is None` yields `visible=False`.

A recommendation id from another plan advisor is not a Risk recommendation id.

### 3.7 `advice_reward(followed: bool) -> float` (BRU-028-06)

`True` returns `1.0`. `False` returns `-1.0`. The action credited is the stored `action_id`. Gate actions are not an input, and a risk-acceptance decision is not an input.

---

## 4. Error Handling

| Situation | Behavior |
|---|---|
| `plan_id` other than `risk-management` | This profile adds no finding and does not change that plan's floor, cap, or item count |
| Risk route `not_applicable` | Content checks skipped. This profile emits no `OMISSION_OF_BASE_PLAN` |
| Risk `pmp_section` of 751 words | No cap finding |
| Risk `pmp_section` of 801 words | `EXCEEDS_SECTION_CAP` |
| Caller item minimum below the profile | Profile minimum stands |
| Unknown `decision_kind` | `ValueError` naming the kind |
| `min_shown_decisions` of 0 or negative | `ValueError` |
| Same `recommendation_id` offered again | Original action and timestamp returned |
| Scale words only in Section 3 | Section 2 still raises `probability-impact scale is missing` |
| Threshold words only in Section 2 | Section 3 still raises `escalation threshold is missing` |

---

## 5. Interpretations to Confirm

These are not verbatim in ADR-028. Stories 28.3 and 28.4 wait on item 1.

1. **One policy, four kinds.** The action set is the table in §2. A call passes one kind and the bandit chooses only inside that kind. The four kinds are the working list in ADR-028 §4.4.1. `recommend_accept_deviation` does not accept a risk. Confirming this set for Risk confirms the same ids for the Scope, Schedule, and Cost advisory policies.
2. **The Tier 1 placeholder filter stays off.** A bullet whose text is only `TBD` counts toward the Risk minimum. ADR-028 does not cite the ADR-025 placeholder sentence. Confirm if Risk should adopt that filter anyway.
3. **The cap is not passed through `max_cap_words`.** Recording 800 and 5,000 on `RiskMeasure` documents the ADR-028 table. The call leaves the argument unset so a future lowering of the universal cap cannot be raised again by this profile.
4. **Phrase presence is the structural check.** The lint uses the phrases in §3.4. It does not parse register rows, recompute a rating, or open another plan. Appetite, taxonomy, response strategies, and the contingency link are review text (BRU-028-07).
5. **Key fields for a `pmp_section` are location, identifier, owner, and rating or status.** The full field list is required only for `full_plan`.
6. **An unset show-minimum withholds every recommendation.** The ADR leaves the number unset on purpose.
7. **Follow is +1 and override is −1** on the recommendation action. That matches the existing reward interval of −1 to 1.

## 6. Out of Scope

Same boundary as BRD-028. `risk.py` and `risk_advice.py` do not import storage. They do not register the policy in a running store. They do not emit the ADR-024 selection episode. They do not implement #31 action masking.
