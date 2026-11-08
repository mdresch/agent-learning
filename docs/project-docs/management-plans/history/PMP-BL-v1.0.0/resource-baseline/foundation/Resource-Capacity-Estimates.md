---
artifact_id: resource-foundation-capacity-estimates
parent_plan_id: resource-management
baseline_id: PMP-BL-v1.0.0
route: foundation_artifact
governance_policy: approve-subsidiary-plan
substage: "6.C-2"
version: "1.0.0"
owner_role: "Project Manager"
depends_on:
  - scope-management
  - schedule-management
approval_status: approved
pmbok_process: "Estimate Resources"
---

# Resource Foundation — Capacity Estimates & Workload Modeling (`PMP-BL-v1.0.0`)

This artifact satisfies PMBOK 8 §2.6.2 *Estimate Resources* (Figure 2-42) for the Resource Management Plan. It reconciles maintainer human capacity against the **Schedule Baseline** effort forecasts ([Schedule-Baseline-WBS-Forecast.md](../../schedule-baseline/foundation/Schedule-Baseline-WBS-Forecast.md)) and Phase 1 milestone timeboxes ([Schedule-Management-Plan.md](../../Schedule-Management-Plan.md) §1.2).

---

## 1. Capacity Modeling Basis

### 1.1 Planning Units & Availability Assumption
* **Unit of Effort:** **Person-Day (pd)**, defined as approximately **6 focused, productive engineering hours** of maintainer focus.
* **Maintainer Availability:** **~5 pd per calendar week** (~30 focused hours per week).
* **Work Style:** High-intensity agile pair engineering; maintainer-paced volunteer initiative. In accordance with [Project-Charter.md](../../../Project-Charter.md) §7, the project is **velocity-driven and milestone-gated**, not bound to rigid calendar delivery dates.

### 1.2 Program Workload vs. Maintainer Capacity

The effort baseline was established at **6.B-4** across all 143 WBS items in [Scope-WBS-Dictionary.md](../../scope-baseline/foundation/Scope-WBS-Dictionary.md):

| Horizon / Work Breakdown Band | Remaining Stories | Low (pd) | Medium (pd) | High (pd) | **Weighted $\bar{d}$ (pd)** | Duration at 5 pd/wk |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| **Full Program** (all incomplete WBS items) | 112 | 181.5 | 373.0 | 708.0 | **396.9** | ~79.4 calendar weeks |
| **Phase 1 Band B** (Epics 15–17, 19–20) | 31 | 54.5 | 109.0 | 202.0 | **115.4** | ~23.1 calendar weeks |
| **Phase 1 CPM Critical Path** (single resource) | 22 | — | 67.0 | — | **67.0** | ~13.4 calendar weeks |
| **Deferred Band C** (Option B / Phase 2) | 12 | 26.0 | 52.0 | 104.0 | **~56.0** | ~11.2 calendar weeks |
| **Program Track Bands D & E** | 69 | 101.0 | 212.0 | 402.0 | **225.5** | ~45.1 calendar weeks |

```
Program Total Workload: [==================================== 396.9 pd ====================================]
Phase 1 Band B Demand:  [============= 115.4 pd =============]
Phase 1 CPM Path (Dur M):[====== 67.0 pd ======]
Charter Serial Windows: [=== 37.5 pd ===] (Aggressive target timebox with AI pair acceleration)
```

---

## 2. Milestone Allocation & Resource Feasibility

Phase 1 delivery is structured around fixed **Charter milestone windows** (Schedule plan §1.2). The table below reconciles maintainer capacity against milestone requirements:

| Milestone | Theme & Anchor | Exit Condition | Maintainer Capacity Allocated | Predecessors | Feasibility Notes |
| :---: | :--- | :--- | :---: | :--- | :--- |
| **M0.5** | Value Research (HYP-AL-011) | Go/No-Go on long-term build; Research Log updated | **5 pd** (40 h timebox) | Charter approval | Parallel with M1–M4; protected from coding preemption. |
| **M1** | Softmax Policy Reuse (Epic 20) | `SoftmaxPolicy` inspection report completed | **5 pd** (~1 week) | Charter approval | Focused technical inspection and contract verification. |
| **M2** | Warm-Start Prototype (Epics 19, 20) | Warm-start / meta-prior runnable; HYP-AL-008 testable | **10 pd** (~2 weeks) | M1 disposition | Implement prior inheritance interfaces and tests. |
| **M3** | CI Bandit Engine (Epics 15, 16, 17) | UCB & Thompson resolvers active under positive-only | **10 pd** (~2 weeks) | M2 disposition | Confidence interval math, distribution updates. |
| **M4** | Autonomy Benchmark (Stories 9.1, 10.1) | 146-episode autonomy fixture green vs REINFORCE | **7.5 pd** (~1.5 weeks) | M3 (+ Epic 34 rec.) | Benchmarking harness; Epic 34 decommissioning unblocks. |
| **M5** | Phase Close & Go/No-Go Gate | Bayes factors recorded; Option B disposition decided | **5 pd** (~1 week) | M0.5 & M4 | Synthesis, statistical verification, formal review. |
| **Res.** | Contingency Buffer (SR-M5-01) | Buffer for Bayes recalculation & review | **5 pd** (PM Reserve) | Before M5 gate | PM-controlled buffer for review and rework. |

**Total Phase 1 Calendar Window:** **37.5 pd** serial window + **5 pd** contingency buffer.  
**Critical Path Length:** M1 (5 pd) + M2 (10 pd) + M3 (10 pd) + M4 (7.5 pd) + M5 (5 pd) = **37.5 pd** (~7.5 calendar weeks at 5 pd/week).

---

## 3. Human–AI Engineering Acceleration Factor

The divergence between the **67 pd** CPM effort duration (or **115.4 pd** total Band B effort) and the **37.5 pd** calendar target window is accounted for by **human–agent pair acceleration**:

1. **Boilerplate & Test Generation (2.0x acceleration):** Writing standardized contract tests ($AC_n$), input/output schemas, and mock fixtures is accelerated by 50%–70% through interactive AI pair sessions.
2. **Linting & Refactoring (2.5x acceleration):** Type checking, `ruff` formatting, and docstring reconciliation are handled rapidly by agent assistants.
3. **Core Algorithmic & Architectural Design (1.0x unaccelerated):** High-level architectural reasoning, Bayesian mathematical models, and governance decisions require deliberate human intellectual effort and cannot be compressed by AI generation.
4. **Overall Modeled Velocity Multiplier:** The human maintainer achieves an effective throughput of approximately **1.6x–1.8x** standard single-developer baseline velocity across mixed implementation tasks.

---

## 4. Workload Bounds & Capacity Limits

* **Maximum Weekly Workload Cap:** **6 pd (36 hours)** per calendar week. Any sprint requiring > 6 pd is formally flagged as an over-allocation risk.
* **Over-allocation Response:** When actual effort exceeds planned estimates by > 20%, the Project Manager triggers the **Descope vs. Reschedule Protocol** ([Resource-Utilization-and-Control-Protocol.md](Resource-Utilization-and-Control-Protocol.md)) rather than absorbing unrecorded overtime.
* **Buffer Management:** The **5 pd** contingency buffer before M5 is monitored in [Schedule-Reserve-Register.md](../../schedule-baseline/foundation/Schedule-Reserve-Register.md) (Risk ID `SR-M5-01`). Consumption > 2 pd requires a logged rationale in `implementation-log.md`.

---

## 5. HR Cost & Labor Rate Schedule (Make-or-Buy & Cost Baseline Anchor)

To provide an empirical foundation for the **Procurement Make-or-Buy Analysis** and the **Cost Management Plan** budget aggregation, human and synthetic labor effort is quantified under a **Dual-Rate Accounting Model**:

### 5.1 Project Labor Rate Schedule

| Resource Role | Named Party / Platform | Internal Economic Shadow Rate | Cash Outlay Rate | External Benchmark Rate (Make-or-Buy) | Accounting Treatment |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Principal Researcher / Tech Lead / PM** | Menno Drescher | **€85.00 / hr**<br/>(€510 / 6-hr pd) | **€0.00 / hr** | **€135.00 / hr**<br/>(€1,080 / 8-hr day for Senior AI/ML Consultant) | **Imputed Economic Value:** Reflects true project investment & asset creation.<br/>**Cash Outlay:** €0.00 (maintainer sweat equity). |
| **AI Engineering Assistant** | Antigravity / Cursor / Claude 3.5 Sonnet | **€2.00 / hr**<br/>active pairing | Usage-based<br/>(≤ €100/mo) | N/A (Proprietary paired capability) | Operational tooling cost (API tokens & IDE subscriptions). |
| **Workstation & Local Compute** | Windows 11 / WSL2, Cosmos DB Emulator | **€0.00 / hr** | **€0.00 / hr** | **€0.65 / hr**<br/>(Cloud GPU / VM instance) | Sunk host hardware capital ($0 incremental). |

### 5.2 Phase 1 Workload Valuation

Applying the internal labor rate (€85.00/hr, €510.00/pd) across Phase 1 effort allocations yields the authoritative baseline valuation:

* **Phase 1 Band B Total Effort (115.4 pd / 692.4 hrs):**
  $$\text{Economic Effort Value} = 115.4\text{ pd} \times €510.00/\text{pd} = \mathbf{€58,854.00} \quad (\text{Cash Outlay} = \mathbf{€0.00})$$
* **Phase 1 CPM Critical Path (67.0 pd / 402.0 hrs):**
  $$\text{Economic Effort Value} = 67.0\text{ pd} \times €510.00/\text{pd} = \mathbf{€34,170.00} \quad (\text{Cash Outlay} = \mathbf{€0.00})$$
* **Charter Serial Milestone Windows (37.5 pd + 5.0 pd Buffer = 42.5 pd / 255.0 hrs):**
  $$\text{Economic Effort Value} = 42.5\text{ pd} \times €510.00/\text{pd} = \mathbf{€21,675.00} \quad (\text{Cash Outlay} = \mathbf{€0.00})$$

### 5.3 Make-or-Buy Comparison Valuation

When Procurement evaluates engaging an external consultancy / temp contractor against internal execution:
$$\text{External Contractor Cost (Band B)} = 115.4\text{ days} \times 8\text{ hrs/day} \times €135.00/\text{hr} = \mathbf{€124,632.00} \text{ cash outlay}$$
$$\text{Cost Avoidance via Internal Sourcing} = €124,632.00 - €0.00 = \mathbf{€124,632.00} \text{ direct cash savings}$$

### 5.4 Human Resources Governance Standard

> [!NOTE] Human Resources Governance Policy
> For this specific project (`agent-learning`), labor rates are estimated by the Project Sponsor/PM based on market averages for senior AI engineering and maintainer opportunity cost.  
> In enterprise organizational environments or future commercial program phases, labor rates, role banding, and billing definitions are strictly governed by the **Human Resources Specialist / HR Department** to ensure standardized compensation governance, legal compliance, and accurate cross-departmental chargeback.
