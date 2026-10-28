---
name: plan-approval-gate
description: Pure decision logic of the per-plan approval gate (ADR-013, Epic 13): canonical content hash, technical-integrity flags and gate constraint, approval record, dependency graph, freshness and transitive staleness, lifecycle state and the formalization check, in agent_learning.pmbok.
---

# Plan approval gate (agent_learning.pmbok)

**Governing:** ADR-013 (with ADR-034 sections 4.2.1, 4.2.2 and 4.3.1), BRD-013, FDD-013, Epic 13. Contract files: `tests/test_plan_hash.py` (Story 13.1), `tests/test_plan_integrity.py` (13.2), `tests/test_plan_approval_record.py` (13.3), `tests/test_plan_graph.py` (13.4), `tests/test_plan_freshness.py` (13.5), `tests/test_plan_lifecycle.py` (13.6), `tests/test_plan_formalization.py` (13.7).

## What it is
Pure functions over plain data (standard library only, no I/O, no storage) that decide, for each of the nine subsidiary plans, whether an approval is still valid and whether the set is ready to formalize into the PMP. It sits beside `plan-lint` in `agent_learning.pmbok` and builds on its parser and flags. It records nothing and approves nothing: a human adjudicates through the `approve-subsidiary-plan` policy, which is only declared (`docs/policy-shapes/approve-subsidiary-plan.actions.json`) and not initialized in any store.

## Modules
- `hashing.py`: `compute_canonical_plan_hash`, `raw_change_hash`, `is_raw_hash`, `plan_hash`.
- `integrity.py`: `integrity_flags`, `gate_constraint_results`.
- `governance.py`: `PlanApprovalRecord`, `build_approval_metadata`, `approval_record`, `latest_approvals`, `effective_upstreams`, `topological_order`, `CyclicDependencyError`, `check_plan_freshness` (`Freshness`), `derive_plan_state` (`PlanState`), `check_formalization` (`FormalizationCheck`, `Blocker`).
- `standards.py` (extended): `VOLATILE_KEYS`, `PLACEHOLDER_TOKENS`, `PROVISIONAL_TOKENS`, `APPROVAL_ACTIONS`, `DISPOSITIONS`, `FEEDBACK_STATUSES`, `GATE_CRITERIA`, `DRAFT_ORDER`, `PLAN_DAG`.
- `lint.py` (extended): `validate_dependencies`.

## Load-bearing constraints
- **The hash ignores form, not meaning.** `compute_canonical_plan_hash` gives the same value for LF, CRLF and lone-CR line endings, a leading BOM, NFC and NFD text, and trailing spaces or tabs (a Markdown hard break of two trailing spaces is kept). It changes for any change to the body or to a static frontmatter value or key order. Keys in `VOLATILE_KEYS` (`last_modified`, `generated_at`, `governance_hash`, `approval_ref`) are removed before hashing. `plan_hash` falls back to `raw_change_hash` (prefix `raw:`) when the frontmatter does not parse; a `raw:` hash is never a valid recorded hash.
- **Total on text.** `plan_hash` does not raise on any `str`; `integrity_flags` does not raise on any `str` or `None` (`None` is a missing artifact). Any other argument type raises `TypeError`.
- **Tier A blocks approval.** `gate_constraint_results` returns `{"no_technical_integrity_block": False}` for `approve_plan` exactly when a Tier A flag exists (`GENERATION_FAILED`, `MISSING_ARTIFACT`, `INVALID_METADATA`, `STUB_GENERATOR`, `PLACEHOLDER_TOKEN`); `reject_plan` and `request_revision_before_decision` stay available. Tokens inside fenced code or HTML comments do not count.
- **The approval record is seven keys, no more.** `build_approval_metadata` returns the ADR-034 section 4.2.1 contract keys only, refuses any string over 256 characters (audit-data minimalism), and refuses a `raw:` hash. `latest_approvals` picks the record with the greatest `(sequence_number, created_at)` per plan and does not mutate its input.
- **The graph is the table.** A test compares `PLAN_DAG` with the `depends_on` of the frontmatter example in each of ADR-025 to ADR-033 and runs `validate_dependencies` over them, so drift between the ADRs and the graph fails. `effective_upstreams` resolves across a `not_applicable` omission; `topological_order` breaks ties by `DRAFT_ORDER`; a cycle raises `CyclicDependencyError` and a diamond is not a cycle.
- **Staleness is transitive.** Editing an upstream plan's hash makes every dependent approval stale, through `pmp_section` and `not_applicable` plans too (ADR-034 Tests 1, 2 and 6). The reason names the offending upstream.
- **A local edit outranks an adjudication.** `derive_plan_state` applies its precedence in a fixed order; an edit to an approved plan gives `REAPPROVAL_REQUIRED`, to a rejected or revision-requested plan `DRAFTED`. Accepted `approve_plan` on a matching hash needs a `freshness` argument or it raises `ValueError`.
- **Formalization lists every blocker.** `check_formalization` reports all blockers in `DRAFT_ORDER`, each with plan, route and reason; `ready` is true exactly when there are none.
- **Purity.** `hashing.py`, `integrity.py` and `governance.py` import the standard library and sibling modules only; a contract test reads the imports. Do not import storage, `tailoring` or the legacy top-level `pmbok/` here.

## Out of scope (see FDD-013)
Orchestration, the CLI, storing approvals in a `LearningStore`, initializing the `approve-subsidiary-plan` policy, and drafting plans (ADR-034 Phase 2).

## Call sites
- `agent_learning/pmbok/__init__.py` and `agent_learning/__init__.py` re-export the public names above.
- No orchestrator or CLI call site yet; `plan-lint` is the neighbouring component.
