---
artifact_type: "post_delivery_impact_assessment"
report_id: "REP-STAGE12-OUTCOME-PHASE2"
baseline_id: "PMP-BL-v1.1.0"
lifecycle_stage: "Stage 12 (Actual Outcome)"
pmbok_process: "5.5 Validate Scope & Value Realization"
date: "2026-11-10"
governance_policy: "none (Empirical Observation; records no approval and certifies no gate)"
evidence_commit: "b18b951"
related_assessment: "REP-STAGE12-OUTCOME-PHASE1 (Stage-12-Actual-Outcome-Assessment.md)"
---

# Stage 12 Actual Outcome Assessment: Phase 2

> Compares what Phase 2 expected (`Project-Charter.md` v2.0 sections 2, 6, 7 and 10, and `Benefits-Management-Plan.md` section 1 and the Phase 2 measurement table) with what the repository shows on 2026-11-10. It follows the shape of the Phase 1 assessment ([Stage-12-Actual-Outcome-Assessment.md](Stage-12-Actual-Outcome-Assessment.md), which stays as written). It uses no production telemetry, because none exists, and it states a measurement only where one was made. A broad pass: exceptions are one line and carried forward.

## 1. Result in one paragraph

Phase 2 built what it set out to build and measured little of the value it promised. All six baseline epics (14, 16, 18, 21, 22, 38) are implemented and the whole suite passes. The real-data checks that were meant to test the value claims ran against the data that exists, and in each case that data cannot answer the question: no override pairs (Epic 18), no routed traffic (Epic 21), a positive-only history (Epic 16). So the technical criteria are met, the drift and fork criteria are met or nearly so, and the value hypotheses are still unresolved. Phase 1 ended in the same place for its own hypotheses.

## 2. Charter success criteria (section 10): expected against actual

| Criterion | Actual | Evidence |
|---|---|---|
| 1. 100% technical delivery: Epics 14, 16, 18, 21, 22, 38 implemented with 100% test pass | **Met.** Every story of the six epics is implemented. Full suite, nothing excluded: 2605 passed, 2 skipped (Java and POSIX Bash). | `phase_rollup.py` lists none of their stories as unimplemented; Stage 10 run at `51ef83d` |
| 2. Hypotheses HYP-AL-005, 018, 025, 026, 027 formally resolved with empirical evidence | **Not met.** HYP-AL-005 is Testing, HYP-AL-025 Formulated, HYP-AL-018 Formulated. HYP-AL-026 and 027 are recorded as Validated at the Phase 1 close, so they were not resolved by Phase 2 work. | Ideation section 2.2 status column |
| 3. Zero governance drift | **Met.** 0 status-drift rows. | `phase_rollup.py --check` exit 0; `update_story_status.py --validate` 257 of 257 |
| 4. Clean fork verification | **Met, weakly.** `src/agent_learning` has no diff against the Microsoft files in the manifest (26 tests pass). A trial merge with `upstream/main` has 0 conflicts. But `upstream/main` (`476f367`, 2026-10-27) is already an ancestor of our head, so there was nothing new to merge. | `test_upstream_untouched.py`; `git merge-tree` |
| 5. `PCD-Phase2` issued and approved | **Not yet.** It is Stage 18. | Project-Status-Register section 1 |

## 3. Deliverables (Charter section 6)

| Deliverable | Acceptance standard | Actual |
|---|---|---|
| DEL-P2-01 to 03 (Epic 14: parser, shift engine, metadata) | Tests pass; shift within 1e-9; metadata round-trips | **Met** by the Epic 14 stories. Story 14.5 replayed 139 real review triage records (the plan asked for 32). |
| DEL-P2-04 (Epic 18: DPO engine) | At least 30% sample-efficiency gain over online exploration | **Built; the gain is unmeasured.** Story 18.6 found 177 committed approve-* episodes and 0 preference pairs, because every one is an accepted approval. |
| DEL-P2-05 (Epics 16, 21: router, Wilson lower bounds) | Deterministic routing between low and full | **Built.** Story 21.7 found no routed episodes, and claims nothing about cost or latency. Story 16.6 replayed a positive-only history. |
| DEL-P2-06 (Epics 22, 38: continuous SIDPA pipeline) | Automated Stages 12 to 18 with 0 drift rows | **Partly.** Epics 22 and 38 are built. Stages 12 to 18 are not automated; they are run by hand or by agents, with generated helpers (`phase_rollup.py`, `stage16_amend.py`, `pr_gate.py`, `shadow_effort.py`). Drift is 0. |
| DEL-P2-07 (isolated extension package) | `src/agent_learning` a clean diff against upstream | **Met in substance, in a different place.** The extension is `src/agent_learning_ext/`, not `agent-training-ext/` (moved in PR #162; CR-20261109-002 corrected the documents). |
| DEL-P2-08 (`PCD-Phase2`) | Close decision certifying M6 to M9 | **Pending** (Stage 18). |

## 4. Benefits (Benefits Management Plan, Phase 2)

| Benefit | Measurement the plan named | Realised? |
|---|---|---|
| BEN-P2-001 Deterministic ingestion of review critique | Replay of 32 real triage records | **Partly.** The replay ran over 139 records and is deterministic. Whether feedback is lost less often is unmeasured. |
| BEN-P2-002 CPU-only preference alignment | DPO convergence against a REINFORCE baseline | **Not measured.** No preference pairs exist (Epic 18, Story 18.6). |
| BEN-P2-003 Continuous governance automation | An automated Stage 12 to 18 cycle with 0 drift | **Partly.** Drift is 0; the cycle is not automated. |
| BEN-P2-004 Upstream fork collision immunity | A clean rebase or fetch against upstream | **Measured, weakly.** 0 conflicts; no new upstream commits to test against (section 2). |
| BEN-P2-005 Multi-armed contextual routing | Ensemble regret bounds on routing decisions | **Not measured.** There is no routed traffic. |

## 5. Facts that can be stated (not value claims)

- Stories: 102 of 164 implemented, 36 approved and Ready but not built, 25 Draft or blocked, 1 superseded. Phase 1 closed at 58 of 144.
- Tests: 2605 passed, 2 skipped, nothing excluded. Phase 1 closed at 1840 passed with `test_spark.py` and `tests/pmbok` excluded.
- Agentic effort (a shadow record, learning only, not an estimate): 254 non-merge commits from 2026-11-07 to 2026-11-10, in 2 working sessions of about 25.5 hours in total, a lower bound that leaves out human review time and tokens (`Shadow-Agentic-Effort-Phase-2.md`).
- Governance: ADR-039 and ADR-040 approved; 56 improvement entries (IMP-001 to IMP-057) and 59 lessons (LL-001 to LL-059) are registered; one Stage 11 audit approved for Phase 2 (episode `198bfc09`).

## 6. What blocks a real outcome measurement

1. **No override pairs.** DPO (Epic 18) learns from rejections and overrides. The recorded history is all approvals.
2. **No routed traffic.** The router (Epic 21) has run on no real decisions, so regret and cost cannot be computed.
3. **No failure history.** The bandits (Epic 16) are checked on a positive-only history, so their value on failures is untested.
4. **No upstream movement.** The fork-collision test has nothing new to merge against.
5. **Planning units.** The M6 to M10 effort figures are human-engineering days, so there is no agentic target to compare actual effort against.

## 7. Notes carried forward (one line each)

- The Charter ties HYP-AL-018 to the DPO engine, but Ideation section 2.2 defines HYP-AL-018 as a linear contextual bandit (#24). The mapping needs a decision.
- The Charter still names `agent-training-ext/` in sections 2, 3 and 6. The correction was left for the Phase 2 close.

## 8. Limits of this assessment

- It reads recorded results; it ran one new check (the trial merge with upstream) and no experiment.
- The Phase 2 charter's numeric targets (the 30% gain, the 32 records) are the only ones available; the rest of the benefits have no numeric target, so "delta against target" is not computable for them.
- It is not an approval. Hypothesis dispositions are decided in Stage 18 (`approve-intent-refinement`).

## 9. Inputs to Stages 13 to 18

- Stage 13: the section 6 blockers, the shadow effort record and the open drift notes in section 7 are the observations.
- Stage 15: the gap between "built" and "measured" is the main lesson, with the human-equivalent estimate point.
- Stage 18: HYP-AL-005, 018, 025 enter with no Bayes factor from real data. Epics 23, 24 and 39 are carried over.
