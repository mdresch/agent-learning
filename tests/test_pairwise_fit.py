"""Contract tests for Story 18.3 — The Fit.

Source ADR: ADR-018 (Pairwise Preference Optimization for Discrete Action Logits)
Source BRD: BRD-018 (BRU-018-04, BRU-018-05, BRU-018-06, BRU-018-07)
Source FDD: FDD-018 (§2.1, §2.2, §3 item 2, G1, G2)
Story: Story 18.3 (The Fit)

Acceptance Criteria:
- AC_0 (Validation): lam of 0.049 raises ValueError, and 0.05 is accepted; a non-finite argument,
  lr <= 0, steps < 1, clamp <= 0, an action missing from theta_ref, and a pair naming an unknown
  action each raise ValueError naming the argument.
- AC_1 (No Pairs): with no pair the returned logits equal theta_ref exactly and converged is true.
- AC_2 (Clamp): every returned logit lies in [-8.0, +8.0], including for a pair set that pushes
  a logit past 8 and for a theta_ref outside the box.
- AC_3 (Step Size): step_size equals min(lr, 1 / (lam + 0.5 * max_degree)), with max_degree the largest
  number of pairs that name one action; on the base set with 18 pairs it is 0.1, and with 3,000 pairs it is below 0.1.
- AC_4 (Monotone): over the iterations the regularised loss never increases for pair sets of 18, 100, 1,000
  and 3,000 pairs; the test uses the loss of Story 18.2 and fails if a step raises it by more than 1e-12.
- AC_5 (Order): on a consistent set of 3,000 pairs (x > y 1,500, x > z 900, y > z 600) the returned
  logits keep x > y > z.
- AC_6 (Honest Convergence): a fit stopped by the cap has converged false and a stationarity above tol;
  a fit that stops early has converged true and stationarity below tol; iterations equals the number of steps taken.
- AC_7 (Deterministic): the same arguments give identical logits on repeated calls and in a fresh process,
  and fit_logits imports no random module.
- AC_8 (Time): the test records the time of a 2,000-step fit on three actions with 1,000 pairs and fails
  only if it exceeds 5 seconds; the recorded value is not claimed as a benchmark.
"""

import time

import pytest

from agent_learning_ext.learners.pairwise import (
    FitResult,
    PreferencePair,
    bt_loss,
    fit_logits,
)


def test_ac0_validation_bounds_and_arguments():
    """AC_0: lam < 0.05, non-finite values, lr<=0, steps<1, clamp<=0, missing actions raise ValueError."""
    actions = ["x", "y", "z"]
    ref_zeros = {"x": 0.0, "y": 0.0, "z": 0.0}
    pair_valid = [PreferencePair(winner="x", loser="y", source_episode_id="ep-1")]

    # lam bounds
    with pytest.raises(ValueError, match="lam"):
        fit_logits(pair_valid, actions, ref_zeros, lam=0.049)

    res_05 = fit_logits(pair_valid, actions, ref_zeros, lam=0.05)
    assert isinstance(res_05, FitResult)

    # non-finite arguments
    with pytest.raises(ValueError, match="lam"):
        fit_logits(pair_valid, actions, ref_zeros, lam=float("nan"))
    with pytest.raises(ValueError, match="lr"):
        fit_logits(pair_valid, actions, ref_zeros, lr=float("inf"))
    with pytest.raises(ValueError, match="clamp"):
        fit_logits(pair_valid, actions, ref_zeros, clamp=float("nan"))
    with pytest.raises(ValueError, match="tol"):
        fit_logits(pair_valid, actions, ref_zeros, tol=float("nan"))
    with pytest.raises(ValueError, match="theta_ref"):
        fit_logits(pair_valid, actions, {"x": float("nan"), "y": 0.0, "z": 0.0})

    # bounds on lr, steps, clamp
    with pytest.raises(ValueError, match="lr"):
        fit_logits(pair_valid, actions, ref_zeros, lr=0.0)
    with pytest.raises(ValueError, match="lr"):
        fit_logits(pair_valid, actions, ref_zeros, lr=-0.1)
    with pytest.raises(ValueError, match="steps"):
        fit_logits(pair_valid, actions, ref_zeros, steps=0)
    with pytest.raises(ValueError, match="clamp"):
        fit_logits(pair_valid, actions, ref_zeros, clamp=0.0)

    # action missing from theta_ref
    with pytest.raises(ValueError, match="theta_ref"):
        fit_logits(pair_valid, actions, {"x": 0.0, "y": 0.0})

    # pair naming an unknown action
    unknown_pair = [PreferencePair(winner="x", loser="unknown_action", source_episode_id="ep-bad")]
    with pytest.raises(ValueError, match="action"):
        fit_logits(unknown_pair, actions, ref_zeros)


def test_ac1_no_pairs_returns_theta_ref_exact():
    """AC_1: With no pair, returned logits equal theta_ref exactly and converged is true."""
    actions = ["x", "y", "z"]
    theta_ref = {"x": 1.25, "y": -0.75, "z": 0.5}

    res = fit_logits([], actions, theta_ref)
    assert res.converged is True
    assert res.iterations == 0
    assert res.stationarity == 0.0
    for a in actions:
        assert res.logits[a] == theta_ref[a]


def test_ac2_logits_clamped_to_box():
    """AC_2: Every logit lies in [-8.0, +8.0], even with strong bias or theta_ref outside box."""
    actions = ["x", "y"]
    # 500 pairs pushing x > y massively
    pairs = [PreferencePair(winner="x", loser="y", source_episode_id=f"ep-{i}") for i in range(500)]
    ref_outside = {"x": 15.0, "y": -12.0}

    res = fit_logits(pairs, actions, ref_outside, clamp=8.0, steps=100)
    for val in res.logits.values():
        assert -8.0 <= val <= 8.0


def test_ac3_step_size_monotonic_formula():
    """AC_3: step_size equals min(lr, 1 / (lam + 0.5 * max_degree)).
    On base set with 18 pairs it is 0.1; on 3,000 pairs it is below 0.1.
    """
    actions = ["x", "y", "z"]
    ref_zeros = {"x": 0.0, "y": 0.0, "z": 0.0}

    # 18 pairs: 10 x > y, 8 y > z
    # max_degree: x has 10, y has 18, z has 8 -> max_degree = 18
    # 1 / (0.05 + 0.5 * 18) = 1 / 9.05 = 0.1105 > lr(0.1) -> step_size = 0.1
    pairs_18 = (
        [PreferencePair(winner="x", loser="y", source_episode_id=f"xy-{i}") for i in range(10)]
        + [PreferencePair(winner="y", loser="z", source_episode_id=f"yz-{i}") for i in range(8)]
    )
    res_18 = fit_logits(pairs_18, actions, ref_zeros, lr=0.1, lam=0.05)
    assert abs(res_18.step_size - 0.1) < 1e-12

    # 3,000 pairs: max_degree >= 1,000 -> step_size < 0.1
    pairs_3000 = (
        [PreferencePair(winner="x", loser="y", source_episode_id=f"p1-{i}") for i in range(1500)]
        + [PreferencePair(winner="x", loser="z", source_episode_id=f"p2-{i}") for i in range(900)]
        + [PreferencePair(winner="y", loser="z", source_episode_id=f"p3-{i}") for i in range(600)]
    )
    res_3000 = fit_logits(pairs_3000, actions, ref_zeros, lr=0.1, lam=0.05)
    expected_step_3000 = min(0.1, 1.0 / (0.05 + 0.5 * 2400))  # x is in 2400 pairs
    assert abs(res_3000.step_size - expected_step_3000) < 1e-12
    assert res_3000.step_size < 0.1


def test_ac4_loss_monotonically_non_increasing():
    """AC_4: Regularised loss never increases over iterations for 18, 100, 1000, 3000 pairs."""
    actions = ["x", "y", "z"]
    ref_zeros = {"x": 0.0, "y": 0.0, "z": 0.0}

    for n_pairs in (18, 100, 1000, 3000):
        # Generate synthetic pairs with various proportions
        p_xy = int(n_pairs * 0.5)
        p_xz = int(n_pairs * 0.3)
        p_yz = n_pairs - p_xy - p_xz
        pairs = (
            [PreferencePair(winner="x", loser="y", source_episode_id=f"p1-{n_pairs}-{i}") for i in range(p_xy)]
            + [PreferencePair(winner="x", loser="z", source_episode_id=f"p2-{n_pairs}-{i}") for i in range(p_xz)]
            + [PreferencePair(winner="y", loser="z", source_episode_id=f"p3-{n_pairs}-{i}") for i in range(p_yz)]
        )

        # Run with trace callback to inspect every iteration
        loss_history: list[float] = []

        def _record_loss(current_theta: dict[str, float], p_set=pairs, hist=loss_history) -> None:
            hist.append(bt_loss(current_theta, p_set, ref_zeros, actions, lam=0.05))

        fit_res = fit_logits(pairs, actions, ref_zeros, steps=100, trace_fn=_record_loss)
        assert fit_res is not None
        assert len(loss_history) >= 2

        for step_idx in range(len(loss_history) - 1):
            diff = loss_history[step_idx + 1] - loss_history[step_idx]
            assert diff <= 1e-12, f"Loss increased at step {step_idx}: diff {diff} > 1e-12"


def test_ac5_order_preserved_on_consistent_set():
    """AC_5: 3,000 consistent pairs (x>y 1500, x>z 900, y>z 600) yields x > y > z."""
    actions = ["x", "y", "z"]
    ref_zeros = {"x": 0.0, "y": 0.0, "z": 0.0}
    pairs = (
        [PreferencePair(winner="x", loser="y", source_episode_id=f"p1-{i}") for i in range(1500)]
        + [PreferencePair(winner="x", loser="z", source_episode_id=f"p2-{i}") for i in range(900)]
        + [PreferencePair(winner="y", loser="z", source_episode_id=f"p3-{i}") for i in range(600)]
    )

    res = fit_logits(pairs, actions, ref_zeros, steps=1000)
    assert res.logits["x"] > res.logits["y"] > res.logits["z"]


def test_ac6_honest_convergence_reporting():
    """AC_6: Cap stop reports converged=False & stationarity>tol; early stop reports converged=True & stationarity<tol."""
    actions = ["x", "y", "z"]
    ref_zeros = {"x": 0.0, "y": 0.0, "z": 0.0}
    pairs = [
        PreferencePair(winner="x", loser="y", source_episode_id="ep-1"),
        PreferencePair(winner="y", loser="z", source_episode_id="ep-2"),
    ]

    # 1. Stopped by cap: steps=1 with tight tolerance
    res_cap = fit_logits(pairs, actions, ref_zeros, steps=1, tol=1e-12)
    assert res_cap.converged is False
    assert res_cap.iterations == 1
    assert res_cap.stationarity > 1e-12

    # 2. Early convergence: steps=2000 with loose tolerance
    res_converged = fit_logits(pairs, actions, ref_zeros, steps=2000, tol=1e-4)
    assert res_converged.converged is True
    assert res_converged.iterations < 2000
    assert res_converged.stationarity <= 1e-4


def test_ac7_deterministic_and_no_random_imports():
    """AC_7: Repeated calls give identical logits; fit_logits module imports no random module."""
    import agent_learning_ext.learners.pairwise as pw_module

    # Must not import random or numpy.random in the module namespace
    assert "random" not in pw_module.__dict__

    actions = ["x", "y", "z"]
    ref_zeros = {"x": 0.0, "y": 0.0, "z": 0.0}
    pairs = [
        PreferencePair(winner="x", loser="y", source_episode_id="ep-1"),
        PreferencePair(winner="y", loser="z", source_episode_id="ep-2"),
    ]

    res1 = fit_logits(pairs, actions, ref_zeros, steps=200)
    res2 = fit_logits(pairs, actions, ref_zeros, steps=200)

    assert res1.logits == res2.logits
    assert res1.iterations == res2.iterations
    assert res1.loss == res2.loss


def test_ac8_time_within_loose_5s_bound():
    """AC_8: 2,000-step fit on 3 actions with 1,000 pairs takes < 5.0 seconds."""
    actions = ["x", "y", "z"]
    ref_zeros = {"x": 0.0, "y": 0.0, "z": 0.0}
    pairs = (
        [PreferencePair(winner="x", loser="y", source_episode_id=f"p1-{i}") for i in range(500)]
        + [PreferencePair(winner="x", loser="z", source_episode_id=f"p2-{i}") for i in range(300)]
        + [PreferencePair(winner="y", loser="z", source_episode_id=f"p3-{i}") for i in range(200)]
    )

    t0 = time.perf_counter()
    res = fit_logits(pairs, actions, ref_zeros, steps=2000, tol=1e-15)  # force all 2,000 steps
    elapsed = time.perf_counter() - t0

    assert res.iterations == 2000
    assert elapsed < 5.0, f"Elapsed time {elapsed:.3f}s exceeded 5.0s limit"
