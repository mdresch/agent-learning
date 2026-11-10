# INSIGHT-006: The review triage holds real accept and decline decisions that the gate history lacks

- **Insight type:** ArchitecturalInsight
- **Recorded:** 2026-11-10 (Stage 14, Phase 2, interpretation of the cited observations)
- **Impact level:** Medium
- **Applicable subsystems:** review triage, Epic 39
- **Derived from:** OBS-013
- **Phase 2 id:** INSIGHT-P2-02 in `Stage-14-Insights-Phase2.md`
- **Confidence:** Medium. Nothing has been run; that the lines are usable as pairs is untested.
- **Goes to:** Epic 39 (already approved, next phase); no new entry.

## Finding

The 249 triage lines record a human declining 62 times, each with a claim type and a verified status, so they are a candidate source of preference pairs and rejection labels. Unlike the approve-* history they contain refusals. This is the idea behind the ADR-039 review-finding corpus.

## Knowledge-base conflict check

Existing records overlap: ADR-039, Epic 39. Proposal: trust existing and link. No conflict found.

*An interpretation by the assistant, not an approval. A draft until the maintainer accepts, changes or drops it; trust, supersede or flag is the maintainer's decision.*
