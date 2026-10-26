"""A low-authority policy learns, for one category of change, how much to escalate.

STATUS: runnable
CODE: sdk
DATA: SYNTHETIC
IDEATION ROW: #21 Category-level escalation learning
ADR: ADR-007
HYPOTHESIS: HYP-AL-007
NOT EVIDENCE: this run does not validate or invalidate the methodology. The outcomes are invented.
Status in the SDK: the escalation policy is implemented but untrained on real data.
"""

from __future__ import annotations

import random

from agent_learning.config import LearnerConfig
from agent_learning.governance import (
    APPLY_AUTOMATICALLY,
    APPLY_WITH_NOTIFICATION,
    ESCALATE_TO_HUMAN,
    ESCALATION_ACTIONS,
)
from agent_learning.learners import ReinforceLearner
from agent_learning.policy import SoftmaxPolicy
from agent_learning.types import Action, Episode, Reward, RewardSource

AGENT = "demo-governance"
# Invented outcome values for ONE category (documentation corrections): escalating every one
# wastes review effort, applying silently is fine, applying with a notice sits in between.
OUTCOME = {ESCALATE_TO_HUMAN: -0.1, APPLY_WITH_NOTIFICATION: 0.3, APPLY_AUTOMATICALLY: 0.8}


def main() -> None:
    print("DATA: SYNTHETIC. NOT EVIDENCE: this run does not validate or invalidate category-level escalation.")
    rng = random.Random(5)
    actions = [Action(id=a) for a in ESCALATION_ACTIONS]
    policy = SoftmaxPolicy.from_actions(actions, agent_id=AGENT, rng=rng)
    learner = ReinforceLearner(LearnerConfig(learning_rate=0.4, entropy_bonus=0.01))

    def show(label: str) -> dict[str, float]:
        probs = {a.id: round(p, 3) for a, p in zip(actions, policy.probabilities())}
        print(label, probs)
        return probs

    before = show("before:")
    for round_number in range(6):
        episodes: list[Episode] = []
        rewards: list[Reward] = []
        for index in range(40):
            decision = policy.choose()
            snapshot = policy.snapshot()
            episode = Episode(
                id=f"r{round_number}-e{index}",
                agent_id=AGENT,
                task_id="escalate-diff-response",
                intent_summary="Respond to a documentation correction",
                action_id=decision.action.id,
                expected_outcome="The correction is applied without harm",
                execution_status="completed",
                result_summary="Synthetic outcome",
                policy_id=snapshot.id,
                policy_version=snapshot.version,
                action_logprob=decision.logprob,
            )
            episodes.append(episode)
            rewards.append(Reward(episode_id=episode.id, agent_id=AGENT, source=RewardSource.AGGREGATE, value=OUTCOME[decision.action.id]))
        learner.update(policy, episodes, rewards)
    after = show("after: ")
    assert after[APPLY_AUTOMATICALLY] > before[APPLY_AUTOMATICALLY]
    print("Lineage-changing diff types stay frozen from autonomy whatever this policy learns (ADR-007 Invariant 4).")


if __name__ == "__main__":
    main()
