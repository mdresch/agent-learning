"""Story 16.3 — Shared Action Statistics (ADR-016, FDD-016 §2.4, E7).

Acceptance Criteria:
  AC_2 (Validation in read_statistics):
       - Rejects action id in statistics outside action space.
       - Rejects negative or non-integer pull_count.
       - Rejects cumulative_reward outside [0, pull_count] or not finite.
       - Rejects mean_reward differing from cumulative_reward / pull_count by > 1e-9.
       - Rejects duplicate ids in consumed_episode_ids.
       - Action missing from statistics reads as zero pulls (0, 0.0, 0.0).

Contract Interpretations (derived via scripts/spec_gate.py):
  I1 (Upstream Fork Purity): Implemented in src/agent_learning_ext/policy/action_statistics.py.
  I2 (Defensive None-Safety): Missing or None metadata safely treated as empty dictionary.
  I3 (Non-Finite Float Rejection): NaNs/Infs rejected with ValueError.
"""

from __future__ import annotations

import math

import pytest

from agent_learning_ext.policy.action_statistics import ActionStats, read_statistics


def test_read_statistics_valid_and_defaults() -> None:
    """read_statistics reads valid entries and fills missing actions with zeros."""
    metadata = {
        "action_statistics": {
            "a": {"pull_count": 10, "cumulative_reward": 8.0, "mean_reward": 0.8},
        },
        "consumed_episode_ids": ["ep-1", "ep-2"],
    }
    stats = read_statistics(metadata, ["a", "b"])

    assert stats["a"] == ActionStats(pull_count=10, cumulative_reward=8.0, mean_reward=0.8)
    assert stats["b"] == ActionStats(pull_count=0, cumulative_reward=0.0, mean_reward=0.0)


def test_read_statistics_none_metadata_safety() -> None:
    """I2: None or empty metadata defaults cleanly without raising AttributeError."""
    stats = read_statistics(None, ["x", "y"])
    assert stats["x"] == ActionStats(pull_count=0, cumulative_reward=0.0, mean_reward=0.0)
    assert stats["y"] == ActionStats(pull_count=0, cumulative_reward=0.0, mean_reward=0.0)


def test_read_statistics_foreign_action_rejected() -> None:
    """AC_2: action in statistics not in action_ids raises ValueError naming it."""
    metadata = {
        "action_statistics": {
            "foreign": {"pull_count": 1, "cumulative_reward": 1.0, "mean_reward": 1.0},
        }
    }
    with pytest.raises(ValueError, match="foreign"):
        read_statistics(metadata, ["a", "b"])


def test_read_statistics_negative_or_non_integer_pulls() -> None:
    """AC_2: negative or non-integer pull count raises ValueError naming the action."""
    bad_neg = {
        "action_statistics": {
            "a": {"pull_count": -1, "cumulative_reward": 0.0, "mean_reward": 0.0},
        }
    }
    with pytest.raises(ValueError, match="a"):
        read_statistics(bad_neg, ["a"])

    bad_float = {
        "action_statistics": {
            "a": {"pull_count": 2.5, "cumulative_reward": 1.0, "mean_reward": 0.4},
        }
    }
    with pytest.raises(ValueError, match="a"):
        read_statistics(bad_float, ["a"])

    bad_bool = {
        "action_statistics": {
            "a": {"pull_count": True, "cumulative_reward": 1.0, "mean_reward": 1.0},
        }
    }
    with pytest.raises(ValueError, match="a"):
        read_statistics(bad_bool, ["a"])


def test_read_statistics_cumulative_reward_bounds_and_finite() -> None:
    """AC_2 & I3: cumulative reward outside [0, pull_count] or non-finite raises ValueError."""
    # < 0
    bad_low = {
        "action_statistics": {
            "a": {"pull_count": 5, "cumulative_reward": -0.1, "mean_reward": 0.0},
        }
    }
    with pytest.raises(ValueError, match="a"):
        read_statistics(bad_low, ["a"])

    # > pull_count
    bad_high = {
        "action_statistics": {
            "a": {"pull_count": 5, "cumulative_reward": 5.1, "mean_reward": 1.0},
        }
    }
    with pytest.raises(ValueError, match="a"):
        read_statistics(bad_high, ["a"])

    # NaN / Inf
    bad_nan = {
        "action_statistics": {
            "a": {"pull_count": 5, "cumulative_reward": float("nan"), "mean_reward": 0.0},
        }
    }
    with pytest.raises(ValueError, match="a"):
        read_statistics(bad_nan, ["a"])

    bad_inf = {
        "action_statistics": {
            "a": {"pull_count": 5, "cumulative_reward": math.inf, "mean_reward": 0.0},
        }
    }
    with pytest.raises(ValueError, match="a"):
        read_statistics(bad_inf, ["a"])


def test_read_statistics_mean_reward_mismatch() -> None:
    """AC_2: mean_reward differing from cumulative_reward / pull_count by > 1e-9 raises ValueError."""
    bad_mean = {
        "action_statistics": {
            "a": {"pull_count": 10, "cumulative_reward": 8.0, "mean_reward": 0.79},
        }
    }
    with pytest.raises(ValueError, match="a"):
        read_statistics(bad_mean, ["a"])

    # Within tolerance passes
    good_mean = {
        "action_statistics": {
            "a": {"pull_count": 10, "cumulative_reward": 8.0, "mean_reward": 0.8 + 1e-10},
        }
    }
    res = read_statistics(good_mean, ["a"])
    assert abs(res["a"].mean_reward - 0.8) < 1e-9


def test_read_statistics_duplicate_consumed_ids() -> None:
    """AC_2: duplicate id in consumed_episode_ids raises ValueError naming the duplicate id."""
    metadata = {
        "action_statistics": {
            "a": {"pull_count": 2, "cumulative_reward": 1.5, "mean_reward": 0.75},
        },
        "consumed_episode_ids": ["ep-1", "ep-2", "ep-1"],
    }
    with pytest.raises(ValueError, match="ep-1"):
        read_statistics(metadata, ["a"])
