# FDD-031: Stakeholder Engagement Plan Standard

**Source ADR:** [ADR-031](../../adr/ADR-031-stakeholder-engagement-plan-standard.md) — Accepted (2026-10-29, Menno), episode `c6564adb-72de-4262-8309-4949e0745f51`  
**Source BRD:** [BRD-031](../Business-Requirements/BRD-031-stakeholder-engagement-plan-standard.md)  
**Status:** Approved (2026-10-30, Menno) — derived from Accepted ADR-031 and BRD-031; adjudicated via `approve-fdd` (robust utility 0.735, episode `77093bb8-b1b9-494e-989b-6b915d61ba19`). §5 interpretations are not confirmed; sections 2–3 implement the approved BRU rules.

---

## 1. Architecture and Component Placement

1. **Profile and section checks** live in `src/agent_learning/pmbok/stakeholder.py`. `lint_plan` in `src/agent_learning/pmbok/lint.py` consults that profile when `plan_id` is `stakeholder-engagement`. The universal constants in `standards.py` stay the ADR-012 baseline. This profile does not change them.
2. **Advisory policy** lives in `src/agent_learning/policy/stakeholder_advice.py`. It builds a `PolicySnapshot` for the existing `SoftmaxPolicy` and a recommendation record. It does not import `LearningStore`. The caller writes any `Episode`.
3. **Purity:** standard library plus existing `agent_learning` types (`PolicySnapshot`, `SoftmaxPolicy`). No file I/O, no network, no sleep, no new record type. The checks do not open the Charter, the Scope plan, or `Stakeholder-Register.md`.
4. **Reuse:** `count_words`, `check_content`, `TOKEN`, `HEADINGS`, `next_step`, `omission_flags`, and `PLAN_DAG` stay as they are. For a Stakeholder `full_plan`, `lint_plan` passes `min_out_of_scope_items=2`. It does not pass `min_floor_words`, `max_cap_words`, or `exclude_placeholders`. A `pmp_section` keeps the universal item minimum of 1. A Stakeholder call does not change the findings of any other `plan_id`.
5. **Already satisfied elsewhere:** `PLAN_DAG["stakeholder-engagement"]` is `("scope-management",)`. No row lists `stakeholder-engagement` as an ancestor. Epic 13 owns staleness. This design adds no edge.

---

## 2. Data Contract

```python
@dataclass(frozen=True)
class StakeholderMeasure:
    floor: int
    cap: int
    min_out_of_scope_items: int

# Lengths equal the ADR-012 baseline. The full_plan item minimum is the raised number.
STAKEHOLDER_MEASURES: Mapping[str, StakeholderMeasure] = MappingProxyType({
    "pmp_section": StakeholderMeasure(floor=150, cap=800, min_out_of_scope_items=1),
    "full_plan": StakeholderMeasure(floor=600, cap=5000, min_out_of_scope_items=2),
})

STAKEHOLDER_PLAN_ID = "stakeholder-engagement"
ADVICE_TASK_ID = "advise-stakeholder-plan-decision"

# Full register field list from ADR-031 §4.2. "name or role" is one field.
REGISTER_FIELDS: tuple[str, ...] = (
    "identifier",
    "name or role",
    "organization or team",
    "project role",
    "interest",
    "influence",
    "current engagement",
    "desired engagement",
    "contact channel",
)

LEVEL_NAMES: tuple[str, ...] = ("unaware", "resistant", "neutral", "supportive", "leading")

DECISION_KINDS: Mapping[str, tuple[str, ...]] = MappingProxyType({
    "route": ("recommend_full_plan", "recommend_pmp_section", "recommend_not_applicable"),
    "paragraph_sufficiency": ("recommend_sufficient", "recommend_insufficient"),
    "graduation": ("recommend_keep_section", "recommend_graduate"),
    "flagged_deviation": ("recommend_accept_deviation", "recommend_refuse_deviation"),
})

@dataclass(frozen=True)
class StakeholderRecommendation:
    recommendation_id: str
    task_id: str                 # always ADVICE_TASK_ID
    decision_kind: str
    action_id: str
    recommended_at: str          # ISO 8601 UTC
    visible: bool                # False until the profile minimum is met
    logits: Mapping[str, float]  # the logits that produced the action
```

`min_shown_decisions` is an `int | None` on the policy profile. `None` means withhold. A set value is a positive integer chosen by the maintainer.

The kind table is the same working list as ADR-031 §4.4.1. There is no department split. The plan owner defaults to the Project Manager and is not an action.

---

## 3. Behavior

### 3.1 `stakeholder_measure(plan_id, route) -> StakeholderMeasure | None` (BRU-031-01)

Returns the row when `plan_id == "stakeholder-engagement"` and `route` is `pmp_section` or `full_plan`. Returns `None` otherwise, including `not_applicable` and every other plan.

### 3.2 Options `lint_plan` passes (BRU-031-01, BRU-031-02)

When `stakeholder_measure` returns a row, `lint_plan` calls `check_content` with:

- `min_floor_words` left unset, so the floor stays `FLOORS[route]`
- `max_cap_words` left unset, so the cap stays `CAPS[route]`
- `exclude_placeholders` left unset, so a `TBD` bullet still counts
- for `full_plan`, effective item minimum = `max(2, caller min_out_of_scope_items or 0)`
- for `pmp_section`, the universal item minimum of 1, raised only when the caller passes a higher value

A Stakeholder `pmp_section` of 159 words is not under floor. A count of 149 is. A count of 801 or 5,001 is over cap. A count of 800 or 5,000 is not.

`not_applicable` skips content checks. This profile does not call `omission_flags` and does not emit `OMISSION_OF_BASE_PLAN`.

### 3.3 `lint_plan` applies the profile (BRU-031-01, BRU-031-04)

After the content checks, `lint_plan` appends `check_stakeholder_sections`. Finding order is parse, metadata, headings, floor, cap, boundary, then the Stakeholder section findings of §3.4. `next_step` is unchanged.

When `stakeholder_measure` returns `None`, this profile adds nothing.

### 3.4 `check_stakeholder_sections(body, route) -> list[LintFlag]` (BRU-031-03)

Section 1 is the text from heading 1 to heading 2. Section 2 is the text from heading 2 to heading 3. The heading regexes are the ADR-012 headings. If a heading is absent, the checks that read that section return nothing, because the missing-heading finding already exists. Findings are Tier B `MISSING_REQUIRED_SECTION`, in the order below. Matching is case-insensitive. The check is phrase presence. It does not parse a register row and it does not open a companion file.

Register contract, read from Section 1:

1. No match for `register`. Message: `stakeholder register contract is missing`.
2. For `pmp_section`, and only when step 1 matched: one finding naming each missing key field. The key fields are location (`location`), identifier (`identifier` or the whole word `id`), role (`role`), interest (`interest`), and influence (`influence`). Message: `stakeholder register contract is incomplete`.
3. For `full_plan`, and only when step 1 matched: one finding naming every missing field from `REGISTER_FIELDS`. Identifier matches `identifier` or the whole word `id`. Name or role matches `name` or `role`. Organization or team matches `organi` or `team`. Project role matches `role`. Interest matches `interest`. Influence matches `influence`. Current engagement matches `current`. Desired engagement matches `desired`. Contact channel matches `contact`.

Engagement levels, read from Section 2:

4. One finding if the scale, `current`, or `desired` is absent. The scale matches `scale`, or at least two names from `LEVEL_NAMES`. Message: `engagement levels are missing`, naming each gap.
5. For `full_plan`, and only when step 4 produced no finding: if none of `all`, `every`, and `each` match, message `engagement levels are incomplete`, naming `all registered stakeholders`.

Engagement actions, read from Section 2:

6. No match for `action`. Message: `engagement actions are missing`.
7. For `full_plan`, and only when step 6 matched: one finding if `owner` or a timing word is absent. Timing matches `timing`, `timebox`, `time box`, or `milestone`. Message: `engagement actions are incomplete`, naming each gap.

`route == "not_applicable"` returns `[]`. A `pmp_section` is not checked for the full field list, the words `all` / `every` / `each`, action owner, or timing. Words in the wrong section do not satisfy the check.

### 3.5 `baseline_snapshot() -> PolicySnapshot` (BRU-031-05)

`task_id` is `advise-stakeholder-plan-decision`. `metadata["decision_authority"]` is `low`. `metadata["requires_human_approval"]` is `false` on this policy. Every action in §2 `DECISION_KINDS` has logit `0.0`. The snapshot carries no episodes and no department split. Calling this function does not write the store and does not create an ADR-024 selection episode. It does not read or copy another plan's advisory snapshot.

### 3.6 `recommend(...) -> StakeholderRecommendation` (BRU-031-06)

The signature matches the Scope, Schedule, Cost, Risk, and Quality advisors: `snapshot`, `decision_kind`, `recommendation_id`, `recommended_at`, `recorded_decisions`, and `min_shown_decisions`. There is no department argument.

`decision_kind` must be one of the four keys. The legal actions are that kind's tuple. `SoftmaxPolicy` chooses among those actions only. The kind restricts the action set. It is not a learned context feature.

If `recommendation_id` was returned before, return that same record, including `action_id` and `recommended_at`. Do not draw again.

`visible` is `True` only when `min_shown_decisions` is an int and `recorded_decisions >= min_shown_decisions`. `min_shown_decisions is None` yields `visible=False`.

A recommendation id from another plan advisor is not a Stakeholder recommendation id.

### 3.7 `advice_reward(followed: bool) -> float` (BRU-031-06)

`True` returns `1.0`. `False` returns `-1.0`. The action credited is the stored `action_id`. Gate actions are not an input.

---

## 4. Error Handling

| Situation | Behavior |
|---|---|
| `plan_id` other than `stakeholder-engagement` | This profile adds no finding and does not change that plan's floor, cap, or item count |
| Stakeholder route `not_applicable` | Content checks skipped. This profile emits no `OMISSION_OF_BASE_PLAN` |
| Stakeholder `pmp_section` of 159 words | No floor finding |
| Stakeholder `pmp_section` of 149 words | `BELOW_STANDARD_FLOOR` from the universal floor of 150 |
| Register words only in Section 2 | Section 1 still raises `stakeholder register contract is missing` |
| Level words only in Section 1 | Section 2 still raises `engagement levels are missing` |
| Unknown `decision_kind` | `ValueError` naming the kind |
| `min_shown_decisions` of 0 or negative | `ValueError` |
| Same `recommendation_id` offered again | Original action and timestamp returned |

---

## 5. Interpretations to Confirm

These are not verbatim in ADR-031. Stories 31.3 and 31.4 wait on item 1.

1. **One policy, four kinds.** The action set is the table in §2. A call passes one kind and the bandit chooses only inside that kind. The four kinds are the working list in ADR-031 §4.4.1. Confirming this set for Stakeholder confirms the same ids for the other plan advisors. There is no department split.
2. **The Tier 1 placeholder filter stays off.** A bullet whose text is only `TBD` counts toward the Stakeholder minimum. ADR-031 does not cite the ADR-025 placeholder sentence.
3. **Floors and caps are not passed in.** Recording 150, 600, 800, and 5,000 on `StakeholderMeasure` documents the ADR-031 table. The call leaves `min_floor_words` and `max_cap_words` unset. The only raised number passed into the lint is the full-plan item minimum of 2.
4. **The register is read from Section 1. Levels and actions are read from Section 2.** A `pmp_section` key field set is location, identifier, role, interest, and influence. `role` satisfies both "name or role" and "project role" on a full plan. Two of the five example level names count as a scale when the word `scale` is absent. `all`, `every`, or `each` is the full-plan signal that the assessment covers the registered stakeholders. The lint does not check that every row exists.
5. **Invariants 1, 2, and 3 have no flag.** Cross-plan `owner_role` lookup, the approve-versus-inform sentence, and data minimization stay review text (BRU-031-07). The lint does not scan for private personal data.
6. **An unset show-minimum withholds every recommendation.** The ADR leaves the number unset on purpose.
7. **Follow is +1 and override is −1** on the recommendation action. That matches the existing reward interval of −1 to 1.

## 6. Out of Scope

Same boundary as BRD-031. `stakeholder.py` and `stakeholder_advice.py` do not import storage. They do not register the policy in a running store. They do not emit the ADR-024 selection episode. They do not add a `PLAN_DAG` edge and they do not open a companion register file.
