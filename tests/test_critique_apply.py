"""Contract tests for Story 14.2 and 14.3: Critique Evidence Application.

Covers:
- Story 14.2: Moving the Pooled Support by the Delta (AC0 - AC3)
- Story 14.3: Doubt, Traceability, and Validation (AC0 - AC4)
"""

import copy
import math
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
from agent_learning_ext.critique_evidence import (
    AppliedCritique,
    CritiqueDelta,
    apply_critique,
    KAPPA_DEFAULT,
    CONFIDENCE_FLOOR,
    TARGET_EPSILON,
    RESOLVER_EPSILON,

)


def _make_snapshot_for_frame(frame: DecisionFrame) -> PolicySnapshot:
    actions = [opt.action for opt in frame.options]
    return PolicySnapshot(
        id="policy-1",
        agent_id="agent-1",
        task_id="test-task",
        version=1,
        actions=actions,
        logits={act.id: 0.0 for act in actions},
        metadata={"decision_authority": DecisionAuthority.FULL.value},
    )


@pytest.fixture
def resolver() -> DecisionResolver:
    return DecisionResolver()


@pytest.fixture
def base_frame() -> DecisionFrame:
    """Fixture described in Epic 14:

    One option with two evidence points on one criterion:
    (support 0.8, confidence 0.8) and (support 0.7, confidence 0.9).
    The resolver pools them to ~0.8666.
    Includes a second option to satisfy DecisionResolver action space constraints.
    """
    criterion = DecisionCriterion(id="arch_soundness", weight=1.0, minimum_sources=1)
    option_a = DecisionOption(
        action=Action(id="opt_a", description="Option A"),
        evidence=(
            EvidencePoint("arch_soundness", "source_1", 0.8, 0.8),
            EvidencePoint("arch_soundness", "source_2", 0.7, 0.9),
        ),
    )
    option_b = DecisionOption(
        action=Action(id="opt_b", description="Option B"),
        evidence=(
            EvidencePoint("arch_soundness", "source_b", 0.5, 0.5),
        ),
    )
    return DecisionFrame(
        task="test-critique",
        criteria=(criterion,),
        options=(option_a, option_b),
        constraints=(),
    )


def _get_pooled_support(resolver: DecisionResolver, frame: DecisionFrame, opt_id: str, crit_id: str) -> float:
    snapshot = _make_snapshot_for_frame(frame)
    result = resolver.resolve(snapshot, frame)
    for assessment in result.assessments:
        if assessment.action.id == opt_id:
            for ca in assessment.criteria:
                if ca.criterion_id == crit_id:
                    return float(ca.support)
    raise ValueError(f"No assessment found for option {opt_id} and criterion {crit_id}")


# ==============================================================================
# Story 14.2: Moving the Pooled Support by the Delta
# ==============================================================================

def test_ac0_exact_shift(resolver, base_frame):
    """AC0: on the base frame, a delta of -0.20 gives a pooled support of 0.6666 and +0.10 gives 0.9666,

    each within 1e-9 of clip(before + delta), measured through DecisionResolver.resolve()
    and not through the module's own arithmetic.
    """
    before = _get_pooled_support(resolver, base_frame, "opt_a", "arch_soundness")
    assert abs(before - 0.866644) < 1e-4

    # Negative shift: -0.20
    delta_neg = CritiqueDelta(
        criterion_id="arch_soundness",
        support_delta=-0.20,
        rationale="Defect found",
        finding_id="Q-1",
    )
    applied_neg = apply_critique(base_frame, "opt_a", [delta_neg])
    assert isinstance(applied_neg, AppliedCritique)
    after_neg = _get_pooled_support(resolver, applied_neg.frame, "opt_a", "arch_soundness")
    target_neg = min(1.0 - TARGET_EPSILON, max(TARGET_EPSILON, before - 0.20))
    assert abs(after_neg - target_neg) < 1e-9
    assert abs(after_neg - (before - 0.20)) < 1e-9

    # Positive shift: +0.10
    delta_pos = CritiqueDelta(
        criterion_id="arch_soundness",
        support_delta=+0.10,
        rationale="Confirmation",
        finding_id="Q-2",
    )
    applied_pos = apply_critique(base_frame, "opt_a", [delta_pos])
    after_pos = _get_pooled_support(resolver, applied_pos.frame, "opt_a", "arch_soundness")
    target_pos = min(1.0 - TARGET_EPSILON, max(TARGET_EPSILON, before + 0.10))
    assert abs(after_pos - target_pos) < 1e-9
    assert abs(after_pos - (before + 0.10)) < 1e-9


def test_ac1_direction_grid(resolver):
    """AC1: over a grid of base supports and deltas, a negative delta never raises

    the pooled support, a positive delta never lowers it, and a zero delta leaves it unchanged.
    """
    for base_p in [0.2, 0.5, 0.8]:
        frame = DecisionFrame(
            task="grid-test",
            criteria=(DecisionCriterion(id="c1", weight=1.0, minimum_sources=1),),
            options=(
                DecisionOption(
                    action=Action(id="opt1", description="Opt 1"),
                    evidence=(EvidencePoint("c1", "s1", base_p, 0.8),),
                ),
                DecisionOption(
                    action=Action(id="opt2", description="Opt 2"),
                    evidence=(EvidencePoint("c1", "s2", 0.5, 0.5),),
                ),
            ),
        )
        before = _get_pooled_support(resolver, frame, "opt1", "c1")
        for delta_val in [-0.3, -0.1, 0.0, 0.1, 0.3]:
            delta = CritiqueDelta("c1", delta_val, "testing direction", "F-1")
            applied = apply_critique(frame, "opt1", [delta])
            after = _get_pooled_support(resolver, applied.frame, "opt1", "c1")

            if delta_val < 0:
                assert after <= before + 1e-9
                assert after < before
            elif delta_val > 0:
                assert after >= before - 1e-9
                assert after > before
            else:
                assert abs(after - before) < 1e-9


def test_ac2_clamp(resolver, base_frame):
    """AC2: deltas of -0.9 and +0.9 on the base frame land within 1e-6 of 0 and 1,

    and the appended point's support is a valid value in [0, 1].
    """
    # -0.9 delta on base frame (~0.8666) -> target clamped to 1e-6
    d_neg = CritiqueDelta("arch_soundness", -0.9, "Extreme defect", "F-neg")
    app_neg = apply_critique(base_frame, "opt_a", [d_neg])
    after_neg = _get_pooled_support(resolver, app_neg.frame, "opt_a", "arch_soundness")
    assert abs(after_neg - 0.0) <= 1e-6 + 1e-9

    appended_pt_neg = [pt for pt in app_neg.frame.options[0].evidence if pt.source == "critique:F-neg"][0]
    assert 0.0 <= appended_pt_neg.support <= 1.0

    # +0.9 delta on base frame -> target clamped to 1 - 1e-6
    d_pos = CritiqueDelta("arch_soundness", +0.9, "Extreme confirmation", "F-pos")
    app_pos = apply_critique(base_frame, "opt_a", [d_pos])
    after_pos = _get_pooled_support(resolver, app_pos.frame, "opt_a", "arch_soundness")
    assert abs(after_pos - 1.0) <= 1e-6 + 1e-9

    appended_pt_pos = [pt for pt in app_pos.frame.options[0].evidence if pt.source == "critique:F-pos"][0]
    assert 0.0 <= appended_pt_pos.support <= 1.0


def test_ac3_sequence(resolver, base_frame):
    """AC3: two deltas on one criterion (-0.20, then -0.10) are applied in order,

    each against the pooled support left by the previous one, and end at before - 0.30 within 1e-9.
    """
    before = _get_pooled_support(resolver, base_frame, "opt_a", "arch_soundness")
    deltas = [
        CritiqueDelta("arch_soundness", -0.20, "First finding", "Q-1"),
        CritiqueDelta("arch_soundness", -0.10, "Second finding", "Q-2"),
    ]
    applied = apply_critique(base_frame, "opt_a", deltas)
    after = _get_pooled_support(resolver, applied.frame, "opt_a", "arch_soundness")
    assert abs(after - (before - 0.30)) < 1e-9


# ==============================================================================
# Story 14.3: Doubt, Traceability and Validation
# ==============================================================================

def test_ac0_doubt_calculation(base_frame):
    """AC0: the appended point's confidence is max(1 - u_after, 0.05),

    where u_after = min(1, u + kappa * max(0, -delta)) and u = 1 - mean(confidence)
    of the criterion's points at that step, including points appended by earlier deltas in the same call.
    A positive delta leaves u_after = u.
    """
    # Base frame has confidences 0.8 and 0.9.
    # mean = 0.85 -> u = 0.15.
    # Delta -0.20 with kappa=0.2 -> u_after = 0.15 + 0.2 * 0.20 = 0.19.
    # c_new = max(1 - 0.19, 0.05) = 0.81.
    d1 = CritiqueDelta("arch_soundness", -0.20, "Rationale", "Q-1")
    applied = apply_critique(base_frame, "opt_a", [d1], kappa=0.2)
    pt1 = [pt for pt in applied.frame.options[0].evidence if pt.source == "critique:Q-1"][0]
    assert abs(pt1.confidence - 0.81) < 1e-9

    # Next delta in sequence: delta = +0.10 (positive delta leaves u_after = u)
    # Evidence points now have confidences [0.8, 0.9, 0.81].
    # mean = (0.8 + 0.9 + 0.81) / 3 = 2.51 / 3 = 0.836666...
    # u = 1 - 0.836666... = 0.163333...
    # Positive delta -> u_after = u.
    # c_new = max(1 - u_after, 0.05) = 1 - 0.163333... = 0.836666...
    d2 = CritiqueDelta("arch_soundness", +0.10, "Rationale 2", "Q-2")
    applied_seq = apply_critique(base_frame, "opt_a", [d1, d2], kappa=0.2)
    pt2 = [pt for pt in applied_seq.frame.options[0].evidence if pt.source == "critique:Q-2"][0]
    expected_c2 = (0.8 + 0.9 + 0.81) / 3.0
    assert abs(pt2.confidence - expected_c2) < 1e-9


def test_ac1_source_and_preservation(base_frame):
    """AC1: every appended point has the source critique:<finding_id>,

    and every point of the input frame is present unchanged in the output.
    """
    deltas = [
        CritiqueDelta("arch_soundness", -0.15, "Finding 1", "F1"),
        CritiqueDelta("arch_soundness", -0.05, "Finding 2", "F2"),
    ]
    applied = apply_critique(base_frame, "opt_a", deltas)
    opt = applied.frame.options[0]

    # Preserved unchanged
    assert opt.evidence[0] == base_frame.options[0].evidence[0]
    assert opt.evidence[1] == base_frame.options[0].evidence[1]

    # Appended points have correct sources
    assert opt.evidence[2].source == "critique:F1"
    assert opt.evidence[3].source == "critique:F2"


def test_ac2_no_mutation(base_frame):
    """AC2: the input frame is equal to its earlier copy after apply_critique; the output is a new object."""
    frame_copy = copy.deepcopy(base_frame)
    delta = CritiqueDelta("arch_soundness", -0.10, "Some flaw", "Q-1")
    applied = apply_critique(base_frame, "opt_a", [delta])

    assert base_frame == frame_copy
    assert applied.frame is not base_frame
    assert applied.frame != base_frame


def test_ac3_validation_errors(base_frame):
    """AC3: ValueError for an unknown criterion, an unknown option, a criterion with no evidence

    on the option, the same finding id twice for one criterion, a finding id already used as a source,
    and kappa outside [0.1, 0.5].
    """
    delta_valid = CritiqueDelta("arch_soundness", -0.10, "Valid", "Q-1")

    # Unknown criterion
    d_bad_crit = CritiqueDelta("unknown_crit", -0.10, "Invalid crit", "Q-1")
    with pytest.raises(ValueError, match="unknown_crit"):
        apply_critique(base_frame, "opt_a", [d_bad_crit])

    # Unknown option
    with pytest.raises(ValueError, match="unknown_opt"):
        apply_critique(base_frame, "unknown_opt", [delta_valid])

    # Criterion with no evidence on the option
    crit2 = DecisionCriterion(id="empty_crit", weight=1.0, minimum_sources=1)
    frame_with_empty_crit = DecisionFrame(
        task="empty-crit",
        criteria=(base_frame.criteria[0], crit2),
        options=base_frame.options,
    )
    d_empty_crit = CritiqueDelta("empty_crit", -0.10, "No evidence", "Q-1")
    with pytest.raises(ValueError, match="empty_crit"):
        apply_critique(frame_with_empty_crit, "opt_a", [d_empty_crit])

    # Same finding id twice for one criterion
    deltas_dup = [
        CritiqueDelta("arch_soundness", -0.10, "First", "DUP-1"),
        CritiqueDelta("arch_soundness", -0.05, "Second", "DUP-1"),
    ]
    with pytest.raises(ValueError, match="DUP-1"):
        apply_critique(base_frame, "opt_a", deltas_dup)

    # Finding id already used as a source
    d_existing_src = CritiqueDelta("arch_soundness", -0.10, "Existing", "source_1")
    with pytest.raises(ValueError, match="source_1"):
        apply_critique(base_frame, "opt_a", [d_existing_src])

    # Finding id colliding with critique: source
    frame_with_critique_src = DecisionFrame(
        task="colliding",
        criteria=base_frame.criteria,
        options=(
            DecisionOption(
                action=Action(id="opt_a", description="Opt A"),
                evidence=(
                    EvidencePoint("arch_soundness", "critique:Q-OLD", 0.5, 0.5),
                ),
            ),
            DecisionOption(
                action=Action(id="opt_b", description="Opt B"),
                evidence=(
                    EvidencePoint("arch_soundness", "source_b", 0.5, 0.5),
                ),
            ),
        ),
    )
    d_colliding = CritiqueDelta("arch_soundness", -0.10, "Colliding", "Q-OLD")
    with pytest.raises(ValueError, match="Q-OLD"):
        apply_critique(frame_with_critique_src, "opt_a", [d_colliding])

    # Kappa outside [0.1, 0.5]
    with pytest.raises(ValueError, match="kappa"):
        apply_critique(base_frame, "opt_a", [delta_valid], kappa=0.05)

    with pytest.raises(ValueError, match="kappa"):
        apply_critique(base_frame, "opt_a", [delta_valid], kappa=0.55)


def test_ac4_resolver_accepts_it(resolver, base_frame):
    """AC4: the resolver accepts every output frame, including one with the minimum confidence

    of 0.05 and one whose appended point has a support within 1e-6 of 0 or 1.
    """
    # Trigger minimum confidence: very high uncertainty
    low_conf_frame = DecisionFrame(
        task="low-conf",
        criteria=(DecisionCriterion("c1", 1.0, 1),),
        options=(
            DecisionOption(
                action=Action("opt1", "Opt 1"),
                evidence=(EvidencePoint("c1", "s1", 0.9, 0.1),),
            ),
            DecisionOption(
                action=Action("opt2", "Opt 2"),
                evidence=(EvidencePoint("c1", "s2", 0.5, 0.5),),
            ),
        ),
    )
    # u = 1 - 0.1 = 0.9. u_after = min(1, 0.9 + 0.5 * 0.5) = 1.0. c_new = max(1 - 1.0, 0.05) = 0.05!
    d_min_conf = CritiqueDelta("c1", -0.5, "Big defect", "MIN-CONF")
    applied_min = apply_critique(low_conf_frame, "opt1", [d_min_conf], kappa=0.5)
    snap_min = _make_snapshot_for_frame(applied_min.frame)
    res_min = resolver.resolve(snap_min, applied_min.frame)
    assert res_min is not None
    assert res_min.assessments[0].feasible is True

    # Extreme shifts
    applied_clamp_neg = apply_critique(base_frame, "opt_a", [CritiqueDelta("arch_soundness", -0.9, "Extreme neg", "EXT-NEG")])
    snap_neg = _make_snapshot_for_frame(applied_clamp_neg.frame)
    res_clamp_neg = resolver.resolve(snap_neg, applied_clamp_neg.frame)
    assert res_clamp_neg is not None

    applied_clamp_pos = apply_critique(base_frame, "opt_a", [CritiqueDelta("arch_soundness", +0.9, "Extreme pos", "EXT-POS")])
    snap_pos = _make_snapshot_for_frame(applied_clamp_pos.frame)
    res_clamp_pos = resolver.resolve(snap_pos, applied_clamp_pos.frame)
    assert res_clamp_pos is not None
