"""Shared types and constants of the subsidiary management plan lint (ADR-012, FDD-012 section 2).

Pure: standard library only, no I/O and no storage.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class LintFlag:
    """One finding of the plan lint.

    ``tier`` is a Flag Tier (A, B or C), never a Plan Tier. ``line`` is the 1-based line in the
    original text when known; ``evidence`` is the offending text.
    """

    code: str
    tier: Literal["A", "B", "C"]
    message: str
    line: int | None = None
    evidence: str = ""
