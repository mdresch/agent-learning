"""Learners: Microsoft's, plus the ones we added and amended.

Import from here when you need our learners. ``agent_learning.learners`` stays exactly as Microsoft ships it.
"""

from __future__ import annotations

from agent_learning.learners import Learner, LearnerResult
from agent_learning.learners.thompson import ThompsonLearner

from .pairwise import (
    CLAMP,
    LAMBDA_MIN,
    LR_DEFAULT,
    STEPS_DEFAULT,
    TOL_DEFAULT,
    FitResult,
    PreferencePair,
    bt_gradient,
    bt_loss,
    build_pair_matrix,
    fit_logits,
    pairs_from_episodes,
)
from .reinforce import ReinforceLearner

__all__ = [
    "CLAMP",
    "LAMBDA_MIN",
    "LR_DEFAULT",
    "STEPS_DEFAULT",
    "TOL_DEFAULT",
    "FitResult",
    "Learner",
    "LearnerResult",
    "PreferencePair",
    "ReinforceLearner",
    "ThompsonLearner",
    "bt_gradient",
    "bt_loss",
    "build_pair_matrix",
    "fit_logits",
    "pairs_from_episodes",
]
