# Implementation Log

This log records completed user stories in accordance with the SIDPA `implement-story` lifecycle. Append-only, never edited.

---

## Story 5.1 — Build `compare_decision_results()` and the `task-policy-compare` CLI
- **Commit:** `310dd3e`
- **Date:** 2026-10-23
- **Branch:** `feat/story-5.1`
- **Source ADR / BRD / FDD:** ADR-005, BRD-005, FDD-005
- **Files Modified/Created:**
  - `src/agent_learning/comparison.py` (pure function comparison module)
  - `src/agent_learning/__init__.py` (exported comparison symbols)
  - `src/agent_learning/cli.py` (added `task-policy-compare` CLI subcommand)
  - `tests/test_comparison.py` (contract tests encoding $AC_0$ through $AC_5$)
  - `docs/user-stories/epic-5-decision-progress-comparison.md` (status updated to Completed)
- **Validation:**
  - $AC_0$: Preconditions check catches mismatched `task_id` (`ValueError`).
  - $AC_1$: Exact per-action deltas computed for ADR-002 pair (`approve_adr +0.03421`, `reject_adr -0.02867`, `request_revision_before_decision -0.03815`).
  - $AC_2$: Correctly classified as `progression` with margin delta `+0.07236`.
  - $AC_3$: CLI `task-policy-compare --sequence` runs end-to-end and outputs progression + deltas.
  - $AC_4$: Regression on counterfactual ADR-005 triggers per-criterion attribution (`consequences_honest`, `gap_disclosure_quality`) and `ESCALATE` once retry cap is hit, exiting 0.
  - $AC_5$: Stateless pure operations with 0 writes and 0 calls to `LearningStore`.
  - Full test suite: 433 passed, 2 skipped (non-Spark).

---

## Story 7.1 — Implement Paired Diff Classification & Escalation Pipeline
- **Commit:** `fe02610`
- **Date:** 2026-10-23
- **Branch:** `feat/story-7.1`
- **Source ADR / BRD / FDD:** ADR-007, BRD-007, FDD-007
- **Files Modified/Created:**
  - `src/agent_learning/governance.py` (governance change pipeline and 7-action taxonomy)
  - `src/agent_learning/decision.py` (added opt-in `audit_evidence` support to `DecisionResult` and `TaskPolicy.decide()`)
  - `src/agent_learning/__init__.py` (re-exported governance symbols)
  - `tests/test_governance.py` (contract tests encoding $AC_0$ through $AC_7$)
  - `tests/fixtures/governance/` (committed test fixtures: erratum, parameter, superseding, pending supersession, supersession update, tiebreak, and adversarial cases)
  - `.claude/skills/governance/SKILL.md` (component skill)
  - `docs/user-stories/epic-7-governance-change-paired-diff-classification-and-escalation.md` (status updated to Completed)
- **Validation:**
  - $AC_0$: Two-stage decoupled pipeline executes FULL classification (Bayesian) then LOW escalation (Softmax bandit).
  - $AC_1$: 7-Action taxonomy grouped across 3 operational tiers evaluated with 4 weighted criteria summing to 1.0.
  - $AC_2$: Ambiguity detection catches diffs within 0.05 margin, immediately returning `NEEDS_USER_TIE_BREAK` and halting without invoking escalation.
  - $AC_3$: Permanent Lineage Freeze hard-overrides `new_superseding_adr`, `pending_supersession_note`, and `supersession_update` to `escalate_to_human`, barring autonomous application.
  - $AC_4$: Classification context transported via ADR-006 `audit_evidence` envelope to `escalate-diff-response.decide()`.
  - $AC_5$: Autonomous updates (`apply_automatically`, `apply_with_notification`) emit immutable audit `Episode` record into store; zero silent changes.
  - $AC_6$: ADR-005 `compare_decision_results` gates baseline updates (+1.0 reward on progression, -1.5 penalty and escalation to human on regression).
  - $AC_7$: Adversarial safety test suite verifies red-team diffs (deleted constraints, inverted logic, removed guardrails, softened MUST, errata, parameter tweaks).
  - Full test suite: 443 passed, 2 skipped across entire agent-learning test suite. Zero regressions.

---

## Story 9.1 — Build Ingestion Scaffolding and Decision Envelope for PMBOK Intent Refinement
- **Commit:** `483fa46`
- **Date:** 2026-10-24
- **Branch:** `feat/story-9.1`
- **Source ADR / BRD / FDD:** ADR-008, BRD-008, FDD-008
- **Files Modified/Created:**
  - `src/agent_learning/pmbok/__init__.py` (top-level package exports)
  - `src/agent_learning/pmbok/models/__init__.py` (model subpackage exports)
  - `src/agent_learning/pmbok/models/intent_refinement.py` (pure dataclass domain models for Stages 1–6 and 18-stage metadata mapping)
  - `src/agent_learning/pmbok/decision.py` (decision envelope bridging PMBOK Stage 6 output to ADR-006 DecisionResult schema)
  - `src/agent_learning/__init__.py` (re-exported PMBOK symbols)
  - `tests/test_pmbok_intent_refinement.py` (contract tests encoding $AC_0$ through $AC_4$ and edge cases)
  - `.claude/skills/pmbok/SKILL.md` (component skill)
  - `docs/user-stories/epic-9-pmbok-intent-refinement-scaffolding.md` (status updated to Completed)
- **Validation:**
  - $AC_0$: Pure dataclass models instantiate valid instances across Stages 1–6; immutability preserved.
  - $AC_1$: Validation invariants catch negative budgets, malformed IDs, and missing mandatory fields.
  - $AC_2$: PMBOK Stage 6 `ApprovedScopeBaseline` maps to ADR-006 `DecisionResult` format with `audit_evidence` metadata.
  - $AC_3$: Policy versioning and stage metadata tracked with 100% fidelity to 18-stage ontology.
  - $AC_4$: Stateless execution with 0 disk writes and 0 calls to `LearningStore`.
  - Full test suite: 452 passed, 2 skipped across entire agent-learning test suite. Zero regressions.

---

## Story 9.2 — Implement Stages 7–18 Lifecycle State Validation and Phase Close Readiness Gate
- **Commit:** `a0e05da`
- **Date:** 2026-10-24
- **Branch:** `feat/story-9.2`
- **Source ADR / BRD / FDD:** ADR-009, BRD-009, FDD-009
- **Files Modified/Created:**
  - `src/agent_learning/pmbok/models/intent_refinement.py` (pure dataclass domain models for Stages 7–18, lifecycle transition validators, and `evaluate_phase_close_readiness()` pure function)
  - `src/agent_learning/pmbok/__init__.py` (re-exported symbols)
  - `src/agent_learning/__init__.py` (re-exported symbols)
  - `tests/test_pmbok_lifecycle_state.py` (contract tests encoding $AC_0$ through $AC_4$ and edge cases)
  - `.claude/skills/pmbok/SKILL.md` (updated component skill)
  - `docs/user-stories/epic-9-pmbok-intent-refinement-scaffolding.md` (status updated to Completed)
- **Validation:**
  - $AC_0$: Pure dataclass models instantiate valid instances across Stages 7–18 with frozen immutability.
  - $AC_1$: Validation invariants catch negative variance, unacknowledged risks, empty deliverables, and malformed identifiers.
  - $AC_2$: Hard stage gating verifies prerequisites across all lifecycle transitions.
  - $AC_3$: `evaluate_phase_close_readiness()` deterministically evaluates 5 readiness criteria, returning `PhaseCloseReadinessResult` with blocking gates.
  - $AC_4$: Stateless execution with 0 disk writes and 0 calls to `LearningStore`.
  - Full test suite: 452 passed, 2 skipped across entire agent-learning test suite. Zero regressions.

---

## Story 2.1 — Implement Optimistic Concurrency and Monotonicity Guard for Cosmos Active Pointer
- **Commit:** `61bf203`
- **Date:** 2026-10-25
- **Branch:** `feat/story-2.1`
- **Source ADR / BRD / FDD:** ADR-002 §4.5, BRD-002, FDD-002
- **Files Modified/Created:**
  - `src/agent_learning/storage/cosmos.py` (added enriched pointer schema, `_store_active_pointer()` with ETag conditional replace, 3-retry backoff loop, and monotonicity guard)
  - `.claude/skills/storage/SKILL.md` (created component skill documenting storage backend constraints, schema invariants, and concurrency rules)
  - `tests/test_storage_cosmos.py` (contract tests encoding $AC_0$ through $AC_4$ and edge cases)
  - `docs/user-stories/epic-2-cosmos-active-policy-optimistic-concurrency.md` (status updated to Completed)
- **Validation:**
  - $AC_0$: `CosmosStore.store_policy()` writes active pointer with `policy_version: policy.version` and `updated_at` in ISO 8601 UTC format.
  - $AC_1$: When an active pointer document exists with `policy_version > candidate.version`, pointer is not overwritten, warning is logged, and candidate snapshot ID is returned safely.
  - $AC_2$: Pointer update uses `replace_item` with `etag` and `MatchConditions.IfNotModified`; `CosmosAccessConditionFailedError` triggers re-read and retries up to 3 times (4 attempts total), raising on exhaustion.
  - $AC_3$: Initial pointer creation uses `create_item()`; racing creations raising `CosmosResourceExistsError` retry via the update path.
  - $AC_4$: `CosmosStore.get_active_policy()` correctly resolves active policies across both legacy (version-less) and enhanced pointer documents without regression.
  - Full test suite: 7/7 passed in `test_storage_cosmos.py`; 459 passed, 2 skipped across entire agent-learning test suite. Zero regressions.

---

## Story 10.1 — Implement Lessons Learned Register Parser, Validation Contract, and Phase Close Readiness Bridge
- **Commit:** `040841e`
- **Date:** 2026-10-25
- **Branch:** `feat/story-10.1`
- **Source ADR / BRD / FDD:** ADR-010, BRD-010, FDD-010
- **Files Modified/Created:**
  - `src/agent_learning/lessons_learned.py` (markdown parser, schema validator, and Phase Close readiness filter)
  - `src/agent_learning/__init__.py` (re-exported symbols)
  - `tests/test_lessons_learned.py` (contract tests encoding $AC_0$ through $AC_4$)
  - `.claude/skills/governance/SKILL.md` (updated component skill with Stage 15 breakout framing and propagation protocol)
  - `.claude/skills/implement-story/SKILL.md` (formalized breakout recap and lessons learned register into SIDPA lifecycle loop)
  - `docs/project-docs/Lessons-Learned-Register.md` (enclosed LL-001 through LL-006)
  - `docs/user-stories/epic-10-lessons-learned-crystallization-and-register.md` (status updated to Completed)
- **Validation:**
  - $AC_0$: `parse_lessons_learned_markdown()` extracts typed `LessonsLearnedEntry` instances with complete 8-field schema and serialized dictionary representation.
  - $AC_1$: Parser strictly validates schema completeness and identifier format (`LL-###`), raising `ValueError` on malformed IDs or missing required fields (`title`, `trap`, `root_cause`, `invariant`, `tier_targets`).
  - $AC_2$: `filter_crystallized_lessons()` filters entries by target Epic/Phase and supports explicit `no-new-lessons` phase sign-offs.
  - $AC_3$: Filtered payloads pass PMBOK 4.7 `evaluate_phase_close_readiness()` validation, contributing to `crystallized_lessons_count` and satisfying the Stage 15 hard gate.
  - $AC_4$: Active file verification confirms that the canonical repository register `docs/project-docs/Lessons-Learned-Register.md` parses cleanly with 100% compliance across `LL-001` through `LL-006`.
  - Full test suite: 5/5 passed in `test_lessons_learned.py`; 464 passed, 2 skipped across entire agent-learning test suite. Zero regressions.

## Story 11.1 — Route Records and the Human-Decision Invariants
- **Commit:** `516bdb3`
- **Date:** 2026-10-25
- **Branch:** `feat/story-11.1` (based on `docs/adr-011-tailoring-route-decision`, because ADR-011 and the Epic 11 specs are not yet on `main`)
- **Source ADR / BRD / FDD:** ADR-011, BRD-011, FDD-011
- **Files Modified/Created:**
  - `src/agent_learning/tailoring.py` (pure module: `Route`, `PlanRoute`, `PLAN_IDS`, `validate_route_set`, `to_episode_metadata`)
  - `src/agent_learning/__init__.py` (re-exported symbols)
  - `tests/test_tailoring.py` (contract tests encoding $AC_0$ through $AC_5$)
  - `.claude/skills/tailoring/SKILL.md` (new component skill)
  - `docs/user-stories/epic-11-project-tailoring-and-route-decision.md` (Story 11.1 status updated to Completed)
- **Validation:**
  - $AC_0$: only `full_plan`, `pmp_section` and `not_applicable` are accepted; any other value raises `ValueError`.
  - $AC_1$: `validate_route_set()` raises naming missing plan ids, and raises on duplicate or unknown ids.
  - $AC_2$: `not_applicable` with a blank reason raises `ValueError`.
  - $AC_3$: a decided route needs a human decider and a deciding role; a pending recommendation is valid.
  - $AC_4$: a decided route must record recommendation, basis and rationale; `to_episode_metadata()` returns both routes and a `diverged` flag.
  - $AC_5$: `tailoring.py` imports nothing from storage and returns a plain dict.
  - Contract: 11/11 passed in `test_tailoring.py` (10 for AC_0 to AC_5 plus 1 added from review). Full suite with `--ignore=tests/test_spark.py --ignore=tests/pmbok`: 475 passed, 2 skipped. **`tests/pmbok` cannot be collected from a clean install** (15 files; undeclared `sqlalchemy`/`tenacity`), a known pre-existing gap not touched by this story, so the suite as the skill specifies it does not run. The earlier 464 figure plus the original 10 tests equals 474, which suggests the earlier "entire suite" figure also excluded `tests/pmbok`.
  - Review (Q Developer, PR #7): no blocking defects. Two minor observations adopted: the decided-route check now gives separate messages for a missing recommended route and a blank basis (test added first, observed RED), and `diverged` compares with `!=`. A third (`DEFAULT_EPSILON` missing from `__all__` in `__init__.py`) is pre-existing and out of this story's scope.

## Story 11.2 — Flags That Never Block, and Integration-Section Home
- **Commit:** `74c49fb`
- **Date:** 2026-10-25
- **Branch:** `feat/story-11.2` (based on `feat/story-11.1`, which it extends; both sit on `docs/adr-011-tailoring-route-decision`)
- **Source ADR / BRD / FDD:** ADR-011, BRD-011, FDD-011
- **Files Modified/Created:**
  - `src/agent_learning/tailoring.py` (`Flag`, `HomeResolution`, `BASELINE_SUBSTANTIATING`, `INTEGRATION_ELEMENTS`, `compute_flags`, `resolve_home`)
  - `src/agent_learning/__init__.py` (re-exported symbols)
  - `tests/test_tailoring.py` (12 contract tests encoding $AC_0$ through $AC_4$, prefixed `s112_`)
  - `.claude/skills/tailoring/SKILL.md` (component skill updated)
  - `docs/user-stories/epic-11-project-tailoring-and-route-decision.md` (Story 11.2 status updated to Completed)
- **Validation:**
  - $AC_0$: each of cost, scope and schedule routed `not_applicable` raises one `baseline_plan_omitted` flag with message and evidence; none when they are at least a section; plans outside the set raise none.
  - $AC_1$: `compute_flags()` never raises for content (empty and partial sets included), and a flagged complete set still passes `validate_route_set()`.
  - $AC_2$: an accepted flagged route needs a rationale. This is already enforced by Story 11.1's rule for every decided route, so this test passes against that rule; Story 11.2 adds the flag codes to episode metadata.
  - $AC_3$: `resolve_home()` puts an element in the Charter if the Charter defines it, in the PMP if only the PMP does, and nowhere if neither; a differing PMP value is a conflict; a blank value is not "defined".
  - $AC_4$: both `element` and `section` granularities are implemented and tested, and an unknown granularity raises, so the ADR-011 open question is not pre-decided.
  - Implementation detail not stated in FDD-011 (FDD unchanged): `resolve_home` takes an optional `elements` argument defaulting to `INTEGRATION_ELEMENTS` (`type`, `routes`, `owners`) so that "neither defines it" can be reported as no home.
  - Contract: 25/25 passed in `test_tailoring.py` (23 original plus 2 added from review). Full suite with `--ignore=tests/test_spark.py --ignore=tests/pmbok`: 489 passed, 2 skipped. `tests/pmbok` still cannot be collected from a clean install (known pre-existing gap, see Story 11.1).
  - LL-007 check: grep found the module docstring still naming only Story 11.1; updated in the same change.
  - Review (Q Developer, PR #8): flagged three "logic errors". Adopted: `_defined` now treats blank strings and every empty container (tuple, set, frozenset as well as list and dict) as undefined; the test was added first and observed RED. Not adopted, with reasons: Q's claim that a section-mode conflict for a PMP-only element is a bug. ADR-011 Invariant 5 requires one home at a time, so a PMP value inside a Charter-held section is a second home and is flagged, not dropped; FDD-011 is silent on section-mode conflicts, so the meaning is now documented in the docstring and the component skill, and a test pins both the agreement and the stray cases. This is an interpretation of an open ADR question (whole section versus per element), recorded for the human to confirm.

## Epic 11 — Closure Record: Project Tailoring and Route Decision
- **Date:** 2026-10-25
- **Stories:** 11.1 (PR #7, commit `516bdb3`) and 11.2 (PR #8, commit `74c49fb`), both with Q Developer's review resolved. Nothing merged at the time of this record.
- **Governing chain:** ADR-011 (Accepted, episode `6c76db96-36b1-4796-a1dd-6325c6ef5208`) -> BRD-011, FDD-011, Epic 11 stories (all Approved through `approve-brd`, `approve-fdd`, `approve-user-stories`).
- **Traceability, from decision to green contract** (contracts in `tests/test_tailoring.py`, code in `src/agent_learning/tailoring.py`, component skill `.claude/skills/tailoring/SKILL.md`):

| ADR-011 decision / invariant | BRD-011 | FDD-011 element | Story AC | Contract tests (name fragment) | Code |
|---|---|---|---|---|---|
| D1 route per plan, human decides; Inv 1 human decides, Inv 2 no silent omission | BRU-011-01, 02 | `Route`, `PlanRoute`, `validate_route_set` | 11.1 AC_0 to AC_3 | `ac0_route_shape`, `ac1_*` (3), `ac2_not_applicable_needs_a_reason`, `ac3_*` (2) | `Route`, `PlanRoute`, `validate_route_set` |
| D2 flags not blocks, both sides recorded; Inv 3 recorded as `Episode` | BRU-011-03, 04 | `compute_flags`, `to_episode_metadata`, `Flag` | 11.1 AC_4; 11.2 AC_0 to AC_2 | `ac4_*` (3), `s112_ac0_*` (3), `s112_ac1_*`, `s112_ac2_*` (2) | `compute_flags`, `to_episode_metadata`, `Flag`, `BASELINE_SUBSTANTIATING` |
| D3 Charter sets limits, integration section home; Inv 5 one home, Charter prevails | BRU-011-05 | `resolve_home`, `HomeResolution` | 11.2 AC_3, AC_4 | `s112_ac3_*` (4), `s112_ac4_*` (4) | `resolve_home`, `HomeResolution`, `INTEGRATION_ELEMENTS` |
| Storage boundary (ADR-002 Invariant #2); Inv 3 | BRU-011-06 | module purity, section 1 | 11.1 AC_5 | `ac5_storage_boundary_*` | module imports no storage; metadata is a plain dict |
| D4 changes follow the cycles (Stage 17 / 18); D5 remedial breakouts; Inv 4 profile, standard and limits declared by humans | none in this epic | none | none | none | **Deferred by design**: Charter template and checks, plan standards, gates, learners, route-aware orchestration (see Out of Scope in BRD, FDD and epic) |

- **Skills touched:** `.claude/skills/tailoring/SKILL.md` (new, updated for 11.2); `.claude/skills/implement-story/SKILL.md` (Tier 2 propagation of LL-010, LL-011 and LL-013 into Steps 0, 1, 3 and 6); `.claude/skills/tailoring/SKILL.md` also carries LL-014. Governance and learner skills unchanged.
- **Code amendments:** `src/agent_learning/tailoring.py` (new) and `src/agent_learning/__init__.py` (re-exports only). No existing behavior changed.
- **Confirmation that the contracts are green** (run on `feat/story-11.2`, 2026-10-25):
  - `tests/test_tailoring.py`: 25 passed (11 for Story 11.1, 14 for Story 11.2). `tests/test_lessons_learned.py`: 5 passed with the register now at `LL-001` to `LL-014`. Together 30 passed.
  - Suite with `--ignore=tests/test_spark.py --ignore=tests/pmbok`: **489 passed, 2 skipped**.
  - **Not covered:** `tests/pmbok` (15 files) cannot be collected from a clean install (undeclared `sqlalchemy` and `tenacity`), and `tests/test_spark.py` needs a JVM. "All contracts green" therefore means every contract that can currently run, not the PMBOK contracts (LL-010).
- **Breakout recap (ADR-010 section 4.1):** held, with the lessons drawn from how the ADR, BRD, FDD, stories, skills and code related. Recorded as `LL-008` to `LL-014` in `docs/project-docs/Lessons-Learned-Register.md`: keep only hardened decisions in an ADR (008), verify the edition of a cited standard (009), implement only against approved and committed specs (010), state every mode and parameter in the FDD (011), state each rule in one story's acceptance criteria (012), keep a skill's validation command one that runs (013), and define blank once and test every container type (014). These replace a first, narrower draft of three lessons (numbered `LL-008` to `LL-010` in that draft), revised after review of the recap.
- **Open for a human:** the section-mode conflict interpretation of `resolve_home` (whole section versus per element, ADR-011 open question); the merge order of the stacked PRs (docs branch, #7, #8).

---

## Correction to Story 2.1 — commit identifiers
- **Date:** 2026-10-26
- **Corrects:** the `Commit` line of the Story 2.1 entry above, which records `61bf203`.
- **Finding:** `61bf203` is the pre-amend commit and is not in `main`. The amend (`git commit --amend`) produced `7d374a1`, and the backfill recorded the old hash. The two commits differ only in `implementation-log.md`.
- **Commits that reached `main` through PR #4 (merge `72e5f14`):**
  - `7d374a1` — `feat(storage): implement optimistic concurrency and monotonicity guard for Cosmos active pointer (Story 2.1)` (the implementation commit this entry meant)
  - `188ed8a` — `fix(storage): strip system fields from replace_item and address review feedback` (cited by LL-001 to LL-004)
  - `370b858` — `chore(tests): remove unused MagicMock and cosmos_mod imports`
- **Validation re-run on 2026-10-26** (branch `docs/adr-028-pmbok-convergence`): `tests/test_storage_cosmos.py` 7 passed; suite with `--ignore=tests/test_spark.py --ignore=tests/pmbok` 490 passed, 2 skipped. The 459 count in the original entry reflects the suite at that time.
- **The original entry is unchanged**, per the append-only rule.


---

## Story 3.1 — Build Tier-Specific Environment Overrides and Authority-Aware Autonomy Reporting
- **Commit:** `759600f`
- **Date:** 2026-10-26
- **Branch:** `feat/story-3.1`
- **Source ADR / BRD / FDD:** ADR-003 (sections 3, 4.3, 4.5, 6, 7), BRD-003, FDD-003
- **Files Modified/Created:**
  - `src/agent_learning/config.py` (tier-aware `_env_tier_int` / `_env_tier_float`, `AutonomyConfig.for_tier` resolves tier variable, then global, then default; `validate_autonomy_monotonicity()`)
  - `src/agent_learning/autonomy.py` (`assess_autonomy()` validates monotonicity when it builds its own config; full-authority policies report `action_probability` and `probability_margin` as `not_applicable` with `authorization_basis="human_adjudication"`)
  - `tests/test_autonomy.py` (Story 3.1 contract section appended; 17 new tests, 33 in the file)
  - `.claude/skills/autonomy/SKILL.md` (new component skill)
  - `docs/decision-making.md` (tier-suffix variables, monotonicity and full-authority reporting documented)
  - `docs/user-stories/epic-3-tier-specific-autonomy-overrides.md` (status updated to Completed)
- **Validation:**
  - $AC_0$ and $AC_1$: `AGENT_LEARNING_AUTONOMY_{METRIC}_{TIER}` beats the global variable, which beats the tier default; `MIN_OUTCOMES_LOW=5` yields 5, 20, 50, 100 across the four tiers.
  - $AC_2$: `validate_autonomy_monotonicity()` raises `ValueError` naming the metric and both tiers for each of the six gates; defaults and equal thresholds pass.
  - $AC_3$: full-authority policies report the two probability criteria as `not_applicable` with `met=True`, `required=None` and a reason citing ADR-003; `authorization_basis` is `human_adjudication`.
  - $AC_4$: low-authority policies keep numeric `required` values and no `status` key, and the existing autonomy tests pass unchanged.
  - Observed RED first: 14 of the new tests failed before implementation (run with a temporary no-op stub of the validator, since the module could not otherwise be imported); the rest were regression guards that already passed.
  - Story contract: `tests/test_autonomy.py` 33 passed.
  - Full suite with `--ignore=tests/test_spark.py --ignore=tests/pmbok`: **507 passed, 2 skipped**. Not covered: `tests/pmbok` (15 files) cannot be collected from a clean install (undeclared `sqlalchemy` and `tenacity`) and `tests/test_spark.py` needs a JVM, so this is not the entire suite (LL-013).
  - `ruff check` on the three touched Python files reports 12 findings, the same 12 as before the change (existing `UP045`, `UP037`, `RUF022`).
- **Interpretations not stated verbatim in the acceptance criteria (LL-011), recorded in the test header:**
  - I1: an unparseable tier-suffixed value falls through to the global variable, then the default, as the existing `_env_int` does (FDD-003's sketch would raise).
  - I2: the monotonicity check covers all six statistical gates (ADR-003 Invariant 5), not only the three in FDD-003 Design 2. `audit_rate` is excluded (ADR-003 4.3).
  - I3: `assess_autonomy()` runs the check when it resolves its own config; a config passed in explicitly is not re-validated.
  - I4: for a full-authority policy, eligibility comes only from explicit acceptance and `requires_human_approval`; the frozen-logit statistical path no longer grants autonomy. This is a behavior change for full-authority policies and is the reading of FDD-003 Design 3, item 4.
- **Open for a human:** whether FDD-003 should be amended to record I1 to I4 (FDD-003 is approved, so the amendment needs its own approval).
- **Review (Step 8):** Amazon Q round 1 raised one finding, `Q-11-1 | crash risk | verified: yes | decision: accepted | _note_global_override read the global variable twice, so a variable removed between the two reads could raise KeyError | fix: 6a92064`. An explicit verdict was then requested on the head commit; the reply is on PR #11.
- **Breakout recap (ADR-010 section 4.1):** held 2026-10-26 after the PR review. Two lessons drafted and accepted by the maintainer: `LL-020` (read a mutable global once, from Q-11-1) and `LL-021` (read a posted command back before trusting a reply, from the `/q` path trap on PRs #10 to #12). Tier 2 targets updated in the autonomy and implement-story skills; Tier 3 proposed, not applied.

---

## Story 36.1 — The Catalog and Its Integrity Check
- **Commit:** `bc467cc`
- **Date:** 2026-10-26
- **Branch:** `feat/story-36.1`
- **Source ADR / BRD / FDD:** ADR-036 (section 4.1, Invariants 1 to 3), BRD-036 (BRU-036-01, BRU-036-08), FDD-036 (sections 1, 2.1)
- **Files Modified/Created:**
  - `src/agent_learning/methodology_catalog.py` (new: `CatalogEntry`, `ExampleClass`, `derive_class`, `parse_catalog`, `validate_catalog`; pure, no file I/O or storage)
  - `src/agent_learning/__init__.py` (re-exports only)
  - `examples/methodologies/catalog.json` (the 32 entries: 9 runnable, 10 proof_of_concept, 13 documented)
  - `tests/test_methodology_catalog.py` (31 tests) and `tests/fixtures/methodology_catalog/ideation_states.json`
  - `.claude/skills/methodology-catalog/SKILL.md` (new component skill)
  - `docs/user-stories/epic-36-...md` (Story 36.1 status updated to Completed)
- **Validation:**
  - $AC_0$: `validate_catalog()` raises `ValueError` naming a missing, duplicate or out-of-range id; the shipped catalog covers 1 to 32 once each.
  - $AC_1$: `derive_class()` maps every state per FDD-036 section 2.1, an unknown state raises, and an entry whose class or state differs from the derived class or the fixture raises, naming the id.
  - $AC_2$: a documented entry with an empty `reason` or `reopening_condition` raises.
  - $AC_3$: a path outside `examples/methodologies/` (including a `..` path) raises; a missing path for a runnable or proof_of_concept entry raises; with `existing_paths` a listed path that is absent raises.
  - $AC_4$: an AST test confirms the module imports nothing from `agent_learning.storage` and none of `os`, `pathlib`, `io`, `shutil`.
  - Observed RED first: collection failed without the module; with a throwaway stub (since removed) 27 of the 31 tests failed on behavior and 4 already passed as guards.
  - Story contract: `tests/test_methodology_catalog.py` 31 passed. One test regex (`outside` before the id) over-specified the message order and was corrected; the module was not bent to it.
  - Full suite with `--ignore=tests/test_spark.py --ignore=tests/pmbok`: **521 passed, 2 skipped**. Not covered: `tests/pmbok` (undeclared `sqlalchemy` and `tenacity`) and `tests/test_spark.py` (needs a JVM), so this is not the entire suite (LL-013).
  - `ruff check` on the two new Python files: all checks passed.
- **Interpretations not stated verbatim in the acceptance criteria (LL-011), recorded in the test header:**
  - I1: the module does no file I/O (FDD-036 section 1), so AC_3's existence check takes an `existing_paths` set from the caller; `None` skips it, because the example directories are built by Stories 36.2 and 36.3.
  - I2: the catalog `state` uses canonical tokens, and the expected states are a hand-transcribed fixture of Ideation section 2.1 (v1.13). Drift between the fixture and the Ideation table is not detected automatically.
  - I3: a candidate with a Proposed ADR is a proof_of_concept even when the Ideation notes a data prerequisite (#23); #29 is a candidate with no ADR, so it is documented.
- **Open for a human:** FDD-036 is approved, so recording I1 (the optional `existing_paths` argument) and I2 (canonical state tokens) there needs its own approval.
- **Review (Step 8):** Amazon Q round 1 reviewed head `1168f03` and reported no merge-blocking defect and no inline finding (findings: 0 accepted, 0 declined, 0 deferred). The explicit verdict round on head `774d298` confirmed all five acceptance criteria and raised one item: `Q-14-1 | documentation | verified: no | decision: declined | validate_catalog is already in __all__ (src/agent_learning/__init__.py line 301; agent_learning.__all__ contains it) | fix: none`. Q then confirmed `validate_catalog` is in `__all__` and that no blocking defect remained at head `9f59748` ("No code change is required to unblock merging this PR"). Its remaining items were recorded as: `Q-14-2 | documentation | verified: yes | decision: declined | DEFAULT_EPSILON is imported but not in __all__; already so on main and not in this diff, so out of scope | fix: none`; `Q-14-3 | documentation | verified: yes | decision: declined | get_capture exists in capture.py, informational only | fix: none`; and two known items already stated in the PR (the suite paths that cannot run, and I1 and I2 awaiting an FDD-036 approval cycle).


---

## Story 36.2 — Runnable Examples for What Exists
- **Commit:** `66e3bcc`
- **Date:** 2026-10-26
- **Branch:** `feat/story-36.2`
- **Source ADR / BRD / FDD:** ADR-036 (section 4.2, Invariants 1 and 3), BRD-036 (BRU-036-02, BRU-036-03), FDD-036 (sections 1, 3 item 6)
- **Files Modified/Created:**
  - `examples/methodologies/{02-reinforce-bandit,03-reasoned-resolution,04-contextual-bandit,05-reward-shaping,06-human-override,12-active-evidence-seeking,19-red-team-validation,20-diff-classification,21-category-escalation}/` (each: `README.md`, `example.py`)
  - `tests/test_methodology_examples.py` (48 tests)
  - `.claude/skills/methodology-catalog/SKILL.md` (examples section added)
  - `docs/user-stories/epic-36-...md` (Story 36.2 status updated to Completed)
- **Validation:**
  - $AC_0$: each of the nine runnable entries has `README.md` and `example.py`, and the runnable ids in the catalog are exactly these nine.
  - $AC_1$: every script header carries STATUS, CODE, `DATA: SYNTHETIC`, the Ideation row, ADR, hypothesis and `NOT EVIDENCE`; every README has Falsification and Real data needed sections.
  - $AC_2$: each script exits 0 offline in an empty temporary directory (all nine in about 15 seconds) and writes no file.
  - $AC_3$: no script names `LocalFileStore`, `CosmosStore` or `get_default_store` or imports a network or cloud client; nothing under `src/` imports from `examples/`; the catalog file is byte-identical after running all nine.
  - Observed RED first: 46 of 48 tests failed before the examples existed; the 2 that passed (the nine-ids check and the no-import-from-`src` check) are guards.
  - Story contract: `tests/test_methodology_examples.py` 48 passed.
  - Full suite with `--ignore=tests/test_spark.py --ignore=tests/pmbok`: **586 passed, 2 skipped**. Not covered: `tests/pmbok` (undeclared `sqlalchemy` and `tenacity`) and `tests/test_spark.py` (needs a JVM), so this is not the entire suite (LL-013).
  - `ruff check` on `examples/methodologies` and the new test file: all checks passed.
- **Interpretations not stated verbatim in the acceptance criteria (LL-011), recorded in the test header:**
  - I1: "runs offline" is tested by running each script in an empty temporary directory with a time limit, plus a scan for network and cloud imports; absence of network access cannot be proven by the test.
  - I2: "leaves the real store unchanged" is tested statically (no durable store named) plus an empty working directory after the run.
  - I3: the falsification criterion and the real data needed are tested in the README, where ADR-036 section 4.2 places them. For methodologies with no registered hypothesis (#5, #6, #12, #19) the README states a proposed criterion and says so.
- **Found, not fixed (outside this story):** `examples/quickstart.py` and `examples/next_best_action.py` build episodes without `intent_summary`, `expected_outcome`, `execution_status` and `result_summary`, so `Episode.is_full` is false and the learner uses zero episodes (quickstart prints "Episodes used: 0" and unchanged probabilities); `next_best_action.py` also needs PyYAML, which is not a declared dependency. The new examples build complete episodes and do not use either file.
- **Open for a human:** whether to fix or retire the two older examples (a separate change); and the proposed falsification criteria for #5, #6, #12 and #19 are authored here, not in the Ideation Document.
- **Review (Step 8):** Amazon Q round 1 reviewed head `16577a7` (two reviews, two inline findings, no defect in the example scripts):
  - `Q-15-1 | test gap | verified: yes | decision: accepted | check=True in the catalog-unchanged test raised before the hash assertion, hiding which script failed | fix: 5048fe2`
  - `Q-15-2 | crash risk | verified: yes | decision: accepted with modification | ast.parse of src files could crash the test with a bare SyntaxError; Q suggested skipping the file, which would hide a broken file, so the test fails with the path and error instead | fix: 5048fe2`
  - `Q-15-3 | test gap | verified: yes | decision: accepted | the same unguarded ast.parse on the example scripts and in the header helper; one _parse helper now covers all three | fix: 5048fe2`
  - `Q-15-4 | style | verified: yes | decision: accepted | the 120 s per-script timeout is generous for scripts that take about 2 s; now 60 s | fix: 5048fe2`
  - `Q-15-5 | test gap | verified: yes | decision: declined | the static scan cannot catch dynamic network calls (os.system and similar); this is interpretation I1, stated in the test header and the PR | fix: none`
  An explicit verdict on the final head was then requested; the reply is on PR #15.


---

## Story 36.3 — Proof-of-Concept Sketches for the ADR-Backed Candidates
- **Commit:** `55ea011`
- **Date:** 2026-10-26
- **Branch:** `feat/story-36.3`
- **Source ADR / BRD / FDD:** ADR-036 (section 4.2), ADR-014 to ADR-023 (formulas sketched), BRD-036 (BRU-036-02), FDD-036
- **Files Modified/Created:**
  - `examples/methodologies/{08-critique-to-evidence,09-thompson-sampling,10-ucb,11-epsilon-greedy,13-pairwise-preference,14-meta-learning,15-warm-start,17-authority-routing,22-scored-search,23-dueling-bandit}/` (each: `README.md`, `sketch.py`)
  - `tests/test_methodology_sketches.py` (53 tests)
  - `.claude/skills/methodology-catalog/SKILL.md` (section 6 added)
  - `docs/user-stories/epic-36-...md` (Story 36.3 status updated to Completed)
- **Validation:**
  - $AC_0$: each of the ten entries has `README.md` and `sketch.py` and is `proof_of_concept` in the catalog; the proof-of-concept ids are exactly these ten.
  - $AC_1$: each header carries `STATUS: proof_of_concept`, `CODE: sketch`, `DATA: SYNTHETIC`, the Ideation row, ADR, hypothesis and `NOT EVIDENCE`.
  - $AC_2$: each sketch runs in an empty temporary directory with a fixed seed, exits 0, writes no file, names no durable store and imports no network or cloud client; standard library only.
  - $AC_3$: each README has Falsification and Real data needed sections. Quoted from the registered hypothesis for #8, #9, #10, #15, #22, #23.
  - $AC_4$: the catalog file is byte-identical after running all ten.
  - Observed RED first: 51 of 53 tests failed before the sketches existed (the 2 guards passed). One sketch (#17) then failed its own hysteresis assertion (my example input had entropy below the floor); fixed the input, not the assertion.
  - Full suite with `--ignore=tests/test_spark.py --ignore=tests/pmbok`: **639 passed, 2 skipped**. Not covered: `tests/pmbok` and `tests/test_spark.py` (LL-013).
  - `ruff check` on `examples/methodologies` and the new test: all checks passed.
- **Interpretations not stated verbatim in the acceptance criteria (LL-011):**
  - I1: the test docstrings label the offline / no-store check as AC_2 and the README check as AC_3 following the Story text; the same I1 limits as Story 36.2 apply (network absence is not provable, only scanned).
  - I2: sketches are plain stdlib Python of the ADR formulas; they do not import `agent_learning`, so "the public SDK only" holds trivially.
  - I3: for #11, #13, #14 and #17 no hypothesis is registered; the README states a criterion proposed there and says so. Those four criteria are authored here, not in the Ideation Document.
  - I4: a sketch asserts only its own arithmetic (a clamp, a band, an ordering of invented data); this checks the sketch, not the methodology.
- **Open for a human:** the four proposed criteria (#11, #13, #14, #17) need review; whether #11 and #17 should get Ideation hypotheses.
- **Review (Step 8):** Amazon Q round 1 reviewed head `146a0b1` (two reviews, four distinct findings, all in the test file, none in the sketches); round 2 reviewed `4e891a9`; then an explicit verdict.
  - `Q-16-1 | logic | verified: yes | decision: accepted | the forbidden-import check missed relative imports (from . import requests) because node.module is None; aliases of ImportFrom nodes are now checked too | fix: 4e891a9`
  - `Q-16-2 | style | verified: yes | decision: declined | implicit None return from _parse; pytest.fail never returns, an unreachable raise adds noise | fix: none`
  - `Q-16-3 | crash risk | verified: yes | decision: declined | rglob on a missing src/ raises on Python 3.12+; src/ is part of this repository and a missing src/ should fail loudly | fix: none`
  - `Q-16-4 | logic | verified: yes | decision: declined | claimed a double backslash in the ADR and HYPOTHESIS regexes; the file has one backslash per line (counted), the pattern matches a real header; Q repeated it in round 2 and retracted it after the evidence | fix: none`
  - Verdict on `4e891a9`: Q replied "No further additions" (after one command that Q did not answer because /q was not at the start of the comment; the second, starting with /q, was answered).


---

## Story 36.4 — The Best-Practice Ledger
- **Commit:** `4761f63`
- **Date:** 2026-10-26
- **Branch:** `feat/story-36.4`
- **Source ADR / BRD / FDD:** ADR-036 (section 4.3, Invariants 4 and 5), BRD-036 (BRU-036-04), FDD-036 (sections 2.2 and 3 item 2)
- **Files Modified/Created:**
  - `src/agent_learning/methodology_ledger.py` (new; `parse_ledger`, `current_entries`, `LedgerEntry`), exported in `__init__.py`
  - `docs/project-docs/Methodology-Best-Practice-Ledger.md` (new register, four candidate entries)
  - `tests/test_methodology_ledger.py` (25 tests)
  - `.claude/skills/methodology-catalog/SKILL.md` (section 7 added; stale pending note updated)
  - `docs/user-stories/epic-36-...md` (Story 36.4 status updated to Completed)
- **Validation:**
  - $AC_0$: an unknown enumeration value, an unknown methodology id, an unknown or missing field, a duplicate id and a bad evidence count each raise `ValueError` naming the entry.
  - $AC_1$: `adopted` on `source-doc` or `synthetic-demo` raises; `adopted` below the declared tier gate raises and at the gate parses (standard 20, low 3); `adopted` without a tier raises.
  - $AC_2$: a status change is a new entry with `supersedes`; an unknown, forward-pointing, cross-methodology or already-superseded target raises; `current_entries` returns the chain tails.
  - $AC_3$: link format is always checked; resolution is checked when `known_links` is passed, and the real-register test passes the LL ids from the Lessons Learned Register and the HYP-AL ids from the Ideation Document.
  - $AC_4$: an AST test shows the module imports nothing from storage and no file-I/O modules.
  - Observed RED first: the test module failed at collection (no module); 25 passed after.
  - Full suite with `--ignore=tests/test_spark.py --ignore=tests/pmbok`: **664 passed, 2 skipped**. Not covered: `tests/pmbok` and `tests/test_spark.py` (LL-013).
  - `ruff check` on the new module and test: clean. `__init__.py` has 3 findings (import order, unused `DEFAULT_EPSILON`, unsorted `__all__`) that exist on main; not touched here.
- **Interpretations not stated verbatim in the acceptance criteria (LL-011), recorded in the test header:**
  - I1: link resolution takes the known identifiers from the caller (the module does no file I/O).
  - I2: "the declared tier" is a `tier` field on the entry, required when adopted; the gate is `AutonomyConfig.for_tier(tier).min_outcomes`, so an environment override applies as it does to autonomy. The FDD dataclass does not list `tier`; it is added.
  - I3: a superseding entry must come after its target, concern the same methodology, and be the only one to supersede it.
  - I4: append-only (never edit) is a file maintenance rule guarded by git history; the parser cannot see it, so it is not tested.
  - I5: an empty register is valid.
- **Seed entries:** BP-001 to BP-004 are `candidate` on `source-doc` evidence with `evidence_count: 0`, each tied to a registered hypothesis or LL entry. They state practices already written in the Ideation Document and LL-004; I authored the wording of the practice and preconditions, which a human should review. Nothing is adopted, because no real episodes of a methodology exist.
- **Open for a human:** FDD-036 section 2.2 should gain the `tier` field (an amendment, not made here); whether BP-004 belongs under #6 (human override) or another catalog id.
- **Review (Step 8):** Amazon Q round 1 reviewed head `546caba` (two reviews, five distinct findings); round 2 reviewed `45455cd`; then an explicit verdict.
  - `Q-17-1 | test gap | verified: yes | decision: accepted | the tests hard-coded the tier gates (19/20, 3) although the gates are environment-overridable; they now read AutonomyConfig.for_tier(tier).min_outcomes and pass with a standard-gate override set | fix: 45455cd`
  - `Q-17-2 | logic | verified: yes | decision: accepted with modification | a required field written empty was reported as missing; a key-presence test would accept an empty practice, so the check stays and the message says missing or empty, pinned by a test | fix: 45455cd`
  - `Q-17-3 | logic | verified: yes | decision: declined | claimed any ## heading truncates an entry body; that is intended (a following non-entry section is prose), and the suggestion would parse its bullets as fields of the entry above; a test pins the behavior | fix: 45455cd (test only)`
  - `Q-17-4 | style | verified: yes | decision: declined | DEFAULT_EPSILON missing from __all__ in __init__.py; exists on main, outside this story | fix: none`
  - `Q-17-5 | test gap | verified: yes | decision: declined | purity test does not cover indirect I/O through config; config.py imports only logging, os, dataclasses and typing, and AC_4 is about storage | fix: none`
  - Verdict on `45455cd`: Q replied "No" to further additions, with no new findings. The first reply to an earlier verdict request is the command that began with /q; the lesson from PR #16 held (/q at the start of the comment).


---

## Story 36.5 — The Review-Triage Learning Loop
- **Commit:** `a7eea8f`
- **Date:** 2026-10-26
- **Branch:** `feat/story-36.5`
- **Source ADR / BRD / FDD:** ADR-036 (section 4.5, Invariants 6 and 7), BRD-036 (BRU-036-05 to BRU-036-07), FDD-036 (sections 2.3, 2.4, 3 items 3 to 5)
- **Files Modified/Created:**
  - `src/agent_learning/review_triage.py` (new; `TriageRecord`, `Reliability`, `parse_triage_line`, `reconstruct_record`, `find_triage_lines`, `to_episode_metadata`, `reliability`); all but `to_episode_metadata` re-exported from `__init__.py`
  - `docs/policy-shapes/{triage-review-finding,route-review-finding}.{actions,profile}.json` (four new files)
  - `tests/test_review_triage.py` (29 tests)
  - `.claude/skills/methodology-catalog/SKILL.md` (section 8 added)
  - `docs/user-stories/epic-36-...md` (Story 36.5 status updated to Completed)
- **Validation:**
  - $AC_0$: a valid line parses; a claim type, verified or decision value outside its vocabulary raises naming the field and value; `unknown` is accepted; a malformed line and an unknown reviewer initial raise. All 15 backticked triage lines already in this log parse.
  - $AC_1$: `to_episode_metadata` returns a plain, JSON-serializable dict; an AST test shows the module imports nothing from a storage module directly.
  - $AC_2$: `reliability` equals `wilson_lower_bound(verified, cases, z)`, excludes `unknown`, counts `partial` as not verified, filters by reviewer and claim type, and gives `lower_bound = None` below `min_cases` (and with no cases).
  - $AC_3$: `reconstruct_record` sets `reconstructed = True`, leaves every field not given as `unknown`, still rejects a value outside the vocabulary, and adds no case to the reliability.
  - $AC_4$: the triage shape lists exactly the three actions and its profile loads with `ComplexityProfile.from_dict` with `requires_human_approval` true.
  - $AC_5$: the routing shape lists only the three verification-order actions (no accept or decline), its profile loads, and the two shapes share no action.
  - $AC_6$: every record's decision is unchanged after `reliability` and `to_episode_metadata`; records are frozen.
  - The tests were written first; the module did not exist at that point, so the first run was after the module was written (29 passed). A RED run was not recorded this time.
  - Full suite with `--ignore=tests/test_spark.py --ignore=tests/pmbok`: **695 passed, 2 skipped**. Not covered: `tests/pmbok` and `tests/test_spark.py` (LL-013).
  - `ruff check` on the new module and test: clean.
- **Interpretations not stated verbatim in the acceptance criteria (LL-011), recorded in the test header:**
  - I1: reviewer and PR come from the finding id; the initial maps to a reviewer name through a table (Q is amazon-q); an unknown initial raises.
  - I2: two spellings the log already uses are read into the FDD vocabulary: `logic` as `logic error`, `accepted with modification` as `accepted` with `(with modification)` put in front of the reason.
  - I3: a backfilled record is one built by `reconstruct_record`.
  - I4: the module imports `wilson_lower_bound` from `agent_learning.autonomy` (as the FDD says), and that module imports storage; AC_1 is tested on the module's own imports.
  - I5: "nothing sets the decision" is tested by value and by frozen dataclasses.
  - I6: profiles: triage is medium impact and reversible with human approval true; routing is low impact and reversible with no approval flag.
  - I7: `to_episode_metadata` is not re-exported from the package root, because `agent_learning.to_episode_metadata` already is the tailoring function.
- **Not done (by design):** the two shapes are declared, not initialized. The maintainer runs `task-policy-init` for each (triage with `full` authority, routing with `low`). No backfill of earlier stories was run: the log already holds 15 complete records in the fixed shape, and no field was reconstructed.
- **Open for a human:** whether to initialize the two policies now or after Story 36.6; the profile values in I6 are my choice.
- **Review (Step 8):** Amazon Q round 1 reviewed head `706a308` (two reviews, no inline finding, no merge-blocking defect; findings: 0 accepted, 0 declined, 0 deferred). A standalone `/q` command then asked for an explicit verdict, and Q replied "No" to further additions on `706a308`.


---

## Story 36.6 — Tailoring for the Store and Lessons Learned, and Template Propagation
- **Commit:** `44888b7` (agent-learning); `2581b0c` (sidpa-template, branch `feat/upgrade-from-agent-learning-2026-10`, local, not pushed)
- **Date:** 2026-10-26
- **Branch:** `feat/story-36.6`
- **Source ADR / BRD / FDD:** ADR-036 (section 4.4, Invariant 4), BRD-036 (BRU-036-09), FDD-036 (section 1); ADR-010 (epic-end recap)
- **Files Modified/Created (agent-learning):**
  - `docs/project-docs/Methodology-Tailoring-Matrix.md` (new; six pairings, all `hypothesis`)
  - `docs/project-docs/Methodology-Best-Practice-Ledger.md` (BP-005 to BP-009 appended, all `candidate`)
  - `docs/project-docs/Lessons-Learned-Register.md` (LL-016 to LL-019: the Epic 36 recap)
  - `tests/test_methodology_tailoring_matrix.py` (8 tests)
  - `.claude/skills/methodology-catalog/SKILL.md` (section 9; stale pending note replaced), `.claude/skills/implement-story/SKILL.md` (Step 8.1 and 8.2: `--repo`, `/q` first)
  - `src/agent_learning/methodology_catalog.py` (one stale comment reworded), `docs/user-stories/epic-36-...md` (Story 36.6 Completed)
- **Files Created/Modified (sidpa-template):** `docs/methodologies/{catalog.json,Tailoring-Matrix.md,README.md}`, `docs/registers/Methodology-Best-Practice-Ledger.template.md` (empty), `scripts/init_project.py` (scaffolds the ledger in the `start` stage), `README.md`, `docs/learning-methodology.md`, `tests/test_template_integrity.py` (3 tests, plus a scaffold assertion)
- **Validation:**
  - $AC_0$: each of the six rows names catalog ids that exist, `Applies to` of `store` or `lessons-learned`, a falsification criterion, hypotheses that exist in the Ideation Document, and is marked `hypothesis`.
  - $AC_1$: each row's `Ledger` is a current `candidate` entry about one of the row's methodologies; no ledger entry is adopted.
  - $AC_2$: the catalog, the matrix, the ledger template and the labeling contract are in `sidpa-template`; its integrity tests pass (**21 passed**, run with `uv run --no-project --with pytest`; 18 before, 3 added).
  - $AC_3$: the Epic 36 recap is recorded as LL-016 to LL-019 in the Lessons Learned Register and indexed; a test checks that an entry names Epic 36 and appears in the index.
  - Full suite with `--ignore=tests/test_spark.py --ignore=tests/pmbok`: **703 passed, 2 skipped**. Not covered: `tests/pmbok` and `tests/test_spark.py` (LL-013).
  - `ruff check` on the new test and the touched module: clean. A RED run was not recorded for the matrix test (the recap test failed only until the LL entries were added; not captured).
- **Interpretations not stated verbatim in the acceptance criteria (LL-011), recorded in the test header:**
  - I1: the matrix is a Markdown table parsed by the test; no module is added.
  - I2: "links to a candidate ledger entry" means the entry exists, is current, is `candidate`, and concerns one of the row's methodology ids.
  - I3: "a need for the store or lessons learned" is the `Applies to` column.
  - I4: AC_2 spans two repositories and is verified by running the template's tests, recorded here, not by a test in this repository.
  - I5: AC_3 is checked by an entry naming Epic 36 and its index row.
  - I6: five new `candidate` ledger entries (BP-005 to BP-009) were needed so that each pairing has a ledger link; BP-002 backs the #9/#10 pairing. Their wording of the practice is mine, from the hypotheses in the Ideation Document; one (BP-008) is `synthetic-demo` evidence, pointing at the sketch.
  - I7: the template's matrix leaves the `Ledger` column as "add a candidate entry first", and its ledger ships empty, because the template stores only template values and the hypothesis ids do not exist there.
- **Recap (ADR-010):** four lessons crystallized: LL-016 (a review command must start its own comment), LL-017 (a package-root re-export can shadow an existing name), LL-018 (name the target repository on every PR command), LL-019 (evidence must be unambiguous in its own representation). Tier 2 targets are updated in this PR (implement-story Step 8, methodology-catalog skill). Tier 3 targets are proposed, not applied.
- **Not done:**
  - The template branch is not pushed, and the template's `implement-story` skill does not yet carry the later Q-loop changes (commit-then-log, Git Bash trap, `/q` first, `--repo`).
  - The template working tree on `master` has an uncommitted edit to `.github/instructions/codacy.instructions.md` that is not mine; I excluded it from my commit.
  - The two review-triage policies are declared, not initialized.
  - `examples/quickstart.py` and `examples/next_best_action.py` still train on zero episodes.
- **Open for a human:** approve or change the five new ledger candidates (BP-005 to BP-009) and the template matrix wording; approve the Tier 3 propagation of LL-016 to LL-018; whether to push the template branch.
- **Review (Step 8):** Amazon Q round 1 reviewed head `c727c14` (two reviews, no inline finding, no merge-blocking defect). One non-blocking observation:
  - `Q-19-1 | style | verified: yes | decision: declined | bare asserts in the matrix test helper; inside a pytest test the assertion names the failing row, and a drifted matrix header should fail loudly | fix: none`
  A standalone `/q` command asked for an explicit verdict; Q replied "No further additions" on `c727c14` and accepted the declination.


---

## Story 4.1 — Capture Diagnostic Migration Snapshot and Correct Replay Docstring
- **Commit:** `194376d`
- **Date:** 2026-10-26
- **Branch:** `feat/story-4.1`
- **Source ADR / BRD / FDD:** ADR-004 (sections 3, 4.1, 4.2, 7), BRD-004, FDD-004 (designs 1 to 3, error-handling table)
- **Files Modified/Created:**
  - `src/agent_learning/cli.py` (`_cmd_set_task_policy_authority` appends a `MigrationRecord` to `metadata["migration_records"]` when the authority changes; an unchanged authority writes nothing)
  - `src/agent_learning/types.py` (`Episode` docstring: the `context_features` replay claim replaced, pointing to ADR-004)
  - `tests/test_authority_migration.py` (new, 15 tests)
  - `.claude/skills/autonomy/SKILL.md` (migration-snapshot section), `docs/decision-making.md` (paragraph under the authority-set command)
  - `docs/user-stories/epic-4-authority-migration-diagnostic-snapshot.md` (status updated to Completed)
- **Validation:**
  - $AC_0$: a change from `low` to `full` and from `full` to `low` each appends one record.
  - $AC_1$: the record has exactly the five fields; `policy_version_at_migration` equals the snapshot version; `action_probabilities_at_migration` equals `SoftmaxPolicy.probabilities()` for non-uniform logits and sums to 1; `migrated_at` parses as ISO 8601 with a zero UTC offset.
  - $AC_2$: setting the current authority appends no record and writes nothing (the stored metadata, including `decision_authority_updated_at`, is unchanged); setting `low` on a policy with no stored authority is a no-op; repeating a change appends once.
  - $AC_3$: `low` to `full` to `low` to `full` appends three records in chronological order, each earlier record equal to its earlier copy, and each record keeps the distribution of its own moment after the logits change.
  - $AC_4$: the `Episode` docstring no longer contains "replay" and states that `context_features` is not consumed by non-contextual bandit selection (ADR-004).
  - $AC_5$: no second snapshot is stored, the only keys added to the metadata are `migration_records` and the three authority keys, and `PolicySnapshot` keeps its fields.
  - Observed RED first: 11 of 15 tests failed before the change; the 4 that passed are guards (the policy-snapshot fields, an empty record list on an old snapshot, the reported authority, and `low` on a policy with no stored authority).
  - Full suite with `--ignore=tests/test_spark.py --ignore=tests/pmbok`: **718 passed, 2 skipped**. Not covered: `tests/pmbok` and `tests/test_spark.py` (LL-013).
  - `ruff check`: the new test is clean; `cli.py` and `types.py` have 78 findings, the same 78 as before the change.
- **Interpretations not stated verbatim in the acceptance criteria (LL-011), recorded in the test header:**
  - I1: the current authority is what `TaskPolicy(snapshot).authority` reports, which is `low` when none is stored.
  - I2: FDD-004's "a 1-element list containing the initial snapshot" is read as one `MigrationRecord`, not a copy of the snapshot.
  - I3: an unchanged authority is idempotent in full (nothing appended, nothing stored). This changes the earlier behavior, where every call rewrote `decision_authority_updated_at`; the command still prints its result and exits 0.
  - I4: "ISO 8601 UTC" means `datetime.fromisoformat` parses it and the offset is zero.
  - I5: "never overwritten or mutated" is tested by comparing earlier records with deep copies taken before later transitions.
  - I6: AC_4 is tested on the docstring text.
  - I7: the CLI builds only `SoftmaxPolicy` snapshots, so a contextual snapshot is not handled.
- **Open for a human:** whether FDD-004 should be amended for I2 and I3 (it is approved, so an amendment needs its own approval). Behavior change to note: a no-op `task-policy-authority-set` no longer refreshes `decision_authority_updated_at`.
- **Review (Step 8):** Amazon Q round 1 reviewed head `afcf87e` (two reviews, two findings, both in the test file; none in `cli.py` or `types.py`); round 2 reviewed `b247eea`; then an explicit verdict.
  - `Q-21-1 | crash risk | verified: yes | decision: accepted | the _stored() test helper could return None and fail with an AttributeError; it now asserts a policy exists | fix: b247eea`
  - `Q-21-2 | test gap | verified: yes | decision: declined | asked for strictly increasing timestamps; that would flake on a coarse clock that repeats a value, the order is proven by the (from, to) pairs, and a comment in the test says so | fix: b247eea (comment only)`
  - Verdict on `b247eea`: Q replied "No" to further additions, with no new findings.
- **Breakout recap (ADR-010 section 4.1):** pending; this is the epic's last story, to be held after the PR review (Step 9).


---

## Story 6.1 — Implement Opt-In Policy Configuration and Lightweight Evidence Capture
- **Commit:** `4d698fa`
- **Date:** 2026-10-26
- **Branch:** `feat/story-6.1`
- **Source ADR / BRD / FDD:** ADR-006 (sections 4.1 to 4.4, 5), BRD-006 (BRU-006-01 to BRU-006-07), FDD-006 (designs 1 to 4 and the error table). BRD-006, FDD-006 and the story were approved first (PR #23; FDD-006 and the story had been aligned with the code, because `audit_evidence` on `DecisionResult` and `decide()` already existed from Epic 7).
- **Files Modified/Created:**
  - `src/agent_learning/decision.py` (`CAPTURE_DECISION_EVIDENCE_KEY`, `capture_decision_evidence_enabled()`, `TaskPolicy(capture_decision_evidence=None)`, enforcement on the low path)
  - `src/agent_learning/capture.py` (`EpisodeCapture.start(decision_result=...)`, write-once check in `end()`)
  - `src/agent_learning/cli.py` (`task-policy-init --capture-decision-evidence`; `task-episode-register --decision-result` with the write-once carry-over; `task-policy-decide` exits 2 on an opted-in policy)
  - `src/agent_learning/__init__.py` (two names exported)
  - `tests/test_evidence_capture.py` (new, 48 tests)
  - `.claude/skills/governance/SKILL.md`, `docs/decision-making.md`, `docs/user-stories/epic-6-...md` (status Completed)
- **Validation:**
  - $AC_0$: absent flag reads False; `TaskPolicy(capture_decision_evidence=True/False)` sets it, `None` leaves a stored value alone; deciding never changes it; the CLI init flag sets it true, and without the flag the key is absent; no toggle subcommand exists.
  - $AC_1$: an opted-in low policy raises `ValueError` with the FDD's exact message for `None`, `{}`, a string, a list, an integer and a list of pairs; a forced action goes through the same check; a failed check leaves the policy unchanged.
  - $AC_2$: a valid mapping, including nested and odd keys, is attached equal in value and the caller's mapping is not changed.
  - $AC_3$: with the flag off or absent no evidence is needed, optional evidence is still attached, and the chosen action sequence is identical with and without evidence for the same seed; the CLI decide on a default policy is unchanged.
  - $AC_4$: `to_dict()` and `from_dict()` round-trip `None`, `{}`, nested and odd mappings through JSON.
  - $AC_5$: `start(decision_result=...)` and `--decision-result` copy the evidence (a copy, not an alias); a different value already present fails; a re-registration without the key carries the stored value over; the same value changes nothing; a different value exits 2 and stores nothing; `end()` rejects a different value in `extra_metadata`; `Episode` and `PolicySnapshot` keep their fields.
  - $AC_6$: one REINFORCE update gives identical logits with and without evidence in the episode metadata; episodes with evidence store and reload; no module under `learners`, `metrics`, `rewards` or `policy` mentions `audit_evidence`.
  - Observed RED first: 25 of 46 tests failed before the change; the 21 that passed are guards for behavior that already existed (the `DecisionResult` round trip and attachment, the learner, the store). Later additions brought the file to 48 tests.
  - A first version wrote `capture_decision_evidence: false` on every `task-policy-init`; that broke `tests/test_cli.py::test_task_policy_init_and_inspection`, which pins the default metadata exactly. The CLI now writes the key only with the flag.
  - Full suite with `--ignore=tests/test_spark.py --ignore=tests/pmbok`: **766 passed, 2 skipped**. Not covered: `tests/pmbok` and `tests/test_spark.py` (LL-013).
  - `ruff check`: the new test is clean; `decision.py`, `capture.py` and `cli.py` have the same findings as before the change.
- **Interpretations not stated verbatim in the acceptance criteria (LL-011), recorded in the test header:**
  - I1: `capture_decision_evidence` defaults to `None` in `TaskPolicy` (leave the stored value), not `False` as the FDD sketch shows, so a stored True is not switched off silently.
  - I2: `decide()` never writes the flag.
  - I3: `task-policy-init` writes the key only when the flag is passed.
  - I4: a forced action goes through the same enforcement.
  - I5: enforcement applies only to the low path.
  - I6: "verbatim" means equal in value.
  - I7: the write-once rule for the two entry points and `end()`.
  - I8: "no performance overhead" is tested as behavior, not time.
  - I9: the learner test and the source scan.
  - I10: `task-policy-decide` cannot pass evidence, so on an opted-in policy it exits 2 with a message pointing to the SDK.
- **Found, not fixed (outside this story):** `task-policy-decide` has no option to supply `audit_evidence` (I10). A policy opted in from the CLI therefore cannot be used through that command. FDD-006 and the story do not specify a way; one would be a small follow-up (for example `--audit-evidence PATH`).
- **Open for a human:** whether to add a CLI way to pass the evidence (FDD amendment and story); whether FDD-006 should record I1 (the `None` default).
- **Review (Step 8):** Amazon Q round 1 reviewed head `bb06aa7` (two reviews, one inline finding). Its second review states "No merge-blocking defects were introduced by this PR". All three remarks were checked against the code and declined:
  - `Q-24-1 | crash risk | verified: no | decision: declined | claimed len(audit_evidence) raises TypeError for a Mapping without __len__; collections.abc.Mapping requires __len__ (it inherits Sized), and a custom Mapping without it cannot be instantiated | fix: none`
  - `Q-24-2 | logic error | verified: no | decision: declined | claimed a pre-existing NameError on feedback_status in _cmd_register_task_episode; the only use outside the guarded block is behind args.require_decision_policy and ..., which short-circuits, and the new tests register without that flag | fix: none`
  - `Q-24-3 | style | verified: yes | decision: declined | design note that DecisionResult.to_dict() copies audit_evidence shallowly; existing behavior from the change that introduced the field, outside this story, and the new episode entry points deep-copy | fix: none`
  - Verdict: Q did not answer two explicit verdict requests on `bb06aa7` (about 25 minutes). The maintainer forwarded Q's second review text and the story was merged on that basis, not on an explicit "no further additions" reply.
- **Breakout recap (ADR-010 section 4.1):** pending; this is the epic's last story, to be held after the PR review (Step 9).
