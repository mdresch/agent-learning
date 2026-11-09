# INSIGHT-002: Story status is held in two places that are updated at different steps

- **Insight type:** ProcessInsight
- **Recorded:** 2026-11-04 (Stage 14, interpretation of the cited observations)
- **Impact level:** Medium
- **Applicable subsystems:** story status, implementation log
- **Derived from:** OBS-003, OBS-006
- **Confidence:** Medium-high. The count and both directions are measured; the cause (two hand-edited sources) is read from how the records are written, not tested.

## Finding

A story's state lives in its epic file (Status line) and in implementation-log.md. They are edited by hand at different steps, so they disagree: 15 stories drift, in both directions (OBS-003). The roll-up script detects the drift and reports it but does not resolve it, by design. Suite counts rose steadily across the same period (OBS-006), so the drift is a bookkeeping problem, not a build problem.

## Knowledge-base conflict check

Existing records overlap: IMP-011 and LL-041. Proposal: trust existing and link; reconciling the 15 status lines remains a human task (AUDIT-006).

*An interpretation by the assistant, not an approval. A human decides trust, supersede or flag for each proposal.*
