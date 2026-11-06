# INSIGHT-004: Gate evidence is split between the repository and an external store

- **Insight type:** ProcessInsight
- **Recorded:** 2026-11-04 (Stage 14, interpretation of the cited observations)
- **Impact level:** Medium
- **Applicable subsystems:** governance gates, store
- **Derived from:** OBS-001, OBS-007, OBS-008
- **Confidence:** Medium. The file counts and the missing episodes are measured; that no tool compares the two copies was not searched for exhaustively.

## Finding

A gate decision and adjudication write nothing; only registering the episode does (OBS-008), and it writes to a store outside the repository (OBS-001). The repository keeps copies under docs/policy-shapes, so the same gate has two records that nothing compares. Two upstream gates (approve-charter, approve-business-case) have no episode at all while later gates do (OBS-007), so the chain's gate record is incomplete in the store and the repo alike.

## Knowledge-base conflict check

Existing records overlap: LL-040 (print the store path first). LL-040 does not cover the two-copy divergence. Proposal: trust existing, and flag the divergence for a human.

*An interpretation by the assistant, not an approval. A human decides trust, supersede or flag for each proposal.*
