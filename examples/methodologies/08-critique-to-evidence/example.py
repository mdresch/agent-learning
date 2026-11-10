"""Critique-to-evidence (methodology #8) using the real agent_learning_ext parser and resolver.

STATUS: runnable
CODE: sdk
DATA: SYNTHETIC
IDEATION ROW: #8 Critique-to-evidence
ADR: ADR-014
HYPOTHESIS: HYP-AL-005
NOT EVIDENCE: this run does not validate or invalidate the methodology. The critiques below are invented.
"""

from __future__ import annotations

from agent_learning.decision import (
    DecisionCriterion,
    DecisionFrame,
    DecisionOption,
    DecisionResolver,
    EvidencePoint,
)
from agent_learning.policy import SoftmaxPolicy
from agent_learning.storage.memory import InMemoryStore
from agent_learning.types import Action
from agent_learning_ext.critique_evidence import apply_critique, parse_critique, to_episode_metadata


def main() -> None:
    print("DATA: SYNTHETIC. NOT EVIDENCE: this run does not validate or invalidate Critique-to-evidence.")
    store = InMemoryStore()

    # Two candidate strategies
    actions = [
        Action(id="async_batch", description="High-throughput batch pipeline"),
        Action(id="sync_atomic", description="Synchronous safe 2PC pipeline"),
    ]

    criteria = (
        DecisionCriterion(id="reliability", weight=0.60, description="Crash resilience"),
        DecisionCriterion(id="throughput", weight=0.40, description="Transaction throughput"),
    )

    # Initial evidence favoring async_batch
    opt_a = DecisionOption(
        action=actions[0],
        evidence=(
            EvidencePoint(criterion_id="reliability", source="benchmarks", support=0.82, confidence=0.85),
            EvidencePoint(criterion_id="throughput", source="benchmarks", support=0.90, confidence=0.90),
        ),
    )
    opt_b = DecisionOption(
        action=actions[1],
        evidence=(
            EvidencePoint(criterion_id="reliability", source="benchmarks", support=0.75, confidence=0.85),
            EvidencePoint(criterion_id="throughput", source="benchmarks", support=0.60, confidence=0.90),
        ),
    )

    frame = DecisionFrame(
        task="select-pipeline",
        criteria=criteria,
        options=(opt_a, opt_b),
    )

    policy = SoftmaxPolicy.from_actions(actions, agent_id="demo-release-agent", task_id="select-pipeline")
    store.store_policy(policy.snapshot())
    snap = policy.snapshot()

    resolver = DecisionResolver()
    res_before = resolver.resolve(snap, frame)
    print(f"before critique: selected={res_before.selected_action.id if res_before.selected_action else None}")

    # Critique identifying defect on async_batch
    critique_text = (
        "- [criterion: reliability] [claim: crash risk] [verified: yes]: Network timeout leak causes crash.\n"
        "- [criterion: throughput] -0.15: Cache eviction overhead."
    )
    deltas = parse_critique(critique_text, source_id="CRIT-001")
    applied = apply_critique(frame, option_id="async_batch", deltas=deltas, kappa=0.20)

    res_after = resolver.resolve(snap, applied.frame)
    print(f"after critique:  selected={res_after.selected_action.id if res_after.selected_action else None}")

    # Metadata serialization
    meta = to_episode_metadata(applied)
    assert len(meta["critique_adjustments"]) == 2

    assert res_before.selected_action.id == "async_batch"
    assert res_after.selected_action.id == "sync_atomic", "critique defect should flip the decision"
    print("  critique-to-evidence ingestion checks passed (parsed, pooled, doubt-inflated, flipped)")


if __name__ == "__main__":
    main()
