# FDD-027: Cost Management Plan Standard and Baseline Contract

**Source ADR:** [ADR-027](../../adr/ADR-027-cost-management-plan-standard-and-baseline-contract.md) — Accepted (2026-10-29, Menno), episode `0ae724ad-5309-4eb2-a333-749cde39c0c0`  
**Source BRD:** [BRD-027](../Business-Requirements/BRD-027-cost-management-plan-standard-and-baseline-contract.md)  
**Status:** Approved (2026-10-30, Menno) — derived from Accepted ADR-027 and BRD-027; adjudicated via `approve-fdd` (robust utility 0.735, episode `85195db2-130d-437a-8434-059a1c603f91`). §5 interpretations are not confirmed; sections 2–3 implement the approved BRU rules.

---

## 1. Architecture and Component Placement

1. **Profile and section checks** live in `src/agent_learning/pmbok/cost.py`. `lint_plan` in `src/agent_learning/pmbok/lint.py` consults that profile when `plan_id` is `cost-management`. The universal constants in `standards.py` stay the ADR-012 baseline.
2. **Advisory policy** lives in `src/agent_learning/policy/cost_advice.py`. It builds a `PolicySnapshot` for the existing `SoftmaxPolicy` and a recommendation record. It does not import `LearningStore`. The caller writes any `Episode`.
3. **Purity:** standard library plus existing `agent_learning` types (`PolicySnapshot`, `SoftmaxPolicy`). No file I/O, no network, no sleep, no new record type. The checks do not open the Charter, the Scope plan, the Schedule plan, or the Risk plan, and they do not import `tests/test_cost_model.py`.
4. **Reuse:** `count_words`, `check_content`, `TOKEN`, `HEADINGS`, `next_step`, and `PLAN_DAG` stay as they are. Cost passes a tighter floor, a tighter cap, and a higher item minimum into the content check. The optional arguments are the ones [FDD-025](FDD-025-scope-management-plan-standard-and-baseline-contract.md) §3.2 and [FDD-026](FDD-026-schedule-management-plan-standard-and-baseline-contract.md) §3.2 already name: `max_cap_words: int | None = None` and `exclude_placeholders: bool = False`. Cost does not add a third pair. Story 27.1 is blocked until those arguments exist with this signature. A Cost call does not change the findings of any other `plan_id`.
5. **Already satisfied elsewhere:** `PLAN_DAG["cost-management"]` is `("scope-management", "schedule-management")`. Risk lists Cost as a direct ancestor. Procurement lists Cost. `DRAFT_ORDER` places Cost after Schedule. Epic 13 owns staleness. This design adds no second graph.

---

## 2. Data Contract

```python
@dataclass(frozen=True)
class CostMeasure:
    floor: int
    cap: int
    min_out_of_scope_items: int

# Keyed by route. not_applicable has no row.
COST_MEASURES: Mapping[str, CostMeasure] = MappingProxyType({
    "pmp_section": CostMeasure(floor=180, cap=750, min_out_of_scope_items=2),
    "full_plan": CostMeasure(floor=700, cap=4500, min_out_of_scope_items=4),
})

COST_PLAN_ID = "cost-management"
ADVICE_TASK_ID = "advise-cost-plan-decision"

DECISION_KINDS: Mapping[str, tuple[str, ...]] = MappingProxyType({
    "route": ("recommend_full_plan", "recommend_pmp_section", "recommend_not_applicable"),
    "paragraph_sufficiency": ("recommend_sufficient", "recommend_insufficient"),
    "graduation": ("recommend_keep_section", "recommend_graduate"),
    "flagged_deviation": ("recommend_accept_deviation", "recommend_refuse_deviation"),
})

@dataclass(frozen=True)
class CostRecommendation:
    recommendation_id: str
    task_id: str                 # always ADVICE_TASK_ID
    decision_kind: str
    action_id: str
    recommended_at: str          # ISO 8601 UTC
    visible: bool                # False until the profile minimum is met
    logits: Mapping[str, float]  # the logits that produced the action
```

`min_shown_decisions` is an `int | None` on the policy profile. `None` means withhold. A set value is a positive integer chosen by the maintainer.

The kind table is the same working list as ADR-027 §4.4.1 and the Scope and Schedule advisory policies. The three policies do not share a snapshot, logits, or episodes.

---

## 3. Behavior

### 3.1 `cost_measure(plan_id, route) -> CostMeasure | None` (BRU-027-01)

Returns the row when `plan_id == "cost-management"` and `route` is `pmp_section` or `full_plan`. Returns `None` otherwise, including `not_applicable` and every other plan.

### 3.2 Options `lint_plan` passes (BRU-027-01, BRU-027-02)

`check_content` accepts `max_cap_words: int | None = None` and `exclude_placeholders: bool = False`, with the behaviour in FDD-025 §3.2. Cost does not redefine the cap rule or the placeholder regex. Whichever of Stories 25.1, 26.1, and 27.1 lands first adds the arguments; the others only pass them.

The placeholder regex is `^(?:\[)?(?:TBD|TBC|FIXME|N/A)(?:\])?[.!]?\s*$` with case ignored. `N/A for post-handover operating cost` still counts.

### 3.3 `lint_plan` applies the profile (BRU-027-01, BRU-027-02, BRU-027-04)

After a successful parse, when `cost_measure` returns a row, `lint_plan` calls `check_content` with:

- effective floor = `max(measure.floor, caller min_floor_words or 0)`
- effective cap = `measure.cap`
- effective item minimum = `max(measure.min_out_of_scope_items, caller min_out_of_scope_items or 0)`
- `exclude_placeholders=True`

It then appends `check_cost_sections`. Finding order is parse, metadata, headings, floor, cap, boundary, then the Cost section findings of §3.4. `next_step` is unchanged: Tier C Cost findings take `CARRY_TO_APPROVAL` unless an `EXCEEDS_SECTION_CAP` is present, which still takes `HUMAN_ROUTE_REVIEW`. A 751-word Cost section produces `EXCEEDS_SECTION_CAP`. A 4,501-word Cost plan produces `EXCEEDS_PLAN_CAP`.

When `cost_measure` returns `None`, this profile adds nothing.

### 3.4 `check_cost_sections(body, route) -> list[LintFlag]` (BRU-027-03)

Section 1 is the text from heading 1 to heading 2. Section 2 is the text from heading 2 to heading 3. The heading regexes are the ADR-012 headings. If a heading is absent, the checks that read that section return nothing, because the missing-heading finding already exists. Findings are Tier B `MISSING_REQUIRED_SECTION`, in the order below. Matching is case-insensitive.

Envelope, read from Section 1:

1. No match for `envelope` or `ceiling`. Message: `management envelope is missing`.
2. For `full_plan`, and only when step 1 matched: one finding if the unit or the approver is absent. The unit matches `unit`, `currency`, `euro`, `dollar`, `person-hour`, `person hour`, or `story point`. The approver matches `approv` or `sponsor`. Message: `management envelope is incomplete`, naming `unit`, `approver`, or both.

Categories and estimating basis, read from Section 2:

3. No match for `categor`. Message: `cost categories are missing`.
4. For `full_plan`, and only when step 3 matched: one finding if any of owner, source, range, or estimating method is absent. Owner matches `owner`. Source matches `source` or `measurement`. Range matches `range` or `accuracy`. Method matches `estimat`. Message: `cost categories and estimating basis are incomplete`, naming each missing part.

Contingency and reserve, read from Section 2:

5. No match for `contingenc`. Message: `contingency rule is missing`.
6. For `full_plan`, and only when step 5 matched: one finding if reserve or release authority is absent. Reserve matches `reserve`. Release authority matches `release`. Message: `contingency and reserve rule is incomplete`, naming `reserve`, `release authority`, or both.

`route == "not_applicable"` returns `[]`. A `pmp_section` is not checked for unit, approver, owner, source, range, estimating method, reserve, or release authority. The check does not count lines and does not require a numeric amount.

### 3.5 `baseline_snapshot() -> PolicySnapshot` (BRU-027-05)

`task_id` is `advise-cost-plan-decision`. `metadata["decision_authority"]` is `low`. `metadata["requires_human_approval"]` is `false` on this policy. Every action in §2 `DECISION_KINDS` has logit `0.0`. The snapshot carries no episodes. Calling this function does not write the store and does not create an ADR-024 selection episode. It does not read or copy the Scope or Schedule advisory snapshot.

### 3.6 `recommend(snapshot, decision_kind, *, recommendation_id, recommended_at, recorded_decisions, min_shown_decisions) -> CostRecommendation` (BRU-027-06)

`decision_kind` must be one of the four keys. The legal actions are that kind's tuple. `SoftmaxPolicy` chooses among those actions only; the other logits are not candidates on this call. The kind restricts the action set. It is not a learned context feature.

If `recommendation_id` was returned before, return that same record, including `action_id` and `recommended_at`. Do not draw again.

`visible` is `True` only when `min_shown_decisions` is an int and `recorded_decisions >= min_shown_decisions`. `min_shown_decisions is None` yields `visible=False`.

The withhold and immutability rules match the Scope and Schedule advisory policies. A recommendation id from either of those policies is not a Cost recommendation id.

### 3.7 `advice_reward(followed: bool) -> float` (BRU-027-06)

`True` returns `1.0`. `False` returns `-1.0`. The action credited is the stored `action_id`. Gate actions are not an input.

---

## 4. Error Handling

| Situation | Behavior |
|---|---|
| `plan_id` other than `cost-management` | This profile adds no finding and does not change that plan's floor, cap, or item count |
| Cost route `not_applicable` | Content checks skipped, as today. Omission remains `omission_flags` |
| `max_cap_words` above the universal cap | Universal cap stands |
| `max_cap_words` or a floor option not an int | `TypeError` |
| Unknown `decision_kind` | `ValueError` naming the kind |
| `min_shown_decisions` of 0 or negative | `ValueError` |
| Same `recommendation_id` offered again | Original action and timestamp returned |
| Envelope words only in Section 2 | Section 1 still raises `management envelope is missing` |
| Category words only in Section 1 | Section 2 still raises `cost categories are missing` |

---

## 5. Interpretations to Confirm

These are not verbatim in ADR-027. Stories 27.3 and 27.4 wait on item 1. Story 27.1 waits on item 2.

1. **One policy, four kinds.** The action set is the table in §2. A call passes one kind and the bandit chooses only inside that kind. The four kinds are the working list in ADR-027 §4.4.1. Confirming this set for Cost confirms the same ids for the Scope and Schedule advisory policies.
2. **One lint signature for the tighter cap and the placeholder filter.** `max_cap_words` and `exclude_placeholders` are shared with FDD-025 and FDD-026. Cost does not define a different regex or a different cap rule. The placeholder rule is inherited for the Tier 1 item count even though ADR-027 §4.3 does not repeat the ADR-025 placeholder sentence.
3. **The envelope is read from Section 1. Categories and contingency are read from Section 2.** That follows ADR-027 §4.2. The lint looks for the phrases in §3.4. It does not parse a category table, and it does not open the Schedule, Scope, or Risk plan.
4. **Staged funding, burn rate, the ±10% tolerance, and Invariants 2 and 3 are review text.** They have no flag (BRU-027-07). A numeric ceiling is not required for the envelope phrase to count.
5. **Effort units count as a unit.** `person-hour`, `person hour`, and `story point` satisfy the full-plan unit check, as ADR-027 §8 item 2 allows when the envelope declares them.
6. **Risk reconciliation is not a lint step.** ADR-027 §4.5 leaves open whether contingency set before the Risk plan needs an explicit Cost re-approval. This design does not add that step.
7. **An unset show-minimum withholds every recommendation.** The ADR leaves the number unset on purpose.
8. **Follow is +1 and override is −1** on the recommendation action. That matches the existing reward interval of −1 to 1.

## 6. Out of Scope

Same boundary as BRD-027. `cost.py` and `cost_advice.py` do not import storage. They do not register the policy in a running store. They do not emit the ADR-024 selection episode. They do not implement #25 credit assignment.
