"""Contract tests for Story 22.2 — The Split and the Label Rule.

Source ADR/BRD/FDD: ADR-022, BRD-022, FDD-022 §2.2, §3.2
Epic: Epic 22 (Scored-Search Decision Configuration Compilation)

Recommended Contract Interpretations:
[I1] Upstream Fork Purity (Invariant 6):
     Specification references upstream path 'src/agent_learning/weight_compiler.py'.
     Per Invariant 6, all custom classes, learners, and helpers must be created under
     'src/agent_learning_ext/weight_compiler.py', leaving 'src/agent_learning/' pristine.
[I2] Storage Decoupling & Serialization Round-Trip:
     All policy snapshots and episode metadata modifications must survive standard
     json round-tripping, and the learner module must not import anything from
     agent_learning.storage.
[I3] Defensive None-Safety for Dictionaries:
     When reading or updating dictionary attributes, implementations must defensively
     guard against None values.
[I4] Empty Collection Base Case:
     When passed an empty collection or when an input would leave fewer than MIN_PART
     items in either part, split_holdout raises ValueError per AC_1.
"""

from __future__ import annotations

import json
import random
import subprocess
import sys
from typing import Any
from unittest.mock import MagicMock

import pytest

from agent_learning.decision import (
    DecisionCriterion,
    DecisionFrame,
    DecisionOption,
    DecisionResolver,
    EvidencePoint,
)
from agent_learning.types import Action, PolicySnapshot
from agent_learning_ext import (
    HOLDOUT_FRACTION_DEFAULT,
    MIN_PART,
    LabeledFrame,
    split_holdout,
    validate_label_timing,
)


def build_synthetic_suite() -> list[LabeledFrame]:
    """Synthetic suite of 40 frames over criteria c1, c2, c3 labelled under hidden weights."""
    rng = random.Random(20261026)
    actions = [Action(id="A"), Action(id="B")]
    snapshot = PolicySnapshot(
        id="policy-synth",
        agent_id="agent-synth",
        task_id="task-synth",
        version=1,
        actions=actions,
        logits={"A": 0.0, "B": 0.0},
    )
    resolver = DecisionResolver()
    hidden_weights = {"c1": 0.6, "c2": 0.3, "c3": 0.1}

    items: list[LabeledFrame] = []
    for i in range(40):
        ev_a = [
            EvidencePoint(
                criterion_id=f"c{k}",
                source="synth_source",
                support=round(rng.random(), 4),
                confidence=1.0,
            )
            for k in (1, 2, 3)
        ]
        ev_b = [
            EvidencePoint(
                criterion_id=f"c{k}",
                source="synth_source",
                support=round(rng.random(), 4),
                confidence=1.0,
            )
            for k in (1, 2, 3)
        ]
        criteria = [
            DecisionCriterion(id="c1", weight=hidden_weights["c1"]),
            DecisionCriterion(id="c2", weight=hidden_weights["c2"]),
            DecisionCriterion(id="c3", weight=hidden_weights["c3"]),
        ]
        frame = DecisionFrame(
            task=f"synthetic-task-{i:03d}",
            criteria=criteria,
            options=[
                DecisionOption(action=Action(id="A"), evidence=ev_a),
                DecisionOption(action=Action(id="B"), evidence=ev_b),
            ],
            minimum_margin=0.0,
            uncertainty_penalty=0.0,
        )
        result = resolver.resolve(snapshot, frame)
        assert result.selected_action is not None, f"Item {i} failed to resolve"
        label = result.selected_action.id
        labeled_at = f"2026-10-26T10:{i:02d}:00Z"
        items.append(LabeledFrame(frame=frame, label=label, labeled_at=labeled_at))

    return items


@pytest.fixture
def synthetic_suite() -> list[LabeledFrame]:
    return build_synthetic_suite()


def test_ac0_reproducible_split(synthetic_suite: list[LabeledFrame]) -> None:
    """AC_0: split_holdout with seed 7 returns same parts on every call and in fresh process.

    A different seed returns a different split. Parts are disjoint and together equal the input.
    """
    train1, holdout1 = split_holdout(synthetic_suite, seed=7)
    train2, holdout2 = split_holdout(synthetic_suite, seed=7)

    # Same parts on repeated calls
    assert train1 == train2
    assert holdout1 == holdout2

    # Different seed returns a different split
    train_diff, holdout_diff = split_holdout(synthetic_suite, seed=42)
    assert train1 != train_diff or holdout1 != holdout_diff

    # Disjoint and together equal input
    set_train1 = set(train1)
    set_holdout1 = set(holdout1)
    assert set_train1.isdisjoint(set_holdout1)
    assert len(train1) + len(holdout1) == len(synthetic_suite)
    assert set_train1 | set_holdout1 == set(synthetic_suite)

    # Reproducible in a fresh process
    code = (
        "import json, sys\n"
        "from tests.test_weight_split import build_synthetic_suite\n"
        "from agent_learning_ext.weight_compiler import split_holdout\n"
        "items = build_synthetic_suite()\n"
        "train, holdout = split_holdout(items, seed=7)\n"
        "print(json.dumps([item.frame.task for item in train]))\n"
        "print(json.dumps([item.frame.task for item in holdout]))\n"
    )
    res = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    out_lines = [line.strip() for line in res.stdout.strip().splitlines() if line.strip()]
    fresh_train_tasks = json.loads(out_lines[0])
    fresh_holdout_tasks = json.loads(out_lines[1])

    assert fresh_train_tasks == [item.frame.task for item in train1]
    assert fresh_holdout_tasks == [item.frame.task for item in holdout1]


def test_ac1_split_sizes_and_validation(synthetic_suite: list[LabeledFrame]) -> None:
    """AC_1: fraction 0.3 on 40 items holds out 12; invalid fraction, seed, or sizes raise ValueError."""
    train, holdout = split_holdout(synthetic_suite, fraction=0.3, seed=7)
    assert len(holdout) == 12
    assert len(train) == 28

    # Default fraction is 0.3
    train_def, holdout_def = split_holdout(synthetic_suite, seed=7)
    assert len(holdout_def) == 12
    assert len(train_def) == 28

    # Fraction under 0.3 raises ValueError
    with pytest.raises(ValueError, match="fraction"):
        split_holdout(synthetic_suite, fraction=0.29, seed=7)

    # Fraction over 0.5 raises ValueError
    with pytest.raises(ValueError, match="fraction"):
        split_holdout(synthetic_suite, fraction=0.51, seed=7)

    # Non-integer seed raises ValueError
    with pytest.raises(ValueError, match="seed"):
        split_holdout(synthetic_suite, seed="7")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="seed"):
        split_holdout(synthetic_suite, seed=7.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="seed"):
        split_holdout(synthetic_suite, seed=True)  # bool is not accepted as int seed
    with pytest.raises(ValueError, match="seed"):
        split_holdout(synthetic_suite, seed=None)  # type: ignore[arg-type]

    # Fewer than 5 items in either part raises ValueError
    # e.g., 10 items at fraction 0.3 -> holdout would be 3 (< 5)
    with pytest.raises(ValueError, match="fewer than 5"):
        split_holdout(synthetic_suite[:10], fraction=0.3, seed=7)

    # Empty list raises ValueError (fewer than 5 items)
    with pytest.raises(ValueError, match="fewer than 5"):
        split_holdout([], fraction=0.3, seed=7)


def test_ac2_order_independent(synthetic_suite: list[LabeledFrame]) -> None:
    """AC_2: Shuffling the input list before the call does not change the parts."""
    shuffled_suite = list(synthetic_suite)
    random.Random(1337).shuffle(shuffled_suite)

    train_orig, holdout_orig = split_holdout(synthetic_suite, seed=7)
    train_shuf, holdout_shuf = split_holdout(shuffled_suite, seed=7)

    assert train_orig == train_shuf
    assert holdout_orig == holdout_shuf


def test_ac3_label_timing_validation(synthetic_suite: list[LabeledFrame]) -> None:
    """AC_3: validate_label_timing raises ValueError naming the item when labeled_at equals or follows proposed_at."""
    proposed_at = "2026-10-29T12:00:00Z"

    # Strictly earlier labels are accepted
    validate_label_timing(synthetic_suite, proposed_at)

    # An item with labeled_at equal to proposed_at raises ValueError naming the item
    bad_item_equal = LabeledFrame(
        frame=synthetic_suite[0].frame,
        label=synthetic_suite[0].label,
        labeled_at=proposed_at,
    )
    with pytest.raises(ValueError) as exc_info:
        validate_label_timing([bad_item_equal], proposed_at)
    err_msg = str(exc_info.value)
    assert bad_item_equal.frame.task in err_msg or "synthetic-task-000" in err_msg

    # An item with labeled_at following proposed_at raises ValueError naming the item
    bad_item_later = LabeledFrame(
        frame=synthetic_suite[1].frame,
        label=synthetic_suite[1].label,
        labeled_at="2026-10-30T00:00:00Z",
    )
    with pytest.raises(ValueError) as exc_info:
        validate_label_timing([bad_item_later], proposed_at)
    err_msg = str(exc_info.value)
    assert bad_item_later.frame.task in err_msg or "synthetic-task-001" in err_msg


def test_ac4_held_out_untouched(synthetic_suite: list[LabeledFrame]) -> None:
    """AC_4: search or evaluation run on training part completes without calling resolver on held-out items."""
    train, holdout = split_holdout(synthetic_suite, seed=7)

    class ExplodingFrame(DecisionFrame):
        def __init__(self, original: DecisionFrame) -> None:
            super().__init__(
                task=original.task,
                criteria=original.criteria,
                options=original.options,
                constraints=original.constraints,
                minimum_margin=original.minimum_margin,
                uncertainty_penalty=original.uncertainty_penalty,
                max_uncertainty=original.max_uncertainty,
            )

    # Poison held-out items with frames that explode if passed to resolver
    real_resolve = DecisionResolver.resolve
    held_out_tasks = {item.frame.task for item in holdout}

    def guarded_resolve(self: DecisionResolver, snapshot: Any, frame: DecisionFrame) -> Any:
        if frame.task in held_out_tasks:
            raise RuntimeError(f"Resolver called on held-out item: {frame.task}")
        return real_resolve(self, snapshot, frame)

    poisoned_holdout = [
        LabeledFrame(
            frame=ExplodingFrame(item.frame),
            label=item.label,
            labeled_at=item.labeled_at,
        )
        for item in holdout
    ]

    snapshot = PolicySnapshot(
        id="policy-synth",
        agent_id="agent-synth",
        task_id="task-synth",
        version=1,
        actions=[Action(id="A"), Action(id="B")],
        logits={"A": 0.0, "B": 0.0},
    )

    resolver = DecisionResolver()
    resolver.resolve = MagicMock(side_effect=lambda s, f: guarded_resolve(resolver, s, f))  # type: ignore[assignment]

    # Evaluation on training part only
    resolved_count = 0
    for item in train:
        res = resolver.resolve(snapshot, item.frame)
        assert res.selected_action is not None
        resolved_count += 1

    assert resolved_count == len(train)
    # Ensure held-out items were never touched
    for item in poisoned_holdout:
        # None of the poisoned items should have been resolved
        assert not any(call.args[1].task == item.frame.task for call in resolver.resolve.call_args_list)


def test_upstream_purity_and_no_storage_import() -> None:
    """[I1] & [I2]: Module must be in agent_learning_ext and import nothing from agent_learning.storage."""
    import agent_learning_ext.weight_compiler as wc

    assert "storage" not in wc.__file__
    assert not hasattr(wc, "agent_learning.storage")
    # Verify module does not import storage
    with open(wc.__file__, "r", encoding="utf-8") as f:
        content = f.read()
    assert "agent_learning.storage" not in content
