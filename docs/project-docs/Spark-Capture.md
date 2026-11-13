---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Initiating"
pmbok_process: "Pre-Project / Strategic Need Identification (Cognitive Feedback)"
lifecycle_stage: "Stage 1 (Intent)"
governance_policy: "approve-ideation"
artifact_id: "spark-capture"
version: "3.0"
phase: "Phase 3"
pmp_baseline: "PMP-BL-v1.1.0"
target_pmp_baseline: "PMP-BL-v1.2.0"
lineage_kernel_hash: "579b62bfe11607b2287b16a99fdc36d14350fe864ffef1d60a8ca1712247c8b8"
inputs:
  - "Stage 18 Intent Refinement Proposal (IRP-20261111-001)"
  - "Phase 2 Close Decision (PCD-20261111-001)"
  - "Cumulative Lineage Kernel (CLK-20261111-001)"
  - "Lessons-Learned-Register.md (LL-001 to LL-067)"
process: "Capture refined problem statement and strategic directives from Phase 2 cognitive feedback without premature solutioning"
outputs:
  - "Spark-Capture.md"
  - "Ideation-Document.md"
---

# Spark Capture — agent-learning

> **PMBOK 8 Process:** `Pre-Project / Strategic Need Identification` (Initiating / Cognitive Feedback Loop)  
> **Governance Policy:** `approve-ideation` | **Lifecycle Stage:** `Stage 1 (Intent)`  
> **Document Version:** `3.0` | **Phase:** `Phase 3` | **Anchor Baseline:** `PMP-BL-v1.1.0` | **Target Baseline:** `PMP-BL-v1.2.0`  
> **Lineage Kernel Hash:** `579b62bfe11607b2287b16a99fdc36d14350fe864ffef1d60a8ca1712247c8b8`  
> **Inputs:** [IRP-20261111-001](../governance/irp/IRP-20261111-001-Phase-2-Intent-Refinement-Proposal.md), [PCD-20261111-001](../governance/decisions/PCD-20261111-001-Phase-2-Close-Decision.md), [CLK-20261111-001](../governance/lineage/CLK-20261111-001-Phase-2-Cumulative-Lineage-Kernel.md), [Lessons-Learned-Register.md](Lessons-Learned-Register.md)  
> **Outputs:** Spark-Capture.md (Source for Ideation-Document.md)

---

## Part 1: Phase 1 Origin Spark (Historical Inception)

**Date:** 2026-10-20 (Version 1.0)  
**Captured by:** Menno  
**Status:** Realized and Closed via Phase 1 Completion (PCD-20261106-001)

### The Spark
Autonomous AI agents are repeatedly bottlenecked by heavy, non-deterministic LLM calls for recurring operational choices. Teams attempt to solve this either through expensive GPU fine-tuning (slow, irreversible, opaque) or brittle prompt hacks that drift over time and cannot be audited. 

What if agents had an in-process, lightweight, Bayesian decision-and-learning layer? Keep the foundation model frozen, and give recurring decisions an explicit, interpretable TaskPolicy with mathematically proven confidence bounds and reinforcement bandits.

### Why Now
In production agentic loops (e.g. SIDPA-template-governed agent systems, triage bots), agents make thousands of repeated discrete decisions daily. Fine-tuning takes hours to days and is unreplayable. A pure in-process policy layer with Thompson sampling and Softmax updates can learn from feedback in milliseconds with zero GPU overhead.

---

## Part 2: Phase 2 Refined Spark (Cognitive Feedback & Double-Loop Evolution)

**Date:** 2026-11-06 (Version 2.0)  
**Captured by:** Menno Drescher / Stage 18 Cognitive Feedback Gate (`IRP-20261106-001`)  
**Anchor Baseline:** `PMP-BL-v1.0.1` | **Target Baseline:** `PMP-BL-v1.1.0`  
**Cumulative Lineage Kernel:** `2402e037cb69f8e416b53caf237249cc1b6f868f1324c5e4083d67080006bf02`  
**Status:** Realized and Closed via Phase 2 Completion (`PCD-20261111-001`, episode `fa8603c7`)

### The Phase 2 Spark
With Phase 1 having proven warm-starting priors, confidence-interval bandits, and policy-based authority enforcement across 1,840 tests and 58 completed stories, autonomous agents can now decide reliably at build-time and run-time. However, agent learning remains largely decoupled from continuous governance feedback: critiques from human reviews, external CI telemetry, and cross-cycle lessons require manual translation into learning signals.

What if agent learning natively incorporates **Option B (Critique-to-Evidence + DPO Preference Optimization)** alongside **governance-aware cognitive feedback loops**? Keep the agent continuously aligned by converting PR review comments and execution critiques into weighted Bayesian evidence pairs, dynamically balancing exploration vs exploitation under homeostatic pivot limits.

### Approved Phase 2 Directives (from Stage 18 Intent Refinement)
1. **`SPARK-001` (Governance-Integrated Learning):** Embed policy-based decision gates and Bayesian authority thresholds directly into learning pipelines, enabling agents to self-triage when decisions exceed learned confidence.
2. **`SPARK-002` (Cognitive Feedback Loops):** Implement full double-loop cognitive learning with Bayes Factor hypothesis adjudication and low-pass outcome damping ($\beta = 0.75$) to eliminate strategic whiplash.
3. **`SPARK-003` (Adaptive Capacity Management):** Dynamically manage homeostatic adaptation capacity ($C_{adapt}$), ensuring strategic pivots remain bounded ($\le \lceil C_{adapt}/2 \rceil$).

---

## Part 3: Phase 3 Refined Spark (Stage 18 Seeding from `IRP-20261111-001`)

**Date:** 2026-11-11 (Version 3.0)  
**Captured by:** Menno Drescher / Stage 18 Cognitive Feedback Gate (`IRP-20261111-001`, `PCD-20261111-001` episode `fa8603c7`)  
**Anchor Baseline:** `PMP-BL-v1.1.0` | **Target Baseline:** `PMP-BL-v1.2.0` (created in Stage 18 as one of its final steps (Sponsor, 2026-11-11))  
**Cumulative Lineage Kernel:** `579b62bfe11607b2287b16a99fdc36d14350fe864ffef1d60a8ca1712247c8b8` (`CLK-20261111-001`, Generation 2)  
**Status:** Seeded Initiating Directive for Phase 3 (awaiting prospective `approve-ideation` at Stage 1)

### The Phase 3 Trigger & Realized Context
Phase 2 delivered all six baseline epics (Epics 14, 16, 18, 21, 22, 38) plus Epic 17 across 2,723 passing tests (`0` failures), operationalizing critique-to-evidence ingestion, discrete DPO preference optimization, deterministic UCB/epsilon-greedy baselines, scored-search decision compilation, packaged contextual learning, and contextual authority ensemble routing under `src/agent_learning_ext/`.

At the same time, Phase 2 execution and the Stage 15–17 close-out surfaced concrete operational and epistemic follow-ups recorded in `IRP-20261111-001` section 5:
1. **Unresolved Empirical Hypotheses:** 19 of the 27 registered hypotheses (`2 Testing`, `17 Formulated`) remain non-terminal because the empirical datasets or external stores they require (`LL-065`) lie outside the Phase 2 build scope; by Sponsor decision (`PCD-20261111-001`), these 19 carry forward unchanged into Phase 3, alongside registering `HYP-AL-028` (DPO sample efficiency).
2. **Deferred Baseline & Governance Adaptations:** Four Stage 17 adaptation items (`GC-P2-04` Tier 2 skill backfill, `GC-P2-05` hand-authored document reconciliation for `HYP-AL-028` and `src/agent_learning_ext/`, `GC-P2-06` and `GC-P2-07` PMP and subsidiary plan regeneration at Stage 7), skill-check enhancements (`IMP-050`, `IMP-031` from `CR-20261111-001`), PR gate parser/waiver fixes (`IMP-065`, `066`, `067`), and deferred ADR alignments (`F3` on `ADR-022`, `F4` on `ADR-016`) were explicitly moved to Phase 3 by the Sponsor so Phase 2 could close cleanly once.
3. **Carry-Over Epics & Multi-Agent WBS Readiness:** Epics `23`, `24`, and `39` plus the Phase Next improvements (`IMP-002`, `006`, `019`, `025`, `027`, `028`, `039`, `068`) carry forward, together with the preparations required before multiple agents can autonomously claim and execute sequenced WBS work packages (`CR-20261111-001` sections 4d–4f: active `Story-Execution-Register.md` hook-up, a `Task-Ownership-Register` with bid/lease semantics, per-task worktree locks, and human-equivalent vs shadow agentic effort tracking).

### Seeded Phase 3 Directives (`IRP-20261111-001` §5)
1. **`SPARK-P3-001` (Baseline Reconciliation & Deferred Stage 17 Adaptations):** Apply the approved Tier 2 text backfill (`GC-P2-04`, `IMP-050`, `IMP-031` per `CR-20261111-001`), reconcile hand-authored documents (`GC-P2-05`: `HYP-AL-028` and `src/agent_learning_ext/`), resolve deferred ADR findings (`F3` / `ADR-022`, `F4` / `ADR-016`), and regenerate the PMP and 9 subsidiary plans under `PMP-BL-v1.2.0` at Stage 7 (`GC-P2-06`, `GC-P2-07`).
2. **`SPARK-P3-002` (PR Gate Hardening & Verification Fidelity):** Implement `IMP-065` (resolved-finding handling in `pr_gate.py`), `IMP-066` (Q review heading coverage), `IMP-067` (malformed bullet reporting), and settle the `complete_story.py done` `DEFAULT_IGNORES` decision and `IMP-068` schedule actuals tracking.
3. **`SPARK-P3-003` (Carry-Over Epics & Hypothesis Empirical Resolution):** Execute Phase 3 carry-over scope (Epics `23`, `24`, `39` and rolled-in Phase Next improvements `IMP-002`, `006`, `019`, `025`, `027`, `028`, `039`) and advance the 19 carried-over hypotheses (`HYP-AL-004`, `005`, `007`, `010`–`025`) plus `HYP-AL-028` where real episode or cross-system evidence is available.
4. **`SPARK-P3-004` (Multi-Agent WBS Execution & Register Instrumentation):** Operationalize the `Story-Execution-Register.md` loop (`CR-20261111-001` §4d) and design the `Task-Ownership-Register` and seven pre-WBS preparations (`CR-20261111-001` §4e–4f) before multi-agent swarms pick up scheduled WBS work packages.

### Immutable Lineage Invariants
- Governance-first development
- Evidence-driven decisions
- Cross-phase knowledge continuity
- High-integrity test coverage
- Deterministic automation

### What This Is Not Yet
This is pre-Ideation. Detailed hypothesis tables and scope boundaries live in `Ideation-Document.md`, `Business-Case.md`, and `Project-Charter.md`.
