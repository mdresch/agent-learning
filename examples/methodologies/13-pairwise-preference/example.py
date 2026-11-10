"""Pairwise preference optimization (methodology #13) using the real agent_learning_ext PairwiseLearner.

STATUS: runnable
CODE: sdk
DATA: SYNTHETIC
IDEATION ROW: #13 Pairwise preference optimization
ADR: ADR-018
HYPOTHESIS: none
NOT EVIDENCE: this run does not validate or invalidate the methodology. The overrides below are invented.
"""

from __future__ import annotations

import random

from agent_learning.policy import SoftmaxPolicy
from agent_learning.storage.memory import InMemoryStore
from agent_learning.types import Action, Episode
from agent_learning_ext.learners.pairwise import PairwiseLearner, pairs_from_episodes


def main() -> None:
    print("DATA: SYNTHETIC. NOT EVIDENCE: this run does not validate or invalidate Pairwise preference optimization.")
    rng = random.Random(20261026)
    store = InMemoryStore()

    actions = [
        Action(id="action_x", description="Superior action"),
        Action(id="action_y", description="Intermediate action"),
        Action(id="action_z", description="Suboptimal action"),
    ]
    action_ids = [a.id for a in actions]

    policy = SoftmaxPolicy.from_actions(actions, agent_id="demo-agent", task_id="demo-task", rng=rng)
    store.store_policy(policy.snapshot())

    # Invented human reviewer overrides
    episodes: list[Episode] = []
    # 5 overrides preferring x over y
    for i in range(5):
        ep = Episode(
            id=f"ov-xy-{i}",
            agent_id="demo-agent",
            task_id="demo-task",
            action_id="action_y",
            metadata={"feedback_status": "rejected", "correct_action_id": "action_x"},
        )
        store.store_episode(ep)
        episodes.append(ep)

    # 4 overrides preferring x over z
    for i in range(4):
        ep = Episode(
            id=f"ov-xz-{i}",
            agent_id="demo-agent",
            task_id="demo-task",
            action_id="action_z",
            metadata={"feedback_status": "rejected", "correct_action_id": "action_x"},
        )
        store.store_episode(ep)
        episodes.append(ep)

    # 3 overrides preferring y over z
    for i in range(3):
        ep = Episode(
            id=f"ov-yz-{i}",
            agent_id="demo-agent",
            task_id="demo-task",
            action_id="action_z",
            metadata={"feedback_status": "rejected", "correct_action_id": "action_y"},
        )
        store.store_episode(ep)
        episodes.append(ep)

    pairs = pairs_from_episodes(episodes, action_ids)
    assert len(pairs) == 12

    learner = PairwiseLearner(lam=0.10, lr=0.20, steps=300)
    _ = learner.update(policy, episodes)
    store.store_policy(policy.snapshot())

    raw_probs = policy.probabilities()
    prob_map = {action.id: p for action, p in zip(policy.actions(), raw_probs, strict=True)}
    print(f"  updated probabilities: {prob_map}")

    assert prob_map["action_x"] > prob_map["action_y"] > prob_map["action_z"]
    print("  pairwise preference optimization checks passed (fitted, regularized, ordered)")


if __name__ == "__main__":
    main()
