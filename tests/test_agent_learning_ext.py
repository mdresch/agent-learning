"""The extension package and its console script.

Fork rule: our commands live in ``agent_learning_ext``, and Microsoft's ``agent-learn`` stays as Microsoft ships it. ``agent-learn-ext`` is
a copy of Microsoft's CLI plus our commands, so it must offer every command ``agent-learn`` does.
"""

from __future__ import annotations

import subprocess
import sys
from importlib import metadata

import pytest


def run(*module_and_args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-B", "-m", *module_and_args],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def test_console_script_is_registered() -> None:
    scripts = {e.name: e.value for e in metadata.entry_points(group="console_scripts")}
    assert scripts.get("agent-learn-ext") == "agent_learning_ext.cli:main"
    assert scripts.get("agent-learn") == "agent_learning.cli:main", (
        "Microsoft's entry point must stay as shipped"
    )


def test_main_prints_help_and_returns_zero_without_a_command() -> None:
    from agent_learning_ext.cli import main

    assert main([]) == 0  # no command prints help and returns 0


def test_python_dash_m_reports_the_same_version() -> None:
    ext = run("agent_learning_ext", "--version")
    base = run("agent_learning.cli", "--version")
    assert ext.returncode == base.returncode == 0
    assert ext.stdout.split()[1:] == base.stdout.split()[1:]


def test_every_microsoft_command_is_still_offered() -> None:
    """agent-learn-ext is a superset: it offers every command Microsoft's agent-learn does."""
    import re

    def commands(module: str) -> set[str]:
        out = run(module, "--help").stdout
        return set(re.findall(r"^\s{4}([a-z][\w-]+)\s", out, flags=re.MULTILINE))

    base, ext = commands("agent_learning.cli"), commands("agent_learning_ext")
    assert base, "could not read Microsoft's command list"
    assert base <= ext, sorted(base - ext)
