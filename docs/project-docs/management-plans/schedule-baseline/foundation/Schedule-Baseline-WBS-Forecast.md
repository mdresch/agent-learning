---
artifact_id: schedule-foundation-wbs-forecast
parent_plan_id: schedule-management
baseline_id: PMP-BL-v1.0.0
route: foundation_artifact
governance_policy: approve-subsidiary-plan
substage: "6.B-4"
version: "1.0.0"
owner_role: "Project Manager"
depends_on:
  - scope-management
unit: person-days
approval_status: approved
---

# Schedule Baseline — WBS Duration Forecast (`PMP-BL-v1.0.0`)

Person-day (**pd**) = one maintainer day (~6 focused hours). **Weighted average** per row: $\bar{d} = (L + 4M + H) / 6$ (beta-PERT mode). **Complexity** `C1`–`C4` is implementation effort (not ADR-003 runtime autonomy tier). **Predecessors and Phase 1 sequence:** [Schedule-Activity-List-Phase1.md](Schedule-Activity-List-Phase1.md) (**6.B-2A**); this file holds estimates only.

| Rollup | Value |
| --- | ---: |
| WBS rows | 143 |
| Closed WBS items (30 complete + Story 8.1 superseded) | 31 |
| Remaining — Low total | 181.5 pd |
| Remaining — Medium total | 373.0 pd |
| Remaining — High total | 708.0 pd |
| Remaining — **Weighted total** | **396.9 pd** (~79 weeks at 5 pd/week) |

## Epic rollup (remaining effort)

| Epic | Stories (rem/total) | Low (pd) | Medium (pd) | High (pd) | Weighted remaining (pd) |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | 0/1 | 0.0 | 0.0 | 0.0 | 0.0 |
| 2 | 0/1 | 0.0 | 0.0 | 0.0 | 0.0 |
| 3 | 0/1 | 0.0 | 0.0 | 0.0 | 0.0 |
| 4 | 0/1 | 0.0 | 0.0 | 0.0 | 0.0 |
| 5 | 0/1 | 0.0 | 0.0 | 0.0 | 0.0 |
| 6 | 0/1 | 0.0 | 0.0 | 0.0 | 0.0 |
| 7 | 0/1 | 0.0 | 0.0 | 0.0 | 0.0 |
| 8 | 0/1 | 0.0 | 0.0 | 0.0 | 0.0 |
| 9 | 0/3 | 0.0 | 0.0 | 0.0 | 0.0 |
| 10 | 0/1 | 0.0 | 0.0 | 0.0 | 0.0 |
| 11 | 0/2 | 0.0 | 0.0 | 0.0 | 0.0 |
| 12 | 0/4 | 0.0 | 0.0 | 0.0 | 0.0 |
| 13 | 0/7 | 0.0 | 0.0 | 0.0 | 0.0 |
| 14 | 6/6 | 13.0 | 26.0 | 52.0 | 28.2 |
| 15 | 6/6 | 9.5 | 19.0 | 37.0 | 20.4 |
| 16 | 6/6 | 9.5 | 19.0 | 37.0 | 20.4 |
| 17 | 6/6 | 9.5 | 19.0 | 37.0 | 20.4 |
| 18 | 6/6 | 13.0 | 26.0 | 52.0 | 28.2 |
| 19 | 7/7 | 14.0 | 28.0 | 49.0 | 29.2 |
| 20 | 6/6 | 12.0 | 24.0 | 42.0 | 25.0 |
| 21 | 7/7 | 14.0 | 28.0 | 56.0 | 30.3 |
| 22 | 7/7 | 14.0 | 35.0 | 70.0 | 37.3 |
| 25 | 4/4 | 5.0 | 10.0 | 18.0 | 10.5 |
| 26 | 4/4 | 5.0 | 10.0 | 18.0 | 10.5 |
| 27 | 4/4 | 5.0 | 10.0 | 18.0 | 10.5 |
| 28 | 4/4 | 5.0 | 10.0 | 18.0 | 10.5 |
| 29 | 4/4 | 5.0 | 10.0 | 18.0 | 10.5 |
| 30 | 4/4 | 5.0 | 10.0 | 18.0 | 10.5 |
| 31 | 4/4 | 5.0 | 10.0 | 18.0 | 10.5 |
| 32 | 4/4 | 5.0 | 10.0 | 18.0 | 10.5 |
| 33 | 4/4 | 5.0 | 10.0 | 18.0 | 10.5 |
| 34 | 5/5 | 10.0 | 20.0 | 40.0 | 21.7 |
| 35 | 4/4 | 6.0 | 12.0 | 24.0 | 13.0 |
| 36 | 0/6 | 0.0 | 0.0 | 0.0 | 0.0 |
| 37 | 4/4 | 6.0 | 12.0 | 20.0 | 12.3 |
| 38 | 6/6 | 6.0 | 15.0 | 30.0 | 16.0 |

## Story-level forecast

| WBS | Epic | Complexity | Low (pd) | Medium (pd) | High (pd) | Weighted avg (pd) | Milestone | Status |
| --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| 1.1 | 1 | C2 | 1.0 | 2.0 | 4.0 | 2.17 | — | Complete |
| 2.1 | 2 | C2 | 1.0 | 2.0 | 4.0 | 2.17 | — | Complete |
| 3.1 | 3 | C2 | 1.0 | 2.0 | 4.0 | 2.17 | — | Complete |
| 4.1 | 4 | C2 | 1.0 | 2.0 | 4.0 | 2.17 | — | Complete |
| 5.1 | 5 | C2 | 1.0 | 2.0 | 4.0 | 2.17 | — | Complete |
| 6.1 | 6 | C2 | 1.0 | 2.0 | 4.0 | 2.17 | — | Complete |
| 7.1 | 7 | C2 | 1.0 | 2.0 | 4.0 | 2.17 | — | Complete |
| 8.1 | 8 | C1 | 0.0 | 0.0 | 0.0 | 0.00 | — | Superseded |
| 9.1 | 9 | C3 | 2.0 | 4.0 | 7.0 | 4.17 | — | Complete |
| 9.2 | 9 | C3 | 2.0 | 4.0 | 7.0 | 4.17 | — | Complete |
| 9.3 | 9 | C3 | 2.0 | 4.0 | 7.0 | 4.17 | — | Complete |
| 10.1 | 10 | C2 | 1.0 | 2.0 | 4.0 | 2.17 | — | Complete |
| 11.1 | 11 | C2 | 1.0 | 2.0 | 4.0 | 2.17 | — | Complete |
| 11.2 | 11 | C2 | 1.0 | 2.0 | 4.0 | 2.17 | — | Complete |
| 12.1 | 12 | C3 | 1.0 | 2.0 | 4.0 | 2.17 | — | Complete |
| 12.2 | 12 | C3 | 1.0 | 2.0 | 4.0 | 2.17 | — | Complete |
| 12.3 | 12 | C3 | 1.0 | 2.0 | 4.0 | 2.17 | — | Complete |
| 12.4 | 12 | C3 | 1.0 | 2.0 | 4.0 | 2.17 | — | Complete |
| 13.1 | 13 | C3 | 1.0 | 2.0 | 4.0 | 2.17 | — | Complete |
| 13.2 | 13 | C3 | 1.0 | 2.0 | 4.0 | 2.17 | — | Complete |
| 13.3 | 13 | C3 | 1.0 | 2.0 | 4.0 | 2.17 | — | Complete |
| 13.4 | 13 | C3 | 1.0 | 2.0 | 4.0 | 2.17 | — | Complete |
| 13.5 | 13 | C3 | 1.0 | 2.0 | 4.0 | 2.17 | — | Complete |
| 13.6 | 13 | C3 | 1.0 | 2.0 | 4.0 | 2.17 | — | Complete |
| 13.7 | 13 | C3 | 1.0 | 2.0 | 4.0 | 2.17 | — | Complete |
| 14.1 | 14 | C3 | 2.0 | 4.0 | 8.0 | 4.33 | Phase 2 | Deferred |
| 14.2 | 14 | C3 | 2.0 | 4.0 | 8.0 | 4.33 | Phase 2 | Deferred |
| 14.3 | 14 | C3 | 2.0 | 4.0 | 8.0 | 4.33 | Phase 2 | Deferred |
| 14.4 | 14 | C3 | 2.0 | 4.0 | 8.0 | 4.33 | Phase 2 | Deferred |
| 14.5 | 14 | C4 | 3.0 | 6.0 | 12.0 | 6.50 | Phase 2 | Deferred |
| 14.6 | 14 | C3 | 2.0 | 4.0 | 8.0 | 4.33 | Phase 2 | Deferred |
| 15.1 | 15 | C3 | 1.5 | 3.0 | 6.0 | 3.25 | M3 | Remaining |
| 15.2 | 15 | C3 | 1.5 | 3.0 | 6.0 | 3.25 | M3 | Remaining |
| 15.3 | 15 | C3 | 1.5 | 3.0 | 6.0 | 3.25 | M3 | Remaining |
| 15.4 | 15 | C3 | 1.5 | 3.0 | 6.0 | 3.25 | M3 | Remaining |
| 15.5 | 15 | C3 | 1.5 | 3.0 | 6.0 | 3.25 | M3 | Remaining |
| 15.6 | 15 | C3 | 2.0 | 4.0 | 7.0 | 4.17 | M3 | Remaining |
| 16.1 | 16 | C3 | 1.5 | 3.0 | 6.0 | 3.25 | M3 | Remaining |
| 16.2 | 16 | C3 | 1.5 | 3.0 | 6.0 | 3.25 | M3 | Remaining |
| 16.3 | 16 | C3 | 1.5 | 3.0 | 6.0 | 3.25 | M3 | Remaining |
| 16.4 | 16 | C3 | 1.5 | 3.0 | 6.0 | 3.25 | M3 | Remaining |
| 16.5 | 16 | C3 | 1.5 | 3.0 | 6.0 | 3.25 | M3 | Remaining |
| 16.6 | 16 | C3 | 2.0 | 4.0 | 7.0 | 4.17 | M3 | Remaining |
| 17.1 | 17 | C3 | 1.5 | 3.0 | 6.0 | 3.25 | M3 | Remaining |
| 17.2 | 17 | C3 | 1.5 | 3.0 | 6.0 | 3.25 | M3 | Remaining |
| 17.3 | 17 | C3 | 1.5 | 3.0 | 6.0 | 3.25 | M3 | Remaining |
| 17.4 | 17 | C3 | 1.5 | 3.0 | 6.0 | 3.25 | M3 | Remaining |
| 17.5 | 17 | C3 | 1.5 | 3.0 | 6.0 | 3.25 | M3 | Remaining |
| 17.6 | 17 | C3 | 2.0 | 4.0 | 7.0 | 4.17 | M3 | Remaining |
| 18.1 | 18 | C3 | 2.0 | 4.0 | 8.0 | 4.33 | Phase 2 | Deferred |
| 18.2 | 18 | C3 | 2.0 | 4.0 | 8.0 | 4.33 | Phase 2 | Deferred |
| 18.3 | 18 | C3 | 2.0 | 4.0 | 8.0 | 4.33 | Phase 2 | Deferred |
| 18.4 | 18 | C3 | 2.0 | 4.0 | 8.0 | 4.33 | Phase 2 | Deferred |
| 18.5 | 18 | C3 | 2.0 | 4.0 | 8.0 | 4.33 | Phase 2 | Deferred |
| 18.6 | 18 | C4 | 3.0 | 6.0 | 12.0 | 6.50 | Phase 2 | Deferred |
| 19.1 | 19 | C3 | 2.0 | 4.0 | 7.0 | 4.17 | M2 | Remaining |
| 19.2 | 19 | C3 | 2.0 | 4.0 | 7.0 | 4.17 | M2 | Remaining |
| 19.3 | 19 | C3 | 2.0 | 4.0 | 7.0 | 4.17 | M2 | Remaining |
| 19.4 | 19 | C3 | 2.0 | 4.0 | 7.0 | 4.17 | M2 | Remaining |
| 19.5 | 19 | C3 | 2.0 | 4.0 | 7.0 | 4.17 | M2 | Remaining |
| 19.6 | 19 | C3 | 2.0 | 4.0 | 7.0 | 4.17 | M2 | Remaining |
| 19.7 | 19 | C3 | 2.0 | 4.0 | 7.0 | 4.17 | M2 | Remaining |
| 20.1 | 20 | C3 | 2.0 | 4.0 | 7.0 | 4.17 | M2 | Remaining |
| 20.2 | 20 | C3 | 2.0 | 4.0 | 7.0 | 4.17 | M2 | Remaining |
| 20.3 | 20 | C3 | 2.0 | 4.0 | 7.0 | 4.17 | M2 | Remaining |
| 20.4 | 20 | C3 | 2.0 | 4.0 | 7.0 | 4.17 | M2 | Remaining |
| 20.5 | 20 | C3 | 2.0 | 4.0 | 7.0 | 4.17 | M2 | Remaining |
| 20.6 | 20 | C3 | 2.0 | 4.0 | 7.0 | 4.17 | M2 | Remaining |
| 21.1 | 21 | C4 | 2.0 | 4.0 | 8.0 | 4.33 | Foundation | Remaining |
| 21.2 | 21 | C4 | 2.0 | 4.0 | 8.0 | 4.33 | Foundation | Remaining |
| 21.3 | 21 | C4 | 2.0 | 4.0 | 8.0 | 4.33 | Foundation | Remaining |
| 21.4 | 21 | C4 | 2.0 | 4.0 | 8.0 | 4.33 | Foundation | Remaining |
| 21.5 | 21 | C4 | 2.0 | 4.0 | 8.0 | 4.33 | Foundation | Remaining |
| 21.6 | 21 | C4 | 2.0 | 4.0 | 8.0 | 4.33 | Foundation | Remaining |
| 21.7 | 21 | C4 | 2.0 | 4.0 | 8.0 | 4.33 | Foundation | Remaining |
| 22.1 | 22 | C4 | 2.0 | 5.0 | 10.0 | 5.33 | Foundation | Remaining |
| 22.2 | 22 | C4 | 2.0 | 5.0 | 10.0 | 5.33 | Foundation | Remaining |
| 22.3 | 22 | C4 | 2.0 | 5.0 | 10.0 | 5.33 | Foundation | Remaining |
| 22.4 | 22 | C4 | 2.0 | 5.0 | 10.0 | 5.33 | Foundation | Remaining |
| 22.5 | 22 | C4 | 2.0 | 5.0 | 10.0 | 5.33 | Foundation | Remaining |
| 22.6 | 22 | C4 | 2.0 | 5.0 | 10.0 | 5.33 | Foundation | Remaining |
| 22.7 | 22 | C4 | 2.0 | 5.0 | 10.0 | 5.33 | Foundation | Remaining |
| 25.1 | 25 | C2 | 1.0 | 2.0 | 4.0 | 2.17 | Program | Remaining |
| 25.2 | 25 | C2 | 1.0 | 2.0 | 4.0 | 2.17 | Program | Remaining |
| 25.3 | 25 | C2 | 1.5 | 3.0 | 5.0 | 3.08 | Program | Remaining |
| 25.4 | 25 | C2 | 1.5 | 3.0 | 5.0 | 3.08 | Program | Remaining |
| 26.1 | 26 | C2 | 1.0 | 2.0 | 4.0 | 2.17 | Program | Remaining |
| 26.2 | 26 | C2 | 1.0 | 2.0 | 4.0 | 2.17 | Program | Remaining |
| 26.3 | 26 | C2 | 1.5 | 3.0 | 5.0 | 3.08 | Program | Remaining |
| 26.4 | 26 | C2 | 1.5 | 3.0 | 5.0 | 3.08 | Program | Remaining |
| 27.1 | 27 | C2 | 1.0 | 2.0 | 4.0 | 2.17 | Program | Remaining |
| 27.2 | 27 | C2 | 1.0 | 2.0 | 4.0 | 2.17 | Program | Remaining |
| 27.3 | 27 | C2 | 1.5 | 3.0 | 5.0 | 3.08 | Program | Remaining |
| 27.4 | 27 | C2 | 1.5 | 3.0 | 5.0 | 3.08 | Program | Remaining |
| 28.1 | 28 | C2 | 1.0 | 2.0 | 4.0 | 2.17 | Program | Remaining |
| 28.2 | 28 | C2 | 1.0 | 2.0 | 4.0 | 2.17 | Program | Remaining |
| 28.3 | 28 | C2 | 1.5 | 3.0 | 5.0 | 3.08 | Program | Remaining |
| 28.4 | 28 | C2 | 1.5 | 3.0 | 5.0 | 3.08 | Program | Remaining |
| 29.1 | 29 | C2 | 1.0 | 2.0 | 4.0 | 2.17 | Program | Remaining |
| 29.2 | 29 | C2 | 1.0 | 2.0 | 4.0 | 2.17 | Program | Remaining |
| 29.3 | 29 | C2 | 1.5 | 3.0 | 5.0 | 3.08 | Program | Remaining |
| 29.4 | 29 | C2 | 1.5 | 3.0 | 5.0 | 3.08 | Program | Remaining |
| 30.1 | 30 | C2 | 1.0 | 2.0 | 4.0 | 2.17 | Program | Remaining |
| 30.2 | 30 | C2 | 1.0 | 2.0 | 4.0 | 2.17 | Program | Remaining |
| 30.3 | 30 | C2 | 1.5 | 3.0 | 5.0 | 3.08 | Program | Remaining |
| 30.4 | 30 | C2 | 1.5 | 3.0 | 5.0 | 3.08 | Program | Remaining |
| 31.1 | 31 | C2 | 1.0 | 2.0 | 4.0 | 2.17 | Program | Remaining |
| 31.2 | 31 | C2 | 1.0 | 2.0 | 4.0 | 2.17 | Program | Remaining |
| 31.3 | 31 | C2 | 1.5 | 3.0 | 5.0 | 3.08 | Program | Remaining |
| 31.4 | 31 | C2 | 1.5 | 3.0 | 5.0 | 3.08 | Program | Remaining |
| 32.1 | 32 | C2 | 1.0 | 2.0 | 4.0 | 2.17 | Program | Remaining |
| 32.2 | 32 | C2 | 1.0 | 2.0 | 4.0 | 2.17 | Program | Remaining |
| 32.3 | 32 | C2 | 1.5 | 3.0 | 5.0 | 3.08 | Program | Remaining |
| 32.4 | 32 | C2 | 1.5 | 3.0 | 5.0 | 3.08 | Program | Remaining |
| 33.1 | 33 | C2 | 1.0 | 2.0 | 4.0 | 2.17 | Program | Remaining |
| 33.2 | 33 | C2 | 1.0 | 2.0 | 4.0 | 2.17 | Program | Remaining |
| 33.3 | 33 | C2 | 1.5 | 3.0 | 5.0 | 3.08 | Program | Remaining |
| 33.4 | 33 | C2 | 1.5 | 3.0 | 5.0 | 3.08 | Program | Remaining |
| 34.1 | 34 | C4 | 2.0 | 4.0 | 8.0 | 4.33 | Program | Remaining |
| 34.2 | 34 | C4 | 2.0 | 4.0 | 8.0 | 4.33 | Program | Remaining |
| 34.3 | 34 | C4 | 2.0 | 4.0 | 8.0 | 4.33 | Program | Remaining |
| 34.4 | 34 | C4 | 2.0 | 4.0 | 8.0 | 4.33 | Program | Remaining |
| 34.5 | 34 | C4 | 2.0 | 4.0 | 8.0 | 4.33 | Program | Remaining |
| 35.1 | 35 | C3 | 1.5 | 3.0 | 6.0 | 3.25 | Program | Remaining |
| 35.2 | 35 | C3 | 1.5 | 3.0 | 6.0 | 3.25 | Program | Remaining |
| 35.3 | 35 | C3 | 1.5 | 3.0 | 6.0 | 3.25 | Program | Remaining |
| 35.4 | 35 | C3 | 1.5 | 3.0 | 6.0 | 3.25 | Program | Remaining |
| 36.1 | 36 | C3 | 1.5 | 3.0 | 5.0 | 3.08 | — | Complete |
| 36.2 | 36 | C3 | 1.5 | 3.0 | 5.0 | 3.08 | — | Complete |
| 36.3 | 36 | C3 | 1.5 | 3.0 | 5.0 | 3.08 | — | Complete |
| 36.4 | 36 | C3 | 1.5 | 3.0 | 5.0 | 3.08 | — | Complete |
| 36.5 | 36 | C3 | 1.5 | 3.0 | 5.0 | 3.08 | — | Complete |
| 36.6 | 36 | C3 | 1.5 | 3.0 | 5.0 | 3.08 | — | Complete |
| 37.1 | 37 | C3 | 1.5 | 3.0 | 5.0 | 3.08 | Program | Remaining |
| 37.2 | 37 | C3 | 1.5 | 3.0 | 5.0 | 3.08 | Program | Remaining |
| 37.3 | 37 | C3 | 1.5 | 3.0 | 5.0 | 3.08 | Program | Remaining |
| 37.4 | 37 | C3 | 1.5 | 3.0 | 5.0 | 3.08 | Program | Remaining |
| 38.1 | 38 | C3 | 1.0 | 2.5 | 5.0 | 2.67 | Program | Remaining |
| 38.2 | 38 | C3 | 1.0 | 2.5 | 5.0 | 2.67 | Program | Remaining |
| 38.3 | 38 | C3 | 1.0 | 2.5 | 5.0 | 2.67 | Program | Remaining |
| 38.4 | 38 | C3 | 1.0 | 2.5 | 5.0 | 2.67 | Program | Remaining |
| 38.5 | 38 | C3 | 1.0 | 2.5 | 5.0 | 2.67 | Program | Remaining |
| 38.6 | 38 | C3 | 1.0 | 2.5 | 5.0 | 2.67 | Program | Remaining |
