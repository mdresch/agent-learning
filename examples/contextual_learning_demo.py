"""Demonstration: Packaged Contextual Learning (ADR-038 / Epic 38).

Run this file with:
    uv run python examples/contextual_learning_demo.py

This walkthrough illustrates:
1. Contextual decision policy (ContextualSoftmaxPolicy):
   - Rather than learning a single global distribution over actions, the policy
     computes logits via W @ phi, conditioning decisions on request context features.
2. Generating context-conditioned choices via policy.choose(state=features).
3. Updating the weight matrix via ContextualReinforceLearner:
   - Evaluates policy gradients w.r.t. weight rows W[action] using logged feature vectors.
4. Testing post-training specialization across distinct user profiles.
"""

from __future__ import annotations

import random

from agent_learning.config import LearnerConfig
from agent_learning.policy.contextual_softmax import ContextualSoftmaxPolicy
from agent_learning.storage.memory import InMemoryStore
from agent_learning.types import Action, Episode, Reward, RewardSource
from agent_learning_ext.learners.contextual_reinforce import ContextualReinforceLearner


def header(title: str) -> None:
    print(f"\n{'=' * 78}")
    print(f"  {title}")
    print(f"{'=' * 78}\n")


def main() -> None:
    print("\n" + "#" * 78)
    print("  AGENT LEARNING EXTENSIONS - CONTEXTUAL REINFORCE DEMO (Epic 38)")
    print("#" * 78)

    rng = random.Random(42)
    store = InMemoryStore()

    # 1. Problem Setup: Support Triage Routing
    header("Step 1: Contextual Decision Formulation")
    print("Scenario: An agent chooses how to resolve technical support inquiries.")
    print("Candidate Actions:")
    print("  - 'concise_cli': Raw shell commands and technical summary.")
    print("  - 'guided_gui':  Step-by-step visual UI instructions.")
    print("\nContext Feature Vector phi = [is_developer, system_urgency, enterprise_tier]:")
    print("  - Feature 0: is_developer (1.0 = Senior Dev / Engineer, 0.0 = Business User)")
    print("  - Feature 1: system_urgency (1.0 = Production Outage, 0.0 = Routine Request)")
    print("  - Feature 2: enterprise_tier (1.0 = Premium Enterprise, 0.0 = Free Tier)")

    actions = [
        Action(id="concise_cli", description="Direct CLI commands & logs"),
        Action(id="guided_gui", description="Step-by-step UI walkthrough"),
    ]
    feature_dim = 3

    policy = ContextualSoftmaxPolicy.from_actions(
        actions=actions,
        feature_dim=feature_dim,
        agent_id="support-agent",
        task_id="choose-guidance-format",
        rng=rng,
    )
    store.store_policy(policy.snapshot())

    # Two test profiles
    profile_dev = [1.0, 1.0, 1.0]   # High-urgency enterprise engineer
    profile_biz = [0.0, 0.2, 0.5]   # Non-technical business user

    header("Step 2: Initial Policy Probabilities (Zero Weights)")
    p_dev_init = policy.probabilities(state=profile_dev)
    p_biz_init = policy.probabilities(state=profile_biz)

    print(f"Profile: Enterprise Engineer {profile_dev}:")
    print(f"  - concise_cli: {p_dev_init[0]:.3f} | guided_gui: {p_dev_init[1]:.3f} (Equal / Uniform)")
    print(f"Profile: Business User       {profile_biz}:")
    print(f"  - concise_cli: {p_biz_init[0]:.3f} | guided_gui: {p_biz_init[1]:.3f} (Equal / Uniform)")

    # 3. Simulate Environment Interactions & User Feedback
    header("Step 3: Simulating Contextual Episodes & User Feedback")
    print("Simulating 3 rounds of customer interactions (40 episodes each):")
    print("  - When user is a developer, 'concise_cli' yields positive satisfaction (+1.0), 'guided_gui' fails (-0.5).")
    print("  - When user is non-technical, 'guided_gui' yields positive satisfaction (+1.0), 'concise_cli' fails (-0.5).")

    learner = ContextualReinforceLearner(LearnerConfig(learning_rate=0.8, baseline_decay=0.8))

    header("Step 4: Training with ContextualReinforceLearner across Rounds")
    for round_num in range(1, 4):
        episodes: list[Episode] = []
        rewards: list[Reward] = []
        for i in range(40):
            is_dev = rng.random() > 0.5
            features = [1.0 if is_dev else 0.0, rng.uniform(0.1, 1.0), rng.uniform(0.0, 1.0)]

            decision = policy.choose(state=features)
            chosen_action = decision.action.id

            if is_dev:
                satisfaction = 1.0 if chosen_action == "concise_cli" else -0.5
            else:
                satisfaction = 1.0 if chosen_action == "guided_gui" else -0.5

            ep = Episode(
                id=f"ctx-r{round_num}-ep-{i}",
                agent_id="support-agent",
                task_id="choose-guidance-format",
                action_id=chosen_action,
                action_logprob=decision.logprob,
                metadata={"feature_vector": features, "feedback_status": "accepted"},
            )
            r = Reward(episode_id=ep.id, value=satisfaction, source=RewardSource.AGGREGATE)

            store.store_episode(ep)
            store.store_reward(r)
            episodes.append(ep)
            rewards.append(r)

        result = learner.update(policy, episodes, rewards)
        store.store_policy(policy.snapshot())
        print(f"  Round {round_num}: used {result.episodes_used} episodes, mean reward = {result.mean_reward:+.3f}")

    # 5. Inspect Learned Weights Matrix
    header("Step 5: Learned Context Weight Matrix W (shape: 2 x 3)")
    weights = policy.snapshot().metadata["context_weights"]
    for aid, row in weights.items():
        row_str = ", ".join(f"{w:+.3f}" for w in row)
        print(f"  Action '{aid:<11}': [ {row_str} ]")

    # 6. Evaluate Specialization on Unseen Requests
    header("Step 6: Context-Conditioned Policy Specialization")
    p_dev_trained = policy.probabilities(state=profile_dev)
    p_biz_trained = policy.probabilities(state=profile_biz)

    print(f"Profile A: Senior Enterprise Engineer {profile_dev}:")
    print(f"  - concise_cli: {p_dev_trained[0]:.1%} (was {p_dev_init[0]:.1%})")
    print(f"  - guided_gui:  {p_dev_trained[1]:.1%} (was {p_dev_init[1]:.1%})")
    print("  -> Result: Strongly favors CLI commands for engineers!")

    print(f"\nProfile B: Business End-User {profile_biz}:")
    print(f"  - concise_cli: {p_biz_trained[0]:.1%} (was {p_biz_init[0]:.1%})")
    print(f"  - guided_gui:  {p_biz_trained[1]:.1%} (was {p_biz_init[1]:.1%})")
    print("  -> Result: Strongly favors step-by-step UI walkthrough for business users!")

    header("Demo Complete")
    print("Packaged Contextual Learning operational in agent_learning_ext.learners.contextual_reinforce!\n")


if __name__ == "__main__":
    main()
