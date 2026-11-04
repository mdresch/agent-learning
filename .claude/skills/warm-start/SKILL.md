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
6. **Provenance Contract (Story 20.2):**
   - Records complete lineage in snapshot metadata:
     - `warm_start_donor_policy_id`: Donor's snapshot UUID.
     - `warm_start_donor_task_id`: Donor's task identifier.
     - `warm_start_donor_version`: Donor's version integer.
     - `warm_start_damping_factor`: Scale factor $\tau \in (0, 1.0]$.
     - `warm_started_at`: Time string passed via `now` argument (no internal clock reads).
     - `warm_start_action_map`: Dictionary mapping target action to donor action.
     - `warm_start_donor_kind`: `"policy"` or `"meta_prior"` (default `"policy"`).
     - `warm_start_donor_gate_met`: Boolean or `None` (`null` in JSON).
   - JSON Safe: Must round-trip losslessly through `json.dumps` and `json.loads`.
7. **CLI Wiring & Refusal Rules (Story 20.3):**
   - Command: `task-policy-warm-start --agent-id <A> --target-task-id <T> (--donor-task-id <D> | --meta-prior <N>) [--damping <X>] [--action-map <JSON>]`
   - Target must be a delegated decision policy with low authority (`decision_authority != "full"`), and strictly cold:
     `updates_applied == 0`, `episodes_seen == 0`, all logits equal to `0.0`, and no prior `warm_start_donor_policy_id` in metadata.
   - Donor must be a different task than target, low authority (`decision_authority != "full"`), and possess at least one logit.
   - Action map: if omitted and action ID sets match identically, identity map is used; if action IDs differ, `--action-map` is mandatory; bad/incomplete maps exit non-zero.
   - `--action-map` is an existing file path if `Path(value).is_file()`, otherwise inline JSON; never discriminate on a leading `{`. The parsed value must be a `dict` (Q-83-9).
   - `--damping` is validated at parse time to `(0, 1.0]` by `_damping_factor`; the handler also sets `updates_applied = 0` on the new snapshot explicitly (Q-83-8, Q-83-10).
   - Atomic storage & isolation: only the new target snapshot version is stored and made active (`store.store_policy(new_target)`). The donor is never touched and never stored (`store_policy` is never called for donor). On any error or refusal, zero writes are made.
8. **No borrowed evidence (Story 20.4):** a warm-started target has `episodes_seen` 0 and is not eligible under `assess_autonomy` on any tier; its copied logits are not outcomes. `warm_start_donor_gate_met` is computed with `AutonomyConfig.for_tier("standard")` (a string literal: `AutonomyTier` is a `Literal`, not an enum, so `AutonomyTier.STANDARD` raised and the broad `except` recorded `false` for every donor until this story). The gate result is recorded only; the copy proceeds either way. The donor is never written, and a later update of the target stores a further target version only.
9. **Seeding from a meta-prior (Story 20.5, FDD-020 §2.1 item 3, J5):** `task-policy-warm-start --meta-prior N` runs the same cold-target checks, then `_warm_start_from_meta_prior`. The prior is the highest-version stored snapshot of `N` (`cli._latest_meta_prior`); it is refused when missing, when it is not a meta-prior, when another stored snapshot of `N` names it in `supersedes` (replaced out of order), and when it is in Beta counts (`representation` thompson or `posterior_parameters` present). The target must declare `family` equal to the prior's and a non-empty `role_map`; `--action-map` is refused. `cli._prior_from_snapshot` reads the stored snapshot back into a `MetaPrior` (roles = sorted action ids, values = logits); `seed_values(prior, role_map, action_ids)` gives the values and they are multiplied by the damping, which defaults to `DAMPING_DEFAULT_META_PRIOR` (1.0). Provenance: kind `meta_prior`, the prior snapshot's id, task id and version, the target's `role_map` as `warm_start_action_map`, `warm_start_donor_gate_met` null. The prior is never written. A `ValueError` from `seed_values` (a role map that is not a bijection onto the prior's roles) is an exit 2 and writes nothing. A stored prior with an action that has no logit is a `ValueError` naming the role (exit 2), never a made-up zero (Q-100-1). `seed_values` returns exactly the given action ids or raises `ValueError`, so no `KeyError` can come from it.
10. **The real-data check (Story 20.6) is a statement that no usable donor exists yet.** Over the recorded `approve-*` tasks of `agent-learning-governance`: the explicit map `approve_adr -> approve_brd`, `reject_adr -> reject_brd`, `request_revision_before_decision -> request_revision_before_decision` is accepted by `warm_start_logits`, the identity map is refused (the ids differ), and every recorded policy as donor is refused as full authority with the store unchanged (ADR-001 section 4.2, ADR-021 Invariant 5: they carry no learned logits). It makes no claim that a warm start reduces supervision (BRU-020-11). Missing data: one converged low-authority policy and a cold target of the same family. `data/agent-learning/` is git-ignored, so the test rebuilds a store from the committed episodes, action files and decision results (FDD-020 §7 item 7); do not rely on a store under `data/agent-learning/` in a test that must run in CI.
