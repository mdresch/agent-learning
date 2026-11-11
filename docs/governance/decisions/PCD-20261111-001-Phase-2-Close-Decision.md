---
artifact_type: "phase_close_decision"
decision_id: "PCD-20261111-001"
phase: "Phase 2"
phase_name: "Advanced Agent Learning with Governance-Integrated Feedback Loops"
version: "1.0"
date: "2026-11-11"
decision: "APPROVE"
authority: "FULL"
governance_policy: "approve-intent-refinement"
related_proposal: "IRP-20261111-001"
---

# Phase Close Decision: PCD-20261111-001

> **Approved** by the Project Sponsor on 2026-11-11. The charter's milestone name for it is `PCD-Phase2` (M10). Seeding of Phase 3 is not yet run.

## Decision

**Phase:** Phase 2, Advanced Agent Learning with Governance-Integrated Feedback Loops (`PMP-BL-v1.1.0`)

**Decision:** APPROVE, by Menno Drescher (Project Sponsor), 2026-11-11, via `approve-intent-refinement`, episode `fa8603c7` (`scripts/approve.py`; ranking approve 0.789, request revision 0.226). **Phase 3 baseline id: `PMP-BL-v1.2.0`**, a minor increment per ADR-008 section 4.6.1, to be formalized with `approve-pmp` at the Stage 7 Project artifact approvals; `PMP-BL-v1.1.0` stays the baseline until then.

**Date:** 2026-11-11

## Rationale (for the Sponsor to confirm or change)

Phase 2 delivered its technical scope: every story of the six baseline epics is implemented and the whole suite passes (2723 passed, 2 skipped). The audit (Stage 11) was approved twice and the Stage 16 and 17 changes are approved and applied, except the items the Sponsor moved to Phase 3. Two charter success criteria are not met: of the five hypotheses named in criterion 2 (HYP-AL-005, 018, 025, 026, 027), three are not resolved with empirical evidence (005 Testing, 018 and 025 Formulated; 026 and 027 were Validated at the Phase 1 close), and this decision is itself criterion 5. The IRP proposes carrying the 19 non-terminal hypotheses to Phase 3 rather than collapsing them to refuted.

## Evidence

- [x] Readiness audit run: no blocker found (IRP section 1)
- [x] Hypotheses: 8 are Validated; the 19 non-terminal are **carried over to Phase 3** unchanged (Sponsor decision, 2026-11-11), an exception to the methodology's terminal-state rule
- [x] Low-pass damping: recorded **not applicable** (Sponsor, 2026-11-11)
- [x] Strategic pivot capacity: recorded **not applicable** (Sponsor, 2026-11-11)
- [x] Intent Refinement Proposal approved: yes, episode `fa8603c7`

## Hypotheses at close (27)

Source: `Ideation-Document.md` section 2.2, status column as recorded. 8 Validated (001, 002, 003, 006, 008, 009, 026, 027), 2 Testing (004, 005), 17 Formulated (007, 010 to 025). HYP-AL-028 is not registered yet (GC-P2-05, deferred to Phase 3). The IRP (section 2) proposes carrying the 19 non-validated forward unchanged; the Sponsor decides.

| HYP-AL | Type | Status | Claim (shortened) |
|---|---|---|---|
| 001 | Value | Validated | A 2–3 action softmax bandit with REINFORCE-with-baseline can earn autonomy |
| 002 | Technical | Validated | Positive-only history cannot earn autonomy for a low-authority bandit |
| 003 | Feasibility | Validated | Full-authority resolution can decide a per-instance case on the first attempt |
| 004 | Adoption | Testing | The packaged softmax/REINFORCE path suffices for most real decisions |
| 005 | Value | Testing (active for Phase 2) | Experience-reflection-retry learning converges faster |
| 006 | Feasibility | Validated | Classifying only what changed against a frozen baseline works |
| 007 | Value | Formulated | A diff-type category's escalation can be learned by low-authority REINFORCE |
| 008 | Feasibility | Validated | Warm-starting from a similar converged policy cuts episodes needed |
| 009 | Technical | Validated | Thompson/UCB crosses the autonomy gate that defeated REINFORCE |
| 010 | Feasibility | Formulated | Offline scored-search can find `DecisionResolver` weights |
| 011 | Adoption | Formulated | A hosted governance-as-a-service layer has paying demand |
| 012 | Technical | Formulated | A confidence-interval bandit can replace ADPA's hand-set constants |
| 013 | Feasibility | Formulated | A policy trained on ADPA's audit-ledger verdicts is feasible |
| 014 | Technical | Formulated | The same approach replaces a third system's hand-set constants |
| 015 | Feasibility | Formulated | Adaptive pairwise comparison (dueling bandit) is feasible |
| 016 | Technical | Formulated | A learned policy can replace SIDPA's static confidence-factor bands |
| 017 | Feasibility | Formulated | Capability-filtered model selection by a low-authority policy |
| 018 | Technical | Formulated | A linear contextual bandit reaches the gate in fewer episodes |
| 019 | Technical | Formulated | A conformal abstention rule gives a calibrated "defer to a human" |
| 020 | Technical | Formulated | Off-policy evaluation ranks policies as running them would |
| 021 | Technical | Formulated | A discounted or windowed update recovers faster after a shift |
| 022 | Feasibility | Formulated | Hard action masking enforces ADR-011's floors and caps |
| 023 | Value | Formulated | Active-learning triage catches more wrong autonomous decisions |
| 024 | Feasibility | Formulated | Outcome-conditioned exemplar selection, recorded in episode metadata |
| 025 | Technical | Formulated | Governance-integrated learning (SPARK-001) |
| 026 | Technical | Validated (Phase 1 Close) | Cognitive feedback damping (SPARK-002) |
| 027 | Feasibility | Validated (Phase 1 Close) | Adaptive capacity management (SPARK-003) |

## Next steps if approved

1. Done 2026-11-11: approval episode `fa8603c7` registered; Phase 3 baseline id `PMP-BL-v1.2.0`.
2. Seed the Phase 3 Spark and Ideation Document from IRP section 5; HYP-AL-028 and the hand-authored document edits (GC-P2-05) come with it.
3. Close Phase 2 in the Project Status Register.
