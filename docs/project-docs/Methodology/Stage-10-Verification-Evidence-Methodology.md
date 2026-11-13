---
artifact_type: "methodology_guide"
stage: "10"
stage_name: "Verification Evidence"
pmbok_process: "8.3 Control Quality"
version: "1.0"
date: "2026-11-12"
owner: "Menno Drescher"
governance_policy: "none — the executable contract test suite is the evidence (input evidence, no decision policy)"
---

# Stage 10: Verification Evidence — Methodology Guide

> **Purpose:** Produce the one thing every later stage treats as ground truth about whether a deliverable actually works: a passing (or failing, named) run of the contract test suite.

> **Alignment:** PMBOK 8 Process 8.3 Control Quality.

> **Authority:** No TaskPolicy decides here. `docs/intent-to-outcome-chain-coverage.md` §2 row 10 names this stage's role as "Input Evidence" — the executable test suite itself, not a human or agent judgment. Stage 11 (Audit Record) is the first point a decision policy runs against this evidence.

---

## 1. Overview

### 1.1 Position in the Chain

```
Stage 9 (Deliverable) — the code and its own contract tests
    ↓
Stage 10 (Verification Evidence) — this stage — the whole suite's run
    ↓
Stage 11 (Audit Record) — approve-audit-record judges conformance against this evidence
```

### 1.2 Inputs

| Input | Source | Mandatory |
|---|---|---|
| The code deliverable and its contract tests | The merged PR from Stage 9 | Yes |
| The whole test suite (not just the story's own tests) | `tests/` | Yes |

### 1.3 Outputs

| Output | Destination | Governed |
|---|---|---|
| Test run result (pass count, skip count, failures) | CI output, cited in the relevant Status Report | No — it is evidence, not a governed document itself |
| A Verification Evidence note, where one phase's close needs it written down | `docs/project-docs/Status-Reports/Stage-10-Verification-Evidence-*.md` | No |

### 1.4 Success Criteria

Stage 10 is healthy when:
- [ ] The whole suite runs with `uv run pytest` and no `--ignore` flags, not a curated subset
- [ ] The pass/fail/skip counts are cited with the date they were taken (counts drift; a stale count misreports current state)
- [ ] A failure is named and routed (to Stage 9 for a fix, or to `heal-contract-failure` if it is a contract defect), not silently re-run until green

---

## 2. Process

### Step 1: Run the whole suite

```bash
uv run pytest
```
No `--ignore` flags by default (per this project's own standing rule — the whole suite, every time). A narrower run is for local iteration only, never the evidence cited in a Status Report or Audit Record.

### Step 2: Record the result with its date

Cite the pass/skip/fail counts with the date the run happened, in the Status Report or episode that depends on it. A number without a date is stale the moment anything else changes — do not let an old count stand in for "the suite is currently green."

### Step 3: Route a failure

A failing test traces either to Stage 9 (the deliverable needs fixing) or, if the failure reveals a contract itself was wrong, to `heal-contract-failure`. Verification Evidence records the failure; it does not interpret it.

### Step 4: Hand off to Stage 11

Stage 11's Audit Record cites this stage's evidence directly — it does not re-run the suite itself, it judges conformance against the recorded result.

---

## 3. Current Instance (as of 2026-11-12)

Project-Status-Register.md records, as of 2026-11-11: **2,723 passed, 2 skipped**. Treat this as a dated snapshot, not a durable fact — re-run the suite rather than citing this number once meaningful time or changes have passed.

---

## 4. Validation

```bash
uv run pytest                                  # the whole suite, no --ignore
uv run pytest -q --tb=no                       # quick pass/fail/skip count only
```

---

## 5. Common Pitfalls

| Pitfall | Mitigation |
|---|---|
| Citing a pass count without its date | Always date-stamp a cited test-suite count |
| Running a curated subset and calling it "the suite passes" | The whole suite, no `--ignore`, is the only evidence that counts |
| Treating a skip as equivalent to a pass | Name why each skip is a skip; a skip hides evidence, it doesn't provide it |

---

## 6. References

- [Intent-to-Outcome Chain Coverage](../../intent-to-outcome-chain-coverage.md) — §2 row 10
- [Stage-10-Verification-Evidence-Phase2.md](../Status-Reports/Stage-10-Verification-Evidence-Phase2.md)
- [Project-Status-Register.md](../Project-Status-Register.md) §1
- [Stage 9: Deliverable Methodology](./Stage-9-Deliverable-Methodology.md)
- [Stage 11: Audit Record Methodology](./Stage-11-Audit-Record-Methodology.md)

---

## Change Log

| Date | Version | Change |
|---|---|---|
| 2026-11-12 | 1.0 | Initial version, grounded in `docs/intent-to-outcome-chain-coverage.md` §2 row 10 (no decision policy at this stage) and the dated test-suite count recorded in Project-Status-Register.md on 2026-11-11. |
