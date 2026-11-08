"""Story 16.2 — Choosing Deterministically (ADR-016, BRD-016, FDD-016).

Acceptance Criteria:
  AC_0 (Argmax): On base statistics choose returns action with highest score of Story 16.1.
  AC_1 (Repeatable): 100 calls on one snapshot, and one call in a fresh process on the same
       snapshot, return the same action.
  AC_2 (Tie-Break): Two actions with equal scores resolve to higher pull count; if pull counts
       also equal, to lexicographically smaller action.id.
  AC_3 (Round-Robin): With three actions and no pulls, choose returns smallest id; after that
       action gets one pull, the next smallest; after all three have one pull, no action scores inf.
  AC_4 (No Log-Probability): Returned Decision has logprob of None and one-hot probabilities
       on chosen action.
  AC_5 (Record): last_decision_record() returns record of FDD-016 §2.3 with null for infinite
       score; survives json.dumps/loads unchanged; mutating it does not change policy.
  AC_6 (Not A Logit Policy): apply_update raises TypeError containing 'UCBLearner'; choose leaves
       snapshot unchanged.

Contract Interpretations (derived via scripts/spec_gate.py):
  I1 (Upstream Fork Purity): Implemented under src/agent_learning_ext/ leaving upstream
      src/agent_learning/ pristine (0 lines diff).
  I2 (Empty Collection Base Case): Policy with empty actions raises ValueError on choose.
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys

import pytest

from agent_learning.policy.base import Decision
from agent_learning.types import Action, PolicySnapshot
from agent_learning_ext.policy.action_statistics import ActionStats
from agent_learning_ext.policy.ucb import UCBPolicy


def _make_snapshot(
    actions: list[Action],
    stats: dict[str, ActionStats] | None = None,
    variant: str = "standard",
    c: float = 2.0 ** 0.5,
) -> PolicySnapshot:
    stat_dict = {}
    if stats is not None:
        for aid, st in stats.items():
            stat_dict[aid] = {
                "pull_count": st.pull_count,
                "cumulative_reward": st.cumulative_reward,
                "mean_reward": st.mean_reward,
            }
    return PolicySnapshot(
        id="snap-test",
        agent_id="test-agent",
        task_id="test-task",
        actions=actions,
        logits={a.id: 0.0 for a in actions},
        metadata={
            "policy_type": "ucb",
            "ucb_variant": variant,
            "exploration_constant": c,
            "action_statistics": stat_dict,
            "consumed_episode_ids": [],
        },
    )


def test_ac0_argmax_choice() -> None:
    """AC_0: on base statistics, choose returns action b with highest score."""
    actions = [Action(id="a", description="action a"), Action(id="b", description="action b")]
    stats = {
        "a": ActionStats(pull_count=10, cumulative_reward=8.0, mean_reward=0.8),
        "b": ActionStats(pull_count=5, cumulative_reward=3.0, mean_reward=0.6),
    }
    snap = _make_snapshot(actions, stats, variant="standard")
    policy = UCBPolicy(snap)
    decision = policy.choose()
    assert decision.action.id == "b"


def test_ac1_repeatable_across_calls_and_processes() -> None:
    """AC_1: 100 calls and fresh process call return the exact same action."""
    actions = [Action(id="x", description="action x"), Action(id="y", description="action y")]
    stats = {
        "x": ActionStats(pull_count=10, cumulative_reward=5.0, mean_reward=0.5),
        "y": ActionStats(pull_count=10, cumulative_reward=6.0, mean_reward=0.6),
    }
    snap = _make_snapshot(actions, stats)
    policy = UCBPolicy(snap)

    first_choice = policy.choose().action.id
    for _ in range(100):
        assert policy.choose().action.id == first_choice

    # Fresh process execution
    snap_json = json.dumps({
        "actions": [{"id": a.id, "description": a.description} for a in actions],
        "stats": {aid: {"pull_count": st.pull_count, "cumulative_reward": st.cumulative_reward, "mean_reward": st.mean_reward} for aid, st in stats.items()},
    })
    code = (
        "import json, sys\n"
        "from agent_learning.types import Action, PolicySnapshot\n"
        "from agent_learning_ext.policy.ucb import UCBPolicy\n"
        "data = json.loads(sys.argv[1])\n"
        "actions = [Action(id=a['id'], description=a['description']) for a in data['actions']]\n"
        "snap = PolicySnapshot(id='s', agent_id='a', task_id='t', actions=actions, logits={a['id']: 0.0 for a in data['actions']}, "
        "metadata={'policy_type': 'ucb', 'ucb_variant': 'standard', 'exploration_constant': 2.0 ** 0.5, "
        "'action_statistics': data['stats'], 'consumed_episode_ids': []})\n"
        "p = UCBPolicy(snap)\n"
        "print(p.choose().action.id)\n"
    )
    res = subprocess.run([sys.executable, "-c", code, snap_json], capture_output=True, text=True, check=True)
    assert res.stdout.strip() == first_choice


def test_ac2_tie_breaking_rules() -> None:
    """AC_2: equal scores tie-break by higher pull count, then lexicographically smaller id."""
    # Sub-case A: Equal score, different pull counts -> higher pull count wins
    # Unpulled actions have score inf. But let's construct equal finite scores:
    # Action A: 10 pulls, reward 5.0 (mean 0.5)
    # Action B: 20 pulls, reward 10.0 (mean 0.5)
    # With total = 30 in wilson variant, symmetric wilson bounds on same mean and same N would differ,
    # but let's test actions with identical scores explicitly by mocking or constructed counts:
    # In wilson variant: two actions with identical counts (e.g. 5 pulls, 3.0 reward) have equal score.
    # If Action 'z' has 10 pulls, 6.0 reward vs Action 'a' has 5 pulls, 3.0 reward:
    # Let's test equal scores where pull count differs:
    # In standard variant: mean + c * sqrt(2 * ln(t) / N).
    # To test pure tie-break logic:
    actions = [Action(id="beta", description="b"), Action(id="alpha", description="a")]
    stats_unexplored = {
        "beta": ActionStats(pull_count=0, cumulative_reward=0.0, mean_reward=0.0),
        "alpha": ActionStats(pull_count=0, cumulative_reward=0.0, mean_reward=0.0),
    }
    # Both score inf, pull counts both 0 -> lexicographical smaller id 'alpha' wins
    snap_lex = _make_snapshot(actions, stats_unexplored, variant="standard")
    p_lex = UCBPolicy(snap_lex)
    assert p_lex.choose().action.id == "alpha"

    # Now give 'beta' 1 pull with reward 1.0 (mean 1.0) and 'alpha' 2 pulls with reward 2.0 (mean 1.0)
    # in wilson variant:
    # 2 pulls with 2.0 has higher lower/upper bound than 1 pull with 1.0.
    # What if we have equal scores directly? Let's verify tie-break by higher pull count:
    # When two actions have identical scores, higher pull count wins:
    actions_tie = [Action(id="p1", description="1"), Action(id="p2", description="2")]
    # If we create equal score scenario by overriding or exact match:
    # Two actions with 0 pulls both score inf. If one has pull count 1 and another has 0, inf wins.
    # What if two actions have same score:
    # We can test with two identical actions whose score and pull counts match -> smaller id wins.
    # Sub-case B: Equal score, different pull counts -> higher pull count wins over lexicographical order
    actions_pull_tie = [Action(id="aaa", description="lower pulls"), Action(id="zzz", description="higher pulls")]
    stats_pull_tie = {
        "aaa": ActionStats(pull_count=5, cumulative_reward=5.0, mean_reward=1.0),
        "zzz": ActionStats(pull_count=10, cumulative_reward=10.0, mean_reward=1.0),
    }
    # In wilson variant, both perfect actions score 1.0 exactly.
    # zzz has pull count 10 > 5, so zzz must win despite aaa being lexicographically smaller.
    snap_pull_tie = _make_snapshot(actions_pull_tie, stats_pull_tie, variant="wilson")
    p_pull_tie = UCBPolicy(snap_pull_tie)
    assert p_pull_tie.choose().action.id == "zzz"

    # Sub-case C: Equal score and equal pull counts -> lexicographical order
    stats_same_pulls = {
        "p2": ActionStats(pull_count=5, cumulative_reward=3.0, mean_reward=0.6),
        "p1": ActionStats(pull_count=5, cumulative_reward=3.0, mean_reward=0.6),
    }
    snap_same = _make_snapshot(actions_tie, stats_same_pulls, variant="standard")
    assert UCBPolicy(snap_same).choose().action.id == "p1"


def test_ac3_round_robin_exploration() -> None:
    """AC_3: with 3 unpulled actions, choose picks smallest id; then next smallest; then no action has inf."""
    actions = [Action(id="c", description="c"), Action(id="a", description="a"), Action(id="b", description="b")]
    stats: dict[str, ActionStats] = {
        "a": ActionStats(pull_count=0, cumulative_reward=0.0, mean_reward=0.0),
        "b": ActionStats(pull_count=0, cumulative_reward=0.0, mean_reward=0.0),
        "c": ActionStats(pull_count=0, cumulative_reward=0.0, mean_reward=0.0),
    }

    # Step 1: all 0 pulls -> smallest id 'a' is chosen
    snap1 = _make_snapshot(actions, stats)
    p1 = UCBPolicy(snap1)
    d1 = p1.choose()
    assert d1.action.id == "a"

    # Step 2: action 'a' gets 1 pull (reward 1.0)
    stats["a"] = ActionStats(pull_count=1, cumulative_reward=1.0, mean_reward=1.0)
    snap2 = _make_snapshot(actions, stats)
    p2 = UCBPolicy(snap2)
    d2 = p2.choose()
    assert d2.action.id == "b"

    # Step 3: action 'b' gets 1 pull (reward 0.0)
    stats["b"] = ActionStats(pull_count=1, cumulative_reward=0.0, mean_reward=0.0)
    snap3 = _make_snapshot(actions, stats)
    p3 = UCBPolicy(snap3)
    d3 = p3.choose()
    assert d3.action.id == "c"

    # Step 4: action 'c' gets 1 pull -> all have 1 pull -> none scores inf
    stats["c"] = ActionStats(pull_count=1, cumulative_reward=0.5, mean_reward=0.5)
    snap4 = _make_snapshot(actions, stats)
    p4 = UCBPolicy(snap4)
    p4.choose()
    rec = p4.last_decision_record()
    assert rec is not None
    for aid, sc in rec["scores"].items():
        assert sc is not None, f"Action {aid} unexpectedly scored inf"


def test_ac4_decision_logprob_and_probabilities() -> None:
    """AC_4: returned Decision has logprob=None and one-hot probabilities."""
    actions = [Action(id="a", description="a"), Action(id="b", description="b")]
    stats = {
        "a": ActionStats(pull_count=10, cumulative_reward=8.0, mean_reward=0.8),
        "b": ActionStats(pull_count=5, cumulative_reward=3.0, mean_reward=0.6),
    }
    snap = _make_snapshot(actions, stats)
    policy = UCBPolicy(snap)
    decision = policy.choose()

    assert isinstance(decision, Decision)
    assert decision.logprob is None
    # Action 'b' was chosen (index 1)
    assert decision.probabilities == [0.0, 1.0]


def test_ac5_last_decision_record() -> None:
    """AC_5: last_decision_record matches FDD-016 §2.3, null for inf, JSON round-trips, immutable."""
    actions = [Action(id="a", description="a"), Action(id="b", description="b")]
    stats = {
        "a": ActionStats(pull_count=0, cumulative_reward=0.0, mean_reward=0.0),
        "b": ActionStats(pull_count=5, cumulative_reward=3.0, mean_reward=0.6),
    }
    snap = _make_snapshot(actions, stats, variant="standard", c=1.414)
    policy = UCBPolicy(snap)

    # Before choose(), record is None
    assert policy.last_decision_record() is None

    # Choose action 'a' (unexplored, score inf)
    policy.choose()
    rec = policy.last_decision_record()
    assert rec is not None

    assert rec["variant"] == "standard"
    assert rec["exploration_constant"] == 1.414
    assert rec["total_pulls"] == 5
    assert rec["chosen"] == "a"
    assert rec["scores"]["a"] is None  # null in JSON
    assert abs(rec["scores"]["b"] - (0.6 + 1.414 * (2.0 * 1.6094379 / 5.0) ** 0.5)) < 1e-4

    # JSON round-trip
    serialized = json.dumps(rec)
    deserialized = json.loads(serialized)
    assert deserialized == rec
    assert deserialized["scores"]["a"] is None

    # Mutating returned record does not alter policy
    rec["chosen"] = "mutated"
    rec["scores"]["a"] = 999.0
    rec2 = policy.last_decision_record()
    assert rec2["chosen"] == "a"
    assert rec2["scores"]["a"] is None


def test_ac6_not_a_logit_policy_and_snapshot_unaltered() -> None:
    """AC_6: apply_update raises TypeError containing UCBLearner; choose leaves snapshot unchanged."""
    actions = [Action(id="a", description="a"), Action(id="b", description="b")]
    stats = {
        "a": ActionStats(pull_count=10, cumulative_reward=8.0, mean_reward=0.8),
        "b": ActionStats(pull_count=5, cumulative_reward=3.0, mean_reward=0.6),
    }
    snap = _make_snapshot(actions, stats)
    snap_copy = copy.deepcopy(snap)

    policy = UCBPolicy(snap)

    with pytest.raises(TypeError, match="UCBLearner"):
        policy.apply_update([0.1, -0.1])

    policy.choose()

    # Verify snapshot was not mutated
    assert policy.snapshot() == snap_copy


def test_i2_empty_action_space_raises() -> None:
    """I2 (Empty Collection Base Case): Policy with empty actions raises ValueError on choose."""
    empty_snap = _make_snapshot(actions=[])
    policy = UCBPolicy(empty_snap)
    with pytest.raises(ValueError, match="policy has no actions"):
        policy.choose()
