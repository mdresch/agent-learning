# BRD-009: Intent Refinement and Cognitive Feedback Loop

**Source ADR:** [ADR-009](../../adr/ADR-009-intent-refinement-and-cognitive-feedback-loop.md) — Accepted (2026-10-25)  
**Governing Baseline:** `PMP-BL-v1.0.0`  
**Status:** Accepted — business requirements derived from an Accepted ADR  
**Stakeholders:** Menno (Sponsor/PM/Maintainer)  

---

## 1. Business Need

On the 18-stage Intent-to-Outcome Chain (`PROJECT-MANAGEMENT-ONTOLOGY.json`), ADR-008 formalized **Stage 17 (Adaptation)** to close the single-loop operational feedback cycle: tailoring subsidiary management plans to maintain adherence to existing baselines. However, a major architectural gap remained unaddressed at the macro-lifecycle level:

When real-world production outcomes (Stage 12) diverge significantly from foundational business expectations (Stage 4), or when systematic lessons learned (Stage 15) prove foundational hypotheses flawed, **operational adaptation within existing project baselines is insufficient**. The organization must engage in **double-loop cognitive learning** (Argyris & Schön, Ashby, Stafford Beer): questioning whether the governing goals, business benefits, and core hypotheses themselves must be reformulated.

In enterprise project management (PMBOK 8 Process 4.7 *Close Project or Phase*), phase completion cannot terminate in passive documentation or unverified meeting notes. It must execute a rigorous cybernetic feedback loop that converts realized empirical evidence into structured catalysts for Phase $N+1$ Initiating artifacts (`Spark-Capture.md` and `Ideation-Document.md`).

This BRD establishes the formal business requirements for **Stage 18 (Intent Refinement)**:
1. **The Machine-Readable Intent Refinement Artifact (`Intent-Refinement-Proposal.md`):** Governed by a strict schema recording the **Outcome Delta Evaluation Matrix**, empirical root causes, hypothesis terminal resolutions, and next-phase Spark directives.
2. **Dedicated Full-Authority Decision Gate (`approve-intent-refinement`):** A Bayesian multi-criteria evaluation gate in `agent-learning-governance` with mandatory human sign-off (`requires_human_approval: true`).
3. **Hypothesis Terminality & Bounded Recurrence ($d_{\max}=2$):** Direct coupling of empirical outcomes into `classify-hypothesis-status` (Stage 3), graduating validated hypotheses into architectural invariants, archiving refuted hypotheses with negative learning penalties, and strictly limiting refinement depth to eliminate defensive moral hazard.
4. **Cybernetic Damping & Hereditary Lineage Kernel:** Low-pass filtering ($\beta \in [0.6, 0.85]$) to eliminate strategic whiplash, S3–S4 homeostatic balance (Beer VSM), and cumulative lineage inheritance across multi-phase handoffs.
5. **Phase Close Readiness & Decommissioning:** Formal preconditions before Stage 18 entry and administrative cleanup of ephemeral resources.

---

## 2. Business Rules (BRU)

- **BRU-009-01 (Single-Loop vs. Double-Loop Separation):** Stage 17 (`Adaptation-Plan.md`) must strictly remain within existing baselines (tailoring subsidiary plans), while Stage 18 (`Intent-Refinement-Proposal.md`) alone has authority to propose amendments to Stage 1 Intent, Stage 3 Hypotheses, and Stage 4 Business Benefits.
- **BRU-009-02 (Full Authority for Refinement Gate):** The `approve-intent-refinement` gate must operate under `DecisionAuthority.FULL` using Bayesian multi-criteria decision reasoning, with `requires_human_approval: true` permanently locked.
- **BRU-009-03 (Hypothesis Terminality Invariant):** No project phase may be formally closed with lingering unadjudicated hypotheses. Every active hypothesis from Stage 3 must resolve to `VALIDATED`, `REFUTED`, or `REFINED`.
- **BRU-009-04 (Bayes Factor Hypothesis Adjudication):** Hypothesis resolutions must be grounded in empirical Bayes factors:
  - $BF_{10} \ge 10 \implies \text{VALIDATED}$ (graduated into immutable architectural invariants).
  - $BF_{10} \le 0.1 \implies \text{REFUTED}$ (archived with negative reinforcement penalty).
- **BRU-009-05 (Maximum Recurrence Depth $d_{\max}=2$):** A hypothesis may only be marked `REFINED` for a maximum of 2 generational cycles ($H \to H.1 \to H.1.1$). On the 3rd cycle ($d=2$), `REFINED` is prohibited: it must collapse to `VALIDATED` if $BF_{10} \ge 10$, or default to `REFUTED` if $BF_{10} < 10$.
- **BRU-009-06 (Outcome Delta Horizon Stratification):** The Outcome Delta Matrix must explicitly stratify metrics between **Immediate** (measured at deliverable acceptance) and **Lagging** (measured after production operationalization) horizons. Lagging metrics with insufficient operational runtime must be recorded as `PENDING_OPERATIONAL_EVALUATION` and bound to an automated post-close audit trigger.
- **BRU-009-07 (Strategic Whiplash Low-Pass Filtering):** Intent refinements must apply exponential moving average smoothing $\mathbf{\Theta}_{N+1} = \beta \mathbf{\Theta}_{N} + (1 - \beta) \nabla \mathcal{L}$ with $\beta \in [0.6, 0.85]$ and bias-corrected warmup ($1 - \beta^N$) for initial generations $N < 3$.
- **BRU-009-08 (System 3–System 4 Homeostatic Balance):** The number of proposed strategic pivots in an Intent Refinement Proposal must be rate-limited against operational adaptation capacity ($\text{Pivots}_{\max} \le \lceil C_{\text{adapt}} / 2 \rceil$).
- **BRU-009-09 (Administrative Decommissioning & Premature Termination):** Approval of an `Intent-Refinement-Proposal.md` under `disposition_type: "project_termination"` must immediately trigger atomic revocation of access tokens, pruning of ephemeral worktrees, and release of sandboxed runners. Under `disposition_type: "phase_handoff"`, it must generate validated catalysts for Phase $N+1$.
- **BRU-009-10 (Cumulative Lineage Kernel):** Every Intent Refinement Proposal must incorporate an immutable `CumulativeLineageKernel` preserving `root_spark_id`, `parent_refinement_id`, `immutable_core_invariants`, and `accumulated_knowledge_hash` to eliminate multi-generational memory decay.
- **BRU-009-11 (Zero Storage Expansion):** All intent refinement proposal payloads, evaluations, and decision episodes must be persisted using ADR-002's five record types as metadata-enriched `Episode` instances, introducing zero new database entities or containers.

---

## 3. Stakeholder Success Metrics

| Metric | Baseline | Target | Verification Method |
|---|---|---|---|
| Double-Loop Feedback Closure | 0% (terminated at Stage 16/17) | 100% of closed phases generate structured Phase $N+1$ Spark directives | Automated verification in `orchestrate_pmbok.py --mode seed-next` |
| Zombie Hypothesis Elimination | Unbounded hypothesis survival | 100% terminal resolution ($d_{\max}=2$ collapse) | Automated validation via `IntentRefinementProposalPayload` |
| Strategic Damping Factor ($\beta$) | N/A (step-function swings) | $\beta \in [0.6, 0.85]$ enforced across rolling outcome deltas | Mathematical check in decision assessment |
| Governance Sign-Off Enforcement | Manual discipline | 0 autonomous bypasses (`requires_human_approval: true`) | TaskPolicy schema lock in `approve-intent-refinement` |
| Epistemic Lineage Retention | Lossy cross-phase handoff | 100% cryptographic trace of root spark and core invariants | Cumulative lineage kernel hash verification |
| Storage Boundary Compliance | 5 record types | 0 new record types or tables added to `LearningStore` | Static audit against `LearningStore` base interface |

---

## 4. Out of Scope

- Autonomous self-refinement of strategic intent without human sign-off (violates ADR-001/008/009 invariants).
- Conflating tactical sprint bug fixes with double-loop strategic intent reformulation.
- Adding relational tables or bespoke document databases to store refinement proposals.
- Real-time modification of active Phase $N$ sprint execution baselines (governed by Stage 17 Adaptation).
