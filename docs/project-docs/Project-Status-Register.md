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
| **Session close-off checkpoint** | 2026-11-10. Story 21.7 ("The Real-Data Check", the last story of Epic 21) is implemented on `feat/story-21.7` (commit `1b60f24`): the router run over the three committed approval policies and the 227 committed episodes shows every recorded gate in `PINNED_FULL` routes full, no episode carries a routing record, and nothing is claimed about cost or latency; it merges after Amazon Q confirms its head and the PR gate passes, and the Epic 21 recap follows. Merged since the last checkpoint: PR #157 (Story 21.6, with the restored `full_authority_excluded` count), #162 (the Epic 14 engine moved into `agent_learning_ext`), #163 (the Sponsor's approval of CR-20261109-001), #164 (26 Stage 16 amendments under CR-20261109-002), #165 (ADR-039, BRD-039, FDD-039 and Epic 39, implementation scheduled for the next phase) and #166 (ADR-040, still Proposed). Open: Q-159-1 (IMP-039); five gate tasks in the episodes are not in `PINNED_FULL` (found by Story 21.7); ADR-040's file reads Proposed while the store holds an approve-adr episode `69365299` for it. |
| **Current macro Stage** | Phase 1 closed (Stages 11-18 completed). Phase 2 is ACTIVE: **Stages 1 through 8 are COMPLETED & APPROVED**. Active macro stage is **Stage 9: Development / Implementation Pipeline** executing within `src/agent_learning_ext/` and `agent-training-ext/` under Invariant 6 upstream collision protection. |
| **Last Epic/unit of work fully completed** | Milestone M6 (Epic 14: Lightweight Critique-to-Evidence Ingestion Engine) 100% complete across all 6 stories (39/39 tests passed, PR #121 merged). Epic 16 (Deterministic UCB Decision Policy) 100% complete across all 6 stories (62/62 tests passed, PR #130 merged, Step 9 recap complete). Milestone M7 (Epic 18: Pairwise Preference Optimization) 100% complete across all 6 stories (36/36 tests passed, PR #128 merged, Step 9 recap complete). Milestone M8 (Epic 17: Scheduled Epsilon-Greedy Policy Baseline) 100% complete across all 6 stories (60/60 tests passed, PR #138 merged, Step 9 recap complete). Epic 22 (Scored-Search Decision Configuration Compilation) 100% complete across all 7 stories (Stories 22.1–22.7 passed, PR #147 approved). Epic 38 (Packaged Contextual Learning) 100% complete across all 6 stories (PRs #153, #154, #155, #156, #158, #159 merged; the recap is in PR #160). Epic 21 (Contextual Authority Ensemble Routing): Stories 21.1 to 21.6 merged (21.6 via PR #157) and Story 21.7 implemented (commit `1b60f24`), complete once its PR merges. Pre-Flight Spec Gate and Bayesian PR Gate operational on `main`. |
| **Next Epic/unit of work to implement** | Milestone M9 closes when Story 21.7 merges and the Epic 21 recap is held. Then Milestone M10 (Phase 2 close: full regression, upstream fork check, `PCD-Phase2`) is open, and CR-20261109-001 (Epic 23 into Phase 2) awaits the Steering Committee decision and its Stage 17 package. Epic 39 is scheduled for the next phase. Epic 24 implementation remains blocked pending baseline authorization. |
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
