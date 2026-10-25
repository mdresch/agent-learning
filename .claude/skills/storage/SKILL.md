---
name: storage
description: Guidance and constraints for LearningStore storage backends (InMemoryStore, LocalFileStore, CosmosStore), including active-policy pointer concurrency and monotonicity guards.
---

# Component Skill: Storage Backends (`agent_learning.storage`)

## 1. Governing Architecture & Specifications
- **ADR:** [ADR-002](../../docs/adr/ADR-002-storage-backend-strategy.md) — Storage Backend Strategy (§4.5 Cosmos active-policy pointer concurrency).
- **BRD:** [BRD-002](../../docs/project-docs/Business-Requirements/BRD-002-cosmos-active-policy-optimistic-concurrency.md) — Cosmos Active-Policy Pointer Optimistic Concurrency.
- **FDD:** [FDD-002](../../docs/project-docs/Functional-Design/FDD-002-cosmos-active-policy-optimistic-concurrency.md) — Cosmos Active-Policy Pointer Concurrency Protection.
- **Story:** [Story 2.1](../../docs/user-stories/epic-2-cosmos-active-policy-optimistic-concurrency.md) — Implement Optimistic Concurrency and Monotonicity Guard for Cosmos Active Pointer.

## 2. Load-Bearing Invariants & Constraints
- **Invariant #1 (ABC Surface Stability):** Never modify `LearningStore` ABC public method signatures. `store_policy(policy: PolicySnapshot) -> str` and `get_active_policy(agent_id: str, task_id: str) -> Optional[PolicySnapshot]` must remain unchanged.
- **Invariant #2 (No Schema Expansion):** Do NOT introduce a sixth record type container. The active pointer lives in the `policies` container with `id = f"active:{task_id}"` and partition key `agent_id`.
- **Active Pointer Schema Enrichment:**
  ```python
  {
      "id": f"active:{quote(policy.task_id, safe='')}",
      "agent_id": policy.agent_id,
      "task_id": policy.task_id,
      "policy_id": policy.id,
      "policy_version": policy.version,
      "record_type": "active_policy",
      "updated_at": _utcnow_iso(),
  }
  ```
- **Monotonicity Guard:** If an active pointer already exists with `policy_version > candidate.version`, do NOT overwrite the pointer. Log a warning and safely return the candidate snapshot ID. If the existing pointer is legacy (lacks `policy_version`), fetch the existing policy snapshot to check version before overwriting.
- **Optimistic Concurrency Control:**
  - Pointer updates execute `replace_item(item=pointer_id, body=pointer_doc, etag=etag, match_condition=MatchConditions.IfNotModified)`.
  - Conflict with `CosmosAccessConditionFailedError` triggers re-reading the pointer and retrying up to 3 times (4 attempts total).
  - Race condition during initial creation raising `CosmosResourceExistsError` retries via the update path.
- **Scope Boundaries:**
  - Distributed locks (ZooKeeper, Redis, Azure Blob Leases) are explicitly out of scope per ADR-002 §4.5.
  - Multi-process file locking in `LocalFileStore` is out of scope; `LocalFileStore` is explicitly documented as single-process.

## 3. Contract Files
- `tests/test_storage_cosmos.py`
- `tests/test_storage_local.py`
- `tests/test_storage_memory.py`
- `tests/test_default_store.py`

## 4. Key Call Sites
- `src/agent_learning/storage/cosmos.py`:
  - `CosmosStore.store_policy()`
  - `CosmosStore._store_active_pointer()`
  - `CosmosStore.get_active_policy()`

