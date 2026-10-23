# Benefits Management Plan — agent-learning Phase 1

**Version:** 1.1
**Date:** 2026-10-21
**Status:** Draft — retrofitted, not a true pre-Charter input
**Source:** `docs/project-docs/Ideation-Document.md` v1.8, `docs/project-docs/Business-Case.md` v1.4, `docs/project-docs/Project-Charter.md` v1.5, and PMBOK® Guide 8th Edition §2.1 (Governance Performance Domain), per excerpts the user supplied directly
**Revision (v1.0 → v1.1):** incorporates two external governance reviews, each checked against the real source chain (Ideation §2.2/§3.1, Project-Charter.md §7) before acceptance — findings were not applied wholesale. See "External Review Disposition" near the end for what was accepted, corrected, or rejected, and why.

---

**Named honestly before anything else:** per PMBOK 8's own Figure 2-3
("Initiate Project or Phase Inputs"), a Benefits Management Plan is
listed as an **input** to project/phase initiation, alongside the
Business Case — meaning it's supposed to exist *before or alongside*
the Charter, not after it. This document was not built in that order;
`Project-Charter.md` was approved first. This is a **retrofit**,
consolidating value content that was already scattered across three
documents (Ideation §2.2, Business Case §4–5, Charter §5) into the
dedicated artifact PMBOK 8 says should have come first. The process
rule going forward, stated explicitly so it isn't lost: **future
projects draft the Benefits Management Plan before or alongside the
Charter, not after.**

---

## 1. Target Benefits

### 1a. Confirmed / Evidence-Based Benefits

Pulled from where they already existed, not invented fresh. **Beneficiary**
is new in v1.1, populated from Ideation §3.1's existing Stakeholder
Register — no new stakeholder category is invented to fill it:

| Benefit | Beneficiary | Source | Tied to |
|---|---|---|---|
| Fewer total manual reviews across the system's lifetime, compounding each time a new governance decision type is introduced | The human adjudicating `low`/`full`-authority tie-breaks (Ideation §3.1) | Charter §5, End-User Value Analysis (Option A) | HYP-AL-008 |
| A packaged repair path for a decision class currently **impossible** to automate, not just slow to automate | SDK adopters / agent builders (Ideation §3.1) — not the decision mechanism itself, which has no standing to benefit | Charter §5, End-User Value Analysis (Option C) | HYP-AL-009, closing the gap HYP-AL-002 proved real |
| Lower integration friction for every future policy an adopter builds | SDK adopters / agent builders (Ideation §3.1) | Charter §5 | HYP-AL-008 |
| **Real second case beyond SocialEngage**: a static, unlearned provider-priority ranking (ADPA's `ai_generation_jobs` AI-provider selection) could become a real UCB/Thompson bandit, using cost/latency/success data already logged with no mechanism to learn from it | SDK adopters / agent builders (Ideation §3.1) — operationally, whoever currently hand-maintains ADPA's static provider-priority ranking | Charter §7, M0.5 Research Log | HYP-AL-009, and the unpackaged contextual-bandit gap (methodology #4) |

Quantification of these benefits (hours avoided, review-count reduction,
etc.) is deliberately deferred, not invented: real episode counts exist
only from M2 onward (§4), and backfilling order-of-magnitude estimates
ahead of that data would be exactly the kind of guess this registry has
avoided everywhere else (Ideation §2.2, Business Case §1/§7).

### 1b. Potential Strategic Benefits (Not Yet Validated)

Kept in a separate table so a governance review doesn't have to infer
which benefits are evidenced and which are targets:

| Benefit | Prospective Beneficiary | Source | Tied to |
|---|---|---|---|
| A possible new revenue-adjacent benefit — a hosted governance-as-a-service layer adopters would pay for, distinct from the free OSS SDK | Prospective hosted-service customers — **not a stakeholder in Ideation §3.1's register today**; would only become one if HYP-AL-011 validates | Charter §5 | HYP-AL-011 — **not yet validated, named as a target, not a claim** |

## 2. Strategic Alignment

Ties directly to the three real gaps named in Business Case §1 (textual
critique discarded; every new policy cold-starts from zero; a stuck
low-authority decision has no repair path short of an authority-mode
migration). This is not alignment to an abstract organizational
strategy — `agent-learning` has no portfolio/program layer above it —
it's alignment to the specific, evidenced problems this session's own
real `TaskPolicy` builds surfaced.

## 3. Benefit Owner

Per PMBOK 8 §2.4.6/2.4.7's framing (project sponsors typically own
benefits realization and secure resources): **Menno**, the same role
already named as Sponsor in Charter §12. No separate owner exists or is
being invented — this project has one person, and PMBOK's own framing
doesn't require more than that.

**Ownership does not end at delivery.** PMBOK 8 §2.4.6/2.4.7 frames
benefits realization, not just delivery, as the sponsor's
responsibility, so Menno's ownership of §1's benefits continues through
**M5** and any post-phase operational validation (e.g. confirming
HYP-AL-009's unstuck decision class still holds up in continued real use
after the M4 re-test) — not a new obligation, just stated explicitly
rather than left to default at the project's formal close.

## 4. Timeframe for Realization

Tied to the Charter's own milestones, not a new timeline:

| Benefit | Realized by | Measured at |
|---|---|---|
| HYP-AL-008's benefit (cold-start reduction) | M2/M4 | Episode-count-to-gate comparison, warm-started vs. cold-started |
| HYP-AL-009's benefit (unstuck decision class) | M3/M4 | `validate-intent-foundation`'s real stored history, re-tested |
| HYP-AL-011's benefit (willingness to pay) | M0.5 | Go/No-Go decision, 40-hour time-box |

## 5. Metrics for Measuring Realization

Deliberately reusing the falsification criteria already defined for
each hypothesis (Ideation §2.2), not inventing parallel metrics that
could drift out of sync with them:

- HYP-AL-008: warm-started episode-count-to-gate **strictly less than**
  an equivalent cold-started policy's — the same comparison its own
  falsification criteria already specify. "Equivalent" is defined
  operationally rather than left implicit: same `TaskPolicy`
  architecture, action count, and authority tier, evaluated against the
  same autonomy-gate thresholds and the same evaluation episode stream —
  only the initial state (warm vs. cold) differs between the two runs
  being compared. No fixed numeric target (e.g. a percentage reduction)
  is set, consistent with Ideation §2.2's own relative, not
  absolute-threshold, falsification criteria for this hypothesis.
- HYP-AL-009: Thompson/UCB crosses the autonomy gate that defeated
  REINFORCE on `validate-intent-foundation`'s real stored history.
- HYP-AL-011: a real prospective contact's response to being asked
  directly, or a real price-point test — not a proxy metric.

## 6. Assumptions and Risks to Benefit Realization

Pulled from Charter §8/§10 rather than restated independently:

- If M1 resolves "No" (§7's `SoftmaxPolicy` dependency), HYP-AL-008's
  benefit may not be realizable as scoped — Charter §7's disposition
  table already governs this branch; this plan doesn't duplicate it.
- If M0.5 resolves "No-Go," HYP-AL-011's benefit is not realized under
  this phase, but the six real policies already built this session
  deliver real value regardless — the benefit statement for HYP-AL-011
  is explicitly contingent, not assumed.
- Option C's confidence-interval math is unvalidated against a real
  stuck-decision dataset until M4 — named in Business Case §6, not
  re-litigated here.

## 7. Potential Disbenefits

New in v1.1. Not previously named anywhere in the
Ideation/Business-Case/Charter chain — checked directly, no
disbenefit-equivalent language exists in any of the three documents.
Each entry below is tied to a monitoring mechanism this project already
has, not a new one invented for this purpose:

| Disbenefit | Monitoring Method |
|---|---|
| Increased compute/decision cost from running a second learning mechanism (UCB/Thompson) alongside REINFORCE | Cost-per-decision, using the same cost/latency logging §1a already cites as existing in ADPA's `ai_generation_jobs` |
| Reduced explainability if a confidence-interval bandit's choice diverges from what the hand-coded authority-tier escalation would have produced | Spot-check at the **M4** benefits review already defined in §8 — not a new review cycle |
| Warm-starting (HYP-AL-008) adds overhead instead of removing it, if §7's `SoftmaxPolicy` converged-state-exposure dependency (Charter §7, flagged open, not yet confirmed) resolves "No" | The same episode-count-to-gate comparison already defined in §5 doubles as this disbenefit's trip-wire — a warm start taking *more* episodes than cold-start is the failure signal |

## 8. Benefits Tracking Approach

Per PMBOK 8 §2.1.6.7 (Monitor and Control Project Performance), which
lists *"assessing whether project deliverables are on track to deliver
planned benefits"* as an ongoing governance activity, not a one-time
check: this plan's own benefits (and, as of v1.1, disbenefits) are
reviewed at **M4** (both hypotheses re-tested against real data) and
**M5** (Phase 1 review) — the same two checkpoints the Charter already
defines, not a third parallel review cycle invented for this document.

---

## External Review Disposition

Two external governance reviews of v1.0 were received and checked
against the real document chain (Ideation §2.2/§3.1, Project-Charter.md)
before any change was made — findings were not applied wholesale:

| Finding | Disposition |
|---|---|
| Gap: missing baseline measures | **Accepted the observation, rejected the proposed fix.** Checked Ideation §2.2: all three hypotheses use relative, not absolute-threshold, falsification criteria by design. §5 now defines "equivalent cold-started policy" operationally instead of adding a numeric target, which would have reintroduced the parallel-metric drift risk §5 already guards against. |
| Gap: benefit ownership ends at project close | **Accepted as written.** §3 now states ownership continues through M5 and post-phase validation. |
| Gap: no disbenefits identified | **Accepted as written** — independently confirmed no disbenefit-equivalent language exists anywhere in the four-document chain. New §7 added. |
| Gap: benefits are mostly qualitative | **Accepted the observation, rejected invented numbers.** §1a now states quantification is deferred until real M2 episode data exists, rather than fabricating order-of-magnitude estimates. |
| Gap: HYP-AL-011 mixed into primary table | **Accepted as written.** Split into §1a (confirmed) and §1b (potential, not yet validated). |
| Claim: plan understates beneficiaries | **Accepted, reframed.** Confirmed structurally — the v1.0 §1 table had no beneficiary column at all for any row. §1a/§1b now add one, populated from Ideation §3.1's existing Stakeholder Register. Rejected the specific framing that "the agent itself" is a beneficiary — a `TaskPolicy` has no standing to benefit in PMBOK terms; the real beneficiary of HYP-AL-009's capability-creation benefit is the adopter who gains a previously-impossible decision class, per Ideation §3.1. |

---

## Provenance & Completeness Self-Assessment

| Field | Status |
|---|---|
| Sequencing | **Named honestly as a retrofit**, not claimed as a properly-ordered input — this document follows the Charter it should have preceded |
| Target Benefits (§1) | Every row traced to an existing document and hypothesis ID; beneficiaries traced to Ideation §3.1's existing register, not invented |
| Metrics (§5) | Deliberately reuse existing falsification criteria rather than parallel metrics that could drift out of sync |
| Disbenefits (§7) | Added in v1.1; each tied to an existing monitoring mechanism, not a new one |
| Tracking approach (§8) | Reuses the Charter's own M4/M5 checkpoints rather than inventing a third review cycle |
| Process rule | Stated explicitly for future projects: draft this plan before or alongside the Charter, consistent with PMBOK 8 Figure 2-3 |
| External review handling | Two reviews received against v1.0; disposition of each finding recorded above rather than applied uncritically |
