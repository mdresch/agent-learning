---
pmbok_edition: "PMBOK 8"
pmbok_domain: "Stakeholders"
process: "13.1 Identify Stakeholders & 13.2 Plan Stakeholder Engagement"
artifact_id: "stakeholder-register"
version: "2.0"
date: "2026-11-08"
phase: "Phase 2"
status: "approved"
pmp_baseline: "PMP-BL-v1.0.1"
target_pmp_baseline: "PMP-BL-v1.1.0"
owner_role: "Project Manager"
sponsor: "Menno Drescher"
---

# Master Stakeholder Register — agent-learning Phase 2

**Artifact ID:** `stakeholder-register`  
**Version:** 2.0  
**Phase:** Phase 2: Autonomous Feedback Loops & Extensible Architecture  
**PMP Baseline:** Governed under `PMP-BL-v1.0.1` (Patch Baseline); Targeting `PMP-BL-v1.1.0` (Minor Increment Baseline).  
**Effective Date:** 2026-11-08  
**Accountable Role:** Project Manager / PMBOK Steward  
**Approving Sponsor:** Menno Drescher (Project Sponsor & Maintainer)  
**Normative Standards:** [ADR-012](../adr/ADR-012-subsidiary-management-plan-standards-and-content-contracts.md), [ADR-031](../adr/ADR-031-stakeholder-engagement-plan-standard.md), [Project-Charter.md](Project-Charter.md) §4 & §5.  
**Related Subsidiary Plan:** [`docs/project-docs/management-plans/Stakeholder-Engagement-Plan.md`](management-plans/Stakeholder-Engagement-Plan.md)  

---

## 1. Executive Summary & Sovereign Agency Mandate

This Master Stakeholder Register establishes the authoritative vocabulary of project roles, engagement strategies, and decision authorities for **Phase 2: Autonomous Feedback Loops & Extensible Architecture**.

In strict accordance with [Project-Charter.md](Project-Charter.md) §5, **Pillar I (Cybernetic Closed-Loop Feedback)**, and **Pillar II (Democratic Epistemics)**:
1. **Sovereign Human Agency:** Autonomous agents execute code generation, mathematical analysis, and regression verification, but **statistical confidence is never permitted to usurp human authority** over architecture baselines, resource commitments, or phase progression (ADR-001, ADR-008 Invariant #4).
2. **Authoritative Role Vocabulary:** In alignment with ADR-031 §4.2, all role names defined in this register serve as the sole authoritative vocabulary for `owner_role` specifications across all project management plans, work packages, and governance gates.
3. **Data Minimization:** Strictly complies with ADR-031 §5 (Invariant #3). Only project roles, organizational units, and public repository handles (`@github_handle`) are recorded; private personal data is excluded.

---

## 2. Master Stakeholder Register Contract (Phase 2)

| Identifier | Role / Name | Organization / Team | Phase 2 Project Responsibilities | Power / Influence | Interest | Current Level | Desired Level | Primary Communication Channel |
|---|---|---|---|---|---|---|---|---|
| **SH-01** | **Menno Drescher** | Project Leadership / Maintainer | Project Sponsor, Principal Maintainer, MPN Liaison to Microsoft. Sole approval authority for Charter, PMP Baselines, and Phase Close decisions. | **High** | **High** | Leading | Leading | GitHub (`@MennoDrescher`), Direct Session Dialogue |
| **SH-02** | **Project Manager** | Project Governance | PMBOK 8 Process Steward. Accountable for Scope, Schedule, Cost baselines, phase rollups, and zero status drift across registers. | **High** | **High** | Leading | Leading | GitHub Issues, PM Artifacts |
| **SH-03** | **Lead Agent Engineer (Antigravity)** | AI Engineering | AI Engineering Pair Assistant. Executes module design, pure stdlib implementation in `agent-training-ext/`, and contract test suites. | **Low (Exec)** | **High** | Supportive | Supportive | Antigravity Task Prompts & Workspace Tasks |
| **SH-04** | **PR Reviewers & Code Adjudicators** | Technical Reviewers | Qualitative review adjudicators. Employs critique tag grammar to translate review findings into Bayesian evidence frames without losing nuance. | **Medium** | **High** | Neutral | Supportive | GitHub PR Reviews, Tag Grammar CLI |
| **SH-05** | **Downstream SDK Adopters & Developers** | Open Source Community | Consumers of discrete policy learning, DPO preference optimization, and contextual bandit algorithms in downstream agent systems. | **Low** | **High** | Neutral | Supportive | GitHub Discussions, Documentation, PyPI Releases |
| **SH-06** | **Upstream Microsoft Maintainers (`microsoft/agent-learning`)** | Microsoft OSS / Upstream | Authors and maintainers of upstream repository (`MargoOs`, `adityasinha-aiplan`, `meiwa7`). Key concern: zero merge conflicts on upstream sync. | **High (Veto)** | **Medium** | Neutral | Supportive | Upstream GitHub PRs / Issues, MPN Channel |
| **SH-07** | **Quality & Governance Auditor** | Compliance & Quality Assurance | Verifies 4-ring test coverage, pure stdlib isolation, and zero status drift in `phase_rollup.py --check`. Audits `Audit-Register.md`. | **Medium** | **High** | Supportive | Leading | GitHub Actions CI, Pytest Reports, Audit Logs |

---

## 3. Classification & Influence / Interest Assessment Grid

Stakeholders are mapped across a $2 \times 2$ Power (Influence) vs. Interest grid to determine engagement protocols:

```
        ▲ High
        │   [KEEP SATISFIED]                     [MANAGE CLOSELY]
        │   • Upstream Microsoft Maintainers      • Project Sponsor & Maintainer (Menno)
  P     │     (`microsoft/agent-learning`)        • Project Manager / PMBOK Steward
  O     │                                         • PR Reviewers & Code Adjudicators
  W     │
  E     │   [MONITOR]                            [KEEP INFORMED]
  R     │   • Indirect Community Observers        • Lead Agent Engineer (Antigravity)
        │                                         • Quality & Governance Auditor
        │                                         • Downstream SDK Adopters & Developers
        └──────────────────────────────────────────────────────────────────────────►
          Low                               INTEREST                            High
```

### Scale Definitions
* **Power / Influence:**
  * *High:* Sovereign approval authority, architectural veto power, or upstream merge gatekeeper.
  * *Medium:* Quality gate blockers, peer review adjudicators, or compliance veto holders.
  * *Low:* Execution-only entities or downstream consumers without direct project governance authority.
* **Interest:**
  * *High:* Directly affected by milestone deliverables, codebase architecture, or scientific hypothesis resolution.
  * *Medium:* Interested in compatibility, release stability, and upstream cleanliness.
  * *Low:* Casual observers or general open-source consumers.

---

## 4. Stakeholder Engagement Assessment Matrix (SEAM)

The matrix identifies the current ($C$) versus desired ($D$) engagement posture for Phase 2:

| Stakeholder Role | Unaware | Resistant | Neutral | Supportive | Leading | Planned Gap Action |
|---|:---:|:---:|:---:|:---:|:---:|---|
| **SH-01: Project Sponsor (Menno)** | | | | | $C, D$ | Maintain leading posture via transparent decision frames and Bayesian gate episodes. |
| **SH-02: Project Manager** | | | | | $C, D$ | Maintain leading posture via automated phase rollups and zero-drift verification. |
| **SH-03: Lead Agent Engineer** | | | | $C, D$ | | Maintain supportive execution under maintainer review; preserve pure stdlib boundaries. |
| **SH-04: PR Reviewers & Adjudicators** | | | $C$ | $D$ | | Deploy tag grammar CLI to make qualitative critique tagging effortless and high-value. |
| **SH-05: Downstream SDK Adopters** | | | $C$ | $D$ | | Deliver clear documentation, isolated extension packaging, and verified example notebooks. |
| **SH-06: Upstream Microsoft Maintainers** | | | $C$ | $D$ | | Maintain pristine `src/agent_learning` diff; route non-invasive proposals via MPN channel. |
| **SH-07: Quality & Governance Auditor** | | | | $C$ | $D$ | Automate gate audits in CI/CD pipeline with explicit JSON decision records. |

*Legend: $C$ = Current Engagement Level; $D$ = Desired Engagement Level.*

---

## 5. Phase 2 Targeted Engagement & Gap-Closing Protocols

| Stakeholder Role | Identified Gap | Targeted Strategic Action | Action Owner | Target Milestone | Falsification / Success Metric |
|---|---|---|---|---|---|
| **SH-04: PR Reviewers** | Neutral $\to$ Supportive | Provide pre-calibrated rubric tags (`[claim: logic error] [verified: yes]`) in `agent-training-ext` CLI so reviewers tag PRs in $< 30$ seconds. | Lead Agent Engineer | Milestone M6 | $\ge 80\%$ of review comments parsed successfully without manual logit calculation. |
| **SH-05: Downstream Adopters** | Neutral $\to$ Supportive | Publish decoupled user guides for DPO training and contextual bandits with zero GPU setup requirements. | Project Manager | Milestones M7 & M8 | Working examples run cleanly on stock Python 3.10+ environments. |
| **SH-06: Upstream Maintainers** | Neutral $\to$ Supportive | Maintain `src/agent_learning` as 100% clean diff against upstream; isolate all extensions in `agent-training-ext/`. | Lead Agent Engineer | Continuous (M6–M10) | `git diff upstream/main -- src/agent_learning` produces 0 lines of diff. |
| **SH-07: Governance Auditor** | Supportive $\to$ Leading | Enforce automated verification of `phase_rollup.py --check` in pre-commit and PR workflows. | Quality Auditor | Milestone M6 | Zero status drift rows across all 18 lifecycle documents. |

---

## 6. Stakeholder Decision Rights & RACI Matrix

In alignment with PMBOK 8 Governance standards, ADR-012, ADR-025, and ADR-031 §4.2:

| Project Decision / Lifecycle Stage | SH-01 (Sponsor) | SH-02 (PM) | SH-03 (Agent) | SH-04 (Reviewers) | SH-05 (Adopters) | SH-06 (Upstream) | SH-07 (Auditor) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Project Charter & Strategic Intent (Stages 1–4)** | **Accountable (A)** | Responsible (R) | Consulted (C) | Informed (I) | Informed (I) | Informed (I) | Informed (I) |
| **Stakeholder Register & Engagement Plan (Stage 5)** | **Accountable (A)** | Responsible (R) | Consulted (C) | Consulted (C) | Informed (I) | Consulted (C) | Consulted (C) |
| **Scope Baseline & Technical Specs (Stage 6)** | **Accountable (A)** | Responsible (R) | Responsible (R) | Consulted (C) | Informed (I) | Consulted (C) | Consulted (C) |
| **Integrated PMP Baseline (`PMP-BL-v1.1.0`) (Stage 7)** | **Accountable (A)** | Responsible (R) | Consulted (C) | Consulted (C) | Informed (I) | Informed (I) | Consulted (C) |
| **Implementation Readiness Authorization (Stage 8)** | **Accountable (A)** | Responsible (R) | Consulted (C) | Consulted (C) | Informed (I) | Informed (I) | Consulted (C) |
| **Code Implementation & Contract Tests (Stage 9–10)** | Informed (I) | Consulted (C) | **Responsible (R)** | Consulted (C) | Informed (I) | Informed (I) | Responsible (R) |
| **Quality Audit Records (Stage 11)** | **Accountable (A)** | Consulted (C) | Consulted (C) | Consulted (C) | Informed (I) | Informed (I) | **Responsible (R)** |
| **Adaptive Feedback & Intent Refinement (Stages 12–18)** | **Accountable (A)** | Responsible (R) | Responsible (R) | Consulted (C) | Consulted (C) | Consulted (C) | Consulted (C) |

*RACI Definition: **R**esponsible = Executes work; **A**ccountable = Sovereign decision authority (sole approver); **C**onsulted = Two-way feedback; **I**nformed = One-way status notification.*

---

## 7. Maintenance, Review Cadence & Privacy Controls

1. **Review Cadence:**
   - Formal audit at every milestone boundary (M6, M7, M8, M9, M10).
   - Dynamic update whenever a new maintainer, core contributor, or external organization interfaces with the project.
   - Comprehensive reconciliation at Phase 2 Close (Stage 18).
2. **Change Control Protocol:**
   - Minor contact channel or organizational changes are submitted via standard PR reviewed by the Project Manager.
   - Any changes to decision authority, role addition/removal, or RACI allocations require formal approval by Project Sponsor Menno Drescher.
3. **Data Privacy Assurance (ADR-031 §5):**
   - The register shall contain no personally identifiable private data (PII).
   - Only public professional handles and repository roles are recorded.

---

## Provenance & Completeness Assessment

| Dimension | Verification Status | Notes |
|---|---|---|
| **Authoritative Roles (§2)** | **Complete** | Defines 7 unambiguous stakeholder groups mapping internal, upstream, and community roles. |
| **Sovereign Human Agency (§1)** | **Enforced** | Codifies strict human supremacy over architecture and baseline decisions (ADR-001/008). |
| **Fork Protection Alignment (§5)** | **Aligned** | Explicitly establishes upstream Microsoft maintainer engagement to prevent fork collisions. |
| **RACI Matrix (§6)** | **Exhaustive** | Maps decision authority across all 18 lifecycle stages in PMBOK 8 terminology. |
| **Data Minimization (§7)** | **Compliant** | Zero private personal data recorded; uses public handles only. |
