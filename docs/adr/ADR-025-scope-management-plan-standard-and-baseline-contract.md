# ADR 025: Scope Management Plan Standard and Baseline Contract

## 1. Executive Brief
Under **ADR-011** (Project Tailoring and Route Decision) and **ADR-012** (Plan Standards and Content Contracts), the **Scope Management Plan** is designated as the primary **Baseline-Substantiating Plan**. It forms the foundational root node of the planning causal DAG ($5.1 \text{ Scope} \to 6.1 \text{ Schedule} \to 7.1 \text{ Cost}$). In PMBOK 8, Scope is developed within the **Scope Performance Domain** under the *Planning* Focus Area, defining the boundaries, decomposition, and verification mechanisms for all project deliverables.

Prior to this ADR, the repository lacked a concrete normative standard for Scope. As observed in baseline `PMP-BL-v1.0.0`, `docs/project-docs/management-plans/Scope-Management-Plan.md` consisted of generic stub sentences that omitted work breakdown structures, out-of-scope boundaries, and deliverable acceptance criteria.

This ADR formalizes the **Scope Management Plan Standard and Baseline Contract**. It specifies:
1. The required domain mechanics (In-Scope, Out-of-Scope boundaries, WBS decomposition, Deliverable Acceptance).
2. The specific quantitative floors and caps for `pmp_section` and `full_plan` routes.
3. The governance and change control triggers that govern scope variance and downstream dependency invalidation under ADR-013.

---

## 2. Status
**Accepted (2026-10-26, Menno)** — First dedicated Baseline-Substantiating Plan standard, inheriting ADR-012. Episode: `432bae92-29a2-4598-8bb0-ec5d38bafbf2`.

---

## 3. Context & Problem Statement
* **Root Node of the Planning DAG:** Per ADR-013 §4.1 and §4.5, planning dependencies form a directed acyclic graph where Schedule and Cost are causally downstream from Scope. If the Scope baseline is vague or unanchored, all downstream baselines (durations, milestones, budgets) become invalid.
* **The Silent Creep Failure Mode:** Without explicit **Out-of-Scope** declarations, generative agents and development teams progressively expand feature sets without formal governance or resource allocation.
* **ADR-011 Mandate for Baseline Plans:** ADR-011 §3.2 and Invariant #2 mandate that cost, scope, and schedule plans cannot be casually omitted; setting `not_applicable` on Scope is a strongly flagged deviation (`FLAG: OMISSION_OF_BASE_PLAN`) requiring an explicit recorded justification and sponsor confirmation.
* **Zero Upfront Deliverable or Breakout Prerequisite:** Designing and baselining the Scope Management Plan requires only high-level Initiating governance inputs ([Project-Charter.md](../project-docs/Project-Charter.md), [Ideation-Document.md](../project-docs/Ideation-Document.md), [Business-Case.md](../project-docs/Business-Case.md)). It does **not** require subsidiary deliverables (such as User Stories, functional specifications, or code work packages) or human breakout sessions to exist prior to designing the plan. The plan establishes the decomposition rules and Definition of Done under which detailed deliverables are elaborated progressively downstream in Stages 7–9.

---

## 4. Technical Decision

### 4.1 Inherited ADR-012 Frontmatter Specification
Every Scope Management Plan artifact (`docs/project-docs/management-plans/Scope-Management-Plan.md` or `.staging/pmp-sections/Scope-Management-Plan.md`) must carry the following frontmatter metadata:

```yaml
---
plan_id: "scope-management"
plan_name: "Scope Management Plan"
pmbok_edition: "PMBOK 8"
pmbok_focus_area: "Planning"
primary_pmbok_domain: "Scope"
secondary_pmbok_domains:
  - "Governance"
legacy_process: "5.1 Plan Scope Management"
route: "full_plan" # full_plan | pmp_section | not_applicable (validated against tailoring matrix)
generator: "llm"   # llm | human | stub | mock (ADR-013 §4.2 audit field)
version: "1.0.0"
baseline_id: "<target-baseline-id>"
owner_role: "Project Manager"
depends_on: []     # Root of the subsidiary-plan DAG (ADR-013 §4.1); Charter/Business Case/Ideation are governance inputs, not plan nodes
inputs:
  - "Project-Charter.md"
  - "docs/project-docs/Ideation-Document.md"
  - "docs/project-docs/Business-Case.md"
outputs:
  - "docs/project-docs/management-plans/Scope-Management-Plan.md" # if full_plan; .staging/pmp-sections/ if pmp_section
governance_policy: "approve-subsidiary-plan" # "approve-subsidiary-plan" (if full_plan) | "approve-pmp" (if pmp_section)
---
```

> [!NOTE]
> Canonical content hashing follows ADR-012 §4.2 and ADR-013 §4.3: the hash is computed dynamically over disk content and stored in `Episode.metadata`, avoiding self-referential in-file hash corruption.

### 4.2 Required Structural Sections & Domain Mechanics

The plan body must use the three literal ADR-012 §4.3.1 headings (`## 1. Intent, Alignment & Boundaries`, `## 2. Domain Mechanics & Standards`, `## 3. Governance, Control & Decision Rights`). The Scope-specific content below is carried as subsections under those headings; renaming the top-level headings raises `FLAG: MISSING_REQUIRED_SECTION`.

#### Under `## 1. Intent, Alignment & Boundaries`
* **PMBOK Input, Process & Output (IPO) Specification:**
  * **Inputs:** `Project-Charter.md` (high-level objectives and constraints), `Ideation-Document.md` (intent spark), `Business-Case.md` (benefits). Zero lower-level deliverables or breakout sessions required prior to planning.
  * **Processes:** Scope boundary itemization, 4-tier WBS decomposition hierarchy (`Phase` $\to$ `Epic` $\to$ `Story` $\to$ `Commit`), WBS dictionary definition, Definition of Done protocol, scope variance categorization.
  * **Outputs:** `Scope-Management-Plan.md` (or `.staging/pmp-sections/Scope-Management-Plan.md`), Approved Project Scope Statement, WBS architecture, and DoD criteria authorizing Stage 7 User Stories.
* **Charter Traceability:** Explicit mapping of project scope to the strategic objectives, high-level requirements, and success metrics declared in [Project-Charter.md](../project-docs/Project-Charter.md).
* **In-Scope Boundary Definition:** Exhaustive itemization of major features, architectural deliverables, code modules, and test suites authorized for development.
* **Mandatory Out-of-Scope Boundary List:** Explicit list of features, platforms, integrations, or capabilities that are **strictly excluded** from the current lifecycle stage or project phase. If no exclusions exist, the plan must state *"None: [rationale]"* in the ADR-012 §4.1 form (rationale $\ge 10$ words, lint-checked) justifying why project exclusions do not apply.

#### Under `## 2. Domain Mechanics & Standards` (Scope decomposition)
* **Work Breakdown Structure (WBS) Architecture:**
  * Decomposition hierarchy: `Project Phase` $\to$ `Epic` $\to$ `User Story` $\to$ `Work Package / Commit`.
  * WBS Dictionary rules: Each deliverable must define acceptance criteria, owner role, and parent epic traceability (mandatory for `full_plan`; optional for `pmp_section` where a concise hierarchy list and DoD summary suffice).
* **Scope Baseline Definition:** The scope baseline comprises:
  1. The Approved Project Scope Statement.
  2. The WBS and Story Mapping in `docs/project-docs/`.
  3. Acceptance Criteria defined in individual User Story artifacts (`docs/project-docs/User-Stories/`). *(Note: Detailed User Story artifacts are progressively elaborated downstream in Stage 7 and verified before work package execution; they are not required prior to designing the plan.)*
* **Requirements Traceability Matrix (RTM) Integration:** Traces high-level business goals (BRD) to functional specifications (FDD) and code verification units (Pytest suites) (required for `full_plan`; optional for `pmp_section`).
* **Deliverable Acceptance & Verification Protocol:** Formal Definition of Done (DoD) required before a deliverable moves to Stage 10 (Verification Evidence). Acceptance criteria must be testable or objectively verifiable; a qualitative criterion (e.g. "user friendly") needs a named validation method. This is assessed in peer review and semantic linting, not by a structural flag.

#### Under `## 3. Governance, Control & Decision Rights`
* **Accountability & Decision Rights:**
  * Project Manager is accountable for scope baseline compliance.
  * Baseline revisions and expansions require Sponsor / Charter Approver authorization via Stage 17 Integrated Change Control (`approve-adaptation-plan`) or design-time baseline feedback via ADR-037 (`BFI-NNN`).
  * Deliverable acceptance authority resides with the Product Owner / PM named in the Stakeholder Register.
* **Variance Tolerances & Escalation:**
  * Unplanned additions $\le 1$ story point or localized refactoring that affects no public interface, approved deliverable, architectural decision, or acceptance criterion (either condition alone qualifies): PM discretion.
  * Structural boundary changes or new feature epics: Triggers Stage 17 Integrated Change Control (`approve-adaptation-plan`) and updates the Project Charter.
* **Transitive Downstream Invalidation:** Per ADR-013 §4.5, any approved Scope baseline modification automatically marks all downstream subsidiary plans in the DAG (Schedule 6.1, Cost 7.1, Quality 8.1, Resource 9.1, Communications 10.1, Risk 11.1, Procurement 12.1, and Stakeholder Engagement 13.2) as `STALE_DEPENDENCY`, requiring re-evaluation.

---

### 4.3 Floor and Cap Thresholds for Scope

Word count is measured on the Markdown body below `---`, using the ADR-012 §4.3.1 stdlib tokenizer (`\b[^\W_]+(?:['’][^\W_]+)?\b`) and excluding frontmatter and code blocks. To preserve agility within the 180-to-750 word band, an embedded `pmp_section` only requires a concise WBS hierarchy line and high-level DoD summary (omitting detailed WBS dictionary fields and formal RTM cross-tables, which are reserved for standalone `full_plan` artifacts).

| Metric | Embedded `pmp_section` | Standalone `full_plan` | Flag Type | Trigger Condition |
|---|---|---|---|---|
| **Word Count Floor** | 180 words | 700 words | `FLAG: BELOW_STANDARD_FLOOR` | Content < floor |
| **Word Count Cap** | 750 words | 4,500 words | `FLAG: EXCEEDS_SECTION_CAP` (`pmp_section`) / `FLAG: EXCEEDS_PLAN_CAP` (`full_plan`) | Content > cap |
| **Out-of-Scope Items** | $\ge 2$ distinct items | $\ge 4$ distinct items | `FLAG: MISSING_BOUNDARY_DEF` | Items < minimum, unless a valid "None: [rationale]" is present |
| **WBS Decomposition** | Hierarchy defined | Full dictionary rules | `FLAG: MISSING_REQUIRED_SECTION` | Missing WBS rules |
| **Acceptance Criteria** | DoD summary | Comprehensive DoD gates | `FLAG: MISSING_REQUIRED_SECTION` | Missing DoD |

> [!NOTE]
> A distinct out-of-scope item is a Markdown list item with non-placeholder text. Items consisting only of a placeholder (`TBD`, `TBC`, `FIXME`, `N/A`) do not count toward the minimum, so `FLAG: MISSING_BOUNDARY_DEF` still fires. Bracketed tokens such as `[TBD]` remain Tier A integrity blocks (ADR-013 §4.2).

> [!NOTE]
> Requirements Traceability Matrix (RTM) integration in `full_plan` is verified during peer review and semantic linting rather than structural flag count.

### 4.4 Learning Methodology

**Now (implemented):** #3 reasoned resolution under `full` authority with permanent `requires_human_approval: true` through `approve-subsidiary-plan` (ADR-013 §4.2), and #6 durable human override. Methodology choice never grants autonomy, and no selection Episode exists yet (ADR-024).

**Possible later (only if its constraint is lifted):** #13 DPO-style pairwise preference for ranking candidate WBS decompositions from historical project approvals. *Unblocked when:* Sufficient decomposed story branches exist with paired reviewer acceptance/rejection episodes.

### 4.4.1 Learner Decision

**Decision:** Build one advisory learner for the Scope Management Plan, as the policy `advise-scope-plan-decision`. The shape is declared with this standard and stays idle, with zero episodes and baseline logits, until real recommendation-versus-decision pairs exist. Synthetic episodes are not used. Building goes through BRD, FDD and a story; this ADR only decides that it is built and on which methodology. The methodology was chosen by hand from the `learning-methodology-selection` skill; when the policy is declared, the selection is recorded as an ADR-024 selection Episode with a human-declared profile. None exists yet and none is invented here.

**What it trains:** The decisions made in this area: the route (full plan, PMP section or N/A with reason), paragraph sufficiency against §4.3, graduation of an over-cap PMP section, and acceptance of a flagged deviation. These four decision types were confirmed as one task id with four kinds (FDD-025 §5 item 1, 2026-10-30, Menno): each recommendation call passes one kind and the bandit draws only within that kind's action set.

**Selected methodology:** #2 softmax bandit with REINFORCE at `low` authority, over a small discrete recommendation set. It fits `learning-methodology-selection` step 3: the decision recurs, the action set is small, and outcomes are contrastive because the human either follows or overrides the recommendation. The reward comes from #5 reward shaping applied to the human decision recorded through #6 durable human override (followed is positive, overridden is negative). The learner trains on the recommendation, not on the approval decision itself.

**Boundaries:**
* Advisory only. The learner recommends and never approves; `approve-subsidiary-plan` stays `full` authority with permanent `requires_human_approval: true`, and its episodes are meant to stay outside REINFORCE (ADR-013 §4.2, ADR-001 §4.2). ADR-001 §4.5 records that this exclusion is not yet enforced in code, so the learner uses its own task id and never shares one with a gate policy.
* The recommendation and the human decision are both recorded; the gap between them is evidence.
* Methodology choice grants no autonomy. The complexity tier is declared by a human in the policy profile and its evidence gate in `autonomy-complexity.md` applies.
* No warm start is assumed. A shared prior across the nine learners (#15, ADR-020) is an untested hypothesis (HYP-AL-008) and is not built; each learner starts cold.
* Positive-only history would plateau REINFORCE (HYP-AL-002). Overrides must therefore be recorded as faithfully as agreements, or the learner is not trained.
* Anchoring and thin data: the learner's recommendation is persisted with a timestamp before the human sees it, so it cannot be altered after the decision. A minimum number of recorded decisions for this area is declared by the maintainer in the policy profile, above the tier minimum, and until it is reached the recommendation is stored but not shown. The number is not set here because no data exists to justify one.

**Plan-specific note:** Out-of-scope sufficiency is a measured floor here (§4.3), so it is one of this learner's paragraph-sufficiency checks. The later candidate stays #13 DPO-style pairwise preference, for ranking candidate WBS decompositions once paired reviewer accept/reject episodes exist.

Source: `learning-methodology-selection` skill and Ideation Document §2.1.

---

### 4.5 PMBOK 8 Alignment

**Source:** *A Guide to the Project Management Body of Knowledge*, Eighth Edition, Plan Scope Management (Figure 2-14). The figure lists end with "Etc.", so the rows below are what the figure names, not an exhaustive set. This subsection records how the ADR relates to the guide; it does not change `depends_on`, `PLAN_DAG` or any threshold.

| | PMBOK 8 | This ADR |
|---|---|---|
| Inputs | Project charter; project management plan; project documents (requirements documentation, risk register, stakeholder register); enterprise environmental factors; organizational process assets. | Charter, Ideation Document and Business Case in; Scope Management Plan out, with the WBS decomposition, Out-of-Scope list and Definition of Done (§4.2). |
| Tools and techniques | Expert judgment; data gathering (interviews, focus groups, questionnaires and surveys); data analysis; test and inspection planning. | Not prescribed; the standard sets structure and measured thresholds and leaves method to the generator and the human reviewer. |
| Outputs | Project management plan updates: scope management plan, requirements management plan, quality management plan. | See §4.1 `outputs` and §4.2. |

**Differences and decisions:**

* **Outputs are wider in the guide.** The same process yields a requirements management plan and a quality management plan. Here the quality plan is its own standard (ADR-029); a requirements management plan has no ADR. Decision: leave both as they are. Whether a requirements management plan is needed is an open question for the maintainer.
* **Requirements documentation, risk register and stakeholder register are guide inputs.** Here they come after Scope (Risk and Stakeholder Engagement depend on Scope in `PLAN_DAG`). Decision: Scope reads them if they exist, but they are not gating inputs and there is no staleness edge back to Scope; a human decides when a change in them calls for re-baselining Scope.
* **Tools and techniques are not specified here.** The guide names interviews, focus groups, questionnaires and test and inspection planning. Decision: not adopted as requirements. The plan standards set structure and measured thresholds, and leave method to the generator and the human reviewer.

## 5. Architectural Invariants
1. **Scope Precedes Schedule and Cost:** Scope drafting and approval must precede Schedule and Cost baseline finalization in the causal DAG.
2. **Mandatory Out-of-Scope Declaration:** A Scope Management Plan without an explicit out-of-scope section (or a valid "None: rationale") raises `FLAG: MISSING_BOUNDARY_DEF`; approval then requires a recorded human rationale in `Episode.metadata`. This is a Tier C flag, not a mechanical block (ADR-012 Invariant 8).
3. **No Silent Omission:** Setting route to `not_applicable` triggers `FLAG: OMISSION_OF_BASE_PLAN` requiring explicit sponsor approval and rationale (ADR-011 §3.2 and Invariant #2).
4. **Remedial Breakouts & Rejection Governance:** 'Breakout' in this context refers strictly to automated intra-section remedial regeneration (ADR-012 §4.5) when a staged section fails linting or formalization; it is never an upfront ceremony or human breakout session. Neither the ADR nor the Scope plan requires prior breakout sessions or pre-existing deliverables before being made available. Symmetrically, if a standalone `full_plan` is rejected under `approve-subsidiary-plan`, its lifecycle state projects to `REJECTED` or `REVISION_REQUESTED` from `LearningStore` episodes (ADR-034 §4.2.2), returning to `DRAFTED` upon staged file modification. In either route, downstream dependent plans become `STALE_DEPENDENCY` per ADR-013 §4.5.
5. **Graduation:** If a `pmp_section` exceeds 750 words, the linter emits `FLAG: EXCEEDS_SECTION_CAP`, prompting the team to graduate the plan to `docs/project-docs/management-plans/Scope-Management-Plan.md`.
6. **Integrity Blocks:** Frontmatter containing `generator: stub` or bodies containing unresolved `[TODO]` tokens are technical integrity violations that mechanically block `approve_plan` (ADR-013 §4.2).
7. **Precedence Hierarchy:** Follows ADR-012 §4.3.4: Tier A (Hard Blocks, ADR-013 §4.2) > Tier B (Structural Flags, ADR-012) > Tier C (Content Flags, ADR-011).

---

## 6. Alternatives Considered
* **Alternative 1: Allow Scope to be Inferred from User Stories without a Plan.**  
  * *Rejected:* Inverting the hierarchy allows backlog items to dictate strategy without high-level boundary controls, causing rampant scope creep.
* **Alternative 2: Combine Scope and Schedule into a Single Document.**  
  * *Rejected:* Violates LL-015 (component credit assignment). Scope defines *what* is built; Schedule defines *when* and in what sequence. Conflating them obscures whether slippages are due to scope expansion or estimation inaccuracies.

---

## 7. Consequences

### Positive
* **Defends the Baseline:** Clear out-of-scope boundaries prevent unmanaged feature creep from generative agents and maintainers.
* **Deterministic Causal Anchor:** Provides the definitive scope foundation from which Schedule durations and Cost budgets are derived.
* **Automated Linter Rules:** Enables deterministic validation of word counts, out-of-scope counts, and DoD definitions.

### Negative
* **Authoring Burden:** Mandates explicit boundary thinking early in the lifecycle, requiring teams to define what they will *not* build before coding begins.

---

## 8. Open Questions & Future Extensions
1. **Automated WBS Extraction:** Should the orchestrator automatically parse existing User Story markdown files to populate the WBS Dictionary during `full_plan` generation? (Deferred to tooling enhancement).
2. **PMBOK 8 Domain Re-basing:** PMBOK 8 has seven performance domains, while the repo uses nine plan areas and one learner per area. The nine are kept; whether learners are regrouped by domain is decided in the plan standards ADR.

---

## 9. Amendment Log

| Date | Change | Why |
|---|---|---|
| 2026-10-25 | Proposed | Initial drafting of ADR-025 Scope Management Plan Standard and Baseline Contract under the ADR-012 framework. |
| 2026-10-25 | Amended for ADR-012 Alignment | Aligned frontmatter schema with ADR-012 (removed in-file hash, added `owner_role`, `generator`, `depends_on: []`, authentic PMBOK 8 `Scope` domain under `Planning` focus area), updated Section 3 to Decision Rights, and corrected staleness references to ADR-013 §4.5. |
| 2026-10-25 | Polish & Errata (Round 3 Review) | Aligned Tier 1 omission citation with ADR-011 §3.2 and Invariant #2, upgraded word tokenizer to Unicode alphanumeric regex with contractions, added Invariant 7 for 3-tier precedence hierarchy. |
| 2026-10-26 | Proposed (Round 4 Review) | Clarified lean 180-word floor for `pmp_section`, made WBS dictionary and RTM optional for `pmp_section`, added disjunctive variance threshold ($\le 1$ SP or localized refactoring), added symmetric `full_plan` rejection governance in Invariant 4, and established $\ge 10$ word rationale requirement for 'None: [rationale]' with exemption in Out-of-Scope count trigger. |
| 2026-10-26 | ADR-012 Alignment Review | Restored literal ADR-012 §4.3.1 headings (Scope content as subsections), split over-cap flag into `EXCEEDS_SECTION_CAP`/`EXCEEDS_PLAN_CAP`, reworded Invariant 2 as a Tier C flag with recorded rationale, switched to the stdlib tokenizer, and described lifecycle states as episode-derived projections. |
| 2026-10-26 | Review Refinements | Clarified `depends_on: []` as root of the subsidiary-plan DAG (governance inputs are not plan nodes), required testable acceptance criteria (semantic review), tightened "localized refactoring", and defined placeholder-only out-of-scope items as non-counting. |
| 2026-10-26 | **Accepted by Menno** | Formally adjudicated and accepted through `approve-adr` TaskPolicy; robust utility 0.944, expected utility 0.965; Episode `432bae92-29a2-4598-8bb0-ec5d38bafbf2`. |
| 2026-10-28 | Daughter ADR Review & Alignment | Added §4.4 Learning Methodology for symmetry with ADR-026–033, linked ADR-037 design-time feedback loop (`BFI-NNN`), and clarified universal downstream invalidation across all 8 daughter plans in `PLAN_DAG`. |
| 2026-10-28 | PMBOK 8 Edition Review | Added §4.5 comparing this standard with the guide's planning process: inputs, tools and techniques, outputs, and each difference with a decision. No change to `depends_on`, `PLAN_DAG`, thresholds or the plan files. Proposed, for maintainer confirmation. |
| 2026-10-28 | Learner Decision | Added §4.4.1 deciding to build the `advise-scope-plan-decision` advisory learner on #2 softmax bandit with REINFORCE at `low` authority, fed by #5 and #6. Advisory only; no episodes created. Corrected the methodology number for pairwise preference from #18 (federated) to #13. This ADR is Accepted. Re-approved 2026-10-29 under `approve-adr` (adjudicated accept, robust utility 0.715 vs. 0.044 reject and 0.110 revise, episode `983c2b87-8309-4414-98fe-93337989b9b5`). |
| 2026-10-28 | Learner Safeguards and Re-basing Gap | Added to §4.4.1 the anchoring and thin-data safeguard, and to §8 the open question on regrouping learners by PMBOK 8 domain. |
| 2026-10-30 | FDD-025 §5 item 1 confirmed | Maintainer confirmed one `advise-scope-plan-decision` task id, four decision kinds per §2 `DECISION_KINDS`, bandit draw scoped to the kind passed on each call; unblocks Epic 25 Stories 25.3–25.4. |
