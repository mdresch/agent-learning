# FDD-013: Subsidiary Plan Approval Gates Before PMP Formalization

**Source ADR:** [ADR-013](../../adr/ADR-013-subsidiary-plan-approval-gates-before-pmp-formalization.md) — Accepted (2026-10-25)  
**Source BRD:** [BRD-013](../Business-Requirements/BRD-013-subsidiary-plan-approval-gates-before-pmp-formalization.md)  
**Status:** Draft — functional design derived from Accepted ADR-013 and BRD-013; awaiting `approve-fdd`.  

ADR-034 §4.2.2 gives the staleness and lifecycle logic only as an "illustrative reference sketch ... to be formally specified in a follow-on ADR". This FDD is that specification for the pure part. Where it departs from the sketch, section 6 says so.

---

## 1. Architecture & Component Placement

1. **Package placement:** `src/agent_learning/pmbok/`, the pure package of Epic 12. New modules: `hashing.py`, `integrity.py` and `governance.py` (the name ADR-034 §4.2.2 gives). `standards.py` gains the constants of section 2.1, and `lint.py` gains `validate_dependencies`. `agent_learning.pmbok.governance` is a different module from the Stage 16 pipeline `agent_learning.governance`; the dotted names do not clash.
2. **Purity boundary:** standard library only (`hashlib`, `unicodedata`, `re`, `dataclasses`, `enum`, `typing`). No file I/O, no `LearningStore`, no `Episode`, no network. The runtime (ADR-034) reads files and episodes and passes plain data in (ADR-013 Invariant 8, §4.10).
3. **Reuse, not duplication:** the Epic 12 parser reads frontmatter (including for hashing); `LintFlag` carries the integrity findings; `PLAN_STANDARDS` and the closed lists stay as they are. Nothing from Epic 12 is changed.
4. **Not here:** the `agent-learn pmbok` commands, store queries, the batch dashboard, `approve-pmp`, adaptation mode, the registry port and the legacy removal (ADR-034).

---

## 2. Data Contract & Domain Model

```python
@dataclass(frozen=True)
class PlanApprovalRecord:                  # governance.py; the reader's view of one gate Episode
    plan_id: str
    canonical_content_hash: str            # 64 lowercase hex; never "raw:"
    action_id: str                         # one of APPROVAL_ACTIONS (the Episode's action_id)
    decision_disposition: str              # "accepted" | "rejected" | "modify"
    feedback_status: str                   # "accepted" | "rejected"
    upstream_hashes: Mapping[str, str]     # effective upstream plan id -> canonical hash at approval
    sequence_number: int
    created_at: str

class CyclicDependencyError(Exception): ...

class Freshness(NamedTuple):
    fresh: bool
    reason: str                            # a code of section 3.5
    offending: str | None                  # the plan that caused a False result, else None

class PlanState(str, Enum):
    NOT_STARTED = "not_started"; DRAFTED = "drafted"; UNDER_REVIEW = "under_review"
    APPROVED = "approved"; REVISION_REQUESTED = "revision_requested"; REJECTED = "rejected"
    STALE_DEPENDENCY = "stale_dependency"; PENDING_UPSTREAM = "pending_upstream"
    REAPPROVAL_REQUIRED = "reapproval_required"
    INVALID_METADATA = "invalid_metadata"  # see interpretation 4

@dataclass(frozen=True)
class Blocker:
    plan_id: str
    route: str
    reason: str

@dataclass(frozen=True)
class FormalizationCheck:
    ready: bool
    blockers: tuple[Blocker, ...]          # in DRAFT_ORDER; empty exactly when ready
```

### 2.1 Constants (`standards.py`)
- `VOLATILE_KEYS = ("last_modified", "generated_at", "governance_hash", "approval_ref")`
- `PLACEHOLDER_TOKENS = ("Stub content for Artifact", "[Insert here]", "[TBD]", "[TODO]")`; `PROVISIONAL_TOKENS = ("TBD", "TODO")`
- `APPROVAL_ACTIONS = ("approve_plan", "reject_plan", "request_revision_before_decision")`, `DISPOSITIONS = ("accepted", "rejected", "modify")`, `FEEDBACK_STATUSES = ("accepted", "rejected")`
- `GATE_CRITERIA = {"charter_alignment": 0.30, "substantive_content": 0.30, "internal_completeness": 0.25, "consistency_with_dependent_plans": 0.15}` (ADR-013 §4.2 weights, fixed here; they sum to 1.0)
- `DRAFT_ORDER = ("scope-management", "schedule-management", "cost-management", "quality-management", "resource-management", "communications-management", "risk-management", "procurement-management", "stakeholder-engagement")` (ADR-013 §4.1: core baselines, then Quality, Resource, Communications, then Risk, Procurement, Stakeholder)
- `PLAN_DAG`, the authoritative dependency graph (ADR-034 ERR-034-06), taken from the `depends_on` of the nine plan ADRs' frontmatter examples:

| plan | depends on |
|---|---|
| scope-management | (none) |
| schedule-management | scope-management |
| cost-management | scope-management, schedule-management |
| quality-management | scope-management |
| resource-management | scope-management, schedule-management |
| communications-management | scope-management |
| risk-management | scope-management, schedule-management, cost-management |
| procurement-management | scope-management, cost-management |
| stakeholder-engagement | scope-management |

---

## 3. Behavior

### 3.1 Canonical hash (`hashing.py`, BRU-013-01)
`compute_canonical_plan_hash(text) -> str` returns 64 lowercase hex characters, in this order:
1. Strip leading BOMs (`﻿`), then NFC-normalize.
2. Normalize `\r\n` and lone `\r` to `\n`.
3. The frontmatter must parse (Epic 12 `parse_frontmatter`); otherwise `ValueError`. Remove from the frontmatter block the lines of each key in `VOLATILE_KEYS` (the key line and the `  - ` lines that follow it). All other lines, including comments and key order, stay.
4. Strip trailing whitespace on every line. Exactly two trailing spaces are kept only on a line that has other content before them (a Markdown hard break); a whitespace-only line becomes empty.
5. Strip leading and trailing blank lines of the whole text.
6. SHA-256 of the UTF-8 encoding (`errors="surrogatepass"`, so no text raises).

`raw_change_hash(text) -> str` is `"raw:"` plus the SHA-256 of the exact UTF-8 text, for change detection only. `plan_hash(text)` returns the canonical hash when the frontmatter parses and the raw hash when it does not. `is_raw_hash(h)` is true for a value starting `raw:`. A non-`str` argument raises `TypeError`.

### 3.2 Technical integrity (`integrity.py`, BRU-013-02)
`integrity_flags(text, *, generation_error=None) -> list[LintFlag]`, in this order:
1. `generation_error` (a non-empty string) gives Tier A `GENERATION_FAILED`.
2. `text is None` (the artifact file is missing) gives Tier A `MISSING_ARTIFACT` and returns.
3. If the frontmatter does not parse, each grammar finding is returned again as Tier A `INVALID_METADATA` (same message, line and evidence): at the gate the grammar failure is the fourth hard block (ADR-012 §4.2.1 rule 8).
4. If it parses and `generator` is `stub` or `mock`: Tier A `STUB_GENERATOR`.
5. For each token of `PLACEHOLDER_TOKENS` present in the visible text (fenced code and HTML comments removed, as in the word count): one Tier A `PLACEHOLDER_TOKEN`, evidence the token.
6. For each unbracketed `TBD` or `TODO` word in the visible text (not inside brackets): one Tier C `PROVISIONAL_TOKEN`.

`gate_constraint_results(flags) -> dict` returns, for each of the three actions, `{"no_technical_integrity_block": ok}`, where `ok` is false for `approve_plan` exactly when any flag is Tier A, and true for the other two actions. This is the shape a `DecisionFrame` takes in `constraint_results`; an action with a false constraint is ruled out. Floors, caps, provisional tokens and Tier B/C flags never change it.

### 3.3 Approval record and policy shape (`governance.py`, BRU-013-03)
- `build_approval_metadata(*, plan_id, canonical_content_hash, upstream_hashes, decision_disposition, feedback_status, run_id, sequence_number) -> dict` returns exactly the ADR-034 §4.2.1 keys: `plan_id`, `canonical_content_hash`, `upstream_hashes`, `decision_disposition`, `feedback_status`, `run_id`, `sequence_number`.
- `approval_record(action_id, metadata, created_at) -> PlanApprovalRecord` reads them back. Both validate: `plan_id` is kebab-case; every hash is 64 lowercase hex (a `raw:` hash is refused); `action_id` is in `APPROVAL_ACTIONS`; the disposition and feedback status are in their closed lists; `sequence_number` is an int (not a bool) of at least 0; `run_id` is a non-empty string; every string is at most 256 characters; `upstream_hashes` is a mapping of plan id to hash. A violation raises `ValueError` naming the key; the reader ignores extra keys, the producer never writes any.
- `latest_approvals(records) -> dict[str, PlanApprovalRecord]` keeps, per plan, the record with the highest `(sequence_number, created_at)`.
- `docs/policy-shapes/approve-subsidiary-plan.actions.json` declares the three actions (idle, no episodes). A test keeps its ids equal to `APPROVAL_ACTIONS`.

### 3.4 Graph (`governance.py`, BRU-013-04)
- `effective_upstreams(plan_id, dag, routes, active_stack=None) -> list[str]` follows the ADR-034 sketch: a `not_applicable` upstream is replaced by its own effective upstreams, recursively; the result is sorted and without duplicates; a missing route means `full_plan`; a cycle on the active path raises `CyclicDependencyError`.
- `topological_order(dag) -> tuple[str, ...]`: dependencies first, ties broken by position in `DRAFT_ORDER`, then by name; a cycle raises `CyclicDependencyError`; an edge to a plan that is not a key of `dag` raises `ValueError`.
- `validate_dependencies(metadata, dag=PLAN_DAG) -> list[LintFlag]` (`lint.py`): for a plan that is a key of `dag`, a `depends_on` that differs as a set from `dag[plan_id]` is one Tier B `INVALID_METADATA` naming `depends_on` and the expected list. Other plans, and a missing or malformed `depends_on` (reported by `validate_metadata`), give nothing.

### 3.5 Freshness (`governance.py`, BRU-013-05)
`check_plan_freshness(plan_id, dag, routes, current_hashes, is_non_stub, approvals, active_stack=None) -> Freshness`, following the ADR-034 sketch, first match wins:
1. Route `not_applicable`: `(True, "NOT_APPLICABLE", None)`.
2. Route `pmp_section`: a missing hash, a stub, or a `raw:` hash gives `(False, "INVALID_OR_STUB_SECTION", plan_id)`; otherwise every effective upstream must be fresh (its failure is returned as is), then `(True, "SECTION_FRESH", None)`.
3. Route `full_plan`:
   - no approval record: `NO_APPROVAL_RECORD`;
   - `action_id` is not `approve_plan`: `NOT_APPROVED_<action_id>`; the action is `approve_plan` but the disposition or feedback status is not `accepted`: `NOT_APPROVED_UNACCEPTED`;
   - current hash missing or `raw:`: `INVALID_METADATA_UNPARSEABLE`;
   - recorded hash differs from the current one: `REAPPROVAL_REQUIRED_CONTENT_MODIFIED`.
4. For each effective upstream: a recorded upstream hash that differs from the current hash gives `STALE_DEPENDENCY_<upstream>`; otherwise the upstream's own freshness is checked, and a failure becomes `PENDING_UPSTREAM_<offending>` when its reason starts `NO_APPROVAL` or `NOT_APPROVED`, and `TRANSITIVE_STALE_FROM_<offending>` otherwise, where `<offending>` is the plan that caused the failure (interpretation 2).
5. Otherwise `(True, "APPROVED_AND_FRESH", None)`.

The `active_stack` is removed on every return path so a diamond is not read as a cycle; a cycle raises `CyclicDependencyError`. The graph has nine nodes, so no memoization is needed.

### 3.6 Lifecycle state (`governance.py`, BRU-013-06)
`derive_plan_state(*, exists, current_hash, in_flight_hash, latest, freshness) -> PlanState`, first match wins:
1. `exists` is false: `NOT_STARTED`.
2. `current_hash` is missing or `raw:`: `INVALID_METADATA`.
3. `in_flight_hash == current_hash`: `UNDER_REVIEW`.
4. `latest` exists and its hash differs from `current_hash`: `REAPPROVAL_REQUIRED` if `latest.action_id` is `approve_plan`, else `DRAFTED`.
5. `latest` exists and its hash matches. A record whose disposition or feedback status is not `accepted` is not a verdict: `DRAFTED`. Otherwise by action: `reject_plan` gives `REJECTED`; `request_revision_before_decision` gives `REVISION_REQUESTED`; `approve_plan` uses `freshness` (required, else `ValueError`): fresh gives `APPROVED`; a reason starting `PENDING_UPSTREAM` gives `PENDING_UPSTREAM`; any other reason gives `STALE_DEPENDENCY`.
6. No `latest`: `DRAFTED`.

### 3.7 Formalization precondition (`governance.py`, BRU-013-07)
`check_formalization(routes, states, *, section_ok, rationale_recorded) -> FormalizationCheck`. For each plan of `DRAFT_ORDER`, in that order:
- no route, or a route outside the closed list: blocker `NO_ROUTE` or `INVALID_ROUTE`;
- `full_plan`: blocker `PLAN_<STATE>` (for example `PLAN_STALE_DEPENDENCY`) unless its state is `APPROVED`; a missing state is `NO_STATE`;
- `pmp_section`: blocker `SECTION_MISSING_OR_STUB` unless `section_ok[plan]` is true;
- `not_applicable`: blocker `NO_OMISSION_RATIONALE` unless `rationale_recorded[plan]` is true.
`ready` is true exactly when there is no blocker. Routes for plans outside `DRAFT_ORDER` are ignored.

---

## 4. Error Handling

| Scenario | Behavior |
|---|---|
| Text that cannot be parsed, given to `plan_hash` | The raw change hash; no exception |
| Text that cannot be parsed, given to `compute_canonical_plan_hash` | `ValueError` |
| Non-`str` text | `TypeError` |
| `integrity_flags` on missing, stub or malformed text | Findings; no exception |
| An approval record with an unknown action, a `raw:` hash, a bad enumeration value or an over-long string | `ValueError` naming the key |
| A cycle in a graph | `CyclicDependencyError` |
| A `derive_plan_state` call that needs `freshness` and has none | `ValueError` |
| A diamond graph | Evaluated without error |
| A plan missing from `routes` in the freshness check | Treated as `full_plan` (the ADR-034 sketch); in `check_formalization` it is the blocker `NO_ROUTE` |

---

## 5. Out of Scope

- The commands, the runtime harness and every store read or write (ADR-034); the batch dashboard.
- `approve-pmp` and the attribution of integration-level defects (BRU-013-09 is a convention).
- Scoring the four gate criteria for a real plan; a decision-frame example for `approve-subsidiary-plan` (it would be invented evidence).
- Adaptation mode, the registry port, the test port and the legacy removal (ADR-034).
- Cycle identity (ADR-035).

## 6. Interpretations to Confirm

These readings are not stated verbatim in ADR-013 or are decided against ADR-034's sketch. They are to be tested and recorded in the test headers and the implementation log (LL-011), and each rule sits in one story (LL-012):
1. **The graph is a constant.** ADR-013 §4.1 gives a drafting order and no edge list; ADR-034 ERR-034-06 makes the global graph authoritative. `PLAN_DAG` takes its edges from the `depends_on` of the nine plan ADRs. ADR-030 and ADR-033 are held for amendment; if their edges change, the constant and a conformance test change with them.
2. **Reason codes name the plan that caused the problem.** ADR-034 Test 1 expects `TRANSITIVE_STALE_FROM_scope-management` for Scope → Schedule (section) → Cost; the sketch's code would name the immediate upstream (`schedule-management`) and return Scope only as the second value. This FDD follows the test: the code names the offending plan.
3. **The action id is `request_revision_before_decision`.** The sketch comments say `request_revision`; the policy shapes and ADR-013 §4.2 use the longer id.
4. **`INVALID_METADATA` is a tenth lifecycle state.** ADR-034's precedence step 2 gives it as a state, but ADR-013 §4.6 lists nine.
5. **Tier A codes** are `GENERATION_FAILED`, `MISSING_ARTIFACT`, `INVALID_METADATA` (promoted at the gate), `STUB_GENERATOR` and `PLACEHOLDER_TOKEN`; an unbracketed `TBD` or `TODO` is a Tier C `PROVISIONAL_TOKEN`. ADR-012 and ADR-013 name the conditions, not the codes.
6. **Placeholders are searched in the visible text** (fences and comments removed), so a plan that quotes `[TBD]` as an example in a code block is not ruled out.
7. **A change to an upstream plan that is invalid or `raw:`** makes the dependent plan stale (`STALE_DEPENDENCY`), not pending.
8. **A record that is not `accepted`/`accepted` is not a verdict.** A `modify` disposition or a rejected recommendation leaves the plan `DRAFTED` and freshness answers `NOT_APPROVED_UNACCEPTED`.
9. **Whitespace and blank lines.** The hard-break exception applies only to a line with content before the two spaces, and only outer blank lines (not outer spaces) are stripped; the ADR sketch's `strip()` and its `endswith("  ")` test differ on those edges.
10. **Metadata limits.** Every string in an approval record is at most 256 characters, and the producer writes only the ADR-034 keys.
11. **The `approve-subsidiary-plan` actions shape is declared here.** ADR-034 ERR-034-02 assigns policy-shape creation to the daughter-ADR milestone; ADR-013 owns the policy, so the idle shape is declared with this epic.
12. **Epic numbering.** ADR-034 §6.1 and §8.1 call its own implementation "Epic 12". With the convention that an epic carries its ADR's number, Epic 12 is ADR-012's and ADR-034's is Epic 34. An errata row in ADR-034 records this.
