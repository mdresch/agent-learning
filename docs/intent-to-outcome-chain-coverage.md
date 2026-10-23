# Intent-to-Outcome Chain & TaskPolicy Coverage — `agent-learning`

This document records the exact status and realization of the 18-stage **Intent-to-Outcome Chain** (`PROJECT-MANAGEMENT-ONTOLOGY.json`) within the `agent-learning` repository.

Unlike external client projects where `agent-learning` acts as an imported dependency, `agent-learning` is a **self-governing codebase**: its own architectural evolutions, requirements, and governance changes are decided, recorded, and verified by its own native `TaskPolicy` engine (`agent-learning-governance`).

---

## The 18-Stage Coverage Matrix

| # | Stage Name | Definition in Ontology | `agent-learning` Realization & TaskPolicy | Artifacts & Evidence in Repository |
|---|---|---|---|---|
| 1 | **Intent** | Foundational purpose and strategic driver | Defined in `docs/project-docs/Project-Charter.md` and `docs/project-docs/Ideation-Document.md` | Strategic motivation: Replace heavy LLM fine-tuning with native, in-process Bayesian reasoning and reinforcement bandits |
| 2 | **Objective** | Specific, measurable goal the project aims to achieve | Defined in `docs/project-docs/Business-Case.md` | Cost, latency, and determinism targets across `standard`, `critical`, and `stateless` tiers |
| 3 | **Hypothesis** | Falsifiable proposition or design assumption | ✅ `agent-learning-governance` / **`classify-hypothesis-status`** (FULL authority, 7 actions) | 11 real hypotheses evaluated (HYP-AL-001 through 011); durable policy state on disk |
| 4 | **Benefit** | Expected positive outcome that justifies investment | Defined in `docs/project-docs/Benefits-Management-Plan.md` | Auditability, zero storage bloat, zero unreplayable drift |
| 5 | **Capability** | Ability the organization gains from a deliverable | Deterministic crystallization via SIDPA lifecycle | `agent_learning.decision`, `agent_learning.comparison`, `agent_learning.governance` |
| 6 | **Project** | Temporary endeavor that produces a unique deliverable | `agent-learning` repository itself | Monorepo containing SDK, CLI, tests, and self-governing lineage |
| 7 | **Requirement** | Condition or capability a solution must meet | ✅ `agent-learning-governance` / **`approve-adr`**, **`approve-brd`**, **`approve-fdd`**, **`approve-user-stories`** (FULL authority) | **ADRs 001–007 Accepted**; BRDs 001–007 and FDDs 001–007 drafted and approved; Epics 1–7 with testable stories |
| 8 | **Work Package** | Deliverable-oriented grouping of activities | ✅ `agent-learning-governance` / **`validate-intent-foundation`** (FULL authority) | Gates entry into the work package; validates intent foundation before worktree provisioning |
| 9 | **Deliverable** | Output that must be accepted | Non-policy by design: managed via SIDPA `implement-story` loop and git worktree isolation | Pure modules: `decision.py`, `comparison.py`, `governance.py` |
| 10 | **Verification Evidence** | Verification or validation artifact (test results) | Pure contract tests under `tests/test_<module>.py`; fixtures under `tests/fixtures/<module>/` | 466 unit & contract tests passing; zero external mocks |
| 11 | **Audit Record** | Formal review verifying compliance or correctness | Durable `Episode` records in `LearningStore` + append-only `implementation-log.md` | Every decision, adjudication, and autonomous update emits an immutable `Episode` |
| 12 | **Actual Outcome** | Empirically realized result evaluated against Benefit | `DecisionResult` and `PairwiseComparison` deltas | Measured robust utility margins and progression classifications |
| 13 | **Observation** | Empirical data point or raw telemetry finding | PR review comments (e.g. Amazon Q), test failure tracebacks | Captured in task transcripts and PR reviews |
| 14 | **Insight** | Interpreted significance synthesized from Observations | Root cause diagnosis via `heal-contract-failure` | Identified "Green Defects" (Contract Incompleteness Failures) |
| 15 | **Lesson Learned** | Formalized, actionable knowledge | Component skills in `.claude/skills/<component>/SKILL.md` | Load-bearing constraints documented and enforced across `comparison`, `governance`, `heal-contract-failure` |
| 16 | **Governance Change** | Formal amendment of policies/baselines from validated lessons | ✅ `agent-learning-governance` / **`classify-diff-type`** (FULL) paired with **`escalate-diff-response`** (LOW) | **ADR-007 / Story 7.1 / PR #2**: 7-action diff classifier across 3 operational tiers paired with 3-action escalation bandit, gated by ADR-005 comparison and ADR-006 evidence transport |
| 17 | **Adaptation** | Empirical modification in behavior/workflow catalyzed by Governance Change | *Active frontier*: Updating agent skills, prompt templates, test harnesses, and workflow definitions | Formalized in Stage 17 roadmap |
| 18 | **Intent Refinement** | Feeds learnings back into strategic motivation, closing the cognition loop | *Active frontier*: Updating top-of-chain Charters and Ideation based on validated governance outcomes | Completes the cognitive loop |

---

## Active Policies in `agent-learning` Governance Lineage

| TaskPolicy | `agent_id` / `task_id` | Authority | Actions | Operational Role |
|---|---|---|---|---|
| **Hypothesis Classification** | `agent-learning-governance` / `classify-hypothesis-status` | `full` | 7 actions (`advance_to_testing`, `mark_validated`, `mark_invalidated`, `mark_inconclusive`, `remain_formulated_blocked`, `flag_for_human_review`, `no_new_evidence`) | Evaluates experimental empirical evidence against formulated hypotheses |
| **ADR Approval** | `agent-learning-governance` / `approve-adr` | `full` | `approve_adr`, `reject_adr`, `request_revision_before_decision` | Evaluates architectural soundness, alternatives, and consequence honesty |
| **BRD Approval** | `agent-learning-governance` / `approve-brd` | `full` | `approve_brd`, `reject_brd`, `request_revision_before_decision` | Evaluates business rules, stakeholder alignment, and boundary definitions |
| **FDD Approval** | `agent-learning-governance` / `approve-fdd` | `full` | `approve_fdd`, `reject_fdd`, `request_revision_before_decision` | Evaluates technical interface design, storage footprint, and invariant enforcement |
| **Story Approval** | `agent-learning-governance` / `approve-user-stories` | `full` | `approve_user_stories`, `reject_user_stories`, `request_revision_before_decision` | Evaluates testability of acceptance criteria and contract feasibility |
| **Foundation Validation** | `agent-learning-governance` / `validate-intent-foundation` | `full` | `accept_foundation_proceed`, `reject_needs_rework`, `flag_for_human_review` | Pre-implementation gate ensuring requirement artifacts are fully grounded |
| **Semantic Diff Classification** | `agent-learning-governance` / `classify-diff-type` | `full` | 7 actions across 3 tiers (`new_superseding_adr`, `amendment_log_entry`, `correction_note`, `clarification_section`, `provenance_note`, `pending_supersession_note`, `supersession_update`) | Evaluates candidate textual diffs against frozen baseline to determine structural form of change |
| **Diff Response Escalation** | `agent-learning-governance` / `escalate-diff-response` | `low` | 3 actions (`escalate_to_human`, `apply_with_notification`, `apply_automatically`) | Learns operational escalation policy from aggregate outcomes via REINFORCE, gated by ADR-005 progression comparison |

---

## Key Lifecycle Invariants Realized in Code

1. **Storage Boundary (ADR-002 Invariant #2):** Exactly 5 durable record types (`Episode`, `Reward`, `PolicySnapshot`, `PolicyMetrics`, `TrainingRun`). All metadata extensions leverage free-form dictionaries (`PolicySnapshot.metadata`, `Episode.metadata`). Zero schema expansion.
2. **Authority Decoupling (ADR-001 & ADR-007):** Semantic reasoning (`classify-diff-type`) must run under `full` authority via Bayesian `DecisionResolver`. Operational escalation (`escalate-diff-response`) runs under `low` authority via `SoftmaxPolicy`.
3. **Progression Gating (ADR-005):** Every applied change must be compared against its previous baseline via `compare_decision_results()`. Detected regressions immediately revert autonomous updates, halt execution, and trigger human escalation.
4. **Lightweight Evidence Transport (ADR-006):** Context from full-authority decisions is transported into low-authority decisions as an uninterpreted `audit_evidence` envelope.
5. **Permanent Lineage Freeze:** Status mutations affecting governance lineage (`new_superseding_adr`, `pending_supersession_note`, `supersession_update`) are permanently locked to human sign-off (`escalate_to_human`).
6. **Audit Integrity:** Zero silent updates. Every autonomous update emits an immutable `Episode` audit record, deferred until after progression verification confirms zero regression.
