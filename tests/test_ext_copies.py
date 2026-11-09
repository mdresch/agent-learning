"""Drift guard for the modules copied into ``agent_learning_ext``.

Fork rule: a Microsoft module that has to behave differently is copied into ``agent_learning_ext`` and amended there. Each
copy starts with ``# ext-source: <Microsoft file> sha256:<fingerprint>``, the fingerprint of the Microsoft file it was
copied from. ``tests/upstream_manifest.json`` holds the fingerprint of every Microsoft file at the pinned upstream commit.

When the pin moves and a Microsoft file changes, the copy no longer matches it. This test fails and names the copy: merge
the upstream change into the copy, then update its hash. Without this a sync could silently leave a copy behind.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "tests" / "upstream_manifest.json").read_text(encoding="utf-8"))
HEADER = re.compile(r"^# ext-source: (?P<path>\S+) sha256:(?P<hash>[0-9a-f]{64})$")


def copies() -> dict[Path, tuple[str, str]]:
    found: dict[Path, tuple[str, str]] = {}
    for path in sorted((ROOT / "src" / "agent_learning_ext").rglob("*.py")):
        first = path.read_text(encoding="utf-8").splitlines()[:1]
        match = HEADER.match(first[0]) if first else None
        if match:
            found[path] = (match["path"], match["hash"])
    return found


def test_there_are_copies_to_check() -> None:
    assert len(copies()) >= 3, "expected the learner, runner and audit copies"


def test_every_copy_names_a_microsoft_file_and_matches_the_pinned_version() -> None:
    stale = []
    for path, (source, digest) in copies().items():
        name = path.relative_to(ROOT).as_posix()
        pinned = MANIFEST["files"].get(source)
        if pinned is None:
            stale.append(f"{name} names {source}, which is not a Microsoft file in the manifest.")
        elif pinned != digest:
            stale.append(
                f"{name} was copied from an older {source}. Microsoft's file changed at the pin "
                f"{MANIFEST['pin'][:10]}: merge the change into the copy, then update its ext-source hash."
            )
    assert not stale, "\n" + "\n".join(stale)


def test_a_copy_has_no_relative_imports() -> None:
    """A relative import in a copy would resolve inside agent_learning_ext and quietly import the wrong module."""
    bad = [
        p.relative_to(ROOT).as_posix()
        for p in copies()
        if re.search(r"^from \.\.", p.read_text(encoding="utf-8"), flags=re.MULTILINE)
    ]
    assert not bad, f"parent-relative import in a copy: {bad}"
