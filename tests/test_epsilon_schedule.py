"""Story 17.1 — The Schedule (ADR-017, BRD-017, FDD-017).

Acceptance Criteria:
  AC_0 (Values): epsilon_at(t, 0.5, 0.05, 0.05) gives 0.5 for t = 0, 0.25 for t = 20,
       0.05 for t = 180 and 0.05 for t = 1000, each within 1e-12, and the test
       recomputes them from the formula itself.
  AC_1 (Non-Increasing): over t from 0 to 5000, the rate never rises from one t
       to the next and never falls below the floor.
  AC_2 (Floor Equals Initial): with floor = eps0 the rate is constant at eps0;
       with delta = 0 it is eps0 for every t.
  AC_3 (Validation): ValueError naming the argument for delta < 0, eps0 < floor,
       a value outside [0, 1], t < 0, and any non-finite argument.

Contract Interpretations (derived via scripts/spec_gate.py):
  I1 (Upstream Fork Purity): All implementations reside in src/agent_learning_ext/,
      leaving upstream src/agent_learning/ pristine.
  I2 (Storage Decoupling): Pure mathematical schedule computation without storage coupling or I/O.
"""

from __future__ import annotations

import pytest

from agent_learning_ext.policy.epsilon_greedy import epsilon_at


def test_ac0_schedule_values_and_recomputation() -> None:
    """AC_0: epsilon_at matches specific decay values and exact closed form within 1e-12."""
    eps0 = 0.5
    delta = 0.05
    floor = 0.05

    test_points = [
        (0, 0.5),
        (20, 0.25),
        (180, 0.05),
        (1000, 0.05),
    ]

    for t, expected_val in test_points:
        computed = epsilon_at(t, eps0, delta, floor)
        # Check against specified value within 1e-12
        assert abs(computed - expected_val) < 1e-12, f"Failed at t={t}: computed {computed} != expected {expected_val}"

        # Recompute from the formula itself: max(floor, eps0 / (1 + delta * t))
        recomputed = max(floor, eps0 / (1.0 + delta * t))
        assert abs(computed - recomputed) < 1e-12, f"Formula recomputation mismatch at t={t}"


def test_ac1_non_increasing_and_never_below_floor() -> None:
    """AC_1: Over t in 0..5000, rate never rises and never falls below the floor."""
    eps0 = 0.5
    delta = 0.05
    floor = 0.05

    prev_rate = float("inf")
    for t in range(5001):
        rate = epsilon_at(t, eps0, delta, floor)
        assert rate <= prev_rate + 1e-15, f"Rate rose at t={t}: {rate} > {prev_rate}"
        assert rate >= floor - 1e-15, f"Rate fell below floor at t={t}: {rate} < {floor}"
        prev_rate = rate

    # Also test another schedule configuration
    eps0_b = 0.8
    delta_b = 0.01
    floor_b = 0.1
    prev_rate_b = float("inf")
    for t in range(0, 5001, 25):
        rate_b = epsilon_at(t, eps0_b, delta_b, floor_b)
        assert rate_b <= prev_rate_b + 1e-15
        assert rate_b >= floor_b - 1e-15
        prev_rate_b = rate_b


def test_ac2_floor_equals_initial_and_zero_delta() -> None:
    """AC_2: With floor = eps0 the rate is constant; with delta = 0 it is eps0 for every t."""
    # When floor == eps0
    eps0 = 0.4
    delta = 0.05
    floor = 0.4
    for t in (0, 1, 10, 100, 5000):
        assert abs(epsilon_at(t, eps0, delta, floor) - 0.4) < 1e-12

    # When delta == 0
    eps0 = 0.6
    delta = 0.0
    floor = 0.1
    for t in (0, 1, 10, 100, 5000):
        assert abs(epsilon_at(t, eps0, delta, floor) - 0.6) < 1e-12


def test_ac3_validation_negative_delta() -> None:
    """AC_3: ValueError naming 'delta' when delta < 0."""
    with pytest.raises(ValueError, match=r"(?i)\bdelta\b"):
        epsilon_at(0, 0.5, -0.01, 0.05)


def test_ac3_validation_eps0_below_floor() -> None:
    """AC_3: ValueError naming 'eps0' or 'floor' when eps0 < floor."""
    with pytest.raises(ValueError, match=r"(?i)\b(eps0|floor)\b"):
        epsilon_at(0, 0.04, 0.05, 0.05)


def test_ac3_validation_outside_unit_interval() -> None:
    """AC_3: ValueError naming the argument when eps0 or floor are outside [0, 1]."""
    with pytest.raises(ValueError, match=r"(?i)\beps0\b"):
        epsilon_at(0, -0.1, 0.05, 0.0)

    with pytest.raises(ValueError, match=r"(?i)\beps0\b"):
        epsilon_at(0, 1.1, 0.05, 0.0)

    with pytest.raises(ValueError, match=r"(?i)\bfloor\b"):
        epsilon_at(0, 0.5, 0.05, -0.01)

    with pytest.raises(ValueError, match=r"(?i)\bfloor\b"):
        epsilon_at(0, 0.5, 0.05, 1.05)


def test_ac3_validation_negative_t() -> None:
    """AC_3: ValueError naming 't' when t < 0."""
    with pytest.raises(ValueError, match=r"(?i)\bt\b"):
        epsilon_at(-1, 0.5, 0.05, 0.05)


@pytest.mark.parametrize(
    ("t", "eps0", "delta", "floor", "expected_arg"),
    [
        (float("nan"), 0.5, 0.05, 0.05, "t"),
        (float("inf"), 0.5, 0.05, 0.05, "t"),
        (0, float("nan"), 0.05, 0.05, "eps0"),
        (0, float("inf"), 0.05, 0.05, "eps0"),
        (0, 0.5, float("nan"), 0.05, "delta"),
        (0, 0.5, float("inf"), 0.05, "delta"),
        (0, 0.5, 0.05, float("nan"), "floor"),
        (0, 0.5, 0.05, float("inf"), "floor"),
    ],
)
def test_ac3_validation_non_finite_arguments(
    t: float,
    eps0: float,
    delta: float,
    floor: float,
    expected_arg: str,
) -> None:
    """AC_3: ValueError naming the argument when any argument is non-finite."""
    with pytest.raises(ValueError, match=rf"(?i)\b{expected_arg}\b"):
        epsilon_at(t, eps0, delta, floor)  # type: ignore[arg-type]


def test_ac3_validation_boolean_arguments() -> None:
    """AC_3: ValueError naming the argument when boolean values are passed."""
    with pytest.raises(ValueError, match=r"(?i)\bt\b"):
        epsilon_at(True, 0.5, 0.05, 0.05)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match=r"(?i)\beps0\b"):
        epsilon_at(0, True, 0.05, 0.05)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match=r"(?i)\bdelta\b"):
        epsilon_at(0, 0.5, False, 0.05)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match=r"(?i)\bfloor\b"):
        epsilon_at(0, 0.5, 0.05, True)  # type: ignore[arg-type]
