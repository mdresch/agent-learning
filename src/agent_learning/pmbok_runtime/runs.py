"""LearningStore adapters for append-only PMBOK orchestration run Episodes."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Protocol

from agent_learning.pmbok.run_state import (
    RUN_AGENT_ID,
    RUN_TASK_ID,
    RunSnapshot,
    build_run_fields,
    latest_run,
)
from agent_learning.types import Episode


class RunStore(Protocol):
    """The LearningStore operations required by the PMBOK run adapter."""

    def store_episode(self, episode: Episode) -> str: ...

    def count_episodes(
        self,
        agent_id: str,
        *,
        task_id: str | None = None,
        full_only: bool = False,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> int: ...

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
    ) -> list[Episode]: ...


def append_run(store: RunStore, snapshot: RunSnapshot, result_summary: str) -> Episode:
    """Append one run-state Episode without creating a separate persistence store."""
    fields = build_run_fields(snapshot, result_summary)
    episode = Episode(
        agent_id=fields.agent_id,
        task_id=fields.task_id,
        action_type=fields.action_type,
        action_logprob=fields.action_logprob,
        metadata=dict(fields.metadata),
        result_summary=fields.result_summary,
        created_at=snapshot.created_at,
    )
    store.store_episode(episode)
    return episode


def _snapshot_from_episode(episode: Episode) -> RunSnapshot:
    metadata = episode.metadata
    processes = metadata.get("processes")
    gate_episode_ids = metadata.get("gate_episode_ids")
    route_episode_ids = metadata.get("route_episode_ids")
    if not isinstance(processes, Mapping):
        raise TypeError(f"Episode {episode.id} has invalid processes metadata")
    if not isinstance(gate_episode_ids, Mapping):
        raise TypeError(f"Episode {episode.id} has invalid gate_episode_ids metadata")
    if not isinstance(route_episode_ids, Mapping):
        raise TypeError(f"Episode {episode.id} has invalid route_episode_ids metadata")

    normalized_gates: dict[str, tuple[str, str, str]] = {}
    for plan_id, episode_ids in gate_episode_ids.items():
        if not isinstance(plan_id, str) or not isinstance(episode_ids, Sequence) or isinstance(episode_ids, str):
            raise TypeError(f"Episode {episode.id} has invalid gate_episode_ids metadata")
        if len(episode_ids) != 3 or not all(isinstance(value, str) for value in episode_ids):
            raise TypeError(f"Episode {episode.id} has invalid gate_episode_ids metadata")
        normalized_gates[plan_id] = (episode_ids[0], episode_ids[1], episode_ids[2])

    run_id = metadata.get("run_id")
    phase = metadata.get("phase")
    sequence_number = metadata.get("sequence_number")
    baseline_hash = metadata.get("baseline_hash")
    if not isinstance(run_id, str) or not isinstance(phase, str):
        raise TypeError(f"Episode {episode.id} has invalid run identity metadata")
    if not isinstance(sequence_number, int):
        raise TypeError(f"Episode {episode.id} has invalid sequence_number metadata")
    if baseline_hash is not None and not isinstance(baseline_hash, str):
        raise TypeError(f"Episode {episode.id} has invalid baseline_hash metadata")
    if not all(
        isinstance(process_id, str) and isinstance(status, str)
        for process_id, status in processes.items()
    ):
        raise TypeError(f"Episode {episode.id} has invalid processes metadata")
    if not all(
        isinstance(plan_id, str) and isinstance(route_id, str)
        for plan_id, route_id in route_episode_ids.items()
    ):
        raise TypeError(f"Episode {episode.id} has invalid route_episode_ids metadata")
    if not isinstance(episode.result_summary, str):
        raise TypeError(f"Episode {episode.id} has invalid result_summary")

    snapshot = RunSnapshot(
        run_id=run_id,
        sequence_number=sequence_number,
        created_at=episode.created_at,
        phase=phase,
        processes=dict(processes),
        baseline_hash=baseline_hash,
        gate_episode_ids=normalized_gates,
        route_episode_ids=dict(route_episode_ids),
    )
    return snapshot


def latest_run_for(store: RunStore, run_id: str) -> RunSnapshot | None:
    """Read the latest snapshot for one run from standard LearningStore episodes."""
    while True:
        count = store.count_episodes(agent_id=RUN_AGENT_ID, task_id=RUN_TASK_ID)
        if count == 0:
            if store.count_episodes(agent_id=RUN_AGENT_ID, task_id=RUN_TASK_ID) == 0:
                return None
            continue
        episodes = store.query_episodes(
            agent_id=RUN_AGENT_ID,
            task_id=RUN_TASK_ID,
            limit=count,
        )
        if (
            store.count_episodes(agent_id=RUN_AGENT_ID, task_id=RUN_TASK_ID) == count
            and len(episodes) == count
        ):
            break

    snapshots = [
        _snapshot_from_episode(episode)
        for episode in episodes
        if episode.metadata.get("run_id") == run_id
    ]
    return latest_run(snapshots)
