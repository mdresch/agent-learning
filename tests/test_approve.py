"""IMP-007: scripts/approve.py runs an approval (frame, decide, compare, register) with the store checked first and
registers only on an explicit request that names the human and the disposition."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("approve", ROOT / "scripts" / "approve.py")
assert SPEC is not None and SPEC.loader is not None
ap = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ap)

TASK = "approve-adaptation-plan"
ACTIONS = ["approve_adaptation_plan", "reject_adaptation_plan", "request_revision_before_decision"]


def _scores(**over) -> dict:
    def ev(support: float) -> dict:
        return {"c1": {"support": support, "confidence": 0.9, "source": "read:doc"}}

    base = {
        "task_id": TASK,
        "subject": "ADP-TEST",
        "task": "Approve, reject or request revision of ADP-TEST",
        "criteria": [{"id": "c1", "weight": 1.0, "description": "the plan is sound"}],
        "options": {ACTIONS[0]: ev(0.9), ACTIONS[1]: ev(0.02), ACTIONS[2]: ev(0.1)},
    }
    base.update(over)
    return base


DECISION = {
    "task_id": TASK,
    "status": "needs_user_feedback",
    "selection_basis": "bayesian_decision",
    "selected_action": None,
    "proposed_action": {"id": ACTIONS[0]},
    "assessments": [
        {"action": {"id": ACTIONS[0]}, "robust_utility": 0.8, "expected_utility": 0.85},
        {"action": {"id": ACTIONS[1]}, "robust_utility": 0.01, "expected_utility": 0.02},
        {"action": {"id": ACTIONS[2]}, "robust_utility": 0.07, "expected_utility": 0.08},
    ],
}
ADJUDICATED = {
    "policy_id": "p1",
    "policy_version": 0,
    "selected_action": {"id": ACTIONS[0]},
    "assessments": DECISION["assessments"],
}


# What the real CLI prints (checked against `task-policy-compare` and a live `task-policy-adjudicate --disposition reject`):
COMPARE_TEXT = (
    "=== Comparison: a.json -> b.json ===\n"
    "Policy: p1 (v0) -> p1 (v0)\n"
    "Classification: PROGRESSION (margin widened by +0.0122; robust utility rose by +0.0122)\n"
    "Leader: approve_adr -> approve_adr (changed: False, feasible: True)\n"
)
REJECTED = {
    "policy_id": "p1",
    "policy_version": 0,
    "status": "rejected",
    "selected_action": None,
    "proposed_action": None,
    "rejected_action_ids": [ACTIONS[0]],
    "selection_basis": "bayesian_decision",
    "assessments": DECISION["assessments"],
}


class Cli:
    """Stands in for ``approve.agent_learn``: records the calls and answers with canned JSON."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []

    def __call__(self, *args: str) -> str:
        self.calls.append(args)
        if args[0] == "task-policy-decide":
            return json.dumps(DECISION)
        if args[0] == "task-policy-adjudicate":
            return json.dumps(REJECTED if "reject" in args else ADJUDICATED)
        if args[0] == "task-policy-compare":
            return COMPARE_TEXT
        return "{}"

    def names(self) -> list[str]:
        return [c[0] for c in self.calls]


@pytest.fixture()
def env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict:
    """A repository-shaped sandbox: its own policy-shapes folder and a store inside it."""
    root = tmp_path / "repo"
    shapes = root / "docs" / "policy-shapes"
    (shapes / "decision-frames").mkdir(parents=True)
    (shapes / "results").mkdir()
    (shapes / "episodes").mkdir()
    (shapes / f"{TASK}.actions.json").write_text(json.dumps([{"id": a} for a in ACTIONS]), encoding="utf-8")
    store = root / "data" / "agent-learning" / "store"
    store.mkdir(parents=True)
    cli = Cli()
    monkeypatch.setattr(ap, "ROOT", root)
    monkeypatch.setattr(ap, "SHAPES", shapes)
    monkeypatch.setattr(ap.s16, "ROOT", root)
    monkeypatch.setenv("AGENT_LEARNING_LOCAL_STORE_DIR", str(store))
    monkeypatch.setattr(ap.s16, "_store_announced", False)
    monkeypatch.setattr(ap.s16, "ALLOW_EXTERNAL_STORE", False)
    monkeypatch.setattr(ap, "agent_learn", cli)
    return {"root": root, "shapes": shapes, "store": store, "cli": cli, "tmp": tmp_path}


def _write(env: dict, scores: dict | None = None) -> Path:
    path = env["tmp"] / "scores.json"
    path.write_text(json.dumps(scores or _scores()), encoding="utf-8")
    return path


# --- the frame ---------------------------------------------------------------------------------------------------


def test_the_frame_has_the_criteria_options_and_evidence_of_the_scores(env: dict) -> None:
    frame = ap.build_frame(_scores())
    assert frame["task"].startswith("Approve") and frame["criteria"][0]["id"] == "c1"
    assert {o["action_id"] for o in frame["options"]} == set(ACTIONS)
    first = next(o for o in frame["options"] if o["action_id"] == ACTIONS[0])
    assert first["evidence"][0] == {"criterion_id": "c1", "source": "read:doc", "support": 0.9, "confidence": 0.9}


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda s: s["options"].pop(ACTIONS[2]), "missing"),
        (lambda s: s["options"][ACTIONS[0]].pop("c1"), "criterion"),
        (lambda s: s["options"][ACTIONS[0]]["c1"].update(support=1.5), "between 0 and 1"),
        (lambda s: s["options"][ACTIONS[0]]["c1"].update(confidence=-0.1), "between 0 and 1"),
        (lambda s: s["criteria"][0].update(weight=0), "weight"),
        (lambda s: s["options"].update({"made_up_action": s["options"][ACTIONS[0]]}), "not an action"),
    ],
)
def test_scores_that_do_not_fit_the_task_are_refused(env: dict, change, message: str) -> None:
    scores = _scores()
    change(scores)
    with pytest.raises(ap.s16.Stop, match=message):
        ap.validate(scores)


# --- decide ------------------------------------------------------------------------------------------------------


def test_decide_prints_the_store_runs_the_decision_and_registers_nothing(
    env: dict, capsys: pytest.CaptureFixture[str]
) -> None:
    assert ap.decide(_write(env), tag="t1") == 0
    out = capsys.readouterr().out
    assert str(env["store"].resolve()) in out
    assert env["cli"].names() == ["task-policy-decide"]
    shapes = env["shapes"]
    assert (shapes / "decision-frames" / "ADP-TEST-t1-approval.json").is_file()
    assert (shapes / "results" / "ADP-TEST-t1-decision-result.json").is_file()
    state = json.loads((shapes / "results" / "ADP-TEST-t1-approval-state.json").read_text(encoding="utf-8"))
    assert state["registered"] is False and len(state["frame_sha256"]) == 64
    assert "register" in out.lower() and "--by" in out


def test_decide_refuses_a_store_outside_the_repository(env: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENT_LEARNING_LOCAL_STORE_DIR", str(env["tmp"] / "elsewhere"))
    with pytest.raises(ap.s16.Stop, match="outside this repository"):
        ap.decide(_write(env), tag="t1")
    assert env["cli"].calls == []


def test_decide_compares_with_the_previous_result_of_the_same_subject(env: dict) -> None:
    ap.decide(_write(env), tag="2026-01-01")
    ap.decide(_write(env), tag="2026-02-01")
    assert env["cli"].names().count("task-policy-compare") == 1
    compare = next(c for c in env["cli"].calls if c[0] == "task-policy-compare")
    assert "ADP-TEST-2026-01-01-decision-result.json" in " ".join(compare)
    saved = (env["shapes"] / "results" / "ADP-TEST-2026-02-01-comparison.txt").read_text(encoding="utf-8")
    assert "Classification: PROGRESSION" in saved


def test_decide_does_not_overwrite_an_earlier_run(env: dict) -> None:
    ap.decide(_write(env), tag="t1")
    with pytest.raises(ap.s16.Stop, match="exists"):
        ap.decide(_write(env), tag="t1")


# --- register ----------------------------------------------------------------------------------------------------


def test_register_needs_a_decision_first(env: dict) -> None:
    with pytest.raises(ap.s16.Stop, match="No pending decision"):
        ap.register("ADP-TEST", tag=None, by="Menno", disposition="accept", summary="approved as written")
    assert env["cli"].calls == []


@pytest.mark.parametrize(
    ("by", "summary", "message"),
    [("", "s", "--by"), ("a\nb", "s", "single line"), ("Menno", "", "--summary"), ("Menno", "x" * 201, "too long")],
)
def test_register_needs_a_named_human_and_a_short_summary(env: dict, by: str, summary: str, message: str) -> None:
    ap.decide(_write(env), tag="t1")
    env["cli"].calls.clear()
    with pytest.raises(ap.s16.Stop, match=message):
        ap.register("ADP-TEST", tag="t1", by=by, disposition="accept", summary=summary)
    assert env["cli"].calls == []


def test_register_refuses_when_the_frame_changed_after_the_decision(env: dict) -> None:
    ap.decide(_write(env), tag="t1")
    frame = env["shapes"] / "decision-frames" / "ADP-TEST-t1-approval.json"
    frame.write_text(frame.read_text(encoding="utf-8") + " ", encoding="utf-8")
    env["cli"].calls.clear()
    with pytest.raises(ap.s16.Stop, match="changed"):
        ap.register("ADP-TEST", tag="t1", by="Menno", disposition="accept", summary="approved")
    assert env["cli"].calls == []


def test_register_adjudicates_then_registers_the_episode_once(env: dict) -> None:
    ap.decide(_write(env), tag="t1")
    env["cli"].calls.clear()
    ap.register("ADP-TEST", tag="t1", by="Menno Drescher", disposition="accept", summary="approved as written")
    assert env["cli"].names() == ["task-policy-adjudicate", "task-episode-register"]
    adjudicate = env["cli"].calls[0]
    assert "accept" in adjudicate and TASK in adjudicate
    episode = json.loads((env["shapes"] / "episodes" / "ADP-TEST-t1-episode.json").read_text(encoding="utf-8"))
    assert episode["task_id"] == TASK and episode["action_id"] == ACTIONS[0]
    assert "Menno Drescher" in episode["result_summary"] and "not backdated" in episode["result_summary"]
    assert episode["metadata"]["decision_disposition"] == "accepted"
    assert "assessed" in episode["input_summary"]
    state = json.loads((env["shapes"] / "results" / "ADP-TEST-t1-approval-state.json").read_text(encoding="utf-8"))
    assert state["registered"] is True and state["episode"] == episode["id"]
    with pytest.raises(ap.s16.Stop, match="No pending decision"):
        ap.register("ADP-TEST", tag="t1", by="Menno", disposition="accept", summary="again")


def test_a_rejection_is_recorded_as_rejected_and_names_no_correct_action(env: dict) -> None:
    """The real CLI answers a rejection with no selected or proposed action; the action is in rejected_action_ids."""
    ap.decide(_write(env), tag="t1")
    ap.register("ADP-TEST", tag="t1", by="Menno", disposition="reject", summary="not ready")
    episode = json.loads((env["shapes"] / "episodes" / "ADP-TEST-t1-episode.json").read_text(encoding="utf-8"))
    meta = episode["metadata"]
    assert meta["decision_disposition"] == "rejected" and meta["rejected_action_id"] == ACTIONS[0]
    assert "correct_action_id" not in meta  # a rejection must not label the rejected action as correct
    assert "Rejected by Menno" in episode["result_summary"]
    assert "--disposition" in env["cli"].calls[-2] and "reject" in env["cli"].calls[-2]


def test_an_accepted_episode_names_the_correct_action(env: dict) -> None:
    ap.decide(_write(env), tag="t1")
    ap.register("ADP-TEST", tag="t1", by="Menno", disposition="accept", summary="approved")
    meta = json.loads((env["shapes"] / "episodes" / "ADP-TEST-t1-episode.json").read_text(encoding="utf-8"))["metadata"]
    assert meta["correct_action_id"] == ACTIONS[0] and "rejected_action_id" not in meta


# --- constraint results ----------------------------------------------------------------------------------------


def test_a_stated_failing_constraint_reaches_the_frame(env: dict) -> None:
    scores = _scores(constraint_results={ACTIONS[0]: {"no_unfixed_critical_flaw": False}})
    ap.validate(scores)
    first = next(o for o in ap.build_frame(scores)["options"] if o["action_id"] == ACTIONS[0])
    assert first["constraint_results"] == {"no_unfixed_critical_flaw": False}


def test_decide_says_which_options_had_their_constraints_taken_as_satisfied(
    env: dict, capsys: pytest.CaptureFixture[str]
) -> None:
    scores = _scores(constraint_results={ACTIONS[0]: {"no_unfixed_critical_flaw": True}})
    ap.decide(_write(env, scores), tag="t1")
    out = capsys.readouterr().out
    assert "taken as satisfied" in out and ACTIONS[1] in out and ACTIONS[2] in out
    assert f"for: {ACTIONS[0]}" not in out


@pytest.mark.parametrize(
    "bad",
    [{"made_up": {"no_unfixed_critical_flaw": True}}, {ACTIONS[0]: {"unlisted": True}}, {ACTIONS[0]: {"no_unfixed_critical_flaw": "yes"}}],
)
def test_constraint_results_must_name_real_actions_and_constraints(env: dict, bad: dict) -> None:
    with pytest.raises(ap.s16.Stop, match="constraint_results"):
        ap.validate(_scores(constraint_results=bad))


def test_register_refuses_a_disposition_other_than_accept_or_reject(env: dict) -> None:
    ap.decide(_write(env), tag="t1")
    env["cli"].calls.clear()
    with pytest.raises(ap.s16.Stop, match="accept or reject"):
        ap.register("ADP-TEST", tag="t1", by="Menno", disposition="revise", summary="needs work")
    assert env["cli"].calls == []


def test_register_refuses_a_store_outside_the_repository(env: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    ap.decide(_write(env), tag="t1")
    env["cli"].calls.clear()
    monkeypatch.setenv("AGENT_LEARNING_LOCAL_STORE_DIR", str(env["tmp"] / "elsewhere"))
    monkeypatch.setattr(ap.s16, "_store_announced", False)
    with pytest.raises(ap.s16.Stop, match="outside this repository"):
        ap.register("ADP-TEST", tag="t1", by="Menno", disposition="accept", summary="approved")
    assert env["cli"].calls == []
