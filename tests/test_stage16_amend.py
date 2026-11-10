"""The Stage 16 amendment script: its measurements and frames are deterministic, and it refuses what it must refuse.

The pipeline calls (``agent-learn``) are covered by the real run recorded in docs/policy-shapes/; these tests cover what the
script decides itself.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("stage16_amend", ROOT / "scripts" / "stage16_amend.py")
assert SPEC is not None and SPEC.loader is not None
s16 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(s16)

BASE = "# BRD\n\n- **BRU-001-01**: The system must update `types.py` so the docstring is right.\n- **BRU-001-02**: Keep ADR-004 in step.\n"


def test_a_one_word_tweak_is_not_a_change_to_a_requirement() -> None:
    cand = BASE.replace("is right", "is correct")
    f = s16.measure("docs/x.md", BASE, cand)
    assert f["normative_touched"] is False and f["change_ratio"] < s16.CHANGED_RATIO


def test_rewriting_a_requirement_is_normative_and_can_invert_it() -> None:
    cand = BASE.replace(
        "The system must update `types.py` so the docstring is right.",
        "The system must not edit `types.py`; the correction lives in ADR-004 instead.",
    )
    f = s16.measure("docs/x.md", BASE, cand)
    assert f["normative_touched"] is True and f["requirement_inverted"] is True
    assert f["terms_removed"] >= 1 and f["terms_kept"] >= 1


def test_deleting_the_terms_a_requirement_carried_is_not_goal_preserving() -> None:
    cand = BASE.replace("update `types.py` so the docstring is right", "do something else entirely")
    f = s16.measure("docs/x.md", BASE, cand)
    assert f["goal_preserved"] is False
    assert s16.observed(f)[1] == 0.90  # intent shift


def test_a_status_line_edit_is_seen() -> None:
    f = s16.measure("docs/x.md", "**Status:** Approved\nBody\n", "**Status:** Approved, amended\nBody\n")
    assert f["status_line_changed"] is True


def test_measuring_is_deterministic() -> None:
    cand = BASE.replace("must update", "must not edit")
    assert s16.measure("docs/x.md", BASE, cand) == s16.measure("docs/x.md", BASE, cand)


def test_the_frame_covers_every_action_and_criterion_and_its_weights_sum_to_one() -> None:
    f = s16.measure("docs/x.md", BASE, BASE.replace("must update", "must not edit"))
    frame = s16.build_frame("docs/x.md", f)
    assert [o["action_id"] for o in frame["options"]] == s16.ACTIONS
    assert all(len(o["evidence"]) == len(s16.CRITERIA) for o in frame["options"])
    assert abs(sum(c["weight"] for c in frame["criteria"]) - 1.0) < 1e-9
    assert all(0 < e["support"] <= 1 for o in frame["options"] for e in o["evidence"])


def test_a_cosmetic_edit_supports_a_correction_note_over_an_amendment() -> None:
    f = s16.measure("docs/x.md", BASE, BASE.replace("is right", "is correct"))
    frame = s16.build_frame("docs/x.md", f)

    def score(action: str) -> float:
        option = next(o for o in frame["options"] if o["action_id"] == action)
        weights = {c["id"]: c["weight"] for c in frame["criteria"]}
        return sum(weights[e["criterion_id"]] * e["support"] for e in option["evidence"])

    assert score("correction_note") > score("amendment_log_entry")


def test_the_lifecycle_actions_need_a_status_change() -> None:
    f = s16.measure("docs/x.md", BASE, BASE.replace("is right", "is correct"))
    frame = s16.build_frame("docs/x.md", f)
    option = next(o for o in frame["options"] if o["action_id"] == "supersession_update")
    assert all(e["support"] == 0.02 for e in option["evidence"])


@pytest.mark.parametrize(
    ("family", "text", "expected"),
    [
        (
            "brd",
            "# BRD\n\n**Status:** Approved (2026-10-23)\n\nBody\n",
            "**Status:** Approved (2026-10-23) RECORD\n",
        ),
        (
            "adr",
            "# ADR\n\n## 2. Status\n\n**Accepted (2026-10-23)**\n\n## 3. Context\n",
            "**Accepted (2026-10-23)** RECORD\n",
        ),
    ],
)
def test_the_record_is_appended_to_the_status_line(family: str, text: str, expected: str) -> None:
    out = s16.status_edit(family, text, "RECORD")
    assert expected in out


def test_a_document_with_no_status_line_is_refused() -> None:
    with pytest.raises(s16.Stop):
        s16.status_edit("docs/project-docs/Functional-Design/FDD-004-x.md", "# FDD\nBody\n", "RECORD")


def test_only_an_approved_governed_document_can_be_amended() -> None:
    with pytest.raises(s16.Stop, match="not in the governance baseline"):
        s16.resolve("README.md")


def test_a_recorded_amendment_satisfies_the_guards_own_pattern() -> None:
    record = "Amended 2026-11-05 at Stage 16: AC_4 reworded, classified `amendment_log_entry` (robust utility 0.9, episode `abcd1234...`) and accepted by Menno."
    found = s16.gb.amendments(f"**Status:** Approved {record}")
    assert [a["episode"] for a in found] == ["abcd1234"]


def test_the_slug_names_the_document_not_its_title() -> None:
    assert s16.slug("docs/adr/ADR-007-governance.md") == "adr-007"
    assert s16.slug("docs/user-stories/epic-4-authority-migration.md") == "epic-4"
    assert s16.slug("docs/project-docs/Functional-Design/FDD-004-x.md") == "fdd-004"


def test_a_store_inside_the_repository_is_accepted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENT_LEARNING_LOCAL_STORE_DIR", str(ROOT / "data" / "agent-learning" / "store"))
    monkeypatch.setattr(s16, "_store_announced", True)
    assert s16.guard_store() == (ROOT / "data" / "agent-learning" / "store").resolve()


def test_a_store_outside_the_repository_is_refused_unless_allowed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("AGENT_LEARNING_LOCAL_STORE_DIR", str(tmp_path))
    monkeypatch.setattr(s16, "_store_announced", True)
    monkeypatch.setattr(s16, "ALLOW_EXTERNAL_STORE", False)
    with pytest.raises(s16.Stop, match="outside this repository"):
        s16.guard_store()
    monkeypatch.setattr(s16, "ALLOW_EXTERNAL_STORE", True)
    assert s16.guard_store() == tmp_path.resolve()
