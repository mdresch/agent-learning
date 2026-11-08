"""Discrete Pairwise Preference Optimization (DPO / Bradley-Terry) interface.

Re-exports core primitives from agent_learning_ext.learners.pairwise under the
agent-training-ext namespace (Milestone M7 / Schedule Baseline Phase 2).
"""

from __future__ import annotations

from agent_learning_ext.learners.pairwise import PreferencePair, pairs_from_episodes

__all__ = ["PreferencePair", "pairs_from_episodes"]
