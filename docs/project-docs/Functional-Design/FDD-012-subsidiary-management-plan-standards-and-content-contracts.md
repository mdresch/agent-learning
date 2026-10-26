# FDD-012: Subsidiary Management Plan Standards and Content Contracts

**Source ADR:** [ADR-012](../../adr/ADR-012-subsidiary-management-plan-standards-and-content-contracts.md) — Accepted (2026-10-25)  
**Source BRD:** [BRD-012](../Business-Requirements/BRD-012-subsidiary-management-plan-standards-and-content-contracts.md)  
**Status:** Draft — functional design derived from Accepted ADR-012 and BRD-012; awaiting `approve-fdd`.  

---

## 1. Architecture & Component Placement

1. **Package placement:** `src/agent_learning/pmbok/`, the pure domain package named in ADR-034 §4.3 (which lists `parser.py` for the grammar). It is a new subpackage of the installed package; the legacy top-level `pmbok/` directory is a different import path and is neither read nor imported.
2. **Modules:** `parser.py` (frontmatter grammar), `standards.py` (constants, the nine-plan table and the shared `LintFlag` type, which the parser and the lint both use), `lint.py` (metadata, content and next-step functions). `__init__.py` re-exports the public names, and `agent_learning/__init__.py` re-exports them from there.
3. **Purity boundary:** standard library only (`re`, `dataclasses`, `enum`, `typing`). No file I/O, no storage access, no network, no sleep, no import of `LearningStore`. Callers pass text and plain data and receive dataclasses. This follows ADR-013 Invariant 8 and ADR-034 §4.3.
4. **Reuse:** routes and the Tier 1 omission rule come from `agent_learning.tailoring` (`PlanRoute`, `Route`, `BASELINE_SUBSTANTIATING`, `compute_flags`). Nothing in it is duplicated or changed.
5. **Not here:** Tier A detection, the content hash, the dependency graph and the approval gate (ADR-013); orchestration and the legacy removal (ADR-034).

---

## 2. Data Contract & Domain Model

```python
@dataclass(frozen=True)
class LintFlag:
    code: str                      # e.g. "INVALID_METADATA"
    tier: Literal["A", "B", "C"]   # Flag Tier, never Plan Tier
    message: str
    line: int | None = None        # 1-based line in the original text, when known
    evidence: str = ""             # the offending text, trimmed

    def __post_init__(self) -> None:
        # A tier outside A, B, C is a programming error and raises ValueError at construction,
        # so next_step() never meets one.
        ...

    @property
    def label(self) -> str:
        """The printed form, "FLAG: " followed by the code, e.g. "FLAG: INVALID_METADATA"."""
        return f"FLAG: {self.code}"

@dataclass(frozen=True)
class ParsedPlan:
    parsed: bool                                   # False when the frontmatter broke the grammar
    metadata: Mapping[str, str | tuple[str, ...]]  # {} when parsed is False
    body: str                                      # text after the closing delimiter ("" when parsed is False)
    body_start_line: int | None                    # 1-based line of the first body line; None when parsed is False
    flags: tuple[LintFlag, ...]                    # grammar findings, all Tier B

@dataclass(frozen=True)
class LintResult:
    plan: ParsedPlan
    flags: tuple[LintFlag, ...]       # all findings in a stable order: parse, metadata, content
    word_count: int | None            # None when not counted

class NextStep(str, Enum):
    READY_FOR_FORMALIZATION = "ready_for_formalization"
    CARRY_TO_APPROVAL = "carry_to_approval"
    HUMAN_ROUTE_REVIEW = "human_route_review"            # keep as a section with rationale, or graduate
    AUTO_REMEDIATE = "auto_remediate"
    ESCALATE_IMMEDIATELY = "escalate_immediately"
    ESCALATE_KEEP_HUMAN_TEXT = "escalate_keep_human_text"
    ESCALATE_RETRIES_EXHAUSTED = "escalate_retries_exhausted"

@dataclass(frozen=True)
class NextStepDecision:
    step: NextStep
    reason: str
    flags: tuple[LintFlag, ...]
```

### 2.1 Constants (`standards.py`)
- `DOMAINS = ("Governance", "Scope", "Schedule", "Finance", "Stakeholders", "Resources", "Risk")`
- `ROUTES = ("full_plan", "pmp_section", "not_applicable")`, `GENERATORS = ("llm", "human", "stub", "mock")`
- `REQUIRED_KEYS`: `plan_id, plan_name, pmbok_edition, pmbok_focus_area, primary_pmbok_domain, legacy_process, route, generator, version, baseline_id, owner_role, depends_on, inputs, outputs, governance_policy`. `secondary_pmbok_domains` is optional.
- `FLOORS = {"pmp_section": 150, "full_plan": 600}`, `CAPS = {"pmp_section": 800, "full_plan": 5000}`, `NONE_MIN_TOKENS = 10`, `MIN_OUT_OF_SCOPE_ITEMS = 1`, `MAX_AUTO_RETRIES = 2`
- `HEADINGS`: the three regexes of ADR-012 §4.3.1, compiled with `re.MULTILINE`.
- `TOKEN = re.compile(r"\b[^\W_]+(?:['’][^\W_]+)?\b")`
- `PLAN_STANDARDS`: the table of ADR-012 §4.4, keyed by `plan_id`:

| plan_id | primary | secondary | legacy | Plan Tier |
|---|---|---|---|---|
| scope-management | Scope | Governance | 5.1 | 1 |
| schedule-management | Schedule | Governance | 6.1 | 1 |
| cost-management | Finance | Governance | 7.1 | 1 |
| quality-management | Governance | Scope | 8.1 | 2 |
| resource-management | Resources | Governance | 9.1 | 3 |
| communications-management | Stakeholders | Governance | 10.1 | 3 |
| risk-management | Risk | Governance, Finance | 11.1 | 2 |
| procurement-management | Finance | Resources, Governance | 12.1 | 3 |
| stakeholder-engagement | Stakeholders | Governance | 13.2 | 3 |

---

## 3. Behavior

### 3.1 `parse_frontmatter(text) -> ParsedPlan` (BRU-012-02)
Implements the grammar of ADR-012 §4.2.1 and ADR-034 §4.3.1, rule by rule:
1. Normalize CRLF to LF and strip a leading BOM. The text must start with a line `---`; the frontmatter ends at the next line that is exactly `---` (no leading or trailing whitespace). Missing either delimiter is a grammar finding.
2. Keys match `^[a-z_]+$`, followed by `:`. A duplicate key is a finding.
3. Scalars: double-quoted (with `\"`, `\\`, `\n` escapes), single-quoted (literal), bare tokens `^[A-Za-z0-9_.-]+$`, or `[]`. A value with spaces or symbols that is not quoted is a finding.
4. Lists: lines `  - item` or `  - "item"` with exactly two spaces of indent, after a key with no scalar value.
5. Comments: whole-line comments and blank lines are dropped; `# ...` after whitespace is allowed after a scalar, after `[]`, after a bare key and after a list item. A `#` inside quotes is text.
6. Prohibited: nested mappings, block scalars (`|`, `>`), anchors and aliases (`&`, `*`), flow mappings (`{`), type tags (`!!`) are findings.
7. Every violation becomes a Tier B `LintFlag("INVALID_METADATA", ...)` with the line number and the line's content. The function never raises. If any finding was produced, `parsed` is `False`, `metadata` is `{}` and `body` is `""` (fail closed: nothing half-read is used).
8. On success `body` starts after the closing delimiter and `body_start_line` is its line number. Metadata values are `str` for scalars and `tuple[str, ...]` for lists (`[]` and a key with no items are `()`).

### 3.2 `validate_metadata(metadata, routes=None) -> list[LintFlag]` (BRU-012-03)
Returns Tier B `INVALID_METADATA` findings, one per problem, in the order below. `metadata` is the parsed mapping; an empty mapping returns one finding (no metadata).
1. Each key in `REQUIRED_KEYS` is present and non-empty (a list key may not be `()` for `inputs` and `outputs`; `depends_on` may be `()`).
2. `plan_id` matches `^[a-z][a-z0-9-]*$`; every `depends_on` item matches the same pattern.
3. `pmbok_edition == "PMBOK 8"`, `pmbok_focus_area == "Planning"`, `version` matches `^\d+\.\d+\.\d+$`, `legacy_process` matches `^\d+\.\d+ \S`.
4. `primary_pmbok_domain` is in `DOMAINS`; every item of `secondary_pmbok_domains` is in `DOMAINS`.
5. `route` is in `ROUTES`; `generator` is in `GENERATORS`.
6. `governance_policy` is `approve-subsidiary-plan` when the route is `full_plan` and `approve-pmp` when it is `pmp_section`; for `not_applicable` any value is accepted.
7. When `plan_id` is one of the nine in `PLAN_STANDARDS`, `primary_pmbok_domain`, the secondary domains (as a set) and the number at the start of `legacy_process` equal the table's.
8. When `routes` (a sequence of `tailoring.PlanRoute`) is given and holds the plan's route, the frontmatter `route` equals it. The plan is found by its legacy number; a missing plan in `routes` is not a finding here.
Extra keys beyond the required and optional ones are allowed and ignored (ADR-035 proposes `cycle_id`).

### 3.3 `count_words(body) -> int` (BRU-012-04)
Remove raw HTML comments (`<!-- ... -->`, multi-line) and fenced code blocks (lines from a ```` ``` ```` fence to the next one; an unclosed fence runs to the end), then count `TOKEN` matches.

### 3.4 `check_content(body, route, *, min_floor_words=None, min_out_of_scope_items=1) -> list[LintFlag]` (BRU-012-04, 05)
For `route == "not_applicable"` returns `[]`. Otherwise, in this order:
1. **Headings (Tier B `MISSING_REQUIRED_SECTION`):** one finding per missing heading regex.
2. **Floor (Tier C `BELOW_STANDARD_FLOOR`):** when the word count is below the effective floor. The effective floor is `max(FLOORS[route], min_floor_words or 0)`: a project standard can raise it and never lower it.
3. **Cap (Tier C):** `EXCEEDS_SECTION_CAP` for a `pmp_section` above 800 words; `EXCEEDS_PLAN_CAP` for a `full_plan` above 5,000. A word count equal to the cap or floor is not a finding.
4. **Boundary (Tier C `MISSING_BOUNDARY_DEF`):** Section 1 is the text from the first heading to the second heading (or to the end if the second is missing). The declaration is accepted when either
   - a line matches `^\s*[-*]?\s*None:\s+(.+)$` and the captured rationale has at least `NONE_MIN_TOKENS` tokens, or
   - a line in Section 1 that contains "out-of-scope" or "out of scope" (case-insensitive) is followed by at least `max(MIN_OUT_OF_SCOPE_ITEMS, min_out_of_scope_items)` distinct bullet items (`^\s*[-*]\s+\S`), counted until a heading or a non-blank, non-bullet line after the first bullet.
   Otherwise one finding is raised: a `None:` line whose rationale is too short is reported as such.
If Section 1 is missing (its heading is absent), the boundary check is skipped, because the missing-section finding already covers it.

### 3.5 `lint_plan(text, *, routes=None, min_floor_words=None, min_out_of_scope_items=1) -> LintResult`
`parse_frontmatter`, then (only if parsed) `validate_metadata`, then `check_content` with the frontmatter `route`. If the frontmatter route is invalid, content checks are skipped. If parsing failed, only the grammar findings are returned and `word_count` is `None`. Finding order is stable: parse, metadata, headings, floor, cap, boundary.

### 3.6 `omission_flags(routes) -> list[LintFlag]`
Wraps `tailoring.compute_flags`: each `baseline_plan_omitted` flag becomes a Tier C `LintFlag("OMISSION_OF_BASE_PLAN", ...)` (ADR-012 §4.4 Plan Tier 1; ADR-011 §3.2). It never blocks.

### 3.7 `next_step(flags, *, generator, retries=0) -> NextStepDecision` (BRU-012-06, 07)
`flags` may include Tier A flags supplied by the caller (their detection is ADR-013). `generator` is the frontmatter value, or `None` when the frontmatter was unreadable. `retries` is how many automatic regenerations were already made. Rules, first match wins:

| # | Condition | Step |
|---|---|---|
| 1 | any Tier A flag, or `generator` is `stub`, `mock`, `None` or not in `GENERATORS` | `ESCALATE_IMMEDIATELY` |
| 2 | any Tier B flag and `generator == "human"` | `ESCALATE_KEEP_HUMAN_TEXT` |
| 3 | any Tier B flag, `generator == "llm"`, `retries < MAX_AUTO_RETRIES` | `AUTO_REMEDIATE` |
| 4 | any Tier B flag, `generator == "llm"`, `retries >= MAX_AUTO_RETRIES` | `ESCALATE_RETRIES_EXHAUSTED` |
| 5 | an `EXCEEDS_SECTION_CAP` flag | `HUMAN_ROUTE_REVIEW` |
| 6 | any other Tier C flag, including `EXCEEDS_PLAN_CAP` | `CARRY_TO_APPROVAL` |
| 7 | no flags | `READY_FOR_FORMALIZATION` |

`NextStepDecision.flags` always holds every flag passed in, including those that did not decide the step (for example a floor flag next to a section cap). `reason` names the deciding condition and the flag codes. Tier B and C flags never produce a block; the strongest step a flag can produce is a human decision.

---

## 4. Error Handling

| Scenario | Behavior |
|---|---|
| Empty text, no frontmatter, no closing delimiter, a BOM-only file | `parsed=False` with an `INVALID_METADATA` finding; no exception |
| Duplicate key, unquoted value with spaces, nested mapping, block scalar, anchor, tag | one `INVALID_METADATA` finding per line, with line and content |
| `non-str` input to any function | `TypeError` (a programming error, not content) |
| `LintFlag` built with a tier other than "A", "B" or "C" | `ValueError` at construction, so `next_step` never sees an unrecognized tier |
| Unknown `generator` value | `ESCALATE_IMMEDIATELY` (treated as unreadable) |
| Option that would lower a floor or the out-of-scope minimum | Ignored; the baseline applies |
| Frontmatter route disagrees with the tailoring matrix | one `INVALID_METADATA` finding; the plan is still linted |
| Route `not_applicable` | Metadata is checked; content checks are skipped |

---

## 5. Out of Scope

- Tier A detection, the content hash, the dependency graph, staleness and the approval gate (ADR-013).
- Orchestration, the three-step commands, runtime clients and the legacy `pmbok/` removal (ADR-034).
- Domain-specific rules for each plan (daughter ADRs 025 to 033); callers pass their raised minimums as options.
- Registering any result as an `Episode`; the caller does that, and no record type is added.

## 6. Interpretations to Confirm

These readings are not stated verbatim in ADR-012 and are decided here, to be tested and recorded in the test header and the implementation log, as LL-011 requires (LL-012 is the separate rule that each rule sits in one story's criteria):
1. **Flag codes** are stored without the "FLAG: " prefix and printed with it.
2. **Fail closed:** unparseable frontmatter returns an empty metadata mapping and body.
3. **Extra keys are allowed;** `cycle_id` (ADR-035, Proposed) is not required.
4. **Table agreement** (check 7 of §3.2) is a Tier B finding when a known plan's domains or legacy number differ from the §4.4 table.
5. **`governance_policy`** is required to match the route only for `full_plan` and `pmp_section`.
6. **Out-of-scope detection** is by the "out-of-scope" marker line plus bullets, with a baseline minimum of one item; the standalone minimum of two in some daughter ADRs is passed in as `min_out_of_scope_items`.
7. **`EXCEEDS_PLAN_CAP`** is carried to approval (an appendix recommendation), and only `EXCEEDS_SECTION_CAP` triggers the keep-or-graduate review.
8. **Equal to the floor or cap** is not a finding.
