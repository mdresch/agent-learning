"""Explicit policy prior warm-starting module.

Pure computational logic for transferring converged action logits from a
donor policy to an uncalibrated target policy (ADR-020, Epic 20).

Constraints:
- Standard library only: no external math libraries, no PRNG, no storage layer imports.
- Zero mutations on input arguments.
"""

from __future__ import annotations

import math
from typing import Dict, Mapping, Sequence

DAMPING_DEFAULT: float = 0.70
DAMPING_DEFAULT_META_PRIOR: float = 1.0


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
        ValueError: If damping is non-finite or not in (0, 1.0].
        ValueError: If action_map keys do not match target_actions exactly.
        ValueError: If multiple target actions map to the same donor action.
        ValueError: If a mapped donor action is missing from donor_logits.
        ValueError: If any donor logit is non-finite.
    """
    # 1. Validate damping parameter
    if not isinstance(damping, (int, float)) or math.isnan(damping) or math.isinf(damping):
        raise ValueError(f"damping must be a finite float, got {damping!r}")
    if damping <= 0.0 or damping > 1.0:
        raise ValueError(f"damping must be in (0, 1], got {damping!r}")

    # 2. Validate action map completeness against target actions
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
        if not isinstance(val, (int, float)) or math.isnan(val) or math.isinf(val):
            raise ValueError(f"Non-finite donor logit for {donor_act!r}: {val!r}")
        result[target_act] = float(val) * damp_float

    return result


__all__ = [
    "DAMPING_DEFAULT",
    "DAMPING_DEFAULT_META_PRIOR",
    "warm_start_logits",
]
