# Epic 20: Explicit Policy Prior Warm-Starting

**Source ADR:** [ADR-020](../adr/ADR-020-explicit-policy-prior-warm-starting.md) — Accepted (2026-10-28)  
**Source BRD/FDD:** [BRD-020](../project-docs/Business-Requirements/BRD-020-explicit-policy-prior-warm-starting.md) / [FDD-020](../project-docs/Functional-Design/FDD-020-explicit-policy-prior-warm-starting.md)  
**Status:** Approved (2026-10-29, Menno) — stories derived from Accepted ADR-020, BRD-020 and FDD-020; adjudicated via `approve-user-stories` (robust utility 0.735, episode `9d327883-440f-47cb-bf8e-b670f873ae53`). The epic number follows the source ADR number, as Epic 19 follows ADR-019.  

Six stories build `src/agent_learning/warm_start.py` and the command `task-policy-warm-start` in `cli.py`. Each rule sits in exactly one story's criteria (LL-012). Contract tests are `tests/test_warm_start_logits.py` (20.1), `tests/test_warm_start_provenance.py` (20.2), `tests/test_warm_start_cli.py` (20.3), `tests/test_warm_start_gate.py` (20.4), `tests/test_warm_start_meta_prior.py` (20.5) and `tests/test_warm_start_real_data.py` (20.6). Measuring the effect on supervision (HYP-AL-008) and Thompson warm starts are not stories (BRD-020 Out of Scope).

**Stories 20.1 to 20.6 are unblocked except for one dependency:** Menno confirmed FDD-020 §4 (J1 to J6) on 2026-10-29 and ADR-020 was amended to match. Story 20.5 depends on Epic 19 (Stories 19.5 and 19.6) and on the correction of FDD-019 named in FDD-020 §7 item 2; Stories 20.1 to 20.4 and 20.6 depend on no other epic.

Fixture used by the criteria below ("the base donor"): a low-authority softmax policy `donor-task` with actions `approve`, `reject`, `escalate` and logits `2.0`, `-1.0`, `0.0`; and a cold target `target-task` with actions `accept`, `decline`, `ask` and the map `accept -> approve`, `decline -> reject`, `ask -> escalate`. Both are built in the tests and labelled synthetic.

---

## Story 20.1 — The Damped Copy

**Status:** Ready  
**As** a maintainer, **I want** the new policy's logits computed from the donor's by one stated formula, **so that** a transfer can be checked by hand.

### Acceptance Criteria:
- **$AC_0$ (Arithmetic):** `warm_start_logits` on the base donor gives `{accept: 1.4, decline: -0.7, ask: 0.0}` within 1e-12 for the default damping 0.70, and `{2.0, -1.0, 0.0}` for damping 1.0, recomputed in the test as `donor * damping`.
- **$AC_1$ (Entropy):** the softmax entropy of the result is 0.5243 for damping 1.0, 0.7541 for 0.70 and 0.9060 for 0.50 within 1e-4, and over a grid of damping values in (0, 1] it never decreases as damping falls.
- **$AC_2$ (Damping Bounds):** damping of 0, a negative value, 1.0001, 1.5, `nan` and `inf` each raise `ValueError` naming the argument; 1.0 and 0.0001 are accepted.
- **$AC_3$ (Complete Map):** an `action_map` whose keys differ from the target actions (one missing, or one extra) raises `ValueError`.
- **$AC_4$ (One To One):** two target actions mapped to the same donor action raise `ValueError`; a map to a donor action absent from the donor logits raises `ValueError`; donor actions that no target maps to are ignored.
- **$AC_5$ (Donor Values):** a non-finite donor logit raises `ValueError`.
- **$AC_6$ (Pure):** the donor logits and the map are equal to their copies after the call, and `warm_start.py` imports nothing from `agent_learning.storage`, no `random` and no `numpy`.

---

## Story 20.2 — The Provenance Record

**Status:** Ready  
**As** an auditor, **I want** each warm start to say exactly what was copied from where, **so that** I can trace which policy seeded which.

### Acceptance Criteria:
- **$AC_0$ (Keys):** `provenance` returns `warm_start_donor_policy_id`, `warm_start_donor_task_id`, `warm_start_donor_version`, `warm_start_damping_factor`, `warm_started_at`, `warm_start_action_map`, `warm_start_donor_kind` and `warm_start_donor_gate_met`, with the donor's snapshot id, task id and version.
- **$AC_1$ (Kind):** `kind` defaults to `"policy"`; `"meta_prior"` is accepted; any other value raises `ValueError`; `gate_met` of `None` is stored as `null`.
- **$AC_2$ (No Clock):** the time is the `now` argument unchanged; the function reads no clock.
- **$AC_3$ (JSON Safe):** the result survives `json.dumps` and `json.loads` unchanged and the donor snapshot is equal to its copy afterwards.

---

## Story 20.3 — The Command for a Policy Donor

**Status:** Ready  
**As** a maintainer, **I want** one command that copies a donor's damped logits into a new policy, **so that** warm starting is a recorded, repeatable step.

### Acceptance Criteria:
- **$AC_0$ (New Version):** `task-policy-warm-start` on the base donor and target stores one new snapshot of `target-task` with the next version, logits `{accept: 1.4, decline: -0.7, ask: 0.0}`, `episodes_seen` 0, the provenance of Story 20.2 in its metadata, and it is the active policy of `target-task`; the earlier version is stored and unchanged.
- **$AC_1$ (Donor Untouched):** the donor snapshot and its episodes are equal to their copies after the command, and `store_policy` was never called for the donor.
- **$AC_2$ (Map Rules):** without `--action-map` and with different action ids the command exits non-zero naming both sets; with identical action ids and no map it uses the identity map; a bad map exits non-zero.
- **$AC_3$ (Cold Target Only):** a target with `updates_applied` above 0, with `episodes_seen` above 0, with any logit not zero, or with an earlier `warm_start_donor_policy_id` exits non-zero naming the reason; a target that is not a decision policy or is full authority does the same.
- **$AC_4$ (Donor Checks):** a donor that is the target, is full authority, or has no logits exits non-zero.
- **$AC_5$ (Nothing Written On Refusal):** after every refusal above and every `ValueError` of Story 20.1 the store is equal to its earlier state.
- **$AC_6$ (Flags):** `--donor-task-id` and `--meta-prior` together, or neither, exit non-zero; the damping defaults to 0.70.

---

## Story 20.4 — No Borrowed Evidence

**Status:** Ready  
**As** an auditor, **I want** a warm-started policy to earn its autonomy itself, **so that** copied logits never stand in for outcomes.

### Acceptance Criteria:
- **$AC_0$ (Gate Unchanged):** after a warm start the target, with no episodes, is not eligible under `assess_autonomy` with the thresholds of its own tier, and its `episodes_seen` is 0.
- **$AC_1$ (Donor Gate Recorded):** `warm_start_donor_gate_met` is true when the donor meets the `standard` tier gate in the test and false when it does not, and in both cases the copy proceeds.
- **$AC_2$ (Decoupled):** after the target's logits are changed by a later update, which stores a further version of the target, the donor snapshot and its episodes are equal to their copies from before the warm start.

---

## Story 20.5 — Seeding From a Family Meta-Prior

**Status:** Ready — depends on Epic 19 Stories 19.5 and 19.6 and on the correction of FDD-019 (FDD-020 §7 item 2).  
**As** a maintainer, **I want** the same command to start a new family member from the family's pooled prior, **so that** there is one way to seed a policy.

### Acceptance Criteria:
- **$AC_0$ (Same Values):** `--meta-prior N` on a target that declares the prior's `family` and a `role_map` stores logits equal to `seed_values` of FDD-019 times the damping, and the provenance has kind `meta_prior`, the prior's snapshot id, task id and version, and the target's `role_map` as the action map.
- **$AC_1$ (Default Damping):** the damping defaults to 1.0 for a meta-prior, so the logits equal `seed_values` exactly; `--damping 0.5` halves them.
- **$AC_2$ (Matching Declaration):** a target without `family`, with another family, or without a `role_map` exits non-zero and writes nothing.
- **$AC_3$ (Which Prior):** the latest non-superseded prior of the name is used; a superseded one, a missing one, and a prior in Beta counts each exit non-zero.
- **$AC_4$ (Exclusive Flags):** `--action-map` with `--meta-prior` exits non-zero.
- **$AC_5$ (Prior Untouched):** the prior snapshot is equal to its copy after the command.

---

## Story 20.6 — The Real-Data Check (No Donor)

**Status:** Ready  
**As** a maintainer, **I want** the command tried on the recorded policies, **so that** the missing real donor is shown, not assumed.

### Acceptance Criteria:
- **$AC_0$ (Real Source):** the store is a temporary copy of the committed one under `data/agent-learning/store`; the policies found, their action ids and their authority are recorded in the test.
- **$AC_1$ (Real Action Sets):** for `approve-adr` as target and `approve-brd` as donor, the explicit map `approve_adr -> approve_brd`, `reject_adr -> reject_brd`, `request_revision_before_decision -> request_revision_before_decision` is accepted by `warm_start_logits`, while the identity map is refused because the ids differ; this gives real action-map cases.
- **$AC_2$ (No Usable Donor):** `task-policy-warm-start` with any recorded `approve-*` policy as donor exits non-zero because it is full authority, and the copy of the store is equal to its earlier state.
- **$AC_3$ (Labelled):** the result is recorded as a statement that no converged low-authority donor exists yet. It makes no claim that a warm start reduces supervision (BRU-020-11), and the docstring names the missing data (one policy that has converged and a cold target of the same family).
