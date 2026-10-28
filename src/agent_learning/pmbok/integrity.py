"""Technical integrity checks and gate constraint evaluation (ADR-013, FDD-013 section 3.2).

Pure: standard library only, no storage and no I/O.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from .parser import parse_frontmatter
from .standards import (
    PLACEHOLDER_TOKENS,
    PROVISIONAL_TOKENS,
    LintFlag,
)

_COMMENT = re.compile(r"<!--.*?(?:-->|\Z)", re.DOTALL)


def _visible_text(text: str) -> str:
    """The text with fenced code blocks and HTML comments removed."""
    kept: list[str] = []
    in_fence = False
    for line in text.replace("\r\n", "\n").split("\n"):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        elif not in_fence:
            kept.append(line)
    return _COMMENT.sub(" ", "\n".join(kept))


def integrity_flags(
    text: str | None,
    *,
    generation_error: str | None = None,
) -> list[LintFlag]:
    """Check a plan artifact for technical integrity deficiencies (FDD-013 section 3.2).

    Findings are evaluated and returned in fixed priority order:
    1. generation_error (non-empty string): Tier A GENERATION_FAILED.
    2. text is None: Tier A MISSING_ARTIFACT, returning immediately.
    3. Unparseable frontmatter: grammar findings upgraded to Tier A INVALID_METADATA.
    4. Generator is 'stub' or 'mock': Tier A STUB_GENERATOR (skipped if unparseable).
    5. PLACEHOLDER_TOKENS in visible text: Tier A PLACEHOLDER_TOKEN for each token.
    6. Unbracketed PROVISIONAL_TOKENS (TBD, TODO) in visible text: Tier C PROVISIONAL_TOKEN.
    """
    if text is not None and not isinstance(text, str):
        raise TypeError(f"text must be a str or None, got {type(text).__name__}")
    if generation_error is not None and not isinstance(generation_error, str):
        raise TypeError(f"generation_error must be a str or None, got {type(generation_error).__name__}")

    flags: list[LintFlag] = []

    # 1. Generation error
    if generation_error:
        flags.append(
            LintFlag(
                code="GENERATION_FAILED",
                tier="A",
                message=f"generation failed: {generation_error}",
                evidence=generation_error,
            )
        )

    # 2. Missing artifact text
    if text is None:
        flags.append(
            LintFlag(
                code="MISSING_ARTIFACT",
                tier="A",
                message="plan artifact file is missing",
                evidence="",
            )
        )
        return flags

    # 3. Frontmatter parse check
    parsed = parse_frontmatter(text)
    if not parsed.parsed:
        for f in parsed.flags:
            flags.append(
                LintFlag(
                    code="INVALID_METADATA",
                    tier="A",
                    message=f.message,
                    line=f.line,
                    evidence=f.evidence,
                )
            )
    else:
        # 4. Stub generator check (only when frontmatter parses)
        generator = parsed.metadata.get("generator")
        if generator in ("stub", "mock"):
            flags.append(
                LintFlag(
                    code="STUB_GENERATOR",
                    tier="A",
                    message=f"generator is {generator!r}",
                    evidence=generator,
                )
            )

    # 5. Placeholder tokens in visible text
    visible = _visible_text(text)
    for token in PLACEHOLDER_TOKENS:
        if token in visible:
            flags.append(
                LintFlag(
                    code="PLACEHOLDER_TOKEN",
                    tier="A",
                    message=f"placeholder token {token!r}",
                    evidence=token,
                )
            )

    # 6. Unbracketed provisional tokens (TBD, TODO) in visible text
    no_brackets = re.sub(r"\[.*?\]", " ", visible, flags=re.DOTALL)
    for token in PROVISIONAL_TOKENS:
        if re.search(rf"\b{re.escape(token)}\b", no_brackets):
            flags.append(
                LintFlag(
                    code="PROVISIONAL_TOKEN",
                    tier="C",
                    message=f"provisional token {token!r}",
                    evidence=token,
                )
            )

    return flags


def gate_constraint_results(flags: Sequence[LintFlag]) -> dict[str, dict[str, bool]]:
    """Return gate constraint evaluation results for the three approval actions (FDD-013 section 3.2).

    approve_plan is false when any flag is Tier A;
    reject_plan and request_revision_before_decision are always true.
    Tier B and C flags never affect the constraint.
    """
    if not isinstance(flags, (list, tuple)):
        raise TypeError(f"flags must be a list or tuple of LintFlag, got {type(flags).__name__}")

    has_tier_a = any(flag.tier == "A" for flag in flags)
    return {
        "approve_plan": {"no_technical_integrity_block": not has_tier_a},
        "reject_plan": {"no_technical_integrity_block": True},
        "request_revision_before_decision": {"no_technical_integrity_block": True},
    }

