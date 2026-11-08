"""Learners: Microsoft's, plus the ones we added and amended.

Import from here when you need our learners. ``agent_learning.learners`` stays exactly as Microsoft ships it.
"""

from __future__ import annotations

from agent_learning.learners import Learner, LearnerResult
from agent_learning.learners.thompson import ThompsonLearner

from .pairwise import PreferencePair, pairs_from_episodes
from .reinforce import ReinforceLearner

__all__ = [
    "Learner",
    "LearnerResult",
    "PreferencePair",
    "ReinforceLearner",
    "ThompsonLearner",
    "pairs_from_episodes",
]
