"""Canonical content hashing for subsidiary management plans (ADR-013 section 4.3; FDD-013 section 3.1).

Pure: standard library only, no storage and no I/O.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

from .parser import parse_frontmatter
from .standards import VOLATILE_KEYS

_HARD_BREAK = re.compile(r"\S  $")


def _clean_line(line: str) -> str:
    """Strip trailing whitespace, preserving exactly two trailing spaces after content."""
    if _HARD_BREAK.search(line):
        return line.rstrip(" \t") + "  "
    return line.rstrip(" \t")


def compute_canonical_plan_hash(text: str) -> str:
    """Compute the 64-character lowercase hex SHA-256 canonical hash of a plan.

    Order of operations (FDD-013 section 3.1):
    1. Strip leading BOMs (\\ufeff), then NFC-normalize.
    2. Normalize \\r\\n and lone \\r to \\n.
    3. The frontmatter must parse (Epic 12 parse_frontmatter); otherwise ValueError.
       Remove from the frontmatter block the lines of each key in VOLATILE_KEYS
       (the key line and the '  - ' lines that follow it). All other lines,
       including comments and key order, stay.
    4. Strip trailing whitespace on every line. Exactly two trailing spaces are kept
       only on a line that has other content before them (a Markdown hard break);
       a whitespace-only line becomes empty.
    5. Strip leading and trailing blank lines of the whole text.
    6. SHA-256 of the UTF-8 encoding (errors="surrogatepass").
    """
    if not isinstance(text, str):
        raise TypeError(f"text must be a str, got {type(text).__name__}")

    # 1. Strip leading BOMs, then NFC-normalize
    text = text.lstrip("\ufeff")
    text = unicodedata.normalize("NFC", text)

    # 2. Normalize \r\n and lone \r to \n
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Clean lines (strip trailing whitespace, keep Markdown hard breaks, empty blank lines)
    raw_lines = [_clean_line(line) for line in text.split("\n")]

    # Strip leading blank lines so frontmatter starts on line 1 of non-blank content
    start_idx = 0
    while start_idx < len(raw_lines) and raw_lines[start_idx] == "":
        start_idx += 1

    trimmed_lines = raw_lines[start_idx:]
    trimmed_text = "\n".join(trimmed_lines)

    # 3. Frontmatter must parse
    parsed = parse_frontmatter(trimmed_text)
    if not parsed.parsed:
        messages = "; ".join(flag.message for flag in parsed.flags)
        raise ValueError(f"Plan frontmatter failed to parse: {messages}")

    closing = next(i for i in range(1, len(trimmed_lines)) if trimmed_lines[i] == "---")

    filtered_fm_lines: list[str] = []
    in_volatile_list = False

    for line in trimmed_lines[1:closing]:
        if line.startswith("  - "):
            if in_volatile_list:
                continue
            filtered_fm_lines.append(line)
            continue

        colon = line.find(":")
        if line and line[0] not in " \t#" and colon != -1:
            key = line[:colon]
            rest = line[colon + 1 :]
            if key in VOLATILE_KEYS:
                value_text = rest.lstrip(" ")
                in_volatile_list = value_text == "" or value_text.startswith("#")
                continue
            else:
                in_volatile_list = False
                filtered_fm_lines.append(line)
                continue

        filtered_fm_lines.append(line)

    all_lines = ["---"] + filtered_fm_lines + ["---"] + trimmed_lines[closing + 1 :]

    # 4 & 5. Strip leading and trailing blank lines of the whole text
    while all_lines and all_lines[0] == "":
        all_lines.pop(0)
    while all_lines and all_lines[-1] == "":
        all_lines.pop()

    canonical_text = "\n".join(all_lines)

    # 6. SHA-256 of UTF-8 encoding with surrogatepass
    return hashlib.sha256(canonical_text.encode("utf-8", errors="surrogatepass")).hexdigest()


def raw_change_hash(text: str) -> str:
    """Compute the raw change hash: 'raw:' plus SHA-256 of the exact UTF-8 text."""
    if not isinstance(text, str):
        raise TypeError(f"text must be a str, got {type(text).__name__}")
    digest = hashlib.sha256(text.encode("utf-8", errors="surrogatepass")).hexdigest()
    return f"raw:{digest}"


def is_raw_hash(hash_val: str) -> bool:
    """Return True if hash_val starts with 'raw:'."""
    if not isinstance(hash_val, str):
        raise TypeError(f"hash_val must be a str, got {type(hash_val).__name__}")
    return hash_val.startswith("raw:")


def plan_hash(text: str) -> str:
    """Return canonical hash when frontmatter parses, else raw_change_hash."""
    if not isinstance(text, str):
        raise TypeError(f"text must be a str, got {type(text).__name__}")
    try:
        return compute_canonical_plan_hash(text)
    except ValueError:
        return raw_change_hash(text)
