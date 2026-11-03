---
name: meta-prior
description: Guidance for hierarchical meta-prior compilation across a task family (ADR-019, Epic 19): pooling converged low-authority policies into a starting prior.
---

# Skill: meta-prior (agent-learning)

## Overview
A meta-prior pools the converged policies of one task family into a per-role starting value for a new policy. `src/agent_learning/meta_prior.py` holds the pure functions and dataclasses; the commands `task-policy-family-set` and `task-policy-meta-compile` in `cli.py` read and write the store (later stories). Seeding a policy from a prior is the `warm_start_*` provenance of Epic 20, not a command here.

## Governing Specifications & Contracts
- **Architecture:** [`docs/adr/ADR-019-hierarchical-meta-prior-compilation.md`](../../docs/adr/ADR-019-hierarchical-meta-prior-compilation.md)
- **Business Requirements:** [`docs/project-docs/Business-Requirements/BRD-019-hierarchical-meta-prior-compilation.md`](../../docs/project-docs/Business-Requirements/BRD-019-hierarchical-meta-prior-compilation.md)
- **Functional Design:** [`docs/project-docs/Functional-Design/FDD-019-hierarchical-meta-prior-compilation.md`](../../docs/project-docs/Functional-Design/FDD-019-hierarchical-meta-prior-compilation.md)
- **User Stories:** [`docs/user-stories/epic-19-hierarchical-meta-prior-compilation.md`](../../docs/user-stories/epic-19-hierarchical-meta-prior-compilation.md)
- **Test Contracts:**
  - `tests/test_meta_prior_softmax.py` (Story 19.1: pooling logits)
  - `tests/test_meta_prior_thompson.py` (Story 19.2: pooling Beta counts)
  - `tests/test_meta_prior_refusals.py` (Story 19.3: refusing a bad family)

## Load-Bearing Constraints & Invariants
1. **Purity:** `meta_prior.py` imports only the standard library (`math`, `collections.abc`, `dataclasses`, `typing`). No `agent_learning.storage`, no `random`, no `numpy`, no file I/O. The CLI does the reading and writing.
2. **Softmax pooling (FDD-019 §3 item 2):** each member's logits are re-indexed by role and zero-centred (`theta~ = theta - mean over roles`), because softmax ignores a constant added to every logit. `values[role]` is the mean of the centred logits over members; `role_spread[role]` is the square root of `sum((theta~ - mu)^2) / (K - 1)`. Adding any constant to a member's logits changes nothing.
3. **Roles, not ids:** members are compared by the role their `role_map` gives each action, never by action id or by the order of actions. The order of `members` changes nothing in `values` and `role_spread`.
4. **The record:** `roles` is sorted; `compiled_from` is `(task_id, version)` per member in input order; `kappa_prior` is `None` for softmax; `sigma_het` is stored as given.
5. **Not yet built (later stories):** member discovery and the commands (19.4, 19.5), `seed_values` (19.6).
6. **Beta pooling (Story 19.2, FDD-019 §3 item 3):** counts are pooled through payoff rates, never as logits. Per role a member's rate is `(alpha - 1) / (alpha + beta - 2)`; the pooled rate is `sum(alpha - 1) / sum(alpha + beta - 2)`; the prior is `(1 + kappa * rate, 1 + kappa * (1 - rate))`, so its strength `alpha + beta - 2` is `kappa_prior` (default 10.0, recorded on the `MetaPrior`) whatever the members' counts. `role_spread` is the standard deviation (`K - 1`) of the members' payoff rates, not of alpha or beta. `values[role]` is an `(alpha, beta)` tuple.
7. **Synthetic only:** no converged same-family low-authority family exists in the recorded store (FDD-019 §8). Every number in the contract is an arithmetic check, not evidence that a meta-prior speeds convergence (BRU-019-12).
8. **Refusals (Story 19.3, FDD-019 §3 item 1 and §5):** `compile_meta_prior` raises `ValueError` naming the cause, in this order: unknown `representation`; `sigma_het` missing, not finite or not positive; for Beta counts `kappa_prior` not in (0, `KAPPA_MAX` = 10]; fewer than `MIN_FAMILY_SIZE` = 4 members (the count is named); a duplicate `task_id`; per member a gate that is not passed, a `role_map` that misses a `params` action, names an action with no value, or sends two actions to one role, and parameters of the wrong kind (a pair among logits, a float among Beta counts, a non-finite number); role sets that differ (the roles are named); a Beta member with `alpha + beta <= 2` for a role (member and role named), before any pooled rate; and, after pooling, a largest role spread strictly above `sigma_het` (role, spread and `sigma_het` named). Nothing is returned or changed when a family is refused.
9. **`sigma_het` defaults to `None`, meaning missing** (FDD-019 H4: no tuning value is invented). A required keyword that is left out would be a `TypeError`, but AC_3 and FDD-019 §5 want a `ValueError`. A softmax prior ignores `kappa_prior`; it is validated only for Beta counts.
10. **A member's action ids are the keys of its `params`** and its `role_map` must have exactly those keys. The CLI (19.4) excludes unqualified members with reasons before this call (H5); the pure function still refuses one passed to it.
