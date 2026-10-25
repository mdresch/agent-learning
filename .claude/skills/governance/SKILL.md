---
name: governance
description: Automated governance change pipeline (Stage 16) and the ADR-010 Breakout & Recap Session (Lessons Learned Register) for agent_learning.
---

# Component: governance (`agent_learning.governance` & `agent_learning.lessons_learned`)

**Governing:** ADR-007, ADR-010, BRD-007, BRD-010, FDD-007, FDD-010, Stories 7.1 and 10.1.
**Contracts:** `tests/test_governance.py`, `tests/test_lessons_learned.py`.

## 1. Load-bearing constraints (Stage 16 Governance Change Pipeline)

- Two-stage decoupled pipeline: `classify-diff-type` runs under `DecisionAuthority.FULL` (Bayesian reasoning over DecisionFrame); `escalate-diff-response` runs under `DecisionAuthority.LOW` (Softmax bandit with REINFORCE).
- 7-Action taxonomy across 3 tiers:
  - Tier 1 (Substantive): `new_superseding_adr`, `amendment_log_entry`
  - Tier 2 (Documentation): `correction_note`, `clarification_section`, `provenance_note`
  - Tier 3 (Lifecycle): `pending_supersession_note`, `supersession_update`
- 4 Standard criteria weights: `semantic_scope_impact` (0.40), `architectural_intent_shift` (0.35), `downstream_contract_footprint` (0.15), `textual_cosmetic_ratio` (0.10).
- Native margin & ambiguity halting: `DecisionFrame.minimum_margin = 0.05`. If utility difference $\le 0.05$, resolver returns `DecisionStatus.NEEDS_USER_TIE_BREAK`. Pipeline halts immediately for human input without invoking escalation policy.
- Human approval gate: when `classify_policy` requires human approval, status `DecisionStatus.NEEDS_USER_FEEDBACK` immediately halts with `disposition="needs_user_feedback"` without bypassing human review.
- Permanent Lineage Freeze: `new_superseding_adr`, `pending_supersession_note`, `supersession_update` are permanently barred from autonomy; hard-overridden to `escalate_to_human`.
- Lightweight evidence transport (ADR-006): `audit_evidence` envelope passed to `escalate-diff-response.decide()`, transported without SDK domain interpretation.
- Deferred audit logging (audit integrity): `Episode` audit record is constructed and persisted strictly after progression verification, ensuring blocked regressions never leave false autonomous execution records in storage.
- Progression gating (ADR-005): candidate amendment verified via `compare_decision_results()`. Progression yields +1.0 reward; regression triggers healing/reversion, disposition override to `escalate_to_human`, and yields -1.5 penalty.
- Stage 16 scope boundary: pipeline terminates with a validated governance baseline; Stage 17 Execution Adaptation is strictly out of scope.
- Zero storage expansion: no new Cosmos containers or LearningStore record types (ADR-002 Invariant #2).

## 2. Breakout & Recap Session (`agent_learning.lessons_learned`)

- **Role & Philosophy:** Not a new stage and not a heavy ceremony: a light recap held once per epic, after its last user story is implemented and reviewed (ADR-010 §4.1), on how the code was created from the stories (traps, defects, review findings). Adds no approval gate or `TaskPolicy`. It is distinct from the formal Stage 15 review, which is separate work and not defined here.
- **Canonical Register:** `docs/project-docs/Lessons-Learned-Register.md` (append-only, human-readable).
- **Schema (§4.3), enforced by the parser:**
  - `Identifier`: `LL-###`, and `Title` in the entry heading
  - `The Trap / Problem`: Real-world defect or hazard observed
  - `The Root Cause`: Underlying technical/procedural mechanism
  - `Actionable Invariant / Rule`: Rule or snippet preventing recurrence
  - `Tier 2/3 Propagation Target`: required to be present; may read `Tier 1 only`
  - Recommended `Epic / Story` (the Phase Close filter matches on it); optional `Date`, `Scope`.
- **No-new-lessons sign-off:** a short `LL-###` entry whose Epic/Phase contains `no-new-lessons` (ADR-010 §4.2).
- **Autonomous Breakout Facilitator (permitted, not built):** an agent may draft findings, register entries and propagation proposals, but a human accepts entries and every cross-repo action needs explicit human approval (ADR-010 §4.7).
- **3-Tier Propagation (Tier 1 always; Tier 2/3 considered, not mandatory):**
  - Tier 1: Project register (historical audit & Phase Close prerequisite).
  - Tier 2: In-repo component skill (`.claude/skills/<component>/SKILL.md`) for active agent enforcement.
  - Tier 3: Universal cross-project rules (`sidpa-template`, `RULE[user_global]`).
- **Phase Close Bridge:** `filter_crystallized_lessons()` outputs dicts with `crystallized: True` which directly satisfy `pmbok.models.intent_refinement.evaluate_phase_close_readiness()`.

## 3. Call sites

- `agent_learning/__init__.py`: re-exports `parse_lessons_learned_markdown`, `load_lessons_learned_register`, `filter_crystallized_lessons`, `LessonsLearnedEntry`, and governance pipeline symbols.
- `agent_learning/lessons_learned.py`: markdown parser and schema validator.
- `agent_learning/governance.py`: core diff classification pipeline and taxonomy constants.
