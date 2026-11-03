"""Contract tests for Epic 19, Story 19.4 (Declaring and Finding Members).

Story: docs/user-stories/epic-19-hierarchical-meta-prior-compilation.md, Story 19.4.
ADR-019 §4.1 and §4.3; BRD-019 (BRU-019-01, BRU-019-03, BRU-019-04); FDD-019 §1 item 2, §2.3, §3 items 6
and 7 (steps 1 and 2) and H1, H2, H5.

The members are built here and are synthetic: no converged same-family low-authority policy exists in the
recorded store (FDD-019 §8).

Interpretation I1: member discovery is a function in ``cli.py``, ``_scan_family(store, agent_id, family)``
(FDD-019 §1 item 2: the CLI reads the store and builds the pure module's inputs). It returns a ``FamilyScan``
with ``members`` (sorted by task id), ``excluded`` (``{"task_id", "reason"}``, the content of the validation
report) and ``representation``. The command that calls it, ``task-policy-meta-compile``, is Story 19.5, so
AC_4's "exits non-zero" for a mix is pinned here as the ``ValueError`` the command will turn into an exit
code; Story 19.5 tests the exit code.

Interpretation I2: ``task-policy-family-set`` needs an active policy for the task but not a decision
policy, because FDD-019 §3 item 6 lists only the family, role-map and action errors. The role map must name
exactly the policy's action ids and send them to distinct, non-empty roles. A family name that is empty or
only whitespace is empty.

Interpretation I3: ``gate_passed`` is ``assess_autonomy(store, snapshot, AutonomyConfig.for_tier("standard"))
.eligible`` (H1), computed through ``cli._gate_passed``. ``assess_autonomy`` reads logits, and a Thompson
snapshot keeps its logits at zero (FDD-015 §1 item 3), so a Thompson member cannot pass the standard-tier
action-probability criterion today. AC_4's Thompson reading is therefore tested with ``_gate_passed``
replaced, and AC_3 uses the real gate on softmax members. That gap is reported in the PR, not hidden here.

Interpretation I4: members are found among the agent's tasks in task-id order; a snapshot whose
``is_family_meta_prior`` is true is never a candidate, whatever its ``family``.
"""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path

import pytest

from agent_learning import cli
from agent_learning.autonomy import assess_autonomy
from agent_learning.config import AutonomyConfig
from agent_learning.meta_prior import FamilyMember
from agent_learning.storage import InMemoryStore
from agent_learning.storage.local import LocalFileStore
from agent_learning.types import Action, Episode, PolicySnapshot, Reward, RewardSource

AGENT = "agent"
FAMILY = "approve-gates"
ROLES = ("approve", "reject", "revise")
ROLE_MAP = {role: role for role in ROLES}


@pytest.fixture(autouse=True)
def _clear_autonomy_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in list(os.environ):
        if name.startswith("AGENT_LEARNING_AUTONOMY_"):
            monkeypatch.delenv(name)


def _policy(task_id: str, version: int, **metadata: object) -> PolicySnapshot:
    meta = {"policy_scope": "delegated_decision", "decision_authority": "low", **metadata}
    return PolicySnapshot(
        id=f"{task_id}-v{version}",
        agent_id=AGENT,
        task_id=task_id,
        version=version,
        actions=[Action(id=role) for role in ROLES],
        logits={"approve": 2.0, "reject": 0.0, "revise": 0.0},
        episodes_seen=version * 20,
        updates_applied=version,
        metadata=meta,
    )


def _outcomes(store: InMemoryStore, task_id: str, count: int) -> None:
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
        store.store_reward(
            Reward(episode_id=episode.id, agent_id=AGENT, source=RewardSource.AGGREGATE, value=0.7)
        )


def _add_member(store: InMemoryStore, task_id: str, *, outcomes: int = 40, **metadata: object) -> None:
    meta: dict[str, object] = {"family": FAMILY, "role_map": dict(ROLE_MAP)}
    meta.update(metadata)
    for version in range(1, 4):
        store.store_policy(_policy(task_id, version, **meta))
    _outcomes(store, task_id, outcomes)


def _scan(store: InMemoryStore, family: str = FAMILY):
    return cli._scan_family(store, AGENT, family)


# ---- AC_0: declaring ------------------------------------------------------------------------------


@pytest.fixture
def file_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> LocalFileStore:
    store = LocalFileStore(tmp_path / "store")
    monkeypatch.setattr(cli, "get_default_store", lambda: store)
    return store


def _family_set(task: str, family: str, role_map: object) -> int:
    raw = role_map if isinstance(role_map, str) else json.dumps(role_map)
    return cli.main(
        ["task-policy-family-set", "--agent-id", AGENT, "--task-id", task, "--family", family, "--role-map", raw]
    )


def test_ac0_family_set_writes_family_and_role_map_without_changing_id_or_version(
    file_store: LocalFileStore,
) -> None:
    file_store.store_policy(_policy("member-1", 2))
    before = file_store.get_active_policy(AGENT, "member-1")
    assert before is not None

    assert _family_set("member-1", FAMILY, ROLE_MAP) == 0

    after = file_store.get_active_policy(AGENT, "member-1")
    assert after is not None
    assert after.id == before.id
    assert after.version == before.version
    assert after.metadata["family"] == FAMILY
    assert after.metadata["role_map"] == ROLE_MAP
    expected = before.to_dict()
    expected["metadata"] = {**before.metadata, "family": FAMILY, "role_map": ROLE_MAP}
    assert after.to_dict() == expected
    assert len(file_store.list_policies(AGENT, "member-1")) == 1


def test_ac0_family_set_prints_the_result(file_store: LocalFileStore, capsys: pytest.CaptureFixture[str]) -> None:
    file_store.store_policy(_policy("member-1", 1))
    assert _family_set("member-1", FAMILY, ROLE_MAP) == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed["family"] == FAMILY
    assert printed["role_map"] == ROLE_MAP


def test_ac0_family_set_can_be_repeated_and_replaces_the_declaration(file_store: LocalFileStore) -> None:
    file_store.store_policy(_policy("member-1", 1))
    assert _family_set("member-1", FAMILY, ROLE_MAP) == 0
    other = {"approve": "yes", "reject": "no", "revise": "maybe"}
    assert _family_set("member-1", "other-family", other) == 0
    snapshot = file_store.get_active_policy(AGENT, "member-1")
    assert snapshot is not None
    assert snapshot.metadata["family"] == "other-family"
    assert snapshot.metadata["role_map"] == other


@pytest.mark.parametrize(
    ("family", "role_map"),
    [
        ("", ROLE_MAP),
        ("   ", ROLE_MAP),
        (FAMILY, {"approve": "x", "reject": "x", "revise": "y"}),  # two actions on one role
        (FAMILY, {"approve": "approve", "reject": "reject"}),  # misses an action
        (FAMILY, {**ROLE_MAP, "ghost": "extra"}),  # an action outside the policy's actions
        (FAMILY, {"approve": "approve", "reject": "", "revise": "revise"}),  # an empty role
        (FAMILY, {"approve": "approve", "reject": 3, "revise": "revise"}),  # a role that is not a string
        (FAMILY, "not json"),
        (FAMILY, "[1, 2]"),
    ],
    ids=["empty-family", "blank-family", "not-injective", "misses-action", "unknown-action", "empty-role",
         "role-not-string", "bad-json", "not-an-object"],
)
def test_ac0_family_set_refuses_and_leaves_the_snapshot_unchanged(
    file_store: LocalFileStore, family: str, role_map: object
) -> None:
    file_store.store_policy(_policy("member-1", 2))
    before = copy.deepcopy(file_store.get_active_policy(AGENT, "member-1").to_dict())

    assert _family_set("member-1", family, role_map) != 0

    after = file_store.get_active_policy(AGENT, "member-1")
    assert after is not None
    assert after.to_dict() == before
    assert len(file_store.list_policies(AGENT, "member-1")) == 1


def test_ac0_family_set_refuses_a_task_with_no_policy(file_store: LocalFileStore) -> None:
    assert _family_set("nobody", FAMILY, ROLE_MAP) != 0
    assert file_store.list_agent_tasks(AGENT) == []


# ---- AC_1: declared only --------------------------------------------------------------------------


def test_ac1_only_a_policy_that_declares_the_family_is_a_member() -> None:
    store = InMemoryStore()
    _add_member(store, "member-a")
    _add_member(store, "member-b")
    # similar actions, no family declared
    for version in range(1, 4):
        store.store_policy(_policy("lookalike", version, role_map=dict(ROLE_MAP)))
    _outcomes(store, "lookalike", 40)
    # another family
    _add_member(store, "member-c", family="another-family")

    scan = _scan(store)

    assert [m.task_id for m in scan.members] == ["member-a", "member-b"]
    assert scan.excluded == []


def test_ac1_a_meta_prior_snapshot_is_never_a_member() -> None:
    store = InMemoryStore()
    _add_member(store, "member-a")
    store.store_policy(
        _policy("the-prior", 1, family=FAMILY, role_map=dict(ROLE_MAP), is_family_meta_prior=True)
    )
    _outcomes(store, "the-prior", 40)

    scan = _scan(store)

    assert [m.task_id for m in scan.members] == ["member-a"]
    assert scan.excluded == []


# ---- AC_2: exclusions with reasons ---------------------------------------------------------------


def test_ac2_unqualified_candidates_are_excluded_with_reasons_and_the_rest_become_members() -> None:
    store = InMemoryStore()
    _add_member(store, "good-1")
    _add_member(store, "good-2")
    _add_member(store, "full-authority", decision_authority="full")
    _add_member(store, "no-map", role_map=None)
    _add_member(store, "too-few-outcomes", outcomes=5)

    scan = _scan(store)

    assert [m.task_id for m in scan.members] == ["good-1", "good-2"]
    reasons = {item["task_id"]: item["reason"] for item in scan.excluded}
    assert set(reasons) == {"full-authority", "no-map", "too-few-outcomes"}
    assert "full" in reasons["full-authority"]
    assert "role_map" in reasons["no-map"]
    assert "gate" in reasons["too-few-outcomes"]
    for member in scan.members:
        assert isinstance(member, FamilyMember)
        assert member.version == 3
        assert member.gate_passed is True
        assert member.role_map == ROLE_MAP
        assert member.params == {"approve": 2.0, "reject": 0.0, "revise": 0.0}


def test_ac2_an_empty_role_map_counts_as_no_role_map() -> None:
    store = InMemoryStore()
    _add_member(store, "empty-map", role_map={})
    scan = _scan(store)
    assert scan.members == []
    assert [item["task_id"] for item in scan.excluded] == ["empty-map"]
    assert "role_map" in scan.excluded[0]["reason"]


# ---- AC_3: the gate is computed ------------------------------------------------------------------


def test_ac3_gate_passed_equals_assess_autonomy_with_the_standard_tier() -> None:
    store = InMemoryStore()
    _add_member(store, "enough", outcomes=40)
    _add_member(store, "too-few", outcomes=5)
    standard = AutonomyConfig.for_tier("standard")

    for task_id, expected in (("enough", True), ("too-few", False)):
        snapshot = store.get_active_policy(AGENT, task_id)
        assert snapshot is not None
        assert assess_autonomy(store, snapshot, standard).eligible is expected
        assert cli._gate_passed(store, snapshot) is expected

    scan = _scan(store)
    assert [m.task_id for m in scan.members] == ["enough"]
    assert [item["task_id"] for item in scan.excluded] == ["too-few"]


def test_ac3_the_standard_tier_is_stricter_than_the_policys_own_default() -> None:
    """Five outcomes pass the low tier but not the standard one; the gate used is the standard one (H1)."""
    store = InMemoryStore()
    _add_member(store, "five", outcomes=5)
    snapshot = store.get_active_policy(AGENT, "five")
    assert snapshot is not None
    assert assess_autonomy(store, snapshot, AutonomyConfig.for_tier("low")).eligible is True
    assert cli._gate_passed(store, snapshot) is False


# ---- AC_4: representation ------------------------------------------------------------------------


def _thompson(store: InMemoryStore, task_id: str, alpha: dict, beta: dict) -> None:
    _add_member(store, task_id, posterior_parameters={"alpha": alpha, "beta": beta})


def test_ac4_thompson_members_are_read_as_pairs_keyed_by_action_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "_gate_passed", lambda store, snapshot: True)  # I3
    store = InMemoryStore()
    _thompson(store, "t-1", {"approve": 14, "reject": 3, "revise": 2}, {"approve": 4, "reject": 8, "revise": 3})
    _thompson(store, "t-2", {"approve": 9}, {"approve": 3})  # reject and revise read as the prior

    scan = _scan(store)

    assert scan.representation == "thompson"
    by_task = {m.task_id: m for m in scan.members}
    assert by_task["t-1"].params == {"approve": (14.0, 4.0), "reject": (3.0, 8.0), "revise": (2.0, 3.0)}
    assert by_task["t-2"].params == {"approve": (9.0, 3.0), "reject": (1.0, 1.0), "revise": (1.0, 1.0)}


def test_ac4_members_without_posterior_parameters_are_read_as_logits() -> None:
    store = InMemoryStore()
    _add_member(store, "s-1")
    _add_member(store, "s-2")
    scan = _scan(store)
    assert scan.representation == "softmax"
    assert all(isinstance(value, float) for m in scan.members for value in m.params.values())


def test_ac4_a_mix_is_refused_naming_the_tasks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "_gate_passed", lambda store, snapshot: True)
    store = InMemoryStore()
    _add_member(store, "soft-1")
    _thompson(store, "beta-1", {"approve": 5}, {"approve": 2})

    with pytest.raises(ValueError) as caught:
        _scan(store)
    assert "soft-1" in str(caught.value)
    assert "beta-1" in str(caught.value)


def test_ac4_no_members_means_no_representation() -> None:
    scan = _scan(InMemoryStore())
    assert scan.members == []
    assert scan.excluded == []
    assert scan.representation is None


# ---- AC_5: read only -----------------------------------------------------------------------------


class _ReadOnlyStore(InMemoryStore):
    """An in-memory store that fails the test on any write."""

    def _refuse(self, *args: object, **kwargs: object):
        raise AssertionError("the scan must not write to the store")

    store_policy = store_episode = store_reward = store_run = store_metric_results = _refuse  # type: ignore[assignment]


def test_ac5_reading_members_writes_nothing() -> None:
    writable = InMemoryStore()
    _add_member(writable, "member-a")
    _add_member(writable, "too-few", outcomes=5)
    _add_member(writable, "no-map", role_map=None)

    reader = _ReadOnlyStore()
    reader._policies = writable._policies
    reader._active_policies = writable._active_policies
    reader._episodes = writable._episodes
    reader._rewards = writable._rewards
    before = {key: copy.deepcopy(value.to_dict()) for key, value in writable._policies.items()}

    scan = cli._scan_family(reader, AGENT, FAMILY)

    assert [m.task_id for m in scan.members] == ["member-a"]
    assert {key: value.to_dict() for key, value in writable._policies.items()} == before
