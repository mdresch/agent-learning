"""Contract tests for Story 20.6: The Real-Data Check (No Donor).

Governing specifications:
- User Story: docs/user-stories/epic-20-explicit-policy-prior-warm-starting.md (Story 20.6)
- Architecture: docs/adr/ADR-020-explicit-policy-prior-warm-starting.md; ADR-001 section 4.2; ADR-021 Invariant 5
- Business Requirements: docs/project-docs/Business-Requirements/BRD-020-explicit-policy-prior-warm-starting.md (BRU-020-11)
- Functional Design: docs/project-docs/Functional-Design/FDD-020-explicit-policy-prior-warm-starting.md (section 5, Test Data)

What this is: the warm-start command and function run over the recorded governance tasks, to show that no
usable donor exists yet, not to assume one. The ``approve-*`` tasks of ``agent-learning-governance`` are full
authority (ADR-001 section 4.2), pinned there (ADR-021 Invariant 5), so they carry no learned logits and
cannot donate.

What this is not: evidence that a warm start reduces supervision (BRU-020-11). Nothing here copies real logits.

Missing data, named on purpose: one policy that has converged and a cold target of the same family, both
low authority, with real episodes.

Acceptance Criteria:
- AC_0 (Real Source): the policies found, their action ids and their authority are recorded.
- AC_1 (Real Action Sets): for approve-adr as target and approve-brd as donor, the explicit map
  approve_adr -> approve_brd, reject_adr -> reject_brd, request_revision_before_decision ->
  request_revision_before_decision is accepted by warm_start_logits, while the identity map is refused
  because the ids differ.
- AC_2 (No Usable Donor): task-policy-warm-start with any recorded approve-* policy as donor exits non-zero
  because it is full authority, and the store is equal to its earlier state.
- AC_3 (Labelled): the result is a statement that no converged low-authority donor exists yet, with no claim
  that a warm start reduces supervision (BRU-020-11).

Interpretation I1 (as Story 19.7, FDD-019 section 7 item 11): the story speaks of "the committed store under
``data/agent-learning/store``", but ``data/agent-learning/`` is ignored by git, so no such store is committed.
The store used here is a temporary ``LocalFileStore`` rebuilt from what is committed: the approval episodes in
``docs/policy-shapes/episodes/``, the ``<task>.actions.json`` files and the decision results in
``docs/policy-shapes/results/`` (which record ``decision_authority``). Where no committed result records the
authority, the task is full authority by ADR-021 Invariant 5, and the source of each task's authority is
recorded. The recorded local store is also checked, when the machine has one, by the last store test.
Interpretation I2: AC_2 needs a cold, low-authority target so that the donor is the thing refused (a full
authority target would be refused first). That target is one synthetic policy, labelled as such; everything
else is recorded.
Interpretation I3: the logits in AC_1 are synthetic and labelled; the recorded policies hold none.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path

import pytest

from agent_learning_ext import cli
from agent_learning.storage.local import LocalFileStore
from agent_learning.types import Action, Episode, PolicySnapshot
from agent_learning.warm_start import warm_start_logits

REPO = Path(__file__).resolve().parent.parent
SHAPES = REPO / "docs" / "policy-shapes"
AGENT = "agent-learning-governance"
LABEL = "no converged low-authority donor exists yet; no claim that a warm start reduces supervision"
SYNTHETIC_TARGET = "synthetic-cold-target"


def _recorded_tasks() -> dict[str, dict]:
    """The approve-* tasks of the governance agent, from the committed episodes, actions and results."""
    episodes_dir = SHAPES / "episodes"
    assert episodes_dir.is_dir(), f"missing {episodes_dir}"
    tasks: dict[str, dict] = {}
    for path in sorted(episodes_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("agent_id") != AGENT or not str(data.get("task_id", "")).startswith("approve-"):
            continue
        data.setdefault("id", path.stem)  # some early episode files carry no id; the file name is theirs
        task = tasks.setdefault(data["task_id"], {"episodes": [], "policy_ids": set()})
        task["episodes"].append(data)
        assert data.get("policy_id") is not None, f"episode file {path} is missing 'policy_id'"
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


def _build_store(root: Path, tasks: dict[str, dict]) -> LocalFileStore:
    store = LocalFileStore(root)
    for task_id, task in sorted(tasks.items()):
        store.store_policy(
            PolicySnapshot(
                id=f"recorded-{task_id}",  # approve-pmp and approve-subsidiary-plan name one policy id; each task gets its own
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


def _synthetic_cold_target(store: LocalFileStore) -> None:
    """The one synthetic policy (I2): a cold, low-authority decision policy."""
    store.store_policy(
        PolicySnapshot(
            id="synthetic-cold-target-v0",
            agent_id=AGENT,
            task_id=SYNTHETIC_TARGET,
            version=0,
            actions=[Action(id="accept"), Action(id="decline"), Action(id="ask")],
            logits={"accept": 0.0, "decline": 0.0, "ask": 0.0},
            metadata={"policy_scope": "delegated_decision", "decision_authority": "low"},
        )
    )


def _warm_start(donor: str, target: str = SYNTHETIC_TARGET, *extra: str) -> int:
    return cli.main(["task-policy-warm-start", "--agent-id", AGENT, "--target-task-id", target,
                     "--donor-task-id", donor, *extra])


# ---- AC_0: the real source ------------------------------------------------------------------------


def test_ac0_the_recorded_policies_their_actions_and_authority(
    recorded: tuple[LocalFileStore, dict[str, dict], Path], record_property: pytest.RecordProperty
) -> None:
    store, tasks, _ = recorded
    assert tasks, "no approve-* tasks of agent-learning-governance found in the committed episodes"
    assert {t.id for t in store.list_agent_tasks(AGENT)} == set(tasks)
    assert {"approve-adr", "approve-brd"} <= set(tasks)

    record_property("policies", json.dumps({
        task_id: {
            "actions": [a.id for a in task["actions"]],
            "authority": task["authority"],
            "authority_source": task["authority_source"],
            "episodes": len(task["episodes"]),
        }
        for task_id, task in sorted(tasks.items())
    }))
    for task_id, task in tasks.items():
        snapshot = store.get_active_policy(AGENT, task_id)
        assert snapshot is not None
        assert [a.id for a in snapshot.actions] == [a.id for a in task["actions"]]
        assert snapshot.metadata["decision_authority"] == task["authority"]
    assert {task["authority"] for task in tasks.values()} == {"full"}


# ---- AC_1: real action sets ----------------------------------------------------------------------


def test_ac1_the_explicit_map_between_the_real_action_sets_is_accepted(
    recorded: tuple[LocalFileStore, dict[str, dict], Path]
) -> None:
    _, tasks, _ = recorded
    target_ids = [a.id for a in tasks["approve-adr"]["actions"]]
    donor_ids = [a.id for a in tasks["approve-brd"]["actions"]]
    assert target_ids == ["approve_adr", "reject_adr", "request_revision_before_decision"]
    assert donor_ids == ["approve_brd", "reject_brd", "request_revision_before_decision"]

    action_map = {
        "approve_adr": "approve_brd",
        "reject_adr": "reject_brd",
        "request_revision_before_decision": "request_revision_before_decision",
    }
    synthetic_logits = {"approve_brd": 2.0, "reject_brd": -1.0, "request_revision_before_decision": 0.0}  # I3
    result = warm_start_logits(synthetic_logits, action_map, target_ids, damping=1.0)
    assert result == pytest.approx({"approve_adr": 2.0, "reject_adr": -1.0, "request_revision_before_decision": 0.0})


def test_ac1_the_identity_map_is_refused_because_the_ids_differ(
    recorded: tuple[LocalFileStore, dict[str, dict], Path]
) -> None:
    _, tasks, _ = recorded
    target_ids = [a.id for a in tasks["approve-adr"]["actions"]]
    donor_ids = [a.id for a in tasks["approve-brd"]["actions"]]
    assert set(target_ids) != set(donor_ids)
    identity = {action_id: action_id for action_id in target_ids}
    with pytest.raises(ValueError):
        warm_start_logits({action_id: 0.0 for action_id in donor_ids}, identity, target_ids)


# ---- AC_2: no usable donor -----------------------------------------------------------------------


def test_ac2_every_recorded_policy_as_donor_is_refused_as_full_authority_and_nothing_is_written(
    recorded: tuple[LocalFileStore, dict[str, dict], Path], capsys: pytest.CaptureFixture[str]
) -> None:
    store, tasks, root = recorded
    _synthetic_cold_target(store)
    before = _tree(root)
    for donor in sorted(tasks):
        capsys.readouterr()
        assert _warm_start(donor) == 2, donor
        assert "full decision authority" in capsys.readouterr().err, donor
    assert _tree(root) == before
    target = store.get_active_policy(AGENT, SYNTHETIC_TARGET)
    assert target is not None and target.version == 0


def test_ac2_a_recorded_policy_as_target_is_refused_as_full_authority(
    recorded: tuple[LocalFileStore, dict[str, dict], Path], capsys: pytest.CaptureFixture[str]
) -> None:
    _, _, root = recorded
    before = _tree(root)
    assert _warm_start("approve-brd", "approve-adr", "--action-map", json.dumps({
        "approve_adr": "approve_brd", "reject_adr": "reject_brd",
        "request_revision_before_decision": "request_revision_before_decision"})) == 2
    assert "full decision authority" in capsys.readouterr().err
    assert _tree(root) == before


def test_ac2_the_recorded_local_store_is_left_equal_when_it_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
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
    assert _warm_start("approve-brd", "approve-adr") != 0
    assert _tree(source) == before
    assert _tree(copy) == before


# ---- AC_3: labelled ------------------------------------------------------------------------------


def test_ac3_the_result_is_a_statement_that_no_donor_exists(record_property: pytest.RecordProperty) -> None:
    record_property("label", LABEL)
    docstring = " ".join((__doc__ or "").split())
    assert "no converged low-authority donor exists yet" in LABEL
    assert "no claim that a warm start reduces supervision" in LABEL
    assert "one policy that has converged and a cold target of the same family" in docstring
    assert "BRU-020-11" in docstring
