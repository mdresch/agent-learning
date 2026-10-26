"""One human acceptance grants durable autonomy for a choice; a rejection withholds it.

STATUS: runnable
CODE: sdk
DATA: SYNTHETIC
IDEATION ROW: #6 Durable explicit human override
ADR: ADR-003
HYPOTHESIS: none
NOT EVIDENCE: this run does not validate or invalidate the methodology. The policy and the feedback are invented.
"""

from __future__ import annotations

from agent_learning.autonomy import assess_autonomy
from agent_learning.storage import InMemoryStore
from agent_learning.types import Action, Episode, PolicySnapshot

AGENT, TASK = "demo-agent", "choose-delegate"


def snapshot() -> PolicySnapshot:
    return PolicySnapshot(
        id="demo-policy",
        agent_id=AGENT,
        task_id=TASK,
        version=1,
        actions=[Action(id="winner"), Action(id="alternative")],
        logits={"winner": 0.0, "alternative": 0.0},  # no learned preference at all
        metadata={"policy_scope": "delegated_decision"},
    )


def feedback_episode(status: str, action_id: str) -> Episode:
    return Episode(
        id=f"feedback-{status}",
        agent_id=AGENT,
        task_id=TASK,
        intent_summary="Choose a delegate",
        action_id=action_id,
        expected_outcome="Use the human's choice",
        execution_status="completed",
        result_summary=f"The human {status} the choice",
        metadata={"feedback_status": status, "correct_action_id": action_id},
    )


def assess(label: str, episode: Episode | None) -> bool:
    store = InMemoryStore()
    policy = snapshot()
    store.store_policy(policy)
    if episode is not None:
        store.store_episode(episode)
    result = assess_autonomy(store, policy)
    print(f"{label:34s} eligible={result.eligible} basis={result.authorization_basis} audit_rate={result.audit_rate}")
    return result.eligible


def main() -> None:
    print("DATA: SYNTHETIC. NOT EVIDENCE: this run does not validate or invalidate human override.")
    no_feedback = assess("no feedback, no outcomes", None)
    accepted = assess("one human acceptance", feedback_episode("accepted", "alternative"))
    rejected = assess("a human rejection", feedback_episode("rejected", "alternative"))
    assert (no_feedback, accepted, rejected) == (False, True, False)


if __name__ == "__main__":
    main()
