"""Tests for evidence-gated autonomous decisions."""

from __future__ import annotations

import os

import pytest

from agent_learning.autonomy import (
    ComplexityProfile,
    assess_autonomy,
    assess_complexity,
    wilson_lower_bound,
)
from agent_learning.config import AutonomyConfig, validate_autonomy_monotonicity
from agent_learning.policy import SoftmaxPolicy
from agent_learning.storage import InMemoryStore
from agent_learning.training import LearningRunner
from agent_learning.types import Action, Episode, PolicySnapshot, Reward, RewardSource


def _policy(version: int, *, winner_logit: float = 2.0) -> PolicySnapshot:
    return PolicySnapshot(
        id=f"policy-{version}",
        agent_id="scout",
        task_id="choose-delegate",
        version=version,
        actions=[Action(id="winner"), Action(id="alternative")],
        logits={"winner": winner_logit, "alternative": 0.0},
        episodes_seen=version * 20,
        updates_applied=version,
        metadata={"policy_scope": "delegated_decision"},
    )


def _store_outcomes(store: InMemoryStore, count: int, *, reward: float = 0.7) -> None:
    for index in range(count):
        episode = Episode(
            id=f"episode-{index}",
            agent_id="scout",
            task_id="choose-delegate",
            intent_summary="Choose a delegate",
            action_id="winner",
            expected_outcome="Use the correct delegate",
            execution_status="completed",
            result_summary="The observable outcome supported the winner",
            metadata={"correct_action_id": "winner", "task_completed": True},
        )
        store.store_episode(episode)
        store.store_reward(
            Reward(
                episode_id=episode.id,
                agent_id=episode.agent_id,
                source=RewardSource.AGGREGATE,
                value=reward,
            )
        )


def test_wilson_lower_bound_requires_more_than_twenty_perfect_outcomes() -> None:
    assert wilson_lower_bound(20, 20) < 0.90
    assert wilson_lower_bound(40, 40) > 0.90


def test_autonomy_requires_all_evidence_gates() -> None:
    store = InMemoryStore()
    snapshot = _policy(1)
    store.store_policy(snapshot)
    _store_outcomes(store, 20)

    assessment = assess_autonomy(store, snapshot)

    assert not assessment.eligible
    assert assessment.criteria["minimum_outcomes"]["met"]
    assert not assessment.criteria["correctness_lower_bound"]["met"]
    assert not assessment.criteria["stable_snapshots"]["met"]


def test_autonomy_accepts_strong_stable_policy() -> None:
    store = InMemoryStore()
    for version in range(1, 4):
        store.store_policy(_policy(version))
    snapshot = store.get_active_policy("scout", "choose-delegate")
    assert snapshot is not None
    _store_outcomes(store, 40)

    assessment = assess_autonomy(store, snapshot)

    assert assessment.eligible
    assert assessment.recommended_action_id == "winner"
    assert assessment.scored_outcomes == 40
    assert assessment.correctness_evaluated == 40
    assert assessment.correctness_rate == 1.0
    assert assessment.correctness_lower_bound > 0.90
    assert assessment.mean_reward == pytest.approx(0.7)
    assert assessment.action_probability > 0.80
    assert assessment.probability_margin > 0.70
    assert assessment.stable_snapshots == 3
    assert all(item["met"] for item in assessment.criteria.values())


def test_observable_reward_drift_revokes_autonomy_without_correctness_labels() -> None:
    store = InMemoryStore()
    for version in range(1, 4):
        store.store_policy(_policy(version))
    snapshot = store.get_active_policy("scout", "choose-delegate")
    assert snapshot is not None
    _store_outcomes(store, 40)
    assert assess_autonomy(store, snapshot).eligible

    for index in range(50):
        episode = Episode(
            id=f"drift-{index}",
            agent_id="scout",
            task_id="choose-delegate",
            intent_summary="Choose a delegate",
            action_id="winner",
            expected_outcome="Complete the delegated task",
            execution_status="failed",
            result_summary="The automatic execution failed",
            metadata={"task_completed": False, "outcome_source": "observable"},
        )
        store.store_episode(episode)
        store.store_reward(
            Reward(
                episode_id=episode.id,
                agent_id=episode.agent_id,
                source=RewardSource.AGGREGATE,
                value=-0.8,
            )
        )

    assessment = assess_autonomy(store, snapshot)

    assert not assessment.eligible
    assert assessment.scored_outcomes == 90
    assert assessment.correctness_evaluated == 40
    assert assessment.correctness_lower_bound > 0.90
    assert assessment.mean_reward is not None and assessment.mean_reward < 0.0
    assert not assessment.criteria["positive_mean_reward"]["met"]


def test_autonomy_config_validates_thresholds() -> None:
    with pytest.raises(ValueError, match="audit_rate"):
        AutonomyConfig(audit_rate=1.1)


def test_complexity_profile_maps_intent_and_decision_dimensions() -> None:
    low = assess_complexity(
        ComplexityProfile(
            intent_ambiguity="low",
            context_variability="stable",
            outcome_observability="direct",
            decision_impact="low",
            reversibility="reversible",
        ),
        2,
    )
    standard = assess_complexity(ComplexityProfile(), 3, profile_source="default")
    high = assess_complexity(
        ComplexityProfile(
            intent_ambiguity="high",
            context_variability="dynamic",
            outcome_observability="subjective",
            decision_impact="medium",
            reversibility="costly",
        ),
        3,
    )
    critical = assess_complexity(
        ComplexityProfile(
            decision_impact="high",
            reversibility="irreversible",
        ),
        2,
    )

    assert low.tier == "low" and low.score == 0
    assert standard.tier == "standard" and standard.score == 6
    assert standard.profile_source == "default"
    assert high.tier == "high"
    assert "ambiguous_subjective_outcome" in high.risk_floors
    assert critical.tier == "critical"
    assert "high_impact_irreversible" in critical.risk_floors


def test_low_complexity_accepts_three_consistent_outcomes() -> None:
    store = InMemoryStore()
    snapshot = _policy(1)
    snapshot.metadata["complexity_profile"] = ComplexityProfile(
        intent_ambiguity="low",
        context_variability="stable",
        outcome_observability="direct",
        decision_impact="low",
        reversibility="reversible",
    ).to_dict()
    store.store_policy(snapshot)
    _store_outcomes(store, 3)

    assessment = assess_autonomy(store, snapshot)

    assert assessment.complexity.tier == "low"
    assert assessment.eligible
    assert assessment.criteria["minimum_outcomes"]["required"] == 3
    assert assessment.criteria["correctness_lower_bound"]["required"] == 0.40


def test_one_user_acceptance_grants_durable_autonomy() -> None:
    store = InMemoryStore()
    snapshot = _policy(1)
    store.store_policy(snapshot)
    store.store_episode(
        Episode(
            id="accepted-policy",
            agent_id="scout",
            task_id="choose-delegate",
            intent_summary="Choose a delegate",
            action_id="alternative",
            expected_outcome="Use the user's accepted delegate",
            execution_status="completed",
            result_summary="The user accepted the alternative",
            metadata={
                "feedback_status": "accepted",
                "correct_action_id": "alternative",
                "task_completed": True,
            },
        )
    )

    assessment = assess_autonomy(store, snapshot)

    assert assessment.eligible
    assert assessment.authorization_basis == "user_acceptance"
    assert assessment.user_feedback_status == "accepted"
    assert assessment.user_feedback_episode_id == "accepted-policy"
    assert assessment.recommended_action_id == "alternative"
    assert assessment.scored_outcomes == 0
    assert assessment.audit_rate == 0.0


def test_policy_metadata_keeps_acceptance_outside_episode_window() -> None:
    store = InMemoryStore()
    snapshot = _policy(1)
    snapshot.metadata["explicit_user_feedback"] = {
        "status": "accepted",
        "action_id": "alternative",
        "episode_id": "older-than-query-window",
        "recorded_at": "2026-08-09T10:00:00+00:00",
    }
    store.store_policy(snapshot)

    assessment = assess_autonomy(store, snapshot)

    assert assessment.eligible
    assert assessment.authorization_basis == "user_acceptance"
    assert assessment.recommended_action_id == "alternative"
    assert assessment.user_feedback_episode_id == "older-than-query-window"
    assert assessment.audit_rate == 0.0


def test_later_user_rejection_revokes_acceptance() -> None:
    store = InMemoryStore()
    snapshot = _policy(1)
    store.store_policy(snapshot)
    for episode_id, status, created_at in (
        ("accepted-policy", "accepted", "2026-08-09T10:00:00+00:00"),
        ("rejected-policy", "rejected", "2026-08-09T11:00:00+00:00"),
    ):
        store.store_episode(
            Episode(
                id=episode_id,
                agent_id="scout",
                task_id="choose-delegate",
                intent_summary="Choose a delegate",
                action_id="winner",
                expected_outcome="Use the user's chosen delegate",
                execution_status="completed",
                result_summary=f"The user {status} the recommendation",
                metadata={"feedback_status": status},
                created_at=created_at,
            )
        )

    assessment = assess_autonomy(store, snapshot)

    assert not assessment.eligible
    assert assessment.authorization_basis == "none"
    assert assessment.user_feedback_status == "rejected"
    assert assessment.user_feedback_episode_id == "rejected-policy"
    assert not assessment.criteria["latest_user_feedback_not_rejected"]["met"]


def test_newer_episode_rejection_overrides_persisted_acceptance() -> None:
    store = InMemoryStore()
    snapshot = _policy(1)
    snapshot.metadata["explicit_user_feedback"] = {
        "status": "accepted",
        "action_id": "winner",
        "episode_id": "accepted-policy",
        "recorded_at": "2026-08-09T10:00:00+00:00",
    }
    store.store_policy(snapshot)
    store.store_episode(
        Episode(
            id="rejected-policy",
            agent_id="scout",
            task_id="choose-delegate",
            intent_summary="Choose a delegate",
            action_id="winner",
            expected_outcome="Use the user's chosen delegate",
            execution_status="completed",
            result_summary="The user rejected the recommendation",
            metadata={"feedback_status": "rejected"},
            created_at="2026-08-09T11:00:00+00:00",
        )
    )

    assessment = assess_autonomy(store, snapshot)

    assert not assessment.eligible
    assert assessment.user_feedback_status == "rejected"
    assert assessment.user_feedback_episode_id == "rejected-policy"


def test_low_complexity_rejects_mixed_correctness_evidence() -> None:
    store = InMemoryStore()
    snapshot = _policy(1)
    snapshot.metadata["complexity_profile"] = ComplexityProfile(
        intent_ambiguity="low",
        context_variability="stable",
        outcome_observability="direct",
        decision_impact="low",
        reversibility="reversible",
    ).to_dict()
    store.store_policy(snapshot)
    _store_outcomes(store, 3)
    store.get_episode("episode-2", "scout").metadata["correct_action_id"] = (
        "alternative"
    )

    assessment = assess_autonomy(store, snapshot)

    assert not assessment.eligible
    assert not assessment.criteria["correctness_lower_bound"]["met"]


def test_pubsub_workload_recommendation_earns_autonomy_after_three_acceptances() -> None:
    store = InMemoryStore()
    policy = SoftmaxPolicy.from_actions(
        [
            Action(id="functions"),
            Action(id="container_apps"),
            Action(id="aks"),
        ],
        agent_id="scout",
        task_id="choose-azure-pubsub-message-processor",
    )
    snapshot = policy.snapshot()
    snapshot.metadata.update(
        {
            "policy_scope": "delegated_decision",
            "complexity_profile": ComplexityProfile(
                intent_ambiguity="low",
                context_variability="stable",
                outcome_observability="direct",
                decision_impact="low",
                reversibility="reversible",
            ).to_dict(),
        }
    )
    store.store_policy(snapshot)

    for index in range(3):
        episode = Episode(
            id=f"acceptance-{index}",
            agent_id="scout",
            task_id="choose-azure-pubsub-message-processor",
            intent_summary="Choose an Azure workload to process PubSub messages",
            action_id="functions",
            action_logprob=-1.386294,
            expected_outcome="Recommend the accepted workload",
            execution_status="completed",
            result_summary="The user accepted the Functions recommendation",
            metadata={"correct_action_id": "functions", "task_completed": True},
        )
        store.store_episode(episode)
        store.store_reward(
            Reward(
                episode_id=episode.id,
                agent_id=episode.agent_id,
                source=RewardSource.AGGREGATE,
                value=0.7,
            )
        )

    runner = LearningRunner(
        store=store,
        policy=SoftmaxPolicy.from_snapshot(snapshot),
        metrics=[],
    )
    runner.run_offline_batch(
        "scout",
        task_id="choose-azure-pubsub-message-processor",
        episode_limit=3,
        score_missing=False,
    )
    trained = store.get_active_policy(
        "scout", "choose-azure-pubsub-message-processor"
    )
    assert trained is not None

    assessment = assess_autonomy(store, trained)

    assert assessment.complexity.score == 1
    assert assessment.complexity.tier == "low"
    assert assessment.scored_outcomes == 3
    assert assessment.stable_snapshots == 1
    assert assessment.eligible


def test_same_evidence_requires_more_for_high_complexity() -> None:
    store = InMemoryStore()
    for version in range(1, 4):
        store.store_policy(_policy(version))
    snapshot = store.get_active_policy("scout", "choose-delegate")
    assert snapshot is not None
    _store_outcomes(store, 40)

    snapshot.metadata["complexity_profile"] = ComplexityProfile(
        intent_ambiguity="low",
        context_variability="stable",
        outcome_observability="direct",
        decision_impact="low",
        reversibility="reversible",
    ).to_dict()
    store.store_policy(snapshot)
    assert assess_autonomy(store, snapshot).eligible

    snapshot.metadata["complexity_profile"] = ComplexityProfile(
        intent_ambiguity="high",
        context_variability="dynamic",
        outcome_observability="subjective",
        decision_impact="high",
        reversibility="costly",
    ).to_dict()
    store.store_policy(snapshot)
    assessment = assess_autonomy(store, snapshot)

    assert assessment.complexity.tier == "high"
    assert not assessment.eligible
    assert assessment.criteria["minimum_outcomes"] == {
        "actual": 40,
        "required": 50,
        "met": False,
    }
    assert assessment.audit_rate == 0.25


def test_human_approval_profile_blocks_otherwise_eligible_policy() -> None:
    store = InMemoryStore()
    for version in range(1, 4):
        store.store_policy(_policy(version))
    snapshot = store.get_active_policy("scout", "choose-delegate")
    assert snapshot is not None
    _store_outcomes(store, 40)
    snapshot.metadata["complexity_profile"] = ComplexityProfile(
        intent_ambiguity="low",
        context_variability="stable",
        outcome_observability="direct",
        decision_impact="low",
        reversibility="reversible",
        requires_human_approval=True,
    ).to_dict()
    snapshot.metadata["explicit_user_feedback"] = {
        "status": "accepted",
        "action_id": "winner",
        "episode_id": "human-accepted-policy",
        "recorded_at": "2026-08-09T10:00:00+00:00",
    }
    store.store_policy(snapshot)

    assessment = assess_autonomy(store, snapshot)

    assert not assessment.eligible
    assert assessment.authorization_basis == "none"
    assert assessment.user_feedback_status == "accepted"
    assert not assessment.criteria["human_approval_not_required"]["met"]


def test_complexity_profile_rejects_unknown_fields() -> None:
    with pytest.raises(ValueError, match="unknown complexity profile fields"):
        ComplexityProfile.from_dict({"intent_complexity": "low"})


# ---------------------------------------------------------------------------
# Story 3.1 contract: tier-specific overrides and authority-aware reporting.
#
# Story 3.1 (docs/user-stories/epic-3-tier-specific-autonomy-overrides.md)
# ADR-003 s3, s4.5, s6, s7 (Invariants 5 and 7)
# BRD-003 / FDD-003 (Designs 1 to 3)
#
# Interpretations not stated verbatim in the acceptance criteria (LL-011):
# - I1: an invalid tier-suffixed value falls through to the global variable, then
#   the built-in default, matching the lenient behavior of the existing _env_int.
# - I2: validate_autonomy_monotonicity() checks all six statistical entry gates
#   (ADR-003 Invariant 5), not only the three listed in FDD-003 Design 2.
# - I3: assess_autonomy() runs the monotonicity check when it resolves its own
#   config (FDD-003: "before policy initialization or decision execution").
# - I4: for a full-authority policy, eligibility comes only from explicit
#   adjudication and requires_human_approval (FDD-003 Design 3, item 4); the
#   frozen-logit statistical path does not grant autonomy.
# ---------------------------------------------------------------------------

_TIERS = ("low", "standard", "high", "critical")


def _clear_autonomy_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in list(os.environ):
        if name.startswith("AGENT_LEARNING_AUTONOMY_"):
            monkeypatch.delenv(name)


def test_ac0_tier_suffixed_variable_takes_precedence_over_global_and_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC_0: AGENT_LEARNING_AUTONOMY_{METRIC}_{TIER} > global variable > default."""
    _clear_autonomy_env(monkeypatch)
    monkeypatch.setenv("AGENT_LEARNING_AUTONOMY_MIN_OUTCOMES", "9")
    monkeypatch.setenv("AGENT_LEARNING_AUTONOMY_MIN_OUTCOMES_STANDARD", "7")

    assert AutonomyConfig.for_tier("standard").min_outcomes == 7
    assert AutonomyConfig.for_tier("high").min_outcomes == 9

    monkeypatch.delenv("AGENT_LEARNING_AUTONOMY_MIN_OUTCOMES")
    monkeypatch.delenv("AGENT_LEARNING_AUTONOMY_MIN_OUTCOMES_STANDARD")
    assert AutonomyConfig.for_tier("high").min_outcomes == 50


def test_ac0_float_metrics_resolve_with_tier_suffix(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC_0: every metric, including float ones, resolves its tier-suffixed variable."""
    _clear_autonomy_env(monkeypatch)
    monkeypatch.setenv("AGENT_LEARNING_AUTONOMY_MIN_CORRECTNESS_LOWER_BOUND_HIGH", "0.96")
    monkeypatch.setenv("AGENT_LEARNING_AUTONOMY_STABLE_SNAPSHOTS_CRITICAL", "6")

    assert AutonomyConfig.for_tier("high").min_correctness_lower_bound == pytest.approx(0.96)
    assert AutonomyConfig.for_tier("critical").stable_snapshots == 6
    assert AutonomyConfig.for_tier("standard").min_correctness_lower_bound == pytest.approx(0.90)


def test_ac0_invalid_tier_value_falls_through_to_global(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC_0 (interpretation I1): an unparseable tier value is ignored, as _env_int does."""
    _clear_autonomy_env(monkeypatch)
    monkeypatch.setenv("AGENT_LEARNING_AUTONOMY_MIN_OUTCOMES_LOW", "many")
    monkeypatch.setenv("AGENT_LEARNING_AUTONOMY_MIN_OUTCOMES", "4")

    assert AutonomyConfig.for_tier("low").min_outcomes == 4


def test_ac1_low_tier_override_preserves_other_tiers(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC_1: MIN_OUTCOMES_LOW=5 sets low to 5; standard, high, critical keep 20, 50, 100."""
    _clear_autonomy_env(monkeypatch)
    monkeypatch.setenv("AGENT_LEARNING_AUTONOMY_MIN_OUTCOMES_LOW", "5")

    assert [AutonomyConfig.for_tier(tier).min_outcomes for tier in _TIERS] == [5, 20, 50, 100]


@pytest.mark.parametrize(
    ("metric", "attr", "low_value"),
    [
        ("MIN_OUTCOMES", "min_outcomes", "30"),
        ("MIN_CORRECTNESS_LOWER_BOUND", "min_correctness_lower_bound", "0.95"),
        ("MIN_MEAN_REWARD", "min_mean_reward", "0.05"),
        ("MIN_ACTION_PROBABILITY", "min_action_probability", "0.7"),
        ("MIN_PROBABILITY_MARGIN", "min_probability_margin", "0.2"),
        ("STABLE_SNAPSHOTS", "stable_snapshots", "4"),
    ],
)
def test_ac2_monotonicity_names_inverted_metric_and_tiers(
    monkeypatch: pytest.MonkeyPatch, metric: str, attr: str, low_value: str
) -> None:
    """AC_2 (interpretation I2): low stricter than standard is rejected for all six gates."""
    _clear_autonomy_env(monkeypatch)
    monkeypatch.setenv(f"AGENT_LEARNING_AUTONOMY_{metric}_LOW", low_value)

    with pytest.raises(ValueError, match=rf"monotonicity.*{attr}.*low.*standard"):
        validate_autonomy_monotonicity()


def test_ac2_monotonicity_accepts_defaults_and_equal_thresholds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC_2: defaults, and a global override that makes tiers equal, are not violations."""
    _clear_autonomy_env(monkeypatch)
    validate_autonomy_monotonicity()

    monkeypatch.setenv("AGENT_LEARNING_AUTONOMY_MIN_OUTCOMES", "10")
    validate_autonomy_monotonicity()


def test_ac2_monotonicity_checks_the_upper_tier_pairs(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC_2: all four tiers are compared, including high against critical."""
    _clear_autonomy_env(monkeypatch)
    monkeypatch.setenv("AGENT_LEARNING_AUTONOMY_MIN_OUTCOMES_HIGH", "150")

    with pytest.raises(ValueError, match=r"min_outcomes.*high.*critical"):
        validate_autonomy_monotonicity()


def test_ac2_assess_autonomy_rejects_inverted_thresholds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC_2 (interpretation I3): assessing with an env-resolved config validates it first."""
    _clear_autonomy_env(monkeypatch)
    monkeypatch.setenv("AGENT_LEARNING_AUTONOMY_MIN_OUTCOMES_LOW", "500")
    store = InMemoryStore()
    snapshot = _policy(1)
    store.store_policy(snapshot)

    with pytest.raises(ValueError, match="monotonicity"):
        assess_autonomy(store, snapshot)


def _full_authority_policy(version: int = 1, **metadata: object) -> PolicySnapshot:
    snapshot = _policy(version, winner_logit=0.0)
    snapshot.metadata["decision_authority"] = "full"
    snapshot.metadata.update(metadata)
    return snapshot


def _accepted_episode(episode_id: str) -> Episode:
    return Episode(
        id=episode_id,
        agent_id="scout",
        task_id="choose-delegate",
        intent_summary="Choose a delegate",
        action_id="winner",
        expected_outcome="Use the accepted delegate",
        execution_status="completed",
        result_summary="The user accepted the winner",
        metadata={"feedback_status": "accepted", "correct_action_id": "winner"},
    )


def test_ac3_full_authority_reports_probability_criteria_as_not_applicable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC_3: action_probability and probability_margin are not_applicable and met."""
    _clear_autonomy_env(monkeypatch)
    store = InMemoryStore()
    snapshot = _full_authority_policy()
    store.store_policy(snapshot)

    assessment = assess_autonomy(store, snapshot)

    for name in ("action_probability", "probability_margin"):
        criterion = assessment.criteria[name]
        assert criterion["status"] == "not_applicable"
        assert criterion["met"] is True
        assert criterion["required"] is None
        assert "ADR-003" in criterion["reason"]
    assert assessment.criteria["action_probability"]["actual"] == pytest.approx(0.5)
    assert assessment.authorization_basis == "human_adjudication"


def test_ac3_full_authority_eligibility_comes_only_from_adjudication(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC_3 (interpretation I4): statistics never grant a full-authority policy autonomy."""
    _clear_autonomy_env(monkeypatch)
    store = InMemoryStore()
    for version in range(1, 4):
        strong = _policy(version)
        strong.metadata["decision_authority"] = "full"
        store.store_policy(strong)
    snapshot = store.get_active_policy("scout", "choose-delegate")
    assert snapshot is not None
    _store_outcomes(store, 40)

    assessment = assess_autonomy(store, snapshot)

    assert not assessment.eligible
    assert assessment.authorization_basis == "human_adjudication"

    store.store_episode(_accepted_episode("accepted-full"))
    accepted = assess_autonomy(store, snapshot)
    assert accepted.eligible
    assert accepted.authorization_basis == "human_adjudication"


def test_ac3_full_authority_human_approval_requirement_still_blocks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC_3: requires_human_approval stays absolute for full authority (ADR-003 Invariant 6)."""
    _clear_autonomy_env(monkeypatch)
    store = InMemoryStore()
    snapshot = _full_authority_policy(
        complexity_profile=ComplexityProfile(requires_human_approval=True).to_dict()
    )
    store.store_policy(snapshot)
    store.store_episode(_accepted_episode("accepted-blocked"))

    assessment = assess_autonomy(store, snapshot)

    assert not assessment.eligible
    assert assessment.criteria["human_approval_not_required"]["met"] is False
    assert assessment.authorization_basis == "human_adjudication"


def test_ac4_low_authority_statistical_gates_are_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC_4: low-authority policies evaluate the probability gates exactly as before."""
    _clear_autonomy_env(monkeypatch)
    store = InMemoryStore()
    for version in range(1, 4):
        store.store_policy(_policy(version))
    snapshot = store.get_active_policy("scout", "choose-delegate")
    assert snapshot is not None
    _store_outcomes(store, 40)

    assessment = assess_autonomy(store, snapshot)

    assert assessment.eligible
    assert assessment.authorization_basis == "statistical_evidence"
    for name in ("action_probability", "probability_margin"):
        assert "status" not in assessment.criteria[name]
        assert assessment.criteria[name]["required"] is not None

    weak = _policy(1, winner_logit=0.0)
    weak_store = InMemoryStore()
    weak_store.store_policy(weak)
    weak_assessment = assess_autonomy(weak_store, weak)
    assert weak_assessment.criteria["action_probability"]["met"] is False
