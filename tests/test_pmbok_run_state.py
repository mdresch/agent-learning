"""Contract tests for Epic 34, Story 34.2.

ADR-034 Invariants 2, 4, and 6; BRD-034 BRU-034-02, BRU-034-06, BRU-034-08;
FDD-034 sections 2, 3.2, and 3.3.
"""

from __future__ import annotations

import ast
from pathlib import Path
from uuid import uuid4

import pytest

from agent_learning.types import Episode

ROOT = Path(__file__).resolve().parent.parent
RUN_STATE = ROOT / "src" / "agent_learning" / "pmbok" / "run_state.py"


def _snapshot(**changes: object):
    from agent_learning.pmbok.run_state import RunSnapshot

    fields: dict[str, object] = {
        "run_id": str(uuid4()),
        "sequence_number": 1,
        "created_at": "2026-10-30T00:00:00Z",
        "phase": "planning",
        "processes": {"4.1": "completed"},
        "baseline_hash": "a" * 64,
        "gate_episode_ids": {"scope-management": ("episode-1", "b" * 64, "accepted")},
        "route_episode_ids": {"scope-management": "route-1"},
    }
    fields.update(changes)
    return RunSnapshot(**fields)


def test_ac0_run_fields_use_governance_identity_and_exact_metadata_keys() -> None:
    from agent_learning.pmbok.run_state import build_run_fields

    fields = build_run_fields(_snapshot(), "run completed")

    assert fields.agent_id == "pmbok-orchestration"
    assert fields.task_id == "pmbok-lifecycle-run"
    assert fields.action_type == "governance"
    assert fields.action_logprob is None
    assert set(fields.metadata) == {
        "run_id",
        "phase",
        "processes",
        "sequence_number",
        "baseline_hash",
        "gate_episode_ids",
        "route_episode_ids",
    }


def test_ac1_latest_run_orders_by_sequence_then_created_at_without_reordering() -> None:
    from agent_learning.pmbok.run_state import latest_run

    assert latest_run([]) is None
    oldest = _snapshot(sequence_number=1, created_at="2026-10-30T01:00:00Z")
    newer_time = _snapshot(sequence_number=1, created_at="2026-10-30T02:00:00Z")
    newer_sequence = _snapshot(sequence_number=2, created_at="2026-10-30T00:30:00Z")
    snapshots = [newer_sequence, oldest, newer_time]

    assert latest_run(snapshots) is newer_sequence
    assert snapshots == [newer_sequence, oldest, newer_time]
    assert latest_run([oldest, newer_time]) is newer_time
    assert latest_run([oldest, _snapshot(
        run_id=oldest.run_id,
        sequence_number=oldest.sequence_number,
        created_at=oldest.created_at,
        phase="earlier input",
    )]).phase == "planning"


def test_ac2_invalid_run_fields_raise_value_error_naming_field() -> None:
    from agent_learning.pmbok.run_state import build_run_fields

    invalid_snapshots = (
        (_snapshot(run_id=""), "run_id"),
        (_snapshot(run_id="not-a-uuid"), "run_id"),
        (_snapshot(run_id="x" * 257), "run_id"),
        (_snapshot(sequence_number=-1), "sequence_number"),
        (_snapshot(processes={"unknown": "completed"}), "processes"),
        (_snapshot(processes={"4.1": "unknown"}), "processes"),
        (_snapshot(created_at="t" * 257), "created_at"),
        (_snapshot(phase="p" * 257), "phase"),
        (_snapshot(processes={"4.1": "s" * 257}), "processes"),
        (_snapshot(processes={"p" * 257: "completed"}), "processes"),
        (_snapshot(baseline_hash="h" * 257), "baseline_hash"),
        (_snapshot(gate_episode_ids={"p" * 257: ("episode", "hash", "accepted")}), "gate_episode_ids"),
        (_snapshot(gate_episode_ids={"plan": ("x" * 257, "hash", "accepted")}), "gate_episode_ids"),
        (_snapshot(route_episode_ids={"p" * 257: "episode"}), "route_episode_ids"),
        (_snapshot(route_episode_ids={"plan": "x" * 257}), "route_episode_ids"),
    )
    for snapshot, field in invalid_snapshots:
        with pytest.raises(ValueError, match=field):
            build_run_fields(snapshot, "result")

    with pytest.raises(ValueError, match="result_summary"):
        build_run_fields(_snapshot(), "r" * 257)


def test_ac3_domain_run_state_is_storage_free_and_pure() -> None:
    assert RUN_STATE.is_file(), f"Missing run-state module: {RUN_STATE}"
    tree = ast.parse(RUN_STATE.read_text(encoding="utf-8"))
    forbidden_imports = {"agent_learning.storage", "pmbok_runtime", "pydantic", "socket"}
    forbidden_calls = {"open", "urlopen", "connect", "sleep"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(
                not any(alias.name == prefix or alias.name.startswith(f"{prefix}.") for prefix in forbidden_imports)
                for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            assert not any(module == prefix or module.startswith(f"{prefix}.") for prefix in forbidden_imports)
        elif isinstance(node, ast.Call):
            name = node.func.id if isinstance(node.func, ast.Name) else (
                node.func.attr if isinstance(node.func, ast.Attribute) else ""
            )
            assert name not in forbidden_calls


def test_ac4_runtime_appends_an_episode_without_creating_a_database_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from agent_learning.pmbok_runtime.runs import append_run, latest_run_for

    class StoreDouble:
        def __init__(self) -> None:
            self.episodes: list[Episode] = []

        def store_episode(self, episode: Episode) -> str:
            self.episodes.append(episode)
            return episode.id

        def count_episodes(
            self,
            agent_id: str,
            *,
            task_id: str | None = None,
            full_only: bool = False,
            start_date: str | None = None,
            end_date: str | None = None,
        ) -> int:
            return len(self.episodes)

        def query_episodes(
            self,
            agent_id: str,
            *,
            limit: int = 100,
            start_date: str | None = None,
            end_date: str | None = None,
            policy_id: str | None = None,
            task_id: str | None = None,
            full_only: bool = False,
        ) -> list[Episode]:
            return self.episodes[:limit]

    monkeypatch.chdir(tmp_path)
    store = StoreDouble()
    snapshot = _snapshot()
    assert latest_run_for(store, snapshot.run_id) is None

    episode = append_run(store, snapshot, "run completed")

    assert store.episodes == [episode]
    assert episode.agent_id == "pmbok-orchestration"
    assert episode.task_id == "pmbok-lifecycle-run"
    assert episode.action_type == "governance"
    assert episode.action_logprob is None
    assert episode.metadata["sequence_number"] == snapshot.sequence_number
    assert episode.result_summary == "run completed"
    unrelated_snapshot = _snapshot(sequence_number=100)
    append_run(store, unrelated_snapshot, "another run")
    assert latest_run_for(store, snapshot.run_id) == snapshot
    later_snapshot = _snapshot(
        run_id=snapshot.run_id,
        sequence_number=2,
        created_at="2026-10-30T00:01:00Z",
    )
    later_episode = append_run(store, later_snapshot, "run updated")
    assert store.episodes[0] is episode
    assert store.episodes[2] is later_episode
    assert episode.metadata["sequence_number"] == 1
    assert latest_run_for(store, snapshot.run_id) == later_snapshot
    assert list(tmp_path.rglob("*.db")) == []
