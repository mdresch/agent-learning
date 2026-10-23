# BRD-002: Cosmos Active-Policy Pointer Concurrency Protection

**Source ADR:** [ADR-002](../../adr/ADR-002-storage-backend-strategy.md) — Accepted (2026-10-23), §4.5
**Status:** Approved (2026-10-23, Menno) — derived from an Accepted ADR's disclosed gap; adjudicated via `approve-brd` (robust utility 0.883, episode `6820c1b5...`).
**Stakeholders:** Menno (Sponsor/PM/maintainer). No separate Product Owner exists for this SDK; naming that rather than inventing one.

## Business Need

ADR-002 §4.2 establishes `CosmosStore` as the production backend for distributed, multi-process, and multi-replica workloads. While snapshot history is concurrency-safe because `advance_version()` mints a fresh, unique snapshot `id` for every version, ADR-002 §4.5 disclosed a real concurrency hazard in active pointer management: the `"active:<task_id>"` pointer document is written via an unconditional `upsert_item()`.

If two replicas finish an offline training update or authority migration concurrently for the same `(agent_id, task_id)`:
1. Both snapshots are persisted safely with unique IDs.
2. The replica writing last overwrites the active pointer document unconditionally.
3. If an older policy update (e.g., version 1) lands after a newer one (e.g., version 2), the system silently regresses to the older policy version.

The business risk is not data loss, but **stale-version activation**: autonomous agents in production could execute decisions using regressed, obsolete policy logits despite a newer policy having already been verified and stored. This BRD formalizes the requirements to enforce monotonic, concurrency-safe active pointer updates in `CosmosStore`.

## Business Rules (BRU)

- **BRU-002-01**: Active-policy pointer updates in `CosmosStore` must enforce version monotonicity. An active pointer write must never overwrite an active pointer document if the currently active document's `version` is strictly greater than the candidate policy's `version` (ADR-002 §4.5).
- **BRU-002-02**: Pointer updates must use optimistic concurrency control via ETag matching (`MatchConditions.IfNotModified` / `if_match`) when updating an existing active pointer document, rather than unconditional `upsert_item()`.
- **BRU-002-03**: On an ETag conflict (HTTP 412 Precondition Failed), `CosmosStore` must re-read the active pointer. If the contending write already activated an equal or higher policy version, the conflict is cleanly resolved as a no-op; if the contending write activated an older version or an orthogonal branch, it must retry the update up to a bounded retry cap (default 3 retries).
- **BRU-002-04**: The pointer document must include `policy_version` explicitly alongside `policy_id`, preserving backward compatibility for `get_active_policy()` readers.
- **BRU-002-05**: Storage boundary discipline must be preserved: no sixth `LearningStore` record type may be introduced, and `LocalFileStore` and `InMemoryStore` contracts must remain intact (ADR-002 §4.1, §7 Invariants #1, #2).

## Stakeholder Success Metrics

| Metric | Current state |
|---|---|
| Concurrent policy writes to `CosmosStore` cannot activate an older policy version over a newer one | Not yet true — today unconditional `_upsert` allows last-writer-wins regression (ADR-002 §4.5) |
| Active-policy pointer update in Cosmos uses ETag conditional replace on update | Not yet true — today calls `upsert_item` unconditionally without ETag checking |
| Pointer document explicitly tracks `policy_version` | Not yet true — pointer currently contains only `id`, `agent_id`, `task_id`, `policy_id`, `record_type` |
| `CosmosStore` unit and contract tests verify concurrent update contention handling | Not yet verified — contract tests do not yet test concurrent active pointer races |

## Out of Scope

- Introducing distributed locks, blob leases, or coordination services — ADR-002 §4.5 explicitly selected ETag-conditioned replace as the preferred remediation.
- Adding multi-process concurrency safety to `LocalFileStore` — ADR-002 §5 rejected this; `LocalFileStore` remains single-process by design.
- Altering the five `LearningStore` durable record types or storage interfaces.

