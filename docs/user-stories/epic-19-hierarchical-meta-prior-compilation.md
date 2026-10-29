# Epic 19: Hierarchical Meta-Prior Compilation Across Task Families

**Source ADR:** [ADR-019](../adr/ADR-019-hierarchical-meta-prior-compilation.md) — Accepted (2026-10-28)  
**Source BRD/FDD:** [BRD-019](../project-docs/Business-Requirements/BRD-019-hierarchical-meta-prior-compilation.md) / [FDD-019](../project-docs/Functional-Design/FDD-019-hierarchical-meta-prior-compilation.md)  
**Status:** Approved (2026-10-29, Menno) — stories derived from Accepted ADR-019, BRD-019 and FDD-019; adjudicated via `approve-user-stories` (robust utility 0.735, episode `13fbf581-1222-49d1-8b5c-06eaf2843811`); corrected 2026-10-29 (Stories 19.5 and 19.6, FDD-019 H8) and re-approved via `approve-user-stories` (robust utility 0.739, episode `bf3c50c4-178f-4120-88be-e5029f054c75`; comparison with the previous approval: flat, within tolerance, no criterion lower). The epic number follows the source ADR number, as Epic 18 follows ADR-018.  

Seven stories build `src/agent_learning/meta_prior.py` and the two commands `task-policy-family-set` and `task-policy-meta-compile` in `cli.py`. Each rule sits in exactly one story's criteria (LL-012). Contract tests are `tests/test_meta_prior_softmax.py` (19.1), `tests/test_meta_prior_thompson.py` (19.2), `tests/test_meta_prior_refusals.py` (19.3), `tests/test_meta_prior_members.py` (19.4), `tests/test_meta_prior_store.py` (19.5), `tests/test_meta_prior_seed.py` (19.6) and `tests/test_meta_prior_real_data.py` (19.7). Building the nine advisory learners, wiring the seeding command (ADR-020) and showing faster convergence are not stories (BRD-019 Out of Scope).

**Stories 19.1 to 19.7 are unblocked except for one dependency:** Menno confirmed FDD-019 §4 (H1 to H7) on 2026-10-29 and ADR-019 was amended to match. Story 19.4's criterion for Thompson members depends on Story 15.2 of Epic 15; the rest of the epic depends on no other epic.

Fixture used by the criteria below ("the base family"): four low-authority softmax members over the roles `approve`, `reject`, `revise` with logits `[1.2, -0.3, 0.1]`, `[1.0, -0.1, 0.3]`, `[1.4, -0.5, 0.0]` and `[1.1, -0.2, 0.2]`, each with the identity `role_map`, all with the gate met. The members are built in the tests and labelled synthetic.

---

## Story 19.1 — Pooling Logits

**Status:** Ready  
**As** a maintainer, **I want** member logits pooled per role after removing each member's arbitrary offset, **so that** the starting point does not depend on a constant softmax ignores.

### Acceptance Criteria:
- **$AC_0$ (Mean And Spread):** on the base family the prior values are `(0.825, -0.625, -0.200)` within 1e-9 and the role spreads `(0.2132, 0.1287, 0.0861)` within 1e-4, recomputed in the test from the formulas of FDD-019 §3 item 2 with `K - 1` in the denominator.
- **$AC_1$ (Centred):** the prior values sum to zero within 1e-12, and each member's centred logits sum to zero.
- **$AC_2$ (Offset Invariance):** adding 5.0 to every logit of one member, or a different constant to each member, leaves the values and spreads unchanged within 1e-12.
- **$AC_3$ (Roles Not Ids):** members whose action ids differ but whose `role_map` agrees give the same prior as the base family, and the order of `members` changes nothing.
- **$AC_4$ (Record):** the `MetaPrior` has `representation` `"softmax"`, `member_count` 4, `kappa_prior` of `None`, the given `sigma_het`, `roles` sorted, and `compiled_from` listing each member's `(task_id, version)` in input order.
- **$AC_5$ (Pure):** `meta_prior.py` imports nothing from `agent_learning.storage`, no `random` and no `numpy`, and performs no file I/O.

---

## Story 19.2 — Pooling Beta Counts

**Status:** Ready  
**As** a maintainer, **I want** Beta-count members pooled in their own representation, **so that** logits and payoff rates are never confused.

### Acceptance Criteria:
- **$AC_0$ (Rate And Prior):** four members with `(alpha, beta)` of `(14, 4)`, `(9, 3)`, `(21, 5)`, `(11, 3)` for one role give a pooled rate of 0.8226 and, with `kappa_prior` 10, a prior of `(9.226, 2.774)` within 1e-3, recomputed in the test from the formula of FDD-019 §3 item 3.
- **$AC_1$ (Spread Over Rates):** the role spread is the standard deviation (denominator `K - 1`) of the members' payoff rates, 0.0164 for the members above within 1e-4.
- **$AC_2$ (Strength):** with `kappa_prior` 5 the prior is `1 + 5 * pbar` and `1 + 5 * (1 - pbar)` within 1e-12; the default is 10.0.
- **$AC_3$ (Role Keyed):** two Thompson members with different action ids but the same `role_map` give the same prior, and the record has `representation` `"thompson"` and the given `kappa_prior`.

---

## Story 19.3 — Refusing a Bad Family

**Status:** Ready  
**As** an auditor, **I want** a family that should not be pooled to be refused with its reason, **so that** a distorted prior is never stored.

### Acceptance Criteria:
- **$AC_0$ (Size):** three members raise `ValueError` naming the count; four are accepted; a duplicate `task_id` raises `ValueError`.
- **$AC_1$ (Gate):** a member with `gate_passed` false raises `ValueError` naming its task id.
- **$AC_2$ (Role Map):** a `role_map` that sends two actions to one role, that misses an action, or that names a role outside the member's roles raises `ValueError`; member role sets that differ raise `ValueError` naming the roles.
- **$AC_3$ (Heterogeneity):** on the base family `sigma_het` 0.15 raises `ValueError` naming the role `approve`, its spread 0.2132 and `sigma_het`, and `sigma_het` 0.25 compiles; a missing, non-finite or non-positive `sigma_het` raises `ValueError`.
- **$AC_4$ (Representation):** an unknown `representation`, a pair among softmax parameters, a float among thompson parameters, or an action without a value raises `ValueError`.
- **$AC_5$ (Beta Strength And Convergence):** `kappa_prior` of 0, a negative value or 10.5 raises `ValueError`; a Thompson member with `alpha + beta` of 2 or less for a role raises `ValueError` naming the member and role, before any pooled rate is computed.

---

## Story 19.4 — Declaring and Finding Members

**Status:** Ready — the Thompson criterion depends on Story 15.2 of Epic 15.  
**As** a maintainer, **I want** a human to declare a policy's family and role map and the compiler to find only qualifying members, **so that** membership and convergence are never guessed.

### Acceptance Criteria:
- **$AC_0$ (Declare):** `task-policy-family-set` writes `family` and `role_map` into the active snapshot's metadata without changing its id or version; an empty family, a `role_map` that is not a bijection onto roles, or an action id outside the policy's actions exits non-zero and leaves the snapshot unchanged.
- **$AC_1$ (Declared Only):** a policy without `family`, or with another family name, is never a member, however similar its actions; a snapshot with `is_family_meta_prior` is never a member.
- **$AC_2$ (Exclusions With Reasons):** a candidate that is full authority, has no `role_map`, or whose ADR-003 gate is not met is excluded, and the validation report names it with its reason; the remaining candidates become `FamilyMember` values with the snapshot version.
- **$AC_3$ (Gate Is Computed):** `gate_passed` equals `assess_autonomy(...).eligible` for the member's active snapshot with the `standard` tier thresholds (FDD-019 H1); the test builds members with enough and with too few scored outcomes and checks both results.
- **$AC_4$ (Representation):** members with `posterior_parameters` are read as `(alpha, beta)` pairs keyed by action id, members without it as logits, and a mix exits non-zero naming the tasks.
- **$AC_5$ (Read Only):** reading members writes nothing to the store.

---

## Story 19.5 — Storing the Prior

**Status:** Ready  
**As** an auditor, **I want** the compiled prior stored as an ordinary snapshot with its full provenance, **so that** I can see exactly which policies and versions it came from.

### Acceptance Criteria:
- **$AC_0$ (Snapshot):** `task-policy-meta-compile` on a constructed store with the base family stores one `PolicySnapshot` whose task id is the output name, with one `Action` per role, `logits` equal to the prior values, and `is_family_meta_prior` true; it is the active policy of its own pseudo-task (the store sets the pointer) and of no member task, and `tasks-list` shows it.
- **$AC_1$ (Provenance):** the snapshot metadata holds `family`, `family_member_count`, `compiled_from` with each member's task id and version, `compile_time`, `sigma_het`, `kappa_prior`, `representation` and `validation_report` with the family size, the excluded members with reasons and the per-role spread; the metadata survives `json.dumps` and `json.loads` unchanged.
- **$AC_2$ (Members Unchanged):** every member snapshot is equal to its earlier copy after the command, and a failed compilation stores nothing and exits non-zero with the reasons.
- **$AC_3$ (Supersession):** compiling again under the same name stores the next version, which records `supersedes` with the earlier snapshot's id; the earlier snapshot is not written (equal to its earlier copy) and still present; only the latest version is offered for seeding; on a `LocalFileStore` the active pointer of the output name ends at the newest version.
- **$AC_4$ (Thompson Form):** a Thompson family stores `posterior_parameters` keyed by role, in the shape of FDD-015 §2.2.
- **$AC_5$ (Storage Boundary):** the store gains no record type, and the pooling module imports nothing from `agent_learning.storage`.

---

## Story 19.6 — Seeding a New Policy

**Status:** Ready  
**As** a maintainer, **I want** a new policy's starting values taken from the prior through its own role map, **so that** it begins from the family's experience and then learns on its own.

### Acceptance Criteria:
- **$AC_0$ (Through The Map):** `seed_values` for a new policy whose action ids differ from the family's, in a different order, gives each action the prior value of the role its `role_map` names.
- **$AC_1$ (Refuses A Bad Map):** a `role_map` that is not a bijection from the policy's action ids onto the prior's roles raises `ValueError`.
- **$AC_2$ (Thompson Seeding):** for a Thompson prior the values are the `(alpha, beta)` pair of the role, not logits.
- **$AC_3$ (No Separate Record):** `seed_values` returns values only and changes neither the prior nor the role map it is given; the record of a seeding is the `warm_start_*` provenance of Story 20.2 of Epic 20, and the module has no `seed_record` (FDD-019 H8).
- **$AC_4$ (No Borrowed Evidence):** a snapshot seeded from a prior, with no episodes, is not eligible under `assess_autonomy` with the `standard` tier thresholds (FDD-019 H1).
- **$AC_5$ (Decoupled):** after the seeded policy's logits are changed, the stored prior is equal to its earlier copy.

---

## Story 19.7 — The Real-Data Check (No Family)

**Status:** Ready  
**As** a maintainer, **I want** the compiler run against the recorded store, **so that** the lack of a real family is shown, not assumed.

### Acceptance Criteria:
- **$AC_0$ (Real Source):** the store is a temporary copy of the committed one under `data/agent-learning/store`; the tasks found and their authority are recorded in the test.
- **$AC_1$ (No Family):** compiling any family name over it exits non-zero with a reason (no member declares the family, or fewer than 4 qualify), and the `approve-*` tasks, if declared into a family in the test, are excluded as full authority with that reason.
- **$AC_2$ (Nothing Stored):** the committed store under `data/agent-learning/store` is equal to its earlier state after the run.
- **$AC_3$ (Labelled):** the result is recorded as a statement that no suitable family exists yet. It makes no claim that a meta-prior speeds convergence (BRU-019-12), and the docstring names the missing data (four or more converged same-family low-authority policies with real episodes and a human-written `role_map` for each).
