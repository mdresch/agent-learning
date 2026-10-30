---
artifact_id: scope-foundation-monitor-control-scope
parent_plan_id: scope-management
baseline_id: PMP-BL-v1.0.0
route: foundation_artifact
governance_policy: approve-subsidiary-plan
substage: "6.A-3"
version: "1.0.0"
owner_role: "Project Manager"
depends_on: []
approval_status: approved
pmbok_process: "Monitor and Control Scope"
---

# Scope Foundation — Monitor and Control Scope (`PMP-BL-v1.0.0`)

PMBOK 8 **Scope Performance Domain** §2.2 — **Monitor and Control Scope**. Variance categories, escalation, and downstream staleness for baseline `PMP-BL-v1.0.0`.

## Roles

* **Project Manager:** Enforce boundaries; reject unauthorized scope; monitor backlog drift.
* **Project Sponsor (Menno Drescher):** Sovereign authority on scope, milestones, budget.

## Scope variance levels

| Level | Definition | Authority | Action |
| --- | --- | --- | --- |
| **0 — Operational** | Refactor or doc fix within an approved story | Developer / Tech Lead | Commit; log in `implementation-log.md` |
| **1 — Story** | Add or adjust $AC_n$ within an epic | Project Manager | Update story; notify Sponsor |
| **2 — Milestone** | New story or epic boundary change | Project Sponsor | Stage 16 governance change |
| **3 — Baseline breach** | New epic, Charter change, Phase 2 work | Project Sponsor | Stage 17 `approve-adaptation-plan` |

## Control activities

1. Compare requested work to [Scope-Project-Scope-Statement.md](Scope-Project-Scope-Statement.md) bands and [Scope-WBS-Dictionary.md](Scope-WBS-Dictionary.md) rows.
2. Reject or defer work outside Band B during Phase 1 unless Level 2+ approval opens Band C.
3. On Level 2+ scope baseline change: re-hash WBS dictionary; mark Schedule and Cost **`STALE_DEPENDENCY`** (ADR-013 §4.5).
4. Record design-time scope defects as **BFI-NNN** on the Scope plan (ADR-037); execution defects via Stage 16 → 17.

## Downstream invalidation (ADR-013)

$$\text{Scope} \longrightarrow \text{Schedule} \longrightarrow \text{Cost}$$

Level 2 or Level 3 changes to the integrated scope baseline require Schedule and Cost subsidiary plans to re-approve before `approve-pmp`.
