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
- **Contract tests:** `tests/test_autonomy.py` (the Story 3.1 section at the end; interpretations I1 to I4 are listed in its header comment); `tests/test_autonomy_posterior.py` (Story 19.8, ADR-003 §4.6).

## 2. Load-Bearing Constraints
- **Resolution order, per metric and per tier:** `AGENT_LEARNING_AUTONOMY_{METRIC}_{TIER}`, then `AGENT_LEARNING_AUTONOMY_{METRIC}`, then the tier default in `_AUTONOMY_TIER_DEFAULTS`. An unparseable value falls through to the next level, as `_env_int` and `_env_float` already do. `WILSON_Z` has no tier suffix.
- **Monotonicity (ADR-003 Invariant 5):** no higher tier may be easier to enter than a lower one on any of the six statistical gates (`min_outcomes`, `min_correctness_lower_bound`, `min_mean_reward`, `min_action_probability`, `min_probability_margin`, `stable_snapshots`). Equal values are allowed. `audit_rate` is not a gate. `validate_autonomy_monotonicity()` raises `ValueError` naming the metric and both tiers, and `assess_autonomy()` calls it when it builds its own config. A config passed in explicitly is not re-validated.
- **Full authority (ADR-003 4.5, Invariant 7):** `assess_autonomy()` reports `action_probability` and `probability_margin` as `status="not_applicable"`, `met=True`, `required=None`, and sets `authorization_basis="human_adjudication"`. Eligibility for a full-authority policy comes only from explicit acceptance and `requires_human_approval`, never from the frozen-logit statistics.
- **`requires_human_approval: true` stays absolute** (ADR-003 Invariant 6) for every authority.
- **Low authority is unchanged:** the probability gates keep their numeric `required` and no `status` key (AC_4).
- Authority is read from `snapshot.metadata["decision_authority"]` (default `low`); do not import `decision.py` into `autonomy.py`.

### Authority-migration snapshot (Story 4.1, ADR-004)
- `task-policy-authority-set` appends one `MigrationRecord` to `snapshot.metadata["migration_records"]` when the authority changes (`low` to `full` or `full` to `low`): `policy_version_at_migration`, `action_probabilities_at_migration` (the softmax distribution at that moment), `from_authority`, `to_authority` and an ISO 8601 UTC `migrated_at`. Records are append-only; earlier ones are never edited.
- Setting the current authority is a full no-op: no record and no store write, so `decision_authority_updated_at` does not move. A policy with no stored authority reads as `low`.
- It is a diagnostic snapshot for inspection. It is not a replay: historical `low` episodes are never recomputed under `full` (ADR-004 section 4.1). `Episode.context_features` is caller-supplied context and is not consumed by non-contextual bandit selection.
- No new `LearningStore` record type or container (ADR-002 Invariant 2); the CLI builds `SoftmaxPolicy` snapshots only.
- Tests: `tests/test_authority_migration.py`.

- **Read a mutable global once (LL-020):** an override variable is read once into a local, and the local is tested and used. `_note_global_override` once read the global twice and raised `KeyError` when it was removed in between.

### Posterior policies (Story 19.8, ADR-003 §4.6, Invariant 8)
- A snapshot that holds `posterior_parameters` (Thompson sampling) keeps `logits` at zero. `_action_probabilities` reads it from `alpha / (alpha + beta)` per action, normalised over the actions (an absent action reads as 0.5): a softmax over `ln(mean)` that is computed for the check and never stored. The recommended action, winner probability, margin and the stable-snapshot count all use it; a tie goes to the earlier action.
- The tier table, the thresholds, every other criterion and the override rules are unchanged, and a snapshot without `posterior_parameters` is assessed exactly as before.
- For a low-authority posterior snapshot the `action_probability` and `probability_margin` criteria carry `"basis": "posterior_mean"`; a softmax snapshot and a full-authority one carry no `basis` key.
- A malformed posterior raises `ValueError` naming the action (it is not scored silently). `assess_autonomy` never writes.
- It is a proxy: not the probability of being the best action, thresholds not calibrated for it, and several actions of similar payoff rate cannot reach the winner-probability criterion. The limits are open items (FDD-019 §7 items 8 to 10); do not describe the reading as more than that.

## 3. Call Sites
- `src/agent_learning/cli.py` calls `assess_autonomy()` unconditionally for both authorities; the branch on authority lives inside `assess_autonomy()`.
- `docs/decision-making.md` documents the environment variables, including the tier suffix.

## 4. Out of Scope
Automatic promotion between complexity tiers, and global threshold replacement without backward compatibility (ADR-003 section 5).
