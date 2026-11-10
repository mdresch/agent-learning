---
artifact_type: "insight_log"
report_id: "REP-STAGE14-INSIGHT-PHASE2"
baseline_id: "PMP-BL-v1.1.0"
lifecycle_stage: "Stage 14 (Insight)"
pmbok_process: "4.4 Manage Project Knowledge (Synthesis)"
date: "2026-11-10"
governance_policy: "human_review (this repository declares no resolve-kb-conflict shape; drafts only, each accepted or rejected by the maintainer)"
evidence_commit: "b18b951"
follows: "Stage-13-Systems-Telemetry-Review-and-Findings.md (REP-STAGE13-OBSERVATION-PHASE2)"
---

# Stage 14 Insights: Phase 2

> **Drafts for the maintainer to accept, change or drop. Records no approval.** Stage 13 said what was seen; this note says what the observations may mean. Each insight names the observations it rests on, how sure it is, and what would change it. An insight that contradicts an approved document is not a knowledge update: it is a baseline finding for the single Stage 16/17 adaptation. In this repository an insight lives as the "root cause" of a register entry, so each one names where it goes next. A broad pass: it makes no claim beyond its sources.

## INSIGHT-P2-01: Built is not measured, because the data that would exercise the learners does not exist

- **Rests on:** Stage 12 section 6 (no override pairs: 177 approve-* episodes, 0 pairs; no routed traffic; a positive-only history); Stage 13 section 7 and the audit (the repo store's 8 policy snapshots show 0 episodes seen and 0 updates).
- **Reading:** the governance gates are full-authority approvals that are almost all accepted, so the history cannot test the learners built to learn from rejection, routing or failure. The learners were built ahead of the data that would use them.
- **Confidence:** high that the data is absent; medium on the reading.
- **Would change it:** a real run on rejection data that already exists elsewhere (see INSIGHT-P2-02).
- **Goes to:** Stage 15 lesson candidate; Phase 3 intent (which data to acquire first).

## INSIGHT-P2-02: The review triage holds real accept and decline decisions that the gate history lacks

- **Rests on:** Stage 13 section 4 (249 triage lines; accepted 178, declined 62, deferred 7, unknown 2; claim types and verified status recorded for each).
- **Reading:** unlike the approve-* history, the triage lines record a human saying no 62 times, with a claim type, so they are a candidate source of preference pairs and rejection labels. That is the idea behind the ADR-039 review-finding corpus.
- **Confidence:** medium. Nothing here has been run; "usable as pairs" is untested.
- **Would change it:** converting the lines to pairs and finding too few distinct situations, or labels that are not independent of the claim type.
- **Goes to:** Epic 39 (already approved, next phase); no new entry.

## INSIGHT-P2-03: A merge can happen while the full-suite result is not yet a blocking fact

- **Rests on:** Stage 13 section 2 (a `Tests` run on `feat/phase-2-examples-and-ledger` at `f26eadb`, created 12:23 on 2026-11-10, ended in failure; PR #173 was merged at 12:26:38; `main` then ran 5 catalog tests red until PR #178). Also the PR #178 merge, where the check list read back empty about a minute after the push and the gate still passed.
- **Reading:** `scripts/pr_gate.py` (lines 362 to 370) blocks only when a check's conclusion is `FAILURE`, `TIMED_OUT` or `ACTION_REQUIRED`. A check that is still running, or a check list that reads back empty, has no conclusion and passes. So a merge can go through while the full-suite result is not yet in. Who or what issued the #173 merge is not established by these facts, so whether it passed through this gate is unknown.
- **Confidence:** high on what the gate does (read from the code); low on whether it was the path for #173.
- **Would change it:** the gate's own log for #173, if one exists.
- **Goes to:** a Stage 15 lesson candidate and an improvement candidate (treat pending or empty checks as not ready); both on the maintainer's decision.

## INSIGHT-P2-04: Numbers and lists copied into approved documents go stale

- **Rests on:** audit AUDIT-011 (ADR-021 named 11 pinned gates; the code needed 18, found in two rounds, IMP-046); AUDIT-013 and AUDIT-014 (ADR-022 says weights are at least 0.0 and a proposal needs accuracy "at least" the baseline; the code requires 0.05 and "strictly greater", and FDD-022 says "strictly beats"); the catalog tests (the Ideation states and the class counts in ADR-036 had to be amended for seven methodologies).
- **Reading:** where a document copies a list or a threshold that code also holds, nothing keeps them equal until a test or a real-data check forces it. The pinned-gate test added in IMP-046 is the one case where something now does.
- **Confidence:** medium-high; four separate cases.
- **Would change it:** finding that these were isolated edits rather than a pattern.
- **Goes to:** Stage 15 lesson candidate; AUDIT-013 and AUDIT-014 remain open as IMP-053 for Phase 3.

## INSIGHT-P2-05: The failing-first practice improved over time, and the cause is not known

- **Rests on:** Stage 13 section 5 (failing-first run noted for 7 of 7 Epic 21 and 6 of 6 Epic 38 stories, 1 of 6 in Epic 18, 1 of 7 in Epic 22, none of 18 in Epics 14, 16 and 17; a loose text search).
- **Reading:** the later epics record it and the earlier ones do not. Whether the practice changed or only the logging did cannot be told from the log.
- **Confidence:** low.
- **Would change it:** checking git history for the earlier stories' first commits (whether tests were committed before code).
- **Goes to:** IMP-057 (already drafted); no new entry.

## INSIGHT-P2-06: A stage with no defined input or deliverable gets reinvented on each pass

- **Rests on:** the Stage 13 discussion in this session; the coverage document's open decision 1 (whether review-triage records count as Stage 13 observations at all); the null telemetry fields (Stage 13 section 7; IMP-058).
- **Reading:** Stage 13 and Stage 14 are defined by role (what is seen, what it means) but not by a source or an output here, so each pass improvises. This pass's Stage 13 and Stage 14 notes are a first deliverable for each.
- **Confidence:** high that the definition is open; medium that two named notes per phase are the right deliverable.
- **Goes to:** a decision for the maintainer on the coverage document's open decision 1; IMP-058 for the telemetry input.

## INSIGHT-P2-07: Planning units and the agentic record do not compare

- **Rests on:** the Sponsor's statement of 2026-11-10 (the planning figures are human-engineering days); Stage 13 section 6 (about 25.5 hours of session time from 2026-11-07 to 2026-11-10, a lower bound that leaves out human review and tokens); the M6 to M10 plan of 30.0 person-days.
- **Reading:** no ratio between the two is supportable, and a schedule built on one would not be a forecast of the other.
- **Confidence:** high that they differ in unit; nothing is claimed about the size of the gap.
- **Goes to:** Stage 15 lesson candidate (already Sponsor-stated); Phase 3 baseline keeps human-engineering days.

## Baseline findings (these contradict approved or stale documents)

These go to the one Stage 16/17 adaptation, not into the knowledge base.

| Finding | Document | Evidence |
|---|---|---|
| The Charter maps HYP-AL-018 to the DPO engine; Ideation section 2.2 defines HYP-AL-018 as a linear contextual bandit (#24) | Project Charter (sections 2, 10), Ideation Document | Stage 12 section 7 |
| The Charter, PMP and generated plans still name `agent-training-ext/` | Project Charter, PMP, management plans | CR-20261109-001 section 6 and CR-20261109-002 |
| ADR-022 Invariants 2 and 5 disagree with the code and FDD-022 | ADR-022 | AUDIT-013, AUDIT-014 (IMP-053, Phase 3) |
| ADR-016 Invariant 4 (LOW authority) has no code path to check | ADR-016 | AUDIT-008 (IMP-054, Phase 3) |

## Limits

- These are readings of recorded observations by one assistant; they are drafts until the maintainer accepts them.
- Four insights (P2-03, P2-05, and parts of P2-01 and P2-02) rest on counts from loose searches or on facts whose cause was not checked; each says so.
- Nothing here was run as an experiment.
