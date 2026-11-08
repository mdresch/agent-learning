"""Story 17.3 — Choosing and Replaying (ADR-017, BRD-017, FDD-017).

Acceptance Criteria:
  AC_0 (Greedy Pick): With rate forced to 0.0 (no safe action) choose returns the action
       with the highest mean; an action with no pulls counts as 0.5; ties go to the higher
       pull count, then the smaller id; the same snapshot gives the same action on 100 calls
       and in a fresh process.
  AC_1 (Branch Coin): The branch is exploration exactly when the first
       random.Random(seed).random() is below the rate, where the seed is
       seed_for(snapshot.id, request_id, timestamp); the test recomputes it, and over
       10,000 distinct request ids on the base policy at t = 0 the share of exploration
       lies within 0.5 ± 0.02.
  AC_2 (Exploration Pick): An exploration step picks rng.choice of the id-sorted safe list;
       over 10,000 seeded decisions on the base policy no exploration picks c.
  AC_3 (Record): last_decision_record() returns the record of FDD-017 §2.3 with request_id,
       timestamp, prng_seed as a decimal string, branch_taken, exploration_rate_applied,
       total_pulls, empirical_means on [0, 1] (0.5 for an unpulled action) and chosen;
       every decision has branch_taken and a seed; the record survives json.dumps and
       json.loads unchanged; mutating it does not change the policy.
  AC_4 (Replay): replay(record, snapshot) returns the recorded branch_taken and chosen
       for records of both branches; for a record whose prng_seed was changed by one it
       raises ValueError.
  AC_5 (Defaults): choose() with no arguments works, supplies a request id and a timestamp,
       records them, and is replayable from its own record.
  AC_6 (Probabilities): Decision.probabilities equal the formula of FDD-017 §3 (for rate 0.2,
       safe subset {a, b} and greedy a: 0.9, 0.1, 0.0), sum to 1 within 1e-12, and
       Decision.logprob is None.
  AC_7 (Not A Logit Policy): apply_update raises TypeError containing EpsilonGreedyLearner,
       and choose leaves the snapshot unchanged.

Contract Interpretations (derived via scripts/spec_gate.py):
  I1 (Upstream Fork Purity): All implementations reside in src/agent_learning_ext/,
      leaving upstream src/agent_learning/ pristine.
  I2 (Empty Collection Base Case): Policy with no actions raises ValueError on choose().
  I3 (Non-Finite Float Rejection): Validates numerical boundary conditions.
"""

from __future__ import annotations

import copy
import json
import random
from typing import Any

import pytest

from agent_learning.policy.thompson import seed_for
from agent_learning.types import Action, PolicySnapshot
from agent_learning_ext.policy.epsilon_greedy import (
    EpsilonGreedyPolicy,
    replay,
)


def make_base_actions() -> list[Action]:
    """Base policy action fixture: a and b reversible, c has no flag."""
    return [
        Action(id="a", description="Action A", parameters={"reversible": True}),
        Action(id="b", description="Action B", parameters={"reversible": True}),
        Action(id="c", description="Action C", parameters={}),
    ]


def test_ac0_greedy_pick_and_tie_breaking() -> None:
    """AC_0: Rate 0.0 selects highest mean; unpulled counts as 0.5; ties go to pull count then id."""
    actions = [
        Action(id="a", description="Action A", parameters={}),  # No safe action -> rate 0.0
        Action(id="b", description="Action B", parameters={}),
        Action(id="c", description="Action C", parameters={}),
    ]
    # Case 1: unpulled actions all count as 0.5, tie-break by higher pull count (all 0) then smaller ID ('a')
    policy = EpsilonGreedyPolicy.from_actions(actions, eps0=0.5, delta=0.05, floor=0.05)
    decision = policy.choose(request_id="req-1", timestamp="2026-11-08T12:00:00Z")
    assert decision.action.id == "a"

    # Case 2: Action 'b' has mean 0.7 > 0.5, should be selected
    metadata: dict[str, Any] = {
        "policy_type": "epsilon_greedy",
        "epsilon_schedule": {"eps0": 0.5, "delta": 0.05, "floor": 0.05},
        "action_statistics": {
            "a": {"pull_count": 5, "cumulative_reward": 2.5, "mean_reward": 0.5},
            "b": {"pull_count": 3, "cumulative_reward": 2.1, "mean_reward": 0.7},
            "c": {"pull_count": 0, "cumulative_reward": 0.0, "mean_reward": 0.0},  # unpulled -> 0.5
        },
        "consumed_episode_ids": [],
    }
    snap = PolicySnapshot(
        agent_id="test",
        task_id="test",
        actions=actions,
        logits={a.id: 0.0 for a in actions},
        metadata=metadata,
    )
    p2 = EpsilonGreedyPolicy.from_snapshot(snap)
    assert p2.choose(request_id="req-2", timestamp="2026-11-08T12:00:00Z").action.id == "b"

    # Case 3: Same mean (0.6), tie-break by higher pull count ('a' has 10 pulls, 'b' has 5 pulls)
    metadata["action_statistics"] = {
        "a": {"pull_count": 10, "cumulative_reward": 6.0, "mean_reward": 0.6},
        "b": {"pull_count": 5, "cumulative_reward": 3.0, "mean_reward": 0.6},
        "c": {"pull_count": 0, "cumulative_reward": 0.0, "mean_reward": 0.0},
    }
    p3 = EpsilonGreedyPolicy.from_snapshot(snap)
    assert p3.choose(request_id="req-3", timestamp="2026-11-08T12:00:00Z").action.id == "a"

    # Consistency across 100 calls
    for i in range(100):
        assert p3.choose(request_id=f"req-call-{i}", timestamp="2026-11-08T12:00:00Z").action.id == "a"


def test_ac1_branch_coin_and_frequency() -> None:
    """AC_1: Branch coin u < rate; share of exploration over 10,000 runs is 0.5 +- 0.02 at t=0."""
    actions = make_base_actions()
    policy = EpsilonGreedyPolicy.from_actions(actions, eps0=0.5, delta=0.05, floor=0.05)

    # Deterministic branch verification
    req_id = "test-req-ac1"
    ts = "2026-11-08T10:00:00Z"
    expected_seed = seed_for(policy.snapshot.id, req_id, ts)
    expected_u = random.Random(expected_seed).random()
    expected_branch = "exploration" if expected_u < 0.5 else "exploitation"

    policy.choose(request_id=req_id, timestamp=ts)
    record = policy.last_decision_record()
    assert record["branch_taken"] == expected_branch
    assert record["prng_seed"] == str(expected_seed)

    # 10,000 distinct request ids at t=0
    exploration_count = 0
    n_trials = 10000
    for i in range(n_trials):
        r_id = f"trial-{i}"
        policy.choose(request_id=r_id, timestamp="2026-11-08T00:00:00Z")
        rec_i = policy.last_decision_record()
        if rec_i["branch_taken"] == "exploration":
            exploration_count += 1

    ratio = exploration_count / n_trials
    assert abs(ratio - 0.5) <= 0.02, f"Exploration share {ratio} not within 0.5 +- 0.02"


def test_ac2_exploration_pick_safe_actions_only() -> None:
    """AC_2: Exploration picks rng.choice of id-sorted safe list; c is never picked."""
    actions = make_base_actions()
    policy = EpsilonGreedyPolicy.from_actions(actions, eps0=1.0, delta=0.0, floor=1.0)  # Always explore

    # 10,000 exploration steps
    n_trials = 10000
    seen_picks: set[str] = set()
    for i in range(n_trials):
        dec = policy.choose(request_id=f"explore-{i}", timestamp="2026-11-08T00:00:00Z")
        assert dec.action.id != "c", "Exploration picked non-reversible action 'c'!"
        seen_picks.add(dec.action.id)

    assert seen_picks == {"a", "b"}


def test_ac3_decision_record_structure_and_immutability() -> None:
    """AC_3: Record fields match FDD-017 §2.3; survives json round-trip; mutation is safe."""
    actions = make_base_actions()
    policy = EpsilonGreedyPolicy.from_actions(actions, eps0=0.5, delta=0.05, floor=0.05)

    req_id = "req-test-rec"
    ts = "2026-11-08T14:30:00Z"
    policy.choose(request_id=req_id, timestamp=ts)
    record = policy.last_decision_record()

    # Required fields per FDD-017 §2.3
    assert record["request_id"] == req_id
    assert record["timestamp"] == ts
    assert isinstance(record["prng_seed"], str)
    assert record["branch_taken"] in ("exploration", "exploitation")
    assert record["exploration_rate_applied"] == 0.5
    assert record["total_pulls"] == 0
    assert record["empirical_means"] == {"a": 0.5, "b": 0.5, "c": 0.5}
    assert record["chosen"] in ("a", "b")

    # JSON round trip
    serialized = json.dumps(record)
    loaded = json.loads(serialized)
    assert loaded == record

    # Immutability: mutating record returned does not mutate policy state
    record["chosen"] = "mutated"
    record["empirical_means"]["a"] = 999.0
    fresh_rec = policy.last_decision_record()
    assert fresh_rec["chosen"] != "mutated"
    assert fresh_rec["empirical_means"]["a"] == 0.5


def test_ac4_replay_both_branches_and_tamper_detection() -> None:
    """AC_4: replay(record, snapshot) verifies both branches; seed mismatch raises ValueError."""
    actions = make_base_actions()
    policy = EpsilonGreedyPolicy.from_actions(actions, eps0=0.5, delta=0.05, floor=0.05)

    # Find an exploration record and an exploitation record
    rec_explore = None
    rec_exploit = None
    for i in range(100):
        policy.choose(request_id=f"branch-search-{i}", timestamp="2026-11-08T00:00:00Z")
        rec = policy.last_decision_record()
        if rec["branch_taken"] == "exploration" and rec_explore is None:
            rec_explore = rec
        elif rec["branch_taken"] == "exploitation" and rec_exploit is None:
            rec_exploit = rec
        if rec_explore and rec_exploit:
            break

    assert rec_explore is not None, "Failed to find exploration record"
    assert rec_exploit is not None, "Failed to find exploitation record"

    # Replay exploration
    replayed_exp = replay(rec_explore, policy.snapshot)
    assert replayed_exp["branch_taken"] == "exploration"
    assert replayed_exp["chosen"] == rec_explore["chosen"]

    # Replay exploitation
    replayed_gre = replay(rec_exploit, policy.snapshot)
    assert replayed_gre["branch_taken"] == "exploitation"
    assert replayed_gre["chosen"] == rec_exploit["chosen"]

    # Tampered seed raises ValueError
    tampered = copy.deepcopy(rec_explore)
    original_seed_int = int(tampered["prng_seed"])
    tampered["prng_seed"] = str(original_seed_int + 1)
    with pytest.raises(ValueError, match=r"(?i)seed"):
        replay(tampered, policy.snapshot)


def test_ac5_defaults_and_self_replayable() -> None:
    """AC_5: choose() with no arguments works, auto-supplies req_id and ts, and replay works."""
    actions = make_base_actions()
    policy = EpsilonGreedyPolicy.from_actions(actions, eps0=0.5, delta=0.05, floor=0.05)

    decision = policy.choose()
    assert decision.action.id in ("a", "b")

    record = policy.last_decision_record()
    assert record["request_id"] is not None
    assert len(record["request_id"]) > 0
    assert record["timestamp"] is not None
    assert len(record["timestamp"]) > 0

    replayed = replay(record, policy.snapshot)
    assert replayed["chosen"] == record["chosen"]
    assert replayed["branch_taken"] == record["branch_taken"]


def test_ac6_selection_probabilities_and_none_logprob() -> None:
    """AC_6: Decision.probabilities match FDD-017 §3 formula and sum to 1.0; logprob is None."""
    actions = make_base_actions()  # a, b safe; c not safe
    # Schedule configured to give eps = 0.2 at t=0
    policy = EpsilonGreedyPolicy.from_actions(actions, eps0=0.2, delta=0.0, floor=0.2)

    # In base policy, greedy action at t=0 is 'a' (tie-break smaller ID).
    # Safe subset S = {a, b}, size 2.
    # P(a) = (1 - 0.2) + 0.2 / 2 = 0.8 + 0.1 = 0.9
    # P(b) = 0.2 / 2 = 0.1
    # P(c) = 0.0
    decision = policy.choose(request_id="req-prob", timestamp="2026-11-08T00:00:00Z")
    assert decision.logprob is None
    assert decision.probabilities is not None

    prob_map = {a.id: decision.probabilities[i] for i, a in enumerate(actions)}
    assert abs(prob_map["a"] - 0.9) < 1e-12
    assert abs(prob_map["b"] - 0.1) < 1e-12
    assert abs(prob_map["c"] - 0.0) < 1e-12
    assert abs(sum(decision.probabilities) - 1.0) < 1e-12


def test_ac7_apply_update_and_snapshot_immutability() -> None:
    """AC_7: apply_update raises TypeError mentioning EpsilonGreedyLearner; choose does not mutate snapshot."""
    actions = make_base_actions()
    policy = EpsilonGreedyPolicy.from_actions(actions, eps0=0.5, delta=0.05, floor=0.05)

    with pytest.raises(TypeError, match=r"EpsilonGreedyLearner"):
        policy.apply_update({})

    snap_before = copy.deepcopy(policy.snapshot.to_dict())
    policy.choose(request_id="req-immut", timestamp="2026-11-08T00:00:00Z")
    snap_after = policy.snapshot.to_dict()
    assert snap_before == snap_after


def test_i2_empty_action_space_raises_value_error() -> None:
    """I2: Empty action space raises ValueError on choose()."""
    snap = PolicySnapshot(
        agent_id="test",
        task_id="test",
        actions=[],
        logits={},
        metadata={
            "policy_type": "epsilon_greedy",
            "epsilon_schedule": {"eps0": 0.5, "delta": 0.05, "floor": 0.05},
            "action_statistics": {},
            "consumed_episode_ids": [],
        },
    )
    policy = EpsilonGreedyPolicy.from_snapshot(snap)
    with pytest.raises(ValueError, match=r"(?i)no actions"):
        policy.choose()
