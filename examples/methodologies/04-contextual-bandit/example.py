"""A contextual softmax policy learns a different best action for each context.

STATUS: runnable
CODE: sdk
DATA: SYNTHETIC
IDEATION ROW: #4 Contextual bandit
ADR: none
HYPOTHESIS: HYP-AL-004
NOT EVIDENCE: this run does not validate or invalidate the methodology. The contexts and rewards are invented.
The policy class is in the SDK but the trainable learner is example-only (it is written out below).
"""

from __future__ import annotations

import random

from agent_learning.policy.contextual_softmax import ContextualSoftmaxPolicy
from agent_learning.types import Action

# phi = [bias, enterprise, consumer]
CONTEXTS = {"enterprise": [1.0, 1.0, 0.0], "consumer": [1.0, 0.0, 1.0]}
BEST = {"enterprise": "call", "consumer": "email"}


def main() -> None:
    print("DATA: SYNTHETIC. NOT EVIDENCE: this run does not validate or invalidate contextual bandits.")
    rng = random.Random(11)
    actions = [Action(id="call"), Action(id="email"), Action(id="wait")]
    policy = ContextualSoftmaxPolicy.from_actions(actions, feature_dim=3, agent_id="demo-agent", rng=rng)

    def show(label: str) -> None:
        for name, phi in CONTEXTS.items():
            probs = policy.probabilities(phi)
            print(f"{label} {name}:", {a.id: round(p, 2) for a, p in zip(actions, probs)})

    show("before")
    baseline, learning_rate = 0.0, 0.3
    for step in range(800):
        name = rng.choice(list(CONTEXTS))
        phi = CONTEXTS[name]
        decision = policy.choose(phi)
        reward = 0.8 if decision.action.id == BEST[name] else -0.2  # invented outcome
        advantage = reward - baseline
        baseline += 0.05 * (reward - baseline)
        chosen = [a.id for a in actions].index(decision.action.id)
        deltas = {
            a.id: [learning_rate * advantage * ((1.0 if i == chosen else 0.0) - decision.probabilities[i]) * x for x in phi]
            for i, a in enumerate(actions)
        }
        policy.apply_update(deltas, baseline=baseline, episodes_seen=step + 1)
    show("after ")

    for name, phi in CONTEXTS.items():
        probs = policy.probabilities(phi)
        greedy = actions[probs.index(max(probs))].id
        assert greedy == BEST[name], (name, greedy)


if __name__ == "__main__":
    main()
