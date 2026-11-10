"""Contract tests for Story 21.7: The Real-Data Check (No Routed Traffic).

Governing specifications:
- User Story: docs/user-stories/epic-21-contextual-authority-ensemble-routing.md (Story 21.7)
- Architecture: docs/adr/ADR-021-contextual-authority-ensemble-routing.md (section 4.5, Invariant 5)
- Business Requirements: docs/project-docs/Business-Requirements/BRD-021-contextual-authority-ensemble-routing.md
  (BRU-021-15)
- Functional Design: docs/project-docs/Functional-Design/FDD-021-contextual-authority-ensemble-routing.md (section 8)

What this is: the router, run over the recorded governance policies and episodes, to show that no routed traffic
and no calibrated threshold exist yet, not to assume it.

What this is not: evidence that routing saves cost or latency (BRU-021-15). Nothing here is calibrated.

Missing data, named on purpose: mixed-difficulty traffic through a hybrid policy, with a context key declared for
each request.

Acceptance Criteria:
- AC_0 (Real Source): the committed policies are copied to a temporary store and the committed episode files are
  read; the counts and task ids are recorded below.
- AC_1 (Gates Route Full): every recorded approve-* task that is in PINNED_FULL routes FULL with reason
  ``pinned`` for any distribution.
- AC_2 (No Routed Episodes): no committed episode carries ``routed_authority`` or a ``routing`` record, so
  ``previous_route`` is None and ``agreement`` finds no episode for any bucket.
- AC_3 (Nothing Written): the copy of the store equals its earlier state after the checks.
- AC_4 (Labelled): the result is a statement that no routed traffic and no calibrated threshold exist yet.

Interpretations from ``scripts/spec_gate.py 21.7 --no-persist`` (PASSED, robust margin +0.0975):
  I1 Round trip: routing records are plain data; nothing here stores a snapshot, and nothing imports
     ``agent_learning.storage`` except ``LocalFileStore`` to read the temporary copy.
  I2 Empty base case: an empty episode list gives ``previous_route`` None and ``agreement`` n 0; a bucket with no
     episode gives the same.
  I3 Non-finite floats: the distributions used are finite; the invalid input (an empty list) is pinned first, so
     it routes FULL with reason ``pinned`` rather than ``anomaly`` (FDD-021 section 3 item 2).
  I4 Tolerances: the counts and reasons are exact; no floating-point comparison is made.
Interpretations added for this contract:
  I5 "The committed store under data/agent-learning/store" is what git tracks there, which is three active-policy
     pointers (approve-brd, approve-fdd, approve-user-stories) and the three snapshots they name. Other pointers on
     a developer's machine (approve-adr among them) are git-ignored (.gitignore) and are not counted, so the
     counts do not depend on the machine. The copy is built from those named files only, and a test checks with
     ``git ls-files`` that they are tracked (LL-037).
  I6 The recorded episodes are every file in docs/policy-shapes/episodes/; 16 early files carry no ``id`` and use
     their file name (as Story 20.6). The count is a floor, because every approval adds a file.
  I7 "For any distribution" is a set of constructed distributions (uniform, peaked, an empty list, a sum that is
     not 1), crossed with every tier and with the approvals a fast path would need (``approved_for_low`` True and
     ``previous`` LOW). They are arithmetic checks and are labelled so.
  I8 Finding, resolved by IMP-046 (2026-11-10): five gate tasks in the episodes had not been in PINNED_FULL
     (approve-audit-record, approve-benefits, approve-business-case, approve-ideation, approve-project-pillars), so their
     routing depended on ``requires_human_approval`` in a complexity profile and no profile for them is committed.
     They are now pinned by name, and ``test_ac1_every_recorded_gate_is_pinned`` asserts that every approve-* task
     in the committed episodes is pinned, so a new gate type must be pinned (or its decision recorded) before it merges.
     Still outside this check: approve-compiled-weights and approve-intent-refinement have policy shapes but no episodes.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

from agent_learning.decision import DecisionAuthority
from agent_learning.storage.local import LocalFileStore
from agent_learning.types import Episode
from agent_learning_ext.decision import TaskPolicy
from agent_learning_ext.routing import PINNED_FULL, agreement, previous_route, route

REPO = Path(__file__).resolve().parent.parent
STORE = REPO / "data" / "agent-learning" / "store"
EPISODES = REPO / "docs" / "policy-shapes" / "episodes"
AGENT = "agent-learning-governance"

# AC_0: recorded on 2026-11-10 from the committed files.
RECORDED_TASKS = {
    "approve-brd": "43ea80ae-f37e-493b-8f0f-554063f7dae0",
    "approve-fdd": "67acdd43-e16b-40af-9d45-385630ae6b6f",
    "approve-user-stories": "d71ffe2f-d496-4655-9d5f-3543303f2595",
}
RECORDED_EPISODE_FILES = 227  # a floor: every approval adds a file
RECORDED_EPISODES_WITHOUT_ID = 16
LABEL = (
    "no routed traffic and no calibrated routing threshold exist yet; no claim about saved cost or latency. "
    "Missing data: mixed-difficulty traffic through a hybrid policy, with a context key declared for each request."
)
NOW = datetime(2026, 11, 10, tzinfo=timezone.utc)
DISTRIBUTIONS = {
    "uniform": [1 / 3, 1 / 3, 1 / 3],
    "peaked": [0.98, 0.01, 0.01],
    "empty": [],
    "sum_not_one": [0.9, 0.9],
}
TIERS = ("low", "standard", "high", "critical")


def _pointer(task: str) -> Path:
    return STORE / "active-policies" / AGENT / f"{task}.json"


def _snapshot_file(policy_id: str) -> Path:
    return STORE / "policies" / AGENT / f"{policy_id}.json"


def _copy_committed_store(dest: Path) -> Path:
    """Copy only the three committed pointers and the snapshots they name (I5)."""
    for task, policy_id in RECORDED_TASKS.items():
        for src, rel in (
            (_pointer(task), Path("active-policies") / AGENT / f"{task}.json"),
            (_snapshot_file(policy_id), Path("policies") / AGENT / f"{policy_id}.json"),
        ):
            assert src.is_file(), f"committed store file is missing: {src}"
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, target)
    return dest


def _digest(root: Path) -> str:
    h = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        h.update(path.relative_to(root).as_posix().encode())
        h.update(hashlib.sha256(path.read_bytes()).digest())
    return h.hexdigest()


def _episode_files() -> list[Path]:
    assert EPISODES.is_dir(), f"missing {EPISODES}"
    return sorted(EPISODES.glob("*.json"))


def _load_episodes() -> list[Episode]:
    episodes = []
    for path in _episode_files():
        data = json.loads(path.read_text(encoding="utf-8"))
        data["id"] = data.get("id") or path.stem  # 16 early files carry no id (I6)
        episodes.append(Episode.from_dict(data))
    return episodes


def _recorded_approve_tasks() -> set[str]:
    tasks = set()
    for path in _episode_files():
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("agent_id") == AGENT and str(data.get("task_id", "")).startswith("approve-"):
            tasks.add(data["task_id"])
    return tasks


# --- AC_0: Real Source ----------------------------------------------------------------------------------


def test_ac0_committed_policies_are_the_three_recorded_gates(tmp_path: Path) -> None:
    copy = _copy_committed_store(tmp_path / "store")
    store = LocalFileStore(copy)
    found = {}
    for task, policy_id in RECORDED_TASKS.items():
        snapshot = store.get_active_policy(AGENT, task)
        assert snapshot is not None, f"no active policy for {task}"
        assert snapshot.id == policy_id
        found[task] = TaskPolicy(snapshot).authority
    assert set(found) == set(RECORDED_TASKS)
    assert len(found) == 3
    assert all(authority == DecisionAuthority.FULL for authority in found.values())
    snapshots = list((copy / "policies" / AGENT).glob("*.json"))
    assert len(snapshots) == 3


def test_ac0_committed_episodes_are_recorded() -> None:
    files = _episode_files()
    assert len(files) >= RECORDED_EPISODE_FILES, f"{len(files)} episode files; {RECORDED_EPISODE_FILES} were recorded"
    without_id = 0
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not data.get("id"):
            without_id += 1
    # only the early files lack an id; later episodes are written with one, so this count does not grow
    assert without_id == RECORDED_EPISODES_WITHOUT_ID
    assert len(_load_episodes()) == len(files)


def test_ac0_the_store_files_are_tracked_by_git() -> None:
    if not (REPO / ".git").exists() or shutil.which("git") is None:
        pytest.skip("not a git checkout")
    wanted = [_pointer(t) for t in RECORDED_TASKS] + [_snapshot_file(p) for p in RECORDED_TASKS.values()]
    tracked = subprocess.run(
        ["git", "ls-files", "data/agent-learning/store"], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout.split()
    tracked_set = {Path(p).as_posix() for p in tracked}
    for path in wanted:
        rel = path.relative_to(REPO).as_posix()
        assert rel in tracked_set, f"{rel} is not tracked by git (LL-037)"


# --- AC_1: Gates Route Full -----------------------------------------------------------------------------


@pytest.mark.parametrize("task", sorted(RECORDED_TASKS))
@pytest.mark.parametrize("dist_name", sorted(DISTRIBUTIONS))
@pytest.mark.parametrize("tier", TIERS)
def test_ac1_recorded_gates_route_full_pinned_for_any_distribution(task: str, dist_name: str, tier: str) -> None:
    assert task in PINNED_FULL
    decision = route(
        DISTRIBUTIONS[dist_name],
        tier,
        task_id=task,
        previous=DecisionAuthority.LOW,
        approved_for_low=True,
    )
    assert decision.authority == DecisionAuthority.FULL
    assert decision.reason == "pinned"


def test_ac1_every_pinned_approve_task_in_the_episodes_routes_full() -> None:
    pinned = sorted(t for t in _recorded_approve_tasks() if t in PINNED_FULL)
    assert set(RECORDED_TASKS) <= set(pinned)
    assert len(pinned) >= 12  # the seven pinned at approval and the five added by IMP-046
    for task in pinned:
        decision = route(DISTRIBUTIONS["uniform"], "low", task_id=task, approved_for_low=True)
        assert (decision.authority, decision.reason) == (DecisionAuthority.FULL, "pinned"), task


def test_ac1_every_recorded_gate_is_pinned() -> None:
    """IMP-046: no approve-* task in the committed episodes depends on a missing complexity profile to route full."""
    unpinned = sorted(t for t in _recorded_approve_tasks() if t not in PINNED_FULL)
    assert unpinned == [], f"approve-* tasks in the committed episodes that are not in PINNED_FULL: {unpinned}"


# --- AC_2: No Routed Episodes ---------------------------------------------------------------------------


def test_ac2_no_committed_episode_carries_a_routing_record() -> None:
    carrying = []
    for path in _episode_files():
        data = json.loads(path.read_text(encoding="utf-8"))
        metadata = data.get("metadata") or {}
        for key in ("routed_authority", "routing"):
            if key in metadata or key in data:
                carrying.append((path.name, key))
    assert carrying == []


def test_ac2_previous_route_is_none_and_agreement_finds_nothing() -> None:
    episodes = _load_episodes()
    buckets = sorted(_recorded_approve_tasks() | set(RECORDED_TASKS) | {"unrouted", "default"})
    assert buckets
    for bucket in buckets:
        assert previous_route(episodes, bucket) is None, bucket
        result = agreement(episodes, bucket, NOW, 365.0)
        assert result["n"] == 0 and result["k"] == 0, (bucket, result)
    # the empty base case (I2)
    assert previous_route([], "default") is None
    assert agreement([], "default", NOW, 365.0)["n"] == 0


# --- AC_3: Nothing Written ------------------------------------------------------------------------------


def test_ac3_the_store_copy_is_unchanged_after_the_checks(tmp_path: Path) -> None:
    copy = _copy_committed_store(tmp_path / "store")
    before = _digest(copy)
    store = LocalFileStore(copy)
    for task in RECORDED_TASKS:
        snapshot = store.get_active_policy(AGENT, task)
        route(DISTRIBUTIONS["uniform"], "low", task_id=task, approved_for_low=True)
        assert TaskPolicy(snapshot).authority == DecisionAuthority.FULL
    previous_route(_load_episodes(), "default")
    assert _digest(copy) == before


# --- AC_4: Labelled -------------------------------------------------------------------------------------


def test_ac4_the_result_is_labelled_and_names_the_missing_data() -> None:
    assert "no routed traffic" in LABEL and "no calibrated routing threshold" in LABEL
    assert "no claim about saved cost or latency" in LABEL
    doc = " ".join((__doc__ or "").split())  # the docstring wraps lines
    assert "mixed-difficulty traffic through a hybrid policy" in doc
    assert "context key declared for each request" in doc
    assert "BRU-021-15" in doc
