"""Contract tests for Epic 19, Story 19.7 (The Real-Data Check, No Family).

Story: docs/user-stories/epic-19-hierarchical-meta-prior-compilation.md, Story 19.7.
ADR-019 §4.1 and §6; BRD-019 (BRU-019-12); FDD-019 §8 (Test Data), §3 item 7 (steps 1 and 2), §5; ADR-021 Invariant 5.

What this is: the compiler run over the recorded governance tasks, to show that no suitable family exists yet,
not to assume it. The ``approve-*`` tasks of ``agent-learning-governance`` share action roles (approve, reject,
revise) but are full authority, so they carry no learned logits and cannot be converged donors.

What this is not: evidence that a meta-prior speeds convergence (BRU-019-12). Nothing here pools real logits.

Missing data, named on purpose: four or more converged same-family low-authority policies with real episodes
and a human-written ``role_map`` for each. The intended family is the nine advisory learners of
``planning-redesign-notes.md`` §4.12, which are not built.

Interpretation I1: the story says "a temporary copy of the committed store under ``data/agent-learning/store``",
but ``data/agent-learning/`` is ignored by git (``.gitignore``), so no such store is committed and a CI run
cannot copy it. What is committed is the recorded material of the same tasks: ``docs/policy-shapes/episodes/``
(the real approval episodes), ``docs/policy-shapes/<task>.actions.json`` (their action spaces) and
``docs/policy-shapes/results/`` (their decision results, which record ``decision_authority``). The store used here
is a temporary ``LocalFileStore`` rebuilt from those files. Where a committed decision result records no
authority for a task, the task is full authority by ADR-021 Invariant 5 (the strategic baseline gates are pinned),
and the source of each task's authority is recorded with the result. The recorded local store is also checked,
when it exists on the machine, by the last test.

Interpretation I2: the ``role_map`` for each task is written by the test (a human-written map, as FDD-019 requires):
the ``approve_*`` action plays ``approve``, the ``reject_*`` action ``reject`` and ``request_revision_before_decision``
plays ``revise``.

Interpretation I3: the family name used when the tasks are declared into one is ``governance-gates``.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path

import pytest

from agent_learning import cli
from agent_learning.storage.local import LocalFileStore
from agent_learning.types import Action, Episode, PolicySnapshot

REPO = Path(__file__).resolve().parent.parent
SHAPES = REPO / "docs" / "policy-shapes"
AGENT = "agent-learning-governance"
FAMILY = "governance-gates"
LABEL = "no suitable family exists yet; no claim that a meta-prior speeds convergence"


def _read_json(path: Path) -> dict:
    assert path.is_file(), f"missing {path}"
    return json.loads(path.read_text(encoding="utf-8"))


def _recorded_tasks() -> dict[str, dict]:
    """The approve-* tasks of the governance agent, from the committed episodes, actions and results."""
    episodes_dir = SHAPES / "episodes"
    assert episodes_dir.is_dir(), f"missing {episodes_dir}"
    tasks: dict[str, dict] = {}
    for path in sorted(episodes_dir.glob("*.json")):
        data = _read_json(path)
        if data.get("agent_id") != AGENT or not str(data.get("task_id", "")).startswith("approve-"):
            continue
        data.setdefault("id", path.stem)  # some early episode files carry no id; the file name is theirs
        task = tasks.setdefault(data["task_id"], {"episodes": [], "policy_ids": set()})
        task["episodes"].append(data)
        task["policy_ids"].add(data["policy_id"])

    authority: dict[str, set[str]] = {}
    for path in sorted((SHAPES / "results").glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and str(data.get("task_id", "")).startswith("approve-") and "decision_authority" in data:
            authority.setdefault(data["task_id"], set()).add(str(data["decision_authority"]))

    for task_id, task in tasks.items():
        actions_path = SHAPES / f"{task_id}.actions.json"
        assert actions_path.is_file(), f"missing actions file for task {task_id!r}: {actions_path}"
        task["actions"] = [Action(id=a["id"]) for a in json.loads(actions_path.read_text(encoding="utf-8"))]
        recorded = authority.get(task_id)
        if recorded:
            assert len(recorded) == 1, f"{task_id}: committed results disagree on authority: {recorded}"
            task["authority"], task["authority_source"] = next(iter(recorded)), "committed decision result"
        else:
            task["authority"], task["authority_source"] = "full", "ADR-021 Invariant 5 (no committed decision result)"
    return tasks


def _role_map(actions: list[Action]) -> dict[str, str]:
    """The human-written role map (I2): approve_* plays approve, reject_* reject, the revision action revise."""
    roles = {}
    for action in actions:
        if action.id.startswith("approve"):
            roles[action.id] = "approve"
        elif action.id.startswith("reject"):
            roles[action.id] = "reject"
        elif action.id == "request_revision_before_decision":
            roles[action.id] = "revise"
        else:
            raise AssertionError(f"no role is written for action {action.id!r}; extend the map in this test")
    assert sorted(roles.values()) == ["approve", "reject", "revise"], f"not a bijection onto the three roles: {roles}"
    return roles


def _build_store(root: Path, tasks: dict[str, dict]) -> LocalFileStore:
    store = LocalFileStore(root)
    for task_id, task in sorted(tasks.items()):
        store.store_policy(
            PolicySnapshot(
                id=f"recorded-{task_id}",  # the episodes of approve-pmp and approve-subsidiary-plan name one policy id, so each task gets its own
                agent_id=AGENT,
                task_id=task_id,
                version=0,
                actions=task["actions"],
                logits={a.id: 0.0 for a in task["actions"]},
                metadata={
                    "policy_scope": "delegated_decision",
                    "decision_authority": task["authority"],
                    "recorded_policy_ids": sorted(task["policy_ids"]),
                },
            )
        )
        for episode in task["episodes"]:
            store.store_episode(Episode.from_dict(episode))
    return store


def _tree(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


@pytest.fixture
def recorded(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[LocalFileStore, dict[str, dict], Path]:
    tasks = _recorded_tasks()
    root = tmp_path / "store"
    store = _build_store(root, tasks)
    monkeypatch.setattr(cli, "get_default_store", lambda: store)
    return store, tasks, root


def _compile(family: str) -> int:
    return cli.main(
        ["task-policy-meta-compile", "--agent-id", AGENT, "--family", family, "--output-prior-name", "governance-prior",
         "--sigma-het", "0.5"]
    )


def _declare_all(tasks: dict[str, dict]) -> None:
    for task_id, task in sorted(tasks.items()):
        role_map = json.dumps(_role_map(task["actions"]))
        assert cli.main(["task-policy-family-set", "--agent-id", AGENT, "--task-id", task_id, "--family", FAMILY,
                         "--role-map", role_map]) == 0


# ---- AC_0: the real source ------------------------------------------------------------------------


def test_ac0_the_recorded_tasks_and_their_authority(
    recorded: tuple[LocalFileStore, dict[str, dict], Path], record_property: pytest.RecordProperty
) -> None:
    store, tasks, _ = recorded
    assert tasks, "no approve-* tasks of agent-learning-governance found in the committed episodes"
    found = {t.id for t in store.list_agent_tasks(AGENT)}
    assert found == set(tasks)

    record_property("tasks", json.dumps({
        task_id: {"episodes": len(task["episodes"]), "authority": task["authority"], "authority_source": task["authority_source"]}
        for task_id, task in sorted(tasks.items())
    }))
    for task_id, task in tasks.items():
        snapshot = store.get_active_policy(AGENT, task_id)
        assert snapshot is not None
        assert snapshot.metadata["decision_authority"] == task["authority"]
        assert len(store.query_episodes(AGENT, task_id=task_id, limit=10_000)) == len(task["episodes"])
    # every recorded approve-* task is full authority: that is why none can be a donor
    assert {task["authority"] for task in tasks.values()} == {"full"}


# ---- AC_1: no family -----------------------------------------------------------------------------


def test_ac1_a_family_no_task_declares_exits_non_zero_with_a_reason(
    recorded: tuple[LocalFileStore, dict[str, dict], Path], capsys: pytest.CaptureFixture[str]
) -> None:
    assert _compile("no-such-family") == 2
    err = capsys.readouterr().err
    assert "0 members" in err and "at least 4" in err


def test_ac1_the_approve_tasks_declared_into_a_family_are_excluded_as_full_authority(
    recorded: tuple[LocalFileStore, dict[str, dict], Path], capsys: pytest.CaptureFixture[str]
) -> None:
    _, tasks, _ = recorded
    _declare_all(tasks)
    capsys.readouterr()

    scan = cli._scan_family(recorded[0], AGENT, FAMILY)
    assert scan.members == []
    assert {item["task_id"] for item in scan.excluded} == set(tasks)
    assert all("full decision authority" in item["reason"] for item in scan.excluded)

    assert _compile(FAMILY) == 2
    err = capsys.readouterr().err
    assert "0 members" in err and "at least 4" in err
    for task_id in tasks:
        assert f"excluded {task_id}: full decision authority" in err


# ---- AC_2: nothing stored ------------------------------------------------------------------------


def test_ac2_the_runs_store_nothing(recorded: tuple[LocalFileStore, dict[str, dict], Path]) -> None:
    store, tasks, root = recorded
    _declare_all(tasks)
    before = _tree(root)

    assert _compile(FAMILY) == 2
    assert _compile("no-such-family") == 2

    assert _tree(root) == before
    assert store.get_active_policy(AGENT, "governance-prior") is None


def test_ac2_the_recorded_local_store_is_left_equal_when_it_exists(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The recorded store is git-ignored (I1); on a machine that has it, a run over a copy must leave it alone."""
    candidates = [Path(os.environ["AGENT_LEARNING_LOCAL_STORE_DIR"])] if os.environ.get("AGENT_LEARNING_LOCAL_STORE_DIR") else []
    candidates.append(REPO / "data" / "agent-learning" / "store")
    source = next((path for path in candidates if path.is_dir()), None)
    if source is None:
        pytest.skip("no recorded local store on this machine (data/agent-learning/ is git-ignored)")

    before = _tree(source)
    copy = tmp_path / "copy"
    shutil.copytree(source, copy)
    local = LocalFileStore(copy)
    monkeypatch.setattr(cli, "get_default_store", lambda: local)

    assert _compile("no-such-family") == 2

    assert _tree(source) == before
    assert _tree(copy) == before


# ---- AC_3: labelled ------------------------------------------------------------------------------


def test_ac3_the_result_is_a_statement_that_no_suitable_family_exists(record_property: pytest.RecordProperty) -> None:
    record_property("label", LABEL)
    docstring = " ".join((__doc__ or "").split())
    assert "no suitable family exists yet" in LABEL
    assert "no claim that a meta-prior speeds convergence" in LABEL
    assert "four or more converged same-family low-authority policies with real episodes and a human-written" in docstring
    assert "BRU-019-12" in docstring
