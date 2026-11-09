"""Contract tests for Story 21.4: The Shadow Record and the Agreement Gate.

Governing specifications:
- ADR-021 §4.1 (Contextual Authority Ensemble Routing)
- BRD-021 (BRU-021-11, BRU-021-12)
- FDD-021 §1 item 4, §2.2, §2.3, §3.4, §3.5, §3.6, §3.7, §4 K1, K7
- Story 21.4 (docs/user-stories/epic-21-contextual-authority-ensemble-routing.md)

Acceptance Criteria:
- AC_0 (Shadow Record): shadow_record("a", 1.2955) returns the shadow action and the entropy
  as a number; an empty action id or a non-finite entropy raises ValueError; the dict contains no reward key.
- AC_1 (Previous Route): previous_route returns the route of the newest episode of the bucket by created_at,
  ignores other buckets and untagged episodes, and returns None when there is none.
- AC_2 (Counting): agreement counts only full-routed episodes of the bucket with a shadow action and a
  feedback_status of accepted or rejected; the final action is correct_action_id when present, else action_id;
  episodes outside the evidence window are dropped.
- AC_3 (Fail Closed): agreement with max_evidence_age_days of None raises ValueError.
- AC_4 (Gate Arithmetic): propose_bucket equals wilson_lower_bound(k, n) of the counts and compares it with
  the standard tier gate; 20 of 20 gives 0.8389 and is not eligible; 34 of 34 gives 0.8985 and is not eligible;
  35 of 35 gives 0.9011 and is eligible; an n below the minimum outcomes is not eligible.
- AC_5 (Reported Beside): the proposal includes base_rate, modal_action, n, k and mean_shadow_entropy_bits;
  a bucket where one action is final in 95% of episodes shows base rate 0.95 beside a perfect agreement.
- AC_6 (Never A Reward): no learner reads shadow_low_action; a ReinforceLearner run over episodes carrying it
  gives the same logits as over the same episodes without it.

Contract Interpretations (LL-011):
- I1: Upstream Fork Purity (Invariant 6): Zero edits to src/agent_learning/. All logic isolated in
  src/agent_learning_ext/routing.py.
- I2: Storage Decoupling & Serialization: Functions perform zero direct file I/O or database access.
  All outputs are plain JSON-serializable dictionaries and DecisionAuthority enums.
- I3: Numerical Precision Tolerances: Floating-point assertions use math.isclose or pytest.approx with
  explicit absolute tolerance (1e-4 for the worked Wilson values and 1e-9 for probabilities/means).
  The gate itself compares the unrounded wilson_lower_bound(k, n) (AC_4 "equals"); rounding before
  the comparison would admit a bound just below the gate. Two assertions are exact by design: the
  reported bound against wilson_lower_bound(k, n) (identity of the same deterministic function, as
  AC_4 "equals" requires) and the AC_6 logits of two identical learner runs (any difference at all
  means the shadow field leaked into the update). Spec gate episode: spec-21_4-8ad60e3c.
- I4: File name follows the epic (tests/test_routing_guard.py), as Stories 21.1 to 21.3 do.
- I5: "a final action" (FDD-021 §3.6) is required for an episode to count: an episode with neither
  correct_action_id nor action_id is dropped, not counted under a placeholder action.
- I6: AC_6 must be able to fail: rewards are AGGREGATE (the only source ReinforceLearner consumes) and
  the test asserts the logits moved, so the invariance is not vacuous. Both the upstream and the
  extension ReinforceLearner are exercised (Story 21.6 changes the extension one).

Heal pass (2026-11-09, heal-contract-failure): the abandoned implement-story run left this contract
under tests/test_routing_agreement.py with a crashing AC_6, a vacuous AC_6 reward source, a
rounding-tolerant AC_4 and no final-action requirement in AC_2; I4 to I6 record the corrections.
"""

from __future__ import annotations

import ast
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from agent_learning.autonomy import wilson_lower_bound
from agent_learning.config import AutonomyConfig
from agent_learning.decision import DecisionAuthority
from agent_learning.learners.reinforce import ReinforceLearner as UpstreamReinforceLearner
from agent_learning.policy.softmax_bandit import SoftmaxPolicy
from agent_learning.types import Action, Episode, Reward, RewardSource
from agent_learning_ext.learners.reinforce import ReinforceLearner as ExtReinforceLearner
from agent_learning_ext.routing import (
    agreement,
    previous_route,
    propose_bucket,
    shadow_record,
)

ROOT = Path(__file__).resolve().parent.parent


def _make_episode(
    ep_id: str,
    *,
    bucket: str | None = "ctx-17",
    route: str | DecisionAuthority | None = "full",
    shadow_action: str | None = "approve_plan",
    shadow_entropy: float | None = 1.2955,
    action_id: str | None = "approve_plan",
    correct_action_id: str | None = None,
    feedback_status: str | None = "accepted",
    created_at: str | datetime = "2026-11-01T12:00:00+00:00",
    action_logprob: float | None = -0.6931,
) -> Episode:
    """Helper to construct episodes for routing agreement tests."""
    meta: dict[str, Any] = {}
    if bucket is not None:
        meta["routing_bucket"] = bucket
        meta["routing"] = {"bucket": bucket, "route": str(route).lower() if route else "full"}
    if route is not None:
        meta["routed_authority"] = str(route).lower() if isinstance(route, (str, DecisionAuthority)) else route
    if shadow_action is not None:
        meta["shadow_low_action"] = shadow_action
        if shadow_entropy is not None:
            meta["shadow_entropy_bits"] = shadow_entropy
    if feedback_status is not None:
        meta["feedback_status"] = feedback_status
    if correct_action_id is not None:
        meta["correct_action_id"] = correct_action_id

    return Episode(
        id=ep_id,
        agent_id="test-agent",
        user_input="test prompt",
        assistant_output="test output",
        action_id=action_id,
        action_logprob=action_logprob,
        created_at=created_at if isinstance(created_at, str) else created_at.isoformat(),
        metadata=meta,
    )


# --- AC_0: Shadow Record -------------------------------------------------------------


def test_ac0_shadow_record_valid() -> None:
    rec = shadow_record("a", 1.2955)
    assert isinstance(rec, dict)
    assert rec == {"shadow_low_action": "a", "shadow_entropy_bits": 1.2955}
    assert "reward" not in rec
    # Must survive standard json serialization (Interpretation I2)
    assert json.loads(json.dumps(rec)) == rec


@pytest.mark.parametrize("bad_action", ["", "   ", None, 123, []])
def test_ac0_shadow_record_invalid_action(bad_action: Any) -> None:
    with pytest.raises(ValueError, match="action"):
        shadow_record(bad_action, 1.2955)  # type: ignore[arg-type]


@pytest.mark.parametrize("bad_entropy", [float("nan"), float("inf"), float("-inf"), "1.2", None, True, False])
def test_ac0_shadow_record_invalid_entropy(bad_entropy: Any) -> None:
    with pytest.raises(ValueError, match="entropy"):
        shadow_record("a", bad_entropy)  # type: ignore[arg-type]


# --- AC_1: Previous Route ------------------------------------------------------------


def test_ac1_previous_route_finds_newest_by_created_at() -> None:
    episodes = [
        _make_episode("ep1", bucket="ctx-17", route="low", created_at="2026-11-01T10:00:00Z"),
        _make_episode("ep2", bucket="ctx-17", route="full", created_at="2026-11-03T12:00:00Z"),
        _make_episode("ep3", bucket="ctx-17", route="low", created_at="2026-11-02T15:00:00Z"),
    ]
    # ep2 is the newest for ctx-17 (2026-11-03)
    route = previous_route(episodes, "ctx-17")
    assert route == DecisionAuthority.FULL


def test_ac1_previous_route_ignores_other_buckets_and_untagged() -> None:
    episodes = [
        _make_episode("ep1", bucket="other-bucket", route="full", created_at="2026-11-05T10:00:00Z"),
        _make_episode("ep2", bucket=None, route=None, created_at="2026-11-06T10:00:00Z"),
        _make_episode("ep3", bucket="ctx-17", route="low", created_at="2026-11-01T10:00:00Z"),
    ]
    route = previous_route(episodes, "ctx-17")
    assert route == DecisionAuthority.LOW

    # For an unknown bucket, returns None
    assert previous_route(episodes, "unknown-bucket") is None
    # For empty episodes, returns None
    assert previous_route([], "ctx-17") is None


def test_ac1_previous_route_supports_datetime_objects() -> None:
    dt1 = datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc)
    dt2 = datetime(2026, 11, 2, 10, 0, tzinfo=timezone.utc)
    episodes = [
        _make_episode("ep1", bucket="ctx-17", route="low", created_at=dt1),
        _make_episode("ep2", bucket="ctx-17", route="full", created_at=dt2),
    ]
    assert previous_route(episodes, "ctx-17") == DecisionAuthority.FULL


# --- AC_2: Counting & Window Filtering ----------------------------------------------


def test_ac2_agreement_counts_only_qualifying_episodes() -> None:
    now = datetime(2026, 11, 10, 0, 0, tzinfo=timezone.utc)
    episodes = [
        # Qualifying match: shadow=approve, final=approve (k+1, n+1)
        _make_episode("ep1", bucket="ctx-17", route="full", shadow_action="approve", action_id="approve", feedback_status="accepted", created_at="2026-11-08T00:00:00Z"),
        # Qualifying mismatch: shadow=approve, final=reject (k+0, n+1)
        _make_episode("ep2", bucket="ctx-17", route="full", shadow_action="approve", action_id="reject", feedback_status="rejected", created_at="2026-11-07T00:00:00Z"),
        # Qualifying with correct_action_id overriding action_id: shadow=approve, action=reject, correct=approve -> match! (k+1, n+1)
        _make_episode("ep3", bucket="ctx-17", route="full", shadow_action="approve", action_id="reject", correct_action_id="approve", feedback_status="rejected", created_at="2026-11-06T00:00:00Z"),
        # Non-qualifying: wrong bucket
        _make_episode("ep4", bucket="other", route="full", shadow_action="approve", action_id="approve", feedback_status="accepted", created_at="2026-11-08T00:00:00Z"),
        # Non-qualifying: route is low (not full)
        _make_episode("ep5", bucket="ctx-17", route="low", shadow_action="approve", action_id="approve", feedback_status="accepted", created_at="2026-11-08T00:00:00Z"),
        # Non-qualifying: missing shadow action
        _make_episode("ep6", bucket="ctx-17", route="full", shadow_action=None, action_id="approve", feedback_status="accepted", created_at="2026-11-08T00:00:00Z"),
        # Non-qualifying: feedback status is pending (unscored)
        _make_episode("ep7", bucket="ctx-17", route="full", shadow_action="approve", action_id="approve", feedback_status="pending", created_at="2026-11-08T00:00:00Z"),
        # Non-qualifying: outside evidence window (older than 10 days)
        _make_episode("ep8", bucket="ctx-17", route="full", shadow_action="approve", action_id="approve", feedback_status="accepted", created_at="2026-10-25T00:00:00Z"),
    ]

    res = agreement(episodes, "ctx-17", now=now, max_evidence_age_days=10)
    assert res["n"] == 3
    assert res["k"] == 2
    assert res["final_action_counts"] == {"approve": 2, "reject": 1}
    assert res["modal_action"] == "approve"
    assert res["base_rate"] == pytest.approx(2 / 3, abs=1e-9)
    assert res["mean_shadow_entropy_bits"] == pytest.approx(1.2955, abs=1e-9)


def test_ac5_mean_entropy_only_over_episodes_carrying_it() -> None:
    """Q-146-1/2: an episode without a finite shadow_entropy_bits still counts in n and k but is
    left out of the mean, so it cannot pull mean_shadow_entropy_bits towards 0."""
    now = datetime(2026, 11, 10, 0, 0, tzinfo=timezone.utc)
    episodes = [
        _make_episode("ep1", shadow_action="approve", action_id="approve", shadow_entropy=1.0, created_at="2026-11-08T00:00:00Z"),
        _make_episode("ep2", shadow_action="approve", action_id="approve", shadow_entropy=0.5, created_at="2026-11-08T00:00:00Z"),
        _make_episode("ep3", shadow_action="approve", action_id="approve", shadow_entropy=None, created_at="2026-11-08T00:00:00Z"),
        _make_episode("ep4", shadow_action="approve", action_id="approve", shadow_entropy=float("nan"), created_at="2026-11-08T00:00:00Z"),
    ]
    res = agreement(episodes, "ctx-17", now=now, max_evidence_age_days=10)
    assert res["n"] == 4
    assert res["k"] == 4
    assert res["mean_shadow_entropy_bits"] == pytest.approx(0.75, abs=1e-9)


def test_ac2_agreement_drops_episode_without_final_action() -> None:
    """I5: an episode with neither correct_action_id nor action_id has no final action."""
    now = datetime(2026, 11, 10, 0, 0, tzinfo=timezone.utc)
    episodes = [
        _make_episode("ep1", shadow_action="approve", action_id="approve", created_at="2026-11-08T00:00:00Z"),
        _make_episode("ep2", shadow_action="approve", action_id=None, created_at="2026-11-08T00:00:00Z"),
    ]
    res = agreement(episodes, "ctx-17", now=now, max_evidence_age_days=10)
    assert res["n"] == 1
    assert res["k"] == 1
    assert res["final_action_counts"] == {"approve": 1}


# --- AC_3: Fail Closed --------------------------------------------------------------


def test_ac3_agreement_fail_closed_on_none_or_invalid_window() -> None:
    now = datetime(2026, 11, 10, 0, 0, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="max_evidence_age_days"):
        agreement([], "ctx-17", now=now, max_evidence_age_days=None)

    with pytest.raises(ValueError, match="max_evidence_age_days"):
        agreement([], "ctx-17", now=now, max_evidence_age_days=0)

    with pytest.raises(ValueError, match="max_evidence_age_days"):
        agreement([], "ctx-17", now=now, max_evidence_age_days=-5)


# --- AC_4: Gate Arithmetic ----------------------------------------------------------


def test_ac4_gate_arithmetic_wilson_lower_bounds_and_eligibility() -> None:
    # 20 of 20: 0.8389 -> ineligible (< 0.90)
    res_20 = {"n": 20, "k": 20, "final_action_counts": {"a": 20}, "modal_action": "a", "base_rate": 1.0, "mean_shadow_entropy_bits": 0.5}
    prop_20 = propose_bucket(res_20)
    assert prop_20["wilson_lower"] == pytest.approx(0.8389, abs=1e-4)
    assert prop_20["eligible"] is False
    assert "below" in prop_20["reason"].lower()

    # 34 of 34: 0.8985 -> ineligible (< 0.90)
    res_34 = {"n": 34, "k": 34, "final_action_counts": {"a": 34}, "modal_action": "a", "base_rate": 1.0, "mean_shadow_entropy_bits": 0.5}
    prop_34 = propose_bucket(res_34)
    assert prop_34["wilson_lower"] == pytest.approx(0.8985, abs=1e-4)
    assert prop_34["eligible"] is False

    # 35 of 35: 0.9011 -> eligible (>= 0.90)
    res_35 = {"n": 35, "k": 35, "final_action_counts": {"a": 35}, "modal_action": "a", "base_rate": 1.0, "mean_shadow_entropy_bits": 0.5}
    prop_35 = propose_bucket(res_35)
    assert prop_35["wilson_lower"] == pytest.approx(0.9011, abs=1e-4)
    assert prop_35["eligible"] is True

    # n below minimum outcomes (e.g. 19 of 19) -> ineligible
    res_19 = {"n": 19, "k": 19, "final_action_counts": {"a": 19}, "modal_action": "a", "base_rate": 1.0, "mean_shadow_entropy_bits": 0.5}
    prop_19 = propose_bucket(res_19)
    assert prop_19["eligible"] is False
    assert "minimum" in prop_19["reason"].lower() or "outcomes" in prop_19["reason"].lower()


@pytest.mark.parametrize(("k", "n"), [(20, 20), (34, 34), (35, 35), (33, 35), (19, 19)])
def test_ac4_reported_bound_equals_wilson_lower_bound(k: int, n: int) -> None:
    """AC_4 "equals": the reported bound is wilson_lower_bound(k, n) itself, not a rounded copy."""
    res = {"n": n, "k": k, "final_action_counts": {"a": n}, "modal_action": "a", "base_rate": 1.0, "mean_shadow_entropy_bits": 0.5}
    assert propose_bucket(res)["wilson_lower"] == wilson_lower_bound(k, n)


def test_ac4_gate_compares_unrounded_bound() -> None:
    """I3: 35 of 35 has a bound of 0.901096...; a gate of 0.9011 must refuse it."""
    res = {"n": 35, "k": 35, "final_action_counts": {"a": 35}, "modal_action": "a", "base_rate": 1.0, "mean_shadow_entropy_bits": 0.5}
    assert wilson_lower_bound(35, 35) < 0.9011
    gate = AutonomyConfig(min_outcomes=20, min_correctness_lower_bound=0.9011)
    assert propose_bucket(res, gate)["eligible"] is False


# --- AC_5: Reported Beside Base Rate ------------------------------------------------


def test_ac5_reported_beside_base_rate() -> None:
    # 100 episodes: 95 'approve', 5 'reject'. Shadow perfectly agrees with final action (k=100)
    res = {
        "n": 100,
        "k": 100,
        "final_action_counts": {"approve": 95, "reject": 5},
        "modal_action": "approve",
        "base_rate": 0.95,
        "mean_shadow_entropy_bits": 0.42,
    }
    prop = propose_bucket(res)
    assert prop["base_rate"] == pytest.approx(0.95, abs=1e-9)
    assert prop["modal_action"] == "approve"
    assert prop["n"] == 100
    assert prop["k"] == 100
    assert prop["mean_shadow_entropy_bits"] == pytest.approx(0.42, abs=1e-9)
    assert prop["eligible"] is True
    # The proposal object is serializable
    assert json.loads(json.dumps(prop)) == prop


def test_ac5_base_rate_from_episodes_beside_perfect_agreement() -> None:
    """AC_5 end to end: 95 of 100 final actions are 'approve' and the shadow always agrees."""
    now = datetime(2026, 11, 10, 0, 0, tzinfo=timezone.utc)
    episodes = [
        _make_episode(
            f"ep{i}",
            shadow_action="approve" if i < 95 else "reject",
            action_id="approve" if i < 95 else "reject",
            created_at="2026-11-08T00:00:00Z",
        )
        for i in range(100)
    ]
    prop = propose_bucket(agreement(episodes, "ctx-17", now=now, max_evidence_age_days=10))
    assert prop["n"] == 100
    assert prop["k"] == 100
    assert prop["base_rate"] == pytest.approx(0.95, abs=1e-9)
    assert prop["modal_action"] == "approve"


# --- AC_6: Never A Reward -----------------------------------------------------------


def test_ac6_no_learner_reads_shadow_low_action_ast_check() -> None:
    """AST analysis confirms neither upstream nor ext learners read shadow_low_action."""
    learner_dirs = [
        ROOT / "src" / "agent_learning" / "learners",
        ROOT / "src" / "agent_learning_ext" / "learners",
    ]
    for l_dir in learner_dirs:
        if not l_dir.is_dir():
            continue
        for py_file in l_dir.glob("*.py"):
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    assert "shadow_low_action" not in node.value, (
                        f"{py_file.name} references 'shadow_low_action'"
                    )


@pytest.mark.parametrize("learner_cls", [UpstreamReinforceLearner, ExtReinforceLearner], ids=["upstream", "ext"])
def test_ac6_reinforce_learner_invariance_to_shadow_low_action(learner_cls: Any) -> None:
    """ReinforceLearner gives identical logits whether shadow_low_action is present or absent (I6)."""
    actions = [Action(id="approve"), Action(id="reject")]
    policy_base = SoftmaxPolicy.from_actions(actions, agent_id="test-agent")
    policy_with_shadow = SoftmaxPolicy.from_actions(actions, agent_id="test-agent")
    initial = dict(policy_base.snapshot().logits)

    episodes_clean: list[Episode] = []
    episodes_shadow: list[Episode] = []
    rewards: list[Reward] = []
    for i in range(10):
        ep_id = f"ep-{i}"
        act = "approve" if i % 2 == 0 else "reject"
        common: dict[str, Any] = {
            "id": ep_id,
            "agent_id": "test-agent",
            "user_input": "input",
            "assistant_output": "output",
            "action_id": act,
            "action_logprob": math.log(0.5),
        }
        episodes_clean.append(Episode(**common, metadata={"feedback_status": "accepted"}))
        episodes_shadow.append(
            Episode(
                **common,
                metadata={
                    "feedback_status": "accepted",
                    # The shadow names the opposite action, so reading it as a label would change the update.
                    **shadow_record("reject" if act == "approve" else "approve", 0.5),
                },
            )
        )
        rewards.append(Reward(episode_id=ep_id, value=1.0 if act == "approve" else -0.5, source=RewardSource.AGGREGATE))

    learner_cls().update(policy_base, episodes_clean, rewards)
    learner_cls().update(policy_with_shadow, episodes_shadow, rewards)

    logits_clean = policy_base.snapshot().logits
    logits_shadow = policy_with_shadow.snapshot().logits
    # Non-vacuous: the learner actually trained on these episodes.
    assert logits_clean != initial
    assert logits_shadow == logits_clean
