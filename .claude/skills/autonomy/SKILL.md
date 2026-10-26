---
name: autonomy
description: Guidance and constraints for evidence-gated autonomy thresholds (agent_learning.autonomy and AutonomyConfig), including tier-specific environment overrides, cross-tier monotonicity and authority-aware reporting for full-authority policies.
---

# Component Skill: Evidence-Gated Autonomy (`agent_learning.autonomy`, `agent_learning.config.AutonomyConfig`)

## 1. Governing Architecture & Specifications
- **ADR:** [ADR-003](../../../docs/adr/ADR-003-evidence-gated-autonomy-thresholds.md), sections 3, 4.3, 4.5, 6 and 7 (Invariants 4 to 7).
- **BRD:** [BRD-003](../../../docs/project-docs/Business-Requirements/BRD-003-tier-specific-autonomy-overrides.md).
- **FDD:** [FDD-003](../../../docs/project-docs/Functional-Design/FDD-003-tier-specific-autonomy-overrides.md).
- **Story:** [Story 3.1](../../../docs/user-stories/epic-3-tier-specific-autonomy-overrides.md).
- **Contract tests:** `tests/test_autonomy.py` (the Story 3.1 section at the end; interpretations I1 to I4 are listed in its header comment).

## 2. Load-Bearing Constraints
- **Resolution order, per metric and per tier:** `AGENT_LEARNING_AUTONOMY_{METRIC}_{TIER}`, then `AGENT_LEARNING_AUTONOMY_{METRIC}`, then the tier default in `_AUTONOMY_TIER_DEFAULTS`. An unparseable value falls through to the next level, as `_env_int` and `_env_float` already do. `WILSON_Z` has no tier suffix.
- **Monotonicity (ADR-003 Invariant 5):** no higher tier may be easier to enter than a lower one on any of the six statistical gates (`min_outcomes`, `min_correctness_lower_bound`, `min_mean_reward`, `min_action_probability`, `min_probability_margin`, `stable_snapshots`). Equal values are allowed. `audit_rate` is not a gate. `validate_autonomy_monotonicity()` raises `ValueError` naming the metric and both tiers, and `assess_autonomy()` calls it when it builds its own config. A config passed in explicitly is not re-validated.
- **Full authority (ADR-003 4.5, Invariant 7):** `assess_autonomy()` reports `action_probability` and `probability_margin` as `status="not_applicable"`, `met=True`, `required=None`, and sets `authorization_basis="human_adjudication"`. Eligibility for a full-authority policy comes only from explicit acceptance and `requires_human_approval`, never from the frozen-logit statistics.
- **`requires_human_approval: true` stays absolute** (ADR-003 Invariant 6) for every authority.
- **Low authority is unchanged:** the probability gates keep their numeric `required` and no `status` key (AC_4).
- Authority is read from `snapshot.metadata["decision_authority"]` (default `low`); do not import `decision.py` into `autonomy.py`.

## 3. Call Sites
- `src/agent_learning/cli.py` calls `assess_autonomy()` unconditionally for both authorities; the branch on authority lives inside `assess_autonomy()`.
- `docs/decision-making.md` documents the environment variables, including the tier suffix.

## 4. Out of Scope
Automatic promotion between complexity tiers, and global threshold replacement without backward compatibility (ADR-003 section 5).
