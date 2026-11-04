---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Monitoring & Controlling"
pmbok_process: "8.2 Manage Quality & 8.3 Control Quality Audits"
lifecycle_stage: "Stage 11 (Audit Record)"
governance_policy: "approve-audit-record"
inputs:
  - "Deliverables (Source code)"
  - "Verification Evidence (Contract test runs)"
  - "Telemetry"
process: "Perform compliance audits, identify drift or regressions, document corrective actions"
outputs:
  - "Audit-Register.md"
  - "Approved Audit Findings"
---

# Audit Register — agent-learning

> **PMBOK 8 Process:** `8.2 Manage Quality & 8.3 Control Quality Audits` (Monitoring & Controlling)  
> **Governance Policy:** `approve-audit-record` | **Lifecycle Stage:** `Stage 11 (Audit Record)`  
> **Inputs:** Deliverables (Source code), Verification Evidence (Contract test runs), Telemetry  
> **Process:** Perform compliance audits, identify drift or regressions, document corrective actions  
> **Outputs:** Audit-Register.md, Approved Audit Findings


| Field | Value |
|---|---|
| Version | 1.0 (live — accumulates as audits actually run) |
| Date | 2026-11-04 |
| Status | Active. First audit run 2026-11-04 (AUDIT-001 to AUDIT-006), bounded sample, approved by Menno on 2026-11-04 via `approve-audit-record` (robust utility 0.682, episode `42114091-0ccd-4c45-9b6b-c97046b048bd`). |
| Source | Instantiated from sidpa-template `docs/registers/Audit-Register.template.md` (commit `e97e8a3`). No audit-sampling rationale yet. |

**Entries are added only when a real audit happens, never backfilled.** The first audit ran on 2026-11-04 at git `f86530a` (prospective: the ADR claims were checked against the code on that date). It is a bounded sample: four ADRs (015, 019, 020, 034) and the story-status drift report. The other ADRs were not audited and nothing here says they are accurate. The findings are an AI reading of the code, accepted by the human at the `approve-audit-record` gate on 2026-11-04.

Centralized, not scattered. Every real audit finding (an ADR's accuracy checked against actual code) and every real Governance Exercise (a real-world prerequisite or claim checked against production reality) lives here once, with a stable ID — other documents **reference** the ID rather than copying the finding into their own text.

This register is conceptually distinct from governance-type documents (the policy/baseline itself) — this is the record of checking reality against that baseline.

## ADR-accuracy audits

| ID | ADR | Pillar | Finding | Verdict | Referenced by |
|---|---|---|---|---|---|
| AUDIT-001 | ADR-015 | IV | Seed and posterior parameters are recorded for replay (`policy/thompson.py` `seed_for`, `replay`); the 5000 ceiling is `N_MAX`, applied in `learners/thompson.py`. | confirmed_accurate | Epic 15 |
| AUDIT-002 | ADR-019 | IV | Each member's `role_map` must be a bijection and the compiler never infers it (`meta_prior.py` validation). | confirmed_accurate | Epic 20 |
| AUDIT-003 | ADR-020 | IV | Damping must be in (0, 1]; non-finite, bool and out-of-range values are refused (`warm_start.py`). | confirmed_accurate | Epic 20 |
| AUDIT-004 | ADR-034 | IV | §6.2 and Invariants 3 and 5 are not yet true: top-level `pmbok/` still has 23 entries; `scripts/orchestrate_pmbok.py` and `tests/pmbok` import it; CI runs `pytest --ignore=tests/pmbok`; `cli.py` has no `pmbok` command. Already tracked as blocked Stories 34.4 and 34.5. | confirmed_with_drift | Stories 34.4, 34.5 |
| AUDIT-005 | ADR-034 | IV | Invariants 1 and 2 hold: none of `sqlalchemy`, `fastapi`, `typer`, `tenacity`, `pytesseract`, `pdf2image`, `pillow` is in `pyproject.toml`, and `src/` has no SQLite use. | confirmed_accurate | none |
| AUDIT-006 | Story status | IV | `phase_rollup.py --check` reports 15 stories with status drift: 1.1 and 9.3 marked Completed with no log entry; 3.1, 4.1, 6.1, 26.1, 34.1 to 34.3 and 36.1 to 36.6 logged but not marked Completed. Corrective action: a human reconciles each status line; not done here. | confirmed_with_drift | IMP-011, LL-041 |

**Verdict taxonomy** (matches `classify-audit-finding`'s real action set, once this project has evidence to build that policy — see "Governance Exercises" below for the parallel reasoning): `confirmed_accurate`, `confirmed_with_drift`, `partially_confirmed`, `contradicted`, `stale_superseded`, `unauditable`, `flag_for_human_review`.

## Governance Exercises

A distinct sub-type from the ADR-accuracy audits above — these check a real-world prerequisite or claim against production reality, not an ADR's accuracy against code. This is also where a story that turns out not to be code-shaped gets reclassified to (see `Story-Execution-Register.template.md`), rather than forcing it into a lighter-weight story variant.

| ID | Checks | Status | Blocker |
|---|---|---|---|
| *(empty — first real exercise gets GOV-EX-001)* | | | |

## Building `classify-audit-finding` for this project

ADPA's own version of this policy was built only after a real finding (AUDIT-001) existed — not before. If this project accumulates more than one real audit finding and the verdict categories above start to feel repetitive rather than freshly reasoned each time, that's the real signal to build the policy — cite it in `docs/root-cause-log.md` when you do, the same way every other policy in this chain traces back to a real trigger.
