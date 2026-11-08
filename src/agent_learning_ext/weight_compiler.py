"""Scored-search decision configuration compilation (Story 22.1).

Source ADR: ADR-022 (Scored-Search Decision Configuration Compilation)
Source BRD: BRD-022 (BRU-022-01, BRU-022-02, BRU-022-03, BRU-022-04, BRU-022-10)
Source FDD: FDD-022 (§1 item 1, §2.1, §2.2, §3.1, §3.2, §3.3, §4 L1, L2, L7)
Story: Story 22.1 (Scoring a Weight Vector With the Real Resolver)

Contract Interpretations:
- [I1] Upstream Fork Purity (Invariant 6): Implemented in src/agent_learning_ext/weight_compiler.py.
- [I2] Defensive None-Safety for Dictionaries: Guards metadata and dict lookups with fallback defaults.
- [I3] Empty Collection Base Case: Collection-processing functions handle empty inputs cleanly without raising.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import Any

from agent_learning.decision import (
    DecisionCriterion,
    DecisionFrame,
    DecisionResolver,
    DecisionResult,
    DecisionStatus,
)
from agent_learning.types import PolicySnapshot

# --- Constants (FDD-022 §2.1) ---

STEP_DEFAULT: float = 0.05
BETA_DEFAULT: float = 0.1
HOLDOUT_FRACTION_DEFAULT: float = 0.3
MIN_PART: int = 5
RESTARTS_DEFAULT: int = 5
MAX_SWEEPS_DEFAULT: int = 20


# --- Dataclasses (FDD-022 §2.2) ---


@dataclass(frozen=True)
class LabeledFrame:
    """A decision frame paired with ground truth disposition and adjudication timestamp."""

    frame: DecisionFrame
    label: str  # the action id the human settled on
    labeled_at: str  # ISO 8601 timestamp


@dataclass(frozen=True)
class CompiledWeights:
    """Frozen result of offline criteria weight search."""

    weights: Mapping[str, float]
    train_accuracy: float
    holdout_accuracy: float
    baseline_holdout_accuracy: float
    holdout_margin: float
    seed: int
    evaluations: int
    sweeps: int
    restarts: int
    proposed_at: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "weights", MappingProxyType(dict(self.weights)))


@dataclass(frozen=True)
class NoImprovement:
    """Outcome when compiled weights fail to strictly outperform baseline holdout accuracy."""

    reason: str
    baseline_holdout_accuracy: float
    best_holdout_accuracy: float


# --- Core Pure Functions (FDD-022 §3.1 - §3.3) ---


def with_weights(
    frame: DecisionFrame,
    weights: Mapping[str, float] | Sequence[float],
) -> DecisionFrame:
    """Return a new DecisionFrame with criteria weights updated.

    Args:
        frame: The original DecisionFrame.
        weights: A mapping of criterion id -> weight, or a sequence of weights matching
            the frame criteria order.

    Returns:
        A new DecisionFrame whose criteria have the given weights.

    Raises:
        ValueError: If weights keys/length differ from frame criteria, or if any weight
            is non-finite, zero, or negative.
    """
    criterion_ids = [c.id for c in frame.criteria]
    criterion_set = set(criterion_ids)

    if isinstance(weights, Mapping):
        if set(weights.keys()) != criterion_set:
            raise ValueError(
                f"weights keys {sorted(weights.keys())} differ from frame criteria {sorted(criterion_set)}"
            )
        ordered_weights = [weights[cid] for cid in criterion_ids]
    elif isinstance(weights, Sequence) and not isinstance(weights, (str, bytes)):
        if len(weights) != len(criterion_ids):
            raise ValueError(
                f"weights sequence length {len(weights)} differs from frame criteria count {len(criterion_ids)}"
            )
        ordered_weights = list(weights)
    else:
        raise ValueError(
            f"weights must be a Mapping or Sequence, got {type(weights).__name__}"
        )

    validated_weights: list[float] = []
    for w in ordered_weights:
        try:
            fw = float(w)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"invalid weight {w!r}") from exc
        if not math.isfinite(fw) or math.isnan(fw) or fw <= 0.0:
            raise ValueError(f"weight must be finite and positive (> 0), got {w!r}")
        validated_weights.append(fw)

    new_criteria = tuple(
        replace(c, weight=w)
        for c, w in zip(frame.criteria, validated_weights, strict=True)
    )
    return replace(frame, criteria=new_criteria)


def evaluate(
    item: LabeledFrame | DecisionFrame,
    weights: Mapping[str, float] | Sequence[float],
    snapshot: PolicySnapshot,
) -> tuple[str | None, float]:
    """Score a candidate weight vector using DecisionResolver.resolve.

    Args:
        item: A LabeledFrame or DecisionFrame to evaluate.
        weights: The weights to apply to the frame's criteria.
        snapshot: The policy snapshot matching the frame's action space.

    Returns:
        A tuple of (predicted_action_id_or_None, robust_margin).
    """
    frame = item.frame if hasattr(item, "frame") else item
    weighted_frame = with_weights(frame, weights)
    resolver = DecisionResolver()
    result: DecisionResult = resolver.resolve(snapshot, weighted_frame)

    if result.status == DecisionStatus.RESOLVED:
        predicted = result.selected_action.id if result.selected_action else None
    elif result.status == DecisionStatus.NEEDS_USER_FEEDBACK:
        predicted = result.proposed_action.id if result.proposed_action else None
    else:
        predicted = None

    # Feasible options not ruled out by constraints or dominance
    viable = [
        assessment
        for assessment in result.assessments
        if assessment.feasible and not assessment.ruled_out_by and assessment.robust_utility is not None
    ]

    if len(viable) < 2:
        margin = 0.0
    else:
        utilities = sorted((float(a.robust_utility) for a in viable), reverse=True)
        margin = max(0.0, min(1.0, utilities[0] - utilities[1]))

    return predicted, margin


def objective(
    weights: Mapping[str, float] | Sequence[float],
    items: LabeledFrame | DecisionFrame | Iterable[LabeledFrame | DecisionFrame],
    snapshot: PolicySnapshot,
    *,
    beta: float = BETA_DEFAULT,
    label: str | None = None,
) -> float:
    """Compute the multi-objective score over a collection of labeled frames.

    Objective: sum(indicator(predicted == label) + beta * margin)

    Args:
        weights: Criteria weights to evaluate.
        items: A single item or iterable of LabeledFrame / DecisionFrame.
        snapshot: Policy snapshot for resolver execution.
        beta: Weight of the margin term (default 0.1).
        label: Explicit label to use when items are bare DecisionFrames without a label.

    Returns:
        The total objective value.
    """
    if isinstance(items, (LabeledFrame, DecisionFrame)):
        item_list: Sequence[LabeledFrame | DecisionFrame] = [items]
    else:
        item_list = list(items)

    if not item_list:
        return 0.0

    total_score = 0.0
    for it in item_list:
        target_label = it.label if hasattr(it, "label") else label
        predicted, margin = evaluate(it, weights, snapshot)
        is_correct = 1.0 if (target_label is not None and predicted == target_label) else 0.0
        total_score += is_correct + beta * margin

    return total_score
