# BRD-014: Lightweight Critique-to-Evidence Ingestion

**Source ADR:** [ADR-014](../../adr/ADR-014-critique-to-evidence-ingestion.md) — Accepted (2026-10-28)  
**Governing Baseline:** none approved yet; cycle `CYC-001` (ADR-035, Proposed)  
**Status:** Draft (2026-10-28) — derived from Accepted ADR-014; not yet adjudicated through `approve-brd`.  
**Stakeholders:** Menno (Sponsor/PM/maintainer); reviewers, human or automated, whose findings should change a decision; SDK adopters who run full-authority decisions  

## Business Need

A reviewer's finding ("missing boundary validation on negative inputs") is text, and a full-authority decision consumes numbers. Today the author must re-draft the decision frame by hand to reflect the finding, and the link between the finding and the changed number is not kept. ADR-014 decides a deterministic way to turn a tagged finding into a bounded change in a criterion's evidence, with the finding cited, and to record it in `Episode.metadata`. No model weights change.

## Business Rules (BRU)

- **BRU-014-01 (Frozen Model):** Ingesting a critique never updates model weights or embeddings (ADR-014 Invariant 1).
- **BRU-014-02 (Bounded Change):** A finding's delta is within [-1.0, 1.0], and the pooled-support target is clipped to [1e-6, 1 - 1e-6] so the log-odds stay finite (ADR-014 §4.1, Invariant 2).
- **BRU-014-03 (Direction):** A defect finding (negative delta) never raises the pooled support of the criterion it names, and a confirming finding (positive delta) never lowers it. The pooled support moves by the delta, clipped to [0, 1]. This is the rule ADR-014 §4.1 states in prose ("only a defect adds doubt"). The mechanism first written in ADR-014 §4.4 did not meet it (FDD-014 §4, D1), so ADR-014 was amended on 2026-10-28 (new Invariant 5).
- **BRU-014-04 (No Guessed Delta):** The system never infers a delta. A finding without a criterion tag and a number is rejected, not guessed. The reviewer chooses the number (ADR-014 §4.1, §6 Negative).
- **BRU-014-05 (Traceability):** Every change to a criterion cites the finding that caused it, in the evidence source (ADR-014 Invariant 3).
- **BRU-014-06 (Storage Boundary):** The applied adjustments and the findings are stored only in `Episode.metadata["critique_adjustments"]`. Zero new `LearningStore` record types (ADR-014 Invariant 4; ADR-002 Invariant #2).
- **BRU-014-07 (Authority Unchanged):** The adjusted frame is resolved under `DecisionAuthority.FULL` with its existing human-approval requirement. A critique never grants autonomy (ADR-014 §4.3; ADR-003).

## Stakeholder Success Metrics

| Metric | Target |
|---|---|
| Direction | 0 cases where a defect finding raises, or a confirming finding lowers, the pooled support |
| Exactness | pooled support after = clip(support before + delta, 1e-6, 1 - 1e-6) within 1e-9 for every tested case |
| Bounds | 0 deltas outside [-1.0, 1.0] accepted; 0 pooled-support targets outside [1e-6, 1 - 1e-6] produced |
| No guessing | 100% of findings without a tag and a number rejected |
| Traceability | 100% of changed criteria carry a `critique:<finding id>` source |
| Storage boundary | 0 new record types; 0 imports from `agent_learning.storage` in the module |

## Out of Scope

- Inferring tags or deltas from free text, with a model or otherwise.
- Writing the rubric a reviewer uses to choose a delta (a prerequisite named in ADR-014 §6, not delivered here).
- Exporting the original Amazon Q comments from the PR threads, which real tagging needs (ADR-014 §4.4, test data).
- Any change to how the resolver pools evidence.
- Fine-tuning, reflection loops, and prompt concatenation (rejected in ADR-014 §5).
