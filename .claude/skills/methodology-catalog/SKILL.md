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
- The example and sketch tests check that every catalog path exists on disk (`tests/test_methodology_examples.py`, `tests/test_methodology_sketches.py`); `validate_catalog(..., existing_paths=...)` is available to callers that pass the set of existing paths. The tailoring matrix (section 9) reads the catalog ids.

## 4. Out of Scope
The review-triage loop (36.5) and generating the catalog state from the Ideation Document (ADR-036 §8).

## 5. Runnable Examples (Story 36.2)
The nine `runnable` entries (#2, #3, #4, #5, #6, #12, #19, #20, #21) each have `examples/methodologies/<NN>-<slug>/` with `README.md` and `example.py`.

- **Labeling contract (ADR-036 §4.2).** The script's docstring has these lines: `STATUS: runnable`, `CODE: sdk`, `DATA: SYNTHETIC`, `IDEATION ROW: #N ...`, `ADR: ...`, `HYPOTHESIS: ...`, and `NOT EVIDENCE: this run does not validate or invalidate the methodology`. The script prints a banner repeating `SYNTHETIC` and `NOT EVIDENCE`. The README has `Falsification` and `Real data needed` headings and says the data is SYNTHETIC. Where no hypothesis is registered, the README says the criterion is proposed there.
- **Runs offline and writes nothing.** Each script uses `InMemoryStore` or no store, imports no network or cloud client, never names `LocalFileStore`, `CosmosStore` or `get_default_store`, and creates no file in its working directory. It exits 0 and may assert its own sanity (for example that a learned probability moved), which checks the library, not the methodology.
- **Episodes must be complete to train.** `Episode.is_full` needs `intent_summary`, an action, `expected_outcome`, `execution_status` and `result_summary`; otherwise a learner uses zero episodes. The older `examples/quickstart.py` and `examples/next_best_action.py` omit these fields and train on nothing, and `next_best_action.py` needs PyYAML, which is not declared; the new examples do not use them.
- **No state change.** Running an example never edits the catalog or any methodology's state (ADR-036 Invariant 1). Examples are not imported by `src/`.
- **Adding a new example:** add the directory and files, set the entry's class and `path` in the catalog, add the id to `RUNNABLE` in `tests/test_methodology_examples.py`, and keep the README's falsification criterion in step with the Ideation hypothesis (LL-007).

## 6. Proof-of-Concept Sketches (Story 36.3)
The ten `proof_of_concept` entries (#8, #9, #10, #11, #13, #14, #15, #17, #22, #23) each have `examples/methodologies/<NN>-<slug>/` with `README.md` and `sketch.py`.

- **Labeling contract.** Same lines as section 5, but `STATUS: proof_of_concept` and `CODE: sketch`, plus a note that the sketch is plain stdlib Python of the ADR formulas, not SDK code (ADR-036 section 4.2). The ADR is Proposed; the methodology is not implemented.
- **Deterministic and offline.** A fixed seed (`SEED`), standard library only, no files written, exit 0. Sketches assert only their own arithmetic (for example, that a clamp holds), which checks the sketch, not the methodology.
- **Where a hypothesis is registered** (#8, #9, #10, #15, #22, #23) the README quotes its falsification criterion; for #11, #13, #14, #17 the README says the criterion is proposed there.
- **Adding a sketch:** add the directory and files, set the catalog entry's class and `path`, add the id to `RUNNABLE` in `tests/test_methodology_sketches.py` (the map name is reused for the sketch set).

## 7. Best-Practice Ledger (Story 36.4)
`agent_learning.methodology_ledger` (`parse_ledger`, `current_entries`, `LedgerEntry`) parses `docs/project-docs/Methodology-Best-Practice-Ledger.md`. Pure: it takes text and returns entries, and imports nothing from storage.

- **Entry:** `## BP-###` with `- field: value` lines (methodology, practice, preconditions, applies_to, evidence_class, evidence_ref, evidence_count, status, optional tier, supersedes, links). Unknown or missing fields, unknown enumeration values, unknown methodology ids and duplicate ids raise `ValueError` naming the entry.
- **Adoption:** `adopted` needs `evidence_class: real-episodes`, a declared `tier`, and `evidence_count` at or above `AutonomyConfig.for_tier(tier).min_outcomes`. `source-doc` and `synthetic-demo` can never be adopted. Today every entry is a `candidate`, because no real episodes of a methodology exist yet.
- **Append-only:** never edit an entry. A status change is a new entry with `supersedes: BP-###` naming an earlier entry of the same methodology; each entry can be superseded once; `current_entries` returns the tails.
- **Links:** `LL-###` and `HYP-AL-###` must match the format, and must exist when the caller passes `known_links` (the register test passes the real ones).
- **Adding an entry:** append a section; run `tests/test_methodology_ledger.py`. Do not raise the evidence class or status without the real episodes.

## 8. Review-Triage Loop (Story 36.5)
`agent_learning.review_triage` turns the Step 8 triage lines of the implement-story skill into evidence. Pure: it takes text and plain data and imports nothing from a storage module directly.

- **Record:** `parse_triage_line("Q-12-3 | claim type | verified: <v> | decision: <d> | <reason> | fix: <commit or none>")` returns a `TriageRecord`; a claim type, `verified` or `decision` outside its vocabulary raises naming the field and value; `unknown` is accepted. The log's `logic` is read as `logic error`, and `accepted with modification` as `accepted` with `(with modification)` in front of the reason. `find_triage_lines(text)` returns the backticked lines of a log.
- **Episode metadata:** `to_episode_metadata(record)` returns a plain dict. Import it from `agent_learning.review_triage`; it is not re-exported from the package root, where `to_episode_metadata` is the tailoring one.
- **Reliability:** `reliability(records, reviewer, claim_type, z=1.96, min_cases=5)` counts `yes` as verified, `no` and `partial` as not, excludes `unknown`, and gives `lower_bound=None` below `min_cases`. It is evidence for a person, not a rule.
- **Backfill:** `reconstruct_record(finding_id, **known)` marks `reconstructed=True` and leaves every field the history does not show as `unknown`. Never fill a field from memory.
- **Shapes (declared, not initialized):** `docs/policy-shapes/triage-review-finding.*` (accept_and_amend, decline_with_reason, defer_to_human; `requires_human_approval: true`) and `route-review-finding.*` (three verification-order actions, no accept or decline). The maintainer initializes them with `task-policy-init` (triage with `full` authority, routing with `low`). Triage is never learned; only the order of verification may be.

## 9. Tailoring Matrix and Template Propagation (Story 36.6)
`docs/project-docs/Methodology-Tailoring-Matrix.md` pairs a need in the store or in lessons learned with catalog ids. `tests/test_methodology_tailoring_matrix.py` parses the table.

- **Every row is a `hypothesis`**, never a finding. A row needs existing catalog ids, `Applies to` of `store` or `lessons-learned`, a falsification criterion, hypotheses that exist in the Ideation Document, and a `Ledger` entry that is current, `candidate`, and about one of the row's methodologies.
- **Adding a row:** append the candidate to the ledger first (a new `BP-###`), then add the row with that id. Do not mark a row as anything but `hypothesis` without real episodes meeting the tier gate.
- **Template:** `sidpa-template` carries `docs/methodologies/` (catalog, matrix, README), the ledger template (empty) and `init_project.py` scaffolds it. The template matrix leaves the `Ledger` column as "add a candidate entry first", because the template ships no ledger entries. Re-copy the catalog and matrix when they change here; the template's integrity tests check structure only.
