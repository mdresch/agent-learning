"""Contract tests for Epic 34, Story 34.1.

ADR-034 Invariant 4, BRD-034 BRU-034-04, and FDD-034 sections 2 and 3.1.
"""

from __future__ import annotations

import ast
from collections.abc import Mapping
from pathlib import Path

import pytest

from agent_learning.pmbok import PLAN_STANDARDS

ROOT = Path(__file__).resolve().parent.parent
MODULE = ROOT / "src" / "agent_learning" / "pmbok" / "legacy_registry.py"
PROCESS_IDS = (
    "4.1", "4.2", "4.3", "4.4", "4.5", "4.6", "4.7",
    "5.1", "5.2", "5.3", "5.4", "5.5", "5.6",
    "6.1", "6.2", "6.3", "6.4", "6.5", "6.6",
    "7.1", "7.2", "7.3", "7.4",
    "8.1", "8.2", "8.3",
    "9.1", "9.2", "9.3", "9.4", "9.5", "9.6",
    "10.1", "10.2", "10.3",
    "11.1", "11.2", "11.3", "11.4", "11.5", "11.6", "11.7",
    "12.1", "12.2", "12.3",
    "13.1", "13.2", "13.3", "13.4",
)
EXPECTED_DEPENDENCIES = {
    "4.1": (),
    "4.2": ("4.1", "5.1", "6.1", "7.1", "8.1", "9.1", "10.1", "11.1", "12.1", "13.2"),
    "4.3": (),
    "4.4": ("4.3",),
    "4.5": (),
    "4.6": (),
    "4.7": (),
    "5.1": ("4.1",),
    "5.2": ("5.1",),
    "5.3": ("5.2",),
    "5.4": ("5.3",),
    "5.5": ("5.4",),
    "5.6": ("5.4",),
    "6.1": ("4.1",),
    "6.2": ("6.1",),
    "6.3": ("6.2",),
    "6.4": ("6.3",),
    "6.5": ("6.4",),
    "6.6": ("6.5",),
    "7.1": ("4.1",),
    "7.2": ("7.1", "6.5"),
    "7.3": ("7.2",),
    "7.4": ("7.3",),
    "8.1": ("4.1", "5.2"),
    "8.2": (),
    "8.3": ("8.2",),
    "9.1": ("4.1",),
    "9.2": ("9.1", "5.4"),
    "9.3": (),
    "9.4": ("9.3",),
    "9.5": ("9.4",),
    "9.6": ("9.3",),
    "10.1": ("4.1",),
    "10.2": (),
    "10.3": ("10.2",),
    "11.1": ("4.1",),
    "11.2": ("11.1",),
    "11.3": ("11.2",),
    "11.4": ("11.3",),
    "11.5": ("11.4",),
    "11.6": ("11.5",),
    "11.7": ("11.6",),
    "12.1": ("4.1",),
    "12.2": ("12.1",),
    "12.3": ("12.2",),
    "13.1": (),
    "13.2": ("13.1",),
    "13.3": (),
    "13.4": ("13.3",),
}


def _legacy_processes() -> Mapping[str, tuple[str, ...]]:
    from agent_learning.pmbok.legacy_registry import legacy_processes

    return legacy_processes()


def test_ac0_catalogue_has_all_processes_and_required_dependencies() -> None:
    processes = _legacy_processes()

    assert len(processes) == len(PROCESS_IDS)
    assert set(processes) == set(PROCESS_IDS)
    assert processes == EXPECTED_DEPENDENCIES
    assert processes["5.1"] == ("4.1",)
    assert processes["4.2"] == (
        "4.1", "5.1", "6.1", "7.1", "8.1", "9.1", "10.1", "11.1", "12.1", "13.2",
    )
    with pytest.raises(KeyError):
        processes["unknown"]


def test_ac1_every_plan_legacy_code_is_in_the_catalogue() -> None:
    processes = _legacy_processes()

    assert {standard.legacy for standard in PLAN_STANDARDS.values()} <= processes.keys()


def test_ac2_catalogue_is_immutable_and_repeatable() -> None:
    processes = _legacy_processes()
    with pytest.raises(TypeError):
        processes["5.1"] = ()  # type: ignore[index]

    assert _legacy_processes() == processes


def test_ac3_module_has_no_forbidden_dependencies_or_io() -> None:
    tree = ast.parse(MODULE.read_text(encoding="utf-8"))
    forbidden_imports = {
        "agent_learning.storage",
        "io",
        "pathlib",
        "pydantic",
        "pmbok",
        "requests",
        "socket",
        "storage",
        "urllib",
    }
    forbidden_calls = {
        "connect",
        "create_connection",
        "open",
        "read_bytes",
        "read_text",
        "sleep",
        "urlopen",
    }
    forbidden_names = {"LearningStore"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_imports
                assert alias.asname not in forbidden_names
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in forbidden_imports
            assert all(alias.name not in forbidden_names for alias in node.names)
        elif isinstance(node, ast.Call):
            called_name = node.func.id if isinstance(node.func, ast.Name) else (
                node.func.attr if isinstance(node.func, ast.Attribute) else ""
            )
            assert called_name not in forbidden_calls
