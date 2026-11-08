"""Scheduled Epsilon-Greedy policy baseline (ADR-017, BRD-017, FDD-017).

Pure standard library exploration schedule and action selection under human safety masks.
"""

from __future__ import annotations

import math

# Constants per FDD-017 §2.1
SELECTION_BASIS: str = "epsilon_greedy"
NEUTRAL_MEAN: float = 0.5


def epsilon_at(t: float, eps0: float, delta: float, floor: float) -> float:
    """Compute the scheduled exploration rate epsilon at pull count t (ADR-017, FDD-017 §3.1).

    Formula:
        max(floor, eps0 / (1.0 + delta * t))

    Args:
        t: Non-negative pull count (int or finite float >= 0).
        eps0: Initial exploration rate in [0, 1].
        delta: Non-negative decay factor (delta >= 0).
        floor: Minimum exploration floor in [0, 1] where floor <= eps0.

    Returns:
        Exploration probability rate in [floor, eps0].

    Raises:
        ValueError: If any argument is non-finite, boolean, outside valid ranges,
            or if eps0 < floor.
    """
    # Validate t
    if isinstance(t, bool):
        raise ValueError("argument 't' must be numeric, not bool")  # noqa: TRY004
    if not isinstance(t, (int, float)) or not math.isfinite(t):
        raise ValueError(f"argument 't' must be finite, got {t!r}")
    if t < 0:
        raise ValueError(f"argument 't' must be non-negative, got {t!r}")

    # Validate delta
    if isinstance(delta, bool):
        raise ValueError("argument 'delta' must be numeric, not bool")  # noqa: TRY004
    if not isinstance(delta, (int, float)) or not math.isfinite(delta):
        raise ValueError(f"argument 'delta' must be finite, got {delta!r}")
    if delta < 0:
        raise ValueError(f"argument 'delta' must be non-negative, got {delta!r}")

    # Validate floor
    if isinstance(floor, bool):
        raise ValueError("argument 'floor' must be numeric, not bool")  # noqa: TRY004
    if not isinstance(floor, (int, float)) or not math.isfinite(floor):
        raise ValueError(f"argument 'floor' must be finite, got {floor!r}")
    if floor < 0.0 or floor > 1.0:
        raise ValueError(f"argument 'floor' must be in [0, 1], got {floor!r}")

    # Validate eps0
    if isinstance(eps0, bool):
        raise ValueError("argument 'eps0' must be numeric, not bool")  # noqa: TRY004
    if not isinstance(eps0, (int, float)) or not math.isfinite(eps0):
        raise ValueError(f"argument 'eps0' must be finite, got {eps0!r}")
    if eps0 < 0.0 or eps0 > 1.0:
        raise ValueError(f"argument 'eps0' must be in [0, 1], got {eps0!r}")

    # Validate ordering
    if eps0 < floor:
        raise ValueError(f"argument 'eps0' ({eps0}) cannot be less than argument 'floor' ({floor})")

    decayed = float(eps0) / (1.0 + float(delta) * float(t))
    return float(max(float(floor), decayed))


__all__ = ["NEUTRAL_MEAN", "SELECTION_BASIS", "epsilon_at"]
