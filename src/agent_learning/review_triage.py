"""Review-triage record, episode metadata and reviewer reliability evidence.

A pure functional module: no file I/O and no storage access. Callers pass text or plain data in
and receive dataclasses or plain dicts out (ADR-036 section 4.5, FDD-036 sections 2.3 and 3).

The record is the fixed one-line shape the implement-story skill writes in Step 8:
``finding_id | claim type | verified: <v> | decision: <d> | <reason> | fix: <commit or none>``.
Nothing here decides anything: reliability is evidence for a person, and the metadata is a plain
dict a caller may attach to an episode. Triage stays with the human (ADR-003 Invariant 6).
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from .autonomy import wilson_lower_bound

__all__ = [
    "Reliability",
    "TriageRecord",
    "find_triage_lines",
    "parse_triage_line",
    "reconstruct_record",
    "reliability",
    "to_episode_metadata",
]

CLAIM_TYPES = frozenset({"logic error", "crash risk", "test gap", "documentation", "style", "unknown"})
VERIFIED = frozenset({"yes", "no", "partial", "unknown"})
DECISIONS = frozenset({"accepted", "declined", "deferred", "unknown"})
REVIEWERS: Mapping[str, str] = {"Q": "amazon-q"}  # finding-id initial -> reviewer name

_CLAIM_ALIASES = {"logic": "logic error"}
_MODIFIED = "accepted with modification"
_FINDING_ID = re.compile(r"^([A-Z]+)-(\d+)-(\d+)$")
_LOGGED_LINE = re.compile(r"`([A-Z]+-\d+-\d+ \| [^`]*)`")


@dataclass(frozen=True)
class TriageRecord:
    """One triaged review finding."""

    finding_id: str
    reviewer: str
    pr: int
    claim_type: str
    verified: str
    decision: str
    reason: str
    fix: str | None
    reconstructed: bool = False


@dataclass(frozen=True)
class Reliability:
    """Counts and a Wilson lower bound; ``lower_bound`` is None when there are too few cases."""

    cases: int
    verified: int
    lower_bound: float | None


def _choice(name: str, value: str, valid: frozenset[str]) -> str:
    if value not in valid:
        raise ValueError(f"{name} must be one of {', '.join(sorted(valid))}; got {value!r}")
    return value


def _identify(finding_id: str, reviewers: Mapping[str, str]) -> tuple[str, int]:
    match = _FINDING_ID.match(finding_id)
    if match is None:
        raise ValueError(f"finding id must look like Q-12-3 (reviewer initial, PR, ordinal); got {finding_id!r}")
    initial, pr, _ordinal = match.groups()
    if initial not in reviewers:
        raise ValueError(f"reviewer initial {initial!r} in {finding_id} is not known; known: {', '.join(sorted(reviewers))}")
    return reviewers[initial], int(pr)


def parse_triage_line(
    line: str, *, reconstructed: bool = False, reviewers: Mapping[str, str] = REVIEWERS
) -> TriageRecord:
    """Parse one triage line, rejecting any field outside its vocabulary; ``unknown`` is accepted.

    The log's older spellings are read as the FDD vocabulary: the claim type ``logic`` as
    ``logic error``, and the decision ``accepted with modification`` as ``accepted`` with
    ``(with modification)`` put in front of the reason.
    """
    parts = [part.strip() for part in line.strip().split(" | ")]
    if len(parts) < 6:
        raise ValueError(
            "triage line needs: finding_id | claim type | verified: <v> | decision: <d> | <reason> | fix: <commit or none>"
        )
    finding_id, claim, verified, decision, fix = parts[0], parts[1], parts[2], parts[3], parts[-1]
    reason = " | ".join(parts[4:-1])
    if not verified.startswith("verified: "):
        raise ValueError(f"{finding_id}: third field must start with 'verified: '; got {verified!r}")
    if not decision.startswith("decision: "):
        raise ValueError(f"{finding_id}: fourth field must start with 'decision: '; got {decision!r}")
    if not fix.startswith("fix: "):
        raise ValueError(f"{finding_id}: last field must start with 'fix: '; got {fix!r}")
    reviewer, pr = _identify(finding_id, reviewers)

    claim = _CLAIM_ALIASES.get(claim, claim)
    decision_value = decision[len("decision: ") :]
    if decision_value == _MODIFIED:
        decision_value = "accepted"
        reason = f"(with modification) {reason}"
    fix_value = fix[len("fix: ") :]
    return TriageRecord(
        finding_id=finding_id,
        reviewer=reviewer,
        pr=pr,
        claim_type=_choice("claim type", claim, CLAIM_TYPES),
        verified=_choice("verified", verified[len("verified: ") :], VERIFIED),
        decision=_choice("decision", decision_value, DECISIONS),
        reason=reason,
        fix=None if fix_value in {"none", ""} else fix_value,
        reconstructed=reconstructed,
    )


def reconstruct_record(
    finding_id: str,
    *,
    claim_type: str = "unknown",
    verified: str = "unknown",
    decision: str = "unknown",
    reason: str = "unknown",
    fix: str | None = None,
    reviewers: Mapping[str, str] = REVIEWERS,
) -> TriageRecord:
    """Build a backfilled record from what repository history shows; every other field reads unknown."""
    reviewer, pr = _identify(finding_id, reviewers)
    return TriageRecord(
        finding_id=finding_id,
        reviewer=reviewer,
        pr=pr,
        claim_type=_choice("claim type", _CLAIM_ALIASES.get(claim_type, claim_type), CLAIM_TYPES),
        verified=_choice("verified", verified, VERIFIED),
        decision=_choice("decision", decision, DECISIONS),
        reason=reason,
        fix=fix,
        reconstructed=True,
    )


def find_triage_lines(text: str) -> list[str]:
    """Return the triage lines written in backticks in a log, in order."""
    return _LOGGED_LINE.findall(text)


def to_episode_metadata(record: TriageRecord) -> dict[str, Any]:
    """Return the record's fields as a plain dict for an episode's metadata (no record type is added)."""
    return {
        "finding_id": record.finding_id,
        "reviewer": record.reviewer,
        "pr": record.pr,
        "claim_type": record.claim_type,
        "verified": record.verified,
        "decision": record.decision,
        "reason": record.reason,
        "fix": record.fix,
        "reconstructed": record.reconstructed,
    }


def reliability(
    records: Iterable[TriageRecord],
    reviewer: str,
    claim_type: str,
    z: float = 1.96,
    min_cases: int = 5,
) -> Reliability:
    """Count a reviewer's verified claims of one type and return their Wilson lower bound.

    Records whose ``verified`` is ``unknown`` are excluded; ``partial`` counts as not verified.
    Below ``min_cases`` the lower bound is None, never a number the cases cannot support.
    """
    cases = verified = 0
    for record in records:
        if record.reviewer != reviewer or record.claim_type != claim_type:
            continue
        if record.verified == "unknown":
            continue
        cases += 1
        if record.verified == "yes":
            verified += 1
    lower_bound = wilson_lower_bound(verified, cases, z) if cases >= max(min_cases, 1) else None
    return Reliability(cases=cases, verified=verified, lower_bound=lower_bound)
