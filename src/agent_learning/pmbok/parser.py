"""Frontmatter grammar parser (ADR-012 section 4.2.1; normative text ADR-034 section 4.3.1).

A fixed standard-library subset of YAML: flat keys, quoted or bare scalars, ``[]``, lists of scalars
and comments. Every violation becomes a Tier B ``INVALID_METADATA`` finding with its line and
content; the parser never raises for content and fails closed (nothing half-read is returned).
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Union

from .standards import LintFlag

Value = Union[str, "tuple[str, ...]"]

_KEY = re.compile(r"[a-z_]+")
_BARE = re.compile(r"[A-Za-z0-9_.-]+")
_NESTED = re.compile(r"\s+[a-z_]+:")
_ESCAPES = {'"': '"', "\\": "\\", "n": "\n"}


@dataclass(frozen=True)
class ParsedPlan:
    """The result of reading a plan's frontmatter."""

    parsed: bool
    metadata: Mapping[str, Value]
    body: str
    body_start_line: int | None
    flags: tuple[LintFlag, ...]


def _flag(message: str, line_no: int, line: str) -> LintFlag:
    return LintFlag(code="INVALID_METADATA", tier="B", message=message, line=line_no, evidence=line)


def _failed(*flags: LintFlag) -> ParsedPlan:
    return ParsedPlan(parsed=False, metadata=MappingProxyType({}), body="", body_start_line=None, flags=tuple(flags))


def _trailer_ok(rest: str) -> bool:
    """Only whitespace, or whitespace followed by a comment, may follow a value."""
    return rest.strip() == "" or (rest[0] in " \t" and rest.lstrip().startswith("#"))


def _scalar(value: str) -> tuple[Value | None, str | None]:
    """Parse one scalar; return ``(value, None)`` or ``(None, error message)``."""
    first = value[0]
    if first == '"':
        out: list[str] = []
        i = 1
        while i < len(value):
            ch = value[i]
            if ch == "\\":
                nxt = value[i + 1] if i + 1 < len(value) else ""
                if nxt not in _ESCAPES:
                    return None, "unsupported escape in a double-quoted string"
                out.append(_ESCAPES[nxt])
                i += 2
            elif ch == '"':
                if not _trailer_ok(value[i + 1 :]):
                    return None, "text after a quoted value that is not a comment"
                return "".join(out), None
            else:
                out.append(ch)
                i += 1
        return None, "unterminated double-quoted string"
    if first == "'":
        end = value.find("'", 1)
        if end == -1:
            return None, "unterminated single-quoted string"
        if not _trailer_ok(value[end + 1 :]):
            return None, "text after a quoted value that is not a comment"
        return value[1:end], None
    if first == "[":
        if not value.startswith("[]") or not _trailer_ok(value[2:]):
            return None, "only the empty list [] is supported"
        return (), None
    if first == "{":
        return None, "flow mappings are not supported"
    if first in "|>":
        return None, "block scalars are not supported"
    if first in "&*":
        return None, "anchors and aliases are not supported"
    if first == "!":
        return None, "type tags are not supported"
    token = re.match(r"\S*", value).group()  # type: ignore[union-attr]
    if not _BARE.fullmatch(token):
        return None, "an unquoted value must match [A-Za-z0-9_.-]+; quote it"
    if not _trailer_ok(value[len(token) :]):
        return None, "an unquoted value must be a single token; quote it"
    return token, None


def parse_frontmatter(text: str) -> ParsedPlan:
    """Read the frontmatter of ``text``; see FDD-012 section 3.1."""
    if not isinstance(text, str):
        raise TypeError("text must be a str")
    normalized = text.replace("\r\n", "\n")
    normalized = normalized.removeprefix("﻿")
    lines = normalized.split("\n")
    shown = lines[:-1] if len(lines) > 1 and lines[-1] == "" else lines

    if lines[0] != "---":
        return _failed(_flag("frontmatter must start with a line that is exactly ---", 1, lines[0]))
    closing = next((i for i in range(1, len(lines)) if lines[i] == "---"), None)
    if closing is None:
        return _failed(_flag("frontmatter has no closing --- line", len(shown), shown[-1]))

    metadata: dict[str, Value] = {}
    flags: list[LintFlag] = []
    current: list[str] | None = None  # the list a following "  - item" line belongs to
    owners: dict[str, list[str]] = {}

    for index in range(1, closing):
        line = lines[index]
        number = index + 1
        stripped = line.strip()
        if stripped == "" or stripped.startswith("#"):
            continue
        if line.startswith("  - "):
            if current is None:
                flags.append(_flag("list item without a key that opens a list", number, line))
                continue
            item = line[4:]
            if item.strip() == "":
                flags.append(_flag("empty list item", number, line))
                continue
            value, error = _scalar(item.lstrip(" "))
            if error is not None or isinstance(value, tuple):
                flags.append(_flag(error or "a list item must be a scalar", number, line))
                continue
            current.append(value)  # type: ignore[arg-type]
            continue
        if line[0] in " \t":
            message = "nested mappings are not supported" if _NESTED.match(line) else "unsupported indentation"
            flags.append(_flag(message, number, line))
            current = None
            continue
        current = None
        colon = line.find(":")
        if colon == -1:
            flags.append(_flag("expected key: value", number, line))
            continue
        key, rest = line[:colon], line[colon + 1 :]
        if not _KEY.fullmatch(key):
            flags.append(_flag("keys must match [a-z_]+", number, line))
            continue
        duplicate = key in metadata or key in owners
        if duplicate:
            flags.append(_flag(f"duplicate key {key}", number, line))
        if rest != "" and rest[0] != " ":
            flags.append(_flag("a value must follow the colon after a space", number, line))
            continue
        value_text = rest.lstrip(" ")
        if value_text == "" or value_text.startswith("#"):
            items: list[str] = []
            current = items
            if not duplicate:
                owners[key] = items
                metadata[key] = ()  # replaced by the collected items below
            continue
        value, error = _scalar(value_text)
        if error is not None:
            flags.append(_flag(error, number, line))
        elif not duplicate:
            metadata[key] = value  # type: ignore[assignment]

    if flags:
        return _failed(*flags)
    for key, items in owners.items():
        metadata[key] = tuple(items)
    return ParsedPlan(
        parsed=True,
        metadata=MappingProxyType(metadata),
        body="\n".join(lines[closing + 1 :]),
        body_start_line=closing + 2,
        flags=(),
    )
