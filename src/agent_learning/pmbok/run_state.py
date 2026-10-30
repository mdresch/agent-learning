"""Pure run snapshots and Episode fields for PMBOK lifecycle orchestration."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from .legacy_registry import LEGACY_PROCESSES

RUN_AGENT_ID = "pmbok-orchestration"
RUN_TASK_ID = "pmbok-lifecycle-run"
PROCESS_STATUSES = ("not_started", "in_progress", "completed", "failed")
MAX_STRING_LENGTH = 256


@dataclass(frozen=True)
class RunSnapshot:
    """One immutable view of orchestration state."""

    run_id: str
    sequence_number: int
    created_at: str
    phase: str
    processes: Mapping[str, str]
    baseline_hash: str | None
    gate_episode_ids: Mapping[str, tuple[str, str, str]]
    route_episode_ids: Mapping[str, str]


@dataclass(frozen=True)
class RunEpisodeFields:
    """Episode fields shared by the PMBOK runtime and standard LearningStore."""

    agent_id: str
    task_id: str
    action_type: str
    action_logprob: None
    metadata: Mapping[str, object]
    result_summary: str


def _validate_string_lengths(value: object, field: str) -> None:
    if isinstance(value, str):
        if len(value) > MAX_STRING_LENGTH:
            raise ValueError(f"{field} must not exceed {MAX_STRING_LENGTH} characters")
    elif isinstance(value, Mapping):
        for key, item in value.items():
            _validate_string_lengths(key, field)
            _validate_string_lengths(item, field)
    elif isinstance(value, (tuple, list)):
        for item in value:
            _validate_string_lengths(item, field)


def _created_at_instant(created_at: str) -> datetime:
    if not isinstance(created_at, str):
        raise TypeError("created_at must be a string")
    value = f"{created_at[:-1]}+00:00" if created_at.endswith("Z") else created_at
    try:
        timestamp = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("created_at must be a timezone-aware ISO-8601 timestamp") from exc
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("created_at must be a timezone-aware ISO-8601 timestamp")
    return timestamp.astimezone(timezone.utc)


def _validate_snapshot(snapshot: RunSnapshot, result_summary: str) -> None:
    if not isinstance(result_summary, str):
        raise TypeError("result_summary must be a string")
    _validate_string_lengths(snapshot.run_id, "run_id")
    if not snapshot.run_id:
        raise ValueError("run_id must not be empty")
    try:
        UUID(snapshot.run_id)
    except (AttributeError, ValueError) as exc:
        raise ValueError("run_id must be a UUID") from exc

    if isinstance(snapshot.sequence_number, bool) or not isinstance(snapshot.sequence_number, int):
        raise TypeError("sequence_number must be an integer")
    if snapshot.sequence_number < 0:
        raise ValueError("sequence_number must be non-negative")
    if not isinstance(snapshot.processes, Mapping):
        raise TypeError("processes must be a mapping")
    if not isinstance(snapshot.created_at, str):
        raise TypeError("created_at must be a string")
    _validate_string_lengths(snapshot.created_at, "created_at")
    _created_at_instant(snapshot.created_at)
    _validate_string_lengths(snapshot.phase, "phase")
    _validate_string_lengths(snapshot.processes, "processes")
    _validate_string_lengths(snapshot.baseline_hash, "baseline_hash")
    _validate_string_lengths(snapshot.gate_episode_ids, "gate_episode_ids")
    _validate_string_lengths(snapshot.route_episode_ids, "route_episode_ids")
    _validate_string_lengths(result_summary, "result_summary")

    for process_id, status in snapshot.processes.items():
        if process_id not in LEGACY_PROCESSES:
            raise ValueError(f"processes contains unknown process id {process_id!r}")
        if status not in PROCESS_STATUSES:
            raise ValueError(f"processes contains unknown status {status!r}")

    for plan_id, episode_ids in snapshot.gate_episode_ids.items():
        if not isinstance(episode_ids, tuple) or len(episode_ids) != 3:
            raise ValueError(f"gate_episode_ids[{plan_id!r}] must contain three strings")
        if not all(isinstance(value, str) for value in episode_ids):
            raise ValueError(f"gate_episode_ids[{plan_id!r}] must contain three strings")

def build_run_fields(snapshot: RunSnapshot, result_summary: str) -> RunEpisodeFields:
    """Validate a snapshot and build its stable Episode identity and metadata."""
    _validate_snapshot(snapshot, result_summary)
    return RunEpisodeFields(
        agent_id=RUN_AGENT_ID,
        task_id=RUN_TASK_ID,
        action_type="governance",
        action_logprob=None,
        metadata={
            "run_id": snapshot.run_id,
            "phase": snapshot.phase,
            "processes": dict(snapshot.processes),
            "sequence_number": snapshot.sequence_number,
            "baseline_hash": snapshot.baseline_hash,
            "gate_episode_ids": dict(snapshot.gate_episode_ids),
            "route_episode_ids": dict(snapshot.route_episode_ids),
        },
        result_summary=result_summary,
    )


def latest_run(snapshots: Sequence[RunSnapshot]) -> RunSnapshot | None:
    """Return the greatest sequence/time snapshot, keeping the first exact tie."""
    return max(
        snapshots,
        key=lambda snapshot: (
            snapshot.sequence_number,
            _created_at_instant(snapshot.created_at),
        ),
        default=None,
    )
