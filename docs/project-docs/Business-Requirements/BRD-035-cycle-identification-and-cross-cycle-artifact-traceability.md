# BRD-035: Cycle Identification and Cross-Cycle Artifact Traceability

**Source ADR:** [ADR-035](../../adr/ADR-035-cycle-identification-and-cross-cycle-artifact-traceability.md) — Proposed (2026-10-26); ready for `approve-adr`  
**Governing Baseline:** none approved yet; the bootstrap pass is `CYC-001` (ADR-035 §4.9)  
**Status:** Draft (2026-10-29) — derived from Proposed ADR-035; not yet adjudicated via `approve-brd`. Adjudication waits until ADR-035 is accepted.  
**Stakeholders:** Menno (Sponsor, Project Manager, maintainer)

## Business Need

A baseline id says how deep a change was. It does not say which pass produced a version, or which Ideation, Business Case, and Charter texts that pass was built on. A rollback or an abandoned pass currently leaves no id. The Charter can change without a version bump, so a version string alone does not identify content. Plan frontmatter says `baseline_id`, while older artifacts say `pmp_baseline`.

ADR-035 names a cycle `CYC-NNN`, keeps an append-only Cycle Register with a provenance pin set, and gives a lookup order from any artifact version to that cycle. The register is a Markdown document. It is not a new `LearningStore` type. Frontmatter is a copy, checked against the register. `cycle_id` and `baseline_id` stay out of the canonical content hash, so re-pointing an unchanged artifact does not void its approval. This requirement is the check. It does not reconstruct pins from git, and it does not edit ADR-008, ADR-012, or ADR-013 in place.

## Business Rules (BRU)

- **BRU-035-01 (A cycle id and a baseline id have one shape):** A `cycle_id` matches `CYC-` plus at least three digits. A `baseline_id` matches `PMP-BL-v` plus three numeric parts. Anything else on a governed artifact is a Tier B `INVALID_METADATA`. `pmp_baseline` and `pmp_baseline_id` are accepted when reading an older artifact. New artifacts use `baseline_id`. An artifact from before the first baseline carries `cycle_id` and omits `baseline_id`.
- **BRU-035-02 (The two linkage keys are hash-neutral):** `cycle_id` and `baseline_id` join `last_modified`, `generated_at`, `governance_hash`, and `approval_ref` as volatile frontmatter. Changing only those two keys leaves the canonical hash unchanged (ADR-035 Invariant 10). The hash still changes when body text or any other frontmatter key changes. This rule amends the volatile set Story 13.1 checks. It does not change the rest of that hash.
- **BRU-035-03 (The register is an event log):** `docs/project-docs/Cycle-Register.md` is append-only. A cycle has an `OPEN` row and, when it ends, one terminal row: `CLOSED_BASELINED`, `ROLLED_BACK`, or `ABANDONED`. The latest row for a `cycle_id` is its current state. Rows are not edited. The first cycle is `CYC-001`. The next new id is the next integer. At most one cycle is `OPEN` (ADR-035 Invariant 2). A `CLOSED_BASELINED` row names the resulting `baseline_id` and a closing pin set. A `ROLLED_BACK` or `ABANDONED` row keeps the opening pins only. Every row cites an `episode_ref`.
- **BRU-035-04 (A pin identifies content):** A pin is an artifact path, a declared version, and a canonical content hash. A reconstructed pin is marked `reconstructed`. A pin whose text cannot be recovered is marked `unrecoverable` and carries no invented hash (ADR-035 Invariants 3 and 8). The opening set is recorded on the `OPEN` row. The closing set is recorded only on `CLOSED_BASELINED`.
- **BRU-035-05 (Lookup stops at the first hit):** For an artifact version, resolve in order: a pin whose hash equals the content hash, then the approval episode's `cycle_id`, then frontmatter when the register contains that cycle and the baseline agrees. From the latest row, read state, baseline, prior cycle, and the pin sets. Following `prior_cycle` is the lineage.
- **BRU-035-06 (Frontmatter is the copy):** A well-formed frontmatter value that disagrees with the register is a Tier B `TRACEABILITY_MISMATCH`. The flag is evidence. It does not block `approve_plan` by itself (ADR-035 Invariant 5). One case is stricter: when the register and the authoritative episode metadata disagree on `cycle_id` or `baseline_id`, the `CLOSED_BASELINED` row is refused until a human records a resolution. The checker returns that refusal. It does not write the register.
- **BRU-035-07 (Cycle and generation stay separate):** `CYC-NNN` is not a hypothesis generation. Documents say "cycle" for the pass and "generation" for ADR-009 recurrence depth. Neither counter resets the other. This rule has no code.
- **BRU-035-08 (No new record and no hash in the file):** The checker is plain data. It adds no `LearningStore` record type (ADR-002 Invariant #2). Pins and hashes are not written into the governed file (ADR-035 Invariant 4). `CYC-001` may be validated as an `OPEN` bootstrap row. This requirement does not mine git history and does not invent a pin.

## Stakeholder Success Metrics

| Metric | Target |
|---|---|
| Id shape | `CYC-001` and `PMP-BL-v1.0.0` pass; `CYC-1`, `CYCLE-001`, and `PMP-BL-v1` are `INVALID_METADATA` |
| Aliases | A file with only `pmp_baseline` yields that value as its baseline; `baseline_id` wins when both are present |
| Hash neutrality | Adding or changing `cycle_id` or `baseline_id` leaves the canonical hash unchanged; changing a body word changes it |
| Register | Two `OPEN` cycles are invalid; a third row for one id is invalid; `CYC-001` then `CYC-003` is invalid |
| Pins | A `reconstructed` pin requires a 64-hex hash; an `unrecoverable` pin uses the token `unrecoverable` and no other hash |
| Lookup | A hash that appears in a pin resolves to that row's cycle and does not consult frontmatter |
| Disagreement | Frontmatter that names another cycle is `TRACEABILITY_MISMATCH`; a register/episode clash refuses closure and writes nothing |
| Storage | 0 new record types; 0 imports of the store from the cycle module |

## Out of Scope

- Editing ADR-008 §4.6, ADR-012 §4.2 and §4.3.4, or ADR-013 §4.3 in place. Those amendments apply when ADR-035 is accepted (ADR-035 §8 item 1). This draft names the volatile-key change the code will make.
- Reconstructing `CYC-001` pins from git, and writing `docs/project-docs/Cycle-Register.md` with recovered hashes (ADR-035 §4.9). The checker accepts the row shape. The reconstruction is a later human pass.
- Git tags `cycle/CYC-NNN` (ADR-035 §8 item 2).
- Adding `trace_id` to `Episode` (ADR-035 §8 item 3).
- Archiving old register rows (ADR-035 §8 item 6).
- Tightening the Charter's no-bump convention (ADR-035 §8 item 5).
- The plan lint floors, caps, and section checks (Epic 12 and the daughter epics).
- Hypothesis generation counters (ADR-009).
