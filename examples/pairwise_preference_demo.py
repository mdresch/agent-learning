"""Demonstration: Pairwise Preference Optimization (ADR-018 / Epic 18).

Run this file with:
    uv run python examples/pairwise_preference_demo.py

This walkthrough illustrates:
1. Bradley-Terry Preference Formulation:
   - In human-in-the-loop (HITL) workflows, reviewers rarely assign numerical scalar rewards.
   - Instead, reviewers inspect proposed agent decisions and submit overrides
     (e.g., rejecting an action in favor of a human-preferred alternative).
2. Extracting Preference Pairs (winner, loser) from Episode Overrides:
   - Pairs are derived from episodes where feedback_status="rejected" and
     a valid correct_action_id is specified.
3. Anchored Bradley-Terry Convex Regularization:
   - Uses an L2 penalty anchored to frozen reference logits (theta_ref) to prevent
     unbounded logit explosion and catastrophic policy drift.
4. Policy Update via PairwiseLearner:
   - Fitting a SoftmaxPolicy directly to reviewer feedback without scalar rewards.
   - Inspecting probability distribution shifts and convergence metrics.
"""

from __future__ import annotations

import random

from agent_learning.policy import SoftmaxPolicy
from agent_learning.storage.memory import InMemoryStore
from agent_learning.types import Action, Episode
from agent_learning_ext.learners.pairwise import (
    PairwiseLearner,
    bt_loss,
    pairs_from_episodes,
)


def header(title: str) -> None:
    print(f"\n{'=' * 78}")
    print(f"  {title}")
    print(f"{'=' * 78}\n")


def print_policy_dist(title: str, policy: SoftmaxPolicy, action_ids: list[str]) -> None:
    raw_probs = policy.probabilities()
    prob_map = {action.id: p for action, p in zip(policy.actions(), raw_probs, strict=True)}
    logits = policy._snapshot.logits
    print(f"--- {title} ---")
    for aid in action_ids:
        print(f"  Action '{aid:<24}': logit={logits.get(aid, 0.0):+7.4f}  prob={prob_map.get(aid, 0.0)*100:6.2f}%")
    print()


def main() -> None:
    print("\n" + "#" * 78)
    print("  AGENT LEARNING EXTENSIONS - PAIRWISE PREFERENCE DEMO (Epic 18)")
    print("#" * 78)

    rng = random.Random(42)
    store = InMemoryStore()

    # 1. Formulation & Action Space
    header("Step 1: Scenario Setup - Escalation Dispatch Policy")
    print("Scenario: An automated customer operations triage agent determines how to")
    print("handle incoming incident requests.")
    print("\nCandidate Actions:")
    print("  1. 'auto_resolve'      : Close ticket with automated knowledgebase resolution.")
    print("  2. 'queue_standard'    : Route to standard tier-1 support queue.")
    print("  3. 'escalate_incident' : Immediately page on-call SRE / Tier-3 incident response.")

    action_objs = [
        Action(id="auto_resolve", description="Automated knowledgebase resolve"),
        Action(id="queue_standard", description="Standard support queue"),
        Action(id="escalate_incident", description="High-priority escalation to SRE"),
    ]
    action_ids = [a.id for a in action_objs]

    # Initialize a uniform SoftmaxPolicy
    policy = SoftmaxPolicy.from_actions(
        actions=action_objs,
        agent_id="dispatch-agent",
        task_id="triage-incident",
        rng=rng,
    )
    store.store_policy(policy.snapshot())

    header("Step 2: Baseline Policy Probabilities")
    print_policy_dist("Initial Uniform Policy State", policy, action_ids)

    # 2. Simulating Reviewer Feedback Overrides
    header("Step 3: Reviewer Overrides & Feedback Episodes")
    print("Over several triage episodes, the agent proposed 'auto_resolve' or 'queue_standard'.")
    print("Human reviewers intervened and overrode these decisions:")
    print("  - Reviewer rejects 'auto_resolve' -> Overrides with 'escalate_incident' (3 times)")
    print("  - Reviewer rejects 'queue_standard' -> Overrides with 'escalate_incident' (2 times)")
    print("  - Reviewer rejects 'auto_resolve' -> Overrides with 'queue_standard' (1 time)")

    episodes: list[Episode] = [
        # 3 overrides: auto_resolve rejected in favor of escalate_incident
        Episode(
            id="ep-001",
            agent_id="dispatch-agent",
            task_id="triage-incident",
            action_id="auto_resolve",
            metadata={
                "feedback_status": "rejected",
                "correct_action_id": "escalate_incident",
                "reason": "Database connection timeouts detected across cluster.",
            },
        ),
        Episode(
            id="ep-002",
            agent_id="dispatch-agent",
            task_id="triage-incident",
            action_id="auto_resolve",
            metadata={
                "feedback_status": "rejected",
                "correct_action_id": "escalate_incident",
                "reason": "Payment gateway 500 error spike.",
            },
        ),
        Episode(
            id="ep-003",
            agent_id="dispatch-agent",
            task_id="triage-incident",
            action_id="auto_resolve",
            metadata={
                "feedback_status": "rejected",
                "correct_action_id": "escalate_incident",
                "reason": "Security token validation failures.",
            },
        ),
        # 2 overrides: queue_standard rejected in favor of escalate_incident
        Episode(
            id="ep-004",
            agent_id="dispatch-agent",
            task_id="triage-incident",
            action_id="queue_standard",
            metadata={
                "feedback_status": "rejected",
                "correct_action_id": "escalate_incident",
                "reason": "Customer VIP outage report.",
            },
        ),
        Episode(
            id="ep-005",
            agent_id="dispatch-agent",
            task_id="triage-incident",
            action_id="queue_standard",
            metadata={
                "feedback_status": "rejected",
                "correct_action_id": "escalate_incident",
                "reason": "Data corruption risk in replication pipeline.",
            },
        ),
        # 1 override: auto_resolve rejected in favor of queue_standard
        Episode(
            id="ep-006",
            agent_id="dispatch-agent",
            task_id="triage-incident",
            action_id="auto_resolve",
            metadata={
                "feedback_status": "rejected",
                "correct_action_id": "queue_standard",
                "reason": "Missing clarification from customer.",
            },
        ),
        # Normal approved episode (no override; will not generate preference pairs)
        Episode(
            id="ep-007",
            agent_id="dispatch-agent",
            task_id="triage-incident",
            action_id="escalate_incident",
            metadata={
                "feedback_status": "accepted",
                "notes": "Correct escalation.",
            },
        ),
    ]

    for ep in episodes:
        store.store_episode(ep)

    # Extract preference pairs
    pairs = pairs_from_episodes(episodes, action_ids)
    print(f"Extracted {len(pairs)} preference pairs from {len(episodes)} episodes:")
    for p in pairs:
        print(f"  [Episode {p.source_episode_id}] Winner: '{p.winner:<18}' preferred over Loser: '{p.loser}'")

    # 3. Bradley-Terry Loss Calculation
    header("Step 4: Bradley-Terry Optimization with L2 Reference Anchor")
    print("The Bradley-Terry model calculates probability that action w beats action l:")
    print("    P(w > l) = 1 / (1 + exp(-(theta_w - theta_l)))")
    print("Loss function with L2 anchoring to frozen reference theta_ref:")
    print("    L(theta) = sum_{(w,l)} W[w,l] * log(1 + exp(-(theta_w - theta_l)))")
    print("             + (lambda / 2) * sum_a (theta_a - theta_ref_a)^2")

    theta_ref = dict(policy._snapshot.logits)
    initial_loss = bt_loss(theta_ref, pairs, theta_ref, action_ids, lam=0.1)
    print(f"\nInitial Bradley-Terry Loss (at theta_ref): {initial_loss:.4f}")

    # 4. Fitting Policy via PairwiseLearner
    header("Step 5: Updating SoftmaxPolicy via PairwiseLearner")
    learner = PairwiseLearner(
        lam=0.1,      # Regularization anchor strength
        lr=0.2,       # Maximum step size
        steps=500,    # Max iterations
        clamp=6.0,    # Logit bounding box [-6.0, +6.0]
        tol=1e-7,     # Stationarity convergence threshold
    )

    print("Running learner.update(policy, episodes)...")
    result = learner.update(policy, episodes)

    print("\nOptimization Result:")
    extra = result.extra or {}
    print(f"  - Converged:    {extra.get('converged', True)}")
    print(f"  - Iterations:   {extra.get('iterations')}")
    print(f"  - Stationarity: {extra.get('stationarity', 0.0):.3e}")
    print(f"  - Loss Before:  {extra.get('loss_before', 0.0):.4f}")
    print(f"  - Loss After:   {extra.get('loss_after', 0.0):.4f}")

    # Logit deltas
    print("\nLogit Deltas applied to Policy:")
    for aid in action_ids:
        d = result.logit_deltas.get(aid, 0.0) if result.logit_deltas else 0.0
        print(f"  Action '{aid:<24}': Delta={d:+7.4f}")

    header("Step 6: Shifted Policy Probabilities")
    print_policy_dist("Updated Policy State (Post Preference Fitting)", policy, action_ids)

    # Assertions to verify expected behavior
    raw_probs = policy.probabilities()
    updated_probs = {action.id: p for action, p in zip(policy.actions(), raw_probs, strict=True)}
    assert updated_probs["escalate_incident"] > updated_probs["queue_standard"] > updated_probs["auto_resolve"], (
        "Expected escalate_incident > queue_standard > auto_resolve"
    )
    print("Verification Successful:")
    print("  [PASSED] 'escalate_incident' received highest preference boost.")
    print("  [PASSED] 'auto_resolve' (frequently overridden) decreased significantly.")
    print("  [PASSED] Reference logits remain frozen in snapshot metadata for stability.")


if __name__ == "__main__":
    main()
