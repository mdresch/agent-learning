# Business Case — agent-learning SDK: Closing the Methodology Gap

# Executive Summary & Metadata Block

| Field | Value |
|---|---|
| Document Title | Business Case — agent-learning SDK: Closing the Methodology Gap |
| Version | 1.4 |
| Date | 2026-10-21 |
| Status | Draft |
| Author | This session, building directly on `docs/project-docs/Ideation-Document.md` v1.4 |
| Approver(s) | Not yet assigned — open-source maintainer review model, per Ideation §3.3 |
| Source | `Ideation-Document.md` §2.1/§2.1.1 (22-methodology landscape, cross-checked against 7 real external agent SDKs) and §2.2 (hypotheses), `docs/templates/business-case-template.md`, this session's own real `TaskPolicy` build history, one round of external review (applied selectively — see Provenance), and real cross-framework research closing the §9 competitive-positioning gap |

This Business Case does not argue for adopting `agent-learning` — that
decision is already made; the SDK is in real use against SocialEngage.
It argues for a specific next step: **which of the Ideation document's
seven genuine, not-yet-built methodology candidates (§2.1, rows #8–11,
#13–15, #17) should actually be built**, and why building on top of the
existing SDK rather than routing around it with more hand-built
`full`-authority workarounds is the right call.

**Value proposition, stated plainly (added on review — the mechanism
description below was burying it):** the adopter-facing pitch is not
"REINFORCE-with-baseline over discrete actions." It is **earned autonomy
with explicit statistical and evidential justification** — a decision
only runs unsupervised once it has cleared a named, inspectable bar, and
every such decision traces to the specific evidence that cleared it.
Everything below is in service of that pitch, not a replacement for it.

---

# 1. Problem Statement & Root Cause Analysis

Across six real `TaskPolicy` builds this session, three concrete,
recurring problems surfaced that the packaged SDK (`SoftmaxPolicy` +
`ReinforceLearner` for `low` authority, `DecisionResolver` for `full`)
does not address:

1. **Rich textual feedback is generated and then discarded.** ADR-0146's
   governance review alone produced eleven dated, substantive amendments
   across two rounds. That critique exists in the Obsidian vault today,
   fully legible to a human, and is invisible to every `TaskPolicy` in
   the SDK — REINFORCE only consumes a scalar reward, never the reasoning
   behind it.
2. **Every new policy starts from zero, even when near-identical policies
   already exist.** `validate-intent-foundation`, `approve-adr`,
   `approve-brd`, `approve-fdd`, `approve-story`, and
   `choose-repository-search` were all cold-started from a uniform prior
   this session, despite sharing the same accept/reject/escalate
   structure. Nothing in the SDK lets a new policy start from what a
   structurally similar one already learned.
3. **A provably stuck low-authority decision has no packaged repair path
   other than switching authority mode entirely.** HYP-AL-002
   (Ideation §2.2) proved `validate-intent-foundation` mathematically
   cannot cross its autonomy gate on positive-only data under REINFORCE.
   The real fix this session used was abandoning the bandit and
   migrating to `full` authority — which worked, but only because that
   decision happened to also be genuinely per-instance-varying. A
   decision that is genuinely stable but simply has *sparse or skewed*
   evidence has no packaged escape hatch at all.

Root cause, common to all three: the SDK's only learning mechanism is a
single, fixed-form policy-gradient bandit. Every gap above is a case
where a *different* learning methodology — not a bigger one — would fit
the real decision shape better.

---

# 2. Gap Analysis Matrix

| Dimension | Current state (packaged, real) | Desired state | Gap |
|---|---|---|---|
| Learning from textual critique | Discarded; only scalar reward feeds REINFORCE | Critique converts into `DecisionFrame` evidence or pairwise preference data | Methodologies #8, #13 (Ideation §2.1) — not built |
| Cold-start cost for a new policy | Every policy starts from a uniform prior | A new policy can inherit priors from a structurally similar converged policy | Methodologies #14, #15 — not built |
| Repair path for a stuck low-authority decision with *sparse*, not per-instance-varying, evidence | Only escape hatch is switching to `full` authority | A sample-efficient bandit variant (confidence-interval-based, not gradient-based) resolves it without changing authority model | Methodologies #9, #10, #11 — not built |
| Routing between `low` and `full` authority | Fixed once, at `task-policy-init` time | Chosen per-instance, automatically, when a decision's shape genuinely varies | Methodology #17 — not built |

---

# 3. Proposed Solution Options & Solution Integrity

Three real candidate build targets, each addressing one gap-cluster
above, scored against the status quo of continuing to route around gaps
by hand.

## Weighted Decision Criteria Table

| Criterion | Weight | A: Warm-start / transfer of priors (#14–15) | B: Critique-to-evidence + DPO pairwise (#8, #13) | C: Thompson sampling / UCB (#9–11) | D: Status quo (hand-rolled workarounds) |
|---|---|---|---|---|---|
| Problem severity | 0.30 | 3 | 4 | 5 | 1 |
| Evidence readiness (real, *usable* session data exists now) | 0.25 | 4 | 3 | 3 | 5 |
| Implementation complexity (5 = simplest) | 0.20 | 5 | 1 | 4 | 5 |
| Strategic fit (frozen-model / CPU-only / auditable) | 0.15 | 5 | 3 | 5 | 3 |
| Redundancy risk (5 = no workaround exists today) | 0.10 | 3 | 5 | 2 | 1 |
| **Weighted score** | | **3.95** | **3.10** | **4.00** | **3.10** |

**Revised on external review** (v1.0 originally scored B=4.10, highest;
C=3.70, third) — kept here as the current, corrected basis rather than
silently overwritten:
- **Problem severity** originally conflated two different claims under one
  score. B's gap (critique discarded) is a real *opportunity cost* —
  nothing has actually failed because of it. C's gap (the entropy
  ceiling) is the one failure in this entire document that is
  **mathematically proven**, not inferred (HYP-AL-002, a live training
  run that plateaued and then declined). A proven failure outranks an
  unexploited opportunity; scores corrected accordingly (B 5→4, C 4→5).
- **Evidence readiness** for B was overstated. "Real data exists" is true
  of the raw ADR-0146 amendment text, but that text is not yet a
  validated pairwise-preference dataset — turning free-form critique
  into usable `(preferred, rejected)` pairs is itself unproven work, not
  a given. Score corrected (B 5→3).
- **Implementation complexity** for B is corrected from 2 to 1 based on
  three concrete risks surfaced on review and now named in §6: critique
  severity is not uniform and has no weighting scheme; preference pairs
  extracted from review text have no established quality bar; and the
  only real source data (ADR governance review) risks training toward
  documentation-review patterns specifically rather than generic agent
  decisions.
- **A** is unchanged — it requires no new math, only reading out and
  reusing a converged policy's existing internal state (contingent on the
  §7 dependency check, still unverified).
- **D** is unchanged — not "free," since every future adopter who hits
  gaps #1–#3 pays the hand-rolling cost again; it scores respectably only
  because nothing new has to be validated to keep doing it.

**Net effect: A and C are now effectively tied for first (3.95 vs. 4.00,
a single-point swing in either direction reorders them — see §6), and B
has dropped to a tie with the status quo.** This reverses the original
recommendation; see §10.

## Solution Integrity Trade-offs

- **Choosing A and C as the primary pair** means deferring the one gap
  (textual critique discarded) that is arguably the most *interesting*
  long-term direction, and the one this project's own
  `experiential-reinforcement-learning-comparison.md` already names as
  the SDK's explicit boundary against ERL. Deferring it is not rejecting
  it — see §10 — but it does mean the "closes the ERL gap" story stays
  untold a while longer.
- **Not choosing B now** is the direct, corrected consequence of §3's
  revised scoring: its complexity was understated and its evidence
  readiness was overstated in the original pass. Building it before
  preference-data quality and a critique-weighting scheme exist would be
  building on an unproven foundation, not a shipped capability.
- **A and C being nearly tied** (3.95 vs. 4.00) means this document
  should not oversell confidence in their exact order — seeing them as a
  paired first phase, not a strict 1-then-2, is the more honest reading
  of a one-point-sensitive result (§6).
- **Rejecting D outright** would be dishonest — it has served every real
  decision this session needed, including the ones now motivating A and
  C. The case against D is about marginal cost to *future* adopters, not
  a claim that it has failed anyone yet.

---

# 4. Hypothesis & Expected Value Premise

Per the template's own instruction, every option still in real
contention after §3's revision (A, B, C) carries a stated, falsifiable
premise — B's is carried forward even though it is now deferred, since
"deferred" is not "rejected" (§10).

| Field | HYP-AL-005 (Ideation §2.2 — Option B, deferred) | HYP-AL-008 (Ideation §2.2 — Option A) | HYP-AL-009 (new — Option C) |
|---|---|---|---|
| **Type** | ValueHypothesis | FeasibilityHypothesis | TechnicalHypothesis |
| **Statement** | ERL-style experience-reflection-retry learning would converge faster or more sample-efficiently than REINFORCE on decisions where textual feedback is already available. | Seeding a new `TaskPolicy`'s initial state from a converged, structurally similar existing policy reduces the episodes needed to reach autonomy-eligibility, compared to a cold uniform start. | A confidence-interval-based bandit (Thompson sampling or UCB) can cross the same autonomy gate that defeated REINFORCE under positive-only evidence (HYP-AL-002), without migrating the decision to `full` authority. |
| **Expected value premise** | Converts eleven currently-wasted ADR-0146 amendment texts into usable training signal at near-zero marginal data-collection cost — the data already exists, though its usability is itself unproven (§3, §6). | Reduces the ~200-episode cold-start cost seen on `choose-repository-search` for any future structurally similar policy — the six policies built this session are the first real warm-start source set. | Provides a packaged repair path for a "stable-but-sparse" decision, closing the one gap in §2 that currently has no fix other than switching authority mode entirely. |
| **Falsification criteria** | If a reflection-based update path, implemented and run on the same real ADR-0146 episode data, does not converge faster/more sample-efficiently than REINFORCE, invalidated. | If a policy warm-started from a converged source reaches its autonomy gate in the same or more episodes than an equivalent cold-started policy, invalidated. | If Thompson/UCB, run against the same real `validate-intent-foundation` 146-episode dataset that defeated REINFORCE, also fails to cross the gate, invalidated — the failure would then be inherent to positive-only evidence itself, not specific to REINFORCE's entropy-bonus mechanics. |
| **Validation method & timeline** | Implement the reflection path; re-run against ADR-0146's real two-round critique; compare episode-count-to-gate against the existing REINFORCE baseline. Deferred per §10 — not scheduled until Phase 3. | Warm-start a new policy (candidate: a 7th structurally-similar TaskPolicy, not yet built) from `approve-adr`'s converged state; compare its episode-count-to-gate against `approve-adr`'s own original cold-start curve. Scheduled Phase 1. | Implement a Thompson-sampling or UCB policy class; re-run it against `validate-intent-foundation`'s real stored episode history; compare against the REINFORCE result already on record (plateau ~0.417). Scheduled Phase 2. |
| **Status** | **Formulated** (unchanged by this document) | **Formulated** (unchanged by this document) | **Formulated** — new this document, added directly in response to the external review's strongest point |

---

# 5. Financial Architecture & Cost-Benefit Analysis

**Named mismatch, not forced ceremony:** `agent-learning` is an
open-source SDK with no budget, revenue, or currency exposure of its own
— there is no real discount rate, inflation assumption, or cost figure to
source honestly for this initiative. Inventing plausible-looking dollar
figures here would fabricate the one thing this document's entire
discipline (cross-session, this document and Ideation alike) has
deliberately avoided: real, sourced evidence over speculative claims.

In place of monetary NPV/ROI, cost-benefit is expressed the same way §3's
weighted matrix already does — ordinally, in engineering-effort and
problem-severity terms, which *are* real and sourced (from this session's
own build history):

| Option | Cost proxy (implementation complexity, inverse of §3 score) | Benefit proxy (problem severity × evidence readiness, §3 scores) |
|---|---|---|
| A | Low (5/5) | Medium (3 × 4 = 12) |
| B | Very high (1/5) | Medium (4 × 3 = 12) |
| C | Medium (4/5) | High (5 × 3 = 15) |

C now carries the highest benefit proxy at a moderate cost; A carries an
equal-lowest cost at a comparable benefit; B now carries the same
benefit as A at roughly five times the cost — the quantitative
restatement of §3's revised weighted score.

---

# 6. Multi-Dimensional Sensitivity & Risk Taxonomy

## Financial Sensitivity (reframed as complexity/severity sensitivity, per §5)

With the revised §3 scores, A (3.95) and C (4.00) are separated by a
single weighted point — testing that margin matters more now than
testing B's already-corrected score:

- If C's complexity turns out one point worse than estimated (4→3, e.g.
  a Thompson/UCB class takes longer to integrate with the existing
  storage backends than expected): 0.30(5) + 0.25(3) + 0.20(3) + 0.15(5)
  + 0.10(2) = **3.80**. A (3.95) overtakes C.
- If A's strategic-fit score turns out one point worse (5→4, e.g. the §7
  dependency check reveals `SoftmaxPolicy`'s internal state is not
  cleanly reusable without a wrapper that weakens auditability): 0.30(3)
  + 0.25(4) + 0.20(5) + 0.15(4) + 0.10(3) = **3.80**. C (4.00) stays
  ahead.

**Neither ranking survives a single one-point swing in the other's
favor.** The honest reading is that A and C are a tied first phase, not
a strictly ordered 1-then-2 — reflected in §10's roadmap, which now
treats them as a paired phase rather than insisting on a sequence
between them.

## Qualitative Risk Taxonomy

| Risk | Option | Severity |
|---|---|---|
| Critique severity is not uniform and has no weighting scheme — "fix a typo" and "the architecture is wrong" would be treated identically by a naive extraction | B | High — identified on external review, not in the original pass |
| Raw review/amendment text has no established quality bar as a `(preferred, rejected)` pairwise-preference pair; extraction itself is unproven work | B | High — identified on external review; this is why evidence-readiness was corrected down in §3 |
| The only real source data (ADR governance review) risks training toward documentation-review patterns specifically, not generic agent decisions | B | Medium — a domain-lock-in risk named on external review |
| A converged-but-wrong prior silently propagates across every policy warm-started from it, compounding a single bad cold-start into many | A | Medium — mitigated if warm-starting only copies the *shape* of the prior, not blind trust, but this is a design choice not yet made |
| Red-team-generated DPO pairs encode this session's own authorship bias in what counts as a "better" response, rather than a general preference signal | B | Medium — the red-team methodology was designed for *testing* discrimination, not for generating a representative preference distribution |
| Thompson/UCB's confidence-interval math, while more auditable in principle, has not actually been validated against a real stuck-decision dataset this session | C | Medium — promoted from Low; C is no longer a deferred option, so this gap matters more now |

---

# 7. Transition State & Dependency Architecture

## Transition State Profile

Not applicable in the usual legacy-system sense — every candidate option
is net-new capability alongside the existing packaged bandit and
resolver, not a replacement for either. Nothing currently in production
is being transitioned away from.

## Dependency Matrix

| Option | Depends on | Status |
|---|---|---|
| A (warm-start) | `SoftmaxPolicy` exposing its converged internal state (logits/weights) in a form that can be read out and passed back in as a new policy's initial state | **Unverified this session — flagged, not assumed.** Must be confirmed against the real class before committing to Option A. |
| B (critique-to-evidence + DPO) | The existing pluggable reward-shaping interface (Ideation §1.1, item 4) that already supports optional Azure AI evaluators | Verified — this interface is real and packaged today |
| C (Thompson/UCB) | A new policy class parallel to `SoftmaxPolicy`; depends on nothing already built beyond the existing `Episode`/storage-backend contracts | Verified — storage/episode contracts are stable and already used by six real policies |

## Legacy Decommissioning Checklist

Not applicable — nothing is being decommissioned.

---

# 8. Stakeholder Governance & Change Strategy

Reuses the real stakeholder register already established in
`Ideation-Document.md` §3.1 rather than re-deriving a parallel one.

## Stakeholder Influence/Interest Matrix

| Stakeholder | Influence | Interest in this initiative specifically |
|---|---|---|
| Microsoft (maintainer org) | High | Decides whether any of A/B/C ships in the real package |
| SDK adopters / agent builders | Low (individually), High (collectively) | The actual beneficiaries of closing gaps #1–#3 — currently paying the hand-rolling cost this initiative removes |
| The human adjudicating a tie-break or escalation | Medium | B directly changes what evidence they're shown; A and C don't change their role |

**Named gap, not filled with invention:** external review correctly
flagged "SDK adopters / agent builders" as too coarse — real,
differentiated personas (e.g., a platform team that mainly needs
auditability vs. a workflow-automation team that mainly needs escalation
learning) plausibly exist. But no user interviews, issue-tracker pattern
analysis, or adoption telemetry exist this session to back any specific
persona split with real evidence. Writing one in now would repeat the
exact mistake this document otherwise avoids — a plausible-sounding but
unsourced claim. This is flagged as real future work, not done here.

**Narrowed, not closed, in `Project-Charter.md` §5:** one real tier of
end user — the downstream beneficiary whose decisions the governed agent
actually serves — is now named with genuine evidence (this session's own
SocialEngage governance case), distinct from inventing four speculative
market personas. Whether adopters would *pay* for a service layer built
on top is now **HYP-AL-011** (Ideation §2.2), explicitly Formulated, not
Validated — the willingness-to-pay question remains as open as the
persona-breadth question above.

## RACI Accountability Matrix — Deployment & Adoption Milestones

[Same gap already named in Ideation §3.3 — this remains an open-source
repo with maintainer PR review, not a staffed rollout with a formal RACI.
Not re-invented here for the same reason.]

## Stakeholder Validation Protocol

None exists today beyond ordinary PR review — named honestly rather than
assumed into existence.

---

# 9. Requirements Traceability & Success Matrix

| Requirement / Objective (traced to) | Option(s) that advance it | Evidence this session | Status |
|---|---|---|---|
| Ideation §1.2 Objective 4 — close the gap between example-only and packaged contextual learning | Indirectly, A and C (both would establish a second packaged learner class alongside the contextual bandit) | `ContextualSoftmaxPolicy` confirmed example-only, never exported | **Not met** |
| Ideation §1.2 Objective 5 — honest comparison across all learning variants | This document itself, plus Ideation §2.1 | 21-methodology landscape survey completed | **Met** — as of this document |
| HYP-AL-002's implied requirement — a packaged repair path for a stuck low-authority decision that isn't genuinely per-instance-varying | C | `validate-intent-foundation`'s entropy-ceiling proof | **Not met** — only the `full`-authority workaround exists today |
| No existing Ideation objective covers "convert textual critique into training signal" | B | ADR-0146's eleven real amendments | **Gap named, not yet an Objective** — this Business Case is the first document to state it; a future Ideation revision should add it explicitly rather than leaving it implicit here only |
| No existing document positions `agent-learning` against other agent frameworks (LangGraph, AutoGen, Semantic Kernel, CrewAI, OpenAI Agents SDK, DSPy, Haystack) | None at v1.1 | **Closed at v1.2** — real, cited research now exists, see `Ideation-Document.md` §2.1.1 | **Met.** Finding: five of seven frameworks (LangGraph, Semantic Kernel, OpenAI Agents SDK, Haystack, and partially AutoGen's non-experimental features) ship no real learning mechanism — `agent-learning`'s core differentiator (earned autonomy with auditable statistical/evidential justification) is not matched by any of them. AutoGen's experimental Task-Centric Memory and CrewAI's `crew.train()` are real but map onto methodologies this project already has (#7/#8, #6). DSPy's offline scored-search compilation is genuinely distinct and is now methodology #22 — a real candidate for optimizing `DecisionResolver`'s hand-set criteria weights (HYP-AL-010), not a competitive threat to the core autonomy-gating value proposition. |

---

# 10. Strategic Recommendation & Implementation Roadmap

**Recommendation, revised on external review:** Build **Option A
(warm-start) and Option C (Thompson/UCB) as a tied first phase**, and
**defer Option B (critique-to-evidence + DPO) to a later phase**, not
rejecting it. This reverses the original v1.0 recommendation. The
reversal is driven by a real correction, not just a differing opinion:
B's original "problem severity" score conflated an unexploited
opportunity with C's gap, which is the only *mathematically proven*
failure in this document (HYP-AL-002). Once that conflation was
corrected, and B's evidence-readiness/complexity scores were corrected
to reflect that raw critique text is not yet a validated
preference-pair dataset, B no longer wins the weighted analysis (§3).

1. **Phase 1 (tied) — Option A (warm-start) and Option C
   (Thompson/UCB).** A is contingent on the §7 dependency check
   (`SoftmaxPolicy`'s internal state must actually be reusable). C is
   contingent on nothing already built. §6's sensitivity shows a single
   point separates them either way, so treat both as Phase 1 rather than
   forcing a false order between them. Validates HYP-AL-008 (A) and the
   new HYP-AL-009 (C) — HYP-AL-009 is the more consequential test, since
   it directly re-attempts the one decision REINFORCE is *proven* unable
   to resolve (HYP-AL-002).
2. **Phase 2 — Option B (critique-to-evidence + DPO) — deferred, not
   rejected.** Real value remains if the ERL-adjacent gap is ever closed
   (HYP-AL-005 stays Formulated), but building it now would be building
   on an unproven foundation per §6's newly-named risks (no
   critique-weighting scheme, no validated preference-pair quality bar,
   domain-lock-in risk to ADR-review patterns specifically). Revisit once
   those three risks have concrete mitigations, not on a fixed timeline.
3. **Two real gaps are explicitly not closed by this roadmap**: user
   personas (§8) and competitive positioning (§9) were both flagged on
   external review as missing, and both are left as named gaps rather
   than filled with unsourced claims. Closing them requires real
   research (user evidence; actually reading competing frameworks'
   docs), not another editing pass on this document.

This recommendation depends on HYP-AL-008 and HYP-AL-009 both resolving
to **Validated** before Phase 1 is considered complete — an
**Invalidated** result on either should trigger a re-scoring of §3's
matrix with the real (not estimated) numbers, not a silent continuation.

**Formalized at `Project-Charter.md` v1.0** — Phase 1 (Options A and C)
now has named resource requirements, a stakeholder register, and an
explicit resourcing gate before Phase 2 (Option B) may consume further
contributor/research time, rather than this recommendation remaining a
document-only conclusion.

---

## Provenance & Completeness Self-Assessment

| Field | Status |
|---|---|
| Problem Statement (§1) | Sourced directly from this session's own six real `TaskPolicy` builds, not speculative |
| Gap Analysis (§2) | Each row traced to a specific Ideation §2.1 methodology row number |
| Weighted scoring (§3) | Scores are this document's own first-pass judgment, not measured data — named as such, not disguised as empirical. **Revised once** (v1.1) after external review identified a real conflation in the "problem severity" criterion between B (opportunity cost) and C (proven failure); the correction was re-derived from this document's own evidence standards, not accepted on authority |
| Hypotheses (§4) | Two cross-referenced from Ideation (HYP-AL-005, HYP-AL-008, unchanged), one new (HYP-AL-009, added directly from external review's strongest point) — none yet tested |
| Financial Architecture (§5) | **Explicitly substituted** — no real budget/currency exists for this open-source SDK; ordinal effort/severity proxies used instead, and the substitution is named rather than hidden behind fabricated dollar figures |
| Dependency Matrix (§7) | One real dependency (Option A on `SoftmaxPolicy`'s exposed state) explicitly flagged **unverified** rather than assumed |
| Requirements Traceability (§9) | One row remains a named gap rather than force-filled: "convert critique into training signal" (no Objective covers it). The competitive-positioning row, left open at v1.1, is **closed at v1.2** with real cited research rather than left unsourced indefinitely — the difference between naming a gap and leaving it unaddressed |
| External review (v1.1 revision) | Applied **selectively**: re-scoring (§3), new risks (§6), new hypothesis (§4 HYP-AL-009), and value-proposition framing were accepted because they were either re-derivable from this document's own evidence or low-risk framing; four detailed user personas were declined (still open) because accepting them as written would have meant asserting unsourced claims as fact |
| Cross-framework research (v1.2) | Two research agents, real citations per framework (not guessed) — see `Ideation-Document.md` §2.1.1 for the full per-framework findings this document's §9 row summarizes |
