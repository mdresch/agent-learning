---
artifact_type: "manual_change_request"
change_request_id: "CR-20261110-001"
stage: "16"
evidence_basis: "execution"
current_baseline: "PMP-BL-v1.1.0"
status: "proposed_awaiting_sponsor_decision"
date: "2026-11-10"
requested_by: "Menno Drescher"
drafted_by: "assistant (draft only; nothing in section 4 is applied)"
---

# Manual Change Request: Bring the `implement-story` Skill Up To Date With the Accepted Lessons and the Code

> **Status:** Proposed. No decision is recorded. The skill file is unchanged until the Sponsor decides (section 6).

## 1. Request

`.claude/skills/implement-story/SKILL.md` is the Tier 2 target of 31 lessons. Reading it against the register and the code (Stage 16 draft, Step 2d) shows:

- **12 lessons are missing from it:** LL-027, 028, 029, 030, 031, 032, 033, 034, 035, 036, 038, 039. None of their ids appears in the skill.
- **Step 6 is out of date.** It ends in `--ignore=tests/test_spark.py --ignore=tests/pmbok`. The whole suite now collects 2606 tests with no `--ignore` (checked 2026-11-10 with `uv run pytest --collect-only -q`), the Spark tests skip without a JVM, and `tests/pmbok` collects once the `dev` and `examples` extras are synced (LL-055, IMP-044, the maintainer's rule to run the whole suite).
- **Step 0 is out of date.** It says plain `uv sync`; LL-033 and LL-055 say a fresh worktree needs the extras and a check.
- **"Enforcement layer: None (no ... CI contract gate)"** and the Step 6 note repeat the old exclusion. CI still runs `pytest --ignore=tests/pmbok` (`.github/workflows/tests.yaml`); that is IMP-056, carried separately, and the skill should say so instead of copying it.

## 2. Why a change request

The skill is not an approved ADR, BRD, FDD or story, so ADR-007 and `scripts/stage16_amend.py` do not cover it and `tests/governance_baseline.json` does not fingerprint it. The route for a Tier 2 change is therefore: a change request (as CR-20261109-001 and -002), a human decision, then one PR that carries the skill edit with the lessons' register lines (LL-041). `tests/test_project_status_register.py` reads this skill and must keep passing.

## 3. Manual Stage 16 assessment

| Assessment field | Assessment |
|---|---|
| Trigger | Stage 15 acceptance of 2026-11-10 and the whole-register check (Stage 16 draft, Steps 2a to 2d) |
| Evidence basis | `execution` |
| Primary diff type | process (how the loop is run); no requirement, interface or baseline change |
| Overall impact | Medium: it changes what every future story run does |
| Proposed escalation | Project Sponsor |
| Decision status | Not decided |

## 4. Proposed edits (text to apply on approval)

Each line cites its lesson so the Step 9 check (`grep -c "LL-0xx"`) finds it. Wording is a draft for the Sponsor to change.

| Step | Add or change | Lessons |
|---|---|---|
| Project facts, test runner note | Replace the `--ignore` note with: the full suite is plain `uv run pytest`; Spark tests skip without a JVM; `tests/pmbok` needs `uv sync --extra dev --extra examples`. State that CI still excludes `tests/pmbok` (IMP-056) so CI is not the whole suite. | LL-013, 055 |
| 0 Worktree | After `git worktree add`: `uv sync --all-extras`, then `uv pip uninstall --python .venv/Scripts/python.exe azure-cosmos`. Accept a RED only after reading its message: it must name the symbol the story adds, not a missing package. | LL-033, 055 |
| 0 Worktree | Confirm with `git log -- docs/policy-shapes` that the story's approval records are committed before the first code commit, and that the PR shows them. | LL-027 |
| 0 | Invoke this skill at the start of the story and re-read a step before doing it. Record a missed step as a deviation in the log; never claim a result (such as "observed RED first") that did not happen. | LL-028 |
| 1 Ingest | When a spec says a constructed member, family or value meets a gate, run that example through the real gate function and record the result in the spec; amend the spec before writing the contract if it fails. | LL-036 |
| 3 Contract | Observe RED by temporarily breaking the behaviour under test, confirm the named tests fail, restore the file, and check `git diff main -- src` is empty; record how RED was obtained. | LL-035 |
| 3 Contract | Derive stable digests with `hashlib.sha256`; `hash(` in a test file is a finding. Compare a container of tuples one key at a time; `pytest.approx(<dict of tuples>)` is a finding. | LL-029, 039 |
| 6 Validate | Replace the command with `uv run pytest` (whole suite). If a gate's tool is missing, try `uvx <tool>` before skipping; if skipped, record the gate as not run, with the reason. Keep the rule that a partial run is never called the whole suite. | LL-013, 030 |
| 8.4 Triage | Check each claim in a reviewer's confirmation against the head commit, as for a first-round finding; log stale or out-of-scope ones as noise with the reason. | LL-031 |
| 8.7 Record | A review with no findings is one prose bullet in the story's log entry (round, head commit, verdict), never a `Q-<PR>-<n>` line; run `tests/test_review_triage.py` after any edit to `implementation-log.md`. | LL-034 |
| 8.9 Merge | Prefer merging the base story first. A stacked PR is unverified: after the base merges, retarget to `main`, merge `main` into the branch, rerun the full suite and wait for CI before the gate. | LL-038 |
| 9 Audit | To claim an omission, read the unfiltered source (for example `grep -c` on the whole entry) and quote it; a filtered output only supports "not found in this view". | LL-032 |

## 5. LL-040 (store path): what it means and where it belongs

LL-040 says to resolve and print the store path before `task-policy-decide`, `task-policy-adjudicate` or `task-episode-register`, and count files before and after.

- **It already belongs in `.claude/skills/governance/SKILL.md` section 2.5, and it is there.** No edit to `implement-story` is needed beyond a pointer, because `implement-story` does not itself run those commands.
- **The live gap is in the tooling, not the skill.** In this shell `AGENT_LEARNING_LOCAL_STORE_DIR` is set to `C:\Users\MennoDrescher\source\repos\socialengage\data\agent-learning\store`, another repository's store. `scripts/stage16_amend.py` runs those commands and neither prints nor checks the path (no reference to the variable in `scripts/` or `src/agent_learning_ext/`). An amendment run here would write its episode to the wrong store.
- **Proposed, as a separate code change (not part of the skill edit):** have `stage16_amend.py` print the resolved path and refuse when it is outside this repository unless told otherwise; this is also the first line of IMP-007's `approve.py`. Needs its own story or IMP and a test. Until then, set the variable for this repository before any `accept`.

## 6. Decision record

| Role | Decision | Date |
|---|---|---|
| Project Sponsor | Pending | |

## 7. Procedure after approval

1. One branch, one PR: edit the skill as section 4; update the Stage 16 draft and, where the lessons name the skill, nothing else by hand.
2. `uv run pytest` (whole suite) and `scripts/pr_gate.py`; the PR cites this request.
3. The next epic recap runs the LL-041 check and finds all 12 ids.
4. Record the result in the Stage 16 assessment; do not edit the register entries.
