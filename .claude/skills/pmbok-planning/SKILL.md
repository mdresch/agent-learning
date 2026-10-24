---
name: pmbok-planning
description: Orchestrates PMBOK 8 subsidiary management plans and synthesizes the integrated Project Management Plan (PMP) with agent-learning decision validation gates.
---

# PMBOK Planning Skill

This skill orchestrates the generation, synthesis, and adaptation of the 9 PMBOK 8 subsidiary management plans and the overarching Project Management Plan (PMP) for projects initialized from `sidpa-template`.

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
