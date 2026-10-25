# ADR 012: Subsidiary Management Plan Standards and Content Contracts

## 1. Executive Brief
ADR-011 established route tailoring (`full_plan`, `pmp_section`, `not_applicable`) and declared that floors and caps are governance flags rather than mechanical blocks. ADR-013 introduced route-aware per-plan approval gates (`approve-subsidiary-plan`), cryptographic content hashing, technical integrity hard blocks, and staged section persistence (`docs/project-docs/.staging/pmp-sections/`).

However, neither ADR formalized:
1. **The content contract:** What structural sections, metadata schemas, and interfaces must a subsidiary plan contain to be valid?
2. **Quantitative floor and cap thresholds:** How are floors (minimum required substantive content) and caps (maximum boundary before graduation is flagged) calculated, tokenized, and verified?
3. **PMBOK 8 Performance Domain mapping:** How the 9 operational subsidiary management plans bridge to PMBOK 8 Performance Domains while maintaining backward compatibility with legacy tooling process numbers (`5.1` through `13.2`).
4. **Remedial breakout vs. graduation triggers:** The exact conditions under which an embedded section triggers a remedial regeneration versus when it is flagged to graduate to a standalone document, and how downstream staleness propagates.
5. **Decoupled plan standards hierarchy:** How universal plan invariants relate to domain-specific plan standards (Scope, Schedule, Cost, Quality, Resource, Communications, Risk, Procurement, Stakeholder).

This ADR establishes the **universal standard framework and content contract** for all PMBOK subsidiary management plans across the agent-learning repository. Individual plans inherit this framework and specify their domain-specific mechanics through dedicated daughter ADRs, beginning with the three Baseline-Substantiating Plans (Scope, Schedule, Cost).

---

## 2. Status
**Proposed (2026-10-25)** — Drafted to establish the standard framework preceding dedicated domain plan specifications (starting with Scope Management Plan). Ready for multi-criteria evaluation under `approve-adr`.

---

## 3. Context & Problem Statement
* **Current Baseline Deficiencies:** In the initial PMBOK baseline (`PMP-BL-v1.0.0`), 8 of the 9 generated plans in `docs/project-docs/management-plans/` contain generic stub text (`"description": "Stub content for Artifact"`), and the Quality plan has formatting errors. No schema exists to validate whether an LLM generator produced actionable governance mechanics or empty fluff.
* **Ambiguous Section Boundaries:** While ADR-011 introduced the concept of `pmp_section` floors and caps, the absence of quantitative thresholds prevents orchestrator linters from emitting deterministic governance flags.
* **PMBOK 8 Domain vs. Process Mismatch:** `scripts/orchestrate_pmbok.py` hardcodes 6th-edition process numbers (`5.1` to `13.2`). In PMBOK 8th Edition, the 10 Knowledge Areas are replaced by Performance Domains (detailed in `docs/design-notes/planning-redesign-notes.md`). Furthermore, operational plans cross-cut multiple domains (e.g. Risk affects Planning, Uncertainty, and Governance). A flexible bridge mapping primary and secondary domains is required.
* **Credit Assignment Needs Structural Anchoring:** Per LL-008, credit assignment requires that plans are evaluated individually. To evaluate them objectively through `approve-subsidiary-plan`, the evaluator requires a standard rubric and uniform section taxonomy.

---

## 4. Technical Decision

### 4.1 The Universal Three-Section Content Contract
Every subsidiary management plan—whether staged as a `pmp_section` or authored as a standalone `full_plan`—must conform to a uniform three-tier macro-structure:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Mandatory YAML Frontmatter (Metadata Contract)           │
├─────────────────────────────────────────────────────────────┤
│ 2. Section 1: Intent, Alignment & Boundaries                │
│    - Core Mandate & Purpose                                 │
│    - Traceability to Project Charter & Upstream Baseline    │
│    - Explicit Out-of-Scope Boundaries                       │
├─────────────────────────────────────────────────────────────┤
│ 3. Section 2: Domain Mechanics & Standards                  │
│    - Methodologies, Algorithms, & Operational Procedures    │
│    - Baselines, Envelopes, or Tolerance Bands               │
│    - Artifacts & Storage Locations                          │
├─────────────────────────────────────────────────────────────┤
│ 4. Section 3: Governance, Control & Decision Rights         │
│    - Accountable Owner Role & Escalation Target             │
│    - Decision Rights (Baseline Changes, Exception Approvals)│
│    - Variance Thresholds & Review Cadence                   │
│    - Integrated Change Control & Adaptation Triggers        │
└─────────────────────────────────────────────────────────────┘
```

1. **Section 1: Intent, Alignment & Boundaries:** Discloses the plan's mandate, links explicitly to the [Project Charter](../project-docs/Project-Charter.md) and upstream dependencies, and explicitly documents **out-of-scope boundaries**. If a plan genuinely has no out-of-scope items, it must explicitly record an entry: *"None: [rationale]"* rather than omitting the section.
2. **Section 2: Domain Mechanics & Standards:** Details the concrete operational practices for that domain (e.g., WBS dictionary for Scope; CPM/milestones for Schedule; EVM/burn rates for Cost; probability-impact matrices for Risk).
3. **Section 3: Governance, Control & Decision Rights:** Identifies the functional owner role, explicit decision authority (who approves baseline changes, who authorizes variance exceptions, who accepts deliverables), variance tolerances (e.g. $\pm 10\%$ cost variance, 2-day schedule slippage), escalation bodies, and adaptation loop triggers.

### 4.2 Universal Frontmatter Metadata Schema
Every plan file (`full_plan` or staged `pmp_section`) must begin with strict YAML frontmatter.

```yaml
---
plan_id: "scope-management"              # Unique plan identifier kebab-case
plan_name: "Scope Management Plan"       # Formal human-readable title
pmbok_edition: "PMBOK 8"                 # Governed framework edition
primary_pmbok_domain: "Planning"         # Primary PMBOK 8 Performance Domain
secondary_pmbok_domains:                 # Optional cross-cutting domain associations
  - "Governance"
legacy_process: "5.1 Plan Scope Management" # Backward-compatible PMBOK 6 process code
route: "full_plan"                       # full_plan | pmp_section | not_applicable
generator: "llm"                         # llm | human | stub (ADR-013 §4.2 audit field)
version: "1.0.0"                         # Semantic plan version
baseline_id: "PMP-BL-v1.0.0"             # Target baseline identifier
owner_role: "Project Manager"            # Functional owner role from Stakeholder Register
depends_on:                              # Machine-readable plan_id dependencies for DAG invalidation
  - "charter"
inputs:
  - "Project-Charter.md"
  - "docs/project-docs/Ideation-Document.md"
outputs:
  - "docs/project-docs/management-plans/Scope-Management-Plan.md"
governance_policy: "approve-subsidiary-plan" # "approve-subsidiary-plan" (if full_plan) | "approve-pmp" (if pmp_section)
---
```

> [!NOTE]
> **No In-File Hash Circularity:** `canonical_content_hash` is **not** stored inside the in-file YAML frontmatter. In accordance with ADR-013 §4.2 and §4.3, the canonical hash is computed dynamically over the LF-normalized disk content and persisted strictly within `Episode.metadata` and the `DecisionFrame`. Storing the hash inside the file being hashed creates a self-referential cryptographic cycle.

### 4.3 Standard Floor and Cap Quantifications

#### Measurement Boundary Rules
To ensure deterministic, reproducible linting:
* **Scope of Measurement:** Word count is calculated exclusively on the **Markdown body below the closing frontmatter delimiter (`---`)**.
* **Exclusions:** YAML frontmatter, raw HTML comments, and fenced code blocks (` ``` `) are excluded from the word count.
* **Tokenization Rule:** Words are delimited by standard Unicode whitespace (`\s+`).

#### Baseline Defaults vs. Project-Level Standard
* **Baseline Defaults:** The numbers in the table below define the repository baseline defaults (`standard: baseline`).
* **Charter Standard Scaling:** The Project Charter's declared `project_standard` (ADR-011 §3.3) may scale or raise the floor (e.g. `standard: high-assurance` may require 1,000 words for full plans), but may **never lower** the baseline floor.
* **Daughter ADR Specialization:** Daughter ADRs may specify higher domain-specific floors or tighter caps.
* **Over-Cap Full Plans:** If a standalone `full_plan` exceeds 5,000 words, the linter emits `FLAG: EXCEEDS_PLAN_CAP`, signaling an over-scoped or bloated document that should split auxiliary reference material into technical appendices.

#### Baseline Quantitative Thresholds

| Metric | Embedded `pmp_section` | Standalone `full_plan` | Flag Type | Enforcement Mechanism |
|---|---|---|---|---|
| **Minimum Floor (Word Count)** | 150 words | 600 words | `FLAG: BELOW_STANDARD_FLOOR` | Governance Flag (Human decides with rationale) |
| **Maximum Cap (Word Count)** | 800 words | 5,000 words | `FLAG: EXCEEDS_SECTION_CAP` / `FLAG: EXCEEDS_PLAN_CAP` | Governance Flag (Graduation or Appendix recommendation) |
| **Mandatory Headings** | Sections 1, 2, 3 present | Sections 1, 2, 3 + subsections | `FLAG: MISSING_REQUIRED_SECTION` | Structural Failure (Triggers remediation) |
| **Out-of-Scope Declaration** | Required in §1 | Required in §1 | `FLAG: MISSING_BOUNDARY_DEF` | Governance Flag (Requires explicit boundary or "None") |
| **Owner Role & Generator** | Required in frontmatter | Required in frontmatter | `FLAG: INVALID_METADATA` | Structural Failure (Missing required metadata) |

#### Hard Blocks vs. Governance Flags (ADR-013 §4.2 Alignment)
* **Technical Integrity Hard Blocks (Ruled Out Outright):** In accordance with ADR-013 §4.2, a candidate plan is mechanically ruled out from `approve_plan` if frontmatter carries `generator: stub` or `generator: mock`, if the body contains placeholder tokens (`Stub content for Artifact`, `[Insert here]`, `[TBD]`, `[TODO]`), or if generation encountered an uncaught exception.
* **Governance Flags (Flags, Not Blocks):** Word count deviations below floor or above cap are surfaced as evidence in the `DecisionFrame`. The human adjudicator may approve the plan, provided a non-empty rationale is recorded in `Episode.metadata` (ADR-011 §3.2, ADR-013 Invariant #5).

### 4.4 PMBOK 8 Performance Domain Mapping & Process Bridge
To bridge modern PMBOK 8 Performance Domains with the repository's 6th-edition process numbers in `scripts/orchestrate_pmbok.py`, the orchestrator recognizes the following bidirectional mapping:

```
Primary Performance Domain     Secondary Domains           Legacy Process  Subsidiary Management Plan       Plan Tier
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
Planning                       Governance, Delivery        5.1            Scope Management Plan            Tier 1 (Substantiating)
Planning                       Delivery, Measurement       6.1            Schedule Management Plan         Tier 1 (Substantiating)
Planning                       Governance, Measurement     7.1            Cost Management Plan             Tier 1 (Substantiating)
Uncertainty                    Planning, Governance        11.1           Risk Management Plan             Tier 2 (Governance)
Delivery & Measurement         Planning, Project Work      8.1            Quality Management Plan          Tier 2 (Governance)
Team & Stakeholders            Project Work                9.1            Resource Management Plan         Tier 3 (Execution)
Stakeholders                   Governance, Delivery        13.2           Stakeholder Engagement Plan      Tier 3 (Execution)
Stakeholders & Delivery        Governance                  10.1           Communications Management Plan   Tier 3 (Execution)
Project Work                   Planning, Governance        12.1           Procurement Management Plan      Tier 3 (Execution)
```

#### Plan Tier Definitions
Tiers are functional governance classifications and do not dictate linear DAG execution sequence:
* **Tier 1 (Baseline-Substantiating):** Creates and substantiates core project baselines (Scope, Schedule, Cost). Must be at least a `pmp_section`; cannot be marked `not_applicable` without heavily flagged sponsor sign-off.
* **Tier 2 (Governance & Control):** Establishes systemic control frameworks, risk tolerances, and verification gates (Risk, Quality).
* **Tier 3 (Execution Support):** Provides operational execution, procurement, team resources, and stakeholder mechanisms (Resource, Stakeholder, Communications, Procurement).

### 4.5 Remedial Breakout vs. Graduation Mechanics
ADR-011 §3.5 and ADR-013 §4.4 establish that foundation breakouts are remedial for sections. We formalize the precise state transitions:

```mermaid
flowchart TD
    SectionDraft["Drafted pmp_section (.staging/)"] --> LintCheck{Linter Check}
    
    %% Structural Failures
    LintCheck -->|Structural Failure<br>(Missing Sec / Broken Schema / Stub)| AutoRemedial["Automatic Remedial Breakout<br>(Bounded: Max 2 Retries)"]
    AutoRemedial -->|Regenerate| SectionDraft
    AutoRemedial -->|Max Retries Exceeded| EscalateHuman["Escalate to Human for Manual Intervention"]
    
    %% Floor Flag
    LintCheck -->|Below Floor < 150w| FloorFlag["Emit FLAG: BELOW_STANDARD_FLOOR"]
    FloorFlag --> HumanReviewFloor{Human Review & Decision}
    HumanReviewFloor -->|Accept with Rationale| StagedReady["Section Approved for PMP Formalization"]
    HumanReviewFloor -->|Trigger Remedial Breakout| ManualBreakout["Trigger Foundation Breakout"]
    ManualBreakout --> SectionDraft
    HumanReviewFloor -->|Graduate to Full Plan| GraduateToFull
    
    %% Cap Flag
    LintCheck -->|Exceeds Cap > 800w| CapFlag["Emit FLAG: EXCEEDS_SECTION_CAP"]
    CapFlag --> HumanReviewCap{Human Review & Decision}
    HumanReviewCap -->|Accept as Section with Rationale| StagedReady
    HumanReviewCap -->|Accept Graduation| GraduateToFull["Promote Route to full_plan<br>(Update Tailoring Matrix)"]
    
    GraduateToFull --> FullPlanDraft["Draft full_plan (docs/project-docs/management-plans/)"]
    FullPlanDraft --> EvaluateFull["Evaluate via approve-subsidiary-plan Gate"]
    
    %% Clean Pass
    LintCheck -->|Passed All Standards| StagedReady
    
    %% Rejection from Formalization
    FormalizeGate["approve-pmp Rejection of Section"] -->|Rejection Feedback| ManualBreakout
```

1. **Remedial Foundation Breakout (Intra-Section Correction):**
   * *Structural Failure Trigger:* Missing mandatory sections, broken frontmatter, or stub tokens automatically trigger regeneration (bounded to a maximum of 2 retries before human escalation).
   * *Human Decision Trigger:* If a section is flagged `BELOW_STANDARD_FLOOR`, the human may choose to trigger a foundation breakout.
   * *PMP Gate Rejection Trigger:* If `approve-pmp` rejects an embedded section during formalization, it triggers a remedial breakout.
   * *Staleness Propagation:* Regenerating an embedded section marks all downstream plans in the causal DAG as `STALE_DEPENDENCY` per ADR-013 §4.8.
2. **Graduation (Route Promotion):**
   * *Trigger:* When an embedded section exceeds its 800-word cap (`FLAG: EXCEEDS_SECTION_CAP`) or when project complexity warrants standalone governance, the human adjudicator may promote the route from `pmp_section` to `full_plan`.
   * *Execution:* The tailoring matrix is updated. A standalone plan is drafted under `docs/project-docs/management-plans/<Name>.md`, subjected to `approve-subsidiary-plan`, and the PMP section is reduced to an executive summary and verified link.
   * *Downstream Invalidation:* Graduation triggers downstream re-verification of approvals per ADR-013 §4.4.

### 4.6 The Decoupled Plan Standards ADR Hierarchy
ADR-012 defines the universal contract and meta-rules. Domain-specific plan standards are specified in dedicated daughter ADRs that inherit ADR-012.

> [!NOTE]
> **ADR Numbering Continuity:** ADR-014 through ADR-023 are allocated to learning policies and algorithmic mechanisms; ADR-024 defines the learning methodology selection chain. Daughter plan standard ADRs are allocated starting at ADR-025:

* **Tier 1 — Baseline-Substantiating Plan Standards (The Core Triad):**
  * `ADR-025`: Scope Management Plan Standard (WBS, scope boundaries, acceptance criteria).
  * `ADR-026`: Schedule Management Plan Standard (Progressive elaboration, milestones, timeboxes).
  * `ADR-027`: Cost Management Plan Standard (Staged funding, management envelope, contingency).
* **Tier 2 — Governance & Control Plan Standards:**
  * `ADR-028`: Risk Management Plan Standard (Uncertainty domain, risk taxonomy, thresholds).
  * `ADR-029`: Quality Management Plan Standard (Quality gates, verification criteria, test coverage).
* **Tier 3 — Execution Support Plan Standards:**
  * `ADR-030`: Resource Management Plan Standard (Roles, team allocation, tooling assets).
  * `ADR-031`: Stakeholder Engagement Plan Standard (Stakeholder matrix, engagement levels).
  * `ADR-032`: Communications Management Plan Standard (Cadence, channels, audience).
  * `ADR-033`: Procurement Management Plan Standard (Sourcing strategies, vendors, contracts).

---

## 5. Architectural Invariants
1. **Universal Contract Compliance:** Every subsidiary management plan—whether standalone or staged section—must provide the standard frontmatter and the three canonical sections (Intent, Mechanics, Governance & Decision Rights).
2. **Deterministic Word Count Scope:** Word counts are evaluated on the Markdown body below the closing frontmatter delimiter (`---`), excluding frontmatter, raw HTML, and fenced code blocks.
3. **Floors as Flags, Not Blocks:** Content falling below declared floors generates a `FLAG: BELOW_STANDARD_FLOOR`. Approval requires a recorded human rationale in `Episode.metadata` (ADR-011 Invariant #1, ADR-013 Invariant #5).
4. **Remedial Breakouts Propagate Staleness:** Remedial breakouts regenerate staged sections in `docs/project-docs/.staging/pmp-sections/`. Affected downstream plans become `STALE_DEPENDENCY` per ADR-013 §4.8.
5. **Graduation Preserves Traceability:** Graduating a section to a full plan updates the tailoring matrix, initiates a standalone `approve-subsidiary-plan` gate, and contracts the PMP entry to a summary.
6. **Zero Entity Sprawl:** Linting snapshots, flag resolutions, and approval evidence are persisted as standard `Episode.metadata` when decision frames are evaluated (ADR-002 Invariant #2).
7. **Canonical Hashing Integrity:** All plans are hashed according to the LF-normalized specification defined in ADR-013 §4.3. Hashes are recorded in `Episode.metadata`, never inside the governed markdown file itself.

---

## 6. Alternatives Considered
* **Alternative 1: Monolithic Plan Standard (Single massive ADR defining all 9 plans).**  
  * *Rejected:* A monolithic document mixing Cost, Risk, Procurement, and Scope creates high governance coupling. Modifying the Risk threshold would require re-adjudicating the entire omnibus ADR.
* **Alternative 2: Ad-Hoc Plan Formats Without Shared Frontmatter.**  
  * *Rejected:* LLM generators produce wildly inconsistent markdown structures. Without a rigid frontmatter contract and uniform 3-section layout, automated linter validation and credit assignment are impossible.
* **Alternative 3: Hard System Blocks on Word Count Floors.**  
  * *Rejected:* Direct contradiction of ADR-011 §3.2. Agile and small-scale projects often summarize plans concisely. Human accountability with recorded rationales is superior to rigid mechanical blocking.
* **Alternative 4: Embedding Canonical Content Hashes in Frontmatter.**  
  * *Rejected:* Creates an irreconcilable self-referential hash paradox. Storing the hash in `Episode.metadata` maintains cryptographic verification without mutating the artifact.

---

## 7. Consequences

### Positive
* **Deterministic Linting:** Automated tools can immediately verify whether an LLM plan generation succeeded, meets minimum floors, and adheres to structural contracts before presenting it to human approvers.
* **Predictable Remedial and Graduation Cycles:** Clear triggers define when an embedded section can be automatically regenerated versus when it must graduate.
* **Clean Traceability to PMBOK 8:** Bridges 6th-edition process numbering in current tooling with 8th-edition Performance Domains without breaking backward compatibility.
* **Modular Domain Evolution:** Allows individual plans (e.g., Scope, Cost) to evolve their specific standards in targeted daughter ADRs without invalidating the general framework.

### Negative
* **Schema Rigidity:** Generators must strictly format frontmatter and top-level headings, requiring robust prompt scaffolding.
* **Word Count Heuristics:** Word counts are a proxy for completeness; a verbose plan may pass the floor while lacking depth. Domain-specific daughter ADRs must enforce section-specific substantive criteria.

---

## 8. Open Questions & Future Extensions
1. **Automated Linter Integration:** When should the linter run in the orchestrator? (Target: Run during `scripts/orchestrate_pmbok.py --mode draft` to emit warnings before `approve-subsidiary-plan` is invoked).
2. **Learner Policy Scoring Rubrics:** How do the advisory learners (`docs/design-notes/planning-redesign-notes.md §4.12` and ADR-011 §6) score domain mechanics beyond word count? (Addressed in future learner ADRs).

---

## 9. Amendment Log

| Date | Change | Why |
|---|---|---|
| 2026-10-25 | Proposed | Initial drafting of the universal plan standards and content contracts framework, establishing the three-section contract, quantitative floors/caps, PMBOK 8 mapping, and decoupled daughter ADR hierarchy. |
| 2026-10-25 | Amended after Multi-LLM Review | Resolved self-referential hash paradox (removed hash from frontmatter, anchored in `Episode.metadata` per ADR-013 §4.3). Fixed PMBOK 8 performance domain bridge to primary/secondary mapping. Aligned hard block tokens and added `generator` field. Reworked remedial breakout diagram to ensure floors remain non-blocking flags with human choice, bounding automated retries to 2. Added downstream `STALE_DEPENDENCY` propagation rules for breakout and graduation. Defined deterministic word-count scope (excluding frontmatter/code). Clarified daughter ADR numbering sequence starting at ADR-025. |
