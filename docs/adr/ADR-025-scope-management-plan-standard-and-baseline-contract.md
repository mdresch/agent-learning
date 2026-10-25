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
**Proposed (2026-10-25)** — First dedicated Baseline-Substantiating Plan standard, inheriting ADR-012. Ready for evaluation under `approve-adr`.

---

## 3. Context & Problem Statement
* **Root Node of the Planning DAG:** Per ADR-013 §4.1 and §4.5, planning dependencies form a directed acyclic graph where Schedule and Cost are causally downstream from Scope. If the Scope baseline is vague or unanchored, all downstream baselines (durations, milestones, budgets) become invalid.
* **The Silent Creep Failure Mode:** Without explicit **Out-of-Scope** declarations, generative agents and development teams progressively expand feature sets without formal governance or resource allocation.
* **ADR-011 Mandate for Baseline Plans:** ADR-011 §3.2 and §4.3 mandate that cost, scope, and schedule plans cannot be casually omitted; setting `not_applicable` on Scope is a strongly flagged deviation (`FLAG: OMISSION_OF_BASE_PLAN`) requiring an explicit recorded justification.

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
route: "full_plan" # full_plan | pmp_section | not_applicable
generator: "llm"   # llm | human | stub | mock (ADR-013 §4.2 audit field)
version: "1.0.0"
baseline_id: "<target-baseline-id>"
owner_role: "Project Manager"
depends_on: []     # Root node in DAG (ADR-013 §4.1)
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

#### Section 1: Intent, Alignment & Scope Boundaries
* **Charter Traceability:** Explicit mapping of project scope to the strategic objectives, high-level requirements, and success metrics declared in [Project-Charter.md](../project-docs/Project-Charter.md).
* **In-Scope Boundary Definition:** Exhaustive itemization of major features, architectural deliverables, code modules, and test suites authorized for development.
* **Mandatory Out-of-Scope Boundary List:** Explicit list of features, platforms, integrations, or capabilities that are **strictly excluded** from the current lifecycle stage or project phase. If no exclusions exist, the plan must state *"None: [rationale]"*.

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

#### Section 3: Governance, Control & Decision Rights
* **Accountability & Decision Rights:**
  * Project Manager is accountable for scope baseline compliance.
  * Baseline revisions and expansions require Sponsor / Charter Approver authorization via Stage 17 Integrated Change Control (`approve-adaptation-plan`).
  * Deliverable acceptance authority resides with the Product Owner / PM named in the Stakeholder Register.
* **Variance Tolerances & Escalation:**
  * Unplanned additions $\le 1$ story point / minor refactoring: PM discretion.
  * Structural boundary changes or new feature epics: Triggers Stage 17 Integrated Change Control (`approve-adaptation-plan`) and updates the Project Charter.
* **Transitive Downstream Invalidation:** Per ADR-013 §4.5, any approved Scope baseline modification automatically marks downstream Schedule (6.1) and Cost (7.1) plans as `STALE_DEPENDENCY`, requiring re-evaluation.

---

### 4.3 Floor and Cap Thresholds for Scope

Word count is measured on the Markdown body below `---`, tokenizing alphanumeric words (`\b[a-zA-Z0-9_-]+\b`) and excluding frontmatter and code blocks.

| Metric | Embedded `pmp_section` | Standalone `full_plan` | Flag Type | Trigger Condition |
|---|---|---|---|---|
| **Word Count Floor** | 180 words | 700 words | `FLAG: BELOW_STANDARD_FLOOR` | Content < floor |
| **Word Count Cap** | 750 words | 4,500 words | `FLAG: EXCEEDS_SECTION_CAP` | Content > cap |
| **Out-of-Scope Items** | $\ge 2$ distinct items | $\ge 4$ distinct items | `FLAG: MISSING_BOUNDARY_DEF` | Items < minimum |
| **WBS Decomposition** | Hierarchy defined | Full dictionary rules | `FLAG: MISSING_REQUIRED_SECTION` | Missing WBS rules |
| **Acceptance Criteria** | DoD summary | Comprehensive DoD gates | `FLAG: MISSING_REQUIRED_SECTION` | Missing DoD |

---

## 5. Architectural Invariants
1. **Scope Precedes Schedule and Cost:** Scope drafting and approval must precede Schedule and Cost baseline finalization in the causal DAG.
2. **Mandatory Out-of-Scope Declaration:** No Scope Management Plan may be approved without an explicit out-of-scope section (or recorded "None: rationale").
3. **No Silent Omission:** Setting route to `not_applicable` triggers `FLAG: OMISSION_OF_BASE_PLAN` requiring explicit sponsor approval and rationale (ADR-011 §3.2).
4. **Remedial Breakouts:** If a staged `pmp_section` suffers structural failure or is rejected during PMP formalization (`approve-pmp`), the orchestrator triggers a remedial foundation breakout within `.staging/pmp-sections/Scope-Management-Plan.md`. Downstream plans become `STALE_DEPENDENCY` per ADR-013 §4.5.
5. **Graduation:** If a `pmp_section` exceeds 750 words, the linter emits `FLAG: EXCEEDS_SECTION_CAP`, prompting the team to graduate the plan to `docs/project-docs/management-plans/Scope-Management-Plan.md`.
6. **Integrity Blocks:** Frontmatter containing `generator: stub` or bodies containing unresolved `[TODO]` tokens are technical integrity violations that mechanically block `approve_plan` (ADR-013 §4.2).

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
| 2026-10-25 | Amended for ADR-012 Alignment | Aligned frontmatter schema with ADR-012 (removed in-file hash, added `owner_role`, `generator`, `depends_on: []`, authentic PMBOK 8 `Scope` domain under `Planning` focus area), updated Section 3 to Decision Rights, and corrected staleness references to ADR-013 §4.5. |
