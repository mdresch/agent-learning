"""Contract tests for the Project Status Register (docs/project-docs/Project-Status-Register.md).

Governing specifications:
- sidpa-template governance change e97e8a3 (docs/registers/Project-Status-Register.template.md,
  docs/sequence-and-lessons.md section 8, rules 23-24): one live, non-governed "where are we" register
  so a model resuming after a session or model limit can read the Phase, Stage and Epic in flight.
- Intent: the register is overwritten in place at every natural pause; it is not an approval artifact.

Acceptance Criteria:
- AC_0 (Present): the register exists under docs/project-docs/ and carries the template's front matter.
- AC_1 (Orientation Fields): section 1 has every orientation field of the template.
- AC_2 (Cites Evidence): the session close-off checkpoint cites real evidence (a commit hash or a PR number),
  not only a document's own lifecycle_stage label.
- AC_3 (Sections): phase status (2), epic status (3) and how-to-keep-current (4) sections exist.
- AC_4 (Skill Hook): the implement-story skill tells the agent to update the register after commit, at any
  natural pause, and in the definition of done.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REGISTER = REPO / "docs" / "project-docs" / "Project-Status-Register.md"
SKILL = REPO / ".claude" / "skills" / "implement-story" / "SKILL.md"

FIELDS = [
    "Current Phase",
    "Current PMP Baseline",
    "Session close-off checkpoint",
    "Current macro Stage",
    "Last Epic/unit of work fully completed",
    "Next Epic/unit of work to implement",
    "Last commit on the base branch",
    "Open side-thread outside the formal loop",
    "Stage numbering",
]


def _text() -> str:
    assert REGISTER.is_file(), f"missing register: {REGISTER}"
    return REGISTER.read_text(encoding="utf-8")


def test_ac0_present_with_front_matter() -> None:
    text = _text()
    assert text.startswith("---")
    assert 'artifact_id: "project-status-register"' in text
    assert re.search(r'^last_updated: "20\d\d-\d\d-\d\d', text, re.MULTILINE)


def test_ac1_orientation_fields() -> None:
    text = _text()
    for field in FIELDS:
        assert f"**{field}" in text, f"section 1 is missing the field {field!r}"


def test_ac2_checkpoint_cites_evidence() -> None:
    text = _text()
    row = next((line for line in text.splitlines() if line.startswith("| **Session close-off checkpoint**")), "")
    assert row, "no session close-off checkpoint row"
    assert re.search(r"\b[0-9a-f]{7}\b|PR #\d+|#\d{2,3}\b", row), "the checkpoint cites no commit hash or PR number"


def test_ac3_sections() -> None:
    text = _text()
    for heading in ("## 1. Current Orientation", "## 2. Phase Status", "## 3. Epic", "## 4. How to keep this current"):
        assert heading in text, f"missing section {heading!r}"


def test_ac4_skill_hook() -> None:
    assert SKILL.is_file(), f"missing skill: {SKILL}"
    skill = SKILL.read_text(encoding="utf-8")
    assert skill.count("Project-Status-Register.md") >= 3
    assert "Session-boundary note" in skill


def test_chain_coverage_uses_template_stage_names() -> None:
    """Governance alignment: stages 5, 17, 18 are named as in sidpa-template docs/chain-coverage.md."""
    doc = REGISTER.parents[1] / "intent-to-outcome-chain-coverage.md"
    assert doc.is_file(), f"missing chain-coverage doc: {doc}"
    text = doc.read_text(encoding="utf-8")
    for row in ("| 5 | **Pillars & Architecture** |", "| 17 | **Adaptation Plan** |", "| 18 | **Intent Refinement** | **Closing / Strategic Feedback** |"):
        assert row in text, f"chain-coverage doc is missing the template-aligned row {row!r}"


def test_audit_register_exists_and_is_empty() -> None:
    """Stage 11 record store exists (instantiated from the template) and holds no backfilled findings."""
    audit = REGISTER.parent / "Audit-Register.md"
    assert audit.is_file(), f"missing audit register: {audit}"
    text = audit.read_text(encoding="utf-8")
    assert "first real audit gets AUDIT-001" in text, "Audit-Register.md must stay empty until a real audit is run"
