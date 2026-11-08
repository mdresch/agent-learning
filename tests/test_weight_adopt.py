"""Contract tests for Story 22.6 — Adopting a Proposal by a Human Decision (ADR-022, Epic 22).

Source ADR: ADR-022 (Scored-Search Decision Configuration Compilation)
Source BRD: BRD-022 (BRU-022-10, BRU-022-11)
Source FDD: FDD-022 (§1 item 2, §1 item 4, §2.5, §3.9, §4 L6)

Contract Interpretations:
- [I1] Upstream Fork Purity (Invariant 6):
  Implemented strictly in src/agent_learning_ext/cli.py and policy shapes.
  Upstream src/agent_learning/ remains 100% untouched.
- [I2] Storage Decoupling & Serialization Round-Trip:
  The store gains no new record type; the adoption creates and stores only a new PolicySnapshot version.
- [I3] Defensive None-Safety:
  Defensively guards dictionary access and attributes against None values.
- [I4] Human Approval Primacy:
  Adoption strictly requires an adjudicated and accepted episode for approve-compiled-weights.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from agent_learning.types import Action, Episode, PolicySnapshot
from agent_learning_ext.routing import route


@pytest.fixture
def snapshot() -> PolicySnapshot:
    return PolicySnapshot(
        id="policy-adopt",
        agent_id="agent-adopt",
        task_id="task-adopt",
        version=1,
        actions=[Action(id="A"), Action(id="B")],
        logits={"A": 0.0, "B": 0.0},
        metadata={"decision_authority": "full", "policy_scope": "delegated_decision"},
    )


@pytest.fixture
def valid_proposal(snapshot: PolicySnapshot) -> dict[str, Any]:
    return {
        "task_id": snapshot.task_id,
        "agent_id": snapshot.agent_id,
        "policy_id": snapshot.id,
        "policy_version": snapshot.version,
        "improved": True,
        "weights": {"c1": 0.6, "c2": 0.3, "c3": 0.1},
        "train_accuracy": 1.0,
        "holdout_accuracy": 0.95,
        "baseline_holdout_accuracy": 0.60,
        "holdout_margin": 0.15,
        "seed": 7,
        "evaluations": 120,
        "sweeps": 4,
        "restarts": 5,
        "proposed_at": "2026-10-27T00:00:00Z",
        "dataset_size": 40,
        "train_size": 28,
        "holdout_size": 12,
        "earliest_labeled_at": "2026-10-26T10:00:00Z",
        "latest_labeled_at": "2026-10-26T10:39:00Z",
        "compile_duration_seconds": 4.5,
    }


@pytest.fixture
def valid_approval_episode() -> Episode:
    return Episode(
        id="ep-approval-1",
        agent_id="agent-adopt",
        task_id="approve-compiled-weights",
        metadata={
            "feedback_status": "adjudicated",
            "decision_disposition": "accepted",
        },
    )


def test_ac0_policy_shape_and_router_pinning() -> None:
    """AC_0 (Shape):

    docs/policy-shapes/approve-compiled-weights.actions.json holds approve_compiled_weights,
    reject_compiled_weights and request_revision_before_decision, and its complexity profile
    declares requires_human_approval true, so the router of FDD-021 pins it.
    """
    repo_root = Path(__file__).resolve().parent.parent
    actions_file = repo_root / "docs" / "policy-shapes" / "approve-compiled-weights.actions.json"
    assert actions_file.is_file(), f"Missing actions shape file: {actions_file}"

    actions_data = json.loads(actions_file.read_text(encoding="utf-8"))
    action_ids = [a["id"] for a in actions_data]
    assert "approve_compiled_weights" in action_ids
    assert "reject_compiled_weights" in action_ids
    assert "request_revision_before_decision" in action_ids

    # Complexity profile check
    profile_file = repo_root / "docs" / "policy-shapes" / "approve-compiled-weights.profile.json"
    assert profile_file.is_file(), f"Missing profile shape file: {profile_file}"
    profile_data = json.loads(profile_file.read_text(encoding="utf-8"))
    assert profile_data.get("requires_human_approval") is True

    # Router pins it to FULL with reason 'pinned'
    decision = route(
        probs=[0.99, 0.01],
        tier="low",
        task_id="approve-compiled-weights",
        requires_human_approval=profile_data["requires_human_approval"],
    )
    assert decision.authority.value == "full"
    assert decision.reason == "pinned"


def test_ac1_needs_valid_approval_episode(
    tmp_path: Path,
    snapshot: PolicySnapshot,
    valid_proposal: dict[str, Any],
) -> None:
    """AC_1 (Needs An Approval Episode):

    task-policy-weights-adopt without --approval-episode, or with an episode that does not exist,
    belongs to another task, or is not adjudicated and accepted, exits non-zero and writes nothing.
    """
    prop_file = tmp_path / "prop.json"
    prop_file.write_text(json.dumps(valid_proposal), encoding="utf-8")

    from agent_learning_ext.cli import main

    # 1. Non-existent episode
    with patch("agent_learning_ext.cli.get_default_store") as mock_get_store:
        mock_store = mock_get_store.return_value
        mock_store.get_active_policy.return_value = snapshot
        mock_store.get_episode.return_value = None

        ret1 = main([
            "task-policy-weights-adopt",
            "--agent-id", snapshot.agent_id,
            "--task-id", snapshot.task_id,
            "--proposal", str(prop_file),
            "--approval-episode", "missing-ep",
        ])
        assert ret1 != 0
        mock_store.store_policy.assert_not_called()

    # 2. Episode belongs to another task
    wrong_task_ep = Episode(
        id="ep-wrong-task",
        agent_id=snapshot.agent_id,
        task_id="approve-adr",
        metadata={"feedback_status": "adjudicated", "decision_disposition": "accepted"},
    )
    with patch("agent_learning_ext.cli.get_default_store") as mock_get_store:
        mock_store = mock_get_store.return_value
        mock_store.get_active_policy.return_value = snapshot
        mock_store.get_episode.return_value = wrong_task_ep

        ret2 = main([
            "task-policy-weights-adopt",
            "--agent-id", snapshot.agent_id,
            "--task-id", snapshot.task_id,
            "--proposal", str(prop_file),
            "--approval-episode", "ep-wrong-task",
        ])
        assert ret2 != 0
        mock_store.store_policy.assert_not_called()

    # 3. Episode not accepted (e.g. rejected)
    rejected_ep = Episode(
        id="ep-rejected",
        agent_id=snapshot.agent_id,
        task_id="approve-compiled-weights",
        metadata={"feedback_status": "adjudicated", "decision_disposition": "rejected"},
    )
    with patch("agent_learning_ext.cli.get_default_store") as mock_get_store:
        mock_store = mock_get_store.return_value
        mock_store.get_active_policy.return_value = snapshot
        mock_store.get_episode.return_value = rejected_ep

        ret3 = main([
            "task-policy-weights-adopt",
            "--agent-id", snapshot.agent_id,
            "--task-id", snapshot.task_id,
            "--proposal", str(prop_file),
            "--approval-episode", "ep-rejected",
        ])
        assert ret3 != 0
        mock_store.store_policy.assert_not_called()


def test_ac2_adopts_proposal_into_new_policy_version(
    tmp_path: Path,
    snapshot: PolicySnapshot,
    valid_proposal: dict[str, Any],
    valid_approval_episode: Episode,
) -> None:
    """AC_2 (Adopts):

    With a valid episode and an improved proposal for the active policy's id and version,
    it stores the next version of the policy with criteria_weights equal to the proposal's
    and compiled_weights_provenance holding the proposal hash, seed, accuracies, split sizes,
    label time range, approval episode id and adoption time; the earlier version is unchanged.
    """
    prop_file = tmp_path / "prop.json"
    prop_file.write_text(json.dumps(valid_proposal), encoding="utf-8")

    from agent_learning_ext.cli import main

    stored_policies: list[PolicySnapshot] = []

    def mock_store_policy(p: PolicySnapshot) -> str:
        stored_policies.append(p)
        return p.id

    with patch("agent_learning_ext.cli.get_default_store") as mock_get_store:
        mock_store = mock_get_store.return_value
        mock_store.get_active_policy.return_value = snapshot
        mock_store.get_episode.return_value = valid_approval_episode
        mock_store.store_policy.side_effect = mock_store_policy

        ret = main([
            "task-policy-weights-adopt",
            "--agent-id", snapshot.agent_id,
            "--task-id", snapshot.task_id,
            "--proposal", str(prop_file),
            "--approval-episode", valid_approval_episode.id,
        ])
        assert ret == 0

    assert len(stored_policies) == 1
    new_policy = stored_policies[0]

    # Earlier version is unchanged
    assert snapshot.version == 1

    # New version has version 2
    assert new_policy.version == 2
    assert new_policy.metadata["criteria_weights"] == valid_proposal["weights"]

    prov = new_policy.metadata["compiled_weights_provenance"]
    expected_hash = hashlib.sha256(json.dumps(valid_proposal, sort_keys=True).encode("utf-8")).hexdigest()
    assert prov["proposal_hash"] == expected_hash
    assert prov["seed"] == valid_proposal["seed"]
    assert prov["holdout_accuracy"] == valid_proposal["holdout_accuracy"]
    assert prov["approval_episode_id"] == valid_approval_episode.id
    assert "adopted_at" in prov


def test_ac3_refuses_unimproved_or_mismatched_proposals(
    tmp_path: Path,
    snapshot: PolicySnapshot,
    valid_approval_episode: Episode,
) -> None:
    """AC_3 (Refuses):

    A proposal with improved false, a proposal for another policy id or version,
    or weights that fail with_weights validation exits non-zero and writes nothing.
    """
    from agent_learning_ext.cli import main

    # 1. Improved is false
    unimproved_prop = tmp_path / "unimproved.json"
    unimproved_prop.write_text(json.dumps({
        "policy_id": snapshot.id,
        "policy_version": snapshot.version,
        "improved": False,
        "reason": "no improvement",
    }), encoding="utf-8")

    # 2. Mismatched version
    wrong_version_prop = tmp_path / "wrong_version.json"
    wrong_version_prop.write_text(json.dumps({
        "policy_id": snapshot.id,
        "policy_version": 999,
        "improved": True,
        "weights": {"c1": 0.5, "c2": 0.5},
    }), encoding="utf-8")

    # 3. Invalid weights (negative or non-finite)
    invalid_weights_prop = tmp_path / "invalid_weights.json"
    invalid_weights_prop.write_text(json.dumps({
        "policy_id": snapshot.id,
        "policy_version": snapshot.version,
        "improved": True,
        "weights": {"c1": -0.5, "c2": 1.5},
    }), encoding="utf-8")

    for bad_prop in (unimproved_prop, wrong_version_prop, invalid_weights_prop):
        with patch("agent_learning_ext.cli.get_default_store") as mock_get_store:
            mock_store = mock_get_store.return_value
            mock_store.get_active_policy.return_value = snapshot
            mock_store.get_episode.return_value = valid_approval_episode

            ret = main([
                "task-policy-weights-adopt",
                "--agent-id", snapshot.agent_id,
                "--task-id", snapshot.task_id,
                "--proposal", str(bad_prop),
                "--approval-episode", valid_approval_episode.id,
            ])
            assert ret != 0, f"Expected non-zero exit for {bad_prop.name}"
            mock_store.store_policy.assert_not_called()


def test_ac4_snapshot_only_no_new_record_types() -> None:
    """AC_4 (Snapshot Only):

    The store gains no record type, and the adoption changes nothing but the new snapshot.
    """
    from agent_learning_ext.storage.cosmos import CosmosStore

    store_methods = [m for m in dir(CosmosStore) if not m.startswith("_")]
    # Verify no new store record types were added to CosmosStore interface
    assert "save_proposal" not in store_methods
    assert "store_compiled_weights" not in store_methods
    assert "get_compiled_weights" not in store_methods
