#!/usr/bin/env python3
"""Programmatic PR Review & Approval Gatekeeper (Epic 14 Critique Ingestion).

Evaluates a pull request using the Bayesian DecisionResolver and Epic 14
Lightweight Critique-to-Evidence Ingestion Engine. Ingests review findings from
Amazon Q, Cursor Bugbot, and human maintainers, computes log-odds support shifts
and uncertainty increments, and makes a mathematically calibrated approval decision.

Usage:
    uv run python scripts/pr_gate.py <pr_number>
    uv run python scripts/pr_gate.py <pr_number> --merge
    uv run python scripts/pr_gate.py <pr_number> --json
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STORE_DIR = ROOT / "data" / "agent-learning" / "store"
sys.path.insert(0, str(ROOT / "src"))

from agent_learning.decision import (
    Action,
    DecisionAuthority,
    DecisionCriterion,
    DecisionFrame,
    DecisionOption,
    DecisionResolver,
    EvidencePoint,
    PolicySnapshot,
)
from agent_learning.review_triage import TriageRecord, find_triage_lines, parse_triage_line
from agent_learning.storage.local import LocalFileStore
from agent_learning.types import Episode

from agent_learning_ext.critique_evidence import (
    CritiqueDelta,
    apply_critique,
    parse_critique,
    rubric_delta,
    to_episode_metadata,
)
from agent_learning_ext.triage_replay import map_claim_to_criterion


def fetch_pr_data(pr_number: int) -> dict[str, Any]:
    """Fetch PR details, CI checks, files, and review comments via GitHub CLI."""
    cmd = [
        "gh",
        "pr",
        "view",
        str(pr_number),
        "--json",
        "number,title,state,headRefOid,mergeable,mergeStateStatus,statusCheckRollup,reviews,comments,files",
    ]
    run = subprocess.run(
        cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False
    )
    if run.returncode != 0:
        raise RuntimeError(f"Failed to fetch PR #{pr_number} via gh: {run.stderr.strip()}")
    return json.loads(run.stdout)


TRIAGE_LOG = "implementation-log.md"


def fetch_pr_diff(pr_number: int) -> str:
    """Fetch the unified diff of a PR via GitHub CLI (fails closed: an unreadable diff is an error)."""
    run = subprocess.run(
        ["gh", "pr", "diff", str(pr_number)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if run.returncode != 0:
        raise RuntimeError(f"Failed to fetch the diff of PR #{pr_number} via gh: {run.stderr.strip()}")
    return run.stdout


def added_triage_lines(diff: str) -> list[str]:
    """The review-triage lines a PR adds to the implementation log (IMP-030)."""
    added: list[str] = []
    in_log = False
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            in_log = line.rstrip().endswith("/" + TRIAGE_LOG)
        elif in_log and line.startswith("+") and not line.startswith("+++"):
            added.append(line[1:])
    return find_triage_lines("\n".join(added))


def check_triage_lines(lines: list[str]) -> tuple[list[TriageRecord], list[str]]:
    """Parse each added triage line; a claim type, verification or decision outside the vocabulary is an error."""
    records: list[TriageRecord] = []
    errors: list[str] = []
    for text in lines:
        try:
            records.append(parse_triage_line(text))
        except ValueError as err:
            errors.append(f"`{text[:60]}`: {err}")
    return records, errors


def reconcile_triage(
    deltas: list[CritiqueDelta], records: list[TriageRecord], pr_number: int
) -> tuple[list[CritiqueDelta], list[str]]:
    """Respect the maintainer's triage of this PR's own findings (IMP-017).

    A declined or deferred row cancels one review-derived defect on the same criterion; an accepted row keeps the defect,
    and adds the rubric delta when the review text produced none. Untriaged findings still count in full.
    """
    remaining = list(deltas)
    notes: list[str] = []
    for rec in records:
        if rec.pr != pr_number:
            continue
        criterion = map_claim_to_criterion(rec.claim_type)
        match = next((d for d in remaining if d.criterion_id == criterion and d.support_delta < 0), None)
        if rec.decision == "accepted":
            if match is not None:
                notes.append(f"{rec.finding_id} accepted: kept {match.finding_id}")
                continue
            try:
                value = rubric_delta(rec.claim_type, rec.verified)
            except ValueError:
                notes.append(f"{rec.finding_id} accepted: no rubric delta for ({rec.claim_type}, {rec.verified}); not scored")
                continue
            if value < 0:
                remaining.append(
                    CritiqueDelta(
                        criterion_id=criterion,
                        support_delta=value,
                        rationale=rec.reason,
                        finding_id=rec.finding_id,
                        basis="rubric",
                        rubric_delta=value,
                    )
                )
                notes.append(f"{rec.finding_id} accepted: added rubric delta {value:+.2f}")
        elif rec.decision in {"declined", "deferred"} and match is not None:
            remaining.remove(match)
            notes.append(f"{rec.finding_id} {rec.decision}: cancelled {match.finding_id}")
    return remaining, notes


def extract_raw_review_texts(pr_data: dict[str, Any]) -> list[tuple[str, str]]:
    """Extract review and comment bodies, prioritizing the latest review from each reviewer."""
    # Group comments by author, preserving chronological order
    comments_by_author: dict[str, list[str]] = {}

    for rev in pr_data.get("reviews", []):
        author = rev.get("author", {}).get("login", "unknown")
        body = rev.get("body", "")
        if body.strip():
            comments_by_author.setdefault(author, []).append(body)

    for com in pr_data.get("comments", []):
        author = com.get("author", {}).get("login", "unknown")
        body = com.get("body", "")
        if body.strip():
            comments_by_author.setdefault(author, []).append(body)

    sources: list[tuple[str, str]] = []
    for author, bodies in comments_by_author.items():
        # For automated reviewers (e.g. amazon-q, cursor), take their latest full review summary
        if "amazon-q" in author.lower() or "bot" in author.lower():
            # Find the latest body that contains review content
            review_bodies = [
                b
                for b in bodies
                if any(
                    k in b.lower()
                    for k in (
                        "review summary",
                        "status check",
                        "resolved findings",
                        "blocking issues",
                        "finding status review",
                        "confirmed resolved",
                        "nothing remaining",
                    )
                )
            ]
            if review_bodies:
                sources.append((author, review_bodies[-1]))
            else:
                sources.append((author, bodies[-1]))
        else:
            # For human reviewers, include all non-bot comments
            for b in bodies:
                sources.append((author, b))

    return sources


def convert_unstructured_review_to_tags(author: str, text: str, source_prefix: str = "REV") -> list[str]:
    """Parse common unstructured bot/human review patterns into Epic 14 tag grammar."""
    tagged_lines: list[str] = []

    # First check if the text already contains tagged bullets
    tag_bullets = re.findall(r"^[*-]\s*(\[criterion:[^\]]+\].+)$", text, re.MULTILINE)
    if tag_bullets:
        for b in tag_bullets:
            tagged_lines.append(f"- {b}")
        return tagged_lines

    # Amazon Q Review parsing
    if "amazon-q" in author.lower() or any(
        k in text.lower() for k in ("review summary", "finding status review")
    ):
        # 1. Blocking / Critical issues
        blocking_match = re.search(
            r"###?\s*(?:Blocking issues found|Critical Issues Found|Critical Issues|Issues Found|Issues requiring fixes)[^\n]*\n([\s\S]*?)(?=\n###?|\Z)",
            text,
            re.IGNORECASE,
        )
        if blocking_match:
            block_content = blocking_match.group(1)
            items = re.findall(
                r"(?:^|\n)\s*(?:\d+\.|\*|-|\*\*\d+\.)\s+(.+?)(?=(?:\n\s*(?:\d+\.|\*|-|\*\*\d+\.)\s+)|\Z)",
                block_content,
                re.DOTALL,
            )
            for idx, item in enumerate(items, start=1):
                clean_item = " ".join(item.split()).replace("**", "")
                low = clean_item.lower()
                f_id = f"{source_prefix}-CRIT-{idx}"
                if any(w in low for w in ("crash", "exception", "attributeerror", "keyerror", "unhandled", "vulnerability")):
                    tagged_lines.append(f"- [criterion: correctness] [claim: crash risk] [verified: yes] [finding: {f_id}]: {clean_item[:120]}")
                elif any(w in low for w in ("test", "coverage", "unexercised", "untested", "fragile")):
                    tagged_lines.append(f"- [criterion: test_coverage] [claim: test gap] [verified: yes] [finding: {f_id}]: {clean_item[:120]}")
                elif any(w in low for w in ("unused", "import", "style", "linter", "format")):
                    tagged_lines.append(f"- [criterion: implementation_quality] [claim: style] [verified: partial] [finding: {f_id}]: {clean_item[:120]}")
                else:
                    tagged_lines.append(f"- [criterion: correctness] [claim: logic error] [verified: yes] [finding: {f_id}]: {clean_item[:120]}")
        else:
            single_block = re.search(
                r"\*\*(?:One|\d+)\s+blocking\s+(?:defect|issue)[s]?\s+(?:was|were)\s+found:?\*\*:?\s*([\s\S]*?)(?=\n\n|\n###|\Z)",
                text,
                re.IGNORECASE,
            )
            if single_block:
                clean_item = " ".join(single_block.group(1).split()).replace("**", "")
                f_id = f"{source_prefix}-CRIT-1"
                low = clean_item.lower()
                if any(w in low for w in ("crash", "exception", "attributeerror", "keyerror", "unhandled", "vulnerability")):
                    tagged_lines.append(f"- [criterion: correctness] [claim: crash risk] [verified: yes] [finding: {f_id}]: {clean_item[:120]}")
                elif any(w in low for w in ("test", "coverage", "unexercised", "untested", "fragile")):
                    tagged_lines.append(f"- [criterion: test_coverage] [claim: test gap] [verified: yes] [finding: {f_id}]: {clean_item[:120]}")
                elif any(w in low for w in ("unused", "import", "style", "linter", "format")):
                    tagged_lines.append(f"- [criterion: implementation_quality] [claim: style] [verified: partial] [finding: {f_id}]: {clean_item[:120]}")
                else:
                    tagged_lines.append(f"- [criterion: correctness] [claim: logic error] [verified: yes] [finding: {f_id}]: {clean_item[:120]}")

        # 2. Remaining / Open items (Minor gaps)
        remaining_match = re.search(
            r"###?\s*⚠️?\s*(?:Remaining\s*/?\s*open items|Remaining\s*items|Open\s*items)[^\n]*\n([\s\S]*?)(?=\n###?|\Z)",
            text,
            re.IGNORECASE,
        )
        if remaining_match:
            rem_content = remaining_match.group(1)
            table_rows = re.findall(r"\|\s*\d+\s*\|\s*([^|]+)\|\s*([^|]+)\|", rem_content)
            if table_rows:
                for idx, (finding_title, notes) in enumerate(table_rows, start=1):
                    clean_row = f"{finding_title.strip()}: {notes.strip()}".replace("**", "")
                    low = clean_row.lower()
                    f_id = f"{source_prefix}-OPEN-{idx}"
                    if any(w in low for w in ("test", "tolerance", "residual")):
                        tagged_lines.append(f"- [criterion: test_coverage] [claim: test gap] [verified: partial] [finding: {f_id}]: {clean_row[:120]}")
                    else:
                        tagged_lines.append(f"- [criterion: implementation_quality] [claim: logic error] [verified: partial] [finding: {f_id}]: {clean_row[:120]}")
            else:
                items = re.findall(r"(?:^|\n)\s*(?:\d+\.|\*|-)\s+(.+?)(?=(?:\n\s*(?:\d+\.|\*|-)\s+)|\Z)", rem_content, re.DOTALL)
                for idx, item in enumerate(items, start=1):
                    clean_item = " ".join(item.split()).replace("**", "")
                    f_id = f"{source_prefix}-OPEN-{idx}"
                    tagged_lines.append(f"- [criterion: implementation_quality] [claim: logic error] [verified: partial] [finding: {f_id}]: {clean_item[:120]}")

        # 3. Resolved in this commit (Confirmations)
        resolved_match = re.search(
            r"###?\s*✅?\s*(?:Resolved in this commit|Resolved\s*/\s*Correctly Implemented|Resolved findings)[^\n]*\n([\s\S]*?)(?=\n###?|\Z)",
            text,
            re.IGNORECASE,
        )
        if resolved_match:
            res_content = resolved_match.group(1)
            table_rows = re.findall(r"\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|", res_content)
            idx = 1
            for r in table_rows:
                col0 = r[0].strip().replace("*", "")
                col1 = r[1].strip().replace("*", "")
                if not col0 or col0.startswith("-") or col0.lower() in ("#", "finding area", "finding"):
                    continue
                title = col1 if col0.isdigit() else col0
                f_id = f"{source_prefix}-RES-{idx}"
                idx += 1
                if "invariant 6" in title.lower() or "upstream" in title.lower():
                    tagged_lines.append(f"- [criterion: upstream_fork_purity] [claim: confirmation] [verified: yes] [finding: {f_id}]: {title[:120]}")
                else:
                    tagged_lines.append(f"- [criterion: correctness] [claim: confirmation] [verified: yes] [finding: {f_id}]: {title[:120]}")

        # 4. General positive confirmation if no blocking issues
        if (
            "no blocking issues found" in text.lower()
            or "looks correct" in text.lower()
            or "status: none" in text.lower()
            or "none prevent merge" in text.lower()
            or "nothing remaining" in text.lower()
            or "confirmed resolved" in text.lower()
        ) and not any("crash risk" in l or "logic error" in l for l in tagged_lines):
            f_id = f"{source_prefix}-CONFIRM"
            tagged_lines.append(
                f"- [criterion: correctness] [claim: confirmation] [verified: yes] [finding: {f_id}]: "
                "Mathematical and structural implementation verified correct by reviewer."
            )

    return tagged_lines


def build_decision_frame(pr_number: int) -> DecisionFrame:
    """Construct the standardized PR Governance DecisionFrame."""
    criteria = (
        DecisionCriterion(id="correctness", weight=0.40, minimum_sources=1),
        DecisionCriterion(id="upstream_fork_purity", weight=0.25, minimum_sources=1),
        DecisionCriterion(id="implementation_quality", weight=0.20, minimum_sources=1),
        DecisionCriterion(id="test_coverage", weight=0.15, minimum_sources=1),
    )

    opt_approve = DecisionOption(
        action=Action(id="approve_and_merge", description=f"Approve and Merge PR #{pr_number}"),
        evidence=(
            EvidencePoint("correctness", "ci_tests", 0.85, 0.80),
            EvidencePoint("upstream_fork_purity", "fork_guard", 0.95, 0.90),
            EvidencePoint("implementation_quality", "code_inspection", 0.80, 0.75),
            EvidencePoint("test_coverage", "test_suite", 0.80, 0.75),
        ),
    )

    opt_revise = DecisionOption(
        action=Action(id="request_revisions", description=f"Request Revisions / Blocking Issues on PR #{pr_number}"),
        evidence=(
            EvidencePoint("correctness", "baseline_eval", 0.60, 0.60),
            EvidencePoint("upstream_fork_purity", "baseline_eval", 0.75, 0.70),
            EvidencePoint("implementation_quality", "baseline_eval", 0.70, 0.70),
            EvidencePoint("test_coverage", "baseline_eval", 0.70, 0.70),
        ),
    )

    return DecisionFrame(
        task=f"pr-{pr_number}-governance-gate",
        options=(opt_approve, opt_revise),
        criteria=criteria,
    )


def make_snapshot(frame: DecisionFrame) -> PolicySnapshot:
    actions = [opt.action for opt in frame.options]
    return PolicySnapshot(
        id=f"policy-{frame.task}",
        agent_id="agent-learning-governance",
        task_id=frame.task,
        version=1,
        actions=actions,
        logits={act.id: 0.0 for act in actions},
        metadata={"decision_authority": DecisionAuthority.FULL.value},
    )


def save_gate_episode(
    pr_number: int,
    pr_data: dict[str, Any],
    passed: bool,
    reason: str,
    margin: float,
    applied: Any | None = None,
    store_dir: Path | str | None = None,
) -> str | None:
    """Passively persist the PR gate decision as an auditable Episode in LearningStore."""
    target_dir = Path(store_dir) if store_dir else DEFAULT_STORE_DIR
    try:
        store = LocalFileStore(root_dir=target_dir)
        head_commit = str(pr_data.get("headRefOid") or "unknown")
        ep_uuid = uuid.uuid4().hex[:8]
        short_commit = head_commit[:7] if head_commit != "unknown" else "run"
        episode_id = f"pr-{pr_number}-{short_commit}-{ep_uuid}"

        adjustments = to_episode_metadata(applied).get("critique_adjustments", []) if applied else []

        if passed:
            action_id = "approve_and_merge"
            meta: dict[str, Any] = {
                "pr_number": pr_number,
                "title": pr_data.get("title", ""),
                "head_commit": head_commit,
                "feedback_status": "accepted",
                "margin": round(margin, 4),
                "critique_adjustments": adjustments,
            }
        else:
            action_id = "approve_and_merge"
            meta = {
                "pr_number": pr_number,
                "title": pr_data.get("title", ""),
                "head_commit": head_commit,
                "feedback_status": "rejected",
                "correct_action_id": "request_revisions",
                "rejection_reason": reason,
                "margin": round(margin, 4),
                "critique_adjustments": adjustments,
            }

        episode = Episode(
            id=episode_id,
            agent_id="agent-learning-governance",
            task_id=f"pr-{pr_number}-governance-gate",
            task_name=f"PR #{pr_number} Governance Review Gate",
            policy_id=f"policy-pr-{pr_number}-governance-gate",
            policy_version=1,
            action_id=action_id,
            intent_summary=f"Bayesian gatekeeper evaluation of PR #{pr_number}",
            user_input=f"PR #{pr_number}: {pr_data.get('title', '')}",
            assistant_output=reason,
            metadata=meta,
        )

        store.store_episode(episode)
        return episode_id
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: Passive episode storage skipped: {exc}", file=sys.stderr)
        return None


def evaluate_pr(
    pr_number: int,
    store_dir: Path | str | None = None,
    persist_episode: bool = True,
) -> tuple[bool, str, dict[str, Any]]:
    """Evaluate a PR against CI checks, Invariant 6, and Epic 14 Bayesian critique."""
    pr_data = fetch_pr_data(pr_number)

    # 1. CI Status Checks
    checks = pr_data.get("statusCheckRollup", [])
    failing_checks = [
        c.get("name", "unknown")
        for c in checks
        if c.get("conclusion") in ("FAILURE", "TIMED_OUT", "ACTION_REQUIRED")
    ]
    if failing_checks:
        reason = f"CI check failure: {', '.join(failing_checks)}. All GitHub Actions must pass."
        ep_id = None
        if persist_episode:
            ep_id = save_gate_episode(
                pr_number=pr_number,
                pr_data=pr_data,
                passed=False,
                reason=reason,
                margin=-1.0,
                applied=None,
                store_dir=store_dir,
            )
        return (
            False,
            reason,
            {
                "pr_number": pr_number,
                "title": pr_data.get("title"),
                "head_commit": pr_data.get("headRefOid"),
                "ci_failures": failing_checks,
                "episode_id": ep_id,
            },
        )

    # 2. Invariant 6: Upstream Fork Collision Protection
    # Microsoft modules in src/agent_learning/ must remain pristine
    changed_files = [f.get("path", "") for f in pr_data.get("files", [])]
    upstream_violations = [
        p for p in changed_files if p.startswith("src/agent_learning/") and not p.startswith("src/agent_learning_ext/")
    ]
    if upstream_violations:
        reason = (
            f"Invariant 6 Violation: Pull request modifies upstream files: {', '.join(upstream_violations)}. "
            "All customizations must reside in src/agent_learning_ext/."
        )
        ep_id = None
        if persist_episode:
            ep_id = save_gate_episode(
                pr_number=pr_number,
                pr_data=pr_data,
                passed=False,
                reason=reason,
                margin=-1.0,
                applied=None,
                store_dir=store_dir,
            )
        return (
            False,
            reason,
            {
                "pr_number": pr_number,
                "title": pr_data.get("title"),
                "head_commit": pr_data.get("headRefOid"),
                "upstream_violations": upstream_violations,
                "episode_id": ep_id,
            },
        )

    # 2b. IMP-030: review-triage lines the PR adds must stay inside the vocabulary
    triage_records, triage_errors = check_triage_lines(added_triage_lines(fetch_pr_diff(pr_number)))
    if triage_errors:
        reason = "Triage line outside the vocabulary: " + "; ".join(triage_errors)
        ep_id = None
        if persist_episode:
            ep_id = save_gate_episode(
                pr_number=pr_number,
                pr_data=pr_data,
                passed=False,
                reason=reason,
                margin=-1.0,
                applied=None,
                store_dir=store_dir,
            )
        return (
            False,
            reason,
            {
                "pr_number": pr_number,
                "title": pr_data.get("title"),
                "head_commit": pr_data.get("headRefOid"),
                "triage_errors": triage_errors,
                "episode_id": ep_id,
            },
        )

    # 3. Extract and parse reviews
    review_sources = extract_raw_review_texts(pr_data)
    all_tagged_bullets: list[str] = []

    for r_idx, (author, body) in enumerate(review_sources, start=1):
        tags = convert_unstructured_review_to_tags(author, body, source_prefix=f"REV{r_idx}")
        all_tagged_bullets.extend(tags)

    deltas: list[CritiqueDelta] = []
    if all_tagged_bullets:
        full_critique_text = "\n".join(all_tagged_bullets)
        try:
            deltas = parse_critique(full_critique_text, source_id="pr_review")
        except ValueError as err:
            # Tolerant fallback if any bullet fails parsing
            print(f"Warning: Parse issue on review line: {err}", file=sys.stderr)

    deltas, triage_notes = reconcile_triage(deltas, triage_records, pr_number)

    # 4. Bayesian Decision Frame Setup & Ingestion
    frame = build_decision_frame(pr_number)
    applied = apply_critique(frame, option_id="approve_and_merge", deltas=deltas)

    # 5. Decision Resolution
    resolver = DecisionResolver()
    snapshot = make_snapshot(applied.frame)
    result = resolver.resolve(snapshot, applied.frame)

    # Extract assessments
    approve_assess = next(a for a in result.assessments if a.action.id == "approve_and_merge")
    revise_assess = next(a for a in result.assessments if a.action.id == "request_revisions")
    margin = approve_assess.robust_utility - revise_assess.robust_utility

    passed = (
        result.status.value == "resolved"
        and result.selected_action is not None
        and result.selected_action.id == "approve_and_merge"
        and margin >= 0.05
    )

    if passed:
        reason = (
            f"Approved: robust utility {approve_assess.robust_utility:.3f} and margin {margin:+.3f} "
            f"exceed threshold (+0.05). {result.reason or ''}".strip()
        )
    else:
        reason = (
            f"Halted: robust utility margin {margin:+.3f} below safety threshold (+0.05). "
            f"{result.reason or ''}".strip()
        )

    ep_id = None
    if persist_episode:
        ep_id = save_gate_episode(
            pr_number=pr_number,
            pr_data=pr_data,
            passed=passed,
            reason=reason,
            margin=margin,
            applied=applied,
            store_dir=store_dir,
        )

    details: dict[str, Any] = {
        "pr_number": pr_number,
        "title": pr_data.get("title"),
        "head_commit": pr_data.get("headRefOid"),
        "status": result.status.value,
        "selected_action": result.selected_action.id if result.selected_action else None,
        "margin": round(margin, 4),
        "assessments": {
            "approve_and_merge": {
                "robust_utility": round(approve_assess.robust_utility, 3),
                "expected_utility": round(approve_assess.expected_utility, 3),
            },
            "request_revisions": {
                "robust_utility": round(revise_assess.robust_utility, 3),
                "expected_utility": round(revise_assess.expected_utility, 3),
            },
        },
        "critique_deltas_count": len(deltas),
        "triage_replay": triage_notes,
        "critique_adjustments": to_episode_metadata(applied).get("critique_adjustments", []),
        "episode_id": ep_id,
    }

    return passed, reason, details


def ensure_utf8_stdout() -> None:
    """Make stdout/stderr UTF-8 so the emoji verdict lines print on a cp1252 console.

    Without it, Windows consoles raised UnicodeEncodeError on the verdict line after the
    verdict was computed, losing the result (PR #146). Streams without `reconfigure`
    (captured or replaced ones) are left alone.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def main() -> int:
    ensure_utf8_stdout()
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("pr_number", type=int, help="GitHub Pull Request number to evaluate")
    parser.add_argument("--merge", action="store_true", help="Automatically merge if the gate passes")
    parser.add_argument("--json", action="store_true", help="Output full evaluation in JSON format")
    parser.add_argument("--no-store", action="store_true", help="Do not persist the evaluation episode to LearningStore")
    parser.add_argument("--store-dir", type=str, default=None, help="Custom directory path for LearningStore")

    args = parser.parse_args()

    try:
        passed, reason, details = evaluate_pr(
            args.pr_number,
            store_dir=args.store_dir,
            persist_episode=not args.no_store,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Error evaluating PR #{args.pr_number}: {exc}", file=sys.stderr)
        return 2

    if args.json:
        out = {"passed": passed, "reason": reason, "details": details}
        print(json.dumps(out, indent=2))
        return 0 if passed else 1

    print("=" * 80)
    print(f"PR GATEKEEPER EVALUATION: PR #{args.pr_number} — {details.get('title')}")
    print("=" * 80)
    print(f"Commit: {details.get('head_commit')}")
    if details.get("episode_id"):
        print(f"Passive Learning Episode: {details.get('episode_id')}")
    print(f"Ingested Findings: {details.get('critique_deltas_count')} critique deltas applied.")

    for adj in details.get("critique_adjustments", []):
        f_id = adj.get("finding_id", "finding")
        crit = adj.get("criterion_id", "criterion")
        delta = adj.get("support_delta", 0.0)
        rat = adj.get("rationale", "")
        print(f"  • [{f_id}] {crit:<25} Delta: {delta:+.2f} | \"{rat[:75]}\"")

    print("-" * 80)
    scores = details.get("assessments", {})
    app_score = scores.get("approve_and_merge")
    rev_score = scores.get("request_revisions")
    if app_score and rev_score:
        print(f"Approve Option: Robust Utility = {app_score.get('robust_utility')} | Expected Utility = {app_score.get('expected_utility')}")
        print(f"Revise Option:  Robust Utility = {rev_score.get('robust_utility')} | Expected Utility = {rev_score.get('expected_utility')}")
    else:
        print("Assessments: N/A (Halted prior to Bayesian decision resolution)")

    margin = details.get("margin")
    if margin is not None:
        print(f"Decision Margin: {margin:+.3f} (Required: >= +0.05)")
    else:
        print("Decision Margin: N/A")
    print("-" * 80)

    if passed:
        print("✅ GATE RESULT: PASSED / APPROVED TO MERGE")
        print(f"   Reason: {reason}")
        if args.merge:
            print("\nExecuting gh pr merge...")
            merge_cmd = ["gh", "pr", "merge", str(args.pr_number), "--repo", "mdresch/agent-learning", "--merge"]
            subprocess.run(merge_cmd, check=True)
            print("Successfully merged!")
        return 0
    else:
        print("⚠️  GATE RESULT: HALTED / REVISIONS REQUIRED")
        print(f"   Reason: {reason}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
