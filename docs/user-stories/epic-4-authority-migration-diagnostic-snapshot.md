# Epic 4: Authority-Migration Diagnostic Snapshot and Docstring Alignment

**Source ADR:** [ADR-004](../adr/ADR-004-authority-migration-comparison-not-replay.md) — Accepted (2026-10-23), §3, §4.1, §4.2, §7
**Source BRD/FDD:** [BRD-004](../project-docs/Business-Requirements/BRD-004-authority-migration-diagnostic-snapshot.md) / [FDD-004](../project-docs/Functional-Design/FDD-004-authority-migration-diagnostic-snapshot.md)

One story, matching FDD-004's designs.

## Story 4.1 — Capture Diagnostic Migration Snapshot and Correct Replay Docstring

**Status:** Approved (2026-10-23, Menno) — derived from an Accepted ADR's disclosed gap; adjudicated via `approve-user-stories` (robust utility 0.883, episode `fb2fab25...`). Completed (2026-10-26) — implemented in feat/story-4.1 with contract tests in tests/test_authority_migration.py.
**As** a policy auditor and operator, **I want** authority migrations to capture a frozen snapshot of the policy's converged softmax distribution and code docstrings to reflect actual non-contextual behavior, **so that** the state at authority elevation is permanently inspectable and developers are not misled into proposing impossible retroactive replays.

**Acceptance Criteria:**
- $AC_0$: `task-policy-authority-set` appends an immutable `MigrationRecord` to `PolicySnapshot.metadata["migration_records"]` whenever authority changes (`low → full` or `full → low`).
- $AC_1$: The captured `MigrationRecord` contains `policy_version_at_migration`, `action_probabilities_at_migration` matching the policy's softmax distribution, `from_authority`, `to_authority`, and ISO 8601 UTC timestamp `migrated_at`.
- $AC_2$: Executing `task-policy-authority-set` with the currently active authority is idempotent and appends no record.
- $AC_3$: Oscillating authority migrations (`low → full → low → full`) append records sequentially in chronological order; prior records are never overwritten or mutated.
- $AC_4$: `Episode.context_features` docstring in `src/agent_learning/types.py` is updated, removing the claim that `context_features` enables policy replay.
- $AC_5$: No new `LearningStore` record type or database container is introduced (ADR-002 Invariant #2).

## Not a story — out of scope per BRD-004/FDD-004

Retroactive calculation or reconstruction of historical `low` episodes under `full` authority is explicitly rejected per ADR-004 §4.1.

