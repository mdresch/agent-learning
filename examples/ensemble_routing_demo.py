"""Demonstration: Contextual Authority Ensemble Routing (ADR-021 / Epic 21).

Run this file with:
    uv run python examples/ensemble_routing_demo.py

This walkthrough illustrates:
1. Uncertainty signals: Shannon entropy (in bits) and decision margin.
2. Deadband hysteresis routing: preventing decision flapping across thresholds.
3. Safety-critical task pinning: high-risk actions hard-pinned to FULL authority
   (cannot be automated regardless of model confidence).
4. Dynamic policy dispatch: policy_for_route() with snapshot immutability.
5. Gradient exclusion: full-routed (reasoned) episodes are excluded from training
   so expert manual decisions never contaminate the learned policy.
"""

from __future__ import annotations

import random

from agent_learning.policy.softmax_bandit import SoftmaxPolicy
from agent_learning.types import Action, Episode, PolicySnapshot, Reward, RewardSource
from agent_learning_ext.decision import DecisionAuthority
from agent_learning_ext.learners.reinforce import ReinforceLearner
from agent_learning_ext.routing import (
    PINNED_FULL,
    RouteDecision,
    RoutingConfig,
    entropy_bits,
    margin,
    policy_for_route,
    route,
)


def header(title: str) -> None:
    print(f"\n{'=' * 78}")
    print(f"  {title}")
    print(f"{'=' * 78}\n")


def subheader(title: str) -> None:
    print(f"\n--- {title} ---")


def demo_signals() -> None:
    header("Step 1: Uncertainty Signals (Shannon Entropy & Margin)")
    print("The router measures decision certainty via two complementary signals:")
    print("  - Shannon Entropy (bits): H(p) = -sum(p * log2(p)). Lower = more peaked/certain.")
    print("  - Decision Margin: difference between top two probabilities. Higher = clearer lead.\n")

    cases = [
        ("Decisive confidence (95% / 5%)", [0.95, 0.05]),
        ("Moderate confidence (80% / 20%)", [0.80, 0.20]),
        ("Borderline split (60% / 30% / 10%)", [0.60, 0.30, 0.10]),
        ("Thin margin (45% / 40% / 15%)", [0.45, 0.40, 0.15]),
        ("Complete uncertainty (50% / 50%)", [0.50, 0.50]),
        ("Maximum entropy uniform (4 options)", [0.25, 0.25, 0.25, 0.25]),
    ]

    print(f"{'Scenario':<38} | {'Probabilities':<20} | {'Entropy (bits)':<14} | {'Margin':<8}")
    print(f"{'-' * 38}-+-{'-' * 20}-+-{'-' * 14}-+-{'-' * 8}")
    for label, probs in cases:
        h = entropy_bits(probs)
        m = margin(probs)
        p_str = str(probs)
        print(f"{label:<38} | {p_str:<20} | {h:<14.4f} | {m:<8.4f}")


def demo_hysteresis() -> None:
    header("Step 2: Hysteresis Deadband Routing (Anti-Flapping)")
    print("A single threshold causes oscillating routes ('hunting') near the boundary.")
    print("Epic 21 defines a dual-threshold deadband [tau_deesc, tau_esc] with margin guard:\n")

    cfg = RoutingConfig(tau_esc=1.00, tau_deesc=0.70, eps_margin=0.20)
    print(f"  RoutingConfig: tau_esc={cfg.tau_esc} bits, tau_deesc={cfg.tau_deesc} bits, eps_margin={cfg.eps_margin}")
    print("  Rules:")
    print("    - Entropy >= 1.00 bits OR margin < 0.20 -> Escalate to FULL authority")
    print("    - Entropy <= 0.70 bits AND approved bucket -> De-escalate to LOW authority")
    print("    - Inside deadband (0.70 to 1.00 bits) -> Keep PREVIOUS route (prevents flapping)\n")

    simulation_stream = [
        ("Clear request", [0.95, 0.05], None),
        ("Slight drift into deadband", [0.80, 0.20], None),  # 0.7219 bits
        ("Uncertain request", [0.55, 0.45], None),          # 0.9928 bits, thin margin
        ("Borderline in deadband again", [0.80, 0.20], None),
        ("Decisive request", [0.92, 0.08], None),
    ]

    current_route = None
    print(f"{'Step':<5} | {'Stream Input':<30} | {'Entropy':<8} | {'Margin':<8} | {'Prev Route':<10} | {'Routed To':<10} | {'Reason'}")
    print(f"{'-' * 5}-+-{'-' * 30}-+-{'-' * 8}-+-{'-' * 8}-+-{'-' * 10}-+-{'-' * 10}-+-{'-' * 15}")

    for idx, (desc, probs, _) in enumerate(simulation_stream, start=1):
        decision: RouteDecision = route(
            probs=probs,
            tier="standard",
            task_id="classify-support-ticket",
            previous=current_route,
            approved_for_low=True,
            cfg=cfg,
        )
        h = entropy_bits(probs)
        m = margin(probs)
        prev_str = current_route or "None"
        new_route_str = decision.authority.value.upper()
        print(f"{idx:<5} | {desc:<30} | {h:<8.3f} | {m:<8.3f} | {prev_str:<10} | {new_route_str:<10} | {decision.reason}")
        current_route = decision.authority.value


def demo_pinned_gates() -> None:
    header("Step 3: Safety-Critical Task Pinning (Refusal of Automated Low Authority)")
    print("In production systems, high-risk operational tasks (e.g. fund transfers,")
    print("compliance sign-offs, production deploys) must NEVER be automated without human oversight.")
    print("The router enforces this via PINNED_FULL, refusing down-routing to LOW.")
    print(f"Total hard-pinned tasks: {len(PINNED_FULL)}")
    print(f"Examples: {list(PINNED_FULL[:5])} ...\n")

    cfg = RoutingConfig(tau_esc=1.00, tau_deesc=0.70, eps_margin=0.20)
    confident_probs = [0.999, 0.001]  # Almost 0 entropy, 0.998 margin!

    print(f"Testing confident distribution {confident_probs} on pinned gates:")
    for gate in ["approve-adr", "approve-brd", "approve-fdd", "approve-user-stories"]:
        decision = route(
            probs=confident_probs,
            tier="low",
            task_id=gate,
            previous="low",
            approved_for_low=True,
            cfg=cfg,
        )
        print(f"  Task: {gate:<22} -> Route: {decision.authority.value.upper():<5} (reason: {decision.reason})")

    # Demonstrating custom task pinning for adopters without our internal governance framework:
    custom_task = "execute_wire_transfer"
    custom_decision = route(
        probs=confident_probs,
        tier="low",
        task_id=custom_task,
        previous="low",
        approved_for_low=True,
        requires_human_approval=True,
        cfg=cfg,
    )
    print(f"  Custom Adopter Task: {custom_task:<15} -> Route: {custom_decision.authority.value.upper():<5} (reason: {custom_decision.reason})")

    # Down-routing refusal via policy_for_route
    snap = PolicySnapshot(
        id="pinned-snap-1",
        agent_id="safety-gate-agent",
        task_id="approve-adr",
        version=1,
        actions=[Action(id="approve", description="Approve"), Action(id="reject", description="Reject")],
        logits={"approve": 5.0, "reject": -5.0},
        metadata={"decision_authority": "full"},
    )
    try:
        policy_for_route(snap, DecisionAuthority.LOW)
    except ValueError as exc:
        print("\nSafety contract verified:")
        print(f"  Attempting down-route on '{snap.task_id}' raised ValueError: {exc}")


def demo_gradient_exclusion() -> None:
    header("Step 4: Training Gradient Exclusion (Reasoning vs Learning Boundary)")
    print("When a request routes to FULL authority, the final decision is made by reasoning")
    print("(e.g. human expert or high-tier model), NOT sampled from the policy.")
    print("Training on full-routed decisions would cause policy gradients to optimize over")
    print("decisions the policy never actually generated, corrupting learned weights.\n")

    actions = [Action(id="action_a", description="Option A"), Action(id="action_b", description="Option B")]
    snap = PolicySnapshot(
        id="policy-demo",
        agent_id="triage-agent",
        task_id="triage",
        version=1,
        actions=actions,
        logits={"action_a": 0.0, "action_b": 0.0},
        metadata={"decision_authority": "low"},
    )
    policy = SoftmaxPolicy(snap, rng=random.Random(42))
    initial_probs = policy.probabilities()
    print(f"Initial policy probabilities: action_a={initial_probs[0]:.3f}, action_b={initial_probs[1]:.3f}\n")

    # Construct episodes:
    # 2 LOW-routed episodes (sampled from policy -> valid training data)
    # 2 FULL-routed episodes (reasoned -> must be excluded from gradient)
    episodes = [
        Episode(
            id="ep-low-1",
            agent_id="triage-agent",
            action_id="action_a",
            action_logprob=-0.693,
            metadata={"routed_authority": "low", "feedback_status": "accepted"},
        ),
        Episode(
            id="ep-low-2",
            agent_id="triage-agent",
            action_id="action_a",
            action_logprob=-0.693,
            metadata={"routed_authority": "low", "feedback_status": "accepted"},
        ),
        Episode(
            id="ep-full-1",
            agent_id="triage-agent",
            action_id="action_b",  # Reasoned decision chose B
            action_logprob=-0.693,
            metadata={"routed_authority": "full", "feedback_status": "accepted"},
        ),
        Episode(
            id="ep-full-2",
            agent_id="triage-agent",
            action_id="action_b",
            action_logprob=-0.693,
            metadata={"routed_authority": "full", "feedback_status": "accepted"},
        ),
    ]

    rewards = [Reward(episode_id=ep.id, value=1.0, source=RewardSource.AGGREGATE) for ep in episodes]

    learner = ReinforceLearner()
    print("Executing ReinforceLearner.update() over the batch (2 LOW + 2 FULL episodes)...")
    result = learner.update(policy, episodes, rewards)

    print("Update Result:")
    print(f"  - Total episodes in batch:      {len(episodes)}")
    print(f"  - Episodes used in gradients:   {result.episodes_used} (the 2 LOW episodes)")
    print(f"  - Full-authority excluded:      {result.extra.get('full_authority_excluded')} (the 2 FULL episodes)")

    updated_probs = policy.probabilities()
    print(f"  - Updated probabilities:        action_a={updated_probs[0]:.3f}, action_b={updated_probs[1]:.3f}")
    print("\nObservation: action_a probability increased because only LOW episodes were trained on.")
    print("Reasoned FULL decisions were cleanly excluded, preserving policy learning integrity.")


def main() -> None:
    print("\n" + "#" * 78)
    print("  AGENT LEARNING EXTENSIONS - ENSEMBLE ROUTING DEMO (Epic 21)")
    print("#" * 78)
    demo_signals()
    demo_hysteresis()
    demo_pinned_gates()
    demo_gradient_exclusion()
    header("Demo Complete")
    print("Contextual Authority Ensemble Routing operational in agent_learning_ext.routing!\n")


if __name__ == "__main__":
    main()
