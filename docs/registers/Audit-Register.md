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
| Date | 2026-11-10 |
| Status | Active. First audit run 2026-11-04 (AUDIT-001 to AUDIT-006), bounded sample, approved by Menno on 2026-11-04 via `approve-audit-record` (robust utility 0.682, episode `42114091-0ccd-4c45-9b6b-c97046b048bd`). Second run, AUDIT-007 to AUDIT-017, approved by Menno on 2026-11-10 via `approve-audit-record` (robust utility 0.699, expected utility 0.775, episode `198bfc09-34ae-4ad7-b8f1-d96eb2ec89a3`). |
| Source | Instantiated from sidpa-template `docs/registers/Audit-Register.template.md` (commit `e97e8a3`). No audit-sampling rationale yet. |

**Entries are added only when a real audit happens, never backfilled.** The first audit ran on 2026-11-04 at git `f86530a` (prospective: the ADR claims were checked against the code on that date). It is a bounded sample: four ADRs (015, 019, 020, 034) and the story-status drift report. The other ADRs were not audited and nothing here says they are accurate. The findings are an AI reading of the code, accepted by the human at the `approve-audit-record` gate on 2026-11-04.

**Second audit run (2026-11-10, Phase 2 close).** Prospective, at git `51ef83d`: AUDIT-007 to AUDIT-017 check one or two stated invariants for each of ADR-014, 016, 018, 021, 022 and 038, one follow-up on ADR-034, and the verification process. It is a bounded sample and says nothing about invariants not listed. The findings are an AI reading of the code, approved by Menno on 2026-11-10 via `approve-audit-record` (episode `198bfc09-34ae-4ad7-b8f1-d96eb2ec89a3`); the 2026-11-04 approval covers AUDIT-001 to AUDIT-006 only. Every corrective action is rolled into Phase 3 (IMP-053 to IMP-057).

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
| AUDIT-007 | ADR-016 | IV | Invariant 1 (no RNG in selection): `src/agent_learning_ext/policy/ucb.py` and `learners/ucb.py` import no `random` or `secrets` (search found none). | confirmed_accurate | Epic 16 |
| AUDIT-008 | ADR-016 | IV | Invariant 4 (runs under `DecisionAuthority.LOW`): neither UCB module mentions authority, and `cli.py` has no UCB entry point, so no code path shows the claim. Corrective action: a human decides whether Invariant 4 is design intent or must be enforced when UCB is wired to a TaskPolicy. | unauditable | Epic 16, IMP-054 |
| AUDIT-009 | ADR-018 | IV | Invariants 3 and 5: `learners/pairwise.py` declares `LAMBDA_MIN = 0.05` and `CLAMP = 8.0`, matching the regularization floor and the logit clamp. The constants were found; each use site was not traced. | partially_confirmed | Epic 18, IMP-055 |
| AUDIT-010 | ADR-021 | IV | Invariant 6 (hysteresis deadband of at least 0.15 bits): `routing.py` declares `MIN_GAP_BITS = 0.15`. | confirmed_accurate | Epic 21 |
| AUDIT-011 | ADR-021 | IV | Invariant 5 (pinned gates): all 18 tasks in `PINNED_FULL` are now named in ADR-021. Until 2026-11-10 the ADR named 11 and `PINNED_FULL` held 11; Story 21.7 found 5 more recorded gates, and a follow-up found 2 more with policy shapes. Both were corrected by Stage 16 correction notes (IMP-046). | confirmed_with_drift | IMP-046, Story 21.7 |
| AUDIT-012 | ADR-014 | IV | Invariant 2 (pooled-support target clipped to [1e-6, 1 - 1e-6]): `critique_evidence.py` declares `TARGET_EPSILON = 1e-6`. | confirmed_accurate | Epic 14 |
| AUDIT-013 | ADR-022 | IV | Invariant 2 (weights non-negative and sum to 1.0): `weight_compiler.py` requires every weight to be at least the step of 0.05 and the sum to be 1.0 within 1e-9. The code is stricter than the ADR's `w_i >= 0.0`. Corrective action: a human decides whether the ADR wording or the code floor is intended. | confirmed_with_drift | Epic 22, IMP-053 |
| AUDIT-014 | ADR-022 | IV | Invariant 5 (holdout acceptance): the ADR says proposed only if holdout accuracy is "at least" the weights in force. The code (`weight_compiler.py` line 553) accepts only when it is strictly greater, and its docstring cites FDD-022 section 3.6. The ADR and the FDD disagree; the code follows the FDD. Corrective action: a Stage 16 correction note to ADR-022, on the human's decision. | confirmed_with_drift | Epic 22, IMP-053 |
| AUDIT-015 | ADR-038 | IV | Invariant 6 (`--feature-dim` on a full-authority init is refused): `cli.py` raises "--feature-dim creates a low-authority contextual policy and cannot be ..." (line 1113). | confirmed_accurate | Epic 38 |
| AUDIT-016 | ADR-034 | IV | Follow-up to AUDIT-004, unchanged: top-level `pmbok/` still has 23 entries, CI still runs `pytest --ignore=tests/pmbok` (`.github/workflows/tests.yaml` line 42), and `cli.py` has no `pmbok` command. Still tracked as blocked Stories 34.4 and 34.5. The local full run, which has no `--ignore`, passes. | confirmed_with_drift | Stories 34.4, 34.5, IMP-056 |
| AUDIT-017 | Story process | IV | Verification evidence: the log shows a failing-first (RED) run for 7 of 7 stories in Epic 21 and 6 of 6 in Epic 38, but for 1 of 6 in Epic 18, 1 of 7 in Epic 22, and none of 18 in Epics 14, 16 and 17 (a loose text search of `implementation-log.md`, so an indication, not a count). Corrective action: none retroactive; the practice is carried forward as a lesson. | confirmed_with_drift | Stage 10, LL-003, IMP-057 |

**Verdict taxonomy** (matches `classify-audit-finding`'s real action set, once this project has evidence to build that policy — see "Governance Exercises" below for the parallel reasoning): `confirmed_accurate`, `confirmed_with_drift`, `partially_confirmed`, `contradicted`, `stale_superseded`, `unauditable`, `flag_for_human_review`.

## Governance Exercises

A distinct sub-type from the ADR-accuracy audits above — these check a real-world prerequisite or claim against production reality, not an ADR's accuracy against code. This is also where a story that turns out not to be code-shaped gets reclassified to (see `Story-Execution-Register.template.md`), rather than forcing it into a lighter-weight story variant.

| ID | Checks | Status | Blocker |
|---|---|---|---|
| *(empty — first real exercise gets GOV-EX-001)* | | | |

## Building `classify-audit-finding` for this project

ADPA's own version of this policy was built only after a real finding (AUDIT-001) existed — not before. If this project accumulates more than one real audit finding and the verdict categories above start to feel repetitive rather than freshly reasoned each time, that's the real signal to build the policy — cite it in `docs/root-cause-log.md` when you do, the same way every other policy in this chain traces back to a real trigger.
