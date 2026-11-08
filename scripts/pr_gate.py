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
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "agent-training-ext"))

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

try:
    from agent_training_ext.critique_evidence import (
        CritiqueDelta,
        apply_critique,
        parse_critique,
        to_episode_metadata,
    )
except ImportError:
    from critique_evidence import (  # type: ignore
        CritiqueDelta,
        apply_critique,
        parse_critique,
        to_episode_metadata,
    )


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
    run = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
    if run.returncode != 0:
        raise RuntimeError(f"Failed to fetch PR #{pr_number} via gh: {run.stderr.strip()}")
    return json.loads(run.stdout)


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
            review_bodies = [b for b in bodies if "review summary" in b.lower() or "status check" in b.lower() or "resolved findings" in b.lower() or "blocking issues" in b.lower()]
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
    if "amazon-q" in author.lower() or "Review Summary" in text:
        # 1. Blocking / Critical issues
        blocking_match = re.search(
            r"###?\s*(?:Blocking issues found|Critical Issues Found|Critical Issues|Issues requiring fixes)[^\n]*\n([\s\S]*?)(?=\n###?|\Z)",
            text,
            re.IGNORECASE,
        )
        if blocking_match:
            block_content = blocking_match.group(1)
            items = re.findall(r"(?:^|\n)\s*(?:\d+\.|\*|-)\s+(.+?)(?=(?:\n\s*(?:\d+\.|\*|-)\s+)|\Z)", block_content, re.DOTALL)
            for idx, item in enumerate(items, start=1):
                clean_item = " ".join(item.split())
                low = clean_item.lower()
                f_id = f"{source_prefix}-CRIT-{idx}"
                if any(w in low for w in ("crash", "exception", "attributeerror", "keyerror", "unhandled", "vulnerability")):
                    tagged_lines.append(f"- [criterion: correctness] [claim: crash risk] [verified: yes] [finding: {f_id}]: {clean_item[:120]}")
                elif any(w in low for w in ("test", "coverage", "unexercised", "untested")):
                    tagged_lines.append(f"- [criterion: test_coverage] [claim: test gap] [verified: yes] [finding: {f_id}]: {clean_item[:120]}")
                elif any(w in low for w in ("unused", "import", "style", "linter", "format")):
                    tagged_lines.append(f"- [criterion: implementation_quality] [claim: style] [verified: partial] [finding: {f_id}]: {clean_item[:120]}")
                else:
                    tagged_lines.append(f"- [criterion: correctness] [claim: logic error] [verified: yes] [finding: {f_id}]: {clean_item[:120]}")

        # 2. Remaining / Open items (Minor gaps)
        remaining_match = re.search(
            r"###?\s*⚠️?\s*Remaining\s*/?\s*open items[^\n]*\n([\s\S]*?)(?=\n###?|\Z)",
            text,
            re.IGNORECASE,
        )
        if remaining_match:
            rem_content = remaining_match.group(1)
            table_rows = re.findall(r"\|\s*\d+\s*\|\s*([^|]+)\|\s*([^|]+)\|", rem_content)
            if table_rows:
                for idx, (finding_title, notes) in enumerate(table_rows, start=1):
                    clean_row = f"{finding_title.strip()}: {notes.strip()}"
                    low = clean_row.lower()
                    f_id = f"{source_prefix}-OPEN-{idx}"
                    if any(w in low for w in ("test", "tolerance", "residual")):
                        tagged_lines.append(f"- [criterion: test_coverage] [claim: test gap] [verified: partial] [finding: {f_id}]: {clean_row[:120]}")
                    else:
                        tagged_lines.append(f"- [criterion: implementation_quality] [claim: logic error] [verified: partial] [finding: {f_id}]: {clean_row[:120]}")
            else:
                items = re.findall(r"(?:^|\n)\s*(?:\d+\.|\*|-)\s+(.+?)(?=(?:\n\s*(?:\d+\.|\*|-)\s+)|\Z)", rem_content, re.DOTALL)
                for idx, item in enumerate(items, start=1):
                    clean_item = " ".join(item.split())
                    f_id = f"{source_prefix}-OPEN-{idx}"
                    tagged_lines.append(f"- [criterion: implementation_quality] [claim: logic error] [verified: partial] [finding: {f_id}]: {clean_item[:120]}")

        # 3. Resolved in this commit (Confirmations)
        resolved_match = re.search(
            r"###?\s*✅?\s*Resolved in this commit[^\n]*\n([\s\S]*?)(?=\n###?|\Z)",
            text,
            re.IGNORECASE,
        )
        if resolved_match:
            res_content = resolved_match.group(1)
            table_rows = re.findall(r"\|\s*\d+\s*\|\s*([^|]+)\|\s*([^|]+)\|", res_content)
            if table_rows:
                for idx, (title, _) in enumerate(table_rows, start=1):
                    clean_t = title.strip().replace("*", "")
                    f_id = f"{source_prefix}-RES-{idx}"
                    if "invariant 6" in clean_t.lower() or "upstream" in clean_t.lower():
                        tagged_lines.append(f"- [criterion: upstream_fork_purity] [claim: confirmation] [verified: yes] [finding: {f_id}]: {clean_t[:120]}")
                    else:
                        tagged_lines.append(f"- [criterion: correctness] [claim: confirmation] [verified: yes] [finding: {f_id}]: {clean_t[:120]}")

        # 4. General positive confirmation if no blocking issues
        if (
            "no blocking issues found" in text.lower()
            or "looks correct" in text.lower()
            or "status: none" in text.lower()
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


def evaluate_pr(pr_number: int) -> tuple[bool, str, dict[str, Any]]:
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
        return (
            False,
            f"CI check failure: {', '.join(failing_checks)}. All GitHub Actions must pass.",
            {"ci_failures": failing_checks},
        )

    # 2. Invariant 6: Upstream Fork Collision Protection
    # Microsoft modules in src/agent_learning/ must remain pristine
    changed_files = [f.get("path", "") for f in pr_data.get("files", [])]
    upstream_violations = [
        p for p in changed_files if p.startswith("src/agent_learning/") and not p.startswith("src/agent_learning_ext/")
    ]
    if upstream_violations:
        return (
            False,
            (
                f"Invariant 6 Violation: Pull request modifies upstream files: {', '.join(upstream_violations)}. "
                "All customizations must reside in src/agent_learning_ext/ or agent-training-ext/."
            ),
            {"upstream_violations": upstream_violations},
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
        "critique_adjustments": to_episode_metadata(applied).get("critique_adjustments", []),
    }

    return passed, reason, details


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("pr_number", type=int, help="GitHub Pull Request number to evaluate")
    parser.add_argument("--merge", action="store_true", help="Automatically merge if the gate passes")
    parser.add_argument("--json", action="store_true", help="Output full evaluation in JSON format")

    args = parser.parse_args()

    try:
        passed, reason, details = evaluate_pr(args.pr_number)
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
    print(f"Ingested Findings: {details.get('critique_deltas_count')} critique deltas applied.")

    for adj in details.get("critique_adjustments", []):
        f_id = adj.get("finding_id", "finding")
        crit = adj.get("criterion_id", "criterion")
        delta = adj.get("support_delta", 0.0)
        rat = adj.get("rationale", "")
        print(f"  • [{f_id}] {crit:<25} Delta: {delta:+.2f} | \"{rat[:75]}\"")

    print("-" * 80)
    scores = details.get("assessments", {})
    app_score = scores.get("approve_and_merge", {})
    rev_score = scores.get("request_revisions", {})
    print(f"Approve Option: Robust Utility = {app_score.get('robust_utility')} | Expected Utility = {app_score.get('expected_utility')}")
    print(f"Revise Option:  Robust Utility = {rev_score.get('robust_utility')} | Expected Utility = {rev_score.get('expected_utility')}")
    print(f"Decision Margin: {details.get('margin'):+.3f} (Required: >= +0.05)")
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
