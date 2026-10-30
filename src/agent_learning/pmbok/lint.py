"""Plan lint checks (ADR-012; FDD-012 section 3). Pure: standard library only, no I/O, no storage."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..tailoring import compute_flags
from .parser import ParsedPlan, parse_frontmatter
from .standards import (
    CAPS,
    DOMAINS,
    FLOORS,
    GENERATORS,
    HEADINGS,
    MAX_AUTO_RETRIES,
    MIN_OUT_OF_SCOPE_ITEMS,
    NONE_MIN_TOKENS,
    PLAN_DAG,
    PLAN_STANDARDS,
    REQUIRED_KEYS,
    ROUTES,
    TOKEN,
    LintFlag,
)

_PLAN_ID = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", re.ASCII)
_VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+", re.ASCII)
_LEGACY = re.compile(r"[0-9]+\.[0-9]+ \S", re.ASCII)
_NON_EMPTY_LISTS = ("inputs", "outputs")
_LIST_KEYS = ("depends_on", "inputs", "outputs")
_POLICY = {"full_plan": "approve-subsidiary-plan", "pmp_section": "approve-pmp"}


def _flag(message: str) -> LintFlag:
    return LintFlag(code="INVALID_METADATA", tier="B", message=message)


def validate_metadata(metadata: Mapping[str, Any], routes: Sequence[Any] | None = None) -> list[LintFlag]:
    """Check parsed frontmatter against the closed lists and the nine-plan table (FDD-012 section 3.2).

    Returns Tier B ``INVALID_METADATA`` findings, one per problem, in a stable order. A key that is
    missing, empty or of the wrong shape is reported once and the checks that depend on it are skipped.
    ``routes`` are tailoring route records (read by ``plan_id`` and ``route``).
    """
    if not isinstance(metadata, Mapping):
        raise TypeError("metadata must be a mapping")
    if not metadata:
        return [_flag("no metadata: the frontmatter is empty")]

    flags: list[LintFlag] = []
    bad: set[str] = set()

    def fail(key: str, message: str) -> None:
        bad.add(key)
        flags.append(_flag(message))

    # 1. Required keys: present, the right shape, not empty.
    valid: dict[str, Any] = {}
    for key in REQUIRED_KEYS:
        if key not in metadata:
            fail(key, f"{key} is required but missing")
            continue
        value = metadata[key]
        if key in _LIST_KEYS:
            if not isinstance(value, tuple):
                fail(key, f"{key} must be a list, got {value!r}")
            elif key in _NON_EMPTY_LISTS and not value:
                fail(key, f"{key} is required but empty")
            else:
                valid[key] = value
        elif not isinstance(value, str):
            fail(key, f"{key} must be a single value, got {value!r}")
        elif value.strip() == "":
            fail(key, f"{key} is required but empty")
        else:
            valid[key] = value

    # 2. plan_id format and the plan ids this plan depends on.
    if "plan_id" in valid and not _PLAN_ID.fullmatch(valid["plan_id"]):
        fail("plan_id", f"plan_id {valid['plan_id']!r} must be kebab-case (a-z, 0-9, -)")
    for item in valid.get("depends_on", ()):
        if not _PLAN_ID.fullmatch(item):
            fail("depends_on", f"depends_on item {item!r} must be a kebab-case plan_id")

    # 3. Fixed values and formats.
    if "pmbok_edition" in valid and valid["pmbok_edition"] != "PMBOK 8":
        fail("pmbok_edition", f"pmbok_edition {valid['pmbok_edition']!r} must be 'PMBOK 8'")
    if "pmbok_focus_area" in valid and valid["pmbok_focus_area"] != "Planning":
        fail("pmbok_focus_area", f"pmbok_focus_area {valid['pmbok_focus_area']!r} must be 'Planning'")
    if "version" in valid and not _VERSION.fullmatch(valid["version"]):
        fail("version", f"version {valid['version']!r} must look like 1.0.0")
    if "legacy_process" in valid and not _LEGACY.match(valid["legacy_process"]):
        fail("legacy_process", f"legacy_process {valid['legacy_process']!r} must look like '5.1 Plan Scope Management'")

    # 4. Domains from the closed list of seven.
    if "primary_pmbok_domain" in valid and valid["primary_pmbok_domain"] not in DOMAINS:
        fail("primary_pmbok_domain", f"primary_pmbok_domain {valid['primary_pmbok_domain']!r} is not one of {', '.join(DOMAINS)}")
    secondary = metadata.get("secondary_pmbok_domains", ())
    if not isinstance(secondary, tuple):
        fail("secondary_pmbok_domains", f"secondary_pmbok_domains must be a list, got {secondary!r}")
    else:
        for item in secondary:
            if item not in DOMAINS:
                fail("secondary_pmbok_domains", f"secondary_pmbok_domains item {item!r} is not one of {', '.join(DOMAINS)}")

    # 5. Closed lists for route and generator.
    route_ok = "route" in valid and valid["route"] in ROUTES
    if "route" in valid and not route_ok:
        fail("route", f"route {valid['route']!r} is not one of {', '.join(ROUTES)}")
    if "generator" in valid and valid["generator"] not in GENERATORS:
        fail("generator", f"generator {valid['generator']!r} is not one of {', '.join(GENERATORS)}")

    # 6. The governance policy follows the route (any value is accepted for not_applicable).
    if route_ok and valid["route"] in _POLICY and "governance_policy" in valid:
        expected = _POLICY[valid["route"]]
        if valid["governance_policy"] != expected:
            fail(
                "governance_policy",
                f"governance_policy {valid['governance_policy']!r} must be {expected!r} for route {valid['route']!r}",
            )

    # 7. A known plan must follow its row of the ADR-012 section 4.4 table.
    row = PLAN_STANDARDS.get(valid.get("plan_id", ""))
    if row is not None:
        plan_id = valid["plan_id"]
        if "primary_pmbok_domain" in valid and "primary_pmbok_domain" not in bad and valid["primary_pmbok_domain"] != row.primary:
            fail(
                "primary_pmbok_domain",
                f"primary_pmbok_domain {valid['primary_pmbok_domain']!r} differs from the ADR-012 table for {plan_id}: {row.primary!r}",
            )
        if isinstance(secondary, tuple) and "secondary_pmbok_domains" not in bad and set(secondary) != set(row.secondary):
            fail(
                "secondary_pmbok_domains",
                f"secondary_pmbok_domains {list(secondary)!r} differs from the ADR-012 table for {plan_id}: {list(row.secondary)!r}",
            )
        if "legacy_process" in valid and "legacy_process" not in bad and valid["legacy_process"].split(" ")[0] != row.legacy:
            fail(
                "legacy_process",
                f"legacy_process {valid['legacy_process']!r} differs from the ADR-012 table for {plan_id}: number {row.legacy}",
            )

    # 8. The frontmatter route agrees with the tailoring route recorded for the plan.
    if routes and route_ok and "legacy_process" in valid and "legacy_process" not in bad:
        number = valid["legacy_process"].split(" ")[0]
        record = next((r for r in routes if str(r.plan_id) == number), None)
        if record is not None:
            recorded = getattr(record.route, "value", record.route)
            if recorded != valid["route"]:
                fail("route", f"route {valid['route']!r} differs from the tailoring route {recorded!r} recorded for plan {number}")

    return flags


# ---------------------------------------------------------------------------
# Content contract (Story 12.3): word count, headings, floors, caps, boundaries


_COMMENT = re.compile(r"<!--.*?(?:-->|\Z)", re.DOTALL)
_NONE_LINE = re.compile(r"^\s*[-*]?\s*None:\s+(.+)$")
_BULLET = re.compile(r"^\s*[-*]\s+(\S.*)$")
_PLACEHOLDER_BULLET = re.compile(
    r"^(?:\[)?(?:TBD|TBC|FIXME|N/A)(?:\])?[.!]?\s*$",
    re.IGNORECASE,
)
_MD_HEADING = re.compile(r"^\s{0,3}#{1,6}\s")
_MARKERS = ("out-of-scope", "out of scope")
_SECTION_NAMES = (
    "1. Intent, Alignment & Boundaries",
    "2. Domain Mechanics & Standards",
    "3. Governance, Control & Decision Rights",
)


@dataclass(frozen=True)
class LintResult:
    """The outcome of linting one plan: the parsed plan, every finding in a stable order, the word count."""

    plan: ParsedPlan
    flags: tuple[LintFlag, ...]
    word_count: int | None


def _visible(text: str) -> str:
    """The text with fenced code and then HTML comments removed (an unclosed fence or comment runs to the end)."""
    kept: list[str] = []
    in_fence = False
    for line in text.replace("\r\n", "\n").split("\n"):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        elif not in_fence:
            kept.append(line)
    return _COMMENT.sub(" ", "\n".join(kept))


def count_words(body: str) -> int:
    """Count words in a plan body the same way every time (ADR-012 section 4.3.1)."""
    if not isinstance(body, str):
        raise TypeError("body must be a str")
    return len(TOKEN.findall(_visible(body)))


def _option(name: str, value: int | None) -> int:
    if value is None:
        return 0
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an int or None")
    return value


def _content_flag(code: str, tier: str, message: str) -> LintFlag:
    return LintFlag(code=code, tier=tier, message=message)  # type: ignore[arg-type]


def _section_one(visible: str) -> str | None:
    first = HEADINGS[0].search(visible)
    if first is None:
        return None
    newline = visible.find("\n", first.end())
    start = len(visible) if newline == -1 else newline + 1
    second = HEADINGS[1].search(visible, first.end())
    return visible[start : second.start() if second else len(visible)]


def _counts_as_boundary_item(text: str, *, exclude_placeholders: bool) -> bool:
    stripped = text.strip()
    if exclude_placeholders and _PLACEHOLDER_BULLET.fullmatch(stripped):
        return False
    return True


def _boundary_problem(section: str, needed: int, *, exclude_placeholders: bool = False) -> str | None:
    """None when Section 1 states its boundaries; otherwise the reason it does not."""
    lines = section.split("\n")
    reasons: list[str] = []
    short_none = False
    for line in lines:
        match = _NONE_LINE.match(line)
        if match is None:
            continue
        if len(TOKEN.findall(match.group(1))) >= NONE_MIN_TOKENS:
            return None
        short_none = True
    best = -1
    for index, line in enumerate(lines):
        if not any(marker in line.lower() for marker in _MARKERS):
            continue
        seen: set[str] = set()
        for after in lines[index + 1 :]:
            if _MD_HEADING.match(after):
                break
            bullet = _BULLET.match(after)
            if bullet is not None:
                item = bullet.group(1).strip()
                if _counts_as_boundary_item(item, exclude_placeholders=exclude_placeholders):
                    seen.add(item.lower())
            elif seen and after.strip():
                break
        if len(seen) >= needed:
            return None
        best = max(best, len(seen))
    if best >= 0:
        reasons.append(f"the out-of-scope list has {best} distinct item(s); at least {needed} required")
    if short_none:
        reasons.append(f"the 'None:' rationale has fewer than {NONE_MIN_TOKENS} tokens")
    if not reasons:
        reasons.append("Section 1 has no out-of-scope list and no 'None: [rationale]' line")
    return "; ".join(reasons)


def check_content(
    body: str,
    route: str,
    *,
    min_floor_words: int | None = None,
    min_out_of_scope_items: int | None = 1,
    max_cap_words: int | None = None,
    exclude_placeholders: bool = False,
) -> list[LintFlag]:
    """Check a plan body against the content contract (FDD-012 section 3.4).

    Findings come in a stable order: headings (Tier B), floor, cap and boundary (Tier C). A project
    standard may raise the floor or the out-of-scope minimum and never lower it.
    """
    if not isinstance(body, str):
        raise TypeError("body must be a str")
    if route not in ROUTES:
        raise ValueError(f"route must be one of {', '.join(ROUTES)}")
    floor_option = _option("min_floor_words", min_floor_words)
    items_option = _option("min_out_of_scope_items", min_out_of_scope_items)
    if max_cap_words is not None:
        if isinstance(max_cap_words, bool) or not isinstance(max_cap_words, int):
            raise TypeError("max_cap_words must be an int or None")
    if route == "not_applicable":
        return []

    visible = _visible(body)
    flags: list[LintFlag] = []
    for pattern, name in zip(HEADINGS, _SECTION_NAMES):
        if pattern.search(visible) is None:
            flags.append(_content_flag("MISSING_REQUIRED_SECTION", "B", f"Section {name} is missing"))

    count = len(TOKEN.findall(visible))
    floor = max(FLOORS[route], floor_option)
    cap = CAPS[route] if max_cap_words is None else min(CAPS[route], max_cap_words)
    if count < floor:
        flags.append(_content_flag("BELOW_STANDARD_FLOOR", "C", f"{count} words is below the floor of {floor} for a {route}"))
    if count > cap:
        code = "EXCEEDS_SECTION_CAP" if route == "pmp_section" else "EXCEEDS_PLAN_CAP"
        flags.append(_content_flag(code, "C", f"{count} words exceeds the cap of {cap} for a {route}"))

    section = _section_one(visible)
    if section is not None:
        problem = _boundary_problem(
            section,
            max(MIN_OUT_OF_SCOPE_ITEMS, items_option),
            exclude_placeholders=exclude_placeholders,
        )
        if problem is not None:
            flags.append(_content_flag("MISSING_BOUNDARY_DEF", "C", f"Section 1 does not state its boundaries: {problem}"))
    return flags


def omission_flags(routes: Sequence[Any]) -> list[LintFlag]:
    """Turn the tailoring omission flags into Tier C findings (ADR-012 section 4.4, Plan Tier 1)."""
    return [
        LintFlag(code="OMISSION_OF_BASE_PLAN", tier="C", message=flag.message, evidence=flag.evidence)
        for flag in compute_flags(routes)
    ]


def lint_plan(
    text: str,
    *,
    routes: Sequence[Any] | None = None,
    min_floor_words: int | None = None,
    min_out_of_scope_items: int | None = 1,
) -> LintResult:
    """Parse, validate and check one plan (FDD-012 section 3.5). Never raises for content."""
    plan = parse_frontmatter(text)
    if not plan.parsed:
        return LintResult(plan=plan, flags=plan.flags, word_count=None)
    flags = list(plan.flags) + validate_metadata(plan.metadata, routes)
    route = plan.metadata.get("route")
    word_count: int | None = None
    if isinstance(route, str) and route in ROUTES and route != "not_applicable":
        word_count = count_words(plan.body)
        plan_id = plan.metadata.get("plan_id")
        measure = None
        if isinstance(plan_id, str):
            from .scope import check_scope_sections, scope_measure

            measure = scope_measure(plan_id, route)
        if measure is not None:
            floor_option = _option("min_floor_words", min_floor_words)
            items_option = _option("min_out_of_scope_items", min_out_of_scope_items)
            flags += check_content(
                plan.body,
                route,
                min_floor_words=max(measure.floor, floor_option),
                min_out_of_scope_items=max(measure.min_out_of_scope_items, items_option),
                max_cap_words=measure.cap,
                exclude_placeholders=True,
            )
            flags += check_scope_sections(plan.body, route)
        else:
            flags += check_content(
                plan.body, route, min_floor_words=min_floor_words, min_out_of_scope_items=min_out_of_scope_items
            )
    return LintResult(plan=plan, flags=tuple(flags), word_count=word_count)


# ---------------------------------------------------------------------------
# Precedence and the next step (Story 12.4)


class NextStep(str, Enum):
    """What happens to a plan after a lint (FDD-012 section 3.7). No step blocks approval for a Tier B or C flag."""

    READY_FOR_FORMALIZATION = "ready_for_formalization"
    CARRY_TO_APPROVAL = "carry_to_approval"
    HUMAN_ROUTE_REVIEW = "human_route_review"  # keep as a section with a rationale, or graduate to a full plan
    AUTO_REMEDIATE = "auto_remediate"
    ESCALATE_IMMEDIATELY = "escalate_immediately"
    ESCALATE_KEEP_HUMAN_TEXT = "escalate_keep_human_text"
    ESCALATE_RETRIES_EXHAUSTED = "escalate_retries_exhausted"


@dataclass(frozen=True)
class NextStepDecision:
    """The next step, why, and every flag that was passed in (including those that did not decide it)."""

    step: NextStep
    reason: str
    flags: tuple[LintFlag, ...]


def _codes(flags: Sequence[LintFlag]) -> str:
    seen: list[str] = []
    for item in flags:
        if item.code not in seen:
            seen.append(item.code)
    return ", ".join(seen) if seen else "none"


def next_step(flags: Sequence[LintFlag], *, generator: str | None, retries: int = 0) -> NextStepDecision:
    """Decide what happens next from the findings, the generator and the retries already made.

    Rules, first match wins (FDD-012 section 3.7). ``flags`` may include Tier A flags supplied by the caller
    (their detection belongs to ADR-013). ``generator`` is the frontmatter value, or ``None`` when the
    frontmatter was unreadable.
    """
    if isinstance(flags, (str, bytes)) or not isinstance(flags, Sequence):
        raise TypeError("flags must be a sequence of LintFlag")
    if not all(isinstance(item, LintFlag) for item in flags):
        raise TypeError("flags must be a sequence of LintFlag")
    if isinstance(retries, bool) or not isinstance(retries, int):
        raise TypeError("retries must be an int")
    if retries < 0:
        raise ValueError("retries must not be negative")

    held = tuple(flags)
    suffix = f"; flags: {_codes(held)}"
    tiers = {item.tier for item in held}

    def decide(step: NextStep, condition: str) -> NextStepDecision:
        return NextStepDecision(step=step, reason=condition + suffix, flags=held)

    if "A" in tiers:
        return decide(NextStep.ESCALATE_IMMEDIATELY, "a Tier A flag: escalate immediately, never regenerate")
    if generator not in GENERATORS or generator in ("stub", "mock"):
        shown = "unreadable" if generator is None or generator == "" else repr(generator)
        return decide(NextStep.ESCALATE_IMMEDIATELY, f"generator is {shown}: cannot be audited or regenerated, escalate immediately")
    if "B" in tiers:
        if generator == "human":
            return decide(NextStep.ESCALATE_KEEP_HUMAN_TEXT, "a Tier B flag on human-written text: escalate and keep the human text, never regenerate over it")
        if retries < MAX_AUTO_RETRIES:
            return decide(NextStep.AUTO_REMEDIATE, f"a Tier B flag on LLM text with {retries} of {MAX_AUTO_RETRIES} automatic retries used")
        return decide(NextStep.ESCALATE_RETRIES_EXHAUSTED, f"a Tier B flag on LLM text after {retries} retries (limit {MAX_AUTO_RETRIES}): escalate")
    if any(item.code == "EXCEEDS_SECTION_CAP" for item in held):
        return decide(NextStep.HUMAN_ROUTE_REVIEW, "a section over its cap needs a keep-or-graduate decision from a human")
    if held:
        return decide(NextStep.CARRY_TO_APPROVAL, "Tier C flags are evidence carried to approval, not blocks")
    return decide(NextStep.READY_FOR_FORMALIZATION, "no flags: ready for formalization")



def validate_dependencies(
    metadata: Mapping[str, Any],
    dag: Mapping[str, Sequence[str]] = PLAN_DAG,
) -> list[LintFlag]:
    """Validate that a plan's depends_on frontmatter metadata matches the authoritative PLAN_DAG (FDD-013 section 3.4).

    For a plan that is a key of dag, a depends_on that differs as a set from dag[plan_id]
    is one Tier B INVALID_METADATA naming depends_on and the expected list.
    Other plans, and a missing or malformed depends_on, give nothing.
    """
    if not isinstance(metadata, Mapping):
        return []
    plan_id = metadata.get("plan_id")
    if not isinstance(plan_id, str) or plan_id not in dag:
        return []

    depends_on = metadata.get("depends_on")
    if not isinstance(depends_on, (tuple, list)):
        return []
    if not all(isinstance(x, str) for x in depends_on):
        return []

    expected = dag[plan_id]
    if set(depends_on) != set(expected):
        expected_list = list(expected)
        return [
            LintFlag(
                code="INVALID_METADATA",
                tier="B",
                message=f"depends_on differs from authoritative DAG dependencies {expected_list!r}",
                evidence=str(depends_on),
            )
        ]

    return []
