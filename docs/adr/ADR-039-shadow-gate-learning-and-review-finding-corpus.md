# ADR 039: Shadow-Gate Learning and the Review-Finding Corpus

## 1. Executive Brief
The approval and stage gates (the `approve-*` policies, `validate-intent-foundation`, `classify-diff-type`, `escalate-diff-response`) are all human-decided. Their episodes record what the human decided, but no learner is ever asked what it would have decided first, so nothing measures whether a learning method could advise at a gate.

This ADR decides two things:
1. **A shadow-gate contract.** Before the human decides at a gate, an advisory learner may record the verdict it would give. The human verdict is the label. Agreement is measured against the base rate. The learner never acts and never approves.
2. **A review-finding corpus.** The 223 Amazon Q findings already logged in the ADR-036 one-line shape are registered as `triage-review-finding` episodes (ADR-036 S1), classified as accepted, declined or deferred, and used as the first contrastive training data for shadow learners. Accepted findings against learner code are also recorded as improvements for those learners.

It adds no `LearningStore` record type (ADR-002 Invariant #2), grants no autonomy (ADR-001, ADR-003), changes no gate's authority, and changes no methodology's state in the Ideation Document (that goes through ADR-024).

---

## 2. Status
**Accepted (2026-11-09, Menno)** — Cross-cutting. Design only. Approval episode `6b98f377-9ab1-4290-91a1-0832546037ea`. Nothing in this ADR is built.

---

## 3. Context & Problem Statement
The counts below were produced on 2026-11-09 by reading `docs/policy-shapes/episodes/*.json` by `task_id`, and by running the project's own `review_triage.find_triage_lines` and `parse_triage_line` over `implementation-log.md` and `docs/**/*.md`. They are re-run when this ADR is adjudicated (Invariant 7).

- **Gates carry little data, and every label is an approval.** The 194 registered gate episodes include `approve-adr` 49, `approve-user-stories` 41, `approve-fdd` 38, `approve-brd` 36 and `approve-subsidiary-plan` 9. Every episode of those five policies records the approving action; none records a rejection or a revision request. Most other gates have one or two episodes.
- **A one-class history cannot test a learner.** A learner can score perfectly on these gates by always predicting "approve", so agreement says nothing about discrimination. This is the positive-only problem recorded as HYP-AL-002. Agreement must be judged against the base rate, as the ADR-021 agreement gate already does.
- **A shadow mechanism exists only for routing.** `shadow_record` and the agreement computation in `agent_learning_ext/routing.py` store `shadow_low_action` and `shadow_entropy_bits` in episode metadata for ADR-021. No other policy uses them.
- **The review-finding loop has no data in it.** ADR-036 (Accepted, Epic 36 Completed) declared `triage-review-finding` and `route-review-finding`, and `review_triage.py` parses the one-line records. No episode under `triage-review-finding` has been registered. The log holds 223 distinct `Q-<PR>-<n>` lines. The parser accepts 221 and rejects 2, which a human must read.
- **The logged findings are contrastive.** Of the 221 parsed: 162 accepted, 53 declined and 6 deferred. By verification: 136 verified and accepted, 24 partial and accepted, 2 not verified but accepted (contradictory rows), 33 not verified and declined, 13 verified but declined, 7 partial and declined, 4 verified and deferred, 2 partial and deferred. By claim type: logic error 111, test gap 45, crash risk 37, documentation 15, style 13. About a quarter are declined. This is the contrast the gate history lacks.
- **Exploration methods do not shadow-train as designed.** Thompson, UCB and epsilon-greedy (#9, #10, #11) earn their value by choosing actions. A shadow learner chooses none, so they reduce to posterior-mean predictors.

## 4. Decision

### 4.1 The shadow-gate contract
At a gate, an advisory learner may record, before the human verdict is shown to it, a plain dictionary in `Episode.metadata`:

| Key | Meaning |
|---|---|
| `shadow_learner` | learner identifier and methodology number (for example `thompson/9`) |
| `shadow_policy_version` | the policy version that produced the verdict |
| `shadow_action` | the action id the learner would have chosen |
| `shadow_probs` | the learner's action probabilities, when it has them |

`shadow_low_action` and `shadow_entropy_bits` from ADR-021 stay as they are. The human's recorded decision is the label. The contract adds no field to `Episode` and no record type.

### 4.2 Agreement is measured against the base rate
For each shadow learner and gate, report `n`, the agreement count `k`, the base rate and the modal action, using the ADR-021 computation. A learner "tracks the human" only if its agreement exceeds the modal-action base rate by a margin the FDD declares and meets the sample floor of the declared tier. The FDD declares the margin, the floor and the statistical rule. The rule uses the Wilson lower bound the SDK already computes (`autonomy.wilson_lower_bound`), so a small sample cannot pass on a lucky run. Alongside agreement, every report carries diagnostics: the confusion matrix over the gate's actions and, for each non-modal action, precision and recall. These are diagnostic. Agreement versus base rate stays the primary measure. Agreement is evidence for a person. It never promotes a learner by itself.

### 4.3 Preliminary assessment: which methodologies suit shadow training at a gate
This classification is a reading of the methodology catalog, the selection skill and the ADRs, not a review of each learner's code. It is advisory and is confirmed or corrected in the FDD after an implementation review. That review checks, for each methodology taken into the first shadow round, that its learner or policy can produce `shadow_action` and `shadow_probs` from the gate's inputs without changing its state.

| Group | Methodologies | Condition |
|---|---|---|
| Eligible with the gate data that exists | #2 REINFORCE, #3 reasoned resolution, #8 critique-to-evidence, #12 active evidence-seeking, #14 meta-prior, #15 warm-start, #17 routing, #22 weight compiler, #13 pairwise preference | #13 needs revision pairs recorded. #14 and #15 are the intended help for thin gates, but the shared-prior premise stays HYP-AL-008 until tested. |
| Eligible, but as posterior-mean predictors only | #9, #10, #11 | Whether they beat #2 on positive-only labels stays HYP-AL-009. |
| Needs a prerequisite first | #4 and #24 (a feature vector per gate), #28 (abstention threshold), #29 (logged action probabilities), #26, #30, #31, #32 | Each also needs its own ADR where none exists. |
| Not gate learners | #1, #7, #16, #18, #25, #27, #19, #20, #21, #23 | Excluded, not applicable, blocked or declined in the catalog, or already a gate, or a test of a gate. |

This table recommends nothing for any gate. A methodology enters shadow use for a gate only by a human decision recorded for that gate.

### 4.4 The review-finding corpus
1. **Register.** Each logged `Q-<PR>-<n>` line becomes an `Episode` under `triage-review-finding` through the existing `review_triage.py` parser and `to_episode_metadata`. A field the log does not show reads `unknown`. The episode is marked `reconstructed`. No outcome is guessed (ADR-036 Invariant 7). Each record also carries the review date and the repository revision (the fix commit where the log gives one), or `unknown`, so changes in standards over time stay visible when the corpus is read.
2. **Classify.** The label is the logged `decision`: accepted, declined or deferred. A row whose `verified` and `decision` contradict each other (for example `verified: no` with `accepted`) is listed for a human to read and is not used as a label until read.
3. **Rejections.** Declined findings are the negative class. The record keeps the reason and whether the claim was verified, because "false claim" and "true but not worth the change" teach different things.
4. **Improvements.** An accepted finding that names a module under `src/agent_learning` or `src/agent_learning_ext` is also listed against that module with its fix commit, so repeated defects in a learner are visible.
5. **Corpus health.** Before any learner is scored on the corpus, the tooling reports the contradiction rate, the share of rows with an `unknown` label field, and the number of usable labelled rows per action. The FDD declares the thresholds for each, with the reasons. If a threshold fails, evaluation does not start and the rows go back to a human to read.
6. **Retrospective evaluation.** The reconstructed corpus cannot satisfy Invariant 2, because every label already exists. It is therefore evaluated only by a time-ordered protocol: findings are ordered by PR number and then finding number, and a finding is scored by a learner trained only on findings that precede it. A learner is never trained and scored on the same record. Results are labelled `retrospective`, are reported apart from prospective agreement, and cannot alone support a decision about a gate. Prospective shadow verdicts on new findings (Step 8) are the only results that count as shadow-gate evidence.
7. **Training.** Shadow learners for `triage-review-finding` and `route-review-finding` may be trained on these episodes, subject to ADR-003 gates and ADR-005 progression. ADR-036 Invariant 9 stands: `triage-review-finding` keeps `requires_human_approval: true` and never leaves full authority.

### 4.5 The ritual
- **Step 8 of `implement-story`** records, for each new finding, the learner's shadow verdict next to the human triage, when a shadow learner is configured.
- **Gate reviews** record the shadow verdict before the human decides. The orchestrator and stage subagents continue to recommend and never approve.
- **Stage 18 and the recap session** report agreement versus base rate and reviewer reliability per claim type. Whether a gate stays manual is a human checkpoint decision, as already decided for the shadow phase.

### 4.6 Governance baseline
Until its acceptance the baseline guard (`tests/test_governance_baseline.py`, `scripts/governance_baseline.py`) did not fingerprint this ADR. Now that it is accepted, it, BRD-039, FDD-039 and its stories are fingerprinted, and every later change goes through Stage 16 (`classify-diff-type`, human acceptance, an episode in the amendment log). This ADR extends ADR-021 and operationalizes ADR-036 without amending either. If implementation turns out to need an amendment to either, that is a Stage 16 change of its own. Before the shadow-gate step is added to `implement-story` or to gate reviews, the guard test must pass on the branch.

### 4.7 What This Does Not Decide
Any change to a gate's authority or approval flag, any promotion of a learner, a `trace_id` on `Episode` (#25), the per-knowledge-area plan learners (their own ADR), and any methodology's state in the Ideation Document.

---

## 5. Architectural Invariants
1. **Shadow Never Acts.** A shadow verdict is recorded and never changes a decision, a gate outcome or a document status.
2. **The Human Verdict Is The Label.** For prospective shadow verdicts, a learner never sees the verdict it is scored against before it records its own. For the reconstructed corpus, the time-ordered protocol of §4.4 item 6 stands in for it, and its results are never counted as shadow-gate evidence.
3. **Base Rate Comes First.** Agreement is reported with the base rate and modal action. Raw agreement alone is not evidence.
4. **No Invented Outcomes.** Corpus records never guess a field. `unknown` is valid. Imported records are marked `reconstructed`.
5. **Gates Stay Human.** `requires_human_approval` is unchanged on every gate (ADR-003 Invariant 6). This ADR grants no shortcut under ADR-003 or ADR-005.
6. **Zero New Record Types.** Everything is `Episode` metadata or a document (ADR-002 Invariant #2).
7. **Verified Counts Only.** Any count in a document derived from this ADR comes from the tooling, not from hand-written numbers.
8. **Write Once.** Shadow metadata is written once by the tooling, before the human verdict is recorded, and is never edited afterwards. A correction is a new episode that references the old one.

---

## 6. Alternatives Considered
1. **Train directly on the approval gates only.** Rejected: the gate history is mostly approvals and small, so results would be uninterpretable.
2. **Let a learner auto-approve low-risk gates.** Rejected: contradicts the decided human-decide principle and ADR-003 Invariant 6.
3. **Backfill the corpus by re-reading the PRs.** Rejected: guesses fields the log does not show (Invariant 4).
4. **Amend ADR-036 instead of a new ADR.** Rejected: the shadow-gate contract spans all gates, not only review triage, and ADR-036 is Accepted.

## 7. Consequences
### Positive
- First contrastive training data in the project, drawn from work already done.
- One shared mechanism measures any method at any gate, so methods can be compared on the same footing.
- Repeated learner defects become visible per module.

### Negative
- More metadata on each gate episode and one more step in each gate review and Step 8.
- Some logged rows need a human read before use.
- Agreement on thin gates will stay inconclusive for a long time.

---

## 8. Open Questions & Future Extensions
Answered by Menno on 2026-11-09:
1. **Agreement margin and sample floor:** set per tier. The sample floors follow the autonomy tiers; the FDD declares one margin over the modal-action base rate.
2. **Improvements list:** a generated view computed from the episodes, grouped by module. It is never hand-edited.
3. **Other reviewers:** they share the single `triage-review-finding` policy, with the reviewer recorded on each episode. Reliability stays computed per reviewer and claim type.
4. **First shadow round:** #2 REINFORCE on `triage-review-finding` and `route-review-finding`; #8 critique-to-evidence at the ADR, BRD and FDD gates; #15 warm-start from the ADR gate to the BRD and FDD gates; #9 Thompson as a posterior-mean predictor against #2. This is a first-round choice, not a promotion of any learner.
5. **Off-policy evaluation (#29):** not a prerequisite for shadow runs. Base-rate agreement is enough to start; revisit when a learner is considered for promotion.

Still open: the numeric margin (FDD), and the exact fields that carry the reviewer on an episode.

---

## 9. Amendment Log

| Date | Change | Why |
|---|---|---|
| 2026-11-09 | Proposed | Initial drafting: shadow-gate contract and the review-finding corpus. |
| 2026-11-09 | Open questions answered | Menno answered all five open questions in chat; recorded in section 8. Status unchanged. |
| 2026-11-09 | Pasted external review assessed | Adopted: Wilson-bound rule and diagnostic metrics (§4.2), review date and revision on corpus records (§4.4), write-once shadow metadata (Invariant 8). Not adopted: the review's example numbers (50/100/250 samples, +10%, 95%, quarterly), because they have no evidence behind them and the tier floors were already decided; and the claim that reviewer reliability is undefined, because ADR-036 S2 and `review_triage.reliability` already define it. |
| 2026-11-09 | Self-critique and a second review assessed | Adopted: provisional counts note (§3), preliminary-assessment wording for §4.3, corpus-health gate (§4.4 item 5), time-ordered retrospective protocol and Invariant 2 scope (§4.4 item 6, Invariant 2), governance baseline section (§4.6, checked against `scripts/governance_baseline.py`). Not adopted: the review's example thresholds (5% and 20% contradiction), left to the FDD with reasons. That review added no findings beyond the five points raised by the author. |
| 2026-11-09 | Third review assessed | Adopted: the FDD's implementation review checks that each first-round learner can emit a shadow verdict without changing its state (§4.3). Not adopted: the 5% contradiction example (FDD decides), and the suggestion to queue updates to `scripts/governance_baseline.py`, because the script is run after a Stage 16 change and is never edited for a new ADR. |
| 2026-11-09 | Fourth review assessed | Nothing new adopted. Already covered: the time-ordered protocol (§4.4 item 6) and the compatibility check (§4.3). The compatibility test it proposes is an FDD or story matter. Not adopted: the 5% quarantine rule and a new `corpus_status` field (no evidence, and a new field); and an "automatic" Stage 16 registration and baseline-script edit on approval, which contradicts the rule that a human accepts every Stage 16 change and that the manifest is never edited by hand. |
| 2026-11-09 | Fifth review assessed | Nothing adopted. Already covered: the prospective versus retrospective split (§4.4 item 6, Invariant 2), the corpus-health gate, the preliminary wording of §4.3 and the baseline step (§4.6). Not adopted: label confidence tiers that drop declined-despite-verified rows from official metrics (this removes the negative class), a fixed review cadence (arbitrary), confidence ratings on the §4.3 table (no evidence behind them), and a checklist naming a "policy registry" and "shadow metrics registry" that do not exist in the repo. |
| 2026-11-09 | **Accepted by Menno** | Formally adjudicated and accepted through `approve-adr`; robust utility 0.670, expected utility 0.751; Episode `6b98f377-9ab1-4290-91a1-0832546037ea`. The support values in the decision frame are the author agent's own judgments, not a separate reviewer's. |
