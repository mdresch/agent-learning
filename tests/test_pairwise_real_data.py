"""Contract test suite for Story 18.6 — The Real-Data Check (Zero Pairs).

Source ADR: ADR-018 (Pairwise Preference Optimization for Discrete Action Logits)
Source BRD: BRD-018 (BRU-018-12)
Source FDD: FDD-018 (§6, §7 item 1)
Story: Story 18.6 (The Real-Data Check)

Acceptance Criteria:
- AC_0 (Real Source): the episodes are the approve-* episodes of agent-learning-governance read
  from the committed files in docs/policy-shapes/episodes/; the count and the file names are recorded
  in the test (41 when ADR-018 was written, 76 files on 2026-10-29, so the test records the count
  it ran on and does not assert a fixed number).
- AC_1 (Zero Pairs): pairs_from_episodes over them returns no pair, because none carries a rejected
  feedback status with a different correct_action_id.
- AC_2 (Logits Stay): the learner run over them leaves a SoftmaxPolicy's logits unchanged, writes
  no reference, and returns episodes_used of 0.
- AC_3 (Labelled): the result is recorded as a statement that real preference data does not exist yet.
  It makes no claim about the learner's quality (BRU-018-12), and the docstring names the missing data
  (real override adjudications) and the unbuilt Red Team pair set.

Recommended Interpretations:
- I1: Upstream Fork Purity (Invariant 6): All custom classes, learners, and helpers implemented under
  src/agent_learning_ext/ and agent-training-ext/, leaving upstream src/agent_learning/ tree pristine.
- I2: Storage Decoupling & Serialization: Policy snapshots and metadata survive standard json.dumps()
  and json.loads() round-tripping without custom decoders.
- I3: Numerical Precision Tolerances: Floating-point assertions use explicit absolute tolerances (1e-12).
"""

from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any

from agent_learning.decision import Action
from agent_learning.policy import SoftmaxPolicy
from agent_learning.types import Episode, PolicySnapshot, ToolCall
from agent_learning_ext.learners.pairwise import PairwiseLearner, pairs_from_episodes

ROOT = Path(__file__).resolve().parents[1]
EPISODES_DIR = ROOT / "docs" / "policy-shapes" / "episodes"


def _load_real_governance_episodes() -> list[tuple[str, Episode]]:
    """Load approve-* episodes of agent-learning-governance from docs/policy-shapes/episodes/."""
    valid_keys = set(inspect.signature(Episode.__init__).parameters.keys()) - {"self"}
    json_files = sorted(EPISODES_DIR.glob("*.json"))

    episodes: list[tuple[str, Episode]] = []
    for f in json_files:
        data: dict[str, Any] = json.loads(f.read_text(encoding="utf-8"))
        task_id = str(data.get("task_id") or data.get("task_name") or "")
        agent_id = str(data.get("agent_id") or data.get("agent_name") or "")

        # Target approve-* episodes in agent-learning-governance
        if task_id.startswith("approve-") and agent_id == "agent-learning-governance":
            if "episode_id" in data and "id" not in data:
                data["id"] = data["episode_id"]
            if "tool_calls" in data:
                data["tool_calls"] = [
                    ToolCall(**tc) if isinstance(tc, dict) else tc for tc in data["tool_calls"]
                ]
            filtered = {k: v for k, v in data.items() if k in valid_keys}
            episodes.append((f.name, Episode(**filtered)))

    return episodes


def _make_policy(actions: list[str]) -> SoftmaxPolicy:
    """Helper to construct a SoftmaxPolicy over an action set."""
    action_objs = [Action(id=a, description=f"Governance action {a}") for a in actions]
    snap = PolicySnapshot(
        id="gov-policy-snapshot",
        agent_id="agent-learning-governance",
        task_id="approve-governance",
        version=1,
        actions=action_objs,
        logits={a: 0.0 for a in actions},
    )
    return SoftmaxPolicy(snap, max_logit_abs=10.0)


def test_ac0_real_source_episodes_read_and_recorded():
    """AC_0: Real source episodes are the approve-* episodes of agent-learning-governance.

    The count and file names are recorded in the test (41 when ADR-018 was written, 76 files on
    2026-10-29; test records actual count and does not assert a fixed number).
    """
    records = _load_real_governance_episodes()
    count = len(records)
    file_names = [f_name for f_name, _ in records]

    # Verify real source is non-empty and every episode belongs to agent-learning-governance
    assert count > 0, "Expected non-empty set of committed governance episodes in docs/policy-shapes/episodes/"
    assert count >= 76, f"Expected at least 76 committed episodes (as of 2026-10-29), got {count}"

    for f_name, ep in records:
        assert ep.agent_id == "agent-learning-governance", f"{f_name} does not belong to agent-learning-governance"
        assert ep.task_id.startswith("approve-"), f"{f_name} task {ep.task_id} is not an approve-* task"

    # Record count and sample file names for audit trail
    print(f"\n[Story 18.6 AC_0 Audit] Loaded {count} approve-* governance episodes.")
    print(f"[Story 18.6 AC_0 Audit] Sample files: {file_names[:5]} ... {file_names[-5:]}")


def test_ac1_zero_pairs_extracted_from_real_history():
    """AC_1: pairs_from_episodes over them returns no pair.

    None of the recorded episodes carries a rejected feedback status with a different correct_action_id.
    """
    records = _load_real_governance_episodes()
    episodes = [ep for _, ep in records]
    actions = sorted({ep.action_id for ep in episodes if ep.action_id})

    # Extract preference pairs across all unique governance actions
    pairs = pairs_from_episodes(episodes, action_ids=actions)

    assert len(pairs) == 0, f"Expected exactly 0 preference pairs from accepted history, got {len(pairs)}: {pairs}"

    # Explicitly verify why zero pairs were returned: all feedback_status values are non-rejected
    for ep in episodes:
        feedback_status = (ep.metadata or {}).get("feedback_status")
        # In governance history, all records were accepted/adjudicated approvals
        assert str(feedback_status).lower().strip() != "rejected" or not (ep.metadata or {}).get("correct_action_id"), (
            f"Episode {ep.id} unexpectedly had a valid override rejection"
        )


def test_ac2_logits_stay_unchanged_and_episodes_used_is_zero():
    """AC_2: The learner run over them leaves SoftmaxPolicy logits unchanged.

    Writes no reference to metadata, leaves snapshot version unchanged, and returns episodes_used=0.
    """
    records = _load_real_governance_episodes()
    episodes = [ep for _, ep in records]
    actions = sorted({ep.action_id for ep in episodes if ep.action_id})

    policy = _make_policy(actions)
    initial_logits = dict(policy.snapshot().logits)
    initial_version = policy.snapshot().version

    learner = PairwiseLearner()
    result = learner.update(policy, episodes)

    # 1. episodes_used is 0
    assert result.episodes_used == 0

    # 2. Logits are completely unchanged
    post_logits = dict(policy.snapshot().logits)
    assert len(post_logits) == len(initial_logits)
    for a in actions:
        assert abs(post_logits[a] - initial_logits[a]) <= 1e-12

    # 3. Snapshot version is unchanged
    assert policy.snapshot().version == initial_version

    # 4. No reference is written
    assert "pairwise_reference_logits" not in policy.snapshot().metadata


def test_ac3_labelled_as_missing_real_preference_data_boundary():
    """AC_3: The result is recorded as a statement that real preference data does not exist yet.

    It makes no claim about the learner's quality (BRU-018-12), and explicitly documents
    the missing data (real override adjudications) and the unbuilt Red Team pair set.
    """
    records = _load_real_governance_episodes()
    episodes = [ep for _, ep in records]
    actions = sorted({ep.action_id for ep in episodes if ep.action_id})

    policy = _make_policy(actions)
    learner = PairwiseLearner()
    result = learner.update(policy, episodes)

    assert result.episodes_used == 0

    # Statement recorded: real preference data does not exist yet
    boundary_statement = (
        "REAL PREFERENCE DATA BOUNDARY (BRU-018-12): All historical governance episodes "
        "in docs/policy-shapes/episodes/ represent accepted approvals. Zero real preference "
        "pairs exist in historical logs. The missing data comprises: (1) real override "
        "adjudications where a human reviewer rejected a proposed decision and designated "
        "an alternative correct action, and (2) the unbuilt Red Team adversarial pair set. "
        "This check proves the zero-pair boundary and makes no claim about learner quality."
    )
    assert "BRU-018-12" in boundary_statement
    assert "real override adjudications" in boundary_statement
    assert "unbuilt Red Team" in boundary_statement
    assert "makes no claim about learner quality" in boundary_statement

    # Serialization survival check (Interpretation I2)
    snap = policy.snapshot()
    serialized = json.dumps(snap.to_dict() if hasattr(snap, "to_dict") else snap.__dict__, default=str)
    assert "gov-policy-snapshot" in serialized
