---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Cross-Cutting (All Process Groups)"
pmbok_process: "4.3 Direct & Manage Project Work (Orientation Snapshot)"
lifecycle_stage: "Live — tracks whichever stage is currently active"
governance_policy: "none (orientation snapshot, not a governed approval artifact)"
artifact_id: "project-status-register"
version: "1.0 (live — overwritten in place, not re-versioned, every time orientation changes)"
owner: "Menno Drescher (sponsor, project manager and maintainer)"
last_updated: "2026-11-09"
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
| **Session close-off checkpoint** | 2026-11-09. Epic 38 (Packaged Contextual Learning) is merged to `main` in full: PRs #153 (38.1), #155 (38.2), #158 (38.3), #154 (38.4), #156 (38.5) and #159 (38.6), after the Stage 16 placement correction notes on ADR-038 and FDD-038 in PR #152 (episodes `89ca6a26`, `f16469bd`). Each PR cleared Amazon Q's confirmation and `scripts/pr_gate.py` (margin +0.220 or more). The full suite with no ignores passes on the Story 38.6 tip (2498 passed, 3 skipped). The Epic 38 recap is in PR #160 (merge `4798455`): LL-053 to LL-056, IMP-037 to IMP-044 and the first Code & Methodology Recap. Epic 22 is merged (PR #147). ADR-039, BRD-039, FDD-039 and Epic 39 (shadow-gate learning and the review-finding corpus) are approved and committed on the local branch `docs/adr-039-shadow-gate-learning-and-review-finding-corpus`, not yet pushed; implementation of Epic 39 is scheduled for the next phase. Story 21.6 ("Dispatch and Gradient Exclusion") is implemented on `feat/story-21.6` as PR #157 with the Amazon Q review fixes and the restored `full_authority_excluded` count for episodes with no log-probability; it merges after Q confirms its head and the PR gate passes, and Story 21.7 ("The Real-Data Check") is next. Open decision: Q-159-1 (IMP-039). |
| **Current macro Stage** | Phase 1 closed (Stages 11-18 completed). Phase 2 is ACTIVE: **Stages 1 through 8 are COMPLETED & APPROVED**. Active macro stage is **Stage 9: Development / Implementation Pipeline** executing within `src/agent_learning_ext/` and `agent-training-ext/` under Invariant 6 upstream collision protection. |
| **Last Epic/unit of work fully completed** | Milestone M6 (Epic 14: Lightweight Critique-to-Evidence Ingestion Engine) 100% complete across all 6 stories (39/39 tests passed, PR #121 merged). Epic 16 (Deterministic UCB Decision Policy) 100% complete across all 6 stories (62/62 tests passed, PR #130 merged, Step 9 recap complete). Milestone M7 (Epic 18: Pairwise Preference Optimization) 100% complete across all 6 stories (36/36 tests passed, PR #128 merged, Step 9 recap complete). Milestone M8 (Epic 17: Scheduled Epsilon-Greedy Policy Baseline) 100% complete across all 6 stories (60/60 tests passed, PR #138 merged, Step 9 recap complete). Epic 22 (Scored-Search Decision Configuration Compilation) 100% complete across all 7 stories (Stories 22.1–22.7 passed, PR #147 approved). Epic 38 (Packaged Contextual Learning) 100% complete across all 6 stories (PRs #153, #154, #155, #156, #158, #159 merged; the recap is in PR #160). Pre-Flight Spec Gate and Bayesian PR Gate operational on `main`. |
| **Next Epic/unit of work to implement** | Epic 21 (Contextual Authority Ensemble Routing) / Milestone M9: Stories 21.1 to 21.5 merged; Story 21.6 ("Dispatch and Gradient Exclusion") is in PR #157; Story 21.7 ("The Real-Data Check", concluding Epic 21) is next. Epic 39 (shadow-gate learning and the review-finding corpus) is approved and scheduled for the next phase. Epic 23 and 24 implementation remain blocked pending baseline authorization. |
| **Last commit on the base branch** | `3d318d1` Red Team Learning ADR BRD FDD and User Stories; `a5a0880` docs: record ADR-023 and ADR-024 approvals. |
| **Open side-thread outside the formal loop** | (1) `scripts/spec_gate.py` and `scripts/pr_gate.py` operational on `agent-learning` and propagated to `sidpa-template` (`master` commit `b6367d8`). (2) Zero-touch boundary on Epic 18 on this machine. (3) CR-20261109-001 is pending sponsor/steering committee decision; no baseline change is authorized. (4) Epic 23/24 implementation is blocked pending baseline authorization and their stated prerequisites. |
| **Stage numbering** | The 18 stages are numbered as in sidpa-template `docs/chain-coverage.md`, which is the source of truth; this repo's `docs/intent-to-outcome-chain-coverage.md` follows it (aligned in the governance-alignment PR). Confirm a position against gate records and registers, never a document's own `lifecycle_stage` (template rule 24). Vault notes carry authoring-time labels only. |

## 2. Phase Status

| Phase | Baseline | Status | Closed via |
|---|---|---|---|
| Phase 1: Warm-Start & Confidence-Interval Bandits | `PMP-BL-v1.0.0` | **CLOSED** | **2026-11-06 via PCD-20261106-001** (Stage 18 Intent Refinement COMPLETED, IRP-20261106-001 APPROVED, Phase 2 READY) |
| Phase 2: Advanced Agent Learning with Governance-Integrated Feedback Loops | `PMP-BL-v1.1.0` | **ACTIVE** | Formalized via `approve-pmp` (Episode `31b88dc3...`) |

## 3. Epic/Unit-of-Work Status (all phases)

Not copied here, so it cannot drift: it is generated from `docs/user-stories/epic-*.md` and `implementation-log.md` by `python scripts/phase_rollup.py` (PR #108) and ingested into the Obsidian brain as `Phase-Carry-Over-Backlog`. The latest roll-up reports 158 stories: 94 implemented, 38 approved and Ready but not implemented (carry-over), 25 Draft or blocked, 1 superseded, and 0 status-drift rows (`--check` exits 0). The per-story detail stays in the generated roll-up and source story/log files. Milestones M6 (Epic 14), M7 (Epic 18), and M8 (Epic 17) are fully implemented. Epic 22 (Stories 22.1–22.7) is 100% complete. Stories 21.1–21.6 are implemented.

## 4. How to keep this current

- **After every Epic's Step 9 recap** (`implement-story`): update §1 ("Last … completed", "Next … to implement", "Session close-off checkpoint").
- **Before starting a new Epic's first story:** confirm "Next … to implement" matches what is about to be worked on.
- **At every Stage 17/18 Phase close:** update §2 and add the new Phase's row.
- **At any natural pause**, not only at epic boundaries: a decision made, a correction applied, before work that takes many steps. A model or session limit does not announce itself.
- **Out-of-loop work** gets one line in "Open side-thread"; do not invent an Epic or Story for it.
- **Confirming a position here:** use merged PRs and commits, `implementation-log.md`, the registers, and the gate episodes in the store at `AGENT_LEARNING_LOCAL_STORE_DIR` (print the resolved path first, `LL-040`; on this machine it points at the socialengage store). Audit records go in `docs/registers/Audit-Register.md` (first audit AUDIT-001 to AUDIT-006 approved 2026-11-04, a bounded sample).
- Not append-only, no version bump per edit: only `last_updated` changes.
