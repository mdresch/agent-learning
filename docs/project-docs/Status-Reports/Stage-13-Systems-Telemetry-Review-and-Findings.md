---
artifact_type: "observation_log"
report_id: "REP-STAGE13-OBSERVATION-PHASE2"
baseline_id: "PMP-BL-v1.1.0"
lifecycle_stage: "Stage 13 (Observation)"
pmbok_process: "4.5 Monitor & Control Project Work"
date: "2026-11-10"
governance_policy: "none (raw observation; records no approval, no interpretation and no fix)"
evidence_commit: "b18b951"
follows: "Stage-12-Actual-Outcome-Assessment-Phase2.md (REP-STAGE12-OUTCOME-PHASE2)"
---

# Stage 13 Systems Telemetry Review and Findings: Phase 2

> **Stage 13 records what was seen, when, and the evidence. It does not say what it means and it fixes nothing.** Meaning is Stage 14, rules are Stage 15, and changes are Stage 16. Nothing here is a claim about cause. Each line names its source so it can be checked.

## 1. What this stage covers here

The chain coverage document defines Stage 13 as: inputs, runtime telemetry and review findings; process, record raw telemetry; output, an uninterpreted observation log. This project has no production or adopter telemetry (the Stage 12 report says the same). The systems telemetry it does have is the set below, and this note is the observation log built from it.

| Source | What it holds |
|---|---|
| GitHub Actions runs (`gh run list`) | Workflow results per push and per PR |
| Local full-suite runs (`uv run pytest`) | Pass, skip and fail counts |
| `scripts/pr_gate.py` output | Gate score and merge result per PR |
| `implementation-log.md` | Review findings in the fixed triage shape, and story entries |
| `scripts/shadow_effort.py` output | Commit times and session lengths |
| The governance stores (repo and socialengage) | Episode file counts |

Not available: runtime telemetry from adopters, token or usage telemetry, latency or cost of any routed decision.

## 2. Continuous integration (GitHub Actions)

Read on 2026-11-10 with `gh run list --limit 100`; the 100 most recent runs all start on or after 2026-11-07, so the window may be cut off at its start.

| Workflow | Runs | Success | Failure |
|---|---|---|---|
| Tests | 50 | 48 | 2 |
| Build Linux CLI | 31 | 30 | 1 |
| Release and Publish | 19 | 0 | 19 |

- **Tests, 2 failures:** run `f26eadb` on branch `feat/phase-2-examples-and-ledger` (2026-11-10 12:23), and run `9e97aed` on `main`, the merge of PR #173 (2026-11-10 12:26). On the same commit as the first, `Build Linux CLI` failed once.
- **Release and Publish:** failed on every run in the window (15 on 2026-11-10 and 5 on 2026-11-09 on `main`). The recorded message is `v0.10.0 already points to 9cbe3c52...; bump the package version` from the step "Reject a version already tagged at another commit" (IMP-052).
- **Other `Tests` runs on `main`:** in the 40 most recent `main` runs, 19 `Tests` runs (5 on 2026-11-09, 14 on 2026-11-10) succeeded and 1 failed (`9e97aed`, above).

## 3. Local full-suite runs

| When | Command and state | Result |
|---|---|---|
| Stage 10, `main` at `51ef83d` | `uv sync --extra dev --extra examples` | 2585 passed, 3 skipped (scikit-learn missing; `test_scorers_nlp_text.py` skipped) |
| Stage 10, same commit | `uv sync --extra dev --extra examples --extra nlp` | 2605 passed, 2 skipped (`test_spark.py` needs Java; the Linux installer test needs POSIX Bash) |
| After PR #173 merged | `main` | 5 failed in `test_methodology_catalog.py`, 2600 passed, 2 skipped |
| After PR #178 merged | `main` | 2605 passed, 2 skipped |

## 4. Review findings (Amazon Q triage in `implementation-log.md`)

- 249 triage lines parsed over 48 PRs (#11 to #167).
- Claim type: logic error 121, test gap 47, crash risk 46, documentation 16, style 15, "logic" 4.
- Verified: yes 161, no 42, partial 37, unknown 9.
- Decision: accepted 178, declined 62, deferred 7, unknown 2.
- PRs #118 and later (an approximate Phase 2 boundary): 113 lines; accepted 100, declined 10, deferred 1, unknown 2.

## 5. Events recorded in the log or the registers

- `pr_gate.py` crashed on Windows with a cp1252 decode error until run with `PYTHONUTF8=1` (LL-059, IMP-045).
- Story 21.6: a review-driven edit removed the pre-existing `full_authority_excluded` count and 6 tests failed; the counter was restored before the merge.
- Story 22.7: the Pre-Flight Spec Gate was not run before its contract was written (recorded as a gap, not backfilled).
- A failing-first (RED) run is noted for 7 of 7 Epic 21 stories and 6 of 6 Epic 38 stories, for 1 of 6 in Epic 18 and 1 of 7 in Epic 22, and for none of 18 in Epics 14, 16 and 17 (a loose text search of the log).
- The log holds 3 dated correction entries.

## 6. Agentic effort (shadow record; a measured lower bound)

From `Shadow-Agentic-Effort-Phase-2.md`: 254 non-merge commits from 2026-11-07 to 2026-11-10, 2 working sessions, 25.5 hours of session time, 3 calendar days with commits. It leaves out human review time and tokens.

## 7. Stores

- Repo store `data/agent-learning/store`: 319 files before and 320 after the Stage 11 approval episode was registered.
- Socialengage store (the `AGENT_LEARNING_LOCAL_STORE_DIR` default): 620 files before and after the policy decision and adjudication.

## 8. Limits

- Read-only: no new experiment was run. Counts were taken from the sources named above on 2026-11-10.
- The CI window and the loose text searches may undercount or overcount; they are indications, not audits.
- It leaves out items already recorded at Stages 10, 11 and 12 (the audit result and the outcome blockers); they stay in their own reports.
- This note is not an approval.

## 9. Observation files

Each item above is also recorded as one file under `docs/observations/`, in the Phase 1 form (OBS-nnn, raw and uninterpreted), so that insights and lessons can cite and link them.

| This note | File |
|---|---|
| Section 2, Tests and Build Linux CLI | OBS-010 |
| Section 2, Release and Publish | OBS-011 |
| Section 3, local suite runs | OBS-012 |
| Section 4, review findings | OBS-013 |
| Section 5, failing-first runs | OBS-014 |
| Section 5, events in the log | OBS-015 |
| Section 6, agentic effort | OBS-016 |
| Not in the sections above: episode telemetry fields and policy snapshot counters | OBS-017 |
| Not in the sections above: how `pr_gate.py` treats pending checks | OBS-018 |
| Section 7, store counts | OBS-019 |
