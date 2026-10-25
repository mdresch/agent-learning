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
  - Full test suite: 464 passed, 1 skipped (0 failures, 100% green).

---

## Story 9.1 — Phase Close Readiness Gate and Intent Refinement Decision Policy
- **Commit:** `4d84651`
- **Date:** 2026-10-25
- **Branch:** `feat/story-9.1`
- **Source ADR / BRD / FDD:** ADR-009, BRD-009, FDD-009
- **Files Modified/Created:**
  - `pmbok/models/intent_refinement.py` (added `ReadinessPreconditionError`, `ReadinessAuditResult`, and `evaluate_phase_close_readiness()`)
  - `scripts/orchestrate_pmbok.py` (added `--mode seed-next`, `--mode decommission`, and `--mode rollback`)
  - `.claude/skills/intent-refinement/SKILL.md` (created component skill)
  - `.claude/skills/pmbok-planning/SKILL.md` (added sections 6 and 7)
  - `tests/pmbok/test_intent_refinement.py` (contract tests encoding $AC_0$ through $AC_11$)
  - `docs/user-stories/epic-9-intent-refinement-and-cognitive-feedback-loop.md` (status updated to Completed)
- **Validation:**
  - $AC_0$: Precondition checks enforce that deliverables are accepted, audit records cleared, and lessons crystallized, raising `ReadinessPreconditionError` on any gap.
  - $AC_1$: `approve-intent-refinement` policy actions configured with full authority options (`approve_intent_refinement`, `reject_intent_refinement`, `request_revision_before_decision`).
  - $AC_2$: `IntentRefinementProposalPayload` strictly validates SemVer identifiers, readiness audit refs, and disposition constraints.
  - $AC_3$: `--mode decommission` logs administrative teardown in target archive.
  - $AC_4$: `--mode seed-next` generates Phase $N+1$ `Spark-Capture.md` and `Ideation-Document.md` with incremented baseline (`PMP-BL-v2.0.0`).
  - $AC_5$: All refinement proposals, decision frames, and evaluation episodes serialize cleanly into standard ADR-002 `Episode` envelopes with zero storage expansion.
  - Full test suite: 17/17 passed in `test_intent_refinement.py`; 294/294 passed in `sidpa-template`.


---

## Story 9.2 — Bayesian Hypothesis Terminality and Recurrence Exhaustion ($d_{\max}=2$)
- **Commit:** `pending`
- **Date:** 2026-10-25
- **Branch:** `feat/story-9.2`
- **Source ADR / BRD / FDD:** ADR-009, BRD-009, FDD-009
- **Files Modified/Created:**
  - `pmbok/models/intent_refinement.py` (added `HypothesisTerminalityError`, `resolve_hypothesis()`, and `adjudicate_hypothesis_batch()`)
  - `.claude/skills/intent-refinement/SKILL.md` (updated with Story 9.2 constraints and APIs)
  - `tests/pmbok/test_intent_refinement.py` (added 6 contract tests for $AC_6, AC_7, AC_8$)
  - `docs/user-stories/epic-9-intent-refinement-and-cognitive-feedback-loop.md` (status updated to Completed)
- **Validation:**
  - $AC_6$: Empirical Bayes factors $BF_{10} \ge 10$ resolve to `VALIDATED` graduating to architecture invariants; $BF_{10} \le 0.1$ resolve to `REFUTED` with negative learning penalty.
  - $AC_7$: Inconclusive hypotheses ($0.1 < BF_{10} < 10$) refine for $d < 2$; at $d = 2$, hypotheses collapse automatically to `REFUTED` due to budget exhaustion.
  - $AC_8$: 100% of Stage 3 hypotheses in a batch resolve to valid terminal states; unadjudicated hypotheses (missing $BF_{10}$) raise `HypothesisTerminalityError`.
  - Full test suite: 23/23 passed in `test_intent_refinement.py` (1.13s); 300/300 passed in `sidpa-template`.


---

## Story 9.2 — Bayesian Hypothesis Terminality and Recurrence Exhaustion ($d_{\max}=2$)
- **Commit:** `pending`
- **Date:** 2026-10-25
- **Branch:** `feat/story-9.2`
- **Source ADR / BRD / FDD:** ADR-009, BRD-009, FDD-009
- **Files Modified/Created:**
  - `pmbok/models/intent_refinement.py` (added `HypothesisTerminalityError`, `resolve_hypothesis()`, and `adjudicate_hypothesis_batch()`)
  - `.claude/skills/intent-refinement/SKILL.md` (updated with Story 9.2 constraints and APIs)
  - `tests/pmbok/test_intent_refinement.py` (added 6 contract tests for $AC_6, AC_7, AC_8$)
  - `docs/user-stories/epic-9-intent-refinement-and-cognitive-feedback-loop.md` (status updated to Completed)
- **Validation:**
  - $AC_6$: Empirical Bayes factors $BF_{10} \ge 10$ resolve to `VALIDATED` graduating to architecture invariants; $BF_{10} \le 0.1$ resolve to `REFUTED` with negative learning penalty.
  - $AC_7$: Inconclusive hypotheses ($0.1 < BF_{10} < 10$) refine for $d < 2$; at $d = 2$, hypotheses collapse automatically to `REFUTED` due to budget exhaustion.
  - $AC_8$: 100% of Stage 3 hypotheses in a batch resolve to valid terminal states; unadjudicated hypotheses (missing $BF_{10}$) raise `HypothesisTerminalityError`.
  - Full test suite: 23/23 passed in `test_intent_refinement.py` (1.13s); 300/300 passed in `sidpa-template`.



---

## Story 9.3 — Low-Pass Outcome Damping and Cumulative Lineage Kernel
- **Commit:** `105b6ef`
- **Date:** 2026-10-25
- **Branch:** `feat/story-9.3`
- **Source ADR / BRD / FDD:** ADR-009, BRD-009, FDD-009
- **Files Modified/Created:**
  - `pmbok/models/intent_refinement.py` (added `StrategicWhiplashError`, `LowPassOutcomeDampingFilter`, `validate_strategic_pivot_capacity()`, `compute_lineage_kernel()`)
  - `.claude/skills/intent-refinement/SKILL.md` (updated with Story 9.3 constraints and API call sites)
  - `tests/pmbok/test_intent_refinement.py` (added 3 contract tests for $AC_9, AC_{10}, AC_{11}$)
  - `docs/user-stories/epic-9-intent-refinement-and-cognitive-feedback-loop.md` (status updated to Completed)
- **Validation:**
  - $AC_9$: `LowPassOutcomeDampingFilter` dampens high-frequency outcome noise with momentum $\beta \in [0.6, 0.85]$ and bias-corrected warmup for $N < 3$.
  - $AC_{10}$: `validate_strategic_pivot_capacity()` enforces S3-S4 homeostatic balance ($\text{Pivots}_{\max} \le \lceil C_{\text{adapt}} / 2 \rceil$), raising `StrategicWhiplashError` on violation.
  - $AC_{11}$: `compute_lineage_kernel()` computes deterministic hereditary SHA-256 knowledge hash linking generations without epistemic decay.
  - Full test suite: 26/26 passed in `test_intent_refinement.py` (1.18s); 303/303 passed in `sidpa-template` (29.20s).

---

## Story 1.1 — Exclude `full`-authority episodes from `ReinforceLearner`'s training batch
- **Commit:** `ce9346c`
- **Date:** 2026-10-25
- **Branch:** `feat/story-1.1`
- **Source ADR / BRD / FDD:** ADR-001 §4.5, BRD-001, FDD-001
- **Files Modified/Created:**
  - `src/agent_learning/learners/reinforce.py` (excluded `action_logprob is None` episodes from gradient update, counted exclusions in `LearnerResult.extra["full_authority_excluded"]`)
  - `src/agent_learning/audit.py` (updated stale warning message at line 562-563 to reflect exclusion rather than fallback)
  - `.claude/skills/learner/SKILL.md` (new component skill documenting REINFORCE decision authority boundary)
  - `tests/test_learner.py` (added contract tests for $AC_0, AC_1, AC_2, AC_3, AC_4$)
  - `tests/test_audit.py` (verified audit replay exclusion and warning emission)
  - `docs/user-stories/epic-1-decision-authority-enforcement.md` (status updated to Completed)
- **Validation:**
  - $AC_0$: `ReinforceLearner.update()` skips an episode when `episode.action_logprob is None`; verified with full-authority episode returning 0 `episodes_used` and identical logits.
  - $AC_1$: `LearnerResult.extra["full_authority_excluded"]` reports exact exclusion count on all update paths, including `0`.
  - $AC_2$: Low-authority importance sampling is unchanged and reweighted properly when `action_logprob` is set.
  - $AC_3$: `audit.py` emits updated ADR-001 §4.5 warning when a full-authority episode is present in an audited batch.
  - $AC_4$: `audit.py`'s direct `ReinforceLearner.update()` call sites (:444 and :503) exclude full-authority episodes without caller-level filtering.
  - Full test suite: 18/18 passed in `test_learner.py`; 101/101 passed in `test_audit.py`; 442/442 passed across entire core test suite; 303/303 passed in `sidpa-template`. Zero regressions.


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
- **Commit:** `1fc13d2`
- **Date:** 2026-10-25
- **Branch:** `feat/story-10.1`
- **Source ADR / BRD / FDD:** ADR-010, BRD-010, FDD-010
- **Files Modified/Created:**
  - `src/agent_learning/lessons_learned.py` (markdown parser, schema validator, and Phase Close readiness filter)
  - `src/agent_learning/__init__.py` (re-exported symbols)
  - `tests/test_lessons_learned.py` (contract tests encoding $AC_0$ through $AC_4$)
  - `.claude/skills/governance/SKILL.md` (updated component skill with Stage 15 breakout framing and propagation protocol)
  - `docs/user-stories/epic-10-lessons-learned-crystallization-and-register.md` (status updated to Completed)
- **Validation:**
  - $AC_0$: `parse_lessons_learned_markdown()` extracts typed `LessonsLearnedEntry` instances with complete 8-field schema and serialized dictionary representation.
  - $AC_1$: Parser strictly validates schema completeness and identifier format (`LL-###`), raising `ValueError` on malformed IDs or missing required fields (`title`, `trap`, `root_cause`, `invariant`, `tier_targets`).
  - $AC_2$: `filter_crystallized_lessons()` filters entries by target Epic/Phase and supports explicit `no-new-lessons` phase sign-offs.
  - $AC_3$: Filtered payloads pass PMBOK 4.7 `evaluate_phase_close_readiness()` validation, contributing to `crystallized_lessons_count` and satisfying the Stage 15 hard gate.
  - $AC_4$: Active file verification confirms that the canonical repository register `docs/project-docs/Lessons-Learned-Register.md` parses cleanly with 100% compliance across `LL-001` through `LL-004`.
  - Full test suite: 5/5 passed in `test_lessons_learned.py`; 464 passed, 2 skipped across entire agent-learning test suite. Zero regressions.
