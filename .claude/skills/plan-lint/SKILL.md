---
name: plan-lint
description: Pure lint for subsidiary management plans (ADR-012): the stdlib frontmatter grammar parser and shared LintFlag type in agent_learning.pmbok; later stories add metadata, content and next-step checks.
---

# Plan lint (agent_learning.pmbok)

**Governing:** ADR-012 (grammar text: ADR-034 section 4.3.1), BRD-012, FDD-012, Epic 12; Scope profile ADR-025 / FDD-025, Epic 25 (Stories 25.1–25.2); Schedule profile ADR-026 / FDD-026, Epic 26 (Story 26.1). Contract files: `tests/test_plan_parser.py` (Story 12.1), `tests/test_plan_metadata.py` (Story 12.2), `tests/test_plan_content.py` (Story 12.3), `tests/test_plan_next_step.py` (Story 12.4), `tests/test_scope_measure.py` (Story 25.1), `tests/test_scope_sections.py` (Story 25.2), `tests/test_schedule_measure.py` (Story 26.1).

## What it is
A pure package (standard library only, no I/O, no storage) that reads a plan's text and returns plain data. It is the new `agent_learning.pmbok` package named in ADR-034 section 4.3; it is not the legacy top-level `pmbok/` directory, which is never imported here.

## Built so far (Stories 12.1 to 12.4, Epic 12 complete)
- `parse_frontmatter(text) -> ParsedPlan`: the fixed grammar subset (flat `[a-z_]+` keys; double-quoted, single-quoted or bare `[A-Za-z0-9_.-]+` scalars; `[]`; lists with exactly two spaces; comments only after whitespace).
- `LintFlag(code, tier, message, line, evidence)` in `standards.py`. A tier outside A, B, C raises `ValueError` at construction, so `next_step` never meets one; `label` prints `FLAG: ` plus the code (the code is stored without the prefix).
- `validate_metadata(metadata, routes=None) -> list[LintFlag]` in `lint.py`: required keys, formats, the closed lists (`DOMAINS`, `ROUTES`, `GENERATORS`), the governance policy that follows the route, the nine-plan table `PLAN_STANDARDS` (a `PlanStandard(primary, secondary, legacy, plan_tier)` per plan, equal to ADR-012 section 4.4) and agreement with tailoring routes. Extra keys such as `cycle_id` are accepted.

## Load-bearing constraints
- **Never raises for content.** Every violation is a Tier B `INVALID_METADATA` finding with the 1-based line and the line's content. Only a non-`str` argument raises `TypeError`.
- **Fail closed.** With any finding, `parsed` is `False`, `metadata` is `{}`, `body` is `""` and `body_start_line` is `None`. Nothing half-read is used.
- **Deterministic.** LF and CRLF forms, and repeated calls, give equal results; keys keep file order; `metadata` is a read-only mapping (scalars `str`, lists `tuple[str, ...]`, `[]` is `()`).
- **Purity.** `parser.py` may import the standard library and `standards` only: not storage, not `tailoring`, not the legacy `pmbok/`, not a YAML library (`pyyaml` is still in `pyproject.toml` for the legacy stack that ADR-034 removes). A contract test reads the imports.
- **One finding per problem, no cascade.** A key that is missing, empty or of the wrong shape is reported once; checks that depend on it (policy, table, route agreement) are skipped. Findings are Tier B `INVALID_METADATA` with `line=None` and the key and value in the message. Only a non-mapping argument raises `TypeError`.
- **The table is checked against the ADR.** `tests/test_plan_metadata.py` reads ADR-012 section 4.4 and the frontmatter example of each of ADR-025 to ADR-033, so drift between the ADRs and `PLAN_STANDARDS` fails a test. `PLAN_STANDARDS.plan_tier` is a Plan Tier (1 to 3), never a Flag Tier.
- **Routes are read by attribute.** `validate_metadata` matches a tailoring `PlanRoute` by `plan_id` equal to the legacy number (`"5.1"`). `lint.py` imports `tailoring` only for `omission_flags` (it wraps `compute_flags`); nothing imports storage or the legacy `pmbok/`.
- **Measured, not judged.** `count_words(body)` removes fenced code (lines starting with three backticks; an unclosed fence runs to the end) and then HTML comments, then counts ADR tokens. Headings and Section 1 are read from that same visible text, so a heading or boundary declaration inside code or a comment does not count. A count equal to a floor or cap is not a finding. A project standard may raise `min_floor_words` or `min_out_of_scope_items`, never lower them.
- **Known quirk of the ADR tokenizer.** A word touching an underscore (`snake_case`, `plan_id`) gives no token, because the underscore is a word character for ``. The test pins it; changing it needs an ADR-012 / ADR-034 amendment.
- **The next step is fixed.** `next_step(flags, *, generator, retries=0) -> NextStepDecision(step, reason, flags)` applies seven rules, first match wins: a Tier A flag, or a generator that is `stub`, `mock`, `None` or unknown, escalates immediately; Tier B with a `human` generator keeps the human text (never regenerated over); Tier B with an `llm` generator is auto-remediated for `retries` 0 and 1 (`MAX_AUTO_RETRIES = 2`) and escalated from 2; an `EXCEEDS_SECTION_CAP` asks for a keep-or-graduate review; any other Tier C flag (including `EXCEEDS_PLAN_CAP` and `OMISSION_OF_BASE_PLAN`) is carried to approval; no flags is ready for formalization. `reason` names the deciding condition and lists every flag code; `flags` holds every flag passed in. Tier B and C flags are evidence for a human and never produce the immediate-escalation step. A bad `retries` (bool, non-int, negative) or a non-`LintFlag` item is a call error, not content.
- **Grammar is not YAML.** Do not widen it to "make a file parse": a plan that breaks the subset goes to a human (ADR-012 section 4.2.1 rule 8).

## Scope profile (Epic 25)
- `scope.py`: `scope_measure(plan_id, route)` returns Scope-only floors, caps, and out-of-scope minimums (`pmp_section`: 180 / 750 / 2; `full_plan`: 700 / 4500 / 4). Other plans keep universal `FLOORS` / `CAPS` / `MIN_OUT_OF_SCOPE_ITEMS`.
- `lint_plan` applies the Scope profile when `plan_id` is `scope-management`: caller `min_floor_words` / `min_out_of_scope_items` cannot relax below the profile; they may raise the bar. `check_content(..., exclude_placeholders=True)` drops placeholder bullets (`TBD`, `TBC`, `FIXME`, `N/A`) from the out-of-scope count.
- `check_scope_sections(body, route)`: Tier B Section 2 checks for WBS phrasing, Definition of Done, embedded hierarchy (`pmp_section`: two of phase/epic/story/commit/work package or an arrow link), and full-plan dictionary fields (phase, epic, story, commit or work package; acceptance criteria, owner, parent). Returns `[]` when Section 2 heading is absent (heading finding only). `lint.py` may import `scope`; purity tests allow that sibling.
- **Advisory policy (Stories 25.3–25.4):** `agent_learning.policy.scope_advice` — `baseline_snapshot()`, `recommend(...)` (one `decision_kind` per call, in-process memo by `recommendation_id`), `advice_reward(followed)`. Task id `advise-scope-plan-decision`; separate from `approve-subsidiary-plan`. Contracts: `tests/test_scope_advice_policy.py`, `tests/test_scope_advice_reward.py`. Idle shape: `docs/policy-shapes/advise-scope-plan-decision.actions.json`.

## Schedule profile (Epic 26)
- `schedule.py`: `schedule_measure(plan_id, route)` returns Schedule-only floors, caps, and out-of-scope minimums (`pmp_section`: 180 / 750 / 2; `full_plan`: 700 / 4500 / 4); all other plans and `not_applicable` return `None`.
- `lint_plan` applies the Schedule profile only to `schedule-management`, using the shared `max_cap_words` and `exclude_placeholders` arguments. It does not apply Scope Section 2 checks to a Schedule plan.
- `schedule.py` is pure: no storage imports, I/O, network access, or new package dependencies.

## Out of scope (see FDD-012 section 5)
Tier A detection, the content hash, the dependency graph, staleness and the approval gate (ADR-013; built in Epic 13, see the `plan-approval-gate` skill); orchestration and the legacy removal (ADR-034); remaining per-plan domain rules (ADR-026 to ADR-033); wiring advisory `recommend` into a CLI (Epic 34).

## Call sites
- `agent_learning.pmbok.__init__` re-exports `ScheduleMeasure` and `schedule_measure` alongside the Scope profile symbols.
- `agent_learning/__init__.py` re-exports `LintFlag`, `ParsedPlan`, `parse_frontmatter`, `validate_metadata`, `PLAN_STANDARDS`, `PlanStandard`, `LintResult`, `check_content`, `count_words`, `lint_plan`, `omission_flags`, `NextStep`, `NextStepDecision` and `next_step`.
- No orchestrator or CLI call site yet.
