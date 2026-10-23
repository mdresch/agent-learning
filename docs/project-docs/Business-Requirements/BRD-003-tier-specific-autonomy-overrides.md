# BRD-003: Tier-Specific Autonomy Overrides and Authority-Aware Autonomy Reporting

**Source ADR:** [ADR-003](../../adr/ADR-003-evidence-gated-autonomy-thresholds.md) — Accepted (2026-10-23), §3, §4.5, §6
**Status:** Approved (2026-10-23, Menno) — derived from an Accepted ADR's disclosed gap; adjudicated via `approve-brd` (robust utility 0.883, episode `d9c8a66b...`).
**Stakeholders:** Menno (Sponsor/PM/maintainer). No separate Product Owner exists for this SDK; naming that rather than inventing one.

## Business Need

ADR-003 establishes complexity-proportional autonomy gating across four tiers (`low`, `standard`, `high`, `critical`) governed by conjunctive entry gates. Two distinct operational gaps were identified in ADR-003:

1. **Environment-Variable Tier Flattening Footgun (§3, §6):**
   `AutonomyConfig.for_tier()` (`config.py:506-540`) resolves environment overrides using global variable names (e.g., `AGENT_LEARNING_AUTONOMY_MIN_OUTCOMES`). Setting this variable applies to every tier equally. An operator attempting to loosen requirements for routine `low`-tier decisions inadvertently lowers requirements for `critical`-tier decisions as well, collapsing the safety guarantees of complexity-proportional gating. Operators require **tier-scoped overrides** that allow tuning a specific tier without mutating the others.

2. **Full-Authority Misleading Statistical Reporting (§4.5, §6):**
   `assess_autonomy()` (`autonomy.py:366`) is called identically regardless of whether a policy is `low` or `full` authority. Because `full`-authority policies resolve decisions via Bayesian reasoning rather than REINFORCE, their logits are permanently frozen. Consequently, `action_probability` and `probability_margin` appear permanently failing in raw CLI output, misleading operators into thinking the policy is "failing statistical gates" when in reality `full` authority is governed by case-by-case human adjudication and `requires_human_approval`.

This BRD formalizes the requirements to enable tier-specific environment overrides and deliver authority-aware autonomy reporting.

## Business Rules (BRU)

- **BRU-003-01**: Environment variable overrides for autonomy gate thresholds must support tier-specific suffixes (e.g., `AGENT_LEARNING_AUTONOMY_MIN_OUTCOMES_LOW`, `AGENT_LEARNING_AUTONOMY_MIN_OUTCOMES_CRITICAL`). A tier-specific variable overrides the threshold for that tier only.
- **BRU-003-02**: Backward compatibility: global override variables (e.g., `AGENT_LEARNING_AUTONOMY_MIN_OUTCOMES`) remain supported as fallbacks when no tier-specific variable is provided, and log an informational warning when used across multiple tiers.
- **BRU-003-03**: Monotonicity validation: when overrides are resolved, the system must validate ADR-003 §7 Invariant #5 — no higher-complexity tier may require weaker entry criteria than a lower-complexity tier. An invalid configuration that inverts tier thresholds must raise a descriptive `ValueError`.
- **BRU-003-04**: Authority-aware autonomy reporting: `assess_autonomy()` / `AutonomyAssessment` must recognize `decision_authority`. When assessing a `full`-authority policy, the report must clearly indicate that execution is governed by `human_approval_required` and per-instance adjudication, explicitly marking learned probability criteria as not applicable (`N/A`) rather than failed.

## Stakeholder Success Metrics

| Metric | Current state |
|---|---|
| Setting an override for `low` tier (e.g., `min_outcomes=5`) leaves `critical` tier at its default (100) | Not true today — global env var flattens all tiers to 5 (ADR-003 §6) |
| Inverting tier thresholds via environment variables (e.g. `critical` requiring fewer outcomes than `low`) is caught at startup | Not caught today — `AutonomyConfig` checks ranges (0–1) but not inter-tier monotonicity |
| CLI autonomy reporting for `full`-authority policies identifies governance basis as adjudication, not failing statistical gates | Not true today — reports frozen probability criteria as `met: false` (ADR-003 §4.5) |

## Out of Scope

- Inferring complexity from free text (rejected in ADR-003 §4.1).
- Automatic tier reclassification based on outcome history (rejected in ADR-003 §5).
- Creating a separate statistical learning algorithm for `full`-authority policies.

