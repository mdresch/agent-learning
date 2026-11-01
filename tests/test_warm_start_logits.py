"""
Contract tests for Story 20.1: The Damped Copy.

Governing specifications:
- User Story: docs/user-stories/epic-20-explicit-policy-prior-warm-starting.md (Story 20.1)
- Architecture: docs/adr/ADR-020-explicit-policy-prior-warm-starting.md
- Business Requirements: docs/project-docs/Business-Requirements/BRD-020-explicit-policy-prior-warm-starting.md
- Functional Design: docs/project-docs/Functional-Design/FDD-020-explicit-policy-prior-warm-starting.md

Acceptance Criteria:
- AC_0 (Arithmetic): warm_start_logits on the base donor gives {accept: 1.4, decline: -0.7, ask: 0.0}
  within 1e-12 for the default damping 0.70, and {2.0, -1.0, 0.0} for damping 1.0,
  recomputed in the test as donor * damping.
- AC_1 (Entropy): the softmax entropy of the result is 0.5243 for damping 1.0, 0.7541 for 0.70
  and 0.9060 for 0.50 within 1e-4, and over a grid of damping values in (0, 1] it never decreases
  as damping falls.
- AC_2 (Damping Bounds): damping of 0, a negative value, 1.0001, 1.5, nan and inf each raise
  ValueError naming the argument; 1.0 and 0.0001 are accepted.
- AC_3 (Complete Map): an action_map whose keys differ from the target actions (one missing,
  or one extra) raises ValueError.
- AC_4 (One To One): two target actions mapped to the same donor action raise ValueError;
  a map to a donor action absent from the donor logits raises ValueError;
  donor actions that no target maps to are ignored.
- AC_5 (Donor Values): a non-finite donor logit raises ValueError.
- AC_6 (Pure): the donor logits and the map are equal to their copies after the call,
  and warm_start.py imports nothing from agent_learning.storage, no random and no numpy.
"""

from __future__ import annotations

import ast
import copy
import importlib.util
import inspect
import math
from pathlib import Path
import pytest

import agent_learning.warm_start
from agent_learning.warm_start import warm_start_logits


@pytest.fixture
def base_donor_logits() -> dict[str, float]:
    """Base donor logits from Story 20.1 specification."""
    return {"approve": 2.0, "reject": -1.0, "escalate": 0.0}


@pytest.fixture
def base_action_map() -> dict[str, str]:
    """Base action mapping from Story 20.1 specification."""
    return {"accept": "approve", "decline": "reject", "ask": "escalate"}


@pytest.fixture
def base_target_actions() -> list[str]:
    """Base target action identifiers from Story 20.1 specification."""
    return ["accept", "decline", "ask"]


def _softmax_entropy(logits: dict[str, float]) -> float:
    """Compute natural-log softmax entropy for a dictionary of logits."""
    max_val = max(logits.values())
    exps = [math.exp(v - max_val) for v in logits.values()]
    denom = sum(exps)
    probs = [e / denom for e in exps]
    return -sum(p * math.log(p) for p in probs if p > 0.0)


def test_ac0_arithmetic(
    base_donor_logits: dict[str, float],
    base_action_map: dict[str, str],
    base_target_actions: list[str],
) -> None:
    """AC_0: warm_start_logits produces exact damped values."""
    # Default damping (0.70)
    result_default = warm_start_logits(base_donor_logits, base_action_map, base_target_actions)
    expected_default = {"accept": 1.4, "decline": -0.7, "ask": 0.0}
    for action, expected_val in expected_default.items():
        assert math.isclose(result_default[action], expected_val, abs_tol=1e-12)

    # Damping 1.0
    result_undamped = warm_start_logits(
        base_donor_logits, base_action_map, base_target_actions, damping=1.0
    )
    expected_undamped = {"accept": 2.0, "decline": -1.0, "ask": 0.0}
    for action, expected_val in expected_undamped.items():
        assert math.isclose(result_undamped[action], expected_val, abs_tol=1e-12)


def test_ac1_entropy(
    base_donor_logits: dict[str, float],
    base_action_map: dict[str, str],
    base_target_actions: list[str],
) -> None:
    """AC_1: Softmax entropy values match specification and are monotonic over damping grid."""
    # Checkpoint values from FDD-020 and AC_1
    res_100 = warm_start_logits(base_donor_logits, base_action_map, base_target_actions, damping=1.0)
    assert math.isclose(_softmax_entropy(res_100), 0.5243, abs_tol=1e-4)

    res_070 = warm_start_logits(base_donor_logits, base_action_map, base_target_actions, damping=0.70)
    assert math.isclose(_softmax_entropy(res_070), 0.7541, abs_tol=1e-4)

    res_050 = warm_start_logits(base_donor_logits, base_action_map, base_target_actions, damping=0.50)
    assert math.isclose(_softmax_entropy(res_050), 0.9060, abs_tol=1e-4)

    # Monotonicity test: over grid in (0, 1], entropy never decreases as damping falls
    grid = [i / 100.0 for i in range(1, 101)]  # 0.01 to 1.00
    entropies = []
    for d in grid:
        res = warm_start_logits(base_donor_logits, base_action_map, base_target_actions, damping=d)
        entropies.append(_softmax_entropy(res))

    # As damping falls (moving backwards through grid from 1.0 down to 0.01), entropy must be non-decreasing
    for i in range(len(entropies) - 1, 0, -1):
        assert entropies[i - 1] >= entropies[i] - 1e-12, (
            f"Entropy decreased as damping fell: d={grid[i]} (H={entropies[i]}) -> "
            f"d={grid[i-1]} (H={entropies[i-1]})"
        )


def test_ac2_damping_bounds(
    base_donor_logits: dict[str, float],
    base_action_map: dict[str, str],
    base_target_actions: list[str],
) -> None:
    """AC_2: Damping out of (0, 1] or non-finite raises ValueError naming 'damping'."""
    invalid_dampings = [0.0, -0.5, -1e-6, 1.0001, 1.5, float("nan"), float("inf"), float("-inf")]
    for d in invalid_dampings:
        with pytest.raises(ValueError) as exc_info:
            warm_start_logits(base_donor_logits, base_action_map, base_target_actions, damping=d)
        assert "damping" in str(exc_info.value).lower(), f"ValueError for {d} did not name damping"

    # Reject bool instances (bool is a subclass of int in Python)
    for bad_bool in [True, False]:
        with pytest.raises(TypeError) as exc_info:
            warm_start_logits(base_donor_logits, base_action_map, base_target_actions, damping=bad_bool)
        assert "damping" in str(exc_info.value).lower(), f"TypeError for {bad_bool} did not name damping"

    # Valid boundary cases
    res_1 = warm_start_logits(base_donor_logits, base_action_map, base_target_actions, damping=1.0)
    assert len(res_1) == len(base_target_actions)

    res_small = warm_start_logits(base_donor_logits, base_action_map, base_target_actions, damping=0.0001)
    assert len(res_small) == len(base_target_actions)


def test_ac3_complete_map(
    base_donor_logits: dict[str, float],
    base_action_map: dict[str, str],
    base_target_actions: list[str],
) -> None:
    """AC_3: Action map keys differing from target actions (missing or extra) raises ValueError."""
    # Missing key
    missing_map = {"accept": "approve", "decline": "reject"}  # missing 'ask'
    with pytest.raises(ValueError) as exc_info:
        warm_start_logits(base_donor_logits, missing_map, base_target_actions)
    assert "map" in str(exc_info.value).lower() or "target" in str(exc_info.value).lower()

    # Extra key
    extra_map = {
        "accept": "approve",
        "decline": "reject",
        "ask": "escalate",
        "extra_target": "approve",
    }
    with pytest.raises(ValueError) as exc_info:
        warm_start_logits(base_donor_logits, extra_map, base_target_actions)
    assert "map" in str(exc_info.value).lower() or "target" in str(exc_info.value).lower()


def test_ac4_one_to_one(
    base_donor_logits: dict[str, float],
    base_target_actions: list[str],
) -> None:
    """AC_4: Injective map enforced, missing donor actions raise, unused donor actions ignored."""
    # Duplicate mapped donor action raises ValueError
    non_injective_map = {"accept": "approve", "decline": "approve", "ask": "escalate"}
    with pytest.raises(ValueError) as exc_info:
        warm_start_logits(base_donor_logits, non_injective_map, base_target_actions)
    assert "multiple" in str(exc_info.value).lower() or "same" in str(exc_info.value).lower()

    # Target mapped to non-existent donor action raises ValueError
    missing_donor_map = {"accept": "approve", "decline": "reject", "ask": "non_existent_action"}
    with pytest.raises(ValueError) as exc_info:
        warm_start_logits(base_donor_logits, missing_donor_map, base_target_actions)
    assert "non_existent_action" in str(exc_info.value)

    # Unmapped donor actions in donor_logits are ignored
    wider_donor_logits = {
        "approve": 2.0,
        "reject": -1.0,
        "escalate": 0.0,
        "unmapped_1": 9.9,
        "unmapped_2": -4.2,
    }
    normal_map = {"accept": "approve", "decline": "reject", "ask": "escalate"}
    res = warm_start_logits(wider_donor_logits, normal_map, base_target_actions)
    assert len(res) == len(base_target_actions)
    assert "unmapped_1" not in res
    assert "unmapped_2" not in res


def test_duplicate_target_actions(
    base_donor_logits: dict[str, float],
    base_action_map: dict[str, str],
) -> None:
    """Duplicate target action identifiers raise ValueError."""
    dup_targets = ["accept", "decline", "accept"]
    with pytest.raises(ValueError) as exc_info:
        warm_start_logits(base_donor_logits, base_action_map, dup_targets)
    assert "duplicate" in str(exc_info.value).lower()


def test_ac5_donor_values(
    base_donor_logits: dict[str, float],
    base_action_map: dict[str, str],
    base_target_actions: list[str],
) -> None:
    """AC_5: Non-finite donor logit raises ValueError; bool logit raises TypeError."""
    for bad_val in [float("nan"), float("inf"), float("-inf")]:
        donor_with_bad = {"approve": 2.0, "reject": bad_val, "escalate": 0.0}
        with pytest.raises(ValueError):
            warm_start_logits(donor_with_bad, base_action_map, base_target_actions)

    for bad_bool in [True, False]:
        donor_with_bad = {"approve": 2.0, "reject": bad_bool, "escalate": 0.0}
        with pytest.raises(TypeError):
            warm_start_logits(donor_with_bad, base_action_map, base_target_actions)


def test_ac6_pure(
    base_donor_logits: dict[str, float],
    base_action_map: dict[str, str],
    base_target_actions: list[str],
) -> None:
    """AC_6: Arguments are unmutated; warm_start.py has zero storage, random, or numpy imports."""
    donor_copy = copy.deepcopy(base_donor_logits)
    map_copy = copy.deepcopy(base_action_map)
    target_copy = copy.deepcopy(base_target_actions)

    warm_start_logits(base_donor_logits, base_action_map, base_target_actions)

    assert base_donor_logits == donor_copy
    assert base_action_map == map_copy
    assert base_target_actions == target_copy

    # Purity check on warm_start.py source code using AST
    source_path = Path(inspect.getfile(agent_learning.warm_start))
    if source_path.suffix == ".pyc":
        source_path = Path(importlib.util.source_from_cache(str(source_path)))
    source_path = source_path.resolve()
    assert source_path.is_file() and source_path.suffix == ".py", (
        f"warm_start.py source not found (resolved: {source_path})"
    )
    source_text = source_path.read_text(encoding="utf-8")

    tree = ast.parse(source_text)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)
                imported_modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_modules.add(node.module)
                imported_modules.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "__import__":
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    imported_modules.add(node.args[0].value)
                    imported_modules.add(node.args[0].value.split(".")[0])

    for mod in imported_modules:
        assert mod not in {"random", "numpy"}, f"warm_start.py violates purity: imports {mod}"
        assert not mod.startswith("agent_learning.storage"), f"warm_start.py violates purity: imports {mod}"
