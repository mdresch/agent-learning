---
name: pmbok-planning
description: Orchestrates PMBOK 8 subsidiary management plans and synthesizes the integrated Project Management Plan (PMP) with agent-learning decision validation gates.
---

# PMBOK Planning Skill

This skill orchestrates the generation, synthesis, and adaptation of the 9 PMBOK 8 subsidiary management plans and the overarching Project Management Plan (PMP) for projects initialized from `sidpa-template`.

## Lightweight Runtime Migration (ADR-034)

The replacement for the legacy PMBOK stack is being delivered by Epic 34. The pure process
catalogue is `agent_learning.pmbok.legacy_registry.legacy_processes()`; its contract is
`tests/test_legacy_registry.py` (Story 34.1). Keep its 49 process IDs and prerequisite tuples
aligned with FDD-034 §2 and the legacy `PROCESS_DEPENDENCY_MAP` until Story 34.5 removes the old
tree. The returned mapping is immutable.

Project run state follows the same boundary: `agent_learning.pmbok.run_state` defines
`RunSnapshot`, `RunEpisodeFields`, `build_run_fields`, and the pure `latest_run` ordering
function. Its contract is `tests/test_pmbok_run_state.py` (Story 34.2). Persist each event as a
new `Episode` through `agent_learning.pmbok_runtime.runs`; use the standard `LearningStore`
interface and keep the seven-field run metadata contract exact. Run episodes use
`action_type="governance"` and `action_logprob=None`, and must never create a database file.
`latest_run_for` retries an unstable append-only read at most three times, then raises
`RuntimeError`; malformed matching records must surface explicit validation errors rather
than being silently skipped. Run `created_at` values are timezone-aware ISO-8601 strings;
latest-run selection compares their instants in UTC without rewriting persisted values.

`agent_learning.pmbok` remains pure: do not add `LearningStore`, `pydantic`, the top-level
`pmbok` package, file I/O, or network I/O to the registry. Runtime storage and external calls
belong in `agent_learning.pmbok_runtime`. Until Story 34.4 delivers the unified CLI, the legacy
orchestration commands below remain transitional; do not extend their implementation.

## Supported Workflows

### 1. Full Planning Orchestration
Executed after `Project-Charter.md` is approved by `approve-charter`. Generates all 9 subsidiary management plans and integrates them into `Project-Management-Plan.md`.

```powershell
python scripts/orchestrate_pmbok.py --mode full --charter docs/project-docs/Project-Charter.md
```

*(Add `--mock` for offline / stub execution without external LLM keys).*

### 2. Closed-Loop Adaptation Regeneration
Executed when an `Adaptation-Plan.md` (Stage 17) evaluates governance amendments via the **Governance Change Impact Matrix** and identifies specific subsidiary plans requiring revision after a Stage 16 Governance Change.

```powershell
python scripts/orchestrate_pmbok.py --mode adapt --adaptation-plan docs/project-docs/Adaptation-Plan.md
```

This scans the checklist in `Adaptation-Plan.md`:
- `[x] Scope Management Plan` $\rightarrow$ regenerates `5.1`
- `[x] Schedule Management Plan` $\rightarrow$ regenerates `6.1`
- `[x] Cost Management Plan` $\rightarrow$ regenerates `7.1`
- `[x] Quality Management Plan` $\rightarrow$ regenerates `8.1`
- `[x] Resource Management Plan` $\rightarrow$ regenerates `9.1`
- `[x] Communications Management Plan` $\rightarrow$ regenerates `10.1`
- `[x] Risk Management Plan` $\rightarrow$ regenerates `11.1`
- `[x] Procurement Management Plan` $\rightarrow$ regenerates `12.1`
- `[x] Stakeholder Engagement Plan` $\rightarrow$ regenerates `13.2`

It regenerates only the checked plans, updates `docs/project-docs/management-plans/`, archives prior baselines to `management-plans/history/{baseline_id}/`, and re-synthesizes `docs/project-docs/Project-Management-Plan.md`.

### 3. Decision Validation Gate Verification
After synthesis, the integrated PMP must be validated via `approve-pmp`:

```powershell
agent-learn task-policy-decide --agent-id template-governance --task-id approve-pmp
```

### 4. PMP Baseline Versioning & Traceability Invariant (Invariant 6)
Every approved PMP receives an immutable SemVer identifier (`PMP-BL-v1.0.0`, `PMP-BL-v1.1.0`). All downstream technical requirements (ADRs, BRDs, FDDs, Stories) must reference the active baseline:
```yaml
---
pmp_baseline: "PMP-BL-v1.0.0"
---
```

### 5. Deterministic Rollback Protocol (Invariant 7)
If downstream execution triggers regressions, atomic rollback restores the prior approved baseline from archive and penalizes the escalation bandit:
```powershell
python scripts/orchestrate_pmbok.py --mode rollback --to-baseline PMP-BL-v1.0.0
```

### 6. Phase Next Evolutionary Seeding (Stage 18 -> Stage 1)
When Stage 18 Intent Refinement completes with a disposition of `phase_handoff` and receives full Bayesian governance approval (`approve-intent-refinement`), run the orchestrator in `seed-next` mode to mechanically scaffold Phase $N+1$:

```powershell
python scripts/orchestrate_pmbok.py --mode seed-next --refinement-proposal docs/project-docs/Intent-Refinement-Proposal.md
```

This automatically:
1. Parses `Intent-Refinement-Proposal.md` for governing baseline, validated invariants, and refined child hypotheses.
2. Increments the major baseline (`PMP-BL-v1.0.0` -> `PMP-BL-v2.0.0`).
3. Seeds `docs/project-docs/Spark-Capture.md` (Stage 1) referencing the governing refinement.
4. Seeds `docs/project-docs/Ideation-Document.md` (Stage 1 Ideation) with carried-over child hypotheses ($d=1, 2$) and formal Bayes factor criteria.
5. Directs the operator to evaluate `approve-ideation` under `template-governance`.

### 7. Administrative Decommissioning (Stage 18 Project Termination)
If Stage 18 outcome evaluation concludes that the project's strategic intent is fully realized or non-viable (`disposition_type: project_termination`), run the orchestrator in `decommission` mode:

```powershell
python scripts/orchestrate_pmbok.py --mode decommission --refinement-proposal docs/project-docs/Intent-Refinement-Proposal.md
```

This generates `docs/archive/decommission_{timestamp}/DECOMMISSION-SUMMARY.md`, archives final baselines, and logs administrative teardown in full compliance with PMBOK 8 Phase Close guidelines.
