"""Contract test suite for Story 22.1 — Scoring a Weight Vector With the Real Resolver.

Source ADR: ADR-022 (Scored-Search Decision Configuration Compilation)
Source BRD: BRD-022 (BRU-022-01, BRU-022-02, BRU-022-03, BRU-022-04, BRU-022-10)
Source FDD: FDD-022 (§1 item 1, §2.1, §2.2, §3.1, §3.2, §3.3, §4 L1, L2, L7)
Story: Story 22.1 (Scoring a Weight Vector With the Real Resolver)

Acceptance Criteria:
- AC_0 (Weights Applied): with_weights on the toy frame with (0.7, 0.3) returns a frame whose
  criteria weights are 0.7 and 0.3 in the original order; its constraints, options and evidence
  are equal to the original's; the original frame is equal to its copy afterwards.
- AC_1 (Validation): with_weights raises ValueError for a key set that differs from the criterion
  ids, a zero, negative, nan or infinite weight.
- AC_2 (Predicted And Margin): evaluate on the toy frame gives predicted A and margin 0.20
  within 1e-9 for (0.7, 0.3); None and margin 0.0 for (0.5, 0.5) (a tie that needs a person);
  B and margin 0.20 for (0.3, 0.7).
- AC_3 (Objective): with label A and beta 0.1 the objective of the toy frame is 1.02 for (0.7, 0.3),
  0.0 for (0.5, 0.5) and 0.02 for (0.3, 0.7) within 1e-9; the objective of a set is the sum
  over its items.
- AC_4 (Constraints Hold): for a frame where option B is ruled out by a constraint, evaluate
  never returns B over a grid of weight vectors, and the margin ignores the ruled-out option.
- AC_5 (Through The Resolver): the test replaces DecisionResolver.resolve with a counting wrapper
  and finds one call per evaluate, as resolve(snapshot, with_weights(...)), where snapshot is
  the one passed to evaluate; the module has no other scoring path.
- AC_6 (Pure): src/agent_learning_ext/weight_compiler.py imports nothing from agent_learning.storage
  and performs no file I/O.

Recommended Contract Interpretations:
- [I1] Upstream Fork Purity (Invariant 6):
  All custom classes and helpers reside in 'src/agent_learning_ext/weight_compiler.py',
  leaving 'src/agent_learning/' pristine.
- [I2] Defensive None-Safety for Dictionaries:
  Defensively guard against None metadata or dictionaries.
- [I3] Empty Collection Base Case:
  When passed an empty collection, objective returns 0.0 without raising.
"""

from __future__ import annotations

import ast
import copy
import math
from pathlib import Path
from typing import Any

import pytest

from agent_learning.decision import (
    Action,
    DecisionAuthority,
    DecisionCriterion,
    DecisionFrame,
    DecisionOption,
    DecisionResolver,
    DecisionResult,
    DecisionStatus,
    EvidencePoint,
)
from agent_learning.types import PolicySnapshot
from agent_learning_ext.weight_compiler import (
    BETA_DEFAULT,
    HOLDOUT_FRACTION_DEFAULT,
    MAX_SWEEPS_DEFAULT,
    MIN_PART,
    RESTARTS_DEFAULT,
    STEP_DEFAULT,
    CompiledWeights,
    LabeledFrame,
    NoImprovement,
    evaluate,
    objective,
    with_weights,
)


@pytest.fixture
def toy_actions() -> tuple[Action, Action]:
    return Action(id="A"), Action(id="B")


@pytest.fixture
def toy_snapshot(toy_actions: tuple[Action, Action]) -> PolicySnapshot:
    return PolicySnapshot(
        id="policy-toy",
        agent_id="agent-toy",
        task_id="toy-task",
        version=1,
        actions=list(toy_actions),
        logits={"A": 0.0, "B": 0.0},
        metadata={"decision_authority": DecisionAuthority.FULL.value},
    )


@pytest.fixture
def toy_frame(toy_actions: tuple[Action, Action]) -> DecisionFrame:
    """The canonical toy frame defined in Epic 22 & FDD-022 §3 Worked Checks.

    Criteria: c1, c2
    Options:
      A: supports 0.9 on c1, 0.3 on c2
      B: supports 0.4 on c1, 0.8 on c2
    One source per criterion at confidence 1.0, uncertainty_penalty=0.0, minimum_margin=0.05.
    """
    act_a, act_b = toy_actions
    c1 = DecisionCriterion(id="c1", weight=1.0, minimum_sources=1)
    c2 = DecisionCriterion(id="c2", weight=1.0, minimum_sources=1)

    opt_a = DecisionOption(
        action=act_a,
        evidence=(
            EvidencePoint(criterion_id="c1", source="s1", support=0.9, confidence=1.0),
            EvidencePoint(criterion_id="c2", source="s2", support=0.3, confidence=1.0),
        ),
    )
    opt_b = DecisionOption(
        action=act_b,
        evidence=(
            EvidencePoint(criterion_id="c1", source="s1", support=0.4, confidence=1.0),
            EvidencePoint(criterion_id="c2", source="s2", support=0.8, confidence=1.0),
        ),
    )

    return DecisionFrame(
        task="toy-task",
        criteria=(c1, c2),
        options=(opt_a, opt_b),
        constraints=(),
        minimum_margin=0.05,
        uncertainty_penalty=0.0,
        max_uncertainty=1.0,
    )


# --- AC_0: Weights Applied ---


def test_ac0_with_weights_applied(toy_frame: DecisionFrame) -> None:
    """AC_0: with_weights on the toy frame with (0.7, 0.3) returns a frame whose criteria

    weights are 0.7 and 0.3 in the original order; its constraints, options and evidence
    are equal to the original's; the original frame is equal to its copy afterwards.
    """
    frame_copy = copy.deepcopy(toy_frame)

    # 1. Apply tuple of weights (0.7, 0.3)
    new_frame = with_weights(toy_frame, (0.7, 0.3))

    assert [c.weight for c in new_frame.criteria] == [0.7, 0.3]
    assert [c.id for c in new_frame.criteria] == ["c1", "c2"]
    assert new_frame.constraints == toy_frame.constraints
    assert new_frame.options == toy_frame.options
    assert toy_frame == frame_copy

    # 2. Also apply dict mapping {"c1": 0.7, "c2": 0.3}
    dict_frame = with_weights(toy_frame, {"c1": 0.7, "c2": 0.3})
    assert [c.weight for c in dict_frame.criteria] == [0.7, 0.3]
    assert [c.id for c in dict_frame.criteria] == ["c1", "c2"]
    assert dict_frame.constraints == toy_frame.constraints
    assert dict_frame.options == toy_frame.options
    assert toy_frame == frame_copy


# --- AC_1: Validation ---


def test_ac1_validation_differing_key_set(toy_frame: DecisionFrame) -> None:
    """AC_1: with_weights raises ValueError for a key set that differs from the criterion ids."""
    # Extra key
    with pytest.raises(ValueError, match="differ"):
        with_weights(toy_frame, {"c1": 0.7, "c2": 0.3, "extra": 0.1})

    # Missing key
    with pytest.raises(ValueError, match="differ"):
        with_weights(toy_frame, {"c1": 0.7})

    # Disjoint keys
    with pytest.raises(ValueError, match="differ"):
        with_weights(toy_frame, {"other1": 0.5, "other2": 0.5})

    # Wrong sequence length
    with pytest.raises(ValueError, match="differ|length"):
        with_weights(toy_frame, (0.7,))
    with pytest.raises(ValueError, match="differ|length"):
        with_weights(toy_frame, (0.7, 0.2, 0.1))


@pytest.mark.parametrize(
    "bad_weight",
    [0.0, -0.05, -1.0, float("nan"), float("inf"), float("-inf")],
)
def test_ac1_validation_non_positive_or_non_finite_weight(
    toy_frame: DecisionFrame, bad_weight: float
) -> None:
    """AC_1: with_weights raises ValueError for zero, negative, nan, or infinite weight."""
    with pytest.raises(ValueError, match="weight"):
        with_weights(toy_frame, (bad_weight, 0.5))

    with pytest.raises(ValueError, match="weight"):
        with_weights(toy_frame, {"c1": 0.5, "c2": bad_weight})


# --- AC_2: Predicted And Margin ---


def test_ac2_predicted_and_margin(toy_frame: DecisionFrame, toy_snapshot: PolicySnapshot) -> None:
    """AC_2: evaluate on the toy frame gives predicted A and margin 0.20 within 1e-9 for (0.7, 0.3);

    None and margin 0.0 for (0.5, 0.5) (a tie that needs a person); B and margin 0.20 for (0.3, 0.7).
    """
    # 1. Weights (0.7, 0.3) -> A leads by 0.20
    pred_1, margin_1 = evaluate(toy_frame, (0.7, 0.3), toy_snapshot)
    assert pred_1 == "A"
    assert pytest.approx(margin_1, abs=1e-9) == 0.20

    # 2. Weights (0.5, 0.5) -> Tie, needs person -> predicted is None, margin is 0.0
    pred_2, margin_2 = evaluate(toy_frame, (0.5, 0.5), toy_snapshot)
    assert pred_2 is None
    assert pytest.approx(margin_2, abs=1e-9) == 0.0

    # 3. Weights (0.3, 0.7) -> B leads by 0.20
    pred_3, margin_3 = evaluate(toy_frame, (0.3, 0.7), toy_snapshot)
    assert pred_3 == "B"
    assert pytest.approx(margin_3, abs=1e-9) == 0.20

    # 4. Also evaluate with LabeledFrame wrapping the DecisionFrame
    labeled_item = LabeledFrame(frame=toy_frame, label="A", labeled_at="2026-10-26T12:00:00Z")
    pred_wrapped, margin_wrapped = evaluate(labeled_item, (0.7, 0.3), toy_snapshot)
    assert pred_wrapped == "A"
    assert pytest.approx(margin_wrapped, abs=1e-9) == 0.20


def test_ac2_evaluate_needs_user_feedback(
    toy_frame: DecisionFrame, toy_actions: tuple[Action, Action]
) -> None:
    """AC_2 / FDD L7: When snapshot requires human approval, status is needs_user_feedback

    and predicted is proposed_action.
    """
    snapshot_approval = PolicySnapshot(
        id="policy-approval",
        agent_id="agent-toy",
        task_id="toy-task",
        version=1,
        actions=list(toy_actions),
        logits={"A": 0.0, "B": 0.0},
        metadata={"complexity_profile": {"requires_human_approval": True}},
    )
    pred, margin = evaluate(toy_frame, (0.7, 0.3), snapshot_approval)
    assert pred == "A"
    assert pytest.approx(margin, abs=1e-9) == 0.20


# --- AC_3: Objective ---


def test_ac3_objective(toy_frame: DecisionFrame, toy_snapshot: PolicySnapshot) -> None:
    """AC_3: with label A and beta 0.1 the objective of the toy frame is 1.02 for (0.7, 0.3),

    0.0 for (0.5, 0.5) and 0.02 for (0.3, 0.7) within 1e-9; the objective of a set is the sum
    over its items.
    """
    labeled_item = LabeledFrame(frame=toy_frame, label="A", labeled_at="2026-10-26T12:00:00Z")

    # (0.7, 0.3): predicted=A, label=A -> 1 + 0.1 * 0.20 = 1.02
    obj_1 = objective((0.7, 0.3), [labeled_item], toy_snapshot, beta=0.1)
    assert pytest.approx(obj_1, abs=1e-9) == 1.02

    # (0.5, 0.5): predicted=None, label=A -> 0 + 0.1 * 0.0 = 0.0
    obj_2 = objective((0.5, 0.5), [labeled_item], toy_snapshot, beta=0.1)
    assert pytest.approx(obj_2, abs=1e-9) == 0.0

    # (0.3, 0.7): predicted=B, label=A -> 0 + 0.1 * 0.20 = 0.02
    obj_3 = objective((0.3, 0.7), [labeled_item], toy_snapshot, beta=0.1)
    assert pytest.approx(obj_3, abs=1e-9) == 0.02

    # Single frame directly with optional label kwarg or single item
    obj_single = objective((0.7, 0.3), labeled_item, toy_snapshot, beta=0.1)
    assert pytest.approx(obj_single, abs=1e-9) == 1.02

    obj_frame_direct = objective((0.7, 0.3), toy_frame, toy_snapshot, beta=0.1, label="A")
    assert pytest.approx(obj_frame_direct, abs=1e-9) == 1.02

    # Sum over a set of items: 2 copies of (0.7, 0.3) item -> 1.02 + 1.02 = 2.04
    obj_set = objective((0.7, 0.3), [labeled_item, labeled_item], toy_snapshot, beta=0.1)
    assert pytest.approx(obj_set, abs=1e-9) == 2.04


def test_ac3_empty_collection_base_case(toy_snapshot: PolicySnapshot) -> None:
    """[I3] Empty Collection Base Case: empty collection returns 0.0 without raising."""
    obj_empty = objective((0.7, 0.3), [], toy_snapshot, beta=0.1)
    assert obj_empty == 0.0


# --- AC_4: Constraints Hold ---


def test_ac4_constraints_hold(toy_snapshot: PolicySnapshot) -> None:
    """AC_4: for a frame where option B is ruled out by a constraint, evaluate never returns B

    over a grid of weight vectors, and the margin ignores the ruled-out option.
    """
    act_a = Action(id="A")
    act_b = Action(id="B")
    c1 = DecisionCriterion(id="c1", weight=1.0, minimum_sources=1)
    c2 = DecisionCriterion(id="c2", weight=1.0, minimum_sources=1)

    # Option B violates constraint "hard_gate"
    opt_a = DecisionOption(
        action=act_a,
        evidence=(
            EvidencePoint(criterion_id="c1", source="s1", support=0.2, confidence=1.0),
            EvidencePoint(criterion_id="c2", source="s2", support=0.2, confidence=1.0),
        ),
        constraint_results={"hard_gate": True},
    )
    opt_b = DecisionOption(
        action=act_b,
        evidence=(
            EvidencePoint(criterion_id="c1", source="s1", support=0.99, confidence=1.0),
            EvidencePoint(criterion_id="c2", source="s2", support=0.99, confidence=1.0),
        ),
        constraint_results={"hard_gate": False},
    )

    constrained_frame = DecisionFrame(
        task="toy-task",
        criteria=(c1, c2),
        options=(opt_a, opt_b),
        constraints=("hard_gate",),
        minimum_margin=0.05,
        uncertainty_penalty=0.0,
    )

    # Test over a grid of weight vectors from 0.05 to 0.95
    grid = [
        (0.05, 0.95),
        (0.2, 0.8),
        (0.5, 0.5),
        (0.8, 0.2),
        (0.95, 0.05),
    ]
    for w in grid:
        pred, margin = evaluate(constrained_frame, w, toy_snapshot)
        # B is NEVER returned, even when it has 0.99 support across all criteria
        assert pred != "B"
        # B was the only other option; with only A feasible (<2 feasible options), margin is 0.0
        assert margin == 0.0

    # Now add option C so there are 2 viable options (A and C) while B is ruled out by constraint.
    # Note: Neither A nor C should Pareto-dominate the other (A better on c1, C better on c2).
    act_c = Action(id="C")
    snap_3 = PolicySnapshot(
        id="policy-3",
        agent_id="agent-toy",
        task_id="toy-task",
        version=1,
        actions=[act_a, act_b, act_c],
        logits={"A": 0.0, "B": 0.0, "C": 0.0},
    )
    opt_a_non_dom = DecisionOption(
        action=act_a,
        evidence=(
            EvidencePoint(criterion_id="c1", source="s1", support=0.8, confidence=1.0),
            EvidencePoint(criterion_id="c2", source="s2", support=0.3, confidence=1.0),
        ),
        constraint_results={"hard_gate": True},
    )
    opt_c = DecisionOption(
        action=act_c,
        evidence=(
            EvidencePoint(criterion_id="c1", source="s1", support=0.2, confidence=1.0),
            EvidencePoint(criterion_id="c2", source="s2", support=0.6, confidence=1.0),
        ),
        constraint_results={"hard_gate": True},
    )
    frame_3 = DecisionFrame(
        task="toy-task",
        criteria=(c1, c2),
        options=(opt_a_non_dom, opt_b, opt_c),
        constraints=("hard_gate",),
        minimum_margin=0.05,
        uncertainty_penalty=0.0,
    )
    # At weights (0.5, 0.5):
    # A has utility 0.5*0.8 + 0.5*0.3 = 0.55
    # C has utility 0.5*0.2 + 0.5*0.6 = 0.40
    # B has 0.99 (ruled out by hard_gate).
    # Margin should be U(A) - U(C) = 0.55 - 0.40 = 0.15, ignoring B!
    pred_3, margin_3 = evaluate(frame_3, (0.5, 0.5), snap_3)
    assert pred_3 == "A"
    assert pytest.approx(margin_3, abs=1e-9) == 0.15


# --- AC_5: Through The Resolver ---


def test_ac5_through_the_resolver(
    monkeypatch: pytest.MonkeyPatch, toy_frame: DecisionFrame, toy_snapshot: PolicySnapshot
) -> None:
    """AC_5: the test replaces DecisionResolver.resolve with a counting wrapper and finds one

    call per evaluate, as resolve(snapshot, with_weights(...)), where snapshot is the one passed
    to evaluate; the module has no other scoring path.
    """
    calls: list[tuple[PolicySnapshot, DecisionFrame]] = []
    original_resolve = DecisionResolver.resolve

    def counting_resolve(self: DecisionResolver, snap: PolicySnapshot, frm: DecisionFrame) -> DecisionResult:
        calls.append((snap, frm))
        return original_resolve(self, snap, frm)

    monkeypatch.setattr(DecisionResolver, "resolve", counting_resolve)

    weights = (0.7, 0.3)
    pred, margin = evaluate(toy_frame, weights, toy_snapshot)

    assert len(calls) == 1
    passed_snapshot, passed_frame = calls[0]
    assert passed_snapshot is toy_snapshot
    assert [c.weight for c in passed_frame.criteria] == [0.7, 0.3]
    assert pred == "A"
    assert pytest.approx(margin, abs=1e-9) == 0.20

    # Ensure objective also scores solely through evaluate / resolve
    calls.clear()
    labeled = LabeledFrame(frame=toy_frame, label="A", labeled_at="2026-10-26T12:00:00Z")
    obj = objective(weights, [labeled], toy_snapshot, beta=0.1)
    assert len(calls) == 1
    assert pytest.approx(obj, abs=1e-9) == 1.02


# --- AC_6: Pure Module Boundary ---


def test_ac6_pure_module_boundary() -> None:
    """AC_6: src/agent_learning_ext/weight_compiler.py imports nothing from agent_learning.storage

    and performs no file I/O.
    """
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "agent_learning_ext"
        / "weight_compiler.py"
    )
    assert module_path.is_file(), f"Expected {module_path} to exist"

    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(module_path))

    for node in ast.walk(tree):
        # 1. No imports from storage
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("agent_learning.storage"), (
                    f"Forbidden import: {alias.name}"
                )
                assert not alias.name.startswith("agent_learning_ext.storage"), (
                    f"Forbidden import: {alias.name}"
                )
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            assert not mod.startswith("agent_learning.storage"), (
                f"Forbidden import from {mod}"
            )
            assert not mod.startswith("agent_learning_ext.storage"), (
                f"Forbidden import from {mod}"
            )

        # 2. No open() calls or file I/O
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "open":
                pytest.fail("Forbidden file I/O: open() called in weight_compiler.py")
            elif isinstance(node.func, ast.Attribute) and node.func.attr in {
                "read_text",
                "read_bytes",
                "write_text",
                "write_bytes",
            }:
                pytest.fail(
                    f"Forbidden file I/O: {node.func.attr}() called in weight_compiler.py"
                )


# --- Dataclasses & Constants Verification ---


def test_constants_and_dataclasses() -> None:
    """Verify constants and dataclasses required by FDD-022 §2.1 and §2.2."""
    assert STEP_DEFAULT == 0.05
    assert BETA_DEFAULT == 0.1
    assert HOLDOUT_FRACTION_DEFAULT == 0.3
    assert MIN_PART == 5
    assert RESTARTS_DEFAULT == 5
    assert MAX_SWEEPS_DEFAULT == 20

    # CompiledWeights frozen & mapping proxy
    raw_weights = {"c1": 0.6, "c2": 0.4}
    cw = CompiledWeights(
        weights=raw_weights,
        train_accuracy=1.0,
        holdout_accuracy=0.9,
        baseline_holdout_accuracy=0.8,
        holdout_margin=0.25,
        seed=42,
        evaluations=10,
        sweeps=3,
        restarts=1,
        proposed_at="2026-10-26T12:00:00Z",
    )
    # Mutating original dict does not mutate stored weights
    raw_weights["c1"] = 0.99
    assert cw.weights["c1"] == 0.6

    # Stored weights cannot be mutated
    with pytest.raises(TypeError):
        cw.weights["c1"] = 0.5  # type: ignore[index]

    # NoImprovement dataclass
    ni = NoImprovement(
        reason="No holdout improvement",
        baseline_holdout_accuracy=1.0,
        best_holdout_accuracy=1.0,
    )
    assert ni.baseline_holdout_accuracy == 1.0
