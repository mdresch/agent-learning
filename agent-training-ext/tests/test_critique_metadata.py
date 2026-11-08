"""Contract tests for Story 14.4: Episode Metadata (AC0 - AC3).

Source: FDD-014 §2.2, ADR-014, epic-14-critique-to-evidence-ingestion.md.
"""

import json
import pytest

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
        AppliedCritique,
        CritiqueDelta,
        apply_critique,
        to_episode_metadata,
        parse_critique,
    )
except ImportError:
    try:
        from critique_evidence import (
            AppliedCritique,
            CritiqueDelta,
            apply_critique,
            to_episode_metadata,
            parse_critique,
        )
    except ImportError:
        from agent_learning.critique_evidence import (
            AppliedCritique,
            CritiqueDelta,
            apply_critique,
            to_episode_metadata,
            parse_critique,
        )


def _make_base_frame():
    crit = DecisionCriterion(id="crit1", weight=1.0)
    opt = DecisionOption(
        action=Action(id="opt1", description="Option 1", parameters={}),
        evidence=(
            EvidencePoint(criterion_id="crit1", source="s1", support=0.8, confidence=0.8),
            EvidencePoint(criterion_id="crit1", source="s2", support=0.7, confidence=0.9),
        ),
    )
    opt2 = DecisionOption(
        action=Action(id="opt2", description="Option 2", parameters={}),
        evidence=(
            EvidencePoint(criterion_id="crit1", source="s1", support=0.5, confidence=0.5),
        ),
    )
    return DecisionFrame(task="test-task", criteria=(crit,), options=(opt, opt2))


def test_ac0_shape_and_fields():
    frame = _make_base_frame()
    text = "- [finding: F-1] [criterion: crit1] [claim: crash risk] [verified: yes]: Critical bug"
    deltas = parse_critique(text, source_id="REV-1")
    applied = apply_critique(frame, "opt1", deltas)

    meta = to_episode_metadata(applied)
    assert "critique_adjustments" in meta
    adjustments = meta["critique_adjustments"]
    assert len(adjustments) == 1

    adj = adjustments[0]
    expected_fields = {
        "finding_id", "criterion_id", "support_delta", "rationale",
        "basis", "rubric_delta", "override", "rubric_version",
        "support_before", "support_after", "uncertainty_before",
        "uncertainty_after", "point_support", "point_confidence", "kappa"
    }
    assert set(adj.keys()) == expected_fields
    assert adj["finding_id"] == "F-1"
    assert adj["criterion_id"] == "crit1"
    assert adj["basis"] == "rubric"
    assert adj["rubric_delta"] == -0.30
    assert adj["override"] is False
    assert adj["rubric_version"] == "1"


def test_ac1_json_safe_roundtrip():
    frame = _make_base_frame()
    text = "- [finding: F-2] [criterion: crit1] -0.15: Test delta"
    deltas = parse_critique(text, source_id="REV-2")
    applied = apply_critique(frame, "opt1", deltas)

    meta = to_episode_metadata(applied)
    serialized = json.dumps(meta)
    deserialized = json.loads(serialized)

    assert deserialized == meta
    assert isinstance(deserialized["critique_adjustments"][0]["support_delta"], float)
    assert isinstance(deserialized["critique_adjustments"][0]["point_support"], float)


def test_ac2_consistent_support_and_confidence():
    frame = _make_base_frame()
    text = "- [finding: F-3] [criterion: crit1] -0.20: Step down"
    deltas = parse_critique(text, source_id="REV-3")
    applied = apply_critique(frame, "opt1", deltas)

    meta = to_episode_metadata(applied)
    adj = meta["critique_adjustments"][0]

    # Verify support_after equals pooled support of output frame
    resolver = DecisionResolver()
    actions = [opt.action for opt in applied.frame.options]
    snapshot = PolicySnapshot(
        id="policy-1",
        agent_id="agent-1",
        task_id="test-task",
        version=1,
        actions=actions,
        logits={act.id: 0.0 for act in actions},
        metadata={"decision_authority": DecisionAuthority.FULL.value},
    )
    res = resolver.resolve(snapshot, applied.frame)
    pooled = res.assessments[0].criteria[0].support
    assert adj["support_after"] == pytest.approx(pooled, abs=1e-9)

    # Verify point_confidence equals appended point's confidence
    out_opt = next(o for o in applied.frame.options if o.action.id == "opt1")
    points = [p for p in out_opt.evidence if p.criterion_id == "crit1"]
    appended_pt = points[-1]
    assert adj["point_confidence"] == pytest.approx(appended_pt.confidence, abs=1e-9)
