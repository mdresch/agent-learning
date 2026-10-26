# Epic 3: Tier-Specific Autonomy Overrides and Authority-Aware Reporting

**Source ADR:** [ADR-003](../adr/ADR-003-evidence-gated-autonomy-thresholds.md) — Accepted (2026-10-23), §3, §4.5, §6
**Source BRD/FDD:** [BRD-003](../project-docs/Business-Requirements/BRD-003-tier-specific-autonomy-overrides.md) / [FDD-003](../project-docs/Functional-Design/FDD-003-tier-specific-autonomy-overrides.md)

One story, matching FDD-003's three designs.

## Story 3.1 — Build Tier-Specific Environment Overrides and Authority-Aware Autonomy Reporting

**Status:** Approved (2026-10-23, Menno) — derived from an Accepted ADR's disclosed gap; adjudicated via `approve-user-stories` (robust utility 0.883, episode `9e0b9639...`). Completed (2026-10-26) — implemented in feat/story-3.1 with contract tests in tests/test_autonomy.py.
**As** an operator configuring policy autonomy, **I want** to override thresholds for specific complexity tiers and see accurate autonomy reporting for full-authority policies, **so that** routine policies can be tuned without weakening critical safety gates and full-authority policies are not falsely reported as failing statistical gates.

**Acceptance Criteria:**
- $AC_0$: `AutonomyConfig.for_tier(tier)` resolves environment variables with tier suffixes (`AGENT_LEARNING_AUTONOMY_{METRIC}_{TIER}`) before checking global variables or defaults.
- $AC_1$: Setting `AGENT_LEARNING_AUTONOMY_MIN_OUTCOMES_LOW=5` sets `low` tier to 5 while preserving `standard` (20), `high` (50), and `critical` (100) at their default thresholds — verified via contract test.
- $AC_2$: `validate_autonomy_monotonicity()` checks all four tiers and raises `ValueError` naming the inverted metric and tiers if a higher-complexity tier is configured with a weaker threshold than a lower tier (ADR-003 §7 Invariant #5).
- $AC_3$: When `assess_autonomy()` evaluates a `full`-authority policy, `criteria["action_probability"]` and `criteria["probability_margin"]` are reported with `status="not_applicable"` and `met=True`, and `authorization_basis="human_adjudication"`.
- $AC_4$: Existing `low`-authority policies evaluate statistical gates exactly as before with zero regression against existing test suites.

## Not a story — out of scope per BRD-003/FDD-003

Global threshold replacement without backward compatibility and automatic dynamic complexity tier promotion are excluded per ADR-003 §5.

