---
artifact_id: "benefits-management-plan"
version: "2.1"
date: "2026-11-12"
phase: "Phase 2"
status: "pending re-approval (GC-P2-05 reconciliation)"
pmp_baseline: "PMP-BL-v1.0.1"
target_pmp_baseline: "PMP-BL-v1.1.0"
governance_reference: "PCD-20261106-001"
---

# Benefits Management Plan — agent-learning Phase 2

**Version:** 2.0  
**Date:** 2026-11-08  
**Status:** **Approved** (Menno, 2026-11-08; adjudicated via `approve-benefits`, episode `8cfdbf52-92bc-445f-aa0d-db729ca8667f`) — Phase 1 Target Benefits Realized & Closed; Phase 2 Target Benefits Active  
**PMP Baseline:** Governed under `PMP-BL-v1.0.1` (Patch Baseline); Targeting `PMP-BL-v1.1.0` (Phase 2 Minor Increment Baseline)  
**Historical Baseline Archive:** Frozen Phase 1 snapshot preserved in [`docs/project-docs/history/PMP-BL-v1.0.0/Benefits-Management-Plan.md`](file:///d:/Source/repos/agent-learning/docs/project-docs/history/PMP-BL-v1.0.0/Benefits-Management-Plan.md).  
**Source Documents:** `docs/project-docs/Spark-Capture.md` v2.0, `docs/project-docs/Ideation-Document.md` v1.14, `docs/project-docs/Business-Case.md` v2.0, `docs/project-docs/Project-Charter.md` v2.0, and `PCD-20261106-001`.

---

## Executive Summary & Sequencing Integrity

In accordance with **PMBOK 8 Figure 2-3 ("Initiate Project or Phase Inputs")**, the Benefits Management Plan is an essential input to phase initiation alongside the Business Case. In Phase 1, this document was created as a retrofit after the Charter. For Phase 2, this governance flaw has been formally resolved: **this Benefits Management Plan v2.0 is authored and reviewed in Stage 3, prior to Stage 4 Project Charter authorization and Stage 6/7 PMP baselining (`PMP-BL-v1.1.0`)**.

Phase 1 successfully validated and realized its core benefits:
- **HYP-AL-008 (Warm-Starting):** Validated in Epic 15 (`WarmStartSoftmaxPolicy`), reducing cold-start episode requirements across structurally similar policies.
- **HYP-AL-009 (Confidence-Interval Bandits):** Validated in Epic 19 (`WilsonScoreUCBPolicy`), breaking the entropy ceiling on sparse positive-only training data.

Phase 2 formalizes the benefits stemming from the approved Phase 2 Sparks (`SPARK-001`, `SPARK-002`, `SPARK-003`) and Stage 2 Ideation (`HYP-AL-005`, `HYP-AL-028`, `HYP-AL-025`, `HYP-AL-026`, `HYP-AL-027`).

---

## 1. Target Benefits (Phase 2)

### 1a. Confirmed / Evidenced Phase 2 Target Benefits

The target benefits for Phase 2 trace directly to the approved Phase 2 Sparks and active research hypotheses:

| Benefit ID | Benefit Statement | Primary Beneficiary | Source / Spark | Linked Hypothesis / Epic |
|---|---|---|---|---|
| **BEN-P2-001** | **Deterministic Ingestion of Review Critique:** Eliminates the loss of qualitative reviewer feedback by deterministically converting tagged review findings into Bayesian evidence points, shifting pooled support exactly by the reviewer delta without guessing or parameter drift. | Human reviewers, PR adjudicators, and agent maintainers | `SPARK-001` (Feedback Loop Grounding), ADR-014 | `HYP-AL-005`, Epic 14 |
| **BEN-P2-002** | **Lightweight CPU-Only Preference Alignment (DPO):** Enables direct preference optimization over discrete task policies from paired comparison data without requiring heavy GPU fine-tuning or external reward models. | SDK adopters and autonomous agent developers | `SPARK-002` (Autonomy Progression), ADR-018 | `HYP-AL-028`, Epic 18 |
| **BEN-P2-003** | **Continuous SIDPA Governance-Integrated Automation:** Automates the synthesis of Stages 12–18 adaptation plans from live learning episodes and triage telemetry, eliminating manual documentation toil while ensuring 0% status drift. | Project manager, compliance auditors, and system architects | `SPARK-003` (Continuous Governance-Integrated Learning) | `HYP-AL-025`, `sidpa-template` |
| **BEN-P2-004** | **Upstream Fork Collision Immunity:** Decouples custom learning extensions into `src/agent_learning_ext`, ensuring the core `microsoft/agent-learning` repository can be synchronized with upstream commits without merge collisions. | Repository maintainers and downstream SDK adopters | Architecture Directive (Menno, 2026-11-07) | `HYP-AL-026`, `HYP-AL-027` |
| **BEN-P2-005** | **Multi-Armed Contextual Authority Routing:** Dynamically ensembles `low` and `full` authority decision models based on context features and statistical uncertainty bounds, maximizing autonomy while bounding catastrophic errors. | Production agent consumers requiring strict SLA guarantees | Ideation §2.1 Methodology #17, ADR-016 | `HYP-AL-016`, Epic 16, Epic 21 |

---

## 2. Strategic Alignment

Phase 2 benefits directly close the operational gaps identified during Phase 1 close-out (Stages 12–18):
1. **Closing the Critique Discarding Bottleneck:** During Phase 1, 32 Amazon Q review findings were logged in `implementation-log.md` but could only be consumed through manual code edits. `BEN-P2-001` directly grounds this critique into the Bayesian evidence frame.
2. **Closing the Manual Governance Toil:** Stages 12–18 in Phase 1 required extensive manual rollups and document editing. `BEN-P2-003` operationalizes `sidpa-template` integration to automate this continuous improvement loop.
3. **Protecting Open-Source Upstream Continuity:** As `agent-learning` diverges from Microsoft's original upstream, `BEN-P2-004` isolates customizations into `src/agent_learning_ext`, preserving seamless pull/merge workflows.

---

## 3. Benefit Owners

Per PMBOK 8 §2.4.6/2.4.7:
- **Primary Benefit Owner:** **Menno Drescher** (Project Sponsor, Maintainer, and Project Manager).
- **Operational Stewards:**
  - *Governance & Compliance Benefits (`BEN-P2-003`, `BEN-P2-004`):* Menno Drescher.
  - *Algorithmic & Learning Benefits (`BEN-P2-001`, `BEN-P2-002`, `BEN-P2-005`):* Menno Drescher.
- **Ownership Horizon:** Ownership begins at Stage 3 approval and extends through Phase 2 execution (Milestones M6–M10) and post-phase operational deployment.

---

## 4. Timeframe for Realization

The benefits are mapped to the milestone schedule established in `Project-Charter.md` v2.0:

| Benefit ID | Milestone Target | Verification Checkpoint | Measurement Mechanism |
|---|---|---|---|
| **BEN-P2-001** | Milestone M6 | Stage 9 execution of Epic 14 | Replay of 32 real Amazon Q review triage records through `critique_evidence.py`. |
| **BEN-P2-002** | Milestone M7 | Stage 9 execution of Epic 18 | DPO loss convergence on pairwise review decisions vs. REINFORCE baseline. |
| **BEN-P2-005** | Milestone M8 | Stage 9 execution of Epic 16/21 | Ensemble regret bounds on contextual routing decisions. |
| **BEN-P2-003** | Milestone M9 | Stage 9 execution of Epic 22/38 | Execution of automated Stage 12–18 adaptation cycle with 0 drift rows. |
| **BEN-P2-004** | Milestone M10 | Phase 2 Close (`PCD-Phase2`) | Clean git rebase/fetch against upstream `microsoft/agent-learning` without conflicts. |

---

## 5. Metrics for Measuring Realization

Metrics are derived strictly from the falsification criteria defined in `Ideation-Document.md` v1.14 and `docs/research/ideation/hypothesis-validation-and-governance-integration.md`:

1. **Critique Ingestion Exactness (`BEN-P2-001` / `HYP-AL-005`):**
   - *Metric:* Measured pooled support delta $|\Delta s_{\text{pooled}} - \text{clip}(s_{\text{before}} + \delta)| \le 10^{-9}$ measured via `DecisionResolver.resolve()`.
   - *Falsification:* Any negative defect finding raising pooled support, or any positive confirmation finding lowering pooled support.
2. **DPO Sample Efficiency (`BEN-P2-002` / `HYP-AL-028`):**
   - *Metric:* Number of pairwise preference samples required to reach policy cross-entropy loss $< 0.10$ relative to REINFORCE episode count.
   - *Target:* At least 30% reduction in required feedback interactions.
3. **Governance Automation Latency & Drift (`BEN-P2-003` / `HYP-AL-025`):**
   - *Metric:* End-to-end execution time of `orchestrate_pmbok.py` and `phase_rollup.py --check` exiting with 0 drift rows across all 18 lifecycle stages.
4. **Upstream Fork Compatibility (`BEN-P2-004` / `HYP-AL-026`):**
   - *Metric:* 0 lines of custom logic in `src/agent_learning` outside baseline interfaces; 100% of extension logic residing in `src/agent_learning_ext`.

---

## 6. Assumptions and Risks to Benefit Realization

- **Assumption 1 (Reviewer Tag Compliance):** Reviewers (human or automated Q) provide findings adhering to the Tag Grammar (`[finding: ...] [criterion: ...] +/-delta: ...`).  
  *Risk:* Free-form text cannot be parsed without manual tagging.  
  *Mitigation:* Predefined delta rubric (`rubric_delta`) allowing claim-type selection (`[claim: ...] [verified: ...]`) when numbers are omitted.
- **Assumption 2 (Extension Packaging Simplicity):** `src/agent_learning_ext` can cleanly import `agent_learning.decision` primitives without circular dependencies.  
  *Mitigation:* Frozen dataclasses and pure functional boundaries enforced in `agent_learning.decision`.
- **Assumption 3 (Sponsor Capacity):** Single-maintainer model remains viable with automated governance assistance.  
  *Mitigation:* GC-001 through GC-004 script automation removes manual status tracking toil.

---

## 7. Potential Disbenefits and Mitigation

| Disbenefit ID | Potential Disbenefit | Impact | Monitoring & Mitigation Method |
|---|---|---|---|
| **DIS-P2-001** | **Subjective Reviewer Bias:** An aggressive reviewer could artificially drive down pooled support using extreme negative deltas. | Policy becomes over-cautious, suppressing valid actions. | Clamping mechanism (`TARGET_EPSILON = 1e-6`) and `kappa` doubt adjustment bounds ($[0.1, 0.5]$); reviewer reliability tracking via `review_triage.reliability`. |
| **DIS-P2-002** | **Secondary Package Indirection:** Introducing `src/agent_learning_ext` adds PYTHONPATH and import resolution overhead. | Potential developer friction during local test runs. | Explicit package configuration in `pyproject.toml` and standardized CLI invocation scripts. |
| **DIS-P2-003** | **Governance Overhead on Small Stories:** Running full PMBOK 18-stage checks on minor refactorings. | Slower cycle time on trivial tasks. | Foundation Pack tailoring rules (ADR-034 / sidpa-template rules 30–33) allow lightweight micro-iterations. |

---

## 8. Benefits Tracking and Review Approach

In alignment with **PMBOK 8 §2.1.6.7 ("Monitor and Control Project Performance")**:
- **Continuous Monitoring:** Each implemented story verifies its specific contract tests against the benefit metrics in Step 6 of `implement-story`.
- **Milestone Gates:** Formal benefits realization reviews occur at:
  - **Milestone M6 Review (Stage 9 Close of Epic 14):** Verification of `BEN-P2-001`.
  - **Milestone M8 Review (Stage 9 Close of Epic 16):** Verification of `BEN-P2-002` and `BEN-P2-005`.
  - **Milestone M10 Phase 2 Close-Out:** Comprehensive benefits audit, feeding Stage 12 (Actual Outcomes) of the Phase 2 lifecycle.

---

## Provenance & Completeness Self-Assessment

| Dimension | Verification Status | Notes |
|---|---|---|
| **Lifecycle Sequencing** | **Compliant** | Authored in Stage 3 as a forward-looking input to Stage 4 Charter and Stage 6/7 Baselines. |
| **Traceability** | **100% Traced** | Every benefit traces to `SPARK-001`–`003`, `Ideation-Document.md` v1.14, and active research hypotheses. |
| **Beneficiaries** | **Explicitly Named** | Grounded in real human roles (Reviewer, Maintainer, Auditor, Adopter); no abstract "agent" entities. |
| **Disbenefits** | **Analyzed & Mitigated** | Reviewer bias, packaging indirection, and governance overhead evaluated with concrete mitigations. |
| **Metrics** | **Falsifiable & Mathematical** | Strict reliance on IEEE 754 precision checks ($10^{-9}$), sample counts, and drift-free validation. |

---

## Amendment Log

| Date | Author | Description |
|---|---|---|
| 2026-11-08 | Menno Drescher | v2.0 — Approved via `approve-benefits`, episode `8cfdbf52-92bc-445f-aa0d-db729ca8667f` (`PCD-20261106-001`). |
| 2026-11-12 | Menno Drescher / Claude | **v2.1 — GC-P2-05 reconciliation:** Replaced all `agent-training-ext` references with the real package path `src/agent_learning_ext` (5 occurrences), and repointed `HYP-AL-018` to `HYP-AL-028` throughout (the DPO sample-efficiency hypothesis; `HYP-AL-018` keeps its distinct LinUCB meaning in `Ideation-Document.md` §2.2.3, per Stage 16 Phase 2 finding F1). Pending `approve-benefits` re-approval. |
