# Agent Training Extension (`agent-training-ext`)

## Context & Purpose
This package (`agent-training-ext/`) hosts custom algorithmic extensions, critique ingestion, and preference learning pipelines for **Phase 2: Autonomous Feedback Loops & Extensible Architecture** under minor baseline increment `PMP-BL-v1.1.0`.

It isolates Phase 2 functionality:
- **Milestone M6 (Epic 14):** Lightweight Critique-to-Evidence Ingestion Engine
  - **Story 14.1:** Tag Grammar and Parser (`parse_critique`, `rubric_delta`, `CritiqueDelta`)
  - **Stories 14.2 & 14.3:** Moving Pooled Support by Delta and Traceability/Doubt (`apply_critique`, `AppliedCritique`)
  - **Story 14.4:** Episode Metadata (`to_episode_metadata`)
  - **Story 14.6:** Pre-calibrated Delta Rubric (`RUBRIC_TABLE`, version "1")

## Upstream Fork Collision Protection Architecture (Invariant 6)
Per project architecture directive (`BEN-P2-004`, `HYP-AL-026`):
The core Microsoft codebase in `src/agent_learning` remains 100% clean (0 lines diff against upstream `microsoft/agent-learning`). All Phase 2 custom extensions reside in `agent-training-ext/` and interface solely with frozen public dataclasses and resolvers (`agent_learning.decision.DecisionFrame`, `DecisionOption`, `EvidencePoint`, `DecisionResolver`).

## Standard Library Purity (Invariant 4)
All modules in `agent-training-ext/` adhere strictly to standard library purity:
- Standard library modules only (`math`, `re`, `dataclasses`, `typing`, `collections`, `json`).
- Zero imports from `agent_learning.storage`.
- Zero file, socket, or network I/O.
