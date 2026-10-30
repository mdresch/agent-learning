# BRD-037: Design-Time Baseline Feedback Loop

**Source ADR:** [ADR-037](../../adr/ADR-037-design-time-baseline-feedback-loop.md) — Accepted (2026-10-27, Menno); Episode `0eb8f52a-dea7-4ef6-8ac5-0e0e21def933`  
**Governing Baseline:** none approved yet; cycle `CYC-001` (ADR-035, Accepted). The unapproved candidate is `PMP-BL-v1.0.0`.  
**Status:** Draft (2026-10-29) — derived from Accepted ADR-037; not yet adjudicated via `approve-brd`.  
**Stakeholders:** Menno (Sponsor, Project Manager, maintainer)

## Business Need

The approved baseline has one route back today: Stage 16, then a Stage 17 Adaptation Plan, then Stage 6. That route is for evidence from executed work. A defect found while writing Stage 7 or checking Stage 8 readiness has no honest place on it. Putting that defect in an Adaptation Plan asks for durations that do not exist yet and asks the approver to accept an amendment instead of a baseline.

ADR-037 adds a second route. A finding is a `BFI-NNN` in the PMP's Pending Baseline Feedback table. The existing policies `classify-diff-type` and `escalate-diff-response` classify and route it. The evidence is marked `design_time`, so a later learner cannot mix it with execution evidence. A Steering-level item is approved as a whole revised baseline. The baseline id moves by a patch (`PMP-BL-v1.0.x`). The execution route, Stage 17, lessons learned, and Intent refinement stay as they are.

`evaluate_governance_diff` does not yet take `evidence_basis`. Until it does, a design-time finding is not sent through that function, because an episode without the key reads as `execution`. This requirement adds the parameter, the BFI check, the patch bump, and the section text a future PMP builder will emit.

## Business Rules (BRU)

- **BRU-037-01 (A finding takes one route):** `evidence_basis` is `design_time` or `execution`. A baseline feedback item is `design_time`. An execution finding is not a BFI. A call that omits the basis records `execution`, which leaves today's callers unchanged (ADR-037 §4.1, §4.10).
- **BRU-037-02 (The BFI is a table row):** A design-time defect is `BFI-NNN` with the stage, the document, at least one citation of a file and a section, the classification, the route, and the status. The row lives in the Pending Baseline Feedback table. `None` is a valid table when there is no open item. The row is not a `LearningStore` record (ADR-037 Invariant 5). A Stage 7 document cites the BFI. It does not correct the baseline inside itself.
- **BRU-037-03 (The existing pair classifies and routes):** `classify-diff-type` and `escalate-diff-response` are unchanged. No new `TaskPolicy` is registered (ADR-037 Invariant 6). The four landing places — editorial, upstream document, within PM authority, Steering Committee — are read by a person from that result against the Charter's approval limits. Those limits are not declared in this repository (ADR-037 §8 item 3). This requirement does not encode them and does not map the seven diff classes onto the four places.
- **BRU-037-04 (Steering level approves a baseline):** The unit of approval is a revised PMP, the changed plans, and the standard set: Spark, Ideation, Business Case, Benefits Statement, and Stakeholder Register. The Charter is included only when it was amended (ADR-037 §4.4). `approve-pmp` records the new baseline. This requirement does not build `approve-pmp` and does not check that those files exist on disk.
- **BRU-037-05 (No numbers and no invented evidence):** A design-time item cites documents that exist. It carries no duration, cost, or estimated date (ADR-037 Invariant 3). A mapping that includes one of those keys is refused.
- **BRU-037-06 (The basis is recorded and is not a bandit feature):** `evaluate_governance_diff` takes optional `evidence_basis`. The closed list is `design_time` and `execution`. The default is `execution`. The value is written on the `audit_evidence` envelope and on the audit episode metadata. It is not an action id, not a logit, and not an input the escalation policy uses to choose. An unknown value raises. A stored episode with no key still reads as `execution` (ADR-037 §4.10). Lineage classes stay frozen: `design_time` does not let them apply themselves.
- **BRU-037-07 (Patch for design-time, minor for execution):** From a baseline id, `design_time` increments the patch and `execution` increments the minor and resets the patch. The major number stays. The two increments are not interchangeable (ADR-037 Invariant 7). Whether a within-PM-authority plan change records a patch, or only a Steering package does, stays open (ADR-037 §8 item 2). The formatter does not answer that question.
- **BRU-037-08 (The other loops stay closed):** A design-time fix is not a lesson (ADR-010), does not open Stage 17, and does not refine Intent (ADR-009). The execution route's inputs stay execution evidence.
- **BRU-037-09 (The section is for the ported builder):** The feedback section names both loops and renders the table. The legacy generator is not edited (ADR-037 §4.11). The ported PMP builder from ADR-034 calls this text later. Until that builder exists, the generated PMP in this repository does not gain the section by this requirement.

## Stakeholder Success Metrics

| Metric | Target |
|---|---|
| Default | A call that omits `evidence_basis` records `execution` |
| Design-time | A call with `design_time` records that value on the envelope and, when an audit episode is written, on its metadata |
| Reader | An episode metadata dict with no key reads as `execution` |
| Bandit | The seven diff actions and the three escalation actions are unchanged; two bases do not change a frozen class's human escalation |
| BFI | A row with no citation, or with a duration, cost, or date key, is refused; a row is not a store record |
| Version | `PMP-BL-v1.0.0` becomes `PMP-BL-v1.0.1` for design-time and `PMP-BL-v1.1.0` for execution |
| Section | Zero items render one `None` row; the legacy `pmbok/` generator is not imported |
| Policies | 0 new task ids |

## Out of Scope

- Replacing `classify-diff-type` or `escalate-diff-response`, and featurizing `evidence_basis` into the low-authority bandit (ADR-006).
- Building `approve-pmp`, assembling the revision package on disk, or archiving the previous baseline (ADR-008 §4.6.2).
- Encoding Charter approval limits, or deciding whether a within-PM plan change records a patch (ADR-037 §8 items 2 and 3).
- Editing the legacy PMP generator, `Project-Management-Plan.md`, or the SIDPA template repository.
- Retro-logging past Adaptation Plans as BFIs (ADR-037 §8 item 4).
- Choosing whether `BFI-NNN` is unique per cycle or per baseline (ADR-037 §8 item 1). The id shape is checked. Uniqueness across cycles is not.
- Lessons learned, Stage 17, and Stage 18.
- Adding a `LearningStore` record type.
