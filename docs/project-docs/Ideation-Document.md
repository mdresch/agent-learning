# Ideation Document — agent-learning SDK

## 📋 DOCUMENT HEADER METADATA BLOCK

| Field | Value |
|---|---|
| Document Title | Ideation Document — agent-learning SDK |
| Version | 1.13 |
| Date | 2026-10-25 |
| Status | Draft |
| Source | `README.md`, `PYPI.md`, `docs/decision-making.md`, `docs/autonomy-complexity.md`, `docs/experiential-reinforcement-learning-comparison.md`, `docs/scout-agent-learn-skill.md`, `docs/scout-automation-agent-learning.md`, `docs/research/main.tex`, `examples/next_best_action.py`, `src/agent_learning/decision.py`/`cli.py`/`audit.py`, `git log`, and this session's own real use of the SDK (building and validating eight real TaskPolicies against the SocialEngage project, including the diff/baseline classification pair) |

This is the first PM-governance-style document this project has — there is
no existing ADR/BRD/FDD/Ideation structure in `agent-learning` today, only
technical/architecture docs (`docs/architecture.md`, `docs/math.md`,
`docs/design.md`, etc.). This document, and the template it's drawn from
(`docs/templates/ideation-document-template.md`, written this session for
a different project and adapted here), are the first application of that
discipline to agent-learning itself.

---

### SECTION 1: EXECUTIVE SUMMARY & STRATEGIC BOUNDARIES

#### 1.1 Executive Summary & Strategic Boundary Definitions

`agent-learning` is a lightweight, in-process decision-and-learning layer
for an existing agent. It keeps the foundation model frozen — no GPU
fine-tuning, no hidden prompt rewrites — and instead gives one recurring
agent-task decision a small, interpretable `TaskPolicy` over explicit
executable alternatives.

The project's real scope is wider than any single mechanism inside it.
Across the codebase and this session's own use of it, at least **five
genuinely distinct learning/resolution variants** coexist under one
`TaskPolicy` abstraction, at different levels of maturity:

1. **Low-authority statistical bandit learning** (packaged, production) — `SoftmaxPolicy` + `ReinforceLearner`, a REINFORCE-with-baseline policy gradient over 2–N discrete actions.
2. **Full-authority reasoned resolution** (packaged, production) — `DecisionResolver`, confidence-weighted Bayesian evidence aggregation with hard constraints, Pareto dominance, and robust utility — no training, resolved per-instance.
3. **Contextual bandit learning** (example-only, **not packaged**) — `ContextualSoftmaxPolicy` + `ContextualReinforceLearner`, demonstrated in `examples/next_best_action.py`, never exported by the SDK.
4. **Pluggable reward shaping** (packaged, production) — local stdlib metrics by default, optional Azure AI evaluators, feeding reward into (1).
5. **Durable explicit human feedback** (packaged, production) — an accept/reject disposition that pins an action and bypasses the statistical gates entirely, a non-gradient form of trust.

`docs/experiential-reinforcement-learning-comparison.md` places the
packaged bandit path on a real external spectrum (SFT → RLVR → ERL) and
is explicit that the SDK sits at the RLVR-like middle panel, with ERL's
richer reflection-and-retry internalization named as something the SDK
does **not** do. That comparison, however, only covers the learned
(low-authority) side — it does not yet integrate the full-authority
Bayesian resolver into the same taxonomy.

This session also confirmed, directly against code and git history
rather than assumed from documentation text, that this exact SDK is the
real decision-governance layer behind Microsoft's own newest flagship
agent, Scout (announced Build 2026) — not a hypothetical fit, a live
one. See §2.1.2.

#### 1.2 Core Project Objectives & Measurable KPI Bounds

| # | Objective | Success Measure |
|---|---|---|
| 1 | Let an agent improve a recurring decision without any GPU training job | Zero fine-tune jobs required end to end (already true — CPU-only REINFORCE update) |
| 2 | Make autonomy earned and auditable, never assumed | Every autonomous execution traces to a specific, inspectable criteria table (complexity tier → required outcomes/correctness/margin) — already true |
| 3 | Support both statistical and reasoned resolution under one `TaskPolicy` abstraction, chosen per decision's actual shape | A decision that genuinely varies per-instance uses `full`; a decision with one stable global answer uses `low` — both already real, both exercised this session |
| 4 | Close the gap between example-only and packaged contextual learning | `ContextualSoftmaxPolicy` has an exported, documented learner and CLI path — **not yet true** |
| 5 | Give adopters an honest, complete answer to "where does this sit relative to SFT/RLVR/ERL" | A comparison that covers all five variants above, not just the low-authority bandit — **not yet true** |

---

### SECTION 2: LEARNING METHODOLOGIES LANDSCAPE & HYPOTHESIS PREMISES

#### 2.1 Learning Methodologies Landscape

A step-back survey, done deliberately rather than building feature-by-feature:
every learning/resolution methodology discussed or built this session, plus
established alternatives from the wider RL/ML literature, each assessed
against this project's own real constraints (frozen foundation model,
CPU-only, auditable, small discrete action spaces) rather than against
whether the technique is good in the abstract.

| # | Methodology | Implementable here? | Status |
|---|---|---|---|
| 1 | Supervised Fine-Tuning (imitate a target output) | **No** | Requires updating model weights to copy an example — contradicts the frozen-model premise outright. **Reopens if** a hosted or fine-tuned model enters scope (a product decision, not a learning one) |
| 2 | RLVR / policy-gradient bandit (REINFORCE-with-baseline) | **Yes** | Implemented, production — `SoftmaxPolicy` + `ReinforceLearner` (HYP-AL-001) |
| 3 | Bayesian / evidence-based reasoned resolution | **Yes** | Implemented, production — `DecisionResolver`; not gradient-based, a genuinely different resolution mode (HYP-AL-003) |
| 4 | Contextual bandit | **Yes, proven feasible** | Example-only (`ContextualSoftmaxPolicy`/`ContextualReinforceLearner`), not packaged (HYP-AL-004) |
| 5 | Pluggable reward shaping (local heuristics vs. LLM-judge evaluators) | **Yes** | Implemented, production — feeds #2 |
| 6 | Durable explicit human override | **Yes** | Implemented, production — non-gradient, granted trust, bypasses statistical gates entirely |
| 7 | ERL — experience, reflection, retry, internalize | **No, in full form** | Requires the policy itself to generate and internalize reflections — needs a generative model as the policy, not a small action-ID bandit. **Reopens if** replayable, resettable task environments exist |
| 8 | Lightweight critique-to-evidence (ERL-inspired, no weight updates) | **Yes** | Not built — candidate; turns textual critique into `DecisionFrame` evidence adjustments without touching model weights |
| 9 | Thompson sampling / Bayesian bandits | **Yes** | Not built — candidate; the SDK already computes Wilson lower bounds, halfway there |
| 10 | UCB (Upper Confidence Bound) | **Yes** | Not built — candidate; simpler than REINFORCE, no gradient or entropy hyperparameter needed |
| 11 | Epsilon-greedy bandit | **Yes** | Not built — weaker/simpler alternative to #9–10, named for completeness |
| 12 | Active evidence-seeking (information-gain-driven) | **Partially** | `InformationNeed`/`estimated_information_gain_bits` already exists on `DecisionResolver`'s `NEEDS_EVIDENCE` path; not yet automated into an actual seeking loop |
| 13 | DPO-style pairwise preference learning | **Yes** | Not built — candidate; this session's own Red Team methodology already produces exactly this kind of paired-preference data |
| 14 | Meta-learning across structurally similar TaskPolicies | **Yes** | Not built — candidate; motivated by cold-starting six structurally similar policies this session |
| 15 | Warm-start / transfer of priors (simpler than #14) | **Yes** | Not built — candidate; seed a new policy's initial state from a similar existing policy's converged state instead of a cold uniform prior |
| 16 | Model-based RL | **No** | Contradicts the project's explicit model-free simplicity philosophy — not worth pursuing as an *acting* policy. **Reopens as evaluation only** once enough episodes exist to fit an outcome model (see #29) |
| 17 | Ensemble routing across authority modes | **Yes** | Not built — candidate; a meta-decision choosing `low` vs. `full` per-instance rather than fixing it at policy-init time |
| 18 | Federated / multi-agent learning | **Not applicable** | Each `TaskPolicy` is single-agent, single-tenant by design — no multi-agent coordination problem exists here. **Reopens if** the hosted multi-tenant layer (HYP-AL-011) is pursued |
| 19 | Adversarial / red-team example generation | **Yes, already practiced** | Used this session as *validation* (testing a policy's discriminative power), not yet as a *training* signal — could feed #13 directly |
| 20 | Diff/baseline classification + scoped verification | **Yes** | **Implemented and validated this session** — `classify-diff-type`, correctly resolved 2 of 3 real test cases and correctly tie-broke the third |
| 21 | Category-level escalation learning | **Yes** | Implemented (`escalate-diff-response`), not yet trained — no episodes registered yet |
| 22 | Offline scored-search compilation of decision configuration (DSPy-style) | **Yes** | Not built — candidate added from external research (below); optimize `DecisionResolver`'s hand-set criteria weights/evidence-trust parameters against a labeled validation set via derivative-free search, instead of hand-tuning them as every `full`-authority policy this session did |
| 23 | Dueling-bandit / active-ranking pairwise comparison (adaptive query selection over pairs + a principled preference model, e.g. Bradley-Terry) | **Yes** | Not built — candidate; registered this session, resolving an open question previously left on `HYP-AL-015`. Distinct from both #12 (single-instance, information-gain-driven evidence-seeking for one decision) and #13 (passive preference learning from an already-collected pairwise dataset) — this instead adaptively selects *which* pair to compare next, to rank a set of N items with fewer total comparisons than ADPA's current exhaustive `n*(n-1)/2` approach |
| 24 | Linear contextual bandit (LinUCB / LinTS) | **Yes** | Not built — candidate; the principled step beyond `ContextualSoftmaxPolicy` (#4). Overlaps ADR-016 (UCB) and ADR-021 (contextual routing). Its exploration weight is a hyperparameter, so it is not parameter-free. Added 2026-10-25 from external review, checked against the repo |
| 25 | Multi-stage credit assignment (propagate outcome credit across the steps of a chain) | **Yes, blocked** | Not built — candidate, blocked: `Episode` has no `trace_id` (only `correlation_id` / `session_id`), so linking steps needs a store-boundary decision under ADR-002 first. No hypothesis registered until that is settled |
| 26 | Outcome-conditioned exemplar selection (choose which past episodes inform a decision) | **Yes** | Not built — candidate; only auditable if the selection itself is recorded in `Episode.metadata`. Distinct from #8 (turns critique into evidence) and #14 (shares priors across policies) |
| 27 | Prioritized experience replay | **Not worth it now** | Declined — at current episode volume replay prioritization has no measurable payoff. Revisit if volume grows by orders of magnitude |
| 28 | Conformal prediction / abstention (a calibrated "defer to a human" trigger) | **Yes** | Not built — candidate; fits the authority model directly. Its exchangeability assumption is weak when outcomes drift, so it is paired with #30 |
| 29 | Off-policy evaluation (inverse-propensity / doubly-robust) | **Yes** | Not built — candidate; scores a candidate policy on logged episodes before it acts. The safe form of #16: evaluation, not acting. Requires the logged action probability to be recorded |
| 30 | Non-stationarity and change-point handling (discounted or windowed updates) | **Yes** | Not built — candidate; project conditions drift, and none of #2, #9–11 assumes otherwise today |
| 31 | Safe / constrained bandits with hard action masking | **Yes** | Not built — candidate; encodes ADR-011's floors and caps as constraints on the action set instead of penalties |
| 32 | Active-learning triage of which decisions get scarce human adjudication | **Yes** | Not built — candidate; related to #23 and #12 but selects decisions to review, not pairs to compare or evidence to seek |

Of the 32 surveyed (the original 23, plus #24-#32 added 2026-10-25):

- 9 are real or partly real: 7 implemented (#2, #3, #5, #6, #19, #20, #21)
  plus #4 (example-only, not packaged) and #12 (partially built);
- 3 are structurally impossible under the frozen-model premise (#1, #7 in
  full form, #16);
- 1 is not applicable to the single-agent shape (#18);
- 1 is declined for now (#27);
- 18 are genuine, not-yet-built candidates worth prioritizing deliberately
  rather than building ad hoc: #8-11, #13-15, #17, #22-23 (the original
  10) and #24-26, #28-32 (8 added 2026-10-25). #25 is blocked on a store
  decision.

9 + 3 + 1 + 1 + 18 = 32. (The earlier text said 10 real and 9 candidates,
which summed to 23 only because the candidate list was miscounted: it
named ten.)

##### 2.1.1 External validation: what other agent SDKs actually ship

Before trusting this landscape as complete, it was checked against seven
real, widely-used agent frameworks/SDKs — not to copy their roadmaps, but
to see whether any of them have already solved something this list
missed, or ship a "learning" claim that doesn't survive scrutiny. Two
research passes this session, with doc citations, found:

| Framework | Real learning mechanism? | Finding |
|---|---|---|
| LangGraph | **No** | "Memory" is a `Store` with embedding-similarity retrieval injected into the prompt — pure recall, nothing scores or updates behavior from outcomes |
| Semantic Kernel | **No** | Same RAG-pattern recall; no scoring loop, optimizer, or outcome-driven persistent update found in current docs |
| OpenAI Agents SDK | **No** (partial textual journaling only) | Sandbox `Memory` has an LLM summarize-and-consolidate-across-runs loop (`MEMORY.md`), but no metric, trainset, or search — textual self-journaling, not optimization |
| Haystack | **No** | Verified directly against current docs and PyPI listing, not just unsearched — pipeline "loops" are runtime control flow; the evaluation framework scores output for a human to read, feeding no update rule |
| AutoGen (Microsoft) | **Yes, experimental** | Task-Centric Memory: test → on failure, LLM diagnoses and phrases advice → retry with advice appended → loop until reliable → persist as a validated insight. Matches **#7/#8** almost exactly — real external evidence that this project's planned ERL-inspired critique-to-evidence work (HYP-AL-005) is an industry-recognized pattern, not a speculative one, even though AutoGen itself labels it research-in-progress |
| CrewAI | **Yes** | `crew.train()`: records human free-text feedback per agent role across iterations, persists it, and automatically re-injects it into future prompts. Matches **#6** exactly — independent confirmation that a non-gradient, human-feedback-as-trust mechanism is a real, separately-arrived-at design elsewhere |
| DSPy | **Yes — and partially new** | Teleprompters (`BootstrapFewShot`, `COPRO`, `MIPROv2`, `GEPA`) search for a better prompt/demo configuration against a metric scored over a train/val set, then **freeze** the result and deploy it unchanged — offline, derivative-free search (generate-and-filter, LLM-proposed coordinate ascent, Bayesian optimization, or reflection-driven Pareto evolution), not a live online update loop. Only its one `BootstrapFinetune` variant is literal SFT (#1, already covered). The rest doesn't map cleanly onto any of #1–#21 — added above as **#22** |

| Microsoft — GitHub Copilot Auto / Azure AI Foundry Model Router | **Yes, in production** | GitHub Copilot's Auto mode (Sept 2026) scores each prompt on reasoning/code-complexity/bug-diagnosis difficulty plus real-time model availability, then picks a model per-prompt across three cost/quality tiers; Azure AI Foundry's Model Router is explicitly documented as "a trained model" choosing the underlying LLM per prompt across Cost/Quality/Balanced modes. Neither publishes an exact weighting formula. Matches **#4** (contextual bandit) and **#9–10** (Thompson/UCB) almost exactly — independent confirmation, at Microsoft's own product scale, that per-instance learned model selection on cost/quality is a real, shipping pattern, not a speculative one. |

**Net finding:** of eight major agent frameworks/platforms checked, four
ship no real learning mechanism at all — "agents that learn" is mostly
marketing for memory-as-storage. Three of the four real exceptions each
independently validate a methodology already in this table (#6, #7/#8)
rather than exposing a gap in it. Only DSPy's offline compilation
approach was genuinely outside the taxonomy, now closed as #22.
Microsoft's own GitHub Copilot/Azure AI Foundry model routing is the
fourth real exception — it confirms #4/#9–10 (contextual bandit,
Thompson/UCB) as production-proven at Microsoft's own product scale,
not just theoretically sound.

**A second external review proposed five more candidates** (persistent
semantic memory learning, teachability, memory extraction/consolidation,
iterative human-feedback adaptation, plan-policy learning) — checked
against the evidence above, not added:
- Persistent memory learning and teachability directly contradict
  findings already cited above (LangGraph's memory and AutoGen's
  Teachability were both explicitly checked and found to be recall, not
  learning).
- Memory extraction/consolidation was freshly verified against CrewAI's
  current memory docs: consolidation is write-time dedup/merge (an LLM
  choosing keep/update/delete/insert_new by content similarity);
  `extract_memories()` is text decomposition. Neither is conditioned on
  outcomes — nothing updates because a memory was used or because using
  it succeeded or failed. ETL, not learning.
- Iterative human-feedback adaptation is `crew.train()` under a new
  name — already mapped to **#6** above.
- Plan-policy learning was proposed despite the reviewer's own
  concession that Semantic Kernel's planners "aren't learning systems."

None survive verification; this table is not revised on their account.
The one fair strategic observation underneath the proposal — that
competing frameworks invest heavily in memory/recall/personalization
infrastructure while this project invests in evidence/decision/autonomy
infrastructure — is worth naming as a real, informative asymmetry: it
suggests this project's focus is relatively uncontested territory, not
that it's missing ground those frameworks have already covered.

##### 2.1.2 Confirmed production adoption: Microsoft Scout

Not a comparison to an external, independently-arrived-at pattern
(§2.1.1 above) — this is the same `agent-learning` codebase, confirmed
as the real decision-governance layer inside Microsoft's own newest
flagship agent, Scout (a Microsoft 365 "Autopilot," announced Build
2026, built on the OpenClaw runtime).

**What was found, and how it was verified, not assumed:**
- Two Microsoft-authored documents already sit in this repo:
  `docs/scout-agent-learn-skill.md` (the live skill instructing Scout
  when and how to create, consult, and record against a `TaskPolicy`
  for any delegated choice among executable alternatives — an Azure
  workload, a language model, a tool/workflow/escalation path) and
  `docs/scout-automation-agent-learning.md` (a separate maintenance
  automation that trains low-authority policies and audits
  full-authority ones on a schedule).
- Checked via `git log --follow`: both authored by **`ctava-msft`**
  across ten real, iterative commits (2026-08-07 to 2026-08-10 — "Add
  task learning loop," "Scope learning to delegated decisions," "Scale
  autonomy gates by decision complexity," "Unify reasoned and learned
  decisions," etc.), plus one `copilot-swe-agent[bot]` commit. `ctava-msft`
  is the same author as the formal research paper now also in this repo
  (`docs/research/main.tex`, "Chris Tava, Microsoft,
  christava@microsoft.com") — not a coincidental name match, the
  identical git handle.
- Checked that the mechanism described is real, not aspirational doc
  text: `policy_scope`, `delegated_decision`, and `decision_authority`
  are implemented in `src/agent_learning/decision.py`, `cli.py`, and
  `audit.py`, with dedicated tests (`test_decision.py`,
  `test_autonomy.py`, `test_cli.py`, `test_audit.py`).
- Found real fixture data tied to the same commit series:
  `data/functional-tests/patient-care-cli/policies/triage-nurse/*.json`,
  committed under "Document Scout learning workflows and fixtures" —
  the same triage-nurse example partially visible (mid-deletion) in
  this session's own git status at the start of this conversation.

**What this confirms:** the exact `low`/`full` decision-authority
split, REINFORCE-trainable low-authority policies, Bayesian-resolved
full-authority `DecisionFrame`s, and complexity-tier autonomy gating
this whole document chain describes are the literal mechanism Scout's
skill uses, live, to decide which executable alternative to delegate
to.

**What this does *not* confirm, named rather than assumed:** not
evidence that Scout uses the *contextual* softmax policy —
HYP-AL-004's named gap (`ContextualSoftmaxPolicy`, still unpackaged) is
untouched by this integration. If anything, the skill document's own
design is directly relevant *counter*-evidence to HYP-AL-004's second
half — see the corrected status there. Also unconfirmed: real
production volume (how many live Scout decisions have actually run
through this, whether any have crossed an autonomy gate) — not
checked, not assumed either way.

##### 2.1.3 ADR coverage of the not-yet-built candidates (added 2026-10-25)

Checked directly against `docs/adr/` and `src/agent_learning/policy/`, not
assumed. Ten candidate ADRs (ADR-014 to ADR-023) exist, one per candidate
methodology. **All ten are `Proposed`, untracked in git, unapproved
(`approve-adr` not run), and have no code or tests.** Their text says only
"ready for multi-criteria evaluation", so they are drafts derived from the
table above, not evidence about the methodologies. The only learning
policies actually implemented remain `SoftmaxPolicy` and
`ContextualSoftmaxPolicy` (`policy/softmax_bandit.py`,
`policy/contextual_softmax.py`).

| Methodology | ADR | Linked hypothesis | ADR status | Code |
|---|---|---|---|---|
| #8 Critique-to-evidence | ADR-014 | HYP-AL-005 | Proposed | none |
| #9 Thompson sampling | ADR-015 | HYP-AL-002 (see also HYP-AL-009) | Proposed | none |
| #10 UCB | ADR-016 | HYP-AL-009 | Proposed | none |
| #11 Epsilon-greedy | ADR-017 | none | Proposed | none |
| #13 DPO-style pairwise preference | ADR-018 | none | Proposed | none |
| #14 Meta-learning across policies | ADR-019 | none | Proposed | none |
| #15 Warm-start / prior transfer | ADR-020 | HYP-AL-008 | Proposed | none |
| #17 Authority ensemble routing | ADR-021 | none | Proposed | none |
| #22 Scored-search compilation | ADR-022 | HYP-AL-010 | Proposed | none |
| #23 Dueling-bandit ranking | ADR-023 | HYP-AL-015 | Proposed | none |

**Not covered by an ADR:** #12 (active evidence-seeking, only partially
built); #1, #7, #16 and #18 (ruled out or not applicable); and #2–6 and
#19–21 (already real, decided earlier). ADR-013 (subsidiary plan approval
gates) belongs to the planning redesign (ADR-011 chain), not to this
landscape.

**Reading of the exclusions, recorded so they are not mistaken for
permanent:** #1, #7, #16 and #18 are excluded under stated premises
(frozen model, no resettable environment, too few episodes to fit an
outcome model, single tenant), not on implementation experience, since none
of the ADRs above has been built. #18 is the one most likely to reopen,
should the hosted multi-tenant layer (HYP-AL-011) be pursued. Reopening
triggers are now recorded in the table rows.

**Count discrepancy, resolved 2026-10-25:** the §2.1 summary said 9
candidates but named ten; it now reads 9 / 3 / 1 / 1 / 18 = 32 after rows
#24-#32 were added. Rows #24-#32 have no ADR yet and none is requested.

#### 2.2 Hypothesis & Expected Value Premises

Per `docs/templates/ideation-document-template.md`'s own convention. Several
of these are not speculative — they were formulated, tested, and resolved
within this same session, against real episode data and real decisions
made for the SocialEngage project. That's unusual for an Ideation
document and worth keeping: these statuses are evidence-backed, not
aspirational.

##### 2.2.1 Core SDK Hypotheses (HYP-AL-001–011)

Validated directly against `agent-learning`/SocialEngage usage this
session — no cross-system or external-platform claims in this subset.

| ID | Type | Statement | Falsification criteria | Status |
|---|---|---|---|---|
| **HYP-AL-001** | ValueHypothesis | A 2–3 action softmax bandit, updated via REINFORCE-with-baseline from local/Azure-evaluator rewards, can let a recurring decision statistically earn autonomy (per complexity-tier gates) without any GPU training job. | If well-behaved, contrastive (not positive-only) episode data cannot cross a `standard`-tier autonomy gate within a few hundred episodes, invalidated. | **Validated** — `code-reviewer`/`choose-repository-search` crossed every gate (`eligible: true`) at 219 episodes this session, with `selection_mode` flipping to `autonomous-greedy`. |
| **HYP-AL-002** | TechnicalHypothesis | Positive-only (survivorship-biased) historical evidence cannot statistically earn autonomy for a low-authority bandit, no matter the volume, because the REINFORCE advantage signal vanishes once the baseline converges to the batch's uniform reward, leaving only the entropy bonus pulling back toward uniform. | If a bandit trained purely on all-correct data for one action does cross the probability/margin gates given enough episodes, invalidated. | **Validated** — `validate-intent-foundation`, trained on 146 real all-positive episodes, plateaued at ~0.417 probability and began *declining* after ~50 further training calls — mathematically incapable of reaching the required 0.75. |
| **HYP-AL-003** | FeasibilityHypothesis | `full` decision authority (`DecisionResolver`) can resolve a genuinely per-instance-varying decision correctly on the first attempt, with no training history at all, for decisions a fixed global bandit preference cannot discriminate. | If full-authority resolution produces an incorrect verdict on a well-evidenced real-vs-red-team contrastive pair, invalidated. | **Validated** — six TaskPolicies (`validate-intent-foundation`, `approve-adr`, `approve-brd`, `approve-fdd`, `approve-story`, plus `resolve-kb-conflict`'s low-authority contrast) each resolved a real artifact and a deliberately-flawed "red team" counterpart correctly, zero training required. |
| **HYP-AL-004** | AdoptionHypothesis | The packaged `ReinforceLearner`/`SoftmaxPolicy` path is sufficient for most real agent decisions, and the unpackaged `ContextualSoftmaxPolicy`/`ContextualReinforceLearner` example is not yet needed widely enough to justify exporting it as a first-class learner. | If adopters repeatedly hit a per-instance-varying decision and route around the missing contextual-bandit path by hand-building `full`-authority `DecisionFrame`s instead (as this session did), that is direct evidence *against* this hypothesis. | **Testing** — this session is itself one live data point against it: we hit exactly this gap on `validate-intent-foundation`, considered the example-only contextual bandit, and chose to hand-build `full`-authority frames instead because the contextual path would have required writing a custom training loop from scratch. Additional context, not direct evidence either way: Microsoft's own GitHub Copilot Auto and Azure AI Foundry Model Router (confirmed real, §2.1.1) are production systems solving exactly this decision shape — per-instance model selection weighing cost and quality — at Microsoft's own product scale. That confirms the underlying need is real and valuable, independent of whether this SDK's specific unpackaged contextual-bandit path is the right implementation for it; the two questions are orthogonal, not the same claim.<br><br>**Update — second real data point against this hypothesis's second half, 2026-10-22:** Microsoft's own Scout skill (`docs/scout-agent-learn-skill.md`, confirmed real — §2.1.2) does exactly what this hypothesis's falsification criteria names: for a per-instance-varying decision, it instructs building a hand-constructed `full`-authority `DecisionFrame` (e.g. its deployment-region example, criteria/evidence/constraints resolved per request) rather than using a contextual bandit. This is not Microsoft solving the same *shape* of problem elsewhere (that was already true — §2.1.1's Copilot Auto/Model Router citation) — this is the SDK's own maintainer, building Microsoft's own flagship agent, choosing the identical `full`-authority workaround this session chose for `validate-intent-foundation`. Two independent real data points (this session's own SocialEngage work, and now Scout) both route around the missing contextual path the same way — precisely the pattern this hypothesis's own falsification criteria treats as evidence *against* its "not yet needed widely enough to justify exporting it" half. The hypothesis's first half — that the packaged marginal path is sufficient for *most* decisions — remains separately supported: Scout's skill still uses `low` authority extensively for stable, bounded choices (e.g. `choose-azure-pubsub-message-processor`). Status kept at **Testing** rather than moved to Invalidated: this is a compound claim and only its second half has now accumulated real counter-evidence — a single uniform verdict across both halves would overstate what's been found, the same distinction HYP-AL-012 already draws for its own three layers. |
| **HYP-AL-005** | ValueHypothesis | ERL-style experience-reflection-retry learning (named in `docs/experiential-reinforcement-learning-comparison.md` as explicitly *not* implemented) would converge faster or more sample-efficiently than REINFORCE on decisions where textual feedback is already available (e.g. this session's own "Red Team" critique episodes). | Implement a reflection-based update path; if it does not converge faster/more sample-efficiently than REINFORCE on the same real episode data, invalidated. | **Formulated** — not yet attempted. The raw material to test it already exists: this session's two-round, eleven-amendment review of ADR-0146 is exactly the kind of textual-feedback signal REINFORCE currently cannot consume at all. |
| **HYP-AL-006** | FeasibilityHypothesis | Treating the last accepted artifact as a frozen baseline and classifying only what *changed* in a new candidate (diff/baseline methodology, methodology #20 above) can correctly distinguish a real decision-change from a mere clarification/amendment, using `full` authority with no training history. | If `classify-diff-type` misclassifies a genuine decision change as a cosmetic diff (or vice versa) on a well-evidenced real case, invalidated. | **Validated** — tested against three real/constructed cases this session: the ADR-0017-19 parameter case correctly resolved to `amendment_log_entry`; a disguised-decision-change red-team case correctly resolved to `new_superseding_adr` despite "minor tweak" framing; the ADR-0145 correction case correctly produced `needs_user_tie_break` (correction_note 0.214 vs. clarification_section 0.195) rather than a false-confident wrong answer. |
| **HYP-AL-007** | ValueHypothesis | Whether a given diff-type *category* (not a specific instance) typically warrants escalation to a human is a stable, repeated question that `low`-authority REINFORCE can legitimately learn from aggregate outcomes, unlike the per-instance `classify-diff-type` judgment itself. | If `escalate-diff-response`, once given real training episodes, cannot cross a `standard`-tier autonomy gate despite well-behaved contrastive data, invalidated — the same test HYP-AL-002 already applied elsewhere. | **Formulated** — `escalate-diff-response` is initialized (`low` authority, 3 actions) but has zero registered episodes; this is the next real test of the full diff-classification pipeline, not yet run. |
| **HYP-AL-008** | FeasibilityHypothesis | Seeding a new `TaskPolicy`'s initial state from a converged, structurally similar existing policy (methodology #15, §2.1 — "warm-start / transfer of priors") reduces the episodes needed to reach autonomy-eligibility, compared to a cold uniform start. | If a policy warm-started from a converged source reaches its autonomy gate in the same or more episodes than an equivalent cold-started policy, invalidated. | **Formulated** — originated in `Business-Case.md` §4 (Option A), carried back here for registry consistency. Depends on an unverified assumption, flagged in the Business Case's §7 Dependency Matrix: that `SoftmaxPolicy` actually exposes its converged internal state for reuse — not yet confirmed against the real class. |
| **HYP-AL-009** | TechnicalHypothesis | A confidence-interval-based bandit (Thompson sampling or UCB, methodologies #9–10, §2.1) can cross the same autonomy gate that defeated REINFORCE under positive-only evidence (HYP-AL-002), without migrating the decision to `full` authority. **UCB / Wilson-bound adaptation is the preferred first implementation, not Thompson sampling** — reasoned from this project's own auditability constraint (§1.2 Objective 2), flagged on `Project-Charter.md` review: UCB is deterministic given the same statistics, consistent with the SDK's existing deterministic Wilson lower bound; Thompson sampling is stochastic and would need explicit RNG-seed capture to stay replayable. | If Thompson/UCB, run against the same real `validate-intent-foundation` 146-episode dataset that defeated REINFORCE, also fails to cross the gate, invalidated — the failure would then be inherent to positive-only evidence itself, not specific to REINFORCE's entropy-bonus mechanics. | **Formulated** — originated in `Business-Case.md` §4 (Option C), added after external review correctly identified this as the hypothesis most directly supported by this project's single strongest piece of proven evidence (HYP-AL-002), carried back here for registry consistency. |
| **HYP-AL-010** | FeasibilityHypothesis | Offline, derivative-free scored-search (methodology #22, §2.1 — DSPy-style compilation, externally validated as a real industry pattern this session) can find `DecisionResolver` criteria weights/evidence-trust parameters that resolve a labeled validation set of past decisions more accurately than this session's own hand-set weights (e.g. `classify-diff-type`'s 0.5/0.25/0.25 split). | If search over the same weight space, scored against the same labeled set, cannot find a configuration that outperforms the hand-set weights by a meaningful margin, invalidated — hand-tuning would then be shown to already be close to optimal for these small criteria spaces. | **Formulated** — added this session directly from the cross-framework research (§2.1.1); not yet attempted. The labeled set already half-exists as this session's own six resolved real-vs-red-team contrastive pairs, though a larger set would be needed for a fair test. |
| **HYP-AL-011** | AdoptionHypothesis | A managed, hosted governance-as-a-service layer built on top of `agent-learning` (audit dashboards, a policy-template library, compliance reporting) — distinct from the free, open-source SDK itself — would be something real adopters value enough to pay for. | If real prospective customers, asked directly (not hypothetically) or tested against a real price point, decline to pay anything for this layer, invalidated. | **Formulated — reframed, 2026-10-22: not resolvable by this project's own research methods.** Originated in `Project-Charter.md` §5 (End-User Value Analysis), added when asked directly whether Phase 1's amendments would be something an end user would pay for. This is not a gap that more document or code research would close — every other hypothesis in this registry can be advanced that way (reading code more carefully, checking git history, finding a real fixture); this one cannot, because "will a real prospective customer pay for this" can only be answered by actually asking real prospective customers or running a real pricing test. No amount of further repository archaeology produces that evidence. `Project-Charter.md`'s M0.5 research phase was separately resolved to **Go** on 2026-10-22, on the real-case-evidence condition alone (ADPA's provider-selection and quality-gate data, and the confirmed Scout integration, §2.1.2) — explicitly independent of this hypothesis, per M0.5's own "and/or" disposition rule. HYP-AL-011 therefore stays open, deliberately, as a separate question from whether Phase 1's technical work proceeds — not a loose end blocking it, and not resolved by the Go decision either. |

##### 2.2.2 Cross-System & Ecosystem Integration Hypotheses (HYP-AL-012–017)

Tests whether this SDK's methodologies apply to real decision points in
sibling systems outside `agent-learning` itself — ADPA, RPAS-BA-Workbench
/ SIDPA, and (HYP-AL-017) an external submission to Vercel's AI Gateway.
Source files cited below are therefore TypeScript
(`qualityRegressionDetector.ts`) and C# (`SolutionEvaluationModels.cs`),
not the Python SDK.

| ID | Type | Statement | Falsification criteria | Status |
|---|---|---|---|---|
| **HYP-AL-012** | TechnicalHypothesis | A confidence-interval-based bandit (UCB/Thompson, the same methodology as HYP-AL-009) can replace ADPA's hand-set quality-gate constants at **three separate layers**, each currently a static number applied uniformly instead of calibrated per template/rule: (1) template-regression — a flat 15-percentage-point quality-drop trigger (`qualityRegressionDetector.ts`); (2) template-health — a flat 70-point per-document success cutoff, 60-point critical-health cutoff, and static 0.4/0.4/0.1/0.1 weighted-average formula (`templateHealthService.ts`); (3) compliance-rule — each `ComplianceRule`'s own hand-set `thresholds.pass/warning/fail` and `weight` (`modules/compliance/types.ts`, seeded per-pack in `pmbokRuleset.ts`/`babokRuleset.ts`/`dmbokRuleset.ts`). All three would calibrate from real per-template or per-rule outcome history instead of one constant applied everywhere regardless of natural score variance. | If a bandit/confidence-interval approach, run against real historical data for templates/rules with enough usage volume (the same real-episode-stream requirement HYP-AL-009 already applies), produces no fewer false regression/non-compliance triggers (on templates or rules that held stable) and no fewer missed regressions (on ones `template_audits`/`compliance_audit_trail` history shows genuinely degraded) than the current flat thresholds, invalidated. Each of the three layers is falsifiable independently — this hypothesis can be partially validated (e.g. layer 1 confirmed, layer 3 invalidated) rather than needing a single uniform verdict across all three. | **Formulated** — corrected twice after further verification, not blocked the way this entry originally read. First drafted assuming no outcome data existed anywhere in ADPA's quality-gate pipeline; re-checked directly against `qualityRegressionDetector.ts` and `templateHealthService.ts` and found that's wrong for layers 1–2 — `quality_audits.overall_score` already accumulates a real per-document, per-template time series (`getQualityTrends` already computes a daily series from it). Layer 3 folded in after confirming `complianceValidationEngine.ts`'s write *path* is real, not just typed interfaces: `compliance_validation_results`, `compliance_rule_results`, and `compliance_audit_trail` have real `INSERT`s (lines 1149, 1209, 1327).<br><br>**Correction, 2026-10-22: that is not the same claim as real historical rows existing, and this entry previously conflated the two.** `docs/07-architecture/EMPTY_TABLES_PURPOSE_AUDIT.md` (ADPA, dated 2026-07-05) lists all three compliance tables among those confirmed to hold **zero rows** at that time — "wired" there means the write path is real, empty means the feature hadn't produced data yet in that environment. No live database check exists to confirm whether that has changed in the 3.5 months since. Layer 3's real-episode-stream prerequisite is therefore **unconfirmed, not established** — downgraded from this entry's earlier claim. Layers 1–2's `quality_audits` table is not named anywhere in that same empty-tables audit, which is weaker, indirect evidence it likely does hold real rows (an audit of empty tables that omits a table is some signal, not a row count) — a meaningfully different confidence level than layer 3's confirmed-empty-as-of status, not the same one this entry previously gave all three layers. A narrower, genuinely separate question — whether a human later confirmed or overturned a `flagged`/`fail` audit verdict itself (template or compliance) — remains unlogged at any of the three layers (checked `templateAuditService.ts`, no override field exists); that question is out of scope for this hypothesis as now scoped, not evidence that this one is blocked too. |
| **HYP-AL-013** | FeasibilityHypothesis | A `low`-authority `TaskPolicy`, trained on real paired data already captured in ADPA's `governance_audit_ledger` (the DRACO tribunal's AI verdict — approved/rejected, rationale, confidence score — alongside the human auditor's actual adjudication decision and schema-enforced mandatory override rationale, recorded via `POST /ledger/:auditId/adjudicate` in `councilRouter.ts`), can learn which categories of DRACO tribunal verdicts a human reliably agrees with vs. overrides — the same category-level REINFORCE pattern already validated for `escalate-diff-response` (HYP-AL-007), applied to a fourth real decision point (ADPA's Governance Council) distinct from SocialEngage diff classification and from HYP-AL-012's template/compliance quality gates. | If a `TaskPolicy` trained on real verdict-vs-human-decision history from the ledger cannot cross a `standard`-tier autonomy gate despite well-behaved contrastive data, invalidated — the same test HYP-AL-002/006/007/012 already apply elsewhere. If the ledger's human decisions turn out to rubber-stamp the AI verdict in all or nearly all cases (no real disagreement to learn from), the data exists but isn't actually contrastive, and the hypothesis is untestable as scoped — a distinct failure mode from invalidation, the same distinction HYP-AL-012 already draws. | **Formulated** — not yet attempted, and its prerequisite is the inverse of HYP-AL-012's: that hypothesis's three layers all have real per-item outcome data but no recorded human-override signal; this one has exactly the human-override signal HYP-AL-012 named as missing, just for a different decision (Council adjudication, not template/compliance scoring). Confirmed via `councilRouter.ts` (found during this session's HIL-point survey): every adjudication records the AI tribunal's verdict and the human's decision + rationale side by side in `governance_audit_ledger`. Not yet checked: real ledger volume (how many adjudications exist) and whether human decisions are contrastive enough to train on — both left as open empirical questions rather than assumed, the same way HYP-AL-009 doesn't assume its own dataset's adequacy ahead of testing it. |
| **HYP-AL-014** | TechnicalHypothesis | A confidence-interval-based bandit (UCB/Thompson, the same methodology as HYP-AL-009/012) can replace a *third* real system's hand-set quality constants: RPAS-BA-Workbench's SIDPA / Solution-Evaluation module (BABOK KA6). Specifically — the Enterprise Value Index's five compiled composite floors (`EviCompositeFloor=85`, `PowerScoreFloor=80`, `CostScoreFloor=80`, `LatencyScoreFloor=75`, `ReliabilityScoreFloor=85`, all `const double` in `SolutionEvaluationModels.cs`); `CapabilityLeakyBucketAccumulator`'s incident threshold (10.0) and decay rate (0.1/day); the documented Benefit-Realization-Index (≥80%) and Knowledge-Loop-Propagation-Rate (>65%) alert targets; and the narrower, textually-described "variance delta exceeded -15% threshold" SIDPA lesson-learned trigger — with thresholds calibrated from each solution instance's own real benefit/telemetry history instead of one constant applied across every deployed solution. | If a bandit/confidence-interval approach, run against real historical KPI/benefit data for solution instances with enough telemetry volume (the same real-episode-stream requirement HYP-AL-009/012 already apply), produces no fewer false floor-breach/lesson-learned triggers and no fewer missed real degradations than the current flat constants, invalidated. Untestable as scoped, not merely unvalidated, if either (a) the -15% SIDPA trigger turns out to be seed/demo text only with no live executing comparison anywhere in the real service code, or (b) no persisted historical telemetry exists beyond in-memory seed collections — both left open rather than assumed either way. | **Formulated** — the weakest-verified of this project's cross-system hypotheses so far, named as such rather than overstated. Confirmed directly from `SolutionEvaluationModels.cs`: the five EVI floors are compiled `const double` constants (strongest form of confirmation — not seed data, not runtime-configurable); `CapabilityLeakyBucketAccumulator`'s threshold/decay are default property values (weaker — could be overridden per capability, not checked either way); `BenefitRealizationIndex`/`KnowledgeLoopPropagationRate` targets are documented in XML doc comments with corresponding `*ThresholdAlert` boolean fields present on the class, confirming an alert mechanism exists in the data model, though its comparison logic wasn't read. The "-15% variance" SIDPA trigger, by contrast, was found only inside a seeded example `GovernedLessonLearnedEntity` built in `SolutionEvaluationService.cs`'s in-memory demo data (`_lessonsLearned.AddRange(...)`) — confirmed as a real description of the intended rule, **not** confirmed as live executing trigger logic; the actual comparison code, if any, has not been located. Real telemetry/outcome-data persistence (a database vs. in-memory seed collections) is entirely unchecked. Three explicit open dependencies, none assumed: (1) is the -15% trigger live code or only descriptive seed data, (2) does historical telemetry persist anywhere beyond seed collections, (3) real data volume per solution instance. Drafted now with these named rather than resolved, per this session's own choice to write up confirmed findings before investigating `SolutionEvaluationService.cs` further.<br><br>**Update, EVI sub-claim only:** `CalculateEnterpriseValueIndex()` (lines 896–990) is now confirmed **live, executing code**, not seed data — resolving open dependency (1) for the EVI floors specifically (the -15% SIDPA trigger's liveness is still unconfirmed). The formula itself is now fully known: four sub-scores (power/cost/latency/reliability), each computed against further hand-set constants beyond the floors (`targetTokJ=21.0`, `tdpCeiling=500.0`, `costCeiling=0.0018`, `latBaseline=35.0`), combined via hand-set composite weights `0.35/0.30/0.20/0.15` — a fourth and fifth layer of hand-set constants on top of the five floors already named. Open dependency (2) is now **confirmed absent, not just unchecked**: `_currentEvi` (line 47) is a private in-memory instance field, overwritten on every call — there is no history table, so zero historical EVI time-series exists today to calibrate anything from. The service also enforces a real "composite laundering" invariant (a high composite score is overridden to `CriticalDeficit`/`HALT` if any sub-score still breaches its floor) — any future calibration of the floor values must preserve this invariant rather than let a learned floor drift to avoid ever triggering it. |
| **HYP-AL-015** | FeasibilityHypothesis | An adaptive pairwise-comparison mechanism (dueling-bandit / active-ranking methodology — registered this session as Methodology #23, Ideation §2.1, distinct from the existing 22-methodology landscape) can reduce the number of human head-to-head judgments ADPA's portfolio prioritization currently forces: `PairwiseComparisonMatrix.tsx` generates every unique pair exhaustively (`n*(n-1)/2` — 190 manual comparisons for 20 projects), with no adaptive selection of which pair to ask next. Separately, a principled preference model (e.g. Bradley-Terry) could replace the current ad-hoc confidence-weighted-win-rate heuristic (min-max normalized, no statistical grounding) with ranks that carry real uncertainty bounds instead of a single point estimate. | If an adaptive pair-selection strategy, tested against a reconstructed or newly collected set of real pairwise judgments, does not reduce the comparisons needed to reach the same ranking confidence as today's exhaustive approach, invalidated. Untestable as scoped, not merely unvalidated, until the raw pairwise judgment data this hypothesis needs is actually collected — confirmed absent today, not assumed (see Status). | **Formulated** — blocked on a confirmed prerequisite, the strongest-confirmed blocker of any hypothesis in this registry so far (HYP-AL-012/014's gaps were calibration-only; this one has no raw data to even retrospectively analyze). Checked directly: grepped the whole `server/src` tree for `project1_id`/`winner_id`/a pairwise-comparison-history table — zero hits. `PairwiseComparisonMatrix.tsx` holds each individual comparison only in React component state (`useState<Comparison[]>`) and discards it once the aggregated `{project_id, priority_score, rank}` triples are POSTed to `prioritizationService.ts` — which itself only persists the final numbers under a synthetic "Pairwise Comparison" criterion, never the underlying judgments. This would need new persistence (an individual-comparison table) before it's testable at all. Resolved this session, previously left open: dueling-bandit/active-ranking methodology does not sit cleanly in the existing 22-methodology landscape — distinct from both #12 (single-instance evidence-seeking) and #13 (passive pairwise preference learning from an already-collected dataset) — and has been registered as a new **Methodology #23** in §2.1. |
| **HYP-AL-016** | TechnicalHypothesis | A `low`-authority `TaskPolicy` can replace SIDPA's illustrative, static Confidence Factor (CF) rating bands (`AAA=1.00`/`AA=0.95`/`A=0.90`/`BBB=0.85`, prospectus §X.4) with a calibrated, auditable scoring mechanism learned from real governance/audit signals — the same category-level REINFORCE pattern already validated for `escalate-diff-response` (HYP-AL-007) — and can similarly calibrate the Accuracy Factor (AF, "ratio of validated outputs to total outputs") from real validated/invalidated output pairs, the same contrastive-evidence requirement HYP-AL-002 already proved REINFORCE needs. This directly answers the prospectus's own stated requirement (§X.9): CF/AF weightings and rating scales are explicitly illustrative and "must be established through the governance process," and any published metric "invites optimization toward the metric itself" — a risk a small, auditable, governed `TaskPolicy` is better positioned to resist than an opaque model, consistent with this SDK's own frozen-model, interpretable-policy constraint. | If a `TaskPolicy` trained on real governance/audit signals (CF) or real validated/invalidated output pairs (AF) cannot cross a `standard`-tier autonomy gate despite well-behaved contrastive data, invalidated — the same test HYP-AL-002/007 already apply elsewhere. Untestable as scoped, not merely unvalidated, until real IPC exists to generate either signal in the first place (see Status). | **Formulated** — two confirmed blockers, plus a third question deliberately left open rather than resolved unilaterally. (1) True IPC does not exist in code: `EnterpriseValueIndexEntity`/`CalculateEnterpriseValueIndex()` implements a weighted-additive hardware-efficiency composite (`0.35×power + 0.30×cost + 0.20×latency + 0.15×reliability`), not the prospectus's multiplicative `RC × AF × AV × CF` form — confirmed by direct comparison against the prospectus's Chapter X formula and worked example (Provider A: RC=100, AF=95%, AV=99%, CF=0.95 → IPC=89.3). (2) No real validated/invalidated output history or governance-audit-signal history exists yet, since nothing currently computes AF or CF at all — this hypothesis cannot be tested until a real IPC implementation exists and begins accumulating that history. (3) Naming convention is unresolved, flagged explicitly rather than assumed: whether RPAS-BA-Workbench's existing `EnterpriseValueIndex` should be renamed to avoid confusion with a future real IPC, kept as a distinct Compute-Capital-layer metric alongside a new Intelligence-Capital-layer IPC, or something else — the user's own call, not decided here. |
| **HYP-AL-017** | FeasibilityHypothesis | A `low`-authority `TaskPolicy`, restricted at selection time to a task-capability-filtered candidate pool (only models verified capable of the task class in question — e.g. embedding models for embedding tasks, reasoning-capable models for multi-step tasks — mirroring SIDPA's IPC-class concept, prospectus §14: "classification allows buyers to match workloads to capacity of appropriate quality"), can learn a weighting that predicts each candidate's actual achieved outcome quality for that task class from real per-selection outcome history, rather than selecting on cost or capability-tier alone — the same confidence-interval bandit methodology already proposed for HYP-AL-009/012/014/016, now applied to model/provider selection itself rather than to a quality-gate threshold. This is the learned-selection core of the user's broader "AI Exchange" proposal (task-restricted pools + spot/contract pricing, SIDPA §14.2–14.4); the pricing-mechanism half is deliberately left un-hypothesized here, named as a separate, not-yet-formulated market-design question distinct from this selection-learning claim. | If a `TaskPolicy` trained on real per-selection outcome-quality data (within a task-capability-restricted pool) cannot cross a `standard`-tier autonomy gate despite well-behaved contrastive data, invalidated — the same test HYP-AL-002/007/013 already apply elsewhere. Untestable as scoped, not merely unvalidated, if (a) no task-capability taxonomy/restriction mechanism exists anywhere to build the candidate pool from, or (b) no real per-selection outcome-quality data is ever recorded (confirmed absent today, not assumed — see Status). | **Formulated** — genuinely new, not a calibration of an existing mechanism the way HYP-AL-012/014/016 are. Real precedent confirmed for the *selection* half (GitHub Copilot Auto, Azure AI Foundry Model Router, §2.1.1), but both are closed Microsoft systems — their actual weighting/training data is not inspectable, so they validate that the need is real, not that any specific mechanism works. No task-capability taxonomy, candidate-pool-restriction logic, or per-selection outcome-quality history exists anywhere in agent-learning, ADPA, or RPAS-BA-Workbench today — this would be built from scratch. Deliberately scoped to the learning/selection question only; the spot-price/reservation-contract market-mechanism half of the "AI Exchange" idea (SIDPA §14.3–14.4) is named but not hypothesized here — a market/pricing-design question, not a falsifiable ML claim in the shape this registry's other entries take, and would need its own framing before being added.<br><br>**Update — external submission, 2026-10-21:** The selection half described above was independently drafted as a public feature proposal and submitted upstream as a GitHub issue against Vercel's AI Gateway (`vercel-labs/ai-sdk-gateway-demo` issue #39, https://github.com/vercel-labs/ai-sdk-gateway-demo/issues/39 — confirmed via direct fetch: open, filed 2026-10-21, no comments yet), proposing a `quality` sort mode alongside AI Gateway's existing `cost`/`ttft`/`tps` routing, scored via either static capability rankings or live outcome telemetry. This is a different system than any named in §2.1.1/§2.2 (Vercel AI Gateway, not ADPA/RPAS-BA-Workbench/SocialEngage) and a real external artifact rather than an internal hypothesis, so it does not itself validate or invalidate this hypothesis's own falsification criteria — no training/outcome data exists for it either. Worth naming deliberately, not silently: the posted issue's Precedent section retains two sentences referencing a future "AI Exchange" where AI prompts route through an exchange and are treated "as a commodity and tradeable assets" — language that directly contradicts that same issue's own Scope section a few paragraphs later, which explicitly excludes marketplaces/spot-pricing/auctions/futures. Confirmed present in the live posted text (re-fetched and quoted verbatim), not an artifact of drafting. Left in on purpose, per explicit instruction, as a live external probe of how strictly outside reviewers (Vercel maintainers, GitHub commenters) distinguish "quality-aware Gateway routing" and provider-side "auto route" features from the market-pricing "AI Exchange" framing this hypothesis's own text already splits apart. Any resulting public reaction (or its absence) would be the first real external signal on the market-framing question this hypothesis explicitly declines to formulate on its own — tracked here, not yet resolved. |

##### 2.2.3 Candidate-Methodology Hypotheses (HYP-AL-018-024), registered 2026-10-25

Each tests one of the new candidates (#24, #26, #28-#32). All are
**Formulated**, none is tested, and none depends on an unapproved ADR. The
numeric targets are **proposed thresholds**, not agreed ones; they are to
be confirmed or changed by the maintainer before any hypothesis is
scheduled. #25 has no hypothesis because it is blocked on the `trace_id`
decision.

| ID | Type | Statement | Falsification criteria | Status |
|---|---|---|---|---|
| **HYP-AL-018** | TechnicalHypothesis | A linear contextual bandit (LinUCB or LinTS, #24) reaches the autonomy gate in fewer episodes than `ContextualSoftmaxPolicy` on the same contextual decision (candidate: `classify-diff-type`). | If, on the same episode set, it needs as many or more episodes to reach the gate (proposed margin: at least 20% fewer is required to keep the hypothesis), invalidated. | **Formulated** |
| **HYP-AL-019** | TechnicalHypothesis | A conformal abstention rule (#28) over a `low`-authority policy's scores produces a calibrated "defer to a human" trigger. | If, on held-out episodes, the share of wrong autonomous decisions among non-abstained cases exceeds the configured error level (proposed: 10%) by more than sampling error, invalidated. Untestable until enough labeled outcomes exist. | **Formulated** |
| **HYP-AL-020** | TechnicalHypothesis | Off-policy evaluation (#29) over logged episodes ranks candidate policies in the same order as running them. | If the OPE ranking disagrees with the realized ranking on a policy pair with a known winner, invalidated. Blocked until the logged action probability is recorded on `Episode`. | **Formulated** |
| **HYP-AL-021** | TechnicalHypothesis | A discounted or windowed update (#30) recovers faster than the current cumulative update after a change in the reward distribution. | If, on a replayed shifted reward sequence, recovery to the pre-shift policy quality takes as many or more episodes than the cumulative update, invalidated. Needs a real or replayed drift case. | **Formulated** |
| **HYP-AL-022** | FeasibilityHypothesis | Hard action masking (#31) can enforce ADR-011's floors and caps without lowering achievable reward below the unmasked policy by more than a stated margin. | If any masked-out action is ever selected, or reward falls by more than the proposed margin (5%) on a replay, invalidated. | **Formulated** |
| **HYP-AL-023** | ValueHypothesis | Active-learning triage (#32) lets a fixed human review budget catch more incorrect autonomous decisions than random sampling. | If at equal review budget it catches no more errors than random sampling, invalidated. | **Formulated** |
| **HYP-AL-024** | FeasibilityHypothesis | Outcome-conditioned exemplar selection (#26), with the selection recorded in `Episode.metadata`, improves a `full`-authority decision's accuracy over using the most recent episodes. | If accuracy on held-out cases is no better than the recency baseline, or the selection cannot be reconstructed from the record, invalidated. | **Formulated** |

---

### SECTION 3: STAKEHOLDER MANAGEMENT & RACI REPRESENTATION

#### 3.1 Stakeholder Register

| Stakeholder | Role / Interest |
|---|---|
| Microsoft (maintainer org) | Owns the repo, PyPI package, and release cadence |
| External contributors (e.g. `MargoOs`, `adityasinha-aiplan`, `meiwa7`, per recent PR history) | Land features (Spark scoring, cost-model docs, README improvements) via PR |
| SDK adopters / agent builders | Consume the package to add a decision layer to their own agent; the actual target users of every objective above |
| The human adjudicating a `low`-authority tie-break or a `full`-authority `needs_user_feedback`/`needs_user_tie_break` result | Not a passive stakeholder — a required participant in the SDK's own designed workflow |

#### 3.2 Communication Management Strategy & Routing Channels

GitHub Issues/PRs is the real, observed channel (merge commits, Dependabot
updates, contributor PRs all visible in `git log`). No separate project
communication plan exists today.

#### 3.3 RACI Matrix

[Not yet formalized — this project currently operates as an open-source
repo with maintainer review on PRs, not a staffed RACI structure. Naming
this gap rather than inventing a fictional RACI table.]

---

### SECTION 4: SCOPE, WBS, AND LIFECYCLE TAILORING ARCHITECTURE

#### 4.1 Scope Statement

**In scope today (real, packaged, production):**
- `low` and `full` decision authority under one `TaskPolicy`
- `SoftmaxPolicy` + `ReinforceLearner`
- `DecisionResolver` (Bayesian evidence aggregation, constraints, Pareto, robust utility)
- Local stdlib + optional Azure AI evaluator scoring
- In-memory, local-file, and Cosmos DB storage backends
- Audit & replay of a recorded training update
- Distributed scoring via PySpark (`score_episode_dataframe`) — scoring only, not distributed training

**Explicitly out of scope today (real gaps, not hidden):**
- `ContextualSoftmaxPolicy` as an exported, trainable, CLI-reachable learner (example-only)
- Any ERL-style reflection/retry/internalization mechanism
- A packaged RACI/stakeholder-management layer for the project's own governance (this document is the first attempt at that)

#### 4.2–4.9

[PMBOK knowledge-area mapping, WBS, schedule, cost, HR, procurement, and
change-management sub-sections from the template are not filled in for
this first pass — this is an open-source SDK with a volunteer/maintainer
contribution model, not a staffed, budgeted project in the sense the
template's enterprise framing assumes. Naming that mismatch rather than
forcing irrelevant ceremony.]

---

### SECTION 5–9

[TOGAF architecture viewpoints, SABSA trust model, DMBOK data governance,
risk register, and lifecycle roadmap sections are deferred for the same
reason as 4.2–4.9 — they apply naturally to a multi-tenant SaaS product
like SocialEngage, less naturally to a Python SDK distributed via PyPI.
A future pass should decide, deliberately, whether any of these add real
value here rather than skipping them by default.]

---

### SECTION 10: ARCHITECTURAL DECISION LOGS

#### 10.1 Formal Decision, Alternative Analysis & Rationale Log

**Decision — Document this project using the same PM-governance
discipline as SocialEngage, rather than inventing a lighter-weight
scheme.** Alternatives: (A) skip formal Ideation/Hypothesis documentation
entirely, given this is "just an SDK"; (B) write a minimal README-style
roadmap instead. **Rationale (chosen: full discipline, scoped
honestly):** the same rigor that caught real gaps in SocialEngage's own
documents (the missing Hypothesis stage, the Location-tab governance
conflict) is exactly the rigor this project's own learning-variant
landscape needed — HYP-AL-002 and HYP-AL-004 above are real findings this
session surfaced that a lighter-weight roadmap would have missed
entirely.

---

## Provenance & Completeness Self-Assessment

| Field | Status |
|---|---|
| Executive Summary & learning-variant landscape | Sourced directly from code (`reinforce.py`, `softmax_bandit.py`, `contextual_softmax.py`, `decision.py`) and this session's real usage |
| Objectives | AI-inferred from the above, cross-checked against `README.md`'s stated goals |
| Learning Methodologies Landscape (§2.1) | 32 methodologies surveyed (23 original, 9 added 2026-10-25) against this project's real constraints, not the literature in the abstract — 9 real or partly real, 4 structurally ruled out or not applicable (premise-conditioned, with reopening triggers), 1 declined, 18 genuine not-yet-built candidates (added #23, dueling-bandit/active-ranking pairwise comparison, resolving an open question previously left on `HYP-AL-015`). §2.1.1 cross-checks this landscape against eight real external agent SDKs/platforms (LangGraph, AutoGen, Semantic Kernel, CrewAI, OpenAI Agents SDK, DSPy, Haystack, and Microsoft's GitHub Copilot Auto / Azure AI Foundry Model Router), each cited to real documentation — four had no learning mechanism at all, three validated existing entries (AutoGen→#7/8, CrewAI→#6, Microsoft→#4/#9–10), one (DSPy) added #22. A second review proposed five more candidates; none survived verification against already-cited evidence (one freshly re-checked against CrewAI's current memory docs) — not added, reasoning recorded in §2.1.1 |
| ADR coverage (§2.1.3) | Checked against `docs/adr/` and `src/agent_learning/policy/` on 2026-10-25: ten Proposed, untracked ADRs (ADR-014 to ADR-023), none approved, none built. Recorded as drafts, not evidence. A count discrepancy in §2.1 (9 stated, 10 listed) is flagged, not fixed |
| Confirmed Production Adoption (§2.1.2) | Not inferred from doc text: `docs/scout-agent-learn-skill.md` and `docs/scout-automation-agent-learning.md`'s authorship confirmed via `git log --follow` (`ctava-msft`, 10 commits, 2026-08-07–10, same author as `docs/research/main.tex`); the `policy_scope`/`delegated_decision`/`decision_authority` fields they describe confirmed implemented in `src/agent_learning/decision.py`/`cli.py`/`audit.py` with dedicated tests, not just described. HYP-AL-004 status corrected accordingly, not left stale |
| Hypotheses (§2.2) | **4 of 24 validated this session with real citations; 1 testing; 19 formulated** — not aspirational. Split into §2.2.1 (Core SDK, HYP-AL-001–011), §2.2.2 (Cross-System & Ecosystem Integration, HYP-AL-012–017) and §2.2.3 (candidate-methodology hypotheses, HYP-AL-018–024, added 2026-10-25 with proposed, unconfirmed thresholds) this session for readability. HYP-AL-011 reframed 2026-10-22: unlike every other entry, it cannot be advanced by this project's own research methods — flagged as a distinct category, not left to look like an oversight. |
| Stakeholders | Sourced from real `git log` contributor history |
| Scope (§4.1) | Sourced directly from package exports (`__init__.py`'s `__all__`) and `experiential-reinforcement-learning-comparison.md`'s own stated scope boundary |
| Sections 4.2–9 | Explicitly not populated — named as a scope mismatch, not silently skipped |
| Downstream documents | `Business-Case.md` (v1.3) built on §2's hypotheses; `Project-Charter.md` (v1.0) formalizes Phase 1 (HYP-AL-008/009) with named resource requirements and a resourcing gate before Phase 2 — this Ideation document is now the first link in a real three-document chain, not a standalone artifact |
