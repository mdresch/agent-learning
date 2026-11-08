"""Scored-Search Decision Configuration Compilation (Story 22.2, ADR-022, FDD-022).

Pure offline module for criteria weight compilation, holdout splitting, and label timing validation.
Invariant 6: Modules under src/agent_learning/ are untouched; all extensions reside here.
"""

from __future__ import annotations

import json
import math
import random
import types
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from agent_learning.decision import (
    DecisionCriterion,
    DecisionFrame,
    DecisionResolver,
    DecisionStatus,
)
from agent_learning.types import PolicySnapshot

# Constants per FDD-022 §2.1
STEP_DEFAULT: float = 0.05
BETA_DEFAULT: float = 0.1
HOLDOUT_FRACTION_DEFAULT: float = 0.3
MIN_PART: int = 5
RESTARTS_DEFAULT: int = 5
MAX_SWEEPS_DEFAULT: int = 20


@dataclass(frozen=True)
class LabeledFrame:
    """A DecisionFrame paired with human adjudication label and timestamp."""

    frame: DecisionFrame
    label: str  # the action id the human settled on
    labeled_at: str  # ISO 8601, when the label was recorded

    def __hash__(self) -> int:
        task = getattr(self.frame, "task", id(self.frame))
        return hash((task, self.label, self.labeled_at))


@dataclass(frozen=True)
class CompiledWeights:
    """Result of weight compilation when heldout accuracy strictly improves over baseline."""

    weights: Mapping[str, float]  # MappingProxyType over dict
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
        if not isinstance(self.weights, types.MappingProxyType):
            object.__setattr__(
                self,
                "weights",
                types.MappingProxyType(dict(self.weights)),
            )


@dataclass(frozen=True)
class NoImprovement:
    """Result when compiled weights do not strictly improve on hold-out."""

    reason: str
    baseline_holdout_accuracy: float
    best_holdout_accuracy: float


def _parse_iso(ts: str | datetime) -> datetime:
    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            return ts.replace(tzinfo=timezone.utc)
        return ts
    dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def validate_label_timing(
    items: Sequence[Any],
    proposed_at: str | datetime,
) -> None:
    """Validate that all items were labeled strictly before proposed_at (FDD-022 §3.6, AC_3).

    Raises ValueError naming the item when any labeled_at equals or follows proposed_at.
    """
    prop_dt = _parse_iso(proposed_at)
    for item in items:
        labeled_at_raw = getattr(item, "labeled_at", None)
        if labeled_at_raw is None and isinstance(item, dict):
            labeled_at_raw = item.get("labeled_at")
        if labeled_at_raw is None:
            raise ValueError(f"Item lacks labeled_at: {item!r}")

        item_dt = _parse_iso(labeled_at_raw)
        if item_dt >= prop_dt:
            task_name = getattr(getattr(item, "frame", None), "task", None)
            name_str = f"item '{task_name}'" if task_name else f"item {item!r}"
            raise ValueError(
                f"{name_str} labeled_at ({labeled_at_raw}) equals or follows "
                f"proposed_at ({proposed_at})"
            )


def split_holdout(
    items: Sequence[LabeledFrame],
    *,
    fraction: float = HOLDOUT_FRACTION_DEFAULT,
    seed: int,
) -> tuple[list[LabeledFrame], list[LabeledFrame]]:
    """Partition items into a training part and a held-out part reproducibly (FDD-022 §3.4).

    AC_0: split_holdout on the synthetic suite with seed 7 returns the same two parts
    on every call and in a fresh process; a different seed returns a different split;
    the parts are disjoint and together equal the input.

    AC_1: a fraction of 0.3 on 40 items holds out 12; a fraction under 0.3 or over 0.5,
    a non-integer seed, and an input that would leave fewer than 5 items in either part
    each raise ValueError.

    AC_2: shuffling the input list before the call does not change the parts (sorts
    deterministically before partitioning).
    """
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError(f"seed must be an integer, got {seed!r}")
    if not isinstance(fraction, (int, float)) or isinstance(fraction, bool):
        raise ValueError(f"fraction must be a float, got {fraction!r}")
    if math.isnan(fraction) or math.isinf(fraction) or fraction < 0.3 or fraction > 0.5:
        raise ValueError(f"fraction must be between 0.3 and 0.5, got {fraction}")

    n = len(items)
    holdout_count = int(round(n * fraction))
    train_count = n - holdout_count

    if train_count < MIN_PART or holdout_count < MIN_PART:
        raise ValueError(
            f"input would leave fewer than {MIN_PART} items in either part: "
            f"total={n}, train={train_count}, holdout={holdout_count}"
        )

    def _deterministic_sort_key(item: Any) -> tuple[str, str, str]:
        labeled_at = getattr(item, "labeled_at", None)
        if labeled_at is None and isinstance(item, dict):
            labeled_at = item.get("labeled_at", "")
        label = getattr(item, "label", None)
        if label is None and isinstance(item, dict):
            label = item.get("label", "")
        frame = getattr(item, "frame", None)
        if frame is None and isinstance(item, dict):
            frame = item.get("frame", "")
        if hasattr(frame, "to_dict"):
            frame_str = json.dumps(frame.to_dict(), sort_keys=True)
        elif isinstance(frame, dict):
            frame_str = json.dumps(frame, sort_keys=True)
        else:
            frame_str = str(frame)
        return (str(labeled_at), str(label), frame_str)

    ordered = sorted(items, key=_deterministic_sort_key)

    rng = random.Random(seed)
    indices = list(range(n))
    rng.shuffle(indices)

    train = [ordered[i] for i in indices[:train_count]]
    holdout = [ordered[i] for i in indices[train_count:]]

    return train, holdout


def with_weights(frame: DecisionFrame, weights: Mapping[str, float]) -> DecisionFrame:
    """Return a new DecisionFrame with criteria weights replaced by weights."""
    frame_criteria_ids = {c.id for c in frame.criteria}
    weight_keys = set(weights.keys())
    if frame_criteria_ids != weight_keys:
        raise ValueError(
            f"Criterion ids mismatch: frame has {sorted(frame_criteria_ids)}, "
            f"weights have {sorted(weight_keys)}"
        )
    for cid, w in weights.items():
        if not isinstance(w, (int, float)) or isinstance(w, bool):
            raise ValueError(f"Weight for {cid} must be numeric: {w!r}")
        if math.isnan(w) or math.isinf(w) or w <= 0.0:
            raise ValueError(f"Weight for {cid} must be finite and positive: {w}")

    new_criteria = [
        DecisionCriterion(
            id=c.id,
            weight=float(weights[c.id]),
            description=c.description,
            direction=c.direction,
        )
        for c in frame.criteria
    ]
    return DecisionFrame(
        task=frame.task,
        criteria=new_criteria,
        options=frame.options,
        constraints=frame.constraints,
        minimum_margin=frame.minimum_margin,
        uncertainty_penalty=frame.uncertainty_penalty,
        max_uncertainty=frame.max_uncertainty,
    )


def evaluate(
    item: LabeledFrame,
    weights: Mapping[str, float],
    snapshot: PolicySnapshot,
) -> tuple[str | None, float]:
    """Score item under weights using DecisionResolver."""
    frame_with_w = with_weights(item.frame, weights)
    resolver = DecisionResolver()
    result = resolver.resolve(snapshot, frame_with_w)

    predicted: str | None = None
    if result.status == DecisionStatus.RESOLVED and result.selected_action:
        predicted = result.selected_action.id
    elif result.status == DecisionStatus.NEEDS_USER_FEEDBACK and result.proposed_action:
        predicted = result.proposed_action.id

    feasible_assessments = [
        a
        for a in result.assessments
        if a.feasible is not False and getattr(a, "robust_utility", None) is not None
    ]
    if len(feasible_assessments) >= 2:
        sorted_utils = sorted(
            [float(a.robust_utility) for a in feasible_assessments],
            reverse=True,
        )
        margin = max(0.0, min(1.0, sorted_utils[0] - sorted_utils[1]))
    else:
        margin = 0.0

    return predicted, margin
