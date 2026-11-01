---
name: warm-start
description: Guidance for explicit prior distribution warm-starting and cross-task policy transfer in agent-learning (ADR-020, Epic 20).
---

# Skill: warm-start (agent-learning)

## Overview
This skill governs the explicit policy prior warm-starting subsystem implemented in `src/agent_learning/warm_start.py` and invoked via `task-policy-warm-start` in `src/agent_learning/cli.py`.

Explicit warm-starting accelerates Bayesian policy convergence by transferring converged action logits from a structurally comparable donor policy to a cold target policy, scaled by an empirical damping factor $\tau \in (0, 1.0]$.

## Governing Specifications & Contracts
- **Architecture:** [`docs/adr/ADR-020-explicit-policy-prior-warm-starting.md`](../../docs/adr/ADR-020-explicit-policy-prior-warm-starting.md)
- **Business Requirements:** [`docs/project-docs/Business-Requirements/BRD-020-explicit-policy-prior-warm-starting.md`](../../docs/project-docs/Business-Requirements/BRD-020-explicit-policy-prior-warm-starting.md)
- **Functional Design:** [`docs/project-docs/Functional-Design/FDD-020-explicit-policy-prior-warm-starting.md`](../../docs/project-docs/Functional-Design/FDD-020-explicit-policy-prior-warm-starting.md)
- **User Stories:** [`docs/user-stories/epic-20-explicit-policy-prior-warm-starting.md`](../../docs/user-stories/epic-20-explicit-policy-prior-warm-starting.md)
- **Test Contracts:**
  - `tests/test_warm_start_logits.py` (Story 20.1 — Arithmetic, entropy monotonicity, validation, purity)
  - `tests/test_warm_start_provenance.py` (Story 20.2 — Provenance metadata generation)
  - `tests/test_warm_start_cli.py` (Story 20.3 — CLI invocation and storage integration)
  - `tests/test_warm_start_gate.py` (Story 20.4 — Autonomy gate evaluation on donor)
  - `tests/test_warm_start_meta_prior.py` (Story 20.5 — Meta-prior seeding)
  - `tests/test_warm_start_real_data.py` (Story 20.6 — Real-data empirical evaluation)

## Load-Bearing Constraints & Invariants
1. **Purity Invariant:** `warm_start.py` is strictly standard-library pure. No `numpy`, no `random`, no `agent_learning.storage`, and no file I/O.
2. **Mathematical Contract:**
   $$\text{target\_logits}[a] = \text{donor\_logits}[\text{action\_map}[a]] \times \tau$$
   where $\tau \in (0, 1.0]$.
3. **Damping Defaults:**
   - Policy-to-policy transfer: $\tau = 0.70$ (`DAMPING_DEFAULT`).
   - Meta-prior transfer: $\tau = 1.0$ (`DAMPING_DEFAULT_META_PRIOR`).
4. **Validation Rules:**
   - Damping $\le 0$, $> 1.0$, `nan`, or `inf` raises `ValueError` explicitly naming `"damping"`.
   - `action_map` must have keys matching `target_actions` exactly (no missing, no extraneous).
   - `action_map` must be injective (no two target actions mapping to the same donor action).
   - Every mapped donor action must exist in `donor_logits`.
   - All donor logits must be finite floating-point numbers.
5. **Autonomy Safety:** Target policy snapshot always starts cold (`version=0`, `episodes_seen=0`, `updates_applied=0`), ensuring the warm-started policy cannot bypass human adjudication gates until empirical evidence accumulates under the new task.

