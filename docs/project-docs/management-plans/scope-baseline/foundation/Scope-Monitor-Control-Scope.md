---
artifact_id: scope-foundation-monitor-control-scope
parent_plan_id: scope-management
baseline_id: PMP-BL-v1.1.0
route: foundation_artifact
governance_policy: approve-subsidiary-plan
substage: "6.A-3"
version: "2.0.0"
owner_role: "Project Manager"
depends_on: []
approval_status: approved
pmbok_process: "Monitor and Control Scope"
---

# Scope Foundation — Monitor and Control Scope (`PMP-BL-v1.1.0`)

**PMBOK 8 Scope Performance Domain** §2.2 — **Monitor and Control Scope**. Variance categories, escalation protocols, and downstream staleness mechanisms for baseline `PMP-BL-v1.1.0`.

**Historical Baseline Archive:** Frozen Phase 1 control protocol preserved in [`docs/project-docs/history/PMP-BL-v1.0.0/management-plans/scope-baseline/foundation/Scope-Monitor-Control-Scope.md`](../../history/PMP-BL-v1.0.0/management-plans/scope-baseline/foundation/Scope-Monitor-Control-Scope.md).

---

## 1. Accountable Roles

* **Project Manager / PMBOK Steward:** Enforces scope boundaries, monitors backlog status drift via `phase_rollup.py --check`, and rejects unauthorized scope additions.
* **Project Sponsor (Menno Drescher):** Holds sovereign authority over scope baselines, milestone authorizations, and budget allocations.
* **Lead Agent Engineer (Antigravity):** Enforces pure standard library implementation and guarantees upstream code isolation in `agent-training-ext/`.

---

## 2. Scope Variance Classification

| Level | Definition | Decision Authority | Required Governance Action |
|---|---|---|---|
| **Level 0 (Operational)** | Minor refactoring, docstrings, or test formatting within an approved Story | Lead Agent Engineer | Immediate commit; record in `implementation-log.md`. |
| **Level 1 (Story Scope)** | Adding or adjusting an Acceptance Criterion ($AC_n$) within an approved Epic | Project Manager | Update User Story specification; notify Sponsor. |
| **Level 2 (Milestone Scope)** | Adding a new User Story, modifying milestone delivery targets, or updating test harness | Project Sponsor | Formal review via Stage 16 Governance Change. |
| **Level 3 (Baseline Breach)** | Adding an Epic, modifying Charter boundaries, Phase 3 work, or **any edit to `src/agent_learning/`** | Project Sponsor | Formal review via Stage 17 Integrated Change (`approve-adaptation-plan`). |

---

## 3. Scope Control & Audit Activities (Phase 2)

1. **Backlog Drift Verification:** Execute `python scripts/phase_rollup.py --check` on every commit and PR. Must exit with 0 drift rows.
2. **Upstream Fork Collision Protection Audit:** Verify that `git diff upstream/main -- src/agent_learning` exhibits zero lines of diff. Any unauthorized addition to `src/agent_learning` is rejected as a Level 3 breach.
3. **Band Enforcement:** Verify that development work traces strictly to authorized Phase 2 bands: Band C (Epics 14, 18) and Band D (Epics 16, 21, 22, 38).
4. **Downstream Invalidation Protocol (ADR-013 §4.5):**
   $$\text{Scope Baseline} \longrightarrow \text{Schedule Baseline} \longrightarrow \text{Cost Baseline}$$
   Any Level 2 or Level 3 change automatically marks Schedule and Cost plans as `STALE_DEPENDENCY` until re-baselined.
