"""Contract tests for Epic 19, Story 19.6 (Seeding a New Policy).

Story: docs/user-stories/epic-19-hierarchical-meta-prior-compilation.md, Story 19.6.
ADR-019 §4.2 and Invariants; BRD-019 (BRU-019-09); FDD-019 §3 items 4 and 5, §4 H7, H8; FDD-020 §2.2 (the
``warm_start_*`` provenance).

The members are built here and are synthetic (FDD-019 §8).

Interpretation I1: ``seed_values(prior, role_map, action_ids)`` returns a new ``dict`` keyed by the new policy's
action ids, in the order of ``action_ids``. A softmax prior gives a float per action (the prior's zero-centred
value for the role), a Thompson prior an ``(alpha, beta)`` tuple.

Interpretation I2: the bijection check is on the keys of ``role_map`` (they must be exactly ``action_ids``, each
once) and on its values (distinct, and exactly ``prior.roles``); every cause is a ``ValueError`` naming the
action or role at fault.

Interpretation I3: AC_5 compiles a prior through the command (so a stored prior exists) and also pools the same
members in memory, because ``seed_values`` takes a ``MetaPrior``. Reading a stored prior back into a
``MetaPrior`` is the seeding command's job (Epic 20, Story 20.5) and is not built here.
"""

from __future__ import annotations

import copy
import os

import pytest

from agent_learning_ext import cli
from agent_learning import meta_prior as meta_prior_module
from agent_learning_ext.autonomy import assess_autonomy
from agent_learning_ext.config import AutonomyConfig
from agent_learning.meta_prior import FamilyMember, MetaPrior, compile_meta_prior, seed_values
from agent_learning.storage import InMemoryStore
from agent_learning.types import Action, PolicySnapshot

ROLES = ("approve", "reject", "revise")
STRONG = [[2.0, 0.0, 0.0], [2.1, 0.1, 0.0], [1.9, 0.0, 0.1], [2.0, -0.1, 0.1]]
RATES = [
    {"approve": 0.82, "reject": 0.30, "revise": 0.20},
    {"approve": 0.84, "reject": 0.28, "revise": 0.22},
    {"approve": 0.80, "reject": 0.32, "revise": 0.18},
    {"approve": 0.83, "reject": 0.30, "revise": 0.20},
]
NEW_IDS = ["accept", "decline", "ask"]  # different ids, in an order that is not the family's
NEW_MAP = {"accept": "approve", "decline": "reject", "ask": "revise"}


@pytest.fixture(autouse=True)
def _clear_autonomy_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in list(os.environ):
        if name.startswith("AGENT_LEARNING_AUTONOMY_"):
            monkeypatch.delenv(name)


def _softmax_prior() -> MetaPrior:
    members = [
        FamilyMember(f"m-{i}", 1, {r: r for r in ROLES}, dict(zip(ROLES, row)), True) for i, row in enumerate(STRONG)
    ]
    return compile_meta_prior(members, representation="softmax", sigma_het=0.5)


def _thompson_prior() -> MetaPrior:
    members = [
        FamilyMember(
            f"b-{i}",
            1,
            {r: r for r in ROLES},
            {r: (rates[r] * 50, (1.0 - rates[r]) * 50) for r in ROLES},
            True,
        )
        for i, rates in enumerate(RATES)
    ]
    return compile_meta_prior(members, representation="thompson", sigma_het=0.5, kappa_prior=8.0)


# ---- AC_0: through the map -----------------------------------------------------------------------


def test_ac0_each_action_gets_the_value_of_the_role_its_map_names() -> None:
    prior = _softmax_prior()
    seeded = seed_values(prior, NEW_MAP, NEW_IDS)
    assert list(seeded) == NEW_IDS
    assert seeded["accept"] == prior.values["approve"]
    assert seeded["decline"] == prior.values["reject"]
    assert seeded["ask"] == prior.values["revise"]


def test_ac0_a_different_order_gives_the_same_value_per_role() -> None:
    prior = _softmax_prior()
    shuffled = ["ask", "accept", "decline"]
    seeded = seed_values(prior, NEW_MAP, shuffled)
    assert list(seeded) == shuffled
    assert seeded["accept"] == prior.values["approve"]
    assert seeded["ask"] == prior.values["revise"]


def test_ac0_the_map_decides_not_the_position_or_the_name() -> None:
    prior = _softmax_prior()
    swapped = {"accept": "reject", "decline": "approve", "ask": "revise"}
    seeded = seed_values(prior, swapped, NEW_IDS)
    assert seeded["accept"] == prior.values["reject"]
    assert seeded["decline"] == prior.values["approve"]


# ---- AC_1: refuses a bad map ---------------------------------------------------------------------


def test_ac1_two_actions_on_one_role_are_refused() -> None:
    with pytest.raises(ValueError, match="role"):
        seed_values(_softmax_prior(), {"accept": "approve", "decline": "approve", "ask": "revise"}, NEW_IDS)


def test_ac1_a_role_outside_the_priors_roles_is_refused_naming_it() -> None:
    with pytest.raises(ValueError, match="escalate"):
        seed_values(_softmax_prior(), {"accept": "approve", "decline": "reject", "ask": "escalate"}, NEW_IDS)


def test_ac1_a_prior_role_left_without_an_action_is_refused_naming_it() -> None:
    with pytest.raises(ValueError, match="revise"):
        seed_values(_softmax_prior(), {"accept": "approve", "decline": "reject"}, ["accept", "decline"])


def test_ac1_an_action_the_map_misses_is_refused_naming_it() -> None:
    with pytest.raises(ValueError, match="ask"):
        seed_values(_softmax_prior(), {"accept": "approve", "decline": "reject"}, NEW_IDS)


def test_ac1_a_map_entry_for_an_unknown_action_is_refused_naming_it() -> None:
    with pytest.raises(ValueError, match="ghost"):
        seed_values(_softmax_prior(), {**NEW_MAP, "ghost": "approve"}, NEW_IDS)


def test_ac1_duplicate_action_ids_are_refused() -> None:
    with pytest.raises(ValueError, match="accept"):
        seed_values(_softmax_prior(), NEW_MAP, ["accept", "accept", "decline"])


# ---- AC_2: Thompson seeding ----------------------------------------------------------------------


def test_ac2_a_thompson_prior_seeds_alpha_beta_pairs() -> None:
    prior = _thompson_prior()
    seeded = seed_values(prior, NEW_MAP, NEW_IDS)
    for action, role in NEW_MAP.items():
        value = seeded[action]
        assert isinstance(value, tuple) and len(value) == 2
        assert value == pytest.approx(prior.values[role], abs=1e-12)
    # strength kappa: alpha + beta - 2 equals the prior's kappa for every role
    assert all(a + b - 2.0 == pytest.approx(8.0, abs=1e-9) for a, b in seeded.values())


# ---- AC_3: values only, no record ----------------------------------------------------------------


def test_ac3_seed_values_changes_neither_the_prior_nor_the_map() -> None:
    prior = _softmax_prior()
    prior_copy = copy.deepcopy(prior)
    role_map = dict(NEW_MAP)
    ids = list(NEW_IDS)

    seeded = seed_values(prior, role_map, ids)

    assert prior == prior_copy
    assert role_map == NEW_MAP
    assert ids == NEW_IDS
    seeded["accept"] = 99.0  # the result is a new dict
    assert prior.values["approve"] != 99.0
    assert seed_values(prior, role_map, ids)["accept"] == prior.values["approve"]


def test_ac3_the_module_has_no_seed_record() -> None:
    assert not hasattr(meta_prior_module, "seed_record")
    assert "seed_record" not in meta_prior_module.__all__


# ---- AC_4: no borrowed evidence ------------------------------------------------------------------


def test_ac4_a_seeded_policy_with_no_episodes_is_not_eligible() -> None:
    prior = _softmax_prior()
    seeded = seed_values(prior, NEW_MAP, NEW_IDS)
    snapshot = PolicySnapshot(
        id="seeded-v0",
        agent_id="agent",
        task_id="new-task",
        version=0,
        actions=[Action(id=a) for a in NEW_IDS],
        logits={a: float(v) for a, v in seeded.items()},
        episodes_seen=0,
        updates_applied=0,
        metadata={"policy_scope": "delegated_decision", "decision_authority": "low"},
    )
    store = InMemoryStore()
    store.store_policy(snapshot)

    assessment = assess_autonomy(store, snapshot, AutonomyConfig.for_tier("standard"))

    assert assessment.eligible is False
    assert assessment.scored_outcomes == 0
    assert assessment.criteria["minimum_outcomes"]["met"] is False
    assert assessment.criteria["stable_snapshots"]["met"] is False
    # the borrowed logits are confident, so the probability criteria are not what stops it
    assert assessment.criteria["action_probability"]["met"] is True


# ---- AC_5: decoupled -----------------------------------------------------------------------------


def test_ac5_changing_the_seeded_logits_leaves_the_stored_prior_alone(monkeypatch: pytest.MonkeyPatch) -> None:
    store = InMemoryStore()
    monkeypatch.setattr(cli, "get_default_store", lambda: store)
    monkeypatch.setattr(cli, "_gate_passed", lambda s, snapshot: True)
    for i, row in enumerate(STRONG):
        for version in (1, 2, 3):
            store.store_policy(
                PolicySnapshot(
                    id=f"m-{i}-v{version}",
                    agent_id="agent",
                    task_id=f"m-{i}",
                    version=version,
                    actions=[Action(id=r) for r in ROLES],
                    logits=dict(zip(ROLES, row)),
                    updates_applied=version,
                    metadata={
                        "policy_scope": "delegated_decision",
                        "decision_authority": "low",
                        "family": "gates",
                        "role_map": {r: r for r in ROLES},
                    },
                )
            )
    assert cli.main(["task-policy-meta-compile", "--agent-id", "agent", "--family", "gates",
                     "--output-prior-name", "gates-prior", "--sigma-het", "0.5"]) == 0
    stored = store.get_active_policy("agent", "gates-prior")
    assert stored is not None
    stored_copy = copy.deepcopy(stored.to_dict())
    prior = _softmax_prior()
    prior_copy = copy.deepcopy(prior)

    seeded = seed_values(prior, NEW_MAP, NEW_IDS)
    policy = PolicySnapshot(
        id="seeded-v0",
        agent_id="agent",
        task_id="new-task",
        version=0,
        actions=[Action(id=a) for a in NEW_IDS],
        logits={a: float(v) for a, v in seeded.items()},
        metadata={"policy_scope": "delegated_decision", "decision_authority": "low"},
    )
    store.store_policy(policy)

    # the seeded policy learns on its own: its logits change and the new version is stored
    learned = PolicySnapshot.from_dict(policy.to_dict())
    learned.id, learned.version, learned.updates_applied = "seeded-v1", 1, 1
    learned.logits["accept"] += 5.0
    learned.logits["decline"] = -9.0
    store.store_policy(learned)
    seeded["accept"] = 99.0  # and so does the dict that was returned

    assert store.get_active_policy("agent", "new-task").logits["accept"] == pytest.approx(
        float(prior.values["approve"]) + 5.0, abs=1e-12
    )
    assert store.get_active_policy("agent", "gates-prior").to_dict() == stored_copy
    assert store.get_policy(stored.id, "agent").to_dict() == stored_copy
    assert prior == prior_copy


def test_the_function_is_exported_from_the_package_root() -> None:
    import agent_learning_ext as agent_learning

    assert agent_learning.seed_values is seed_values
    assert "seed_values" in agent_learning.__all__
