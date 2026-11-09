---
artifact_id: cost-foundation-pack-manifest
parent_plan_id: cost-management
baseline_id: PMP-BL-v1.0.0
route: foundation_pack
governance_policy: approve-subsidiary-plan
version: "1.1.0"
owner_role: "Project Manager"
depends_on:
  - scope-management
  - schedule-management
pack_status: approved
---

# Cost Foundation Pack — Manifest (`PMP-BL-v1.0.0`)

Roll-up for **Stage 6.D** (proactive cost foundation breakouts) establishing the authoritative **Integrated Cost Baseline** before the first `approve-subsidiary-plan` on [Cost-Management-Plan.md](../Cost-Management-Plan.md) **v1.1+**.

**Pack state:** Complete — all six foundation artifacts under [foundation/](foundation/) are authored with agent-learning project details, mathematically validated, and approved (`approval_status: approved`).

**Normative standards:** [ADR-027](../../../adr/ADR-027-cost-management-plan-standard-and-baseline-contract.md) (Cost plan contract, Tier 1), [ADR-013](../../../adr/ADR-013-subsidiary-plan-approval-gates-before-pmp-formalization.md), [ADR-012](../../../adr/ADR-012-subsidiary-management-plan-standards-and-content-contracts.md). **Path A (normative):** Tier-1 foundation pack normative for the first Cost subsidiary approval—record **BFI-004** on the Cost plan at **6.D-7** without amending ADR-027.

**PMBOK 8 anchor:** Finance Performance Domain **§2.4** (printed pp. 58–67); processes **§2.4.2** (Figures **2-26**–**2-30**); reserves **Fig. 2-25**; check outcomes **§2.4.5 Table 2-8**. Legacy process **7.1 Plan Cost Management** maps to **Plan Financial Management**.

---

## Integrated cost baseline (this cycle)

When **6.D-6** and **6.D-7** complete, the **integrated cost baseline** for `PMP-BL-v1.0.0` is:

1. **Approved this manifest** (registry hashes current).
2. **Approved [Cost-Management-Plan.md](../Cost-Management-Plan.md) v1.1+** — envelope authority (§1), governance (§3), variance (§2).
3. **Approved foundation artifacts** (six files, substages **6.D-0P** … **6.D-5**):

| # | Substage | Artifact | PMBOK §2.4.2 process |
| ---: | --- | --- | --- |
| 1 | 6.D-0P | [Cost-Pillar-Overview-and-Trace.md](foundation/Cost-Pillar-Overview-and-Trace.md) | Strategy trace (inputs to Plan Financial Management) |
| 2 | 6.D-1 | [Cost-Categories-and-Estimating-Basis.md](foundation/Cost-Categories-and-Estimating-Basis.md) | Plan Financial Management (Fig. 2-27) |
| 3 | 6.D-2 | [Cost-Estimates-by-Category.md](foundation/Cost-Estimates-by-Category.md) | Estimate Costs (Fig. 2-28) |
| 4 | 6.D-3 | [Cost-Staged-Budget-and-Baseline.md](foundation/Cost-Staged-Budget-and-Baseline.md) | Develop Budget (Fig. 2-29; Fig. 2-25 reserves) |
| 5 | 6.D-4 | [Cost-Variance-and-Control-Protocol.md](foundation/Cost-Variance-and-Control-Protocol.md) | Monitor and Control Finances (Fig. 2-30) |
| 6 | 6.D-5 | [Cost-Domain-Checklist.md](foundation/Cost-Domain-Checklist.md) | §2.4.5 Table 2-8 |

**Management envelope** authority and **amendment log** stay in the **Cost plan**; categories, estimates, staged baseline, control rules, and Table 2-8 evidence stay in **foundation/**.

---

## Upstream inputs & gates

| Input | Requirement |
| --- | --- |
| [Project-Charter.md](../../Project-Charter.md) | Funding limits, Phase 1 financial boundaries |
| [Scope-Management-Plan.md](../Scope-Management-Plan.md) **v1.2+** | WBS / deliverables (**6.A-7** approved, hash `3febf6edd1dbed564df2a8618176d32c42ec19a5d02dcf3ea45b594b70cb33a8`) |
| [Schedule-Management-Plan.md](../Schedule-Management-Plan.md) **v1.2+** | Milestones, timeboxes, pd forecast (**6.B-7** approved, hash `3b6da5f529f68f90133aa17d6b5e8ef84ebf9d332b0279744dad50c5b4b49dba`) |
| [Resource-Capacity-Estimates.md](../resource-baseline/foundation/Resource-Capacity-Estimates.md) | Unit labor rate schedule (€85/h shadow, €0/h cash) |
| [Procurement-Management-Plan.md](../Procurement-Management-Plan.md) | Make-or-Buy analysis & external spend limits (zero temp contractor) |
| [Project-Pillars.md](../../Project-Pillars.md) | **Approved** (episode `8fe9fea9-6ef1-44be-82a9-e09677e47a4a`) |

**6.D-0:** Scope **6.A-7** and Schedule **6.B-7** approved before Cost foundation breakouts (ADR-027 Tier 1: Scope → Schedule → Cost).

---

## Stage 6.D substage checklist (PMBOK §2.4.2)

| Substage | Process / gate | Artifact | Review focus | Done |
| --- | --- | --- | --- | --- |
| **6.D-0** | Upstream | Scope **6.A-7** + Schedule **6.B-7** | Integrated scope + schedule baselines | ☑ |
| **6.D-0P** | Strategy trace | [Cost-Pillar-Overview-and-Trace.md](foundation/Cost-Pillar-Overview-and-Trace.md) | Pillars ↔ cost categories ↔ milestones | ☑ |
| **6.D-1** | Plan Financial Management | [Cost-Categories-and-Estimating-Basis.md](foundation/Cost-Categories-and-Estimating-Basis.md) | Envelope unit, categories, owners, methods | ☑ |
| **6.D-2** | Estimate Costs | [Cost-Estimates-by-Category.md](foundation/Cost-Estimates-by-Category.md) | Estimates + basis; tie to pd / usage | ☑ |
| **6.D-3** | Develop Budget | [Cost-Staged-Budget-and-Baseline.md](foundation/Cost-Staged-Budget-and-Baseline.md) | Staged funding, contingency, cost baseline | ☑ |
| **6.D-4** | Monitor and Control Finances | [Cost-Variance-and-Control-Protocol.md](foundation/Cost-Variance-and-Control-Protocol.md) | CV/CPI thresholds; burn-rate cadence | ☑ |
| **6.D-5** | Domain outcomes | [Cost-Domain-Checklist.md](foundation/Cost-Domain-Checklist.md) | PMBOK §2.4.5 Table 2-8 | ☑ |
| **6.D-6** | Roll-up | **This manifest** | All six artifacts `approved`; registry hashes set | ☑ |
| **6.D-7** | Plan gate | Cost Management Plan **v1.1+** | Integrated baseline; **BFI-004** closed | ☑ |

Recommended order after **6.D-0:** **0P → 1 → 2 → 3 → 4 → 5 → 6 → 7**.

---

## Artifact registry

| artifact_id | Path | substage | version | approval_status | content_hash |
| --- | --- | --- | --- | --- | --- |
| cost-foundation-pillar-overview-trace | `foundation/Cost-Pillar-Overview-and-Trace.md` | 6.D-0P | 1.0.0 | approved | `29907ec05a8b41ce519d526d31a148c62f2d4b7c5c6b39bce351c82d6d85d843` |
| cost-foundation-categories-estimating-basis | `foundation/Cost-Categories-and-Estimating-Basis.md` | 6.D-1 | 1.0.0 | approved | `a037a0a610f242b44d2b813e1c4dfc61a0816e8c0bffc384e85918351722d9ba` |
| cost-foundation-estimates-by-category | `foundation/Cost-Estimates-by-Category.md` | 6.D-2 | 1.0.0 | approved | `066584a33854c96d96e300e54f704753cb2da4da756f7600cc0c4098cb43d48f` |
| cost-foundation-staged-budget-baseline | `foundation/Cost-Staged-Budget-and-Baseline.md` | 6.D-3 | 1.0.0 | approved | `d552c51909ba9ca04477ed7d1f84ea50df0587e97837331c5b68bffa121d2307` |
| cost-foundation-variance-control-protocol | `foundation/Cost-Variance-and-Control-Protocol.md` | 6.D-4 | 1.0.0 | approved | `07133185047257580b17efdb3cc0d8dc14f2869014058b3492cad8576e44b956` |
| cost-foundation-domain-checklist | `foundation/Cost-Domain-Checklist.md` | 6.D-5 | 1.0.0 | approved | `9e097a09453fa9d57d2b786cfc443cb0ca67532ba04f2c689da5a985d4a6ae90` |

---

## Plan gate 6.D-7 (Cost Management Plan)

| | |
| --- | --- |
| **Target** | [Cost-Management-Plan.md](../Cost-Management-Plan.md) **v1.1.0** (`plan_id: cost-management`) |
| **Policy** | `approve-subsidiary-plan` |
| **Upstream deps (ADR-013)** | `scope-management` (**6.A-7** approved, hash `3febf6edd1dbed564df2a8618176d32c42ec19a5d02dcf3ea45b594b70cb33a8`), `schedule-management` (**6.B-7** approved, hash `3b6da5f529f68f90133aa17d6b5e8ef84ebf9d332b0279744dad50c5b4b49dba`) |
| **Pack evidence** | This manifest **6.D-6** ☑; all six registry `content_hash` values set; artifact `approval_status: approved` |

**Entry criteria (all required before 6.D-7):**

1. **6.D-0** — Upstream Scope Management Plan **v1.2.0** approved at **6.A-7** and Schedule Management Plan **v1.2.0** approved at **6.B-7**.
2. **6.D-0P … 6.D-5** — Each foundation artifact breakout-approved; hashes in registry above.
3. **6.D-6** — This manifest checklist ☑ for rows **6.D-0P** through **6.D-5**; `pack_status: approved`.

**Exit criteria (6.D-7 complete):**

1. Subsidiary approval recorded for **Cost Management Plan v1.1+** (canonical content hash per ADR-013).
2. **BFI-004** on the Cost plan set to **`applied`** (Tier-1 foundation pack normative for first approval — Path A, no ADR-027 amendment).
3. Tick **Done** for **6.D-7** in the checklist above.
4. **Authorizes** integrated cost baseline for `PMP-BL-v1.0.0`.
5. **Unblocks** [Procurement-Management-Plan.md](../Procurement-Management-Plan.md) Stage **6.E-0** and downstream Risk Cost dependency in `PLAN_DAG`.

**Approval record:** Episode `72d23862-3d3e-4438-8950-884f06bd0fd0`; canonical Cost Management Plan hash `4abc8f43b5a49cd1b968df4138992ae3900fd77d4168354c5d63218f6e16489b`. The decision covers `PMP-BL-v1.0.0`, manifest v1.1.0, and foundation pack path `cost-baseline/Cost-Foundation-Pack-Manifest.md`.


---

## Amendment log

| Date | Author | Description |
| --- | --- | --- |
| 2026-10-30 | Menno Drescher / Cursor | Initial scaffold: manifest **v1.0.0**, Stage **6.D** checklist, six stub foundation artifacts (PMBOK §2.4.2, ADR-027). |
| 2026-11-01 | Menno Drescher / Antigravity | **v1.1.0 — 6.D-6:** Upstream 6.D-0 verified; foundation breakouts 6.D-0P … 6.D-5 authored with project details and approved; registry hashes set; `pack_status: approved`. |

| 2026-11-01 | Menno Drescher | **6.D-7 complete:** Cost Management Plan v1.1.0 approved by the Project Sponsor; BFI-004 applied; approval Episode `72d23862-3d3e-4438-8950-884f06bd0fd0`. |
