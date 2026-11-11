"""Tests for Methodology #15: Warm-Start / Prior Transfer Demonstration."""

from __future__ import annotations

from agent_learning.types import PolicySnapshot
from agent_learning.warm_start import DAMPING_DEFAULT, warm_start_logits
from examples.warm_start_demo import (
    build_cold_target_snapshot,
    build_converged_donor_snapshot,
    compute_shannon_entropy,
    demonstrate_provenance_and_isolation,
    softmax,
)


def test_damping_flattens_distribution_and_increases_entropy():
    donor = build_converged_donor_snapshot()
    action_map = {
        "approve_risk": "approve_plan",
        "request_risk_revision": "request_revision",
        "reject_risk": "reject_plan",
    }
    target_actions = list(action_map.keys())

    raw_logits = warm_start_logits(donor.logits, action_map, target_actions, damping=1.0)
    damped_logits = warm_start_logits(donor.logits, action_map, target_actions, damping=DAMPING_DEFAULT)

    raw_probs = softmax(raw_logits)
    damped_probs = softmax(damped_logits)

    raw_entropy = compute_shannon_entropy(list(raw_probs.values()))
    damped_entropy = compute_shannon_entropy(list(damped_probs.values()))

    # Damping compresses logits toward 0, expanding entropy
    assert damped_entropy > raw_entropy
    # The max probability is reduced to allow local exploration
    assert max(damped_probs.values()) < max(raw_probs.values())
    # Ordinal ranking is preserved
    assert damped_probs["approve_risk"] > damped_probs["request_risk_revision"] > damped_probs["reject_risk"]


def test_provenance_records_lineage_and_preserves_donor():
    donor = build_converged_donor_snapshot()
    cold_target = build_cold_target_snapshot()

    warm_target = demonstrate_provenance_and_isolation(donor, cold_target)

    # Recipient has provenance keys
    meta = warm_target.metadata
    assert meta["warm_start_donor_policy_id"] == donor.id
    assert meta["warm_start_donor_task_id"] == donor.task_id
    assert meta["warm_start_donor_version"] == donor.version
    assert meta["warm_start_damping_factor"] == DAMPING_DEFAULT
    assert meta["warm_start_donor_kind"] == "policy"
    assert meta["warm_start_donor_gate_met"] is True

    # Target version bumped
    assert warm_target.version == cold_target.version + 1

