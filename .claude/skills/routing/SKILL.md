---
name: routing
description: Guidance for Contextual Authority Ensemble Routing (entropy/margin signals, hysteresis route, pinned gates, shadow record and agreement gate) in agent-learning (ADR-021, Epic 21).
---

# Skill: routing (agent-learning)

## Overview
Routes a request to `LOW` or `FULL` decision authority from the entropy and margin of the low policy's distribution, the tier, the bucket's human approval and the previous route of the bucket, and gathers the shadow evidence a human uses to approve a bucket for the fast path. The code lives in `src/agent_learning_ext/routing.py` (FDD-021 §1 names `src/agent_learning/routing.py`; the upstream fork stays untouched, Invariant 6, as recorded in the Story 21.1 to 21.3 contracts).

## Governing Specifications & Contracts
- **Architecture:** [`docs/adr/ADR-021-contextual-authority-ensemble-routing.md`](../../docs/adr/ADR-021-contextual-authority-ensemble-routing.md)
- **Business Requirements:** [`docs/project-docs/Business-Requirements/BRD-021-contextual-authority-ensemble-routing.md`](../../docs/project-docs/Business-Requirements/BRD-021-contextual-authority-ensemble-routing.md)
- **Functional Design:** [`docs/project-docs/Functional-Design/FDD-021-contextual-authority-ensemble-routing.md`](../../docs/project-docs/Functional-Design/FDD-021-contextual-authority-ensemble-routing.md)
- **User Stories:** [`docs/user-stories/epic-21-contextual-authority-ensemble-routing.md`](../../docs/user-stories/epic-21-contextual-authority-ensemble-routing.md)
- **Test Contracts:**
  - `tests/test_routing_signals.py` (Story 21.1: entropy and margin)
  - `tests/test_routing_route.py` (Story 21.2: the route)
  - `tests/test_routing_pinning.py` (Story 21.3: pinned gates)
  - `tests/test_routing_guard.py` (Story 21.4: shadow record and agreement gate)

## Load-Bearing Constraints & Invariants
1. **Purity:** the module imports nothing from any `storage` module, no `random`, no `numpy`, and does no file I/O. Callers read episodes and snapshots and pass them in.
2. **Signals (21.1):** entropy is `-sum p log2 p` (zero terms contribute 0); margin is top minus second probability, a missing second read as 0.
3. **Route (21.2/21.3):** a pinned task (`PINNED_FULL`, eleven tasks) or `requires_human_approval` always routes `FULL` with reason `pinned`, even for invalid input; invalid input otherwise routes `FULL` with reason `anomaly`; `LOW` needs an approved bucket.
4. **Shadow record (21.4):** `shadow_record(low_action_id, entropy_bits)` returns only `shadow_low_action` and `shadow_entropy_bits`; an empty action id or a non-finite (or non-numeric, or `bool`) entropy raises `ValueError`. It carries no reward key, and **no learner may read `shadow_low_action`** (AC_6): it is evidence for a human, never a label.
5. **Previous route (21.4):** derived from episodes (K1), not stored: the newest by `created_at` among episodes whose `routing_bucket` / `routing.bucket` matches and that carry a route; `None` otherwise.
6. **Agreement counting (21.4):** an episode counts only if it is in the bucket, full-routed, has `shadow_low_action`, a `feedback_status` of `accepted`/`rejected`, a **final action** (`correct_action_id`, else `action_id`; an episode with neither is dropped, never counted under a placeholder), and `created_at` inside `[now - max_evidence_age_days, now]`.
7. **Fail closed (21.4, BRU-021-11):** `agreement` with `max_evidence_age_days` of `None` (or non-positive / non-finite) raises `ValueError`.
8. **Gate (21.4, K7):** `propose_bucket` reports `wilson_lower` as exactly `wilson_lower_bound(k, n)` and compares that **unrounded** value with the standard-tier `min_correctness_lower_bound`; rounding before the comparison would admit a bound just below the gate. `n` below `min_outcomes` is never eligible. The 20-outcome floor is not binding: 35 of 35 (0.9011) is the first perfect run to pass 0.90.
9. **Base rate beside, not a gate (ADR-021 §4.4):** `base_rate`, `modal_action` and `mean_shadow_entropy_bits` are reported next to the bound so an approver can see whether agreement exceeds chance.

## Call Sites
- `agent_learning_ext.__init__` lazily exports `route`, `shadow_record`, `previous_route`, `agreement`, `propose_bucket`.
- Planned: `task-policy-routing-set --approve-bucket` (Story 21.5) computes `agreement` then `propose_bucket` and refuses unless eligible.
