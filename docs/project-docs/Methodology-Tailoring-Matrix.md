# Methodology Tailoring Matrix (Organizational Process Assets)

**Governing ADR:** [ADR-036](../adr/ADR-036-learning-methodology-examples-ledger-and-review-triage-loop.md) — Accepted (2026-10-26), section 4.4  
**Checked by:** `tests/test_methodology_tailoring_matrix.py` (every row names existing catalog ids, a need for the store or lessons learned, a falsification criterion, and a ledger entry that is a `candidate`).  
**Status of every row:** `hypothesis`. No row is a finding. A row becomes a finding only through real episodes meeting the tier gate, recorded in the [ledger](Methodology-Best-Practice-Ledger.md) (ADR-036 Invariant 4); nothing here changes a methodology's state in the Ideation Document.  
**Maintenance Rule:** append-only in the manner of the ledger. A pairing that is later falsified is retired by a new row that supersedes it, not by editing the row.

## Pairings

| Need | Applies to | Methodology (catalog ids) | Hypothesis | Falsifiable by | Ledger | Status |
|---|---|---|---|---|---|---|
| Cold start of a new `TaskPolicy` in the store | store | #15 warm-start | HYP-AL-008 | Episodes to reach the gate, against a cold start | BP-005 | hypothesis |
| Positive-only history stalls a policy | store | #9, #10 | HYP-AL-002, HYP-AL-009 | Crossing the gate on the same dataset | BP-013 | hypothesis |
| Drift in stored outcomes | store | #30 | HYP-AL-021 | Recovery after a shifted reward sequence | BP-006 | hypothesis |
| Retrieving the lessons relevant to a decision | lessons-learned | #26 | HYP-AL-024 | Accuracy against a recency baseline | BP-007 | hypothesis |
| Turning review critique into evidence | lessons-learned | #8 | HYP-AL-005 | Convergence against REINFORCE on the same episodes | BP-008 | hypothesis |
| Choosing which findings need a human | lessons-learned | #32, #28 | HYP-AL-023, HYP-AL-019 | Errors caught at equal review budget | BP-009 | hypothesis |

## Reading the matrix
- **Need** is a place in the store or in lessons learned where a learning methodology might help. **Methodology** is the catalog id (`examples/methodologies/catalog.json`); the example or sketch for it is under `examples/methodologies/`.
- **Falsifiable by** is the test that would drop the pairing, taken from the hypothesis in the Ideation Document.
- **Ledger** is the `candidate` practice that backs the row. It stays `candidate` until real episodes meet the tier gate.
- A pairing whose methodology is only `documented` (#26, #28, #30, #32) has no example yet; the row is still a hypothesis, and the catalog entry names what would reopen it.
