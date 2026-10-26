"""Catalog of the learning methodologies and its integrity check.

A pure functional module (standard library only): no file I/O and no storage access.
Callers pass decoded JSON in and receive dataclasses out (ADR-036, FDD-036).

Each of the 32 methodologies in Ideation section 2.1 has one entry. Its class follows from
its state: implemented, example-only, partial or practiced methods are ``runnable``;
candidates with a Proposed ADR are ``proof_of_concept``; everything else is ``documented``.
An example never changes a methodology's state (ADR-036 Invariant 1).
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any

__all__ = [
    "CatalogEntry",
    "ExampleClass",
    "derive_class",
    "parse_catalog",
    "validate_catalog",
]

CATALOG_IDS = range(1, 33)
PATH_PREFIX = "examples/methodologies/"

# Canonical tokens for the state column of Ideation section 2.1.
_RUNNABLE_STATES = frozenset({"implemented", "example_only", "partial", "practiced"})
_OTHER_STATES = frozenset({"candidate", "blocked", "excluded", "declined", "not_applicable"})
STATES = _RUNNABLE_STATES | _OTHER_STATES


class ExampleClass(str, Enum):
    RUNNABLE = "runnable"
    PROOF_OF_CONCEPT = "proof_of_concept"
    DOCUMENTED = "documented"


_FIELDS = {
    "id", "name", "state", "example_class", "adr", "hypothesis", "path", "reason", "reopening_condition",
}
_REQUIRED = {"id", "name", "state", "example_class"}


@dataclass(frozen=True)
class CatalogEntry:
    """One methodology's catalog record."""

    id: int
    name: str
    state: str
    example_class: ExampleClass
    adr: str | None = None
    hypothesis: str | None = None
    path: str | None = None
    reason: str = ""
    reopening_condition: str = ""

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> CatalogEntry:
        """Parse one entry strictly: unknown or missing fields and unknown values raise."""
        if not isinstance(payload, Mapping):
            raise TypeError("catalog entry must be a JSON object")
        unknown = sorted(set(payload) - _FIELDS)
        if unknown:
            raise ValueError(f"unknown catalog entry fields: {', '.join(unknown)}")
        missing = sorted(_REQUIRED - set(payload))
        if missing:
            raise ValueError(f"catalog entry is missing fields: {', '.join(missing)}")
        try:
            example_class = ExampleClass(payload["example_class"])
        except ValueError:
            valid = ", ".join(item.value for item in ExampleClass)
            raise ValueError(f"example_class must be one of {valid}; got {payload['example_class']!r}") from None
        if not isinstance(payload["id"], int) or isinstance(payload["id"], bool):
            raise TypeError(f"catalog id must be an integer; got {payload['id']!r}")
        return cls(
            id=payload["id"],
            name=str(payload["name"]),
            state=str(payload["state"]),
            example_class=example_class,
            adr=payload.get("adr"),
            hypothesis=payload.get("hypothesis"),
            path=payload.get("path"),
            reason=str(payload.get("reason") or ""),
            reopening_condition=str(payload.get("reopening_condition") or ""),
        )


def parse_catalog(data: Any) -> list[CatalogEntry]:
    """Parse decoded catalog JSON (a list of entry objects) into entries."""
    if not isinstance(data, list):
        raise TypeError("catalog must be a JSON array")
    return [CatalogEntry.from_dict(item) for item in data]


def derive_class(state: str, adr: str | None) -> ExampleClass:
    """Return the example class a state implies (FDD-036 section 2.1)."""
    if state not in STATES:
        valid = ", ".join(sorted(STATES))
        raise ValueError(f"unknown methodology state {state!r}; state must be one of {valid}")
    if state in _RUNNABLE_STATES:
        return ExampleClass.RUNNABLE
    if state == "candidate" and adr:
        return ExampleClass.PROOF_OF_CONCEPT
    return ExampleClass.DOCUMENTED


def _path_is_under_examples(path: str) -> bool:
    if not path.startswith(PATH_PREFIX) or path == PATH_PREFIX:
        return False
    return ".." not in path.split("/")


def validate_catalog(
    entries: Collection[CatalogEntry],
    ideation_states: Mapping[int, str],
    existing_paths: Collection[str] | None = None,
) -> None:
    """Raise ``ValueError`` listing every problem found; return ``None`` when the catalog is valid.

    ``ideation_states`` maps a methodology id to its expected canonical state. When
    ``existing_paths`` is given, each entry's path must be in it; ``None`` skips that check
    (a caller without a view of the filesystem passes None).
    """
    problems: list[str] = []
    seen: dict[int, int] = {}
    for entry in entries:
        seen[entry.id] = seen.get(entry.id, 0) + 1
    for entry_id in sorted(seen):
        if entry_id not in CATALOG_IDS:
            problems.append(f"id {entry_id} is outside {CATALOG_IDS.start} to {CATALOG_IDS.stop - 1}")
        if seen[entry_id] > 1:
            problems.append(f"duplicate id {entry_id}")
    missing = [i for i in CATALOG_IDS if i not in seen]
    if missing:
        problems.append("missing ids: " + ", ".join(str(i) for i in missing))

    for entry in entries:
        label = f"#{entry.id}"
        try:
            expected = derive_class(entry.state, entry.adr)
        except ValueError as exc:
            problems.append(f"{label} {exc}")
            expected = None
        if expected is not None and entry.example_class is not expected:
            problems.append(
                f"{label} class {entry.example_class.value} but state {entry.state} gives {expected.value}"
            )
        if entry.id in ideation_states and ideation_states[entry.id] != entry.state:
            problems.append(
                f"{label} state {entry.state} differs from the Ideation state {ideation_states[entry.id]}"
            )
        if entry.example_class is ExampleClass.DOCUMENTED:
            if not entry.reason.strip():
                problems.append(f"{label} documented entry needs a non-empty reason")
            if not entry.reopening_condition.strip():
                problems.append(f"{label} documented entry needs a non-empty reopening_condition")
            if entry.path is not None:
                problems.append(f"{label} documented entry must not have a path")
        elif entry.path is None:
            problems.append(f"{label} {entry.example_class.value} entry needs a path")
        elif not _path_is_under_examples(entry.path):
            problems.append(f"{label} path {entry.path} is outside {PATH_PREFIX}")
        elif existing_paths is not None and entry.path not in existing_paths:
            problems.append(f"{label} path {entry.path} does not exist")
    if problems:
        raise ValueError("; ".join(problems))
