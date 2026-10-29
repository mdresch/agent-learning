# BRD-019: Hierarchical Meta-Prior Compilation Across Task Families

**Source ADR:** [ADR-019](../../adr/ADR-019-hierarchical-meta-prior-compilation.md) — Accepted (2026-10-28)  
**Governing Baseline:** none approved yet; cycle `CYC-001` (ADR-035, Proposed)  
**Status:** Approved (2026-10-29, Menno) — derived from Accepted ADR-019; adjudicated via `approve-brd` (robust utility 0.732, episode `7c750fae-af86-41db-a5dd-ae299cb25438`); corrected 2026-10-29 (BRU-019-08 and BRU-019-11, FDD-019 H8) and re-approved via `approve-brd` (robust utility 0.735, episode `d65f2549-c709-4476-93ad-efee969f3777`; comparison with the previous approval: flat, within tolerance, no criterion lower).  
**Stakeholders:** Menno (Sponsor/PM/maintainer); SDK adopters who run a cluster of similar low-authority policies and want a new member to start from the family's experience; auditors who must see which policies a starting point came from  

## Business Need

A new policy in a cluster of similar policies (the nine advisory knowledge-area learners planned for the PMBOK plans are the intended cluster) starts knowing nothing, although its siblings have already learned what the family's actions are worth. Copying one sibling's values carries that sibling's quirks (ADR-020 is the one-to-one copy). ADR-019 decides an offline step that pools the values of at least four converged siblings into one starting point per action role, refuses to pool a family whose members disagree too much, and records exactly which policies and versions it came from. A new policy is then seeded from that starting point, and from that moment learns on its own. Nothing is built, and no suitable family exists today.

## Business Rules (BRU)

- **BRU-019-01 (Read-Only Aggregation):** Compiling a meta-prior only reads member policies and their evidence. It never changes a member policy, and a policy seeded from a prior never changes the prior (ADR-019 Invariants 1 and 2).
- **BRU-019-02 (Declared Family):** A policy belongs to a family only through a `family` value a human declared in its metadata. A policy without it is never pooled. At least four members are required (ADR-019 §4.1).
- **BRU-019-03 (Converged Donors Only):** A member qualifies only if the ADR-003 autonomy gate is met on its active version, evaluated from its recorded episodes. The compiler never decides a policy is converged on its own judgement. Only low-authority policies qualify, because only they have learned values (ADR-019 §4.1, Invariant 7; FDD-019 H1).
- **BRU-019-04 (Declared Role Map):** Each member declares a `role_map` from its action ids to roles. It must be a bijection onto the family's role set, the role sets of all members must be identical, and the compiler never infers a map (ADR-019 §4.1, Invariant 3).
- **BRU-019-05 (Zero-Centred Pooling):** Softmax logits are zero-centred per member before pooling, so a constant added to every logit of a member changes nothing. The prior is the mean of the centred logits per role (ADR-019 §4.1).
- **BRU-019-06 (Heterogeneity Refusal):** The per-role standard deviation across members is a diagnostic. If its maximum exceeds the `sigma_het` declared at compile time, no prior is produced and the reason is reported. `sigma_het` has no default (ADR-019 §4.1; FDD-019 H4).
- **BRU-019-07 (One Representation):** A family is compiled either as logits or as Beta counts, never mixed. For Beta counts the prior per role is `alpha = 1 + kappa * p`, `beta = 1 + kappa * (1 - p)` with `p` the pooled payoff rate and `0 < kappa <= 10`; a member with no observation for a role is rejected before the rate is computed (ADR-019 §4.2, Invariant 6).
- **BRU-019-08 (Seeding Through The Policy's Own Map):** A new policy's initial values are the prior's values mapped from roles to its own action ids through its own declared `role_map`, and the seeding is recorded in its snapshot by the `warm_start_*` provenance of ADR-020 (ADR-019 §4.2, §4.3; FDD-019 H8).
- **BRU-019-09 (No Borrowed Evidence):** A meta-prior and the values a policy takes from it are not scored outcomes. They never count toward the ADR-003 gate (ADR-019 §4.2, Invariant 5).
- **BRU-019-10 (Storage Boundary):** A prior is an ordinary `PolicySnapshot` with `is_family_meta_prior` set, plus its provenance in metadata. Zero new `LearningStore` record types (ADR-019 Invariant 4; ADR-002).
- **BRU-019-11 (Reproducible Provenance):** Every prior records its members (task id and snapshot version), the compile time, `sigma_het`, `kappa_prior`, the representation, and the validation report. A defective prior is superseded by a new compilation; the old one is kept unchanged, the new one records `supersedes`, and only the latest version is offered for seeding (ADR-019 §4.3, Invariant 8; FDD-019 H8).
- **BRU-019-12 (No Claim Of Effectiveness):** No suitable family exists today. The `approve-*` policies share roles but are full authority and have no learned logits; the nine advisory learners are not built. The first evidence is that compilation on the recorded store finds no family and says why. Nothing is claimed about faster convergence (ADR-019 §4.4, test data).

## Stakeholder Success Metrics

| Metric | Target |
|---|---|
| Pooling | the pooled mean and per-role variance equal hand-computed values to 1e-9 on tested families |
| Offset invariance | adding any constant to every logit of one member leaves the prior unchanged to 1e-12 |
| Refusal | 100% of families with fewer than 4 members, an unconverged or full-authority member, a non-bijective or differing role map, a mixed representation, a bad `kappa_prior`, or a spread above `sigma_het` are refused with a reason |
| Formula | the Beta prior equals `1 + kappa * p` and `1 + kappa * (1 - p)` to 1e-12 on tested families |
| Read-only | 0 member snapshots changed by a compilation (deep-equal before and after) |
| Provenance | 100% of stored priors carry the members and versions, `compile_time`, `sigma_het`, `kappa_prior`, `representation` and the validation report |
| Seeding | a policy seeded through a different action-id order than the family's gets the same value per role |
| Gate separation | a freshly seeded policy with no episodes is not eligible under the ADR-003 gate |
| Storage boundary | 0 new record types; 0 imports from `agent_learning.storage` in the pooling module |

## Out of Scope

- Building the nine advisory knowledge-area learners, the intended family. The compiler is built and tested on constructed families.
- A family registry with owners, a re-compilation cadence or a drift parameter. ADR-019's review triage declined them.
- Inferring a role map or convergence, or pooling policies without a declared family.
- Per-member James-Stein shrinkage (ADR-019 §4.1 states it is not computed) and model-agnostic meta-learning.
- One-to-one prior transfer between two policies (ADR-020, a separate decision).
- Showing that a seeded policy converges faster. That needs a real family with real episodes.
