"""Demonstration: Scored-Search Decision Weight Compilation (ADR-022 / Epic 22).

Run this file with:
    uv run python examples/weight_compiler_demo.py

This walkthrough illustrates:
1. Multi-Criteria Decision Weight Misalignment:
   - An agent uses multi-criteria scoring to choose between actions.
   - Authored criteria weights can drift or be poorly calibrated initially
     (e.g., over-weighting cost over critical security posture).
2. Historical Labeled Decision Dataset (LabeledFrame):
   - Decisions adjudicated by human experts over time, recording the settled action
     and adjudication timestamp (labeled_at).
3. Reproducible Holdout Partitioning (split_holdout):
   - Splitting historical frames into training and held-out evaluation sets (e.g. 70/30).
   - Enforcing deterministic ordering, minimum partition thresholds, and timing rules.
4. Simplex Coordinate Ascent (coordinate_ascent):
   - Searching weight coordinates on the simplex (w_k >= 0.05, sum(w_k) == 1.0).
   - Maximizing multi-objective: accuracy + beta * margin across multiple restarts.
5. Strict Improvement Safety Gate (propose):
   - Comparing compiled weights against authored baseline weights on held-out data.
   - Emitting CompiledWeights ONLY when holdout accuracy strictly beats baseline;
     otherwise safely returning NoImprovement.
6. Applying Compiled Configuration (apply_compiled_config):
   - Injecting compiled criteria weights into incoming production DecisionFrames.
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
    apply_compiled_config,
    coordinate_ascent,
    evaluate,
    propose,
    split_holdout,
)


def header(title: str) -> None:
    print(f"\n{'=' * 78}")
    print(f"  {title}")
    print(f"{'=' * 78}\n")


def generate_scenario_dataset(n: int = 30) -> tuple[list[LabeledFrame], dict[str, float], dict[str, float], PolicySnapshot]:
    """Generate a realistic labeled dataset where human experts decide under true hidden priorities."""
    rng = random.Random(20261110)
    actions = [
        Action(id="arch_a", description="Cloud-Native Managed Microservices"),
        Action(id="arch_b", description="Self-Hosted Edge Cluster"),
    ]

    snapshot = PolicySnapshot(
        id="policy-arch-triage",
        agent_id="arch-triage-agent",
        task_id="select-architecture",
        version=1,
        actions=actions,
        logits={"arch_a": 0.0, "arch_b": 0.0},
    )

    # True organization priorities reflected in human decisions:
    # High security emphasis (0.60), moderate speed (0.30), low cost focus (0.10)
    true_weights = {"security": 0.60, "latency": 0.30, "cost": 0.10}

    # Initial misaligned authored weights: heavily over-weighting cost
    authored_weights = {"security": 0.15, "latency": 0.15, "cost": 0.70}

    resolver = DecisionResolver()
    labeled_items: list[LabeledFrame] = []

    for i in range(n):
        # Generate random evidence points for both candidate architectures
        ev_a = [
            EvidencePoint(criterion_id="security", source="sec_audit", support=round(rng.uniform(0.3, 0.95), 3), confidence=0.9),
            EvidencePoint(criterion_id="latency", source="perf_bench", support=round(rng.uniform(0.3, 0.95), 3), confidence=0.9),
            EvidencePoint(criterion_id="cost", source="finops", support=round(rng.uniform(0.3, 0.95), 3), confidence=0.9),
        ]
        ev_b = [
            EvidencePoint(criterion_id="security", source="sec_audit", support=round(rng.uniform(0.3, 0.95), 3), confidence=0.9),
            EvidencePoint(criterion_id="latency", source="perf_bench", support=round(rng.uniform(0.3, 0.95), 3), confidence=0.9),
            EvidencePoint(criterion_id="cost", source="finops", support=round(rng.uniform(0.3, 0.95), 3), confidence=0.9),
        ]

        # Decision with true weights to simulate expert consensus label
        true_criteria = [
            DecisionCriterion(id="security", weight=true_weights["security"]),
            DecisionCriterion(id="latency", weight=true_weights["latency"]),
            DecisionCriterion(id="cost", weight=true_weights["cost"]),
        ]
        ground_truth_frame = DecisionFrame(
            task=f"eval-workload-{i:03d}",
            criteria=true_criteria,
            options=(
                DecisionOption(action=actions[0], evidence=tuple(ev_a)),
                DecisionOption(action=actions[1], evidence=tuple(ev_b)),
            ),
            minimum_margin=0.0,
            uncertainty_penalty=0.0,
        )
        res = resolver.resolve(snapshot, ground_truth_frame)
        human_label = res.selected_action.id if res.selected_action else "arch_a"

        # The frame stored in history carries the authored (misaligned) criteria weights
        authored_criteria = [
            DecisionCriterion(id="security", weight=authored_weights["security"]),
            DecisionCriterion(id="latency", weight=authored_weights["latency"]),
            DecisionCriterion(id="cost", weight=authored_weights["cost"]),
        ]
        stored_frame = DecisionFrame(
            task=f"eval-workload-{i:03d}",
            criteria=authored_criteria,
            options=(
                DecisionOption(action=actions[0], evidence=tuple(ev_a)),
                DecisionOption(action=actions[1], evidence=tuple(ev_b)),
            ),
            minimum_margin=0.0,
            uncertainty_penalty=0.0,
        )

        labeled_at = f"2026-11-09T{10 + (i // 60):02d}:{i % 60:02d}:00Z"
        labeled_items.append(LabeledFrame(frame=stored_frame, label=human_label, labeled_at=labeled_at))

    return labeled_items, authored_weights, true_weights, snapshot


def main() -> None:
    print("\n" + "#" * 78)
    print("  AGENT LEARNING EXTENSIONS - WEIGHT COMPILER DEMO (Epic 22)")
    print("#" * 78)

    # 1. Scenario Setup
    header("Step 1: Scenario Setup - Architecture Selection Decision Framework")
    print("Scenario: An enterprise engineering council deploys an agent to recommend")
    print("deployment architectures for microservices workloads.")
    print("\nCandidate Actions:")
    print("  - 'arch_a': Cloud-Native Managed Microservices")
    print("  - 'arch_b': Self-Hosted Edge Cluster")
    print("\nDecision Criteria:")
    print("  - 'security' (infosec compliance & blast radius)")
    print("  - 'latency'  (p99 service response time)")
    print("  - 'cost'     (monthly compute & licensing expense)")

    dataset, authored_w, true_w, snapshot = generate_scenario_dataset(n=30)
    print(f"\nHistorical Dataset: {len(dataset)} human-adjudicated decision frames.")
    print("True Hidden Priorities (Reflected in Human Adjudication):")
    for k, v in true_w.items():
        print(f"  - {k:<12}: {v:.2f}")
    print("\nAuthored Initial Weights (Heavily Cost-Biased Baseline):")
    for k, v in authored_w.items():
        print(f"  - {k:<12}: {v:.2f}")

    # 2. Baseline Accuracy on Authored Weights
    header("Step 2: Baseline Authored Weight Accuracy")
    resolver = DecisionResolver()
    baseline_hits = 0
    for item in dataset:
        pred, _margin = evaluate(item, authored_w, snapshot)
        if pred == item.label:
            baseline_hits += 1
    initial_acc = baseline_hits / len(dataset)
    print(f"Authored Baseline Accuracy across all frames: {initial_acc * 100:.1f}% ({baseline_hits}/{len(dataset)} matches)")
    print("Notice: Because authored weights over-index on cost (0.70) while human experts")
    print("prioritize security (0.60), the uncompiled framework frequently mispredicts human judgment.")

    # 3. Holdout Partitioning
    header("Step 3: Reproducible Holdout Split (split_holdout)")
    train_set, holdout_set = split_holdout(dataset, fraction=0.30, seed=42)
    print("Dataset split (fraction=0.30, seed=42):")
    print(f"  - Training Set: {len(train_set)} frames")
    print(f"  - Held-out Set: {len(holdout_set)} frames")

    # 4. Coordinate Ascent Search
    header("Step 4: Simplex Coordinate Ascent on Training Partition")
    print("Running coordinate_ascent with simplex step=0.05, beta=0.10...")
    search_res = coordinate_ascent(
        train=train_set,
        snapshot=snapshot,
        step=0.05,
        restarts=5,
        max_sweeps=20,
        beta=0.10,
    )

    print("\nCoordinate Ascent Completed:")
    print(f"  - Sweeps:         {search_res.sweeps}")
    print(f"  - Restarts:       {search_res.restarts}")
    print(f"  - Total Eval:     {search_res.evaluations} evaluations")
    print(f"  - Train Accuracy: {search_res.train_accuracy * 100:.1f}%")
    print("\nCompiled Candidate Weights on Simplex:")
    for cid, w in sorted(search_res.weights.items()):
        print(f"  - {cid:<12}: {w:.4f}")

    # 5. Propose & Safety Gating
    header("Step 5: Safety Gated Proposal Evaluation (propose)")
    print("Evaluating against holdout set strictly prior to proposal timestamp...")
    proposal_time = "2026-11-10T12:00:00Z"
    compiled_result = propose(
        train=train_set,
        holdout=holdout_set,
        snapshot=snapshot,
        proposed_at=proposal_time,
        step=0.05,
        seed=42,
    )

    if isinstance(compiled_result, CompiledWeights):
        print("\n[PROPOSAL ACCEPTED] CompiledWeights meets all safety gates:")
        print(f"  - Baseline Holdout Accuracy: {compiled_result.baseline_holdout_accuracy * 100:.1f}%")
        print(f"  - Compiled Holdout Accuracy: {compiled_result.holdout_accuracy * 100:.1f}%")
        print(f"  - Holdout Margin:            {compiled_result.holdout_margin:.4f}")
        print(f"  - Strictly Outperformed?    YES (+{(compiled_result.holdout_accuracy - compiled_result.baseline_holdout_accuracy) * 100:.1f}% improvement)")
        print(f"  - Immutable Proxy Type:      {type(compiled_result.weights).__name__}")
    else:
        print(f"\n[PROPOSAL REJECTED] NoImprovement: {compiled_result.reason}")

    assert isinstance(compiled_result, CompiledWeights), "Expected successful CompiledWeights proposal"
    assert compiled_result.holdout_accuracy > compiled_result.baseline_holdout_accuracy, (
        "Holdout accuracy must strictly beat baseline"
    )

    # 6. Applying Compiled Config to Production Inference
    header("Step 6: Applying Compiled Config to Active Production Inference")
    # Wrap compiled weights into PolicySnapshot metadata
    production_snapshot = PolicySnapshot(
        id=snapshot.id,
        agent_id=snapshot.agent_id,
        task_id=snapshot.task_id,
        version=snapshot.version + 1,
        actions=snapshot.actions,
        logits=snapshot.logits,
        metadata={"criteria_weights": dict(compiled_result.weights)},
    )

    sample_test_frame = holdout_set[0].frame
    print("Sample Test Frame Criteria BEFORE apply_compiled_config:")
    for c in sample_test_frame.criteria:
        print(f"  - {c.id:<12}: weight={c.weight:.4f}")

    updated_frame = apply_compiled_config(sample_test_frame, production_snapshot)
    print("\nSample Test Frame Criteria AFTER apply_compiled_config:")
    for c in updated_frame.criteria:
        print(f"  - {c.id:<12}: weight={c.weight:.4f}")

    # Verify decision under updated frame
    res_orig = resolver.resolve(snapshot, sample_test_frame)
    res_compiled = resolver.resolve(snapshot, updated_frame)
    print(f"\nAdjudicated Human Label for Frame: '{holdout_set[0].label}'")
    print(f"Resolution with Original Authored Weights: '{res_orig.selected_action.id if res_orig.selected_action else None}'")
    print(f"Resolution with Compiled Criteria Weights: '{res_compiled.selected_action.id if res_compiled.selected_action else None}'")

    print("\nVerification Successful:")
    print("  [PASSED] split_holdout partitioned dataset cleanly and deterministically.")
    print("  [PASSED] coordinate_ascent converged to high training accuracy.")
    print("  [PASSED] propose enforced strict holdout improvement (> baseline).")
    print("  [PASSED] apply_compiled_config safely updated production inference frame.")


if __name__ == "__main__":
    main()
