"""A candidate change to a decision document is classified against a frozen baseline.

STATUS: runnable
CODE: sdk
DATA: SYNTHETIC
IDEATION ROW: #20 Diff/baseline classification with scoped verification
ADR: ADR-007
HYPOTHESIS: HYP-AL-006
NOT EVIDENCE: this run does not validate or invalidate the methodology. The diffs and their scores are invented.
"""

from __future__ import annotations

from agent_learning.decision import (
    DecisionAuthority,
    DecisionCriterion,
    DecisionFrame,
    DecisionOption,
    EvidencePoint,
    TaskPolicy,
)
from agent_learning.governance import (
    DIFF_ACTIONS,
    ESCALATION_ACTIONS,
    GOVERNANCE_CRITERIA_WEIGHTS,
    evaluate_governance_diff,
)
from agent_learning.types import Action, PolicySnapshot

AGENT = "demo-governance"


def classify_policy() -> TaskPolicy:
    return TaskPolicy(
        PolicySnapshot(
            id="classify-demo",
            agent_id=AGENT,
            task_id="classify-diff-type",
            version=0,
            actions=[Action(id=a) for a in DIFF_ACTIONS],
            logits={a: 0.0 for a in DIFF_ACTIONS},
            metadata={"decision_authority": DecisionAuthority.FULL.value},
        )
    )


def escalate_policy() -> TaskPolicy:
    return TaskPolicy(
        PolicySnapshot(
            id="escalate-demo",
            agent_id=AGENT,
            task_id="escalate-diff-response",
            version=0,
            actions=[Action(id=a) for a in ESCALATION_ACTIONS],
            logits={a: 0.0 for a in ESCALATION_ACTIONS},
            metadata={"decision_authority": DecisionAuthority.LOW.value, "capture_decision_evidence": True},
        )
    )


def frame(task: str, favored: str) -> DecisionFrame:
    """Give one diff class strong support on every criterion and the others little."""
    options = []
    for action_id in DIFF_ACTIONS:
        support = 0.85 if action_id == favored else 0.08
        options.append(
            DecisionOption(
                action=Action(id=action_id),
                evidence=[
                    EvidencePoint(criterion_id=c, source=f"diff-analysis-{c}", support=support, confidence=0.9)
                    for c in GOVERNANCE_CRITERIA_WEIGHTS
                ],
            )
        )
    criteria = [DecisionCriterion(id=c, weight=w) for c, w in GOVERNANCE_CRITERIA_WEIGHTS.items()]
    return DecisionFrame(task=task, criteria=criteria, options=options)


def main() -> None:
    print("DATA: SYNTHETIC. NOT EVIDENCE: this run does not validate or invalidate diff classification.")
    cases = [
        ("a corrected typo in a cross-reference", "correction_note"),
        ("a reversal of the decision wearing a 'minor tweak' label", "new_superseding_adr"),
    ]
    results = {}
    for task, favored in cases:
        outcome = evaluate_governance_diff(classify_policy(), escalate_policy(), frame(task, favored), "docs/adr/ADR-DEMO.md")
        selected = outcome.classification_result.selected_action
        results[favored] = outcome
        print(f"{task}\n  classified={selected.id if selected else None} lineage_frozen={outcome.lineage_frozen} disposition={outcome.disposition}")
    assert results["new_superseding_adr"].lineage_frozen
    assert results["new_superseding_adr"].disposition == "escalate_to_human"
    assert not results["correction_note"].lineage_frozen


if __name__ == "__main__":
    main()
