# FDD-008: PMBOK 8 Lifecycle Orchestration and Closed-Loop Adaptation Feedback

**Source ADR:** [ADR-008](../../adr/ADR-008-pmbok-lifecycle-orchestration-and-pmp-adaptation-loop.md) — Accepted (2026-10-24)  
**Governing Baseline:** `PMP-BL-v1.0.0`  
**Source BRD:** [BRD-008](../Business-Requirements/BRD-008-pmbok-lifecycle-orchestration-and-pmp-adaptation-loop.md)  
**Status:** Draft — functional design derived from an Accepted ADR and BRD  

---

## 1. System Architecture & Component Interactions

The PMBOK 8 Orchestration Engine integrates natively into `agent-learning` to orchestrate project management subsidiary plans and close the continuous adaptation loop.

```
       Stage 1-4: Initiating
 [Spark] → [Ideation] → [Business Case] → [Charter]
                                               │
                                               ▼
                              ┌───────────────────────────────────┐
                              │  scripts/orchestrate_pmbok.py     │
                              │  (PMBOK 8 Planning Orchestrator)  │
                              └─────────────────┬─────────────────┘
                                                │
                 ┌──────────────────────────────┴──────────────────────────────┐
                 ▼                                                             ▼
     [9 Subsidiary Plans]                                            [Integrated PMP]
  Scope, Schedule, Cost, Quality,                                 Project-Management-Plan.md
  Resource, Comms, Risk, Proc, Stk                                             │
                 │                                                             ▼
                 │                                                 ┌───────────────────────┐
                 │                                                 │     approve-pmp       │
                 │                                                 │ (Bayesian Full Auth)  │
                 │                                                 └───────────┬───────────┘
                 │                                                             │
                 ▼                                                             ▼
  Stage 7: Technical Specifications (ADR → BRD → FDD → Stories) ←──────────────┘
                 │
                 ▼
  Stage 8-11: Work Package Execution & Quality Audit
                 │
                 ▼
  Stage 15: Lessons Learned & Evidence Synthesis
                 │
                 ▼
  Stage 16: Governance Change (ADR-007 Paired Diff Pipeline)
                 │
                 ▼
  Stage 17: Adaptation Plan (Adaptation-Plan.md)
                 │
                 └───────────────────────────────┐
                                                 ▼
                              ┌───────────────────────────────────┐
                              │ orchestrate_pmbok.py --mode adapt │
                              │ (Selective Sub-Plan Re-execution) │
                              └───────────────────────────────────┘
```

---

## 2. Functional Interfaces & Data Contracts

### 2.1 PMBOK Planning Orchestrator CLI (`scripts/orchestrate_pmbok.py`)

- **Full Planning Mode:**
  ```powershell
  python scripts/orchestrate_pmbok.py --mode full --charter docs/project-docs/Project-Charter.md --output-dir docs/project-docs/management-plans
  ```
  Executes all 9 subsidiary planning process agents in dependency order:
  1. `4.2-plan-scope-management`
  2. `4.2-plan-schedule-management`
  3. `4.2-plan-cost-management`
  4. `4.2-plan-quality-management`
  5. `4.2-plan-resource-management`
  6. `4.2-plan-communications-management`
  7. `4.2-plan-risk-management`
  8. `4.2-plan-procurement-management`
  9. `4.2-plan-stakeholder-engagement`
  Synthesizes output into `docs/project-docs/Project-Management-Plan.md`.

- **Adaptive Feedback Mode:**
  ```powershell
  python scripts/orchestrate_pmbok.py --mode adapt --adaptation-plan docs/project-docs/Adaptation-Plan.md
  ```
  Parses the modified areas list from `Adaptation-Plan.md` (e.g. `Quality Management`, `Risk Management`), selects only those corresponding agent keys, re-runs those agents against updated context, and re-synthesizes `Project-Management-Plan.md`.

### 2.2 Decision Gate: `approve-pmp`

- **Task ID:** `approve-pmp`
- **Agent ID:** `agent-learning-governance`
- **Authority:** `DecisionAuthority.FULL` (Bayesian Multi-Criteria Decision Reasoning)
- **Complexity Profile:** `Tier: Standard`, `requires_human_approval: true`
- **Actions (3-Action Governance Taxonomy):**
  - `approve_pmp`: All 9 subsidiary plans are coherent, baselines are defined, risk reserves are realistic, and quality gates are defined.
  - `reject_pmp`: Fundamental flaws, irreconcilable scope/schedule contradictions, or missing baseline governance.
  - `request_revision_before_decision`: Specific subsidiary plans require rework before PMP baseline sign-off.
- **Evaluation Criteria:**
  - `subsidiary_plan_completeness` (weight: 0.30): Coverage across all required knowledge areas.
  - `baseline_coherence` (weight: 0.30): Harmony across scope, schedule, cost, quality, and risk.
  - `adaptation_responsiveness` (weight: 0.25): Fidelity to lessons learned and governance change inputs.
  - `governance_traceability` (weight: 0.15): Direct lineage to Project Charter and Business Case.

### 2.3 Storage Invariant

In full compliance with ADR-002:
- PMP decision frames, evaluations, and human adjudications are persisted as `Episode` records in the `episodes/agent-learning-governance/` partition.
- No schema changes or external tables are introduced.

### 2.4 PMP Baseline Versioning & History Archival

- **Baseline ID Schema:** `PMP-BL-v{major}.{minor}.{patch}`
- **Directory Layout:**
  ```
  docs/project-docs/
    Project-Management-Plan.md          <-- Active approved baseline (PMP-BL-v1.1.0)
    management-plans/
      Scope-Management-Plan.md
      Risk-Management-Plan.md
      ...
      history/
        PMP-BL-v1.0.0/                  <-- Prior archived baseline snapshot
          Project-Management-Plan.md
          Scope-Management-Plan.md
          ...
  ```
- **Tagging Contract:** Downstream requirements specify:
  ```yaml
  ---
  pmp_baseline: "PMP-BL-v1.1.0"
  ---
  ```

### 2.5 Deterministic Rollback Protocol

If `compare_decision_results()` flags a `regression` upon post-adaptation verification or downstream test execution:
1. Orchestrator executes:
   ```powershell
   python scripts/orchestrate_pmbok.py --mode rollback --to-baseline PMP-BL-v1.0.0
   ```
2. Copies `management-plans/history/PMP-BL-v1.0.0/*` into `management-plans/` and restores `Project-Management-Plan.md`.
3. Emits negative reward (-1.5) to `escalate-diff-response` for the episode.
4. Registers an audit episode documenting the rollback rationale.

### 2.6 Configurable Decision Weighting Profiles

Decision frames for `approve-pmp` support profile selection:
- **`profile: standard` (default):** `subsidiary_plan_completeness` (0.35), `baseline_coherence` (0.35), `adaptation_responsiveness` (0.15), `governance_traceability` (0.15).
- **`profile: regulated`:** `subsidiary_plan_completeness` (0.25), `baseline_coherence` (0.45), `adaptation_responsiveness` (0.15), `governance_traceability` (0.15).
- **`profile: spike`:** `subsidiary_plan_completeness` (0.20), `baseline_coherence` (0.20), `adaptation_responsiveness` (0.30), `governance_traceability` (0.30).

