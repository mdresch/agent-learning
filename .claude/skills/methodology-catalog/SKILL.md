---
name: methodology-catalog
description: The catalog of the 32 learning methodologies (agent_learning.methodology_catalog): one entry each, a class derived from the methodology's state, and an integrity check. Use before adding an example, sketch or catalog entry.
---

# Component Skill: Methodology Catalog (`agent_learning.methodology_catalog`)

## 1. Governing Architecture & Specifications
- **ADR:** [ADR-036](../../../docs/adr/ADR-036-learning-methodology-examples-ledger-and-review-triage-loop.md) §4.1 and §4.2, Invariants 1 to 3. Related: ADR-024 (methodology selection).
- **BRD:** [BRD-036](../../../docs/project-docs/Business-Requirements/BRD-036-learning-methodology-examples-ledger-and-review-triage-loop.md) BRU-036-01 and BRU-036-08.
- **FDD:** [FDD-036](../../../docs/project-docs/Functional-Design/FDD-036-learning-methodology-examples-ledger-and-review-triage-loop.md) §1 and §2.1.
- **Story:** [Story 36.1](../../../docs/user-stories/epic-36-learning-methodology-examples-ledger-and-review-triage-loop.md).
- **Contract tests:** `tests/test_methodology_catalog.py` (interpretations I1 to I3 in its header). Fixture: `tests/fixtures/methodology_catalog/ideation_states.json`.
- **Data:** `examples/methodologies/catalog.json`.

## 2. Load-Bearing Constraints
- **Exactly 32 entries**, ids 1 to 32 once each. A missing, duplicate or out-of-range id raises and is named.
- **Class follows state.** `implemented`, `example_only`, `partial`, `practiced` give `runnable`. A `candidate` with an ADR gives `proof_of_concept`. `blocked`, `excluded`, `declined`, `not_applicable` and a `candidate` with no ADR give `documented`. Current counts: 9 runnable, 10 proof_of_concept, 13 documented.
- **State is a canonical token** copied from the Ideation §2.1 row (not its free text). The test fixture holds the expected states; it is hand-transcribed, so update it in the same change as the Ideation table (LL-007).
- **A documented entry has a non-empty `reason` and `reopening_condition` and no `path`.** A runnable or proof_of_concept entry has a `path` under `examples/methodologies/` with no `..`.
- **Pure module.** No file I/O, no storage import. Path existence is checked against a set the caller passes as `existing_paths`; `None` skips it (the example directories are built by Stories 36.2 and 36.3, which pass the real set).
- **An example never changes a methodology's state** or a hypothesis status (ADR-036 Invariant 1), and nothing under `src/` imports from `examples/`.
- Moving an entry from `documented` to `proof_of_concept` requires its ADR to exist. Changing a state goes through ADR-024, not this catalog.

## 3. Call Sites
- Re-exported from `agent_learning/__init__.py`.
- Stories 36.2 and 36.3 add example directories and call `validate_catalog(..., existing_paths=...)`; Story 36.6 reads the catalog for the tailoring matrix.

## 4. Out of Scope
The example directories themselves (36.2, 36.3), the best-practice ledger (36.4), the review-triage loop (36.5), and generating the catalog state from the Ideation Document (ADR-036 §8).
