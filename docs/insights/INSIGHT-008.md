# INSIGHT-008: Numbers and lists copied into approved documents go stale

- **Insight type:** ProcessInsight
- **Recorded:** 2026-11-10 (Stage 14, Phase 2, interpretation of the cited observations)
- **Impact level:** Medium
- **Applicable subsystems:** ADR-021, ADR-022, ADR-036, Ideation
- **Derived from:** OBS-012, with audit findings AUDIT-011, AUDIT-013, AUDIT-014
- **Phase 2 id:** INSIGHT-P2-04 in `Stage-14-Insights-Phase2.md`
- **Confidence:** Medium-high; four separate cases.
- **Goes to:** Stage 15 lesson candidate; IMP-053 stays open for Phase 3.

## Finding

ADR-021 named 11 pinned gates where the code needed 18 (found in two rounds, IMP-046); ADR-022 says weights are at least 0.0 and a proposal needs accuracy "at least" the baseline, where the code requires 0.05 and "strictly greater" and FDD-022 says "strictly beats"; the catalog tests failed after seven methodologies were promoted until the Ideation states and ADR-036 counts were amended. Where a document copies a list or threshold that code also holds, nothing keeps them equal until a test or a real-data check forces it.

## Knowledge-base conflict check

Overlaps IMP-046, IMP-053. Proposal: trust existing and link. AUDIT-013 and AUDIT-014 are baseline findings for Stage 16.

*An interpretation by the assistant, not an approval. A draft until the maintainer accepts, changes or drops it; trust, supersede or flag is the maintainer's decision.*
