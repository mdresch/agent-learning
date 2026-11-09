"""Policies: Microsoft's, plus the ones we added.

Import from here when you need our policies. ``agent_learning.policy`` stays exactly as Microsoft ships it.
"""

from __future__ import annotations

from agent_learning.policy import ContextualSoftmaxPolicy, Policy, SoftmaxPolicy
from agent_learning.policy.scope_advice import (
    ADVICE_TASK_ID,
    DECISION_KINDS,
    GATE_TASK_ID,
    ScopeRecommendation,
    advice_reward,
    baseline_snapshot,
    recommend,
)
from agent_learning.policy.thompson import ThompsonPolicy
from agent_learning_ext.policy.action_statistics import ActionStats, add_rewards, read_statistics, reward_to_r
from agent_learning_ext.policy.epsilon_greedy import EpsilonGreedyPolicy, epsilon_at, replay
from agent_learning_ext.policy.ucb import C_DEFAULT, SELECTION_BASIS, WILSON_Z, UCBPolicy, ucb_scores

__all__ = [
    "ADVICE_TASK_ID",
    "C_DEFAULT",
    "DECISION_KINDS",
    "GATE_TASK_ID",
    "SELECTION_BASIS",
    "WILSON_Z",
    "ActionStats",
    "ContextualSoftmaxPolicy",
    "EpsilonGreedyPolicy",
    "Policy",
    "ScopeRecommendation",
    "SoftmaxPolicy",
    "ThompsonPolicy",
    "UCBPolicy",
    "add_rewards",
    "advice_reward",
    "baseline_snapshot",
    "epsilon_at",
    "read_statistics",
    "recommend",
    "replay",
    "reward_to_r",
    "ucb_scores",
]
