"""Scored-search decision configuration compilation (Story 22.1 & Story 22.2).

Source ADR: ADR-022 (Scored-Search Decision Configuration Compilation)
Source BRD: BRD-022 (BRU-022-01, BRU-022-02, BRU-022-03, BRU-022-04, BRU-022-05, BRU-022-06, BRU-022-10)
Source FDD: FDD-022 (§1 item 1, §2.1, §2.2, §3.1, §3.2, §3.3, §3.4, §3.6, §4 L1, L2, L7)
Stories:
- Story 22.1 (Scoring a Weight Vector With the Real Resolver)
- Story 22.2 (The Split and the Label Rule)

Contract Interpretations:
- [I1] Upstream Fork Purity (Invariant 6): Implemented in src/agent_learning_ext/weight_compiler.py.
- [I2] Defensive None-Safety for Dictionaries: Guards metadata and dict lookups with fallback defaults.
- [I3] Empty Collection Base Case: Collection-processing functions handle empty inputs cleanly without raising.
"""

from __future__ import annotations

import json
import math
import random
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import datetime, timezone
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

    def __hash__(self) -> int:
        task = getattr(self.frame, "task", id(self.frame))
        return hash((task, self.label, self.labeled_at))


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
        if not isinstance(self.weights, MappingProxyType):
            object.__setattr__(self, "weights", MappingProxyType(dict(self.weights)))


@dataclass(frozen=True)
class CoordinateAscentResult:
    """Result of coordinate ascent search over criteria weights (FDD-022 §3.5)."""

    weights: Mapping[str, float]
    train_accuracy: float
    train_objective: float
    evaluations: int
    sweeps: int
    restarts: int

    def __post_init__(self) -> None:
        if not isinstance(self.weights, MappingProxyType):
            object.__setattr__(self, "weights", MappingProxyType(dict(self.weights)))


@dataclass(frozen=True)
class NoImprovement:
    """Outcome when compiled weights fail to strictly outperform baseline holdout accuracy."""

    reason: str
    baseline_holdout_accuracy: float
    best_holdout_accuracy: float


# --- Helper Functions ---


def _parse_iso(ts: str | datetime) -> datetime:
    """Parse ISO 8601 timestamp string or datetime into UTC-aware datetime."""
    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            return ts.replace(tzinfo=timezone.utc)
        return ts
    dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


# --- Core Pure Functions (FDD-022 §3.1 - §3.6) ---


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
        if isinstance(w, bool):
            raise ValueError(f"invalid weight {w!r}")
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


def _project_to_simplex(weights: Mapping[str, float], step: float) -> dict[str, float]:
    """Ensure all weights are at least step and sum to 1.0 within 1e-9."""
    res = {k: max(step, float(v)) for k, v in weights.items()}
    tot = sum(res.values())
    res = {k: v / tot for k, v in res.items()}
    for _ in range(10):
        if all(v >= step - 1e-9 for v in res.values()):
            break
        res = {k: max(step, v) for k, v in res.items()}
        tot = sum(res.values())
        res = {k: v / tot for k, v in res.items()}
    return res


def coordinate_ascent(
    train: Sequence[LabeledFrame],
    snapshot: PolicySnapshot,
    *,
    step: float = STEP_DEFAULT,
    restarts: int = RESTARTS_DEFAULT,
    max_sweeps: int = MAX_SWEEPS_DEFAULT,
    beta: float = BETA_DEFAULT,
) -> CoordinateAscentResult:
    """Optimize criteria weights via coordinate ascent on training partition (FDD-022 §3.5).

    AC_0: Every weight vector evaluated is positive, at least step 0.05, and sums to 1.0 within 1e-9.
          Items whose frames have different criterion ids raise ValueError.
    AC_1: Training objective of returned weights is at least that of every start point,
          and never decreases from one accepted candidate to the next.
    AC_2: Synthetic suite returns weights within 0.05 of (0.6, 0.3, 0.1) and training accuracy 1.0.
    AC_3: Deterministic execution and reproducibility across runs and fresh processes.
    AC_4: Stops after max_sweeps or when sweep accepts nothing; reports evaluations, sweeps, restarts.
          restarts=1 uses only the mean of the frames' own weights.
    """
    if not train:
        raise ValueError("train items cannot be empty")

    first_frame = getattr(train[0], "frame", None)
    if first_frame is None and isinstance(train[0], dict):
        first_frame = train[0].get("frame")
    if first_frame is None:
        raise ValueError(f"First item lacks a DecisionFrame: {train[0]!r}")

    first_cids = {c.id for c in first_frame.criteria}

    for idx, item in enumerate(train):
        fr = getattr(item, "frame", None)
        if fr is None and isinstance(item, dict):
            fr = item.get("frame")
        if fr is None:
            raise ValueError(f"Item {idx} lacks a DecisionFrame: {item!r}")
        item_cids = {c.id for c in fr.criteria}
        if item_cids != first_cids:
            raise ValueError(
                f"All items must share one set of criterion ids, mismatch: "
                f"{sorted(first_cids)} vs {sorted(item_cids)}"
            )

    cids = sorted(first_cids)
    K = len(cids)

    # 1. Start points in specified deterministic order:
    # 1a. Mean of frames' own normalized weights
    mean_w: dict[str, float] = {cid: 0.0 for cid in cids}
    for item in train:
        fr = getattr(item, "frame", None) or item["frame"]
        norm = sum(c.weight for c in fr.criteria)
        for c in fr.criteria:
            mean_w[c.id] += (c.weight / norm) / len(train)
    sp1 = _project_to_simplex(mean_w, step)

    # 1b. Uniform weights
    sp2 = {cid: 1.0 / K for cid in cids}

    # 1c. For each criterion in sorted id order: 0.5 on it, rest shared equally
    sp_criteria: list[dict[str, float]] = []
    for cid in cids:
        if K > 1:
            pt = {other: (0.5 / (K - 1)) if other != cid else 0.5 for other in cids}
        else:
            pt = {cid: 1.0}
        sp_criteria.append(_project_to_simplex(pt, step))

    all_start_points = [sp1, sp2, *sp_criteria]
    num_restarts = max(1, min(restarts, len(all_start_points)))
    start_points = all_start_points[:num_restarts]

    total_evaluations = 0
    best_overall_obj: float = -float("inf")
    best_overall_w: dict[str, float] = {}
    best_overall_sweeps: int = 0

    for start_w in start_points:
        curr_w = dict(start_w)
        curr_obj = objective(curr_w, train, snapshot, beta=beta)
        total_evaluations += len(train)

        sweeps_completed = 0
        for _ in range(max_sweeps):
            sweeps_completed += 1
            accepted_in_sweep = False
            for cid in cids:
                for delta in (+step, -step):
                    cand = dict(curr_w)
                    cand[cid] = max(step, cand[cid] + delta)
                    tot = sum(cand.values())
                    cand = {k: v / tot for k, v in cand.items()}
                    if any(v < step - 1e-9 for v in cand.values()):
                        continue
                    cand_obj = objective(cand, train, snapshot, beta=beta)
                    total_evaluations += len(train)
                    if cand_obj > curr_obj + 1e-12:
                        curr_w = cand
                        curr_obj = cand_obj
                        accepted_in_sweep = True
            if not accepted_in_sweep:
                break

        if curr_obj > best_overall_obj + 1e-12:
            best_overall_obj = curr_obj
            best_overall_w = curr_w
            best_overall_sweeps = sweeps_completed

    hits = sum(evaluate(it, best_overall_w, snapshot)[0] == it.label for it in train)
    train_acc = hits / len(train)

    return CoordinateAscentResult(
        weights=best_overall_w,
        train_accuracy=train_acc,
        train_objective=best_overall_obj,
        evaluations=total_evaluations,
        sweeps=best_overall_sweeps,
        restarts=num_restarts,
    )

