# FDD-004: Authority-Migration Diagnostic Snapshot and Docstring Alignment

**Source ADR:** [ADR-004](../../adr/ADR-004-authority-migration-comparison-not-replay.md) — Accepted (2026-10-23), §3, §4.1, §4.2, §7
**Source BRD:** [BRD-004](../Business-Requirements/BRD-004-authority-migration-diagnostic-snapshot.md)
**Status:** Approved (2026-10-23, Menno) — derived from an Accepted ADR's disclosed gap; adjudicated via `approve-fdd` (robust utility 0.883, episode `2bb6e21c...`).

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

## Design 3: Correct Stale Docstring in `src/agent_learning/types.py`

Current lines 130–132:
```python
    Tool calls made while generating the assistant output are captured
    in ``tool_calls``. Outcomes (evaluator metrics, user feedback)
    are attached. ``context_features`` carries the input the policy used
    to choose its action (so the learner can replay the decision).
```

**Proposed Correction:**
```python
    Tool calls made while generating the assistant output are captured
    in ``tool_calls``. Outcomes (evaluator metrics, user feedback)
    are attached. ``context_features`` carries optional caller-supplied
    contextual attributes used for reward shaping and observability;
    it is not consumed by non-contextual bandit action selection (see ADR-004).
```

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

