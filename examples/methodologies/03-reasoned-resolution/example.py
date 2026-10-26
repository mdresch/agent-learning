"""A full-authority decision is resolved from weighed evidence, with no training.

STATUS: runnable
CODE: sdk
DATA: SYNTHETIC
IDEATION ROW: #3 Bayesian reasoned resolution
ADR: none
HYPOTHESIS: HYP-AL-003
NOT EVIDENCE: this run does not validate or invalidate the methodology. The evidence scores are invented.
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
from agent_learning.types import Action, PolicySnapshot


def make_policy(requires_human_approval: bool) -> TaskPolicy:
    snapshot = PolicySnapshot(
        id="demo-policy",
        agent_id="demo-agent",
        task_id="choose-region",
        version=0,
        actions=[Action(id="east"), Action(id="west")],
        logits={"east": 0.0, "west": 0.0},
        metadata={
            "decision_authority": DecisionAuthority.FULL.value,
            "requires_human_approval": requires_human_approval,
        },
    )
    return TaskPolicy(snapshot)


def make_frame() -> DecisionFrame:
    def option(action_id: str, capacity: float, latency: float) -> DecisionOption:
        return DecisionOption(
            action=Action(id=action_id),
            evidence=[
                EvidencePoint(criterion_id="capacity", source="quota", support=capacity),
                EvidencePoint(criterion_id="capacity", source="forecast", support=capacity - 0.05),
                EvidencePoint(criterion_id="latency", source="probe", support=latency),
            ],
        )

    return DecisionFrame(
        task="Choose a deployment region",
        criteria=[
            DecisionCriterion(id="capacity", weight=0.7, minimum_sources=2),
            DecisionCriterion(id="latency", weight=0.3),
        ],
        options=[option("east", 0.85, 0.8), option("west", 0.55, 0.6)],
    )


def main() -> None:
    print("DATA: SYNTHETIC. NOT EVIDENCE: this run does not validate or invalidate reasoned resolution.")
    frame = make_frame()

    result = make_policy(requires_human_approval=False).decide(frame)
    print("status:", result.status.value, "| selected:", result.selected_action.id if result.selected_action else None)
    for assessment in result.assessments:
        print(f"  {assessment.action.id}: robust utility {assessment.robust_utility:.3f}")

    gated = make_policy(requires_human_approval=True).decide(frame)
    print("with human approval required:", gated.status.value, "| proposed:", gated.proposed_action.id)
    assert result.selected_action is not None and result.selected_action.id == "east"
    assert gated.selected_action is None


if __name__ == "__main__":
    main()
