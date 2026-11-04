---
artifact_type: "post_delivery_impact_assessment"
report_id: "REP-STAGE12-OUTCOME-PHASE1"
baseline_id: "PMP-BL-v1.0.0"
lifecycle_stage: "Stage 12 (Actual Outcome)"
pmbok_process: "5.5 Validate Scope & Value Realization"
date: "2026-11-04"
governance_policy: "none (Empirical Observation; records no approval and certifies no gate)"
evidence_commit: "f86530a"
---

# Stage 12 Actual Outcome Assessment: Phase 1

> Compares what Phase 1 expected (`Project-Charter.md` §2, §6, §7 and `Benefits-Management-Plan.md` §1, §5) with what the repository shows on 2026-11-04. It uses no production telemetry, because none exists. It states a measurement only where one was made.

## 1. Result in one paragraph

Phase 1 built the machinery for both options and validated neither hypothesis. The warm-start path (Option A) and the Thompson policy (Option C) exist and are tested. Neither HYP-AL-008 nor HYP-AL-009 has been tested against the comparison its own falsification criteria name, so both are still Formulated. The benefits the Benefits Management Plan lists are not yet realised and cannot be measured from the evidence available.

## 2. Charter objectives (§2): expected against actual

| Objective | Expected | Actual | Evidence |
|---|---|---|---|
| Resolve the `SoftmaxPolicy` reusable-state dependency | A verified yes or no | **Met.** YES_SATISFIED on 2026-11-01. | `Status-Reports/M1-Softmax-State-Inspection-Report.md` |
| Validate or invalidate HYP-AL-008 | Warm-started episodes-to-gate strictly below a cold start | **Not met.** Still Formulated. Story 20.6 found no converged low-authority donor, and its record says no claim is made that a warm start reduces supervision. | `implementation-log.md` Story 20.6 |
| Validate or invalidate HYP-AL-009 | Thompson or UCB crosses the autonomy gate that defeated REINFORCE | **Not met.** Still Formulated. Story 15.6 is a consistency check on the recorded positive-only history; it claims nothing about better decisions. | `implementation-log.md` Story 15.6 |
| Recorded Phase 2 go/no-go | A recorded decision | **Not met.** No such record exists. | `Project-Status-Register.md` §2 |
| M0.5 research Go/No-Go (40-hour time-box) | A recorded decision | **Met.** Go on 2026-10-22, at 16 of 40 hours (the sponsor's own figure). HYP-AL-011 is reframed, not resolved. | `Project-Charter.md` §5, §7 |

## 3. Milestones (§7)

| Milestone | Status |
|---|---|
| M0.5 | Resolved: Go |
| M1 | Done |
| M2: Option A built | Built (Epic 20, `warm_start.py`, `task-policy-warm-start`). Run against a real donor: no, none exists. |
| M3: Option C built | Thompson built (Epic 15). UCB (Epic 16) and the other policies (Epics 14, 17, 18) are approved, Ready and not built. |
| M4: both re-tested on real data | Not done for either hypothesis (see §2). |
| M5: Phase 1 review | Open: this assessment and Stages 17 and 18 feed it. |

## 4. Benefits (Benefits Management Plan §1a)

| Expected benefit | Tied to | Realised? |
|---|---|---|
| Fewer manual reviews across the system's lifetime | HYP-AL-008 | **Unmeasured.** The plan itself defers quantification until real episode counts exist, and none exist for a warm-started policy. |
| A repair path for a decision class impossible to automate | HYP-AL-009 | **Partly.** A Thompson policy class exists. Whether it crosses the gate is untested; the plan names at least 100 scored episodes including failures as the bar (BRU-015-10), and that history does not exist. |
| Lower integration friction for future policies | HYP-AL-008 | **Unmeasured.** The mechanism exists; no adopter use is recorded. |
| A real second case (ADPA provider ranking) | HYP-AL-009 | **Not started.** |
| Hosted governance-as-a-service (§1b) | HYP-AL-011 | **Not validated.** Willingness to pay has not been asked of anyone. |

## 5. Impact deltas that can be stated

These are facts from the repository, not value claims:

- Full test suite at `3567c96`: 1857 passed, 1 skipped, with `tests/test_spark.py` and `tests/pmbok` excluded (LL-013, ADR-034).
- Stories: 58 of 144 implemented, 60 approved and Ready but not built, 25 Draft or blocked, 1 superseded (`python scripts/phase_rollup.py`).
- Drift: 15 stories have a status line that disagrees with `implementation-log.md` (AUDIT-006).
- Audit: one bounded audit approved on 2026-11-04 (AUDIT-001 to AUDIT-006). It found ADR-034's decommissioning criteria not yet met (AUDIT-004).

## 6. What blocks a real outcome measurement

1. **No low-authority donor.** HYP-AL-008 needs a converged low-authority policy to warm-start from. Story 20.6 found none. IMP-010 proposes a read-only donor-candidates command.
2. **No scored history with failures.** HYP-AL-009 needs a history with failures. The recorded `approve-*` history is almost all positive (Story 15.6).
3. **Unbuilt epics.** Epics 14, 16, 17 and 18 hold the comparison methods and the real-data checks, and are carry-over.
4. **Store location.** `data/agent-learning/` is git-ignored and the recorded store lives where `AGENT_LEARNING_LOCAL_STORE_DIR` points (LL-040), so a checkout cannot reproduce a measurement.

## 7. Limits of this assessment

- It reads recorded results; it did not run any new experiment.
- The Phase 1 charter has no numeric targets (the plan sets none for HYP-AL-008), so "delta against target" is not computable.
- It is not an approval. Hypothesis dispositions are decided in Stage 18 (`approve-intent-refinement`), and the Phase 2 go/no-go is a human decision.

## 8. Inputs to Stages 13 to 18

- Stage 13: raw observations from §6 and the open drift rows go into `OBS-*.md` notes in the Obsidian brain.
- Stage 18: HYP-AL-008 and HYP-AL-009 enter with no Bayes factor from real data, which `adjudicate_hypothesis_batch()` cannot treat as a terminal state without one. The carry-over backlog is the seed for the next phase.
