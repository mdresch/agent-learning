---
artifact_id: "business-case"
version: "2.1"
date: "2026-11-12"
phase: "Phase 2"
status: "pending re-approval (GC-P2-05 reconciliation)"
pmp_baseline: "PMP-BL-v1.0.1"
target_pmp_baseline: "PMP-BL-v1.1.0"
governance_reference: "PCD-20261106-001"
---

# Business Case — agent-learning Phase 2: Autonomous Feedback Loops & Extensible Architecture

## Executive Summary & Metadata Block

| Field | Value |
|---|---|
| **Document Title** | Business Case — agent-learning Phase 2: Autonomous Feedback Loops & Extensible Architecture |
| **Version** | 2.1 |
| **Date** | 2026-11-12 |
| **Status** | Pending re-approval (GC-P2-05 reconciliation — see Amendment Log) — v2.0 last approved 2026-11-08 (Menno; adjudicated via `approve-business-case`, episode `eca6fc5c-966b-4088-b0f6-157f57e99d52`); Governed under `PMP-BL-v1.0.1` targeting `PMP-BL-v1.1.0`. |
| **Author** | Project Team (Maintainer & Assistant), building on `Spark-Capture.md` v2.0 and `Ideation-Document.md` v1.14 |
| **Approver** | Menno Drescher (Sponsor, Project Manager, and Maintainer) |
| **Source Documents** | `Spark-Capture.md` v2.0, `Ideation-Document.md` v1.14, `Benefits-Management-Plan.md` v2.0, `PCD-20261106-001`, and the Research Library (`docs/research/ideation/`). |
| **Research Architecture (`LL-044`)** | In accordance with `LL-044` ("The Monolithic Ideation Trap"), exploratory taxonomies and comparative framework benchmarks reside in `docs/research/ideation/`. This Business Case focuses strictly on strategic justification, economic trade-offs, architecture isolation, and governance gates. |

---

## 1. Problem Statement & Operational Drivers

In Phase 1, `agent-learning` successfully solved cold-start initialization (`WarmStartSoftmaxPolicy`, Epic 15) and sparse-evidence bandit stagnation (`WilsonScoreUCBPolicy`, Epic 19). However, operational experience closing Phase 1 (Stages 11–18) surfaced four critical capability gaps:

1. **Rich Review Critique Is Generated and Discarded:**  
   During code reviews and governance gate checks, human reviewers and automated tools (e.g. Amazon Q) produce nuanced, tagged critique lines. Currently, this critique is discarded by reinforcement learning algorithms (REINFORCE/UCB) which consume only a scalar reward, losing the specific evidential reasoning behind the feedback.
2. **Absence of Lightweight, CPU-Only Preference Alignment (DPO):**  
   While large language model agents rely on heavy GPU fine-tuning for alignment, discrete decision-policy bandits have no packaged path to optimize directly from pairwise preference comparisons `(preferred, rejected)`, forcing policies to rely entirely on trial-and-error exploration.
3. **Continuous Governance Toil in Lifecycle Adaptation (Stages 12–18):**  
   Synthesizing actual outcomes, observations, insights, lessons learned, and governance changes into an actionable adaptation plan currently requires substantial manual maintenance, risking document status drift and slow cycle times.
4. **Upstream Fork Collision Vulnerability:**  
   Modifying the core `microsoft/agent-learning` codebase directly introduces substantial risk of git merge conflicts when synchronizing with upstream Microsoft updates. A clean architectural decoupling is urgently required to isolate repository extensions into a dedicated `src/agent_learning_ext` workspace.

**Root Cause:** The Phase 1 platform lacks an ingestion grammar for qualitative feedback, an offline preference optimization algorithm, and an isolated extension module structure.

---

## 2. Gap Analysis Matrix (Phase 2)

| Dimension | Phase 1 Baseline State (`PMP-BL-v1.0.1`) | Desired Phase 2 Target State (`PMP-BL-v1.1.0`) | Capability Gap |
|---|---|---|---|
| **Textual Critique Ingestion** | Text critique discarded; only scalar reward consumed | Deterministic Tag Grammar parses critique directly into Bayesian `EvidencePoint`s with exact shift arithmetic | Epic 14 (ADR-014, `HYP-AL-005`) |
| **Preference Alignment** | Policy updates require online exploration or scalar reward shaping | Direct Preference Optimization (DPO) optimizes discrete policy logits from pairwise comparisons offline | Epic 18 (ADR-018, `HYP-AL-028`) |
| **Continuous Adaptation Loop** | Stages 12–18 adaptation plans authored and tracked manually | Automated script synthesis and validation (`orchestrate_pmbok.py`, `phase_rollup.py`) integrated with `sidpa-template` | Epics 22, 38 (`HYP-AL-025`) |
| **Upstream Fork Protection** | Custom code mixed with upstream files in `src/agent_learning` | All custom extensions isolated in `src/agent_learning_ext/`, leaving core upstream untouched | Architecture Directive (`HYP-AL-026`, `HYP-AL-027`) |
| **Authority Ensembling** | Policy authority mode (`low` vs `full`) fixed statically at init | Dynamic contextual routing ensembles models based on predictive uncertainty | Epics 16, 21 (ADR-016, ADR-021; no hypothesis registered — see note) |

> **Authority Ensembling hypothesis note (2026-11-13, PR #208 review, Amazon Q Developer):** this row previously cited `HYP-AL-016`, which is a different, withdrawn hypothesis (the RPAS-BA-Workbench CF rating-band claim — `Hypothesis-Register.md` §2). No hypothesis for the dynamic-contextual-routing claim above was ever actually registered; ADR-016/ADR-021 and Epics 16/21 are real and implemented, but this gap's own underlying claim has not been stated as a falsifiable hypothesis. The citation is removed rather than force-fit to an unrelated id.

---

## 3. Proposed Solution Options & Trade-Off Analysis

To address the Phase 2 gaps, three strategic implementation approaches were evaluated:

### Weighted Decision Criteria Table

| Criterion | Weight | Option 1: In-Tree Core Modifications | Option 2: External Script Workarounds | Option 3 (Selected): Governed Modular Extension (`src/agent_learning_ext`) |
|---|---|---|---|---|
| **Upstream Merge Immunity** | 0.30 | 1 (Guaranteed conflicts) | 4 (Disconnected scripts) | **5 (Clean package isolation)** |
| **Governance & Audit Integrity** | 0.25 | 4 (In-repo, but brittle) | 2 (Unversioned/untested) | **5 (Strict PMBOK / SIDPA lifecycle)** |
| **Algorithmic Exactness** | 0.20 | 4 (Direct access) | 2 (Approximations) | **5 (Pure mathematical contracts, 1e-9 tolerance)** |
| **Implementation Complexity** | 0.15 | 4 (Simple in-tree) | 5 (Ad-hoc scripts) | **3 (Requires dual-package PYTHONPATH setup)** |
| **Maintainability & Portability** | 0.10 | 2 (Polluted fork) | 2 (Fragmented) | **5 (Independent publishable extension)** |
| **Weighted Score** | **1.00** | **2.65** | **3.05** | **4.65** |

### Solution Integrity Assessment

- **Option 1 (In-Tree Core Modifications):** Directly adding critique ingestion and DPO into `src/agent_learning/` is initially fast, but decisively rejected due to upstream fork pollution. Any future sync from `microsoft/agent-learning` would result in merge conflicts.
- **Option 2 (External Script Workarounds):** Writing standalone scripts outside the repository avoids upstream conflicts, but breaks traceability, unit testing rigor, and governance gating.
- **Option 3 (Selected — Governed Modular Extension via `src/agent_learning_ext`):** Custom algorithms are packaged in `src/agent_learning_ext/`, importing frozen dataclasses and interfaces from `src/agent_learning/decision.py`. This guarantees zero upstream collisions, 100% contract testability, and full alignment with PMBOK 8 governance standards.

---

## 4. Strategic Hypotheses & Direct Evidence

### 4a. Phase 1 Hypotheses (Validated & Closed)

| Hypothesis ID | Statement | Delivered Deliverable | Phase 1 Outcome |
|---|---|---|---|
| **HYP-AL-008** | Warm-starting policy priors reduces cold-start episodes vs uniform prior. | Epic 15 (`WarmStartSoftmaxPolicy`) | **VALIDATED** (Significant episode reduction on structurally similar policies). |
| **HYP-AL-009** | Confidence-interval bandits (Wilson UCB) overcome positive-only evidence plateaus. | Epic 19 (`WilsonScoreUCBPolicy`) | **VALIDATED** (Autonomy gate crossed on `validate-intent-foundation` data). |

### 4b. Phase 2 Active Hypotheses

| Hypothesis ID | Type | Statement & Expected Value | Falsification Criteria & Validation Method |
|---|---|---|---|
| **HYP-AL-005** | Technical | Review critique parsed into signed deltas moves pooled support by exactly the delta without altering unreferenced criteria. | Falsified if a negative finding raises pooled support, a positive finding lowers it, or numerical deviation $> 10^{-9}$ measured via `DecisionResolver.resolve()`. Validated via Epic 14. |
| **HYP-AL-028** | Technical | DPO loss optimization on discrete policy logits converges with $\ge 30\%$ fewer feedback interactions than online REINFORCE. | Falsified if DPO requires equal or more sample episodes than REINFORCE on pairwise review benchmark datasets. Validated via Epic 18. |
| **HYP-AL-025** | Process | Automated Stage 12–18 adaptation loops eliminate status drift across all 18 lifecycle documents. | Falsified if `phase_rollup.py --check` reports $>0$ drift rows during a continuous learning release. Validated via Epics 22 & 38. |
| **HYP-AL-026** | Architecture | Decoupling custom extensions into `src/agent_learning_ext` allows git rebase against upstream Microsoft HEAD with 0 conflicts. | Falsified if upstream branch synchronization requires resolving merge conflicts in `src/agent_learning/`. Validated at Milestone M10. |

---

## 5. Financial Architecture & Resource Allocation

As an open-source research and engineering effort, financial valuation is expressed in terms of engineering capacity and risk avoidance:

- **Total Phase 2 Engineering Budget:** Estimated at **120–160 focused engineering hours** across Milestones M6–M10.
- **Resource Breakdown:**
  - *Milestone M6 (Critique Ingestion Engine / Epic 14):* 30 hours.
  - *Milestone M7 (DPO Preference Engine / Epic 18):* 35 hours.
  - *Milestone M8 (Contextual Routing & Ensemble / Epics 16, 21):* 30 hours.
  - *Milestone M9 (Continuous SIDPA Automation / Epics 22, 38):* 35 hours.
  - *Milestone M10 (Integration, Verification, Phase Close):* 20 hours.
- **Economic Value Realization:**
  - **Avoided Upstream Merge Costs:** Eliminates estimated 40+ hours of manual conflict resolution per upstream sync.
  - **Turnaround Velocity:** Reduces reviewer adjudication cycle time by $\ge 40\%$ through automated critique-to-evidence translation.
  - **Compliance Assurance:** 100% elimination of audit status drift, ensuring seamless handoffs.

---

## 6. Sensitivity Analysis & Risk Taxonomy

| Risk ID | Risk Event | Severity | Probability | Mitigation Strategy |
|---|---|---|---|---|
| **RSK-P2-001** | Reviewer formatting errors in critique bullet tags. | Medium | High | Robust grammar parser rejecting non-compliant lines with specific line numbers; fallback delta rubric (`rubric_delta`). |
| **RSK-P2-002** | Extreme reviewer score distortion (swamping existing evidence). | High | Low | Clamping mechanism (`TARGET_EPSILON = 1e-6`) and doubt multiplier $\kappa \in [0.1, 0.5]$ to prevent probability collapse. |
| **RSK-P2-003** | Upstream Microsoft architectural refactor of base classes. | High | Low | Pure stdlib contracts; `src/agent_learning_ext` interfaces only with public frozen dataclasses (`DecisionFrame`, `DecisionOption`, `EvidencePoint`). |
| **RSK-P2-004** | Single-maintainer cognitive overload across 18 stages. | Medium | Medium | Automated stage rollup and validation scripts (`phase_rollup.py`, `update_story_status.py`) operationalized in Stage 17. |

---

## 7. Packaging & Dependency Architecture

```
agent-learning/ (Repository Root)
├── src/agent_learning/          <-- Upstream Microsoft core (CLEAN, FROZEN)
│   ├── decision.py              <-- DecisionFrame, EvidencePoint, DecisionResolver
│   └── types.py                 <-- Episode, Action
├── src/agent_learning_ext/          <-- Custom Extension Workspace (NEW)
│   ├── critique_evidence.py     <-- Pure parser & delta applicator (Epic 14)
│   ├── dpo_preference.py        <-- Pairwise discrete DPO optimizer (Epic 18)
│   └── tests/                   <-- Extension contract test suites
└── docs/project-docs/           <-- PMBOK 8 / SIDPA Governed Artifacts
```

- **Dependency Invariant:** Modules in `src/agent_learning_ext` import strictly standard library modules (`re`, `math`, `dataclasses`, `typing`) and public data structures from `agent_learning.decision`. No imports from `agent_learning.storage` and zero file/network I/O.
- **Runtime Purity:** Zero performance impact on upstream `agent-learning` core execution.

---

## 8. Stakeholder Alignment & RACI Model

| Role | Individual / Group | Responsibilities |
|---|---|---|
| **Accountable (A)** | Menno Drescher (Sponsor) | Approves Business Case, Charter, and baselines; owns benefits realization. |
| **Responsible (R)** | Assistant / Lead Engineer | Authors artifacts, develops extension packages, and authors contract test suites. |
| **Consulted (C)** | Downstream Adopters & Reviewers | Provides feedback on tag grammar ergonomics and DPO convergence metrics. |
| **Informed (I)** | Community & Stakeholders | Receives release notices, changelogs, and audit records. |

---

## 9. Requirements Traceability & Success Criteria

| Requirement | Traced Spark / Hypothesis | Verification Standard | Target Milestone |
|---|---|---|---|
| **REQ-P2-01: Critique Tag Parsing** | `SPARK-001` / `HYP-AL-005` | 100% pass on `test_critique_parse.py` across all grammar edge cases. | M6 |
| **REQ-P2-02: Exact Support Shift** | `SPARK-001` / `HYP-AL-005` | $|\Delta s_{\text{pooled}} - \delta| \le 10^{-9}$ measured via `DecisionResolver.resolve()`. | M6 |
| **REQ-P2-03: Discrete Policy DPO** | `SPARK-002` / `HYP-AL-028` | Convergence on paired comparison datasets without GPU requirements. | M7 |
| **REQ-P2-04: Extension Decoupling** | Directive / `HYP-AL-026` | `src/agent_learning` remains 100% clean diff against upstream baseline. | M6–M10 |
| **REQ-P2-05: Zero Governance Drift** | `SPARK-003` / `HYP-AL-025` | `phase_rollup.py --check` exits with 0 drift rows throughout Phase 2. | M6–M10 |

---

## 10. Strategic Recommendation & Implementation Roadmap

**Formal Recommendation:** Proceed with Phase 2 implementation under **Option 3 (Governed Modular Extension via `src/agent_learning_ext`)**, deploying the scope across Milestones M6 through M10:

1. **Milestone M6 (Lead): Critique-to-Evidence Ingestion Engine (Epic 14)**  
   Deploy `critique_evidence.py` and contract tests in `src/agent_learning_ext/`. Execute Stories 14.1 through 14.6.
2. **Milestone M7: DPO Pairwise Preference Optimization (Epic 18)**  
   Implement discrete DPO loss engine for policy alignment without GPU requirements.
3. **Milestone M8: Contextual Authority Ensemble Routing (Epics 16, 21)**  
   Implement dynamic routing and deterministic confidence bounds.
4. **Milestone M9: Continuous Governance Automation (Epics 22, 38)**  
   Automate Stage 12–18 adaptation loops and package contextual policies.
5. **Milestone M10: Phase 2 Final Integration & Close-Out**  
   Execute full regression suite, perform upstream Microsoft sync verification, and conduct Phase 2 Close (`PCD-Phase2`).

---

## Provenance & Completeness Self-Assessment

| Dimension | Verification Status | Notes |
|---|---|---|
| **Sequencing Compliance** | **100% Compliant** | Authored in Stage 3 alongside `Benefits-Management-Plan.md` v2.0 prior to Stage 4 Charter. |
| **Traceability** | **Complete** | All problem statements and solutions trace to `SPARK-001`–`003` and `Ideation-Document.md` v1.14. |
| **Decoupling (`LL-044`)** | **Enforced** | Framework comparisons and literature surveys housed in `docs/research/ideation/`. |
| **Architecture Integrity** | **Enforced** | `src/agent_learning_ext` isolation established to prevent upstream fork collisions. |
| **Economic Basis** | **Honest & Sourced** | Sourced engineering complexity and risk-avoidance proxies used in place of fabricated ROI. |

---

## Amendment Log

| Date | Author | Description |
|---|---|---|
| 2026-11-08 | Menno Drescher | v2.0 — Approved (`PCD-20261106-001`). |
| 2026-11-12 | Menno Drescher / Claude | **v2.1 — GC-P2-05 reconciliation:** Replaced all `agent-training-ext` references with the real package path `src/agent_learning_ext` (11 occurrences), and repointed `HYP-AL-018` to `HYP-AL-028` throughout (the DPO sample-efficiency hypothesis; `HYP-AL-018` keeps its distinct LinUCB meaning in `Ideation-Document.md` §2.2.3, per Stage 16 Phase 2 finding F1). Pending `approve-business-case` re-approval. |
| 2026-11-13 | Menno Drescher / Claude | **Header/frontmatter split fixed (PR #208 review, Amazon Q Developer):** The body header table still read Version 2.0 / Status Approved after the v2.1 bump above, contradicting the frontmatter's `version: "2.1"` / `status: "pending re-approval"` — fixed to match. Also: `HYP-AL-018`'s LinUCB meaning, cited above at `Ideation-Document.md` §2.2.3, now lives in `Hypothesis-Register.md` §3 (Stage 2's own document since 2026-11-12). |
