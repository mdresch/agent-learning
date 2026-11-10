"""Contract for IMP-064: PMBOK regeneration must not overwrite a validated document or reset the baseline id.

Source: IMP-064 (Continuous-Improvement-Register), ADP-20261110-002 step GC-P2-06, Stage 16 Phase 2 note.

Intent: ``scripts/orchestrate_pmbok.py`` wrote every generated plan, the PMP, and the seed-next Spark and
Ideation files with an unconditional ``write_text``, and called ``synthesize_pmp_markdown`` without a baseline
id, so the function default ``PMP-BL-v1.0.0`` was stamped on the PMP. The guard lives in
``scripts/pmbok_write_guard.py`` (pure functions, no ``pmbok`` import) so it can be tested without running the
orchestrator.

Rules encoded:
- AC_1: a file that does not exist is created.
- AC_2: a file whose content is identical is left alone and reported unchanged.
- AC_3: an existing file whose content differs is NOT overwritten unless the caller passes ``overwrite=True``.
- AC_4: ``read_baseline_id`` returns the id in the existing PMP frontmatter, and the default only when there is
  no PMP; a PMP with a malformed id is an error, not a silent default.
- AC_5: ``orchestrate_pmbok.py`` routes every generated write through the guard and passes the baseline id read
  from the existing PMP.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
GUARD = REPO / "scripts" / "pmbok_write_guard.py"
ORCH = REPO / "scripts" / "orchestrate_pmbok.py"


def _load():
    assert GUARD.is_file(), f"missing {GUARD}"
    spec = importlib.util.spec_from_file_location("pmbok_write_guard", GUARD)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_ac1_creates_a_missing_file(tmp_path):
    g = _load()
    target = tmp_path / "plan.md"
    assert g.write_generated(target, "new", overwrite=False) == "created"
    assert target.read_text(encoding="utf-8") == "new"


def test_ac2_identical_content_is_unchanged(tmp_path):
    g = _load()
    target = tmp_path / "plan.md"
    target.write_text("same", encoding="utf-8")
    assert g.write_generated(target, "same", overwrite=False) == "unchanged"
    assert target.read_text(encoding="utf-8") == "same"


def test_ac3_differing_content_is_not_overwritten_by_default(tmp_path):
    g = _load()
    target = tmp_path / "plan.md"
    target.write_text("validated v2.0 content", encoding="utf-8")
    assert g.write_generated(target, "generic template", overwrite=False) == "skipped"
    assert target.read_text(encoding="utf-8") == "validated v2.0 content"


def test_ac3_overwrite_flag_replaces_the_file(tmp_path):
    g = _load()
    target = tmp_path / "plan.md"
    target.write_text("old", encoding="utf-8")
    assert g.write_generated(target, "new", overwrite=True) == "overwritten"
    assert target.read_text(encoding="utf-8") == "new"


def test_ac4_baseline_id_is_read_from_the_existing_pmp(tmp_path):
    g = _load()
    pmp = tmp_path / "Project-Management-Plan.md"
    pmp.write_text('---\npmp_baseline: "PMP-BL-v1.1.0"\n---\n# PMP\n', encoding="utf-8")
    assert g.read_baseline_id(pmp, default="PMP-BL-v1.0.0") == "PMP-BL-v1.1.0"


def test_ac4_default_only_when_there_is_no_pmp(tmp_path):
    g = _load()
    assert g.read_baseline_id(tmp_path / "missing.md", default="PMP-BL-v1.0.0") == "PMP-BL-v1.0.0"


def test_ac4_malformed_baseline_id_is_an_error(tmp_path):
    g = _load()
    pmp = tmp_path / "Project-Management-Plan.md"
    pmp.write_text('---\npmp_baseline: "baseline one"\n---\n', encoding="utf-8")
    with pytest.raises(ValueError, match="baseline"):
        g.read_baseline_id(pmp, default="PMP-BL-v1.0.0")


def test_ac4_pmp_without_a_baseline_line_is_an_error(tmp_path):
    g = _load()
    pmp = tmp_path / "Project-Management-Plan.md"
    pmp.write_text("# PMP with no frontmatter\n", encoding="utf-8")
    with pytest.raises(ValueError, match="baseline"):
        g.read_baseline_id(pmp, default="PMP-BL-v1.0.0")


def test_ac5_the_orchestrator_uses_the_guard_for_every_generated_write():
    source = ORCH.read_text(encoding="utf-8")
    for direct in ("doc_path.write_text(", "pmp_file.write_text(", "spark_file.write_text(", "ideation_file.write_text("):
        assert direct not in source, f"{direct} bypasses the guard"
    assert source.count("write_generated(") >= 4
    assert "read_baseline_id(" in source
    assert "baseline_id=" in source
    assert "--overwrite" in source
