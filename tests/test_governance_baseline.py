"""Guard: approved governance documents change only through Stage 16.

ADR-007 freezes an approved ADR, BRD, FDD or user story. ``tests/governance_baseline.json`` fingerprints each one.
A document that differs from its fingerprint fails this test until the change has been classified (``classify-diff-type``),
accepted, recorded in the document as ``Amended <date> at Stage 16 ... episode `<id>```, and the baseline refreshed with
``scripts/governance_baseline.py``, which checks that record against the episode store.

Epic files ignore ``**Status:**`` lines in the fingerprint, because implementing a story updates them as progress.
The guard is run on a small fake tree below, so each way it should fail is shown to fail.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "governance_baseline", ROOT / "scripts" / "governance_baseline.py"
)
assert SPEC is not None and SPEC.loader is not None
gb = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gb)


def test_approved_documents_are_unchanged_apart_from_recorded_amendments() -> None:
    manifest = json.loads(gb.MANIFEST.read_text(encoding="utf-8"))
    problems = gb.find_problems(manifest, ROOT)
    assert not problems, "\n" + "\n".join(problems)


def test_manifest_is_well_formed() -> None:
    manifest = json.loads(gb.MANIFEST.read_text(encoding="utf-8"))
    docs = manifest["documents"]
    assert len(docs) >= 100
    for rel, entry in docs.items():
        assert (ROOT / rel).is_file(), rel
        assert len(entry["sha256"]) == 64 and entry["family"] in gb.FAMILIES, rel
        assert entry["status"] in gb.GOVERNED, rel
        assert all(a["stage"] == 16 and len(a["episode"]) == 8 for a in entry["amendments"]), rel


# --- the guard has to be able to fail: a tiny fake tree -------------------------------------------------------------

ADR = "# ADR 1\n\n## 2. Status\n\n**Accepted (2026-10-23)** approved by Menno, episode `aaaaaaaa...`.\n\n## 3. Context\nThe decision.\n"
BRD = "# BRD-001\n\n**Status:** Approved (2026-10-23, Menno), adjudicated via `approve-brd` (episode `bbbbbbbb...`).\n\nRule A.\n"
FDD = "# FDD-001\n\n**Status:** Approved (2026-10-23, Menno), adjudicated via `approve-fdd` (episode `cccccccc...`).\n\nDesign 1.\n"
EPIC = (
    "# Epic 1\n\n**Status:** Approved (2026-10-23, Menno), adjudicated via `approve-user-stories` (episode `dddddddd...`).\n\n"
    "## Story 1.1\n\n**Status:** Approved\n\n- AC_0: first criterion.\n"
)
PATHS = {
    "adr": "docs/adr/ADR-001-x.md",
    "brd": "docs/project-docs/Business-Requirements/BRD-001-x.md",
    "fdd": "docs/project-docs/Functional-Design/FDD-001-x.md",
    "story": "docs/user-stories/epic-1-x.md",
}
RECORD = "Amended 2026-11-05 at Stage 16: AC_0 reworded, classified `amendment_log_entry` (robust utility 0.9, episode `eeeeeeee...`) and accepted."


@pytest.fixture
def tree(tmp_path: Path) -> tuple[dict, Path]:
    for family, text in {"adr": ADR, "brd": BRD, "fdd": FDD, "story": EPIC}.items():
        path = tmp_path / PATHS[family]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.replace("\n", "\r\n").encode())  # CRLF on purpose: line endings must not matter
    manifest, errors, _ = gb.refresh(None, tmp_path, None, init=True)
    assert not errors
    return manifest, tmp_path


def edit(root: Path, family: str, old: str, new: str) -> None:
    path = root / PATHS[family]
    path.write_text(path.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")


def test_a_clean_tree_has_no_problems(tree: tuple[dict, Path]) -> None:
    manifest, root = tree
    assert gb.find_problems(manifest, root) == []


@pytest.mark.parametrize(
    "family,old,new",
    [
        ("adr", "The decision.", "A different decision."),
        ("brd", "Rule A.", "Rule B."),
        ("fdd", "Design 1.", "Design 2."),
    ],
)
def test_an_edit_to_an_approved_document_is_caught(
    tree: tuple[dict, Path], family: str, old: str, new: str
) -> None:
    manifest, root = tree
    edit(root, family, old, new)
    problems = gb.find_problems(manifest, root)
    assert len(problems) == 1 and "Stage 16" in problems[0] and PATHS[family] in problems[0]


def test_an_edit_to_story_content_is_caught(tree: tuple[dict, Path]) -> None:
    manifest, root = tree
    edit(root, "story", "first criterion", "second criterion")
    assert any("has changed since it was baselined" in p for p in gb.find_problems(manifest, root))


def test_story_progress_in_a_status_line_is_not_an_amendment(tree: tuple[dict, Path]) -> None:
    manifest, root = tree
    edit(
        root,
        "story",
        "**Status:** Approved\n",
        "**Status:** In Progress (Stories 1.1 In Progress)\n",
    )
    assert gb.find_problems(manifest, root) == []
    edit(
        root,
        "story",
        "**Status:** In Progress (Stories 1.1 In Progress)\n",
        "**Status:** Completed (2026-11-05), implemented in feat/story-1.1.\n",
    )
    assert gb.find_problems(manifest, root) == []


def test_a_governed_document_cannot_slip_back_to_draft(tree: tuple[dict, Path]) -> None:
    manifest, root = tree
    edit(root, "brd", "**Status:** Approved", "**Status:** Draft")
    assert any("unrecorded lifecycle change" in p for p in gb.find_problems(manifest, root))


def test_a_removed_document_is_caught(tree: tuple[dict, Path]) -> None:
    manifest, root = tree
    (root / PATHS["fdd"]).unlink()
    assert any("the file is gone" in p for p in gb.find_problems(manifest, root))


def test_a_newly_approved_document_must_enter_the_baseline(tree: tuple[dict, Path]) -> None:
    manifest, root = tree
    extra = root / "docs/project-docs/Business-Requirements/BRD-002-y.md"
    extra.write_text("# BRD-002\n\n**Status:** Approved (2026-11-05, Menno)\n\nRule.\n", encoding="utf-8")
    assert any("not in the governance baseline" in p for p in gb.find_problems(manifest, root))


def test_a_draft_is_not_governed_yet(tree: tuple[dict, Path]) -> None:
    manifest, root = tree
    (root / "docs/project-docs/Business-Requirements/BRD-002-y.md").write_text(
        "# BRD-002\n\n**Status:** Draft\n\nRule.\n", encoding="utf-8"
    )
    assert gb.find_problems(manifest, root) == []


def test_deleting_a_recorded_amendment_is_caught(tree: tuple[dict, Path]) -> None:
    manifest, root = tree
    edit(root, "brd", "Rule A.", f"Rule A. {RECORD}")
    manifest, errors, _ = gb.refresh(manifest, root, lambda *_: None)
    assert not errors and gb.find_problems(manifest, root) == []
    edit(root, "brd", RECORD, "")
    problems = gb.find_problems(manifest, root)
    assert any("no longer records its Stage 16 amendment" in p for p in problems)


# --- the only sanctioned way to update the manifest -------------------------------------------------------------------


def test_refresh_refuses_a_change_with_no_stage_16_record(tree: tuple[dict, Path]) -> None:
    manifest, root = tree
    edit(root, "brd", "Rule A.", "Rule B.")
    _, errors, _ = gb.refresh(manifest, root, lambda *_: None)
    assert len(errors) == 1 and "records no new" in errors[0]


def test_refresh_accepts_a_change_with_a_verified_record_and_updates_the_baseline(
    tree: tuple[dict, Path],
) -> None:
    manifest, root = tree
    edit(root, "brd", "Rule A.", f"Rule B. {RECORD}")
    seen: list[tuple] = []
    new, errors, notes = gb.refresh(manifest, root, lambda *a: seen.append(a))
    assert not errors and notes and seen == [("classify-diff-type", "eeeeeeee", "BRD-001-x.md")]
    assert [a["episode"] for a in new["documents"][PATHS["brd"]]["amendments"]] == ["eeeeeeee"]
    assert gb.find_problems(new, root) == []


def test_refresh_refuses_when_the_episode_does_not_check_out(tree: tuple[dict, Path]) -> None:
    manifest, root = tree
    edit(root, "brd", "Rule A.", f"Rule B. {RECORD}")
    _, errors, _ = gb.refresh(
        manifest, root, lambda *_: "classify-diff-type episode eeeeeeee was not accepted"
    )
    assert errors and "was not accepted" in errors[0]


def test_refresh_does_not_take_the_approval_episode_for_an_amendment(tree: tuple[dict, Path]) -> None:
    manifest, _ = tree
    entry = manifest["documents"][PATHS["brd"]]
    assert entry["approval_episode"] == "bbbbbbbb" and entry["amendments"] == []


def test_refresh_adds_a_newly_approved_document_only_with_a_verified_approval_episode(
    tree: tuple[dict, Path],
) -> None:
    manifest, root = tree
    extra = root / "docs/project-docs/Business-Requirements/BRD-002-y.md"
    extra.write_text(
        "# BRD-002\n\n**Status:** Approved (2026-11-05, Menno), adjudicated via `approve-brd` (episode `ffffffff...`).\n\nRule.\n",
        encoding="utf-8",
    )
    calls: list[tuple] = []
    new, errors, _ = gb.refresh(manifest, root, lambda *a: calls.append(a))
    assert (
        not errors
        and calls == [("approve-brd", "ffffffff", None)]
        and "docs/project-docs/Business-Requirements/BRD-002-y.md" in new["documents"]
    )
    extra.write_text("# BRD-002\n\n**Status:** Approved (2026-11-05, Menno)\n\nRule.\n", encoding="utf-8")
    _, errors, _ = gb.refresh(manifest, root, lambda *_: None)
    assert errors and "cites no approval episode" in errors[0]
