# Methodology Best-Practice Ledger (Organizational Process Assets)

**Governing ADR:** [ADR-036](../adr/ADR-036-learning-methodology-examples-ledger-and-review-triage-loop.md) — Accepted (2026-10-26), section 4.3  
**Parser and validator:** `agent_learning.methodology_ledger` (`parse_ledger`, `current_entries`); contract tests in `tests/test_methodology_ledger.py`.  
**Maintenance Rule:** Append-only. An entry is never edited. A status change is a new entry whose `supersedes` names the earlier entry of the same methodology; the latest entry in a chain is the current one. Git history is the guard against edits.  
**Adoption Rule:** a practice is `adopted` only on `real-episodes` evidence whose `evidence_count` meets the outcome gate of the tier declared for the decision (ADR-003: low 3, standard 20, high 50, critical 100 by default). `source-doc` and `synthetic-demo` evidence can never be adopted. Everything below is therefore a `candidate`.  
**Relation to the Lessons Learned Register:** an LL entry is a process lesson; a ledger entry is a practice of a learning methodology. A practice that is also a lesson links to the LL entry in `links`.

## How to add an entry
Append a section `## BP-###` (next number) with one `- field: value` line per field:

| Field | Value |
|---|---|
| `methodology` | catalog id, 1 to 32 (`examples/methodologies/catalog.json`) |
| `practice` | the practice, one sentence |
| `preconditions` | when it applies |
| `applies_to` | `store`, `lessons-learned`, `both` or `other` |
| `evidence_class` | `source-doc`, `synthetic-demo` or `real-episodes` |
| `evidence_ref` | where the evidence is |
| `evidence_count` | number of real episodes (0 for the other two classes) |
| `status` | `candidate`, `adopted` or `retired` |
| `tier` | `low`, `standard`, `high` or `critical`; required when `adopted` |
| `supersedes` | optional, the earlier `BP-###` this entry changes the status of |
| `links` | optional, comma-separated `LL-###` and `HYP-AL-###` identifiers that exist |

---

## BP-001
- methodology: 2
- practice: Train a low-authority policy on contrastive episodes, with failures as well as successes, never on positive-only history.
- preconditions: A recurring decision whose past outcomes include both correct and incorrect actions.
- applies_to: both
- evidence_class: source-doc
- evidence_ref: Ideation HYP-AL-002 (REINFORCE advantage vanishes on all-correct data)
- evidence_count: 0
- status: candidate
- links: HYP-AL-002

## BP-002
- methodology: 9
- practice: When positive-only evidence is all that exists, try a confidence-interval bandit (UCB with a Wilson bound first, Thompson sampling second) before moving the decision to full authority.
- preconditions: A decision with positive-only history that is stuck below the autonomy gate under REINFORCE.
- applies_to: store
- evidence_class: source-doc
- evidence_ref: Ideation HYP-AL-009 (UCB preferred over Thompson as the first implementation)
- evidence_count: 0
- status: candidate
- links: HYP-AL-009

## BP-003
- methodology: 20
- practice: Learn the question "does this category of change warrant escalation" from aggregate outcomes, and keep the per-instance classification a resolver judgment.
- preconditions: A stable, repeated category-level question with recorded outcomes.
- applies_to: both
- evidence_class: source-doc
- evidence_ref: Ideation HYP-AL-007; implemented as escalate-diff-response
- evidence_count: 0
- status: candidate
- links: HYP-AL-007

## BP-004
- methodology: 6
- practice: Keep triage of external review findings with the human, and record each human disposition as an episode so a later policy can learn from it without taking over the decision.
- preconditions: A review loop where the reviewer's claims are verified by a person or by evidence before they are accepted or declined.
- applies_to: lessons-learned
- evidence_class: source-doc
- evidence_ref: Lessons Learned Register LL-004 and the Q review records in implementation-log.md
- evidence_count: 0
- status: candidate
- links: LL-004
