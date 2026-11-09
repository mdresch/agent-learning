# BRD-039: Shadow-Gate Learning and the Review-Finding Corpus

**Source ADR:** [ADR-039](../../adr/ADR-039-shadow-gate-learning-and-review-finding-corpus.md) — Accepted (2026-11-09, Menno); Episode `6b98f377-9ab1-4290-91a1-0832546037ea`  
**Governing Baseline:** none approved yet; cycle `CYC-001` (ADR-035, Accepted). The unapproved candidate is `PMP-BL-v1.0.0`.  
**Status:** Approved (2026-11-09, Menno) — derived from Accepted ADR-039; adjudicated via `approve-brd` (robust utility 0.672, episode `169fcc02-4b02-493f-aff0-7c0f59fe7e70`). The support values in the decision frame are the author agent's own judgments.  
**Stakeholders:** Menno (Sponsor/PM/maintainer); maintainers who run `implement-story` Step 8 and the gate reviews; SDK adopters who want to measure a learner against a human decision before trusting it

## Business Need

Every approval and stage gate in this project is decided by a person, and no learner is ever asked what it would have decided. Nothing measures whether a learning method could advise at a gate. The registered gate history cannot answer the question either: every registered episode of `approve-adr`, `approve-user-stories`, `approve-fdd`, `approve-brd` and `approve-subsidiary-plan` records an approval, so a learner that always says "approve" scores perfectly there. The project does hold 223 logged Amazon Q review findings in the ADR-036 one-line shape. 221 parse, and about a quarter of those were declined. That is the only contrastive human-decision history, and it has never been registered as episodes (ADR-036 S1).

ADR-039 decides a write-once shadow-verdict record, an agreement report that is judged against the base rate, and a registered, health-checked, time-ordered review-finding corpus. This BRD states what the SDK and the rituals must do for that to be true. It adds no autonomy and changes no gate.

## Business Rules (BRU)

- **BRU-039-01 (Shadow Never Acts):** A shadow verdict is recorded in `Episode.metadata` and never changes a decision, a gate outcome or a document status (ADR-039 Invariant 1).
- **BRU-039-02 (Four Keys, No New Type):** The record is the four keys of ADR-039 §4.1 inside `Episode.metadata`. No field is added to `Episode`, no record type is added to `LearningStore` (Invariant 6; ADR-002).
- **BRU-039-03 (Write Once):** Shadow keys are written once, before the human verdict is recorded, and never edited. A correction is a new episode that references the old one (Invariant 8).
- **BRU-039-04 (Base Rate First):** An agreement report states `n`, `k`, the modal action, the base rate, the Wilson lower bound, the confusion matrix, and precision and recall for each non-modal action. Raw agreement alone is never reported as a result (Invariant 3).
- **BRU-039-05 (Declared Rule):** Whether a learner "tracks the human" follows the rule in FDD-039 §3: the tier's sample floor, then a margin over the base rate, then the Wilson lower bound. A one-class history is reported as not testable, never as tracking (ADR-039 §4.2, Invariant 3).
- **BRU-039-06 (Read-Only Report):** The report and the corpus health check read episodes and text. They write nothing, because agreement is evidence for a person and never an action (ADR-039 §4.2, Invariant 1).
- **BRU-039-07 (Corpus Is Reconstructed And Unguessed):** Each registered finding is an `Episode` under `triage-review-finding`, marked `reconstructed`. A field the log does not show reads `unknown`. The review date is `unknown` because the log line carries none (Invariant 4; ADR-036 Invariant 7).
- **BRU-039-08 (Contradictions Are Held Out):** A row whose `verified` and `decision` contradict, or whose label field is `unknown`, is listed for a human to read and is not used as a label until read (ADR-039 §4.4 item 2).
- **BRU-039-09 (Health Before Scoring):** No learner is scored on the corpus until the health report passes the thresholds in FDD-039 §3.4. A failed report stops evaluation (ADR-039 §4.4 item 5).
- **BRU-039-10 (Time-Ordered Only):** The reconstructed corpus is evaluated only by training on earlier findings (ordered by PR number, then finding number) and scoring on the next. A learner is never scored on a record it trained on. Results are labelled `retrospective` and are never counted as shadow-gate evidence (§4.4 item 6; Invariant 2).
- **BRU-039-11 (Registration Is A Human Act):** Registering the corpus writes to the local store and is never run by an agent on its own. It is idempotent: a second run adds nothing (ADR-039 §4.4 item 1; ADR-036 Invariant 6).
- **BRU-039-12 (Training Stays Gated):** Training on the corpus follows ADR-003 gates and ADR-005 progression. `triage-review-finding` keeps `requires_human_approval: true` (ADR-036 Invariant 9).
- **BRU-039-13 (Improvements Are A View):** The list of accepted findings against learner modules is generated from the episodes, grouped by module, and never hand-edited (ADR-039 §8 item 2).
- **BRU-039-14 (Rituals Record The Verdict First):** `implement-story` Step 8 and the gate reviews record a shadow verdict, when a shadow learner is configured, before the human decision is recorded (ADR-039 §4.5).
- **BRU-039-15 (Fork Rule):** New code goes in `agent_learning_ext`. No Microsoft module is edited (`tests/test_upstream_untouched.py`).
- **BRU-039-16 (Counts From Tooling):** A count in a status report or a document derived from this work comes from the tooling, not from a hand-written number (Invariant 7).

## Stakeholder Success Metrics

| Metric | Target |
|---|---|
| Contract | A shadow record has exactly the four keys; a second write to the same episode raises and changes nothing |
| One-class gates | A gate whose history is a single action reports `not_testable`; 0 learners are reported as tracking on a one-class history |
| Rule worked case | On the cases in FDD-039 §3.3, the reported status and Wilson bounds match within 1e-6 |
| Health | The report shows contradiction, `unknown` and held-out shares computed by tooling; a corpus with a held-out share above the threshold stops evaluation |
| Registration | After one run the store holds one `triage-review-finding` episode per parsed finding; a second run adds 0 |
| No guessing | 0 registered episodes carry a review date, a verification or a decision that the log line does not show |
| Time order | 0 retrospective scores use a record at or after the one being scored |
| Rituals | `implement-story` Step 8 and the gate review text state "record the shadow verdict before the human decision" |
| Fork | `tests/test_upstream_untouched.py` still passes; the new modules import nothing that edits a Microsoft module |

## Out of Scope

- Promoting any learner, or changing any gate's authority or approval flag. Shadow results are evidence for a person.
- Shadow runs of #8 critique-to-evidence and #15 warm-start at the ADR, BRD and FDD gates. Those gates hold only approvals, so a shadow run cannot show discrimination there until they hold rejections or revision requests. The first retrospective round fixes the baselines a learner must beat on the review-finding corpus. Adapters for #2 REINFORCE and #9 Thompson follow in a later story.
- A `trace_id` on `Episode` (#25), off-policy evaluation (#29), and the per-knowledge-area plan learners.
- Reviewers other than Amazon Q. The reviewer is recorded on each episode so they can join later (ADR-039 §8 item 3).
- Propagating the Step 8 change to `sidpa-template`. That is a Tier 3 proposal for a human to approve.
