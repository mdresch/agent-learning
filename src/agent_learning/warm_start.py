"""Explicit policy prior warm-starting module.

Pure computational logic for transferring converged action logits from a
donor policy to an uncalibrated target policy (ADR-020, Epic 20).

Constraints:
- Standard library only: no external math libraries, no PRNG, no storage layer imports.
- Zero mutations on input arguments.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

DAMPING_DEFAULT: float = 0.70
DAMPING_DEFAULT_META_PRIOR: float = 1.0
VALID_DONOR_KINDS: frozenset[str] = frozenset({"policy", "meta_prior"})


def warm_start_logits(
    donor_logits: Mapping[str, float],
    action_map: Mapping[str, str],
    target_actions: Sequence[str],
    *,
    damping: float = DAMPING_DEFAULT,
) -> dict[str, float]:
    """Compute damped target policy logits from a donor's converged logits.

    Args:
        donor_logits: Mapping of donor action IDs to logit values.
        action_map: Bijective mapping from target action ID to donor action ID.
        target_actions: Complete sequence of target action IDs.
        damping: Scale factor in (0, 1.0]. Defaults to DAMPING_DEFAULT (0.70).

    Returns:
        Dictionary mapping each target action ID to its scaled logit:
            target_logits[a] = donor_logits[action_map[a]] * damping

    Raises:
        TypeError: If damping is a bool or not a numeric type.
        ValueError: If damping is non-finite or not in (0, 1.0].
        ValueError: If target_actions contains duplicate action identifiers.
        ValueError: If action_map keys do not match target_actions exactly.
        ValueError: If multiple target actions map to the same donor action.
        ValueError: If a mapped donor action is missing from donor_logits.
        TypeError: If any donor logit is a bool or not a numeric type.
        ValueError: If any donor logit is non-finite.
    """
    # 1. Validate damping parameter
    if isinstance(damping, bool) or not isinstance(damping, (int, float)):
        raise TypeError(f"damping must be a float, got {type(damping).__name__}")
    if not math.isfinite(damping) or damping <= 0.0 or damping > 1.0:
        raise ValueError(f"damping must be in (0, 1], got {damping!r}")

    # 2. Validate action map completeness against target actions
    if len(target_actions) != len(set(target_actions)):
        raise ValueError("target_actions contains duplicate action identifiers.")
    target_set = set(target_actions)
    map_keys = set(action_map.keys())
    if target_set != map_keys:
        missing = sorted(target_set - map_keys)
        extra = sorted(map_keys - target_set)
        raise ValueError(
            f"action_map keys must match target_actions exactly. Missing: {missing}, extra: {extra}"
        )

    # 3. Validate one-to-one mapping (injective)
    donor_targets = list(action_map.values())
    if len(donor_targets) != len(set(donor_targets)):
        raise ValueError("Multiple target actions are mapped to the same donor action.")

    # 4. Validate donor actions presence and logit finiteness
    damp_float = float(damping)
    result: dict[str, float] = {}

    for target_act in target_actions:
        donor_act = action_map[target_act]
        if donor_act not in donor_logits:
            raise ValueError(f"Mapped donor action {donor_act!r} not found in donor_logits.")
        val = donor_logits[donor_act]
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            raise TypeError(f"Donor logit for {donor_act!r} must be a float, got {type(val).__name__}")
        if not math.isfinite(val):
            raise ValueError(f"Non-finite donor logit for {donor_act!r}: {val!r}")
        result[target_act] = float(val) * damp_float

    return result


def provenance(
    donor: Any,
    damping: float,
    now: str,
    *,
    action_map: Mapping[str, str],
    kind: str = "policy",
    gate_met: bool | None = None,
) -> dict[str, Any]:
    """Build provenance record for a warm-started policy snapshot (Story 20.2).

    Args:
        donor: Donor policy snapshot with id, task_id, and version attributes.
        damping: Scale factor in (0, 1.0].
        now: Timestamp string for the warm-start event. Not queried from clock.
        action_map: Mapping of target action IDs to donor action IDs.
        kind: Kind of donor ("policy" or "meta_prior"). Defaults to "policy".
        gate_met: Whether donor satisfies autonomy gate (bool or None).

    Returns:
        Dictionary with full lineage metadata keys suitable for JSON serialization.

    Raises:
        ValueError: If kind is not 'policy' or 'meta_prior'.
        TypeError: If damping is a bool or not a number, or gate_met is not a bool/None.
        ValueError: If damping is non-finite or not in (0, 1.0].
        TypeError: If now is not a string, or donor id/task_id/version or action_map have invalid types.
        ValueError: If now is empty/whitespace, donor attributes are missing/empty, donor version is negative,
            or action_map keys/values are empty.
    """
    if kind not in VALID_DONOR_KINDS:
        raise ValueError(
            f"kind must be one of {', '.join(sorted(VALID_DONOR_KINDS))}; got {kind!r}"
        )

    if isinstance(damping, bool) or not isinstance(damping, (int, float)):
        raise TypeError(f"damping must be a float, got {type(damping).__name__}")
    if not math.isfinite(damping) or damping <= 0.0 or damping > 1.0:
        raise ValueError(f"damping must be in (0, 1], got {damping!r}")

    if not isinstance(now, str):
        raise TypeError(f"now must be a string, got {type(now).__name__}")
    if not now.strip():
        raise ValueError("now must be a non-empty string")

    if gate_met is not None and not isinstance(gate_met, bool):
        raise TypeError(f"gate_met must be bool or None, got {type(gate_met).__name__}")

    donor_id = getattr(donor, "id", None)
    donor_task_id = getattr(donor, "task_id", None)
    donor_version = getattr(donor, "version", None)
    if donor_id is None or donor_task_id is None or donor_version is None:
        raise ValueError("donor must have non-null 'id', 'task_id', and 'version' attributes")

    if not isinstance(donor_id, str):
        raise TypeError(f"donor id must be a string, got {type(donor_id).__name__}")
    if not donor_id.strip():
        raise ValueError("donor id must be a non-empty string")

    if not isinstance(donor_task_id, str):
        raise TypeError(f"donor task_id must be a string, got {type(donor_task_id).__name__}")
    if not donor_task_id.strip():
        raise ValueError("donor task_id must be a non-empty string")

    if isinstance(donor_version, bool) or not isinstance(donor_version, int):
        raise TypeError(f"donor version must be an int, got {type(donor_version).__name__}")
    if donor_version < 0:
        raise ValueError(f"donor version must be a non-negative int, got {donor_version!r}")

    if not isinstance(action_map, Mapping):
        raise TypeError(f"action_map must be a Mapping, got {type(action_map).__name__}")
    validated_map: dict[str, str] = {}
    for k, v in action_map.items():
        if not isinstance(k, str):
            raise TypeError(f"action_map keys must be strings, got {type(k).__name__}")
        if not k.strip():
            raise ValueError("action_map keys must be non-empty strings")
        if not isinstance(v, str):
            raise TypeError(f"action_map values must be strings, got {type(v).__name__}")
        if not v.strip():
            raise ValueError("action_map values must be non-empty strings")
        validated_map[k] = v

    return {
        "warm_start_donor_policy_id": donor_id,
        "warm_start_donor_task_id": donor_task_id,
        "warm_start_donor_version": donor_version,
        "warm_start_damping_factor": float(damping),
        "warm_started_at": now,
        "warm_start_action_map": validated_map,
        "warm_start_donor_kind": kind,
        "warm_start_donor_gate_met": gate_met,
    }


__all__ = [
    "DAMPING_DEFAULT",
    "DAMPING_DEFAULT_META_PRIOR",
    "VALID_DONOR_KINDS",
    "provenance",
    "warm_start_logits",
]
