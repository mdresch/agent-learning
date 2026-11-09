# FDD-024: Learning Methodology Selection Chain

**Source ADR:** [ADR-024](../../adr/ADR-024-learning-methodology-selection-chain.md) — Accepted (2026-10-26, Menno); Episode `f99f1078-db8f-4575-9bb4-77a95ef73b97`. Open questions resolved 2026-10-28 (ADR-024 §7).  
**Source BRD:** [BRD-024](../Business-Requirements/BRD-024-learning-methodology-selection-chain.md) (Approved 2026-11-09)<br>
**Status:** Approved (2026-11-09, Menno) — derived from Accepted ADR-024 and approved BRD-024; adjudicated via `approve-fdd` (robust utility 0.762, episode `f8eec8ca-fdd5-4ab3-b3a2-485270b383b4`). Section 4 records Menno's confirmed option A choices for D1-D14. Still open: the separate D5 catalog and Ideation state update, Menno's review of the Appendix A seed rows, Menno declaring the D10 seed profiles, the `PMP-BL-v1.1.0` scope decision, and the stale ADR-024 §2 wording (§7). Document approval does not authorize implementation.

---

## 1. Architecture & Component Placement

1. **Module** `src/agent_learning_ext/methodology_selection.py`. It holds the vocabulary constants, the dataclasses of §2 and the functions of §3. It uses the standard library (`dataclasses`, `typing`, `collections.abc`), `CatalogEntry` and `parse_catalog` from `agent_learning.methodology_catalog`, and `ComplexityProfile` from `agent_learning_ext.autonomy`. It imports nothing from `agent_learning.storage`, `agent_learning_ext.routing` or `agent_learning_ext.weight_compiler` (BRU-024-16), uses no random number, and does no file I/O. Callers pass decoded JSON in and receive frozen dataclasses or plain dicts out, as `methodology_catalog.parse_catalog` does.
2. **Upstream purity (Invariant 6 of the fork rule, `tests/test_upstream_untouched.py`):** no file under `src/agent_learning/` is edited. The module goes under `src/agent_learning_ext/`, like `routing.py` and `weight_compiler.py`.
3. **Package export:** the public names are added to `_EXPORTS` in `src/agent_learning_ext/__init__.py`. Every name is prefixed or specific, so none shadows an existing root name (LL-017): `to_episode_metadata` already maps to `agent_learning.tailoring`, so this module's equivalent is `selection_episode_metadata`.
4. **Data files** (D1, confirmed): the rule table `examples/methodologies/selection-rules.json` (§2.3) beside `catalog.json`, and the seed cases `examples/methodologies/selection-seed-cases.json` (§2.6). The module never opens them; the tests and any caller read them and pass the decoded JSON.
5. **Policy shape** (D8, confirmed): `docs/policy-shapes/select-learning-methodology.actions.json` and `.profile.json`. The selection is recorded on its own task.
6. **No CLI command** (D8, confirmed). The module returns metadata only; the caller writes the Episode. No store is read or written by this epic.

### 1.1 What exists and what is new

| Exists today (reused, not rebuilt) | Where | Used for |
|---|---|---|
| The 32 catalog entries with a canonical `state`, `adr`, `reason` and `reopening_condition`, and `validate_catalog` | `examples/methodologies/catalog.json`, `agent_learning.methodology_catalog` (ADR-036, Story 36.1) | Each methodology's state, from which maturity is derived (D4, D5), and the reason text of a state-level rejection |
| `ComplexityProfile.from_dict` with strict field and value checks | `agent_learning_ext.autonomy` (ADR-003) | The complexity part of the profile (BRU-024-03) |
| The recommend-then-decide record: decided by a human, a role, a rationale, `diverged` | `agent_learning.tailoring.to_episode_metadata` (ADR-011, Story 11.1) | The shape of the decision record; this module follows it but does not import it |
| The hand-written decision tree and Ideation index | `.claude/skills/learning-methodology-selection/SKILL.md` | The source of the proposed seed rows (Appendix A). Under D12 the rule table becomes authoritative and the skill's decision tree a pointer to it |
| The Ideation §2.1 table of 32 rows | `docs/project-docs/Ideation-Document.md` | The id check of BRU-024-14 |

New in this design: the `UseCaseProfile` schema and its parser, the rule table and its integrity check, the filter with reasons, the maturity ranking, the decision record and its validation, the episode metadata, the seed rule table, and the seed cases file.

---

## 2. Data Contract

### 2.1 Constants (closed lists)
| Name | Value | Source |
|---|---|---|
| `FEEDBACK_TYPES` | `scalar_reward`, `binary_outcome`, `ordinal_preference`, `textual_critique`, `none` | ADR-024 §7 |
| `OUTCOME_POLARITIES` | `contrastive`, `positive_only` | ADR-024 §3.1 |
| `ACTION_SPACES` | `discrete`, `ranking`, `configuration` | D2, confirmed |
| `CONTEXT_DEPENDENCE` | `global`, `per_instance` | D2, confirmed |
| `EPISODE_VOLUMES` | `one_off`, `recurring` | D2, confirmed |
| `DRIFT` | `stationary`, `drifting` | D2, confirmed |
| `PREREQUISITES` | `episode_trace_id`, `logged_action_probability`, `persisted_pairwise_judgments` | ADR-024 §2 |
| `REASON_CODES` | `premise_violated`, `prerequisite_missing`, `declined` | ADR-024 §3.2 names the first two; `declined` added by D3, confirmed |
| `MATURITY_ORDER` | `implemented`, `example_only`, `drafted`, `candidate` | ADR-024 §3.3; state mapping D4, confirmed |
| `COST_ORDER` | `low`, `medium`, `high` | D6, confirmed |
| `REQUIRE_KEYS` | `action_space`, `feedback_type`, `outcome_polarity`, `context_dependence`, `episode_volume`, `drift`, `has_hard_constraints` | the profile fields a rule may test, in this order |
| `DECISION_KINDS` | `apply`, `build_request` | ADR-024 §3.4; D7, confirmed (no `no_fit` kind) |

### 2.2 Dataclasses
```python
@dataclass(frozen=True)
class UseCaseProfile:
    policy_task_id: str                 # the decision being profiled; the outcome link of ADR-024 §7
    action_space: str                   # ACTION_SPACES
    feedback_type: str                  # FEEDBACK_TYPES
    outcome_polarity: str | None        # OUTCOME_POLARITIES; None exactly when feedback_type is "none" (D2)
    context_dependence: str             # CONTEXT_DEPENDENCE
    episode_volume: str                 # EPISODE_VOLUMES
    drift: str                          # DRIFT
    hard_constraints: tuple[str, ...]   # declared names, may be empty; has_hard_constraints = bool(hard_constraints)
    action_probabilities_logged: bool
    complexity_profile: ComplexityProfile
    declared_by_role: str               # non-blank
    declared_by_human: bool             # must be True
    rationale: str                      # non-blank
    retroactive: bool = False           # True for a seed case (ADR-024 §7)

@dataclass(frozen=True)
class SelectionRule:
    id: int                                        # catalog id
    requires: Mapping[str, tuple[str | bool, ...]] # REQUIRE_KEYS -> allowed values; an absent key allows any value
    prerequisites: tuple[str, ...]                 # PREREQUISITES
    cost: str                                      # COST_ORDER
    source: str                                    # the Ideation row and evidence the row was judged from
    role: str = "primary"                          # D9, confirmed: "primary" or "adjunct"

@dataclass(frozen=True)
class PrerequisiteStatus:
    satisfied_by: str        # "repository" or "profile"
    present: bool | None     # hand-judged for "repository"; None for "profile"
    evidence: str            # non-blank for "repository"

@dataclass(frozen=True)
class SelectionRuleTable:
    version: str
    prerequisites: Mapping[str, PrerequisiteStatus]
    rules: tuple[SelectionRule, ...]

@dataclass(frozen=True)
class RejectionReason:
    code: str                # REASON_CODES
    detail: str              # names the field and value, the catalog state, or the prerequisite

@dataclass(frozen=True)
class MethodologyRejection:
    id: int
    reasons: tuple[RejectionReason, ...]   # at least one

@dataclass(frozen=True)
class EligibleMethodology:
    id: int
    maturity: str            # MATURITY_ORDER
    cost: str                # COST_ORDER

@dataclass(frozen=True)
class MethodologySelection:
    rule_table_version: str
    eligible: tuple[EligibleMethodology, ...]   # ranked, first is the recommendation
    rejected: tuple[MethodologyRejection, ...]  # ascending id
    recommended_id: int | None                  # None when nothing is eligible

@dataclass(frozen=True)
class SelectionDecision:
    decided_id: int
    kind: str                # DECISION_KINDS
    decided_by_role: str
    decided_by_human: bool
    rationale: str
```

### 2.3 The rule table file
```json
{
  "version": "1",
  "ideation_version": "1.14",
  "prerequisites": {
    "episode_trace_id": {"satisfied_by": "repository", "present": false,
                         "evidence": "Episode has correlation_id and session_id but no trace_id (src/agent_learning/types.py)"},
    "logged_action_probability": {"satisfied_by": "profile"},
    "persisted_pairwise_judgments": {"satisfied_by": "repository", "present": false,
                                     "evidence": "HYP-AL-015: individual pairwise judgments are not persisted"}
  },
  "rules": [
    {"id": 2,
     "requires": {"action_space": ["discrete"], "feedback_type": ["scalar_reward", "binary_outcome"],
                  "outcome_polarity": ["contrastive"], "context_dependence": ["global"],
                  "episode_volume": ["recurring"], "drift": ["stationary"]},
     "prerequisites": [], "cost": "low",
     "source": "Ideation §2.1 #2; HYP-AL-002 (plateau on positive-only history); #30 (assumes stationarity)"}
  ]
}
```
A `profile` prerequisite is satisfied by `action_probabilities_logged` (the only profile-satisfied prerequisite in the ADR). The proposed 32 rows are Appendix A.

### 2.4 The profile input
```json
{"policy_task_id": "example-task", "action_space": "discrete", "feedback_type": "binary_outcome",
 "outcome_polarity": "positive_only", "context_dependence": "global", "episode_volume": "recurring",
 "drift": "stationary", "hard_constraints": [], "action_probabilities_logged": false,
 "complexity_profile": {"intent_ambiguity": "low", "context_variability": "variable", "outcome_observability": "direct",
                        "decision_impact": "high", "reversibility": "reversible", "requires_human_approval": true,
                        "rationale": "..."},
 "declared_by_role": "maintainer", "declared_by_human": true, "rationale": "...", "retroactive": false}
```

### 2.5 Episode metadata of a selection
```json
{
  "methodology_selection": {
    "rule_table_version": "1",
    "policy_task_id": "example-task",
    "retroactive": false,
    "profile": {"...": "the profile of §2.4, as declared"},
    "eligible": [{"id": 3, "maturity": "implemented", "cost": "low"},
                 {"id": 10, "maturity": "drafted", "cost": "low"},
                 {"id": 9, "maturity": "drafted", "cost": "medium"}],
    "rejected": [{"id": 1, "reasons": [{"code": "premise_violated", "detail": "state excluded: ..."}]}],
    "recommended_id": 3,
    "decided_id": 10,
    "decision_kind": "build_request",
    "diverged": true,
    "decided_by_role": "maintainer",
    "decided_by_human": true,
    "rationale": "..."
  }
}
```
The values are the worked fixture of §3 (profile P1). The record carries no `feedback_status`, `decision_authority`, `complexity_profile` write, tier or threshold for the profiled task (BRU-024-12); the complexity profile appears only inside `profile`, as declared.

### 2.6 The seed cases file
```json
{"cases": [{"profile": {"...": "§2.4 with retroactive true, declared by Menno"},
            "known_methodology_id": 3,
            "evidence": "the policy shape or code that shows the methodology this policy uses"}]}
```
The six seed cases are those of D10 (confirmed). Their profiles are not yet declared; Menno declares them (Invariant 4). The file contains no episode and no outcome.

---

## 3. Behavior

1. **`parse_use_case_profile(payload) -> UseCaseProfile`** (BRU-024-01 to 03). Raises `TypeError` for a non-mapping, and `ValueError` naming the field for an unknown or missing field, a value outside its closed list, `outcome_polarity` that is `None` while `feedback_type` is not `none` or set while it is `none`, a blank `policy_task_id`, `declared_by_role` or `rationale`, `declared_by_human` not exactly `True`, a non-boolean `action_probabilities_logged` or `retroactive`, or a blank or non-string entry in `hard_constraints`. `complexity_profile` is parsed by `ComplexityProfile.from_dict`, whose errors propagate. The module has no other way to make a profile.
2. **`parse_selection_rules(payload) -> SelectionRuleTable`** (BRU-024-02, 13). Strict: an unknown or missing key, a key in `requires` outside `REQUIRE_KEYS`, a value outside that key's closed list (`has_hard_constraints` takes `true` or `false`), an empty allowed list, a prerequisite outside `PREREQUISITES`, a `prerequisites` map whose keys are not exactly `PREREQUISITES`, a cost outside `COST_ORDER`, a blank `source` or `version`, a `repository` prerequisite with `present` not a boolean or a blank `evidence`, or a `profile` prerequisite other than `logged_action_probability` each raise `ValueError` naming the row id and the key.
3. **`validate_selection_rules(table, catalog_entries) -> None`** (BRU-024-04, 13). Raises `ValueError` listing every problem: a rule id that is duplicated, or the set of rule ids differing from the set of catalog ids (naming the missing and the extra ids); a catalog entry with state `blocked` whose rule has no prerequisite that is missing in the table (a `repository` prerequisite with `present` false, or `logged_action_probability`). The 32-row check is this function applied to the real catalog, which `validate_catalog` already requires to hold ids 1 to 32.
4. **`maturity_of(entry: CatalogEntry) -> str | None`** (BRU-024-07; D4, confirmed). Mapping: `implemented` gives `implemented`; `example_only`, `partial` and `practiced` give `example_only`; `candidate` with an `adr` gives `drafted`; `candidate` without an `adr`, and `blocked`, give `candidate`; `excluded`, `not_applicable` and `declined` give `None` (they never reach the ranking, item 5). Maturity is derived from the catalog state; the rule table holds none (D5, confirmed). The committed states are out of date (§7 item 2); their update is a separate change.
5. **`select_methodology(profile, table, catalog_entries) -> MethodologySelection`** (BRU-024-04 to 08). It calls `validate_selection_rules` on the same rule table and catalog entries it then filters, and raises before filtering if they fail. That call is the guard that keeps a `blocked` methodology out of the eligible list: a validated table always has a missing prerequisite for it, so step 3 rejects it. There is no path through `select_methodology` that skips the validator. A `blocked` state gives no reason of its own (D13, confirmed). For each rule, in ascending id, it collects every reason, in this order:
   1. **State.** Catalog state `excluded` or `not_applicable` gives `premise_violated` with detail `state <state>: <catalog reason>`; `declined` gives `declined` with the catalog reason (D3, confirmed).
   2. **Premises.** For each key of `REQUIRE_KEYS` in order, present in `requires`, whose profile value is not in the allowed list: `premise_violated` with detail `<key> <value> not in <allowed>`. `has_hard_constraints` is `bool(profile.hard_constraints)`. A `None` polarity is not in any allowed list.
   3. **Prerequisites.** For each prerequisite of the row, in row order, that is missing: `prerequisite_missing` with the prerequisite's name. A `repository` prerequisite is missing when `present` is false; `logged_action_probability` is missing when the profile's `action_probabilities_logged` is false.
   A rule with at least one reason is rejected with all of them; otherwise it is eligible. Eligible methodologies are sorted by (`MATURITY_ORDER` index, `COST_ORDER` index, id). The first is `recommended_id`; with none eligible it is `None`. An `adjunct` row (D9, confirmed) is listed as eligible in its ranked place but is never the recommendation: `recommended_id` is the first eligible `primary` row, and `None` when only adjuncts are eligible. The function changes none of its inputs and is deterministic.
6. **`validate_selection_decision(selection, decision) -> SelectionDecision`** (BRU-024-09, 10; D7). Raises `ValueError` unless `decided_by_human` is `True`, `decided_by_role` and `rationale` are non-blank, and `kind` is in `DECISION_KINDS`. Then (D7, confirmed):
   - `decided_id` eligible with maturity `implemented`: `kind` must be `apply`.
   - `decided_id` eligible with any other maturity: `kind` must be `build_request`.
   - `decided_id` rejected, and every reason `prerequisite_missing`: `kind` must be `build_request`.
   - `decided_id` rejected with any `premise_violated` or `declined` reason, or not in the selection: `ValueError`.
   It returns the decision unchanged.
7. **`selection_episode_metadata(profile, selection, decision) -> dict`** (BRU-024-11). Validates the decision (item 6) and returns the plain dict of §2.5. `diverged` is `decided_id != recommended_id` when there is a recommendation. When `recommended_id` is `None` it is `null` (D14, confirmed), so that `true` always means a recommendation was overridden. The record also carries `decided_by_human` from the decision, so the human-decision rule can be checked from `Episode.metadata` alone. The profile is written back with `complexity_profile` as its `to_dict()`. The dict round-trips through `json.dumps` and `json.loads` unchanged.
8. **No autonomy** (BRU-024-12). No function takes a store, a `PolicySnapshot`, an `AutonomyConfig` or a `TaskPolicy`. The returned metadata holds no top-level `feedback_status`, `decision_disposition` or `correct_action_id`; those belong to the Episode of the selection task (D8, confirmed), never to the profiled task.
9. **The Ideation check** (BRU-024-14). The test reads `docs/project-docs/Ideation-Document.md` inside the test (LL-023), takes the text from the line `#### 2.1 Learning Methodologies Landscape` to the next line starting `##### 2.1.1`, and collects the integers of the lines matching `^\| (\d+) \| `. These must equal the rule ids, and each rule's `source` must contain `#<id>`. The table's `ideation_version` must equal the Ideation header's `Version`. Run on the current Ideation Document (v1.14), the extraction returns ids 1 to 32 in order.
10. **The seed cases** (BRU-024-15). For each case, `parse_use_case_profile` must accept the profile with `retroactive` true, and `select_methodology` on the seed table and the real catalog must either make `known_methodology_id` eligible or reject it; the test records which, and a case whose known methodology is rejected is reported by id and reason, not hidden. The check reads no store and writes nothing.

**Worked checks (run on a scratch implementation of items 4 and 5 on 2026-11-09; to be re-run through the real functions at Ingest, LL-036).** Fixture catalog (synthetic): #1 `excluded`, #2 `implemented`, #3 `implemented`, #9 `candidate` with ADR-015, #10 `candidate` with ADR-016, #25 `blocked`, #30 `candidate` without an ADR. Fixture rules: #1 none; #2 the row of §2.3, cost low; #3 `action_space` discrete, cost low; #9 and #10 the #2 row without `outcome_polarity`, cost medium and low; #25 prerequisite `episode_trace_id` (missing), cost high; #30 `drift` drifting and `episode_volume` recurring, cost medium. Base profile P1: discrete, `binary_outcome`, `positive_only`, global, recurring, stationary, no hard constraints, probabilities not logged.
- **P1:** eligible `3 (implemented, low)`, `10 (drafted, low)`, `9 (drafted, medium)`; recommendation 3. Rejected: 1 `premise_violated` (state excluded), 2 `premise_violated` (`outcome_polarity positive_only not in [contrastive]`), 25 `prerequisite_missing` (`episode_trace_id`), 30 `premise_violated` (`drift stationary not in [drifting]`). 3 eligible + 4 rejected = 7.
- **P2** (P1 with `contrastive`): eligible `2, 3, 10, 9`; recommendation 2. #2 and #3 tie on maturity and cost, and the lower id wins.
- **P3** (P2 with `drifting`): eligible `3 (implemented, low)`, `30 (candidate, medium)`; #2, #9 and #10 rejected on `drift`.
- **P4** (P1 with `feedback_type` none, polarity `None`, `one_off`): eligible only 3. #2 carries three reasons in key order: `feedback_type`, `outcome_polarity`, `episode_volume`.
- **P5** (`ranking`, `ordinal_preference`, contrastive): nothing eligible, `recommended_id` `None`; #3 rejected on `action_space`.
- **Decisions on P1:** choosing 3 with `apply` is valid and not diverged; on P5 (no recommendation), choosing 25 with `build_request` gives `diverged` `null` (D14); choosing 10 with `build_request` is valid and diverged; choosing 10 with `apply` raises; choosing 2 raises (premise); choosing 25 with `build_request` is valid (D7).
- **Adjunct (D9):** with #3's cost set to `medium` and an `adjunct` row #6 (`implemented`, AS discrete, cost low) added, P1 ranks `6, 3, 10, 9` and recommends 3, the first `primary` row.
- **Layers:** a profile P6 (P2 with `per_instance`) and a drafted row #17 (AS discrete, EV recurring, CD `per_instance`, cost high) give eligible `3, 17`; #2, #9 and #10 are rejected on `context_dependence`.
- **Profile prerequisite:** a row #29 with prerequisite `logged_action_probability` is rejected with `prerequisite_missing` when the profile's flag is false and eligible when it is true.
- **Real catalog maturity** (the D4 mapping applied to the 32 committed entries as they stand on 2026-11-09, before the D5 state update): `implemented` 6 (#2, #3, #5, #6, #20, #21), `example_only` 3 (#4, #12, #19), `drafted` 10, `candidate` 8 (#24 to #32 except #27, including blocked #25), and 5 that never rank (#1, #7, #16, #18, #27). 6 + 3 + 10 + 8 + 5 = 32.

---

## 4. Points ADR-024 Left Open

Each row is a place where ADR-024 is silent or ambiguous and code needs an answer. Menno answered each one on 2026-11-09, choosing option A every time; the alternatives and the reasons are kept. The "Stories" column names the stories each row governs.

| # | ADR-024 says | Option A (confirmed) | Alternative (option B, not chosen) | Why it needed a choice, and the answer | Stories |
|---|---|---|---|---|---|
| D1 | "a versioned JSON data file ... like `catalog.json`" | `examples/methodologies/selection-rules.json` and `selection-seed-cases.json`, beside the catalog they are read with | `docs/methodologies/`, which `sidpa-template` already carries | The ADR names the format, not the place. Confirmed option A (Menno, 2026-11-09). | 24.6, 24.7 |
| D2 | Profile fields are listed; only feedback types have a vocabulary | The closed lists of §2.1; `outcome_polarity` is `None` exactly when feedback is `none`; hard constraints are a list of names; persisted pairwise judgments is a repository prerequisite, not a profile field | Numeric episode volume, more action-space kinds, or pairwise judgments as a profile field | Each list is a design choice the ADR left to "small closed lists". Confirmed option A (Menno, 2026-11-09). | 24.1, 24.3 |
| D3 | Two removal reasons: premise violated, prerequisite missing; "a closed list of filter reasons" | Three codes: add `declined` for #27, whose state says "declined for now", not "impossible" | Fold `declined` into `premise_violated` | Reporting a declined method as a violated premise misstates the catalog. Confirmed option A (Menno, 2026-11-09). | 24.2, 24.3 |
| D4 | Four maturity levels; the catalog has ten states | The mapping of §3 item 4 (`partial` and `practiced` as `example_only`; `blocked` as `candidate`) | `partial` as `drafted`; `practiced` never recommended | The approval frame named this gap: the ranking vocabulary is narrower than the states. Confirmed option A (Menno, 2026-11-09). | 24.4 |
| D5 | Rank by maturity; the table starts from the Ideation Document and the evidence in the repository | Derive maturity from the catalog `state` only, so there is one source. Before the seed table is used, the catalog and Ideation states are brought up to date by a separate change | Carry a maturity column in the rule table | The catalog and Ideation §2.1 still say `candidate` for #8, #9, #10, #11, #13, #14 and #15, whose Epics 14 to 20 are all Completed, and for #22 and #17 (Epics 22 and 21 partly built). As committed, every one of them ranks `drafted`. ADR-024 also still says "ADR-014 to ADR-023, none built". The methodology-catalog skill says a state change "goes through ADR-024", but ADR-024 decides no procedure for it. Confirmed option A (Menno, 2026-11-09). Maturity comes from the catalog `state` only. Before the seed table is used, a separate change that Menno approves updates the catalog and Ideation §2.1 states; that change is not part of Epic 24 | 24.4, 24.6, 24.7 |
| D6 | "implementation cost breaks ties" | A hand-judged cost per row, `low`, `medium` or `high`; a remaining tie goes to the lower id | Effort in story points, or no further tie-break (ties reported) | The ADR names no unit, and a deterministic order needs a last key. Confirmed option A (Menno, 2026-11-09). | 24.2, 24.4 |
| D7 | Choose another *eligible* methodology; "choosing a blocked or unbuilt methodology is allowed only as a recorded request to build it" | `apply` only for an `implemented` eligible methodology; `build_request` for any other eligible one and for one rejected only for missing prerequisites; never for a premise or declined rejection. With nothing eligible, the only valid decision is such a build request | Blocked (prerequisite-missing) methodologies are not choosable at all; or a third kind `no_fit` that records "none fits" with a rationale (the skill's "propose a new row") | §3.4 says "eligible" but also allows a "blocked" choice, which §3.2 removes. Whether `example_only` (#4) can be applied is the same question. Confirmed option A (Menno, 2026-11-09). The `no_fit` kind was not chosen | 24.5 |
| D8 | "both are recorded as an `Episode`"; no task, policy or writer named | A task `select-learning-methodology` with a shape of three actions (`accept_recommendation`, `choose_other_eligible`, `request_build`), `full` authority and a profile with `requires_human_approval: true` (so the ADR-021 router pins it without editing `PINNED_FULL`). The module returns the metadata only, as Epic 11 does; the Episode is written by the caller, as the committed approval episodes are | A new `agent-learn-ext methodology-select` command that builds and stores the Episode | The approval frame of ADR-024 named this gap. Confirmed option A (Menno, 2026-11-09). | 24.5 |
| D9 | Hard filters remove what cannot apply | A row `role` of `primary` or `adjunct`. #5 (reward shaping), #6 (human override), #12 (evidence-seeking), #19 (red-team), #20 and #21 (diff policies) are `adjunct`: listed when eligible, never recommended | Give those rows premises narrow enough to keep them out of most profiles, with no new field | With the vocabulary of D2, the adjuncts pass every filter for a discrete decision and, being `implemented` and `low` cost, outrank #3 and every learning method. Confirmed option A (Menno, 2026-11-09). | 24.2, 24.4, 24.6 |
| D10 | Real, already-built policies are profiled as seed cases, flagged `retroactive`; no episodes invented | Menno declares the seed profiles (Invariant 4 forbids an agent doing it). Proposed candidates from the committed shapes: `approve-adr` (full authority, #3), `classify-diff-type` (#20), `escalate-diff-response` (#21), `triage-review-finding` (#3), `route-review-finding` (#2), `validate-intent-foundation`. They live in the seed cases file only and are not written as Episodes | Also write one retroactive selection Episode per case | A retroactive Episode would record a decision on a date it was not made. `validate-intent-foundation`'s known answer is itself contested (REINFORCE plateaued, full authority was the workaround, UCB later crossed the gate), and its 146 episodes are in the git-ignored store (LL-037). Confirmed option A (Menno, 2026-11-09). All six cases are kept, including `validate-intent-foundation`, in the seed cases file only, with no Episodes written. Their profiles are not yet declared; Menno declares them | 24.7 |
| D11 | The profile includes "the existing complexity profile"; selecting grants no autonomy | Recorded only; no rule may test it (`REQUIRE_KEYS` excludes it) | `requires_human_approval: true` removes the low-authority learners, as step 1 of the skill's decision tree does | Filtering on it mixes the complexity axis into the methodology choice, which `docs/decision-making.md` keeps separate; not filtering means the skill's step 1 is not encoded. Confirmed option A (Menno, 2026-11-09). | 24.1 |
| D12 | The table "starts from the Ideation Document"; the skill is "guidance, not a mechanism" | Once the seed table is committed it is authoritative for the selection; the skill's decision tree is replaced by a pointer to the table and to this chain, in the same change (LL-007) | Keep both, with the skill as a summary that may lag | The approval frame named "which source is authoritative between the rule table and the skill". Confirmed option A (Menno, 2026-11-09). | 24.6 |
| D13 | Every rejection has a reason (Invariant 2); nothing says how a `blocked` state is reported | `select_methodology` validates its own inputs (§3 item 5), and a `blocked` methodology is rejected only through its missing prerequisite; the state adds no reason of its own | `blocked` also adds a state reason (`prerequisite_missing`, detail `state blocked: <catalog reason>`), so the filter keeps it out even without the validator | Option B duplicates the prerequisite reason for every blocked row; option A relies on the validator, which the function always calls. Raised by review Q-148-1. Confirmed option A (Menno, 2026-11-09). | 24.3 |
| D14 | Recommendation and decision are both recorded, and whether they differ is derivable (the ADR-011 shape) | `diverged` is `null` when there is no recommendation | `diverged` is `true` when there is no recommendation (the first draft of this FDD) | With nothing eligible there is nothing to depart from, so `true` misreads as an override; `null` adds a third value a reader must handle. Raised by review Q-148-4. Confirmed option A (Menno, 2026-11-09). | 24.5 |

---

## 5. Error Handling

| Scenario | Behavior |
|---|---|
| Profile not a mapping | `TypeError` |
| Profile with an unknown or missing field, a value outside its list, a polarity inconsistent with feedback `none`, a blank task id, role or rationale, `declared_by_human` not `True`, or a non-boolean flag | `ValueError` naming the field |
| Invalid complexity profile | the `ComplexityProfile.from_dict` error, unchanged |
| Rule table with an unknown key, an unknown value, an empty allowed list, an unknown prerequisite or cost, a blank source or version, or a malformed prerequisite status | `ValueError` naming the row id and the key |
| Rule ids that differ from the catalog ids, or a duplicate rule id | `ValueError` naming the missing, extra or duplicated ids |
| A `blocked` methodology with no missing prerequisite in its row | `ValueError` naming the id |
| Nothing eligible | `recommended_id` `None`; not an error |
| Decision not by a human, without a role or rationale, or with an unknown kind | `ValueError` |
| Decision on a premise-rejected, declined or unknown id, or with the wrong kind for its maturity | `ValueError` |
| Any attempt to persist a selection as a new record type | prohibited by ADR-002 Invariant #2; the selection lives in `Episode.metadata` |

| ADR-024 invariant | Where it is enforced |
|---|---|
| 1 A human decides, the system recommends | `select_methodology` returns only a recommendation; `validate_selection_decision` requires a human |
| 2 Every rejection has a reason | `select_methodology` rejects only with reasons; `validate_selection_rules` refuses tables that do not cover the catalog |
| 3 Recorded in `Episode.metadata` | `selection_episode_metadata` |
| 4 Profile declared by humans | `parse_use_case_profile` is the only constructor and requires `declared_by_human` |
| 5 No autonomy granted | §3 item 8; no store, snapshot or autonomy input |

---

## 6. Out of Scope

A learned selector; inferring a profile; changing a methodology's catalog or Ideation state; building a requested methodology; calling the router or the weight compiler; wiring the selection into `task-policy-init`; editing ADR-003, `ComplexityProfile` or `assess_autonomy`; a new CLI command (D8 option A, confirmed); generating the rule table from the Ideation Document.

---

## 7. Decisions and Open Questions

1. **Decided: D1 to D14 (2026-11-09).** Menno confirmed option A for all fourteen rows of §4. §2 and §3 are written to those answers.
2. **Open: the catalog and Ideation states are out of date (D5).** Seven methodologies with completed epics (#8, #9, #10, #11, #13, #14, #15), and two with partly built epics (#17, #22), are still `candidate` in the catalog, its test fixture and Ideation §2.1, while Ideation §2.2 marks HYP-AL-008 and HYP-AL-009 Validated. Until the states are corrected, a selection ranks those methodologies as `drafted`, which understates them. Under D5 the correction is a separate change that Menno approves, to the catalog, the fixture `tests/fixtures/methodology_catalog/ideation_states.json` and Ideation §2.1 together (LL-007). It is not part of Epic 24, and it must land before the seed table is used (Stories 24.4 and 24.6).
3. **Open: Menno's hand review of Appendix A.** The 32 proposed seed rows are a draft. Story 24.6 commits them only after Menno has reviewed them.
4. **Open: the D10 seed profiles.** The six cases are chosen; their profiles are not declared. Invariant 4 requires Menno to declare them before Story 24.7.
5. **Open: scope authorization.** `PMP-BL-v1.1.0` authorizes Bands C and D (Epics 14, 16, 18, 21, 22, 38). Epic 24 is in neither, so implementing it needs a scope decision (a governance change or a baseline increment) after these specs are approved. Drafting and approving them does not.
6. **Open: ADR-024 §2 is stale.** It says ADR-014 to ADR-023 are "none built"; most are now built. Whether to amend the ADR's context is Menno's call; the decision in §3 is not affected.
7. **Open: no selection exists.** No profile has been declared, no selection recorded, and no rule checked against a real decision. The first evidence is the seed cases (Story 24.7), labelled `retroactive`, and nothing is claimed about recommendation quality (BRU-024-17).
8. **Open: the per-use-case prerequisites.** Pairwise judgments may exist for one use case and not another; under D2 they are a repository-level fact. A use case that has them would need the row or the profile to change.

---

## 8. Test Data

*Real:* the committed catalog (`examples/methodologies/catalog.json`, `git ls-files` confirms it is tracked), the Ideation Document, and the committed policy shapes under `docs/policy-shapes/` that seed cases would cite. No selection episode exists. The local store under `data/agent-learning/store` is git-ignored (`.gitignore` line 35), so no criterion reads it (LL-037). *Gap:* Menno-declared profiles of real policies (D10) and real selections. *Oracle:* the synthetic fixtures of §3, labelled as arithmetic and ordering checks, not as evidence (ADR-036 labelling).

---

## Appendix A. Proposed Seed Rows (draft for Menno's hand judgment)

Derived from Ideation §2.1 and the skill's decision tree. Columns use the abbreviations AS (`action_space`), FB (`feedback_type`), OP (`outcome_polarity`), CD (`context_dependence`), EV (`episode_volume`), DR (`drift`), HC (`has_hard_constraints`). "bandit" means AS discrete, FB scalar or binary, EV recurring, DR stationary. The vocabulary (D2), mapping (D4), costs (D6) and roles (D9) follow the confirmed options. The rows themselves still await Menno's hand review (§7 item 3), and Story 24.6 commits them only after it.

| # | Requires | Prerequisites | Cost | Role (D9) | Source |
|---|---|---|---|---|---|
| 1 | none (state `excluded`) | none | high | primary | Ideation #1 |
| 2 | bandit, OP contrastive, CD global | none | low | primary | #2; HYP-AL-002; #30 |
| 3 | AS discrete | none | low | primary | #3; skill steps 1–2 |
| 4 | bandit, OP contrastive, CD per_instance | none | medium | primary | #4; HYP-AL-004 |
| 5 | AS discrete, FB scalar or binary or textual_critique, EV recurring | none | low | adjunct | #5 (feeds #2) |
| 6 | AS discrete | none | low | adjunct | #6 |
| 7 | none (state `excluded`) | none | high | primary | #7 |
| 8 | AS discrete, FB textual_critique | none | medium | primary | #8; HYP-AL-005 |
| 9 | bandit, CD global | none | medium | primary | #9; HYP-AL-002, HYP-AL-009 |
| 10 | bandit, CD global | none | low | primary | #10; HYP-AL-009 |
| 11 | bandit, CD global | none | low | primary | #11 |
| 12 | AS discrete | none | medium | adjunct | #12 |
| 13 | AS discrete, FB ordinal_preference | none | medium | primary | #13 |
| 14 | AS discrete, EV recurring | none | high | primary | #14 |
| 15 | AS discrete, EV recurring | none | medium | primary | #15; HYP-AL-008 |
| 16 | none (state `excluded`) | none | high | primary | #16 |
| 17 | AS discrete, EV recurring, CD per_instance | none | high | primary | #17 |
| 18 | none (state `not_applicable`) | none | high | primary | #18 |
| 19 | AS discrete | none | low | adjunct | #19 |
| 20 | AS discrete | none | low | adjunct | #20 |
| 21 | AS discrete, EV recurring | none | low | adjunct | #21; HYP-AL-007 |
| 22 | AS configuration | none | medium | primary | #22; HYP-AL-010 |
| 23 | AS ranking, FB ordinal_preference | `persisted_pairwise_judgments` | high | primary | #23; HYP-AL-015 |
| 24 | bandit, CD per_instance | none | medium | primary | #24; HYP-AL-018 |
| 25 | none (state `blocked`) | `episode_trace_id` | high | primary | #25 |
| 26 | AS discrete, EV recurring | none | medium | primary | #26; HYP-AL-024 |
| 27 | none (state `declined`) | none | medium | primary | #27 |
| 28 | AS discrete, FB scalar or binary, EV recurring, DR stationary | none | medium | primary | #28; HYP-AL-019 |
| 29 | AS discrete, EV recurring | `logged_action_probability` | medium | primary | #29; HYP-AL-020 |
| 30 | FB scalar or binary, EV recurring, DR drifting | none | medium | primary | #30; HYP-AL-021 |
| 31 | AS discrete, EV recurring, HC true | none | medium | primary | #31; HYP-AL-022 |
| 32 | AS discrete, EV recurring | none | medium | primary | #32; HYP-AL-023 |
