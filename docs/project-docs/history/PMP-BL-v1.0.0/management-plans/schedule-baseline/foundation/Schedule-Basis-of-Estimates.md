---
artifact_id: schedule-foundation-basis-of-estimates
parent_plan_id: schedule-management
baseline_id: PMP-BL-v1.0.0
route: foundation_artifact
governance_policy: approve-subsidiary-plan
substage: "6.B-1"
version: "1.0.0"
owner_role: "Project Manager"
depends_on:
  - scope-management
approval_status: approved
---

# Schedule Foundation — Basis of Estimates (`PMP-BL-v1.0.0`)

This artifact satisfies PMBOK 8 §2.3 Develop Schedule step 3 (estimate effort and duration) for the Schedule Management Plan. It governs all rows in [Schedule-Baseline-WBS-Forecast.md](Schedule-Baseline-WBS-Forecast.md). **Activity sequencing (step 4):** [Schedule-Activity-List-Phase1.md](Schedule-Activity-List-Phase1.md) (**6.B-2A**). **Topic pillar ↔ milestone ↔ effort:** [Schedule-Pillar-Overview-and-Trace.md](Schedule-Pillar-Overview-and-Trace.md).

## Estimation unit and capacity

| Item | Value |
| --- | --- |
| **Unit** | Person-day (**pd**); ~6 focused hours per pd |
| **Planning capacity** | ~5 pd per calendar week (maintainer-paced, volunteer project) |
| **Calendar dates** | Not committed; Charter §7 remains indicative windows only |

## Three-point duration and weighted average

For each WBS story id:

- **Low (L):** Optimistic duration with familiar stack and no surprise dependencies.
- **Medium (M):** Most likely; used as planned value (PV) for SPI in the Schedule plan §2.6.
- **High (H):** Adverse case (data gaps, legacy test collection, decommission risk).

**Weighted average (planning):** $\bar{d} = (L + 4M + H) / 6$ (beta-PERT mode).

## Complexity C1–C4 (implementation effort)

| Code | Meaning | Typical story shape |
| --- | --- | --- |
| **C1** | Trivial / superseded | No remaining work |
| **C2** | Standard contract story | Single module, clear AC |
| **C3** | Multi-module or policy math | Bandit, lint profile, BFI |
| **C4** | Cross-cutting or data-heavy | Decommission, real-data replay |

This scale is **not** ADR-003 autonomy tier scoring.

## Inputs and exclusions

| Input | Source |
| --- | --- |
| WBS identities | [Scope-WBS-Dictionary.md](../../scope-baseline/foundation/Scope-WBS-Dictionary.md) |
| Execution bands | Scope §1.5 (Phase 1 Band B vs deferred) |
| Milestone anchors | [Schedule-Management-Plan.md](../../Schedule-Management-Plan.md) §1.2 |

| Exclusion | Rule |
| --- | --- |
| Store-backed velocity | No reads from `LearningStore` for estimates (BRU-026-08) |
| Auto-generated calendar | No wall-clock schedule without Sponsor decision |

## Revision triggers

Re-baseline forecast rows when: Scope WBS changes (Level 2+); story AC materially changes; Epic 34/M4 harness assumptions change; or SPI red on critical path per Schedule plan §2.6.
