---
artifact_type: "verification_evidence_record"
report_id: "REP-STAGE10-VERIFICATION-PHASE2"
baseline_id: "PMP-BL-v1.1.0"
lifecycle_stage: "Stage 10 (Verification Evidence)"
pmbok_process: "8.3 Control Quality"
date: "2026-11-11"
governance_policy: "none (Input Evidence; records a test run and certifies no gate)"
evidence_commit: "4942de0"
---

# Stage 10 Verification Evidence: Phase 2

A simple confirmation that the test suite was run and what it reported. Stage 10 has no approval gate (`docs/intent-to-outcome-chain-coverage.md`, row 10); this record is the evidence the Stage 11 audit and the Stage 12 assessment read.

| Item | Value |
|---|---|
| Run on | 2026-11-11 |
| Commit | `4942de0` (`main` after PR #202), plus documentation-only edits on the branch of PR #203 |
| Command | `uv run pytest` (plain, the whole suite, no `--ignore`) |
| Result | **2723 passed, 2 skipped, 0 failed**, 175 s |
| Skipped | Java (Spark) and POSIX Bash tests, which skip when their tool is absent |

## Limits

- **CI is narrower.** `.github/workflows/tests.yaml` still runs `pytest --ignore=tests/pmbok` (IMP-056), so a green CI is not this run.
- **Failing-first evidence is a separate matter.** AUDIT-017 in `docs/registers/Audit-Register.md` records which stories show a RED run in `implementation-log.md`; this record says nothing about it.
- **One run, one machine.** It is not a trend; earlier counts are in `implementation-log.md` (2696 passed at the previous handover, 2606 collected on 2026-11-10).
