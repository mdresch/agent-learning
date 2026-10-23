# FDD-002: Cosmos Active-Policy Pointer Concurrency Protection

**Source ADR:** [ADR-002](../../adr/ADR-002-storage-backend-strategy.md) — Accepted (2026-10-23), §4.5
**Source BRD:** [BRD-002](../Business-Requirements/BRD-002-cosmos-active-policy-optimistic-concurrency.md)
**Status:** Approved (2026-10-23, Menno) — derived from an Accepted ADR's disclosed gap; adjudicated via `approve-fdd` (robust utility 0.883, episode `7c938899...`).

## Design 1: Pointer Document Schema Enrichment

Current behavior in `CosmosStore.store_policy()` (`src/agent_learning/storage/cosmos.py:383-392`):

```python
self._upsert(
    "policies",
    {
        "id": f"active:{quote(policy.task_id, safe='')}",
        "agent_id": policy.agent_id,
        "task_id": policy.task_id,
        "policy_id": policy.id,
        "record_type": "active_policy",
    },
)
```

The pointer document lacks `version`, making it impossible to evaluate version precedence without fetching the full target snapshot.

**Proposed Schema Enhancement:**

```python
pointer_doc = {
    "id": f"active:{quote(policy.task_id, safe='')}",
    "agent_id": policy.agent_id,
    "task_id": policy.task_id,
    "policy_id": policy.id,
    "policy_version": policy.version,
    "record_type": "active_policy",
    "updated_at": _utcnow_iso(),
}
```

This retains full backward compatibility for `get_active_policy()` (`cosmos.py:434-440`), which reads `pointer.get("policy_id")`.

## Design 2: Conditional Update with ETag and Monotonicity Guard

Replace unconditional `_upsert()` for the pointer document with a dedicated helper `_store_active_pointer(policy: PolicySnapshot, max_retries: int = 3) -> None`.

```python
def _store_active_pointer(self, policy: PolicySnapshot, max_retries: int = 3) -> None:
    self._ensure_ready()
    container = self._containers["policies"]
    pointer_id = f"active:{quote(policy.task_id, safe='')}"
    
    for attempt in range(max_retries + 1):
        try:
            # 1. Read existing pointer and capture its ETag
            existing = self._read("policies", pointer_id, policy.agent_id)
            if existing is None:
                # Document does not exist; attempt initial creation
                pointer_doc = {
                    "id": pointer_id,
                    "agent_id": policy.agent_id,
                    "task_id": policy.task_id,
                    "policy_id": policy.id,
                    "policy_version": policy.version,
                    "record_type": "active_policy",
                    "updated_at": _utcnow_iso(),
                }
                container.create_item(pointer_doc)
                return

            existing_version = existing.get("policy_version")
            if existing_version is not None and existing_version > policy.version:
                logger.warning(
                    "Active pointer for %s/%s already at higher version (%s > %s); skipping update",
                    policy.agent_id, policy.task_id, existing_version, policy.version,
                )
                return

            if existing.get("policy_id") == policy.id:
                return  # Identical snapshot already active

            # 2. Prepare replacement doc and execute conditional replace using ETag
            pointer_doc = {
                **existing,
                "policy_id": policy.id,
                "policy_version": policy.version,
                "updated_at": _utcnow_iso(),
            }
            etag = existing.get("_etag")
            container.replace_item(
                item=pointer_id,
                body=pointer_doc,
                etag=etag,
                match_condition=MatchConditions.IfNotModified if etag else None,
            )
            return
        except cosmos_exceptions.CosmosResourceExistsError:
            # Another process created the item in the interim; retry
            if attempt == max_retries:
                raise
        except cosmos_exceptions.CosmosAccessConditionFailedError:
            # ETag mismatch: another process updated the pointer in the interim
            if attempt == max_retries:
                raise
```

## Error Handling & Compatibility

| Condition | Behavior |
|---|---|
| Concurrent write to same active pointer with higher version | Current write detects `existing_version > policy.version` and safely exits without regressing pointer. |
| Concurrent write with conflicting ETag | Catches `CosmosAccessConditionFailedError`, re-reads pointer, and retries up to 3 times. |
| Existing pointer created before this update (lacks `policy_version`) | Falls back to checking whether target snapshot version can be verified via `get_policy()`, then overwrites with enriched schema. |
| `LocalFileStore` and `InMemoryStore` | Unaffected; `LocalFileStore` continues to disclose single-process limitation; `CosmosStore` gains concurrency safety. |

## Out of Scope

- Distributed locks or blob leases (rejected in ADR-002 §4.5).
- Modifying `LearningStore` ABC interface signature (preserves Invariant #1).

