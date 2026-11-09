---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Initiating"
pmbok_process: "Pre-Project / Strategic Need Identification (Cognitive Feedback)"
lifecycle_stage: "Stage 1 (Intent)"
governance_policy: "approve-ideation"
artifact_id: "spark-capture"
version: "2.0"
phase: "Phase 2"
pmp_baseline: "PMP-BL-v1.0.1"
target_pmp_baseline: "PMP-BL-v1.1.0"
lineage_kernel_hash: "2402e037cb69f8e416b53caf237249cc1b6f868f1324c5e4083d67080006bf02"
inputs:
  - "Stage 18 Intent Refinement Proposal (IRP-20261106-001)"
  - "Phase 1 Close Decision (PCD-20261106-001)"
  - "Lessons-Learned-Register.md (LL-001 to LL-046)"
process: "Capture refined problem statement and strategic directives from Phase 1 cognitive feedback without premature solutioning"
outputs:
  - "Spark-Capture.md"
  - "Ideation-Document.md"
---

# Spark Capture — agent-learning

> **PMBOK 8 Process:** `Pre-Project / Strategic Need Identification` (Initiating / Cognitive Feedback Loop)  
> **Governance Policy:** `approve-ideation` | **Lifecycle Stage:** `Stage 1 (Intent)`  
> **Document Version:** `2.0` | **Phase:** `Phase 2` | **Anchor Baseline:** `PMP-BL-v1.0.1`  
> **Lineage Kernel Hash:** `2402e037cb69f8e416b53caf237249cc1b6f868f1324c5e4083d67080006bf02`  
> **Inputs:** [IRP-20261106-001](../governance/irp/IRP-20261106-001-Phase-1-Intent-Refinement-Proposal.md), [PCD-20261106-001](../governance/decisions/PCD-20261106-001-Phase-1-Close-Decision.md), [Lessons-Learned-Register.md](Lessons-Learned-Register.md)  
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
In production agentic loops (e.g. SocialEngage, ADPA, triage bots), agents make thousands of repeated discrete decisions daily. Fine-tuning takes hours to days and is unreplayable. A pure in-process policy layer with Thompson sampling and Softmax updates can learn from feedback in milliseconds with zero GPU overhead.

---

## Part 2: Phase 2 Refined Spark (Cognitive Feedback & Double-Loop Evolution)

**Date:** 2026-11-06 (Version 2.0)  
**Captured by:** Menno Drescher / Stage 18 Cognitive Feedback Gate (`IRP-20261106-001`)  
**Anchor Baseline:** `PMP-BL-v1.0.1` | **Target Baseline:** `PMP-BL-v1.1.0`  
**Cumulative Lineage Kernel:** `2402e037cb69f8e416b53caf237249cc1b6f868f1324c5e4083d67080006bf02`  
**Status:** Active Initiating Directive for Phase 2

### The Phase 2 Spark
With Phase 1 having proven warm-starting priors, confidence-interval bandits, and policy-based authority enforcement across 1,840 tests and 58 completed stories, autonomous agents can now decide reliably at build-time and run-time. However, agent learning remains largely decoupled from continuous governance feedback: critiques from human reviews, external CI telemetry, and cross-cycle lessons require manual translation into learning signals.

What if agent learning natively incorporates **Option B (Critique-to-Evidence + DPO Preference Optimization)** alongside **governance-aware cognitive feedback loops**? Keep the agent continuously aligned by converting PR review comments and execution critiques into weighted Bayesian evidence pairs, dynamically balancing exploration vs exploitation under homeostatic pivot limits.

### Approved Phase 2 Directives (from Stage 18 Intent Refinement)
1. **`SPARK-001` (Governance-Integrated Learning):** Embed policy-based decision gates and Bayesian authority thresholds directly into learning pipelines, enabling agents to self-triage when decisions exceed learned confidence.
2. **`SPARK-002` (Cognitive Feedback Loops):** Implement full double-loop cognitive learning with Bayes Factor hypothesis adjudication and low-pass outcome damping ($\beta = 0.75$) to eliminate strategic whiplash.
3. **`SPARK-003` (Adaptive Capacity Management):** Dynamically manage homeostatic adaptation capacity ($C_{adapt}$), ensuring strategic pivots remain bounded ($\le \lceil C_{adapt}/2 \rceil$).

### Immutable Lineage Invariants
- Governance-first development
- Evidence-driven decisions
- Cross-phase knowledge continuity
- High-integrity test coverage
- Deterministic automation

### What This Is Not Yet
This is pre-Ideation. Don't draft Hypotheses or Objectives here — that belongs in `Ideation-Document.md` and `Project-Charter.md`.
