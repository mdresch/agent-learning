# FDD-004: Authority-Migration Diagnostic Snapshot and Docstring Alignment

**Source ADR:** [ADR-004](../../adr/ADR-004-authority-migration-comparison-not-replay.md) — Accepted (2026-10-23), §3, §4.1, §4.2, §7
**Source BRD:** [BRD-004](../Business-Requirements/BRD-004-authority-migration-diagnostic-snapshot.md)
**Status:** Approved (2026-10-23, Menno) — derived from an Accepted ADR's disclosed gap; adjudicated via `approve-fdd` (robust utility 0.883, episode `2bb6e21c...`). Amended 2026-11-05 at Stage 16: Design 3 now leaves `types.py` untouched, classified `amendment_log_entry` via `classify-diff-type` (robust utility 0.896, episode `2516ec2e...`) and accepted by Menno; Story 4.1 AC_4 and BRD-004 BRU-004-05 were amended in the same change. Changes to this document go through Stage 16.

## Design 1: `MigrationRecord` Structure

A lightweight dictionary schema representing the diagnostic snapshot at migration time:

```python
class MigrationRecord(TypedDict):
    policy_version_at_migration: int
    action_probabilities_at_migration: dict[str, float]
    from_authority: str
    to_authority: str
    migrated_at: str
```

- **Placement:** Stored inside `PolicySnapshot.metadata["migration_records"]` as a list of mappings.
- **Immutability:** Each transition appends a new item; existing records are never modified or purged.
- **Key design choice:** `policy_id` is excluded to avoid redundant denormalization, as `PolicySnapshot.id` already anchors the entity and `policy_version_at_migration` uniquely identifies the snapshot version.

## Design 2: Transition Capture in `_cmd_set_task_policy_authority`

Current implementation (`src/agent_learning/cli.py:876-902`):

```python
snapshot.metadata.update(
    {
        "decision_authority": args.authority,
        "decision_authority_source": "configured",
        "decision_authority_updated_at": datetime.now(timezone.utc).isoformat(),
    }
)
store.store_policy(snapshot)
```

**Proposed Implementation:**

```python
current_authority = TaskPolicy(snapshot).authority.value
target_authority = args.authority.lower()

if current_authority != target_authority:
    # Compute the policy's converged softmax distribution at migration time
    policy = SoftmaxPolicy.from_snapshot(snapshot)
    probs_list = policy.probabilities()
    action_probs = {
        action.id: prob for action, prob in zip(snapshot.actions, probs_list)
    }
    
    migration_record = {
        "policy_version_at_migration": snapshot.version,
        "action_probabilities_at_migration": action_probs,
        "from_authority": current_authority,
        "to_authority": target_authority,
        "migrated_at": datetime.now(timezone.utc).isoformat(),
    }
    
    records = snapshot.metadata.setdefault("migration_records", [])
    records.append(migration_record)

    snapshot.metadata.update(
        {
            "decision_authority": target_authority,
            "decision_authority_source": "configured",
            "decision_authority_updated_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    store.store_policy(snapshot)
```

If `current_authority == target_authority`, the command is idempotent and no duplicate record is appended.

## Design 3: Correct the Replay Claim in Documentation, Not in `src/agent_learning/types.py` (amended at Stage 16, 2026-11-05)

Microsoft's `src/agent_learning/types.py` is never edited in place (fork rule): it stays identical to the pinned upstream so that merging `upstream/main` never clashes with code we wrote. Its docstring currently reads:

Lines 130–132 as Microsoft ships them:
```python
    Tool calls made while generating the assistant output are captured
    in ``tool_calls``. Outcomes (evaluator metrics, user feedback)
    are attached. ``context_features`` carries the input the policy used
    to choose its action (so the learner can replay the decision).
```

That claim is materially incorrect (ADR-004 §3). The correction therefore lives in documentation, and three checks hold:

1. ADR-004 §3 states that the docstring is materially incorrect and that `context_features` is caller-supplied context used for reward shaping and observability, not decision evidence and not consumed by non-contextual bandit action selection or historical replay.
2. `src/agent_learning/types.py` is byte-identical to the pinned upstream version, guarded by `tests/test_upstream_untouched.py`.
3. No document this project owns claims that `context_features` lets the learner replay the decision, except quotations of Microsoft's docstring in ADR-004, BRD-004 and FDD-004 that name it as the defect.

The replacement docstring formerly proposed here is withdrawn: it was never applied to Microsoft's file.

## Error Handling & Compatibility

| Scenario | Behavior |
|---|---|
| First authority transition for a policy | `metadata["migration_records"]` is initialized as a 1-element list containing the initial snapshot. |
| Multiple authority oscillations (`low → full → low → full`) | Records accumulate chronologically; `policy_version_at_migration` and `migrated_at` track each shift accurately. |
| Existing policy snapshots without `migration_records` | Backward-compatible: `snapshot.metadata.get("migration_records", [])` returns an empty list. |
| Store compatibility | Zero schema changes to `LearningStore` (satisfies ADR-002 §7 Invariant #2). |

## Out of Scope

- Retroactive replay of historical `low` decisions (ADR-004 §4.1).
- Automatic decision frame synthesis.

