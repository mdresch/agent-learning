# Skill: implement-story (agent-learning)

Instantiated from the `sidpa-template` skill. The loop (steps 0-8) is unchanged; the project facts below were confirmed on Story 5.1 and replace the template's "confirm first" section.

## Confirmed project facts

- **Base branch:** `main`.
- **Isolation:** none needed. State is the file-based `LearningStore`; tests use `tmp_path`/in-memory stores. Worktrees are still used (Step 0), but a new worktree needs its own `.venv` (`pip install -e .[dev]`).
- **Test runner:** pytest via the repo venv: `.venv/Scripts/python -m pytest`. Contracts live in `tests/test_<module>.py` (flat, no per-epic directories).
- **Fixtures:** contract tests that use real artifacts (e.g. DecisionResult JSONs) keep them **committed** under `tests/fixtures/<module>/`. Never read fixtures from the repo root or from untracked files: Story 5.1 originally did, and its contract would have failed on a clean clone.
- **Enforcement layer:** none (no hooks, no CI gate on contracts). Step 3 is discipline-only; see `heal-contract-failure`.
- **Spec documents:** ADRs in `docs/adr/`, BRD/FDD in `docs/project-docs/{Business-Requirements,Functional-Design}/`, stories in `docs/user-stories/epic-<N>-*.md`.
- **Log:** `implementation-log.md` at the repo root, append-only.

## The loop - mandatory, in order

0. **Worktree:** `git worktree add ../agent-learning-story-<X.Y> -b feat/story-<X.Y> main`; set up the venv there before Step 5.
1. **Ingest** Story (`Status: Ready`), ADR, BRD, FDD. Hierarchy: ADR > BRD/FDD > Story.
2. **State intent:** Intent / Scope / Contract to encode / Explicitly out of scope.
3. **Contract (RED):** one pytest per Acceptance Criterion, module docstring naming Story, ADR, BRD, FDD. Run it and see it fail before implementing.
4. **Component skill:** create or update `.claude/skills/<component>/SKILL.md` (governing ADRs/Stories, contract files, load-bearing constraints, call sites). Not optional; Story 5.1 skipped it and `comparison` was backfilled afterwards.
5. **Implement (GREEN):** minimal code.
6. **Validate:** story contract, then the full `tests/` suite, from the venv.
7. **Commit and log:** append to `implementation-log.md` in the same commit with hash `pending`, backfilled by the next commit. If you `git commit --amend`, backfill from the final hash: the pre-amend hash is dead (Story 5.1 logged `d032f07`, the real hash was `310dd3e`).
8. **PR, don't merge directly:** push `feat/story-<X.Y>`, `gh pr create --base main`, remove the worktree only after it merges upstream.

## Definition of done

Contract exists, was seen RED, and passes; full suite passes; fixtures are committed; component `SKILL.md` current; traceability accurate; log entry present with a real or `pending` hash.
