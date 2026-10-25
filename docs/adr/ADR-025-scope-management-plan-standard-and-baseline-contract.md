# ADR 025: Scope Management Plan Standard and Baseline Contract

## 1. Executive Brief
Under **ADR-011** (Project Tailoring and Route Decision) and **ADR-012** (Plan Standards and Content Contracts), the **Scope Management Plan** is designated as the primary **Baseline-Substantiating Plan**. It forms the foundational root node of the planning causal DAG ($5.1 \text{ Scope} \to 6.1 \text{ Schedule} \to 7.1 \text{ Cost}$). In PMBOK 8, Scope is developed within the **Planning Performance Domain**, defining the boundaries, decomposition, and verification mechanisms for all project deliverables.

Prior to this ADR, the repository lacked a concrete normative standard for Scope. As observed in baseline `PMP-BL-v1.0.0`, `docs/project-docs/management-plans/Scope-Management-Plan.md` consisted of generic stub sentences that omitted work breakdown structures, out-of-scope boundaries, and deliverable acceptance criteria.

This ADR formalizes the **Scope Management Plan Standard and Baseline Contract**. It specifies:
1. The required domain mechanics (In-Scope, Out-of-Scope boundaries, WBS decomposition, Deliverable Acceptance).
2. The specific quantitative floors and caps for `pmp_section` and `full_plan` routes.
3. The governance and change control triggers that govern scope variance and downstream dependency invalidation under ADR-013.

---

## 2. Status
**Proposed (2026-10-25)** — First dedicated Baseline-Substantiating Plan standard, inheriting ADR-012. Ready for evaluation under `approve-adr`.

---

## 3. Context & Problem Statement
* **Root Node of the Planning DAG:** Per ADR-013 §4.8, planning dependencies form a directed acyclic graph where Schedule and Cost are causally downstream from Scope. If the Scope baseline is vague or unanchored, all downstream baselines (durations, milestones, budgets) become invalid.
* **The Silent Creep Failure Mode:** Without explicit **Out-of-Scope** declarations, generative agents and development teams progressively expand feature sets without formal governance or resource allocation.
* **ADR-011 Mandate for Baseline Plans:** ADR-011 §4.3 mandates that cost, scope, and schedule plans cannot be casually omitted; setting `not_applicable` on Scope is a strongly flagged deviation requiring an explicit recorded justification.

---

## 4. Technical Decision

### 4.1 Inherited ADR-012 Frontmatter Specification
Every Scope Management Plan artifact (`docs/project-docs/management-plans/Scope-Management-Plan.md` or `.staging/pmp-sections/Scope-Management-Plan.md`) must carry the following frontmatter metadata:

```yaml
---
plan_id: "scope-management"
plan_name: "Scope Management Plan"
pmbok_edition: "PMBOK 8"
pmbok_domain: "Planning"
legacy_process: "5.1 Plan Scope Management"
route: "full_plan" # full_plan | pmp_section | not_applicable
version: "1.0.0"
baseline_id: "PMP-BL-v1.0.0"
author_role: "Project Manager"
canonical_content_hash: "<sha256>"
inputs:
  - "Project-Charter.md"
  - "docs/project-docs/Ideation-Document.md"
  - "docs/project-docs/Business-Case.md"
outputs:
  - "docs/project-docs/management-plans/Scope-Management-Plan.md"
governance_policy: "approve-subsidiary-plan"
---
```

### 4.2 Required Structural Sections & Domain Mechanics

#### Section 1: Intent, Alignment & Scope Boundaries
* **Charter Traceability:** Explicit mapping of project scope to the strategic objectives, high-level requirements, and success metrics declared in [Project-Charter.md](file:///c:/Users/MennoDrescher/source/repos/agent-learning/docs/project-docs/Project-Charter.md).
* **In-Scope Boundary Definition:** Exhaustive itemization of major features, architectural deliverables, code modules, and test suites authorized for development.
* **Mandatory Out-of-Scope Boundary List:** Explicit list of features, platforms, integrations, or capabilities that are **strictly excluded** from the current lifecycle stage or project phase. A plan omitting an out-of-scope list violates ADR-011 Invariant #2 and triggers a linter flag.

#### Section 2: Scope Domain Mechanics & Decomposition
* **Work Breakdown Structure (WBS) Architecture:**
  * Decomposition hierarchy: `Project Phase` $\to$ `Epic` $\to$ `User Story` $\to$ `Work Package / Commit`.
  * WBS Dictionary rules: Each deliverable must define acceptance criteria, owner role, and parent epic traceability.
* **Scope Baseline Definition:** The scope baseline comprises:
  1. The Approved Project Scope Statement.
  2. The WBS and Story Mapping in `docs/project-docs/`.
  3. Acceptance Criteria defined in individual User Story artifacts (`docs/project-docs/User-Stories/`).
* **Requirements Traceability Matrix (RTM) Integration:** Traces high-level business goals (BRD) to functional specifications (FDD) and code verification units (Pytest suites).
* **Deliverable Acceptance & Verification Protocol:** Formal Definition of Done (DoD) required before a deliverable moves to Stage 10 (Verification Evidence).

#### Section 3: Scope Governance, Control & Escalation
* **Accountability:** Project Manager is accountable for scope baseline compliance; Sponsor / Charter Approver is the escalation target for baseline expansions.
* **Variance Tolerances & Escalation:**
  * Unplanned additions $\le 1$ story point / minor refactoring: PM discretion.
  * Structural boundary changes or new feature epics: Triggers Stage 17 Integrated Change Control (`approve-adaptation-plan`) and updates the Project Charter.
* **Transitive Downstream Invalidation:** Per ADR-013 §4.8, any approved Scope baseline modification automatically marks downstream Schedule (6.1) and Cost (7.1) plans as `STALE_DEPENDENCY`, requiring re-evaluation.

---

### 4.3 Floor and Cap Thresholds for Scope

| Metric | Embedded `pmp_section` | Standalone `full_plan` | Flag Type | Trigger Condition |
|---|---|---|---|---|
| **Word Count Floor** | 180 words | 700 words | `BELOW_STANDARD_FLOOR` | Content < floor |
| **Word Count Cap** | 750 words | 4,500 words | `EXCEEDS_SECTION_CAP` | Content > cap |
| **Out-of-Scope Items** | $\ge 2$ distinct items | $\ge 4$ distinct items | `MISSING_OUT_OF_SCOPE` | Items < minimum |
| **WBS Decomposition** | Hierarchy defined | Full dictionary rules | `INCOMPLETE_WBS_RULES` | Missing WBS rules |
| **Acceptance Criteria** | DoD summary | Comprehensive DoD gates | `MISSING_ACCEPTANCE_DOD` | Missing DoD |

---

## 5. Architectural Invariants
1. **Scope Precedes Schedule and Cost:** Scope drafting and approval must precede Schedule and Cost baseline finalization in the causal DAG.
2. **Mandatory Out-of-Scope Declaration:** No Scope Management Plan may be approved without an explicit, non-empty out-of-scope section.
3. **No Silent Omission:** Setting route to `not_applicable` triggers `FLAG: OMISSION_OF_BASE_PLAN` requiring explicit sponsor approval and rationale.
4. **Remedial Breakouts:** If a staged `pmp_section` lacks boundary definitions or falls below 180 words, the orchestrator triggers a remedial foundation breakout within `.staging/pmp-sections/Scope-Management-Plan.md`.
5. **Graduation:** If a `pmp_section` exceeds 750 words, the linter emits `FLAG: EXCEEDS_SECTION_CAP`, prompting the team to graduate the plan to `docs/project-docs/management-plans/Scope-Management-Plan.md`.
6. **Integrity Blocks:** Frontmatter containing `generator: stub` or bodies containing unresolved `[TODO]` tokens are technical integrity violations that mechanically block `approve_plan` (ADR-013 Invariant #1).

---

## 6. Alternatives Considered
* **Alternative 1: Allow Scope to be Inferred from User Stories without a Plan.**  
  * *Rejected:* Inverting the hierarchy allows backlog items to dictate strategy without high-level boundary controls, causing rampant scope creep.
* **Alternative 2: Combine Scope and Schedule into a Single Document.**  
  * *Rejected:* Violates LL-008 (component credit assignment). Scope defines *what* is built; Schedule defines *when* and in what sequence. Conflating them obscures whether slippages are due to scope expansion or estimation inaccuracies.

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

---

## 9. Amendment Log

| Date | Change | Why |
|---|---|---|
| 2026-10-25 | Proposed | Initial drafting of ADR-025 Scope Management Plan Standard and Baseline Contract under the ADR-012 framework. |
