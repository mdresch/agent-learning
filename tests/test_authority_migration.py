"""Contract tests for the authority-migration diagnostic snapshot.

Story 4.1 (docs/user-stories/epic-4-authority-migration-diagnostic-snapshot.md)
ADR-004 sections 3, 4.1, 4.2 and 7 (docs/adr/ADR-004-...)
BRD-004, FDD-004 designs 1 to 3 and the error-handling table

Interpretations not stated verbatim in the acceptance criteria (LL-011):
- I1: "the current authority" is what `TaskPolicy(snapshot).authority` reports, which is `low` when
  the snapshot stores no authority yet. Setting `low` on such a policy is therefore a no-op: no
  record and no write (AC_2).
- I2: FDD-004's error table says the first transition initializes "a 1-element list containing
  the initial snapshot". That is read as one `MigrationRecord` (the five fields of design 1), not a
  copy of the whole snapshot, which design 2's code confirms.
- I3: an unchanged authority is idempotent in full: nothing is appended and nothing is stored, so
  `decision_authority_updated_at` does not move either (design 2 puts the whole update inside the
  `if current != target` branch). The command still prints its result and exits 0.
- I4: "ISO 8601 UTC" is tested by parsing `migrated_at` with `datetime.fromisoformat` and requiring a
  zero UTC offset.
- I5: "never overwritten or mutated" (AC_3) is tested by comparing deep copies of earlier records
  with the same records after later transitions.
- I6: AC_4 (amended at Stage 16, 2026-11-05) is tested on the documentation, not on Microsoft's docstring: ADR-004 §3
  states the corrected behaviour, `types.py` still matches the upstream pin, no document we own claims replay except
  as a quoted defect, and the story, BRD-004 and FDD-004 agree.
- I7: AC_5 is tested by what the migration does not do: it stores no second snapshot, adds no key
  other than `migration_records` to the metadata it already updates, and `PolicySnapshot` keeps its
  fields. The CLI builds only `SoftmaxPolicy` snapshots, so a contextual snapshot is out of scope.
"""

from __future__ import annotations

import copy
import dataclasses
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from agent_learning_ext import cli
from agent_learning.policy import SoftmaxPolicy
from agent_learning.storage import InMemoryStore
from agent_learning.types import Action, PolicySnapshot

RECORD_KEYS = {
    "policy_version_at_migration",
    "action_probabilities_at_migration",
    "from_authority",
    "to_authority",
    "migrated_at",
}
SNAPSHOT_FIELDS = {
    "id", "agent_id", "version", "actions", "logits", "baseline", "episodes_seen",
    "updates_applied", "metadata", "created_at", "task_id",
}


@pytest.fixture()
def store(monkeypatch: pytest.MonkeyPatch) -> InMemoryStore:
    in_memory = InMemoryStore()
    monkeypatch.setattr(cli, "get_default_store", lambda: in_memory)
    return in_memory


def _policy(store: InMemoryStore, *, authority: str | None = None) -> PolicySnapshot:
    snapshot = SoftmaxPolicy.from_actions(
        [Action(id="east"), Action(id="west"), Action(id="north")],
        agent_id="agent-1",
        task_id="choose-region",
        initial_logits={"east": 1.2, "west": -0.4, "north": 0.1},
    ).snapshot()
    snapshot.metadata = {"policy_scope": "delegated_decision", "decision_context": "Choose a deployment region"}
    if authority is not None:
        snapshot.metadata["decision_authority"] = authority
    store.store_policy(snapshot)
    return snapshot


def _set(authority: str, capsys: pytest.CaptureFixture[str]) -> dict:
    code = cli.main(
        ["task-policy-authority-set", "--agent-id", "agent-1", "--task-id", "choose-region", "--authority", authority]
    )
    assert code == 0
    return json.loads(capsys.readouterr().out)


def _stored(store: InMemoryStore) -> PolicySnapshot:
    snapshot = store.get_active_policy("agent-1", "choose-region")
    assert snapshot is not None, "no active policy for agent-1 / choose-region"
    return snapshot


def _records(store: InMemoryStore) -> list[dict]:
    return list(_stored(store).metadata.get("migration_records", []))


# --- AC_0 and AC_1: a record is appended with the right content -------------------------------------


def test_ac0_a_change_from_low_to_full_appends_one_record(store: InMemoryStore, capsys) -> None:
    _policy(store)
    _set("full", capsys)
    records = _records(store)
    assert len(records) == 1
    assert records[0]["from_authority"] == "low" and records[0]["to_authority"] == "full"


def test_ac0_a_change_from_full_to_low_appends_a_record(store: InMemoryStore, capsys) -> None:
    _policy(store, authority="full")
    _set("low", capsys)
    [record] = _records(store)
    assert record["from_authority"] == "full" and record["to_authority"] == "low"


def test_ac1_the_record_has_exactly_the_five_fields(store: InMemoryStore, capsys) -> None:
    _policy(store)
    _set("full", capsys)
    [record] = _records(store)
    assert set(record) == RECORD_KEYS


def test_ac1_the_record_captures_the_version_and_the_softmax_distribution_at_migration(
    store: InMemoryStore, capsys
) -> None:
    snapshot = _policy(store)
    expected = SoftmaxPolicy.from_snapshot(snapshot).probabilities()
    version = snapshot.version
    _set("full", capsys)
    [record] = _records(store)
    assert record["policy_version_at_migration"] == version
    probabilities = record["action_probabilities_at_migration"]
    assert set(probabilities) == {"east", "west", "north"}
    assert [probabilities[a.id] for a in snapshot.actions] == pytest.approx(expected)
    assert sum(probabilities.values()) == pytest.approx(1.0)
    assert probabilities["east"] > probabilities["north"] > probabilities["west"]  # not uniform


def test_ac1_migrated_at_is_an_iso_8601_utc_timestamp(store: InMemoryStore, capsys) -> None:
    _policy(store)
    _set("full", capsys)
    [record] = _records(store)
    stamp = datetime.fromisoformat(record["migrated_at"])
    assert stamp.utcoffset() == timedelta(0)


def test_ac1_the_command_still_reports_the_new_authority(store: InMemoryStore, capsys) -> None:
    _policy(store)
    result = _set("full", capsys)
    assert result["decision_authority"] == "full"
    assert result["current_policy"]["metadata"]["decision_authority_source"] == "configured"


# --- AC_2: idempotent -----------------------------------------------------------------------------


def test_ac2_setting_the_current_authority_appends_no_record_and_writes_nothing(store: InMemoryStore, capsys) -> None:
    _policy(store, authority="full")
    before = copy.deepcopy(_stored(store).metadata)
    result = _set("full", capsys)
    assert result["decision_authority"] == "full"
    assert _records(store) == []
    assert _stored(store).metadata == before  # includes decision_authority_updated_at (interpretation I3)


def test_ac2_a_policy_with_no_stored_authority_reads_as_low_so_setting_low_is_a_no_op(
    store: InMemoryStore, capsys
) -> None:
    _policy(store)
    result = _set("low", capsys)
    assert result["decision_authority"] == "low"
    assert _records(store) == []


def test_ac2_repeating_a_change_appends_only_once(store: InMemoryStore, capsys) -> None:
    _policy(store)
    _set("full", capsys)
    _set("full", capsys)
    assert len(_records(store)) == 1


# --- AC_3: oscillation ------------------------------------------------------------------------------


def test_ac3_oscillation_appends_records_in_order_and_never_changes_earlier_ones(store: InMemoryStore, capsys) -> None:
    _policy(store)
    history: list[list[dict]] = []
    for authority in ("full", "low", "full"):
        _set(authority, capsys)
        history.append(copy.deepcopy(_records(store)))
    final = _records(store)
    assert [(r["from_authority"], r["to_authority"]) for r in final] == [("low", "full"), ("full", "low"), ("low", "full")]
    stamps = [datetime.fromisoformat(r["migrated_at"]) for r in final]
    assert stamps == sorted(stamps)  # non-decreasing: a coarse clock may repeat a value; order is proven by the pairs above
    for step, earlier in enumerate(history):
        assert final[: len(earlier)] == earlier, f"records changed after step {step + 1}"


def test_ac3_each_record_keeps_the_distribution_of_its_own_moment(store: InMemoryStore, capsys) -> None:
    snapshot = _policy(store)
    _set("full", capsys)
    first = copy.deepcopy(_records(store)[0])
    stored = _stored(store)
    stored.logits = {"east": -2.0, "west": 3.0, "north": 0.0}  # the policy moves on
    store.store_policy(stored)
    _set("low", capsys)
    records = _records(store)
    assert records[0] == first
    assert records[1]["action_probabilities_at_migration"]["west"] > records[0]["action_probabilities_at_migration"]["west"]
    assert snapshot.id == stored.id


# --- backward compatibility (FDD-004 error table) ---------------------------------------------------


def test_a_snapshot_without_migration_records_reads_as_an_empty_list(store: InMemoryStore) -> None:
    snapshot = _policy(store)
    assert snapshot.metadata.get("migration_records", []) == []
    assert _records(store) == []


# --- AC_4 (amended at Stage 16, 2026-11-05): the replay claim is corrected in documentation -------------------

ROOT = Path(__file__).resolve().parents[1]
ADR_004 = ROOT / "docs" / "adr" / "ADR-004-authority-migration-comparison-not-replay.md"
QUOTING_THE_DEFECT = ("ADR-004", "BRD-004", "FDD-004")


def _text(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def _the_one(pattern: str) -> Path:
    hits = list(ROOT.glob(pattern))
    assert len(hits) == 1, (pattern, hits)
    return hits[0]


def _owned_documents() -> list[Path]:
    return [*ROOT.glob("docs/**/*.md"), ROOT / "README.md", ROOT / "PYPI.md"]


def test_ac4a_adr_004_states_the_corrected_behaviour() -> None:
    text = _text(ADR_004)
    for required in ("materially incorrect", "non-contextual", "reward shaping", "not decision evidence"):
        assert required in text, f"ADR-004 no longer says {required!r}"


def test_ac4b_types_py_is_microsofts_unedited_version() -> None:
    manifest = json.loads((ROOT / "tests" / "upstream_manifest.json").read_text(encoding="utf-8"))
    path = "src/agent_learning/types.py"
    digest = hashlib.sha256((ROOT / path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    assert digest == manifest["files"][path], "types.py differs from the pinned upstream version"
    assert path not in manifest["known_edited"]


def test_ac4c_no_owned_document_claims_replay_except_as_a_quoted_defect() -> None:
    hits = [p for p in _owned_documents() if "can replay the decision" in _text(p).lower()]
    stray = [p.name for p in hits if not p.name.startswith(QUOTING_THE_DEFECT)]
    assert not stray, f"documents that claim replay: {stray}"
    still_quoting = {prefix for prefix in QUOTING_THE_DEFECT if any(p.name.startswith(prefix) for p in hits)}
    assert still_quoting == set(QUOTING_THE_DEFECT), "ADR-004, BRD-004 and FDD-004 must each still name the defect"


def test_ac4d_story_brd_and_fdd_agree_and_none_still_demands_the_docstring_edit() -> None:
    story = _text(_the_one("docs/user-stories/epic-4-*.md"))
    brd = _text(_the_one("docs/project-docs/Business-Requirements/BRD-004-*.md"))
    fdd = _text(_the_one("docs/project-docs/Functional-Design/FDD-004-*.md"))
    parts = {
        "Story 4.1 AC_4": story[story.index("$AC_4$"):story.index("$AC_5$")],
        "BRD-004 BRU-004-05": brd[brd.index("**BRU-004-05**"):brd.index("**BRU-004-05**") + 900],
        "FDD-004 Design 3": fdd[fdd.index("## Design 3"):fdd.index("## Error Handling")],
    }
    for name, text in parts.items():
        assert "amended at Stage 16" in text, name
        assert "ADR-004" in text and "types.py" in text and "fork rule" in text, name
    demands = ("docstring in `src/agent_learning/types.py` is updated", "`types.py` must be updated")
    stray = [(p.name, d) for p in _owned_documents() for d in demands if d in _text(p)]
    assert not stray, stray


# --- AC_5: no new record type ---------------------------------------------------------------------------


def test_ac5_migration_stores_no_second_snapshot_and_adds_only_the_records_key(store: InMemoryStore, capsys) -> None:
    snapshot = _policy(store)
    keys_before = set(snapshot.metadata)
    _set("full", capsys)
    assert len(store.list_policies("agent-1", "choose-region")) == 1
    added = set(_stored(store).metadata) - keys_before
    assert added == {"migration_records", "decision_authority", "decision_authority_source", "decision_authority_updated_at"}


def test_ac5_policy_snapshot_keeps_its_fields() -> None:
    assert {f.name for f in dataclasses.fields(PolicySnapshot)} == SNAPSHOT_FIELDS
