"""Scored-search decision compilation (methodology #22) using the real agent_learning_ext weight_compiler.

STATUS: runnable
CODE: sdk
DATA: SYNTHETIC
IDEATION ROW: #22 Scored-search decision compilation
ADR: ADR-022
HYPOTHESIS: HYP-AL-010
NOT EVIDENCE: this run does not validate or invalidate the methodology. The frames below are invented.
"""

from __future__ import annotations

import random

from agent_learning.decision import (
    DecisionCriterion,
    DecisionFrame,
    DecisionOption,
    DecisionResolver,
    EvidencePoint,
)
from agent_learning.types import Action, PolicySnapshot
from agent_learning_ext.weight_compiler import (
    CompiledWeights,
    LabeledFrame,
    propose,
    split_holdout,
)


def main() -> None:
    print("DATA: SYNTHETIC. NOT EVIDENCE: this run does not validate or invalidate Scored-search decision compilation.")
    rng = random.Random(20261026)

    actions = [Action(id="opt_a"), Action(id="opt_b")]
    snapshot = PolicySnapshot(
        id="policy-weight-demo",
        agent_id="demo-agent",
        task_id="demo-task",
        version=1,
        actions=actions,
        logits={"opt_a": 0.0, "opt_b": 0.0},
    )

    hidden_weights = {"c1": 0.60, "c2": 0.30, "c3": 0.10}
    authored_weights = {"c1": 0.10, "c2": 0.10, "c3": 0.80}

    resolver = DecisionResolver()
    labeled_items: list[LabeledFrame] = []

    for i in range(30):
        ev_a = [EvidencePoint(criterion_id=f"c{k}", source="audit", support=round(rng.uniform(0.2, 0.9), 3), confidence=0.9) for k in (1, 2, 3)]
        ev_b = [EvidencePoint(criterion_id=f"c{k}", source="audit", support=round(rng.uniform(0.2, 0.9), 3), confidence=0.9) for k in (1, 2, 3)]

        # Hidden ground truth frame determines human label
        gt_criteria = [DecisionCriterion(id=f"c{k}", weight=hidden_weights[f"c{k}"]) for k in (1, 2, 3)]
        gt_frame = DecisionFrame(
            task=f"task-{i:03d}",
            criteria=gt_criteria,
            options=(DecisionOption(action=actions[0], evidence=tuple(ev_a)), DecisionOption(action=actions[1], evidence=tuple(ev_b))),
        )
        res = resolver.resolve(snapshot, gt_frame)
        label = res.selected_action.id if res.selected_action else "opt_a"

        # Stored frame holds the misaligned authored weights
        auth_criteria = [DecisionCriterion(id=f"c{k}", weight=authored_weights[f"c{k}"]) for k in (1, 2, 3)]
        stored_frame = DecisionFrame(
            task=f"task-{i:03d}",
            criteria=auth_criteria,
            options=(DecisionOption(action=actions[0], evidence=tuple(ev_a)), DecisionOption(action=actions[1], evidence=tuple(ev_b))),
        )
        labeled_items.append(LabeledFrame(frame=stored_frame, label=label, labeled_at=f"2026-10-26T10:{i:02d}:00Z"))

    train_set, holdout_set = split_holdout(labeled_items, fraction=0.30, seed=42)
    assert len(train_set) == 21 and len(holdout_set) == 9

    compiled = propose(
        train=train_set,
        holdout=holdout_set,
        snapshot=snapshot,
        proposed_at="2026-10-26T12:00:00Z",
        step=0.05,
        restarts=5,
        seed=42,
    )

    assert isinstance(compiled, CompiledWeights), "compiled weights should beat baseline on holdout"
    assert compiled.holdout_accuracy > compiled.baseline_holdout_accuracy
    print(f"  compiled weights: {dict(compiled.weights)}")
    print(f"  accuracy: baseline={compiled.baseline_holdout_accuracy:.2f} -> compiled={compiled.holdout_accuracy:.2f}")
    print("  scored-search decision compilation checks passed (split, ascents, proposed)")


if __name__ == "__main__":
    main()
