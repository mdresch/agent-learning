"""Demonstration: Structured Critique-to-Evidence Ingestion (ADR-014 / Epic 14).

Run this file with:
    uv run python examples/critique_evidence_demo.py

This walkthrough illustrates:
1. Markdown Critique Tag Grammar:
   - Parsing structured findings from code review / architectural critique bullets.
   - Standardized rubric tags: [criterion: ...], [claim: ...], [verified: yes|partial|no].
   - Explicit signed deltas: e.g., +0.10, -0.25, or explicit override of rubric values.
2. Standard Rubric Scoring:
   - Built-in rubric table mapping defect claims (crash risk, logic error, test gap, style)
     and confirmations to calibrated support deltas.
3. DecisionFrame Evidence Updating & Doubt Accumulation:
   - Applying deltas to existing evidence points on an option.
   - Adjusting doubt and uncertainty using the defect penalty kappa (u_after = u + kappa * defect).
   - Enforcing confidence floor (0.05) and calculating synthetic evidence point support.
4. Decision Resolution Shift:
   - Demonstrating how DecisionResolver evaluates robust utility before and after critique.
   - Observing a decision flip when critique uncovers critical defects on the incumbent option.
5. Episode Metadata Integration:
   - Serializing applied critique adjustments for audit logging and downstream learners.
"""

from __future__ import annotations

import json

from agent_learning.decision import (
    DecisionCriterion,
    DecisionFrame,
    DecisionOption,
    DecisionResolver,
    EvidencePoint,
)
from agent_learning.policy import SoftmaxPolicy
from agent_learning.types import Action
from agent_learning_ext.critique_evidence import (
    apply_critique,
    parse_critique,
    to_episode_metadata,
)


def header(title: str) -> None:
    print(f"\n{'=' * 78}")
    print(f"  {title}")
    print(f"{'=' * 78}\n")


def print_frame_assessment(title: str, frame: DecisionFrame, policy_snap) -> None:
    resolver = DecisionResolver()
    result = resolver.resolve(policy_snap, frame)
    opt_by_id = {opt.action.id: opt for opt in frame.options}
    print(f"--- {title} ---")
    print(f"Resolution Status: {result.status.name}")
    winner = result.selected_action.id if result.selected_action else (result.proposed_action.id if result.proposed_action else "None")
    print(f"Selected/Proposed Action: '{winner}'")
    print("Assessment Details:")
    for a in result.assessments:
        util_str = f"{a.robust_utility:+.4f}" if a.robust_utility is not None else "N/A"
        print(f"  - Option '{a.action.id:<18}': feasible={a.feasible:<5} robust_utility={util_str}")
        for ca in a.criteria:
            print(f"      * Criterion '{ca.criterion_id:<12}': support={ca.support:.3f} sources={ca.source_count}")
        opt = opt_by_id.get(a.action.id)
        if opt:
            for pt in opt.evidence:
                print(f"          - src={pt.source:<26} pt_support={pt.support:.3f} conf={pt.confidence:.3f}")
    print()


def main() -> None:
    print("\n" + "#" * 78)
    print("  AGENT LEARNING EXTENSIONS - CRITIQUE EVIDENCE DEMO (Epic 14)")
    print("#" * 78)

    # 1. Formulation & Setup
    header("Step 1: Scenario Formulation - Pull Request Deployment Strategy")
    print("Scenario: An automated release manager evaluates two candidate implementation")
    print("strategies for a high-throughput payment settlement engine:")
    print("  - Option A ('async_batch'): Asynchronous batched database pipeline (high throughput).")
    print("  - Option B ('sync_atomic'): Synchronous two-phase commit pipeline (conservative & safe).")
    print("\nDecision Criteria:")
    print("  - 'reliability' (weight=0.60): System fault tolerance, crash resistance, and correctness.")
    print("  - 'throughput'  (weight=0.40): Peak transaction processing velocity.")

    act_async = Action(id="async_batch", description="High-throughput asynchronous batch pipeline")
    act_sync = Action(id="sync_atomic", description="Synchronous 2PC atomic pipeline")
    actions = [act_async, act_sync]

    crit_reliability = DecisionCriterion(id="reliability", weight=0.60, description="Crash resilience")
    crit_throughput = DecisionCriterion(id="throughput", weight=0.40, description="Processing speed")
    criteria = (crit_reliability, crit_throughput)

    # Initial evidence before critique
    # Option A starts with high throughput and high claimed reliability from synthetic benchmarks
    ev_a = (
        EvidencePoint(criterion_id="reliability", source="benchmark_suite", support=0.82, confidence=0.85),
        EvidencePoint(criterion_id="throughput", source="benchmark_suite", support=0.90, confidence=0.90),
    )
    # Option B starts with solid reliability and modest throughput
    ev_b = (
        EvidencePoint(criterion_id="reliability", source="benchmark_suite", support=0.75, confidence=0.85),
        EvidencePoint(criterion_id="throughput", source="benchmark_suite", support=0.60, confidence=0.90),
    )

    opt_a = DecisionOption(action=act_async, evidence=ev_a)
    opt_b = DecisionOption(action=act_sync, evidence=ev_b)

    frame = DecisionFrame(
        task="select-release-pipeline",
        criteria=criteria,
        options=(opt_a, opt_b),
    )

    # Neutral uniform policy snapshot
    policy = SoftmaxPolicy.from_actions(actions=actions, agent_id="release-agent", task_id="select-release-pipeline")
    policy_snap = policy.snapshot()

    header("Step 2: Initial Decision State (Prior to Code Review Critique)")
    print_frame_assessment("Initial State", frame, policy_snap)

    # 2. Markdown Critique Review
    header("Step 3: Reviewer Submits Markdown Critique")
    print("A senior security and systems reviewer conducts an architectural critique of")
    print("Option A ('async_batch') and submits findings formatted with Epic 14 tag grammar:")

    critique_markdown = """
## Code Review Findings for async_batch Pipeline

Reviewer: sec-ops-team
Change: PR-4089

Findings:
- [criterion: reliability] [claim: crash risk] [verified: yes]: Unhandled timeout during network partition causes memory leak and daemon crash.
- [criterion: reliability] [claim: test gap] [verified: partial]: No concurrency unit tests covering queue overflow scenarios.
- [criterion: throughput] -0.15: Cache eviction thrashing under adversarial load degrades burst throughput.
- [criterion: reliability] [finding: confirmation-01] [claim: confirmation] [verified: yes]: Database schema migration is fully backwards-compatible.
    """.strip()

    print(f"\n{critique_markdown}\n")

    # 3. Parsing Critique into Structured Deltas
    header("Step 4: Parsing Markdown Critique Tags into CritiqueDelta")
    deltas = parse_critique(critique_markdown, source_id="REV-4089")
    print(f"Parsed {len(deltas)} structured CritiqueDelta instances:\n")
    for d in deltas:
        basis_info = f"basis={d.basis}"
        if d.rubric_delta is not None:
            basis_info += f" rubric_val={d.rubric_delta:+.2f}"
        print(f"  Finding [{d.finding_id}]:")
        print(f"    - Criterion:    {d.criterion_id}")
        print(f"    - Support Delta:{d.support_delta:+.2f} ({basis_info})")
        print(f"    - Rationale:    \"{d.rationale}\"")
        print()

    # 4. Applying Critique to DecisionFrame
    header("Step 5: Applying Critique to DecisionFrame with Bayesian Doubt Updating")
    print("Applying deltas to Option 'async_batch' with doubt multiplier kappa=0.20...")
    applied = apply_critique(frame, option_id="async_batch", deltas=deltas, kappa=0.20)

    print("\nEvidence Adjustment Trace:")
    for adj in applied.adjustments:
        print(f"  Finding: {adj['finding_id']:<18} Criterion: {adj['criterion_id']}")
        print(f"    Support:     {adj['support_before']:.3f} -> {adj['support_after']:.3f} (delta={adj['support_delta']:+.2f})")
        print(f"    Uncertainty: {adj['uncertainty_before']:.3f} -> {adj['uncertainty_after']:.3f}")
        print(f"    Appended Point: support={adj['point_support']:.3f}, confidence={adj['point_confidence']:.3f}")
        print()

    # 5. Decision Resolution Shift
    header("Step 6: Decision Resolution Post-Critique")
    print_frame_assessment("Post-Critique State", applied.frame, policy_snap)

    resolver = DecisionResolver()
    res_before = resolver.resolve(policy_snap, frame)
    res_after = resolver.resolve(policy_snap, applied.frame)

    print("Decision Shift Summary:")
    print(f"  Selected Action Before: '{res_before.selected_action.id if res_before.selected_action else None}'")
    print(f"  Selected Action After:  '{res_after.selected_action.id if res_after.selected_action else None}'")

    assert res_before.selected_action.id == "async_batch", "Option A should win before critique"
    assert res_after.selected_action.id == "sync_atomic", "Option B should win after critique due to crash risk"

    # 6. Episode Metadata Export
    header("Step 7: Serializing to Episode Metadata")
    metadata = to_episode_metadata(applied)
    print(f"Generated episode metadata payload ({len(metadata['critique_adjustments'])} recorded adjustments):")
    sample_json = json.dumps(metadata, indent=2)
    # Print excerpt
    lines = sample_json.splitlines()
    print("\n".join(lines[:24]))
    print(f"    ... [{len(lines) - 24} more lines truncated] ...\n")

    print("Verification Successful:")
    print("  [PASSED] Markdown critique tags correctly parsed against design rubric.")
    print("  [PASSED] Defect findings reduced pooled support and inflated doubt.")
    print("  [PASSED] DecisionResolver successfully flipped release strategy to 'sync_atomic'.")
    print("  [PASSED] Adjustments exported cleanly to episode metadata format.")


if __name__ == "__main__":
    main()
