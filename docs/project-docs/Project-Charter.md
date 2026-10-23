# Project Charter — agent-learning Phase 1: Warm-Start & Confidence-Interval Bandits

**Version:** 1.9
**Project Sponsor / Initiator:** Menno
**Date:** 2026-10-22
**Status:** **Approved** — M1 underway; M0.5 resolved: **Go**

**Versioning convention from this point forward:** this charter is now
approved and stable. Routine execution-time findings — new M0.5 research
log entries, case examples examined, incremental progress on M1–M5 — are
appended directly where they belong (e.g., the M0.5 Research Log in §5)
**without** bumping the version number or adding a Provenance row each
time. A version bump is reserved for actual structural changes to the
charter itself: a new gate, a corrected disposition, a scope change —
the kind of changes v1.1 through v1.7 actually were, not routine data
accumulation.
**Source:** `docs/project-docs/Ideation-Document.md` v1.9, `docs/project-docs/Business-Case.md` v1.4, and the real structure of `socialengage/docs/project docs/Project-Charter.md` (sections 1–3, 6–10 adapted directly; sections 4–5 added — this charter needed a resourcing and stakeholder section the SocialEngage charter didn't, because that project is solo/self-funded and this one is not)

---

## 1. Purpose and Justification

Across this session's Ideation and Business Case work, `agent-learning`'s
methodology landscape was surveyed (22 real methodologies, 2 external
review rounds), and a weighted analysis (Business Case §3, revised on
review) concluded that **Option A (warm-start / transfer of priors) and
Option C (Thompson sampling / UCB)** should be built as a tied first
phase, with **Option B (critique-to-evidence + DPO) deferred**, not
rejected, until its named risks have real mitigations (Business Case §6,
§10).

This charter exists because that recommendation, on its own, is still
just a document — nothing yet commits any actual time to it, and nothing
yet gates when Phase 2 research is allowed to start consuming more of
that time. This charter formalizes Phase 1 as a scoped initiative with
named resource requirements and an explicit decision gate, rather than
letting exploration continue to drift forward informally the way it has
for the rest of this session.

## 2. Objectives

- Resolve Business Case §7's flagged, unverified dependency: does
  `SoftmaxPolicy` actually expose its converged internal state in a form
  reusable as a new policy's initial state?
- Validate or invalidate **HYP-AL-008** (warm-start reduces episodes
  needed to reach autonomy-eligibility, vs. a cold uniform start).
- Validate or invalidate **HYP-AL-009** (a confidence-interval-based
  bandit can cross the autonomy gate that defeated REINFORCE under
  positive-only evidence, per HYP-AL-002).
- Produce a **recorded** decision on whether Option B (Phase 2) proceeds
  — the actual mechanism behind this charter's resourcing gate (§9),
  not an informal default.
- **Added on request, applying the same resourcing-gate principle one
  step earlier:** within a time-boxed **40-hour research investment**
  (Menno's own stated resourcing decision, not a derived estimate),
  gather real additional case evidence beyond the single SocialEngage
  example in §5, and get a preliminary read on HYP-AL-011
  (willingness-to-pay) — producing a recorded **Go/No-Go** decision on
  whether the long-term technical commitment (M2–M5) is justified at
  all, before any further time is spent building it.

## 3. Scope

### In Scope (Phase 1)

- **The 40-hour End-User Value Research phase (M0.5, §7)** — gathering
  real additional case examples of the benefits described in §5's
  End-User Value Analysis, and a preliminary (not necessarily
  conclusive) test of HYP-AL-011. Explicitly separate from, and not
  nested inside, the technical work below — it investigates a different
  question (is this worth building at all) and can run in parallel with
  M1, not sequentially after it.
- The §7 dependency check itself (read-only investigation of
  `SoftmaxPolicy`'s internals — no commitment to building anything until
  this resolves)
- Warm-start seeding path for a new `TaskPolicy`, contingent on the §7
  check passing
- A Thompson-sampling or UCB policy class, parallel to `SoftmaxPolicy`
- Re-testing both against real stored data: a warm-started 7th
  structurally similar policy (source: `approve-adr`'s converged state)
  for HYP-AL-008; `validate-intent-foundation`'s real 146-episode history
  for HYP-AL-009

  **Named gap, flagged on review rather than discovered during M2:** no
  7th policy or its episode history exists yet — unlike HYP-AL-009,
  which replays data already on record, HYP-AL-008's test requires
  *generating* a genuinely new comparison: a cold-started control arm
  and a warm-started arm of the same new policy, run against comparable
  real decisions, to get a fair episode-count-to-gate comparison at all.
  This is an experimental-design and data-collection cost, distinct from
  the *implementation* complexity Business Case §3 scored at 5/5 — that
  score covers the code change (seeding initial state), not the cost of
  running two parallel arms long enough to compare. Conflating those two
  cost axes under one score would repeat the exact mistake the Business
  Case's own §3 revision already corrected once (problem-severity vs.
  evidence-readiness). Scoping the comparison methodology itself is real
  work for M2, not assumed away by this charter.

### Out of Scope (Phase 1)

- **Building or piloting the governance-as-a-service layer itself**
  (HYP-AL-011) — the 40-hour research phase tests the *question*, it
  does not build or sell anything
- **Option B (critique-to-evidence + DPO pairwise learning)** — explicitly
  deferred per Business Case §10, not part of this charter
- The user-persona gap and the (now-closed) competitive-positioning gap
  named in Business Case §8–9 — unrelated to Phase 1's resourcing
- The still-open `classify-diff-type` tie-break from earlier in this
  session (ADR-0145 correction case) — a separate, unresolved thread

## 4. Resource Requirements (Human)

**Named honestly, not fabricated:** no FTE budget or headcount exists
for an open-source SDK with a volunteer/maintainer-review model (Ideation
§3.3). What follows translates Business Case §3/§5's own ordinal
complexity scores into role-types and *relative* effort, not measured
estimates presented as fact.

| Role | Needed for | Relative effort (from Business Case §3/§5 complexity scores) | Notes |
|---|---|---|---|
| SDK-internals contributor (familiar with `SoftmaxPolicy`/`ReinforceLearner`) | §7 dependency check; Option A implementation | **Low** — complexity 5/5, the lowest-cost item in the entire 22-methodology landscape | Work is blocked on M1; if §7 resolves "no," this role's remaining work may not be needed at all |
| New-policy-class implementer (comfortable with confidence-interval / Bayesian bandit reasoning) | Option C (Thompson sampling or UCB) | **Medium** — complexity 4/5 | Not starting from zero: the SDK already computes Wilson lower bounds elsewhere, which is the same statistical family |
| Maintainer / reviewer | PR review and merge decision for both options | Not effort-scored, but the real bottleneck resource in a volunteer-maintainer OSS project (Ideation §3.3's named RACI gap) | This, not engineering hours, is this project's actual scarce resource |
| Decision adjudicator (human reviewing a `needs_user_feedback`/`needs_user_tie_break` result) | Ongoing SDK role, not Phase-1-specific | Already a defined role (Ideation §3.1) | Listed for completeness, not new demand created by this charter |
| End-user value researcher (Menno) | M0.5 — the 40-hour research phase | **40 hours — Menno's own stated resourcing decision, not derived from Business Case §3/§5's ordinal scores like every other row above.** Named as a different kind of number for the same reason MPN access was labeled "stated, not verified" in §4 below: it's a real planning commitment, not a measured estimate. | Gathers additional real case evidence and a preliminary HYP-AL-011 signal; produces the M0.5 Go/No-Go, not a full market study |

**Where might the first two roles actually come from?** Checked directly
rather than assumed: there is no `CONTRIBUTING.md` in this repo and no
explicit "contributions welcomed" statement anywhere in the README —
only the standard Microsoft Open Source Code of Conduct boilerplate,
which signals this is a real, sanctioned Microsoft OSS project but makes
no promise about how (or whether) external proposals get resourced.
What *is* real, already cited in Ideation §3.1 from the git log: external
contributors (`MargoOs`, `adityasinha-aiplan`, `meiwa7`) have actually
landed merged PRs (Spark scoring, cost-model docs, README improvements).
That's observed behavior, stronger evidence than a policy statement. Three
real resourcing paths follow from this, not just one:

1. **Menno** prototypes it directly, as this session's own exploration
   has done throughout — the path this charter was originally written
   assuming.
2. **An external GitHub contributor** picks it up — has real precedent
   (the three names above), though nothing guarantees it happens for
   *this specific* proposal.
3. **Microsoft's own maintainers** build it themselves, if they judge
   HYP-AL-008/009 worth prioritizing. This path is materially stronger
   than a cold GitHub issue: Menno has access to the **Microsoft Partner
   Network**, a real, existing channel for routing a properly-addressed
   proposal to the right internal stakeholders rather than an
   unaddressed issue sitting in a public queue. **Named as the user's own
   stated access, not independently verified here** — the same way any
   other first-person fact about the user's own professional context
   would be taken as given. This still does not *guarantee* this specific
   proposal gets prioritized or even reaches the actual small team that
   maintains `agent-learning` inside a large org — but it is a real
   formal route to make the ask, not a hope.

This charter does not need to pick one of the three — §9's resourcing
gate (below) applies regardless of which path actually supplies the
work. If the MPN path is pursued, drafting that proposal is itself a
pre-M1 activity worth scoping explicitly, not an assumption folded
silently into M1.

## 5. Stakeholder Register (Phase 1)

Reuses `Ideation-Document.md` §3.1 and `Business-Case.md` §8 rather than
re-deriving a third parallel register. Only Phase-1-specific entries are
added here:

| Stakeholder | Influence | Interest in Phase 1 specifically |
|---|---|---|
| Menno (initiator of this exploration track) | High | Decides whether to actually build Option A/C against the real SDK, and when the §9 resourcing gate opens for Phase 2 |
| Microsoft (maintainer org) | High | Not only a PR-acceptance gate — per §4's revised resourcing analysis, Microsoft is also a *possible direct resourcing source* (their own maintainers could build this), as well as the one who'd need to accept any externally-built PR. This charter commits them to neither role. Menno's Microsoft Partner Network access (§4) is a real route to reach the right internal stakeholders directly, distinct from the public GitHub issue queue — but routing through MPN still doesn't guarantee this specific proposal lands with the team that actually maintains `agent-learning`. |
| External GitHub contributors (real precedent: `MargoOs`, `adityasinha-aiplan`, `meiwa7`, per Ideation §3.1's git-log citation) | Low individually, but the second of §4's three real resourcing paths | Could pick up Option A or C the same way they've landed other real features — unconfirmed for this specific proposal, but not hypothetical as a pattern |
| Future adopters hitting Business Case §1's three named gaps | Low individually, high collectively | The eventual beneficiaries — same stakeholder already named in Business Case §8, repeated here for Phase-1 traceability |
| **Downstream beneficiary — the team/process the governed agent actually serves** | Not yet named anywhere in this document chain until this revision | See End-User Value Analysis below — grounded in this session's own real case study, not an invented persona |

### End-User Value Analysis (added on request — not in Business Case §8's original persona gap)

`agent-learning` is not itself user-facing — it's infrastructure a
developer embeds inside their own agent. That means "end user" is really
two tiers, and the second one has gone unnamed in this document chain
until now:

1. **The agent-builder / SDK adopter** — already named in Ideation §3.1
   and Business Case §8 as "SDK adopters / agent builders." They consume
   the package directly.
2. **The downstream beneficiary — whoever the governed agent's decisions
   actually serve.** This tier has no invented persona here, because
   this session already has a real, evidenced example of it: the
   **SocialEngage governance process itself**. Every `approve-adr`,
   `approve-brd`, `approve-fdd`, and `approve-story` decision this
   session made real use of `agent-learning` to replace ad hoc judgment
   calls with statistically-justified, auditable ones. That's not a
   hypothetical market segment — it's the literal case study this whole
   three-document chain is built from.

**What each tier gains from Phase 1, reasoned from evidence already on
record, not new research:**

| | Agent-builder / SDK adopter | Downstream beneficiary (SocialEngage-style) |
|---|---|---|
| **Option A (warm-start)** | Lower integration friction — every *new* policy they add inherits a head start instead of a cold uniform prior | Fewer total manual reviews across the system's lifetime, compounding each time a *new* governance decision type is introduced (e.g., a hypothetical future `approve-test-plan`) |
| **Option C (UCB/Thompson)** | Unlocks a decision class that is currently **impossible** to automate under the packaged SDK, not just slow to automate | `validate-intent-foundation` — the real check for whether new work traces to a real Intent/Objective — is this session's own proven-stuck example (HYP-AL-002). Option C is the one concrete path to making *that specific, already-observed pain point* genuinely autonomous and auditable, not a speculative future one |

**Which adds more value to the end user?** Reasoned, not asserted as
settled: **Option C has the more dramatic story** — it turns a decision
that is *provably, permanently* stuck into one that could clear the
autonomy gate at all, versus Option A's efficiency gain on a decision
that would eventually clear the gate regardless. But **Option A's value
compounds at scale** — every future policy benefits, not just one. This
is the same "tied, not strictly ordered" conclusion Business Case §3
already reached for different reasons; end-user value analysis doesn't
overturn it, it reinforces it from a different angle.

### M0.5 Research Log (real findings, logged as they occur)

The first real candidate case examined for this 40-hour phase — a
**negative** result, logged honestly rather than discarded for not
strengthening the case, since only recording positive matches would
repeat the exact survivorship-bias mistake HYP-AL-002 already exposed
once:

| Candidate | Source checked | Verdict | Why |
|---|---|---|---|
| `github.com/mdresch/adaptive-learning-assessments` | README, `src/core` tree, `src/core/bkt_engine.py` (not checked: `src/api`, `src/db`, `src/models`, `scripts/`, `tests/`) | **Weak match — not adopted as a case** | A Bayesian Knowledge Tracing system for programming learners. Its README names "Adaptive Challenge Selection" as a goal, but it isn't implemented — no bandit or selection logic exists in the code. The one real discrete-choice function (`recommend_practice_intensity`, 4 fixed options) is a hardcoded rule, and **nothing in the codebase logs whether a recommendation was followed or helped** — no outcome signal means no methodology in the landscape has data to learn from here, regardless of fit otherwise. The decision also looks per-learner-varying, which would rule out a `low`-authority bandit even if outcome data existed; at best a future `full`-authority candidate, contingent on the project adding outcome logging it doesn't have today. |
| `C:\Users\MennoDrescher\source\repos\adpa` (local, "ADPA Framework") — provider-selection decision, per `docs/07-architecture/ADR-016-multi-provider-ai-strategy-and-failover-architecture.md` | The ADR itself (verified against running code per its own text), plus a direct grep for provider-selection logic in `server/src/services/jobs/AIGenerationJobService.ts` | **Strong match — the first real positive case** | Every AI generation job selects one of 7 discrete provider types (openai/google/mistral/azure/anthropic/ollama/foundry-local). Real outcome data **already exists**: `ai_generation_jobs` logs `provider`, `model`, `input_tokens`, `output_tokens`, `cost`, `duration_ms` per job, and `FallbackExecutor` logs failure reason and error class per attempt — the exact gap that sank the first candidate is already solved here. But selection today is **not learned** — it's a static, manually-set DB `priority` column, ascending order; "intelligent failover" in the README is inflated language for a deterministic fallback chain, the same pattern CrewAI's "memory" turned out to be. That gap is the opportunity: real logged rewards (cost/latency/success) exist with no mechanism to learn from them — a direct fit for **Option C (UCB/Thompson)**. ADR §3.5 also notes provider selection is "configurable per job type," a genuinely **contextual** bandit shape — the unpackaged gap already named as methodology #4 in Business Case §3. One adjacent finding, named honestly as *not* evidence for agent-learning: the ADR's own Action Item #3 (an unbuilt generation-level cost-budget gate) would be a good `full`-authority shape, but it's ADPA's unbuilt future work, not an existing case to point at today. |

This doesn't move M0.5 toward No-Go by itself — one examined case is not
40 hours — but it's the kind of honest negative that belongs in the
record, not just the positives.

**Additional context surfaced outside M0.5's time-box, 2026-10-22:**
Parallel Ideation-document work this session — a separate research
thread, not counted against M0.5's 40-hour budget — formalized four more
real cross-system candidates where Option C's confidence-interval-bandit
family specifically (not Option A) could apply: ADPA's three-layer
quality-gate constants (HYP-AL-012), RPAS-BA-Workbench/SIDPA's
Enterprise Value Index floors (HYP-AL-014), SIDPA's illustrative
Confidence/Accuracy Factor rating bands (HYP-AL-016), and
task-capability-restricted model/provider selection — independently
drafted and submitted upstream as a public GitHub feature request
against Vercel's AI Gateway (HYP-AL-017). All four remain
**Formulated**, not Validated — each still needs real outcome-history
data most don't yet have (per Ideation §2.2.2's own named blockers), so
none of this moves M0.5's Go/No-Go by itself, the same caveat already
stated above for the ADPA provider-selection case. Named here only as
additional, not-yet-tested breadth for Option C's value case, consistent
with this log's own practice of citing full detail from its source
rather than duplicating it (Ideation §2.2.2, not re-derived here). Two
further candidates from the same Ideation pass are explicitly **not**
Option A/C evidence, named for completeness rather than counted toward
this phase: HYP-AL-013 (category-level escalation learning — the
already-shipped REINFORCE/`SoftmaxPolicy` family, not Option A or C) and
HYP-AL-015 (a newly-registered, genuinely distinct Methodology #23 —
dueling-bandit/active-ranking — not a confidence-interval bandit at
all).

**M0.5 resolved — Go, 2026-10-22.** Per §7's own disposition rule, the
"real additional case evidence found beyond SocialEngage" condition is
satisfied on its own — the ADPA provider-selection case and the
ADPA quality-gate case (HYP-AL-012) above are both real, independently
sourced, and strong, and the confirmed Scout integration (Ideation
§2.1.2) is stronger evidence still that continued investment in this
SDK's approach is justified, even though it isn't a Phase-1-specific
case example. This condition is explicitly **independent** of
HYP-AL-011 per §7's own "and/or" wording, so M2–M5 proceed as scoped
without resolving HYP-AL-011 first. **Actual research time: 16 of the
40-hour budget (Menno's own stated figure, not independently tracked or
derived here)** — the remaining ~24 hours were not needed once the
case-evidence condition was met, consistent with the 40-hour figure
being a time-box ceiling rather than a mandatory floor (§11). HYP-AL-011 itself is not being declared No-Go or
abandoned — it is reframed, not resolved, in Ideation §2.2.1: unlike
every other open question in this document chain, it cannot be advanced
by more code or document research, only by actually asking real
prospective customers. That is a deliberately separate, still-open
question from this Go decision, not a loose end left by it.

**Would they value this enough to pay for it as a service?** Honestly:
**I don't know, and asserting an answer here would be exactly the kind
of fabricated market claim this document chain has refused to make
everywhere else.** One real distinction worth making precisely: the
*SDK itself* is free, open-source infrastructure — nobody pays Microsoft
to `pip install agent-learning`. What *could* plausibly be paid for is a
different product layered on top — a managed governance-as-a-service
offering (hosted audit dashboards, a policy-template library, compliance
reporting) — but that is a distinct product from what this charter
scopes, and nothing checked this session tests real willingness to pay
for it. This is now **HYP-AL-011** in the Ideation Document's registry,
Formulated, not Validated — the honest next step is a real pricing or
customer-discovery test, not a confident guess dressed up as analysis.

## 6. Deliverables

- A recorded **Go/No-Go decision from M0.5's 40-hour research phase**,
  with whatever real case evidence and HYP-AL-011 signal was actually
  found — documented regardless of which way it resolves; a No-Go is a
  real, useful outcome of research, not a result to avoid producing
- §7 dependency check, written up with a verified yes/no answer (not
  left flagged indefinitely)
- Working warm-start seeding path for a new `TaskPolicy` (conditional on
  the above)
- Working Thompson-sampling or UCB policy class, tested against
  `validate-intent-foundation`'s real stored episode history
- HYP-AL-009 updated from **Formulated** to **Validated** or
  **Invalidated** in the Ideation Document's registry
- HYP-AL-008 either updated the same way (if M1 = Yes and Option A is
  actually tested), **or**, if M1 = No, its disposition — path (a) patch
  and proceed, or (b) drop Option A for this phase — recorded explicitly
  immediately at M1's close (§7's disposition table), carried forward
  into this registry as "**Formulated — blocked on M1, disposition
  recorded**" rather than left ambiguous
- A recorded Phase 2 go/no-go decision

## 7. High-Level Milestones

| Milestone | Description |
|---|---|
| M0 — MPN proposal drafted and routed (optional, if pursued) | A properly-addressed proposal for HYP-AL-008/009, scoped from this charter, submitted via the Microsoft Partner Network to reach the right internal stakeholders — a real formal ask, not an assumption that Microsoft will notice this charter on its own |
| **M0.5 — End-User Value Research (40-hour time-box)** | Gather real additional case examples of §5's End-User Value Analysis beyond the single SocialEngage example; get a preliminary read on HYP-AL-011. Runs in parallel with M0 and M1 — investigates a different question (is this worth building) than either, so it doesn't block or get blocked by them. Produces a recorded **Go/No-Go** on the long-term technical commitment (M2–M5). |
| M1 — §7 dependency resolved | `SoftmaxPolicy` internals inspected directly; the reusable-state question answered yes or no, not left as an assumption |
| M2 — Option A implemented (if M1 = yes) | Warm-start seeding built and run against a 7th structurally similar policy |
| M3 — Option C implemented | Thompson/UCB policy class built, parallel to `SoftmaxPolicy`. **Default to UCB / Wilson-bound adaptation first, not Thompson sampling** — reasoned from §9's own auditability constraint, not a new fact: UCB is deterministic given the same statistics, consistent with the SDK's existing (deterministic) Wilson lower bound already in use elsewhere; Thompson sampling is stochastic and would need explicit RNG-seed capture to stay replayable/auditable, an extra burden §9 doesn't currently account for. Treat Thompson sampling as a secondary variant, only if UCB proves insufficient. |
| M4 — Both re-tested against real data | HYP-AL-008 tested on episode-count-to-gate; HYP-AL-009 tested on `validate-intent-foundation`'s stored history |
| M5 — Phase 1 review | HYP-AL-008/009 statuses resolved; recorded decision on whether Option B (Phase 2) proceeds |

**M0.5 disposition — written explicitly from the start this time**, not
retrofitted after a review found the gap, the way M1's was:

| M0.5 Result | Outcome |
|---|---|
| **Go** — real additional case evidence found beyond SocialEngage, and/or HYP-AL-011 shows a credible positive signal (not necessarily Validated outright — a preliminary 40-hour research pass isn't a full customer-discovery program, but a clearly negative signal is distinguishable from an encouraging one) | Proceed to M2–M5 as scoped, independent of M1's own separate Yes/No branch below |
| **No-Go** — no additional real case evidence found, and/or HYP-AL-011 shows a clearly negative signal (real prospective contacts decline interest when actually asked) | The long-term technical commitment (M2–M5) **does not proceed as currently scoped**. This is **not** a falsification of HYP-AL-008/009 — market interest and technical validity are different questions, the same category distinction already made for M1's own disposition below. Two honest options at that point: (a) treat this as a personal/SocialEngage-only tool with no broader ambition — the six real policies already built this session deliver real value regardless of any wider market finding; or (b) revisit later with more evidence, not abandoning the hypotheses, just declining to commit further research time now |

**Resolved, 2026-10-22: Go.** Full reasoning logged in §5's M0.5
Research Log rather than repeated here.

**M1 disposition, made explicit on review** (the milestone table above
implicitly handled this but didn't say so — worth stating directly rather
than leaving the branch to be inferred):

| M1 Result | Outcome |
|---|---|
| **Yes** — `SoftmaxPolicy` exposes reusable converged state | Proceed to M2 as scoped; HYP-AL-008 moves to **Testing**. |
| **No** — state is not cleanly reusable | Option A is **blocked on an implementation gap, not disproven**. HYP-AL-008's own falsification criteria (Ideation §2.2.1 — Core SDK Hypotheses, per the Ideation v1.9 subsection split) require comparing a warm-started policy's episode-count-to-gate against a cold-started one — an SDK-internals limitation settles neither way, so HYP-AL-008 stays **Formulated**, it does not become Invalidated (this document's hypothesis-status vocabulary already has a slot for "not yet tested"; no new status is needed). Two live options follow: (a) scope a small SDK change to expose the needed state — which would also force a re-score of Business Case §3, since Option A's complexity score (5/5, "requires no new math") would no longer hold once new code is required; or (b) drop Option A from this phase and proceed with Option C alone. **Recorded immediately at M1's close, not deferred to M5** — this choice doesn't depend on Option C's M3/M4 results at all, so parking it until M5 would only add latency for no reason. If (a) is chosen, the patch can proceed in parallel with M3. M5's job is to confirm what was already decided here, not to make the decision itself — fixing the circularity an external review correctly flagged between this table and §6/§11's original wording. |

No calendar dates are set at charter stage — the same reasoning as the
real SocialEngage charter this one is adapted from: this is
volunteer-paced exploration, not date-committed delivery. Milestones are
sequenced by dependency, not by date.

## 8. Assumptions

- Menno (or any future contributor) has available time to pursue this
  outside other commitments — unverified, same category of assumption
  the real SocialEngage charter names for its own solo model
- `SoftmaxPolicy` exposes its converged internal state in some reusable
  form — the single assumption M1 exists specifically to *test*, not to
  take on faith
- The existing `Episode`/storage-backend contracts (already used by six
  real policies this session) remain stable enough for a new policy
  class to reuse without modification

## 9. Constraints

- **No real budget exists — this charter introduces a resourcing gate,
  not a funding gate.** `agent-learning` is a volunteer/maintainer-
  reviewed open-source SDK (Ideation §3.3); there is no dollar amount to
  gate against, consistent with Business Case §5's explicit substitution
  of effort/severity proxies for NPV/ROI. What this charter *does*
  introduce is now **two applications of the same gate, not one**: the
  long-term technical commitment (M2–M5) may not begin consuming
  contributor or research time until **M0.5's** 40-hour research phase
  produces a recorded Go/No-Go; and separately, **Option B** (Phase 2)
  may not begin consuming further time until **M5** produces its own
  recorded decision. Neither is an informal drift forward, which is what
  happened with this session's own exploration before this charter
  existed. This is the real mechanism behind "a funding requirement
  before initial research consumes more budget," translated into the
  scarce resource this project actually has — time and attention, not
  money — and applied consistently at two points, not just one.
- Volunteer/contributor capacity — no guaranteed availability; the same
  bus-factor risk the real SocialEngage charter names for its own solo
  model applies here too, arguably more so since no one is even
  committed full-time
- Any implementation must preserve the frozen-model / CPU-only /
  auditable constraints already established in Ideation §1.1 — not
  negotiable, regardless of resourcing

## 10. High-Level Risks

Pulled from Business Case §6 at summary level, not duplicated in full:
§7's dependency could resolve "no," voiding Option A's entire resource
allocation above; Option C's confidence-interval math has not been
validated against a real stuck-decision dataset yet, which is itself
what M4 exists to test. Full risk detail lives in Business Case §6.

## 11. Success Criteria

**M0.5's success criterion, stated separately since it gates a different
decision than the rest of this section:** a recorded Go/No-Go decision
produced within the 40-hour time-box, regardless of which way it
resolves — a No-Go is success for the research phase even though it
means M2–M5 doesn't proceed as scoped. Conflating "the research
concluded" with "the research said yes" would undermine the whole point
of running it before committing further time.

**Corrected on review — the original wording here created a deadlock
with §7's v1.3 disposition table and has been fixed, not just
reworded.** HYP-AL-009 reaching a **resolved** status — Validated or
Invalidated, either being a real, useful outcome. HYP-AL-008 reaching a
resolved status **if M1 = Yes and it was actually tested**, or, **if
M1 = No**, having its path-(a)-or-(b) disposition formally recorded at
M1's close (§7) — that recorded disposition, not a forced
Validated/Invalidated verdict, is what counts as HYP-AL-008's half of
success in that branch. Meeting whichever applies triggers M5 and the
recorded Phase 2 decision.

## 12. Approval

As with the real SocialEngage charter this one is adapted from, formal
sign-off here is a self-commitment, not a multi-party approval — this
charter does not bind Microsoft or its maintainers to anything; it is
Menno's own planning artifact for exploring and extending
`agent-learning`. It is considered approved when Menno elects to begin
M1 and/or M0.5 — the two can start independently, since neither blocks
the other. Any resulting code would still need real maintainer PR review to
land in the upstream SDK, per the RACI gap already named in Ideation
§3.3 — this charter authorizes exploration, not a merge.

**Approved by:** Menno (Sponsor)
**Date:** 2026-10-21

**Added after approval:** `Benefits-Management-Plan.md` v1.0 now exists,
consolidating the value content scattered across §5 and the Ideation/
Business Case documents. Per PMBOK 8 Figure 2-3, it should have preceded
this Charter as an input — it didn't, and that's named explicitly in
its own provenance rather than silently fixed. Future projects: draft
the Benefits Management Plan before or alongside the Charter.

---

## Provenance & Completeness Self-Assessment

| Field | Status |
|---|---|
| Purpose & Objectives (§1–2) | Traced directly to Business Case §10's revised recommendation, not restated loosely |
| Resource Requirements (§4) | **Explicitly not fabricated** — ordinal role/effort translation from Business Case §3/§5's existing complexity scores, named as a translation rather than a measured estimate |
| Stakeholder Register (§5) | Deliberately not re-derived from scratch — cross-references Ideation §3.1 / Business Case §8, only adding what's genuinely Phase-1-specific |
| Constraints (§9) | The "funding requirement" idea this charter was built to address is reframed honestly as a **resourcing gate** (time, not money) — naming the substitution rather than forcing a budget figure that doesn't exist |
| Approval (§12) | Explicitly scoped to Menno's own exploration track — does not claim authority over Microsoft's actual roadmap or maintainer decisions |
| Resource Requirements (§4) & Stakeholder Register (§5), v1.1 revision | Checked, not assumed: no `CONTRIBUTING.md` or "contributions welcomed" statement exists in this repo (verified directly), but real git-log evidence of merged external PRs (already cited in Ideation §3.1) supports a broader resourcing picture than "Menno alone" — three real paths named (Menno, an external contributor, Microsoft's own maintainers), with the Microsoft path marked **possible, not assured** rather than asserted |
| Resource Requirements (§4), Stakeholder Register (§5), Milestones (§7), v1.2 revision | Microsoft Partner Network access **taken as the user's own stated fact, not independently verified** by any tool here — distinguished explicitly from the git-log evidence above, which *was* independently checked. Added M0 as an optional, non-blocking milestone rather than folding "Microsoft will resource this" into M1 as a silent assumption |
| Milestones (§7), v1.3 revision | External review correctly flagged that M1's failure branch was implicit, not stated. Accepted the underlying point; corrected the review's own proposed wording ("HYP-AL-008 invalidated") against the hypothesis's actual falsification criteria in Ideation §2.2 — an SDK-internals limitation blocks the planned test, it doesn't falsify the hypothesis, so the correct disposition is **Formulated** (not yet tested), not **Invalidated** |
| Deliverables (§6), Milestones (§7), Success Criteria (§11), v1.4 revision | **Real bug, not a style note**: a fourth review found that v1.3's own "stays Formulated" fix for HYP-AL-008 was never propagated into §6/§11, which still required Validated/Invalidated to trigger M5 — a literal deadlock on the M1=No branch. Fixed in all three sections, not just reworded. Also moved the path-(a)/(b) decision from "M5 to record" to "recorded immediately at M1's close," since it doesn't depend on Option C's results — the original M5 framing added latency with no real reason behind it. Added a named gap on HYP-AL-008's actual test requiring a genuinely new 7th policy and fresh comparison episodes (not yet generated), distinguishing experimental-design cost from the implementation-complexity score Business Case §3 already covers. Added a reasoned (not newly-researched) preference for UCB/Wilson-bound adaptation over Thompson sampling in M3, grounded in this document's own existing auditability constraint |
| Stakeholder Register (§5), End-User Value Analysis, v1.5 revision | Added on direct request, not on external review. Named one real end-user tier (the downstream beneficiary — reasoned from this session's own SocialEngage governance case, not an invented persona) and compared Option A vs. C's value to it. **Explicitly declined to assert a willingness-to-pay answer** — no customer discovery or pricing evidence exists this session, so that question was formalized as a new, honestly-labeled hypothesis (HYP-AL-011, Ideation §2.2) rather than guessed |
| Objectives (§2), Scope (§3), Resources (§4), Milestones (§7), Constraints (§9), Success Criteria (§11), Approval (§12), v1.6 revision | Added **M0.5**, a new 40-hour time-boxed research gate (Menno's own stated resourcing decision, recorded as such — not derived like the ordinal scores elsewhere in §4), applying the same resourcing-gate principle already established for Phase 2 (§9) one step earlier: before M2–M5's technical commitment, not just before Option B. Propagated the new gate through every section it touches, including its own explicit Go/No-Go disposition table written from the start — deliberately avoiding the exact failure mode a prior review caught (a gate mentioned once but not threaded through §6/§11) |
| Stakeholder Register (§5), M0.5 Research Log, v1.7 revision | First real M0.5 finding logged: a real candidate repo (`adaptive-learning-assessments`, investigated directly via WebFetch, not assumed) was a **weak match** — recorded as a negative result rather than discarded, specifically to avoid repeating the survivorship-bias mistake HYP-AL-002 already exposed once. Named exactly what was checked and what wasn't, rather than implying an exhaustive audit |
| Status, Approval (§12), v1.8 revision | **Charter approved by Menno; M1 and M0.5 underway.** Last revision under the per-finding versioning discipline used through v1.7 — from here, routine execution-time findings (further M0.5 Research Log entries, M1–M5 progress) are appended directly without a version bump, reserving future bumps for genuine structural changes to the charter itself |
| Status (header), §5 M0.5 Research Log, §7 M0.5 disposition, v1.9 revision | **M0.5 resolved: Go.** A genuine disposition resolution, not a routine log entry, so it gets the version bump the v1.8 convention reserves for exactly this. Resolved on the case-evidence condition alone (ADPA provider-selection, ADPA quality gates, Scout), independent of HYP-AL-011 per §7's own "and/or" rule — not on a forced or guessed answer to HYP-AL-011, which stays open and is separately reframed in Ideation §2.2.1 |
