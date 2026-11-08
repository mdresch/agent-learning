---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Monitoring & Controlling / Adaptive Closing"
pmbok_process: "4.6 Perform Integrated Change Control & Tailoring"
lifecycle_stage: "Stage 17 (Adaptation)"
governance_policy: "approve-adaptation-plan"
pmp_baseline: "PMP-BL-v1.0.0"
version: "0.1 (draft, not approved)"
date: "2026-11-04"
inputs:
  - "Audit-Register.md findings (AUDIT-001 to AUDIT-006, approved 2026-11-04)"
  - "Stage 12 Actual Outcome Assessment, Observations OBS-001 to OBS-009, Insights INSIGHT-001 to INSIGHT-004"
  - "Lessons-Learned-Register.md LL-040 to LL-043 and Continuous-Improvement-Register.md IMP-014"
process: "Operationalize governance changes into behavioral/skill updates and tailor management plan updates"
outputs:
  - "Adaptation-Plan.md"
---

# Adaptation Plan: Phase 1 close

> **Governance Policy:** `approve-adaptation-plan` | **Lifecycle Stage:** `Stage 17 (Adaptation)` | **Baseline:** `PMP-BL-v1.0.0`
> Draft for the human to review. It approves nothing and changes no management plan.

## Stage 16 status (read this first)

The Stage 16 pipeline (`classify-diff-type`, `escalate-diff-response`) has **no episode** in the store at `AGENT_LEARNING_LOCAL_STORE_DIR` (0 and 0 on 2026-11-04). The governance changes made during Phase 1 (the sidpa-template alignment, the Project Status Register, the skill edits below) were not classified through it. ADR-008 expects Stage 17 to respond to an accepted Stage 16 amendment, so this plan has no such input. That is recorded as a gap, not filled: no Stage 16 episode is backfilled. The amendments below are therefore **proposed**, and each needs its own Stage 16 classification (run prospectively, with a human decision) before this plan can honestly be approved.

## Triggering Governance Changes

| ID | Change | Origin | State |
|---|---|---|---|
| A1 | Rules added to `governance`, `implement-story`, `heal-contract-failure` and `intent-refinement` skills (LL-040, LL-042, LL-043) | Stage 15 lessons | Made, in PR #117 (not merged); no Stage 16 episode |
| A2 | Move the Stage 18 tooling onto the path ADR-034 keeps, or amend ADR-034 to keep it | IMP-014, INSIGHT-003, AUDIT-004, OBS-009 | Proposed, not made |
| A3 | Make the status update part of the commit sequence: `implement-story` Step 7 sets the story's `Status` to `Completed (date)` in its epic file and runs `phase_rollup.py --check` with no drift row for that story; `complete_story.py done` is the later automation (IMP-011). The one-off reconciliation of the 15 existing drift rows is done (2026-11-04, see `implementation-log.md`); the rule is not. | AUDIT-006, INSIGHT-002, IMP-011 | Proposed, not made |

## Scope of Behavioral / Tooling Adaptation

- **Workflow / Process Adjustments:** A phase-close stage is not run until its tests have been run under `uv run` in a clean environment and the result reported (A1, LL-043). Governance commands print and count the store before and after (A1, LL-040). A story is not finished until its `Status` line says Completed and the roll-up shows no drift row for it, in the same Step 7 sequence as the log entry (A3). The 15 existing drift rows were reconciled on 2026-11-04.
- **Agent Skill / Tooling Updates:** the four skill edits in A1 are made. A3 changes `implement-story` Step 7 and the definition of done (Tier 2); automating it in `scripts/complete_story.py done` is code and needs its own story. A2 is not: it needs either a port of `evaluate_phase_close_readiness`, hypothesis adjudication and `seed-next` into `src/agent_learning/pmbok/`, or an ADR-034 amendment. Until one is chosen, `scripts/orchestrate_pmbok.py` cannot be imported in the project environment (OBS-009), so `--mode adapt` and `--mode seed-next` are unavailable.
- **Environmental / Configuration Changes:** none made. CI keeps `--ignore=tests/pmbok` (AUDIT-004).

## Governance Change Impact Matrix

Assessment by the assistant from the records above, for the human to correct; not measured.

| Amendment / Change | Scope (5.1) | Schedule (6.1) | Cost (7.1) | Quality (8.1) | Resource (9.1) | Comms (10.1) | Risk (11.1) | Procurement (12.1) | Stakeholder (13.2) |
|---|---|---|---|---|---|---|---|---|---|
| A1 skill rules | None | None | None | Medium | Low | None | Low | None | None |
| A2 Stage 18 tooling | Low | Medium | Low | High | Medium | None | Medium | None | None |
| A3 status in the commit sequence | None | None | None | Medium | Low | Low | Low | None | None |

## Tailored Subsidiary Management Plan Updates (Feeding back to PMP)

- [ ] **Scope Management Plan:** A2 adds a port or an ADR-034 amendment to Phase Next scope.
- [ ] **Schedule Management Plan:** A2 needs a slot before Stage 18 can run its tooling.
- [ ] **Cost Management Plan:** none.
- [ ] **Quality Management Plan:** the run-before-stage rule (LL-043).
- [ ] **Resource Management Plan:** none beyond the skill text in A1.
- [ ] **Communications Management Plan:** none.
- [ ] **Risk Management Plan:** new risk: a phase-close stage depends on code CI does not run (INSIGHT-003).
- [ ] **Procurement Management Plan:** none.
- [ ] **Stakeholder Engagement Plan:** none.

The boxes are left unchecked on purpose. The subsidiary plans and the PMP are generated by the orchestrator, and `--mode adapt` cannot run (see above), so this plan does not hand-edit them. The baseline stays `PMP-BL-v1.0.0`. A new baseline (`PMP-BL-v1.1.0`) is cut only when the plans are regenerated and `approve-pmp` is run.

## Rollback & Recovery Pathway

A1 is a text change to four skill files and is reverted with `git revert` of its commit (`9c0df07`, `7b20438`). A2 and A3 change no baseline; A3's skill text is reverted the same way. No `PMP-BL` archive exists to restore from, because no new baseline is cut.

## Verification & Rollout Gates

- A1: `grep -c "LL-0xx"` finds each id in its Tier 2 file (LL-040, LL-042, LL-043 pass on 2026-11-04); the lessons tests pass.
- A2: the Stage 18 readiness and adjudication code imports under `uv run` with no missing dependency, and has a test that CI runs (the legacy `tests/pmbok/test_intent_refinement.py` was deleted on 2026-11-04).
- A3: `grep -c "phase_rollup" .claude/skills/implement-story/SKILL.md` finds the new Step 7 rule; the next story logged shows no drift row for itself; `python scripts/phase_rollup.py --check` already exits 0 after the one-off reconciliation.

## What this is not yet

Stage 17 only. It does not decide whether HYP-AL-008 and HYP-AL-009 are validated, whether Phase 2 proceeds, or what the next phase's intent is; those belong to Stage 18 (`approve-intent-refinement`).
