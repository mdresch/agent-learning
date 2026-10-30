---
artifact_id: scope-foundation-pack-manifest
parent_plan_id: scope-management
baseline_id: PMP-BL-v1.0.0
route: foundation_pack
governance_policy: approve-subsidiary-plan
version: "1.2.0"
owner_role: "Project Manager"
depends_on: []
pack_status: approved
---

# Scope Foundation Pack — Manifest (`PMP-BL-v1.0.0`)

Roll-up for **Stage 6.A** (proactive scope foundation breakouts) before the first `approve-subsidiary-plan` on [Scope-Management-Plan.md](../Scope-Management-Plan.md) **v1.2+**.

**Pack state:** Foundation breakouts **6.A-0P … 6.A-5** **approved** (2026-10-30); registry hashes below. **6.A-6** roll-up complete. **Next:** **6.A-7** — `approve-subsidiary-plan` on [Scope-Management-Plan.md](../Scope-Management-Plan.md) **v1.2.0** and close **BFI-002**.

**Integrated scope baseline (after 6.A-6 + 6.A-7):** approved **this manifest** (registry hashes current) + approved **Scope Management Plan v1.2+** + **six approved foundation artifacts**:

| Substage | Artifact |
| --- | --- |
| 6.A-0P | [Scope-Pillar-Overview-and-Trace.md](foundation/Scope-Pillar-Overview-and-Trace.md) |
| 6.A-1 | [Scope-Project-Scope-Statement.md](foundation/Scope-Project-Scope-Statement.md) |
| 6.A-2 | [Scope-WBS-Dictionary.md](foundation/Scope-WBS-Dictionary.md) |
| 6.A-3 | [Scope-Monitor-Control-Scope.md](foundation/Scope-Monitor-Control-Scope.md) |
| 6.A-4 | [Scope-Validate-Scope.md](foundation/Scope-Validate-Scope.md) |
| 6.A-5 | [Scope-Domain-Checklist.md](foundation/Scope-Domain-Checklist.md) |

Governance and decomposition rules stay in the **Scope plan**; §2.2 evidence stays in **foundation/**.

**Topic pillars:** Strategic scope rolls up to the nine **topic pillars** in [Project-Pillars.md](../../../Project-Pillars.md). The foundation pack ties pillars to WBS bands and Charter milestones in [Scope-Pillar-Overview-and-Trace.md](foundation/Scope-Pillar-Overview-and-Trace.md) (**6.A-0P**). Review that artifact before or with **Define Scope** (6.A-1).

**Upstream gate:** [Project-Charter.md](../../../Project-Charter.md), [Project-Pillars.md](../../../Project-Pillars.md) (**Approved**; `approve-project-pillars` episode `8fe9fea9-6ef1-44be-82a9-e09677e47a4a`), Ideation, and Business Case — no subsidiary plan dependency (Scope is DAG root per ADR-013).

---

## Stage 6.A substage checklist (PMBOK §2.2 processes)

| Substage | Process | Artifact | Review focus | Done |
| --- | --- | --- | --- | --- |
| **6.A-0** | Inputs | Charter + Ideation + Business Case + **Project-Pillars** (Approved) | Strategic scope and pillar model authorized | ☑ |
| **6.A-0P** | **Pillar trace** | [Scope-Pillar-Overview-and-Trace.md](foundation/Scope-Pillar-Overview-and-Trace.md) | Nine topic pillars ↔ bands ↔ M1–M5 | ☑ |
| **6.A-1** | **Define Scope** | [Scope-Project-Scope-Statement.md](foundation/Scope-Project-Scope-Statement.md) | In/out of scope, bands, milestone trace; consistent with 6.A-0P | ☑ |
| **6.A-2** | **Develop Scope Structure** | [Scope-WBS-Dictionary.md](foundation/Scope-WBS-Dictionary.md) | 143 rows, 100% rule, epic parents | ☑ |
| **6.A-3** | **Monitor and Control Scope** | [Scope-Monitor-Control-Scope.md](foundation/Scope-Monitor-Control-Scope.md) | Variance levels, staleness | ☑ |
| **6.A-4** | **Validate Scope** | [Scope-Validate-Scope.md](foundation/Scope-Validate-Scope.md) | DoD, RTM convention | ☑ |
| **6.A-5** | Domain outcomes | [Scope-Domain-Checklist.md](foundation/Scope-Domain-Checklist.md) | Table 2-6 scope outcomes | ☑ |
| **6.A-6** | Roll-up | This manifest | All artifacts approved; checklist ☑ | ☑ |
| **6.A-7** | Plan gate | Scope Management Plan v1.2+ | Integrated baseline; BFI-002 applied or closed | ☐ |

Schedule foundation **6.B-0** requires Scope plan **v1.2+** approved after **6.A-7**.

Epic **13.7** / **34.4** may later automate manifest verification; Path A does not require code.

---

## Plan gate **6.A-7** (Scope Management Plan)

| | |
| --- | --- |
| **Target** | [Scope-Management-Plan.md](../Scope-Management-Plan.md) **v1.2.0** (`plan_id: scope-management`) |
| **Policy** | `approve-subsidiary-plan` |
| **Upstream deps (ADR-013)** | None — Scope is DAG root; initiating inputs per **6.A-0** only |
| **Pack evidence** | This manifest **6.A-6** ☑; all six registry `content_hash` values set; artifact `approval_status: approved` |

**Entry criteria (all required before 6.A-7):**

1. **6.A-0** — Charter, Ideation, Business Case, [Project-Pillars.md](../../../Project-Pillars.md) **Approved** (episode `8fe9fea9-6ef1-44be-82a9-e09677e47a4a`).
2. **6.A-0P … 6.A-5** — Each foundation artifact breakout-approved; hashes in registry below.
3. **6.A-6** — This manifest checklist ☑ for rows **6.A-0P** through **6.A-5**; `pack_status` may move to `approved` at roll-up.

**Exit criteria (6.A-7 complete):**

1. Subsidiary approval recorded for **Scope Management Plan v1.2+** (canonical content hash per ADR-013).
2. **BFI-002** on the Scope plan set to **`applied`** (Tier-1 foundation pack normative for first approval — Path A, no ADR-025 amendment).
3. Tick **Done** for **6.A-7** in the checklist above.
4. **Unblocks** [Schedule-Foundation-Pack-Manifest.md](../schedule-baseline/Schedule-Foundation-Pack-Manifest.md) **6.B-0**.

**Approval notes should cite:** `PMP-BL-v1.0.0`, manifest version, and foundation pack path `scope-baseline/Scope-Foundation-Pack-Manifest.md`.

---

## Artifact registry

| artifact_id | Path | substage | version | approval_status | content_hash |
| --- | --- | --- | --- | --- | --- |
| scope-foundation-pillar-overview-trace | `foundation/Scope-Pillar-Overview-and-Trace.md` | 6.A-0P | 1.0.0 | approved | `5d75fbf70138b266563b7004823015351101555be0678182bbab9db18bcb77e6` |
| scope-foundation-project-scope-statement | `foundation/Scope-Project-Scope-Statement.md` | 6.A-1 | 1.0.0 | approved | `42864ccfcce78aff2a538ed54cb7c6f10e82b21f5e5e726b1a99790136db1027` |
| scope-foundation-wbs-dictionary | `foundation/Scope-WBS-Dictionary.md` | 6.A-2 | 1.0.0 | approved | `bb482a54a653335fff94830b71524986b5f972421503e492f9ce6c6d027291bb` |
| scope-foundation-monitor-control-scope | `foundation/Scope-Monitor-Control-Scope.md` | 6.A-3 | 1.0.0 | approved | `0f56e3548c3ba9e4f4ca6298b09c08352a024aa7e56e44014ad21cdee07c7e3a` |
| scope-foundation-validate-scope | `foundation/Scope-Validate-Scope.md` | 6.A-4 | 1.0.0 | approved | `1cbf218988a1ebf90edc46b8bc8b95e3e5918e154845b13aa1475a02acb78d1f` |
| scope-foundation-domain-checklist | `foundation/Scope-Domain-Checklist.md` | 6.A-5 | 1.0.0 | approved | `271f9d4aa1138f079a4de5c7582392f1946d2d0b34a5853dd31c90155868b530` |

---

## Approval runbook (Path A)

1. Confirm **6.A-0** initiating inputs are Accepted.
2. Breakout **6.A-0P**, then **6.A-1 … 6.A-5** (one episode per artifact or one batch with per-file disposition).
3. Update artifact frontmatter and registry hashes; tick checklist.
4. **6.A-6** when all **six** foundation artifacts are approved.
5. `approve-subsidiary-plan` on **Scope Management Plan v1.2+** (**6.A-7**).
6. Close **BFI-002** on the Scope plan when 6.A-7 completes.

Then proceed to Schedule foundation **6.B** (depends on approved Scope).

---

## Amendment log

| Date | Author | Description |
| --- | --- | --- |
| 2026-10-30 | Menno Drescher / Cursor | Initial scope foundation pack (§2.2 processes); Path A, no ADR-025 amendment. |
| 2026-10-30 | Menno Drescher / Cursor | Added **6.A-0P** pillar overview & trace linked to [Project-Pillars.md](../../../Project-Pillars.md). |
| 2026-10-30 | Menno Drescher | [Project-Pillars.md](../../../Project-Pillars.md) marked **Approved**; upstream gate and 6.A-0 checklist updated. |
| 2026-10-30 | Menno Drescher / Cursor | **v1.1.0** — Integrated baseline table; **§ Plan gate 6.A-7** (entry/exit, BFI-002, unblocks Schedule **6.B-0**). |
| 2026-10-30 | Menno Drescher | **v1.2.0 — 6.A-6:** Foundation **6.A-0P … 6.A-5** approved; registry hashes recorded; `pack_status: approved`. |
