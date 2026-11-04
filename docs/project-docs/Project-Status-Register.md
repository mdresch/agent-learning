---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Cross-Cutting (All Process Groups)"
pmbok_process: "4.3 Direct & Manage Project Work (Orientation Snapshot)"
lifecycle_stage: "Live — tracks whichever stage is currently active"
governance_policy: "none (orientation snapshot, not a governed approval artifact)"
artifact_id: "project-status-register"
version: "1.0 (live — overwritten in place, not re-versioned, every time orientation changes)"
owner: "Menno Drescher (sponsor, project manager and maintainer)"
last_updated: "2026-11-04"
origin: "Instantiated from sidpa-template docs/registers/Project-Status-Register.template.md (commit e97e8a3)"
---

# Project Status Register — agent-learning

> **Purpose:** answer in under a minute: which Phase and Stage is this project at, what just finished, what is
> next. A model resuming after a session or model limit reads this first, then the evidence it cites.
>
> **Not a governed approval artifact** (no `approve-*` policy gates it) and **not append-only**: overwrite in
> place at every natural pause, not only at epic boundaries. It records no approval and certifies no gate.

## 1. Current Orientation (read this first)

| Field | Value |
|---|---|
| **Current Phase** | Phase 1, "Warm-Start & Confidence-Interval Bandits" (`Project-Charter.md` v1.9, Approved). Phase 1 is open: it closes on a recorded Phase 2 go/no-go decision, and no Stage 17 or 18 record exists. |
| **Current PMP Baseline** | `PMP-BL-v1.0.0` (`Project-Management-Plan.md` header: Approved, baseline formalized; `Status-Reports/Baseline-Formalization-Notice-PMP-BL-v1.0.0.md`). |
| **Session close-off checkpoint** | 2026-11-04. Epic 20 is complete and merged (Story 20.6 in PR #101; recap in PR #107, base commit `da6d537`). In flight, outside any epic: the Stage 17/18 roll-up of Phase 1. Merged for it: Obsidian vault sync (`obsidian-second-brain` `9349e10`) and the sidpa-template governance changes (PR #2, then `e97e8a3`). Open: PR #108 (`scripts/phase_rollup.py`, the carry-over backlog generator) and the PR that adds this register. No Stage 17 or 18 gate has been run. Evidence is cited from merged PRs, `implementation-log.md` and the gate episodes, not from any document's own `lifecycle_stage`. |
| **Current macro Stage** | Project level: Stages 1 to 8 have their documents, and Stage 9 (Deliverable) is the active stage for the carry-over stories. The gates `approve-ideation`, `approve-charter` and `approve-business-case` have registered policies but **zero recorded episodes** (checked 2026-11-04), and they are not to be backfilled: that is a recorded gap, not an approval. Stage 11 (audit record) has none. The formal Stage 15 review has not been held (the ADR-010 light recap per epic stands in; it is not Stage 15). Stages 17 and 18 have not started. Epic level: no epic is mid-implementation. |
| **Last Epic/unit of work fully completed** | Epic 20 (Explicit Policy Prior Warm-Starting), Stories 20.1 to 20.6. Closing evidence: `LL-041`, `LL-042` and the Epic 20 entry in the Recap Log of `Continuous-Improvement-Register.md`, IMP-009 to IMP-013 (all `Rolled into Phase Next Intent Refinement`), PR #107. |
| **Next Epic/unit of work to implement** | **Not decided.** `python scripts/phase_rollup.py` (PR #108) lists the carry-over: 60 stories approved and Ready (Epics 14, 16, 17, 18, 21, 22 and 38, plus 16 stories across Epics 26 to 33 and 35) and 25 stories whose epic is approved but which are Draft or blocked on your confirmations. Story 21.7's acceptance criterion names a store that is git-ignored; amend its wording when 21.7 is implemented (FDD-019 §7 item 11, FDD-020 §7 item 7). |
| **Last commit on the base branch** | `da6d537` Merge pull request #107 (Epic 20 recap and Tier 2 propagation). |
| **Open side-thread outside the formal loop** | (1) `scripts/phase_rollup.py` and `.claude/skills/phase-rollup/` (PR #108) were built from a maintainer request, with no ADR, BRD, FDD or story; recorded under "Tooling" in `implementation-log.md`. (2) `obsidian-second-brain/scripts/ingest-agent-learning.mjs` now ingests the Continuous Improvement Register. (3) Five leftover worktrees from earlier story runs exist beside the repo (`agent-learning-story-11.1`, `11.2`, `19.6`, `19.7`, `26.1`); under `LL-042` each is a started run to inspect, and none has been inspected or removed. |
| **Stage-label overload caveat** | Two documents number the 18 stages differently. This repo's `docs/intent-to-outcome-chain-coverage.md` says 8 Implementation Readiness, 9 Deliverable, 15 Lesson Learned, 16 Governance Change, 17 Adaptation, 18 Intent Refinement. sidpa-template's `docs/second-brain-lifecycle-and-scripts.md` says 9 Readiness Gate, 15 Diagnostic Insights, 16 Lessons Learned, 17 Governance Change, 18 Adaptation & Intent Refinement. In this project use the chain-coverage numbering; the `intent-refinement` skill's preconditions (Stage 9 deliverables, Stage 11 audit, Stage 15 lessons) follow it. Vault notes carry their own `lifecycle_stage` labels, which are authoring-time labels only. |

## 2. Phase Status

| Phase | Baseline | Status | Closed via |
|---|---|---|---|
| Phase 1: Warm-Start & Confidence-Interval Bandits | `PMP-BL-v1.0.0` | Open | Not closed. Needs the Stage 17 Adaptation Plan and Stage 18 Intent Refinement records and a recorded Phase 2 go/no-go. |

## 3. Epic/Unit-of-Work Status (all phases)

Not copied here, so it cannot drift: it is generated from `docs/user-stories/epic-*.md` and `implementation-log.md` by `python scripts/phase_rollup.py` (PR #108) and ingested into the Obsidian brain as `Phase-Carry-Over-Backlog`. As of 2026-11-04 it reports 144 stories: 58 implemented, 60 approved and Ready but not implemented, 25 Draft or blocked, 1 superseded, with 15 status-drift rows (`--check`). The per-story detail stays in `implementation-log.md`.

## 4. How to keep this current

- **After every Epic's Step 9 recap** (`implement-story`): update §1 ("Last … completed", "Next … to implement", "Session close-off checkpoint").
- **Before starting a new Epic's first story:** confirm "Next … to implement" matches what is about to be worked on.
- **At every Stage 17/18 Phase close:** update §2 and add the new Phase's row.
- **At any natural pause**, not only at epic boundaries: a decision made, a correction applied, before work that takes many steps. A model or session limit does not announce itself.
- **Out-of-loop work** gets one line in "Open side-thread"; do not invent an Epic or Story for it.
- **Confirming a position here:** use merged PRs and commits, `implementation-log.md`, the registers, and the gate episodes in the store at `AGENT_LEARNING_LOCAL_STORE_DIR` (print the resolved path first, `LL-040`; on this machine it points at the socialengage store). This project has no `Audit-Register.md`.
- Not append-only, no version bump per edit: only `last_updated` changes.
