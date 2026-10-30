---
plan_id: "scope-management"
plan_name: "Scope Management Plan"
pmbok_edition: "PMBOK 8"
pmbok_focus_area: "Planning"
primary_pmbok_domain: "Scope"
secondary_pmbok_domains:
  - "Governance"
legacy_process: "5.1 Plan Scope Management"
route: "full_plan"
generator: "llm"
version: "1.2.0"
baseline_id: "PMP-BL-v1.0.0"
owner_role: "Project Manager"
depends_on: []
foundation_pack: "docs/project-docs/management-plans/scope-baseline/Scope-Foundation-Pack-Manifest.md"
inputs:
  - "Project-Charter.md"
  - "docs/project-docs/Ideation-Document.md"
  - "docs/project-docs/Business-Case.md"
outputs:
  - "docs/project-docs/management-plans/Scope-Management-Plan.md"
  - "docs/project-docs/management-plans/scope-baseline/Scope-Foundation-Pack-Manifest.md"
  - "docs/project-docs/management-plans/scope-baseline/foundation/"
governance_policy: "approve-subsidiary-plan"
---

# Scope Management Plan — agent-learning

> **PMBOK 8 Domain:** `Scope` (Planning Focus Area) | **Legacy Process:** `5.1 Plan Scope Management`  
> **Governance Policy:** `approve-subsidiary-plan` | **Lifecycle Stage:** `Stage 6 (Planning)`  
> **Route:** `full_plan` | **Baseline Identifier:** `PMP-BL-v1.0.0`  
> **Foundation pack:** [Scope-Foundation-Pack-Manifest.md](scope-baseline/Scope-Foundation-Pack-Manifest.md) (Stage **6.A**, PMBOK §2.2)  
> **Accountable Role:** Project Manager | **Approving Sponsor:** Menno Drescher  
> **Normative Standard:** [ADR-012](../../adr/ADR-012-subsidiary-management-plan-standards-and-content-contracts.md) and [ADR-025](../../adr/ADR-025-scope-management-plan-standard-and-baseline-contract.md)  
> **Charter alignment:** [Project-Charter.md](../Project-Charter.md) — Phase 1 *Warm-Start & Confidence-Interval Bandits*

For `PMP-BL-v1.0.0`, the **integrated scope baseline** = approved **[Scope-Foundation-Pack-Manifest.md](scope-baseline/Scope-Foundation-Pack-Manifest.md)** + approved **this plan** (v1.2+). **Define Scope**, **Develop Scope Structure**, **Monitor and Control Scope**, and **Validate Scope** evidence is in [scope-baseline/foundation/](scope-baseline/foundation/) and is gated per the manifest **6.A** checklist before the first subsidiary approval. **Topic pillars** ([Project-Pillars.md](../Project-Pillars.md)) trace to bands and milestones via [Scope-Pillar-Overview-and-Trace.md](scope-baseline/foundation/Scope-Pillar-Overview-and-Trace.md) (**6.A-0P**). Listing a WBS row does not authorize implementation when execution bands mark that work deferred (see [Scope-Project-Scope-Statement.md](scope-baseline/foundation/Scope-Project-Scope-Statement.md)).

---

## 1. Intent, Alignment & Boundaries

### 1.1 Core Mandate & Charter Traceability
This plan establishes scope mechanisms, verification gates, and boundaries for the `agent-learning` program. **Phase 1** (Charter §2–§3) is the near-term execution focus: warm-start, confidence-interval bandits, and the M5 gate on Option B. The WBS in §2.2 also includes **program and design backlog** work (PMBOK subsidiary-plan machinery, accepted learning ADRs not yet built) so the 100% rule covers the full approved artifact stack. Phase 1 objectives operationalize [Project-Charter.md](../Project-Charter.md) §2 and §3:
1. **Unverified Dependency Resolution:** Resolve whether `SoftmaxPolicy` exposes its converged internal state in a structured format reusable as an initial prior distribution for successor policies (Milestone M1).
2. **Warm-Start Empirical Validation (HYP-AL-008):** Validate whether prior-distribution warm-starting reduces the number of interaction episodes required to achieve statistical autonomy eligibility compared to a cold uniform prior (Milestone M2).
3. **Confidence-Interval Bandit Autonomy (HYP-AL-009):** Validate whether an upper confidence bound (UCB) or Thompson sampling bandit can cross the Wilson lower-bound autonomy threshold when operating under positive-only (survivorship-biased) empirical evidence (Milestone M3).
4. **Phase 2 Resourcing Gate:** Formulate a rigorous, empirical decision on whether Option B (critique-to-evidence ingestion and Direct Preference Optimization) warrants development (Milestone M5).
5. **End-User Value Research (M0.5):** Conduct a time-boxed 40-hour qualitative case analysis to assess willingness-to-pay and end-user value drivers before committing to downstream production deployment.

### 1.2 In-Scope Deliverables & Architectural Modules
The authorized deliverables for Phase 1 are strictly bounded to the following components:
* **M0.5 (End-User Value Analysis):** Qualitative case studies extending beyond the SocialEngage example; preliminary empirical testing of HYP-AL-011 recorded in the Research Log.
* **M1 (State Inspection & Serialization):** Technical verification report and export/import serializers for `SoftmaxPolicy` parameters, preserving numerical stability and policy integrity.
* **M2 (Warm-Start Prior Module):** Concrete implementation of hierarchical prior seeding for discrete bandit policies in `src/agent_learning/`, accompanied by automated warm-start benchmarking fixtures.
* **M3 (Confidence-Interval Bandit Engine):** Mathematical implementation of deterministic UCB-1 and Bayesian Thompson sampling policy resolvers capable of maintaining exploration under positive-only reward feedback.
* **M4 (Autonomy Verification Harness):** Automated synthetic evaluation environment reproducing the 146-episode `validate-intent-foundation` dataset to benchmark autonomy gate crossing against baseline REINFORCE.
* **M5 (Phase 1 Synthesis & Decision Frame):** Comprehensive evaluation episode registering empirical Bayes factors for HYP-AL-008 and HYP-AL-009, feeding the formal Stage 18 Intent Refinement gate.

### 1.3 Mandatory Out-of-Scope Boundary
To prevent silent scope creep and maintain architectural focus, the following capabilities are explicitly **excluded** from Phase 1 scope:
* **Option B Implementation (Critique-to-Evidence & DPO):** No implementation of Direct Preference Optimization (DPO), pairwise reward preference fine-tuning, or offline critique parsers (deferred to Phase 2 per Business Case §6).
* **Multi-Modal / OCR Ingestion:** No image processing, scanned PDF extraction, or integration with external OCR engines (`pytesseract`, `pdf2image`, `pillow`).
* **Relational Database Infrastructure:** Zero new database engines, SQLite tables, or SQLAlchemy schemas, strictly adhering to ADR-002 Invariant #2 and ADR-028.
* **Microservice Web Server Deployment:** No FastAPI or Uvicorn server hosting; the repository remains an embedded Python SDK and CLI tool.
* **Continuous Reinforcement Learning in Production:** No unbounded autonomous policy adaptation without explicit human sign-off gates.

### 1.5 WBS Execution Authorization (Program vs Phase 1)

Normative bands and milestone trace for foundation approval: [Scope-Project-Scope-Statement.md](scope-baseline/foundation/Scope-Project-Scope-Statement.md).

The WBS dictionary is the **complete program backlog**. The table below states **when work may start** without a further baseline change. “Approved spec” means ADR, BRD, FDD, and user stories are Accepted/Approved; it is not permission to implement.

| Band | Epics (indicative) | Authorization | Notes |
| --- | --- | --- | --- |
| **A — Foundation (built or superseded)** | 1–7, 9–13, 36 | Execute under DoD §2.5 | Epic 8.1 superseded by ADR-034/013; surviving PMP gate intent lives in Epics 12–13 and 34. |
| **B — Phase 1 product (Charter §3)** | 15–17, 19–20; harness via 9–10 | **Authorized for Phase 1** | Maps to M2–M4; epsilon-greedy (17) is baseline, not Charter-primary. |
| **C — Phase 2 / Option B (deferred)** | 14, 18 | **Not authorized in Phase 1** | Requires M5 outcome and Level 3 change (§3.1) before `implement-story`. |
| **D — Learning design backlog** | 21, 22, 38 | Approved spec; implement when scheduled | Epic 22 rows trace to ADR-022 until `epic-22-*.md` exists (Level 2). ADR-023 has no user stories yet. Epic 38 Ready. |
| **E — PMBOK baseline machinery** | 25–35, 37, 34 | Program scope; parallel track | Subsidiary-plan lint/advisory (25–33), cycle traceability (35), design-time BFI (37), legacy decommission (34). |
| **F — Governance research** | M0.5, M5 | Charter time-box / gate | Recorded in Charter §5–§7 and Research Log; not decomposed as epics. |

### 1.6 Charter Milestone to WBS Trace
| Milestone | Charter intent | Primary WBS anchor |
| --- | --- | --- |
| **M0.5** | End-user value research (40 h) | Charter §5; HYP-AL-011 |
| **M1** | `SoftmaxPolicy` state inspect / serialize | Epic 20 (warm-start path); M1 report |
| **M2** | Warm-start prior module (HYP-AL-008) | Epics 19, 20 |
| **M3** | UCB / Thompson (HYP-AL-009) | Epics 15, 16 |
| **M4** | Autonomy verification harness | Stories 9.1, 10.1; synthetic fixture per Charter |
| **M5** | Phase 1 synthesis; Option B gate | Story 9.1 / Stage 18; unlocks Band C if approved |

### 1.7 Requirements Traceability (RTM Convention)
Full matrix maintenance is deferred; traceability is **structural** until a generated RTM artifact is added:

1. **Epic** — `docs/user-stories/epic-NN-*.md` header links **ADR**, **BRD**, **FDD**, and `PMP-BL-v1.0.0`.
2. **Story** — Each `## Story N.M` holds acceptance criteria $AC_n$; contract tests live in `tests/test_*.py` named in the epic or story.
3. **Work package** — Closing commit recorded in `implementation-log.md` under that story id.
4. **Governance** — ADR corpus index: [docs/adr/README.md](../../adr/README.md) (Accepted ADR-001–038).

---

### 1.4 PMBOK Input, Process & Output (IPO) Specification
In accordance with PMBOK® Guide 8th Edition (Scope Performance Domain §2.2):
* **Inputs (PMBOK 8 §2.2.2.1 & §4):**
  - **Project Charter:** High-level scope, strategic intent, and approval requirements ([Project-Charter.md](../Project-Charter.md)).
  - **Business Documents:** Business Case ([Business-Case.md](../Business-Case.md)) and Ideation Document ([Ideation-Document.md](../Ideation-Document.md)).
  - **Enterprise Environmental Factors (EEFs):** Organizational governance frameworks, technology constraints (CPU-only execution, frozen models).
  - **Organizational Process Assets (OPAs):** ADR standards ([ADR-012](../../adr/ADR-012-subsidiary-management-plan-standards-and-content-contracts.md), [ADR-025](../../adr/ADR-025-scope-management-plan-standard-and-baseline-contract.md)) and lessons learned.
* **Processes (PMBOK 8 §2.2.2 & §5):**
  - **Plan Scope Management:** Defining how scope is identified, structured, and validated.
  - **Elicit & Analyze Requirements:** Eliciting stakeholder requirements without gold plating.
  - **Define Scope:** Delineating in-scope capabilities and non-negotiable out-of-scope exclusions.
  - **Develop Scope Structure (WBS):** Decomposing scope across 4 tiers (`Phase` $\to$ `Epic` $\to$ `Story` $\to$ `Commit`) with 100% rule.
  - **Validate & Control Scope:** Enforcing Definition of Done (DoD) verification gates and managing scope variance.
* **Outputs (PMBOK 8 §2.2.2 & §4):**
  - **Scope Management Plan:** this document (v1.2+).
  - **Integrated scope baseline:** [Scope-Foundation-Pack-Manifest.md](scope-baseline/Scope-Foundation-Pack-Manifest.md) + foundation artifacts (Define / WBS / Control / Validate).
  - **Requirements Traceability Matrix (RTM):** Convention in §1.7 and [Scope-Validate-Scope.md](scope-baseline/foundation/Scope-Validate-Scope.md); standalone RTM file deferred.

---

## 2. Domain Mechanics & Standards

### 2.1 Work Breakdown Structure (WBS) & Decomposition Hierarchy
Project scope is decomposed across four hierarchical tiers:

$$\text{Project Phase} \longrightarrow \text{Epic} \longrightarrow \text{User Story} \longrightarrow \text{Work Package / Commit}$$

The dictionary in [foundation/Scope-WBS-Dictionary.md](scope-baseline/foundation/Scope-WBS-Dictionary.md) is the user-story tier. On **2026-10-30** it lists **143** story rows: **35** epic files under `docs/user-stories/`, plus **seven** Epic 22 rows reserved for [ADR-022](../../adr/ADR-022-scored-search-decision-compilation.md) before `epic-22-*.md` is authored. No epic file exists for Epic 23 or Epic 24. [ADR-023](../../adr/ADR-023-active-dueling-bandit-ranking-engine.md) is Accepted with **no** user stories yet — not in the dictionary.

The diagram this section used before that date is withdrawn. It named Story 0.1, and it assigned Epics 12–15 to tooling, warm-start serialization, confidence-interval bandits, and phase close. Those headings are not the written stories. The written work for those themes is:

* **Tooling convergence:** Epic 34.
* **Warm-start:** Epics 19 and 20.
* **Confidence-interval bandits:** Epics 15, 16, and 17.
* **Phase close:** Stories 9.1 and 10.1.

A work package is the commit that closes one story, recorded in `implementation-log.md`. This dictionary does not list commits.

### 2.2 WBS Dictionary & 100% Rule

The canonical **143-row** WBS dictionary for `PMP-BL-v1.0.0` is a foundation artifact (PMBOK **Develop Scope Structure**):

**[scope-baseline/foundation/Scope-WBS-Dictionary.md](scope-baseline/foundation/Scope-WBS-Dictionary.md)**

Rules (unchanged): every deliverable maps to one **parent** epic and one user story; each row names an **owner** (PM or delegate in the epic header); unassigned work packages are prohibited; the 100% rule requires dev work, documentation, and tests to trace to approved **acceptance criteria** ($AC_n$). Epic 14 and 18 are Band **C** (not Phase 1 authorized). Epic 22 rows are Band **D** placeholders for ADR-022.

Decomposition hierarchy and epic-file inventory: §2.1.

### 2.3 Implementation Snapshot (First Presentation)
As of the amendment date below, **31** user stories are completed or superseded in practice: Epics **1–7**, **9–13**, and **36** (see `implementation-log.md` and epic status lines). **Epic 8.1** is superseded, not delivered as written. **Bands B, C, D (except completed 36), and E** are predominantly **not built**. Epic **34** (legacy decommission) remains a quality-gate blocker for a fully collecting test suite. This snapshot is informational; the baseline remains the approved WBS, not only completed work.

### 2.4 Scope Baseline Definition
The official **integrated Scope Baseline** for `PMP-BL-v1.0.0` comprises:

1. **[Scope-Foundation-Pack-Manifest.md](scope-baseline/Scope-Foundation-Pack-Manifest.md)** (Stage **6.A-6** roll-up; registry hashes for breakout artifacts).
2. **Scope Management Plan** (this document, **v1.2.0** — subsidiary approval at manifest **6.A-7**).
3. **6.A-0P — Pillar trace:** [Scope-Pillar-Overview-and-Trace.md](scope-baseline/foundation/Scope-Pillar-Overview-and-Trace.md).
4. **6.A-1 — Define Scope:** [Scope-Project-Scope-Statement.md](scope-baseline/foundation/Scope-Project-Scope-Statement.md).
5. **6.A-2 — Develop Scope Structure:** [Scope-WBS-Dictionary.md](scope-baseline/foundation/Scope-WBS-Dictionary.md) (143 story rows).
6. **6.A-3 — Monitor and Control Scope:** [Scope-Monitor-Control-Scope.md](scope-baseline/foundation/Scope-Monitor-Control-Scope.md).
7. **6.A-4 — Validate Scope:** [Scope-Validate-Scope.md](scope-baseline/foundation/Scope-Validate-Scope.md).
8. **6.A-5 — Domain outcomes:** [Scope-Domain-Checklist.md](scope-baseline/foundation/Scope-Domain-Checklist.md).
9. **User story contracts:** Acceptance criteria in `docs/user-stories/` tied to `PMP-BL-v1.0.0` in epic headers.

**Readiness (2026-10-30):** Foundation breakouts **6.A-0P … 6.A-5** are **approved**; manifest **6.A-6** is complete (`pack_status: approved` on manifest **v1.2.0**). This plan **v1.2.0** is **ready** for **`approve-subsidiary-plan`** (**6.A-7**). The integrated baseline is **binding** for downstream plans (Schedule **6.B-0**) only after **6.A-7** and **BFI-002** `applied`.

Phase 1 **execution** is Band **B** plus M0.5/M5; the full baseline still lists Bands C–E for change control and the 100% rule.

### 2.5 Deliverable Acceptance Protocol (Definition of Done)

Normative **Validate Scope** artifact: [Scope-Validate-Scope.md](scope-baseline/foundation/Scope-Validate-Scope.md). Summary: contract tests ($AC_n$), RED-first, stdlib-first implementation, full suite green, `implementation-log.md`, peer-reviewed PR.

---

## 3. Governance, Control & Decision Rights

**Monitor and Control Scope** (variance and staleness): [Scope-Monitor-Control-Scope.md](scope-baseline/foundation/Scope-Monitor-Control-Scope.md).

### 3.1 Accountabilities & Escalation Thresholds
* **Project Manager:** Accountable for enforcing scope boundaries, monitoring backlog drift, and rejecting unauthorized feature requests.
* **Project Sponsor (Menno Drescher):** Holds sovereign authority over project scope, milestone gates, and budget authorization.

| Variance Level | Definition | Authority | Action Required |
|---|---|---|---|
| **Level 0 (Operational)** | Minor refactoring or doc clarification within an approved Story | Developer / Tech Lead | Immediate commit; log in `implementation-log.md`. |
| **Level 1 (Story Scope)** | Adding or adjusting an Acceptance Criterion within an Epic | Project Manager | Update Story spec; notify Sponsor. |
| **Level 2 (Milestone Scope)** | Adding a new User Story or altering an Epic boundary | Project Sponsor | Formal review via Stage 16 Governance Change. |
| **Level 3 (Baseline Breach)** | Adding an Epic, modifying Charter boundaries, or Phase 2 work | Project Sponsor | Stage 17 Integrated Change (`approve-adaptation-plan`). |

### 3.2 Transitive Downstream Invalidation (ADR-013 §4.5)
Per ADR-013 §4.5, Scope forms the foundational root node of the planning directed acyclic graph:
$$\text{Scope Management Plan} \longrightarrow \text{Schedule Management Plan} \longrightarrow \text{Cost Management Plan}$$

Any Level 2 or Level 3 change to this Scope Management Plan automatically marks:
1. `Schedule-Management-Plan.md` as **`STALE_DEPENDENCY`** (requiring schedule recalculation).
2. `Cost-Management-Plan.md` as **`STALE_DEPENDENCY`** (requiring budget re-estimation).

Re-validation of downstream plans must occur before composite formalization under `approve-pmp` is permitted.

### 3.3 Subsidiary approval with scope advisory recommendations (ADR-025 §4.4.1, BRU-025-05–06)

Scope baseline authorization uses **two task ids**. They are sequential in intent but **not** merged into one policy.

| Step | Task id | Authority | Outcome |
| --- | --- | --- | --- |
| 1 — Measure | *(lint only)* | — | `lint_plan` on this file applies ADR-012 plus the Scope profile (ADR-025 / Epic 25). Findings are evidence for the human; they do not approve the plan. |
| 2 — Advise *(optional, when implemented)* | `advise-scope-plan-decision` | **Low** — advisory only | For each maintainer question, the caller passes **one** decision kind (`route`, `paragraph_sufficiency`, `graduation`, `flagged_deviation`). The bandit draws **only** among that kind's actions ([FDD-025](../../project-docs/Functional-Design/FDD-025-scope-management-plan-standard-and-baseline-contract.md) §2 `DECISION_KINDS`, confirmed 2026-10-30). The recommendation and `recommended_at` are **stored before display**; follow or override is recorded for later REINFORCE on the **recommendation action**, not on gate actions. |
| 3 — Decide | `approve-subsidiary-plan` | **Full** — human required | The Project Manager / Sponsor adjudicates `approve_plan`, `reject_plan`, or `request_revision_before_decision`. **Only this step** binds the integrated Scope baseline (manifest **6.A-7**, BFI-002). |

**Operating rule (2026-10-30, Menno):** Human approval is mandatory for subsidiary scope baseline; **`advise-scope-plan-decision` may recommend** route, sufficiency, graduation, or deviation handling **before** that decision. Recommendations never substitute for `approve_plan`. Idle policy shape: [advise-scope-plan-decision.actions.json](../../policy-shapes/advise-scope-plan-decision.actions.json). Implementation: Epic 25 Stories 25.3–25.4; methodology selection episode (ADR-024) is recorded separately when the policy is declared.

---

## Baseline Feedback (Stage 7-8 → 6)

| bfi_id | stage | document | citation | classification | evidence_basis | status |
| --- | ---: | --- | --- | --- | --- | --- |
| BFI-002 | 7 | Scope Management Plan / foundation pack | [ADR-025](../../adr/ADR-025-scope-management-plan-standard-and-baseline-contract.md) §3; [Scope-Foundation-Pack-Manifest.md](scope-baseline/Scope-Foundation-Pack-Manifest.md) § Stage 6.A | *(empty — process interpretation)* | design_time | open |

**BFI-002 (open):** ADR-025 §3 states Scope baselining has no upfront breakout prerequisite. For this repository, **Tier-1 Scope foundation pack** artifacts under Stage **6.A** (PMBOK §2.2 Define / Develop Structure / Monitor & Control / Validate) are **normative** for the first `approve-subsidiary-plan` on `scope-management` v1.2+: integrated baseline = manifest + plan. Documented Path A without amending ADR-025. Close as `applied` when **6.A-7** completes.

---

## 4. Amendment Log

| Date | Author | Description |
|---|---|---|
| 2026-10-25 | Menno Drescher / Antigravity | Initial full baseline Scope Management Plan replacing stub mock content per ADR-012 and ADR-025. |
| 2026-10-30 | Menno Drescher / Cursor | Replaced the WBS diagram with the dictionary of 137 written stories in 35 epics. The previous diagram named stories those files do not contain. |
| 2026-10-30 | Menno Drescher / Cursor | **v1.1.0 — First presentation pass:** unified program WBS and Phase 1 boundaries in one plan; §1.5–§1.7 (authorization bands, milestone map, RTM convention); Epic 38 stories; 143-row dictionary; §2.3 implementation snapshot. |
| 2026-10-30 | Menno Drescher / Cursor | **v1.2.0 — Foundation pack:** Stage 6.A manifest; foundation artifacts per PMBOK §2.2 processes; WBS dictionary relocated to `scope-baseline/foundation/`; integrated baseline = manifest + plan; BFI-002. |
| 2026-10-30 | Menno Drescher / Cursor | **Pillar trace:** [Scope-Pillar-Overview-and-Trace.md](scope-baseline/foundation/Scope-Pillar-Overview-and-Trace.md) (6.A-0P) links scope to [Project-Pillars.md](../Project-Pillars.md). |
| 2026-10-30 | Menno Drescher | [Project-Pillars.md](../Project-Pillars.md) **Approved** (2026-10-30); scope foundation upstream gate satisfied for pillar source. |
| 2026-10-30 | Menno Drescher | Foundation pack **6.A-6** complete; §2.4 aligned to all six breakout artifacts + manifest; plan **ready** for **6.A-7** subsidiary gate. |
