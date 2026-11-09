"""Contract tests for Epic 19, Story 19.5 (Storing the Prior).

Story: docs/user-stories/epic-19-hierarchical-meta-prior-compilation.md, Story 19.5.
ADR-019 §4.3 and Invariants; BRD-019 (BRU-019-01, BRU-019-08, BRU-019-10); FDD-019 §1 item 4, §2.3, §3 item 7
(steps 3 and 4), §5 and H6, H8; ADR-002 (no new record type).

The members are built here and are synthetic (FDD-019 §8).

Interpretation I1: the "base family" of the story has logits whose own winner probabilities (0.55 to 0.64) are
below the ``standard`` tier's 60% for some members, so no member built from them can pass the real gate. The
exact-number tests (AC_0) therefore replace ``cli._gate_passed``; every other test uses members that pass the
real gate, and the Thompson family (AC_4) goes through the real gate that Story 19.8 made possible.

Interpretation I2: the first compilation under a name is version 0, like every new snapshot; each later one is
the previous version plus one. ``supersedes`` is a key of ``metadata`` (``PolicySnapshot`` has no such field), set
on every version after the first (FDD-019 §2.3, H8).

Interpretation I3: the prior is not a decision policy (no ``policy_scope``), so ``tasks-list --decision-only``
leaves it out while plain ``tasks-list`` shows it. Its ``logits`` are the pooled values for a softmax prior and
zeros for a Thompson prior, whose values are in ``posterior_parameters``.

Interpretation I4: an output name that is the task id of an existing policy that is not a meta-prior is refused,
because storing under it would overwrite or shadow a task (FDD-019 H6: the prior is its own pseudo-task).

Interpretation I5: a refusal prints its reasons to stderr, including the excluded candidates with their reasons,
and exits 2.
"""

from __future__ import annotations

import copy
import json
import math
import os
from datetime import datetime
from pathlib import Path

import pytest

from agent_learning_ext import cli
from agent_learning.storage import InMemoryStore
from agent_learning.storage.local import LocalFileStore
from agent_learning.types import Action, Episode, PolicySnapshot, Reward, RewardSource

AGENT = "agent"
FAMILY = "approve-gates"
NAME = "approve-gates-prior"
ROLES = ("approve", "reject", "revise")
ROLE_MAP = {role: role for role in ROLES}
BASE_LOGITS = [[1.2, -0.3, 0.1], [1.0, -0.1, 0.3], [1.4, -0.5, 0.0], [1.1, -0.2, 0.2]]
STRONG_LOGITS = [[2.0, 0.0, 0.0], [2.1, 0.1, 0.0], [1.9, 0.0, 0.1], [2.0, -0.1, 0.1]]


@pytest.fixture(autouse=True)
def _clear_autonomy_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in list(os.environ):
        if name.startswith("AGENT_LEARNING_AUTONOMY_"):
            monkeypatch.delenv(name)


AnyStore = InMemoryStore | LocalFileStore


@pytest.fixture
def store(monkeypatch: pytest.MonkeyPatch) -> InMemoryStore:
    memory = InMemoryStore()
    monkeypatch.setattr(cli, "get_default_store", lambda: memory)
    return memory


@pytest.fixture
def local_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> LocalFileStore:
    """Used where the active-policy pointer or the on-disk layout is the thing under test."""
    local = LocalFileStore(tmp_path / "store")
    monkeypatch.setattr(cli, "get_default_store", lambda: local)
    return local


def _outcomes(store: AnyStore, task_id: str, count: int = 40) -> None:
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


def _add_member(
    store: AnyStore,
    task_id: str,
    logits: list[float],
    *,
    outcomes: int = 40,
    posterior: tuple[dict, dict] | None = None,
    **meta: object,
) -> None:
    metadata: dict[str, object] = {"policy_scope": "delegated_decision", "decision_authority": "low"}
    metadata.update({"family": FAMILY, "role_map": dict(ROLE_MAP)})
    if posterior is not None:
        metadata["posterior_parameters"] = {"alpha": posterior[0], "beta": posterior[1]}
    metadata.update(meta)
    for version in range(1, 4):
        store.store_policy(
            PolicySnapshot(
                id=f"{task_id}-v{version}",
                agent_id=AGENT,
                task_id=task_id,
                version=version,
                actions=[Action(id=role) for role in ROLES],
                logits=dict(zip(ROLES, logits)),
                episodes_seen=version * 20,
                updates_applied=version,
                metadata=copy.deepcopy(metadata),
            )
        )
    _outcomes(store, task_id, outcomes)


def _softmax_family(store: AnyStore, rows: list[list[float]] = STRONG_LOGITS) -> None:
    for index, row in enumerate(rows):
        _add_member(store, f"member-{index}", row)


def _compile(*extra: str, family: str = FAMILY, name: str = NAME, sigma: str = "0.5") -> int:
    return cli.main(
        ["task-policy-meta-compile", "--agent-id", AGENT, "--family", family, "--output-prior-name", name,
         "--sigma-het", sigma, *extra]
    )


def _everything(store: AnyStore) -> dict[str, dict]:
    """Every stored policy snapshot, by id, as a dict."""
    out: dict[str, dict] = {}
    for task in store.list_agent_tasks(AGENT):
        for snapshot in store.list_policies(AGENT, task.id, limit=500):
            out[snapshot.id] = snapshot.to_dict()
    return out


def _centred_mean(rows: list[list[float]]) -> list[float]:
    centred = [[x - sum(row) / len(row) for x in row] for row in rows]
    return [sum(row[r] for row in centred) / len(centred) for r in range(len(ROLES))]


# ---- AC_0: the snapshot ---------------------------------------------------------------------------


def test_ac0_the_base_family_is_stored_as_one_snapshot(
    store: AnyStore, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli, "_gate_passed", lambda s, snapshot: True)  # I1
    _softmax_family(store, BASE_LOGITS)
    members_before = {t.id: store.get_active_policy(AGENT, t.id).id for t in store.list_agent_tasks(AGENT)}

    assert _compile(sigma="0.25") == 0

    prior = store.get_active_policy(AGENT, NAME)
    assert prior is not None
    assert prior.agent_id == AGENT
    assert prior.task_id == NAME
    assert [a.id for a in prior.actions] == list(ROLES)
    assert [prior.logits[r] for r in ROLES] == pytest.approx([0.825, -0.625, -0.200], abs=1e-9)
    assert prior.metadata["is_family_meta_prior"] is True
    assert "policy_scope" not in prior.metadata
    assert json.loads(capsys.readouterr().out)["id"] == prior.id

    # active only as its own pseudo-task, of no member
    members_after = {t.id: store.get_active_policy(AGENT, t.id).id for t in store.list_agent_tasks(AGENT) if t.id != NAME}
    assert members_after == members_before
    assert len(store.list_policies(AGENT, NAME)) == 1


def test_ac0_tasks_list_shows_the_prior_and_decision_only_does_not(
    store: AnyStore, capsys: pytest.CaptureFixture[str]
) -> None:
    _softmax_family(store)
    assert _compile() == 0
    capsys.readouterr()

    assert cli.main(["tasks-list", AGENT]) == 0
    listed = [item["id"] for item in json.loads(capsys.readouterr().out)]
    assert NAME in listed

    assert cli.main(["tasks-list", AGENT, "--decision-only"]) == 0
    decision_only = [item["id"] for item in json.loads(capsys.readouterr().out)]
    assert NAME not in decision_only


def test_ac0_the_values_equal_the_pooled_logits(store: AnyStore) -> None:
    _softmax_family(store, STRONG_LOGITS)
    assert _compile() == 0
    prior = store.get_active_policy(AGENT, NAME)
    assert prior is not None
    assert [prior.logits[r] for r in ROLES] == pytest.approx(_centred_mean(STRONG_LOGITS), abs=1e-12)
    assert sum(prior.logits.values()) == pytest.approx(0.0, abs=1e-12)


# ---- AC_1: provenance ----------------------------------------------------------------------------


def test_ac1_the_metadata_holds_the_provenance(store: AnyStore) -> None:
    _softmax_family(store)
    _add_member(store, "excluded-no-map", STRONG_LOGITS[0], role_map=None)  # a candidate that is excluded
    assert _compile(sigma="0.5") == 0

    prior = store.get_active_policy(AGENT, NAME)
    assert prior is not None
    meta = prior.metadata
    assert meta["family"] == FAMILY
    assert meta["family_member_count"] == 4
    assert meta["compiled_from"] == [{"task_id": f"member-{i}", "version": 3} for i in range(4)]
    datetime.fromisoformat(meta["compile_time"])
    assert meta["sigma_het"] == 0.5
    assert meta["kappa_prior"] is None
    assert meta["representation"] == "softmax"

    report = meta["validation_report"]
    assert report["family_size"] == 4
    assert [item["task_id"] for item in report["excluded"]] == ["excluded-no-map"]
    assert "role_map" in report["excluded"][0]["reason"]
    assert set(report["role_spread"]) == set(ROLES)
    assert all(isinstance(v, float) and v >= 0 for v in report["role_spread"].values())


def test_ac1_the_metadata_survives_json_unchanged(store: AnyStore) -> None:
    _softmax_family(store)
    assert _compile() == 0
    prior = store.get_active_policy(AGENT, NAME)
    assert prior is not None
    again = PolicySnapshot.from_dict(json.loads(json.dumps(prior.to_dict())))
    assert again.to_dict() == prior.to_dict()
    assert again.metadata == prior.metadata


# ---- AC_2: members unchanged, refusals store nothing ---------------------------------------------


def test_ac2_member_snapshots_are_equal_to_their_copies(store: AnyStore) -> None:
    _softmax_family(store)
    before = _everything(store)
    assert _compile() == 0
    after = _everything(store)
    for snapshot_id, snapshot in before.items():
        assert after[snapshot_id] == snapshot
    assert set(after) - set(before) == {store.get_active_policy(AGENT, NAME).id}


def test_ac2_a_family_too_small_stores_nothing_and_says_why(
    store: AnyStore, capsys: pytest.CaptureFixture[str]
) -> None:
    _softmax_family(store, STRONG_LOGITS[:3])
    _add_member(store, "excluded-no-map", STRONG_LOGITS[0], role_map=None)
    before = _everything(store)

    assert _compile() == 2

    err = capsys.readouterr().err
    assert "3" in err and "4" in err
    assert "excluded-no-map" in err and "role_map" in err
    assert _everything(store) == before
    assert store.get_active_policy(AGENT, NAME) is None


def test_ac2_a_family_that_is_too_heterogeneous_stores_nothing(
    store: AnyStore, capsys: pytest.CaptureFixture[str]
) -> None:
    _softmax_family(store, STRONG_LOGITS)
    before = _everything(store)

    assert _compile(sigma="0.0001") == 2

    err = capsys.readouterr().err
    assert "sigma_het" in err
    assert any(role in err for role in ROLES)
    assert _everything(store) == before
    assert store.get_active_policy(AGENT, NAME) is None


def test_ac2_a_mix_of_representations_is_refused_naming_the_tasks(
    store: AnyStore, capsys: pytest.CaptureFixture[str]
) -> None:
    _softmax_family(store, STRONG_LOGITS[:3])
    _add_member(store, "beta-member", [0.0, 0.0, 0.0], posterior=({"approve": 41.0, "reject": 15.0, "revise": 10.0},
                                                                    {"approve": 9.0, "reject": 35.0, "revise": 40.0}))
    before = _everything(store)

    assert _compile() == 2

    err = capsys.readouterr().err
    assert "beta-member" in err and "member-0" in err
    assert _everything(store) == before


def test_ac2_an_output_name_that_is_a_task_policy_is_refused(store: AnyStore) -> None:
    _softmax_family(store)
    before = _everything(store)
    assert _compile(name="member-0") == 2
    assert _everything(store) == before


def test_ac2_the_output_name_is_checked_before_the_family_is_pooled(
    store: AnyStore, capsys: pytest.CaptureFixture[str]
) -> None:
    """Q-96-1: a refused name is reported at once, even when the family would also be refused."""
    _softmax_family(store, STRONG_LOGITS[:3])  # too few members as well
    assert _compile(name="member-0") == 2
    err = capsys.readouterr().err
    assert "--output-prior-name" in err
    assert "at least" not in err


@pytest.mark.parametrize("missing", ["--agent-id", "--family", "--output-prior-name", "--sigma-het"])
def test_ac2_every_required_flag_is_required(store: AnyStore, missing: str) -> None:
    flags = {"--agent-id": AGENT, "--family": FAMILY, "--output-prior-name": NAME, "--sigma-het": "0.5"}
    del flags[missing]
    argv = ["task-policy-meta-compile"] + [part for item in flags.items() for part in item]
    with pytest.raises(SystemExit):
        cli.main(argv)


# ---- AC_3: supersession --------------------------------------------------------------------------


def test_ac3_compiling_again_stores_the_next_version_and_leaves_the_old_one_alone(store: AnyStore) -> None:
    _softmax_family(store)
    assert _compile() == 0
    first = store.get_active_policy(AGENT, NAME)
    assert first is not None
    first_copy = copy.deepcopy(first.to_dict())
    assert "supersedes" not in first.metadata

    assert _compile() == 0
    second = store.get_active_policy(AGENT, NAME)
    assert second is not None
    assert second.id != first.id
    assert second.version == first.version + 1
    assert second.metadata["supersedes"] == first.id

    old = store.get_policy(first.id, AGENT)
    assert old is not None
    assert old.to_dict() == first_copy
    assert {p.id for p in store.list_policies(AGENT, NAME)} == {first.id, second.id}

    assert _compile() == 0
    third = store.get_active_policy(AGENT, NAME)
    assert third is not None
    assert third.version == second.version + 1
    assert third.metadata["supersedes"] == second.id
    assert store.get_policy(second.id, AGENT).to_dict() == second.to_dict()


def test_ac3_only_the_latest_version_is_the_active_one(local_store: LocalFileStore) -> None:
    store = local_store
    _softmax_family(store)
    assert _compile() == 0
    assert _compile() == 0
    newest = max(store.list_policies(AGENT, NAME), key=lambda p: p.version)
    assert store.get_active_policy(AGENT, NAME).id == newest.id


# ---- AC_4: the Thompson form ---------------------------------------------------------------------


def _beta_member(store: AnyStore, task_id: str, rates: dict[str, float]) -> None:
    alpha = {a: rate * 50 for a, rate in rates.items()}
    beta = {a: (1.0 - rate) * 50 for a, rate in rates.items()}
    _add_member(store, task_id, [0.0, 0.0, 0.0], posterior=(alpha, beta))


def test_ac4_a_thompson_family_stores_posterior_parameters_keyed_by_role(store: AnyStore) -> None:
    rows = [
        {"approve": 0.82, "reject": 0.30, "revise": 0.20},
        {"approve": 0.84, "reject": 0.28, "revise": 0.22},
        {"approve": 0.80, "reject": 0.32, "revise": 0.18},
        {"approve": 0.83, "reject": 0.30, "revise": 0.20},
    ]
    for index, rates in enumerate(rows):
        _beta_member(store, f"beta-{index}", rates)

    assert _compile("--kappa-prior", "5", sigma="0.5") == 0

    prior = store.get_active_policy(AGENT, NAME)
    assert prior is not None
    assert prior.metadata["representation"] == "thompson"
    assert prior.metadata["kappa_prior"] == 5.0
    assert prior.metadata["is_family_meta_prior"] is True
    assert prior.logits == {r: 0.0 for r in ROLES}

    posterior = prior.metadata["posterior_parameters"]
    assert set(posterior) == {"alpha", "beta"}
    assert set(posterior["alpha"]) == set(ROLES) == set(posterior["beta"])
    for role in ROLES:
        pairs = [(row[role] * 50, (1.0 - row[role]) * 50) for row in rows]
        pooled = sum(a - 1 for a, _ in pairs) / sum(a + b - 2 for a, b in pairs)
        assert posterior["alpha"][role] == pytest.approx(1.0 + 5.0 * pooled, abs=1e-9)
        assert posterior["beta"][role] == pytest.approx(1.0 + 5.0 * (1.0 - pooled), abs=1e-9)
    assert all(math.isfinite(v) for part in posterior.values() for v in part.values())


def test_ac4_the_default_strength_is_ten(store: AnyStore) -> None:
    for index in range(4):
        _beta_member(store, f"beta-{index}", {"approve": 0.82, "reject": 0.30, "revise": 0.20})
    assert _compile(sigma="0.5") == 0
    prior = store.get_active_policy(AGENT, NAME)
    assert prior is not None and prior.metadata["kappa_prior"] == 10.0
    alpha, beta = prior.metadata["posterior_parameters"]["alpha"]["approve"], prior.metadata["posterior_parameters"]["beta"]["approve"]
    assert alpha + beta - 2.0 == pytest.approx(10.0, abs=1e-9)


# ---- AC_5: storage boundary ----------------------------------------------------------------------


def test_ac5_the_store_gains_no_record_type(local_store: LocalFileStore, tmp_path: Path) -> None:
    store = local_store
    _softmax_family(store)
    root = tmp_path / "store"
    kinds_before = sorted(p.name for p in root.iterdir())
    assert _compile() == 0
    assert sorted(p.name for p in root.iterdir()) == kinds_before


def test_ac5_the_pooling_module_imports_nothing_from_storage() -> None:
    source = Path(__file__).resolve().parent.parent / "src" / "agent_learning" / "meta_prior.py"
    assert source.is_file(), f"missing {source}"
    imports = [
        line
        for line in source.read_text(encoding="utf-8").splitlines()
        if line.lstrip().startswith(("import", "from"))
    ]
    assert imports, "no imports found"
    assert not [line for line in imports if "storage" in line]
