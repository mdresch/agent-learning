"""Deterministic Upper Confidence Bound (UCB) learner (ADR-016, FDD-016).

Implements count-based episode updates for UCBPolicy.
Pure standard library only: zero random numbers, zero file I/O.
"""

from __future__ import annotations
