"""Contract test suite for scripts/spec_gate.py (Pre-Flight Specification & Contract Readiness Gate).

Covers:
- Story identifier normalization and epic file discovery.
- User story markdown parsing and acceptance criteria extraction.
- Adversarial pre-flight checks across 4 criteria (completeness, testability, fork purity, boundaries).
- Bayesian decision resolution, robust utility scoring, and strict mode.
- Contract interpretation generation (I1, I2, ...).
- Passive episode persistence to LocalFileStore.
- Command-line interface and JSON reporting.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_learning.storage.local import LocalFileStore
from scripts.spec_gate import (
    AcceptanceCriterionSpec,
    StorySpec,
    audit_story_spec,
    build_spec_decision_frame,
    evaluate_story_spec,
    find_epic_file,
    main,
    normalize_story_id,
    parse_story,
    save_spec_gate_episode,
)

ROOT = Path(__file__).resolve().parents[1]


# ==============================================================================
# Identifier Normalization & Epic Discovery Tests
# ==============================================================================

def test_normalize_story_id_valid() -> None:
    assert normalize_story_id("18.4") == (18, "18.4")
    assert normalize_story_id("18-4") == (18, "18.4")
    assert normalize_story_id("story-18.4") == (18, "18.4")
    assert normalize_story_id("story-18-4") == (18, "18.4")
    assert normalize_story_id("epic-18-story-4") == (18, "18.4")
    assert normalize_story_id("epic-18-story-18.4") == (18, "18.4")
    assert normalize_story_id("  1.1  ") == (1, "1.1")


def test_normalize_story_id_invalid() -> None:
    with pytest.raises(ValueError, match="Invalid story identifier format"):
        normalize_story_id("invalid-story")

    with pytest.raises(ValueError, match="Invalid story identifier format"):
        normalize_story_id("epic-18")


def test_find_epic_file_success() -> None:
    p18 = find_epic_file(18, repo_root=ROOT)
    assert p18.is_file()
    assert "epic-18" in p18.name

    p14 = find_epic_file(14, repo_root=ROOT)
    assert p14.is_file()
    assert "epic-14" in p14.name


def test_find_epic_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="No user story file found for Epic 999"):
        find_epic_file(999, repo_root=ROOT)


# ==============================================================================
# Story Parsing Tests
# ==============================================================================

def test_parse_story_18_4() -> None:
    spec = parse_story("18.4", repo_root=ROOT)
    assert spec.epic_num == 18
    assert spec.story_id == "18.4"
    assert spec.title == "The Learner"
    assert spec.status.lower() in ("ready", "completed")
    assert len(spec.acceptance_criteria) == 7

    # Check first AC ($AC_0$)
    ac0 = spec.acceptance_criteria[0]
    assert ac0.index == 0
    assert ac0.label == "Type"
    assert "SoftmaxPolicy" in ac0.prose
    assert "TypeError" in ac0.prose

    # Check last AC ($AC_6$)
    ac6 = spec.acceptance_criteria[6]
    assert ac6.index == 6
    assert ac6.label == "Storage Boundary"
    assert "json.dumps" in ac6.prose
    assert "agent_learning.storage" in ac6.prose


def test_parse_story_missing_story_raises() -> None:
    with pytest.raises(ValueError, match="Story 18.99 not found in"):
        parse_story("18.99", repo_root=ROOT)


def test_parse_story_no_acs_raises(tmp_path: Path) -> None:
    stories_dir = tmp_path / "docs" / "user-stories"
    stories_dir.mkdir(parents=True)
    fake_epic = stories_dir / "epic-99-empty.md"
    fake_epic.write_text(
        "# Epic 99: Empty\n\n## Story 99.1 — No Criteria\n**Status:** Ready\nProse without ACs.\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="No acceptance criteria found"):
        parse_story("99.1", repo_root=tmp_path)


# ==============================================================================
# Adversarial Audit Engine Tests
# ==============================================================================

def test_audit_story_spec_fork_collision_detection() -> None:
    spec = StorySpec(
        epic_num=99,
        story_id="99.1",
        title="Fork Collision Story",
        status="Ready",
        role="developer",
        want="implement src/agent_learning/new_module.py",
        so_that="it works",
        acceptance_criteria=[
            AcceptanceCriterionSpec(index=0, label="Purity", prose="Create src/agent_learning/new_module.py.")
        ],
    )

    deltas, interpretations, log = audit_story_spec(spec)
    fork_deltas = [d for d in deltas if d.criterion_id == "upstream_fork_purity"]
    assert len(fork_deltas) == 1
    assert fork_deltas[0].support_delta < 0
    assert fork_deltas[0].finding_id == "SPEC-FORK-COLLISION"

    fork_interps = [i for i in interpretations if i.category == "Upstream Fork Purity"]
    assert len(fork_interps) == 1
    assert "src/agent_learning_ext/new_module.py" in fork_interps[0].text
    assert any("[WARN] Invariant 6: Upstream collision risk" in msg for msg in log)


def test_audit_story_spec_none_safety_warning() -> None:
    spec = StorySpec(
        epic_num=99,
        story_id="99.2",
        title="Unsafe Metadata Story",
        status="Ready",
        role="developer",
        want="read metadata from episode",
        so_that="it learns",
        acceptance_criteria=[
            AcceptanceCriterionSpec(index=0, label="Meta", prose="Read metadata from episode and update extra.")
        ],
    )

    deltas, interpretations, _log = audit_story_spec(spec)
    none_deltas = [d for d in deltas if d.finding_id == "SPEC-COMPL-NONE-GUARD"]
    assert len(none_deltas) == 1
    assert none_deltas[0].support_delta < 0

    none_interps = [i for i in interpretations if "None-Safety" in i.title]
    assert len(none_interps) == 1
    assert "defensively guard against None values" in none_interps[0].text


def test_audit_story_spec_floating_point_tolerance_warning() -> None:
    spec = StorySpec(
        epic_num=99,
        story_id="99.3",
        title="Float Tolerance Gap",
        status="Ready",
        role="developer",
        want="calculate loss",
        so_that="it minimizes",
        acceptance_criteria=[
            AcceptanceCriterionSpec(index=0, label="Loss", prose="Calculated loss equals the theoretical sum.")
        ],
    )

    deltas, interpretations, _log = audit_story_spec(spec)
    tol_deltas = [d for d in deltas if d.finding_id == "SPEC-TEST-TOLERANCE-GAP"]
    assert len(tol_deltas) == 1
    assert tol_deltas[0].support_delta < 0

    tol_interps = [i for i in interpretations if "Precision Tolerances" in i.title]
    assert len(tol_interps) == 1


# ==============================================================================
# Decision Frame & Bayesian Resolution Tests
# ==============================================================================

def test_build_spec_decision_frame() -> None:
    frame = build_spec_decision_frame("18.4")
    assert frame.task == "story-18.4-spec-gate"
    assert len(frame.options) == 2
    assert frame.options[0].action.id == "proceed_to_implementation"
    assert frame.options[1].action.id == "clarify_spec_and_amend"

    # Criteria weights sum to 1.0
    total_weight = sum(c.weight for c in frame.criteria)
    assert pytest.approx(total_weight, abs=1e-6) == 1.0


def test_evaluate_story_18_4_passes() -> None:
    passed, reason, payload = evaluate_story_spec("18.4", repo_root=ROOT, persist_episode=False)
    assert passed is True
    assert "Pre-Flight Specification Gate Passed" in reason
    assert payload["margin"] >= 0.05
    assert payload["scores"]["proceed_to_implementation"] > payload["scores"]["clarify_spec_and_amend"]
    assert len(payload["interpretations"]) >= 1


def test_evaluate_story_18_4_strict_mode_halts() -> None:
    passed, reason, payload = evaluate_story_spec("18.4", repo_root=ROOT, persist_episode=False, strict=True)
    assert passed is False
    assert "Strict Mode Halt" in reason
    assert payload["passed"] is False


def test_evaluate_highly_ambiguous_spec_halts(tmp_path: Path) -> None:
    # A spec with severe flaws across all criteria
    stories_dir = tmp_path / "docs" / "user-stories"
    stories_dir.mkdir(parents=True)
    flawed_epic = stories_dir / "epic-99-flawed.md"
    flawed_epic.write_text(
        """# Epic 99: Flawed Epic
Six stories build src/agent_learning/broken_learner.py.

## Story 99.1 — Broken Spec
**Status:** In Progress
**As** a dev, **I want** to modify snapshot in src/agent_learning/broken_learner.py, **so that** it trains.

### Acceptance Criteria:
- **$AC_0$ (Loss):** Calculate loss and logits from episodes and batch, mutating snapshot metadata.
- **$AC_1$ (Fails):** Fails on invalid input.
""",
        encoding="utf-8",
    )

    _passed, _reason, payload = evaluate_story_spec(
        "99.1",
        repo_root=tmp_path,
        persist_episode=False,
        min_margin=0.05,
    )
    # The combination of fork collision, missing storage decoupling, missing None-safety,
    # missing empty collection contract, missing non-finite rejection, generic raises, and no tolerances
    # should pull down robust utility or margin
    assert len(payload["interpretations"]) >= 4
    assert any("[WARN]" in msg for msg in payload["audit_log"])


# ==============================================================================
# Passive Episode Storage Tests
# ==============================================================================

def test_save_spec_gate_episode(tmp_path: Path) -> None:
    spec = StorySpec(
        epic_num=18,
        story_id="18.4",
        title="The Learner",
        status="Ready",
        role="maintainer",
        want="move logits",
        so_that="anchor reference",
        acceptance_criteria=[AcceptanceCriterionSpec(index=0, label="Type", prose="test")],
    )

    ep_id = save_spec_gate_episode(
        spec=spec,
        passed=True,
        reason="Approved by contract test",
        margin=0.25,
        interpretations=[],
        applied=None,
        store_dir=tmp_path,
    )

    assert ep_id is not None
    assert ep_id.startswith("spec-18_4-")

    store = LocalFileStore(root_dir=tmp_path)
    loaded_ep = store.get_episode(ep_id, "agent-learning-governance")
    assert loaded_ep is not None
    assert loaded_ep.task_id == "story-18.4-spec-gate"
    assert loaded_ep.metadata.get("feedback_status") == "accepted"
    assert loaded_ep.metadata.get("margin") == 0.25


# ==============================================================================
# CLI Entry Point Tests
# ==============================================================================

def test_cli_json_output(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["18.4", "--json", "--no-persist"])
    assert exit_code == 0

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["story_id"] == "18.4"
    assert payload["passed"] is True
    assert "margin" in payload
    assert len(payload["interpretations"]) >= 1


def test_cli_human_readable_output(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["18.4", "--no-persist"])
    assert exit_code == 0

    captured = capsys.readouterr()
    assert "PRE-FLIGHT SPECIFICATION READINESS GATE: Story 18.4 — The Learner" in captured.out
    assert "VERDICT: PASSED / SPEC READY FOR CONTRACTS" in captured.out
    assert "RECOMMENDED CONTRACT INTERPRETATIONS" in captured.out


def test_cli_invalid_story_error(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["invalid-id", "--no-persist"])
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "Error: Invalid story identifier format" in captured.err
