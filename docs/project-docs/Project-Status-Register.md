---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Cross-Cutting (All Process Groups)"
pmbok_process: "4.3 Direct & Manage Project Work (Orientation Snapshot)"
lifecycle_stage: "Live — tracks whichever stage is currently active"
governance_policy: "none (orientation snapshot, not a governed approval artifact)"
artifact_id: "project-status-register"
version: "1.0 (live — overwritten in place, not re-versioned, every time orientation changes)"
owner: "Menno Drescher (sponsor, project manager and maintainer)"
last_updated: "2026-11-08"
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
| **Current Phase** | Phase 2, "Advanced Agent Learning with Governance-Integrated Feedback Loops" (ACTIVE; PMP baseline PMP-BL-v1.1.0 formalized). Phase 1 is **CLOSED** (2026-11-06 via PCD-20261106-001; IRP-20261106-001 APPROVED). |
| **Current PMP Baseline** | `PMP-BL-v1.1.0` (`Project-Management-Plan.md` v2.0 formalized via `approve-pmp`, episode `31b88dc3-01fc-4e3f-934e-c0be73a8e372`). All 9 subsidiary management plans (Scope, Schedule, Cost, Resource, Stakeholder Engagement, Communications, Procurement, Quality, Risk) are fully validated and updated to v2.0.0 under `PMP-BL-v1.1.0`. |
| **Session close-off checkpoint** | 2026-11-08. Epic 16 (Deterministic UCB Decision Policy) 100% complete across all 6 stories (Stories 16.1–16.6). 62 contract tests passing. PR #130 merged. Step 9 breakout recap complete (LL-046, IMP-021..IMP-023 recorded). Phase rollup: 75 stories implemented, 0 drift rows. Next: Milestone M8 (Epic 17: Scheduled Epsilon-Greedy Policy Baseline) or next prioritized unit. |
| **Current macro Stage** | Phase 1 closed (Stages 11-18 completed). Phase 2 is ACTIVE: **Stages 1 through 8 are COMPLETED & APPROVED**. Active macro stage is **Stage 9: Development / Implementation Pipeline** executing within `src/agent_learning_ext/` on this workstation, while Epic 18 is maintained on the paired workstation under Invariant 6 upstream collision protection. |
| **Last Epic/unit of work fully completed** | Milestone M6 (Epic 14: Lightweight Critique-to-Evidence Ingestion Engine) 100% complete across all 6 stories (PR #121 merged). Epic 16 (Deterministic UCB Decision Policy) 100% complete across all 6 stories (62/62 tests passed, PR #123, #124, #126, #127, #129, #130 merged, Step 9 recap complete). Milestone M7 Stories 18.1–18.5 merged to `main` (PR #125). |
| **Next Epic/unit of work to implement** | Epic 17 (Scheduled Epsilon-Greedy Policy Baseline, Stories 17.1–17.6) or next prioritized unit. Epic 18 remains isolated on separate workstation. |
| **Last commit on the base branch** | `b8fe5cb` Merge pull request #130 from mdresch/feat/story-16.6; `fbfb611` Merge pull request #129 from mdresch/feat/story-16.5; `48d1fd5` Merge pull request #127 from mdresch/feat/story-16.4; `b1ae8ab` Merge pull request #126 from mdresch/feat/story-16.3. |
| **Open side-thread outside the formal loop** | (1) `scripts/spec_gate.py` and `scripts/pr_gate.py` operational on `agent-learning` and propagated to `sidpa-template` (`master` commit `b6367d8`). (2) Zero-touch boundary on Epic 18 on this machine. (3) `scripts/phase_rollup.py` and `.claude/skills/phase-rollup/` verified (0 status drift across 144 stories). |
| **Stage numbering** | The 18 stages are numbered as in sidpa-template `docs/chain-coverage.md`, which is the source of truth; this repo's `docs/intent-to-outcome-chain-coverage.md` follows it (aligned in the governance-alignment PR). Confirm a position against gate records and registers, never a document's own `lifecycle_stage` (template rule 24). Vault notes carry authoring-time labels only. |

## 2. Phase Status

| Phase | Baseline | Status | Closed via |
|---|---|---|---|
| Phase 1: Warm-Start & Confidence-Interval Bandits | `PMP-BL-v1.0.0` | **CLOSED** | **2026-11-06 via PCD-20261106-001** (Stage 18 Intent Refinement COMPLETED, IRP-20261106-001 APPROVED, Phase 2 READY) |
| Phase 2: Advanced Agent Learning with Governance-Integrated Feedback Loops | `PMP-BL-v1.1.0` | **ACTIVE** | Formalized via `approve-pmp` (Episode `31b88dc3...`) |

## 3. Epic/Unit-of-Work Status (all phases)

Not copied here, so it cannot drift: it is generated from `docs/user-stories/epic-*.md` and `implementation-log.md` by `python scripts/phase_rollup.py` (PR #108) and ingested into the Obsidian brain as `Phase-Carry-Over-Backlog`. As of 2026-11-08 it reports 144 stories: 71 implemented, 47 approved and Ready but not implemented, 25 Draft or blocked, 1 superseded, with 0 status-drift rows (`--check` exits 0). The per-story detail stays in `implementation-log.md`. Milestone M6 (Epic 14 Stories 14.1–14.6) fully implemented and verified in `agent-training-ext/`. Milestone M7 (Epic 18 Stories 18.1–18.5) implemented and verified.

## 4. How to keep this current

- **After every Epic's Step 9 recap** (`implement-story`): update §1 ("Last … completed", "Next … to implement", "Session close-off checkpoint").
- **Before starting a new Epic's first story:** confirm "Next … to implement" matches what is about to be worked on.
- **At every Stage 17/18 Phase close:** update §2 and add the new Phase's row.
- **At any natural pause**, not only at epic boundaries: a decision made, a correction applied, before work that takes many steps. A model or session limit does not announce itself.
- **Out-of-loop work** gets one line in "Open side-thread"; do not invent an Epic or Story for it.
- **Confirming a position here:** use merged PRs and commits, `implementation-log.md`, the registers, and the gate episodes in the store at `AGENT_LEARNING_LOCAL_STORE_DIR` (print the resolved path first, `LL-040`; on this machine it points at the socialengage store). Audit records go in `docs/registers/Audit-Register.md` (first audit AUDIT-001 to AUDIT-006 approved 2026-11-04, a bounded sample).
- Not append-only, no version bump per edit: only `last_updated` changes.
