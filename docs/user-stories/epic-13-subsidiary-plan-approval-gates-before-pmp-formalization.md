# Epic 13: Subsidiary Plan Approval Gates Before PMP Formalization

**Source ADR:** [ADR-013](../adr/ADR-013-subsidiary-plan-approval-gates-before-pmp-formalization.md) — Accepted (2026-10-25)  
**Source BRD/FDD:** [BRD-013](../project-docs/Business-Requirements/BRD-013-subsidiary-plan-approval-gates-before-pmp-formalization.md) / [FDD-013](../project-docs/Functional-Design/FDD-013-subsidiary-plan-approval-gates-before-pmp-formalization.md)  
**Status:** Draft — stories derived from Accepted ADR-013, BRD-013 and FDD-013; awaiting `approve-user-stories`.  

Seven stories build the pure decision logic of the per-plan gate in `src/agent_learning/pmbok/`, on top of the Epic 12 parser and lint. Each rule sits in exactly one story's criteria (LL-012). Contract tests are `tests/test_plan_hash.py`, `tests/test_plan_integrity.py`, `tests/test_plan_approval_record.py`, `tests/test_plan_graph.py`, `tests/test_plan_freshness.py`, `tests/test_plan_lifecycle.py` and `tests/test_plan_formalization.py`. Fixtures that are real artifacts live committed under `tests/fixtures/pmbok/`; tests that read the real ADRs anchor their paths to the test file's location and look the file up inside the helper, with an assertion that names it if missing (LL-006, LL-023). A test that depends on a normative pattern runs the pattern first (LL-022).

The six normative scenarios of ADR-034 §6.1 map as follows: Test 1 and Test 2 to Story 13.5, Test 3 to Story 13.4, Test 4 to Story 13.6, Test 5 (grammar conformance) was delivered by Epic 12, Test 6 to Story 13.5.

---

## Story 13.1 — The Canonical Content Hash

**Status:** Draft  
**As** a governance reviewer,  
**I want** one hash per plan that does not change with line endings, a BOM, trailing spaces or volatile metadata, and does change with real content,  
**So that** an approval stays valid exactly as long as the approved content does.

### Acceptance Criteria:
- **$AC_0$ (Known Value):** `compute_canonical_plan_hash` of a fixed plan text equals the SHA-256 (64 lowercase hex characters) of the expected normalized text, computed independently in the test.
- **$AC_1$ (Invariance):** The hash is equal for the LF, CRLF and lone-CR forms of a text; with and without leading BOMs; for NFC and NFD forms of the same characters; with added or removed trailing spaces and tabs (except the Markdown hard break); with leading and trailing blank lines added; and when a volatile key (`last_modified`, `generated_at`, `governance_hash`, `approval_ref`), as a scalar or with list items, is added, changed or removed.
- **$AC_2$ (Sensitivity):** The hash differs when a body word changes, a static frontmatter value changes, a static key is added, static keys are reordered, or a line gains or loses exactly two trailing spaces after content (a hard break). A whitespace-only line of two spaces is the same as an empty line.
- **$AC_3$ (Raw Change Hash):** `raw_change_hash` starts `raw:` and changes with any byte change, including line endings. `plan_hash` returns the canonical hash for text that parses and the raw hash for text that does not. `is_raw_hash` tells them apart. `compute_canonical_plan_hash` of unparseable text raises `ValueError`.
- **$AC_4$ (Total on `str`):** No `str` makes `plan_hash` raise (including lone surrogates, empty text and text without frontmatter); a non-`str` raises `TypeError`; repeated calls are equal.
- **$AC_5$ (Real Plans):** The frontmatter example of ADR-025, with a body appended, gives the same hash in LF and CRLF form.

---

## Story 13.2 — Technical Integrity and the Gate Constraint

**Status:** Draft  
**As** a governance reviewer,  
**I want** the conditions that rule a plan out found mechanically and handed to the decision frame as a hard constraint,  
**So that** a stub, a placeholder or a failed generation can never be approved, while floors, caps and provisional tokens stay evidence.

### Acceptance Criteria:
- **$AC_0$ (Stub Generator):** A parsed plan whose `generator` is `stub` or `mock` gives one Tier A `STUB_GENERATOR`; `llm` and `human` give none.
- **$AC_1$ (Placeholders):** Each of `Stub content for Artifact`, `[Insert here]`, `[TBD]` and `[TODO]` in the visible text gives one Tier A `PLACEHOLDER_TOKEN` naming the token; a token inside fenced code or an HTML comment does not; several tokens give several findings in the order of `PLACEHOLDER_TOKENS`.
- **$AC_2$ (Process Failure):** A `generation_error` gives Tier A `GENERATION_FAILED`; `text=None` gives Tier A `MISSING_ARTIFACT` and nothing else about the text.
- **$AC_3$ (Unparseable Frontmatter):** Frontmatter that breaks the grammar gives each of its Epic 12 findings again as Tier A `INVALID_METADATA` with the same line and evidence; the stub check is skipped because the generator cannot be read.
- **$AC_4$ (Flags, Not Blocks):** An unbracketed `TBD` or `TODO` word gives a Tier C `PROVISIONAL_TOKEN`, not a Tier A flag; a plan below its floor or above its cap gives no integrity finding of any tier.
- **$AC_5$ (Gate Constraint):** `gate_constraint_results` is false for `approve_plan` exactly when any flag is Tier A and true for `reject_plan` and `request_revision_before_decision` always; Tier B and C flags never change it.
- **$AC_6$ (Feeds the Next Step):** Passing the Tier A findings of a stub plan to the Epic 12 `next_step` gives `ESCALATE_IMMEDIATELY`; a clean plan gives no integrity finding.
- **$AC_7$ (Total and Ordered):** Findings come in the order of FDD-013 §3.2; no `str` or `None` makes `integrity_flags` raise; the result is deterministic.

---

## Story 13.3 — The Approval Record and the Policy Shape

**Status:** Draft  
**As** a maintainer,  
**I want** one definition of what an approval leaves in the store, shared by the writer and the reader, and the policy's actions declared,  
**So that** the gate that produces approvals and the check that consumes them cannot drift apart.

### Acceptance Criteria:
- **$AC_0$ (Producer):** `build_approval_metadata` returns exactly the seven ADR-034 §4.2.1 keys and no others, with the values given.
- **$AC_1$ (Round Trip):** `approval_record` reads what `build_approval_metadata` wrote, for each of the three actions and each disposition, without loss; extra keys in the stored metadata are ignored.
- **$AC_2$ (Validation):** Each of these raises `ValueError` naming the key: a plan id that is not kebab-case; a hash that is not 64 lowercase hex, including a `raw:` hash, in `canonical_content_hash` or in any `upstream_hashes` value; an unknown action, disposition or feedback status; a negative, boolean or non-integer `sequence_number`; an empty `run_id`; a missing contract key.
- **$AC_3$ (Latest Wins):** `latest_approvals` keeps, per plan, the record with the highest `(sequence_number, created_at)`, whatever the input order, and does not change its input.
- **$AC_4$ (Audit Minimalism):** Any string above 256 characters is refused in the producer and in the reader, so a plan body cannot be embedded.
- **$AC_5$ (Policy Shape):** `docs/policy-shapes/approve-subsidiary-plan.actions.json` holds exactly the three actions of `APPROVAL_ACTIONS`, in the structure of the other `approve-*` shapes; `GATE_CRITERIA` holds the four ADR-013 §4.2 criteria with weights that sum to 1.0.

---

## Story 13.4 — The Dependency Graph

**Status:** Draft  
**As** a maintainer,  
**I want** one authoritative dependency graph that every plan's `depends_on` must agree with,  
**So that** staleness follows a single, checkable structure.

### Acceptance Criteria:
- **$AC_0$ (Authoritative Graph):** `PLAN_DAG` has the nine plans and the edges of FDD-013 §2.1. For each of ADR-025 to ADR-033, the `depends_on` of the frontmatter example (first fenced `yaml` block that starts with `---`, parsed by the Epic 12 parser) equals the graph's edges for that plan, so drift fails a test.
- **$AC_1$ (Order):** `topological_order(PLAN_DAG)` puts every plan after its dependencies, breaks ties by `DRAFT_ORDER` then by name, and `DRAFT_ORDER` is itself a valid order of the graph.
- **$AC_2$ (Effective Upstreams):** `effective_upstreams` returns the direct dependencies; replaces a `not_applicable` one by its own effective upstreams, recursively through several omitted plans; returns a sorted list without duplicates; treats a missing route as `full_plan`.
- **$AC_3$ (Cycles and Diamonds):** A cyclic graph (A → B → A, and a longer ring) raises `CyclicDependencyError` from both `effective_upstreams` and `topological_order`; a diamond (a plan depending on two plans that depend on one root) evaluates without error; an edge to a plan that is not a key raises `ValueError` in `topological_order`.
- **$AC_4$ (`depends_on` Agrees):** `validate_dependencies` gives one Tier B `INVALID_METADATA` naming `depends_on` for a known plan whose list differs as a set from the graph (extra, missing, or wrong plan), none when it agrees in any order, and none for an unknown plan or a missing or malformed `depends_on`.
- **$AC_5$ (Real Plans):** `validate_dependencies` gives no finding for the frontmatter example of each of ADR-025 to ADR-033.

---

## Story 13.5 — Freshness and Transitive Staleness

**Status:** Draft  
**As** a governance reviewer,  
**I want** to know whether an approval still holds, and which plan broke it,  
**So that** a change stales only the branch that depends on it and the answer points at its cause.

### Acceptance Criteria:
- **$AC_0$ (Basic Outcomes):** `check_plan_freshness` returns `(True, "NOT_APPLICABLE", None)` for an omitted plan; `(True, "SECTION_FRESH", None)` for a present, non-stub section whose ancestors are fresh; `(True, "APPROVED_AND_FRESH", None)` for an accepted approval whose hash and recorded upstream hashes match; and a fixed code and offending plan for each failure below.
- **$AC_1$ (Approval Problems):** No record gives `NO_APPROVAL_RECORD`; a `reject_plan` or `request_revision_before_decision` record gives `NOT_APPROVED_<action_id>`; an `approve_plan` record whose disposition or feedback status is not `accepted` gives `NOT_APPROVED_UNACCEPTED`.
- **$AC_2$ (Content):** A current hash that differs from the approved one gives `REAPPROVAL_REQUIRED_CONTENT_MODIFIED`; a missing or `raw:` current hash gives `INVALID_METADATA_UNPARSEABLE`; a recorded upstream hash that differs from the upstream's current hash, or is missing, gives `STALE_DEPENDENCY_<upstream>`.
- **$AC_3$ (Mixed-Route Staleness, ADR-034 Test 1):** Scope (`full_plan`) → Schedule (`pmp_section`) → Cost (`full_plan`): changing Scope's current hash makes Cost `(False, "TRANSITIVE_STALE_FROM_scope-management", "scope-management")` through Schedule, even though Schedule's own content is unchanged.
- **$AC_4$ (Omission Bypass, ADR-034 Test 2):** Scope (`full_plan`) → Schedule (`not_applicable`) → Cost (`full_plan`): changing Scope's current hash makes Cost stale through the bypass; editing nothing but Schedule's omission leaves Cost fresh.
- **$AC_5$ (Bounded Scope):** On `PLAN_DAG`, changing a support plan that nothing core depends on (for example Quality or Communications) leaves Scope, Schedule and Cost fresh, and changing one orthogonal plan does not stale another.
- **$AC_6$ (Technical Integrity Upstream, ADR-034 Test 6):** An upstream section with a stub or `raw:` hash gives `INVALID_OR_STUB_SECTION` and makes every dependent approval stale (`TRANSITIVE_STALE_FROM_<section>`); an upstream full plan with a `raw:` hash makes its dependents stale.
- **$AC_7$ (Pending versus Stale):** A dependent whose upstream has no accepted approval gives `PENDING_UPSTREAM_<offending>`; one whose upstream was modified gives `TRANSITIVE_STALE_FROM_<offending>`, naming the plan at the root of the chain.
- **$AC_8$ (Pure and Safe):** A cycle raises `CyclicDependencyError`; a diamond is not read as a cycle; the inputs are not changed; repeated calls are equal.

---

## Story 13.6 — The Lifecycle State

**Status:** Draft  
**As** a maintainer,  
**I want** each plan's governance state computed from what is on disk and in the store,  
**So that** the state is never stored, never ambiguous, and always agrees with the hash.

### Acceptance Criteria:
- **$AC_0$ (Precedence):** `derive_plan_state` applies FDD-013 §3.6 in order: a missing file is `NOT_STARTED`; a missing or `raw:` hash is `INVALID_METADATA`; an in-flight review for the current hash is `UNDER_REVIEW`; a local edit outranks a past adjudication; then the verdict; then `DRAFTED`.
- **$AC_1$ (Local Edit, ADR-034 Test 4):** Editing an approved plan (its hash differs from the approved one) gives `REAPPROVAL_REQUIRED`; editing a rejected or revision-requested plan gives `DRAFTED`; submitting the edited plan for review gives `UNDER_REVIEW`.
- **$AC_2$ (Verdicts That Match the Hash):** An accepted `reject_plan` gives `REJECTED`; an accepted `request_revision_before_decision` gives `REVISION_REQUESTED`; an accepted `approve_plan` gives `APPROVED` when the freshness is fresh, `PENDING_UPSTREAM` when its reason starts `PENDING_UPSTREAM`, and `STALE_DEPENDENCY` for any other reason.
- **$AC_3$ (Not a Verdict):** A record whose disposition or feedback status is not `accepted` leaves a matching plan `DRAFTED`; a plan with no record and no review is `DRAFTED`.
- **$AC_4$ (Needs Freshness):** An accepted `approve_plan` that matches the current hash and has no `freshness` raises `ValueError`; other cases do not need it.
- **$AC_5$ (Total):** Every combination of {file present or missing} × {parseable, raw or missing hash} × {in-flight review: none, matching, other} × {latest record: none, or one of the three actions with matching or different hash and accepted or not accepted} × {freshness: fresh, pending, stale} returns exactly one `PlanState`, and each of the ten states is reached by some combination.

---

## Story 13.7 — Formalization and the Package Contract

**Status:** Draft  
**As** a maintainer,  
**I want** one answer to "may the PMP be formalized, and if not which plans stand in the way",  
**So that** a stub, a stale approval or an unrationalized omission can never reach a baseline, and a refusal points at a plan.

### Acceptance Criteria:
- **$AC_0$ (Ready):** With every `full_plan` `APPROVED`, every `pmp_section` ok and every `not_applicable` rationalized, `check_formalization` returns `ready=True` and no blockers.
- **$AC_1$ (Route Conditions):** A `full_plan` in any state but `APPROVED` is the blocker `PLAN_<STATE>`; a missing state is `NO_STATE`; a `pmp_section` that is missing or a stub is `SECTION_MISSING_OR_STUB`; a `not_applicable` plan with no recorded rationale is `NO_OMISSION_RATIONALE`.
- **$AC_2$ (Routes):** A plan with no route is `NO_ROUTE`; a route outside the closed list is `INVALID_ROUTE`; routes for plans outside the nine are ignored.
- **$AC_3$ (Attribution):** Blockers come in `DRAFT_ORDER`; each names its plan, route and reason; `ready` is true exactly when there are none; several blockers are all reported.
- **$AC_4$ (End to End):** A scenario built only from the functions of Stories 13.1 to 13.6 (hash, approval metadata, record, freshness, state, formalization) over a three-plan route set is ready after approval; becomes not ready with the stale plan named after the upstream plan is edited; and is ready again after the dependent is re-approved.
- **$AC_5$ (Purity and Exports):** `hashing.py`, `integrity.py` and `governance.py` import only the standard library and their siblings (and `lint.py` imports `tailoring`); none imports storage, the legacy `pmbok/` or a third-party package; the result types are frozen dataclasses or named tuples; no record type is added to the store module; `pyproject.toml` gains no dependency; the package and the root export every public name of the epic.

---

## Out of Scope per BRD-013/FDD-013

- The `agent-learn pmbok` commands, the runtime harness, every store read or write and the batch dashboard (ADR-034).
- `approve-pmp` and the attribution of integration-level defects (BRU-013-09 is a convention).
- Scoring the gate criteria for a real plan; a decision-frame example for `approve-subsidiary-plan`.
- Adaptation mode, the registry port, the test port and the legacy removal (ADR-034).
- Cycle identity (ADR-035).
