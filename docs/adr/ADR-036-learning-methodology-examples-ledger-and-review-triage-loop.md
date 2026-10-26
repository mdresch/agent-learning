# ADR 036: Learning Methodology Examples, Best-Practice Ledger and the Review-Triage Learning Loop

## 1. Executive Brief
The landscape in the Ideation Document (§2.1) lists 32 learning methodologies. Nine are real or partly real, ten have a Proposed ADR and no code, and thirteen are blocked, excluded, declined or have no ADR yet. Only some of the real ones have a runnable example, none of the rest has any worked example, and nothing records which practices have actually worked. The `sidpa-template` repository is meant to scaffold projects that use these methodologies where they fit the project's store and lessons learned, but it has nothing concrete to point to.

This ADR decides three things:
1. **An example catalog.** One entry per methodology (32), each classed as `runnable`, `proof_of_concept` or `documented`, with strict labeling so an example is never mistaken for evidence.
2. **A best-practice ledger.** An append-only register of practices per methodology, where a practice can be `adopted` only on real episodes.
3. **A review-triage learning loop.** The first methodology that learns while the project is being built: every automated-review finding is triaged during `implement-story` Step 8, recorded in a fixed shape, and used as evidence for the next decision. It uses critique-to-evidence (#8), reasoned resolution (#3) and confidence-bound reliability estimates (#9, #10) before any trained policy.

It adds no `LearningStore` record type (ADR-002 Invariant #2), grants no autonomy (ADR-003, ADR-001), and changes no methodology's state in the Ideation Document (that goes through ADR-024).

---

## 2. Status
**Accepted (2026-10-26, Menno)** — Cross-cutting. Episode: `f0047810-a3f2-49f4-8023-e3058fce3ed9`.

---

## 3. Context & Problem Statement
* **Catalog gap.** Ideation §2.1 states each methodology's feasibility in prose. A reader cannot run one, see its limits, or see what real data it needs.
* **Evidence risk.** An illustrative example with invented data can read as proof. The selection skill already forbids fabricating episodes to make a methodology look viable.
* **No practice memory.** Lessons Learned (ADR-010) records project process lessons. Nothing records, per methodology, which practices were tried, under what preconditions, and with what real result.
* **A learning loop already exists in the work.** `implement-story` Step 8 sends each PR to an automated reviewer, and the author triages every finding against the repository and accepts or declines it. On this repository that is 23 inline Amazon Q comments across eight merged PRs, plus four more findings on PRs #10 and #11, and a set of declined claims from other reviews. The decision and its reason are not recorded in a form a policy could use.
* **Constraints on learning from it.** The real data is small and, for Q, almost entirely accepted findings (HYP-AL-002: positive-only history cannot earn autonomy for a REINFORCE policy). Decline decisions affect gates, so a human must stay in the loop (ADR-001, ADR-008 Invariant #4), and under ADR-003 Invariant 6 the human-approval flag blocks learned authorization outright. The author who triages is also the author of the code under review.

---

## 4. Technical Decision

### 4.1 The Example Catalog
`examples/methodologies/catalog.json` has exactly one entry per methodology id 1 to 32. Each entry has: `id`, `name`, `state` (copied from Ideation §2.1), `class`, `adr`, `hypothesis`, `path`, and for `documented` entries a `reason` and a `reopening_condition`.

| Class | Applies to | What exists |
|---|---|---|
| `runnable` | State is Implemented, example-only, partial or practiced: #2, #3, #4, #5, #6, #12, #19, #20, #21 | A directory with `README.md` and an `example.py` that runs offline against the real SDK |
| `proof_of_concept` | A Proposed ADR and no code: #8 to #11, #13 to #15, #17, #22, #23 | A directory with `README.md` and a `sketch.py` that runs offline, seeded, with stdlib and the public SDK only |
| `documented` | Blocked, excluded, declined, or candidate with no ADR: #1, #7, #16, #18, #24 to #32 | A catalog entry and a short note only. No code |

The class follows from the state; a mismatch is a catalog error. Moving a methodology from `documented` to `proof_of_concept` requires its ADR to exist. This ADR does not change any methodology's state.

### 4.2 Labeling Contract (never evidence)
Every example and sketch starts with a header that names: `STATUS` (`runnable` or `proof_of_concept`), `CODE` (`sdk` or `sketch`), `DATA: SYNTHETIC`, the Ideation row, the ADR and hypothesis where any, and `NOT EVIDENCE: this run does not validate or invalidate the methodology`. The README states the falsification criterion copied from the hypothesis and the real data that would be needed to test it. Examples use an in-memory or temporary store, never the project's real store. No file under `src/` imports from `examples/`. Running an example never edits the catalog `state`.

### 4.3 The Best-Practice Ledger
`docs/project-docs/Methodology-Best-Practice-Ledger.md` is an append-only, version-controlled Markdown register in the manner of the Lessons-Learned Register. Entries are `BP-###` with: `methodology` (catalog id), `practice`, `preconditions`, `applies_to` (`store`, `lessons-learned`, `both`, `other`), `evidence_class` (`source-doc`, `synthetic-demo`, `real-episodes`), `evidence_ref`, `evidence_count`, `status` (`candidate`, `adopted`, `retired`), and links to `LL-###` and `HYP-AL-###`. Rules: `adopted` requires `real-episodes` evidence that meets the outcome gate of the tier declared for the decision (ADR-003). `synthetic-demo` and `source-doc` can never be adopted. A status change is a new entry that references the one it supersedes (`supersedes: BP-###`); the latest wins.

### 4.4 Tailoring for the Store and for Lessons Learned
A tailoring matrix lists candidate pairings, each marked `hypothesis`, never `finding`:

| Need | Candidate methodology | Falsifiable by |
|---|---|---|
| Cold start of a new `TaskPolicy` in the store | #15 warm-start (HYP-AL-008) | Episodes to reach the gate vs a cold start |
| Positive-only history stalls a policy | #9, #10 (HYP-AL-002, HYP-AL-009) | Crossing the gate on the same dataset |
| Drift in stored outcomes | #30 (HYP-AL-021) | Recovery after a shifted reward sequence |
| Retrieving the lessons relevant to a decision | #26 (HYP-AL-024) | Accuracy against a recency baseline |
| Turning review critique into evidence | #8 (HYP-AL-005) | Convergence vs REINFORCE on the same episodes |
| Choosing which findings need a human | #32, #28 (HYP-AL-023, HYP-AL-019) | Errors caught at equal review budget |

Each pairing links to a ledger `candidate` entry. The matrix is propagated to `sidpa-template` as a Tier 3 rule only after the stories that build the catalog are complete.

### 4.5 The Review-Triage Learning Loop
The loop turns Step 8 of `implement-story` into a source of decisions that improve with use. It has stages, and a stage is entered only when its predecessor's condition holds.

| Stage | What happens | Methodology | Authority |
|---|---|---|---|
| S0 Capture | Each finding is triaged against the repository and written in a fixed one-line shape in the story's log entry: `Q-<PR>-<n>`, claim type, `verified`, `decision`, reason, fix commit. Unknown fields read `unknown` | None (record keeping) | Human |
| S1 Episodes | The same records are registered as `Episode` metadata under a `TaskPolicy` `triage-review-finding`, declared and initialized idle, with actions `accept_and_amend`, `decline_with_reason`, `defer_to_human` | #3 reasoned resolution over a `DecisionFrame` (criteria such as verified-by-repository, blast radius, reviewer reliability) | `full`, `requires_human_approval: true` |
| S2 Reliability evidence | The frame's reviewer-reliability criterion is supplied by a confidence bound on the share of that reviewer's findings of that claim type that were verified. The SDK already computes the Wilson lower bound. With too few cases the criterion reports no evidence rather than a number | #9, #10 style bounds; #8 critique-to-evidence for the finding text | `full` |
| S3 Learned ordering | A separate `low`-authority softmax policy, `route-review-finding`, chooses only which finding to verify first and which verification to run, a low-impact reversible choice with no approval flag. It is considered when contrastive outcomes (verified and unverified findings) meet the declared tier's gate, through the ADR-003 gates and the ADR-005 progression check | #2 | `low`, gated |

At every stage the human decides whether a finding is accepted, declined or deferred, and the merge remains a human-withholdable action (Step 8). The loop recommends and records; it does not decide. `triage-review-finding` keeps `requires_human_approval: true` permanently, and under ADR-003 Invariant 6 that flag blocks every learned authorization path, so no trained policy ever accepts or declines a finding. S3 therefore learns only the ordering and routing of verification work, under its own policy. Historical comments (the 23 inline Q comments) may be backfilled only as `reconstructed` records whose `verified` and `decision` fields read `unknown` unless the repository history shows them; no outcome is guessed.

### 4.6 What This Does Not Decide
Per-methodology effectiveness, any change to a methodology's state in the Ideation Document, any new `LearningStore` record type, a `trace_id` on `Episode` (#25), and any autonomy for review decisions beyond ADR-003's gates.

---

## 5. Architectural Invariants
1. **Examples Are Not Evidence.** Every example is labeled synthetic and never changes a methodology's state or a hypothesis status.
2. **Class Follows State.** A catalog entry's class is derived from the state in Ideation §2.1; a mismatch is an error.
3. **No Import Into the SDK.** Nothing under `src/` imports from `examples/`.
4. **Adoption Needs Real Episodes.** A ledger practice is `adopted` only on `real-episodes` evidence meeting the tier gate.
5. **Append-Only Ledger.** Entries are never edited; a status change supersedes.
6. **Human Triage.** Every accept, decline and defer on a review finding is a human decision; the loop only recommends and records.
7. **No Invented Outcomes.** A record never guesses a field; `unknown` is valid. Backfilled records are marked `reconstructed`.
8. **Zero New Record Types.** Everything is a document or `Episode` metadata (ADR-002 Invariant #2).
9. **Progression Is Gated.** A learned `route-review-finding` policy follows ADR-003's gates and ADR-005 progression; this ADR grants no shortcut. `triage-review-finding` never leaves full authority with human approval.

---

## 6. Alternatives Considered
* **Alternative 1: Runnable examples for all 32.** *Rejected:* Blocked, excluded and declined methodologies have nothing honest to run, and sketches of candidates risk reading as evidence. The three classes keep the limits visible.
* **Alternative 2: Document the methodologies in prose only.** *Rejected:* This is the current state and does not let a reader run or falsify anything.
* **Alternative 3: Train a triage policy now.** *Rejected:* The data is small and almost entirely positive for Q; HYP-AL-002 shows REINFORCE cannot earn autonomy from it. Staging with reasoned resolution first uses what the data can support.
* **Alternative 4: Store triage decisions in a new record type.** *Rejected:* Violates ADR-002 Invariant #2; `Episode.metadata` suffices.
* **Alternative 5: Let the loop auto-accept high-reliability findings.** *Rejected:* Decline and accept decisions affect gates (ADR-001, ADR-008 Invariant #4), and the author who triages is also the author under review. ADR-003 Invariant 6 also makes a human-approval flag absolute.

---

## 7. Consequences

### Positive
* Each methodology gets a visible, runnable or explicitly documented entry, with limits stated.
* Practices accumulate in one ledger with an honest evidence class.
* The project begins to learn from its own build loop from the first triaged finding, at no cost in autonomy.

### Negative
* Authoring burden: 19 example directories and a fixed-shape record on every finding.
* Synthetic examples can still be misread despite the labels.
* Reliability evidence is weak at small counts; the loop reports "no evidence" until it has enough, which looks like inaction.

---

## 8. Open Questions & Future Extensions
1. Which complexity tier should `route-review-finding` declare (it sets the S3 gate)?
2. Whether the catalog's `state` should be generated from the Ideation Document to remove the copy.
3. Whether other reviewers (human peer review, other bots) join the same policy or get their own.
4. A `trace_id` on `Episode` (#25) would let a finding be linked to the commit that fixed it mechanically.
5. How the best-practice ledger relates to LL entries when a practice is also a process lesson.

---

## 9. Amendment Log

| Date | Change | Why |
|---|---|---|
| 2026-10-26 | Proposed | Initial drafting: example catalog, best-practice ledger, review-triage learning loop. |
| 2026-10-26 | **Accepted by Menno** | Formally adjudicated and accepted through `approve-adr`; robust utility 0.748, expected utility 0.816; Episode `f0047810-a3f2-49f4-8023-e3058fce3ed9`. |
