"""Demonstration: Category-Level Escalation Learning (Methodology #21 / ADR-007).

Run this file with:
    python examples/category_escalation_demo.py

Architecture Overview:
1. The Governance Fatigue Problem (HYP-AL-007):
   - Uniform escalation rules fail in enterprise environments:
     (a) Escalate everything to humans -> Review fatigue, slow releases, ignored alerts.
     (b) Act silently everywhere -> Severe risk of undetected schema or security regressions.
     (c) Static hardcoded rules -> Brittle, failing to adapt to historical defect rates.
2. 4-Tier Enterprise Escalation Taxonomy:
   - ACT_SILENTLY: Autonomous execution; zero alerts or interruptions.
   - NOTIFY: Asynchronous broadcast to Slack/Teams/log; non-blocking.
   - ESCALATE_TO_MANAGER: Synchronous gate; operational team manager must sign off.
   - ESCALATE_TO_EXECUTIVE: High-stakes gate; VP/Director/Compliance board approval required.
3. Category-Specific Policy Partitioning:
   - We evaluate four distinct operational categories:
     * Category 1: Documentation & Cosmetic (Low risk -> optimal: ACT_SILENTLY)
     * Category 2: Dependency Patch (Operational maintenance -> optimal: NOTIFY)
     * Category 3: Schema & Business Logic (Medium/High operational risk -> optimal: ESCALATE_TO_MANAGER)
     * Category 4: Security & Sovereign Keying (Critical corporate risk -> optimal: ESCALATE_TO_EXECUTIVE)
4. Policy Gradient Optimization:
   - Uses ReinforceLearner to learn optimal escalation tiers by balancing review overhead
     costs against regression blast radius.
"""

from __future__ import annotations

import copy
import math
import random
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from agent_learning.config import LearnerConfig
from agent_learning.learners import ReinforceLearner
from agent_learning.policy import SoftmaxPolicy
from agent_learning.types import (
    Action,
    Episode,
    PolicySnapshot,
    Reward,
    RewardSource,
)


def header(title: str) -> None:
    print(f"\n{'=' * 78}")
    print(f"  {title}")
    print(f"{'=' * 78}\n")


# 4-Tier Escalation Actions
ACT_SILENTLY: str = "act_silently"
NOTIFY: str = "notify"
ESCALATE_TO_MANAGER: str = "escalate_to_manager"
ESCALATE_TO_EXECUTIVE: str = "escalate_to_executive"

GOVERNANCE_TIERS: tuple[str, ...] = (
    ACT_SILENTLY,
    NOTIFY,
    ESCALATE_TO_MANAGER,
    ESCALATE_TO_EXECUTIVE,
)


@dataclass(frozen=True)
class CategoryProfile:
    id: str
    name: str
    description: str
    # Ground truth outcome rewards for simulation: balances review cost vs defect penalty
    # Reward in [-1.0, +1.0]
    expected_rewards: dict[str, float]


CATEGORIES: list[CategoryProfile] = [
    CategoryProfile(
        id="cat_cosmetic_docs",
        name="Documentation & Typo Corrections",
        description="Markdown fixes, typo corrections, comments, and README updates.",
        expected_rewards={
            ACT_SILENTLY: 0.85,             # Fast, zero interruption, safe
            NOTIFY: 0.40,                   # Harmless, slight notification noise
            ESCALATE_TO_MANAGER: -0.40,     # Wastes manager's time on trivial fixes
            ESCALATE_TO_EXECUTIVE: -0.90,   # Massive executive alert fatigue
        },
    ),
    CategoryProfile(
        id="cat_dependency_patch",
        name="Patch Dependency Bumps",
        description="Routine minor/patch dependency bumps with passing automated tests.",
        expected_rewards={
            ACT_SILENTLY: 0.20,             # Slightly risky if upstream regression occurs
            NOTIFY: 0.85,                   # Sweet spot: team informed via asynchronous alert
            ESCALATE_TO_MANAGER: -0.15,     # Unnecessary review bottleneck
            ESCALATE_TO_EXECUTIVE: -0.80,   # Severe over-escalation
        },
    ),
    CategoryProfile(
        id="cat_schema_business_logic",
        name="Database Schema & Settlement Logic",
        description="Relational table migrations, transaction flow changes, billing math.",
        expected_rewards={
            ACT_SILENTLY: -0.85,            # Catastrophic: silent schema corruption risk
            NOTIFY: -0.30,                  # Asynchronous notice insufficient to stop errors
            ESCALATE_TO_MANAGER: 0.90,      # Optimal: operational manager verifies invariants
            ESCALATE_TO_EXECUTIVE: 0.10,    # Acceptable for major shifts, but slows sprint
        },
    ),
    CategoryProfile(
        id="cat_security_sovereignty",
        name="Cryptographic Keys & Sovereign Routing",
        description="Threshold secret sharing topologies, cross-border jurisdictional routing.",
        expected_rewards={
            ACT_SILENTLY: -1.00,            # Unacceptable: statutory non-compliance violation
            NOTIFY: -0.70,                  # Inadequate: post-facto audit failure
            ESCALATE_TO_MANAGER: 0.20,      # Good, but manager lacks statutory sign-off authority
            ESCALATE_TO_EXECUTIVE: 0.95,    # Optimal: corporate compliance / VP approval required
        },
    ),
]


def build_initial_policy(category_id: str) -> PolicySnapshot:
    """Builds an uncalibrated policy with uniform logits across the 4 escalation tiers."""
    actions = [Action(id=a) for a in GOVERNANCE_TIERS]
    return PolicySnapshot(
        id=f"policy-escalate-{category_id}-v1",
        agent_id="enterprise-governor",
        task_id=f"escalate-{category_id}",
        version=1,
        actions=actions,
        logits={a.id: 0.0 for a in actions},  # Equal 25% distribution
        updates_applied=0,
        metadata={"category_id": category_id},
    )


def simulate_environment_reward(category: CategoryProfile, action_id: str, rng: random.Random) -> float:
    """Simulates real-world noisy feedback reflecting review cost vs defect protection."""
    mean_val = category.expected_rewards[action_id]
    noise = rng.gauss(0.0, 0.12)
    return max(-1.0, min(1.0, mean_val + noise))


def run_single_category_walkthrough(category: CategoryProfile) -> None:
    header(f"WALKTHROUGH: {category.name.upper()} ({category.id})")
    print(f"Description: {category.description}")
    print("\nExpected Utility Rubric (Review Cost vs Defect Risk):")
    for action_id, expected_r in category.expected_rewards.items():
        print(f"  * {action_id:<24} -> Net Reward: {expected_r:+.2f}")

    rng = random.Random(42)
    snapshot = build_initial_policy(category.id)
    policy = SoftmaxPolicy(snapshot)
    learner = ReinforceLearner(LearnerConfig(learning_rate=0.45, entropy_bonus=0.02))

    actions = policy.actions()

    def format_probs(p_list: Sequence[float]) -> str:
        return " | ".join(f"{a.id.split('_')[-1]}: {p*100:.1f}%" for a, p in zip(actions, p_list))

    print(f"\nInitial Uniform Probabilities: {format_probs(policy.probabilities())}")

    print("\nRunning 10 Policy Gradient Rounds (20 episodes per round)...")
    for r_idx in range(1, 11):
        episodes: list[Episode] = []
        rewards: list[Reward] = []

        for e_idx in range(20):
            probs = policy.probabilities()
            chosen_idx = rng.choices(range(len(actions)), weights=probs)[0]
            chosen_action = actions[chosen_idx]

            reward_val = simulate_environment_reward(category, chosen_action.id, rng)

            snap = policy.snapshot()
            ep_id = f"ep-{category.id}-r{r_idx}-e{e_idx}"
            episodes.append(
                Episode(
                    id=ep_id,
                    agent_id=snap.agent_id,
                    task_id=snap.task_id,
                    intent_summary=f"Determine governance tier for {category.name}",
                    action_id=chosen_action.id,
                    expected_outcome="Optimal escalation balance",
                    execution_status="completed",
                    result_summary=f"Tier {chosen_action.id} yielded reward {reward_val:+.2f}",
                    created_at="2026-11-11T00:00:00+00:00",
                )
            )
            rewards.append(
                Reward(
                    id=f"rw-{ep_id}",
                    episode_id=ep_id,
                    source=RewardSource.AGGREGATE,
                    value=reward_val,
                    created_at="2026-11-11T00:00:00+00:00",
                )
            )

        learner.update(policy, episodes, rewards)
        print(f"  Round {r_idx:02d}: {format_probs(policy.probabilities())}")

    final_probs = {a.id: p for a, p in zip(actions, policy.probabilities())}
    winner = max(final_probs.items(), key=lambda x: x[1])
    print(f"\nConverged Dominant Tier: '{winner[0]}' ({winner[1]*100:.1f}% confidence)")


def run_full_enterprise_benchmark() -> None:
    header("PHASE 2: MULTI-CATEGORY ENTERPRISE BENCHMARK (HYP-AL-007)")
    print("Evaluating automated convergence across all 4 enterprise change categories:")
    print("Goal: Verify that each category autonomously converges to its specialized optimal tier.\n")

    summary_table: list[dict[str, Any]] = []

    for cat in CATEGORIES:
        rng = random.Random(1337)
        snapshot = build_initial_policy(cat.id)
        policy = SoftmaxPolicy(snapshot)
        learner = ReinforceLearner(LearnerConfig(learning_rate=0.45, entropy_bonus=0.01))
        actions = policy.actions()

        for _ in range(14):  # 14 rounds x 25 episodes
            episodes: list[Episode] = []
            rewards: list[Reward] = []
            for e_idx in range(25):
                probs = policy.probabilities()
                chosen_idx = rng.choices(range(len(actions)), weights=probs)[0]
                action = actions[chosen_idx]
                r_val = simulate_environment_reward(cat, action.id, rng)

                snap = policy.snapshot()
                ep_id = f"sim-{cat.id}-{e_idx}"
                episodes.append(
                    Episode(
                        id=ep_id,
                        agent_id=snap.agent_id,
                        task_id=snap.task_id,
                        intent_summary=f"Escalate {cat.name}",
                        action_id=action.id,
                        expected_outcome="Balance speed and review",
                        execution_status="completed",
                        result_summary="Simulation run",
                        created_at="2026-11-11T00:00:00+00:00",
                    )
                )
                rewards.append(
                    Reward(
                        id=f"rw-{ep_id}",
                        episode_id=ep_id,
                        source=RewardSource.AGGREGATE,
                        value=r_val,
                        created_at="2026-11-11T00:00:00+00:00",
                    )
                )
            learner.update(policy, episodes, rewards)

        final_p = {a.id: p for a, p in zip(actions, policy.probabilities())}
        best_tier, best_prob = max(final_p.items(), key=lambda x: x[1])
        target_optimal = max(cat.expected_rewards.items(), key=lambda x: x[1])[0]

        summary_table.append({
            "category": cat.name,
            "learned_tier": best_tier,
            "confidence": best_prob,
            "target_optimal": target_optimal,
            "match": best_tier == target_optimal,
            "distribution": final_p,
        })

    print(f"{'Category':<36} {'Optimal Tier':<24} {'Learned Dominant Tier':<24} {'Confidence'}")
    print(f"{'-' * 34}   {'-' * 22}   {'-' * 22}   {'-' * 12}")
    for row in summary_table:
        status_flag = "MATCH" if row["match"] else "MISMATCH"
        print(
            f"{row['category']:<36} "
            f"{row['target_optimal']:<24} "
            f"{row['learned_tier']:<24} "
            f"{row['confidence']*100:5.1f}% [{status_flag}]"
        )

    all_matched = all(r["match"] for r in summary_table)
    print("\nFALSIFICATION CONCLUSION (HYP-AL-007):")
    print("  Hypothesis: 'Category-level policy gradient learning converges to differentiated,")
    print("               cost-optimal escalation tiers without manual threshold tuning.'")
    print(f"  Status: {'CONFIRMED (100% convergence across all categories)' if all_matched else 'FALSIFIED'}")


def main() -> None:
    # Walk through the schema business logic category in detail
    schema_cat = next(c for c in CATEGORIES if c.id == "cat_schema_business_logic")
    run_single_category_walkthrough(schema_cat)

    # Run enterprise-wide multi-category benchmark
    run_full_enterprise_benchmark()


if __name__ == "__main__":
    main()
