# INSIGHT-007: A merge can happen while the full-suite result is not yet a blocking fact

- **Insight type:** ProcessInsight
- **Recorded:** 2026-11-10 (Stage 14, Phase 2, interpretation of the cited observations)
- **Impact level:** High
- **Applicable subsystems:** pr_gate, CI, merge
- **Derived from:** OBS-010, OBS-012, OBS-018
- **Phase 2 id:** INSIGHT-P2-03 in `Stage-14-Insights-Phase2.md`
- **Confidence:** High on what the gate does; low on whether it was the path for PR #173.
- **Goes to:** Stage 15 lesson candidate; improvement candidate.

## Finding

`pr_gate.py` blocks only on a completed failure. A check that is still running, or a check list that reads back empty, has no conclusion and passes (OBS-018). A red `Tests` run existed on the branch before PR #173 merged, and `main` then ran 5 tests red until PR #178 (OBS-010, OBS-012). Who or what issued the #173 merge is not established.

## Knowledge-base conflict check

No existing record covers the gate's handling of pending checks. Proposal: a Stage 15 lesson and an improvement candidate (treat pending or empty checks as not ready), on the maintainer's decision.

*An interpretation by the assistant, not an approval. A draft until the maintainer accepts, changes or drops it; trust, supersede or flag is the maintainer's decision.*
