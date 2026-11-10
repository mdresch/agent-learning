"""Thompson sampling (methodology #9) using the real agent_learning ThompsonPolicy and ThompsonLearner.

STATUS: runnable
CODE: sdk
DATA: SYNTHETIC
IDEATION ROW: #9 Thompson sampling
ADR: ADR-015
HYPOTHESIS: HYP-AL-002, see also HYP-AL-009
NOT EVIDENCE: this run does not validate or invalidate the methodology. The rewards below are invented.
"""

from __future__ import annotations

import random

from agent_learning.learners.thompson import ThompsonLearner
from agent_learning.policy.thompson import SELECTION_BASIS, ThompsonPolicy
from agent_learning.storage.memory import InMemoryStore
from agent_learning.types import Action, Episode, Reward, RewardSource


def main() -> None:
    print("DATA: SYNTHETIC. NOT EVIDENCE: this run does not validate or invalidate Thompson sampling.")
    rng = random.Random(20261026)
    store = InMemoryStore()

    actions = [
        Action(id="action_a", description="High-reward action"),
        Action(id="action_b", description="Low-reward action"),
    ]
    policy = ThompsonPolicy.from_actions(actions, agent_id="demo-agent", task_id="demo-task")
    learner = ThompsonLearner()
    store.store_policy(policy.snapshot())

    true_p = {"action_a": 0.8, "action_b": 0.4}
    counts = {a.id: 0 for a in actions}

    for round_idx in range(5):
        episodes: list[Episode] = []
        rewards: list[Reward] = []
        for step in range(20):
            # Fixed request id and timestamp make every draw replayable from the recorded seed.
            decision = policy.choose(request_id=f"r{round_idx}-s{step}", timestamp="2026-11-10T00:00:00+00:00")
            act_id = decision.action.id
            counts[act_id] += 1
            snap = policy.snapshot()

            success = rng.random() < true_p[act_id]
            ep_id = f"ts-r{round_idx}-s{step}"
            episodes.append(
                Episode(
                    id=ep_id,
                    agent_id="demo-agent",
                    task_id="demo-task",
                    action_id=act_id,
                    policy_id=snap.id,
                    policy_version=snap.version,
                    metadata={"selection_basis": SELECTION_BASIS},
                )
            )
            # Reward values are in [-1, 1]; the learner maps them to a success probability.
            rewards.append(
                Reward(
                    episode_id=ep_id,
                    agent_id="demo-agent",
                    source=RewardSource.AGGREGATE,
                    value=1.0 if success else -1.0,
                )
            )

        for ep in episodes:
            store.store_episode(ep)
        _ = learner.update(policy, episodes, rewards)
        store.store_policy(policy.snapshot())

    posterior = policy.posterior()
    print(f"  pull counts: {counts}")
    print(f"  posterior alpha: {posterior['alpha']}")
    assert counts["action_a"] > counts["action_b"], "Thompson sampling should pull the better action more often"
    assert len(policy.consumed_episode_ids()) == 100
    print("  Thompson checks passed (seeded draws, Beta posterior updated, each episode counted once)")


if __name__ == "__main__":
    main()
