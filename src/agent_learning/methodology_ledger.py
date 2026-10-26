"""Best-practice ledger parser for the learning methodologies.

A pure functional module (standard library plus the tier gates in ``config``): no file I/O and
no storage access. Callers pass the register text in and receive dataclasses out (ADR-036
section 4.3, FDD-036 sections 2.2 and 3).

The register is append-only. A practice is ``adopted`` only on ``real-episodes`` evidence that
meets the outcome gate of the tier declared for the decision (ADR-003); ``synthetic-demo`` and
``source-doc`` evidence can never be adopted. A status change is a new entry that supersedes an
earlier one, and the latest entry in a chain is the current one.
"""

from __future__ import annotations

import re
from collections.abc import Collection
from dataclasses import dataclass

from .config import AutonomyConfig

__all__ = [
    "LedgerEntry",
    "current_entries",
    "parse_ledger",
]

CATALOG_IDS = range(1, 33)
APPLIES_TO = frozenset({"store", "lessons-learned", "both", "other"})
EVIDENCE_CLASSES = frozenset({"source-doc", "synthetic-demo", "real-episodes"})
STATUSES = frozenset({"candidate", "adopted", "retired"})
TIERS = frozenset({"low", "standard", "high", "critical"})

_HEADING = re.compile(r"^## (BP-\d{3})\s*$", re.MULTILINE)
_ANY_H2 = re.compile(r"^## ", re.MULTILINE)
_FIELD = re.compile(r"^- ([a-z_]+):[ \t]*(.*?)\s*$")
_LINK = re.compile(r"^(LL-\d{3}|HYP-AL-\d{3})$")

_REQUIRED = (
    "methodology",
    "practice",
    "preconditions",
    "applies_to",
    "evidence_class",
    "evidence_ref",
    "evidence_count",
    "status",
)
_OPTIONAL = ("tier", "supersedes", "links")


@dataclass(frozen=True)
class LedgerEntry:
    """One practice record in the register."""

    id: str
    methodology: int
    practice: str
    preconditions: str
    applies_to: str
    evidence_class: str
    evidence_ref: str
    evidence_count: int
    status: str
    tier: str | None = None
    supersedes: str | None = None
    links: tuple[str, ...] = ()


def _blocks(text: str) -> list[tuple[str, str]]:
    """Split the register into (entry id, body) pairs; other headings and text are ignored."""
    blocks: list[tuple[str, str]] = []
    headings = list(_HEADING.finditer(text))
    for match in headings:
        end = len(text)
        following = _ANY_H2.search(text, match.end())
        if following is not None:
            end = following.start()
        blocks.append((match.group(1), text[match.end() : end]))
    return blocks


def _fields(entry_id: str, body: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in body.splitlines():
        match = _FIELD.match(line)
        if match is None:
            continue
        key, value = match.groups()
        if key not in _REQUIRED and key not in _OPTIONAL:
            raise ValueError(f"{entry_id}: unknown field {key!r}")
        if key in fields:
            raise ValueError(f"{entry_id}: field {key!r} appears twice")
        fields[key] = value
    missing = [key for key in _REQUIRED if not fields.get(key)]
    if missing:
        raise ValueError(f"{entry_id}: missing or empty fields: {', '.join(missing)}")
    return fields


def _choice(entry_id: str, name: str, value: str, valid: frozenset[str]) -> str:
    if value not in valid:
        raise ValueError(f"{entry_id}: {name} must be one of {', '.join(sorted(valid))}; got {value!r}")
    return value


def _entry(entry_id: str, body: str, known_links: Collection[str] | None) -> LedgerEntry:
    fields = _fields(entry_id, body)
    try:
        methodology = int(fields["methodology"])
    except ValueError:
        raise ValueError(f"{entry_id}: methodology must be an integer; got {fields['methodology']!r}") from None
    if methodology not in CATALOG_IDS:
        raise ValueError(
            f"{entry_id}: methodology {methodology} is outside {CATALOG_IDS.start} to {CATALOG_IDS.stop - 1}"
        )
    try:
        count = int(fields["evidence_count"])
    except ValueError:
        raise ValueError(f"{entry_id}: evidence_count must be an integer; got {fields['evidence_count']!r}") from None
    if count < 0:
        raise ValueError(f"{entry_id}: evidence_count must not be negative; got {count}")

    status = _choice(entry_id, "status", fields["status"], STATUSES)
    evidence_class = _choice(entry_id, "evidence_class", fields["evidence_class"], EVIDENCE_CLASSES)
    applies_to = _choice(entry_id, "applies_to", fields["applies_to"], APPLIES_TO)
    tier = _choice(entry_id, "tier", fields["tier"], TIERS) if fields.get("tier") else None

    if status == "adopted":
        if evidence_class != "real-episodes":
            raise ValueError(
                f"{entry_id}: adopted needs real-episodes evidence; got {evidence_class} (it can never be adopted)"
            )
        if tier is None:
            raise ValueError(f"{entry_id}: adopted needs a declared tier")
        gate = AutonomyConfig.for_tier(tier).min_outcomes  # type: ignore[arg-type]
        if count < gate:
            raise ValueError(f"{entry_id}: adopted has {count} real episodes, below the {tier} tier gate of {gate}")

    links = tuple(part.strip() for part in fields.get("links", "").split(",") if part.strip())
    for link in links:
        if not _LINK.match(link):
            raise ValueError(f"{entry_id}: link {link!r} is not an LL-### or HYP-AL-### identifier")
        if known_links is not None and link not in known_links:
            raise ValueError(f"{entry_id}: link {link} does not resolve to an existing identifier")

    return LedgerEntry(
        id=entry_id,
        methodology=methodology,
        practice=fields["practice"],
        preconditions=fields["preconditions"],
        applies_to=applies_to,
        evidence_class=evidence_class,
        evidence_ref=fields["evidence_ref"],
        evidence_count=count,
        status=status,
        tier=tier,
        supersedes=fields.get("supersedes") or None,
        links=links,
    )


def parse_ledger(text: str, *, known_links: Collection[str] | None = None) -> list[LedgerEntry]:
    """Parse the register text into entries, in register order.

    Raises ``ValueError`` naming the entry for an unknown field or enumeration value, an unknown
    methodology id, an ``adopted`` entry without enough real-episode evidence for its tier, or a
    ``supersedes`` that does not name an earlier entry of the same methodology that no other
    entry already supersedes. When ``known_links`` is given, every link must be in it; ``None``
    skips that check (the format check always runs).
    """
    entries: list[LedgerEntry] = []
    by_id: dict[str, LedgerEntry] = {}
    superseded_by: dict[str, str] = {}
    for entry_id, body in _blocks(text):
        if entry_id in by_id:
            raise ValueError(f"duplicate entry id {entry_id}")
        entry = _entry(entry_id, body, known_links)
        target = entry.supersedes
        if target is not None:
            if target not in by_id:
                raise ValueError(f"{entry_id}: supersedes {target}, which is not an earlier entry")
            if by_id[target].methodology != entry.methodology:
                raise ValueError(f"{entry_id}: supersedes {target}, which concerns a different methodology")
            if target in superseded_by:
                raise ValueError(f"{entry_id}: {target} is already superseded by {superseded_by[target]}")
            superseded_by[target] = entry_id
        by_id[entry_id] = entry
        entries.append(entry)
    return entries


def current_entries(entries: Collection[LedgerEntry]) -> list[LedgerEntry]:
    """Return the entries no other entry supersedes: the latest in each chain."""
    superseded = {entry.supersedes for entry in entries if entry.supersedes}
    return [entry for entry in entries if entry.id not in superseded]
