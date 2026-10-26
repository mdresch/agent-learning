"""When evidence is missing, the resolver says which evidence would change the decision.

STATUS: runnable
CODE: sdk
DATA: SYNTHETIC
IDEATION ROW: #12 Active evidence-seeking (information-gain-driven)
ADR: none
HYPOTHESIS: none
NOT EVIDENCE: this run does not validate or invalidate the methodology. The decision and its evidence are invented.
Only the report of what is missing exists in the SDK; an automated loop that goes and gets it does not.
"""

from __future__ import annotations

from agent_learning.decision import (
    DecisionAuthority,
    DecisionCriterion,
    DecisionFrame,
    DecisionOption,
    DecisionStatus,
    TaskPolicy,
)
from agent_learning.types import Action, PolicySnapshot


def main() -> None:
    print("DATA: SYNTHETIC. NOT EVIDENCE: this run does not validate or invalidate active evidence-seeking.")
    policy = TaskPolicy(
        PolicySnapshot(
            id="demo-policy",
            agent_id="demo-agent",
            task_id="choose-region",
            version=0,
            actions=[Action(id="east"), Action(id="west")],
            logits={"east": 0.0, "west": 0.0},
            metadata={"decision_authority": DecisionAuthority.FULL.value},
        )
    )
    frame = DecisionFrame(
        task="Choose a deployment region",
        criteria=[
            DecisionCriterion(id="capacity", weight=0.8, minimum_sources=2),
            DecisionCriterion(id="latency", weight=0.2),
        ],
        constraints=["residency"],
        options=[
            DecisionOption(action=Action(id="east")),
            DecisionOption(action=Action(id="west"), constraint_results={"residency": True}),
        ],
    )
    result = policy.decide(frame)
    print("status:", result.status.value)
    for need in result.information_needs:
        print(f"  need {need.kind:10s} option={need.option_id:5s} field={need.field_id:9s} gain={need.estimated_information_gain_bits:.3f} bits")
    assert result.status is DecisionStatus.NEEDS_EVIDENCE
    assert result.information_needs


if __name__ == "__main__":
    main()
