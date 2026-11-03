"""Contract tests for Epic 19, Story 19.3 (Refusing a Bad Family).

Story: docs/user-stories/epic-19-hierarchical-meta-prior-compilation.md, Story 19.3.
ADR-019 §4.1 to §4.3 and Invariants; BRD-019; FDD-019 §2.2, §3 item 1, §5 and H1, H4, H5.

The members are built here and are synthetic (FDD-019 §8).

Interpretation I1: a member's action ids are the keys of its ``params``. Its ``role_map`` must have
exactly those keys and map them to distinct roles (a bijection onto its roles). A ``params`` action that
the map misses and a map entry whose action has no value in ``params`` are two different messages for the
same refusal, so AC_2's "misses an action" and AC_4's "an action without a value" are each pinned. "Names a
role outside the member's roles" is read as a role that the other members do not have, which is the
role-sets-differ refusal; the message names the roles.

Interpretation I2: AC_3 says a missing ``sigma_het`` raises ``ValueError``, but a required keyword that is
left out is a ``TypeError`` in Python. The parameter therefore defaults to ``None``, which means "missing";
no tuning value is invented (FDD-019 H4). An explicit ``None`` is refused the same way.

Interpretation I3: the heterogeneity check compares the largest role spread with ``sigma_het`` and refuses
when it is strictly above; it applies to both representations. A ``kappa_prior`` is validated only for the
Beta representation (FDD-019 §3 item 1), and a softmax prior ignores it.

Interpretation I4: this story replaces the ``NotImplementedError`` for an unbuilt representation with the
``ValueError`` of AC_4, and the Story 19.1 test that expected the old error now expects the new one.
"""

from __future__ import annotations

import math

import pytest

from agent_learning.meta_prior import KAPPA_MAX, MIN_FAMILY_SIZE, FamilyMember, compile_meta_prior

ROLES = ("approve", "reject", "revise")
BASE_LOGITS = [
    [1.2, -0.3, 0.1],
    [1.0, -0.1, 0.3],
    [1.4, -0.5, 0.0],
    [1.1, -0.2, 0.2],
]
PAIRS = [(14.0, 4.0), (9.0, 3.0), (21.0, 5.0), (11.0, 3.0)]


def _soft(index: int, logits: list[float], **kw) -> FamilyMember:
    fields = {
        "task_id": f"task-{index}",
        "version": index + 1,
        "role_map": {r: r for r in ROLES},
        "params": dict(zip(ROLES, logits)),
        "gate_passed": True,
    }
    fields.update(kw)
    return FamilyMember(**fields)


def _soft_family(**overrides: dict) -> list[FamilyMember]:
    return [_soft(i, row, **overrides.get(str(i), {})) for i, row in enumerate(BASE_LOGITS)]


def _beta(index: int, pair: tuple[float, float], **kw) -> FamilyMember:
    fields = {
        "task_id": f"task-{index}",
        "version": index + 1,
        "role_map": {"approve": "approve"},
        "params": {"approve": pair},
        "gate_passed": True,
    }
    fields.update(kw)
    return FamilyMember(**fields)


def _beta_family(pairs: list[tuple[float, float]] = PAIRS) -> list[FamilyMember]:
    return [_beta(i, pair) for i, pair in enumerate(pairs)]


def _soft_compile(members: list[FamilyMember], **kw):
    kw.setdefault("sigma_het", 0.25)
    return compile_meta_prior(members, representation="softmax", **kw)


def _beta_compile(members: list[FamilyMember], **kw):
    kw.setdefault("sigma_het", 0.25)
    return compile_meta_prior(members, representation="thompson", **kw)


def test_the_constants() -> None:
    assert MIN_FAMILY_SIZE == 4
    assert KAPPA_MAX == 10.0


@pytest.mark.parametrize("count", [0, 1, 2, 3])
def test_ac0_a_family_under_four_is_refused_naming_the_count(count: int) -> None:
    with pytest.raises(ValueError, match=rf"\b{count}\b.*4|4.*\b{count}\b"):
        _soft_compile(_soft_family()[:count])


def test_ac0_four_members_are_accepted() -> None:
    assert _soft_compile(_soft_family()).member_count == 4


def test_ac0_a_duplicate_task_id_is_refused_naming_it() -> None:
    members = _soft_family(**{"2": {"task_id": "task-0"}})
    with pytest.raises(ValueError, match="task-0"):
        _soft_compile(members)


def test_ac1_a_member_that_has_not_passed_the_gate_is_refused_naming_its_task() -> None:
    members = _soft_family(**{"2": {"gate_passed": False}})
    with pytest.raises(ValueError, match="task-2"):
        _soft_compile(members)


def test_ac2_two_actions_on_one_role_are_refused() -> None:
    members = _soft_family(**{"1": {"role_map": {"approve": "approve", "reject": "approve", "revise": "revise"}}})
    with pytest.raises(ValueError, match="task-1.*role"):
        _soft_compile(members)


def test_ac2_a_map_that_misses_an_action_is_refused_naming_it() -> None:
    members = _soft_family(**{"1": {"role_map": {"approve": "approve", "reject": "reject"}}})
    with pytest.raises(ValueError, match="revise"):
        _soft_compile(members)


def test_ac2_a_map_that_names_an_action_with_no_value_is_refused_naming_it() -> None:
    members = _soft_family(**{"1": {"role_map": {**{r: r for r in ROLES}, "ghost": "extra"}}})
    with pytest.raises(ValueError, match="ghost"):
        _soft_compile(members)


def test_ac2_member_role_sets_that_differ_are_refused_naming_the_roles() -> None:
    members = _soft_family(**{"3": {"role_map": {"approve": "approve", "reject": "reject", "revise": "escalate"}}})
    with pytest.raises(ValueError, match="escalate"):
        _soft_compile(members)


def test_ac3_a_sigma_het_below_the_spread_is_refused_naming_role_spread_and_sigma() -> None:
    with pytest.raises(ValueError) as caught:
        _soft_compile(_soft_family(), sigma_het=0.15)
    text = str(caught.value)
    assert "approve" in text
    assert "0.2132" in text
    assert "0.15" in text
    assert "sigma_het" in text


def test_ac3_a_sigma_het_above_the_spread_compiles() -> None:
    prior = _soft_compile(_soft_family(), sigma_het=0.25)
    assert prior.sigma_het == 0.25


def test_ac3_a_sigma_het_equal_to_the_spread_compiles() -> None:
    spread = _soft_compile(_soft_family()).role_spread["approve"]
    assert _soft_compile(_soft_family(), sigma_het=spread).sigma_het == spread


@pytest.mark.parametrize("bad", [None, math.nan, math.inf, -math.inf, 0.0, -0.25])
def test_ac3_a_missing_or_unusable_sigma_het_is_refused(bad: float | None) -> None:
    with pytest.raises(ValueError, match="sigma_het"):
        compile_meta_prior(_soft_family(), representation="softmax", sigma_het=bad)


def test_ac3_leaving_sigma_het_out_is_a_value_error() -> None:
    with pytest.raises(ValueError, match="sigma_het"):
        compile_meta_prior(_soft_family(), representation="softmax")


def test_ac3_the_spread_check_also_applies_to_beta_counts() -> None:
    with pytest.raises(ValueError, match="sigma_het"):
        _beta_compile(_beta_family(), sigma_het=0.005)
    assert _beta_compile(_beta_family(), sigma_het=0.02).representation == "thompson"


def test_ac4_an_unknown_representation_is_refused() -> None:
    with pytest.raises(ValueError, match="representation"):
        compile_meta_prior(_soft_family(), representation="bayes", sigma_het=0.25)


def test_ac4_a_pair_among_softmax_parameters_is_refused() -> None:
    members = _soft_family(**{"1": {"params": {"approve": (1.0, 2.0), "reject": 0.0, "revise": 0.1}}})
    with pytest.raises(ValueError, match="task-1"):
        _soft_compile(members)


def test_ac4_a_float_among_thompson_parameters_is_refused() -> None:
    members = _beta_family()
    members[2] = _beta(2, PAIRS[2], params={"approve": 0.8})
    with pytest.raises(ValueError, match="task-2"):
        _beta_compile(members)


def test_ac4_a_non_finite_logit_is_refused() -> None:
    members = _soft_family(**{"0": {"params": {"approve": math.nan, "reject": 0.0, "revise": 0.1}}})
    with pytest.raises(ValueError, match="task-0"):
        _soft_compile(members)


@pytest.mark.parametrize("kappa", [0.0, -1.0, 10.5, math.nan, math.inf])
def test_ac5_a_kappa_outside_zero_to_ten_is_refused(kappa: float) -> None:
    with pytest.raises(ValueError, match="kappa_prior"):
        _beta_compile(_beta_family(), kappa_prior=kappa)


@pytest.mark.parametrize("kappa", [0.001, 5.0, 10.0])
def test_ac5_a_kappa_inside_zero_to_ten_is_accepted(kappa: float) -> None:
    assert _beta_compile(_beta_family(), kappa_prior=kappa).kappa_prior == kappa


def test_ac5_a_softmax_prior_ignores_kappa() -> None:
    assert _soft_compile(_soft_family(), kappa_prior=0.0).kappa_prior is None


@pytest.mark.parametrize("pair", [(1.0, 1.0), (1.5, 0.5), (1.0, 0.5)])
def test_ac5_a_member_not_converged_is_refused_naming_member_and_role(pair: tuple[float, float]) -> None:
    members = _beta_family()
    members[1] = _beta(1, pair)
    with pytest.raises(ValueError, match="task-1.*approve|approve.*task-1"):
        _beta_compile(members)


def test_ac5_the_convergence_check_comes_before_any_pooled_rate() -> None:
    members = [_beta(i, (1.0, 1.0)) for i in range(4)]  # every denominator is zero
    with pytest.raises(ValueError):
        _beta_compile(members)  # a ZeroDivisionError would fail this


def test_ac5_a_pair_just_above_the_bound_is_accepted() -> None:
    members = _beta_family()
    members[1] = _beta(1, (1.2, 1.05))  # alpha + beta = 2.25, payoff rate 0.8
    assert _beta_compile(members).member_count == 4


def test_a_refused_family_returns_nothing_and_changes_nothing() -> None:
    members = _soft_family(**{"2": {"gate_passed": False}})
    before = [(m.task_id, dict(m.role_map), dict(m.params), m.gate_passed) for m in members]
    with pytest.raises(ValueError):
        _soft_compile(members)
    assert [(m.task_id, dict(m.role_map), dict(m.params), m.gate_passed) for m in members] == before
