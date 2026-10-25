# Epic 2: Cosmos Active-Policy Pointer Concurrency Protection

**Source ADR:** [ADR-002](../adr/ADR-002-storage-backend-strategy.md) — Accepted (2026-10-23), §4.5
**Source BRD/FDD:** [BRD-002](../project-docs/Business-Requirements/BRD-002-cosmos-active-policy-optimistic-concurrency.md) / [FDD-002](../project-docs/Functional-Design/FDD-002-cosmos-active-policy-optimistic-concurrency.md)

One story, matching FDD-002's designs.

## Story 2.1 — Implement Optimistic Concurrency and Monotonicity Guard for Cosmos Active Pointer

**Status:** Completed (2026-10-25) — implemented in feat/story-2.1 with contract tests in tests/test_storage_cosmos.py.
**As** an engineer running multi-replica agent workloads with `CosmosStore`, **I want** active-policy pointer updates to be protected by ETag concurrency checks and version monotonicity checks, **so that** a racing policy update cannot overwrite or regress the active pointer to an older version.

**Acceptance Criteria:**
- $AC_0$: `CosmosStore.store_policy()` writes the `"active:<task_id>"` pointer document with `policy_version: policy.version` and `updated_at` in ISO format.
- $AC_1$: When an active pointer document already exists in Cosmos with `policy_version > candidate.version`, `CosmosStore.store_policy()` does not overwrite the pointer, logs a warning, and returns the candidate snapshot ID safely.
- $AC_2$: Updating an existing active pointer uses `replace_item` with `etag` and `MatchConditions.IfNotModified`; an ETag conflict (`CosmosAccessConditionFailedError`) triggers re-reading the pointer and retrying up to 3 times.
- $AC_3$: When the active pointer does not exist initially, creation uses `create_item()`; racing creations raising `CosmosResourceExistsError` retry via the update path.
- $AC_4$: `CosmosStore.get_active_policy()` continues to correctly resolve active policies across both legacy (version-less) and enhanced pointer documents without regression.

## Not a story — out of scope per BRD-002/FDD-002

Distributed locking across Cosmos replicas, multi-process concurrency locks in `LocalFileStore`, and creating a sixth `LearningStore` record type are excluded per ADR-002 §4.5 and §5.

