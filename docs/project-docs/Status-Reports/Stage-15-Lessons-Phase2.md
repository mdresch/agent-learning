---
artifact_type: "lesson_learned_assessment"
report_id: "REP-STAGE15-LESSON-PHASE2"
baseline_id: "PMP-BL-v1.1.0"
lifecycle_stage: "Stage 15 (Lesson Learned)"
pmbok_process: "4.4 Manage Project Knowledge (Lessons Learned Register)"
date: "2026-11-10"
governance_policy: "human_review (no resolve-kb-conflict shape is declared here; the maintainer accepts or drops each entry)"
follows: "Stage-14-Insights-Phase2.md (REP-STAGE14-INSIGHT-PHASE2)"
---

# Stage 15 Lessons: Phase 2

> **Maintainer decision, 2026-11-10: LL-060 to LL-064 and IMP-059 to IMP-061 accepted as drafted (Menno Drescher).** A broad pass: each insight is either crystallized into a lesson, already carried elsewhere, or held. Entries are in `Lessons-Learned-Register.md` (LL-060 to LL-064) and `Continuous-Improvement-Register.md` (IMP-059 to IMP-061).

## Insight to lesson

| Insight | Outcome | Entry |
|---|---|---|
| INSIGHT-005 (built is not measured) | Lesson | LL-062 |
| INSIGHT-006 (triage holds real declines) | Carried by Epic 39 (approved, next phase); no lesson | ADR-039 |
| INSIGHT-007 (merge gate passes unfinished checks) | Lesson and improvement | LL-060, IMP-059 |
| INSIGHT-008 (document lists go stale) | Lesson and improvement | LL-061, IMP-060 |
| INSIGHT-009 (failing-first practice) | Carried by IMP-057; no lesson (low confidence) | IMP-057 |
| INSIGHT-010 (stage without input or output) | Lesson and improvement | LL-064, IMP-061 |
| INSIGHT-011 (human days are not agentic forecasts) | Lesson | LL-063 |

## Checks run

- `load_lessons_learned_register()` parses 64 entries; LL-064 is the last. `tests/test_lessons_learned.py`: 5 passed.
- Every new lesson names its insight and observation ids.

## Still open after acceptance

- LL-064 and IMP-061 touch the chain coverage document, so they go through Stage 16/17 as a baseline finding, not a hand edit.
- IMP-059 to IMP-061 are rolled into Phase Next Intent Refinement; none is built yet.
- Tier 2 and Tier 3 propagation is not done; targets are named in the entries and need approval before any skill or template changes.
- Obsidian ingestion has not been run.
