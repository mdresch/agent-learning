"""Contract tests for Epic 19, Story 19.8 (Reading a Posterior at the Gate).

Story: docs/user-stories/epic-19-hierarchical-meta-prior-compilation.md, Story 19.8.
ADR-003 §4.6 (and §4.3, §4.5); FDD-019 H9, §1 item 6, §3 item 7.2, §5; FDD-015 §1 item 3, §3 item 3.4.

The members are built here and are synthetic (FDD-019 §8).

What this pins: a snapshot that holds ``posterior_parameters`` keeps its logits at zero, and the gate reads
its action probabilities from the posterior means instead: ``mean = alpha / (alpha + beta)`` per action,
normalised over the actions (the same as a softmax over ``ln(mean)``).

What this does not claim (FDD-019 §7 items 8 to 10, left open on purpose): that the normalised mean is the
probability of being the best action; that the 60% and 15-point thresholds, chosen for softmax, are
calibrated for it; or that a policy with several actions of similar payoff rate can meet it. The tests use
decisions with one high-rate action and low-rate rivals, which is what the reading suits.

Interpretation I1: the "calculated logits" of the ADR are a way to say the reading is a softmax of
``ln(mean)``; AC_0 checks that equivalence numerically and the code need not compute logits at all.

Interpretation I2: an action missing from the posterior mapping reads as the prior, mean 0.5, because
``ThompsonPolicy`` reads it that way (FDD-015 §2.2).

Interpretation I3: ``_scan_family`` reads the posterior before it runs the gate (H9), so AC_8's malformed
member is excluded with the reason that ``ThompsonPolicy`` gives, and the gate is not run for it.
"""

from __future__ import annotations

import copy
import math
import os

import pytest

from agent_learning_ext import cli
from agent_learning_ext.autonomy import assess_autonomy
from agent_learning_ext.config import AutonomyConfig
from agent_learning.policy.thompson import ThompsonPolicy
from agent_learning.storage import InMemoryStore
from agent_learning.types import Action, Episode, PolicySnapshot, Reward, RewardSource

AGENT = "agent"
ROLES = ("approve", "reject", "revise")
STANDARD = AutonomyConfig.for_tier("standard")


@pytest.fixture(autouse=True)
def _clear_autonomy_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in list(os.environ):
        if name.startswith("AGENT_LEARNING_AUTONOMY_"):
            monkeypatch.delenv(name)


def _pairs(rates: dict[str, float], scale: int = 50) -> tuple[dict[str, float], dict[str, float]]:
    """alpha and beta that give each action the payoff mean ``rate`` with ``scale`` pseudo-counts."""
    return (
        {a: rate * scale for a, rate in rates.items()},
        {a: (1.0 - rate) * scale for a, rate in rates.items()},
    )


def _posterior_snapshot(
    task_id: str = "t",
    version: int = 3,
    rates: dict[str, float] | None = None,
    **metadata: object,
) -> PolicySnapshot:
    rates = rates or {"approve": 0.82, "reject": 0.30, "revise": 0.20}
    alpha, beta = _pairs(rates)
    meta: dict[str, object] = {
        "policy_scope": "delegated_decision",
        "decision_authority": "low",
        "posterior_parameters": {"alpha": alpha, "beta": beta},
        "consumed_episode_ids": [],
    }
    meta.update(metadata)
    return PolicySnapshot(
        id=f"{task_id}-v{version}",
        agent_id=AGENT,
        task_id=task_id,
        version=version,
        actions=[Action(id=a) for a in ROLES],
        logits={a: 0.0 for a in ROLES},
        episodes_seen=version * 20,
        updates_applied=version,
        metadata=meta,
    )


def _outcomes(store: InMemoryStore, task_id: str, count: int = 40) -> None:
    for index in range(count):
        episode = Episode(
            id=f"{task_id}-episode-{index}",
            agent_id=AGENT,
            task_id=task_id,
            intent_summary="Decide",
            action_id="approve",
            expected_outcome="Correct decision",
            execution_status="completed",
            result_summary="The outcome supported the decision",
            metadata={"correct_action_id": "approve", "task_completed": True},
        )
        store.store_episode(episode)
        store.store_reward(Reward(episode_id=episode.id, agent_id=AGENT, source=RewardSource.AGGREGATE, value=0.7))


def _member(store: InMemoryStore, task_id: str, rates: dict[str, float] | None = None, outcomes: int = 40, **meta: object):
    for version in range(1, 4):
        store.store_policy(_posterior_snapshot(task_id, version, rates, **meta))
    _outcomes(store, task_id, outcomes)
    snapshot = store.get_active_policy(AGENT, task_id)
    assert snapshot is not None
    return snapshot


def _expected_probabilities(rates: dict[str, float]) -> list[float]:
    means = [rates[a] for a in ROLES]
    return [m / sum(means) for m in means]


# ---- AC_0: the reading ----------------------------------------------------------------------------


def test_ac0_the_gate_reads_the_normalised_posterior_means() -> None:
    rates = {"approve": 0.82, "reject": 0.30, "revise": 0.20}
    store = InMemoryStore()
    snapshot = _member(store, "t", rates)

    assessment = assess_autonomy(store, snapshot, STANDARD)

    expected = _expected_probabilities(rates)
    ranked = sorted(expected, reverse=True)
    assert assessment.recommended_action_id == "approve"
    assert assessment.action_probability == pytest.approx(expected[0], abs=1e-12)
    assert assessment.probability_margin == pytest.approx(ranked[0] - ranked[1], abs=1e-12)
    assert assessment.action_probability == pytest.approx(0.82 / 1.32, abs=1e-12)


def test_ac0_it_is_a_softmax_over_the_log_of_the_means() -> None:
    rates = {"approve": 0.82, "reject": 0.30, "revise": 0.20}
    logits = [math.log(rates[a]) for a in ROLES]
    exps = [math.exp(x) for x in logits]
    softmax = [e / sum(exps) for e in exps]
    assert softmax == pytest.approx(_expected_probabilities(rates), abs=1e-12)

    store = InMemoryStore()
    assessment = assess_autonomy(store, _member(store, "t", rates), STANDARD)
    assert assessment.action_probability == pytest.approx(max(softmax), abs=1e-12)


def test_ac0_an_action_missing_from_the_mapping_reads_as_the_prior() -> None:
    snapshot = _posterior_snapshot(rates={"approve": 0.9})
    snapshot.metadata["posterior_parameters"] = {"alpha": {"approve": 45.0}, "beta": {"approve": 5.0}}
    store = InMemoryStore()
    store.store_policy(snapshot)

    assessment = assess_autonomy(store, snapshot, STANDARD)

    assert assessment.recommended_action_id == "approve"
    assert assessment.action_probability == pytest.approx(0.9 / (0.9 + 0.5 + 0.5), abs=1e-12)


def test_ac0_a_tie_goes_to_the_earlier_action() -> None:
    store = InMemoryStore()
    snapshot = _member(store, "t", {"approve": 0.5, "reject": 0.5, "revise": 0.5})
    assessment = assess_autonomy(store, snapshot, STANDARD)
    assert assessment.recommended_action_id == "approve"
    assert assessment.action_probability == pytest.approx(1.0 / 3.0, abs=1e-12)
    assert assessment.probability_margin == pytest.approx(0.0, abs=1e-12)


# ---- AC_1: logits untouched ----------------------------------------------------------------------


def test_ac1_assessing_leaves_the_snapshot_and_its_zero_logits_alone() -> None:
    store = InMemoryStore()
    snapshot = _member(store, "t")
    before = copy.deepcopy(snapshot.to_dict())

    assess_autonomy(store, snapshot, STANDARD)

    assert snapshot.to_dict() == before
    assert snapshot.logits == {a: 0.0 for a in ROLES}


# ---- AC_2: same as the display -------------------------------------------------------------------


def test_ac2_the_winner_probability_is_the_largest_display_probability() -> None:
    store = InMemoryStore()
    snapshot = _member(store, "t")
    shown = ThompsonPolicy.from_snapshot(snapshot).choose(request_id="r", timestamp="2026-11-03T00:00:00+00:00")
    assessment = assess_autonomy(store, snapshot, STANDARD)
    assert assessment.action_probability == pytest.approx(max(shown.probabilities), abs=1e-12)


# ---- AC_3: softmax unchanged ---------------------------------------------------------------------


def test_ac3_a_softmax_snapshot_is_assessed_as_before() -> None:
    snapshot = PolicySnapshot(
        id="s-v3",
        agent_id=AGENT,
        task_id="s",
        version=3,
        actions=[Action(id=a) for a in ROLES],
        logits={"approve": 2.0, "reject": 0.0, "revise": 0.0},
        episodes_seen=60,
        updates_applied=3,
        metadata={"policy_scope": "delegated_decision", "decision_authority": "low"},
    )
    store = InMemoryStore()
    store.store_policy(snapshot)
    exps = [math.exp(x) for x in (2.0, 0.0, 0.0)]
    probabilities = [e / sum(exps) for e in exps]

    assessment = assess_autonomy(store, snapshot, STANDARD)

    assert assessment.action_probability == pytest.approx(probabilities[0], abs=1e-12)
    assert assessment.criteria["action_probability"] == {
        "actual": assessment.action_probability,
        "required": STANDARD.min_action_probability,
        "met": assessment.action_probability >= STANDARD.min_action_probability,
    }
    assert assessment.criteria["probability_margin"] == {
        "actual": assessment.probability_margin,
        "required": STANDARD.min_probability_margin,
        "met": assessment.probability_margin >= STANDARD.min_probability_margin,
    }


# ---- AC_4: passing -------------------------------------------------------------------------------


def test_ac4_a_member_with_a_clear_winner_is_eligible_on_the_standard_tier() -> None:
    store = InMemoryStore()
    snapshot = _member(store, "good", {"approve": 0.82, "reject": 0.30, "revise": 0.20})

    assessment = assess_autonomy(store, snapshot, STANDARD)

    assert assessment.eligible is True
    assert assessment.scored_outcomes == 40
    assert assessment.stable_snapshots == 3
    assert assessment.action_probability >= STANDARD.min_action_probability
    assert assessment.probability_margin >= STANDARD.min_probability_margin
    assert all(item["met"] for item in assessment.criteria.values())


def test_ac4_equal_payoff_rates_fail_and_the_report_shows_the_value() -> None:
    store = InMemoryStore()
    snapshot = _member(store, "flat", {"approve": 0.5, "reject": 0.5, "revise": 0.5})

    assessment = assess_autonomy(store, snapshot, STANDARD)

    assert assessment.eligible is False
    criterion = assessment.criteria["action_probability"]
    assert criterion["met"] is False
    assert criterion["actual"] == pytest.approx(0.3333, abs=1e-4)
    assert criterion["required"] == 0.60


# ---- AC_5: stability -----------------------------------------------------------------------------


def test_ac5_earlier_snapshots_are_read_the_same_way() -> None:
    store = InMemoryStore()
    for version in (1, 2, 3):
        store.store_policy(_posterior_snapshot("steady", version))
    _outcomes(store, "steady")
    steady = store.get_active_policy(AGENT, "steady")
    assert steady is not None
    assert assess_autonomy(store, steady, STANDARD).stable_snapshots == 3


def test_ac5_a_history_whose_winner_changes_breaks_the_count() -> None:
    store = InMemoryStore()
    store.store_policy(_posterior_snapshot("moving", 1, {"approve": 0.2, "reject": 0.85, "revise": 0.3}))
    store.store_policy(_posterior_snapshot("moving", 2))
    store.store_policy(_posterior_snapshot("moving", 3))
    _outcomes(store, "moving")
    moving = store.get_active_policy(AGENT, "moving")
    assert moving is not None

    assessment = assess_autonomy(store, moving, STANDARD)

    assert assessment.stable_snapshots == 2
    assert assessment.eligible is False


# ---- AC_6: labelled basis ------------------------------------------------------------------------


def test_ac6_the_two_criteria_carry_the_basis_for_a_posterior_snapshot() -> None:
    store = InMemoryStore()
    assessment = assess_autonomy(store, _member(store, "t"), STANDARD)
    assert assessment.criteria["action_probability"]["basis"] == "posterior_mean"
    assert assessment.criteria["probability_margin"]["basis"] == "posterior_mean"
    assert "basis" not in assessment.criteria["minimum_outcomes"]


def test_ac6_a_softmax_snapshot_carries_no_basis() -> None:
    snapshot = PolicySnapshot(
        id="s-v1",
        agent_id=AGENT,
        task_id="s",
        version=1,
        actions=[Action(id=a) for a in ROLES],
        logits={"approve": 2.0, "reject": 0.0, "revise": 0.0},
        metadata={"policy_scope": "delegated_decision", "decision_authority": "low"},
    )
    assessment = assess_autonomy(InMemoryStore(), snapshot, STANDARD)
    assert "basis" not in assessment.criteria["action_probability"]
    assert "basis" not in assessment.criteria["probability_margin"]


def test_ac6_full_authority_keeps_its_not_applicable_report() -> None:
    snapshot = _posterior_snapshot(decision_authority="full")
    assessment = assess_autonomy(InMemoryStore(), snapshot, STANDARD)
    assert assessment.criteria["action_probability"]["status"] == "not_applicable"
    assert "basis" not in assessment.criteria["action_probability"]


# ---- AC_7: malformed posterior -------------------------------------------------------------------


@pytest.mark.parametrize(
    "posterior",
    [
        {"alpha": {"approve": math.nan}, "beta": {"approve": 5.0}},
        {"alpha": {"approve": -1.0}, "beta": {"approve": 5.0}},
        {"alpha": {"approve": 5.0}, "beta": {"approve": 0.0}},
        {"alpha": {"ghost": 5.0}, "beta": {"approve": 5.0}},
    ],
    ids=["nan", "negative", "zero-beta", "unknown-action"],
)
def test_ac7_a_malformed_posterior_is_refused_naming_the_action(posterior: dict) -> None:
    snapshot = _posterior_snapshot()
    snapshot.metadata["posterior_parameters"] = posterior
    store = InMemoryStore()
    store.store_policy(snapshot)
    before = {key: value.to_dict() for key, value in store._policies.items()}

    with pytest.raises(ValueError, match="approve|ghost"):
        assess_autonomy(store, snapshot, STANDARD)

    assert {key: value.to_dict() for key, value in store._policies.items()} == before


# ---- AC_8: through the scan ----------------------------------------------------------------------


def test_ac8_the_scan_uses_the_real_gate_for_thompson_members() -> None:
    store = InMemoryStore()
    for task in ("good-1", "good-2"):
        _member(store, task, family="gates", role_map={r: r for r in ROLES})
    _member(store, "weak", {"approve": 0.5, "reject": 0.5, "revise": 0.5}, family="gates", role_map={r: r for r in ROLES})
    bad = _member(store, "malformed", family="gates", role_map={r: r for r in ROLES})
    bad.metadata["posterior_parameters"] = {"alpha": {"approve": math.nan}, "beta": {"approve": 5.0}}
    store.store_policy(bad)

    scan = cli._scan_family(store, AGENT, "gates")

    assert scan.representation == "thompson"
    assert [m.task_id for m in scan.members] == ["good-1", "good-2"]
    for member in scan.members:
        assert member.params["approve"] == pytest.approx((41.0, 9.0), abs=1e-9)
        assert member.params["reject"] == pytest.approx((15.0, 35.0), abs=1e-9)
        assert member.gate_passed is True
    reasons = {item["task_id"]: item["reason"] for item in scan.excluded}
    assert set(reasons) == {"weak", "malformed"}
    assert "gate" in reasons["weak"]
    assert "posterior_parameters" in reasons["malformed"]


# ---- AC_9: the limits stay open ------------------------------------------------------------------


def test_ac9_the_open_limits_are_named_and_no_quality_claim_is_made() -> None:
    docstring = " ".join((__doc__ or "").split())
    assert "FDD-019 §7 items 8 to 10" in docstring
    assert "probability of being the best action" in docstring
    assert "calibrated" in docstring
    assert "several actions of similar payoff rate" in docstring
