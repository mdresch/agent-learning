"""Contract tests for Story 20.3: The Command for a Policy Donor.

Governing specifications:
- User Story: docs/user-stories/epic-20-explicit-policy-prior-warm-starting.md (Story 20.3)
- Architecture: docs/adr/ADR-020-explicit-policy-prior-warm-starting.md (§4.1, §4.2, §4.3)
- Business Requirements: docs/project-docs/Business-Requirements/BRD-020-explicit-policy-prior-warm-starting.md (BRU-020-01, BRU-020-02, BRU-020-03, BRU-020-04, BRU-020-05, BRU-020-07, BRU-020-08, BRU-020-10)
- Functional Design: docs/project-docs/Functional-Design/FDD-020-explicit-policy-prior-warm-starting.md (§1.2, §1.4, §1.5, §2.1, §2.2, §3.3)

Acceptance Criteria:
- AC_0 (New Version): task-policy-warm-start on the base donor and target stores one new snapshot
  of target-task with the next version, logits {accept: 1.4, decline: -0.7, ask: 0.0}, episodes_seen 0,
  the provenance of Story 20.2 in its metadata, and it is the active policy of target-task;
  the earlier version is stored and unchanged.
- AC_1 (Donor Untouched): the donor snapshot and its episodes are equal to their copies after
  the command, and store_policy was never called for the donor.
- AC_2 (Map Rules): without --action-map and with different action ids the command exits non-zero
  naming both sets; with identical action ids and no map it uses the identity map; a bad map exits non-zero.
- AC_3 (Cold Target Only): a target with updates_applied above 0, with episodes_seen above 0,
  with any logit not zero, or with an earlier warm_start_donor_policy_id exits non-zero naming the reason;
  a target that is not a decision policy or is full authority does the same.
- AC_4 (Donor Checks): a donor that is the target, is full authority, or has no logits exits non-zero.
- AC_5 (Nothing Written On Refusal): after every refusal above and every ValueError of Story 20.1
  the store is equal to its earlier state.
- AC_6 (Flags): --donor-task-id and --meta-prior together, or neither, exit non-zero; the damping defaults to 0.70.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
import pytest

from agent_learning import cli
from agent_learning.storage.local import LocalFileStore
from agent_learning.types import Action, Episode, PolicySnapshot


@pytest.fixture
def base_donor_snapshot() -> PolicySnapshot:
    """The base donor policy snapshot specified in Epic 20."""
    return PolicySnapshot(
        id="donor-snap-0001",
        agent_id="test-agent",
        task_id="donor-task",
        version=1,
        actions=[Action(id="approve"), Action(id="reject"), Action(id="escalate")],
        logits={"approve": 2.0, "reject": -1.0, "escalate": 0.0},
        baseline=0.0,
        episodes_seen=10,
        updates_applied=2,
        metadata={"policy_scope": "delegated_decision", "decision_authority": "low"},
    )


@pytest.fixture
def base_target_snapshot() -> PolicySnapshot:
    """The cold target policy snapshot specified in Epic 20."""
    return PolicySnapshot(
        id="target-snap-0000",
        agent_id="test-agent",
        task_id="target-task",
        version=0,
        actions=[Action(id="accept"), Action(id="decline"), Action(id="ask")],
        logits={"accept": 0.0, "decline": 0.0, "ask": 0.0},
        baseline=0.0,
        episodes_seen=0,
        updates_applied=0,
        metadata={"policy_scope": "delegated_decision", "decision_authority": "low"},
    )


@pytest.fixture
def file_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> LocalFileStore:
    """Isolated file store wired into cli.get_default_store."""
    store = LocalFileStore(tmp_path / "store")
    monkeypatch.setattr(cli, "get_default_store", lambda: store)
    return store


def test_ac0_new_version(
    file_store: LocalFileStore,
    base_donor_snapshot: PolicySnapshot,
    base_target_snapshot: PolicySnapshot,
) -> None:
    """AC_0: task-policy-warm-start stores new version with damped logits and provenance; earlier unchanged."""
    file_store.store_policy(base_donor_snapshot)
    file_store.store_policy(base_target_snapshot)

    action_map = json.dumps({"accept": "approve", "decline": "reject", "ask": "escalate"})
    exit_code = cli.main(
        [
            "task-policy-warm-start",
            "--agent-id",
            "test-agent",
            "--target-task-id",
            "target-task",
            "--donor-task-id",
            "donor-task",
            "--action-map",
            action_map,
        ]
    )
    assert exit_code == 0

    active_target = file_store.get_active_policy("test-agent", "target-task")
    assert active_target is not None
    assert active_target.id != base_target_snapshot.id
    assert active_target.version == 1
    assert active_target.episodes_seen == 0
    assert active_target.logits == {"accept": 1.4, "decline": -0.7, "ask": 0.0}

    # Provenance metadata present
    meta = active_target.metadata
    assert meta["warm_start_donor_policy_id"] == base_donor_snapshot.id
    assert meta["warm_start_donor_task_id"] == "donor-task"
    assert meta["warm_start_donor_version"] == 1
    assert meta["warm_start_damping_factor"] == 0.70
    assert meta["warm_start_action_map"] == {"accept": "approve", "decline": "reject", "ask": "escalate"}
    assert meta["warm_start_donor_kind"] == "policy"
    assert "warm_started_at" in meta
    assert "warm_start_donor_gate_met" in meta

    # Earlier version is stored and unchanged
    v0_target = file_store.get_policy(base_target_snapshot.id, "test-agent")
    assert v0_target is not None
    assert v0_target.version == 0
    assert v0_target.logits == {"accept": 0.0, "decline": 0.0, "ask": 0.0}
    assert "warm_start_donor_policy_id" not in v0_target.metadata


def test_ac1_donor_untouched(
    file_store: LocalFileStore,
    base_donor_snapshot: PolicySnapshot,
    base_target_snapshot: PolicySnapshot,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC_1: Donor snapshot and its episodes are untouched, and store_policy is never called for donor."""
    file_store.store_policy(base_donor_snapshot)
    file_store.store_policy(base_target_snapshot)

    donor_episode = Episode(
        id="ep-donor-001",
        agent_id="test-agent",
        task_id="donor-task",
        session_id="session-1",
        created_at="2026-10-25T10:00:00+00:00",
    )
    file_store.store_episode(donor_episode)

    donor_copy = copy.deepcopy(base_donor_snapshot.to_dict())
    episode_copy = copy.deepcopy(donor_episode.to_dict())

    orig_store_policy = file_store.store_policy

    def guarded_store_policy(policy: PolicySnapshot) -> str:
        assert policy.task_id != "donor-task", "store_policy must never be called for donor!"
        return orig_store_policy(policy)

    monkeypatch.setattr(file_store, "store_policy", guarded_store_policy)

    action_map = json.dumps({"accept": "approve", "decline": "reject", "ask": "escalate"})
    exit_code = cli.main(
        [
            "task-policy-warm-start",
            "--agent-id",
            "test-agent",
            "--target-task-id",
            "target-task",
            "--donor-task-id",
            "donor-task",
            "--action-map",
            action_map,
        ]
    )
    assert exit_code == 0

    donor_after = file_store.get_policy(base_donor_snapshot.id, "test-agent")
    assert donor_after is not None
    assert donor_after.to_dict() == donor_copy

    ep_after = file_store.get_episode("ep-donor-001", "test-agent")
    assert ep_after is not None
    assert ep_after.to_dict() == episode_copy


def test_ac2_map_rules(
    file_store: LocalFileStore,
    base_donor_snapshot: PolicySnapshot,
    base_target_snapshot: PolicySnapshot,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC_2: Missing map with different IDs exits non-zero naming both sets; identical IDs uses identity map; bad map exits non-zero."""
    file_store.store_policy(base_donor_snapshot)
    file_store.store_policy(base_target_snapshot)

    # 1. Missing map with different action ids
    exit_code = cli.main(
        [
            "task-policy-warm-start",
            "--agent-id",
            "test-agent",
            "--target-task-id",
            "target-task",
            "--donor-task-id",
            "donor-task",
        ]
    )
    assert exit_code != 0
    captured = capsys.readouterr()
    err_text = captured.err + captured.out
    assert "approve" in err_text and "accept" in err_text

    # 2. Identical action IDs and no map -> uses identity map
    same_action_target = PolicySnapshot(
        id="target-same-actions",
        agent_id="test-agent",
        task_id="same-task",
        version=0,
        actions=[Action(id="approve"), Action(id="reject"), Action(id="escalate")],
        logits={"approve": 0.0, "reject": 0.0, "escalate": 0.0},
        metadata={"policy_scope": "delegated_decision", "decision_authority": "low"},
    )
    file_store.store_policy(same_action_target)

    exit_code_identity = cli.main(
        [
            "task-policy-warm-start",
            "--agent-id",
            "test-agent",
            "--target-task-id",
            "same-task",
            "--donor-task-id",
            "donor-task",
        ]
    )
    assert exit_code_identity == 0
    active_same = file_store.get_active_policy("test-agent", "same-task")
    assert active_same is not None
    assert active_same.logits == {"approve": 1.4, "reject": -0.7, "escalate": 0.0}
    assert active_same.metadata["warm_start_action_map"] == {
        "approve": "approve",
        "reject": "reject",
        "escalate": "escalate",
    }

    # 3. Bad maps exit non-zero
    bad_maps = [
        "not-json",
        json.dumps(["accept", "approve"]),  # array instead of dict
        json.dumps(123),  # scalar instead of dict
        json.dumps({"accept": "approve"}),  # incomplete
        json.dumps({"accept": "approve", "decline": "approve", "ask": "escalate"}),  # non-injective
        json.dumps({"accept": "approve", "decline": "reject", "ask": "missing_act"}),  # missing donor act
    ]
    for bad_map in bad_maps:
        code = cli.main(
            [
                "task-policy-warm-start",
                "--agent-id",
                "test-agent",
                "--target-task-id",
                "target-task",
                "--donor-task-id",
                "donor-task",
                "--action-map",
                bad_map,
            ]
        )
        assert code != 0

    # 4. Map from a relative file path that begins with a brace (Q-83-9): it is a file, not inline JSON
    monkeypatch.chdir(tmp_path)
    map_file = tmp_path / "{custom}_map.json"
    map_file.write_text(
        json.dumps({"accept": "approve", "decline": "reject", "ask": "escalate"}),
        encoding="utf-8",
    )
    target_file_snap = copy.deepcopy(base_target_snapshot)
    target_file_snap.task_id = "target-task-file"
    file_store.store_policy(target_file_snap)
    code_file = cli.main(
        [
            "task-policy-warm-start",
            "--agent-id",
            "test-agent",
            "--target-task-id",
            "target-task-file",
            "--donor-task-id",
            "donor-task",
            "--action-map",
            map_file.name,
        ]
    )
    assert code_file == 0
    active_file = file_store.get_active_policy("test-agent", "target-task-file")
    assert active_file is not None
    assert active_file.logits == {"accept": 1.4, "decline": -0.7, "ask": 0.0}


def test_ac3_cold_target_only(
    file_store: LocalFileStore,
    base_donor_snapshot: PolicySnapshot,
    base_target_snapshot: PolicySnapshot,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """AC_3: Non-cold target (updates, episodes, non-zero logits, prior warm-start, non-decision, full authority) exits non-zero naming reason."""
    file_store.store_policy(base_donor_snapshot)
    action_map = json.dumps({"accept": "approve", "decline": "reject", "ask": "escalate"})

    def make_target(**kwargs: object) -> PolicySnapshot:
        snap = copy.deepcopy(base_target_snapshot)
        for k, v in kwargs.items():
            if k == "metadata":
                snap.metadata.update(v)  # type: ignore[arg-type]
            else:
                setattr(snap, k, v)
        snap.id = f"target-{abs(hash(str(kwargs)))}"
        return snap

    test_cases = [
        (make_target(updates_applied=1), "updates_applied"),
        (make_target(episodes_seen=5), "episodes_seen"),
        (make_target(logits={"accept": 0.5, "decline": 0.0, "ask": 0.0}), "logits"),
        (make_target(metadata={"warm_start_donor_policy_id": "prev-donor-1"}), "warm_start_donor_policy_id"),
        (make_target(metadata={"policy_scope": "other"}), "decision"),
        (make_target(metadata={"decision_authority": "full"}), "authority"),
    ]

    for idx, (target_snap, reason_keyword) in enumerate(test_cases):
        sub_task_id = f"target-task-{idx}"
        target_snap.task_id = sub_task_id
        file_store.store_policy(target_snap)
        code = cli.main(
            [
                "task-policy-warm-start",
                "--agent-id",
                "test-agent",
                "--target-task-id",
                sub_task_id,
                "--donor-task-id",
                "donor-task",
                "--action-map",
                action_map,
            ]
        )
        assert code != 0, f"Expected non-zero exit for non-cold target: {reason_keyword}"
        captured = capsys.readouterr()
        err_msg = (captured.err + captured.out).lower()
        assert reason_keyword.lower() in err_msg, f"Expected error to mention {reason_keyword!r}, got: {err_msg}"


def test_ac4_donor_checks(
    file_store: LocalFileStore,
    base_donor_snapshot: PolicySnapshot,
    base_target_snapshot: PolicySnapshot,
) -> None:
    """AC_4: Donor that is target, is full authority, or has no logits exits non-zero."""
    file_store.store_policy(base_target_snapshot)
    action_map = json.dumps({"accept": "approve", "decline": "reject", "ask": "escalate"})

    # 1. Donor is target
    code_self = cli.main(
        [
            "task-policy-warm-start",
            "--agent-id",
            "test-agent",
            "--target-task-id",
            "target-task",
            "--donor-task-id",
            "target-task",
            "--action-map",
            action_map,
        ]
    )
    assert code_self != 0

    # 2. Donor is full authority
    full_auth_donor = PolicySnapshot.from_dict(base_donor_snapshot.to_dict())
    full_auth_donor.metadata["decision_authority"] = "full"
    file_store.store_policy(full_auth_donor)

    code_full = cli.main(
        [
            "task-policy-warm-start",
            "--agent-id",
            "test-agent",
            "--target-task-id",
            "target-task",
            "--donor-task-id",
            "donor-task",
            "--action-map",
            action_map,
        ]
    )
    assert code_full != 0

    # 3. Donor has no logits
    no_logits_donor = PolicySnapshot.from_dict(base_donor_snapshot.to_dict())
    no_logits_donor.logits = {}
    file_store.store_policy(no_logits_donor)

    code_no_logits = cli.main(
        [
            "task-policy-warm-start",
            "--agent-id",
            "test-agent",
            "--target-task-id",
            "target-task",
            "--donor-task-id",
            "donor-task",
            "--action-map",
            action_map,
        ]
    )
    assert code_no_logits != 0


def test_ac5_nothing_written_on_refusal(
    file_store: LocalFileStore,
    base_donor_snapshot: PolicySnapshot,
    base_target_snapshot: PolicySnapshot,
) -> None:
    """AC_5: After every refusal above and every ValueError of Story 20.1, store is equal to earlier state."""
    file_store.store_policy(base_donor_snapshot)
    file_store.store_policy(base_target_snapshot)

    def get_store_state() -> dict[str, list[dict[str, object]]]:
        return {
            "policies": [p.to_dict() for p in file_store.list_policies("test-agent", "target-task")],
            "donor_policies": [p.to_dict() for p in file_store.list_policies("test-agent", "donor-task")],
        }

    initial_state = get_store_state()
    action_map = json.dumps({"accept": "approve", "decline": "reject", "ask": "escalate"})

    def run_refusal(argv: list[str]) -> None:
        try:
            code = cli.main(argv)
            assert code != 0
        except SystemExit as exc:
            assert exc.code != 0
        assert get_store_state() == initial_state

    # 1. Invalid damping values (argparse validator / Story 20.1 ValueError)
    for bad_damping in ["0.0", "-0.5", "1.5", "not-a-number"]:
        run_refusal(
            [
                "task-policy-warm-start",
                "--agent-id",
                "test-agent",
                "--target-task-id",
                "target-task",
                "--donor-task-id",
                "donor-task",
                "--damping",
                bad_damping,
                "--action-map",
                action_map,
            ]
        )

    # 2. Bad action maps
    bad_maps = [
        "not-json",
        json.dumps(["accept", "approve"]),
        json.dumps(123),
        json.dumps({"accept": "approve"}),
        json.dumps({"accept": "approve", "decline": "approve", "ask": "escalate"}),
        json.dumps({"accept": "approve", "decline": "reject", "ask": "missing"}),
    ]
    for bm in bad_maps:
        run_refusal(
            [
                "task-policy-warm-start",
                "--agent-id",
                "test-agent",
                "--target-task-id",
                "target-task",
                "--donor-task-id",
                "donor-task",
                "--action-map",
                bm,
            ]
        )

    # 3. Missing action map when action IDs differ
    run_refusal(
        [
            "task-policy-warm-start",
            "--agent-id",
            "test-agent",
            "--target-task-id",
            "target-task",
            "--donor-task-id",
            "donor-task",
        ]
    )

    # 4. Target non-existent
    run_refusal(
        [
            "task-policy-warm-start",
            "--agent-id",
            "test-agent",
            "--target-task-id",
            "nonexistent-target-task",
            "--donor-task-id",
            "donor-task",
            "--action-map",
            action_map,
        ]
    )

    # 5. Donor refusal scenarios (AC_4)
    donor_refusals = [
        "target-task",  # donor is target
        "nonexistent-donor",  # donor not found
    ]
    for d_task in donor_refusals:
        run_refusal(
            [
                "task-policy-warm-start",
                "--agent-id",
                "test-agent",
                "--target-task-id",
                "target-task",
                "--donor-task-id",
                d_task,
                "--action-map",
                action_map,
            ]
        )

    # 6. Flag combinations (AC_6)
    run_refusal(
        [
            "task-policy-warm-start",
            "--agent-id",
            "test-agent",
            "--target-task-id",
            "target-task",
        ]
    )
    run_refusal(
        [
            "task-policy-warm-start",
            "--agent-id",
            "test-agent",
            "--target-task-id",
            "target-task",
            "--donor-task-id",
            "donor-task",
            "--meta-prior",
            "family-meta-prior",
        ]
    )
    run_refusal(
        [
            "task-policy-warm-start",
            "--agent-id",
            "test-agent",
            "--target-task-id",
            "target-task",
            "--meta-prior",
            "family-meta-prior",
        ]
    )


def test_ac5_nothing_written_on_non_cold_target_refusal(
    file_store: LocalFileStore,
    base_donor_snapshot: PolicySnapshot,
    base_target_snapshot: PolicySnapshot,
) -> None:
    """AC_5: After every AC_3 non-cold target refusal, the target and donor stores equal their earlier state."""
    file_store.store_policy(base_donor_snapshot)
    action_map = json.dumps({"accept": "approve", "decline": "reject", "ask": "escalate"})

    cases = {
        "updates": {"updates_applied": 1},
        "episodes": {"episodes_seen": 5},
        "logits": {"logits": {"accept": 0.5, "decline": 0.0, "ask": 0.0}},
        "prior-warm-start": {"metadata": {"warm_start_donor_policy_id": "prev-donor-1"}},
        "not-decision": {"metadata": {"policy_scope": "other"}},
        "full-authority": {"metadata": {"decision_authority": "full"}},
    }

    def store_state(task_id: str) -> list[list[dict[str, object]]]:
        return [
            [p.to_dict() for p in file_store.list_policies("test-agent", task_id)],
            [p.to_dict() for p in file_store.list_policies("test-agent", "donor-task")],
        ]

    for name, overrides in cases.items():
        snap = copy.deepcopy(base_target_snapshot)
        snap.task_id = f"non-cold-{name}"
        for key, value in overrides.items():
            if key == "metadata":
                snap.metadata.update(value)  # type: ignore[arg-type]
            else:
                setattr(snap, key, value)
        file_store.store_policy(snap)

        before = store_state(snap.task_id)
        code = cli.main(
            [
                "task-policy-warm-start",
                "--agent-id",
                "test-agent",
                "--target-task-id",
                snap.task_id,
                "--donor-task-id",
                "donor-task",
                "--action-map",
                action_map,
            ]
        )
        assert code != 0, f"Expected refusal for {name}"
        assert store_state(snap.task_id) == before, f"Store changed after refusal for {name}"


def test_ac6_flags(
    file_store: LocalFileStore,
    base_donor_snapshot: PolicySnapshot,
    base_target_snapshot: PolicySnapshot,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """AC_6: --donor-task-id and --meta-prior together, or neither, exit non-zero; damping defaults to 0.70."""
    file_store.store_policy(base_donor_snapshot)
    file_store.store_policy(base_target_snapshot)

    # 1. Neither flag provided
    code_neither = cli.main(
        [
            "task-policy-warm-start",
            "--agent-id",
            "test-agent",
            "--target-task-id",
            "target-task",
        ]
    )
    assert code_neither != 0

    # 2. Both flags provided
    code_both = cli.main(
        [
            "task-policy-warm-start",
            "--agent-id",
            "test-agent",
            "--target-task-id",
            "target-task",
            "--donor-task-id",
            "donor-task",
            "--meta-prior",
            "family-meta-prior",
        ]
    )
    assert code_both != 0

    # 3. Meta-prior flag alone: Story 20.3 refused it as not yet implemented; since Story 20.5 (2026-11-04) it is
    #    implemented, and a prior that does not exist is refused by name.
    capsys.readouterr()  # clear prior captured output
    code_meta_only = cli.main(
        [
            "task-policy-warm-start",
            "--agent-id",
            "test-agent",
            "--target-task-id",
            "target-task",
            "--meta-prior",
            "family-meta-prior",
        ]
    )
    assert code_meta_only != 0
    captured_meta = capsys.readouterr()
    assert "'family-meta-prior' not found" in (captured_meta.err + captured_meta.out)

    # 4. Damping defaults to 0.70
    file_store.store_policy(base_target_snapshot)
    action_map = json.dumps({"accept": "approve", "decline": "reject", "ask": "escalate"})
    code_default = cli.main(
        [
            "task-policy-warm-start",
            "--agent-id",
            "test-agent",
            "--target-task-id",
            "target-task",
            "--donor-task-id",
            "donor-task",
            "--action-map",
            action_map,
        ]
    )
    assert code_default == 0
    active = file_store.get_active_policy("test-agent", "target-task")
    assert active is not None
    assert active.metadata["warm_start_damping_factor"] == 0.70
    assert active.logits["accept"] == 1.4
