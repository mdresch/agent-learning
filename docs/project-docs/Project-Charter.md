---
artifact_id: "project-charter"
version: "2.0"
date: "2026-11-08"
phase: "Phase 2"
status: "approved"
pmp_baseline: "PMP-BL-v1.0.1"
target_pmp_baseline: "PMP-BL-v1.1.0"
governance_reference: "PCD-20261106-001"
---

# Project Charter — agent-learning Phase 2: Autonomous Feedback Loops & Extensible Architecture

**Version:** 2.0  
**Project Sponsor / Initiator:** Menno Drescher  
**Date:** 2026-11-08  
**Status:** **Approved** (Menno, 2026-11-08; adjudicated via `approve-charter`, episode `b6e2fdba-0468-4951-8ceb-e81f08f2ed9b`) — Phase 1 Closed per `PCD-20261106-001`; Phase 2 Milestones M6–M10 Authorized  
**PMP Baseline:** Governed by `PMP-BL-v1.0.1` (Patch Baseline); Targeting `PMP-BL-v1.1.0` (Phase 2 Minor Increment Baseline).  
**Historical Baseline Archive:** Frozen Phase 1 snapshot preserved in [`docs/project-docs/history/PMP-BL-v1.0.0/Project-Charter.md`](file:///d:/Source/repos/agent-learning/docs/project-docs/history/PMP-BL-v1.0.0/Project-Charter.md).  
**Source Documents:** `docs/project-docs/Spark-Capture.md` v2.0, `docs/project-docs/Ideation-Document.md` v1.14, `docs/project-docs/Benefits-Management-Plan.md` v2.0, `docs/project-docs/Business-Case.md` v2.0, `PCD-20261106-001`, and the Research Library (`docs/research/ideation/`).  
**Research Architecture Note (`LL-044`):** Per `LL-044`, all exploratory comparative framework studies, algorithmic landscape taxonomies, and multi-system integration studies are cleanly decoupled into `docs/research/ideation/`. This Charter focuses strictly on governed phase objectives, deliverables, milestones, resource commitments, and gate controls.

---

## 1. Purpose and Justification

Phase 1 established that **Option A (warm-start / transfer of priors)** and **Option C (Thompson sampling / UCB)** successfully resolved initial cold-start and stuck-decision failures in the `agent-learning` SDK. Specifically, Epic 15 delivered warm-start prior seeding (validating **HYP-AL-008**), Epic 19 delivered deterministic Wilson Lower Bound / UCB bandits (validating **HYP-AL-009**), and Epic 20 completed empirical verification.

Phase 1 concluded with formal close decision [`PCD-20261106-001`](file:///d:/Source/repos/agent-learning/docs/governance/decisions/PCD-20261106-001-Phase-1-Close-Decision.md). That decision formally certified completion of Milestones M1–M5, satisfied the Option B resourcing gate, and authorized the initiation of **Phase 2: Option B (Critique-to-Evidence Ingestion Engine & DPO Pairwise Preference Optimization)**, alongside Contextual Authority Ensemble Routing and Cognitive Feedback Loops.

This Phase 2 Charter formalizes the transition from `PMP-BL-v1.0.1` to minor baseline `PMP-BL-v1.1.0`, defining the scope, milestones, deliverables, resource allocations, and governance controls for Phase 2 execution.

---

## 2. Project Objectives (Phase 2)

### Retrospective Phase 1 Objectives (Satisfied & Closed)
- [x] Resolve Business Case §7 dependency: `SoftmaxPolicy` exposes reusable internal state (Resolved: Yes).
- [x] Validate **HYP-AL-008**: Warm-start reduces episodes to autonomy gate (Validated in Epic 15).
- [x] Validate **HYP-AL-009**: Confidence-interval bandit crosses autonomy gate under positive-only data (Validated in Epic 19).
- [x] Produce recorded decision on whether Option B proceeds (Satisfied via `PCD-20261106-001`).
- [x] End-User Value Research M0.5 (Resolved: Go).

### Active Phase 2 Objectives
1. **Implement Critique-to-Evidence Ingestion Engine (Epic 14):** Build a deterministic tag grammar and parser to convert rich reviewer feedback into structured Bayesian evidence frames, guaranteeing that defect findings lower pooled support and confirmation findings raise it without guessing (`BEN-P2-001`, `HYP-AL-005`).
2. **Implement DPO Pairwise Preference Optimization Engine (Epic 18):** Construct pairwise preference dataset pipelines and train discrete policy logits directly from preference comparisons offline without requiring heavy GPU fine-tuning (`BEN-P2-002`, `HYP-AL-018`).
3. **Implement Contextual Authority Ensemble Routing & Deterministic UCB (Epics 16, 21):** Deploy multi-armed contextual routing with deterministic lower bounds across authority tiers (`BEN-P2-005`, `HYP-AL-016`).
4. **Implement Cognitive Feedback Loops & Packaged Contextual Learning (Epics 22, 38):** Establish closed-loop intent refinement triggers and export packaged contextual policies (`BEN-P2-003`, `HYP-AL-025`).
5. **Establish Upstream Fork Collision Protection Architecture:** Enforce strict isolation of custom extensions into `agent-training-ext/`, keeping core `src/agent_learning` untouched to guarantee conflict-free synchronization with upstream `microsoft/agent-learning` (`BEN-P2-004`, `HYP-AL-026`).
6. **Enforce Research Decoupling (`LL-044`):** Ensure deep exploratory research remains housed in `docs/research/ideation/` without bloating governed lifecycle documents.

---

## 3. Project Scope & Architecture Boundaries

### In Scope (Phase 2)
- **Extension Package Development (`agent-training-ext/`):**
  - *Critique Ingestion Module:* Tag grammar parser, delta rubric, frame modifier, and episode metadata generator (Epic 14).
  - *DPO Preference Module:* Pairwise preference builder, Bradley-Terry / DPO loss formulations for discrete policies (Epic 18).
  - *Contextual Ensemble Router:* Multi-armed contextual routing with deterministic lower confidence bounds (Epics 16, 21).
  - *Continuous Learning Loops:* Closed-loop intent refinement triggers and packaged contextual exports (Epics 22, 38).
- **Contract Test Suites:** Comprehensive unit and integration test coverage in `agent-training-ext/tests/`.
- **Governance Automation Integration:** Linking `phase_rollup.py`, `update_story_status.py`, and `orchestrate_pmbok.py` to `sidpa-template` lifecycle stages.
- **Milestones M6 through M10 Delivery.**

### Out of Scope (Phase 2)
- Direct modification of `src/agent_learning` core upstream files (except for approved extension hooks/registration if upstream explicitly adopts them).
- Introducing deep neural network fine-tuning or GPU hardware dependencies (all algorithms strictly frozen-model, CPU-only, standard library only).
- Unconstrained, non-deterministic natural language processing without grammar constraints.
- Modifying Phase 1 frozen baseline archives (`PMP-BL-v1.0.0` and `PMP-BL-v1.0.1` historical records).

---

## 4. Human Resource Commitments & Sourcing Model

The project operates under an open-source maintainer governance model. Planned resource commitments are established as follows:

| Role | Individual / Group | Focus Area | Capacity Commitment |
|---|---|---|---|
| **Project Sponsor & Maintainer** | Menno Drescher | Governance adjudication, benefits ownership, architecture approval, PR review | Ongoing (Estimated 30–40 hours across Phase 2) |
| **Lead Agent Engineer** | Assistant (Antigravity) | Module design, mathematical formulation, contract test implementation, documentation | Primary engineering throughput across Milestones M6–M10 |
| **External Contributors** | GitHub Community / MPN Contacts | Peer reviews, upstream alignment checks, issue reporting | Voluntary / Precedent-based (`MargoOs`, `adityasinha-aiplan`, `meiwa7`) |

**Upstream Microsoft Channel:** Menno maintains access to the Microsoft Partner Network (MPN) as a formal channel to route proposals and architecture alignments to internal Microsoft maintainers when appropriate.

---

## 5. Stakeholder Alignment & Engagement Strategy

| Stakeholder Category | Primary Interests in Phase 2 | Engagement & Communication Channel |
|---|---|---|
| **Project Sponsor (Menno)** | Value realization, zero status drift, upstream code isolation | Phase gate reviews, PMBOK 18-stage status register |
| **SDK Adopters / Developers** | Sample-efficient discrete policy alignment, CPU-only execution, simple extension API | Python package exports, documentation in `docs/`, example notebooks |
| **PR Reviewers & Code Adjudicators** | Transparent critique ingestion without losing qualitative feedback | Tag grammar CLI tools, automated episode metadata audit trails |
| **Upstream Maintainers (`microsoft/agent-learning`)** | Non-invasive fork maintenance, clean PR boundaries, bug reports | Clean upstream diffs, isolated `agent-training-ext` workspace |

---

## 6. Key Deliverables (Phase 2)

| Deliverable ID | Deliverable Description | Associated Epic | Acceptance Standard |
|---|---|---|---|
| **DEL-P2-01** | Tag Grammar Specification & Deterministic Parser | Epic 14 (Story 14.1) | 100% pass on `test_critique_parse.py`; pure stdlib; rejects invalid tags with line numbers. |
| **DEL-P2-02** | Exact Pooled Support Shift & Doubt Applicator | Epic 14 (Stories 14.2, 14.3) | $|\Delta s_{\text{pooled}} - \delta| \le 10^{-9}$ measured via `DecisionResolver.resolve()`. |
| **DEL-P2-03** | Critique Episode Metadata Formatter | Epic 14 (Story 14.4) | Survives JSON round-trip; attaches to `Episode.metadata["critique_adjustments"]`. |
| **DEL-P2-04** | Pairwise DPO Loss Engine for Discrete Policies | Epic 18 | $\ge 30\%$ sample efficiency gain over online exploration on review corpora. |
| **DEL-P2-05** | Contextual Authority Ensemble Router | Epics 16, 21 | Deterministic Wilson lower bounds routing between `low` and `full` authority tiers. |
| **DEL-P2-06** | Continuous SIDPA Adaptation Pipeline | Epics 22, 38 | Automated execution of Stages 12–18 with 0 drift rows in `phase_rollup.py --check`. |
| **DEL-P2-07** | Isolated `agent-training-ext` Package Structure | Architecture Directive | `src/agent_learning` remains clean diff against upstream Microsoft HEAD. |
| **DEL-P2-08** | Phase 2 Close Decision Package (`PCD-Phase2`) | Phase Close Gate | Formal close decision certifying M6–M10 completion and baselining `PMP-BL-v1.1.0`. |

---

## 7. Milestone Schedule (Milestones M6–M10)

| Milestone | Target Scope / Deliverables | Entry Gate Criteria | Target Milestone Outcome |
|---|---|---|---|
| **M6** | **Critique-to-Evidence Ingestion Engine (Epic 14)** | Stage 8 Authorization; `agent-training-ext` initialized | Stories 14.1–14.6 complete; 32 review records replayed. |
| **M7** | **DPO Pairwise Preference Optimization Engine (Epic 18)** | M6 Complete; pairwise dataset generated | DPO loss engine operationalized and verified. |
| **M8** | **Contextual Authority Ensemble Routing (Epics 16, 21)** | M7 Complete; feature extractors defined | Multi-armed contextual router operationalized. |
| **M9** | **Continuous SIDPA Automation (Epics 22, 38)** | M8 Complete; stage scripts integrated | Automated Stage 12–18 adaptation loop validated. |
| **M10** | **Phase 2 Review & Close Gate Adjudication** | M6–M9 Complete; full regression green | Formal issuance and approval of Phase 2 Close Decision (`PCD-Phase2`). |

*Note: In accordance with open-source project management practices, milestones are dependency-sequenced rather than calendar-fixed.*

---

## 8. Assumptions, Constraints & Dependencies

### Assumptions
1. Downstream review text contains sufficient semantic density to express findings in tag grammar.
2. The maintainer model provides sufficient focused time to adjudicate milestone gates.
3. Upstream `microsoft/agent-learning` core abstractions (`DecisionFrame`, `DecisionOption`, `EvidencePoint`) remain structurally stable.

### Constraints
1. **Upstream Fork Collision Protection:** Custom code must reside exclusively in `agent-training-ext/`. `src/agent_learning/` must remain a pristine reflection of upstream Microsoft code.
2. **Computational Boundary:** Strictly frozen-model, CPU-only, standard library only. Zero GPU hardware or deep neural network framework dependencies.
3. **Decoupled Research Library (`LL-044`):** Exploratory surveys and comparative analyses reside exclusively in `docs/research/ideation/`.
4. **Governance Invariant:** Zero status drift permitted across project registers (`phase_rollup.py --check` must always exit 0).

---

## 9. Risk Management Taxonomy

| Risk ID | Risk Description | Severity | Probability | Planned Mitigation Strategy |
|---|---|---|---|---|
| **RSK-CHARTER-01** | **Tag Grammar Reviewer Resistance:** Reviewers find manual tag authoring tedious. | Medium | High | Support predefined claim-type rubric (`rubric_delta`) so reviewers can tag `[claim: logic error] [verified: yes]` without manual math. |
| **RSK-CHARTER-02** | **Upstream Microsoft Breaking Refactors:** Upstream changes core dataclass signatures. | High | Low | Program against frozen dataclass interfaces; write adapter layers in `agent-training-ext` if necessary. |
| **RSK-CHARTER-03** | **Contextual Feature Overfitting:** Contextual router overfits small episode counts. | High | Medium | Enforce deterministic Wilson lower-bound penalties; regularize feature vectors. |
| **RSK-CHARTER-04** | **Governance Fatigue:** Multi-stage governance slows down small bug fixes. | Medium | Medium | Use Foundation Pack micro-iteration tailoring rules (ADR-034) for trivial updates. |

---

## 10. Success Criteria & Phase Close Conditions

Phase 2 will be declared successful and ready for formal close-out when:
1. **100% Technical Delivery:** Epics 14, 16, 18, 21, 22, and 38 are fully implemented with 100% unit and contract test pass rate.
2. **Hypothesis Resolution:** `HYP-AL-005`, `HYP-AL-018`, `HYP-AL-025`, `HYP-AL-026`, and `HYP-AL-027` are formally resolved with empirical evidence.
3. **Zero Governance Drift:** `python scripts/phase_rollup.py --check` confirms 0 status drift rows across all 18 lifecycle documents.
4. **Clean Fork Verification:** `src/agent_learning` exhibits zero merge conflicts against upstream Microsoft HEAD.
5. **Formal Close Decision:** Issuance and approval of `PCD-Phase2` transitioning the repository to baseline `PMP-BL-v1.1.0`.

---

## 11. Project Authorization & Sign-Off

**Project Sponsor:** Menno Drescher  
**Role:** Project Sponsor, Maintainer, and Initiator  
**Signature Basis:** Adjudicated via `approve-charter` under Bayesian Decision Authority `FULL`.  
**Baseline Anchor:** Governed under `PMP-BL-v1.0.1` targeting minor baseline increment `PMP-BL-v1.1.0`.

---

## Provenance & Completeness Self-Assessment

| Dimension | Verification Status | Notes |
|---|---|---|
| **Purpose & Justification (§1)** | **100% Traced** | Directly cites `PCD-20261106-001`, `Business-Case.md` v2.0, and `Benefits-Management-Plan.md` v2.0. |
| **Objectives (§2)** | **Complete** | Explicitly separates satisfied Phase 1 objectives from active Phase 2 targets. |
| **Scope & Boundaries (§3)** | **Enforced** | Establishes the `agent-training-ext` clean boundary to prevent upstream fork collisions. |
| **Human Sourcing (§4)** | **Sourced & Honest** | Reflects maintainer + assistant model; references real external PR precedent. |
| **Milestones (§7)** | **Cleanly Sequenced** | Formulates Milestones M6 through M10; marks M0–M5 as Completed. |
| **Research Architecture (`LL-044`)** | **Decoupled** | Deep research decoupled into `docs/research/ideation/` to avoid the Monolithic Ideation Trap. |
