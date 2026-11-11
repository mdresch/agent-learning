"""Demonstration: AI Code-Review Triage & Calibrated TaskPolicy PR Gate (ADR-036 / ADR-001).

Run this file with:
    python examples/review_triage_gate_demo.py

What Developer Problem This Solves:
When teams wire automated AI code reviewers (e.g., Amazon Q, Copilot, static bots)
into a pull-request merge gate, treating every bot comment with a fixed high confidence
causes two failure modes:
  1. False-positive fatigue: A reviewer with a noisy track record on one claim type
     (e.g., hallucinated 'logic error' claims) blocks clean PRs and forces wasted rework.
  2. Blind whitelisting: Disabling or down-weighting the reviewer globally causes the
     team to miss claim types where that same reviewer is highly accurate (e.g., 'crash risk').

How Agent Learning Solves It:
  1. Historical Triage Parsing (`agent_learning.review_triage`):
     Parses structured one-line triage records from `implementation-log.md` using
     `find_triage_lines` and `parse_triage_line`.
  2. Claim-Type Reliability Calibration (`reliability` + Wilson Lower Bound):
     Computes a conservative 95% Wilson score lower bound per (reviewer, claim_type),
     returning `None` whenever a slice has fewer than `min_cases=5` verified outcomes.
  3. Calibrated `TaskPolicy` Resolution (`DecisionAuthority.FULL`):
     Maps the calibrated Wilson lower bound onto `EvidencePoint.confidence` inside a
     multi-criteria `DecisionFrame` resolved by `TaskPolicy.decide(frame)`.
  4. Human-in-the-Loop Triage & Episode Lineage (`to_episode_metadata` + `EpisodeCapture`):
     Preserves human triage authority (ADR-003 Invariant 6), demonstrates tie-break
     adjudication via `TaskPolicy.adjudicate()`, and persists triage metadata onto episodes.
"""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Mapping

from agent_learning import (
    Action,
    CaptureConfig,
    DecisionAuthority,
    DecisionCriterion,
    DecisionFrame,
    DecisionOption,
    DecisionResult,
    EpisodeCapture,
    EvidencePoint,
    InMemoryStore,
    PolicySnapshot,
    TaskPolicy,
    TieBreakDisposition,
)
from agent_learning.comparison import compare_decision_results
from agent_learning.review_triage import (
    REVIEWERS,
    Reliability,
    TriageRecord,
    find_triage_lines,
    parse_triage_line,
    reconstruct_record,
    reliability,
    to_episode_metadata,
)

# Extend the reviewer initial map for a multi-bot engineering org
ORG_REVIEWERS: Mapping[str, str] = {
    **REVIEWERS,  # "Q": "amazon-q"
    "S": "semgrep-pro",
}

CONFIDENCE_FLOOR = 0.05
DEFAULT_UNPROVEN_CONFIDENCE = 0.25


def header(title: str) -> None:
    print(f"\n{'=' * 82}")
    print(f"  {title}")
    print(f"{'=' * 82}\n")


# ==============================================================================
# 1. Historical Implementation Log with Triaged Review Findings
# ==============================================================================

HISTORICAL_IMPLEMENTATION_LOG = """
# Implementation Log — Recent Pull Request Triage Records

### PR #190 — Story 31.1
- `Q-190-1 | crash risk | verified: yes | decision: accepted | unchecked None dereference on empty payload | fix: a1b2c3d`
- `Q-190-2 | logic error | verified: no | decision: declined | guard already enforced by schema validator | fix: none`

### PR #192 — Story 31.2
- `Q-192-1 | crash risk | verified: yes | decision: accepted | division by zero when episode count is 0 | fix: b2c3d4e`
- `Q-192-2 | logic error | verified: no | decision: declined | loop bound is inclusive by specification | fix: none`

### PR #195 — Story 32.1
- `Q-195-1 | crash risk | verified: yes | decision: accepted | missing KeyError guard on optional metadata field | fix: c3d4e5f`
- `Q-195-2 | logic error | verified: no | decision: declined | sorting order is intentionally descending | fix: none`

### PR #198 — Story 32.2
- `Q-198-1 | crash risk | verified: yes | decision: accepted | unclosed file handle on validation exception path | fix: d4e5f6a`
- `Q-198-2 | logic error | verified: partial | decision: accepted with modification | edge case only applies to negative weights | fix: e5f6a7b`

### PR #201 — Story 33.1
- `Q-201-1 | crash risk | verified: yes | decision: accepted | null pointer when snapshot actions tuple is empty | fix: f6a7b8c`
- `Q-201-2 | logic error | verified: no | decision: declined | zero-centering offset cancels out in softmax | fix: none`

### PR #203 — Story 33.2
- `Q-203-1 | crash risk | verified: no | decision: declined | path is guaranteed non-null by caller contract | fix: none`
- `Q-203-2 | logic error | verified: yes | decision: accepted | off-by-one in window slice boundary | fix: 1a2b3c4`

### PR #205 — Story 34.1
- `Q-205-1 | crash risk | verified: yes | decision: accepted | index error when candidate list has 1 item | fix: 2b3c4d5`
- `Q-205-2 | logic error | verified: no | decision: declined | digest helper returns 64 hex chars as expected | fix: none`
- `Q-205-3 | style | verified: yes | decision: accepted | redundant import alias removed | fix: 3c4d5e6`

### PR #206 — Phase 2 Closure
- `Q-206-1 | logic error | verified: no | decision: declined | fc927c0b...d5100 is 64 hex chars; reviewer miscounted | fix: none`
- `Q-206-2 | logic error | verified: no | decision: declined | digest matches approve._digest() sha256 output | fix: none`
- `Q-206-3 | documentation | verified: yes | decision: accepted | duplicate table header row in status register | fix: 98e8373`
"""


def build_pr_gate_task_policy() -> TaskPolicy:
    """Create a FULL-authority TaskPolicy governing PR merge decisions."""
    actions = [
        Action(
            id="approve_merge",
            description="Approve and merge the pull request into main",
        ),
        Action(
            id="request_author_fix",
            description="Block merge and request targeted code changes from the PR author",
        ),
        Action(
            id="escalate_human_review",
            description="Escalate ambiguous or high-risk findings to a human maintainer",
        ),
    ]
    snapshot = PolicySnapshot(
        id="policy-pr-gate-v1",
        agent_id="ci-governance-agent",
        task_id="pr-merge-gate",
        version=1,
        actions=actions,
        logits={a.id: 0.0 for a in actions},
        metadata={
            "decision_authority": DecisionAuthority.FULL.value,
            "description": "Evidence-gated PR merge decision policy with calibrated reviewer confidence",
        },
    )
    return TaskPolicy(snapshot)


def calibrated_confidence(rel: Reliability) -> float:
    """Convert a reviewer's Wilson lower bound into a bounded EvidencePoint confidence."""
    if rel.lower_bound is None:
        return DEFAULT_UNPROVEN_CONFIDENCE
    return max(CONFIDENCE_FLOOR, min(1.0, round(rel.lower_bound, 4)))


def build_pr_decision_frame(
    policy: TaskPolicy,
    *,
    bot_claim_type: str,
    bot_confidence: float,
    unmitigated_crash: bool = False,
    minimum_margin: float = 0.05,
) -> DecisionFrame:
    """Construct a DecisionFrame for the PR gate given the bot's claim and confidence."""
    actions = {a.id: a for a in policy.snapshot().actions}

    criteria = (
        DecisionCriterion(
            id="code_correctness",
            weight=0.65,
            minimum_sources=2,
            description="Absence of functional bugs, logic errors, or crash defects",
        ),
        DecisionCriterion(
            id="ci_verification",
            weight=0.20,
            minimum_sources=1,
            description="Automated test suite, typecheck, and contract lint pass rate",
        ),
        DecisionCriterion(
            id="delivery_velocity",
            weight=0.15,
            minimum_sources=1,
            description="Avoiding unnecessary rework cycles or false-positive merge blocks",
        ),
    )

    # When the bot flags a defect, it argues strongly AGAINST approve_merge (support=0.04)
    # and FOR request_author_fix (support=0.95) on `code_correctness`.
    bot_source = f"amazon-q:{bot_claim_type.replace(' ', '_')}"

    approve_option = DecisionOption(
        action=actions["approve_merge"],
        evidence=(
            EvidencePoint("code_correctness", "pytest_suite", support=0.84, confidence=0.65),
            EvidencePoint("code_correctness", bot_source, support=0.04, confidence=bot_confidence),
            EvidencePoint("ci_verification", "github_actions_ci", support=0.92, confidence=0.90),
            EvidencePoint("delivery_velocity", "cycle_time_model", support=0.95, confidence=0.85),
        ),
        constraint_results={
            "ci_green": True,
            "no_unmitigated_crash_risk": not unmitigated_crash,
        },
    )

    fix_option = DecisionOption(
        action=actions["request_author_fix"],
        evidence=(
            EvidencePoint("code_correctness", "pytest_suite", support=0.55, confidence=0.60),
            EvidencePoint("code_correctness", bot_source, support=0.95, confidence=bot_confidence),
            EvidencePoint("ci_verification", "github_actions_ci", support=0.96, confidence=0.85),
            EvidencePoint("delivery_velocity", "cycle_time_model", support=0.35, confidence=0.85),
        ),
        constraint_results={
            "ci_green": True,
            "no_unmitigated_crash_risk": True,
        },
    )

    escalate_option = DecisionOption(
        action=actions["escalate_human_review"],
        evidence=(
            EvidencePoint("code_correctness", "pytest_suite", support=0.60, confidence=0.60),
            EvidencePoint("code_correctness", bot_source, support=0.70, confidence=bot_confidence),
            EvidencePoint("ci_verification", "github_actions_ci", support=0.98, confidence=0.85),
            EvidencePoint("delivery_velocity", "cycle_time_model", support=0.20, confidence=0.85),
        ),
        constraint_results={
            "ci_green": True,
            "no_unmitigated_crash_risk": True,
        },
    )

    return DecisionFrame(
        task="pr-merge-gate",
        criteria=criteria,
        options=(approve_option, fix_option, escalate_option),
        constraints=("ci_green", "no_unmitigated_crash_risk"),
        minimum_margin=minimum_margin,
        uncertainty_penalty=0.15,
    )


def print_decision_summary(label: str, result: DecisionResult) -> None:
    print(f"--- {label} ---")
    print(f"  Policy ID / Version : {result.policy_id} (v{result.policy_version})")
    print(f"  Decision Status     : {result.status.value.upper()}")
    winner = (
        result.selected_action.id
        if result.selected_action
        else (result.proposed_action.id if result.proposed_action else "None")
    )
    print(f"  Selected / Proposed : {winner}")
    if result.authorization_basis:
        print(f"  Authorization Basis : {result.authorization_basis}")
    print(f"  Reason              : {result.reason}")
    print("  Option Assessments  :")
    for assessment in result.assessments:
        ru = f"{assessment.robust_utility:+.4f}" if assessment.robust_utility is not None else "   N/A"
        eu = f"{assessment.expected_utility:+.4f}" if assessment.expected_utility is not None else "   N/A"
        unc = f"{assessment.uncertainty:.4f}" if assessment.uncertainty is not None else " N/A"
        ruled = f" (ruled_out_by={list(assessment.ruled_out_by)})" if assessment.ruled_out_by else ""
        print(
            f"    * {assessment.action.id:<22} feasible={str(assessment.feasible):<5} "
            f"expected={eu}  uncertainty={unc}  robust={ru}{ruled}"
        )
    print()


def main() -> None:
    print("\n" + "#" * 82)
    print("  TASKPOLICY + REVIEW TRIAGE CALIBRATION DEMO (ADR-036 / ADR-001)")
    print("#" * 82)

    # ==========================================================================
    # Step 1: Parse Historical Triage Records & Calibrate Reviewer Reliability
    # ==========================================================================
    header("STEP 1: PARSE TRIAGE HISTORY & CALIBRATE WILSON LOWER-BOUND RELIABILITY")

    raw_lines = find_triage_lines(HISTORICAL_IMPLEMENTATION_LOG)
    records: list[TriageRecord] = [
        parse_triage_line(line, reviewers=ORG_REVIEWERS) for line in raw_lines
    ]
    # Also include one reconstructed legacy record from git history
    records.append(
        reconstruct_record(
            "S-180-1",
            claim_type="crash risk",
            verified="yes",
            decision="accepted",
            reason="backfilled from commit history",
            fix="998877a",
            reviewers=ORG_REVIEWERS,
        )
    )

    print(f"Parsed {len(raw_lines)} structured triage lines from implementation-log.md (+1 reconstructed).")
    print("\nReviewer Reliability Table (95% Wilson Lower Bound, min_cases=5):")
    print(
        f"  {'Reviewer':<12} | {'Claim Type':<15} | {'Verified / Cases':<16} | "
        f"{'Empirical Rate':<14} | {'Wilson LB':<10} | {'Calibrated Conf'}"
    )
    print(f"  {'-' * 12}-+-{'-' * 15}-+-{'-' * 16}-+-{'-' * 14}-+-{'-' * 10}-+-{'-' * 15}")

    claim_types_to_check = ("crash risk", "logic error", "documentation", "style")
    calibrated_by_claim: dict[str, Reliability] = {}
    for claim_type in claim_types_to_check:
        rel = reliability(records, reviewer="amazon-q", claim_type=claim_type, min_cases=5)
        calibrated_by_claim[claim_type] = rel
        rate_str = f"{rel.verified / rel.cases:.1%}" if rel.cases else "N/A"
        lb_str = f"{rel.lower_bound:.4f}" if rel.lower_bound is not None else "None (<5)"
        conf_val = calibrated_confidence(rel)
        print(
            f"  {'amazon-q':<12} | {claim_type:<15} | "
            f"{f'{rel.verified} / {rel.cases}':<16} | {rate_str:<14} | {lb_str:<10} | {conf_val:.4f}"
        )

    # ==========================================================================
    # Step 2: Scenario A vs B — Handling a Noisy Bot Claim ('logic error')
    # ==========================================================================
    header("STEP 2: SCENARIO A vs. B — NOISY 'LOGIC ERROR' CLAIM ON A CLEAN PR")

    policy = build_pr_gate_task_policy()
    naive_conf = 0.90
    calibrated_logic_conf = calibrated_confidence(calibrated_by_claim["logic error"])

    print("Incoming PR #207: All unit tests and CI checks pass, but 'amazon-q' posts a")
    print("suspect 'logic error' comment claiming a SHA-256 hex digest is 63 chars instead of 64.\n")

    # Scenario A: Naive static confidence (0.90) -> False-Positive PR Block!
    frame_naive = build_pr_decision_frame(
        policy,
        bot_claim_type="logic error",
        bot_confidence=naive_conf,
    )
    result_naive = policy.decide(frame_naive)
    print_decision_summary(
        f"Scenario A: Naive Uncalibrated Bot Confidence (confidence = {naive_conf:.2f})",
        result_naive,
    )

    # Scenario B: Calibrated Wilson LB confidence (0.05 floor from LB=0.0199) -> Clean Merge!
    frame_calibrated = build_pr_decision_frame(
        policy,
        bot_claim_type="logic error",
        bot_confidence=calibrated_logic_conf,
    )
    result_calibrated = policy.decide(frame_calibrated)
    print_decision_summary(
        f"Scenario B: Wilson-Calibrated Bot Confidence (confidence = {calibrated_logic_conf:.4f})",
        result_calibrated,
    )

    # Compare Calibrated vs. Naive using ADR-005 decision-progress comparison
    all_actions = tuple(policy.snapshot().actions)
    delta = compare_decision_results(
        replace(result_calibrated, candidate_actions=all_actions),
        replace(result_naive, candidate_actions=all_actions),
    )
    print("  [Decision-Progress Comparison: Wilson-Calibrated -> Naive Uncalibrated Override]")
    print(f"    * Classification : {delta.classification.value.upper()} ({delta.classification_reason})")
    print(f"    * Leader Shift   : '{delta.leader_before}' -> '{delta.leader_after}' (leader_changed={delta.leader_changed})")
    print(
        f"    * Margin Delta   : {delta.margin_before:+.4f} -> {delta.margin_after:+.4f} "
        f"({delta.margin_delta:+.4f})"
    )
    if delta.attribution:
        top_attr = delta.attribution[0]
        print(
            f"    * Root-Cause Criterion Attribution : '{top_attr['criterion_id']}' support dropped "
            f"{top_attr['before_support']:.3f} -> {top_attr['after_support']:.3f} ({top_attr['support_delta']:+.3f})"
        )
    print()

    # ==========================================================================
    # Step 3: Scenario C — High-Reliability Claim Type ('crash risk')
    # ==========================================================================
    header("STEP 3: SCENARIO C — GENUINE 'CRASH RISK' CLAIM FROM THE SAME REVIEWER")

    crash_conf = calibrated_confidence(calibrated_by_claim["crash risk"])
    print("Incoming PR #208: 'amazon-q' flags a 'crash risk' (unchecked None dereference).")
    print(f"Because 'amazon-q' has 6/7 verified accuracy on 'crash risk' (Wilson LB = {crash_conf:.4f}),")
    print("the TaskPolicy takes the finding seriously, rules out `approve_merge`, and selects `request_author_fix`:\n")

    frame_crash = build_pr_decision_frame(
        policy,
        bot_claim_type="crash risk",
        bot_confidence=crash_conf,
        unmitigated_crash=True,
    )
    result_crash = policy.decide(frame_crash)
    print_decision_summary(
        f"Scenario C: High-Reliability 'crash risk' Claim (confidence = {crash_conf:.4f})",
        result_crash,
    )

    # ==========================================================================
    # Step 4: Scenario D — Tie-Break Adjudication & Episode Lineage Recording
    # ==========================================================================
    header("STEP 4: HUMAN TIE-BREAK ADJUDICATION & EPISODE METADATA LINEAGE")

    # Suppose an unproven claim type ('documentation', <5 cases -> confidence=0.25)
    # with a strict margin requirement (0.30) triggers NEEDS_USER_TIE_BREAK:
    unproven_conf = calibrated_confidence(calibrated_by_claim["documentation"])
    borderline_frame = build_pr_decision_frame(
        policy,
        bot_claim_type="documentation",
        bot_confidence=unproven_conf,
        minimum_margin=0.30,
    )
    borderline_result = policy.decide(borderline_frame)
    print_decision_summary(
        f"Scenario D1: Unproven Slice (conf={unproven_conf:.2f}, min_margin=0.30) Triggers NEEDS_USER_TIE_BREAK",
        borderline_result,
    )

    # Human maintainer inspects the finding, rejects the false-positive 'request_author_fix'
    # proposal, and accepts the runner-up 'approve_merge'.
    after_reject = policy.adjudicate(borderline_result, TieBreakDisposition.REJECT)
    final_adjudicated = policy.adjudicate(after_reject, TieBreakDisposition.ACCEPT)
    print_decision_summary(
        "Scenario D2: After Human Maintainer Adjudication (REJECT fix -> ACCEPT approve_merge)",
        final_adjudicated,
    )

    # Record the new triage line and attach its metadata to the Episode in storage
    new_triage_line = (
        "Q-207-1 | logic error | verified: no | decision: declined | "
        "sha256 hex digest is 64 chars; verified via len(digest) == 64 | fix: none"
    )
    new_record = parse_triage_line(new_triage_line, reviewers=ORG_REVIEWERS)
    triage_meta = to_episode_metadata(new_record)

    store = InMemoryStore()
    store.store_policy(policy.snapshot())
    capture = EpisodeCapture(
        config=CaptureConfig(
            enabled=True,
            agent_id=policy.snapshot().agent_id,
            task_id=policy.snapshot().task_id,
        ),
        store=store,
    )
    assert final_adjudicated.selected_action is not None
    ctx = capture.start(
        "Evaluate PR #207 merge readiness with triaged reviewer finding Q-207-1",
        task_id=policy.snapshot().task_id,
        intent_summary="Run calibrated PR gate on PR #207",
        action_type="governance_gate",
        action_name=final_adjudicated.selected_action.id,
        expected_outcome="Merge clean PR without false-positive block",
        policy_id=policy.snapshot().id,
        policy_version=policy.snapshot().version,
        action_id=final_adjudicated.selected_action.id,
        metadata={"review_triage": triage_meta},
    )
    episode = capture.end(
        ctx,
        assistant_output=f"Selected {final_adjudicated.selected_action.id} ({final_adjudicated.authorization_basis})",
        execution_status="completed",
        result_summary=final_adjudicated.reason,
    )

    print("Recorded Episode with Structured Triage Metadata:")
    print(
        json.dumps(
            {
                "episode_id": episode.id,
                "agent_id": episode.agent_id,
                "task_id": episode.task_id,
                "action_id": episode.action_id,
                "authorization_basis": final_adjudicated.authorization_basis,
                "review_triage": episode.metadata.get("review_triage"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
