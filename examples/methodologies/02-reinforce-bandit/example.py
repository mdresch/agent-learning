"""A softmax policy learns from rewards with REINFORCE and a baseline.

STATUS: runnable
CODE: sdk
DATA: SYNTHETIC
IDEATION ROW: #2 RLVR / policy-gradient bandit (REINFORCE with baseline)
ADR: none
HYPOTHESIS: HYP-AL-001
NOT EVIDENCE: this run does not validate or invalidate the methodology. The rewards below are invented.
"""

from __future__ import annotations

import random

from agent_learning.config import LearnerConfig
from agent_learning.learners import ReinforceLearner
from agent_learning.policy import SoftmaxPolicy
from agent_learning.storage import InMemoryStore
from agent_learning.types import Action, Episode, Reward, RewardSource

AGENT = "demo-agent"


def main() -> None:
    print("DATA: SYNTHETIC. NOT EVIDENCE: this run does not validate or invalidate REINFORCE.")
    rng = random.Random(7)
    store = InMemoryStore()
    actions = [
        Action(id="concise", description="Short, direct answer"),
        Action(id="detailed", description="Step-by-step answer"),
    ]
    policy = SoftmaxPolicy.from_actions(actions, agent_id=AGENT, rng=rng)
    learner = ReinforceLearner(LearnerConfig(learning_rate=0.4, entropy_bonus=0.01))
    store.store_policy(policy.snapshot())

    before = policy.probabilities()
    for round_number in range(5):
        episodes: list[Episode] = []
        rewards: list[Reward] = []
        for index in range(40):
            decision = policy.choose()
            snapshot = policy.snapshot()
            # Invented, contrastive outcomes: "detailed" tends to succeed, "concise" tends to fail.
            value = 0.8 if decision.action.id == "detailed" else -0.2
            episode = Episode(
                id=f"r{round_number}-e{index}",
                agent_id=AGENT,
                intent_summary="Answer a support question",
                action_id=decision.action.id,
                expected_outcome="The customer's question is resolved",
                execution_status="completed",
                result_summary="Synthetic outcome",
                policy_id=snapshot.id,
                policy_version=snapshot.version,
                action_logprob=decision.logprob,
            )
            store.store_episode(episode)
            episodes.append(episode)
            rewards.append(Reward(episode_id=episode.id, agent_id=AGENT, source=RewardSource.AGGREGATE, value=value))
        result = learner.update(policy, episodes, rewards)
        store.store_policy(policy.snapshot())
        print(f"round {round_number}: episodes_used={result.episodes_used} mean_reward={result.mean_reward:+.2f}")

    after = policy.probabilities()
    print("probabilities before:", {a.id: round(p, 3) for a, p in zip(actions, before)})
    print("probabilities after: ", {a.id: round(p, 3) for a, p in zip(actions, after)})
    assert after[1] > before[1], "the policy should shift toward the rewarded action"


if __name__ == "__main__":
    main()
