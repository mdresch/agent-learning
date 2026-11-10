"""IMP-063: driving the PR gate without a store writes to a temporary one, not the governance store."""

from __future__ import annotations

from pathlib import Path

import scripts.pr_gate as pr_gate


def test_the_default_gate_store_is_temporary_under_test() -> None:
    assert pr_gate.DEFAULT_STORE_DIR != pr_gate.ROOT / "data" / "agent-learning" / "store"
    assert not pr_gate.DEFAULT_STORE_DIR.is_relative_to(pr_gate.ROOT)
