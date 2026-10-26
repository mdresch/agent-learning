# Epic 12: Subsidiary Management Plan Standards and Content Contracts

**Source ADR:** [ADR-012](../adr/ADR-012-subsidiary-management-plan-standards-and-content-contracts.md) — Accepted (2026-10-25)  
**Source BRD/FDD:** [BRD-012](../project-docs/Business-Requirements/BRD-012-subsidiary-management-plan-standards-and-content-contracts.md) / [FDD-012](../project-docs/Functional-Design/FDD-012-subsidiary-management-plan-standards-and-content-contracts.md)  
**Status:** Draft — stories derived from Accepted ADR-012, BRD-012 and FDD-012; awaiting `approve-user-stories`.  

Four stories build the pure plan lint in `src/agent_learning/pmbok/`. Each rule sits in exactly one story's criteria (LL-012). Contract tests are `tests/test_plan_parser.py`, `tests/test_plan_metadata.py`, `tests/test_plan_content.py` and `tests/test_plan_next_step.py`. Fixtures that are real artifacts live committed under `tests/fixtures/pmbok/`; the conformance tests also read the real ADR files, anchored to the test file's location (LL-006).

---

## Story 12.1 — The Frontmatter Grammar Parser

**Status:** Draft  
**As** a maintainer reading generated plans,  
**I want** frontmatter read by a fixed standard-library grammar that reports every violation instead of crashing,  
**So that** a plan with broken metadata is found and sent to a human, and no outside YAML package is needed.

### Acceptance Criteria:
- **$AC_0$ (Canonical Example):** The ADR-012 §4.2 example frontmatter parses with `parsed=True` and every field equal to the documented value (scalars as `str`, lists as tuples, `[]` as `()`), and the body and its start line are correct.
- **$AC_1$ (Grammar Rules):** Each rule of FDD-012 §3.1 is covered by passing and failing cases: CRLF and a leading BOM are normalized; delimiters must stand alone on their lines; keys match `^[a-z_]+$`; double-quoted escapes work and single-quoted text is literal; bare tokens must match `^[A-Za-z0-9_.-]+$`; lists use exactly two spaces; comments are allowed after a scalar, `[]`, a bare key and a list item, and a `#` inside quotes is text.
- **$AC_2$ (Findings, Never Exceptions):** Duplicate keys, an unquoted value with spaces, a nested mapping, a block scalar, an anchor or alias, a flow mapping, a type tag, a missing opening delimiter and a missing closing delimiter each produce a Tier B `INVALID_METADATA` finding with the 1-based line and the line's content. Empty text and a text of only a BOM do the same. No input makes `parse_frontmatter` raise (a `str` is required; anything else raises `TypeError`).
- **$AC_3$ (Fail Closed):** When any finding is produced, `parsed` is `False`, `metadata` is `{}` and `body` is `""`.
- **$AC_4$ (Volatile Parity Ready):** Parsing the same text twice, and parsing the LF and CRLF forms of the same text, give equal results. The parsed mapping keeps the keys in file order.
- **$AC_5$ (Purity):** `parser.py` imports only the standard library, nothing from storage, from the legacy `pmbok/` directory or from `agent_learning.tailoring`.

---

## Story 12.2 — Metadata Validation and the Nine-Plan Standards

**Status:** Draft  
**As** a governance reviewer,  
**I want** a plan's metadata checked against the closed lists and the ADR-012 table,  
**So that** a wrong domain, route or generator is a visible finding and the route agrees with the tailoring matrix.

### Acceptance Criteria:
- **$AC_0$ (Required Fields):** `validate_metadata` returns one Tier B `INVALID_METADATA` finding for each missing or empty required key in FDD-012 §2.1; `secondary_pmbok_domains` and `depends_on` may be absent or empty respectively, and `inputs` and `outputs` may not be empty. An empty mapping returns a single "no metadata" finding.
- **$AC_1$ (Closed Lists and Formats):** A primary or secondary domain outside the seven, a `route` or `generator` outside its list, a `pmbok_edition` other than "PMBOK 8", a `pmbok_focus_area` other than "Planning", a malformed `version`, `legacy_process`, `plan_id` or `depends_on` item each produce a finding naming the key and the value.
- **$AC_2$ (Governance Policy):** `governance_policy` must be `approve-subsidiary-plan` for `full_plan` and `approve-pmp` for `pmp_section`; for `not_applicable` any value passes.
- **$AC_3$ (Nine-Plan Table):** `PLAN_STANDARDS` holds the nine rows of ADR-012 §4.4 (primary domain, secondary domains, legacy number, Plan Tier). For each known `plan_id`, a domain set or legacy number that differs from the table is a finding. An unknown `plan_id` is checked only against the closed lists.
- **$AC_4$ (Route Agreement):** Given `tailoring.PlanRoute` records, a frontmatter `route` that differs from the plan's recorded route is a finding; a plan absent from the records is not.
- **$AC_5$ (Conformance):** The frontmatter of each of the nine daughter ADRs (ADR-025 to ADR-033, read from `docs/adr/`) parses and returns no metadata finding, so a drift between the ADRs and the table is caught.
- **$AC_6$ (Extra Keys):** Keys beyond the required and optional ones, such as `cycle_id`, are accepted without a finding.

---

## Story 12.3 — The Content Contract: Headings, Length and Boundaries

**Status:** Draft  
**As** a governance reviewer,  
**I want** every plan measured the same way for structure, length and stated boundaries,  
**So that** flags are reproducible evidence and a project standard can only raise the bar.

### Acceptance Criteria:
- **$AC_0$ (Word Count):** `count_words` counts only the body after the closing delimiter, ignores raw HTML comments (including multi-line) and fenced code (including an unclosed fence), counts "don't" as one word and "well-known" as two, and ignores `##`, `---`, `|` and `-` on their own. A fixed text returns a known count.
- **$AC_1$ (Headings):** Each missing mandatory heading (the three regexes of ADR-012 §4.3.1) produces one Tier B `MISSING_REQUIRED_SECTION` finding; present headings produce none; heading order is not checked.
- **$AC_2$ (Floors):** A body below the floor for its route (150 for `pmp_section`, 600 for `full_plan`) produces a Tier C `BELOW_STANDARD_FLOOR`; a count equal to the floor does not. `min_floor_words` above the baseline raises the floor; a value below it is ignored.
- **$AC_3$ (Caps):** A `pmp_section` above 800 words produces `EXCEEDS_SECTION_CAP`; a `full_plan` above 5,000 produces `EXCEEDS_PLAN_CAP`; a count equal to the cap does not. Both are Tier C.
- **$AC_4$ (Boundary Declaration):** Section 1 passes with a `None:` line whose rationale has at least 10 tokens, or with an out-of-scope marker followed by at least the required number of distinct bullets (baseline 1; `min_out_of_scope_items` can raise it, never lower it). A `None:` line with fewer than 10 tokens, a marker with too few bullets, and no declaration each produce a Tier C `MISSING_BOUNDARY_DEF`. A plan with no Section 1 heading gets no boundary finding.
- **$AC_5$ (Route Not Applicable):** `check_content` returns `[]` for a `not_applicable` route; `lint_plan` still validates the metadata.
- **$AC_6$ (Omission of a Base Plan):** `omission_flags` turns each `tailoring.compute_flags` result into a Tier C `OMISSION_OF_BASE_PLAN`; the Charter-defined Tier 1 plans (scope, schedule, cost) can raise it and no other plan can.
- **$AC_7$ (`lint_plan`):** `lint_plan` runs parse, metadata and content in the stable order of FDD-012 §3.5, returns only grammar findings and `word_count=None` when parsing failed, is deterministic (the same text gives the same result), and never raises for any text.

---

## Story 12.4 — Precedence and the Next Step

**Status:** Draft  
**As** a maintainer deciding what happens after a lint,  
**I want** the next step fixed by the findings, the generator and the retry count,  
**So that** an LLM plan is retried at most twice, a human's text is never overwritten, and flags reach the approver as evidence instead of blocks.

### Acceptance Criteria:
- **$AC_0$ (Precedence):** `next_step` applies the table of FDD-012 §3.7 in order, so Tier A beats Tier B beats Tier C in every mixed set; a test covers each pair.
- **$AC_1$ (Immediate Escalation):** A Tier A flag, a `stub` or `mock` generator, a `None` generator (unreadable frontmatter) and an unknown generator value each give `ESCALATE_IMMEDIATELY`, whatever the retry count.
- **$AC_2$ (Human Text Is Kept):** A Tier B flag with `generator == "human"` gives `ESCALATE_KEEP_HUMAN_TEXT` and never `AUTO_REMEDIATE`.
- **$AC_3$ (Bounded Retries):** A Tier B flag with `generator == "llm"` gives `AUTO_REMEDIATE` for `retries` 0 and 1 and `ESCALATE_RETRIES_EXHAUSTED` from 2; `retries` is not changed by the call.
- **$AC_4$ (Content Flags Are Evidence):** `EXCEEDS_SECTION_CAP` gives `HUMAN_ROUTE_REVIEW`; any other Tier C flag, including `EXCEEDS_PLAN_CAP` and `OMISSION_OF_BASE_PLAN`, gives `CARRY_TO_APPROVAL`; no flags gives `READY_FOR_FORMALIZATION`. No Tier B or C flag ever produces a step that blocks approval.
- **$AC_5$ (Total and Explained):** Every combination of {no flag, Tier C only, section cap, Tier B, Tier A} × {llm, human, stub, mock, `None`} × {retries 0, 1, 2} returns exactly one step with a non-empty `reason` that names the deciding condition and the flag codes.
- **$AC_6$ (No Storage, No New Dependency):** `lint.py` and `standards.py` import nothing from storage or the legacy `pmbok/`; `pyproject.toml` gains no dependency; the result types are plain frozen dataclasses with no record type added to `LearningStore` (ADR-002 Invariant #2).

---

## Out of Scope per BRD-012/FDD-012

- Tier A detection, the content hash, the dependency graph and staleness, and the `approve-subsidiary-plan` gate (ADR-013).
- Orchestration commands, runtime clients and the legacy `pmbok/` removal (ADR-034).
- Domain-specific content rules (daughter ADRs 025 to 033) beyond raising a floor or the out-of-scope minimum.
- Scoring plan quality beyond structure and length.
