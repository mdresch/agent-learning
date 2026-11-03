"""Contract tests for Epic 19, Story 19.2 (Pooling Beta Counts).

Story: docs/user-stories/epic-19-hierarchical-meta-prior-compilation.md, Story 19.2.
ADR-019 §4.1 and §4.2; BRD-019; FDD-019 §2.1, §2.2, §3 item 3.

The members are built here and are synthetic: no converged Thompson family exists in the recorded
store (FDD-019 §8). The numbers are arithmetic checks, not evidence.

Interpretation I1: the worked check of FDD-019 §3 is "for one role", so the story's fixture is four
members that each have the single role ``approve``. A second test pools two roles, each on its own.

Interpretation I2: ``values[role]`` is the pair ``(alpha, beta)`` as a tuple; ``role_spread[role]`` is
the standard deviation of the members' payoff rates ``(alpha - 1) / (alpha + beta - 2)``, with
``K - 1`` in the denominator, not a spread of alpha or beta.

Interpretation I3: refusing a member with ``alpha + beta <= 2``, a ``kappa_prior`` outside (0, 10]
and a family of fewer than 4 is Story 19.3. The fixtures are valid by construction.
"""

from __future__ import annotations

import math

import pytest

from agent_learning.meta_prior import FamilyMember, MetaPrior, compile_meta_prior

PAIRS = [(14.0, 4.0), (9.0, 3.0), (21.0, 5.0), (11.0, 3.0)]
SIGMA = 0.25


def _member(index: int, pair: tuple[float, float], *, action: str = "approve", role: str = "approve") -> FamilyMember:
    return FamilyMember(
        task_id=f"task-{index}",
        version=index + 1,
        role_map={action: role},
        params={action: pair},
        gate_passed=True,
    )


def _family(pairs: list[tuple[float, float]] = PAIRS, **kw) -> list[FamilyMember]:
    return [_member(i, pair, **kw) for i, pair in enumerate(pairs)]


def _compile(members: list[FamilyMember], **kw) -> MetaPrior:
    return compile_meta_prior(members, representation="thompson", sigma_het=SIGMA, **kw)


def _expected(pairs: list[tuple[float, float]], kappa: float) -> tuple[float, float, float]:
    """FDD-019 §3 item 3, written out again: payoff rates, pooled rate, prior, spread with K - 1."""
    rates = [(a - 1.0) / (a + b - 2.0) for a, b in pairs]
    pbar = sum(a - 1.0 for a, _ in pairs) / sum(a + b - 2.0 for a, b in pairs)
    mean = sum(rates) / len(rates)
    spread = math.sqrt(sum((p - mean) ** 2 for p in rates) / (len(rates) - 1))
    return 1.0 + kappa * pbar, 1.0 + kappa * (1.0 - pbar), spread


def test_ac0_the_worked_check_gives_the_pooled_rate_and_the_prior() -> None:
    prior = _compile(_family(), kappa_prior=10.0)
    alpha, beta = prior.values["approve"]

    pbar = (13 + 8 + 20 + 10) / (16 + 10 + 24 + 12)
    assert pbar == pytest.approx(0.8226, abs=1e-4)
    assert (alpha, beta) == pytest.approx((9.226, 2.774), abs=1e-3)

    expected_alpha, expected_beta, _ = _expected(PAIRS, 10.0)
    assert (alpha, beta) == pytest.approx((expected_alpha, expected_beta), abs=1e-12)
    assert alpha - 1.0 == pytest.approx(10.0 * pbar, abs=1e-12)
    assert beta - 1.0 == pytest.approx(10.0 * (1.0 - pbar), abs=1e-12)


def test_ac1_the_spread_is_over_payoff_rates_not_counts() -> None:
    prior = _compile(_family())
    assert prior.role_spread["approve"] == pytest.approx(0.0164, abs=1e-4)
    assert prior.role_spread["approve"] == pytest.approx(_expected(PAIRS, 10.0)[2], abs=1e-12)

    rates = [13 / 16, 8 / 10, 20 / 24, 10 / 12]
    assert rates == pytest.approx([0.8125, 0.8, 0.8333, 0.8333], abs=1e-4)


def test_ac2_kappa_scales_the_prior_and_the_default_is_ten() -> None:
    pbar = 51 / 62
    prior = _compile(_family(), kappa_prior=5.0)
    assert prior.values["approve"] == pytest.approx((1.0 + 5.0 * pbar, 1.0 + 5.0 * (1.0 - pbar)), abs=1e-12)
    assert prior.kappa_prior == 5.0

    default = _compile(_family())
    assert default.kappa_prior == 10.0
    assert default.values["approve"] == _compile(_family(), kappa_prior=10.0).values["approve"]


def test_ac2_the_prior_strength_is_kappa_whatever_the_members_counts() -> None:
    small = _compile(_family([(3.0, 2.0), (4.0, 3.0), (2.0, 2.0), (5.0, 2.0)]), kappa_prior=7.0)
    big = _compile(_family([(300.0, 200.0), (400.0, 300.0), (200.0, 200.0), (500.0, 200.0)]), kappa_prior=7.0)
    for prior in (small, big):
        alpha, beta = prior.values["approve"]
        assert alpha + beta - 2.0 == pytest.approx(7.0, abs=1e-12)


def test_ac3_action_ids_do_not_matter_only_roles() -> None:
    base = _compile(_family())
    renamed = _compile(_family(action="verdict_yes"))
    # per role: older pytest versions cannot approx a mapping whose values are tuples
    assert renamed.values["approve"] == pytest.approx(base.values["approve"], abs=1e-12)
    assert renamed.role_spread == pytest.approx(base.role_spread, abs=1e-12)
    assert renamed.roles == base.roles


def test_ac3_the_record_names_the_representation_and_kappa() -> None:
    prior = _compile(_family(), kappa_prior=4.0)
    assert prior.representation == "thompson"
    assert prior.kappa_prior == 4.0
    assert prior.member_count == 4
    assert prior.sigma_het == SIGMA
    assert prior.roles == ("approve",)
    assert prior.compiled_from == (("task-0", 1), ("task-1", 2), ("task-2", 3), ("task-3", 4))


def test_two_roles_are_pooled_each_on_its_own() -> None:
    reject_pairs = [(3.0, 9.0), (2.0, 6.0), (4.0, 11.0), (3.0, 8.0)]
    members = []
    for i, (yes, no) in enumerate(zip(PAIRS, reject_pairs)):
        members.append(
            FamilyMember(
                task_id=f"task-{i}",
                version=i + 1,
                role_map={"a": "approve", "r": "reject"},
                params={"a": yes, "r": no},
                gate_passed=True,
            )
        )
    prior = _compile(members, kappa_prior=10.0)
    assert prior.roles == ("approve", "reject")
    for role, pairs in (("approve", PAIRS), ("reject", reject_pairs)):
        alpha, beta, spread = _expected(pairs, 10.0)
        assert prior.values[role] == pytest.approx((alpha, beta), abs=1e-12)
        assert prior.role_spread[role] == pytest.approx(spread, abs=1e-12)


def test_the_order_of_members_changes_nothing_in_the_values() -> None:
    base = _compile(_family())
    reversed_prior = _compile(list(reversed(_family())))
    assert reversed_prior.values["approve"] == pytest.approx(base.values["approve"], abs=1e-12)
    assert reversed_prior.role_spread["approve"] == pytest.approx(base.role_spread["approve"], abs=1e-12)


def test_the_inputs_are_not_changed() -> None:
    members = _family()
    before = [(m.task_id, dict(m.role_map), dict(m.params)) for m in members]
    _compile(members)
    assert [(m.task_id, dict(m.role_map), dict(m.params)) for m in members] == before
