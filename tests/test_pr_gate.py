"""Contract test suite for scripts/pr_gate.py (PR Review & Approval Gatekeeper).

Covers:
- Unstructured review text parsing into Epic 14 critique grammar.
- CI status check enforcement.
- Invariant 6 (Upstream Fork Purity) enforcement.
- Bayesian decision resolution and robust utility thresholding.
- Command-line interface and reporting.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from agent_learning.storage.local import LocalFileStore
from agent_learning_ext.learners.pairwise import pairs_from_episodes
from scripts.pr_gate import (
    build_decision_frame,
    convert_unstructured_review_to_tags,
    evaluate_pr,
    extract_raw_review_texts,
    main,
)


def test_convert_pretagged_lines() -> None:
    text = "- [criterion: correctness] [claim: logic error] [verified: yes] [finding: Q-1]: Off-by-one error."
    tags = convert_unstructured_review_to_tags("reviewer", text)
    assert len(tags) == 1
    assert "[criterion: correctness]" in tags[0]
    assert "[finding: Q-1]" in tags[0]


def test_convert_amazon_q_blocking_issues() -> None:
    text = """
### Blocking issues found
1. Unhandled AttributeError when metadata dictionary is None.
2. Missing test coverage for negative logits input.
3. Unused import `sys` in runner.py.
4. Calculation logic does not compute posterior normalization correctly.
"""
    tags = convert_unstructured_review_to_tags("amazon-q", text, source_prefix="TEST")
    assert len(tags) == 4

    # 1. Crash risk -> correctness
    assert "[criterion: correctness]" in tags[0]
    assert "[claim: crash risk]" in tags[0]
    assert "[finding: TEST-CRIT-1]" in tags[0]

    # 2. Test gap -> test_coverage
    assert "[criterion: test_coverage]" in tags[1]
    assert "[claim: test gap]" in tags[1]
    assert "[finding: TEST-CRIT-2]" in tags[1]

    # 3. Style -> implementation_quality
    assert "[criterion: implementation_quality]" in tags[2]
    assert "[claim: style]" in tags[2]
    assert "[finding: TEST-CRIT-3]" in tags[2]

    # 4. Logic error -> correctness
    assert "[criterion: correctness]" in tags[3]
    assert "[claim: logic error]" in tags[3]
    assert "[finding: TEST-CRIT-4]" in tags[3]


def test_convert_amazon_q_remaining_items_table() -> None:
    text = """
### ⚠️ Remaining / open items
| # | Finding | Notes |
|---|---|---|
| 1 | Test coverage on float tolerances | Needs additional tests |
| 2 | Refactor loop variable | Code clarity |
"""
    tags = convert_unstructured_review_to_tags("amazon-q", text, source_prefix="TEST")
    assert len(tags) == 2
    assert "[criterion: test_coverage]" in tags[0]
    assert "[claim: test gap]" in tags[0]
    assert "[finding: TEST-OPEN-1]" in tags[0]

    assert "[criterion: implementation_quality]" in tags[1]
    assert "[claim: logic error]" in tags[1]
    assert "[finding: TEST-OPEN-2]" in tags[1]


def test_convert_amazon_q_resolved_items_table() -> None:
    text = """
### ✅ Resolved in this commit
| # | Finding | Notes |
|---|---|---|
| 1 | Invariant 6 Upstream Purity | Upstream files left untouched |
| 2 | Robust Bayesian inference | Verified mathematically |
"""
    tags = convert_unstructured_review_to_tags("amazon-q", text, source_prefix="TEST")
    assert len(tags) == 2
    assert "[criterion: upstream_fork_purity]" in tags[0]
    assert "[claim: confirmation]" in tags[0]
    assert "[finding: TEST-RES-1]" in tags[0]

    assert "[criterion: correctness]" in tags[1]
    assert "[claim: confirmation]" in tags[1]
    assert "[finding: TEST-RES-2]" in tags[1]


def test_convert_amazon_q_clean_verdict() -> None:
    text = "Review Summary: All checks pass and no blocking issues found. Code looks correct."
    tags = convert_unstructured_review_to_tags("amazon-q", text, source_prefix="TEST")
    assert len(tags) == 1
    assert "[criterion: correctness]" in tags[0]
    assert "[claim: confirmation]" in tags[0]
    assert "[finding: TEST-CONFIRM]" in tags[0]


def test_extract_raw_review_texts_bot_latest() -> None:
    pr_data = {
        "reviews": [
            {"author": {"login": "amazon-q[bot]"}, "body": "Initial review: Review Summary\nBlocking issues found\n1. Bug"},
            {"author": {"login": "amazon-q[bot]"}, "body": "Second review: Review Summary\nNo blocking issues found."},
        ],
        "comments": [
            {"author": {"login": "maintainer"}, "body": "Please address the comment."},
        ],
    }
    sources = extract_raw_review_texts(pr_data)
    authors = [author for author, _ in sources]
    assert "amazon-q[bot]" in authors
    assert "maintainer" in authors

    q_body = next(body for author, body in sources if author == "amazon-q[bot]")
    assert "Second review" in q_body
    assert "Initial review" not in q_body


def test_build_decision_frame_weights_sum_to_one() -> None:
    frame = build_decision_frame(123)
    total_weight = sum(c.weight for c in frame.criteria)
    assert total_weight == pytest.approx(1.0)
    option_ids = {opt.action.id for opt in frame.options}
    assert option_ids == {"approve_and_merge", "request_revisions"}


def test_evaluate_pr_ci_check_failure() -> None:
    mock_pr = {
        "title": "Fix bug",
        "headRefOid": "abc1234",
        "statusCheckRollup": [
            {"name": "test", "conclusion": "FAILURE"},
            {"name": "build-installer", "conclusion": "SUCCESS"},
        ],
        "files": [],
        "reviews": [],
        "comments": [],
    }
    with patch("scripts.pr_gate.fetch_pr_data", return_value=mock_pr):
        passed, reason, details = evaluate_pr(123)
        assert passed is False
        assert "CI check failure: test" in reason
        assert "test" in details.get("ci_failures", [])


def test_evaluate_pr_invariant_6_violation() -> None:
    mock_pr = {
        "title": "Modify upstream directly",
        "headRefOid": "abc1234",
        "statusCheckRollup": [
            {"name": "test", "conclusion": "SUCCESS"},
        ],
        "files": [
            {"path": "src/agent_learning/core.py"},
        ],
        "reviews": [],
        "comments": [],
    }
    with patch("scripts.pr_gate.fetch_pr_data", return_value=mock_pr):
        passed, reason, details = evaluate_pr(123)
        assert passed is False
        assert "Invariant 6 Violation" in reason
        assert "src/agent_learning/core.py" in details.get("upstream_violations", [])


def test_evaluate_pr_clean_pass() -> None:
    mock_pr = {
        "title": "Clean Story Delivery",
        "headRefOid": "abc1234",
        "statusCheckRollup": [
            {"name": "test", "conclusion": "SUCCESS"},
            {"name": "build-installer", "conclusion": "SUCCESS"},
        ],
        "files": [
            {"path": "src/agent_learning_ext/learner.py"},
            {"path": "tests/test_learner.py"},
        ],
        "reviews": [
            {
                "author": {"login": "amazon-q[bot]"},
                "body": "Review Summary: All checks pass. No blocking issues found. Code looks correct.",
            }
        ],
        "comments": [],
    }
    with patch("scripts.pr_gate.fetch_pr_data", return_value=mock_pr):
        passed, reason, details = evaluate_pr(123)
        assert passed is True
        assert details["selected_action"] == "approve_and_merge"
        assert details["margin"] >= 0.05
        assert "Approved" in reason


def test_evaluate_pr_blocking_critique_halts() -> None:
    mock_pr = {
        "title": "Unsafe PR",
        "headRefOid": "abc1234",
        "statusCheckRollup": [
            {"name": "test", "conclusion": "SUCCESS"},
        ],
        "files": [
            {"path": "src/agent_learning_ext/feature.py"},
        ],
        "reviews": [
            {
                "author": {"login": "amazon-q[bot]"},
                "body": """Review Summary
### Blocking issues found
1. Unhandled exception crash risk in production code.
2. Logic error causing invalid state transitions.
""",
            }
        ],
        "comments": [],
    }
    with patch("scripts.pr_gate.fetch_pr_data", return_value=mock_pr):
        passed, reason, details = evaluate_pr(123)
        assert passed is False
        assert "Halted" in reason
        assert details["margin"] < 0.05


def test_cli_main_json_output(capsys: pytest.CaptureFixture[str]) -> None:
    mock_eval = (
        True,
        "Approved with robust utility 0.700",
        {"pr_number": 999, "margin": 0.15, "title": "Test PR"},
    )
    with patch("sys.argv", ["pr_gate.py", "999", "--json"]), patch(
        "scripts.pr_gate.evaluate_pr", return_value=mock_eval
    ):
        code = main()
        assert code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["passed"] is True
        assert data["details"]["pr_number"] == 999


def test_cli_main_early_halt_output(capsys: pytest.CaptureFixture[str]) -> None:
    mock_eval = (
        False,
        "Invariant 6 Violation: Pull request modifies upstream files",
        {"pr_number": 999, "title": "Test PR", "upstream_violations": ["src/agent_learning/core.py"]},
    )
    with patch("sys.argv", ["pr_gate.py", "999"]), patch(
        "scripts.pr_gate.evaluate_pr", return_value=mock_eval
    ):
        code = main()
        assert code == 1
        captured = capsys.readouterr()
        assert "GATE RESULT: HALTED" in captured.out
        assert "Decision Margin: N/A" in captured.out


def test_evaluate_pr_passive_episode_storage_accepted(tmp_path: Path) -> None:
    mock_pr = {
        "title": "Clean Story Delivery",
        "headRefOid": "abc12345678",
        "statusCheckRollup": [{"name": "test", "conclusion": "SUCCESS"}],
        "files": [{"path": "src/agent_learning_ext/learner.py"}],
        "reviews": [
            {
                "author": {"login": "amazon-q[bot]"},
                "body": "Review Summary: All checks pass. No blocking issues found.",
            }
        ],
        "comments": [],
    }
    with patch("scripts.pr_gate.fetch_pr_data", return_value=mock_pr):
        passed, _, details = evaluate_pr(101, store_dir=tmp_path, persist_episode=True)
        assert passed is True
        ep_id = details.get("episode_id")
        assert ep_id is not None

        # Verify persisted in LocalFileStore
        store = LocalFileStore(root_dir=tmp_path)
        ep = store.get_episode(ep_id, "agent-learning-governance")
        assert ep is not None
        assert ep.action_id == "approve_and_merge"
        assert ep.metadata.get("feedback_status") == "accepted"
        assert ep.metadata.get("pr_number") == 101

        # Accepted episodes contribute no preference pairs
        pairs = pairs_from_episodes([ep], ["approve_and_merge", "request_revisions"])
        assert len(pairs) == 0


def test_evaluate_pr_passive_episode_storage_rejected_yields_preference_pair(tmp_path: Path) -> None:
    mock_pr = {
        "title": "Buggy PR",
        "headRefOid": "bad98765432",
        "statusCheckRollup": [{"name": "test", "conclusion": "SUCCESS"}],
        "files": [{"path": "src/agent_learning_ext/buggy.py"}],
        "reviews": [
            {
                "author": {"login": "amazon-q[bot]"},
                "body": """Review Summary
### Blocking issues found
1. Unhandled exception crash risk in production code.
2. Logic error causing invalid state transitions.
""",
            }
        ],
        "comments": [],
    }
    with patch("scripts.pr_gate.fetch_pr_data", return_value=mock_pr):
        passed, _, details = evaluate_pr(102, store_dir=tmp_path, persist_episode=True)
        assert passed is False
        ep_id = details.get("episode_id")
        assert ep_id is not None

        # Verify persisted in LocalFileStore
        store = LocalFileStore(root_dir=tmp_path)
        ep = store.get_episode(ep_id, "agent-learning-governance")
        assert ep is not None
        assert ep.action_id == "approve_and_merge"
        assert ep.metadata.get("feedback_status") == "rejected"
        assert ep.metadata.get("correct_action_id") == "request_revisions"

        # Rejected episodes naturally yield Bradley-Terry preference pairs!
        pairs = pairs_from_episodes([ep], ["approve_and_merge", "request_revisions"])
        assert len(pairs) == 1
        assert pairs[0].winner == "request_revisions"
        assert pairs[0].loser == "approve_and_merge"
        assert pairs[0].source_episode_id == ep_id


def test_evaluate_pr_passive_episode_storage_ci_failure(tmp_path: Path) -> None:
    mock_pr = {
        "title": "Failing CI PR",
        "headRefOid": "ci000111",
        "statusCheckRollup": [{"name": "test", "conclusion": "FAILURE"}],
        "files": [{"path": "src/agent_learning_ext/mod.py"}],
        "reviews": [],
        "comments": [],
    }
    with patch("scripts.pr_gate.fetch_pr_data", return_value=mock_pr):
        passed, _, details = evaluate_pr(103, store_dir=tmp_path, persist_episode=True)
        assert passed is False
        ep_id = details.get("episode_id")
        assert ep_id is not None

        store = LocalFileStore(root_dir=tmp_path)
        ep = store.get_episode(ep_id, "agent-learning-governance")
        assert ep is not None
        assert ep.metadata.get("feedback_status") == "rejected"
        assert ep.metadata.get("correct_action_id") == "request_revisions"


def test_evaluate_pr_no_store_flag(tmp_path: Path) -> None:
    mock_pr = {
        "title": "No store PR",
        "headRefOid": "nostore1",
        "statusCheckRollup": [{"name": "test", "conclusion": "SUCCESS"}],
        "files": [{"path": "src/agent_learning_ext/clean.py"}],
        "reviews": [
            {
                "author": {"login": "amazon-q[bot]"},
                "body": "Review Summary: All checks pass. No blocking issues found.",
            }
        ],
        "comments": [],
    }
    with patch("scripts.pr_gate.fetch_pr_data", return_value=mock_pr):
        passed, _, details = evaluate_pr(104, store_dir=tmp_path, persist_episode=False)
        assert passed is True
        assert details.get("episode_id") is None
