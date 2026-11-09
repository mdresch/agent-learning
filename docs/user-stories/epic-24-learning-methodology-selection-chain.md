# Epic 24: Learning Methodology Selection Chain

**Source ADR:** [ADR-024](../adr/ADR-024-learning-methodology-selection-chain.md) — Accepted (2026-10-26, Menno); Episode `f99f1078-db8f-4575-9bb4-77a95ef73b97`  
**Source BRD/FDD:** [BRD-024](../project-docs/Business-Requirements/BRD-024-learning-methodology-selection-chain.md) / [FDD-024](../project-docs/Functional-Design/FDD-024-learning-methodology-selection-chain.md) (both Draft)  
**Status:** Draft — stories derived from Accepted ADR-024 and Draft BRD-024 and FDD-024. Awaiting human approval through `approve-user-stories`, after `approve-brd` and `approve-fdd`. The epic number follows the source ADR number, as Epic 21 follows ADR-021.  

Seven stories build `src/agent_learning_ext/methodology_selection.py`, the seed rule table, the seed cases file, and the policy shape of the selection task. Nothing under `src/agent_learning/` is edited. Each rule sits in exactly one story's criteria (LL-012). Contract tests are `tests/test_methodology_selection_profile.py` (24.1), `tests/test_methodology_selection_rules.py` (24.2), `tests/test_methodology_selection_filter.py` (24.3), `tests/test_methodology_selection_ranking.py` (24.4), `tests/test_methodology_selection_decision.py` (24.5), `tests/test_methodology_selection_seed_table.py` (24.6) and `tests/test_methodology_selection_seed_cases.py` (24.7). A learned selector, building a requested methodology, and changing a methodology's catalog state are not stories (BRD-024 Out of Scope).

**Every story is blocked.** Each waits on one or more choices in FDD-024 §4 (D1 to D14), named in its status line, and on approval of the three documents (LL-010). Implementing Epic 24 also needs a scope decision, because `PMP-BL-v1.1.0` does not authorize it (FDD-024 §7 item 3). The criteria below are written against the options FDD-024 proposes (option A); a different choice changes the criteria that name that row.

Fixtures used by the criteria below are those of FDD-024 §3, "Worked checks", built in the tests and labelled synthetic: "the fixture catalog" (#1 `excluded`, #2 and #3 `implemented`, #9 `candidate` with ADR-015, #10 `candidate` with ADR-016, #25 `blocked`, #30 `candidate` without an ADR), "the fixture rules" (version `test-1`), and the profiles P1 to P6.

---

## Story 24.1 — The Use-Case Profile

**Status:** Draft — blocked on FDD-024 D2 (the closed lists)  
**As** a maintainer declaring a decision, **I want** a strict profile that only a human can declare, **so that** the methodology is chosen from what the decision really is, not from what an agent guesses.

### Acceptance Criteria:
- **$AC_0$ (Accepts A Declared Profile):** `parse_use_case_profile` on the payload of FDD-024 §2.4 returns a `UseCaseProfile` with each field equal to the payload, `hard_constraints` as a tuple, and `complexity_profile` equal to `ComplexityProfile.from_dict` of the same mapping.
- **$AC_1$ (Declared By A Human):** the payload with `declared_by_human` `false`, missing, or the string `"true"` raises `ValueError`; so does a blank `declared_by_role`, a blank `rationale`, or a blank `policy_task_id`, each naming the field.
- **$AC_2$ (Closed Lists):** an unknown field (`confidence`) raises naming it; a missing field raises naming it; `feedback_type` `reward`, `action_space` `continuous`, `context_dependence` `local`, `episode_volume` `weekly` and `drift` `seasonal` each raise naming the field and the value; each value of FDD-024 §2.1 for these fields is accepted.
- **$AC_3$ (Polarity Follows Feedback):** `feedback_type` `none` with `outcome_polarity` `null` is accepted; `none` with `contrastive` raises; `binary_outcome` with `null` raises.
- **$AC_4$ (Flags And Constraints):** `action_probabilities_logged` or `retroactive` given as `1` or `"false"` raises; `hard_constraints` containing a blank string or a number raises; `[]` and `["no_deploy_friday"]` are accepted.
- **$AC_5$ (Complexity Profile Reused):** a `complexity_profile` with `decision_impact` `huge` raises the same exception type and message as `ComplexityProfile.from_dict` on that mapping.
- **$AC_6$ (Pure, And Only One Way In):** `methodology_selection.py` lives under `src/agent_learning_ext/`, imports nothing from `agent_learning.storage` or `agent_learning.types`, imports no `random` and no `numpy`, and calls no `open`; `parse_use_case_profile` is the only public function whose return annotation is `UseCaseProfile`; the input mapping equals its deep copy after the call; `tests/test_upstream_untouched.py` still passes.

---

## Story 24.2 — The Rule Table and Its Integrity Check

**Status:** Draft — blocked on FDD-024 D2, D3, D6, D9 and D11  
**As** a maintainer, **I want** the rule table parsed strictly and checked against the catalog, **so that** a rule cannot name an unknown field, value or methodology, and no methodology lacks a rule.

### Acceptance Criteria:
- **$AC_0$ (Parses):** `parse_selection_rules` on the fixture rules returns a `SelectionRuleTable` with version `test-1`, seven rules in the file's order, and the `requires` lists of rule #2 as tuples.
- **$AC_1$ (Strict Rows):** each of these raises `ValueError` naming the rule id and the key: an unknown top-level key, an unknown row key, a `requires` key `complexity_tier` (not in `REQUIRE_KEYS`; FDD-024 D11), a `requires` value `continuous`, an empty allowed list, `has_hard_constraints` allowed `["yes"]`, a prerequisite `trace`, a cost `tiny`, a blank `source`, and a blank `version`.
- **$AC_2$ (Prerequisite Statuses):** a `prerequisites` map missing `persisted_pairwise_judgments`, or with an extra name, raises; a `repository` prerequisite with `present` `"no"` or a blank `evidence` raises; `episode_trace_id` marked `satisfied_by` `profile` raises.
- **$AC_3$ (Same Ids As The Catalog):** `validate_selection_rules` with the fixture catalog raises naming 30 when rule #30 is removed, naming 31 when a rule #31 is added, and naming 2 when rule #2 appears twice; with the fixture rules it returns `None`.
- **$AC_4$ (Blocked Needs A Missing Prerequisite):** with catalog #25 `blocked`, rule #25 with no prerequisites raises naming 25, and rule #25 with `episode_trace_id` set `present` true raises naming 25; the fixture rules pass.
- **$AC_5$ (Role, D9 option A only):** a rule `role` other than `primary` or `adjunct` raises naming the rule id; a rule without `role` reads as `primary`.

---

## Story 24.3 — Hard Filters That Give A Reason

**Status:** Draft — blocked on FDD-024 D2, D3 and D13  
**As** an auditor, **I want** every methodology a selection sets aside to carry its reason, **so that** nothing is dropped silently.

### Acceptance Criteria:
- **$AC_0$ (Every Methodology Once):** for each of P1 to P5 on the fixture catalog and rules, the eligible ids and the rejected ids together are `{1, 2, 3, 9, 10, 25, 30}`, with no id twice; P1 has 3 eligible and 4 rejected; P5 has 0 eligible and 7 rejected. `select_methodology` with the fixture rules lacking #30 raises the error of Story 24.2 $AC_3$ before filtering.
- **$AC_1$ (State Reasons):** #1 is rejected for every profile with code `premise_violated` and a detail starting `state excluded:` that contains the catalog reason; a fixture entry with state `not_applicable` gives `premise_violated`; one with state `declined` gives code `declined` with the catalog reason (FDD-024 D3).
- **$AC_2$ (Premise Reasons):** for P1, #2 has exactly one reason, `premise_violated`, whose detail names `outcome_polarity` and `positive_only`; for P3, #2, #9 and #10 are rejected with a detail naming `drift`; for P4, #2 has three reasons, in the order `feedback_type`, `outcome_polarity`, `episode_volume`; for P5, #3 is rejected on `action_space`.
- **$AC_3$ (Hard Constraints):** a rule requiring `has_hard_constraints` `true` rejects P1 (`hard_constraints` `[]`) with a detail naming `has_hard_constraints`, and makes the methodology eligible for P1 with `hard_constraints` `["no_deploy_friday"]`.
- **$AC_4$ (Prerequisites):** with the fixture catalog (#25 `blocked`), #25 is rejected with `prerequisite_missing` and detail `episode_trace_id` for every profile, and with no other reason (D13 option A). A rule #29 requiring `logged_action_probability` is rejected with `prerequisite_missing` for P1 and is eligible for P1 with `action_probabilities_logged` true. A repository prerequisite that is present adds no reason: with a separate fixture where catalog #25 has state `candidate` (no ADR) and `episode_trace_id` is `present` true, #25 is eligible for P1 with maturity `candidate` and cost `high`, last in the order `3, 10, 9, 25`. The blocked-state guard itself is the check of Story 24.2 $AC_4$, which `select_methodology` runs first.
- **$AC_5$ (Coded And Explained):** across P1 to P6, every rejection has at least one reason, every code is in `REASON_CODES`, and every detail is non-blank.
- **$AC_6$ (Inputs Unchanged):** the profile, the rule table and the catalog entries equal their deep copies after each call.

---

## Story 24.4 — Ranking By Maturity, As A Recommendation

**Status:** Draft — blocked on FDD-024 D4, D5, D6 and D9  
**As** a maintainer, **I want** the eligible methodologies ranked by how real they are, cheapest first among equals, **so that** I see what I can use today before what would need building.

### Acceptance Criteria:
- **$AC_0$ (Maturity Mapping):** `maturity_of` returns `implemented` for `implemented`; `example_only` for `example_only`, `partial` and `practiced`; `drafted` for `candidate` with an ADR; `candidate` for `candidate` without an ADR and for `blocked`; `None` for `excluded`, `not_applicable` and `declined` (FDD-024 D4). On the 32 entries of the committed `examples/methodologies/catalog.json` it gives the counts pinned in the test; on 2026-11-09 they are 6 `implemented`, 3 `example_only`, 10 `drafted`, 8 `candidate` and 5 `None`, and they change in the same change as any catalog state (FDD-024 D5; LL-007).
- **$AC_1$ (Order):** the eligible ids, in order, are `3, 10, 9` for P1, `2, 3, 10, 9` for P2, and `3, 30` for P3, each with the maturity and cost of FDD-024 §3.
- **$AC_2$ (Tie-Breaks):** in P2, #2 precedes #3 (same maturity and cost, lower id); in P1, #10 precedes #9 (same maturity, lower cost).
- **$AC_3$ (Recommendation Only):** `recommended_id` is 3 for P1, 2 for P2 and `None` for P5; `MethodologySelection` has no field for a decision.
- **$AC_4$ (Deterministic):** fifty calls with the rule rows and the catalog entries in shuffled orders give the same eligible order, the same rejected set and the same recommendation for P2.
- **$AC_5$ (Adjuncts Are Not Recommended, D9 option A only):** with rule #3's cost set to `medium` and an `adjunct` rule #6 (catalog `implemented`, `action_space` discrete, cost `low`) added, P1's eligible order is `6, 3, 10, 9` and `recommended_id` is 3; with only adjuncts eligible, `recommended_id` is `None`.
- **$AC_6$ (Layers, Not Calls):** for P6 with a `drafted` rule #17 (`action_space` discrete, `episode_volume` recurring, `context_dependence` `per_instance`, cost high), the eligible order is `3, 17`; `methodology_selection.py` imports neither `agent_learning_ext.routing` nor `agent_learning_ext.weight_compiler`, checked on its syntax tree.

---

## Story 24.5 — The Human Decision and the Episode Record

**Status:** Draft — blocked on FDD-024 D7, D8 and D14  
**As** an auditor, **I want** the recommendation, the decision and its rationale stored together on an ordinary episode, **so that** I can later see what was recommended, what was decided, why, and whether the two differed, and so that no autonomy follows from it.

### Acceptance Criteria:
- **$AC_0$ (A Human, A Role, A Rationale):** `validate_selection_decision` raises `ValueError` for `decided_by_human` false, a blank `decided_by_role`, a blank `rationale`, and a `kind` of `adopt`.
- **$AC_1$ (Apply Only What Is Built):** on P1, deciding 3 with `apply` is returned unchanged; 3 with `build_request` raises; 10 with `build_request` is returned unchanged; 10 with `apply` raises.
- **$AC_2$ (What Cannot Be Chosen):** on P1, deciding 2 (rejected on a premise) raises with either kind; 25 (rejected only for a missing prerequisite) with `build_request` is returned unchanged and with `apply` raises (FDD-024 D7); a methodology rejected as `declined` raises; id 99 raises.
- **$AC_3$ (The Record):** `selection_episode_metadata` for P1 and the decision 10 `build_request` returns the dict of FDD-024 §2.5 with `rule_table_version` `test-1`, the eligible list `3, 10, 9` with maturity and cost, every rejection with its codes and details, `recommended_id` 3, `decided_id` 10, `decision_kind` `build_request`, `diverged` true, `decided_by_role` and `decided_by_human` true from the decision, the profile as declared and `policy_task_id` from the profile; the decision 3 `apply` gives `diverged` false; P5 with 25 `build_request` gives `recommended_id` `null` and `diverged` `null` (FDD-024 D14 option A; `true` under option B). Each dict equals `json.loads(json.dumps(dict))`.
- **$AC_4$ (No Autonomy):** the record has no top-level `feedback_status`, `decision_disposition`, `correct_action_id` or `decision_authority`; no public function of the module has a parameter annotated as a store, `PolicySnapshot`, `TaskPolicy` or `AutonomyConfig`; the `complexity_profile` inside the record equals the declared one's `to_dict()`.
- **$AC_5$ (Its Own Task, D8 option A):** `docs/policy-shapes/select-learning-methodology.actions.json` holds exactly `accept_recommendation`, `choose_other_eligible` and `request_build`, and `select-learning-methodology.profile.json` parses with `ComplexityProfile.from_dict` and has `requires_human_approval` true, so `agent_learning_ext.routing.route` returns full with reason `pinned` for that task.

---

## Story 24.6 — The Seed Rule Table, Checked Against the Ideation Document

**Status:** Draft — blocked on FDD-024 D1, D5, D9 and D12, and on Menno's review of FDD-024 Appendix A  
**As** a maintainer, **I want** the hand-judged rule table committed and checked against Ideation §2.1, **so that** the two cannot drift apart unnoticed (LL-007).

### Acceptance Criteria:
- **$AC_0$ (Committed And Valid):** `examples/methodologies/selection-rules.json` is tracked (`git ls-files` lists it), parses with `parse_selection_rules`, has 32 rules, and passes `validate_selection_rules` against `parse_catalog` of the committed `catalog.json`.
- **$AC_1$ (Matches The Ideation Document):** the extraction of FDD-024 §3 item 9, run on `docs/project-docs/Ideation-Document.md` read inside the test (LL-023), returns the ids 1 to 32, equal to the rule ids; each rule's `source` contains `#<id>`; the table's `ideation_version` equals the Ideation header's `Version` (`1.14` on 2026-11-09).
- **$AC_2$ (Drift Is Caught):** the same check, given the Ideation text with row 32 removed, fails naming 32; given a table whose `ideation_version` is `1.13`, it fails naming both versions.
- **$AC_3$ (Prerequisites Match The Code):** `episode_trace_id` is `present` false and `Episode` (from `agent_learning.types`) has no field named `trace_id`; `persisted_pairwise_judgments` is `present` false with evidence citing HYP-AL-015.
- **$AC_4$ (A Change Raises The Version):** the test pins the SHA-256 of the table file (line endings normalized, LL-029) for its current `version`; a change to the file without a new version and a new pin fails, naming the version.
- **$AC_5$ (One Authority, D12 option A):** `.claude/skills/learning-methodology-selection/SKILL.md` names `examples/methodologies/selection-rules.json` and FDD-024 as the authority for selection, and its decision tree is replaced by a pointer to them.

---

## Story 24.7 — The Retroactive Seed Cases

**Status:** Draft — blocked on FDD-024 D10 (Menno chooses the cases and declares their profiles) and D5  
**As** a maintainer, **I want** the policies already built profiled after the fact and run through the rules, **so that** the rules are checked against the methodologies those policies actually use, without inventing any episode.

### Acceptance Criteria:
- **$AC_0$ (Declared By Menno, Flagged Retroactive):** `examples/methodologies/selection-seed-cases.json` is tracked; every profile parses with `parse_use_case_profile`, has `retroactive` true and a `declared_by_role` that names Menno; every `evidence` path is tracked (`git ls-files`); every `known_methodology_id` is a catalog id.
- **$AC_1$ (Known Answer Checked, Not Assumed):** for each case, `select_methodology` on the committed table and catalog is run, and the test pins, per case, whether the known methodology is the recommendation, eligible at a stated rank, or rejected with stated reason codes; a later change to the table or the catalog that alters any case fails naming the case.
- **$AC_2$ (Mismatches Shown):** a case whose known methodology is rejected is listed in the test by case and reason, not skipped or removed.
- **$AC_3$ (Nothing Invented, Nothing Written):** the seed file has no key `episode`, `outcome`, `reward` or `feedback_status`; the test imports nothing from `agent_learning.storage`, and the listing of `examples/methodologies/` is the same after the test as before.
- **$AC_4$ (Labelled):** the test docstring states that the cases are profiled after the fact, that agreement with the known answer is not evidence that the rules suit new decisions, and that no selection has yet been recorded for a new decision (BRU-024-17).

---

## Out of Scope per ADR-024 / BRD-024 / FDD-024

- A learned selector, and training on recorded selections.
- Inferring a profile from prose, episodes or an agent's output.
- Changing a methodology's state in the catalog or in Ideation §2.1 (FDD-024 D5 asks who does it, and how).
- Building a methodology that a selection requests.
- Calling the router or the weight compiler, and wiring a selection into `task-policy-init`.
- Editing ADR-003, `ComplexityProfile` or `assess_autonomy`.
- A CLI command that writes the selection Episode, unless Menno chooses FDD-024 D8 option B.
