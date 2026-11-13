---
artifact_type: "methodology_guide"
stage: "11"
stage_name: "Audit Record"
pmbok_process: "8.2 Manage Quality Audits"
version: "1.0"
date: "2026-11-12"
owner: "Menno Drescher"
governance_policy: "approve-audit-record (FULL authority)"
---

# Stage 11: Audit Record — Methodology Guide

> **Purpose:** Turn Stage 10's verification evidence into a substantiated audit finding — compliance or non-conformance, classified impact, actionable remediation — recorded in the Audit Register, not an unverified assertion.

> **Alignment:** PMBOK 8 Process 8.2 Manage Quality Audits.

> **Authority:** FULL authority via `approve-audit-record` (3 actions: `approve_audit_record`, `reject_audit_record`, `request_revision_before_decision`).

> **Authority in this repository:** the Sponsor decides every audit record. `approve-audit-record` explicitly checks for substantiated evidence and factual verification — an audit finding that is "unsubstantiated" or "misclassifies governance boundaries" is rejected outright by the policy's own description, not merely flagged.

---

## 1. Overview

### 1.1 Position in the Chain

```
Stage 10 (Verification Evidence) — the test-suite run this stage audits against
    ↓
Stage 11 (Audit Record) — this stage
    ↓
Stage 12 (Actual Outcome) and, eventually, Stage 13-15 (Observation → Insight → Lesson Learned) if the finding becomes a lesson
```

### 1.2 Inputs

| Input | Source | Mandatory |
|---|---|---|
| Verification evidence (Stage 10) | The dated test-suite run | Yes |
| The deliverable and the story it claims to satisfy | The merged PR, the story's acceptance criteria | Yes |

### 1.3 Outputs

| Output | Destination | Governed |
|---|---|---|
| Audit Register entries | `docs/registers/Audit-Register.md` | Yes (via `approve-audit-record`, per entry) |
| Audit Finding (where a dedicated write-up is needed) | A named `AUDIT-NNN` entry/finding | Yes |

### 1.4 Success Criteria

Stage 11 is complete, per audit record, when:
- [ ] The finding cites real evidence (a specific test run, a specific artifact), not an assertion
- [ ] Impact is classified correctly against the governance boundaries it actually crosses
- [ ] A non-conformance names an actionable remediation, not a vague "fix later"
- [ ] `approve-audit-record` has run and the decision is recorded with its episode id

---

## 2. Process

### Step 1: Draft the finding against real evidence

State what was checked, against what standard, using what evidence (a Stage 10 test run, a specific artifact's content). An audit finding that cannot point to real evidence is not ready for submission.

### Step 2: Classify impact

Name whether this is a compliance confirmation or a non-conformance, and which governance boundary it touches (scope, schedule, cost, quality, architecture). A non-conformance also names a remediation action.

### Step 3: Submit for `approve-audit-record`

Run the policy's recommendation, show it to the Sponsor, and wait. On the Sponsor's explicit instruction, run `task-policy-adjudicate` then `task-episode-register`, printing the store path and file count before and after (LL-040).

### Step 4: Record in the register

Append the approved entry to `docs/registers/Audit-Register.md` with its id, date, and episode. A correction to an existing entry is a new dated entry, never an edit that erases the original (the same append-only discipline the Lessons Learned Register follows).

---

## 3. Current Instance (as of 2026-11-12)

`AUDIT-001` to `AUDIT-006` were approved 2026-11-04; `AUDIT-007` to `AUDIT-017` were approved 2026-11-10, episode `198bfc09` (Project-Status-Register.md §1). As of 2026-11-11, Stage 11 is the only one of Stages 10-12 with a real approval gate — Stage 10 is test evidence and Stage 12 is an empirical report, neither governed by a decision policy.

---

## 4. Validation

```bash
grep -n "^## AUDIT-" docs/registers/Audit-Register.md | tail -20
```

---

## 5. Common Pitfalls

| Pitfall | Mitigation |
|---|---|
| An audit finding with no cited evidence | `approve-audit-record` rejects unsubstantiated findings outright |
| Misclassifying which governance boundary a finding crosses | Check against the actual boundary (scope/schedule/cost/quality/architecture), not a convenient label |
| Editing an existing Audit Register entry instead of appending a correction | Append-only; a correction is a new dated entry |

---

## 6. References

- [Intent-to-Outcome Chain Coverage](../../intent-to-outcome-chain-coverage.md) — §2 row 11, §4 `approve-audit-record`
- [Audit-Register.md](../../registers/Audit-Register.md)
- [Stage 10: Verification Evidence Methodology](./Stage-10-Verification-Evidence-Methodology.md)
- [Stage 12: Actual Outcome Methodology](./Stage-12-Actual-Outcome-Methodology.md)

---

## Change Log

| Date | Version | Change |
|---|---|---|
| 2026-11-12 | 1.0 | Initial version, grounded in `docs/policy-shapes/approve-audit-record.actions.json` and the real `AUDIT-001` to `AUDIT-017` entries recorded in Project-Status-Register.md. |
