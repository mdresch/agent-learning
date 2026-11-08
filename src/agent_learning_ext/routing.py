"""Contextual Authority Ensemble Routing signals and dispatch logic.

Source ADR: ADR-021 §4.1 (Contextual Authority Ensemble Routing)
Source BRD: BRD-021
Source FDD: FDD-021 §1, §2
Stories: 21.1 to 21.7

This module provides the pure routing arithmetic, uncertainty signals (entropy and margin),
hysteresis routing logic, pinning tables, and dispatch helpers.

Purity invariant (Story 21.1 AC_2):
This module imports nothing from agent_learning.storage or agent_learning_ext.storage,
uses no random number generator (no random), and uses no numpy. All arithmetic is pure Python.
"""

from __future__ import annotations

import math
from collections.abc import Sequence


def entropy_bits(probabilities: Sequence[float]) -> float:
    """Compute Shannon entropy in bits (base-2 logarithm) over a discrete probability distribution.

    Formula:
        H(p) = - sum_{p_i > 0} p_i * log2(p_i)

    Boundary conditions:
        - 0.0 probability contributes 0.0 (limit p -> 0 of p * log2(p) = 0).
        - An empty sequence returns 0.0.
        - Single-action distribution [1.0] returns 0.0.
        - Input sequence is never mutated.

    Args:
        probabilities: Sequence of discrete action probabilities.

    Returns:
        Shannon entropy in bits (float >= 0.0).
    """
    total = 0.0
    for p in probabilities:
        if p > 0.0:
            total -= p * math.log2(p)
    return total


# Convenient alias matching standard terminology
entropy = entropy_bits


def margin(probabilities: Sequence[float]) -> float:
    """Compute decision margin: difference between highest and second-highest probabilities.

    Formula:
        Margin(p) = p_(1) - p_(2)

    Boundary conditions:
        - Single-action distribution [1.0] has p_(1) = 1.0 and p_(2) = 0.0, margin = 1.0.
        - Empty sequence returns 0.0.
        - Input sequence is never mutated (sorting is performed on a copy).

    Args:
        probabilities: Sequence of discrete action probabilities.

    Returns:
        Decision margin (float >= 0.0).
    """
    n = len(probabilities)
    if n == 0:
        return 0.0
    if n == 1:
        return float(probabilities[0])

    # Find two largest elements without mutating the input sequence
    first = float("-inf")
    second = float("-inf")
    for p in probabilities:
        p_val = float(p)
        if p_val > first:
            second = first
            first = p_val
        elif p_val > second:
            second = p_val

    return first - second
