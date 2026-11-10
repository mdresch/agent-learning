#!/usr/bin/env python3
"""One command for an approval run: frame, decide, compare, then register on request (IMP-007).

Approving an ADR, an FDD, a plan or a story took a frame builder, a decision, a comparison script, an adjudication and an
episode builder each time, and one run checked the wrong store (LL-040). This script runs those steps with the real
pipeline and leaves the same evidence in ``docs/policy-shapes/``. It never chooses the disposition: the human does.

    uv run python scripts/approve.py decide <scores.json> [--tag <tag>]
        Prints the resolved store and its file count first, and refuses a store outside this repository. Builds the
        decision frame from the scores, runs ``task-policy-decide``, compares with the previous result of the same
        subject when there is one, and prints the ranking. Registers nothing.

    uv run python scripts/approve.py register <subject> --by "<name>" --disposition accept|reject --summary "<one line>"
        Only after you have read the decision. Refuses if the frame changed since ``decide``. Runs
        ``task-policy-adjudicate``, then registers the episode. An approval that was only requested to be revised is not
        registered: change the scores and run ``decide`` again.

The scores file is JSON. Evidence supports are assessments (the assessor's reading), not measurements, and the episode says so:

    {"task_id": "approve-adaptation-plan", "subject": "ADP-20261110-002", "task": "Approve, reject or request revision of ...",
     "criteria": [{"id": "validation_and_rollback", "weight": 1.0, "description": "..."}],
     "options": {"approve_adaptation_plan": {"validation_and_rollback": {"support": 0.9, "confidence": 0.85, "source": "..."}}, ...},
     "constraints": ["no_unfixed_critical_flaw"]}

Every action of ``docs/policy-shapes/<task_id>.actions.json`` needs an option, and every option needs every criterion.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import uuid
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHAPES = ROOT / "docs" / "policy-shapes"
AGENT_ID = "agent-learning-governance"


def _load_stage16():
    spec = importlib.util.spec_from_file_location("stage16_amend", ROOT / "scripts" / "stage16_amend.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# The store guard (IMP-062) and the CLI wrapper are stage16_amend's: one check, shared, not copied.
s16 = _load_stage16()


def agent_learn(*args: str) -> str:
    return s16.agent_learn(*args)


def _parse_json(text: str) -> dict:
    return s16.parse_json(text)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _task_actions(task_id: str) -> list[str]:
    path = SHAPES / f"{task_id}.actions.json"
    if not path.is_file():
        raise s16.Stop(f"{path.name} not found: {task_id} is not a task with a recorded action list.")
    return [a["id"] for a in json.loads(path.read_text(encoding="utf-8"))]


# --- the frame ---------------------------------------------------------------------------------------------------


def validate(scores: dict) -> None:
    for key in ("task_id", "subject", "task", "criteria", "options"):
        if not scores.get(key):
            raise s16.Stop(f"The scores need a non-empty {key!r}.")
    actions = _task_actions(scores["task_id"])
    criteria = scores["criteria"]
    ids = [c.get("id") for c in criteria]
    if not all(ids) or len(set(ids)) != len(ids):
        raise s16.Stop("Every criterion needs a unique id.")
    for c in criteria:
        if not isinstance(c.get("weight"), (int, float)) or c["weight"] <= 0:
            raise s16.Stop(f"Criterion {c.get('id')!r}: the weight must be a positive number.")
    options = scores["options"]
    for action in options:
        if action not in actions:
            raise s16.Stop(f"{action!r} is not an action of {scores['task_id']} ({', '.join(actions)}).")
    for action in actions:
        if action not in options:
            raise s16.Stop(f"The option for {action!r} is missing: every action of {scores['task_id']} needs one.")
        for cid in ids:
            ev = options[action].get(cid)
            if ev is None:
                raise s16.Stop(f"{action}: no evidence for criterion {cid!r}.")
            for field in ("support", "confidence"):
                if not isinstance(ev.get(field), (int, float)) or not 0 <= ev[field] <= 1:
                    raise s16.Stop(f"{action} / {cid}: {field} must be a number between 0 and 1.")
            if not ev.get("source"):
                raise s16.Stop(f"{action} / {cid}: the evidence needs a source.")


def build_frame(scores: dict) -> dict:
    constraints = scores.get("constraints") or ["no_unfixed_critical_flaw"]
    ids = [c["id"] for c in scores["criteria"]]
    return {
        "task": scores["task"],
        "criteria": [
            {"id": c["id"], "weight": c["weight"], "minimum_sources": 1, "description": c.get("description", "")}
            for c in scores["criteria"]
        ],
        "options": [
            {
                "action_id": action,
                "evidence": [
                    {
                        "criterion_id": cid,
                        "source": ev[cid]["source"],
                        "support": ev[cid]["support"],
                        "confidence": ev[cid]["confidence"],
                    }
                    for cid in ids
                ],
                "constraint_results": {name: True for name in constraints},
            }
            for action, ev in scores["options"].items()
        ],
        "constraints": constraints,
        "minimum_margin": 0.05,
        "uncertainty_penalty": 0.10,
        "max_uncertainty": 1.0,
    }


# --- decide ------------------------------------------------------------------------------------------------------


def _paths(subject: str, tag: str) -> dict[str, Path]:
    base = f"{subject}-{tag}"
    return {
        "frame": SHAPES / "decision-frames" / f"{base}-approval.json",
        "result": SHAPES / "results" / f"{base}-decision-result.json",
        "comparison": SHAPES / "results" / f"{base}-comparison.json",
        "adjudicated": SHAPES / "results" / f"{base}-adjudication-result.json",
        "state": SHAPES / "results" / f"{base}-approval-state.json",
        "episode": SHAPES / "episodes" / f"{base}-episode.json",
    }


def _ranking(result: dict) -> list[tuple[float, str]]:
    rows = [(a["robust_utility"], a["action"]["id"]) for a in result["assessments"] if a.get("robust_utility") is not None]
    return sorted(rows, reverse=True)


def decide(scores_path: Path | str, tag: str | None = None) -> int:
    scores = json.loads(Path(scores_path).read_text(encoding="utf-8"))
    validate(scores)
    s16.guard_store()
    subject, task_id = scores["subject"], scores["task_id"]
    tag = tag or date.today().isoformat()  # noqa: DTZ011
    paths = _paths(subject, tag)
    if paths["frame"].exists() or paths["state"].exists():
        raise s16.Stop(f"{paths['frame'].name} exists. Pass --tag to name this run differently; earlier runs are evidence.")

    previous = sorted(
        p for p in (SHAPES / "results").glob(f"{subject}-*-decision-result.json") if p.name < paths["result"].name
    )
    _write(paths["frame"], build_frame(scores))
    result = _parse_json(
        agent_learn("task-policy-decide", "--agent-id", AGENT_ID, "--task-id", task_id, "--decision-frame", str(paths["frame"]))
    )
    _write(paths["result"], result)
    _write(
        paths["state"],
        {
            "task_id": task_id,
            "subject": subject,
            "tag": tag,
            "frame_sha256": _digest(paths["frame"]),
            "registered": False,
            "episode": None,
        },
    )

    ranking = _ranking(result)
    print(f"\n{subject}: status {result.get('status')}; proposed {(result.get('proposed_action') or {}).get('id')}")
    print("  ranking: " + ", ".join(f"{a} {u:.3f}" for u, a in ranking[:4]))
    if len(ranking) > 1:
        print(f"  margin to runner-up {ranking[0][0] - ranking[1][0]:.3f}")
    if previous:
        comparison = _parse_json(
            agent_learn("task-policy-compare", "--sequence", str(previous[-1]), str(paths["result"]))
        )
        _write(paths["comparison"], comparison)
        print(f"  compared with {previous[-1].name}: {comparison.get('classification')}: {comparison.get('classification_reason')}")
    print(f"  evidence: {paths['frame'].relative_to(ROOT).as_posix()} (+ result)")
    print("\nNothing is registered. If you decide, run:")
    print(f'  uv run python scripts/approve.py register {subject} --tag {tag} --by "<your name>" --disposition accept|reject --summary "<one line>"')
    return 0


# --- register ----------------------------------------------------------------------------------------------------


def _pending(subject: str, tag: str | None) -> Path | None:
    states = sorted((SHAPES / "results").glob(f"{subject}-*-approval-state.json"), reverse=True)
    for path in states:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not data["registered"] and (tag is None or data["tag"] == tag):
            return path
    return None


def register(subject: str, tag: str | None, by: str, disposition: str, summary: str) -> int:
    by, summary = by.strip(), summary.strip()
    if not by:
        raise s16.Stop("--by is required: the human who decides.")
    if not summary:
        raise s16.Stop("--summary is required and cannot be empty.")
    if "\n" in by or "\r" in by:
        raise s16.Stop("--by must be a single line.")
    if "\n" in summary or "\r" in summary:
        raise s16.Stop("--summary must be a single line.")
    if len(by) > 100:
        raise s16.Stop(f"--by is too long ({len(by)} > 100 chars).")
    if len(summary) > 200:
        raise s16.Stop(f"--summary is too long ({len(summary)} > 200 chars).")
    if disposition not in {"accept", "reject"}:
        raise s16.Stop("The disposition is accept or reject. To ask for a revision, change the scores and run decide again.")
    state_path = _pending(subject, tag)
    if state_path is None:
        raise s16.Stop(f"No pending decision for {subject}. Run `decide` first (a registered one cannot be registered twice).")
    state = json.loads(state_path.read_text(encoding="utf-8"))
    paths = _paths(subject, state["tag"])
    if _digest(paths["frame"]) != state["frame_sha256"]:
        raise s16.Stop(f"{paths['frame'].name} changed after `decide` ran. Run `decide` again: the decision applies to that frame only.")
    s16.guard_store()

    task_id = state["task_id"]
    adjudicated = _parse_json(
        agent_learn(
            "task-policy-adjudicate", "--agent-id", AGENT_ID, "--task-id", task_id,
            "--decision-result", str(paths["result"]), "--disposition", disposition,
        )
    )
    _write(paths["adjudicated"], adjudicated)
    chosen = (adjudicated.get("selected_action") or adjudicated.get("proposed_action") or {}).get("id")
    if not chosen:
        raise s16.Stop("The adjudication named no action; nothing was registered.")
    best = next((a for a in adjudicated["assessments"] if a["action"]["id"] == chosen), {})
    utils = [u for u, _ in _ranking(adjudicated)]
    today = date.today().isoformat()  # noqa: DTZ011
    verb = "Accepted" if disposition == "accept" else "Rejected"
    episode = {
        "id": str(uuid.uuid4()),
        "agent_id": AGENT_ID,
        "task_id": task_id,
        "user_input": f"{task_id} for {subject}: {summary}",
        "assistant_output": f"{chosen}: robust utility {best.get('robust_utility', float('nan')):.3f}",
        "intent_summary": summary,
        "action_type": "recommendation",
        "action_name": chosen.replace("_", " ").capitalize(),
        "target": subject,
        "input_summary": (
            f"Decision frame {paths['frame'].relative_to(ROOT).as_posix()}: the evidence supports are assessed by the assessor "
            "from the documents, not measured."
        ),
        "expected_outcome": f"{by} explicit {disposition}",
        "execution_status": "completed",
        "result_summary": f"{verb} by {by}, {today} ({task_id}), prospectively at the time of the decision; not backdated.",
        "policy_id": adjudicated.get("policy_id"),
        "policy_version": adjudicated.get("policy_version"),
        "action_id": chosen,
        "metadata": {
            "feedback_status": "adjudicated",
            "decision_disposition": "accepted" if disposition == "accept" else "rejected",
            "selection_basis": adjudicated.get("selection_basis", "bayesian_decision"),
            "correct_action_id": chosen,
            "task_completed": True,
            "robust_utility": best.get("robust_utility"),
            "expected_utility": best.get("expected_utility"),
            "decision_margin": round(utils[0] - utils[1], 4) if len(utils) > 1 else None,
            "subject": subject,
            "frame_sha256": state["frame_sha256"],
        },
    }
    _write(paths["episode"], episode)
    agent_learn(
        "task-episode-register", "--agent-id", AGENT_ID, "--task-id", task_id,
        "--episode", str(paths["episode"]), "--decision-result", str(paths["adjudicated"]),
    )
    state.update(registered=True, episode=episode["id"])
    _write(state_path, state)
    print(f"Recorded: {chosen}, episode {episode['id'][:8]}, {verb.lower()} by {by}.")
    return 0


# --- command line ------------------------------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--allow-external-store", action="store_true", help="allow the store to be outside this repository")
    sub = parser.add_subparsers(dest="command", required=True)
    d = sub.add_parser("decide", parents=[common], help="build the frame, decide, compare; register nothing")
    d.add_argument("scores")
    d.add_argument("--tag", help="name for this run's evidence files (default: today's date)")
    r = sub.add_parser("register", parents=[common], help="record the human's decision")
    r.add_argument("subject")
    r.add_argument("--tag", help="the run to register (default: the newest pending one)")
    r.add_argument("--by", required=True, help="the human who decides")
    r.add_argument("--disposition", required=True, help="accept or reject")
    r.add_argument("--summary", required=True, help="what was decided, in one line")
    args = parser.parse_args(argv)
    s16.ALLOW_EXTERNAL_STORE = args.allow_external_store
    try:
        code = (
            decide(args.scores, args.tag)
            if args.command == "decide"
            else register(args.subject, args.tag, args.by, args.disposition, args.summary)
        )
        store = s16.resolve_store()
        print(f"Governance store: {store} ({s16.store_file_count(store)} files after)")
        return code
    except s16.Stop as err:
        print(f"Stopped: {err}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
