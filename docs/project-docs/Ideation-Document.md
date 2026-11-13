---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Initiating"
pmbok_process: "Pre-Project / Design Assumption Formulation (Cognitive Feedback)"
lifecycle_stage: "Stage 1 (Intent)"
governance_policy: "approve-ideation"
artifact_id: "ideation-document"
version: "1.21"
phase: "Phase 3"
pmp_baseline: "PMP-BL-v1.1.0"
target_pmp_baseline: "PMP-BL-v1.2.0"
lineage_kernel_hash: "579b62bfe11607b2287b16a99fdc36d14350fe864ffef1d60a8ca1712247c8b8"
inputs:
  - "Spark-Capture.md (v3.0)"
  - "Stage 18 Intent Refinement Proposal (IRP-20261111-001)"
  - "Phase 2 Close Decision (PCD-20261111-001)"
  - "Cumulative Lineage Kernel (CLK-20261111-001)"
outputs:
  - "Ideation-Document.md"
  - "Project-Charter.md"
---

# Ideation Document — agent-learning SDK

## 📋 DOCUMENT HEADER METADATA BLOCK

| Field | Value |
|---|---|
| Document Title | Ideation Document — agent-learning SDK |
| Version | 1.20 |
| Date | 2026-11-12 |
| Updated | 2026-11-12 (v1.21): Fixed a stale "Stage 3 hypothesis" reference (§2.2 item 3, autonomous bidding agents) to "Stage 2," following the Initiating-group renumbering. Earlier 2026-11-12 (v1.20): **Section 5–9 partly superseded by Stage 7** — the risk register and lifecycle roadmap it deferred now exist (`Risk-Management-Plan.md`, `Project-Management-Plan.md`); TOGAF/SABSA/DMBOK stay an honest, separate exclusion, not a Stage 7 gap. Earlier 2026-11-12 (v1.19): **Section 10 (Architectural Decision Logs) superseded by Stage 5's real ADR process** — `Project-Pillars.md` and the 38 approved ADRs under `docs/adr/` already do, far more rigorously, what this section's one meta-decision entry was standing in for. Earlier 2026-11-12 (v1.18): **Section 3 (Stakeholder Management & RACI) superseded by `Stakeholder-Register.md`** — Stage 4's real Charter input, v2.0, already has 7 named stakeholders and a full 18-stage RACI matrix; Ideation's own 4-row table and "RACI not yet formalized" note were stale. **Section 4 (Scope, WBS & Lifecycle Tailoring) superseded by Stage 7's nine real subsidiary plans** — all exist and are filled in (`docs/project-docs/management-plans/`); the real Scope Statement and WBS live in `Scope-Management-Plan.md`. Both sections replaced with pointers, same pattern as the §2.2 hypothesis extraction. Earlier 2026-11-12 (v1.16): **Hypotheses extracted to `Hypothesis-Register.md`** (Sponsor decision) — §2.2.1–2.2.4 (all `HYP-AL-NNN` statements, falsification criteria, status) moved verbatim out of this document into Stage 2's own register, so Stage 2's ongoing classification work no longer requires reopening this Stage 1 artifact. §2.2.5 renamed §2.2 "Phase 3 Seeding & Carry-Over Disposition"; its hypothesis-count item now points at the register instead of restating it. `lifecycle_stage` corrected to Stage 1 only (was also claiming the old "Stage 3 Hypothesis" number). Earlier 2026-11-11: Seeded for Phase 3 from Stage 18 Intent Refinement (`IRP-20261111-001`, `PCD-20261111-001` episode `fa8603c7`, `CLK-20261111-001`). Added `HYP-AL-028` and the Phase 3 carry-over disposition. Earlier 2026-11-10: section 2.1 rows #8, #9, #10, #11, #13, #17 and #22 synced from candidate to Implemented (Epics 14, 15, 16, 17, 18, 21 and 22 are built); aligned with `tests/fixtures/methodology_catalog/ideation_states.json` (LL-007). |
| Status | **v1.20 approved by the Sponsor 2026-11-12, episode `d526e945`** (the v1.16–v1.20 structural decoupling rewrite on top of the earlier v1.15 approval, episode `c60c7021`). Phase 2 Closed via `PCD-20261111-001`, episode `fa8603c7`; Phase 3 target baseline `PMP-BL-v1.2.0` set by PCD, created in Stage 18 as one of its final steps (Sponsor, 2026-11-11); anchor baseline remains `PMP-BL-v1.1.0` until then. Lineage Kernel `579b62bfe11607b2...` (`CLK-20261111-001`). |
| Source | `README.md`, `PYPI.md`, `docs/decision-making.md`, `docs/autonomy-complexity.md`, `docs/experiential-reinforcement-learning-comparison.md`, `docs/scout-agent-learn-skill.md`, `docs/scout-automation-agent-learning.md`, `docs/research/main.tex`, `examples/next_best_action.py`, `src/agent_learning/decision.py`/`cli.py`/`audit.py`, `src/agent_learning_ext/`, `git log`, and empirical Phase 1 & Phase 2 execution results across 2,723 passing tests and 102 completed stories |

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

**Decoupled to the research library, 2026-11-12 (LL-044, "The Monolithic Ideation Trap").** The full 32-methodology survey — each assessed against this project's real constraints (frozen foundation model, CPU-only, auditable, small discrete action spaces), not against whether the technique is interesting in the abstract — now lives in [`docs/research/ideation/learning-methodologies-landscape.md`](../research/ideation/learning-methodologies-landscape.md). Synthesized insight only, per LL-044's own rule:

- **9 are real or partly real:** 7 implemented (#2 REINFORCE, #3 `DecisionResolver`, #5 reward shaping, #6 human override, #19 red-team generation, #20 diff classification, #21 escalation learning) plus #4 (contextual bandit, example-only) and #12 (active evidence-seeking, partially built).
- **3 are structurally impossible** under the frozen-model premise (#1 SFT, #7 ERL in full form, #16 model-based RL); **1 is not applicable** to the single-agent shape (#18 federated learning); **1 is declined for now** (#27 prioritized replay).
- **18 are genuine, not-yet-built candidates**, several since implemented in Phase 2 (#8 critique-to-evidence/ADR-014, #9 Thompson/ADR-015, #10 UCB/ADR-016, #13 DPO/ADR-018, #15 warm-start/ADR-020, #17 ensemble routing/ADR-021, #22 scored-search/ADR-022, #23 dueling-bandit/ADR-023) — current build status is tracked by the real ADRs in `docs/adr/`, not restated here.

##### 2.1.1 External validation: what other agent SDKs actually ship

**Decoupled to the research library, 2026-11-12 (LL-044).** The full eight-framework audit (LangGraph, Semantic Kernel, OpenAI Agents SDK, Haystack, AutoGen, CrewAI, DSPy, Microsoft GitHub Copilot Auto/Azure AI Foundry Model Router) and the second-review candidate check now live in [`docs/research/ideation/agent-frameworks-comparative-study.md`](../research/ideation/agent-frameworks-comparative-study.md).

**Net finding:** of eight major agent frameworks/platforms checked, four ship no real learning mechanism at all — "agents that learn" is mostly marketing for memory-as-storage. Three of the four real exceptions (AutoGen, CrewAI, DSPy) each independently validate a methodology already in this landscape (#6, #7/#8) or close a genuine gap (DSPy → #22). Microsoft's own GitHub Copilot Auto / Azure AI Foundry Model Router is the fourth — independent confirmation, at Microsoft's own product scale, that per-instance learned model selection (#4, #9–10) is a real, shipping pattern, not a speculative one. A second external review proposed five more candidates; none survived verification against the evidence already cited (full reasoning in the research doc).

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

#### 2.2 Phase 3 Seeding & Carry-Over Disposition (`IRP-20261111-001` / `PCD-20261111-001`), 2026-11-11

**Hypotheses moved to their own document, 2026-11-12 (Sponsor decision).** Every `HYP-AL-NNN` statement, falsification criterion, and status (formerly §2.2.1–2.2.4 here, ~150 lines) now lives in [`Hypothesis-Register.md`](Hypothesis-Register.md) — Stage 2's own output, governed by `classify-hypothesis-status`, decoupled from this document so Stage 2's ongoing classification work never requires reopening this Stage 1 artifact once `approve-ideation` has closed it. Content was moved verbatim; nothing changed except location. See [Stage 1: Intent Methodology](Methodology/Stage-1-Intent-Methodology.md) and [Stage 2: Hypothesis Methodology](Methodology/Stage-2-Hypothesis-Methodology.md).

At Phase 2 close (`PCD-20261111-001`, episode `fa8603c7`, Lineage Kernel `CLK-20261111-001`), the Project Sponsor approved the following hypothesis and scope dispositions for Phase 3 (`Spark-Capture.md` v3.0, target baseline `PMP-BL-v1.2.0`):

1. **Hypotheses at Handoff (28 total, full detail in `Hypothesis-Register.md`):**
   - **8 Validated:** `HYP-AL-001`, `002`, `003`, `006`, `008`, `009`, `026`, `027`.
   - **19 Non-Terminal Carried Over Unchanged (Sponsor exception to collapse rule):** `HYP-AL-004`, `005` (`Testing`); `HYP-AL-007`, `010` to `025` (`Formulated`). No Bayes factors were fabricated where external stores or datasets (`LL-065`) were absent.
   - **1 Newly Registered:** `HYP-AL-028` (`Formulated`, DPO sample efficiency).
2. **Seeded Phase 3 Scope Inputs (`IRP-20261111-001` §5):**
   - **Deferred Adaptation Plan items (`ADP-20261110-002`, `CR-20261111-001`):** `GC-P2-04` (Tier 2 skill backfill for `LL-014`, `015`, `046`, `047`, `065`–`067`), `GC-P2-05` (repointing `HYP-AL-018` $\to$ `HYP-AL-028` and `agent-training-ext/` $\to$ `src/agent_learning_ext/` in Charter, Business Case, and Benefits Management Plan), `GC-P2-06` and `GC-P2-07` (regenerating the PMP and 9 subsidiary plans at Stage 7 with human-engineering effort units), `IMP-050` (Step 8 review checklist), and `IMP-031` (Tier 2 propagation check script).
   - **Approved PR Gate & Schedule Fixes:** `IMP-065`, `066`, `067` (PR gate resolved-finding handling, Q heading coverage, malformed bullets) and `IMP-068` (actuals against the schedule plan).
   - **Carry-Over Epics & Deferred ADR Findings:** `Epic 23`, `Epic 24`, `Epic 39`; `F3` (`ADR-022` Invariants 2 and 5 / `IMP-053`) and `F4` (`ADR-016` Invariant 4 / `IMP-054`).
   - **Rolled-In Phase Next Improvements:** `IMP-002`, `006`, `019`, `025`, `027`, `028`, `039`, plus the open decision on whether `complete_story.py done` drops `DEFAULT_IGNORES`.
   - **Multi-Agent & Register Ideation Inputs (`CR-20261111-001` §4d–4f):** Active `Story-Execution-Register.md` hook-up, `Task-Ownership-Register` (agent bidding and lease expiration), and the seven pre-WBS preparations before multiple agents pick up scheduled WBS work packages.

3. **Phase 3 idea, 2026-11-11 (Sponsor): autonomous bidding agents on tasks.** Start preparing in Phase 3 for agents that bid on tasks and are awarded ownership of them, beginning with a first supervised case: a human awards each task and bids are scored by this repository's own decision machinery. First builds: the machine-readable task list and the claim and bid register (`CR-20261111-001` §4e and §4f items 1 and 2). It stays an idea until formalized, in this order: Benefits Statement, Business Case, Project Charter, then the design decisions (ADRs, BRD, FDD) and user stories. No hypothesis id, TaskPolicy or bids are registered yet; the Stage 2 hypothesis is formulated when the first case shows the decision shape. Statutory gates stay human-approved, and a swarm never approves its own gates.

4. **Improvements still to be implemented (2026-11-11, from `Continuous-Improvement-Register.md`):** 49 of the 67 IMP entries are not fully implemented. Entries marked Implemented in the register are left out.

   | IMP | Improvement | Register state |
   |---|---|---|
   | IMP-002 | Make the Thompson sampling record self-describing | Rolled into Phase Next |
   | IMP-003 | Find the failure history that HYP-AL-002 needs | Rolled into Phase Next |
   | IMP-005 | Read a Thompson policy by the probability that each action is the best | Rolled into Phase Next |
   | IMP-006 | Commit a small recorded-store fixture so real-data checks run in CI | Rolled into Phase Next |
   | IMP-008 | Move the posterior-gate story out of Epic 19 | Rolled into Phase Next |
   | IMP-009 | Share the real-data test helpers | Rolled into Phase Next |
   | IMP-010 | Report which stored policies could donate | Rolled into Phase Next |
   | IMP-011 | Flag stories whose status disagrees with the log | Rolled into Phase Next |
   | IMP-012 | Detect an existing story branch or worktree before Step 0 | Rolled into Phase Next |
   | IMP-013 | Build the Cosmos test fakes' exceptions in one place | Rolled into Phase Next |
   | IMP-014 | Move the Stage 18 tooling onto the path ADR-034 keeps | Rolled into Phase Next |
   | IMP-016 | Multi-Reviewer and Bugbot Ingestion in PR Gatekeeper | Partly implemented |
   | IMP-018 | Empirical Reviewer Reliability Weighting | Rolled into Phase Next |
   | IMP-019 | Passive Governance Learning Harvester | Rolled into Phase Next |
   | IMP-022 | Public Ingestion Guard Ordering Pattern (Deduplication First) | Partly implemented |
   | IMP-023 | Low-Authority Exploration Dataset Generation for HYP-AL-009 | Rolled into Phase Next |
   | IMP-025 | Automated Preference Pair Adapter from Curated Triage Dataset | Rolled into Phase Next |
   | IMP-026 | Synthetic Red Team Pair Set for Discrete Policy Robustness | Rolled into Phase Next |
   | IMP-027 | Dual-Access Invocation Pattern (Callable Property Wrapper) for Extension Policies | Rolled into Phase Next |
   | IMP-028 | Automated Action Space Reversibility Linter and Declarative Registry | Rolled into Phase Next |
   | IMP-029 | Multi-Policy Offline Benchmarking Harness with Synthetic Failure Injection | Rolled into Phase Next |
   | IMP-031 | Backfill Tier 2 targets for LL-045 to LL-048 and script the LL-041 check | Rolled into Phase Next |
   | IMP-032 | Generate the Project Status Register's repository facts from git | Rolled into Phase Next |
   | IMP-035 | Decouple Pareto Pruning from Feasible Margin Calculation in Scored Search | Rolled into Phase Next |
   | IMP-036 | Red Team Benchmark Dataset for Scored-Search Weight Compilation | Rolled into Phase Next |
   | IMP-037 | Let `train` call `ContextualReinforceLearner` | Rolled into Phase Next |
   | IMP-038 | Helper that copies the decide payload's `feature_vector` onto the episode | Rolled into Phase Next |
   | IMP-039 | Close the two Epic 38 known gaps (Q-159-1 and the `autonomy` block) | Rolled into Phase Next |
   | IMP-040 | Update demo 04 to use the packaged learner and move catalog row #4 | Rolled into Phase Next |
   | IMP-041 | Trial a contextual policy on `escalate-diff-response` with the Stage 16 measurements as features | Rolled into Phase Next |
   | IMP-042 | Compare a contextual learner with the claim-type baseline on `route-review-finding` | Rolled into Phase Next |
   | IMP-044 | Align `implement-story` Step 0 and Step 6 with the whole-suite rule | In-flight candidate |
   | IMP-047 | Build a synthetic mixed-difficulty benchmark for the router | Rolled into Phase Next |
   | IMP-048 | Wire `route` into `task-policy-decide` behind an explicit flag | Rolled into Phase Next |
   | IMP-049 | Record the module in the review-triage line | Rolled into Phase Next |
   | IMP-050 | Put the exact Step 8 commands in a checklist in `implement-story` | Rolled into Phase Next |
   | IMP-053 | Correct ADR-022 Invariants 2 and 5 to match FDD-022 and the code, or decide the code is wrong | Rolled into Phase Next |
   | IMP-054 | Decide whether ADR-016 Invariant 4 (UCB runs under LOW authority) is enforced | Rolled into Phase Next |
   | IMP-055 | Trace each use of the pairwise regularization floor and logit clamp | Rolled into Phase Next |
   | IMP-056 | Close the ADR-034 gap: decommission top-level `pmbok/` and drop the CI `--ignore=tests/pmbok` | Rolled into Phase Next |
   | IMP-057 | Make the failing-first (RED) run a required line in each story log entry | Rolled into Phase Next |
   | IMP-058 | Capture real telemetry in governance episodes and learner runs | Rolled into Phase Next |
   | IMP-059 | Treat pending or empty required checks as not ready in `pr_gate.py` | Rolled into Phase Next |
   | IMP-060 | Bind lists and thresholds stated in approved documents to the code that holds them | Rolled into Phase Next |
   | IMP-061 | Name an input source and output path for every stage, and update the chain coverage document | Rolled into Phase Next |
   | IMP-065 | Count a finding accepted with a recorded fix commit as resolved in the PR gate | Rolled into Phase Next |
   | IMP-066 | Make the gate read Amazon Q's findings whatever the heading | Rolled into Phase Next |
   | IMP-067 | Stop a malformed tagged bullet from dropping every review delta in the PR gate | Rolled into Phase Next |
   | IMP-068 | Compare measured actuals with the schedule management plan and warn on variance | Rolled into Phase Next |

> **Research Library Reference (LL-044):** Full empirical validation criteria, mathematical formulations (Wilson lower bounds, low-pass filter equations, adaptive capacity bounding), and the native integration blueprint with `sidpa-template` governance workflows are decoupled and documented in [`docs/research/ideation/hypothesis-validation-and-governance-integration.md`](../../research/ideation/hypothesis-validation-and-governance-integration.md).


---

### SECTION 3: STAKEHOLDER MANAGEMENT & RACI REPRESENTATION

**Superseded by `Stakeholder-Register.md`, 2026-11-12.** This section's earlier content — a 4-row generic stakeholder table, an honest "RACI not yet formalized" gap note — predates the real Master Stakeholder Register and is now stale. `Stakeholder-Register.md` v2.0 (approved, Stage 4's own Charter input) already has what this section once lacked: 7 named stakeholders (`SH-01`–`SH-07`) with power/interest ratings, a full influence/interest grid, a Stakeholder Engagement Assessment Matrix, and a RACI matrix spanning all 18 lifecycle stages (§6 there). Nothing here is re-stated; see that document directly. This is the same decoupling this document's own §2.2 already applied to hypotheses: content that belongs to a later stage's real artifact should not also live, duplicated or stale, inside Stage 1's Ideation Document.

---

### SECTION 4: SCOPE, WBS, AND LIFECYCLE TAILORING ARCHITECTURE

**Superseded by Stage 7's real subsidiary plans, 2026-11-12.** This section's earlier content — a hand-written in/out-of-scope list, and a note that "WBS, schedule, cost, HR, procurement... are not filled in... this is not a staffed project" — predates Stage 7's actual output and is now stale: all nine subsidiary management plans exist, are filled in, and are each Sponsor-approved (`docs/project-docs/management-plans/`): Scope, Schedule (plus `Schedule-Baseline-WBS-Forecast.md`), Cost, Quality, Resource, Communications, Risk, Procurement, and Stakeholder Engagement. The real Scope Statement and WBS live in `Scope-Management-Plan.md` (§1.2–1.3, §2.1), not here. Nothing is re-stated; see those documents directly — the same decoupling already applied to hypotheses (§2.2) and stakeholder management (§3).

---

### SECTION 5–9

**Partly superseded by Stage 7's real subsidiary plans, 2026-11-12.** The risk register and lifecycle roadmap this section once deferred are no longer gaps: `Risk-Management-Plan.md` and the integrated `Project-Management-Plan.md` (both Stage 7, `docs/project-docs/management-plans/`) already cover them, filled in and Sponsor-approved. TOGAF architecture viewpoints, the SABSA trust model, and DMBOK data governance are a separate, honest exclusion, not a Stage 7 gap: no PMBOK subsidiary plan is a TOGAF viewpoint or a SABSA model, and they still apply more naturally to a multi-tenant SaaS product than to a Python SDK distributed via PyPI. A future pass should still decide, deliberately, whether any of those three add real value here, rather than skipping them by default.

---

### SECTION 10: ARCHITECTURAL DECISION LOGS

**Superseded by Stage 5's real ADR process, 2026-11-12.** This section's one entry was a meta-decision about documentation discipline, not a technical architecture decision — and the role it was standing in for (a decision log with alternatives analysis and rationale) is now done far more rigorously by the real thing: `Project-Pillars.md` (Stage 5's own artifact, decomposing the Charter into pillars) and the 38 approved ADRs under `docs/adr/`, each with its own Alternatives Considered section, Sponsor decision, and episode. Nothing is re-stated; see those directly — the same decoupling already applied to §2.2 (hypotheses → Stage 2), §3 (stakeholders → Stage 4), and §4 (scope/WBS → Stage 7).

---

## Provenance & Completeness Self-Assessment

**Rewritten 2026-11-12.** This table previously asserted completeness for content Ideation no longer owns (hypotheses, stakeholders, scope, ADR coverage) — hand-written claims that went stale the moment that content moved to its real owning stage. The fix is not to re-assert them here: each owning stage's own Methodology guide carries a live `## Validation` check (a real `grep`/command against the actual artifact) that can be re-run to confirm the claim still holds, rather than a prose assertion that can drift unnoticed. This table now covers only what Ideation itself still owns.

| Field | Status |
|---|---|
| Executive Summary & learning-variant landscape (§1.1) | Sourced directly from code (`reinforce.py`, `softmax_bandit.py`, `contextual_softmax.py`, `decision.py`) and real usage |
| Objectives (§1.2) | Cross-checked against `README.md`'s stated goals |
| Learning Methodologies Landscape (§2.1) | Synthesized summary only; the full 32-methodology survey and the 8-framework external validation are decoupled to the research library (LL-044) — check them there, not here |
| Hypotheses | Owned by Stage 2 — check `Hypothesis-Register.md` directly, or run [Stage 2: Hypothesis Methodology](Methodology/Stage-2-Hypothesis-Methodology.md) §4's validation command |
| Stakeholders & RACI | Owned by Stage 4 — `Stakeholder-Register.md` carries its own "Provenance & Completeness Assessment" (§ at its end) |
| Scope, WBS & subsidiary plans | Owned by Stage 7 — check `Scope-Management-Plan.md` and the other eight subsidiary plans directly, or run [Stage 7: Project (PMP & Baselines) Methodology](Methodology/Stage-7-Project-PMP-and-Baselines-Methodology.md) §4 |
| Architectural decisions | Owned by Stage 5 — each of the 38 ADRs under `docs/adr/` carries its own Alternatives Considered, Consequences, and Amendment Log |
| Downstream documents | `Business-Case.md`, `Benefits-Management-Plan.md`, and `Project-Charter.md` build on this document and on `Hypothesis-Register.md` — this Ideation document is one link in a real chain, not a standalone artifact |
