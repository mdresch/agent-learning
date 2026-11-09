"""Governance baseline: approved ADRs, BRDs, FDDs and user stories change only through Stage 16.

ADR-007 freezes an approved document. Any change to it (a correction, a clarification, an amendment, a lifecycle move) is
classified by ``classify-diff-type``, accepted by a human, and recorded. ``tests/test_governance_baseline.py`` enforces it:
it fails when an approved document differs from the fingerprint in ``tests/governance_baseline.json``.

    uv run python scripts/governance_baseline.py --init     first time: fingerprint every approved document as it stands
    uv run python scripts/governance_baseline.py            after a Stage 16 change: re-fingerprint what changed

The second command is the only sanctioned way to update the manifest. For each changed document it refuses unless the document's
Status line (or an ADR's Amendment Log row) records the change as

    Amended <date> at Stage 16 ... episode `<8 hex>`...

and that episode exists in the local store, was accepted, and names this document. For a document that became approved it needs
the approval episode in its Status and checks it the same way. Epic files ignore ``**Status:**`` lines in the fingerprint,
because implementing a story updates them as progress, not as an amendment.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections.abc import Callable
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tests" / "governance_baseline.json"
AGENT_ID = "agent-learning-governance"

# family -> (glob, the policy whose episode approved a document of that family)
FAMILIES = {
    "adr": ("docs/adr/ADR-*.md", "approve-adr"),
    "brd": ("docs/project-docs/Business-Requirements/BRD-*.md", "approve-brd"),
    "fdd": ("docs/project-docs/Functional-Design/FDD-*.md", "approve-fdd"),
    "story": ("docs/user-stories/epic-*.md", "approve-user-stories"),
}
GOVERNED = {"approved", "accepted", "completed", "superseded", "in"}
EPISODE = re.compile(r"episode `([0-9a-f]{8})")
AMENDMENT = re.compile(r"[Aa]mended (\d{4}-\d{2}-\d{2}) at Stage 16\b.*?episode `([0-9a-f]{8})")

Verify = Callable[
    [str, str, str | None], str | None
]  # (task_id, episode prefix, document name) -> error or None


def normalize(text: str) -> str:
    return text.replace("\r\n", "\n")


def read(path: Path) -> str:
    return normalize(path.read_text(encoding="utf-8"))


def status_line(family: str, text: str) -> str:
    if family == "adr":
        m = re.search(r"^##\s*\d*\.?\s*Status\s*\n+\s*(.+)", text, re.MULTILINE)
    else:
        m = re.search(r"^\*\*Status:\*\*\s*(.+)", text, re.MULTILINE)
    return m.group(1) if m else ""


def status_word(family: str, text: str) -> str:
    m = re.match(r"\W*([A-Za-z]+)", status_line(family, text))
    return m.group(1).lower() if m else ""


def fingerprint(family: str, text: str) -> str:
    lines = normalize(text).split("\n")
    if family == "story":
        lines = [line for line in lines if not line.startswith("**Status:**")]
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def amendments(text: str) -> list[dict]:
    seen: dict[str, dict] = {}
    for line in text.split("\n"):
        for m in AMENDMENT.finditer(line):
            seen.setdefault(m.group(2), {"date": m.group(1), "episode": m.group(2), "stage": 16})
    return list(seen.values())


def approval_episode(family: str, text: str) -> str | None:
    m = EPISODE.search(status_line(family, text))
    return m.group(1) if m else None


def discover(root: Path) -> dict[str, str]:
    found: dict[str, str] = {}
    for family, (pattern, _) in FAMILIES.items():
        for path in sorted(root.glob(pattern)):
            found[path.relative_to(root).as_posix()] = family
    return found


def find_problems(manifest: dict, root: Path) -> list[str]:
    """What the test asserts is empty."""
    docs: dict[str, dict] = manifest["documents"]
    problems: list[str] = []
    discovered = discover(root)
    for rel, family in discovered.items():
        text = read(root / rel)
        word = status_word(family, text)
        entry = docs.get(rel)
        if entry is None:
            if word in GOVERNED:
                problems.append(
                    f"{rel} is {word} but is not in the governance baseline. Record its approval episode in its Status, "
                    "then run scripts/governance_baseline.py."
                )
            continue
        if word not in GOVERNED:
            problems.append(
                f"{rel} was {entry['status']} and now reads {word!r}: an unrecorded lifecycle change."
            )
            continue
        if fingerprint(family, text) != entry["sha256"]:
            problems.append(
                f"{rel} is an approved document and has changed since it was baselined. Changes to it go through Stage 16: "
                "classify the diff (classify-diff-type), have it accepted, record `Amended <date> at Stage 16 ... episode `<id>`` "
                "in its Status, then run scripts/governance_baseline.py."
            )
        for item in entry["amendments"]:
            if item["episode"] not in text:
                problems.append(f"{rel} no longer records its Stage 16 amendment, episode {item['episode']}.")
    for rel in sorted(set(docs) - set(discovered)):
        problems.append(
            f"{rel} is in the governance baseline but the file is gone. Removing or renaming it is a Stage 16 change."
        )
    return problems


def refresh(
    manifest: dict | None, root: Path, verify: Verify | None, init: bool = False
) -> tuple[dict, list[str], list[str]]:
    """Return (new manifest, errors, notes). Writes nothing."""
    docs: dict[str, dict] = {} if init or manifest is None else json.loads(json.dumps(manifest["documents"]))
    errors: list[str] = []
    notes: list[str] = []
    for rel, family in discover(root).items():
        text = read(root / rel)
        word = status_word(family, text)
        digest = fingerprint(family, text)
        found = amendments(text)
        entry = docs.get(rel)
        if init:
            if word in GOVERNED:
                docs[rel] = {
                    "family": family,
                    "status": word,
                    "sha256": digest,
                    "approval_episode": approval_episode(family, text),
                    "amendments": found,
                }
            continue
        if entry is None:
            if word not in GOVERNED:
                continue
            episode = approval_episode(family, text)
            if episode is None:
                errors.append(f"{rel} is {word} but its Status cites no approval episode.")
                continue
            error = verify(FAMILIES[family][1], episode, None) if verify else None
            if error:
                errors.append(f"{rel}: {error}")
                continue
            docs[rel] = {
                "family": family,
                "status": word,
                "sha256": digest,
                "approval_episode": episode,
                "amendments": found,
            }
            notes.append(f"added {rel} (approval episode {episode})")
            continue
        if word not in GOVERNED:
            errors.append(f"{rel} was {entry['status']} and now reads {word!r}.")
            continue
        if digest == entry["sha256"]:
            continue
        known = {a["episode"] for a in entry["amendments"]}
        new = [a for a in found if a["episode"] not in known]
        if not new:
            errors.append(
                f"{rel} changed, but its Status records no new `Amended <date> at Stage 16 ... episode `<id>``."
            )
            continue
        bad = [e for a in new if verify and (e := verify("classify-diff-type", a["episode"], Path(rel).name))]
        if bad:
            errors.extend(f"{rel}: {b}" for b in bad)
            continue
        entry.update({"status": word, "sha256": digest, "amendments": entry["amendments"] + new})
        notes.append(f"re-fingerprinted {rel} (amendment episode {', '.join(a['episode'] for a in new)})")
    out = {
        "_comment": (
            "Fingerprint of every approved ADR, BRD, FDD and epic file. A change to one goes through Stage 16 (ADR-007) and is "
            "recorded in its Status as `Amended <date> at Stage 16 ... episode `<id>``. Update this file only with "
            "scripts/governance_baseline.py, which checks that record against the episode store."
        ),
        "baseline_date": (manifest or {}).get("baseline_date") or date.today().isoformat(),  # noqa: DTZ011
        "documents": dict(sorted(docs.items())),
    }
    return out, errors, notes


def store_verifier() -> Verify:
    """Check an episode in the local LearningStore: it exists, was accepted, and (for amendments) names the document."""
    cache: dict[str, list[dict]] = {}

    def verify(task_id: str, prefix: str, target: str | None) -> str | None:
        if task_id not in cache:
            run = subprocess.run(
                [
                    "uv",
                    "run",
                    "agent-learn-ext",
                    "task-episodes-list",
                    AGENT_ID,
                    "--task-id",
                    task_id,
                    "--limit",
                    "500",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            if run.returncode != 0:
                err_detail = run.stderr.strip() or f"exit code {run.returncode}"
                return f"failed to query store for task {task_id}: {err_detail}"
            out = run.stdout
            if "[" in out:
                try:
                    parsed_rows = json.loads(out[out.index("[") :])
                    cache[task_id] = [
                        row.get("episode", row) if isinstance(row, dict) else row
                        for row in parsed_rows
                    ]
                except Exception as exc:
                    return f"failed to parse store episodes for task {task_id}: {exc}"
            else:
                cache[task_id] = []
        match = [e for e in cache[task_id] if e["id"].startswith(prefix)]
        if not match:
            return f"no {task_id} episode {prefix} in the local store"
        ep = match[0]
        if ep.get("metadata", {}).get("decision_disposition") != "accepted":
            return f"{task_id} episode {prefix} was not accepted"
        if target is not None and ep.get("target") != target:
            return f"{task_id} episode {prefix} names {ep.get('target')!r}, not {target!r}"
        return None

    return verify


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="fingerprint every approved document as it stands (first time only)",
    )
    args = parser.parse_args()
    manifest = (
        json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.is_file() and not args.init else None
    )
    if not args.init and manifest is None:
        print("No baseline yet: run with --init once.")
        return 2
    new, errors, notes = refresh(manifest, ROOT, None if args.init else store_verifier(), init=args.init)
    if errors:
        print("Not updated. These need a Stage 16 record first:")
        print("\n".join(f"  - {e}" for e in errors))
        return 1
    MANIFEST.write_text(json.dumps(new, indent=2) + "\n", encoding="utf-8")
    print(f"{len(new['documents'])} documents in the baseline.", *notes, sep="\n  ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
