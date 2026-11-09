"""Contract tests for Story 21.5: Human Decisions and the Promotion Seed.

Governing specifications:
- ADR-021 §4.1 (threshold ownership), §4.4 (promotion seeds without a gradient, evidence expires),
  Invariant 9 (threshold change control)
- BRD-021 (BRU-021-05, BRU-021-11, BRU-021-12, BRU-021-13, BRU-021-14)
- FDD-021 §1 items 2 and 5, §2.1 (SEED_DAMPING_DEFAULT), §2.4 (routing_state), §3 items 8 and 10,
  §4 K1, K4, K5, §5
- Story 21.5 (docs/user-stories/epic-21-contextual-authority-ensemble-routing.md)

Acceptance Criteria:
- AC_0 (Seed Arithmetic): seed_prior with counts (18, 3, 1) gives (0.8889, -0.2018, -0.6870) at damping
  0.70 and (1.2698, -0.2883, -0.9815) at damping 1.0, within 1e-4; the logits sum to 0; damping of 0, 1.5,
  a negative count, or a missing action raises ValueError.
- AC_1 (Needs An Approval Episode): every action of task-policy-routing-set except --revoke-bucket exits
  non-zero and writes nothing without --approval-episode, with an episode that does not exist, belongs to
  another task, or is not adjudicated and accepted.
- AC_2 (Approve A Bucket): --approve-bucket with an eligible proposal writes the bucket as approved with the
  approval episode id, the time, the seed prior and its provenance (damping and counts); with an ineligible
  proposal, or with max_evidence_age_days unset, it exits non-zero and writes nothing.
- AC_3 (Thresholds Revalidate): --set-thresholds writes valid thresholds, rejects an invalid RoutingConfig,
  and marks every approved bucket revalidate true, after which the router receives approved_for_low false
  for them until a new approval.
- AC_4 (Revoke): --revoke-bucket sets approved false without an approval episode.
- AC_5 (Same Snapshot): the command changes only routing_state, keeping the snapshot id and version; a
  snapshot without routing_state is never routed.
- AC_6 (Seed Not Evidence): a bucket seeded this way, with no LOW episodes of its own, adds no scored
  outcome to any autonomy gate.

Contract Interpretations (spec gate episode spec-21_5-ae035296, margin +0.1941; LL-011):
- I1: Upstream Fork Purity (Invariant 6): FDD-021 §1 names src/agent_learning/routing.py; the code lives in
  src/agent_learning_ext/routing.py and the command in src/agent_learning_ext/cli.py (agent-learn-ext).
  src/agent_learning/ is untouched (tests/test_upstream_untouched.py).
- I2: Storage Decoupling & Serialization Round-Trip: routing.py still imports no storage module; the
  routing_state the command writes survives json.dumps/json.loads and PolicySnapshot.to_dict/from_dict
  (asserted after every successful write, which goes through a real InMemoryStore copy).
- I3: Empty Collection Base Case: seed_prior with empty counts and no action ids returns {} and all-zero
  counts give the uniform (all-zero) prior, without raising; --approve-bucket over a store with no
  routed episode gives n = 0, an ineligible proposal, exit non-zero and nothing written.
- I4: The approval-episode check is one helper shared with task-policy-weights-adopt (Story 22.6): the
  episode is looked up under --approval-agent-id (default --agent-id, then agent-learning-governance), its
  task_id must be approve-routing-thresholds (for --set-thresholds and --set-max-evidence-age-days) or
  approve-routing-bucket (for --approve-bucket), and feedback_status adjudicated with decision_disposition
  accepted (FDD-021 §3 item 10).
- I5: "the router receives approved_for_low false" is made concrete by routing.approved_for_low(snapshot,
  bucket): true only when the snapshot carries routing_state, the bucket is approved and revalidate is not
  true. "Never routed" is routing.is_routed(snapshot), false without routing_state (FDD-021 §1 item 5);
  approved_for_low is then false for every bucket. Wiring either into task-policy-decide is out of scope.
- I6: --set-thresholds marks only buckets whose approved is true; an unapproved bucket is left as it is.
  A JSON object with keys other than tau_esc, tau_deesc and eps_margin is rejected as an invalid config.
- I7: --approve-bucket reads the task's episodes from the store (at most 500, newest first, the CLI's
  episode cap; an undercount can only make a bucket less eligible), computes agreement with the stored
  max_evidence_age_days and now = the current UTC time, and propose_bucket with the standard tier
  AutonomyConfig. The seed counts are the agreement's final-action counts over every action id of the
  policy, an unseen action counted 0 (Laplace smoothing gives it a finite logit). A final action outside the
  policy's actions makes seed_prior raise, and the command writes nothing.
- I8: --revoke-bucket on a bucket that is not in routing_state (or a snapshot without routing_state) exits
  non-zero and writes nothing; it never creates routing_state, which would make the snapshot routed.
- I9: AC_6 must be able to fail. The fixture's stored logits recommend revise_plan while the seed's modal
  action is approve_plan, and every episode carries an AGGREGATE reward, so a seed written into the stored
  logits would move assess_autonomy's scored outcomes (the test shows this with that mutant snapshot).
  Both the extension and the upstream assess_autonomy are checked over all four tiers.
- I10: Every worked number of AC_0 is recomputed in the test from f_a = (n_a + 1) / (N + |A|) and
  logit = damping * (ln f_a - mean ln f), and also checked against the literals, within 1e-4.

The episodes, snapshots and approval episodes are built in the tests and labelled synthetic.
"""

from __future__ import annotations

import ast
import copy
import json
import math
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from agent_learning.autonomy import assess_autonomy as upstream_assess_autonomy
from agent_learning.config import AutonomyConfig as UpstreamAutonomyConfig
from agent_learning.storage.memory import InMemoryStore
from agent_learning.types import Action, Episode, PolicySnapshot, Reward, RewardSource
from agent_learning_ext import routing
from agent_learning_ext.autonomy import assess_autonomy as ext_assess_autonomy
from agent_learning_ext.config import AutonomyConfig as ExtAutonomyConfig

ROOT = Path(__file__).resolve().parent.parent

AGENT = "agent-routing"
TASK = "classify-request"
BUCKET = "ctx-17"
ACTIONS = ("approve_plan", "reject_plan", "revise_plan")
THRESHOLDS = {"tau_esc": 1.0, "tau_deesc": 0.7, "eps_margin": 0.2}


# --- helpers ------------------------------------------------------------------------


def _fn(name: str) -> Any:
    """Resolve a routing function at call time, so a missing one fails its own test (RED)."""
    value = getattr(routing, name, None)
    assert value is not None, f"agent_learning_ext.routing.{name} is missing"
    return value


def _expected_seed(counts: list[int], damping: float) -> list[float]:
    """FDD-021 §3 item 8 / K5, recomputed independently of the implementation."""
    total = sum(counts)
    freqs = [(c + 1) / (total + len(counts)) for c in counts]
    logs = [math.log(f) for f in freqs]
    mean_log = sum(logs) / len(logs)
    return [damping * (lf - mean_log) for lf in logs]


def _snapshot(metadata_extra: dict[str, Any] | None = None, logits: dict[str, float] | None = None) -> PolicySnapshot:
    metadata: dict[str, Any] = {"policy_scope": "delegated_decision", "decision_authority": "low"}
    if metadata_extra:
        metadata.update(metadata_extra)
    return PolicySnapshot(
        id="policy-routing-1",
        agent_id=AGENT,
        task_id=TASK,
        version=3,
        actions=[Action(id=a) for a in ACTIONS],
        logits=dict(logits) if logits is not None else {a: 0.0 for a in ACTIONS},
        metadata=metadata,
    )


def _approval(ep_id: str, task_id: str, *, status: str = "adjudicated", disposition: str = "accepted") -> Episode:
    return Episode(
        id=ep_id,
        agent_id=AGENT,
        task_id=task_id,
        action_id="approve",
        metadata={"feedback_status": status, "decision_disposition": disposition},
    )


def _routed_episode(
    ep_id: str,
    final_action: str,
    *,
    age_days: float = 1.0,
    bucket: str = BUCKET,
    shadow: str | None = None,
    status: str = "accepted",
) -> Episode:
    """A synthetic full-routed, scored episode of the bucket (FDD-021 §2.3)."""
    created = (datetime.now(timezone.utc) - timedelta(days=age_days)).isoformat()
    return Episode(
        id=ep_id,
        agent_id=AGENT,
        task_id=TASK,
        action_id=final_action,
        action_name=final_action,
        intent_summary="synthetic routed request",
        expected_outcome="synthetic",
        execution_status="succeeded",
        result_summary="synthetic",
        created_at=created,
        metadata={
            "routed_authority": "full",
            "routing_bucket": bucket,
            "routing": {"bucket": bucket, "route": "full", "reason": "entropy"},
            "shadow_low_action": shadow if shadow is not None else final_action,
            "shadow_entropy_bits": 1.2955,
            "feedback_status": status,
        },
    )


def _eligible_counts() -> dict[str, int]:
    # 36 of 36 agreements: Wilson lower bound 36 / (36 + 1.96^2) = 0.9036 >= 0.90.
    return {"approve_plan": 30, "reject_plan": 4, "revise_plan": 2}


def _store_with(
    snapshot: PolicySnapshot,
    *,
    counts: dict[str, int] | None = None,
    approvals: bool = True,
    rewards: bool = False,
) -> InMemoryStore:
    store = InMemoryStore()
    store.store_policy(snapshot)
    if approvals:
        store.store_episode(_approval("appr-thresholds", "approve-routing-thresholds"))
        store.store_episode(_approval("appr-bucket", "approve-routing-bucket"))
        store.store_episode(_approval("appr-pending", "approve-routing-bucket", status="pending", disposition="accepted"))
        store.store_episode(_approval("appr-rejected", "approve-routing-bucket", disposition="rejected"))
        store.store_episode(_approval("appr-other-task", "approve-adr"))
    i = 0
    for action, n in (counts or {}).items():
        for _ in range(n):
            ep = _routed_episode(f"routed-{i:03d}", action)
            store.store_episode(ep)
            if rewards:
                store.store_reward(
                    Reward(episode_id=ep.id, agent_id=AGENT, source=RewardSource.AGGREGATE, value=1.0)
                )
            i += 1
    return store


def _run(store: InMemoryStore, *args: str) -> int:
    from agent_learning_ext.cli import main

    with patch("agent_learning_ext.cli.get_default_store", return_value=store):
        try:
            return main(["task-policy-routing-set", "--agent-id", AGENT, "--task-id", TASK, *args])
        except SystemExit as exc:  # argparse errors
            return int(exc.code) if isinstance(exc.code, int) else 2


def _active(store: InMemoryStore) -> PolicySnapshot:
    snap = store.get_active_policy(AGENT, TASK)
    assert snap is not None
    return snap


def _state_dump(store: InMemoryStore) -> dict[str, Any]:
    """Everything the command could write: every policy version and the active pointer.

    Deep-copied through JSON: InMemoryStore's to_dict/from_dict share the metadata dict, so a later
    write would otherwise change this "before" picture too and hide it.
    """
    return json.loads(
        json.dumps(
            {
                "policies": [p.to_dict() for p in store.list_policies(AGENT, TASK)],
                "active": _active(store).to_dict(),
            }
        )
    )


def _without_routing_state(snapshot_dict: dict[str, Any]) -> dict[str, Any]:
    d = copy.deepcopy(snapshot_dict)
    d["metadata"].pop("routing_state", None)
    return d


def _assert_round_trips(snapshot: PolicySnapshot) -> None:
    state = snapshot.metadata["routing_state"]
    assert json.loads(json.dumps(state)) == state
    assert PolicySnapshot.from_dict(json.loads(json.dumps(snapshot.to_dict()))).metadata["routing_state"] == state


def _assert_command_live(store: InMemoryStore) -> None:
    """Positive control for a refusal test: the command exists and a valid call on the same store succeeds.

    Without it a refusal test passes for any reason the command exits non-zero (an unknown command too).
    """
    store.store_episode(_approval("appr-thresholds", "approve-routing-thresholds"))
    assert _run(store, "--set-thresholds", '{"tau_esc": 1.3, "tau_deesc": 0.5}', "--approval-episode", "appr-thresholds") == 0
    assert _active(store).metadata["routing_state"]["thresholds"]["tau_esc"] == 1.3


def _approved_state(**bucket_extra: Any) -> dict[str, Any]:
    bucket = {
        "approved": True,
        "revalidate": False,
        "approval_episode_id": "appr-bucket-earlier",
        "approved_at": "2026-11-01T08:00:00+00:00",
        "prior": {"approve_plan": 0.8889, "reject_plan": -0.2018, "revise_plan": -0.687},
        "prior_provenance": {"damping": 0.7, "counts": {"approve_plan": 18, "reject_plan": 3, "revise_plan": 1}},
    }
    bucket.update(bucket_extra)
    return {
        "routing_state": {
            "thresholds": dict(THRESHOLDS),
            "max_evidence_age_days": 30,
            "buckets": {BUCKET: bucket},
        }
    }


# --- AC_0: Seed Arithmetic -------------------------------------------------------------


@pytest.mark.parametrize(
    "damping, literals",
    [(0.70, (0.8889, -0.2018, -0.6870)), (1.0, (1.2698, -0.2883, -0.9815))],
)
def test_ac0_seed_prior_worked_numbers(damping: float, literals: tuple[float, float, float]) -> None:
    seed_prior = _fn("seed_prior")
    counts = {"approve_plan": 18, "reject_plan": 3, "revise_plan": 1}
    prior = seed_prior(counts, list(ACTIONS), damping=damping)

    assert set(prior) == set(ACTIONS)
    recomputed = _expected_seed([18, 3, 1], damping)
    for action, lit, rec in zip(ACTIONS, literals, recomputed):
        assert math.isclose(prior[action], rec, abs_tol=1e-9), (action, prior[action], rec)
        assert math.isclose(prior[action], lit, abs_tol=1e-4), (action, prior[action], lit)
        assert math.isclose(rec, lit, abs_tol=1e-4), "the AC literal disagrees with the formula"
    assert math.isclose(sum(prior.values()), 0.0, abs_tol=1e-12)


def test_ac0_seed_prior_worked_frequencies_and_default_damping() -> None:
    """f = (0.76, 0.16, 0.08) and base rate 0.8182 (FDD-021 §3 worked checks); default damping is 0.70."""
    total, k = 22, 3
    assert [(c + 1) / (total + k) for c in (18, 3, 1)] == pytest.approx([0.76, 0.16, 0.08], abs=1e-12)
    assert 18 / 22 == pytest.approx(0.8182, abs=1e-4)
    assert _fn("SEED_DAMPING_DEFAULT") == 0.70
    seed_prior = _fn("seed_prior")
    counts = {"approve_plan": 18, "reject_plan": 3, "revise_plan": 1}
    assert seed_prior(counts, list(ACTIONS)) == seed_prior(counts, list(ACTIONS), damping=0.70)


def test_ac0_seed_prior_follows_action_id_order_and_is_pure() -> None:
    seed_prior = _fn("seed_prior")
    counts = {"revise_plan": 1, "approve_plan": 18, "reject_plan": 3}
    before = dict(counts)
    order = ["revise_plan", "approve_plan", "reject_plan"]
    prior = seed_prior(counts, order, damping=0.70)
    assert list(prior) == order
    assert counts == before
    assert prior["approve_plan"] == pytest.approx(0.8889, abs=1e-4)


@pytest.mark.parametrize("bad_damping", [0, 0.0, 1.5, -0.1, float("nan"), float("inf"), True])
def test_ac0_seed_prior_rejects_bad_damping(bad_damping: Any) -> None:
    seed_prior = _fn("seed_prior")
    with pytest.raises(ValueError):
        seed_prior({"a": 1, "b": 2}, ["a", "b"], damping=bad_damping)


def test_ac0_seed_prior_accepts_damping_one() -> None:
    seed_prior = _fn("seed_prior")
    prior = seed_prior({"a": 1, "b": 2}, ["a", "b"], damping=1.0)
    assert prior["b"] > prior["a"]


@pytest.mark.parametrize(
    "counts, action_ids",
    [
        ({"a": -1, "b": 2}, ["a", "b"]),  # negative count
        ({"a": 1}, ["a", "b"]),  # action id missing from counts
        ({"a": 1, "b": 2, "c": 3}, ["a", "b"]),  # count for an action missing from action_ids
        ({"a": 1.5, "b": 2}, ["a", "b"]),  # not a whole count
        ({"a": True, "b": 2}, ["a", "b"]),  # bool is not a count
        ({"a": 1, "b": 2}, ["a", "a", "b"]),  # duplicate action id
    ],
)
def test_ac0_seed_prior_rejects_bad_counts(counts: dict[str, Any], action_ids: list[str]) -> None:
    seed_prior = _fn("seed_prior")
    with pytest.raises(ValueError):
        seed_prior(counts, action_ids, damping=0.70)


def test_ac0_seed_prior_empty_and_zero_counts() -> None:
    """I3: empty input gives {}; all-zero counts give the uniform (all-zero) prior."""
    seed_prior = _fn("seed_prior")
    assert seed_prior({}, [], damping=0.70) == {}
    zero = seed_prior({"a": 0, "b": 0, "c": 0}, ["a", "b", "c"], damping=0.70)
    assert zero == pytest.approx({"a": 0.0, "b": 0.0, "c": 0.0}, abs=1e-12)


def test_ac0_routing_module_still_pure() -> None:
    """I2: routing.py (now with seed_prior) imports no storage module, no random and no numpy."""
    tree = ast.parse((ROOT / "src" / "agent_learning_ext" / "routing.py").read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    assert not [m for m in imported if "storage" in m or m in ("random", "numpy") or m.startswith("numpy.")]


# --- AC_1: Needs An Approval Episode ------------------------------------------------------

# (action args, the approval episode a valid call cites, the approval of the other routing task)
_GATED_ACTIONS = [
    (["--set-thresholds", '{"tau_esc": 1.2, "tau_deesc": 0.6}'], "appr-thresholds", "appr-bucket"),
    (["--set-max-evidence-age-days", "45"], "appr-thresholds", "appr-bucket"),
    (["--approve-bucket", BUCKET], "appr-bucket", "appr-thresholds"),
]


def _gated_store() -> InMemoryStore:
    # routing_state with an age set and an eligible bucket evidence, so the positive control succeeds.
    snap = _snapshot({"routing_state": {"thresholds": dict(THRESHOLDS), "max_evidence_age_days": 30, "buckets": {}}})
    return _store_with(snap, counts=_eligible_counts())


@pytest.mark.parametrize("action_args, valid_approval, other_task_approval", _GATED_ACTIONS)
def test_ac1_positive_control_valid_approval_writes(
    action_args: list[str], valid_approval: str, other_task_approval: str
) -> None:
    """The same call with a valid approval episode succeeds and writes, so the refusals below are real."""
    store = _gated_store()
    before = _state_dump(store)
    assert _run(store, *action_args, "--approval-episode", valid_approval) == 0
    assert _state_dump(store) != before


@pytest.mark.parametrize("action_args, valid_approval, other_task_approval", _GATED_ACTIONS)
@pytest.mark.parametrize(
    "approval_case",
    ["missing", "not_found", "other_task", "other_routing_task", "pending", "rejected"],
)
def test_ac1_refused_without_valid_approval(
    action_args: list[str],
    valid_approval: str,
    other_task_approval: str,
    approval_case: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    store = _gated_store()
    before = _state_dump(store)
    approval_args = {
        "missing": [],
        "not_found": ["--approval-episode", "does-not-exist"],
        "other_task": ["--approval-episode", "appr-other-task"],
        "other_routing_task": ["--approval-episode", other_task_approval],
        "pending": ["--approval-episode", "appr-pending"],
        "rejected": ["--approval-episode", "appr-rejected"],
    }[approval_case]
    if valid_approval == "appr-thresholds" and approval_case in ("pending", "rejected"):
        # The pending / rejected fixtures belong to approve-routing-bucket; build thresholds ones.
        status, disp = ("pending", "accepted") if approval_case == "pending" else ("adjudicated", "rejected")
        store.store_episode(_approval("appr-t-" + approval_case, "approve-routing-thresholds", status=status, disposition=disp))
        approval_args = ["--approval-episode", "appr-t-" + approval_case]
        before = _state_dump(store)

    capsys.readouterr()
    code = _run(store, *action_args, *approval_args)
    err = capsys.readouterr().err.lower()
    assert code != 0
    assert _state_dump(store) == before, "a refused command wrote to the store"
    assert "approval episode" in err, err
    expected_cause = {
        "missing": "required",
        "not_found": "not found",
        "other_task": "belongs to",
        "other_routing_task": "belongs to",
        "pending": "not adjudicated and accepted",
        "rejected": "not adjudicated and accepted",
    }[approval_case]
    assert expected_cause in err, err


def test_ac1_weights_adopt_shares_the_approval_check() -> None:
    """I4: one approval-episode helper serves both approval-gated commands."""
    from agent_learning_ext import cli

    helper = getattr(cli, "_approval_episode_error", None)
    assert helper is not None, "cli._approval_episode_error is missing"
    src = Path(cli.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    callers = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and any(
            isinstance(c, ast.Call) and isinstance(c.func, ast.Name) and c.func.id == "_approval_episode_error"
            for c in ast.walk(node)
        )
    }
    assert {"_cmd_adopt_weights", "_cmd_routing_set"} <= callers, callers


# --- AC_2: Approve A Bucket ----------------------------------------------------------------


def test_ac2_approve_eligible_bucket_writes_seed_and_provenance() -> None:
    snap = _snapshot({"routing_state": {"thresholds": dict(THRESHOLDS), "max_evidence_age_days": 30, "buckets": {}}})
    store = _store_with(snap, counts=_eligible_counts())
    # Evidence that must not count: outside the 30-day window, and another bucket.
    store.store_episode(_routed_episode("old-1", "reject_plan", age_days=40))
    store.store_episode(_routed_episode("other-bucket-1", "reject_plan", bucket="ctx-99"))

    t0 = datetime.now(timezone.utc)
    assert _run(store, "--approve-bucket", BUCKET, "--approval-episode", "appr-bucket") == 0
    t1 = datetime.now(timezone.utc)

    active = _active(store)
    bucket = active.metadata["routing_state"]["buckets"][BUCKET]
    assert bucket["approved"] is True
    assert bucket["revalidate"] is False
    assert bucket["approval_episode_id"] == "appr-bucket"
    approved_at = datetime.fromisoformat(bucket["approved_at"].replace("Z", "+00:00"))
    assert t0 - timedelta(seconds=1) <= approved_at <= t1 + timedelta(seconds=1)

    counts = _eligible_counts()
    assert bucket["prior_provenance"] == {"damping": 0.70, "counts": counts}
    expected = _expected_seed([counts[a] for a in ACTIONS], 0.70)
    for action, value in zip(ACTIONS, expected):
        assert math.isclose(bucket["prior"][action], value, abs_tol=1e-9), (action, bucket["prior"], expected)
    assert math.isclose(sum(bucket["prior"].values()), 0.0, abs_tol=1e-9)
    _assert_round_trips(active)


def test_ac2_approve_bucket_with_explicit_damping_and_unseen_action() -> None:
    """I7: an action never final is counted 0 and still gets a finite logit; --damping is recorded."""
    snap = _snapshot({"routing_state": {"thresholds": dict(THRESHOLDS), "max_evidence_age_days": 30, "buckets": {}}})
    store = _store_with(snap, counts={"approve_plan": 33, "reject_plan": 3})
    assert _run(store, "--approve-bucket", BUCKET, "--approval-episode", "appr-bucket", "--damping", "1.0") == 0
    bucket = _active(store).metadata["routing_state"]["buckets"][BUCKET]
    assert bucket["prior_provenance"] == {
        "damping": 1.0,
        "counts": {"approve_plan": 33, "reject_plan": 3, "revise_plan": 0},
    }
    expected = _expected_seed([33, 3, 0], 1.0)
    assert [bucket["prior"][a] for a in ACTIONS] == pytest.approx(expected, abs=1e-9)
    assert all(math.isfinite(v) for v in bucket["prior"].values())


@pytest.mark.parametrize(
    "counts",
    [
        {"approve_plan": 20},  # 20 of 20: Wilson 0.8389, below 0.90
        {"approve_plan": 34},  # 34 of 34: 0.8985
        {"approve_plan": 10},  # below the minimum outcomes
        {},  # I3: no routed episode at all
    ],
)
def test_ac2_ineligible_proposal_refused(counts: dict[str, int], capsys: pytest.CaptureFixture[str]) -> None:
    snap = _snapshot({"routing_state": {"thresholds": dict(THRESHOLDS), "max_evidence_age_days": 30, "buckets": {}}})
    store = _store_with(snap, counts=counts)
    before = _state_dump(store)
    capsys.readouterr()
    assert _run(store, "--approve-bucket", BUCKET, "--approval-episode", "appr-bucket") != 0
    assert _state_dump(store) == before
    assert "not eligible" in capsys.readouterr().err.lower()


def test_ac2_ineligible_by_disagreement_refused() -> None:
    """36 scored episodes but the shadow disagrees on 3: Wilson(33, 36) is below 0.90."""
    snap = _snapshot({"routing_state": {"thresholds": dict(THRESHOLDS), "max_evidence_age_days": 30, "buckets": {}}})
    store = _store_with(snap, counts={"approve_plan": 33})
    for i in range(3):
        store.store_episode(_routed_episode(f"miss-{i}", "reject_plan", shadow="approve_plan"))
    before = _state_dump(store)
    assert _run(store, "--approve-bucket", BUCKET, "--approval-episode", "appr-bucket") != 0
    assert _state_dump(store) == before
    # Control: 36 agreements without a miss on an otherwise equal store are approved.
    eligible = _store_with(_snapshot({"routing_state": {"thresholds": dict(THRESHOLDS), "max_evidence_age_days": 30, "buckets": {}}}), counts={"approve_plan": 36})
    assert _run(eligible, "--approve-bucket", BUCKET, "--approval-episode", "appr-bucket") == 0


@pytest.mark.parametrize(
    "metadata_extra",
    [
        {"routing_state": {"thresholds": dict(THRESHOLDS), "buckets": {}}},  # age unset
        {"routing_state": {"thresholds": dict(THRESHOLDS), "max_evidence_age_days": None, "buckets": {}}},
        {},  # no routing_state at all
    ],
)
def test_ac2_max_evidence_age_unset_refused(metadata_extra: dict[str, Any], capsys: pytest.CaptureFixture[str]) -> None:
    store = _store_with(_snapshot(metadata_extra), counts=_eligible_counts())
    before = _state_dump(store)
    capsys.readouterr()
    assert _run(store, "--approve-bucket", BUCKET, "--approval-episode", "appr-bucket") != 0
    assert _state_dump(store) == before
    assert "max_evidence_age_days" in capsys.readouterr().err


def test_ac2_final_action_outside_policy_refused() -> None:
    """I7: a final action the policy does not have makes seed_prior raise; nothing is written."""
    snap = _snapshot({"routing_state": {"thresholds": dict(THRESHOLDS), "max_evidence_age_days": 30, "buckets": {}}})
    store = _store_with(snap, counts={"approve_plan": 36, "escalate_plan": 1})
    before = _state_dump(store)
    assert _run(store, "--approve-bucket", BUCKET, "--approval-episode", "appr-bucket") != 0
    assert _state_dump(store) == before
    _assert_command_live(store)


# --- AC_3: Thresholds Revalidate -------------------------------------------------------------


def test_ac3_set_thresholds_writes_valid_config() -> None:
    store = _store_with(_snapshot(), counts={})
    new = {"tau_esc": 1.2, "tau_deesc": 0.6, "eps_margin": 0.25}
    assert _run(store, "--set-thresholds", json.dumps(new), "--approval-episode", "appr-thresholds") == 0
    active = _active(store)
    assert active.metadata["routing_state"]["thresholds"] == new
    _assert_round_trips(active)
    cfg = routing.RoutingConfig(**active.metadata["routing_state"]["thresholds"])
    assert (cfg.tau_esc, cfg.tau_deesc, cfg.eps_margin) == (1.2, 0.6, 0.25)


def test_ac3_set_thresholds_fills_default_margin() -> None:
    store = _store_with(_snapshot(), counts={})
    assert _run(store, "--set-thresholds", '{"tau_esc": 1.0, "tau_deesc": 0.7}', "--approval-episode", "appr-thresholds") == 0
    assert _active(store).metadata["routing_state"]["thresholds"] == THRESHOLDS


@pytest.mark.parametrize(
    "bad",
    [
        '{"tau_esc": 0.8, "tau_deesc": 0.7}',  # gap under 0.15
        '{"tau_esc": 0.849, "tau_deesc": 0.7}',  # gap 0.149
        '{"tau_esc": 0.5, "tau_deesc": 0.7}',  # inverted
        '{"tau_esc": NaN, "tau_deesc": 0.7}',  # non-finite
        '{"tau_esc": 1.0, "tau_deesc": -0.2}',  # negative
        '{"tau_esc": 1.0, "tau_deesc": 0.7, "eps_margin": 0}',
        '{"tau_esc": 1.0, "tau_deesc": 0.7, "eps_margin": 1.5}',
        '{"tau_esc": 1.0}',  # tau_deesc has no default
        '{"tau_esc": 1.0, "tau_deesc": 0.7, "extra": 1}',  # I6: unknown key
        '[1.0, 0.7]',  # not an object
        "not json",
    ],
)
def test_ac3_invalid_thresholds_rejected(bad: str) -> None:
    store = _store_with(_snapshot(_approved_state()), counts={})
    before = _state_dump(store)
    assert _run(store, "--set-thresholds", bad, "--approval-episode", "appr-thresholds") != 0
    assert _state_dump(store) == before
    _assert_command_live(store)


def test_ac3_threshold_change_revalidates_approved_buckets_until_reapproval() -> None:
    state = _approved_state()
    state["routing_state"]["buckets"]["ctx-unapproved"] = {"approved": False, "revalidate": False}
    store = _store_with(_snapshot(state), counts=_eligible_counts())
    approved_for_low = _fn("approved_for_low")
    cfg = routing.RoutingConfig(**THRESHOLDS)

    # Positive control: before the change the approved bucket reaches the router approved, and routes low.
    before = _active(store)
    assert approved_for_low(before, BUCKET) is True
    low = routing.route([0.95, 0.05], "standard", TASK, None, approved_for_low(before, BUCKET), False, cfg)
    assert low.authority.value == "low" and low.reason == "low"

    assert _run(store, "--set-thresholds", json.dumps(THRESHOLDS), "--approval-episode", "appr-thresholds") == 0
    after = _active(store)
    buckets = after.metadata["routing_state"]["buckets"]
    assert buckets[BUCKET]["revalidate"] is True
    assert buckets["ctx-unapproved"] == {"approved": False, "revalidate": False}  # I6
    assert approved_for_low(after, BUCKET) is False
    full = routing.route([0.95, 0.05], "standard", TASK, "low", approved_for_low(after, BUCKET), False, cfg)
    assert full.authority.value == "full" and full.reason == "not_approved"

    # A new approval restores it.
    assert _run(store, "--approve-bucket", BUCKET, "--approval-episode", "appr-bucket") == 0
    again = _active(store)
    assert again.metadata["routing_state"]["buckets"][BUCKET]["revalidate"] is False
    assert approved_for_low(again, BUCKET) is True


# --- AC_4: Revoke ------------------------------------------------------------------------------


def test_ac4_revoke_without_approval_episode() -> None:
    store = _store_with(_snapshot(_approved_state()), counts={}, approvals=False)
    approved_for_low = _fn("approved_for_low")
    assert approved_for_low(_active(store), BUCKET) is True
    assert _run(store, "--revoke-bucket", BUCKET) == 0
    active = _active(store)
    assert active.metadata["routing_state"]["buckets"][BUCKET]["approved"] is False
    assert approved_for_low(active, BUCKET) is False
    _assert_round_trips(active)


@pytest.mark.parametrize("metadata_extra", [{}, {"routing_state": {"thresholds": dict(THRESHOLDS), "buckets": {}}}])
def test_ac4_revoke_unknown_bucket_writes_nothing(metadata_extra: dict[str, Any]) -> None:
    """I8: revoking a bucket that is not there never creates routing_state."""
    store = _store_with(_snapshot(metadata_extra), counts={}, approvals=False)
    before = _state_dump(store)
    assert _run(store, "--revoke-bucket", BUCKET) != 0
    assert _state_dump(store) == before
    _assert_command_live(store)


def test_ac4_exactly_one_action() -> None:
    store = _store_with(_snapshot(_approved_state()), counts={})
    before = _state_dump(store)
    assert _run(store) != 0
    assert _run(store, "--revoke-bucket", BUCKET, "--approve-bucket", BUCKET, "--approval-episode", "appr-bucket") != 0
    assert _state_dump(store) == before
    assert _run(store, "--revoke-bucket", BUCKET) == 0  # control: one action alone is accepted


# --- AC_5: Same Snapshot ------------------------------------------------------------------------


@pytest.mark.parametrize(
    "start_state, action_args",
    [
        ({}, ["--set-thresholds", json.dumps(THRESHOLDS), "--approval-episode", "appr-thresholds"]),
        ({}, ["--set-max-evidence-age-days", "30", "--approval-episode", "appr-thresholds"]),
        (
            {"routing_state": {"thresholds": dict(THRESHOLDS), "max_evidence_age_days": 30, "buckets": {}}},
            ["--approve-bucket", BUCKET, "--approval-episode", "appr-bucket"],
        ),
        (_approved_state(), ["--revoke-bucket", BUCKET]),
    ],
)
def test_ac5_only_routing_state_changes(start_state: dict[str, Any], action_args: list[str]) -> None:
    snap = _snapshot(copy.deepcopy(start_state), logits={"approve_plan": 0.3, "reject_plan": -0.1, "revise_plan": -0.2})
    store = _store_with(snap, counts=_eligible_counts())
    before = json.loads(json.dumps(_active(store).to_dict()))  # deep copy, see _state_dump
    versions_before = len(store.list_policies(AGENT, TASK))

    assert _run(store, *action_args) == 0
    after_snap = _active(store)
    after = after_snap.to_dict()
    assert after["id"] == before["id"]
    assert after["version"] == before["version"]
    assert len(store.list_policies(AGENT, TASK)) == versions_before
    assert after.get("metadata", {}).get("routing_state") != before.get("metadata", {}).get("routing_state")
    assert _without_routing_state(after) == _without_routing_state(before)
    _assert_round_trips(after_snap)


def test_ac5_set_max_evidence_age_days_written_and_validated() -> None:
    store = _store_with(_snapshot(), counts={})
    assert _run(store, "--set-max-evidence-age-days", "45", "--approval-episode", "appr-thresholds") == 0
    assert _active(store).metadata["routing_state"]["max_evidence_age_days"] == 45
    before = _state_dump(store)
    for bad in ("0", "-3", "nan", "inf", "abc"):
        assert _run(store, "--set-max-evidence-age-days", bad, "--approval-episode", "appr-thresholds") != 0
    assert _state_dump(store) == before


def test_ac5_snapshot_without_routing_state_is_never_routed() -> None:
    is_routed = _fn("is_routed")
    approved_for_low = _fn("approved_for_low")
    plain = _snapshot()
    assert is_routed(plain) is False
    assert approved_for_low(plain, BUCKET) is False
    # Even a bucket-shaped entry elsewhere in metadata does not make it routed.
    stray = _snapshot({"buckets": {BUCKET: {"approved": True}}})
    assert is_routed(stray) is False and approved_for_low(stray, BUCKET) is False

    # Positive control: once a human decision writes routing_state the snapshot is routed.
    store = _store_with(_snapshot(), counts={})
    assert _run(store, "--set-thresholds", json.dumps(THRESHOLDS), "--approval-episode", "appr-thresholds") == 0
    assert is_routed(_active(store)) is True
    assert is_routed(_snapshot(_approved_state())) is True
    assert approved_for_low(_snapshot(_approved_state()), BUCKET) is True
    assert approved_for_low(_snapshot(_approved_state()), "ctx-unknown") is False


def test_ac5_refused_commands_never_create_routing_state() -> None:
    store = _store_with(_snapshot(), counts=_eligible_counts())
    for args in (
        ["--set-thresholds", '{"tau_esc": 0.8, "tau_deesc": 0.7}', "--approval-episode", "appr-thresholds"],
        ["--set-thresholds", json.dumps(THRESHOLDS)],
        ["--approve-bucket", BUCKET, "--approval-episode", "appr-bucket"],
        ["--revoke-bucket", BUCKET],
    ):
        assert _run(store, *args) != 0, args
        assert "routing_state" not in _active(store).metadata, args
    assert _fn("is_routed")(_active(store)) is False


# --- AC_6: Seed Not Evidence ---------------------------------------------------------------------

_TIERS = ("low", "standard", "high", "critical")


def _assessments(store: InMemoryStore, snapshot: PolicySnapshot) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for tier in _TIERS:
        out[f"ext-{tier}"] = asdict(ext_assess_autonomy(store, snapshot, ExtAutonomyConfig.for_tier(tier)))
        out[f"upstream-{tier}"] = asdict(
            upstream_assess_autonomy(store, snapshot, UpstreamAutonomyConfig.for_tier(tier))
        )
    return out


def _ac6_store() -> InMemoryStore:
    # Stored logits recommend revise_plan; the seed's modal action is approve_plan (I9).
    snap = _snapshot(
        {"routing_state": {"thresholds": dict(THRESHOLDS), "max_evidence_age_days": 30, "buckets": {}}},
        logits={"approve_plan": -1.0, "reject_plan": 0.0, "revise_plan": 1.0},
    )
    store = _store_with(snap, counts=_eligible_counts(), rewards=True)
    # Newest scored episode is a rejection with a correction, so no explicit-feedback override applies.
    newest = _routed_episode("routed-newest", "revise_plan", age_days=0.01, shadow="approve_plan", status="rejected")
    newest.metadata["correct_action_id"] = "approve_plan"
    store.store_episode(newest)
    return store


def test_ac6_seed_adds_no_scored_outcome_to_any_gate() -> None:
    store = _ac6_store()
    episodes_before = len(store.query_episodes(AGENT, limit=10_000))
    rewards_before = len(store.query_rewards(AGENT, limit=10_000))
    before = _assessments(store, _active(store))
    # The fixture is not empty: revise_plan's two scored episodes count today.
    assert before["ext-standard"]["scored_outcomes"] == 2
    assert before["upstream-standard"]["scored_outcomes"] == 2

    assert _run(store, "--approve-bucket", BUCKET, "--approval-episode", "appr-bucket") == 0
    seeded = _active(store)
    assert seeded.metadata["routing_state"]["buckets"][BUCKET]["approved"] is True
    # No LOW episode of the bucket exists.
    assert not [
        e for e in store.query_episodes(AGENT, limit=10_000) if e.metadata.get("routed_authority") == "low"
    ]

    after = _assessments(store, seeded)
    for key in before:
        assert after[key]["scored_outcomes"] == before[key]["scored_outcomes"], key
        assert after[key] == before[key], key
    assert len(store.query_episodes(AGENT, limit=10_000)) == episodes_before
    assert len(store.query_rewards(AGENT, limit=10_000)) == rewards_before
    assert seeded.logits == {"approve_plan": -1.0, "reject_plan": 0.0, "revise_plan": 1.0}


def test_ac6_is_not_vacuous_a_seed_in_the_logits_would_count() -> None:
    """I9: the mutant that writes the seed into the stored logits changes the scored outcomes."""
    store = _ac6_store()
    assert _run(store, "--approve-bucket", BUCKET, "--approval-episode", "appr-bucket") == 0
    seeded = _active(store)
    mutant = PolicySnapshot.from_dict(seeded.to_dict())
    mutant.logits = dict(seeded.metadata["routing_state"]["buckets"][BUCKET]["prior"])
    honest = _assessments(store, seeded)
    leaked = _assessments(store, mutant)
    assert leaked["ext-standard"]["scored_outcomes"] != honest["ext-standard"]["scored_outcomes"]
    assert leaked["upstream-standard"]["scored_outcomes"] != honest["upstream-standard"]["scored_outcomes"]
