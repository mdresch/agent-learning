---
name: phase-rollup
description: Generates the Phase Carry-Over Backlog (implemented vs approved-but-not-implemented stories) from the story files and implementation-log.md for the Stage 17/18 roll-up and the Obsidian brain; never stored, never hand-edited.
---

# Component: phase-rollup (`scripts/phase_rollup.py`)

**Governing:** the Phase 1 roll-up request of 2026-11-04 (separate approved-but-unbuilt stories from implemented ones, so the next phase can plan them); IMP-011 (status drift); LL-041.
**Contract:** `tests/test_phase_rollup.py` (fixtures in `tests/fixtures/phase_rollup/`).

## Load-bearing constraints

- **Generated, never stored.** The backlog is computed from `docs/user-stories/epic-*.md` and `implementation-log.md` each time. Do not commit a copy or edit the output; the Obsidian ingest (`obsidian-second-brain/scripts/ingest-agent-learning.mjs`) runs the script on every ingest.
- **Four groups.** `implemented` (a log entry, or a status starting Completed/Done), `superseded` (Superseded), `ready` (Ready or Approved), `draft` (anything else). A story is in exactly one group; the groups add up to the number of `## Story` headings.
- **Drift is reported, not resolved.** A story logged but not marked Completed/Done, or marked Completed/Done with no log entry, is listed under "Status drift" and keeps its group. `--check` exits 1 when drift exists; it is not wired into CI (19 stories drift today).
- **Nothing is silently dropped.** `build()` asserts that every `## Story` heading in a file has a parseable `**Status:**` line.
- **Deterministic.** No timestamps in the output, so the same inputs give the same text.
- **No retroactive approvals.** The backlog describes what was built and what was not; it does not certify any gate (see the no-retroactive-gate-approvals preference).

## Call sites

- `python scripts/phase_rollup.py [--output FILE] [--check]`
- Obsidian vault: `scripts/ingest-agent-learning.mjs` writes `06 Synthesis & Lessons Learned/Phase-Carry-Over-Backlog.md`.
