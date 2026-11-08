"""Guard: Microsoft's modules are never edited in place.

Fork rule (decided by the maintainer, recorded here until its ADR is written): code that came from
microsoft/agent-learning is never edited. A change goes into a duplicated module in ``agent_learning_ext`` so that merging
``upstream/main`` never clashes with code we wrote.

``tests/upstream_manifest.json`` fingerprints every Microsoft source file at a pinned upstream commit. Thirteen files were
already edited before the rule was written down; they sit in ``known_edited`` as debt that may only shrink:

* a Microsoft file that differs from the pin and is NOT in ``known_edited`` fails: a new in-place edit.
* a file in ``known_edited`` that now matches the pin fails until you delete it from the list: the ratchet.
* a ``known_edited`` entry that names no Microsoft file fails: a typo, or a list that was grown by hand.

Moving the pin after a sync is ``uv run python scripts/refresh_upstream_manifest.py``. Never add a path to ``known_edited``.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tests" / "upstream_manifest.json"


def fingerprint(data: bytes) -> str:
    """Hash with line endings ignored: git stores LF, a Windows working tree has CRLF."""
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def find_problems(manifest: dict, root: Path) -> list[str]:
    files: dict[str, str] = manifest["files"]
    known = set(manifest["known_edited"])
    problems: list[str] = []

    for name in sorted(known - files.keys()):
        problems.append(
            f"known_edited lists {name}, which is not a Microsoft file in the manifest. The list may only shrink."
        )

    for name, pinned in sorted(files.items()):
        path = root / name
        matches = path.is_file() and fingerprint(path.read_bytes()) == pinned
        if name in known:
            if matches:
                problems.append(
                    f"{name} matches the pin again: delete it from known_edited (the debt shrank)."
                )
        elif not matches:
            what = "was removed" if not path.is_file() else "was edited in place"
            problems.append(
                f"{name} {what}. Microsoft modules are never edited: restore it with "
                f"`git checkout <pin> -- {name}` and put the change in a duplicated module in agent_learning_ext."
            )
    return problems


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_microsoft_modules_are_unedited_apart_from_known_debt() -> None:
    problems = find_problems(load_manifest(), ROOT)
    assert not problems, "\n" + "\n".join(problems)


def test_manifest_is_well_formed() -> None:
    manifest = load_manifest()
    assert re.fullmatch(r"[0-9a-f]{40}", manifest["pin"]), "pin must be a full commit hash"
    assert manifest["files"], "manifest lists no Microsoft files"
    assert all(n.startswith("src/agent_learning/") and n.endswith(".py") for n in manifest["files"])
    assert all(re.fullmatch(r"[0-9a-f]{64}", h) for h in manifest["files"].values())
    assert manifest["known_edited"] == sorted(set(manifest["known_edited"])), (
        "known_edited must be sorted and unique"
    )


# The guard has to be able to fail. These cases run it on a tiny fake tree, so no real file is touched.


@pytest.fixture
def tree(tmp_path: Path) -> tuple[dict, Path]:
    (tmp_path / "src" / "agent_learning").mkdir(parents=True)
    names = ["src/agent_learning/a.py", "src/agent_learning/b.py", "src/agent_learning/c.py"]
    files = {}
    for n in names:
        (tmp_path / n).write_bytes(f"# {n}\r\nvalue = 1\r\n".encode())  # CRLF on purpose
        files[n] = fingerprint(f"# {n}\nvalue = 1\n".encode())
    return {"pin": "0" * 40, "files": files, "known_edited": []}, tmp_path


def test_clean_tree_has_no_problems_even_with_crlf(tree: tuple[dict, Path]) -> None:
    manifest, root = tree
    assert find_problems(manifest, root) == []


def test_a_new_in_place_edit_is_caught(tree: tuple[dict, Path]) -> None:
    manifest, root = tree
    (root / "src/agent_learning/b.py").write_text("value = 2\n")
    problems = find_problems(manifest, root)
    assert (
        len(problems) == 1
        and "b.py was edited in place" in problems[0]
        and "agent_learning_ext" in problems[0]
    )


def test_a_removed_microsoft_file_is_caught(tree: tuple[dict, Path]) -> None:
    manifest, root = tree
    (root / "src/agent_learning/c.py").unlink()
    assert any("c.py was removed" in p for p in find_problems(manifest, root))


def test_known_debt_is_allowed_to_stay_edited(tree: tuple[dict, Path]) -> None:
    manifest, root = tree
    (root / "src/agent_learning/a.py").write_text("value = 99\n")
    manifest["known_edited"] = ["src/agent_learning/a.py"]
    assert find_problems(manifest, root) == []


def test_restoring_a_file_forces_it_off_the_debt_list(tree: tuple[dict, Path]) -> None:
    manifest, root = tree
    manifest["known_edited"] = ["src/agent_learning/a.py"]  # a.py is untouched, so the debt is paid
    problems = find_problems(manifest, root)
    assert len(problems) == 1 and "delete it from known_edited" in problems[0]


def test_a_debt_entry_for_an_unknown_file_is_caught(tree: tuple[dict, Path]) -> None:
    manifest, root = tree
    manifest["known_edited"] = ["src/agent_learning/new_module.py"]
    assert any("not a Microsoft file" in p for p in find_problems(manifest, root))
