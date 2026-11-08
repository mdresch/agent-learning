"""Contract tests for Story 18.1 — Pairs From Episodes.

Source ADR: ADR-018 (Pairwise Preference Optimization for Discrete Action Logits)
Source BRD: BRD-018 (BRU-018-01, BRU-018-02, BRU-018-07, BRU-018-11)
Source FDD: FDD-018 (§2.2, §3 item 1, G3, G5)
Story: Story 18.1 (Pairs From Episodes)

Acceptance Criteria:
- AC_0 (Override): an episode with feedback_status "rejected", an action_id of "y"
  and a correct_action_id of "x" gives the pair (winner "x", loser "y") with its episode id;
  " Rejected " is read the same way.
- AC_1 (No Pair): an accepted episode, a rejected one with no correct_action_id,
  one whose correct_action_id equals action_id, one whose correct_action_id or action_id
  is outside action_ids, and one whose correct_action_id is not a string each give no pair and no error.
- AC_2 (Not The ADR Field): an episode with decision_disposition "modify" but no feedback_status
  of rejected gives no pair (the field ADR-018 names is not read; FDD-018 G3).
- AC_3 (Once): the same episode id offered twice gives one pair; the order of the pairs
  is the order of first appearance.
- AC_4 (Inputs Untouched): the episodes are equal to their deep copies after the call.
"""

from copy import deepcopy
import pytest

from agent_learning.types import Episode
from agent_learning_ext.learners.pairwise import PreferencePair, pairs_from_episodes


def _make_episode(
    episode_id: str,
    action_id: str,
    feedback_status: str | None = None,
    correct_action_id: object = None,
    decision_disposition: str | None = None,
) -> Episode:
    metadata: dict[str, object] = {}
    if feedback_status is not None:
        metadata["feedback_status"] = feedback_status
    if correct_action_id is not None:
        metadata["correct_action_id"] = correct_action_id
    if decision_disposition is not None:
        metadata["decision_disposition"] = decision_disposition
    return Episode(
        id=episode_id,
        agent_id="test-agent",
        task_id="test-task",
        user_input="test-input",
        assistant_output="test-output",
        intent_summary="test-intent",
        action_type="recommendation",
        action_name=action_id,
        target="test-target",
        input_summary="test-summary",
        expected_outcome="test-outcome",
        execution_status="completed",
        result_summary="test-result",
        policy_id="test-policy",
        policy_version=1,
        action_id=action_id,
        metadata=metadata,
    )


def test_ac0_override_pair():
    """AC_0: Rejected feedback with different correct_action_id yields pair with winner, loser, and id."""
    action_ids = ["x", "y", "z"]
    ep1 = _make_episode("ep-1", action_id="y", feedback_status="rejected", correct_action_id="x")
    pairs = pairs_from_episodes([ep1], action_ids)
    assert len(pairs) == 1
    assert pairs[0] == PreferencePair(winner="x", loser="y", source_episode_id="ep-1")

    # Whitespace and capitalization tolerance: " Rejected "
    ep2 = _make_episode("ep-2", action_id="y", feedback_status=" Rejected ", correct_action_id="x")
    pairs2 = pairs_from_episodes([ep2], action_ids)
    assert len(pairs2) == 1
    assert pairs2[0] == PreferencePair(winner="x", loser="y", source_episode_id="ep-2")


def test_ac1_no_pair_conditions():
    """AC_1: Filter cases that must produce no pair and raise no error."""
    action_ids = ["x", "y", "z"]

    episodes = [
        # 1. accepted episode
        _make_episode("ep-accepted", action_id="y", feedback_status="accepted", correct_action_id="x"),
        # 2. rejected with no correct_action_id
        _make_episode("ep-no-correct", action_id="y", feedback_status="rejected"),
        # 3. correct_action_id equals action_id
        _make_episode("ep-same-action", action_id="y", feedback_status="rejected", correct_action_id="y"),
        # 4. correct_action_id outside action_ids
        _make_episode("ep-unknown-correct", action_id="y", feedback_status="rejected", correct_action_id="unknown"),
        # 5. action_id outside action_ids
        _make_episode("ep-unknown-action", action_id="outside", feedback_status="rejected", correct_action_id="x"),
        # 6. correct_action_id is not a string (e.g. integer or list)
        _make_episode("ep-non-string-correct", action_id="y", feedback_status="rejected", correct_action_id=123),
    ]

    for ep in episodes:
        pairs = pairs_from_episodes([ep], action_ids)
        assert pairs == [], f"Expected no pair for episode {ep.id}, got {pairs}"


def test_ac2_not_the_adr_field():
    """AC_2: decision_disposition 'modify' without feedback_status 'rejected' gives no pair (FDD-018 G3)."""
    action_ids = ["x", "y", "z"]
    ep = _make_episode("ep-modify", action_id="y", decision_disposition="modify", correct_action_id="x")
    pairs = pairs_from_episodes([ep], action_ids)
    assert pairs == []


def test_ac3_once_and_order_preserved():
    """AC_3: Same episode id offered twice gives one pair; order is order of first appearance."""
    action_ids = ["x", "y", "z"]
    ep1 = _make_episode("ep-1", action_id="y", feedback_status="rejected", correct_action_id="x")
    ep2 = _make_episode("ep-2", action_id="z", feedback_status="rejected", correct_action_id="y")
    ep1_duplicate = _make_episode("ep-1", action_id="y", feedback_status="rejected", correct_action_id="x")

    pairs = pairs_from_episodes([ep1, ep2, ep1_duplicate], action_ids)
    assert len(pairs) == 2
    assert pairs[0] == PreferencePair(winner="x", loser="y", source_episode_id="ep-1")
    assert pairs[1] == PreferencePair(winner="y", loser="z", source_episode_id="ep-2")


def test_ac4_inputs_untouched():
    """AC_4: Episodes are equal to their deep copies after the call."""
    action_ids = ["x", "y", "z"]
    ep1 = _make_episode("ep-1", action_id="y", feedback_status="rejected", correct_action_id="x")
    ep2 = _make_episode("ep-2", action_id="z", feedback_status="accepted", correct_action_id="y")
    episodes = [ep1, ep2]
    clones = deepcopy(episodes)

    _ = pairs_from_episodes(episodes, action_ids)

    assert episodes == clones
    for orig, clone in zip(episodes, clones):
        assert orig.metadata == clone.metadata
