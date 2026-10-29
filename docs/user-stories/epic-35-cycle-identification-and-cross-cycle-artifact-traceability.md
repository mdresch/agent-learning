# Epic 35: Cycle Identification and Cross-Cycle Artifact Traceability

**Source ADR:** [ADR-035](../adr/ADR-035-cycle-identification-and-cross-cycle-artifact-traceability.md) — Proposed (2026-10-26)  
**Source BRD/FDD:** [BRD-035](../project-docs/Business-Requirements/BRD-035-cycle-identification-and-cross-cycle-artifact-traceability.md) / [FDD-035](../project-docs/Functional-Design/FDD-035-cycle-identification-and-cross-cycle-artifact-traceability.md)  
**Status:** Draft (2026-10-29) — derived from Proposed ADR-035, BRD-035 and FDD-035; not yet adjudicated via `approve-user-stories`. Implementation waits until ADR-035 is accepted.

Four stories. Each rule sits in one story (LL-012). Contract tests: `tests/test_cycle_ids.py` (35.1), `tests/test_cycle_register.py` (35.2), `tests/test_cycle_lookup.py` (35.3), `tests/test_cycle_flags.py` (35.4). Stories 35.2 and 35.3 also wait until FDD-035 §5 item 1 is confirmed. BRU-035-07 has no story: cycle and generation stay different words, and no counter is code.

---

## Story 35.1 — Cycle and baseline ids, and a hash that ignores them

**Status:** Draft — blocked on acceptance of ADR-035  
**As** a governance reviewer,  
**I want** `cycle_id` and `baseline_id` recognized, and left out of the canonical hash,  
**so that** re-pointing an unchanged artifact at a new cycle does not void the approval.

### Acceptance Criteria

- **$AC_0$ (Shape):** `CYC-001` and `CYC-1000` match the cycle pattern. `CYC-1`, `CYC-01`, and `CYCLE-001` do not. `PMP-BL-v1.0.0` and `PMP-BL-v10.2.3` match the baseline pattern. `PMP-BL-v1` and `v1.0.0` do not.
- **$AC_1$ (Alias):** `read_baseline` returns `baseline_id` when that key is present, including when `pmp_baseline` is also present. It returns `pmp_baseline` when only that alias is present, and `pmp_baseline_id` when only that alias is present. It returns `None` when all three are absent.
- **$AC_2$ (Volatile):** `VOLATILE_KEYS` contains the Epic 13 four names plus `cycle_id` and `baseline_id`. The canonical hash is unchanged when only `cycle_id` changes, when only `baseline_id` changes, and when both change. The hash changes when a body word changes. The hash changes when `pmp_baseline` changes.
- **$AC_3$ (Existing keys):** Changing only `last_modified`, `generated_at`, `governance_hash`, or `approval_ref` still leaves the hash unchanged.
- **$AC_4$ (Purity):** `cycle.py` imports no storage module. The story updates the volatile-key expectation in `tests/test_plan_hash.py` so the two new names are part of that assertion.

---

## Story 35.2 — The register is an event log with one open cycle

**Status:** Draft — blocked on confirmation of FDD-035 §5 item 1, and on acceptance of ADR-035  
**As** a governance reviewer,  
**I want** the Cycle Register rejected when it reopens a cycle, skips a number, or leaves two cycles open,  
**so that** the latest row is a trustworthy current state.

### Acceptance Criteria

- **$AC_0$ (Parse):** A table with the FDD-035 §2 header and one data row returns one `CycleRow`. A pin cell whose text is `docs/a.md|v1|` followed by 64 lowercase hex characters and `|reconstructed` returns one pin with that mark. A missing header raises `ValueError`.
- **$AC_1$ (Pins):** `live` and `reconstructed` with a 64-hex hash parse. `unrecoverable` with the token `unrecoverable` parses. `unrecoverable` with a hex hash raises `ValueError`. An unknown mark raises `ValueError`.
- **$AC_2$ (Event log):** One `OPEN` row for `CYC-001` returns no validation message. A second row `CLOSED_BASELINED` with a baseline id and a closing pin returns none. A third row for `CYC-001` returns a message for rule 4. A second row `ROLLED_BACK` with a closing pin or a baseline id returns a message for rule 9.
- **$AC_3$ (One open, monotonic):** Two `OPEN` rows for `CYC-001` and `CYC-002` return a message for rule 5. Introducing `CYC-003` while `CYC-002` has never appeared returns a message for rule 2. A register whose first id is `CYC-002` returns a message for rule 1.
- **$AC_4$ (Bootstrap):** An in-memory `CYC-001` `OPEN` row, trigger `initial`, a non-empty `episode_ref`, an empty baseline, and one `unrecoverable` pin passes `validate_register`. The test does not write `Cycle-Register.md`.
- **$AC_5$ (No write):** `parse_register` and `validate_register` do not create or modify a file.

---

## Story 35.3 — Lookup stops at the first source that hits

**Status:** Draft — blocked on Story 35.2  
**As** a governance reviewer,  
**I want** a content hash in a pin to decide the cycle before frontmatter is consulted,  
**so that** a stale copy in frontmatter cannot override the register.

### Acceptance Criteria

- **$AC_0$ (Pin):** A hash present on a `live` or `reconstructed` pin returns source `pin` and that cycle's latest row. Frontmatter naming a different cycle does not change the hit. An `unrecoverable` pin is not a hit.
- **$AC_1$ (Last pin row):** Two rows pin the same hash. The hit's `cycle_id` is the later row's id. The returned row is the latest row of that id.
- **$AC_2$ (Episode):** With no pin hit, a non-empty episode id that the register contains returns source `episode`. Frontmatter is not consulted. An episode id absent from the register returns `None` and does not return the frontmatter cycle.
- **$AC_3$ (Frontmatter):** With no pin and no episode id, frontmatter is a hit only when the register has that cycle and the baseline equals the latest row, including both empty. A different baseline returns `None`.
- **$AC_4$ (Lineage):** Given a hit, the caller can follow `prior_cycle` through the rows to `CYC-001`. A `prior_cycle` that matches no earlier row is reported by `validate_register` rule 10, and `lookup` is not asked to repair it.

---

## Story 35.4 — Frontmatter is checked, and a clash refuses closure

**Status:** Draft — blocked on Story 35.3  
**As** a governance reviewer,  
**I want** a bad or disagreeing frontmatter id flagged, and a clash between the register and the episode to refuse the closing row,  
**so that** the copy can be corrected and the authoritative pair cannot be closed while they disagree.

### Acceptance Criteria

- **$AC_0$ (Malformed):** `CYC-1` produces one Tier B `INVALID_METADATA` whose message says `cycle_id` is malformed. `PMP-BL-v1` produces one whose message says `baseline_id` is malformed. An empty baseline produces no baseline-format finding.
- **$AC_1$ (Disagree):** A well-formed frontmatter cycle that differs from the lookup row produces one Tier B `TRACEABILITY_MISMATCH` naming the field. Agreeing values produce no mismatch finding.
- **$AC_2$ (Unknown episode):** An episode id that is not in the register produces `TRACEABILITY_MISMATCH` with the episode message. It does not also produce a frontmatter hit.
- **$AC_3$ (Closure):** `closure_refused` is `True` when the two cycle ids differ, and when the two baseline ids differ. It is `False` when one side of a pair is empty. The function writes nothing.
- **$AC_4$ (No new record):** `cycle.py` imports no storage module. No test writes a hash into a governed artifact file.

---

## Out of Scope for this epic

- Editing the ADR-008, ADR-012, or ADR-013 files.
- Creating `Cycle-Register.md` from git history.
- Git tags, `trace_id`, and register archival.
- Changing floors, caps, or plan-section checks.
- A hypothesis-generation counter.
