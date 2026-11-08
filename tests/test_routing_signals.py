"""Contract test suite for Story 21.1 — Entropy and Margin.

Source ADR: ADR-021 §4.1 (Contextual Authority Ensemble Routing)
Source BRD: BRD-021
Source FDD: FDD-021 §1, §2
Story: Story 21.1 (Entropy and Margin)

Acceptance Criteria:
- AC_0 (Entropy In Bits): entropy is 2.0 for the uniform distribution over four actions,
  1.0 for [0.5, 0.5], 0.2864 for [0.95, 0.05], 0.7219 for [0.8, 0.2] and 1.4577 for
  [0.45, 0.40, 0.15], within 1e-4, recomputed in the test from -sum p log2 p; a zero
  probability contributes 0.
- AC_1 (Margin): the margin is 0.90, 0.60, 0.0, 0.30 and 0.05 for [0.95, 0.05],
  [0.8, 0.2], [0.5, 0.5], [0.6, 0.3, 0.1] and [0.45, 0.40, 0.15]; a single-action
  distribution [1.0] has entropy 0 and margin 1.0.
- AC_2 (Pure): routing.py imports nothing from agent_learning.storage, no random and no
  numpy, and the input sequence is equal to its copy after the call.

Recommended Interpretations:
- I1: Upstream Fork Purity (Invariant 6): Specification references upstream path
  'src/agent_learning/routing.py'. Per Invariant 6, all custom classes, learners, and helpers
  must be created under 'src/agent_learning_ext/routing.py' (or 'agent-training-ext/'), leaving
  the upstream 'src/agent_learning/' tree completely pristine.
- I2: Empty Collection Base Case: When passed an empty collection or when no probabilities
  are provided, entropy_bits and margin return 0.0 without raising, leaving input unmutated.
"""

from __future__ import annotations

import ast
import inspect
import math
from collections.abc import Sequence
from pathlib import Path

# Per Invariant 6 (Upstream Fork Purity), routing is implemented in agent_learning_ext.routing
from agent_learning_ext.routing import entropy_bits, margin


def _expected_entropy(probabilities: Sequence[float]) -> float:
    """Recompute Shannon entropy in bits directly from definition: -sum p log2 p."""
    total = 0.0
    for p in probabilities:
        if p > 0.0:
            total -= p * math.log2(p)
    return total


def test_ac0_entropy_in_bits() -> None:
    """AC_0: Entropy in bits against specified targets and direct definition."""
    cases = [
        ([0.25, 0.25, 0.25, 0.25], 2.0),
        ([0.5, 0.5], 1.0),
        ([0.95, 0.05], 0.2864),
        ([0.8, 0.2], 0.7219),
        ([0.45, 0.40, 0.15], 1.4577),
    ]

    for probs, expected_target in cases:
        val = entropy_bits(probs)
        # Check against the specified benchmark within 1e-4
        assert abs(val - expected_target) <= 1e-4, (
            f"entropy_bits({probs}) = {val}, expected {expected_target} within 1e-4"
        )
        # Recomputed directly in test from -sum p log2 p within 1e-4 (and numerical precision)
        recomputed = _expected_entropy(probs)
        assert abs(val - recomputed) <= 1e-4, (
            f"entropy_bits({probs}) = {val}, recomputed {recomputed}"
        )

    # Zero probability contributes 0
    zero_cases = [
        [1.0, 0.0],
        [0.0, 1.0],
        [0.5, 0.5, 0.0],
        [0.0, 0.5, 0.0, 0.5],
        [0.25, 0.25, 0.25, 0.25, 0.0],
    ]
    for probs in zero_cases:
        val = entropy_bits(probs)
        non_zero = [p for p in probs if p > 0.0]
        expected = _expected_entropy(non_zero)
        assert abs(val - expected) <= 1e-4, (
            f"entropy_bits({probs}) with zero prob = {val}, expected {expected}"
        )

    # Single-action distribution [1.0] has entropy 0
    assert abs(entropy_bits([1.0]) - 0.0) <= 1e-12

    # Empty collection base case (Interpretation I2)
    assert abs(entropy_bits([]) - 0.0) <= 1e-12


def test_ac1_margin() -> None:
    """AC_1: Margin between two highest probabilities, including single-action distribution."""
    cases = [
        ([0.95, 0.05], 0.90),
        ([0.8, 0.2], 0.60),
        ([0.5, 0.5], 0.0),
        ([0.6, 0.3, 0.1], 0.30),
        ([0.45, 0.40, 0.15], 0.05),
    ]

    for probs, expected_margin in cases:
        val = margin(probs)
        assert abs(val - expected_margin) <= 1e-4, (
            f"margin({probs}) = {val}, expected {expected_margin} within 1e-4"
        )

    # Single-action distribution [1.0] has entropy 0 and margin 1.0
    assert abs(entropy_bits([1.0]) - 0.0) <= 1e-12
    assert abs(margin([1.0]) - 1.0) <= 1e-12

    # Empty collection base case (Interpretation I2)
    assert abs(margin([]) - 0.0) <= 1e-12


def test_ac2_pure() -> None:
    """AC_2: routing.py imports nothing from agent_learning.storage, no random and no numpy, and leaves input sequence untouched."""
    import agent_learning_ext.routing as routing_mod

    # 1. AST-level import check to verify forbidden modules are never imported
    source_file = Path(inspect.getfile(routing_mod)).resolve()
    tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))

    forbidden_modules = {"random", "numpy", "np"}
    forbidden_prefixes = ("agent_learning.storage", "agent_learning_ext.storage")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                assert name not in forbidden_modules, f"routing.py must not import '{name}'"
                for prefix in forbidden_prefixes:
                    assert not name.startswith(prefix), f"routing.py must not import '{name}'"
        elif isinstance(node, ast.ImportFrom):
            mod_name = node.module or ""
            assert mod_name not in forbidden_modules, f"routing.py must not import from '{mod_name}'"
            for prefix in forbidden_prefixes:
                assert not mod_name.startswith(prefix), f"routing.py must not import from '{mod_name}'"

    # 2. Input sequence remains completely untouched (equal to copy) after calls
    test_inputs = [
        [0.45, 0.40, 0.15],
        [0.1, 0.6, 0.3],  # Unsorted order to verify in-place sorting is NOT done
        [0.95, 0.05],
        [1.0],
        [],
    ]

    for original in test_inputs:
        copied = list(original)
        _ = entropy_bits(original)
        assert original == copied, f"entropy_bits modified input: {original} != {copied}"
        _ = margin(original)
        assert original == copied, f"margin modified input: {original} != {copied}"
