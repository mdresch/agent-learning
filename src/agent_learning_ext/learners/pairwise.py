"""Pairwise Preference Optimization for discrete action logits (ADR-018, Epic 18).

Fits a SoftmaxPolicy's action logits directly to preference pairs (winner, loser)
extracted from human reviewer overrides with the Bradley-Terry model and convex
L2 regularization anchored to frozen reference logits.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np

from agent_learning.types import Episode


@dataclass(frozen=True)
class PreferencePair:
    """An ordinal preference between two discrete actions derived from an episode override."""

    winner: str
    loser: str
    source_episode_id: str


def pairs_from_episodes(
    episodes: Sequence[Episode],
    action_ids: Sequence[str],
) -> list[PreferencePair]:
    """Extract preference pairs from reviewer override episodes (FDD-018 §3 item 1).

    An episode yields a pair (winner=correct_action_id, loser=action_id) when:
    - metadata["feedback_status"], stripped and lowercased, is "rejected"
    - metadata["correct_action_id"] is a string in action_ids
    - action_id is in action_ids
    - correct_action_id != action_id

    Episodes offered multiple times contribute at most one pair, preserving
    the order of first appearance (G5). Input episodes are never modified.
    """
    valid_actions = set(action_ids)
    pairs: list[PreferencePair] = []
    seen_episode_ids: set[str] = set()

    for ep in episodes:
        if ep.id in seen_episode_ids:
            continue

        meta: dict[str, Any] = getattr(ep, "metadata", {}) or {}

        # 1. Feedback status check
        status_raw = meta.get("feedback_status")
        if not isinstance(status_raw, str):
            continue
        if status_raw.strip().lower() != "rejected":
            continue

        # 2. Correct action check
        correct_action = meta.get("correct_action_id")
        if not isinstance(correct_action, str):
            continue
        if correct_action not in valid_actions:
            continue

        # 3. Proposed action check
        proposed_action = getattr(ep, "action_id", None)
        if not isinstance(proposed_action, str):
            continue
        if proposed_action not in valid_actions:
            continue

        # 4. Differing actions
        if correct_action == proposed_action:
            continue

        seen_episode_ids.add(ep.id)
        pairs.append(
            PreferencePair(
                winner=correct_action,
                loser=proposed_action,
                source_episode_id=ep.id,
            )
        )

    return pairs


def build_pair_matrix(
    pairs: Sequence[PreferencePair],
    action_ids: Sequence[str],
) -> np.ndarray:
    """Build preference count matrix W of shape (|A|, |A|) (FDD-018 §2.4).

    W[w, l] is the count of pairs preferring action w over action l.
    """
    action_to_idx = {a: i for i, a in enumerate(action_ids)}
    n = len(action_ids)
    W = np.zeros((n, n), dtype=np.float64)
    for p in pairs:
        w_idx = action_to_idx.get(p.winner)
        l_idx = action_to_idx.get(p.loser)
        if w_idx is not None and l_idx is not None:
            W[w_idx, l_idx] += 1.0
    return W


def _as_vector(data: Mapping[str, float] | np.ndarray | Sequence[float], action_ids: Sequence[str]) -> np.ndarray:
    """Convert a mapping or array of action values to a float64 1D array ordered by action_ids."""
    if isinstance(data, Mapping):
        missing = [a for a in action_ids if a not in data]
        if missing:
            raise ValueError(f"Missing required action(s) in parameter mapping: {missing}")
        return np.array([float(data[a]) for a in action_ids], dtype=np.float64)
    arr = np.asarray(data, dtype=np.float64)
    if arr.ndim != 1 or arr.shape[0] != len(action_ids):
        raise ValueError(f"Expected 1D array of length {len(action_ids)}, got shape {arr.shape}")
    return arr


def _resolve_W(pairs_or_W: Sequence[PreferencePair] | np.ndarray, action_ids: Sequence[str]) -> np.ndarray:
    """Validate and return count matrix W of shape (|A|, |A|)."""
    n = len(action_ids)
    if isinstance(pairs_or_W, np.ndarray):
        if pairs_or_W.ndim != 2 or pairs_or_W.shape != (n, n):
            raise ValueError(f"Expected 2D preference matrix W of shape ({n}, {n}), got shape {pairs_or_W.shape}")
        if np.any(pairs_or_W < 0.0):
            raise ValueError("Preference count matrix W must contain non-negative values")
        return pairs_or_W
    if isinstance(pairs_or_W, (str, bytes)) or not isinstance(pairs_or_W, Sequence):
        raise TypeError(f"Expected sequence of PreferencePair or 2D ndarray, got {type(pairs_or_W)}")
    for item in pairs_or_W:
        if not isinstance(item, PreferencePair):
            raise TypeError(f"Expected elements of pairs to be PreferencePair, got {type(item)}")
    return build_pair_matrix(pairs_or_W, action_ids)


def bt_loss(
    theta: Mapping[str, float] | np.ndarray | Sequence[float],
    pairs_or_W: Sequence[PreferencePair] | np.ndarray,
    theta_ref: Mapping[str, float] | np.ndarray | Sequence[float],
    action_ids: Sequence[str],
    *,
    lam: float = 0.05,
) -> float:
    """Calculate the regularized Bradley-Terry cross-entropy loss (FDD-018 §2.4).

    loss(theta) = sum_{(w,l)} W[w][l] * log(1 + exp(-(theta_w - theta_l)))
                + (lambda / 2) * sum_a (theta_a - theta_ref_a)^2
    """
    if lam < 0.0:
        raise ValueError(f"Regularization parameter lam must be non-negative, got {lam}")
    t_vec = _as_vector(theta, action_ids)
    r_vec = _as_vector(theta_ref, action_ids)
    W = _resolve_W(pairs_or_W, action_ids)

    # Z[w, l] = theta_w - theta_l
    Z = t_vec[:, None] - t_vec[None, :]
    # log(1 + exp(-z)) computed with numerically stable logaddexp
    pair_cross_entropy = np.sum(W * np.logaddexp(0.0, -Z))

    # L2 regularizer anchored to theta_ref
    reg = 0.5 * lam * np.sum((t_vec - r_vec) ** 2)

    return float(pair_cross_entropy + reg)


def bt_gradient(
    theta: Mapping[str, float] | np.ndarray | Sequence[float],
    pairs_or_W: Sequence[PreferencePair] | np.ndarray,
    theta_ref: Mapping[str, float] | np.ndarray | Sequence[float],
    action_ids: Sequence[str],
    *,
    lam: float = 0.05,
) -> dict[str, float]:
    """Calculate the exact gradient of the regularized Bradley-Terry loss (FDD-018 §2.4).

    grad_a = -sum_l W[a][l] * s(a, l) + sum_w W[w][a] * s(w, a) + lambda * (theta_a - theta_ref_a)
    with s(w, l) = 1 / (1 + exp(theta_w - theta_l)) = sigmoid(-(theta_w - theta_l)).
    """
    if lam < 0.0:
        raise ValueError(f"Regularization parameter lam must be non-negative, got {lam}")
    t_vec = _as_vector(theta, action_ids)
    r_vec = _as_vector(theta_ref, action_ids)
    W = _resolve_W(pairs_or_W, action_ids)

    # Z[i, j] = theta_i - theta_j
    Z = t_vec[:, None] - t_vec[None, :]
    # S[i, j] = 1 / (1 + exp(Z[i, j])) = sigmoid(-Z[i, j])
    # Numerically stable: 1 / (1 + exp(z)) = exp(-logaddexp(0, z))
    S = np.exp(-np.logaddexp(0.0, Z))

    # M[i, j] = W[i, j] * S[i, j]
    M = W * S

    # grad_a = - sum_l M[a, l] + sum_w M[w, a] + lam * (theta_a - theta_ref_a)
    # sum_l M[a, l] is row sum (axis=1); sum_w M[w, a] is column sum (axis=0)
    data_grad = - np.sum(M, axis=1) + np.sum(M, axis=0)
    reg_grad = lam * (t_vec - r_vec)

    total_grad = data_grad + reg_grad
    return {a: float(total_grad[i]) for i, a in enumerate(action_ids)}

