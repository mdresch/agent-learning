---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Cross-Cutting (All Process Groups)"
pmbok_process: "4.3 Direct & Manage Project Work (Orientation Snapshot)"
lifecycle_stage: "Live — tracks whichever stage is currently active"
governance_policy: "none (orientation snapshot, not a governed approval artifact)"
artifact_id: "project-status-register"
version: "1.0 (live — overwritten in place, not re-versioned, every time orientation changes)"
owner: "Menno Drescher (sponsor, project manager and maintainer)"
last_updated: "2026-11-10"
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
| **Session close-off checkpoint** | 2026-11-10 (later): the Stage 15 lessons and improvements (LL-060 to LL-064, IMP-059 to IMP-061) were accepted and the Stage 16 assessment (`Status-Reports/Stage-16-Governance-Change-Phase2.md`) was approved by the Sponsor; CR-20261110-001 was applied (PR #187) and CR-20261110-002 fixes the tooling change set. Stage 17 is next and nothing in it is done. Earlier checkpoint of 2026-11-10 follows. Every story of the six Phase 2 baseline epics (14, 16, 18, 21, 22, 38) is implemented, and Epic 17 as well; `phase_rollup.py` lists no unimplemented story in them. Step 9 recaps are held for Epics 38 and 21. Since the last checkpoint: ADR-040 accepted (#170), IMP-046 five gates pinned (#171), CR-20261109-001 Steering Committee approval (#172). On 2026-11-10 the Sponsor moved Epic 23 to Phase 3 so Phase 2 closes once; CR-001 now carries that decision (section 7). In review: #174 (the last two shape-only gates pinned), #175 (CR-001 rescope), #176 (shadow record of agentic effort, learning only). Open: Q-159-1 (IMP-039); IMP-052 (release workflow fails on each push). |
| **Current macro Stage** | Phase 1 closed (Stages 11-18 completed). Phase 2 is ACTIVE: **Stages 1 through 8 are COMPLETED & APPROVED**. **Stage 9: Development / Implementation Pipeline** is functionally complete for the baseline epics, executing within `src/agent_learning_ext/` under Invariant 6 upstream collision protection (the engine formerly in `agent-training-ext/` now lives there; PR #162). No formal Stage 9 exit is recorded yet. Stages 10 to 18 run once for the whole phase. |
| **Last Epic/unit of work fully completed** | Milestone M6 (Epic 14: Lightweight Critique-to-Evidence Ingestion Engine) 100% complete across all 6 stories (39/39 tests passed, PR #121 merged). Epic 16 (Deterministic UCB Decision Policy) 100% complete across all 6 stories (62/62 tests passed, PR #130 merged, Step 9 recap complete). Milestone M7 (Epic 18: Pairwise Preference Optimization) 100% complete across all 6 stories (36/36 tests passed, PR #128 merged, Step 9 recap complete). Milestone M8 (Epic 17: Scheduled Epsilon-Greedy Policy Baseline) 100% complete across all 6 stories (60/60 tests passed, PR #138 merged, Step 9 recap complete). Epic 22 (Scored-Search Decision Configuration Compilation) 100% complete across all 7 stories (Stories 22.1–22.7 passed, PR #147 approved). Epic 38 (Packaged Contextual Learning) 100% complete across all 6 stories (PRs #153, #154, #155, #156, #158, #159 merged; the recap is in PR #160). Epic 21 (Contextual Authority Ensemble Routing) 100% complete across all 7 stories (21.6 via PR #157, 21.7 via PR #167; the recap is held). Pre-Flight Spec Gate and Bayesian PR Gate operational on `main`. |
| **Next Epic/unit of work to implement** | No baseline epic remains. Next is the Phase 2 close, run once: Stages 13 and 14 exist as notes with per-item files (drafts), Stage 15 is accepted and Stage 16 is approved by the Sponsor (Stage 10 verification evidence and the Stage 11 and 12 gates are to be confirmed against their records), then the one Stage 17 adaptation (`ADP-20261110-001` plus the Stage 16 items: HYP-AL-028, the Business Case and Benefits Management Plan boundary wording, CR-20261110-002), then Stage 18 and `PCD-Phase2` (Milestone M10). Epics 23 and 24 (Phase 3) and Epic 39 (next phase) are carried over; the Epic 23 effort, cost and 5 ms analysis is kept as an input in `ADP-20261110-001`. Schedules stay in human-engineering person-days; agentic effort is recorded as a shadow record for learning only. |
| **Last commit on the base branch** | `66d6787` on `main` (2026-11-10), before the Stage 16 approval commit. |
| **Open side-thread outside the formal loop** | (1) `scripts/spec_gate.py` and `scripts/pr_gate.py` operational on `agent-learning` and propagated to `sidpa-template`. (2) Epic 24 is blocked pending its own scope authorization; Epic 23 is Phase 3 scope. (3) The `agent-learn pmbok` commands against ADR-034 Invariant 5 are a held item. (4) PR #173 (Phase 2 demos and methodology ledger entries) is open and not part of this work. |
| **Stage numbering** | The 18 stages are numbered as in sidpa-template `docs/chain-coverage.md`, which is the source of truth; this repo's `docs/intent-to-outcome-chain-coverage.md` follows it (aligned in the governance-alignment PR). Confirm a position against gate records and registers, never a document's own `lifecycle_stage` (template rule 24). Vault notes carry authoring-time labels only. |

## 2. Phase Status

| Phase | Baseline | Status | Closed via |
|---|---|---|---|
| Phase 1: Warm-Start & Confidence-Interval Bandits | `PMP-BL-v1.0.0` | **CLOSED** | **2026-11-06 via PCD-20261106-001** (Stage 18 Intent Refinement COMPLETED, IRP-20261106-001 APPROVED, Phase 2 READY) |
| Phase 2: Advanced Agent Learning with Governance-Integrated Feedback Loops | `PMP-BL-v1.1.0` | **ACTIVE** | Formalized via `approve-pmp` (Episode `31b88dc3...`) |

## 3. Epic/Unit-of-Work Status (all phases)

Not copied here, so it cannot drift: it is generated from `docs/user-stories/epic-*.md` and `implementation-log.md` by `python scripts/phase_rollup.py` (PR #108) and ingested into the Obsidian brain as `Phase-Carry-Over-Backlog`. The latest roll-up (2026-11-10) reports 164 stories: 102 implemented, 36 approved and Ready but not implemented (carry-over), 25 Draft or blocked, 1 superseded, and 0 status-drift rows. The per-story detail stays in the generated roll-up and source story/log files. Milestones M6 to M9 (Epics 14, 18, 16, 21, 22, 38) are fully implemented; Epic 17 as well.

## 4. How to keep this current

- **After every Epic's Step 9 recap** (`implement-story`): update §1 ("Last … completed", "Next … to implement", "Session close-off checkpoint").
- **Before starting a new Epic's first story:** confirm "Next … to implement" matches what is about to be worked on.
- **At every Stage 17/18 Phase close:** update §2 and add the new Phase's row.
- **At any natural pause**, not only at epic boundaries: a decision made, a correction applied, before work that takes many steps. A model or session limit does not announce itself.
- **Out-of-loop work** gets one line in "Open side-thread"; do not invent an Epic or Story for it.
- **Confirming a position here:** use merged PRs and commits, `implementation-log.md`, the registers, and the gate episodes in the store at `AGENT_LEARNING_LOCAL_STORE_DIR` (print the resolved path first, `LL-040`; on this machine it points at the socialengage store). Audit records go in `docs/registers/Audit-Register.md` (first audit AUDIT-001 to AUDIT-006 approved 2026-11-04, a bounded sample).
- Not append-only, no version bump per edit: only `last_updated` changes.
