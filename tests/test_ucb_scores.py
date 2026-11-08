"""Story 16.1 — The Scores (ADR-016, BRD-016, FDD-016).

Acceptance Criteria:
  AC_0 (Standard): On base statistics with variant="standard" and default c, scores are
       1.8408 for 'a' and 2.0719 for 'b' within 1e-4, recomputed from UCB1 formula.
  AC_1 (Wilson): With variant="wilson", action with 10 pulls and 10.0 reward scores 1.0
       and one with 10 pulls and 0.0 scores 0.2775 within 1e-4; scores on base statistics
       match closed form of ADR-016 §4.1 within 1e-9.
  AC_2 (Unexplored): Action with no pulls scores math.inf in both variants; in standard
       variant total == 1 gives bonus of 0.
  AC_3 (Reuse): Over grid of N in 1..50 and k in 0..N (step 0.5), 1 - wilson_lower_bound(N - k, N)
       equals wilson score within 1e-12; wilson_lower_bound returns same values as before
       for integer arguments.
  AC_4 (Validation): ValueError for unknown variant, c <= 0, total != sum(pull counts),
       negative or non-integer pull count, and cumulative reward outside [0, pull_count]
       or not finite.
  AC_5 (No RNG): Static check finds no import of random and no call into it in policy/ucb.py
       and learners/ucb.py.

Contract Interpretations (derived via scripts/spec_gate.py):
  I1 (Upstream Fork Purity): All implementations reside in src/agent_learning_ext/, leaving
      upstream src/agent_learning/ pristine.
  I2 (Storage Decoupling): Pure mathematical scoring without storage coupling or I/O.
"""

from __future__ import annotations

import ast
import math
from pathlib import Path

import pytest

from agent_learning_ext.autonomy import wilson_lower_bound
from agent_learning_ext.policy.action_statistics import ActionStats
from agent_learning_ext.policy.ucb import C_DEFAULT, WILSON_Z, ucb_scores


def test_ac0_standard_base_statistics() -> None:
    """AC_0: standard variant scores match UCB1 formula on base statistics."""
    # Base statistics fixture:
    # a: 10 pulls, cumulative reward 8.0
    # b: 5 pulls, cumulative reward 3.0
    # total: 15
    stats = {
        "a": ActionStats(pull_count=10, cumulative_reward=8.0, mean_reward=0.8),
        "b": ActionStats(pull_count=5, cumulative_reward=3.0, mean_reward=0.6),
    }
    total = 15

    scores = ucb_scores(stats, total, variant="standard")

    # Formula recomputation
    expected_a = 0.8 + C_DEFAULT * math.sqrt(2.0 * math.log(15) / 10.0)
    expected_b = 0.6 + C_DEFAULT * math.sqrt(2.0 * math.log(15) / 5.0)

    assert abs(scores["a"] - 1.8408) < 1e-4
    assert abs(scores["b"] - 2.0719) < 1e-4
    assert abs(scores["a"] - expected_a) < 1e-12
    assert abs(scores["b"] - expected_b) < 1e-12


def test_ac1_wilson_extremes_and_closed_form() -> None:
    """AC_1: wilson variant boundary extremes and closed-form match within 1e-9."""
    # Boundary extremes
    stats_perfect = {
        "a": ActionStats(pull_count=10, cumulative_reward=10.0, mean_reward=1.0),
    }
    scores_perfect = ucb_scores(stats_perfect, 10, variant="wilson")
    assert abs(scores_perfect["a"] - 1.0) < 1e-4

    stats_zero = {
        "b": ActionStats(pull_count=10, cumulative_reward=0.0, mean_reward=0.0),
    }
    scores_zero = ucb_scores(stats_zero, 10, variant="wilson")
    assert abs(scores_zero["b"] - 0.2775) < 1e-4

    # Base statistics match closed form from ADR-016 §4.1 within 1e-9
    stats_base = {
        "a": ActionStats(pull_count=10, cumulative_reward=8.0, mean_reward=0.8),
        "b": ActionStats(pull_count=5, cumulative_reward=3.0, mean_reward=0.6),
    }
    scores_base = ucb_scores(stats_base, 15, variant="wilson")

    def wilson_upper_closed_form(k: float, n: int, z: float = WILSON_Z) -> float:
        p_hat = k / n
        z2 = z * z
        numerator = p_hat + (z2 / (2.0 * n)) + z * math.sqrt((p_hat * (1.0 - p_hat) / n) + (z2 / (4.0 * n * n)))
        denominator = 1.0 + (z2 / n)
        return numerator / denominator

    assert abs(scores_base["a"] - wilson_upper_closed_form(8.0, 10)) < 1e-9
    assert abs(scores_base["b"] - wilson_upper_closed_form(3.0, 5)) < 1e-9


def test_ac2_unexplored_action_and_total_one_bonus() -> None:
    """AC_2: pull_count == 0 gives math.inf in both variants; total == 1 gives bonus of 0."""
    stats_unexplored = {
        "a": ActionStats(pull_count=0, cumulative_reward=0.0, mean_reward=0.0),
        "b": ActionStats(pull_count=1, cumulative_reward=1.0, mean_reward=1.0),
    }
    scores_standard = ucb_scores(stats_unexplored, 1, variant="standard")
    scores_wilson = ucb_scores(stats_unexplored, 1, variant="wilson")

    assert scores_standard["a"] == math.inf
    assert scores_wilson["a"] == math.inf

    # In standard variant, total == 1 gives bonus 0, so score equals mean_reward
    assert abs(scores_standard["b"] - 1.0) < 1e-12


def test_ac3_wilson_symmetry_reuse_and_integer_invariance() -> None:
    """AC_3: 1 - wilson_lower_bound(N - k, N) == wilson score within 1e-12; integer invariance."""
    # Grid test: N from 1 to 50, k from 0 to N in steps of 0.5
    for n in range(1, 51):
        k = 0.0
        while k <= n + 1e-9:
            stats = {"x": ActionStats(pull_count=n, cumulative_reward=k, mean_reward=k / n)}
            score = ucb_scores(stats, n, variant="wilson")["x"]
            sym = 1.0 - wilson_lower_bound(n - k, n, z=WILSON_Z)
            assert abs(score - sym) < 1e-12, f"Failed for N={n}, k={k}: score={score}, sym={sym}"
            k += 0.5

    # Check integer arguments return same values as before (regression guard)
    assert abs(wilson_lower_bound(8, 10) - (1.0 - ucb_scores({"x": ActionStats(10, 2.0, 0.2)}, 10, variant="wilson")["x"])) < 1e-12

    # Validation guards on successes
    with pytest.raises(ValueError, match="successes"):
        wilson_lower_bound(-0.1, 10)
    with pytest.raises(ValueError, match="successes"):
        wilson_lower_bound(10.1, 10)
    with pytest.raises(ValueError, match="successes"):
        wilson_lower_bound(float("nan"), 10)


def test_ac4_validation_errors() -> None:
    """AC_4: ValueError for invalid inputs."""
    valid_stats = {"a": ActionStats(pull_count=5, cumulative_reward=3.0, mean_reward=0.6)}

    # Unknown variant
    with pytest.raises(ValueError, match="variant"):
        ucb_scores(valid_stats, 5, variant="unknown")

    # c <= 0 or bool
    with pytest.raises(ValueError, match="c"):
        ucb_scores(valid_stats, 5, variant="standard", c=0.0)
    with pytest.raises(ValueError, match="c"):
        ucb_scores(valid_stats, 5, variant="standard", c=-1.0)
    with pytest.raises(ValueError, match="c"):
        ucb_scores(valid_stats, 5, variant="standard", c=True)  # type: ignore

    # total != sum(pull_count) or bad total type
    with pytest.raises(ValueError, match="total"):
        ucb_scores(valid_stats, 6, variant="standard")
    with pytest.raises(ValueError, match="total"):
        ucb_scores(valid_stats, 4, variant="wilson")
    with pytest.raises(ValueError, match="total"):
        ucb_scores(valid_stats, 5.0, variant="standard")  # type: ignore
    with pytest.raises(ValueError, match="total"):
        ucb_scores(valid_stats, True, variant="standard")  # type: ignore

    # Negative pull count
    bad_pulls = {"a": ActionStats(pull_count=-1, cumulative_reward=0.0, mean_reward=0.0)}
    with pytest.raises(ValueError, match="pull_count"):
        ucb_scores(bad_pulls, 0)

    # Non-integer pull count
    bad_type = {"a": ActionStats(pull_count=2.5, cumulative_reward=1.0, mean_reward=0.4)}  # type: ignore
    with pytest.raises(ValueError, match="pull_count"):
        ucb_scores(bad_type, 2)

    # Cumulative reward outside [0, pull_count]
    bad_cum_low = {"a": ActionStats(pull_count=5, cumulative_reward=-0.1, mean_reward=0.0)}
    with pytest.raises(ValueError, match="cumulative_reward"):
        ucb_scores(bad_cum_low, 5)

    bad_cum_high = {"a": ActionStats(pull_count=5, cumulative_reward=5.1, mean_reward=1.0)}
    with pytest.raises(ValueError, match="cumulative_reward"):
        ucb_scores(bad_cum_high, 5)

    # Non-finite cumulative reward
    bad_nan = {"a": ActionStats(pull_count=5, cumulative_reward=float("nan"), mean_reward=0.0)}
    with pytest.raises(ValueError, match="cumulative_reward"):
        ucb_scores(bad_nan, 5)


def test_ac5_no_random_imports_or_calls() -> None:
    """AC_5: Static check finds no import of random and no call into it in ucb modules."""
    root = Path(__file__).resolve().parents[1]
    paths = [
        root / "src" / "agent_learning_ext" / "policy" / "ucb.py",
        root / "src" / "agent_learning_ext" / "learners" / "ucb.py",
    ]

    for path in paths:
        assert path.exists(), f"Module {path} must exist"
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name != "random", f"Found 'import random' in {path}"
            elif isinstance(node, ast.ImportFrom):
                assert node.module != "random", f"Found 'from random import ...' in {path}"
            elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "random":
                pytest.fail(f"Found reference to random module attribute '{node.attr}' in {path}")
