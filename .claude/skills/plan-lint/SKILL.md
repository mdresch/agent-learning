---
name: plan-lint
description: Pure lint for subsidiary management plans (ADR-012): the stdlib frontmatter grammar parser and shared LintFlag type in agent_learning.pmbok; later stories add metadata, content and next-step checks.
---

# Plan lint (agent_learning.pmbok)

**Governing:** ADR-012 (grammar text: ADR-034 section 4.3.1), BRD-012, FDD-012, Epic 12. Contract files: `tests/test_plan_parser.py` (Story 12.1); `tests/test_plan_metadata.py`, `tests/test_plan_content.py`, `tests/test_plan_next_step.py` follow in Stories 12.2 to 12.4.

## What it is
A pure package (standard library only, no I/O, no storage) that reads a plan's text and returns plain data. It is the new `agent_learning.pmbok` package named in ADR-034 section 4.3; it is not the legacy top-level `pmbok/` directory, which is never imported here.

## Built so far (Story 12.1)
- `parse_frontmatter(text) -> ParsedPlan`: the fixed grammar subset (flat `[a-z_]+` keys; double-quoted, single-quoted or bare `[A-Za-z0-9_.-]+` scalars; `[]`; lists with exactly two spaces; comments only after whitespace).
- `LintFlag(code, tier, message, line, evidence)` in `standards.py`. The closed tier check and `label` arrive in Story 12.4.

## Load-bearing constraints
- **Never raises for content.** Every violation is a Tier B `INVALID_METADATA` finding with the 1-based line and the line's content. Only a non-`str` argument raises `TypeError`.
- **Fail closed.** With any finding, `parsed` is `False`, `metadata` is `{}`, `body` is `""` and `body_start_line` is `None`. Nothing half-read is used.
- **Deterministic.** LF and CRLF forms, and repeated calls, give equal results; keys keep file order; `metadata` is a read-only mapping (scalars `str`, lists `tuple[str, ...]`, `[]` is `()`).
- **Purity.** `parser.py` may import the standard library and `standards` only: not storage, not `tailoring`, not the legacy `pmbok/`, not a YAML library (`pyyaml` is still in `pyproject.toml` for the legacy stack that ADR-034 removes). A contract test reads the imports.
- **Grammar is not YAML.** Do not widen it to "make a file parse": a plan that breaks the subset goes to a human (ADR-012 section 4.2.1 rule 8).

## Out of scope (see FDD-012 section 5)
Tier A detection, the content hash, the dependency graph, staleness and the approval gate (ADR-013); orchestration and the legacy removal (ADR-034); per-plan domain rules (ADR-025 to ADR-033).

## Call sites
- `agent_learning/__init__.py` re-exports `LintFlag`, `ParsedPlan` and `parse_frontmatter`.
- No orchestrator or CLI call site yet.
