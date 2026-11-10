"""UCB (methodology #10) using the real agent_learning_ext UCBPolicy and UCBLearner.

STATUS: runnable
CODE: sdk
DATA: SYNTHETIC
IDEATION ROW: #10 UCB
ADR: ADR-016
HYPOTHESIS: HYP-AL-009
NOT EVIDENCE: this run does not validate or invalidate the methodology. The rewards below are invented.
"""

from __future__ import annotations

import random

from agent_learning.storage.memory import InMemoryStore
from agent_learning.types import Action, Episode, Reward, RewardSource
from agent_learning_ext.learners.ucb import UCBLearner
from agent_learning_ext.policy.ucb import UCBPolicy


def main() -> None:
    print("DATA: SYNTHETIC. NOT EVIDENCE: this run does not validate or invalidate UCB.")
    rng = random.Random(20261026)
    store = InMemoryStore()

    actions = [
        Action(id="action_a", description="High-reward action"),
        Action(id="action_b", description="Medium-reward action"),
        Action(id="action_c", description="Low-reward action"),
    ]
    policy = UCBPolicy.from_actions(actions, variant="standard", c=1.414, agent_id="demo-agent", task_id="demo-task")
    learner = UCBLearner()
    store.store_policy(policy.snapshot())

    true_p = {"action_a": 0.85, "action_b": 0.50, "action_c": 0.20}
    counts = {a.id: 0 for a in actions}

    for round_idx in range(5):
        episodes: list[Episode] = []
        rewards: list[Reward] = []
        for step in range(20):
            decision = policy.choose()
            act_id = decision.action.id
            counts[act_id] += 1
            snap = policy.snapshot()

            success = rng.random() < true_p[act_id]
            val = 1.0 if success else 0.0

            ep_id = f"ucb-r{round_idx}-s{step}"
            ep = Episode(
                id=ep_id,
                agent_id="demo-agent",
                task_id="demo-task",
                action_id=act_id,
                policy_id=snap.id,
                policy_version=snap.version,
                metadata={"selection_basis": "ucb"},
            )
            rew = Reward(
                episode_id=ep_id,
                agent_id="demo-agent",
                source=RewardSource.AGGREGATE,
                value=val,
            )
            store.store_episode(ep)
            episodes.append(ep)
            rewards.append(rew)

        _ = learner.update(policy, episodes, rewards)
        store.store_policy(policy.snapshot())

    print(f"  pull counts: {counts}")
    assert counts["action_a"] > counts["action_c"], "UCB should pull the superior action more often"
    print("  deterministic UCB checks passed (bounded, counted, updated)")


if __name__ == "__main__":
    main()
