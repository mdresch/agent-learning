# FDD-003: Tier-Specific Autonomy Overrides and Authority-Aware Autonomy Reporting

**Source ADR:** [ADR-003](../../adr/ADR-003-evidence-gated-autonomy-thresholds.md) — Accepted (2026-10-23), §3, §4.5, §6
**Source BRD:** [BRD-003](../Business-Requirements/BRD-003-tier-specific-autonomy-overrides.md)
**Status:** Approved (2026-10-23, Menno) — derived from an Accepted ADR's disclosed gap; adjudicated via `approve-fdd` (robust utility 0.883, episode `1686efdb...`).

## Design 1: Tier-Specific Environment Variable Resolution

Current behavior (`src/agent_learning/config.py:506-540`):

```python
defaults = _AUTONOMY_TIER_DEFAULTS[tier]
return cls(
    min_outcomes=_env_int(
        "AGENT_LEARNING_AUTONOMY_MIN_OUTCOMES",
        int(defaults["min_outcomes"]),
    ),
    ...
)
```

**Proposed Implementation:**
Add a tier-aware helper `_env_tier_override(metric: str, tier: AutonomyTier, default_val: Any, val_type: type)`:

```python
def _env_tier_int(metric: str, tier: AutonomyTier, default: int) -> int:
    tier_key = f"AGENT_LEARNING_AUTONOMY_{metric}_{tier.value.upper()}"
    global_key = f"AGENT_LEARNING_AUTONOMY_{metric}"
    if tier_key in os.environ:
        return int(os.environ[tier_key])
    if global_key in os.environ:
        logger.info("Using global autonomy override %s=%s for tier %s", global_key, os.environ[global_key], tier.value)
        return int(os.environ[global_key])
    return default
```

Resolution precedence for every metric:
1. `AGENT_LEARNING_AUTONOMY_{METRIC}_{TIER}` (e.g., `AGENT_LEARNING_AUTONOMY_MIN_OUTCOMES_LOW`)
2. `AGENT_LEARNING_AUTONOMY_{METRIC}` (global legacy override)
3. `_AUTONOMY_TIER_DEFAULTS[tier][metric]` (built-in baseline)

## Design 2: Cross-Tier Monotonicity Validation

Add `validate_autonomy_monotonicity() -> None` invoked when configs are built across tiers:

```python
def validate_autonomy_monotonicity() -> None:
    tiers = [AutonomyTier.LOW, AutonomyTier.STANDARD, AutonomyTier.HIGH, AutonomyTier.CRITICAL]
    configs = [AutonomyConfig.for_tier(t) for t in tiers]
    
    for i in range(len(configs) - 1):
        c_low, c_high = configs[i], configs[i + 1]
        t_low, t_high = tiers[i].value, tiers[i + 1].value
        
        if c_low.min_outcomes > c_high.min_outcomes:
            raise ValueError(f"Autonomy monotonicity violation: {t_low} min_outcomes ({c_low.min_outcomes}) > {t_high} ({c_high.min_outcomes})")
        if c_low.min_correctness_lower_bound > c_high.min_correctness_lower_bound:
            raise ValueError(f"Autonomy monotonicity violation: {t_low} correctness ({c_low.min_correctness_lower_bound}) > {t_high} ({c_high.min_correctness_lower_bound})")
        if c_low.min_mean_reward > c_high.min_mean_reward:
            raise ValueError(f"Autonomy monotonicity violation: {t_low} mean_reward ({c_low.min_mean_reward}) > {t_high} ({c_high.min_mean_reward})")
```

Enforces ADR-003 §7 Invariant #5: no higher-complexity tier may require weaker entry criteria than a lower-complexity tier.

## Design 3: Authority-Aware Autonomy Reporting

In `src/agent_learning/autonomy.py:assess_autonomy()`:
Inspect policy snapshot authority:

```python
authority_str = snapshot.metadata.get("decision_authority", "low")
is_full_authority = (authority_str.lower() == "full")
```

When `is_full_authority` is `True`:
1. Mark `authorization_basis` as `"human_adjudication"`.
2. Do not report `action_probability` and `probability_margin` as failed criteria in `criteria`.
3. Annotate the assessment result:
   ```python
   criteria["action_probability"] = {
       "actual": action_probability,
       "required": None,
       "status": "not_applicable",
       "reason": "full decision authority uses reasoned resolution, not learned policy logits (ADR-003 §4.5)",
       "met": True,
   }
   ```
4. `eligible` is determined strictly by whether human approval is required (`requires_human_approval`) and explicit adjudication history, rather than frozen bandit statistics.

## Error Handling & Compatibility

| Scenario | Behavior |
|---|---|
| User sets `AGENT_LEARNING_AUTONOMY_MIN_OUTCOMES_LOW=5` | Only `low` tier is set to 5; `standard` (20), `high` (50), `critical` (100) remain untouched. |
| User sets `AGENT_LEARNING_AUTONOMY_MIN_OUTCOMES=10` (legacy global) | Retains current behavior for backward compatibility, with an informational log. |
| User configures invalid inverted thresholds | `validate_autonomy_monotonicity()` raises `ValueError` before policy initialization or decision execution. |
| Full-authority policy assessed in CLI | Output distinguishes between human governance requirements and statistical gates, preventing false alarms. |

## Out of Scope

- Automated promotion between complexity tiers (ADR-003 §5).

