"""Lightweight Critique-to-Evidence Ingestion (Epic 14 / Stories 14.1, 14.2, 14.3, 14.4).

Lives in agent_learning_ext (the fork rule); Microsoft's agent_learning is not edited.
Converts markdown critique findings into structured CritiqueDelta instances
following the tag grammar of FDD-014 §2.1, applies them to DecisionFrame
according to FDD-014 §3, and outputs episode metadata.
Pure module: standard library only, imports nothing from the storage subsystem,
and performs no file or network I/O.
"""

from collections import defaultdict
from dataclasses import dataclass
import math
import re
from typing import Optional, Sequence

from agent_learning.decision import (
    DecisionFrame,
    DecisionOption,
    EvidencePoint,
)

# FDD-014 §2.3 Constants
KAPPA_DEFAULT: float = 0.2
CONFIDENCE_FLOOR: float = 0.05
TARGET_EPSILON: float = 1e-6
RESOLVER_EPSILON: float = 1e-12
RUBRIC_VERSION: str = "1"

# FDD-014 §2.4 Delta rubric (design A, version "1")
RUBRIC_TABLE: dict[tuple[str, str], float] = {
    ("crash risk", "yes"): -0.30,
    ("crash risk", "partial"): -0.15,
    ("crash risk", "no"): 0.00,
    ("logic error", "yes"): -0.25,
    ("logic error", "partial"): -0.13,
    ("logic error", "no"): 0.00,
    ("test gap", "yes"): -0.15,
    ("test gap", "partial"): -0.08,
    ("test gap", "no"): 0.00,
    ("documentation", "yes"): -0.10,
    ("documentation", "partial"): -0.05,
    ("documentation", "no"): 0.00,
    ("style", "yes"): -0.05,
    ("style", "partial"): -0.03,
    ("style", "no"): 0.00,
    ("confirmation", "yes"): 0.10,
    ("confirmation", "partial"): 0.05,
    ("confirmation", "no"): 0.00,
}

_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
_TAG_PATTERN = re.compile(r"\[([A-Za-z0-9_]+):\s*([^\]]+)\]")
_SIGNED_NUM_PATTERN = re.compile(r"^([+-])(\d+(?:\.\d+)?)$")


@dataclass(frozen=True)
class CritiqueDelta:
    """A single parsed critique delta from a markdown bullet finding."""

    criterion_id: str
    support_delta: float  # [-1.0, 1.0]
    rationale: str  # the finding text, kept verbatim
    finding_id: str  # given in the tag, else f"{source_id}#{n}"
    basis: str = "explicit"  # "explicit" or "rubric"
    rubric_delta: Optional[float] = None  # the rubric's value when claim and verified were given
    override: bool = False  # True when an explicit number differs from rubric_delta by > 0.005
    rubric_version: str = RUBRIC_VERSION


@dataclass(frozen=True)
class AppliedCritique:
    """The result of applying a sequence of critique deltas to a decision frame."""

    frame: DecisionFrame
    adjustments: tuple[dict[str, object], ...]


def rubric_delta(claim_type: str, verified: str) -> float:
    """Return the predefined rubric delta for a given claim type and verification result."""
    known_claims = {"crash risk", "logic error", "test gap", "documentation", "style", "confirmation"}
    if claim_type not in known_claims:
        raise ValueError(f"Unknown claim_type: {claim_type!r}")

    known_verified = {"yes", "partial", "no"}
    if verified not in known_verified:
        raise ValueError(f"Unknown verified: {verified!r}")

    key = (claim_type, verified)
    if key not in RUBRIC_TABLE:
        raise ValueError(f"No rubric delta for ({claim_type!r}, {verified!r})")

    return RUBRIC_TABLE[key]


def parse_critique(text: str, source_id: str) -> list[CritiqueDelta]:
    """Parse critique findings from Markdown text according to FDD-014 tag grammar.

    Args:
        text: The markdown review or critique text.
        source_id: Source identifier (e.g. 'REV-001', matching [A-Za-z0-9._-]+).

    Returns:
        A list of CritiqueDelta objects in the order they appear in the text.

    Raises:
        ValueError: If source_id is invalid, or if any bullet has syntax/grammar/bounds errors.
    """
    if not source_id or not _ID_PATTERN.match(source_id):
        raise ValueError(f"Invalid source_id: {source_id!r}")

    deltas: list[CritiqueDelta] = []
    bullet_index = 0

    lines = text.splitlines()
    for line_idx, raw_line in enumerate(lines, 1):
        stripped = raw_line.strip()
        # Non-bullet lines are ignored
        if not (stripped.startswith("- ") or stripped.startswith("* ")):
            continue

        bullet_index += 1
        bullet_body = stripped[2:].strip()

        # Rationale delimiter check: find first colon outside square brackets
        in_bracket = False
        colon_pos = -1
        for i, ch in enumerate(bullet_body):
            if ch == "[":
                in_bracket = True
            elif ch == "]":
                in_bracket = False
            elif ch == ":" and not in_bracket:
                colon_pos = i
                break

        if colon_pos == -1:
            raise ValueError(f"Line {line_idx}: missing rationale delimiter ':' in bullet")

        header = bullet_body[:colon_pos].strip()
        rationale = bullet_body[colon_pos + 1 :].strip()
        if not rationale:
            raise ValueError(f"Line {line_idx}: empty rationale")

        # Extract all tags [tag: value]
        tags: dict[str, str] = {}
        for match in _TAG_PATTERN.finditer(header):
            tag_name = match.group(1).strip()
            tag_val = match.group(2).strip()
            tags[tag_name] = tag_val

        # Remove tags from header to inspect remaining tokens
        remainder = _TAG_PATTERN.sub("", header).strip()

        # Validate criterion tag
        criterion_id = tags.get("criterion")
        if not criterion_id:
            raise ValueError(f"Line {line_idx}: bullet missing required [criterion: ...] tag")
        if not _ID_PATTERN.match(criterion_id):
            raise ValueError(f"Line {line_idx}: invalid criterion id: {criterion_id!r}")

        # Validate finding tag
        raw_finding = tags.get("finding")
        if raw_finding:
            if not _ID_PATTERN.match(raw_finding):
                raise ValueError(f"Line {line_idx}: invalid finding id: {raw_finding!r}")
            finding_id = raw_finding
        else:
            finding_id = f"{source_id}#{bullet_index}"

        # Inspect remainder for explicit signed number
        explicit_delta: Optional[float] = None
        if remainder:
            num_match = _SIGNED_NUM_PATTERN.match(remainder)
            if num_match:
                explicit_delta = float(remainder)
            else:
                raise ValueError(f"Line {line_idx}: unsigned or non-numeric delta: {remainder!r}")

        # Check rubric tags
        claim_type = tags.get("claim")
        verified = tags.get("verified")

        # Determine delta & basis
        if explicit_delta is not None and claim_type is not None and verified is not None:
            r_delta = rubric_delta(claim_type, verified)
            override = abs(explicit_delta - r_delta) > 0.005
            delta = explicit_delta
            basis = "explicit"
            r_val = r_delta
        elif explicit_delta is not None:
            if claim_type is not None or verified is not None:
                raise ValueError(f"Line {line_idx}: both [claim: ...] and [verified: ...] required for rubric")
            delta = explicit_delta
            basis = "explicit"
            r_val = None
            override = False
        elif claim_type is not None and verified is not None:
            r_delta = rubric_delta(claim_type, verified)
            delta = r_delta
            basis = "rubric"
            r_val = r_delta
            override = False
        else:
            raise ValueError(
                f"Line {line_idx}: bullet must provide either a signed number or both [claim: ...] and [verified: ...]"
            )

        # Bounds check
        if delta < -1.0 or delta > 1.0:
            raise ValueError(f"Line {line_idx}: delta {delta} outside [-1.0, 1.0]")

        deltas.append(
            CritiqueDelta(
                criterion_id=criterion_id,
                support_delta=delta,
                rationale=rationale,
                finding_id=finding_id,
                basis=basis,
                rubric_delta=r_val,
                override=override,
            )
        )

    return deltas


def _logit(p: float) -> float:
    return math.log(p / (1.0 - p))


def _sigmoid(x: float) -> float:
    if x >= 0.0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    else:
        z = math.exp(x)
        return z / (1.0 + z)


def apply_critique(
    frame: DecisionFrame,
    option_id: str,
    deltas: Sequence[CritiqueDelta],
    *,
    kappa: float = KAPPA_DEFAULT,
) -> AppliedCritique:
    """Apply critique deltas to an option in a DecisionFrame according to FDD-014 §3."""
    if not (0.1 <= kappa <= 0.5):
        raise ValueError(f"kappa {kappa} outside [0.1, 0.5]")

    target_option: Optional[DecisionOption] = None
    for opt in frame.options:
        if opt.action.id == option_id:
            target_option = opt
            break
    if target_option is None:
        raise ValueError(f"Unknown option {option_id!r}")

    valid_criteria = {c.id for c in frame.criteria}
    seen_findings_by_crit: dict[str, set[str]] = defaultdict(set)
    existing_sources = {pt.source for pt in target_option.evidence}

    for d in deltas:
        if d.criterion_id not in valid_criteria:
            raise ValueError(f"Unknown criterion {d.criterion_id!r}")
        if d.finding_id in seen_findings_by_crit[d.criterion_id]:
            raise ValueError(f"Duplicate finding id {d.finding_id!r} for criterion {d.criterion_id!r}")
        seen_findings_by_crit[d.criterion_id].add(d.finding_id)
        if d.finding_id in existing_sources or f"critique:{d.finding_id}" in existing_sources:
            raise ValueError(f"Finding id {d.finding_id!r} already used as source")

    current_evidence = list(target_option.evidence)
    adjustments: list[dict[str, object]] = []

    for delta in deltas:
        crit_pts = [pt for pt in current_evidence if pt.criterion_id == delta.criterion_id]
        if not crit_pts:
            raise ValueError(f"Criterion {delta.criterion_id!r} has no evidence on option {option_id!r}")

        # Step 2: Pool them exactly as the resolver does
        log_odds = 0.0
        for pt in crit_pts:
            prob = min(1.0 - RESOLVER_EPSILON, max(RESOLVER_EPSILON, pt.support))
            log_odds += pt.confidence * _logit(prob)
        s = _sigmoid(log_odds)

        # Step 3: Target: s_star clamped to [TARGET_EPSILON, 1 - TARGET_EPSILON]
        s_star = min(1.0 - TARGET_EPSILON, max(TARGET_EPSILON, s + delta.support_delta))

        # Step 4: Doubt
        mean_c = sum(pt.confidence for pt in crit_pts) / len(crit_pts)
        u = 1.0 - mean_c
        defect_delta = max(0.0, -delta.support_delta)
        u_after = min(1.0, u + kappa * defect_delta)
        c_new = max(1.0 - u_after, CONFIDENCE_FLOOR)

        # Step 5: Support of the appended point that moves pooled log-odds onto target
        delta_lo = _logit(s_star) - _logit(s)
        p_new = _sigmoid(delta_lo / c_new)
        p_new = min(1.0, max(0.0, p_new))

        # Step 6: Append EvidencePoint and record adjustment
        new_pt = EvidencePoint(
            criterion_id=delta.criterion_id,
            source=f"critique:{delta.finding_id}",
            support=p_new,
            confidence=c_new,
        )
        current_evidence.append(new_pt)

        adjustments.append({
            "finding_id": delta.finding_id,
            "criterion_id": delta.criterion_id,
            "support_delta": delta.support_delta,
            "rationale": delta.rationale,
            "basis": delta.basis,
            "rubric_delta": delta.rubric_delta,
            "override": delta.override,
            "rubric_version": RUBRIC_VERSION,
            "support_before": s,
            "support_after": s_star,
            "uncertainty_before": u,
            "uncertainty_after": u_after,
            "point_support": p_new,
            "point_confidence": c_new,
            "kappa": kappa,
        })

    new_options = []
    for opt in frame.options:
        if opt.action.id == option_id:
            new_options.append(
                DecisionOption(
                    action=opt.action,
                    evidence=tuple(current_evidence),
                    constraint_results=dict(opt.constraint_results),
                )
            )
        else:
            new_options.append(opt)

    new_frame = DecisionFrame(
        task=frame.task,
        criteria=frame.criteria,
        options=tuple(new_options),
        constraints=frame.constraints,
        minimum_margin=frame.minimum_margin,
        uncertainty_penalty=frame.uncertainty_penalty,
        max_uncertainty=frame.max_uncertainty,
    )

    return AppliedCritique(frame=new_frame, adjustments=tuple(adjustments))


def to_episode_metadata(applied: AppliedCritique) -> dict[str, object]:
    """Return JSON-serialisable critique adjustments dictionary for episode metadata."""
    return {"critique_adjustments": list(applied.adjustments)}
