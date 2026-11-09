---
artifact_id: scope-foundation-wbs-dictionary
parent_plan_id: scope-management
baseline_id: PMP-BL-v1.0.0
route: foundation_artifact
governance_policy: approve-subsidiary-plan
substage: "6.A-2"
version: "1.0.0"
owner_role: "Project Manager"
depends_on: []
approval_status: approved
pmbok_process: "Develop Scope Structure"
---

# Scope Foundation — WBS Dictionary (`PMP-BL-v1.0.0`)

PMBOK 8 **Scope Performance Domain** §2.2 — **Develop Scope Structure (WBS)**. Canonical **143** story rows for baseline `PMP-BL-v1.0.0`. Boundaries and execution bands: [Scope-Project-Scope-Statement.md](Scope-Project-Scope-Statement.md). **Topic pillar trace** (epic → ADR → pillar): [Scope-Pillar-Overview-and-Trace.md](Scope-Pillar-Overview-and-Trace.md).

## WBS Dictionary & 100% Rule
Every deliverable maps to one parent epic and one user story. Unassigned work packages are prohibited. The 100% rule requires development work, documentation updates, and test suites to trace to an approved story acceptance criterion ($AC_n$).

Each row below uses these dictionary fields:

* **Parent epic:** the epic named in the row. The story file is the child of that epic.
* **Owner role:** Project Manager.
* **Acceptance criteria:** the $AC_n$ items in that story file. This dictionary records the story id and title. It does not copy the criteria.

Epic 14 and Epic 18 are Band **C** (§1.5): written and approved, **not authorized for Phase 1 implementation**. Epic 22 rows are Band **D** placeholders for ADR-022.

| Story | Title | Parent epic |
| --- | --- | --- |
| 1.1 | Exclude full-authority episodes from ReinforceLearner's training batch | Epic 1: Decision Authority Enforcement |
| 2.1 | Implement Optimistic Concurrency and Monotonicity Guard for Cosmos Active Pointer | Epic 2: Cosmos Active-Policy Pointer Concurrency Protection |
| 3.1 | Build Tier-Specific Environment Overrides and Authority-Aware Autonomy Reporting | Epic 3: Tier-Specific Autonomy Overrides and Authority-Aware Reporting |
| 4.1 | Capture Diagnostic Migration Snapshot and Correct Replay Docstring | Epic 4: Authority-Migration Diagnostic Snapshot and Docstring Alignment |
| 5.1 | Build compare_decision_results() and the task-policy-compare CLI | Epic 5: Decision-Progress Comparison and Regression Healing |
| 6.1 | Implement Opt-In Policy Configuration and Lightweight Evidence Capture | Epic 6: Opt-In Lightweight Evidence Capture for Low-Authority Decisions |
| 7.1 | Implement Paired Diff Classification & Escalation Pipeline | Epic 7: Automated Governance Change — Paired Diff Classification and Escalation Pipeline |
| 8.1 | Native PMBOK 8 Orchestration Engine and PMP Decision Gate | Epic 8: PMBOK 8 Lifecycle Orchestration and Closed-Loop Adaptation Feedback |
| 9.1 | Phase Close Readiness Gate and Intent Refinement Decision Policy | Epic 9: Intent Refinement and Cognitive Feedback Loop |
| 9.2 | Bayesian Hypothesis Terminality and Recurrence Exhaustion ($d_{\max}=2$) | Epic 9: Intent Refinement and Cognitive Feedback Loop |
| 9.3 | Low-Pass Outcome Damping and Cumulative Lineage Kernel | Epic 9: Intent Refinement and Cognitive Feedback Loop |
| 10.1 | Implement Lessons Learned Register Parser, Validation Contract, and Phase Close Readiness Bridge | Epic 10: Stage 15 Lessons Learned Crystallization and OPA Register |
| 11.1 | Route Records and the Human-Decision Invariants | Epic 11: Project Tailoring and Route Decision |
| 11.2 | Flags That Never Block, and Integration-Section Home | Epic 11: Project Tailoring and Route Decision |
| 12.1 | The Frontmatter Grammar Parser | Epic 12: Subsidiary Management Plan Standards and Content Contracts |
| 12.2 | Metadata Validation and the Nine-Plan Standards | Epic 12: Subsidiary Management Plan Standards and Content Contracts |
| 12.3 | The Content Contract: Headings, Length and Boundaries | Epic 12: Subsidiary Management Plan Standards and Content Contracts |
| 12.4 | Precedence and the Next Step | Epic 12: Subsidiary Management Plan Standards and Content Contracts |
| 13.1 | The Canonical Content Hash | Epic 13: Subsidiary Plan Approval Gates Before PMP Formalization |
| 13.2 | Technical Integrity and the Gate Constraint | Epic 13: Subsidiary Plan Approval Gates Before PMP Formalization |
| 13.3 | The Approval Record and the Policy Shape | Epic 13: Subsidiary Plan Approval Gates Before PMP Formalization |
| 13.4 | The Dependency Graph | Epic 13: Subsidiary Plan Approval Gates Before PMP Formalization |
| 13.5 | Freshness and Transitive Staleness | Epic 13: Subsidiary Plan Approval Gates Before PMP Formalization |
| 13.6 | The Lifecycle State | Epic 13: Subsidiary Plan Approval Gates Before PMP Formalization |
| 13.7 | Formalization and the Package Contract | Epic 13: Subsidiary Plan Approval Gates Before PMP Formalization |
| 14.1 | The Tag Grammar and Parser | Epic 14: Lightweight Critique-to-Evidence Ingestion |
| 14.2 | Moving the Pooled Support by the Delta | Epic 14: Lightweight Critique-to-Evidence Ingestion |
| 14.3 | Doubt, Traceability and Validation | Epic 14: Lightweight Critique-to-Evidence Ingestion |
| 14.4 | Episode Metadata | Epic 14: Lightweight Critique-to-Evidence Ingestion |
| 14.5 | Replay on the Real Triage Records | Epic 14: Lightweight Critique-to-Evidence Ingestion |
| 14.6 | The Delta Rubric | Epic 14: Lightweight Critique-to-Evidence Ingestion |
| 15.1 | The Seed and the Replay | Epic 15: Bayesian Bandit Posterior Sampling (Thompson Sampling) |
| 15.2 | Posterior State in the Snapshot | Epic 15: Bayesian Bandit Posterior Sampling (Thompson Sampling) |
| 15.3 | Choosing by Probability Matching | Epic 15: Bayesian Bandit Posterior Sampling (Thompson Sampling) |
| 15.4 | The Conjugate Update and the Ceiling | Epic 15: Bayesian Bandit Posterior Sampling (Thompson Sampling) |
| 15.5 | Staying Out of REINFORCE | Epic 15: Bayesian Bandit Posterior Sampling (Thompson Sampling) |
| 15.6 | The Positive-Only Check (HYP-AL-002) | Epic 15: Bayesian Bandit Posterior Sampling (Thompson Sampling) |
| 16.1 | The Scores | Epic 16: Deterministic Upper Confidence Bound (UCB) Decision Policy |
| 16.2 | Choosing Deterministically | Epic 16: Deterministic Upper Confidence Bound (UCB) Decision Policy |
| 16.3 | Statistics in the Snapshot | Epic 16: Deterministic Upper Confidence Bound (UCB) Decision Policy |
| 16.4 | Counting Each Episode Once | Epic 16: Deterministic Upper Confidence Bound (UCB) Decision Policy |
| 16.5 | Staying Out of REINFORCE | Epic 16: Deterministic Upper Confidence Bound (UCB) Decision Policy |
| 16.6 | The Positive-Only Check (HYP-AL-009) | Epic 16: Deterministic Upper Confidence Bound (UCB) Decision Policy |
| 17.1 | The Schedule | Epic 17: Scheduled Epsilon-Greedy Policy Baseline |
| 17.2 | The Safety Mask | Epic 17: Scheduled Epsilon-Greedy Policy Baseline |
| 17.3 | Choosing and Replaying | Epic 17: Scheduled Epsilon-Greedy Policy Baseline |
| 17.4 | Statistics and the Learner | Epic 17: Scheduled Epsilon-Greedy Policy Baseline |
| 17.5 | Staying Out of REINFORCE | Epic 17: Scheduled Epsilon-Greedy Policy Baseline |
| 17.6 | The Positive-Only Baseline Run | Epic 17: Scheduled Epsilon-Greedy Policy Baseline |
| 18.1 | Pairs From Episodes | Epic 18: Pairwise Preference Optimization for Discrete Action Logits |
| 18.2 | The Loss and Its Gradient | Epic 18: Pairwise Preference Optimization for Discrete Action Logits |
| 18.3 | The Fit | Epic 18: Pairwise Preference Optimization for Discrete Action Logits |
| 18.4 | The Learner | Epic 18: Pairwise Preference Optimization for Discrete Action Logits |
| 18.5 | Through the Runner | Epic 18: Pairwise Preference Optimization for Discrete Action Logits |
| 18.6 | The Real-Data Check (Zero Pairs) | Epic 18: Pairwise Preference Optimization for Discrete Action Logits |
| 19.1 | Pooling Logits | Epic 19: Hierarchical Meta-Prior Compilation Across Task Families |
| 19.2 | Pooling Beta Counts | Epic 19: Hierarchical Meta-Prior Compilation Across Task Families |
| 19.3 | Refusing a Bad Family | Epic 19: Hierarchical Meta-Prior Compilation Across Task Families |
| 19.4 | Declaring and Finding Members | Epic 19: Hierarchical Meta-Prior Compilation Across Task Families |
| 19.5 | Storing the Prior | Epic 19: Hierarchical Meta-Prior Compilation Across Task Families |
| 19.6 | Seeding a New Policy | Epic 19: Hierarchical Meta-Prior Compilation Across Task Families |
| 19.7 | The Real-Data Check (No Family) | Epic 19: Hierarchical Meta-Prior Compilation Across Task Families |
| 20.1 | The Damped Copy | Epic 20: Explicit Policy Prior Warm-Starting |
| 20.2 | The Provenance Record | Epic 20: Explicit Policy Prior Warm-Starting |
| 20.3 | The Command for a Policy Donor | Epic 20: Explicit Policy Prior Warm-Starting |
| 20.4 | No Borrowed Evidence | Epic 20: Explicit Policy Prior Warm-Starting |
| 20.5 | Seeding From a Family Meta-Prior | Epic 20: Explicit Policy Prior Warm-Starting |
| 20.6 | The Real-Data Check (No Donor) | Epic 20: Explicit Policy Prior Warm-Starting |
| 21.1 | Entropy and Margin | Epic 21: Contextual Authority Ensemble Routing |
| 21.2 | The Route | Epic 21: Contextual Authority Ensemble Routing |
| 21.3 | Pinned Gates | Epic 21: Contextual Authority Ensemble Routing |
| 21.4 | The Shadow Record and the Agreement Gate | Epic 21: Contextual Authority Ensemble Routing |
| 21.5 | Human Decisions and the Promotion Seed | Epic 21: Contextual Authority Ensemble Routing |
| 21.6 | Dispatch and Gradient Exclusion | Epic 21: Contextual Authority Ensemble Routing |
| 21.7 | The Real-Data Check (No Routed Traffic) | Epic 21: Contextual Authority Ensemble Routing |
| 22.1 | Scoring a Weight Vector With the Real Resolver | Epic 22: Scored-Search Decision Configuration Compilation |
| 22.2 | The Split and the Label Rule | Epic 22: Scored-Search Decision Configuration Compilation |
| 22.3 | The Coordinate Ascent | Epic 22: Scored-Search Decision Configuration Compilation |
| 22.4 | Proposing Only a Real Improvement | Epic 22: Scored-Search Decision Configuration Compilation |
| 22.5 | Applying Frozen Weights | Epic 22: Scored-Search Decision Configuration Compilation |
| 22.6 | Adopting a Proposal by a Human Decision | Epic 22: Scored-Search Decision Configuration Compilation |
| 22.7 | The Real-Data Regression Check | Epic 22: Scored-Search Decision Configuration Compilation |
| 25.1 | Scope floors, caps, and exclusions | Epic 25: Scope Management Plan Standard and Baseline Contract |
| 25.2 | WBS and Definition of Done | Epic 25: Scope Management Plan Standard and Baseline Contract |
| 25.3 | The idle Scope advisory policy | Epic 25: Scope Management Plan Standard and Baseline Contract |
| 25.4 | Record the recommendation, then show it | Epic 25: Scope Management Plan Standard and Baseline Contract |
| 26.1 | Schedule floors, caps, and exclusions | Epic 26: Schedule Management Plan Standard and Baseline Contract |
| 26.2 | Milestone register, timebox, and estimation basis | Epic 26: Schedule Management Plan Standard and Baseline Contract |
| 26.3 | The idle Schedule advisory policy | Epic 26: Schedule Management Plan Standard and Baseline Contract |
| 26.4 | Record the recommendation, then show it | Epic 26: Schedule Management Plan Standard and Baseline Contract |
| 27.1 | Cost floors, caps, and exclusions | Epic 27: Cost Management Plan Standard and Baseline Contract |
| 27.2 | Envelope, categories, and contingency | Epic 27: Cost Management Plan Standard and Baseline Contract |
| 27.3 | The idle Cost advisory policy | Epic 27: Cost Management Plan Standard and Baseline Contract |
| 27.4 | Record the recommendation, then show it | Epic 27: Cost Management Plan Standard and Baseline Contract |
| 28.1 | Risk floors, caps, and exclusions | Epic 28: Risk Management Plan Standard |
| 28.2 | Scale, register contract, and escalation | Epic 28: Risk Management Plan Standard |
| 28.3 | The idle Risk advisory policy | Epic 28: Risk Management Plan Standard |
| 28.4 | Record the recommendation, then show it | Epic 28: Risk Management Plan Standard |
| 29.1 | Quality floors, caps, and exclusions | Epic 29: Quality Management Plan Standard |
| 29.2 | Gates, verification, and nonconformance | Epic 29: Quality Management Plan Standard |
| 29.3 | The idle Quality advisory policy | Epic 29: Quality Management Plan Standard |
| 29.4 | Record the recommendation, then show it | Epic 29: Quality Management Plan Standard |
| 30.1 | Resource lengths and the full-plan exclusion minimum | Epic 30: Resource Management Plan Standard |
| 30.2 | Catalogue, allocation, and tooling | Epic 30: Resource Management Plan Standard |
| 30.3 | The idle Resource advisory policy | Epic 30: Resource Management Plan Standard |
| 30.4 | Record the recommendation, then show it | Epic 30: Resource Management Plan Standard |
| 31.1 | Stakeholder lengths and the full-plan exclusion minimum | Epic 31: Stakeholder Engagement Plan Standard |
| 31.2 | Register, engagement levels, and actions | Epic 31: Stakeholder Engagement Plan Standard |
| 31.3 | The idle Stakeholder advisory policy | Epic 31: Stakeholder Engagement Plan Standard |
| 31.4 | Record the recommendation, then show it | Epic 31: Stakeholder Engagement Plan Standard |
| 32.1 | Communications lengths and the full-plan exclusion minimum | Epic 32: Communications Management Plan Standard |
| 32.2 | Matrix, decision-recording rule, and escalation path | Epic 32: Communications Management Plan Standard |
| 32.3 | The idle Communications advisory policy | Epic 32: Communications Management Plan Standard |
| 32.4 | Record the recommendation, then show it | Epic 32: Communications Management Plan Standard |
| 33.1 | Procurement lengths and the full-plan exclusion minimum | Epic 33: Procurement Management Plan Standard |
| 33.2 | Make-or-buy criteria, intake rule, and licence checks | Epic 33: Procurement Management Plan Standard |
| 33.3 | The idle Procurement advisory policy | Epic 33: Procurement Management Plan Standard |
| 33.4 | Record the recommendation, then show it | Epic 33: Procurement Management Plan Standard |
| 34.1 | The 49-process registry is pure data | Epic 34: PMBOK Tooling Decommissioning and Lightweight LearningStore Convergence |
| 34.2 | A project run is an Episode, and the latest one wins | Epic 34: PMBOK Tooling Decommissioning and Lightweight LearningStore Convergence |
| 34.3 | The client is the standard library, and secrets stay out of the record | Epic 34: PMBOK Tooling Decommissioning and Lightweight LearningStore Convergence |
| 34.4 | One CLI dispatches draft, approve, formalize, and adapt | Epic 34: PMBOK Tooling Decommissioning and Lightweight LearningStore Convergence |
| 34.5 | The legacy tree is gone and the suite collects | Epic 34: PMBOK Tooling Decommissioning and Lightweight LearningStore Convergence |
| 35.1 | Cycle and baseline ids, and a hash that ignores them | Epic 35: Cycle Identification and Cross-Cycle Artifact Traceability |
| 35.2 | The register is an event log with one open cycle | Epic 35: Cycle Identification and Cross-Cycle Artifact Traceability |
| 35.3 | Lookup stops at the first source that hits | Epic 35: Cycle Identification and Cross-Cycle Artifact Traceability |
| 35.4 | Frontmatter is checked, and a clash refuses closure | Epic 35: Cycle Identification and Cross-Cycle Artifact Traceability |
| 36.1 | The Catalog and Its Integrity Check | Epic 36: Learning Methodology Examples, Best-Practice Ledger and the Review-Triage Learning Loop |
| 36.2 | Runnable Examples for What Exists | Epic 36: Learning Methodology Examples, Best-Practice Ledger and the Review-Triage Learning Loop |
| 36.3 | Proof-of-Concept Sketches for the ADR-Backed Candidates | Epic 36: Learning Methodology Examples, Best-Practice Ledger and the Review-Triage Learning Loop |
| 36.4 | The Best-Practice Ledger | Epic 36: Learning Methodology Examples, Best-Practice Ledger and the Review-Triage Learning Loop |
| 36.5 | The Review-Triage Learning Loop | Epic 36: Learning Methodology Examples, Best-Practice Ledger and the Review-Triage Learning Loop |
| 36.6 | Tailoring for the Store and Lessons Learned, and Template Propagation | Epic 36: Learning Methodology Examples, Best-Practice Ledger and the Review-Triage Learning Loop |
| 37.1 | Record design-time evidence on the existing governance call | Epic 37: Design-Time Baseline Feedback Loop |
| 37.2 | A baseline feedback item cites documents and carries no numbers | Epic 37: Design-Time Baseline Feedback Loop |
| 37.3 | Design-time bumps the patch, execution bumps the minor | Epic 37: Design-Time Baseline Feedback Loop |
| 37.4 | The pending-feedback section names both loops | Epic 37: Design-Time Baseline Feedback Loop |
| 38.1 | The Weight-Row Update | Epic 38: Packaged Contextual Learning |
| 38.2 | Skipped Episodes Are Counted | Epic 38: Packaged Contextual Learning |
| 38.3 | One Learner, One Policy Class | Epic 38: Packaged Contextual Learning |
| 38.4 | Init Can Create The Contextual Policy | Epic 38: Packaged Contextual Learning |
| 38.5 | Decide Requires The Feature List | Epic 38: Packaged Contextual Learning |
| 38.6 | Scalar Commands Leave The Weight Rows Alone | Epic 38: Packaged Contextual Learning |