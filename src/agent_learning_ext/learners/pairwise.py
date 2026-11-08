"""Pairwise Preference Optimization for discrete action logits (ADR-018, Epic 18).

Fits a SoftmaxPolicy's action logits directly to preference pairs (winner, loser)
extracted from human reviewer overrides with the Bradley-Terry model and convex
L2 regularization anchored to frozen reference logits.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np

from agent_learning.learners import Learner, LearnerResult
from agent_learning.policy import Policy, SoftmaxPolicy
from agent_learning.types import Episode


@dataclass(frozen=True)
class PreferencePair:
    """An ordinal preference between two discrete actions derived from an episode override."""

    winner: str
    loser: str
    source_episode_id: str


# FDD-018 §2.1 Constants
LAMBDA_MIN: float = 0.05
CLAMP: float = 8.0
LR_DEFAULT: float = 0.1
STEPS_DEFAULT: int = 2000
TOL_DEFAULT: float = 1e-8


@dataclass(frozen=True)
class FitResult:
    """The result of fitting action logits to pairwise preferences (FDD-018 §2.2)."""

    logits: dict[str, float]
    converged: bool
    iterations: int
    stationarity: float
    step_size: float
    loss: float


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


def fit_logits(
    pairs: Sequence[PreferencePair],
    action_ids: Sequence[str],
    theta_ref: Mapping[str, float] | Sequence[float],
    *,
    lam: float = 0.05,
    lr: float = 0.1,
    steps: int = 2000,
    clamp: float = 8.0,
    tol: float = 1e-8,
    trace_fn: Callable[[dict[str, float]], None] | None = None,
) -> FitResult:
    """Fit action logits directly to preference pairs via projected gradient descent (FDD-018 §3 item 2).

    Parameters:
    - pairs: Sequence of PreferencePair(winner, loser, source_episode_id).
    - action_ids: Sequence of valid discrete action identifiers.
    - theta_ref: Anchor reference logits, as a mapping or sequence aligned with action_ids.
    - lam: L2 regularization parameter (must be >= LAMBDA_MIN = 0.05).
    - lr: Maximum step size (learning rate, must be > 0).
    - steps: Maximum iterations cap (must be >= 1).
    - clamp: Absolute logit boundary box [-clamp, +clamp] (must be > 0).
    - tol: Stationarity tolerance for early stopping (must be > 0).
    - trace_fn: Optional callback invoked with the current logit mapping before optimization
      and after each iteration step.
    """
    # 1. Parameter validation (AC_0)
    if not math.isfinite(lam) or lam < LAMBDA_MIN:
        raise ValueError(f"Regularization parameter lam must be at least {LAMBDA_MIN}, got {lam}")
    if not math.isfinite(lr) or lr <= 0.0:
        raise ValueError(f"Learning rate lr must be a finite positive float, got {lr}")
    if steps < 1:
        raise ValueError(f"Iteration cap steps must be at least 1, got {steps}")
    if not math.isfinite(clamp) or clamp <= 0.0:
        raise ValueError(f"Clamp parameter clamp must be a finite positive float, got {clamp}")
    if not math.isfinite(tol) or tol <= 0.0:
        raise ValueError(f"Tolerance tol must be a finite positive float, got {tol}")

    # 2. Reference logits validation (AC_0)
    if isinstance(theta_ref, Mapping):
        missing = [a for a in action_ids if a not in theta_ref]
        if missing:
            raise ValueError(f"Missing action(s) in theta_ref: {missing}")
        for a in action_ids:
            val = float(theta_ref[a])
            if not math.isfinite(val):
                raise ValueError(f"Non-finite value in theta_ref for action '{a}': {val}")
        r_vec = np.array([float(theta_ref[a]) for a in action_ids], dtype=np.float64)
    else:
        arr = np.asarray(theta_ref, dtype=np.float64)
        if arr.ndim != 1 or arr.shape[0] != len(action_ids):
            raise ValueError(f"Expected 1D sequence in theta_ref of length {len(action_ids)}, got shape {arr.shape}")
        if not np.all(np.isfinite(arr)):
            raise ValueError("All values in theta_ref must be finite")
        r_vec = arr

    # 3. Pair actions validation (AC_0)
    valid_actions = set(action_ids)
    for p in pairs:
        if p.winner not in valid_actions or p.loser not in valid_actions:
            raise ValueError(
                f"Preference pair names unknown action(s): winner='{p.winner}', loser='{p.loser}' not in {action_ids}"
            )

    # 4. Pair deduplication by episode ID (FDD-018 §3 item 2.1, G5)
    deduped_pairs: list[PreferencePair] = []
    seen_episodes: set[str] = set()
    for p in pairs:
        if p.source_episode_id in seen_episodes:
            continue
        seen_episodes.add(p.source_episode_id)
        deduped_pairs.append(p)

    # 5. Build count matrix W and calculate max_degree (AC_3)
    W = build_pair_matrix(deduped_pairs, action_ids)
    if len(action_ids) > 0 and len(deduped_pairs) > 0:
        degrees = np.sum(W, axis=1) + np.sum(W, axis=0)
        max_degree = float(np.max(degrees))
    else:
        max_degree = 0.0

    step_size = float(min(lr, 1.0 / (lam + 0.5 * max_degree)))

    # Start at theta_ref clipped to box (AC_2, FDD-018 §3 item 2.3)
    theta = np.clip(r_vec, -clamp, clamp)

    # Case: No pairs (AC_1)
    if len(deduped_pairs) == 0:
        res_logits = {a: float(theta[i]) for i, a in enumerate(action_ids)}
        if trace_fn is not None:
            trace_fn(res_logits)
        no_pairs_loss = bt_loss(theta, W, r_vec, action_ids, lam=lam)
        return FitResult(
            logits=res_logits,
            converged=True,
            iterations=0,
            stationarity=0.0,
            step_size=step_size,
            loss=no_pairs_loss,
        )

    # Initial trace recording
    if trace_fn is not None:
        trace_fn({a: float(theta[i]) for i, a in enumerate(action_ids)})

    converged = False
    stationarity = 0.0
    actual_iterations = steps

    # 6. Projected Gradient Descent loop (AC_4, AC_6)
    for step_idx in range(1, steps + 1):
        # Exact vectorized gradient of regularized Bradley-Terry loss
        Z = theta[:, None] - theta[None, :]
        S = np.exp(-np.logaddexp(0.0, Z))
        M = W * S
        data_grad = - np.sum(M, axis=1) + np.sum(M, axis=0)
        reg_grad = lam * (theta - r_vec)
        grad = data_grad + reg_grad

        # Gradient step + projection onto box [-clamp, +clamp]
        theta_candidate = np.clip(theta - step_size * grad, -clamp, clamp)
        stationarity = float(np.max(np.abs(theta - theta_candidate)) / step_size)

        theta = theta_candidate

        if trace_fn is not None:
            trace_fn({a: float(theta[i]) for i, a in enumerate(action_ids)})

        if stationarity <= tol:
            converged = True
            actual_iterations = step_idx
            break

    # 7. Final regularized loss (FDD-018 §2.4)
    final_loss = bt_loss(theta, W, r_vec, action_ids, lam=lam)

    return FitResult(
        logits={a: float(theta[i]) for i, a in enumerate(action_ids)},
        converged=converged,
        iterations=actual_iterations,
        stationarity=stationarity,
        step_size=step_size,
        loss=final_loss,
    )


def _validate_or_freeze_reference(
    policy: Policy,
    action_ids: Sequence[str],
    *,
    freeze: bool,
) -> tuple[dict[str, float], dict[str, float]]:
    """Validate stored reference logits, or freeze if missing and freeze=True.

    Reads metadata and logits directly from policy._snapshot to prevent source divergence.
    Returns (theta_ref, stored_dict_for_extra).
    Raises ValueError on invalid/corrupt reference.
    Raises AttributeError if policy has no _snapshot.metadata.
    """
    if not hasattr(policy, "_snapshot") or not hasattr(policy._snapshot, "metadata"):
        raise AttributeError(
            f"Policy of type '{type(policy).__name__}' does not expose persistent '_snapshot.metadata'"
        )
    snap = policy._snapshot
    metadata = snap.metadata
    if "pairwise_reference_logits" in metadata:
        ref_raw = metadata["pairwise_reference_logits"]
        if not isinstance(ref_raw, Mapping):
            raise ValueError("pairwise_reference_logits in policy metadata must be a mapping")
        missing = [a for a in action_ids if a not in ref_raw]
        if missing:
            raise ValueError(f"Missing action(s) in pairwise_reference_logits: {missing}")
        for a in action_ids:
            val = float(ref_raw[a])
            if not math.isfinite(val):
                raise ValueError(f"Non-finite value for action '{a}' in pairwise_reference_logits: {val}")
        theta_ref = {a: float(ref_raw[a]) for a in action_ids}
        return theta_ref, dict(ref_raw)

    theta_ref = {a: float(snap.logits[a]) for a in action_ids}
    if freeze:
        metadata["pairwise_reference_logits"] = dict(theta_ref)
    return theta_ref, dict(theta_ref)


class PairwiseLearner(Learner):
    """Pairwise Preference Optimization learner for discrete SoftmaxPolicy (FDD-018 §3 item 3).

    Fits action logits directly to preference pairs (winner, loser) extracted from human
    reviewer overrides with the Bradley-Terry model and convex L2 regularization anchored
    to frozen reference logits.
    """

    def __init__(
        self,
        *,
        lam: float = LAMBDA_MIN,
        lr: float = LR_DEFAULT,
        steps: int = STEPS_DEFAULT,
        clamp: float = CLAMP,
        tol: float = TOL_DEFAULT,
    ) -> None:
        if not math.isfinite(lam) or lam < LAMBDA_MIN:
            raise ValueError(f"Regularization parameter lam must be at least {LAMBDA_MIN}, got {lam}")
        if not math.isfinite(lr) or lr <= 0.0:
            raise ValueError(f"Learning rate lr must be a finite positive float, got {lr}")
        if steps < 1:
            raise ValueError(f"Iteration cap steps must be at least 1, got {steps}")
        if not math.isfinite(clamp) or clamp <= 0.0:
            raise ValueError(f"Clamp parameter clamp must be a finite positive float, got {clamp}")
        if not math.isfinite(tol) or tol <= 0.0:
            raise ValueError(f"Tolerance tol must be a finite positive float, got {tol}")

        self.lam = lam
        self.lr = lr
        self.steps = steps
        self.clamp = clamp
        self.tol = tol

    def update(
        self,
        policy: Any,
        episodes: Sequence[Episode],
        rewards: Sequence[float] | None = None,
    ) -> LearnerResult:
        """Update a SoftmaxPolicy with preference pairs extracted from episodes (FDD-018 §3 item 3)."""
        # 1. Type validation (AC_0)
        if not isinstance(policy, SoftmaxPolicy):
            raise TypeError(f"PairwiseLearner requires a SoftmaxPolicy instance, got {type(policy)}")
        if policy.max_logit_abs < CLAMP:
            raise ValueError(
                f"SoftmaxPolicy max_logit_abs ({policy.max_logit_abs}) must be at least CLAMP ({CLAMP})"
            )

        snapshot = policy.snapshot()
        action_ids = [a.id if hasattr(a, "id") else str(a) for a in snapshot.actions]

        # 2. Extract preference pairs (AC_3, FDD-018 G3, G5)
        pairs = pairs_from_episodes(episodes, action_ids)
        unique_episode_ids = {ep.id for ep in episodes}

        # 3. Handle zero pairs path (AC_3)
        if len(pairs) == 0:
            theta_ref, ref_extra = _validate_or_freeze_reference(
                policy, action_ids, freeze=False
            )
            loss_zero = bt_loss(snapshot.logits, [], theta_ref, action_ids, lam=self.lam)
            return LearnerResult(
                episodes_used=0,
                mean_reward=0.0,
                baseline_before=snapshot.baseline,
                baseline_after=snapshot.baseline,
                logit_deltas={},
                consumed_inputs=None,
                extra={
                    "pairs": 0,
                    "skipped_episodes": len(unique_episode_ids),
                    "converged": True,
                    "iterations": 0,
                    "stationarity": 0.0,
                    "step_size": min(self.lr, 1.0 / self.lam),
                    "loss_before": loss_zero,
                    "loss_after": loss_zero,
                    "reference_logits": ref_extra,
                },
            )

        # 4. Resolve and validate reference logits (AC_1, FDD-018 G4)
        theta_ref, ref_extra = _validate_or_freeze_reference(
            policy, action_ids, freeze=True
        )

        # 5. Compute loss before update
        loss_before = bt_loss(snapshot.logits, pairs, theta_ref, action_ids, lam=self.lam)

        # 6. Fit logits from theta_ref (FDD-018 G5)
        fit_res = fit_logits(
            pairs=pairs,
            action_ids=action_ids,
            theta_ref=theta_ref,
            lam=self.lam,
            lr=self.lr,
            steps=self.steps,
            clamp=self.clamp,
            tol=self.tol,
        )

        # 7. Compute deltas = fitted - current (FDD-018 §3 item 3.4)
        deltas = {a: float(fit_res.logits[a] - snapshot.logits[a]) for a in action_ids}

        # 8. Apply deltas to policy, keeping episodes_seen unchanged (FDD-018 §3 item 3.4, AC_4)
        policy.apply_update(
            deltas,
            baseline=snapshot.baseline,
            episodes_seen=snapshot.episodes_seen,
        )

        pair_episode_ids = {p.source_episode_id for p in pairs}
        return LearnerResult(
            episodes_used=len(pairs),
            mean_reward=0.0,
            baseline_before=snapshot.baseline,
            baseline_after=snapshot.baseline,
            logit_deltas=deltas,
            consumed_inputs=None,
            extra={
                "pairs": len(pairs),
                "skipped_episodes": len(unique_episode_ids - pair_episode_ids),
                "converged": fit_res.converged,
                "iterations": fit_res.iterations,
                "stationarity": fit_res.stationarity,
                "step_size": fit_res.step_size,
                "loss_before": loss_before,
                "loss_after": fit_res.loss,
                "reference_logits": dict(theta_ref),
            },
        )


__all__ = [
    "CLAMP",
    "LAMBDA_MIN",
    "LR_DEFAULT",
    "STEPS_DEFAULT",
    "TOL_DEFAULT",
    "FitResult",
    "PairwiseLearner",
    "PreferencePair",
    "bt_gradient",
    "bt_loss",
    "build_pair_matrix",
    "fit_logits",
    "pairs_from_episodes",
]

