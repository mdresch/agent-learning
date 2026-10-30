"""Visible plan body text (fences and comments stripped). Shared by lint and scope checks."""

from __future__ import annotations

import re

_COMMENT = re.compile(r"<!--.*?(?:-->|\Z)", re.DOTALL)


def visible_for_measurement(text: str) -> str:
    """Plan body with fenced code and HTML comments removed (ADR-012 visible text)."""
    kept: list[str] = []
    in_fence = False
    for line in text.replace("\r\n", "\n").split("\n"):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        elif not in_fence:
            kept.append(line)
    return _COMMENT.sub(" ", "\n".join(kept))
