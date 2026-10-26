---
name: methodology-catalog
description: The catalog of the 32 learning methodologies (agent_learning.methodology_catalog) and its runnable examples under examples/methodologies/: one entry each, a class derived from the methodology's state, an integrity check, and the labeling contract every example must follow. Use before adding an example, sketch or catalog entry.
---

# Component Skill: Methodology Catalog (`agent_learning.methodology_catalog`)

## 1. Governing Architecture & Specifications
- **ADR:** [ADR-036](../../../docs/adr/ADR-036-learning-methodology-examples-ledger-and-review-triage-loop.md) §4.1 and §4.2, Invariants 1 to 3. Related: ADR-024 (methodology selection).
- **BRD:** [BRD-036](../../../docs/project-docs/Business-Requirements/BRD-036-learning-methodology-examples-ledger-and-review-triage-loop.md) BRU-036-01 and BRU-036-08.
- **FDD:** [FDD-036](../../../docs/project-docs/Functional-Design/FDD-036-learning-methodology-examples-ledger-and-review-triage-loop.md) §1 and §2.1.
- **Story:** [Story 36.1](../../../docs/user-stories/epic-36-learning-methodology-examples-ledger-and-review-triage-loop.md).
- **Contract tests:** `tests/test_methodology_catalog.py` (Story 36.1) and `tests/test_methodology_examples.py` (Story 36.2); interpretations in each header. Fixture: `tests/fixtures/methodology_catalog/ideation_states.json`.
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
- Story 36.3 adds proof-of-concept directories and calls `validate_catalog(..., existing_paths=...)`; Story 36.6 reads the catalog for the tailoring matrix.

## 4. Out of Scope
The proof-of-concept sketches (36.3), the best-practice ledger (36.4), the review-triage loop (36.5), and generating the catalog state from the Ideation Document (ADR-036 §8).

## 5. Runnable Examples (Story 36.2)
The nine `runnable` entries (#2, #3, #4, #5, #6, #12, #19, #20, #21) each have `examples/methodologies/<NN>-<slug>/` with `README.md` and `example.py`.

- **Labeling contract (ADR-036 §4.2).** The script's docstring has these lines: `STATUS: runnable`, `CODE: sdk`, `DATA: SYNTHETIC`, `IDEATION ROW: #N ...`, `ADR: ...`, `HYPOTHESIS: ...`, and `NOT EVIDENCE: this run does not validate or invalidate the methodology`. The script prints a banner repeating `SYNTHETIC` and `NOT EVIDENCE`. The README has `Falsification` and `Real data needed` headings and says the data is SYNTHETIC. Where no hypothesis is registered, the README says the criterion is proposed there.
- **Runs offline and writes nothing.** Each script uses `InMemoryStore` or no store, imports no network or cloud client, never names `LocalFileStore`, `CosmosStore` or `get_default_store`, and creates no file in its working directory. It exits 0 and may assert its own sanity (for example that a learned probability moved), which checks the library, not the methodology.
- **Episodes must be complete to train.** `Episode.is_full` needs `intent_summary`, an action, `expected_outcome`, `execution_status` and `result_summary`; otherwise a learner uses zero episodes. The older `examples/quickstart.py` and `examples/next_best_action.py` omit these fields and train on nothing, and `next_best_action.py` needs PyYAML, which is not declared; the new examples do not use them.
- **No state change.** Running an example never edits the catalog or any methodology's state (ADR-036 Invariant 1). Examples are not imported by `src/`.
- **Adding a new example:** add the directory and files, set the entry's class and `path` in the catalog, add the id to `RUNNABLE` in `tests/test_methodology_examples.py`, and keep the README's falsification criterion in step with the Ideation hypothesis (LL-007).
