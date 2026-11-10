#!/usr/bin/env python3
"""Stage 16 for an approved governance document: measure the edit, classify it, record the human's acceptance.

ADR-007 freezes an approved ADR, BRD, FDD or user story. A change to one is classified by ``classify-diff-type``, accepted
by a human, and recorded in the document. This script runs those steps with the real pipeline, so each change is handled
the same way and leaves its evidence in the repository. It never accepts on anyone's behalf.

    uv run python scripts/stage16_amend.py propose <document>
        Edit the document first (uncommitted). Measures the edit against HEAD, builds the decision frame from the
        measurements, runs ``agent-learn-ext task-policy-decide`` and saves frame, result and measurements under
        docs/policy-shapes/. Prints the classification. Registers nothing.

    uv run python scripts/stage16_amend.py accept <document> --by "<name>" --summary "<what changed>"
        Only after you have read the classification and agree. Refuses if the document changed since ``propose``.
        Runs ``task-policy-adjudicate --disposition accept``, registers the episode, records
        ``Amended <date> at Stage 16 ... episode `<id>``` in the document's Status, and refreshes the governance baseline.

If you disagree with the classification, do not run ``accept``: change the edit and run ``propose`` again, or revert it.

The scoring rubric (IDEAL below) is a fixed table, the same for every document: for each action, the value on each criterion
for which that action is the right answer. The measurements come from the diff, never from the author's opinion of it.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import uuid
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENT_ID = "agent-learning-governance"
CLASSIFY = "classify-diff-type"
SHAPES = ROOT / "docs" / "policy-shapes"
CLI = ["uv", "run", "agent-learn-ext"]

ACTIONS = [
    "new_superseding_adr",
    "amendment_log_entry",
    "correction_note",
    "clarification_section",
    "provenance_note",
    "pending_supersession_note",
    "supersession_update",
]
LIFECYCLE = {"pending_supersession_note", "supersession_update"}
CRITERIA = [
    ("semantic_scope_impact", 0.40, "Scope of semantic impact"),
    ("architectural_intent_shift", 0.35, "Shift in architectural intent"),
    ("downstream_contract_footprint", 0.15, "Impact on downstream contracts"),
    ("textual_cosmetic_ratio", 0.10, "Ratio of structural to cosmetic diff"),
]
# Per action, the value on each criterion (scope, intent, footprint, substantive) for which it is the right answer.
IDEAL = {
    "amendment_log_entry": (0.30, 0.10, 0.50, 0.80),
    "correction_note": (0.05, 0.05, 0.10, 0.10),
    "clarification_section": (0.15, 0.10, 0.25, 0.40),
    "provenance_note": (0.00, 0.00, 0.05, 0.05),
    "new_superseding_adr": (0.90, 0.90, 0.80, 0.90),
}
NORMATIVE = re.compile(r"\b(must|shall)\b|\$?AC_\d|BRU-\d|Design \d")
NORMATIVE_ID = re.compile(r"\bAC_\d+\b|\bBRU-\d+-\d+\b|\bDesign \d+\b")
TERM = re.compile(r"`([^`]{3,60})`|\b(ADR-\d+|BRD-\d+|FDD-\d+)\b")
AMENDMENT = re.compile(r"[Aa]mended \d{4}-\d{2}-\d{2} at Stage 16\b")
CHANGED_RATIO = 0.15  # below this a changed line is a wording tweak, not a change to a requirement
GOVERNED_DIRS = ("docs/adr", "docs/project-docs", "docs/user-stories")


def load_baseline():
    baseline_path = ROOT / "scripts" / "governance_baseline.py"
    if not baseline_path.is_file():
        raise RuntimeError(f"governance_baseline.py not found at {baseline_path}")
    spec = importlib.util.spec_from_file_location("governance_baseline", baseline_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load spec for governance_baseline from {baseline_path}")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        raise RuntimeError(f"Failed to execute governance_baseline module: {exc}") from exc
    return module


_gb = None


def get_gb():
    global _gb
    if _gb is None:
        _gb = load_baseline()
    return _gb


def __getattr__(name: str):
    if name == "gb":
        return get_gb()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


class Stop(Exception):
    """A rule was not met; nothing further is done."""


def normalize(text: str) -> str:
    return text.replace("\r\n", "\n")


def git_head(rel: str) -> str:
    run = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=ROOT, capture_output=True, check=False)
    if run.returncode != 0:
        raise Stop(f"{rel} is not in HEAD. Commit the approved version first, then edit it.")
    return normalize(run.stdout.decode("utf-8"))  # utf-8 explicitly: the Windows default codec fakes changes


def head_commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


def digest(text: str) -> str:
    return hashlib.sha256(normalize(text).encode("utf-8")).hexdigest()


# --- measurement ------------------------------------------------------------------------------------------------------


def downstream_refs(rel: str, ids: set[str]) -> int:
    """Other governed documents that mention an identifier the edit touched."""
    if not ids:
        return 0
    count = 0
    for folder in GOVERNED_DIRS:
        for path in (ROOT / folder).rglob("*.md"):
            other = path.relative_to(ROOT).as_posix()
            if other == rel:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if any(i in text for i in ids):
                count += 1
    return count


def measure(rel: str, base: str, cand: str) -> dict:
    diff = list(difflib.unified_diff(base.splitlines(), cand.splitlines(), lineterm="", n=0))
    removed = [line[1:] for line in diff if line.startswith("-") and not line.startswith("---")]
    added = [line[1:] for line in diff if line.startswith("+") and not line.startswith("+++")]
    removed_text, added_text = " ".join(removed), " ".join(added)
    # Terms the removed text carried (identifiers in backticks, ADR/BRD/FDD references): do they survive in the added text?
    terms = {m.group(1) or m.group(2) for line in removed for m in TERM.finditer(line)}
    kept = {t for t in terms if t.lower() in added_text.lower()}
    goal_preserved = (len(kept) / len(terms) >= 0.8) if terms else True
    inverted = bool(re.search(r"\b(must|shall)\b(?! not)", removed_text)) and bool(
        re.search(r"\b(must|shall) not\b|\bnever\b", added_text)
    )
    ratio = difflib.SequenceMatcher(None, removed_text, added_text).ratio() if removed and added else 0.0
    change_ratio = 1 - ratio if (removed and added) else (1.0 if (removed or added) else 0.0)
    normative = any(NORMATIVE.search(line) for line in removed + added) and change_ratio >= CHANGED_RATIO
    status_changed = any(re.match(r"\*\*Status:\*\*", line) for line in removed + added)
    ids = {m.group(0) for line in removed for m in NORMATIVE_ID.finditer(line)}
    refs = downstream_refs(rel, ids)
    return {
        "lines": len(removed) + len(added),
        "terms_removed": len(terms),
        "terms_kept": len(kept),
        "goal_preserved": goal_preserved,
        "requirement_inverted": inverted,
        "normative_touched": normative,
        "status_line_changed": status_changed,
        "downstream_refs": refs,
        "change_ratio": round(change_ratio, 2),
    }


def observed(f: dict) -> tuple[float, float, float, float]:
    scope = (0.25 if f["goal_preserved"] else 0.85) + (0.10 if f["requirement_inverted"] else 0.0)
    if not f["normative_touched"]:
        scope = 0.05
    intent = 0.10 if f["goal_preserved"] else 0.90
    footprint = min(0.9, 0.2 + 0.15 * f["downstream_refs"]) if f["normative_touched"] else 0.10
    substantive = 0.90 if f["normative_touched"] else 0.10
    return scope, intent, footprint, substantive


def build_frame(rel: str, f: dict) -> dict:
    obs = observed(f)
    name = Path(rel).name
    options = []
    for action in ACTIONS:
        evidence = []
        for i, (cid, _, _) in enumerate(CRITERIA):
            if action in LIFECYCLE:
                support = 0.95 if f["status_line_changed"] else 0.02
            elif action in IDEAL:
                support = max(0.02, 1 - abs(obs[i] - IDEAL[action][i]))
            else:
                raise Stop(f"Unknown action {action!r} without an ideal profile")
            evidence.append(
                {
                    "criterion_id": cid,
                    "source": f"measured:{name}:{cid}={obs[i]:.2f}",
                    "support": round(support, 3),
                    "confidence": 0.7 if cid == "downstream_contract_footprint" else 0.9,
                }
            )
        options.append(
            {"action_id": action, "evidence": evidence, "constraint_results": {"valid_format": True}}
        )
    return {
        "task": f"Classify the diff to {rel}",
        "criteria": [{"id": c, "weight": w, "minimum_sources": 1, "description": d} for c, w, d in CRITERIA],
        "options": options,
        "constraints": ["valid_format"],
        "minimum_margin": 0.05,
    }


# --- the real pipeline ------------------------------------------------------------------------------------------------


STORE_VAR = "AGENT_LEARNING_LOCAL_STORE_DIR"
ALLOW_EXTERNAL_STORE = False  # set by --allow-external-store
_store_announced = False


def resolve_store() -> Path:
    """The store the CLI will write to: the variable if set, else the CLI's default, resolved from the repository root."""
    raw = os.environ.get(STORE_VAR) or "data/agent-learning/store"
    path = Path(raw).expanduser()
    return (path if path.is_absolute() else ROOT / path).resolve()


def store_file_count(store: Path) -> int:
    return sum(1 for p in store.rglob("*") if p.is_file()) if store.exists() else 0


def guard_store() -> Path:
    """IMP-062: print the store and its file count; refuse a store outside this repository unless allowed (LL-040)."""
    global _store_announced
    store = resolve_store()
    if not store.is_relative_to(ROOT.resolve()) and not ALLOW_EXTERNAL_STORE:
        raise Stop(
            f"The governance store {store} is outside this repository ({ROOT}). Set {STORE_VAR} to "
            f"{ROOT / 'data' / 'agent-learning' / 'store'}, or pass --allow-external-store if this is intended."
        )
    if not _store_announced:
        print(f"Governance store: {store} ({store_file_count(store)} files before)")
        _store_announced = True
    return store


def agent_learn(*args: str) -> str:
    store = guard_store()
    run = subprocess.run(
        [*CLI, *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        env={**os.environ, STORE_VAR: str(store)},
    )
    if run.returncode != 0:
        raise Stop(f"`agent-learn-ext {' '.join(args)}` failed:\n{run.stdout}{run.stderr}")
    return run.stdout


def parse_json(text: str) -> dict:
    if "{" not in text:
        raise Stop(f"No JSON object found in output: {text.strip()[:200]}")
    try:
        return json.loads(text[text.index("{") :])
    except (ValueError, json.JSONDecodeError) as exc:
        raise Stop(f"Failed to parse JSON output: {exc}") from exc


def slug(rel: str) -> str:
    stem = Path(rel).stem.lower()
    m = re.match(r"(adr|brd|fdd)-(\d+)", stem)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    m = re.match(r"epic-(\d+)", stem)
    return f"epic-{m.group(1)}" if m else re.sub(r"[^a-z0-9]+", "-", stem)[:40]


def resolve(doc: str) -> str:
    path = (ROOT / doc) if not Path(doc).is_absolute() else Path(doc)
    rel = path.resolve().relative_to(ROOT).as_posix()
    gb = get_gb()
    manifest = json.loads(gb.MANIFEST.read_text(encoding="utf-8"))
    if rel not in manifest["documents"]:
        raise Stop(
            f"{rel} is not in the governance baseline. Only an approved ADR, BRD, FDD or epic is amended through Stage 16."
        )
    return rel


def paths_for(rel: str, tag: str) -> dict[str, Path]:
    base = f"amend-{slug(rel)}-{tag}"
    return {
        "frame": SHAPES / "decision-frames" / f"{base}.json",
        "result": SHAPES / "results" / f"{base}-decision-result.json",
        "adjudicated": SHAPES / "results" / f"{base}-adjudication-result.json",
        "episode": SHAPES / "episodes" / f"{base}-episode.json",
        "measure": SHAPES / "results" / f"{base}-measurements.json",
    }


def pending(rel: str) -> Path | None:
    """The newest measurements file for this document that has not been accepted yet."""
    found = sorted((SHAPES / "results").glob(f"amend-{slug(rel)}-*-measurements.json"))
    for path in reversed(found):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data["document"] == rel and not data.get("accepted"):
            return path
    return None


def propose(doc: str, tag: str | None) -> int:
    rel = resolve(doc)
    base = git_head(rel)
    cand = normalize((ROOT / rel).read_text(encoding="utf-8"))
    if base == cand:
        raise Stop(f"{rel} is identical to HEAD: there is no edit to classify.")
    gb = get_gb()
    if (
        gb.fingerprint(gb.discover(ROOT)[rel], cand)
        == json.loads(gb.MANIFEST.read_text(encoding="utf-8"))["documents"][rel]["sha256"]
    ):
        raise Stop(f"{rel} matches its baseline: there is no edit to classify.")
    tag = tag or date.today().isoformat()  # noqa: DTZ011
    paths = paths_for(rel, tag)
    if paths["frame"].exists():
        raise Stop(f"{paths['frame'].name} exists. Pass --tag to name this amendment differently.")
    features = measure(rel, base, cand)
    frame = build_frame(rel, features)
    paths["frame"].write_text(json.dumps(frame, indent=2) + "\n", encoding="utf-8")
    result = parse_json(
        agent_learn(
            "task-policy-decide",
            "--agent-id",
            AGENT_ID,
            "--task-id",
            CLASSIFY,
            "--decision-frame",
            str(paths["frame"]),
        )
    )
    paths["result"].write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    ranked = sorted(
        (
            (a["robust_utility"], a["action"]["id"])
            for a in result["assessments"]
            if a.get("robust_utility") is not None
        ),
        reverse=True,
    )
    proposed = (result.get("selected_action") or result.get("proposed_action") or {}).get("id")
    paths["measure"].write_text(
        json.dumps(
            {
                "document": rel,
                "tag": tag,
                "base_commit": head_commit(),
                "candidate_sha256": digest(cand),
                "features": features,
                "observed": [round(x, 2) for x in observed(features)],
                "proposed_action": proposed,
                "accepted": False,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"{rel}")
    print(
        f"  measured: {features['lines']} changed lines, change ratio {features['change_ratio']}, "
        f"terms kept {features['terms_kept']}/{features['terms_removed']}, requirement inverted "
        f"{features['requirement_inverted']}, downstream references {features['downstream_refs']}, "
        f"status line changed {features['status_line_changed']}"
    )
    print(f"  status:   {result['status']}  ({result.get('reason', '')})")
    print(f"  proposed: {proposed}")
    if len(ranked) > 1:
        print(
            "  ranking:  "
            + ", ".join(f"{a} {u:.3f}" for u, a in ranked[:4])
            + f"   margin to runner-up {ranked[0][0] - ranked[1][0]:.3f}"
        )
    print(f"  evidence: {paths['frame'].relative_to(ROOT).as_posix()} (+ result, measurements)")
    print("\nNothing is registered. If you agree with the classification, run:")
    print(
        f'  uv run python scripts/stage16_amend.py accept {rel} --by "<your name>" --summary "<what changed>"'
    )
    if proposed in {"new_superseding_adr", "pending_supersession_note", "supersession_update"}:
        print(
            f"\nNote: {proposed} means this is more than an amendment. The right route may be a new ADR, not this edit."
        )
    return 0


def status_edit(family: str, text: str, record: str) -> str:
    if family == "adr":
        m = re.search(r"^(##\s*\d*\.?\s*Status\s*\n+\s*)(.+)$", text, re.MULTILINE)
    else:
        m = re.search(r"^(\*\*Status:\*\*\s*)(.+)$", text, re.MULTILINE)
    if not m:
        raise Stop("The document has no Status line to carry the amendment record.")
    return text[: m.end()] + " " + record + text[m.end() :]


def accept(doc: str, by: str, summary: str) -> int:
    by = by.strip()
    summary = summary.strip()
    if not by or not summary:
        raise Stop("Both --by and --summary are required and cannot be empty.")
    if "\n" in by or "\r" in by:
        raise Stop("--by must be a single line without newline characters.")
    if "\n" in summary or "\r" in summary:
        raise Stop("--summary must be a single line without newline characters.")
    if len(by) > 100:
        raise Stop(f"--by is too long ({len(by)} > 100 chars).")
    if len(summary) > 200:
        raise Stop(f"--summary is too long ({len(summary)} > 200 chars).")
    rel = resolve(doc)
    pend = pending(rel)
    if pend is None:
        raise Stop(f"No pending proposal for {rel}. Run `propose` first.")
    meas = json.loads(pend.read_text(encoding="utf-8"))
    tag = meas["tag"]
    paths = paths_for(rel, tag)
    path = ROOT / rel
    current = normalize(path.read_text(encoding="utf-8"))
    if digest(current) != meas["candidate_sha256"]:
        raise Stop(
            f"{rel} changed after `propose` classified it. Run `propose` again: the classification applies to that edit only."
        )
    adjudicated = parse_json(
        agent_learn(
            "task-policy-adjudicate",
            "--agent-id",
            AGENT_ID,
            "--task-id",
            CLASSIFY,
            "--decision-result",
            str(paths["result"]),
            "--disposition",
            "accept",
        )
    )
    paths["adjudicated"].write_text(json.dumps(adjudicated, indent=2) + "\n", encoding="utf-8")
    selected = adjudicated["selected_action"]["id"]
    best = next((a for a in adjudicated["assessments"] if a["action"]["id"] == selected), None)
    if best is None:
        raise Stop(f"Selected action {selected!r} was not found in adjudicated assessments.")
    utils = sorted(
        (a["robust_utility"] for a in adjudicated["assessments"] if a.get("robust_utility") is not None),
        reverse=True,
    )
    f = meas["features"]
    today = date.today().isoformat()  # noqa: DTZ011
    episode = {
        "id": str(uuid.uuid4()),
        "agent_id": AGENT_ID,
        "task_id": CLASSIFY,
        "user_input": f"Classify the diff to {Path(rel).name} under Stage 16: {summary}",
        "assistant_output": f"{selected}: robust utility {best['robust_utility']:.3f}",
        "intent_summary": summary,
        "action_type": "recommendation",
        "action_name": selected.replace("_", " ").capitalize(),
        "target": Path(rel).name,
        "input_summary": (
            f"Candidate diff of {rel} against HEAD {meas['base_commit']}: {f['lines']} changed lines, change ratio "
            f"{f['change_ratio']}. Gate frame built from measurements of the diff by scripts/stage16_amend.py "
            f"(terms kept {f['terms_kept']}/{f['terms_removed']}, requirement inverted {f['requirement_inverted']}, "
            f"downstream references {f['downstream_refs']}, status line changed {f['status_line_changed']})."
        ),
        "expected_outcome": f"{by} explicit ACCEPT of this classification",
        "execution_status": "completed",
        "result_summary": (
            f"Accepted by {by}, {today} (Stage 16 {CLASSIFY}), prospectively at the time of acceptance; not backdated."
        ),
        "policy_id": adjudicated["policy_id"],
        "policy_version": adjudicated["policy_version"],
        "action_id": selected,
        "metadata": {
            "feedback_status": "adjudicated",
            "decision_disposition": "accepted",
            "selection_basis": "bayesian_decision",
            "correct_action_id": selected,
            "task_completed": True,
            "robust_utility": best["robust_utility"],
            "expected_utility": best.get("expected_utility"),
            "decision_margin": round(utils[0] - utils[1], 4) if len(utils) > 1 else None,
            "artifact_commit": meas["base_commit"],
            "stage": 16,
            "amendment": summary,
        },
    }
    paths["episode"].write_text(json.dumps(episode, indent=2) + "\n", encoding="utf-8")
    agent_learn(
        "task-episode-register",
        "--agent-id",
        AGENT_ID,
        "--task-id",
        CLASSIFY,
        "--episode",
        str(paths["episode"]),
        "--decision-result",
        str(paths["adjudicated"]),
    )
    record = (
        f"Amended {today} at Stage 16: {summary}, classified `{selected}` "
        f"(robust utility {best['robust_utility']:.3f}, episode `{episode['id'][:8]}...`) and accepted by {by}."
    )
    gb = get_gb()
    updated = status_edit(gb.discover(ROOT)[rel], current, record)
    if b"\r\n" in path.read_bytes():  # keep the file's own line endings
        updated = updated.replace("\n", "\r\n")
    path.write_bytes(updated.encode("utf-8"))
    meas["accepted"] = True
    meas["episode"] = episode["id"][:8]
    pend.write_text(json.dumps(meas, indent=2) + "\n", encoding="utf-8")
    gb = get_gb()
    manifest = json.loads(gb.MANIFEST.read_text(encoding="utf-8"))
    new, errors, notes = gb.refresh(manifest, ROOT, gb.store_verifier())
    if errors:
        raise Stop("The baseline was not refreshed:\n  " + "\n  ".join(errors))
    gb.MANIFEST.write_text(json.dumps(new, indent=2) + "\n", encoding="utf-8")
    print(f"Recorded: {selected}, episode {episode['id'][:8]}, accepted by {by}.")
    print(*notes, sep="\n  ")
    print(f"Evidence: {paths['frame'].relative_to(ROOT).as_posix()} and the matching result/episode files.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("propose", help="measure the edit, classify it, register nothing")
    p.add_argument("document")
    p.add_argument("--tag", help="name for this amendment's evidence files (default: today's date)")
    a = sub.add_parser("accept", help="record the human's acceptance and refresh the baseline")
    a.add_argument("document")
    a.add_argument("--by", required=True, help="the human who accepts the classification")
    a.add_argument("--summary", required=True, help="what changed, in one line")
    parser.add_argument(
        "--allow-external-store", action="store_true", help=f"allow {STORE_VAR} to point outside this repository"
    )
    args = parser.parse_args()
    global ALLOW_EXTERNAL_STORE
    ALLOW_EXTERNAL_STORE = args.allow_external_store
    try:
        code = propose(args.document, args.tag) if args.command == "propose" else accept(args.document, args.by, args.summary)
        if _store_announced:
            store = resolve_store()
            print(f"Governance store: {store} ({store_file_count(store)} files after)")
        return code
    except Stop as e:
        print(f"Stopped: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
