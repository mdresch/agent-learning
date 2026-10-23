---
name: implement-story
description: Executes the SIDPA story implementation loop (Steps 0–8) for agent-learning with contract-driven development, component skill maintenance, and audit logging.
---

# Skill: implement-story (agent-learning)

Instantiated from the `sidpa-template` skill. The loop (steps 0-8) is mandatory and executed in order; the project facts below reflect confirmed repository conventions.

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

## The loop — mandatory, in order

0. **Worktree:** `git worktree add ../agent-learning-story-<X.Y> -b feat/story-<X.Y> main`; run `uv sync` in the worktree before Step 5.
1. **Ingest:** Story (`Status: Ready`), ADR, BRD, FDD. Hierarchy: ADR > BRD/FDD > Story. If a story has no code deliverable (operational/governance exercise), record findings in the appropriate register rather than forcing code.
2. **State intent:** Intent / Scope / Contract to encode / Explicitly out of scope.
3. **Contract (RED):** One pytest per Acceptance Criterion; header docstring naming Story, ADR, BRD, FDD; fixtures loaded from `tests/fixtures/<module>/`. Run and verify failing (RED) before implementing.
4. **Component skill:** Create or update `.claude/skills/<component>/SKILL.md` (governing ADRs/Stories, contract files, load-bearing constraints, call sites). Required Definition-of-Done item.
5. **Implement (GREEN):** Minimal code — no speculative generalization.
6. **Validate:** Run the story contract, then full suite (`uv run pytest --ignore=tests/test_spark.py`).
7. **Commit & log:** Append to `implementation-log.md` with commit hash `pending`. If amending (`git commit --amend`), always backfill with the final commit hash.
8. **PR, don't merge directly:** Push `feat/story-<X.Y>` to `origin`, open PR via `gh pr create --repo mdresch/agent-learning --base main`, and remove worktree only after merge.

## Definition of done

Contract exists, observed RED, and passes; full suite passes; fixtures are committed under `tests/fixtures/<module>/`; component `SKILL.md` is current; traceability is accurate; `implementation-log.md` entry is recorded with resolved commit hash.
