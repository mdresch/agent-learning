"""Contract tests for Story 20.5: Seeding From a Family Meta-Prior.

Governing specifications:
- User Story: docs/user-stories/epic-20-explicit-policy-prior-warm-starting.md (Story 20.5)
- Architecture: docs/adr/ADR-020-explicit-policy-prior-warm-starting.md; docs/adr/ADR-019 (section 4.2)
- Business Requirements: docs/project-docs/Business-Requirements/BRD-020-explicit-policy-prior-warm-starting.md
- Functional Design: docs/project-docs/Functional-Design/FDD-020-explicit-policy-prior-warm-starting.md
  (section 2.1 item 3, J5, section 5); FDD-019 section 3 item 4 (seed_values), section 2.3

Acceptance Criteria:
- AC_0 (Same Values): --meta-prior N on a target that declares the prior's family and a role_map stores logits
  equal to seed_values of FDD-019 times the damping, and the provenance has kind meta_prior, the prior's snapshot
  id, task id and version, and the target's role_map as the action map.
- AC_1 (Default Damping): the damping defaults to 1.0 for a meta-prior, so the logits equal seed_values exactly;
  --damping 0.5 halves them.
- AC_2 (Matching Declaration): a target without family, with another family, or without a role_map exits
  non-zero and writes nothing.
- AC_3 (Which Prior): the latest non-superseded prior of the name is used; a superseded one, a missing one, and
  a prior in Beta counts each exit non-zero.
- AC_4 (Exclusive Flags): --action-map with --meta-prior exits non-zero.
- AC_5 (Prior Untouched): the prior snapshot is equal to its copy after the command.

Interpretation I1 (superseded): the prior used is the highest-version stored snapshot of the name that is a
meta-prior. If another stored snapshot of the name names it in ``supersedes`` (it was replaced out of order),
the command refuses instead of choosing between them. A lower version that a newer one supersedes is simply
not used (AC_3, first half).
Interpretation I2 (gate): warm_start_donor_gate_met is null for a meta-prior (FDD-020 section 2.1).
Interpretation I3: the prior in the main tests is compiled through ``task-policy-meta-compile`` from four
synthetic members, so the command reads what Story 19.5 really stores; the Beta prior is built by hand.
Everything here is synthetic.
"""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path

import pytest

from agent_learning import cli
from agent_learning.meta_prior import MetaPrior, seed_values
from agent_learning.storage.local import LocalFileStore
from agent_learning.types import Action, Episode, PolicySnapshot, Reward, RewardSource

AGENT = "test-agent"
FAMILY = "approve-gates"
NAME = "approve-gates-prior"
ROLES = ("approve", "reject", "revise")
ROLE_MAP = {role: role for role in ROLES}
TARGET_MAP = {"accept": "approve", "decline": "reject", "ask": "revise"}
MEMBER_LOGITS = [[2.0, 0.0, 0.0], [2.1, 0.1, 0.0], [1.9, 0.0, 0.1], [2.0, -0.1, 0.1]]


@pytest.fixture(autouse=True)
def _clear_autonomy_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in list(os.environ):
        if name.startswith("AGENT_LEARNING_AUTONOMY_"):
            monkeypatch.delenv(name)


@pytest.fixture
def store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> LocalFileStore:
    local = LocalFileStore(tmp_path / "store")
    monkeypatch.setattr(cli, "get_default_store", lambda: local)
    return local


def _member(store: LocalFileStore, task_id: str, logits: list[float]) -> None:
    metadata = {"policy_scope": "delegated_decision", "decision_authority": "low",
                "family": FAMILY, "role_map": dict(ROLE_MAP)}
    for version in range(1, 4):
        store.store_policy(PolicySnapshot(
            id=f"{task_id}-v{version}", agent_id=AGENT, task_id=task_id, version=version,
            actions=[Action(id=role) for role in ROLES], logits=dict(zip(ROLES, logits)),
            episodes_seen=version * 20, updates_applied=version, metadata=copy.deepcopy(metadata),
        ))
    for index in range(40):
        episode = Episode(
            id=f"{task_id}-episode-{index}", agent_id=AGENT, task_id=task_id, intent_summary="Decide",
            action_id="approve", expected_outcome="Correct decision", execution_status="completed",
            result_summary="The outcome supported the decision",
            metadata={"correct_action_id": "approve", "task_completed": True},
        )
        store.store_episode(episode)
        store.store_reward(Reward(episode_id=episode.id, agent_id=AGENT, source=RewardSource.AGGREGATE, value=0.7))


def _compile(store: LocalFileStore, name: str = NAME) -> PolicySnapshot:
    for index, row in enumerate(MEMBER_LOGITS):
        if store.get_active_policy(AGENT, f"member-{index}") is None:
            _member(store, f"member-{index}", row)
    code = cli.main(["task-policy-meta-compile", "--agent-id", AGENT, "--family", FAMILY,
                     "--output-prior-name", name, "--sigma-het", "0.5"])
    assert code == 0
    prior = store.get_active_policy(AGENT, name)
    assert prior is not None
    return prior


def _target(store: LocalFileStore, **meta: object) -> PolicySnapshot:
    metadata: dict[str, object] = {"policy_scope": "delegated_decision", "decision_authority": "low",
                                   "family": FAMILY, "role_map": dict(TARGET_MAP)}
    metadata.update(meta)
    for key in [k for k, v in metadata.items() if v is None]:
        del metadata[key]
    snapshot = PolicySnapshot(
        id="target-v0", agent_id=AGENT, task_id="target-task", version=0,
        actions=[Action(id=a) for a in TARGET_MAP], logits={a: 0.0 for a in TARGET_MAP}, metadata=metadata,
    )
    store.store_policy(snapshot)
    return snapshot


def _run(*extra: str, name: str = NAME) -> int:
    return cli.main(["task-policy-warm-start", "--agent-id", AGENT, "--target-task-id", "target-task",
                     "--meta-prior", name, *extra])


def _tree(root: Path) -> dict[str, bytes]:
    return {str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def _as_meta_prior(prior: PolicySnapshot) -> MetaPrior:
    roles = tuple(sorted(a.id for a in prior.actions))
    return MetaPrior(representation="softmax", roles=roles, values={r: prior.logits[r] for r in roles},
                     member_count=4, role_spread={r: 0.0 for r in roles}, sigma_het=0.5, kappa_prior=None,
                     compiled_from=())


# ---- AC_0 and AC_1 -----------------------------------------------------------------------------


def test_ac0_logits_equal_seed_values_and_provenance_names_the_prior(store: LocalFileStore) -> None:
    prior = _compile(store)
    _target(store)
    assert _run("--damping", "0.8") == 0

    target = store.get_active_policy(AGENT, "target-task")
    assert target is not None and target.version == 1 and target.episodes_seen == 0
    expected = seed_values(_as_meta_prior(prior), TARGET_MAP, list(TARGET_MAP))
    assert target.logits == pytest.approx({a: expected[a] * 0.8 for a in TARGET_MAP}, abs=1e-12)
    meta = target.metadata
    assert meta["warm_start_donor_kind"] == "meta_prior"
    assert meta["warm_start_donor_policy_id"] == prior.id
    assert meta["warm_start_donor_task_id"] == NAME
    assert meta["warm_start_donor_version"] == prior.version
    assert meta["warm_start_action_map"] == TARGET_MAP
    assert meta["warm_start_donor_gate_met"] is None
    assert meta["warm_start_damping_factor"] == 0.8
    earlier = store.get_policy("target-v0", AGENT)
    assert earlier is not None and earlier.logits == {a: 0.0 for a in TARGET_MAP}


def test_ac1_default_damping_is_one_and_half_is_half(store: LocalFileStore) -> None:
    prior = _compile(store)
    expected = seed_values(_as_meta_prior(prior), TARGET_MAP, list(TARGET_MAP))
    _target(store)
    assert _run() == 0
    full = store.get_active_policy(AGENT, "target-task")
    assert full is not None
    assert full.logits == pytest.approx(expected, abs=1e-12)
    assert full.metadata["warm_start_damping_factor"] == 1.0

    # a second, cold target for the 0.5 case
    store.store_policy(PolicySnapshot(
        id="half-v0", agent_id=AGENT, task_id="half-task", version=0,
        actions=[Action(id=a) for a in TARGET_MAP], logits={a: 0.0 for a in TARGET_MAP},
        metadata={"policy_scope": "delegated_decision", "decision_authority": "low",
                  "family": FAMILY, "role_map": dict(TARGET_MAP)},
    ))
    assert cli.main(["task-policy-warm-start", "--agent-id", AGENT, "--target-task-id", "half-task",
                     "--meta-prior", NAME, "--damping", "0.5"]) == 0
    half = store.get_active_policy(AGENT, "half-task")
    assert half is not None
    assert half.logits == pytest.approx({a: v * 0.5 for a, v in expected.items()}, abs=1e-12)


# ---- AC_2 ---------------------------------------------------------------------------------------


@pytest.mark.parametrize("override", [{"family": None}, {"family": "another-family"}, {"role_map": None}])
def test_ac2_a_target_that_does_not_match_the_prior_writes_nothing(
    store: LocalFileStore, override: dict[str, object], tmp_path: Path
) -> None:
    _compile(store)
    _target(store, **override)
    before = _tree(tmp_path / "store")
    assert _run() != 0
    assert _tree(tmp_path / "store") == before


def test_ac2_a_role_map_that_does_not_fit_the_prior_writes_nothing(store: LocalFileStore) -> None:
    _compile(store)
    _target(store, role_map={"accept": "approve", "decline": "reject", "ask": "unknown-role"})
    assert _run() != 0
    target = store.get_active_policy(AGENT, "target-task")
    assert target is not None and target.version == 0


# ---- AC_3 ---------------------------------------------------------------------------------------


def test_ac3_the_latest_prior_is_used_not_the_one_it_supersedes(store: LocalFileStore) -> None:
    first = _compile(store)
    second = _compile(store)
    assert second.version == first.version + 1 and second.metadata["supersedes"] == first.id
    _target(store)
    assert _run() == 0
    target = store.get_active_policy(AGENT, "target-task")
    assert target is not None
    assert target.metadata["warm_start_donor_policy_id"] == second.id
    assert target.metadata["warm_start_donor_version"] == second.version


def test_ac3_a_superseded_latest_prior_is_refused(store: LocalFileStore) -> None:
    first = _compile(store)
    second = _compile(store)
    # a stored snapshot that replaces the latest one out of order, with a lower version
    store.store_policy(PolicySnapshot(
        id="late-replacement", agent_id=AGENT, task_id=NAME, version=0,
        actions=list(second.actions), logits=dict(second.logits),
        metadata={**copy.deepcopy(second.metadata), "supersedes": second.id},
    ))
    assert first.id != second.id
    _target(store)
    assert _run() != 0
    target = store.get_active_policy(AGENT, "target-task")
    assert target is not None and target.version == 0


def test_ac3_a_missing_prior_exits_non_zero(store: LocalFileStore) -> None:
    _target(store)
    assert _run(name="no-such-prior") != 0
    target = store.get_active_policy(AGENT, "target-task")
    assert target is not None and target.version == 0


def test_ac3_a_task_that_is_not_a_meta_prior_exits_non_zero(store: LocalFileStore) -> None:
    _member(store, "ordinary", [1.0, 0.0, -1.0])
    _target(store)
    assert _run(name="ordinary") != 0


def test_ac3_a_prior_in_beta_counts_exits_non_zero(store: LocalFileStore) -> None:
    store.store_policy(PolicySnapshot(
        id="beta-prior-v0", agent_id=AGENT, task_id="beta-prior", version=0,
        actions=[Action(id=r) for r in ROLES], logits={r: 0.0 for r in ROLES},
        metadata={"is_family_meta_prior": True, "family": FAMILY, "representation": "thompson",
                  "posterior_parameters": {"alpha": {r: 3.0 for r in ROLES}, "beta": {r: 2.0 for r in ROLES}}},
    ))
    _target(store)
    assert _run(name="beta-prior") != 0
    target = store.get_active_policy(AGENT, "target-task")
    assert target is not None and target.version == 0


# ---- AC_4 and AC_5 ------------------------------------------------------------------------------


def test_ac4_action_map_with_meta_prior_exits_non_zero(store: LocalFileStore) -> None:
    _compile(store)
    _target(store)
    assert _run("--action-map", json.dumps(TARGET_MAP)) != 0
    target = store.get_active_policy(AGENT, "target-task")
    assert target is not None and target.version == 0


def test_ac5_the_prior_is_left_equal(store: LocalFileStore) -> None:
    prior = _compile(store)
    before = prior.to_dict()
    _target(store)
    assert _run() == 0
    after = store.get_active_policy(AGENT, NAME)
    assert after is not None and after.to_dict() == before
    stored = store.get_policy(prior.id, AGENT)
    assert stored is not None and stored.to_dict() == before


# ---- Q-100-1: a malformed stored prior is a clean refusal, not a crash ----------------------------


def test_a_prior_with_an_action_that_has_no_logit_is_refused_cleanly(
    store: LocalFileStore, capsys: pytest.CaptureFixture[str]
) -> None:
    store.store_policy(PolicySnapshot(
        id="broken-prior-v0", agent_id=AGENT, task_id="broken-prior", version=0,
        actions=[Action(id=r) for r in ROLES], logits={"approve": 0.5, "reject": -0.5},
        metadata={"is_family_meta_prior": True, "family": FAMILY, "representation": "softmax"},
    ))
    _target(store)
    assert _run(name="broken-prior") == 2
    err = capsys.readouterr().err
    assert "revise" in err and "no logit" in err
    target = store.get_active_policy(AGENT, "target-task")
    assert target is not None and target.version == 0
