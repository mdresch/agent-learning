"""Discrete Pairwise Preference Optimization (DPO / Bradley-Terry) interface.

Re-exports core primitives from agent_learning_ext.learners.pairwise under the
agent-training-ext namespace (Milestone M7 / Schedule Baseline Phase 2).
"""

from __future__ import annotations

from agent_learning_ext.learners.pairwise import (
    CLAMP,
    LAMBDA_MIN,
    LR_DEFAULT,
    STEPS_DEFAULT,
    TOL_DEFAULT,
    FitResult,
    PairwiseLearner,
    PreferencePair,
    bt_gradient,
    bt_loss,
    build_pair_matrix,
    fit_logits,
    pairs_from_episodes,
)
from agent_learning_ext.training import TrainingRunner

__all__ = [
    "CLAMP",
    "LAMBDA_MIN",
    "LR_DEFAULT",
    "STEPS_DEFAULT",
    "TOL_DEFAULT",
    "FitResult",
    "PairwiseLearner",
    "PreferencePair",
    "TrainingRunner",
    "bt_gradient",
    "bt_loss",
    "build_pair_matrix",
    "fit_logits",
    "pairs_from_episodes",
]
