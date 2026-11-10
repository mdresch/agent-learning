---
artifact_type: "governance_change_assessment"
report_id: "REP-STAGE16-GOVERNANCE-CHANGE-PHASE2"
baseline_id: "PMP-BL-v1.1.0"
lifecycle_stage: "Stage 16 (Governance Change)"
pmbok_process: "4.6 Perform Integrated Change Control"
date: "2026-11-10"
status: "APPROVED by the Project Sponsor 2026-11-10. Stage 17 is next. Nothing in Stage 17 is done."
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
| B. Tier 2/3 target, ID cited in a skill, script, source or test | LL-001 to 007, 010, 011, 013, 016, 018, 020 to 023, 025, 026, 037, 040 to 046, 049, 050, 052 | 29 | Checked in Step 2d: 24 applied, 3 in code only (LL-001 to 003), 1 partly (LL-044), 1 not applied (LL-046). |
| C. Tier 2/3 target, ID cited nowhere | LL-014, 015, 017, 027 to 036, 038, 039, 047, 048, 051, 061 | 19 | Checked in Step 2d: 2 applied (LL-017, 051), 1 in code only (LL-048), 1 partly (LL-061), 15 not applied. |

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

### Step 2d: The 48 Tier 2/3 lessons (buckets B and C) checked against their Tier 2 targets

Method: the named Tier 2 target was searched for the rule (by LL id, then by its wording) and the full `implement-story` skill was read. No test was run. Tier 3 (`sidpa-template`) is outside this repository and was not checked.

| Result | Lessons | Count |
|---|---|---|
| Rule is in the named Tier 2 target | LL-004, 005, 006, 007, 010, 011, 013, 016, 017, 018, 020, 021, 022, 023, 025, 026, 037, 040, 041, 042, 043, 045, 049, 050, 051, 052 | 26 |
| Rule is enforced in code or tests, but the named skill is silent | LL-001, 002, 003 (`storage` skill; `cosmos.py` and `test_storage_cosmos.py` hold the rule), LL-048 (wrappers exist in `policy/epsilon_greedy.py`; no skill mentions them) | 4 |
| Partly | LL-044 (`docs/research/ideation/README.md` exists; the named `stage-1` or `ideation` skill does not), LL-061 (`routing` skill states the pinned count; no general rule or check) | 2 |
| Not applied | LL-014 (`tailoring`), 015 (`learning-methodology-selection`), 027, 028, 029, 030, 031, 032, 033, 034, 035, 036, 038, 039 (`implement-story`), 046 (`ucb`, `spec_gate.py`), 047 (`pairwise-preference`, `spec_gate.py`) | 16 |

What this shows:

- **Twelve of the 16 are `implement-story` steps** (LL-027 to 036, 038, 039): approvals committed first, loading the skill, no `hash()` in tests, `uvx` for a missing tool, checking a confirmation, unfiltered omission checks, worktree setup, the no-finding review line, breaking code to see RED, running a spec's worked example, stacked PRs, `approx` on tuples. The skill has none of their ids. This is what IMP-031 said for LL-045 to 048 and LL-041 requires against; it holds for these too.
- **Bucket B is mostly sound:** 24 of 29 are in the named target and 3 more are in code. The earlier "probably applied" reading was right for the older lessons.
- **Conflicts to settle, not just add:** the skill's Step 6 still ends in `--ignore=tests/pmbok` (LL-013), while LL-055 and IMP-044 say run the whole suite. Step 0 says plain `uv sync`, while LL-033 and LL-055 say `uv sync --all-extras` (plus the dev and examples extras). Step 6 and Step 0 need one reading.
- **Two Tier 2 targets name skills that do not exist** (`stage-1`, `ideation`, LL-044). Decide whether to create them or retarget the lesson.
- **Routed:** CR-20261110-001 proposes one edit to `implement-story` for the 12 lessons, Step 6 and Step 0, with the text drafted; it awaits the Sponsor. The skill is not an ADR, BRD, FDD or story, so `stage16_amend.py` does not apply. LL-040 already sits in the `governance` skill; the live gap is that `stage16_amend.py` does not print or check the store path, and `AGENT_LEARNING_LOCAL_STORE_DIR` here points at the socialengage store. That is a tooling change, listed in the CR as separate.
- **IMP overlap:** LL-033, 034 are the cause behind IMP-001 (open); LL-046, 047 behind IMP-021, 024 (open); LL-051 is applied. Fixing the IMPs and the skill together avoids two passes.

## Step 5: Decisions of the Sponsor, 2026-11-10

> **Decision (2026-11-10, Menno Drescher, Project Sponsor):** proposals A and B approved as written ("Approve both A and B proposals"). **Applied on the same day:** A: the Continuous Improvement Register dispositions (seven rolled into Phase Next, four marked as the code shows, fifteen marked `In-Flight Candidate (CR-20261110-002)`) and CR-20261110-002, which fixes the scope and order of the 15 and builds none of them. B: LL-065 to LL-067 appended to the Lessons Learned Register, the identifier crosswalk in its header, index rows for LL-053 to LL-067 (the index had stopped at LL-052), and a correction note on the Stage 17 assessment. No Phase 1 record was renumbered or rewritten.

### A. The 20 open In-Flight improvements (Step 2c)

Proposal: split by what they touch, and add the two new entries.

| Proposed disposition | Entries | Why |
|---|---|---|
| In-flight, one tooling change set (route 2: a change request, then one PR) | IMP-001, 007, 015, 017, 021, 024, 030, 031, 043, 044, 045, 050, 052, 062, 063 | They fix the gate, the spec gate, `complete_story.py`, the skills and the workflow that the accepted lessons keep naming; small; IMP-044 and IMP-031 are already covered by CR-20261110-001 and the Tier 2 backfill |
| Phase Next (route 5: roll in) | IMP-002, 006, 019, 025, 027, 028, 039 | They add features or change an approved FDD (IMP-002 FDD-015, IMP-039 FDD-038) and need their own story or an FDD amendment |
| Already done: update the status | IMP-004, 020, 022, and IMP-016 (partly) | The code exists; a status line change only, by the maintainer |

Not yet checked and not part of this proposal: IMP-044 and IMP-050 as written overlap CR-20261110-001 (the Step 6 edit is done); mark them implemented only after the maintainer reads the merged skill.

### B. F5: Phase 1 lesson ids LL-044, LL-045, LL-046

What the check showed:

- The Phase 1 Stage 15 to 18 records (assessments, Adaptation Plan ADP-20261106-001, SPA-20261106-001, IRP, PCD, the Stage 15 and 17 methodology appendices) use LL-044 to LL-046 for three lessons that the register never received: External Evidence Dependency, Single Source of Truth for Story Status, Dual Evidence Storage. Their full text is in the Stage 15 assessment, section 3.
- The live approved documents that cite LL-044 (Project Charter, Business Case, Ideation Document, Spark Capture, Quality Management Plan) mean the register's LL-044, the Monolithic Ideation Trap, and are correct. The collision is confined to the Phase 1 records.
- The three lessons were acted on in Phase 1 (SPA-20261106-001 for evidence synchronisation; GC-003 and GC-004 as direct changes), so the register lacks lessons that drove real changes.
- LL-046 as Phase 1 wrote it (gate evidence split between `AGENT_LEARNING_LOCAL_STORE_DIR` and `docs/policy-shapes/episodes/`) is the same split found again on 2026-11-10 (the socialengage store); it is still current.

Proposal (no renumbering, no rewriting of dated records):

1. Append the three lessons to the register as **LL-065, LL-066, LL-067**, text taken from the Stage 15 assessment section 3, with a line "Cited as LL-044, LL-045, LL-046 in the Phase 1 records".
2. Add an **identifier crosswalk** to the register header: Phase 1 id to register id (044 to 065, 045 to 066, 046 to 067).
3. Leave the Phase 1 records as they are, with one dated correction note on their entry document (the Stage 17 assessment, whose links `Lessons-Learned-Register.md#ll-046` resolve to the wrong lesson) pointing at the crosswalk.
4. The Tier 2 targets named by the three entries join the Step 2d backfill (Tier 2 for LL-067: the `governance` skill; the other two: `implement-story`).

Alternative: record that the three were never adopted. Not proposed, because the changes they drove exist.

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
- **F3 and F4: decided 2026-11-10 (Menno Drescher, Project Sponsor): processed in the next phase, not in this adaptation.** ADR-022 Invariants 2 and 5 (IMP-053) and ADR-016 Invariant 4 (IMP-054) keep their dispositions "Rolled into Phase Next Intent Refinement" and stay as recorded baseline findings. Neither ADR is amended now; the amendments go through `stage16_amend.py` in the next phase. F4 keeps its open question (change the code or the ADR).
- F4 has low confidence: it is not clear whether the fix is code (add the path) or the ADR (drop the invariant). Flag, do not classify further.
- One adaptation covers all of this (Stage 16/17), as agreed.

- F5 (see Step 5 B for the proposal): the Phase 1 lessons "External Evidence Dependency", "Single Source of Truth for Story Status" and "Dual Evidence Storage" appear in no register entry. Decide whether to register them under new IDs (LL-065 onward) or record that they were never adopted. Corrected references go through the amendment tooling, nothing is re-scored. Files: Stage 15, 16, 17 assessments, ADP-20261106-001, SPA-20261106-001, IRP-20261106-001, Adaptation-Plan.md, and the Stage 15 methodology appendix.

## F1 and F2 checked (2026-11-10)

**F1: HYP-AL-018 means two different things. Confirmed; a Sponsor decision is needed.**

- **Ideation Document section 2.2.3** (and its 2026-10-25 copy in `history/PMP-BL-v1.0.0/`) defines HYP-AL-018 as a linear contextual bandit (LinUCB or LinTS, methodology #24) reaching the autonomy gate faster than `ContextualSoftmaxPolicy`. ADR-038 and FDD-024 use it that way.
- **The Project Charter** (objective 2 and success criterion 2), **the Business Case** (rows for Epic 18, REQ-P2-03, and a hypothesis table row stating a DPO sample-efficiency claim), **the Benefits Management Plan** (BEN-P2-002) and the generated Scope plans use HYP-AL-018 for DPO pairwise preference (Epic 18, ADR-018).
- DPO (#13) has no hypothesis in the Ideation Document (its hypothesis column reads "none"). The DPO claim was written into the Business Case under an id the Ideation Document had already given to another hypothesis.
- Stage 12 already records HYP-AL-018 as Formulated, so the Charter's "formally resolved" criterion for it is not met under either meaning.

**Decision (2026-11-10, Menno Drescher, Project Sponsor): approved. The DPO hypothesis is registered as HYP-AL-028; HYP-AL-018 keeps the LinUCB meaning.** The Ideation Document, Charter, Business Case and Benefits Management Plan changes are carried by the Stage 17 package; none is made yet.

*The proposal as presented:* register the DPO sample-efficiency hypothesis in the Ideation Document as a new id (the next free one is HYP-AL-028; HYP-AL-018 keeps the LinUCB meaning that two ADRs and the Ideation Document use), then repoint the Charter, Business Case and Benefits Management Plan to it; the generated Scope plans are regenerated. The Charter, Business Case and Ideation Document are approved documents, outside the ADR-007 freeze, so this goes in the single Phase 2 close adaptation as a baseline change, accepted by the Sponsor. Alternative: give HYP-AL-018 the DPO meaning and move LinUCB to a new id; this touches two accepted ADRs and FDD-024 as well, so it is not proposed.

**F2: `agent-training-ext/` in the Charter, PMP and plans. Mostly covered; two documents are missing from the package.**

- The folder does not exist; the code is in `src/agent_learning_ext/` (PR #162).
- CR-20261109-001 (section 6) and the Epic 23 package `ADP-20261110-001` (section 7) already carry the change: the PMP is regenerated at `PMP-BL-v1.2.0`, the Charter's boundary wording is a Stage 16 amendment, and the generated plans are regenerated, including the stale references that CR-20261109-002 left for it.
- **Not in that table:** the **Business Case** (11 mentions) and the **Benefits Management Plan** (5). Both are hand-authored approved documents, so a regeneration will not reach them. FDD-023 (2 mentions) stays with Epic 23 and Phase 3.
- *Proposal:* add the Business Case and the Benefits Management Plan to the Stage 17 package with the Charter. No new request is needed. About 157 mentions in current documents remain until that adaptation runs.

## Stage 16 Completion Summary (draft, awaiting the Sponsor's approval of this assessment)

### Processing summary

- **Lessons processed:** 67 (LL-001 to LL-067, including the three registered today); coverage in Steps 2a and 2d.
- **Improvements processed:** 62 entries (IMP-001 to IMP-063; there is no IMP-034); the 24 In-Flight entries checked against the code in Step 2c.
- **Baseline findings:** 5 (F1 to F5), all classified.
- **Governance episodes created:** none. No approved ADR, BRD, FDD or story was edited in this pass, and `stage16_amend.py` was not run.
- **Baseline Revision Packages:** 0. **Subsidiary Plan Amendments:** 0. **Change requests:** CR-20261110-001 (approved and applied, PR #187), CR-20261110-002 (dispositions approved, build pending). `ADP-20261110-001` is an input to Stage 17.

### Decisions made (all by the Project Sponsor, 2026-11-10)

| Item | Decision | Status |
|---|---|---|
| `implement-story` and `heal-contract-failure` skills (12 lessons, Step 6, Step 0) | Approved, CR-20261110-001 | Applied, merged |
| Improvement dispositions (15 in-flight, 7 Phase Next, 4 marked as the code shows) | Approved, proposal A | Applied; build of the 15 pending (CR-20261110-002) |
| Phase 1 lessons LL-044 to LL-046 | Registered as LL-065 to LL-067, crosswalk added, Stage 17 assessment note, proposal B | Applied |
| F3 (ADR-022) and F4 (ADR-016) | Deferred to the next phase | Recorded |
| Stage 16 methodology | Amended to v1.1 | Applied |
| Governance store | Local store merged and committed, 350 episodes, 18 active policies | Applied |

### Open for Stage 17 and the next phase

1. **F1 (approved 2026-11-10):** register HYP-AL-028 for DPO in the Ideation Document and repoint the Charter, Business Case and Benefits Management Plan to it, in the Stage 17 package.
2. **F2:** add the Business Case and the Benefits Management Plan to the `ADP-20261110-001` change table; regenerate the PMP and plans.
3. Build the 15 in-flight tooling changes (CR-20261110-002), starting with IMP-062 and IMP-063.
4. Tier 2 backfill still owed: LL-014, 015, 046, 047, and the entries for LL-065 to LL-067; the Step 2d unapplied list.
5. LL-063: confirm whether the PMP states the unit of its effort figures.
6. Update `Project-Status-Register.md` when the Sponsor approves this assessment.

### Approval

- [x] Stage 16 assessment approved by the Sponsor (Menno Drescher, 2026-11-10: "lets continue and approve the assessment")
- [x] `Project-Status-Register.md` updated (2026-11-10)
- [x] Artifacts committed (this note, CR-20261110-001 and -002, the registers)

## Not done

The changes listed above for Stage 17 and the next phase. Nothing was escalated outside the Sponsor, and no governance episode exists for this pass.
