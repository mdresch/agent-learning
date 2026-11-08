"""Contract test suite for Story 21.3: Pinned Gates (Epic 21).

Acceptance Criteria:
- AC_0 (The List): PINNED_FULL equals the eleven tasks of FDD-021 §2.1, and the test lists them.
- AC_1 (Always Full): for each pinned task, over a grid of distributions, tiers, previous values
  and approved_for_low values, route returns full with reason pinned.
- AC_2 (Declared Pin): a task not in the set, called with requires_human_approval true, routes
  full with reason pinned; the same task with false and an approved bucket can route low.
- AC_3 (Pin Beats Invalid Input): a pinned task with invalid probabilities routes full with
  reason pinned, not anomaly.
- AC_4 (Shape Files): docs/policy-shapes/approve-routing-thresholds.actions.json and
  approve-routing-bucket.actions.json each hold the three actions approve_*, reject_* and
  request_revision_before_decision, and both task ids are in PINNED_FULL.

Interpretations Recorded:
- I_1: Upstream Fork Purity (Invariant 6): Zero changes in src/agent_learning/. All logic isolated
       under src/agent_learning_ext/.
- I_2: Storage Decoupling & Serialization Round-Trip: Policy shapes and routing decisions survive
       JSON serialization without storage dependencies.
- I_3: Empty Collection Base Case: Safe handling on empty collections.
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path

import pytest

from agent_learning.decision import DecisionAuthority
from agent_learning_ext.routing import (
    PINNED_FULL,
    RoutingConfig,
    route,
)

ROOT = Path(__file__).resolve().parent.parent
POLICY_SHAPES_DIR = ROOT / "docs" / "policy-shapes"

EXPECTED_PINNED_TASKS = (
    "approve-charter",
    "approve-adr",
    "approve-brd",
    "approve-fdd",
    "approve-user-stories",
    "approve-pmp",
    "approve-adaptation-plan",
    "approve-subsidiary-plan",
    "retrospective",
    "approve-routing-thresholds",
    "approve-routing-bucket",
)


@pytest.fixture
def base_config() -> RoutingConfig:
    return RoutingConfig(tau_esc=1.0, tau_deesc=0.70, eps_margin=0.20)


def test_ac0_the_list() -> None:
    """AC_0: PINNED_FULL equals the eleven tasks of FDD-021 §2.1, and the test lists them."""
    assert len(PINNED_FULL) == 11, f"Expected 11 pinned tasks, found {len(PINNED_FULL)}"
    assert PINNED_FULL == EXPECTED_PINNED_TASKS, (
        f"PINNED_FULL mismatch.\nExpected: {EXPECTED_PINNED_TASKS}\nFound: {PINNED_FULL}"
    )
    assert set(PINNED_FULL) == set(EXPECTED_PINNED_TASKS)


def test_ac1_always_full(base_config: RoutingConfig) -> None:
    """AC_1: for each pinned task, over a grid of distributions, tiers, previous values and approved_for_low, route returns FULL with reason 'pinned'."""
    sample_probs = [
        [0.99, 0.01],  # very low entropy (~0.08 bits), high margin (0.98)
        [0.95, 0.05],  # low entropy (0.2864 bits), margin 0.90
        [0.80, 0.20],  # deadband entropy (0.7219 bits), margin 0.60
        [0.50, 0.50],  # high entropy (1.0 bit), margin 0.0
    ]
    tiers = ["low", "standard", "high", "critical"]
    previous_values = [
        None,
        DecisionAuthority.LOW,
        DecisionAuthority.FULL,
        "low",
        "full",
    ]
    approved_for_low_values = [True, False]
    requires_human_approval_values = [False, True]

    for task_id in PINNED_FULL:
        for probs, tier, prev, app_low, req_human in itertools.product(
            sample_probs,
            tiers,
            previous_values,
            approved_for_low_values,
            requires_human_approval_values,
        ):
            decision = route(
                probs=probs,
                tier=tier,
                task_id=task_id,
                previous=prev,
                approved_for_low=app_low,
                requires_human_approval=req_human,
                cfg=base_config,
            )
            assert decision.authority == DecisionAuthority.FULL, (
                f"Task {task_id} did not route FULL: {decision}"
            )
            assert decision.reason == "pinned", (
                f"Task {task_id} did not have reason 'pinned': {decision.reason}"
            )
            assert decision.anomaly is None


def test_ac2_declared_pin(base_config: RoutingConfig) -> None:
    """AC_2: a task not in the set, called with requires_human_approval true, routes full with reason 'pinned'; false with approved bucket routes low."""
    # 1. Unpinned task with requires_human_approval=True routes FULL with reason 'pinned'
    decision_pinned = route(
        probs=[0.99, 0.01],
        tier="low",
        task_id="routine-unpinned-task",
        previous=DecisionAuthority.LOW,
        approved_for_low=True,
        requires_human_approval=True,
        cfg=base_config,
    )
    assert decision_pinned.authority == DecisionAuthority.FULL
    assert decision_pinned.reason == "pinned"

    # 2. Same unpinned task with requires_human_approval=False and approved_for_low=True routes LOW with reason 'low'
    decision_unpinned = route(
        probs=[0.99, 0.01],
        tier="low",
        task_id="routine-unpinned-task",
        previous=DecisionAuthority.LOW,
        approved_for_low=True,
        requires_human_approval=False,
        cfg=base_config,
    )
    assert decision_unpinned.authority == DecisionAuthority.LOW
    assert decision_unpinned.reason == "low"


def test_ac3_pin_beats_invalid_input(base_config: RoutingConfig) -> None:
    """AC_3: a pinned task with invalid probabilities routes full with reason 'pinned', not 'anomaly'."""
    invalid_probability_cases = [
        [],
        [float("nan"), 0.5],
        [float("inf"), 0.0],
        [-0.1, 1.1],
        [0.45, 0.45],  # Sums to 0.9
        [0.60, 0.50],  # Sums to 1.1
        [True, False],  # Booleans rejected
    ]

    for probs in invalid_probability_cases:
        for task_id in ["approve-charter", "approve-routing-thresholds", "approve-routing-bucket"]:
            decision = route(
                probs=probs,
                tier="standard",
                task_id=task_id,
                previous=DecisionAuthority.LOW,
                approved_for_low=True,
                requires_human_approval=False,
                cfg=base_config,
            )
            assert decision.authority == DecisionAuthority.FULL
            assert decision.reason == "pinned", (
                f"Expected reason 'pinned' for pinned task with invalid probs, got {decision.reason}"
            )
            assert decision.entropy_bits is None
            assert decision.margin is None
            assert decision.anomaly is None


def test_ac4_shape_files() -> None:
    """AC_4: approve-routing-thresholds and approve-routing-bucket each hold the three actions approve_*, reject_* and request_revision_before_decision, and both task ids are in PINNED_FULL."""
    # Both tasks must be in PINNED_FULL
    assert "approve-routing-thresholds" in PINNED_FULL
    assert "approve-routing-bucket" in PINNED_FULL

    expected_shapes = [
        ("approve-routing-thresholds", POLICY_SHAPES_DIR / "approve-routing-thresholds.actions.json"),
        ("approve-routing-bucket", POLICY_SHAPES_DIR / "approve-routing-bucket.actions.json"),
    ]

    for task_id, path in expected_shapes:
        assert path.is_file(), f"Policy shape file missing: {path}"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(data, list), f"Expected list of actions in {path}, got {type(data)}"
        assert len(data) == 3, f"Expected exactly 3 actions in {path}, got {len(data)}"

        for idx, item in enumerate(data):
            assert isinstance(item, dict), f"Item {idx} in {path} must be a dict"
            assert "id" in item and isinstance(item["id"], str) and item["id"].strip(), (
                f"Missing or invalid 'id' in item {idx} of {path}"
            )
            assert "description" in item and isinstance(item["description"], str) and item["description"].strip(), (
                f"Missing or invalid 'description' in item {idx} of {path}"
            )
            assert "parameters" in item and isinstance(item["parameters"], dict), (
                f"Missing or invalid 'parameters' in item {idx} of {path}"
            )

        action_ids: list[str] = [item["id"] for item in data]
        expected_task_prefix = "approve-"
        assert task_id.startswith(expected_task_prefix), (
            f"Task ID must start with '{expected_task_prefix}': {task_id}"
        )
        suffix = task_id[len(expected_task_prefix):].replace("-", "_")
        expected_approve = f"approve_{suffix}"
        expected_reject = f"reject_{suffix}"

        assert expected_approve in action_ids, f"Expected {expected_approve} in {action_ids}"
        assert expected_reject in action_ids, f"Expected {expected_reject} in {action_ids}"
        assert "request_revision_before_decision" in action_ids

        # JSON round-trip serialization check (I_2)
        serialized = json.dumps(data, indent=2)
        deserialized = json.loads(serialized)
        assert deserialized == data


def test_governance_baseline_passes() -> None:
    """Baseline Check: running governance baseline check confirms adding tasks and shapes leaves baseline valid."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "governance_baseline", ROOT / "scripts" / "governance_baseline.py"
    )
    assert spec is not None and spec.loader is not None
    assert hasattr(spec.loader, "exec_module"), "Loader must implement exec_module"
    gb = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(gb)
    except Exception as exc:
        pytest.fail(f"Failed to execute governance_baseline module: {exc}")

    manifest = json.loads(gb.MANIFEST.read_text(encoding="utf-8"))
    problems = gb.find_problems(manifest, ROOT)
    assert not problems, "Governance baseline problems detected:\n" + "\n".join(problems)
