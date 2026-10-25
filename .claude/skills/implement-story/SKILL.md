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

0. **Worktree:** `git worktree add ../agent-learning-story-<X.Y> -b feat/story-<X.Y> main`; run `uv sync` in the worktree before Step 5. Before creating it, run `git status --short` in the base checkout and commit or stash anything the story depends on, such as approved specs, because a worktree forks from committed state only (LL-008).
1. **Ingest:** Story (`Status: Ready`), ADR, BRD, FDD. Hierarchy: ADR > BRD/FDD > Story. If a story has no code deliverable (operational/governance exercise), record findings in the appropriate register rather than forcing code.
2. **State intent:** Intent / Scope / Contract to encode / Explicitly out of scope.
3. **Contract (RED):** One pytest per Acceptance Criterion; header docstring naming Story, ADR, BRD, FDD; fixtures loaded from `tests/fixtures/<module>/`. Run and verify failing (RED) before implementing. If a test asserts behavior the acceptance criteria or the design do not state, record it as an interpretation in the test docstring and the log (LL-009).
4. **Component skill:** Create or update `.claude/skills/<component>/SKILL.md` (governing ADRs/Stories, contract files, load-bearing constraints, call sites). Required Definition-of-Done item.
5. **Implement (GREEN):** Minimal code — no speculative generalization.
6. **Validate:** Run the story contract, then full suite (`uv run pytest --ignore=tests/test_spark.py`). If the change adds a step or entry, changes a count, or completes something another document describes as pending, grep the repo for the old number or phrase and update every occurrence in the same change (LL-007). If the full suite cannot run, record in the log which paths were excluded, why, and the resulting count, and never call that count the entire suite (LL-010).
7. **Commit & log:**
   - **Optional trap note:** If something surprising happened in this story, jot a one-line note for the epic-end breakout recap (ADR-010 §4.1). Optional, never a gate; do not write an `LL-###` entry per story.
   - **Commit:** Commit implementation, test contracts, and component skills.
   - **Audit log:** Append to `implementation-log.md` with commit hash `pending`. If amending (`git commit --amend`), always backfill with the final commit hash.
8. **PR, review & merge:** Push `feat/story-<X.Y>` to `origin`, open PR via `gh pr create --repo mdresch/agent-learning --base main`. Request automated/peer review (e.g., `/q review`). Address review findings before merge. Remove worktree only after PR merge.
9. **Breakout & recap (last story of the epic only):** After contracts are verified (Step 6) and Q Developer has approved the epic's final story PR (Step 8), hold the light breakout recap defined in ADR-010 §4.1: how the code was created from the stories, covering unexpected traps, subtle defects and review findings. This is not the formal Stage 15 review, which is separate. Record each lesson as an `LL-###` entry in `docs/project-docs/Lessons-Learned-Register.md` (required fields: title, trap, root cause, rule, propagation target, which may read `Tier 1 only`; include Epic / Story so the Phase Close filter matches), or record a short no-new-lessons sign-off entry (Epic/Phase containing `no-new-lessons`, propagation target `Tier 1 register sign-off`). An Autonomous Breakout Facilitator may draft these, but a human accepts them (ADR-010 §4.7). Consider propagating component-specific rules to `.claude/skills/` (Tier 2) and universal rules to `sidpa-template` (Tier 3). Commit the register change with the epic's closing PR or a follow-up docs commit. Skip this step for every story that is not the epic's last.

## Definition of done

Contract exists, observed RED, and passes; full suite passes; fixtures are committed under `tests/fixtures/<module>/`; component `SKILL.md` is current; for the epic's last story only, the ADR-010 breakout recap is held and recorded in `docs/project-docs/Lessons-Learned-Register.md` (an `LL-###` entry or a short no-new-lessons sign-off entry); traceability is accurate; `implementation-log.md` entry is recorded with resolved commit hash.
