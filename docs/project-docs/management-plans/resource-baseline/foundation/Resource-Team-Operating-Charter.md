---
artifact_id: resource-foundation-team-operating-charter
parent_plan_id: resource-management
baseline_id: PMP-BL-v1.1.0
route: foundation_artifact
governance_policy: approve-subsidiary-plan
substage: "6.C-4"
version: "2.0.0"
owner_role: "Project Manager"
depends_on:
  - scope-management
  - schedule-management
approval_status: approved
pmbok_process: "Lead the Team"
---

# Resource Foundation — Team Operating Charter (`PMP-BL-v1.1.0`)

Operating agreements, engineering ethics, and human–agent collaborative boundaries for **Phase 2: Autonomous Feedback Loops & Extensible Architecture**.

**Historical Baseline Archive:** Frozen Phase 1 operating charter preserved in [`docs/project-docs/history/PMP-BL-v1.0.0/management-plans/resource-baseline/foundation/Resource-Team-Operating-Charter.md`](../../history/PMP-BL-v1.0.0/management-plans/resource-baseline/foundation/Resource-Team-Operating-Charter.md).

---

## 1. Core Operating Principles (Phase 2)

```
+-----------------------------------------------------------------------------------+
|                        PHASE 2 CORE OPERATING PRINCIPLES                          |
+-----------------------------------------------------------------------------------+
|  1. Observed RED-First   | Never write code without a failing contract test ($AC_n)|
|  2. Pure Stdlib First    | Zero extraneous runtime dependencies in extensions      |
|  3. Inspectable Autonomy | Every Bayesian resolution records an explicit Episode   |
|  4. Immutable Baselines  | Canonical hashing prevents silent specification drift   |
|  5. Generational Memory  | Post-epic recaps crystallize lessons into active rules  |
|  6. Fork Collision Guard | Never edit src/agent_learning/; isolate in ext package   |
|  7. Decoupled Research   | Exploratory surveys remain in docs/research/ideation/   |
+-----------------------------------------------------------------------------------+
```

---

## 2. Human–Agent Collaboration Protocols

* **Human Sponsor & Tech Lead (Menno Drescher):**
  - Holds sole decision authority over Charter scope, milestone progression, and baseline formalization.
  - Reviews every PR and adjudicates Bayesian governance gates.
  - Manages upstream Microsoft Partner Network (MPN) relationships.
* **Lead Agent Engineer (Antigravity):**
  - Authors contract tests ($AC_n$) observing RED state before GREEN implementation.
  - Strictly develops within `agent-training-ext/` using pure Python standard library.
  - Guarantees `src/agent_learning` exhibits zero lines of diff against upstream Microsoft HEAD.
  - Maintains `python scripts/phase_rollup.py --check` exiting with code 0 at all times.
