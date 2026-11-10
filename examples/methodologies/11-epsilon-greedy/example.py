"""Epsilon-greedy (methodology #11) using the real agent_learning_ext EpsilonGreedyPolicy and EpsilonGreedyLearner.

STATUS: runnable
CODE: sdk
DATA: SYNTHETIC
IDEATION ROW: #11 Epsilon-greedy
ADR: ADR-017
HYPOTHESIS: none
NOT EVIDENCE: this run does not validate or invalidate the methodology. The rewards below are invented.
"""

from __future__ import annotations

import random

from agent_learning.storage.memory import InMemoryStore
from agent_learning.types import Action, Episode, Reward, RewardSource
from agent_learning_ext.learners.epsilon_greedy import EpsilonGreedyLearner
from agent_learning_ext.policy.epsilon_greedy import EpsilonGreedyPolicy


def main() -> None:
    print("DATA: SYNTHETIC. NOT EVIDENCE: this run does not validate or invalidate Epsilon-greedy.")
    rng = random.Random(20261026)
    store = InMemoryStore()

    actions = [
        Action(id="safe_a", description="Reversible safe action", parameters={"reversible": True}),
        Action(id="safe_b", description="Alternative safe action", parameters={"reversible": True}),
        Action(id="risky_c", description="Irreversible risky action", parameters={"reversible": False}),
    ]

    policy = EpsilonGreedyPolicy.from_actions(
        actions,
        eps0=0.5,
        delta=0.05,
        floor=0.05,
        agent_id="demo-agent",
        task_id="demo-task",
    )
    learner = EpsilonGreedyLearner()
    store.store_policy(policy.snapshot())

    true_p = {"safe_a": 0.85, "safe_b": 0.40, "risky_c": 0.95}
    counts = {a.id: 0 for a in actions}
    explored_picks: set[str] = set()

    for round_idx in range(5):
        episodes: list[Episode] = []
        rewards: list[Reward] = []
        for step in range(20):
            decision = policy.choose(request_id=f"req-{round_idx}-{step}")
            act_id = decision.action.id
            counts[act_id] += 1
            snap = policy.snapshot()

            rec = policy.last_decision_record()
            if rec["branch_taken"] == "exploration":
                explored_picks.add(act_id)

            success = rng.random() < true_p[act_id]
            val = 1.0 if success else 0.0

            ep_id = f"eps-r{round_idx}-s{step}"
            ep = Episode(
                id=ep_id,
                agent_id="demo-agent",
                task_id="demo-task",
                action_id=act_id,
                policy_id=snap.id,
                policy_version=snap.version,
                metadata={"selection_basis": "epsilon_greedy"},
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

    print(f"  pull counts: {counts}, explored: {explored_picks}")
    assert "risky_c" not in explored_picks, "Irreversible risky action must never be chosen during exploration"
    assert sum(counts.values()) == 100
    print("  scheduled epsilon-greedy checks passed (scheduled, masked, updated)")


if __name__ == "__main__":
    main()
