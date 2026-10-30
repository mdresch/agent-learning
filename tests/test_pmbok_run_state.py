"""Contract tests for Epic 34, Story 34.2.

ADR-034 Invariants 2, 4, and 6; BRD-034 BRU-034-02, BRU-034-06, BRU-034-08;
FDD-034 sections 2, 3.2, and 3.3.

Interpretation I1 (FDD-034 §4): `latest_run_for` retries a changing append-only
store three times, then raises `RuntimeError` rather than return stale state or
wait indefinitely.

Interpretation I2 (FDD-034 §§3.2–3.3): `created_at` is timezone-aware ISO-8601;
ordering compares instants normalized to UTC while persistence retains the
original timestamp string.
"""

from __future__ import annotations

import ast
from dataclasses import replace
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
    later_instant = _snapshot(sequence_number=1, created_at="2026-10-30T01:00:00Z")
    earlier_offset = _snapshot(sequence_number=1, created_at="2026-10-30T02:00:00+02:00")
    equal_instant = _snapshot(sequence_number=1, created_at="2026-10-30T03:00:00+02:00")
    assert latest_run([later_instant, earlier_offset]) is later_instant
    assert latest_run([later_instant, equal_instant]) is later_instant
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
        (_snapshot(created_at=""), "created_at"),
        (_snapshot(created_at="2026-10-30T00:00:00"), "created_at"),
        (_snapshot(created_at="not-a-timestamp"), "created_at"),
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

    with pytest.raises(TypeError, match="phase"):
        build_run_fields(_snapshot(phase=1), "result")
    with pytest.raises(ValueError, match="run_id"):
        build_run_fields(_snapshot(run_id=123), "result")
    with pytest.raises(TypeError, match="sequence_number"):
        build_run_fields(_snapshot(sequence_number=True), "result")
    with pytest.raises(ValueError, match="result_summary"):
        build_run_fields(_snapshot(), "r" * 257)

    from agent_learning.pmbok.run_state import latest_run

    with pytest.raises(ValueError, match="timezone-aware"):
        latest_run([_snapshot(created_at="not-a-timestamp")])


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
    from agent_learning.pmbok.run_state import build_run_fields
    from agent_learning.pmbok_runtime.runs import append_run, latest_run_for

    class StoreDouble:
        def __init__(self) -> None:
            self.episodes: list[Episode] = []
            self.append_after_query: Episode | None = None
            self.append_on_query: Episode | None = None
            self.count_call_count = 0
            self.query_count = 0
            self.persisted_id: str | None = None

        def store_episode(self, episode: Episode) -> str:
            stored_episode = (
                replace(episode, id=self.persisted_id)
                if self.persisted_id is not None
                else episode
            )
            self.episodes.append(stored_episode)
            return stored_episode.id

        def count_episodes(
            self,
            agent_id: str,
            *,
            task_id: str | None = None,
            full_only: bool = False,
            start_date: str | None = None,
            end_date: str | None = None,
        ) -> int:
            self.count_call_count += 1
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
            self.query_count += 1
            episodes = self.episodes[:limit]
            if self.append_after_query is not None:
                self.episodes.append(self.append_after_query)
                self.append_after_query = None
            if self.append_on_query is not None:
                self.episodes.append(replace(self.append_on_query, id=str(uuid4())))
            return episodes

    monkeypatch.chdir(tmp_path)
    store = StoreDouble()
    snapshot = _snapshot()
    assert latest_run_for(store, snapshot.run_id) is None
    assert store.count_call_count == 1

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

    racing_snapshot = _snapshot(
        run_id=snapshot.run_id,
        sequence_number=3,
        created_at="2026-10-30T00:02:00Z",
    )
    fields = build_run_fields(racing_snapshot, "run appended during query")
    store.append_after_query = Episode(
        agent_id=fields.agent_id,
        task_id=fields.task_id,
        action_type=fields.action_type,
        action_logprob=fields.action_logprob,
        metadata=dict(fields.metadata),
        result_summary=fields.result_summary,
        created_at=racing_snapshot.created_at,
    )
    expected_snapshot = _snapshot(run_id=snapshot.run_id, sequence_number=3, created_at="2026-10-30T00:02:00Z")
    assert latest_run_for(store, snapshot.run_id) == expected_snapshot

    malformed_metadata = dict(store.episodes[-1].metadata)
    malformed_metadata["sequence_number"] = True
    malformed_episode = replace(
        store.episodes[-1],
        id=str(uuid4()),
        metadata=malformed_metadata,
    )
    store.episodes.append(malformed_episode)
    with pytest.raises(TypeError, match="sequence_number"):
        latest_run_for(store, snapshot.run_id)
    store.episodes.pop()

    invalid_process_metadata = dict(store.episodes[-1].metadata)
    invalid_process_metadata["processes"] = {"removed-process": "completed"}
    invalid_process_episode = replace(
        store.episodes[-1],
        id="invalid-process-episode",
        metadata=invalid_process_metadata,
    )
    store.episodes.append(invalid_process_episode)
    with pytest.raises(ValueError, match="Episode invalid-process-episode has invalid run fields"):
        latest_run_for(store, snapshot.run_id)
    store.episodes.pop()

    invalid_status_metadata = dict(store.episodes[-1].metadata)
    invalid_status_metadata["processes"] = {"4.1": "unknown"}
    invalid_status_episode = replace(
        store.episodes[-1],
        id="invalid-status-episode",
        metadata=invalid_status_metadata,
    )
    store.episodes.append(invalid_status_episode)
    with pytest.raises(ValueError, match="Episode invalid-status-episode has invalid run fields"):
        latest_run_for(store, snapshot.run_id)
    store.episodes.pop()

    invalid_timestamp_episode = replace(
        store.episodes[-1],
        id="invalid-timestamp-episode",
        created_at="not-a-timestamp",
    )
    store.episodes.append(invalid_timestamp_episode)
    with pytest.raises(ValueError, match="Episode invalid-timestamp-episode has invalid created_at"):
        latest_run_for(store, snapshot.run_id)
    store.episodes.pop()

    store.append_on_query = store.episodes[-1]
    query_count = store.query_count
    with pytest.raises(RuntimeError, match="stable"):
        latest_run_for(store, snapshot.run_id)
    assert store.query_count - query_count == 3

    canonical_store = StoreDouble()
    canonical_store.persisted_id = "canonical-episode-id"
    canonical_episode = append_run(canonical_store, _snapshot(), "canonical id")
    assert canonical_episode.id == canonical_store.episodes[0].id == canonical_store.persisted_id
    assert list(tmp_path.rglob("*.db")) == []
