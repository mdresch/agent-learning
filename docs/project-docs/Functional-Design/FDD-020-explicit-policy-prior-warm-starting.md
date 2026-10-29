# FDD-020: Explicit Policy Prior Warm-Starting

**Source ADR:** [ADR-020](../../adr/ADR-020-explicit-policy-prior-warm-starting.md) — Accepted (2026-10-28)  
**Source BRD:** [BRD-020](../Business-Requirements/BRD-020-explicit-policy-prior-warm-starting.md)  
**Status:** Approved (2026-10-29, Menno) — derived from Accepted ADR-020 and BRD-020; adjudicated via `approve-fdd` (robust utility 0.726, episode `50914a5d-1fd7-405c-ba9c-8a412fc60049`). Section 4 lists where this design departs from ADR-020 §4.1 to §4.4. Menno confirmed the departures J1 to J6 on 2026-10-29 (J1 as record-but-do-not-block, J5 as the same command with a default damping of 1.0) and ADR-020 §4.1, §4.2, §4.3 and §4.4 were amended to match.  

---

## 1. Architecture & Component Placement

1. **Pure module** `src/agent_learning/warm_start.py` holding `warm_start_logits` and `provenance`. Standard library only: no `numpy`, no `random`, nothing from `agent_learning.storage`, no file I/O.
2. **CLI wiring** in `src/agent_learning/cli.py`: `task-policy-warm-start`, which does every read and write, in the manner of `task-policy-authority-set`. It reads the target and the donor with `get_active_policy`, and writes one new snapshot with `store_policy`.
3. **Package export:** `warm_start_logits` and `provenance` are re-exported from `agent_learning/__init__.py`.
4. **State in the snapshot** (BRU-020-07): the transfer is recorded in `PolicySnapshot.metadata` only (section 2.2).
5. **The store moves the active pointer on every `store_policy`.** Both `LocalFileStore` and `CosmosStore` set the active-policy pointer of the stored snapshot's task, and the Cosmos store refuses to move it to a lower version. A new version of the target is therefore made active simply by storing it. Nothing else is stored, so the donor is never written.
6. **Meta-prior donors** use the pure `seed_values` of FDD-019 §3 item 4 for the role mapping (J5). Thompson policies are not covered (BRD-020 Out of Scope).

---

## 2. Data Contract

### 2.1 Constants
| Name | Value | Meaning |
|---|---|---|
| `DAMPING_DEFAULT` | 0.70 | the default for a policy donor (ADR-020 §4.1) |
| `DAMPING_DEFAULT_META_PRIOR` | 1.0 | the default for a meta-prior donor, which ADR-019 §4.2 initialises undamped (J5) |

### 2.2 Provenance
`provenance(donor, damping, now, *, action_map, kind="policy", gate_met=None)` returns the keys of ADR-020 §4.3 and three more (J1, J3):
```json
{
  "warm_start_donor_policy_id": "9a7d3f12-...",
  "warm_start_donor_task_id": "approve-quality-plan",
  "warm_start_donor_version": 4,
  "warm_start_damping_factor": 0.75,
  "warm_started_at": "2026-10-29T08:00:00+00:00",
  "warm_start_action_map": {"approve_plan": "approve_plan"},
  "warm_start_donor_kind": "policy",
  "warm_start_donor_gate_met": true
}
```
`warm_start_donor_kind` is `"policy"` or `"meta_prior"`. For a meta-prior the donor ids are those of the prior snapshot and `warm_start_action_map` is the target's `role_map` (action id to role). `warm_start_donor_gate_met` is `null` for a meta-prior. The action ids above are placeholders.

---

## 3. Behavior

1. **`warm_start_logits(donor_logits, action_map, target_actions, *, damping=0.70) -> dict[str, float]`.** It raises `ValueError` for: `damping` not finite, not above 0 or above 1; `action_map` keys that are not exactly the set of `target_actions`; two target actions mapped to the same donor action; a mapped donor action absent from `donor_logits`; a non-finite donor logit. It returns, for each target action `a`, `donor_logits[action_map[a]] * damping` (J6). Donor actions that no target action maps to are ignored.
2. **`provenance(...)`** returns the dict of section 2.2 and does not read the clock: `now` is passed in.
3. **`task-policy-warm-start --agent-id A --target-task-id T (--donor-task-id D | --meta-prior N) [--damping X] [--action-map JSON]`.**
   1. The target is `get_active_policy(A, T)`. It must be a delegated decision policy (`metadata["policy_scope"]` of the decision-policy scope), low authority (`decision_authority` is not `full`), and **cold**: `updates_applied` 0, `episodes_seen` 0, every logit 0.0, and no `warm_start_donor_policy_id` in its metadata (J2). Otherwise the command exits non-zero naming the reason and writes nothing.
   2. **Policy donor (`--donor-task-id`).** The donor is `get_active_policy(A, D)`, a different task from the target, low authority, with at least one logit. `--action-map` is required unless the donor and target action ids are identical, in which case the identity map is used (J6). The command computes whether the donor's ADR-003 gate is met with `assess_autonomy` (the `standard` tier thresholds) and records it as `warm_start_donor_gate_met`; it does not block on it (J1). The damping defaults to 0.70.
   3. **Meta-prior donor (`--meta-prior N`)** (J5). The donor is the latest snapshot of task `N` with `is_family_meta_prior`, softmax representation, and not superseded. The target must declare `family` equal to the prior's and a `role_map` (FDD-019 §2.3); `--action-map` is not allowed. The values come from `seed_values(prior, role_map, action_ids)` and are then damped by `tau`, which defaults to 1.0 for a meta-prior (ADR-019 §4.2).
   4. A copy of the target snapshot is made. Its `logits` are set to the result, `episodes_seen` and `baseline` stay 0, the provenance is added to its metadata, `advance_version()` is called, and `store_policy` stores it, which makes it the active policy of `T` (item 5 of section 1). The previous version stays stored and unchanged (J4).
   5. The donor and every episode are not written, so the donor is unchanged (BRU-020-03). The command prints the new snapshot and the provenance.
4. **After the copy** the policy trains as any other: later updates create further versions of the target only.

**Worked checks (arithmetic, to be re-run when built).** Donor logits `approve 2.0`, `reject -1.0`, `escalate 0.0`; map `accept -> approve`, `decline -> reject`, `ask -> escalate`. With `tau = 1.0` the new logits are `(2.0, -1.0, 0.0)` and the softmax is `(0.8438, 0.0420, 0.1142)` with entropy 0.5243. With `tau = 0.70` the logits are `(1.4, -0.7, 0.0)`, the softmax `(0.7304, 0.0894, 0.1801)` and the entropy 0.7541. With `tau = 0.50` the softmax is `(0.6285, 0.1402, 0.2312)` and the entropy 0.9060.

---

## 4. Departures from ADR-020 §4.1 to §4.4

Each is a place where ADR-020, as first accepted, left a gap that code needs closed or did not fit the code that exists today. Menno confirmed all six on 2026-10-29 and ADR-020 was amended; the "ADR-020 says" column is the text before that amendment.

| # | ADR-020 says | This FDD does | Why |
|---|---|---|---|
| J1 | The donor is "a converged donor"; "Requires human operator to select a valid, structurally comparable donor policy"; no check is specified | Structural checks (low authority, has logits, a valid map) block; whether the donor's ADR-003 gate is met is computed and recorded as `warm_start_donor_gate_met` but does not block | The ADR makes the donor a human judgement and names negative transfer as a known cost. A hard gate would contradict that; recording it keeps the audit trail honest. Needs Menno's choice |
| J2 | Warm-starting "a new policy", with no check that it is new | The target must be cold (no update, no episodes seen, all logits zero, no earlier warm start); otherwise the command refuses and writes nothing | Without it the command could overwrite logits a policy had learned |
| J3 | Provenance keys: donor policy id, task id, version, damping, time | Adds `warm_start_action_map`, `warm_start_donor_kind` and `warm_start_donor_gate_met` | The map is needed to reproduce the copy, and the kind distinguishes a policy donor from a meta-prior |
| J4 | "The recipient snapshot records the transfer in `PolicySnapshot.metadata`" | The copy is a new version of the target, stored and made active; the previous version is kept | A decision result is bound to an exact policy id and version, so changing logits in place would leave earlier decisions tied to values they were not made under. `store_policy` makes the new version active |
| J5 | Not stated (ADR-019 §4.2 initialises a new policy from a meta-prior and names no command) | The same command takes `--meta-prior`, the map comes from the target's declared `role_map`, the damping default is 1.0 and the kind is `meta_prior`; softmax only | One seeding path instead of two; ADR-019 initialises from the pooled mean undamped, so the default differs from the 0.70 of ADR-020. This supersedes FDD-019's separate `seed_record` and its `seeded_from_meta_prior` key. Needs Menno's choice |
| J6 | `m` maps recipient actions to donor actions; "an exact action-set match or an explicit complete bijection"; §4.4 says "not a complete bijection onto the target actions" | The map's keys are exactly the target actions and its values are distinct donor actions; donor actions nobody maps to are ignored; the map may be omitted only when the id sets are identical | "Bijection onto the target actions" cannot be a bijection when the donor has more actions. The rule above is what the formula needs |

---

## 5. Error Handling

| Scenario | Behavior |
|---|---|
| `damping` outside (0, 1] or non-finite | `ValueError`; the command exits non-zero, nothing written |
| `action_map` keys differ from the target actions, two targets map to one donor action, or a mapped donor action is missing | `ValueError` naming it; nothing written |
| No `--action-map` and the action ids differ | error naming both sets; nothing written |
| The target is not a decision policy, is full authority, or is not cold | error naming the reason; nothing written |
| The donor is the target, is full authority, or has no logits | error; nothing written |
| `--meta-prior` with no matching prior, a superseded prior, a non-softmax prior, or a target whose `family` or `role_map` does not match | error; nothing written |
| `--donor-task-id` and `--meta-prior` together, or neither | error |
| `--action-map` together with `--meta-prior` | error |
| Donor gate not met | the copy proceeds; `warm_start_donor_gate_met` is false |

---

## 6. Out of Scope

Measuring the effect on supervision (HYP-AL-008); Thompson policies; choosing a donor or inferring a map; the audit replay of a warm start; a shared global weight vector.

---

## 7. Decisions and Open Questions

1. **J1 to J6: decided (2026-10-29).** Menno confirmed them and ADR-020 was amended to match. J1 records the donor gate without blocking, and J5 uses the same command with a default damping of 1.0.
2. **Open, and a correction to merged documents: how the stores treat the prior of ADR-019.** `store_policy` sets the active pointer of the stored snapshot's task on both stores. FDD-019 H6, ADR-019 §4.3 and Story 19.5 say the stored prior is "never made the active policy"; for the prior's own output name that is not what the store does, and it also lists the prior under `tasks-list`. They also mark the old prior `superseded_by` by storing it again, which on `LocalFileStore` would move the pointer back to the old version while `CosmosStore` refuses to. A separate correction should make a prior the active policy of its own pseudo-task, mark supersession on the newer snapshot (`supersedes`) instead of rewriting the older one, and drop `seed_record` in favour of J5.
3. **Open: Thompson warm start.** The copy of a Beta posterior is a different operation from damping a logit and depends on the FDD-015 snapshot, which is not built.
4. **Open: effect measurement.** HYP-AL-008 needs a real converged donor and a cold-start comparison; neither exists.
5. **Open: audit.** Provenance lives in the snapshot metadata. The warm start is not a training run and is not in the audit replay (FDD-018 §7 item 2).
6. **Walkthrough sketch.** `examples/methodologies/15-warm-start/sketch.py` computes the damped softmax correctly and needs no change beyond the arithmetic check of section 3.

---

## 8. Test Data

*Real:* the `approve-*` action sets give real action-map cases (the same role mapping as ADR-019). They are full authority and carry no learned logits, so they are not usable donors and a real transfer cannot be run. *Gap:* one policy that has actually converged, and a cold target of the same family. *Oracle:* the damping arithmetic and entropies of section 3, built from constructed policies, labelled as arithmetic checks, not as evidence.
