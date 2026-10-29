# FDD-019: Hierarchical Meta-Prior Compilation Across Task Families

**Source ADR:** [ADR-019](../../adr/ADR-019-hierarchical-meta-prior-compilation.md) — Accepted (2026-10-28)  
**Source BRD:** [BRD-019](../Business-Requirements/BRD-019-hierarchical-meta-prior-compilation.md)  
**Status:** Approved (2026-10-29, Menno) — derived from Accepted ADR-019 and BRD-019; adjudicated via `approve-fdd` (robust utility 0.726, episode `36384424-ef89-49dc-8b69-3791a0a381b9`). Section 4 lists where this design departs from ADR-019 §4.1 to §4.4. Menno confirmed the departures H1 to H7 on 2026-10-29 (H1 as the `standard` tier gate for low-authority policies, H2 as a new command, H7 as pure functions here) and ADR-019 §4.1, §4.3 and §4.4 were amended to match.  

---

## 1. Architecture & Component Placement

1. **Pure module** `src/agent_learning/meta_prior.py` holding `FamilyMember`, `MetaPrior`, `compile_meta_prior`, `seed_values` and `seed_record`. Standard library only: no `numpy`, no `random`, nothing from `agent_learning.storage`, no file I/O.
2. **CLI wiring** in `src/agent_learning/cli.py`: `task-policy-meta-compile` (reads members from the store, builds `FamilyMember` values, calls the pure module, stores the prior) and `task-policy-family-set` (declares `family` and `role_map` on an existing policy, H2). Both follow the pattern of `task-policy-authority-set`: they read and write the store through the CLI composition root only.
3. **Package export:** `FamilyMember`, `MetaPrior`, `compile_meta_prior`, `seed_values` and `seed_record` are re-exported from `agent_learning/__init__.py`.
4. **State in snapshots** (BRU-019-10): a member policy's `PolicySnapshot.metadata` holds `family` and `role_map` (H2). A compiled prior is a `PolicySnapshot` (H6). A seeded policy records `metadata["seeded_from_meta_prior"]` (section 2.3). No new record type.
5. **Shared types are unchanged.** The Thompson representation reads the `posterior_parameters` shape of FDD-015 §2.2, so reading Thompson members from the store depends on Story 15.2 of Epic 15; the pooling itself does not.

---

## 2. Data Contract

### 2.1 Dataclasses
```python
@dataclass(frozen=True)
class FamilyMember:
    task_id: str
    version: int                                     # the active snapshot version (H3)
    role_map: Mapping[str, str]                      # action id -> role
    params: Mapping[str, float | tuple[float, float]]  # logit, or (alpha, beta), keyed by action id
    gate_passed: bool                                # the ADR-003 gate result for the active version (H1)

@dataclass(frozen=True)
class MetaPrior:
    representation: str                              # "softmax" or "thompson"
    roles: tuple[str, ...]                           # sorted
    values: Mapping[str, float | tuple[float, float]]  # per role: pooled logit, or (alpha, beta)
    member_count: int
    role_spread: Mapping[str, float]                 # per-role standard deviation (logits, or payoff rates)
    sigma_het: float
    kappa_prior: float | None                        # None for softmax
    compiled_from: tuple[tuple[str, int], ...]       # (task_id, version) per member, in input order
```

### 2.2 Constants
| Name | Value | Meaning |
|---|---|---|
| `MIN_FAMILY_SIZE` | 4 | the smallest family that is pooled (ADR-019 §4.1) |
| `KAPPA_MAX` | 10.0 | the largest prior strength (ADR-019 §4.2) |

`sigma_het` has no default value (H4). `kappa_prior` defaults to 10.0.

### 2.3 Stored forms
A **member policy** carries `metadata["family"]` (a non-empty string) and `metadata["role_map"]` (action id to role), both written by a human through `task-policy-family-set`.

A **compiled prior** is a `PolicySnapshot` with `task_id` equal to the output name, one `Action` per role, and:
- softmax: `logits` per role holding the pooled values;
- thompson: `metadata["posterior_parameters"] = {"alpha": {role: a}, "beta": {role: b}}`, the shape of FDD-015 §2.2 keyed by role;
- `metadata["is_family_meta_prior"] = true`, `family`, `family_member_count`, `compiled_from` (a list of `{task_id, version}`), `compile_time`, `sigma_het`, `kappa_prior`, `representation`, and `validation_report` (family size, excluded members with reasons, per-role spread);
- `superseded_by` (a snapshot id) once a later compilation replaces it.

A **seeded policy** carries `metadata["seeded_from_meta_prior"] = {"prior_task_id", "prior_snapshot_id", "prior_version", "seeded_at"}`.

---

## 3. Behavior

1. **`compile_meta_prior(members, *, representation, sigma_het, kappa_prior=10.0) -> MetaPrior`.** It raises `ValueError` naming the cause for: fewer than `MIN_FAMILY_SIZE` members; an unknown `representation`; `sigma_het` not finite or not positive; a member with `gate_passed` false; a `role_map` that is not a bijection from the member's action ids onto its roles; member role sets that differ; `params` that do not match the representation (a pair for softmax, a float for thompson, or an action without a value); a duplicate `task_id`; for thompson, `kappa_prior <= 0` or above `KAPPA_MAX`, and any member with `alpha + beta <= 2` for a role (not converged, and the pooled-rate denominator would be zero); and a maximum role spread above `sigma_het`.
2. **Softmax.** For each member the logits are re-indexed by role and zero-centred: `theta~[k][r] = theta[k][r] - mean over q of theta[k][q]`. `mu[r]` is the mean over members of `theta~[k][r]`, and `spread[r]` is the square root of `sum over k of (theta~[k][r] - mu[r])^2 / (K - 1)`. The prior values are `mu`.
3. **Thompson.** For each role `p[k][r] = (alpha - 1) / (alpha + beta - 2)`. The pooled rate is `pbar[r] = sum over k of (alpha[k][r] - 1) / sum over k of (alpha[k][r] + beta[k][r] - 2)`. The prior is `alpha = 1 + kappa * pbar[r]` and `beta = 1 + kappa * (1 - pbar[r])`. `spread[r]` is the standard deviation, with `K - 1` in the denominator, of the `p[k][r]` around their mean.
4. **`seed_values(prior, role_map, action_ids)`** returns, for each of the new policy's action ids, the prior's value for the role the map gives it. It raises `ValueError` unless `role_map` is a bijection from `action_ids` onto `prior.roles`. For softmax the returned logits are the prior's centred values; they carry no evidence (BRU-019-09). The caller writes them into a new policy's snapshot.
5. **`seed_record(prior_snapshot, seeded_at)`** returns the dict of section 2.3 for the seeded policy.
6. **`task-policy-family-set --agent-id A --task-id T --family F --role-map JSON`** writes `family` and `role_map` into the active snapshot's metadata of `T`, without changing its id or version (the pattern of `task-policy-authority-set`). It raises an error for an empty family name, a `role_map` that is not a bijection onto roles, or an action id outside the policy's actions.
7. **`task-policy-meta-compile --agent-id A --family F --output-prior-name N --sigma-het S [--kappa-prior K]`.**
   1. It lists the agent's tasks (`list_agent_tasks`) and takes each task's active policy (`get_active_policy`), ignoring snapshots whose metadata marks them as meta-priors.
   2. A task is a candidate only if its `family` equals `F`. A candidate is **excluded, with a reason in the validation report**, when it is full authority, has no `role_map`, or its ADR-003 gate is not met (H1, H5). The remaining policies become `FamilyMember` values: the representation is thompson when every member has `posterior_parameters`, softmax when every member has no `posterior_parameters`, and a mix is an error.
   3. It calls `compile_meta_prior`. On `ValueError` nothing is stored and the reasons, including the excluded members, are printed with a non-zero exit.
   4. On success it builds the prior snapshot of section 2.3. If a prior with the output name exists, the new snapshot is the next version and the old snapshot gets `superseded_by` (H6). The member snapshots are not written (BRU-019-01).
8. **Seeding is not wired to a command here** (H7).

**Worked checks (arithmetic, to be re-run when built).** Four members with logits `[1.2, -0.3, 0.1]`, `[1.0, -0.1, 0.3]`, `[1.4, -0.5, 0.0]`, `[1.1, -0.2, 0.2]` over roles `(approve, reject, revise)`: after zero-centring the pooled mean is `(0.825, -0.625, -0.200)`, which sums to zero, and the spreads are `(0.2132, 0.1287, 0.0861)`; with `sigma_het = 0.15` the family is refused (0.2132 is above it), and with `sigma_het = 0.25` it is accepted. Adding 5 to every logit of the first member changes nothing. Four Thompson members for one role with `(alpha, beta)` of `(14, 4)`, `(9, 3)`, `(21, 5)`, `(11, 3)` have payoff rates `(0.8125, 0.8, 0.8333, 0.8333)`, a pooled rate `pbar = 0.8226`, and with `kappa = 10` the prior is `alpha = 9.226`, `beta = 2.774`; the spread is `0.0164`.

---

## 4. Departures from ADR-019 §4.1 to §4.4

Each is a place where ADR-019, as first accepted, did not fit the code that exists today or left a gap that code needs closed. Menno confirmed all seven on 2026-10-29 and ADR-019 was amended; the "ADR-019 says" column is the text before that amendment.

| # | ADR-019 says | This FDD does | Why |
|---|---|---|---|
| H1 | A member is converged when it passed "at least 20 scored outcomes, Wilson lower bound >= 0.90"; "the compiler checks the recorded assessment" | `gate_passed` is computed when compiling, by `assess_autonomy` on the member's active snapshot with the thresholds of one stated tier, and only low-authority policies qualify | No assessment is stored anywhere: `assess_autonomy` computes it from episodes. The numbers 20 and 0.90 are the `standard` tier's; the `low` tier needs only 3 outcomes and 0.40, and the gate has further conditions (action probability, margin, stable snapshots). Full-authority policies have no learned logits. Chosen by Menno on 2026-10-29 |
| H2 | `family` and `role_map` are human-set fields in the policy metadata | A command `task-policy-family-set` writes them | `task-policy-init` has no such option and the converged members already exist, so a human needs a way to declare them. Chosen by Menno on 2026-10-29 |
| H3 | `FamilyMember` has no version; `compiled_from` records "each member's snapshot version" | `FamilyMember` carries `version`, and the module defines `MetaPrior` | The provenance cannot be built without the version, and the ADR names the result type without defining it |
| H4 | `sigma_het` is "declared at compile time" | It is a required argument with no default; `kappa_prior` keeps the default 10.0 | The ADR gives no value, and a default would be an invented tuning (the same as FDD-017 F5) |
| H5 | `compile_meta_prior` raises when a member has not passed the gate, and the validation report lists "rejected members with reasons" | The CLI excludes non-qualifying members, with reasons, before compiling; the pure function still refuses an unqualified member passed to it | The two statements fit together only if rejection happens before the call. Otherwise a family with one unconverged member could never be reported, only refused |
| H6 | The prior is "a template snapshot in `LearningStore`" | A `PolicySnapshot` with one `Action` per role, stored under the output name as its task id, never made active, found by `is_family_meta_prior` and left out of member discovery; a later compilation is the next version and marks the old one `superseded_by` | `PolicySnapshot` needs a task id and actions; the prior will appear in `tasks-list`, so discovery has to exclude it |
| H7 | A new policy is initialised from the prior (§4.2) | This epic provides the pure `seed_values` and `seed_record`; the command that applies a prior to a policy is not built here | ADR-020 designs the one seeding command, `task-policy-warm-start`. A second command here would duplicate it. Whether that command accepts a meta-prior is for the ADR-020 FDD. Chosen by Menno on 2026-10-29 |

---

## 5. Error Handling

| Scenario | Behavior |
|---|---|
| Fewer than 4 members | `ValueError` naming the count; nothing stored |
| A member with `gate_passed` false passed to `compile_meta_prior` | `ValueError` naming the task |
| `role_map` not a bijection, or role sets differ | `ValueError` naming the task or the roles |
| Mixed representations among members | CLI error; `ValueError` from the module if `params` do not match |
| Maximum spread above `sigma_het` | `ValueError` naming the role, the spread and `sigma_het` |
| `sigma_het` missing, non-finite or not positive | `ValueError`; the CLI requires the flag |
| `kappa_prior <= 0` or above 10 | `ValueError` |
| A thompson member with `alpha + beta <= 2` for a role | `ValueError` naming the member and role (before the pooled rate) |
| `seed_values` with a `role_map` that is not a bijection onto the prior's roles | `ValueError` |
| `task-policy-family-set` with an empty family or a bad map | error exit; the snapshot is unchanged |
| A candidate that is full authority, lacks a `role_map`, or fails the gate | excluded with its reason in the validation report; not an error unless fewer than 4 remain |
| The family has no member at all | `ValueError` for fewer than 4 members, with an empty exclusion list |

---

## 6. Out of Scope

Building the nine advisory learners; a family registry, cadence or drift parameter; inferring a role map, convergence or family membership; James-Stein shrinkage and meta-learning; one-to-one transfer (ADR-020); the command that applies a prior to a policy (H7); showing faster convergence.

---

## 7. Decisions and Open Questions

1. **H1 to H7: decided (2026-10-29).** Menno confirmed them and ADR-019 was amended to match. H1 is the `standard` tier gate for low-authority policies, H2 the `task-policy-family-set` command, H7 pure seeding functions with the command left to ADR-020.
2. **Open: where seeding is wired.** ADR-020's `task-policy-warm-start` copies one donor's values with a damping factor (`tau`, default 0.70) and records `warm_start_*` provenance. A meta-prior seed has no damping in ADR-019. Whether the same command takes a meta-prior, and whether damping applies, is decided in the ADR-020 FDD.
3. **Open: the nine advisory learners do not exist.** No family can be compiled from real data until they are built, trained and declared; Story 19.6 shows the empty result.
4. **Open: exchangeability.** ADR-019 §6 accepts that one radically different member distorts the mean. `sigma_het` is the only guard, and its value is the maintainer's to set when compiling.
5. **Open: Thompson members.** Reading them from the store depends on the FDD-015 snapshot shape, which is not built.
6. **Open: audit.** Nothing here is part of the audit replay, which supports only the REINFORCE run (FDD-018 §7 item 2).
7. **Walkthrough sketch aligned (2026-10-29).** `examples/methodologies/14-meta-learning/sketch.py` used a family of three, divided by `K`, added a `gamma` to the variance and did not zero-centre. It now uses four members, zero-centres the logits, divides by `K - 1`, adds no `gamma`, and refuses a family whose spread exceeds `sigma_het`, as ADR-019 requires. It is still a sketch, not evidence (ADR-036), and is rewritten against the real module once built.

---

## 8. Test Data

*Real:* none suitable. The `approve-*` tasks share action roles, but they are full authority (ADR-001 §4.2) and pinned there (ADR-021 Invariant 5), so they carry no learned logits and cannot be converged donors. The recorded store therefore holds no family, and Story 19.6 checks that compilation says so. The intended family is the nine advisory learners of `planning-redesign-notes.md` §4.12, which are not built. *Gap:* four or more converged same-family low-authority policies with real episodes, and a human-written `role_map` for each. *Oracle:* the hand-computed pooled means, spreads and Beta prior of section 3, built from constructed members and labelled as arithmetic checks, not as evidence.
