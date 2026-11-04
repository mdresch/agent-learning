# INSIGHT-003: The Stage 18 tooling lives only in the legacy tree that CI skips

- **Insight type:** ArchitecturalInsight
- **Recorded:** 2026-11-04 (Stage 14, interpretation of the cited observations)
- **Impact level:** High
- **Applicable subsystems:** pmbok, Stage 17 and 18 tooling
- **Derived from:** OBS-002, OBS-006
- **Confidence:** Medium. The location of the modules and the CI exclusion are measured; whether the legacy code still passes its own tests was not run.

## Finding

The readiness check, hypothesis adjudication and phase seeding named by the intent-refinement skill (evaluate_phase_close_readiness, seed-next) are in the top-level pmbok/ package and scripts/orchestrate_pmbok.py. src/agent_learning/pmbok has no intent_refinement module. Their tests are in tests/pmbok, which CI excludes, and ADR-034 plans to delete that tree (OBS-002, AUDIT-004). Running Stage 18 therefore depends on code that is neither maintained in CI nor on the path ADR-034 sets out.

## Knowledge-base conflict check

No existing record states this combination. ADR-034 and Stories 34.4 and 34.5 cover the decommissioning but not the Stage 18 dependency. Proposal: flag, for a human to decide whether it needs an ADR-034 amendment or a story.

*An interpretation by the assistant, not an approval. A human decides trust, supersede or flag for each proposal.*
