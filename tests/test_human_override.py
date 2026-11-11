"""Tests for Methodology #06: Durable Explicit Human Override & Autonomous Delegation."""

from __future__ import annotations

import copy
from agent_learning.autonomy import ComplexityProfile, assess_autonomy
from agent_learning.storage import InMemoryStore
from agent_learning.types import Action, Episode, PolicySnapshot
from examples.human_override_demo import (
    AGENT_ID,
    TASK_ID,
    build_base_policy,
    make_feedback_episode,
)


def test_cold_policy_defaults_to_supervised_ineligible():
    store = InMemoryStore()
    policy = build_base_policy()
    store.store_policy(policy)

    assessment = assess_autonomy(store, policy)
    assert not assessment.eligible
    assert assessment.authorization_basis == "none"
    assert assessment.audit_rate == 0.10


def test_explicit_acceptance_grants_autonomy_and_suppresses_audits():
    store = InMemoryStore()
    policy = build_base_policy()
    store.store_policy(policy)

    ep = make_feedback_episode(
        episode_id="ep-accept-001",
        action_id="aws_frankfurt_sovereign",
        feedback_status="accepted",
        created_at="2026-11-10T12:00:00+00:00",
    )
    store.store_episode(ep)

    assessment = assess_autonomy(store, policy)
    assert assessment.eligible
    assert assessment.authorization_basis == "user_acceptance"
    assert assessment.recommended_action_id == "aws_frankfurt_sovereign"
    assert assessment.user_feedback_status == "accepted"
    assert assessment.audit_rate == 0.0


def test_override_is_durable_via_policy_metadata():
    store = InMemoryStore()
    policy = build_base_policy()
    policy.metadata["explicit_user_feedback"] = {
        "status": "accepted",
        "action_id": "aws_frankfurt_sovereign",
        "episode_id": "older-than-window",
        "recorded_at": "2026-11-10T10:00:00+00:00",
    }
    store.store_policy(policy)

    assessment = assess_autonomy(store, policy)
    assert assessment.eligible
    assert assessment.authorization_basis == "user_acceptance"
    assert assessment.recommended_action_id == "aws_frankfurt_sovereign"
    assert assessment.audit_rate == 0.0


def test_newer_rejection_immediately_revokes_autonomy():
    store = InMemoryStore()
    policy = build_base_policy()
    policy.metadata["explicit_user_feedback"] = {
        "status": "accepted",
        "action_id": "aws_frankfurt_sovereign",
        "episode_id": "older-accept",
        "recorded_at": "2026-11-10T10:00:00+00:00",
    }
    store.store_policy(policy)

    # Newer rejection episode
    reject_ep = make_feedback_episode(
        episode_id="newer-reject",
        action_id="aws_frankfurt_sovereign",
        feedback_status="rejected",
        created_at="2026-11-10T14:00:00+00:00",
    )
    store.store_episode(reject_ep)

    assessment = assess_autonomy(store, policy)
    assert not assessment.eligible
    assert assessment.authorization_basis == "none"
    assert assessment.user_feedback_status == "rejected"
    assert assessment.audit_rate == 0.10


def test_requires_human_approval_invariant_strictly_blocks_autonomy():
    store = InMemoryStore()
    high_risk_policy = build_base_policy(requires_human_approval=True)
    high_risk_policy.metadata["explicit_user_feedback"] = {
        "status": "accepted",
        "action_id": "swiss_alpine_vault",
        "episode_id": "ep-high-risk-accepted",
        "recorded_at": "2026-11-10T15:00:00+00:00",
    }
    store.store_policy(high_risk_policy)

    assessment = assess_autonomy(store, high_risk_policy)
    assert not assessment.eligible
    assert assessment.authorization_basis == "none"

