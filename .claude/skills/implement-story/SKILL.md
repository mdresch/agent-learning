---
name: implement-story
description: Executes the SIDPA story implementation loop (Steps 0–9; Step 9 runs only for the epic's last story) for agent-learning with contract-driven development, component skill maintenance, and audit logging.
---

# Skill: implement-story (agent-learning)

Instantiated from the `sidpa-template` skill. The loop (steps 0-9; step 9 runs only for the epic's last story) is mandatory and executed in order; the project facts below reflect confirmed repository conventions.

## Confirmed project facts

- **Base branch:** `main`.
- **Remotes:** `origin` (`https://github.com/mdresch/agent-learning.git`), `upstream` (`https://github.com/microsoft/agent-learning.git`).
- **Isolation:** None needed. State is the file-based `LearningStore`; tests use `tmp_path` / in-memory stores. Worktrees are used (Step 0), provisioned via `uv sync`.
- **Test runner:** `uv run pytest tests/test_<module>.py`. Contracts live in `tests/test_<module>.py` (flat, no per-epic directories).
  - *Note:* Full suite run requires `--ignore=tests/test_spark.py` unless Java/JVM is locally installed (Spark is an optional dependency for distributed DataFrame evaluation).
- **Fixtures:** Contract tests using real artifacts (e.g. `DecisionResult` JSONs) must live committed under `tests/fixtures/<module>/`. Never read fixtures from the repo root or from untracked files.
- **Enforcement layer:** None (no pre-commit hooks, no CI contract gate). Step 3 is discipline-only; see `heal-contract-failure`.
- **Spec documents:** ADRs in `docs/adr/`, BRD/FDD in `docs/project-docs/{Business-Requirements,Functional-Design}/`, stories in `docs/user-stories/epic-<N>-*.md`.
- **Log:** `implementation-log.md` at repo root, append-only.
- **Lessons Learned / OPA Register:** `docs/project-docs/Lessons-Learned-Register.md` governed by ADR-010. Append-only Markdown OPA recording the ADR-010 breakout recap (never a `LearningStore` record type).

## The loop — mandatory, in order

0. **Worktree:** `git worktree add ../agent-learning-story-<X.Y> -b feat/story-<X.Y> main`; run `uv sync` in the worktree before Step 5. Before creating it, confirm the story's BRD, FDD and stories are approved, and run `git status --short` in the base checkout to commit or stash anything the story depends on, because a worktree forks from committed state only (LL-010).
1. **Ingest:** Story (`Status: Ready`), ADR, BRD, FDD. The BRD, FDD and stories must be approved, not only marked Ready by their author (LL-010). Hierarchy: ADR > BRD/FDD > Story. If a story has no code deliverable (operational/governance exercise), record findings in the appropriate register rather than forcing code.
2. **State intent:** Intent / Scope / Contract to encode / Explicitly out of scope.
3. **Contract (RED):** One pytest per Acceptance Criterion; header docstring naming Story, ADR, BRD, FDD; fixtures loaded from `tests/fixtures/<module>/`. Run and verify failing (RED) before implementing. If a test asserts behavior the acceptance criteria or the design do not state, record it as an interpretation in the test docstring and the log, and amend the FDD or the open questions (LL-011).
4. **Component skill:** Create or update `.claude/skills/<component>/SKILL.md` (governing ADRs/Stories, contract files, load-bearing constraints, call sites). Required Definition-of-Done item.
5. **Implement (GREEN):** Minimal code — no speculative generalization.
6. **Validate:** Run the story contract, then full suite (`uv run pytest --ignore=tests/test_spark.py`). If the change adds a step or entry, changes a count, or completes something another document describes as pending, grep the repo for the old number or phrase and update every occurrence in the same change (LL-007). If the full suite cannot run, record in the log which paths were excluded, why, and the resulting count, and never call that count the entire suite (LL-013).
7. **Commit & log:**
   - **Optional trap note:** If something surprising happened in this story, jot a one-line note for the epic-end breakout recap (ADR-010 §4.1). Optional, never a gate; do not write an `LL-###` entry per story.
   - **Commit:** Commit implementation, test contracts, and component skills.
   - **Audit log:** Append to `implementation-log.md` with commit hash `pending`. If amending (`git commit --amend`), always backfill with the final commit hash.
8. **PR, Q review, amendments and merge:** the story ends on `main` only after Amazon Q has nothing further to add.
   1. **Open the PR.** Push `feat/story-<X.Y>` to `origin` and run `gh pr create --repo mdresch/agent-learning --base main --head feat/story-<X.Y>`. The description lists the summary, every interpretation (I1, I2, ...) that needs confirming, and the test plan, naming any paths excluded from the suite and why.
   2. **Request the review.** Comment `/q review` on the PR (`gh pr comment <n> --repo mdresch/agent-learning --body "/q review"`). To get an answer for a later commit, comment it again after each push.
   3. **Read the result.** `gh pr view <n> --repo mdresch/agent-learning --json reviews,state,mergeStateStatus` for the summary and `gh api repos/mdresch/agent-learning/pulls/<n>/comments` for the inline findings. Check which commit each comment is on. Q only ever posts `COMMENTED`; it never approves, so a clean state needs an explicit verdict (step 6).
   4. **Triage every finding against the repository before acting.** Accept what the code or the spec supports. Decline what it does not, with a one-line reason in the PR. A reviewer's claim is not evidence: confirm it by reading the code, running the case, or checking the cited ADR. Record each finding in the fixed shape of step 7 as you triage it, so the decisions can later be replayed as learning data (ADR-036).
   5. **Amend.** Fix accepted findings in new commits on the story branch. Do not amend or force-push the implementation commit (the log cites its hash). Re-run the story contract and the full suite, push, and comment `/q review` again.
   6. **Repeat 2 to 5 until Q has no further additions**, meaning all of: Q's latest review is on the current head commit; it reports no blocking defect and no new finding; no inline comment on the head commit is unaddressed. Ask for the verdict explicitly in the last request: `/q confirm whether every earlier finding is resolved in this commit and list anything remaining` (LL-004). Merge on an explicit positive verdict. Silence is not a clean review: if Q has not answered the latest request, wait or ask the human, and do not merge. After three rounds, or if Q repeats a finding that was declined, stop and ask the human.
   7. **Record the review.** Before merging, add a bullet to the story's `implementation-log.md` entry (it is still unmerged, so it can be edited) listing the Q rounds, the findings accepted, and the findings declined with reasons. List each finding on one line in this shape: `Q-<PR>-<n> | <claim type> | verified: yes/no/partial | decision: accepted/declined/deferred | <one-line reason> | fix: <commit or none>`. Claim types: logic error, crash risk, test gap, documentation, style. Do not guess a field; write `unknown`.
   8. **Merge to `main`** when Q is clean on the head commit, `mergeStateStatus` is `CLEAN`, and the full suite passed on the head commit: `gh pr merge <n> --repo mdresch/agent-learning --merge` (a merge commit, as earlier stories). Then `git checkout main`, `git pull --ff-only origin main`, and remove the worktree (`git worktree remove ../agent-learning-story-<X.Y>`). The human can withhold or override the merge at any point by saying so.
9. **Breakout & recap (last story of the epic only):** After contracts are verified (Step 6) and Step 8 has reached "Q has no further additions" on the epic's final story PR (Q comments, it never approves), hold the light breakout recap defined in ADR-010 §4.1: how the code was created from the stories, covering unexpected traps, subtle defects and review findings. This is not the formal Stage 15 review, which is separate. Record each lesson as an `LL-###` entry in `docs/project-docs/Lessons-Learned-Register.md` (required fields: title, trap, root cause, rule, propagation target, which may read `Tier 1 only`; include Epic / Story so the Phase Close filter matches), or record a short no-new-lessons sign-off entry (Epic/Phase containing `no-new-lessons`, propagation target `Tier 1 register sign-off`). An Autonomous Breakout Facilitator may draft these, but a human accepts them (ADR-010 §4.7). Consider propagating component-specific rules to `.claude/skills/` (Tier 2) and universal rules to `sidpa-template` (Tier 3). Commit the register change with the epic's closing PR or a follow-up docs commit. Skip this step for every story that is not the epic's last.

## Definition of done

Contract exists, observed RED, and passes; full suite passes; fixtures are committed under `tests/fixtures/<module>/`; component `SKILL.md` is current; for the epic's last story only, the ADR-010 breakout recap is held and recorded in `docs/project-docs/Lessons-Learned-Register.md` (an `LL-###` entry or a short no-new-lessons sign-off entry); traceability is accurate; `implementation-log.md` entry is recorded with resolved commit hash; the PR has reached "Q has no further additions" with accepted findings amended and declined ones explained, and is merged to `main` with the worktree removed.
