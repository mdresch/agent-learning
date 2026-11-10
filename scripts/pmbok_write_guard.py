"""Write guard for the PMBOK orchestrator (IMP-064).

``orchestrate_pmbok.py`` generates plans from a template. Without a guard it replaced validated documents and
stamped a default baseline id on the PMP. These helpers are pure (no ``pmbok`` import) so a contract test can
exercise them without running the orchestrator.
"""

from __future__ import annotations

import re
from pathlib import Path

_BASELINE = re.compile(r"""^pmp_baseline(?:_id)?:\s*['"]?(PMP-BL-v\d+\.\d+\.\d+)['"]?\s*$""", re.MULTILINE)
_ANY_BASELINE_LINE = re.compile(r"^pmp_baseline(?:_id)?:", re.MULTILINE)


def write_generated(path: Path, content: str, *, overwrite: bool) -> str:
    """Write generated ``content`` to ``path`` without replacing a different existing file.

    Returns ``created``, ``unchanged``, ``skipped`` (exists and differs, ``overwrite`` is false) or
    ``overwritten``. The caller reports the outcome; a skipped file is never an error, because the existing file
    may be the validated one.
    """
    path = Path(path)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return "created"
    if path.read_text(encoding="utf-8") == content:
        return "unchanged"
    if not overwrite:
        return "skipped"
    path.write_text(content, encoding="utf-8")
    return "overwritten"


def read_baseline_id(pmp_path: Path, *, default: str) -> str:
    """Return the baseline id in an existing PMP's frontmatter; ``default`` only when there is no PMP.

    A PMP that exists but has no readable ``pmp_baseline`` line is an error: guessing would stamp a wrong id on
    the integrated plan.
    """
    pmp_path = Path(pmp_path)
    if not pmp_path.exists():
        return default
    text = pmp_path.read_text(encoding="utf-8")
    found = _BASELINE.search(text)
    if found:
        return found.group(1)
    if _ANY_BASELINE_LINE.search(text):
        raise ValueError(f"{pmp_path} has a pmp_baseline line that is not a PMP-BL-vX.Y.Z id")
    raise ValueError(f"{pmp_path} has no pmp_baseline line, so its baseline id cannot be read")
