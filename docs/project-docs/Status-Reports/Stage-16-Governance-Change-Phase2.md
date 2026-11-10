---
artifact_type: "governance_change_assessment"
report_id: "REP-STAGE16-GOVERNANCE-CHANGE-PHASE2"
baseline_id: "PMP-BL-v1.1.0"
lifecycle_stage: "Stage 16 (Governance Change)"
pmbok_process: "4.6 Perform Integrated Change Control"
date: "2026-11-10"
status: "DRAFT - Steps 1 to 3 (input check, triage, classification). No escalation decided, nothing amended."
follows: "Stage-15-Lessons-Phase2.md (REP-STAGE15-LESSON-PHASE2)"
---

# Stage 16: Governance Change, Phase 2 (draft)

> **Scope: the whole register, LL-001 to LL-064.** Only LL-043 and LL-046 (under Phase 1 titles) went through Stage 16 before. Step 2a covers the other lessons and Step 2b the improvements (IMP-001 to IMP-061).

> A broad pass over what Stage 15 accepted and what Stage 14 flagged as baseline findings. Classifications are the assistant's readings; the escalation decision (Step 5) and every amendment are the maintainer's. Approved ADR, BRD, FDD and story changes need a Stage 16 episode and `scripts/governance_baseline.py`; generated plans are regenerated, never hand-patched.

## Step 1: Inputs

- Stage 15: accepted by the maintainer 2026-11-10 (LL-060 to LL-064, IMP-059 to IMP-061).
- Baseline: PMP-BL-v1.1.0. Open change requests: CR-20261109-001 (Epic 23 scope) and CR-20261109-002 (26 wording corrections, amendments in progress).
- Governance episodes for Stages 13 to 15: none, by design (`human_review`).

## Step 2a: Whole-register coverage (64 lessons)

Method: each lesson's Tier 2/3 target is read from the register, then the ID is searched in `.claude/`, `scripts/`, `src/` and `tests/` and counted in the Continuous Improvement Register. **This is a heuristic.** A rule can be in a skill without the ID, and an ID in a test is not proof the skill was changed. Bucket B and C need a read of each named target before any claim.

| Bucket | Lessons | Count | Reading |
|---|---|---|---|
| A. Tier 1 only | LL-008, 009, 012, 019, 024, 053 to 060, 062 to 064 | 16 | No propagation owed. LL-053 to 060 point at IMP entries for the skill or tool change. |
| B. Tier 2/3 target, ID cited in a skill, script, source or test | LL-001 to 007, 010, 011, 013, 016, 018, 020 to 023, 025, 026, 037, 040 to 046, 049, 050, 052 | 29 | Probably applied. Spot-check the named target. |
| C. Tier 2/3 target, ID cited nowhere | LL-014, 015, 017, 027 to 036, 038, 039, 047, 048, 051, 061 | 19 | Propagation unverified. |

Within C, LL-014, 015, 017 and 027 to 032 (nine lessons, 2026-10-25 to 2026-10-28) have no IMP entry either, so nothing tracks them. LL-033 to 036, 038, 039, 047, 048, 051 and 061 are at least named in an IMP.

LL-041 says a lesson's Tier 2 propagation belongs in the same PR; bucket C is where that was not met, or not recorded.

### This pass's five lessons

| Lesson | Needs a governance change? | Route |
|---|---|---|
| LL-060 (merge gate and pending checks) | No, tooling | Direct fix through IMP-059 |
| LL-061 (document lists vs code) | Yes for the drifted ADRs (findings 3 and 4); the check is tooling | Stage 16 for the ADRs; IMP-060 for the check |
| LL-062 (learner epic needs a data count first) | Yes, a new rule in the epic and spec gate | Stage 16 |
| LL-063 (effort figures are human days) | Probably no; already the working rule | Maintainer to confirm whether the PMP states the unit |
| LL-064 (stage needs input, output, owner) | Yes, coverage document | Stage 16 (IMP-061) |

## Step 2b: Whole-register coverage (60 improvements)

Read from the status column of `Continuous-Improvement-Register.md`. The register defines `In-Flight Candidate` as "can be introduced in the active phase ... evaluated through the governance change pipeline (Stages 16 to 17)".

| Status | Count | IMP entries |
|---|---|---|
| Implemented | 3 | IMP-033, 046, 051 |
| Rolled into Phase Next Intent Refinement | 33 | IMP-003, 005, 008 to 014, 018, 023, 026, 029, 032, 035 to 038, 040 to 042, 047 to 049, 053 to 061 |
| In-Flight Candidate | 24 | IMP-001, 002, 004, 006, 007, 015 to 017, 019 to 022, 024, 025, 027, 028, 030, 031, 039, 043, 044, 045, 050, 052 |

What this shows:

- **24 entries still say they await Stage 16/17, some since Epic 14 (2026-10).** The Phase 1 Stage 16 pass took LL-043 and LL-046 only, and the Phase 1 Intent Refinement Proposal cites no IMP id. So none of the 24 was evaluated, and their status is stale or unproven.
- **Status may lag the code.** IMP-045 (read `gh` output as UTF-8) is In-Flight, yet `scripts/pr_gate.py` line 524 calls `reconfigure(encoding="utf-8")`; LL-059 still says to run with `PYTHONUTF8=1`. Whether it is fixed needs a test, not a guess. IMP-043 (union merge for the log) has no `.gitattributes`, so it looks open.
- **Numbering gap:** there is no IMP-034 in the register or in any document.
- **"Rolled into Phase Next" is a label.** I found no document that records which phase-close decision rolled each of the 33 in. Treat it as a claim to confirm, as with the lesson IDs.
- IMP-031 ("backfill Tier 2 targets for LL-045 to LL-048 and script the LL-041 check") is the register's own record that bucket C above is real; it is In-Flight and not done.

Needed: for each of the 24, read the named change and mark it implemented, still open, or dropped; then decide for the open ones whether they are this adaptation's in-flight changes or go to Phase Next. Nothing is re-scored.

### Step 2c: The 24 In-Flight improvements checked against the code

Method: for each entry, the named file, function or command was searched for and, where it exists, read. No test was run. "Open" means the named change is not in the code; the register status is unchanged until the maintainer decides.

| Result | Entries |
|---|---|
| Already in the code (status stale) | IMP-004 (`_prior_from_snapshot` in `cli.py`, refuses a missing logit; private to the CLI), IMP-020 (`spec_gate.py` uses all four Epic 14 criteria), IMP-022 (`add_rewards` skips a seen id before validating; `store_episodes` not read) |
| Partly | IMP-016 (`convert_unstructured_review_to_tags` exists and names Bugbot; Claude and human summaries not confirmed) |
| Open (20) | IMP-001, 002, 006, 007, 015, 017, 019, 021, 024, 025, 027, 028, 030, 031, 039, 043, 044, 045, 050, 052 |

Evidence for the open ones:

- IMP-001: `complete_story.py` has no `worktree`, `--none` or `Co-Authored-By` handling. IMP-007: no `scripts/approve.py`. IMP-019, 025, 028: no harvester, preference-pair loader or reversibility lint command. IMP-015: the fixture file exists, no export script.
- IMP-002: `policy/thompson.py` still has `replay(record, policy_id)`. IMP-027: `CallableSnapshot` stays in `epsilon_greedy.py`; no `base_compat`.
- IMP-017: `pr_gate.py` does not call `triage_replay`; IMP-030: it has no triage check at all.
- IMP-031: no LL-045 to LL-048 id in any named Tier 2 target. IMP-043: no `.gitattributes`. IMP-044: `implement-story` Step 6 still lists `--ignore=tests/pmbok`. IMP-050: Step 8 is prose with the literal confirm text but no checklist.
- IMP-045: the gate's `gh` call (`subprocess.run(..., text=True)`, line 60) sets no encoding; the `reconfigure` at line 524 covers output only. LL-059's workaround still applies.
- IMP-052: `publish.yaml` still fails when the tag points at another commit, which is the unbumped-push case.
- IMP-021, 024: `spec_gate.py` has no widening check and no `rel_tol` check. IMP-006: no committed store fixture. IMP-039: `autonomy.py` has no contextual handling.

Reading: 4 of 24 are done or mostly done, 20 are open. Of the 20, 13 touch `pr_gate.py`, `spec_gate.py`, `complete_story.py` or the `implement-story` skill, which is the tooling the lessons keep pointing at (IMP-001, 007, 017, 021, 024, 030, 031, 043, 044, 045, 050, 052 and IMP-015).

## Step 3: Classification

| Item | Diff type | Evidence basis | Impact | Confidence |
|---|---|---|---|---|
| LL-062 spec-gate rule | process | execution | medium | medium |
| LL-064 / IMP-061 coverage document | content | execution | low | high |
| F1 Charter maps HYP-AL-018 to the DPO engine; Ideation 2.2 says linear contextual bandit | content | design_time | medium | high |
| F2 Charter, PMP and plans still name `agent-training-ext/` | content (generated plans regenerate) | design_time | low | high |
| F3 ADR-022 Invariants 2 and 5 vs code and FDD-022 (IMP-053) | content on an approved ADR | execution | medium | high |
| F4 ADR-016 Invariant 4 has no code path (IMP-054) | structural or scope, unclear | design_time | medium | low |
| F5 Phase 1 documents use LL-044, LL-045, LL-046 for lessons the register does not hold under those IDs (the register's three are different lessons); SPA-20261106-001 cites LL-046 | content (references) | execution | medium | high |

## Notes for Step 5

- F2 may already be covered by CR-20261109-001 section 6 and CR-002; check before opening anything new.
- F3 and F4 are marked Phase 3 in the registers; deciding whether to move them into this adaptation is the maintainer's call.
- F4 has low confidence: it is not clear whether the fix is code (add the path) or the ADR (drop the invariant). Flag, do not classify further.
- One adaptation covers all of this (Stage 16/17), as agreed.

- F5: the Phase 1 lessons "External Evidence Dependency", "Single Source of Truth for Story Status" and "Dual Evidence Storage" appear in no register entry. Decide whether to register them under new IDs (LL-065 onward) or record that they were never adopted. Corrected references go through the amendment tooling, nothing is re-scored. Files: Stage 15, 16, 17 assessments, ADP-20261106-001, SPA-20261106-001, IRP-20261106-001, Adaptation-Plan.md, and the Stage 15 methodology appendix.

## Not done

Reading each bucket B and C target to confirm propagation;

Escalation decisions, change requests, amendments, governance episodes and the Project-Status-Register update.
