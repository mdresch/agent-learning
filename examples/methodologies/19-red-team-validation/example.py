"""A flawed counterpart is run through the same policy to test its discriminative power.

STATUS: runnable
CODE: sdk
DATA: SYNTHETIC
IDEATION ROW: #19 Adversarial / red-team example generation
ADR: none
HYPOTHESIS: none
NOT EVIDENCE: this run does not validate or invalidate the methodology. Both proposals and their scores are invented.
This is the practice used to validate a policy, not a training signal.
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


def make_policy() -> TaskPolicy:
    return TaskPolicy(
        PolicySnapshot(
            id="demo-policy",
            agent_id="demo-agent",
            task_id="review-proposal",
            version=0,
            actions=[Action(id="approve"), Action(id="reject")],
            logits={"approve": 0.0, "reject": 0.0},
            metadata={"decision_authority": DecisionAuthority.FULL.value},
        )
    )


def frame(label: str, approve_support: float, flaw_fixed: bool) -> DecisionFrame:
    def option(action_id: str, support: float, no_flaw: bool) -> DecisionOption:
        return DecisionOption(
            action=Action(id=action_id),
            evidence=[EvidencePoint(criterion_id="soundness", source=f"{label}-review", support=support, confidence=0.9)],
            constraint_results={"no_unfixed_critical_flaw": no_flaw},
        )

    return DecisionFrame(
        task=f"Review the {label} proposal",
        criteria=[DecisionCriterion(id="soundness")],
        constraints=["no_unfixed_critical_flaw"],
        options=[option("approve", approve_support, flaw_fixed), option("reject", 1.0 - approve_support, True)],
    )


def main() -> None:
    print("DATA: SYNTHETIC. NOT EVIDENCE: this run does not validate or invalidate red-team validation.")
    # The flawed proposal is made persuasive on purpose: high support, but it carries an unfixed critical flaw.
    cases = {"real": frame("real", 0.85, True), "flawed": frame("flawed", 0.90, False)}
    outcomes = {}
    for label, case in cases.items():
        result = make_policy().decide(case)
        picked = result.selected_action.id if result.selected_action else None
        outcomes[label] = picked
        ruled_out = [a.action.id for a in result.assessments if not a.feasible]
        print(f"{label:7s} status={result.status.value} selected={picked} ruled_out={ruled_out}")
    assert outcomes == {"real": "approve", "flawed": "reject"}, outcomes


if __name__ == "__main__":
    main()
