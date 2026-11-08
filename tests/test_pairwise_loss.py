"""Contract tests for Story 18.2 — The Loss and Its Gradient.

Source ADR: ADR-018 (Pairwise Preference Optimization for Discrete Action Logits)
Source BRD: BRD-018 (BRU-018-01, BRU-018-03)
Source FDD: FDD-018 (§2.4, G1)
Story: Story 18.2 (The Loss and Its Gradient)

Acceptance Criteria:
- AC_0 (Loss): on the base set with pairs x > y x2 and y > z x1 and theta = (0.3, -0.2, 0.1),
  the loss equals the term-by-term sum of log(1 + exp(-(theta_w - theta_l))) plus
  (lambda / 2) * ||theta - theta_ref||^2, computed in the test, within 1e-12.
- AC_1 (Gradient): the analytic gradient equals a central finite difference of the loss
  within 1e-6 on at least five random theta and pair sets.
- AC_2 (Aggregated): the matrix form of FDD-018 §2.4 equals the sum over individual pairs
  within 1e-12, including a pair set with repeated pairs.
- AC_3 (Single Pair): for one pair x > y, theta_ref = 0 and lambda = 0.05, the gradient
  at theta = (0, 0) is (-0.5, +0.5, 0) and at theta = (1.3235, -1.3235, 0) is zero within 1e-3.
"""

import math
import numpy as np
import pytest

from agent_learning_ext.learners.pairwise import (
    PreferencePair,
    bt_loss,
    bt_gradient,
    build_pair_matrix,
)


def test_ac0_loss_exact_value():
    """AC_0: Term-by-term loss calculation equals analytical loss within 1e-12."""
    actions = ["x", "y", "z"]
    pairs = [
        PreferencePair(winner="x", loser="y", source_episode_id="ep-1"),
        PreferencePair(winner="x", loser="y", source_episode_id="ep-2"),
        PreferencePair(winner="y", loser="z", source_episode_id="ep-3"),
    ]
    theta = {"x": 0.3, "y": -0.2, "z": 0.1}
    theta_ref = {"x": 0.0, "y": 0.0, "z": 0.0}
    lam = 0.05

    # Term-by-term reference computation
    # Pair 1: x > y
    term1 = math.log(1.0 + math.exp(-(theta["x"] - theta["y"])))
    # Pair 2: x > y
    term2 = math.log(1.0 + math.exp(-(theta["x"] - theta["y"])))
    # Pair 3: y > z
    term3 = math.log(1.0 + math.exp(-(theta["y"] - theta["z"])))

    # Regularization
    reg = (lam / 2.0) * sum((theta[a] - theta_ref[a]) ** 2 for a in actions)
    expected_loss = term1 + term2 + term3 + reg

    actual_loss = bt_loss(theta, pairs, theta_ref, actions, lam=lam)
    assert abs(actual_loss - expected_loss) < 1e-12


def test_ac1_gradient_matches_finite_difference():
    """AC_1: Analytic gradient matches central finite difference of loss within 1e-6 on >= 5 random setups."""
    actions = ["x", "y", "z"]
    lam = 0.05
    rng = np.random.default_rng(42)
    eps = 1e-7

    for trial in range(5):
        # Generate random theta and theta_ref
        t_arr = rng.uniform(-2.0, 2.0, size=len(actions))
        r_arr = rng.uniform(-1.0, 1.0, size=len(actions))
        theta = {a: float(t_arr[i]) for i, a in enumerate(actions)}
        theta_ref = {a: float(r_arr[i]) for i, a in enumerate(actions)}

        # Generate random pairs
        pairs = []
        for p_idx in range(rng.integers(3, 10)):
            w, l = rng.choice(actions, size=2, replace=False)
            pairs.append(PreferencePair(winner=str(w), loser=str(l), source_episode_id=f"rand-{trial}-{p_idx}"))

        grad_dict = bt_gradient(theta, pairs, theta_ref, actions, lam=lam)
        analytic_grad = np.array([grad_dict[a] for a in actions], dtype=np.float64)

        # Central finite difference
        num_grad = np.zeros(len(actions), dtype=np.float64)
        for i, a in enumerate(actions):
            theta_plus = dict(theta)
            theta_minus = dict(theta)
            theta_plus[a] += eps
            theta_minus[a] -= eps
            loss_plus = bt_loss(theta_plus, pairs, theta_ref, actions, lam=lam)
            loss_minus = bt_loss(theta_minus, pairs, theta_ref, actions, lam=lam)
            num_grad[i] = (loss_plus - loss_minus) / (2.0 * eps)

        max_err = np.max(np.abs(analytic_grad - num_grad))
        assert max_err < 1e-6, f"Trial {trial} failed: max finite diff error {max_err} >= 1e-6"


def test_ac2_aggregated_matrix_form_equals_pair_sum():
    """AC_2: Matrix form of FDD-018 §2.4 equals pair sum within 1e-12, including repeated pairs."""
    actions = ["x", "y", "z"]
    # Repeat x > y 5 times, y > z 3 times, z > x 2 times
    pairs = (
        [PreferencePair(winner="x", loser="y", source_episode_id=f"xy-{i}") for i in range(5)]
        + [PreferencePair(winner="y", loser="z", source_episode_id=f"yz-{i}") for i in range(3)]
        + [PreferencePair(winner="z", loser="x", source_episode_id=f"zx-{i}") for i in range(2)]
    )
    theta = {"x": 1.2, "y": -0.8, "z": 0.4}
    theta_ref = {"x": 0.1, "y": -0.1, "z": 0.0}
    lam = 0.08

    W = build_pair_matrix(pairs, actions)

    # Loss comparison: pair list vs matrix W
    loss_from_pairs = bt_loss(theta, pairs, theta_ref, actions, lam=lam)
    loss_from_W = bt_loss(theta, W, theta_ref, actions, lam=lam)
    assert abs(loss_from_pairs - loss_from_W) < 1e-12

    # Gradient comparison: pair list vs matrix W
    grad_from_pairs = bt_gradient(theta, pairs, theta_ref, actions, lam=lam)
    grad_from_W = bt_gradient(theta, W, theta_ref, actions, lam=lam)

    for a in actions:
        assert abs(grad_from_pairs[a] - grad_from_W[a]) < 1e-12


def test_ac3_single_pair_gradient_values():
    """AC_3: Single pair x > y, theta_ref = 0, lambda = 0.05.
    At theta = (0, 0, 0), gradient is (-0.5, +0.5, 0).
    At theta = (1.3235, -1.3235, 0), gradient is zero within 1e-3.
    """
    actions = ["x", "y", "z"]
    pairs = [PreferencePair(winner="x", loser="y", source_episode_id="ep-single")]
    theta_ref = {"x": 0.0, "y": 0.0, "z": 0.0}
    lam = 0.05

    # Check at theta = (0, 0, 0)
    theta_zero = {"x": 0.0, "y": 0.0, "z": 0.0}
    grad_zero = bt_gradient(theta_zero, pairs, theta_ref, actions, lam=lam)
    assert abs(grad_zero["x"] - (-0.5)) < 1e-12
    assert abs(grad_zero["y"] - 0.5) < 1e-12
    assert abs(grad_zero["z"] - 0.0) < 1e-12

    # Check at stationary point theta = (1.3235, -1.3235, 0)
    t = 1.3235
    theta_stat = {"x": t, "y": -t, "z": 0.0}
    grad_stat = bt_gradient(theta_stat, pairs, theta_ref, actions, lam=lam)
    assert abs(grad_stat["x"]) < 1e-3
    assert abs(grad_stat["y"]) < 1e-3
    assert abs(grad_stat["z"]) < 1e-3
