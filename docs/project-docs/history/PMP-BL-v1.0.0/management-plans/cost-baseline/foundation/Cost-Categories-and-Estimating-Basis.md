---
artifact_id: cost-foundation-categories-estimating-basis
parent_plan_id: cost-management
baseline_id: PMP-BL-v1.0.0
route: foundation_artifact
governance_policy: approve-subsidiary-plan
substage: "6.D-1"
version: "1.0.0"
owner_role: "Project Manager"
depends_on:
  - scope-management
  - schedule-management
approval_status: approved
pmbok_process: "Plan Financial Management"
---

# Cost Foundation — Cost Categories & Estimating Basis (`PMP-BL-v1.0.0`)

This artifact satisfies PMBOK 8 §2.4.2 *Plan Financial Management* (Figure 2-27) for the Cost Management Plan. It defines the formal units of measure, precision levels, estimating methodologies, and cost breakdown categories for **Phase 1: Warm-Start & Confidence-Interval Bandits**.

---

## 1. Units of Measure, Precision & Currency Standards

* **Effort Units:** **Person-Day (pd)**, defined as 6 focused engineering hours, and **Hours (hrs)**.
* **Financial Currency:** **Euros (€)**. Incurred USD tooling expenses (e.g. cloud API billing) are converted at the benchmark rate of **€1.00 = $1.08 USD**.
* **Precision Levels:**
  - Effort estimates: Rounded to the nearest **0.1 pd** (or **0.5 hours**).
  - Financial figures: Calculated to exact cents, reported to the nearest **€1.00**.
  - Earned Value Management ($EVM$) ratios ($CPI, SPI$): Precision to **two decimal places** (e.g. `0.92`).

---

## 2. Estimating Methodologies & Source Traceability

Cost estimates are generated using a hybrid **Bottom-Up** and **Parametric Rate-Conversion** methodology anchored in approved upstream baselines:

1. **Effort Forecasting (Bottom-Up):**
   * Aggregated directly from the 143 WBS dictionary items in [Scope-WBS-Dictionary.md](../../scope-baseline/foundation/Scope-WBS-Dictionary.md) and PERT three-point estimates ($\bar{d} = \frac{L + 4M + H}{6}$) in [Schedule-Baseline-WBS-Forecast.md](../../schedule-baseline/foundation/Schedule-Baseline-WBS-Forecast.md).
2. **Labor Valuation (Parametric Conversion):**
   * Effort hours are multiplied by the unit labor rate schedule approved in [Resource-Capacity-Estimates.md](../../resource-baseline/foundation/Resource-Capacity-Estimates.md) §5.
3. **External Spend Boundaries (Procurement Intake):**
   * Cloud, tooling, and API costs are bounded by the authoritative Make-or-Buy analysis and approved procurement limits in [Procurement-Management-Plan.md](../../Procurement-Management-Plan.md) §2.3 and §2.4.

---

## 3. Authoritative Cost Breakdown Structure (CBS)

Project costs are classified into six distinct categories:

| Category ID | Category Name | Scope Description | Measurement Basis | Phase 1 Cash Outlay | Phase 1 Economic Valuation |
| :--- | :--- | :--- | :--- | :---: | :---: |
| **CAT-LAB** | Internal Labor | Engineering, research, testing, architecture, and governance by maintainer. | Actual hours $\times$ €85.00/hr (internal shadow rate). | **€0.00**<br/>(Maintainer equity) | **€58,854.00**<br/>(115.4 pd Band B) |
| **CAT-EXT** | External Contractors | Third-party software engineering consultants or temp contractors. | Invoiced contractor hours. | **€0.00**<br/>(Strictly prohibited) | **€0.00**<br/>(Avoided €143.3k) |
| **CAT-CLD** | Cloud Services & APIs | Model API consumption (Gemini, Claude, Azure OpenAI) for pair programming & testing. | Monthly credit card / API usage invoices. | **≤ €200.00**<br/>(Capped at €100/mo) | **€200.00** |
| **CAT-HW** | Host Hardware & Compute | Developer workstation, WSL2 Linux environment, local storage. | Host depreciation & power. | **€0.00**<br/>(Sunk hardware) | **€0.00** |
| **CAT-CONT**| Contingency Reserve | Known-unknown risks in technical implementation (15% reserve). | 25.0 engineering hours + €50 API buffer. | **€50.00** | **€2,175.00**<br/>(25h $\times$ €85 + €50) |
| **CAT-MGMT**| Management Reserve | Unknown-unknown risks and Sponsor-initiated research exploration. | 5.0 person-days (30.0 hours) buffer. | **€0.00** | **€2,550.00**<br/>(30h $\times$ €85) |

---

## 4. Human Resources Governance Protocol

> [!NOTE] HR Labor Rate Authority
> In accordance with [Resource-Capacity-Estimates.md](../../resource-baseline/foundation/Resource-Capacity-Estimates.md) §5.4, the €85.00/hr internal labor rate is an estimated opportunity cost baseline established by the Project Sponsor/PM for `agent-learning`.  
> In organizational enterprise settings or future corporate project iterations, all labor rate tables, standard job grade classifications, and temp contractor rate ceilings are formally owned and governed by the **Human Resources Specialist / HR Department** to ensure compliance with enterprise payroll structures, collective labor agreements, and statutory billing requirements.
