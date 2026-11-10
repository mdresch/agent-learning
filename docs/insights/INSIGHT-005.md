# INSIGHT-005: Built is not measured: the data that would exercise the learners does not exist

- **Insight type:** ArchitecturalInsight
- **Recorded:** 2026-11-10 (Stage 14, Phase 2, interpretation of the cited observations)
- **Impact level:** High
- **Applicable subsystems:** evidence, store, Epics 18, 21, 16
- **Derived from:** OBS-017 and the Stage 12 report (section 6)
- **Phase 2 id:** INSIGHT-P2-01 in `Stage-14-Insights-Phase2.md`
- **Confidence:** Medium-high. The data is recorded as absent; that the learners were built ahead of the data that would use them is an inference.
- **Goes to:** Stage 15 lesson candidate; Phase 3 intent (which data to acquire first).

## Finding

The governance gates are full-authority approvals that are almost all accepted, so the history cannot test the learners built to learn from rejection, routing or failure. The repo store shows no trained policy (OBS-017), and Stage 12 found no override pairs (177 approve-* episodes, 0 pairs), no routed traffic and a positive-only history.

## Knowledge-base conflict check

Existing records overlap: Charter section 10, Stage 12 section 6, IMP-058. Proposal: trust existing and link. No conflict found.

*An interpretation by the assistant, not an approval. A draft until the maintainer accepts, changes or drops it; trust, supersede or flag is the maintainer's decision.*
