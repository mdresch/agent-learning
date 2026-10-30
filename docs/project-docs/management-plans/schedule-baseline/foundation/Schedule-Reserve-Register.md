---
artifact_id: schedule-foundation-reserve-register
parent_plan_id: schedule-management
baseline_id: PMP-BL-v1.0.0
route: foundation_artifact
governance_policy: approve-subsidiary-plan
substage: "6.B-3"
version: "1.0.0"
owner_role: "Project Manager"
depends_on:
  - scope-management
approval_status: approved
---

# Schedule Foundation — Reserve Register (`PMP-BL-v1.0.0`)

Buffers and contingency for schedule risk (PMBOK 8 §2.3.5 Table 2-7: sufficient buffers for known-unknowns). Durations in **pd**.

## Management reserve (milestone)

| Reserve id | Amount (pd) | Holder | Purpose | Consumption rule |
| --- | ---: | --- | --- | --- |
| **SR-M5-01** | 5 | Project Manager | Bayes recalculation, peer review, M5 synthesis | Log in `implementation-log.md`; Sponsor approves extension beyond 5 pd |

## Contingency (epic triggers)

Contingency is **not** added to every story; it is invoked when the **High** estimate driver materializes.

| Trigger | Epic / milestone | Contingency (pd) | When to apply |
| --- | --- | ---: | --- |
| Legacy test collection | Epic **34** before **M4** | up to **8** (Epic 34 High rollup) | If `tests/pmbok` or legacy tree blocks full suite green |
| Real-data validation | **14.5**, **18.6**, **19.7**, **20.6** | per story High − Medium | Only when Band C authorized and data available |
| Schedule slip | Critical path | **SR-M5-01** first | Then `approve-adaptation-plan` or BFI |

## Float summary

| Element | Float note |
| --- | --- |
| **M0.5** | Parallel to M1–M4 chain; must complete before **M5** |
| **Non-critical program epics** | Bands D–E; no calendar float assigned until scheduled |

## Change control

Adding a new reserve row or increasing **SR-M5-01** requires Schedule plan amendment (Level 2+) and marks Cost / Resource / Risk **STALE_DEPENDENCY** per ADR-013.
