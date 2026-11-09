---
artifact_id: cost-foundation-pack-manifest
parent_plan_id: cost-management
baseline_id: PMP-BL-v1.1.0
route: foundation_pack
governance_policy: approve-subsidiary-plan
version: "2.0.0"
owner_role: "Project Manager"
depends_on:
  - scope-management
  - schedule-management
pack_status: approved
---

# Cost Foundation Pack — Manifest (`PMP-BL-v1.1.0`)

Roll-up for **Stage 6.D** (proactive cost foundation breakouts) for Phase 2 under `PMP-BL-v1.0.1` targeting minor baseline increment `PMP-BL-v1.1.0`.

**Historical Baseline Archive:** Frozen Phase 1 manifest preserved in [`docs/project-docs/history/PMP-BL-v1.0.0/management-plans/cost-baseline/Cost-Foundation-Pack-Manifest.md`](../../history/PMP-BL-v1.0.0/management-plans/cost-baseline/Cost-Foundation-Pack-Manifest.md).

**Pack State:** Upstream Scope and Schedule baselines verified complete. Foundation breakouts **6.D-0P … 6.D-5** updated and **approved** for Phase 2; registry hashes recorded below. **6.D-6** roll-up complete. **6.D-7** subsidiary approval formalizes the Phase 2 Cost Baseline on [Cost-Management-Plan.md](../Cost-Management-Plan.md) **v2.0.0**.

**Integrated Cost Baseline (`PMP-BL-v1.1.0`):**
Approved **this manifest** (v2.0.0) + approved **Cost Management Plan v2.0.0** + **six approved foundation artifacts**:

| Substage | Artifact | Role in Phase 2 Cost Baseline |
|---|---|---|
| **6.D-0P** | [Cost-Pillar-Overview-and-Trace.md](foundation/Cost-Pillar-Overview-and-Trace.md) | Maps Phase 2 financial boundaries and GPU spend avoidance to topic pillars |
| **6.D-1** | [Cost-Categories-and-Estimating-Basis.md](foundation/Cost-Categories-and-Estimating-Basis.md) | Cost Breakdown Structure (CBS), units of measure, and precision standards |
| **6.D-2** | [Cost-Estimates-by-Category.md](foundation/Cost-Estimates-by-Category.md) | Bottom-up milestone estimates across M6–M10 (€15,550 base / €250 cash) |
| **6.D-3** | [Cost-Staged-Budget-and-Baseline.md](foundation/Cost-Staged-Budget-and-Baseline.md) | Time-phased budget baseline (€19,175 economic / €300 max cash envelope) |
| **6.D-4** | [Cost-Variance-and-Control-Protocol.md](foundation/Cost-Variance-and-Control-Protocol.md) | Weekly EVM equations ($CV, CPI, EAC$) and 3-tier variance tolerance bands |
| **6.D-5** | [Cost-Domain-Checklist.md](foundation/Cost-Domain-Checklist.md) | PMBOK 8 §2.4.5 Table 2-8 Finance Performance Domain check sign-off |

---

## Artifact Registry (Phase 2 Canonical Hashes)

| artifact_id | Path | substage | version | approval_status | content_hash |
|---|---|:---:|:---:|:---:|---|
| cost-foundation-pillar-overview-trace | `foundation/Cost-Pillar-Overview-and-Trace.md` | 6.D-0P | 2.0.0 | approved | `bac41825904a2a98159e1a0eddbc56205833461400f0d717e022597b976ce94a` |
| cost-foundation-categories-estimating-basis | `foundation/Cost-Categories-and-Estimating-Basis.md` | 6.D-1 | 2.0.0 | approved | `d35a9220a8419c0cf20d6f469d8f082f267e64e1a9c70e9d44903defccde273c` |
| cost-foundation-estimates-by-category | `foundation/Cost-Estimates-by-Category.md` | 6.D-2 | 2.0.0 | approved | `c532708e87dc51fba9b4b427d4b82a4c4688c11ce2f1a4fdab1c6ebc8cf0172e` |
| cost-foundation-staged-budget-baseline | `foundation/Cost-Staged-Budget-and-Baseline.md` | 6.D-3 | 2.0.0 | approved | `5c5b670771394b7a4abd2221f3123a13454ba33d207e8a31c8a1286a35f30e4b` |
| cost-foundation-variance-control-protocol | `foundation/Cost-Variance-and-Control-Protocol.md` | 6.D-4 | 2.0.0 | approved | `3c122a7588bc89ff70ca886c383a066f17e977357b9e79f1cc164a9285e45482` |
| cost-foundation-domain-checklist | `foundation/Cost-Domain-Checklist.md` | 6.D-5 | 2.0.0 | approved | `97c6a658a0a32e7c95d6b84ea70cbd29dae1df1b58ea1682cca63156987c82e6` |
