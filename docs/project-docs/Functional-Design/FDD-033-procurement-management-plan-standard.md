# FDD-033: Procurement Management Plan Standard

**Source ADR:** [ADR-033](../../adr/ADR-033-procurement-management-plan-standard.md) — Accepted (2026-10-29, Menno), episode `7362459e-b596-4f85-8872-5b7063eef015`  
**Source BRD:** [BRD-033](../Business-Requirements/BRD-033-procurement-management-plan-standard.md)  
**Status:** Draft (2026-10-29) — derived from Accepted ADR-033 and BRD-033; not yet adjudicated via `approve-fdd`. §5 interpretations are not confirmed.

---

## 1. Architecture and Component Placement

1. **Profile and section checks** live in `src/agent_learning/pmbok/procurement.py`. `lint_plan` in `src/agent_learning/pmbok/lint.py` consults that profile when `plan_id` is `procurement-management`. The universal constants in `standards.py` stay the ADR-012 baseline. This profile does not change them.
2. **Advisory policy** lives in `src/agent_learning/policy/procurement_advice.py`. It builds a `PolicySnapshot` for the existing `SoftmaxPolicy` and a recommendation record. It does not import `LearningStore`. The caller writes any `Episode`.
3. **Purity:** standard library plus existing `agent_learning` types (`PolicySnapshot`, `SoftmaxPolicy`). No file I/O, no network, no sleep, no new record type. The checks do not open the Charter, the Scope plan, the Cost plan, or `pyproject.toml`.
4. **Reuse:** `count_words`, `check_content`, `TOKEN`, `HEADINGS`, `next_step`, `omission_flags`, and `PLAN_DAG` stay as they are. For a Procurement `full_plan`, `lint_plan` passes `min_out_of_scope_items=2`. It does not pass `min_floor_words`, `max_cap_words`, or `exclude_placeholders`. A `pmp_section` keeps the universal item minimum of 1. A Procurement call does not change the findings of any other `plan_id`.
5. **Already satisfied elsewhere:** `PLAN_DAG["procurement-management"]` is `("scope-management", "cost-management")`. That tuple does not contain `resource-management`. No row lists `procurement-management` as an ancestor. Epic 13 owns staleness. This design adds no edge.

---

## 2. Data Contract

```python
@dataclass(frozen=True)
class ProcurementMeasure:
    floor: int
    cap: int
    min_out_of_scope_items: int

# Lengths equal the ADR-012 baseline. The full_plan item minimum is the raised number.
PROCUREMENT_MEASURES: Mapping[str, ProcurementMeasure] = MappingProxyType({
    "pmp_section": ProcurementMeasure(floor=150, cap=800, min_out_of_scope_items=1),
    "full_plan": ProcurementMeasure(floor=600, cap=5000, min_out_of_scope_items=2),
})

PROCUREMENT_PLAN_ID = "procurement-management"
ADVICE_TASK_ID = "advise-procurement-plan-decision"

# Closed set from ADR-033 §4.4.1. Recorded on the pair. Not a second logit map.
# "procurement" here is this policy's deciding role. It is not the Resource policy's department id.
DECIDING_ROLES: tuple[str, ...] = ("procurement", "project_manager")

# Full intake justification fields from ADR-033 §4.2.
INTAKE_FIELDS: tuple[str, ...] = (
    "need",
    "alternatives",
    "licence",
    "maintenance",
    "exit",
)

DECISION_KINDS: Mapping[str, tuple[str, ...]] = MappingProxyType({
    "route": ("recommend_full_plan", "recommend_pmp_section", "recommend_not_applicable"),
    "paragraph_sufficiency": ("recommend_sufficient", "recommend_insufficient"),
    "graduation": ("recommend_keep_section", "recommend_graduate"),
    "flagged_deviation": ("recommend_accept_deviation", "recommend_refuse_deviation"),
})

@dataclass(frozen=True)
class ProcurementRecommendation:
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

The kind table is the same working list as ADR-033 §4.4.1. `PolicySnapshot.logits` holds the one map. There is no `metadata["department_logits"]` and no per-role map. The deciding role is stored on the recommendation. It does not select which logits are read. The plan `owner_role` stays Project Manager and is not an action.

---

## 3. Behavior

### 3.1 `procurement_measure(plan_id, route) -> ProcurementMeasure | None` (BRU-033-01)

Returns the row when `plan_id == "procurement-management"` and `route` is `pmp_section` or `full_plan`. Returns `None` otherwise, including `not_applicable` and every other plan.

### 3.2 Options `lint_plan` passes (BRU-033-01, BRU-033-02)

When `procurement_measure` returns a row, `lint_plan` calls `check_content` with:

- `min_floor_words` left unset, so the floor stays `FLOORS[route]`
- `max_cap_words` left unset, so the cap stays `CAPS[route]`
- `exclude_placeholders` left unset, so a `TBD` bullet still counts
- for `full_plan`, effective item minimum = `max(2, caller min_out_of_scope_items or 0)`
- for `pmp_section`, the universal item minimum of 1, raised only when the caller passes a higher value

A Procurement `pmp_section` of 159 words is not under floor. A count of 149 is. A count of 801 or 5,001 is over cap. A count of 800 or 5,000 is not.

`not_applicable` skips content checks. This profile does not call `omission_flags` and does not emit `OMISSION_OF_BASE_PLAN`.

### 3.3 `lint_plan` applies the profile (BRU-033-01, BRU-033-04)

After the content checks, `lint_plan` appends `check_procurement_sections`. Finding order is parse, metadata, headings, floor, cap, boundary, then the Procurement section findings of §3.4. `next_step` is unchanged.

When `procurement_measure` returns `None`, this profile adds nothing. A floor finding on another plan, when one is produced, is that plan's universal floor.

### 3.4 `check_procurement_sections(body, route) -> list[LintFlag]` (BRU-033-03)

Section 2 is the text from heading 2 to heading 3. The heading regexes are the ADR-012 headings. If heading 2 is absent, this function returns nothing, because the missing-heading finding already exists. Findings are Tier B `MISSING_REQUIRED_SECTION`, in the order below. Matching is case-insensitive substring presence on Section 2. The check does not parse a register row, does not open a companion file, and does not read Section 1 or Section 3.

Each pair has a missing step and an incomplete step. The missing step fires when the statement's keyword is absent. The incomplete step fires only when that missing step did not fire, and then only when a required part is still absent. The two steps of a pair never both fire.

Make-or-buy criteria:

1. Fires when Section 2 contains neither `make-or-buy` nor `make or buy`. Message: `make-or-buy criteria are missing`.
2. Fires only when step 1 did not fire, which is when a make-or-buy phrase was found. One finding names each missing part. Both routes require factors (`factor`). A `full_plan` also requires weighting (`weight`). Message: `make-or-buy criteria are incomplete`. A `pmp_section` that has the phrase and `factor` produces no weighting finding. A phrase with every required part produces no make-or-buy finding.

Dependency intake rule:

3. Fires when Section 2 contains no `intake`. Message: `dependency intake rule is missing`.
4. Fires only when step 3 did not fire, which is when `intake` was found, and only for `full_plan`. One finding names each missing field from `INTAKE_FIELDS`. Need matches `need`. Alternatives match `alternative`. Licence matches `licen`, so `licence` and `license` both match. Maintenance matches `maintenance`. The substring `maintainer` does not match `maintenance`. Exit matches `exit`. Message: `dependency intake rule is incomplete`. A `pmp_section` that has `intake` produces no justification-field finding.

Contract and licence checks:

5. Fires when Section 2 contains neither `contract` nor `licen`. Message: `contract and licence checks are missing`.
6. Fires only when step 5 did not fire, which is when `contract` or `licen` was found. One finding names each missing check. Both routes require licence compatibility (`compatib`), usage limits (`usage`), data handling and retention (both `data` and `retain`; `retention` contains `retain`), and change-of-terms rights (`change-of-term` or `change of term`). A `full_plan` also requires a verification owner (`owner`). Message: `contract and licence checks are incomplete`. A `pmp_section` that lists the four checks produces no owner finding.

`route == "not_applicable"` returns `[]`. Words in Section 1 or Section 3 do not satisfy the check. A make-or-buy phrase, `intake`, or `contract` / `licen` that is absent still produces the missing finding when the later field words are present in Section 2.

### 3.5 `baseline_snapshot() -> PolicySnapshot` (BRU-033-05)

`task_id` is `advise-procurement-plan-decision`. `metadata["decision_authority"]` is `low`. `metadata["requires_human_approval"]` is `false` on this policy. `PolicySnapshot.logits` has every action in §2 `DECISION_KINDS` at logit `0.0`, and no other action. The snapshot has no `department_logits` and no per-role logit map. It carries no episodes. Calling this function does not write the store and does not create an ADR-024 selection episode. It does not read or copy another plan's advisory snapshot, including the Resource policy's department maps.

### 3.6 `recommend(..., deciding_role) -> ProcurementRecommendation` (BRU-033-06)

The other arguments match the Scope, Schedule, Cost, Risk, Quality, Stakeholder, and Communications advisors: `snapshot`, `decision_kind`, `recommendation_id`, `recommended_at`, `recorded_decisions`, and `min_shown_decisions`.

`deciding_role` must be `procurement` or `project_manager`. `decision_kind` must be one of the four keys. The legal actions are that kind's tuple. `SoftmaxPolicy` chooses among `PolicySnapshot.logits` for those actions only. The kind restricts the action set. It is not a learned context feature. The role is stored on the recommendation. It is not a learned feature and it does not select a logit map.

If `recommendation_id` was returned before, return that same record, including `action_id`, `deciding_role`, and `recommended_at`. Do not draw again.

`visible` is `True` only when `min_shown_decisions` is an int and `recorded_decisions >= min_shown_decisions`. `min_shown_decisions is None` yields `visible=False`.

A recommendation id from another plan advisor is not a Procurement recommendation id.

### 3.7 `advice_reward(followed: bool) -> float` (BRU-033-06)

`True` returns `1.0`. `False` returns `-1.0`. The action credited is the stored `action_id` on the single logit map. The stored `deciding_role` is left unchanged. Gate actions are not an input.

---

## 4. Error Handling

| Situation | Behavior |
|---|---|
| `plan_id` other than `procurement-management` | This profile adds no finding and does not change that plan's floor, cap, or item count |
| Procurement route `not_applicable` | Content checks skipped. This profile emits no `OMISSION_OF_BASE_PLAN` |
| Procurement `pmp_section` of 159 words | No floor finding |
| Procurement `pmp_section` of 149 words | `BELOW_STANDARD_FLOOR` from the universal floor of 150 |
| Make-or-buy, intake, or licence words only in Section 1 or Section 3 | Section 2 still raises the matching missing finding |
| Keyword absent and the later field words present | The missing finding fires. The incomplete finding does not |
| Unknown `decision_kind` | `ValueError` naming the kind |
| Unknown `deciding_role` | `ValueError` naming the role |
| `min_shown_decisions` of 0 or negative | `ValueError` |
| Same `recommendation_id` offered again, including with the other role | Original action, role, and timestamp returned |

---

## 5. Interpretations to Confirm

These are not verbatim in ADR-033. Stories 33.3 and 33.4 wait on items 1 and 2.

1. **One policy, four kinds.** The action set is the table in §2. A call passes one kind and the bandit chooses only inside that kind. The four kinds are the working list in ADR-033 §4.4.1. Confirming this set for Procurement confirms the same ids for the other plan advisors.
2. **The deciding role is recorded. The logits stay one map.** The role ids are `procurement` and `project_manager`. ADR-033 §4.4.1 says a full Procurement plan goes to the Procurement department where one exists, otherwise to the Project Manager, and that the deciding role is recorded with each pair. It does not say the logits are kept apart by role. The role is stored on the recommendation and is immutable with it. It does not select a second map, and it is not a contextual feature. An unknown role raises `ValueError`. The id `procurement` on this policy is not the Resource policy's `procurement` department map. The plan `owner_role` stays Project Manager.
3. **The Tier 1 placeholder filter stays off.** A bullet whose text is only `TBD` counts toward the Procurement minimum. ADR-033 does not cite the ADR-025 placeholder sentence.
4. **Floors and caps are not passed in.** Recording 150, 600, 800, and 5,000 on `ProcurementMeasure` documents the ADR-033 table. The call leaves `min_floor_words` and `max_cap_words` unset. The only raised number passed into the lint is the full-plan item minimum of 2. Inheriting ADR-027 does not copy Cost's 180, 700, 750, or 4,500.
5. **All three structural checks are read from Section 2, and the incomplete step runs only after the keyword was found.** Make-or-buy presence is `make-or-buy` or `make or buy`. Factors are `factor`. Weighting is `weight`. Intake presence is `intake`. A full plan then requires `need`, `alternative`, `licen`, `maintenance`, and `exit`. `maintainer` does not satisfy `maintenance`. Contract and licence presence is `contract` or `licen`. Both routes then require `compatib`, `usage`, both `data` and `retain`, and `change-of-term` or `change of term`. A full plan also requires `owner`. The five example make-or-buy factors in ADR-033 §4.2 are not each required. The lint does not parse intake rows.
6. **Invariants 1, 2, and 3, beyond the full-plan intake words, stay review text.** The intake record as episode evidence, the Cost-envelope change-control sentence, the 10% contingency example, acquisition classes, supplier selection, and supplier performance stay with the human reviewer (BRU-033-07). The lint does not open `pyproject.toml` or the Cost plan. The word `exit` on a full plan is the intake-rule field. It is not a scan of each dependency's replacement steps.
7. **An unset show-minimum withholds every recommendation.** The ADR leaves the number unset on purpose.
8. **Follow is +1 and override is −1** on the recommendation action of the single logit map. That matches the existing reward interval of −1 to 1.

## 6. Out of Scope

Same boundary as BRD-033. `procurement.py` and `procurement_advice.py` do not import storage. They do not register the policy in a running store. They do not emit the ADR-024 selection episode. They do not add a `PLAN_DAG` edge, they do not open `pyproject.toml` or the Cost plan, and they do not write into another plan.
