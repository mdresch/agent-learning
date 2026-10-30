# ADR 035: Cycle Identification and Cross-Cycle Artifact Traceability

## 1. Executive Brief
The Intent-to-Outcome chain is a closed loop (ADR-008 §4.4, ADR-009): Ideation, Business Case and Charter lead to a PMP baseline and its plans, then to ADR, BRD, FDD and stories, then to deliverables, evidence and lessons, and back through Stage 16 governance change, Stage 17 adaptation and Stage 18 intent refinement into a revised baseline. Each pass produces new versions of the same artifacts.

Today the repository can say which **baseline** governs an artifact (`PMP-BL-vX.Y.Z`, ADR-008 §4.6), but it cannot say which **cycle** produced a given version, nor which versions of the upstream governance documents that cycle was built on. This ADR defines:
1. A **cycle**, a monotonic **`cycle_id`**, and its lifecycle states.
2. A **Cycle Register** that records, per cycle, its trigger, its outcome and a **Provenance Pin Set** (artifact, declared version, canonical content hash).
3. A **lookup rule** that answers "which version belongs to which cycle" for any artifact.
4. The frontmatter and `Episode.metadata` fields that carry the link, with the register as authority and frontmatter validated against it.

It adds no `LearningStore` record type (ADR-002 Invariant #2) and no hash inside governed files (ADR-012 §4.2 note).

---

## 2. Status
**Accepted (2026-10-29, Menno)** — Cross-cutting traceability standard. Episode: `76a4003b-a725-4405-b3c1-d2f8122671c6`. The §8.1 amendments to ADR-008, ADR-012 and ADR-013 are now authorized and are not edited in this adjudication.

---

## 3. Context & Problem Statement
Findings from the repository as of 2026-10-26:
* **Baseline is not cycle.** `PMP-BL-v1.1.0` and `v2.0.0` encode the *depth* of change (ADR-008 §4.6.1), not the pass that caused it. A rolled-back or abandoned pass leaves no identifier at all.
* **Upstream versions are not pinned.** The Ideation Document is at v1.13, the Charter at v1.9 and the Business Case at v1.4, each versioned independently. Nothing records which of them a given baseline was built from.
* **Version alone does not identify content.** The Charter's own convention is that routine execution findings are appended *without* a version bump, so two different texts can share "v1.9". Identification needs a content hash, as ADR-013 §4.3 already does for plans.
* **The baseline field has two names.** Plan frontmatter uses `baseline_id`; `Project-Management-Plan.md` and ADR-008/009 use `pmp_baseline` (with `pmp_baseline_id` accepted as an alias in ADR-009). ADR-008 Invariant 6 requires every ADR, BRD, FDD and story to reference its governing baseline, but the ADR files themselves carry no such field.
* **"Cycle" already means two things.** ADR-009 uses "generational cycles" for hypothesis recurrence ($H \to H.1 \to H.1.1$, $d_{\max}=2$). That is a refinement generation, not a delivery pass. The two must not be conflated.
* **`baseline_id` is already hashed.** ADR-013 §4.3 strips only `last_modified`, `generated_at`, `governance_hash` and `approval_ref`. Plans already carry `baseline_id`, so re-pointing an unchanged plan at a new baseline today changes its canonical hash and would invalidate its approval. Adding `cycle_id` would add a second such key.
* **Episodes carry no cycle link.** `Episode` has `correlation_id`, `session_id` and free `metadata`, and no `trace_id` (the missing field that blocks methodology #25). Decision-result files use ad hoc names such as `-v1`.

---

## 4. Technical Decision

### 4.1 Definition of a Cycle
A **cycle** is one pass through the closed loop that is opened by a trigger and ends in exactly one outcome. Triggers:
1. **Initial** — the first Ideation-to-baseline pass.
2. **Adaptation** — an accepted Stage 16 governance change leading to an approved Stage 17 adaptation plan (ADR-008).
3. **Refinement** — an approved Stage 18 Intent Refinement Proposal (ADR-009).

A cycle's `cycle_id` has the form `CYC-NNN` (zero-padded, monotonic, never reused). States:

| State | Meaning |
|---|---|
| `OPEN` | Trigger accepted; artifacts being revised. |
| `CLOSED_BASELINED` | Ended with a baseline approved by `approve-pmp`; records the resulting `baseline_id`. |
| `ROLLED_BACK` | Ended by ADR-008 §4.7 rollback; the prior baseline is restored, the `cycle_id` is retained. |
| `ABANDONED` | Ended by decision without a baseline. |

At most one cycle is `OPEN` at a time (aligned with the ADR-009 stabilization rule, Invariant 13). A cycle yields at most one approved baseline. Opening a cycle while another is `OPEN` is refused, and a register containing two `OPEN` cycles is invalid.

**Transition authority.** Every transition is backed by a human-approved episode, and its register row cites that episode's ID. No tool changes cycle state on its own.

| Transition | Authorizing episode |
|---|---|
| Open (`initial`) | Charter approval (`approve-charter`) |
| Open (`adaptation`) | `approve-adaptation-plan` (ADR-008) |
| Open (`refinement`) | Approved Intent Refinement Proposal (`approve-intent-refinement`, ADR-009) |
| `CLOSED_BASELINED` | `approve-pmp` |
| `ROLLED_BACK` | The ADR-008 §4.7 rollback decision |
| `ABANDONED` | An `approve-adaptation-plan` episode whose accepted disposition is to end the cycle without a baseline |

All of these gates carry permanent `requires_human_approval: true`, so the Sponsor / Charter Approver is the authority in each case.

### 4.2 The Cycle Register
`docs/project-docs/Cycle-Register.md` is an append-only, version-controlled Markdown register, in the manner of the Lessons-Learned Register (ADR-010). It is a document, not a `LearningStore` entity.

**Append-only means event-log rows.** A cycle is recorded by one row per state change: an `OPEN` row at opening and one terminal row at closure. Rows are never edited or deleted, and the **latest row for a `cycle_id` defines its current state**. Each row records:

| Field | Content |
|---|---|
| `cycle_id` | `CYC-NNN` |
| `state` | Per §4.1 |
| `date` | Date of this row |
| `trigger` | `initial` / `adaptation` / `refinement` (on the `OPEN` row) |
| `episode_ref` | ID of the authorizing episode (§4.1 table) |
| `baseline_id` | Resulting baseline (on a `CLOSED_BASELINED` row) |
| `opening_pin_set` | Provenance Pin Set at opening (on the `OPEN` row) |
| `closing_pin_set` | Provenance Pin Set at approval (on a `CLOSED_BASELINED` row only) |
| `prior_cycle` | The `cycle_id` this one revises, if any |

### 4.3 Provenance Pin Set
A cycle records one pin per upstream governance artifact:

```
pin: { artifact: "<path>", version: "<declared version>", content_hash: "<canonical hash>" }
```

**Pin timing.** The `opening_pin_set` is recorded when the cycle opens. A `CLOSED_BASELINED` row additionally records a `closing_pin_set` taken at `approve-pmp`, so mid-cycle changes to upstream documents are visible as the difference between the two. `ROLLED_BACK` and `ABANDONED` rows keep only the opening pins.

**Pinned artifacts.** The Ideation Document, the Business Case, the Project Charter, the document that currently hosts the tailoring matrix, and, when the trigger is `adaptation`, the approved Adaptation Plan. Under ADR-011 the integration section (which holds the routes) has one home at a time, either `Project-Charter.md` or `Project-Management-Plan.md`; pin whichever hosts it, and if both pinned documents are the same file, pin it once.

The `content_hash` uses the ADR-013 §4.3 canonical LF-normalized scheme. The pin set is stored in the register rows and in the `approve-pmp` `Episode.metadata`; it is never stored inside the governed file (ADR-012 §4.2 note). Because the Charter may change without a version bump, the hash is what identifies the content.

### 4.4 Fields That Carry the Link
Frontmatter keys (flat scalars, so no change to the ADR-034 §4.3.1 grammar):

| Key | Where | Rule |
|---|---|---|
| `cycle_id` | Every governed artifact: plans, ADR, BRD, FDD, stories, adaptation plans, Ideation, Business Case, Charter | The cycle in which **this version** was produced. |
| `baseline_id` | Every governed artifact produced after the first baseline | Canonical name for the governing baseline. |

`pmp_baseline` and `pmp_baseline_id` remain **accepted aliases** on read, for compatibility with ADR-008/009 artifacts; new artifacts use `baseline_id`. Artifacts that predate the first baseline carry `cycle_id` and omit `baseline_id`.

`Episode.metadata` for any approval or adjudication episode records `cycle_id`, `baseline_id` and the artifact's `version` and canonical `content_hash` (ADR-013 §4.3).

**Hash neutrality.** `cycle_id` and `baseline_id` are linkage keys, added to the volatile frontmatter set that `strip_volatile_frontmatter` excludes from the canonical hash (an amendment to ADR-013 §4.3). Re-pointing an unchanged artifact at a new cycle or baseline therefore does not invalidate its approval. An artifact carried forward unchanged keeps the `cycle_id` of the cycle in which that version was authored, and its `baseline_id` is updated to the new baseline when one is approved.

### 4.5 Authority and Validation
The Cycle Register and `Episode.metadata` are authoritative; frontmatter is a convenience copy validated against them, as `route` is validated against the tailoring matrix (ADR-012 Invariant 9). A frontmatter `cycle_id` or `baseline_id` that disagrees with the register, or that is malformed, raises a **Tier B** structural flag (ADR-012 §4.3.4):
* `FLAG: INVALID_METADATA` for malformed `cycle_id` (not `^CYC-\d{3,}$`) or `baseline_id` (not `^PMP-BL-v\d+\.\d+\.\d+$`).
* `FLAG: TRACEABILITY_MISMATCH` for disagreement with the register.

Both are flags resolved by recorded rationale, not mechanical blocks (ADR-012 Invariant 8), because the frontmatter is the copy and is corrected by editing it. One case is stricter: if the register and the authoritative `Episode.metadata` disagree on an artifact's `cycle_id` or `baseline_id`, both authoritative sources conflict. The register row that would close the cycle (`CLOSED_BASELINED`) is refused until a human resolves the conflict and records the resolution.

### 4.6 The Lookup Rule: "Which Version, Which Cycle"
Given any artifact version `(path, version, content_hash)`:
Resolve in this order and stop at the first hit:
1. **Pin set:** a register row whose `opening_pin_set` or `closing_pin_set` contains the `content_hash` (upstream governance artifacts).
2. **Approval episode:** the artifact's authoritative approval `Episode.metadata.cycle_id` (plans, ADRs and other artifacts that have approval episodes).
3. **Validated frontmatter:** for an artifact with no pin and no approval episode (for example a story), the frontmatter `cycle_id` and `baseline_id`, accepted only if the register has that `cycle_id` and its baseline matches.

Then, from the latest register row for that `cycle_id`, read `state`, `baseline_id`, `prior_cycle` and the pin sets. Following `prior_cycle` links yields the lineage from the initial cycle to the present, and the difference between two cycles' pin sets shows exactly which upstream versions changed. The register keeps no per-artifact inventory for downstream artifacts; that would duplicate the episode record and grow without bound.

The full trace chain is: hypothesis (Ideation) $\to$ Business Case $\to$ Charter $\to$ **cycle** $\to$ baseline $\to$ plans $\to$ ADR / BRD / FDD / stories $\to$ approval episodes.

### 4.7 Relation to Hypothesis Generations
A refinement generation ($H \to H.1 \to H.1.1$, ADR-009) is recorded with the `cycle_id` in which it was adjudicated. The two counters are independent; neither resets the other. Documents say "cycle" for `CYC-NNN` and "generation" for hypothesis recurrence depth.

### 4.8 Decision Comparisons Across Cycles
When ADR-005 progression comparison is run on successive decision results for the same artifact, each result is identified by `(artifact, version, cycle_id)` in the registering episode's metadata, replacing ad hoc `-v1` file naming as the source of truth. File names may remain as a convenience.

### 4.9 Migration
The current baseline, `PMP-BL-v1.0.0` (the baseline `Project-Management-Plan.md` carries today), is a legacy bootstrap baseline with no approved governance status (ADR-013 §4.8, ADR-034 §4.2.3). It was never approved through `approve-pmp`, so it cannot be a `CLOSED_BASELINED` cycle. The current state is therefore recorded as `CYC-001` with state **`OPEN`**, `trigger: initial`, and a note that it holds the legacy bootstrap baseline. `CYC-001` becomes `CLOSED_BASELINED` only when the first baseline approved through a built `approve-pmp` supersedes it.

Its `opening_pin_set` is **reconstructed** from git history at the commit that created the bootstrap baseline, and each pin is marked `reconstructed: true`. No hash is invented; where an upstream document's state at that time cannot be recovered, the pin is recorded as `unrecoverable`.

---

## 5. Architectural Invariants
1. **Cycles Are Never Reused or Renumbered:** `CYC-NNN` is monotonic; rolled-back and abandoned cycles keep their identifiers.
2. **One Open Cycle:** At most one cycle is `OPEN`. Opening a second is refused, and a register with two `OPEN` cycles is invalid.
3. **Identification Is By Hash, Not Version Alone:** An artifact version is identified by `(version, canonical content_hash)`.
4. **No Hash In-File:** Pins and hashes live in the register and `Episode.metadata`, never in the governed file (ADR-012 §4.2).
5. **Register Is Authoritative:** Frontmatter is validated against it; disagreement is a Tier B flag, not a block.
6. **Zero New Record Types:** No `LearningStore` entity is added (ADR-002 Invariant #2); the register is a version-controlled document.
7. **Cycle and Generation Are Distinct:** `CYC-NNN` and hypothesis recurrence depth are separate counters.
8. **No Fabricated Provenance:** Reconstructed pins are marked `reconstructed: true`; unrecoverable ones are marked `unrecoverable`.
9. **Rows Are Immutable, Transitions Are Authorized:** Register rows are never edited; every state change cites a human-approved episode (§4.1).
10. **Linkage Keys Are Hash-Neutral:** `cycle_id` and `baseline_id` are excluded from the canonical content hash.

---

## 6. Alternatives Considered
* **Alternative 1: Use the baseline ID as the cycle ID.** *Rejected:* Baseline encodes change depth, not the pass; rollbacks and abandoned passes would have no identity, and one baseline number cannot pin upstream versions.
* **Alternative 2: Store hashes and pins in each artifact's frontmatter.** *Rejected:* Self-referential hash paradox (ADR-012 §4.2 note); frontmatter pins would also drift from the approved record.
* **Alternative 3: Rely on git commits and tags as the cycle record.** *Rejected as sole mechanism:* Git history identifies commits but not cycle triggers, outcomes or the governance pins; kept as the source for migration reconstruction.
* **Alternative 4: A new `Cycle` entity in `LearningStore`.** *Rejected:* Violates ADR-002 Invariant #2 (zero entity sprawl).
* **Alternative 5: Add `trace_id` to `Episode` first.** *Rejected here:* A schema change outside this ADR's scope; `cycle_id` in `metadata` is a coarse link that does not replace a per-run trace.

---

## 7. Consequences

### Positive
* Any artifact version can be placed in a cycle, a baseline and an upstream-version context.
* Rollbacks and abandoned passes are visible rather than silent.
* Changes between cycles can be explained as pin-set differences.
* Resolves the `baseline_id` / `pmp_baseline` split without breaking existing artifacts.

### Negative
* Authoring burden: each governed artifact gains `cycle_id`, and the register must be maintained.
* Existing artifacts need backfill; reconstructed pins carry less certainty than live ones.
* ADR-025 and ADR-026 to ADR-033 list frontmatter keys explicitly, so their templates lag until ADR-012 and each daughter ADR gain `cycle_id` through amendment.

---

## 8. Open Questions & Future Extensions
1. **Amending the Accepted ADRs:** On acceptance, apply: ADR-008 §4.6 (canonical `baseline_id`, aliases), ADR-012 §4.2 (`cycle_id` key) and §4.3.4 (add `FLAG: INVALID_METADATA` use for ids and the new Tier B `FLAG: TRACEABILITY_MISMATCH`), and ADR-013 §4.3 (add `cycle_id` and `baseline_id` to the volatile set). This draft does not edit them.
2. **Per-Cycle Tags:** Whether git tags `cycle/CYC-NNN` should mark the closing commit (deferred to tooling).
3. **`trace_id`:** Whether a per-run `trace_id` should later be added to `Episode` (methodology #25) and how it would relate to `cycle_id`.
4. **Register Parsing:** A validator for the register and pin sets in the pure `agent_learning.pmbok` module (ADR-034).
5. **Charter Versioning:** Whether the Charter's no-bump-for-routine-updates convention should be tightened now that hashes carry identity.
6. **Register Growth:** Whether closed-cycle rows may be moved to dated archive files, or a machine-readable projection kept alongside, once the register is large (deferred to tooling; the latest-row-wins rule must survive any split).

---

## 9. Amendment Log

| Date | Change | Why |
|---|---|---|
| 2026-10-26 | Proposed | Initial drafting: cycle definition, Cycle Register, Provenance Pin Set, frontmatter and episode fields, authority rule, lookup rule and migration. |
| 2026-10-26 | Round 2 Review | Event-log register rows (latest wins) with `episode_ref`; transition authority table and single-OPEN enforcement; opening and closing pin sets; tailoring-matrix host document and Adaptation Plan pinned; `cycle_id`/`baseline_id` made hash-neutral (ADR-013 §4.3 amendment); lookup order pin set, then episode, then validated frontmatter; `CYC-001` recorded as `OPEN` bootstrap, not `CLOSED_BASELINED`; register-vs-episode conflict blocks closure; status wording and amendment list corrected. |
| 2026-10-29 | **Accepted by Menno** | Formally adjudicated and accepted through `approve-adr`; robust utility 0.762, expected utility 0.828; Episode `76a4003b-a725-4405-b3c1-d2f8122671c6`. §8.1 now authorizes the named amendments to ADR-008, ADR-012 and ADR-013; those files are not edited in this adjudication. |
