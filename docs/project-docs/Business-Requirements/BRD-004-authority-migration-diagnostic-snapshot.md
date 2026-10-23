# BRD-004: Authority-Migration Diagnostic Snapshot and Docstring Alignment

**Source ADR:** [ADR-004](../../adr/ADR-004-authority-migration-comparison-not-replay.md) — Accepted (2026-10-23), §3, §4.1, §4.2, §7
**Status:** Approved (2026-10-23, Menno) — derived from an Accepted ADR's disclosed gap; adjudicated via `approve-brd` (robust utility 0.883, episode `ee36273a...`).
**Stakeholders:** Menno (Sponsor/PM/maintainer). No separate Product Owner exists for this SDK; naming that rather than inventing one.

## Business Need

In the agent-learning SDK, policies can migrate between `low` and `full` decision authority via `task-policy-authority-set` (ADR-001 §4.3). Prior to ADR-004, authority migration was a silent configuration flip that captured no diagnostic evidence of the policy's learned state.

ADR-004 established two fundamental findings:
1. **No Fabricated Retroactive Replay (§4.1):**
   Historical `low`-authority decisions cannot be retroactively re-evaluated under `full` authority because the required `DecisionFrame` (criteria, weights, options, constraints) was never generated or captured at decision time. Attempting to synthesize this evidence after the fact would manufacture false confidence in the migration.
2. **Diagnostic Snapshot Capture at Migration Time (§4.2):**
   Because the learned bandit is non-contextual, the complete representation of what the policy had learned at migration time is its softmax action probability distribution. At the exact instant of authority migration, the SDK must record a frozen, diagnostic `MigrationRecord` inside `PolicySnapshot.metadata`.
3. **Docstring Defect in `types.py:130-132` (§3):**
   The docstring for `Episode.context_features` currently claims it carries input "so the learner can replay the decision." This statement is materially incorrect and actively misleading: `SoftmaxPolicy` is non-contextual and never reads `context_features` during action selection, and no replay mechanism exists. This docstring must be aligned with actual system behavior.

This BRD formalizes the requirements to persist diagnostic migration snapshots and align codebase documentation.

## Business Rules (BRU)

- **BRU-004-01**: Every successful execution of `task-policy-authority-set` that transitions authority (`low → full` or `full → low`) must append exactly one immutable `MigrationRecord` to `PolicySnapshot.metadata["migration_records"]` (ADR-004 §4.2, §7 Invariant #4).
- **BRU-004-02**: The `MigrationRecord` must capture:
  - `policy_version_at_migration`: integer version of the snapshot at transition time.
  - `action_probabilities_at_migration`: dictionary mapping action IDs to their converged softmax probabilities at transition time.
  - `from_authority`: string representing the previous authority.
  - `to_authority`: string representing the newly active authority.
  - `migrated_at`: ISO 8601 UTC timestamp of the transition.
  `policy_id` is deliberately omitted as redundant with the enclosing `PolicySnapshot.id`.
- **BRU-004-03**: Storage boundary discipline: `MigrationRecord` must be persisted exclusively within `PolicySnapshot.metadata` — it must never create a sixth `LearningStore` record type (ADR-002 §7 Invariant #2, ADR-004 §4.2).
- **BRU-004-04**: No retroactive replay: the system must not attempt to re-evaluate historical `low`-authority episodes under `full` authority during or after migration (ADR-004 §4.1, §7 Invariant #1).
- **BRU-004-05**: Docstring correction: `Episode.context_features` in `types.py` must be updated to accurately state that `context_features` provides caller-supplied context for reward shaping and observability, not for non-contextual bandit action selection or historical replay (ADR-004 §3).

## Stakeholder Success Metrics

| Metric | Current state |
|---|---|
| `task-policy-authority-set` creates a diagnostic `MigrationRecord` in `PolicySnapshot.metadata` | Not true today — migration is currently a silent metadata update with no snapshot (ADR-004 §3) |
| Multiple authority transitions append records sequentially without overwriting earlier transitions | Not true today — no history array exists |
| `Episode.context_features` docstring accurately describes actual behavior | Not true today — docstring claims non-existent replay capability (ADR-004 §3) |

## Out of Scope

- Retroactively recalculating historical `low`-authority episodes under `full` authority (rejected in ADR-004 §4.1).
- Creating a separate database container or record type for migration history (rejected in ADR-004 §4.2).

