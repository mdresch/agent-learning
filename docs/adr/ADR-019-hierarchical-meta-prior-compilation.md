# ADR 019: Hierarchical Meta-Prior Compilation Across Task Families

## 1. Executive Brief
As autonomous governance expands across the 18-stage lifecycle (ADR-008, ADR-009, ADR-011), the repository deploys clusters of structurally similar task policies—such as the nine advisory knowledge-area learners planned in `docs/design-notes/planning-redesign-notes.md` §4.12 (`low` authority if they become policies), multi-stage document classification gates, and tier-specific escalation handlers. While ADR-020 provides direct 1-to-1 prior transfer between a single donor and recipient, scaling to complex task families requires synthesizing collective statistical experience from across *all* previously converged peer policies.

This ADR introduces **Hierarchical Meta-Prior Compilation Across Task Families** (Methodology #14 from `Ideation-Document.md` §2.1). Grounded in Empirical Bayes hierarchical modeling, this offline compilation utility aggregates parameter vectors across family members into a robust meta-prior distribution, providing accelerated cold-start convergence for newly instantiated family members without cross-task contamination.

## 2. Status
**Accepted (2026-10-28, Menno)** — Derived from `Ideation-Document.md` §2.1 (Methodology #14). Approved as a design through `approve-adr` (robust utility 0.677, expected utility 0.757; Episode `f3a99dcf-b62b-4810-b043-1c1c0dfb0289`). Amazon Q reviewed this text in PR #36. Nothing is built; the gaps named in the code-design section stay open.

## 3. Context & Problem Statement
- **The Limits of 1-to-1 Transfer (ADR-020):** 1-to-1 prior transfer is vulnerable to donor-specific idiosyncrasies or localized overfitting. If the selected donor policy converged on a skewed distribution, that bias is transferred directly to the target.
- **Shared Family Structure:** Policies within a common governance family (e.g., `family = "pmbok_advisory_learners"`) share the same action roles (such as `approve`, `reject`, `revise`) and experience similar baseline rejection rates.
- **Statistical Shrinkage:** Hierarchical Bayesian modeling provides pooled (empirical Bayes) estimation, borrowing statistical strength across multiple sparse policies to produce a more robust prior than any single policy could generate alone.

## 4. Technical Decision

### 4.1 Empirical Bayes Pooling
Let a policy family $\mathcal{F} = \{P_1, \dots, P_K\}$ consist of $K \ge 4$ converged policies sharing a set of canonical action roles $R$ and a declared `family` value (a human-set field in the policy metadata; policies without it are never pooled). A policy is **converged** when `assess_autonomy` finds the ADR-003 gate met on its active version, evaluated at compile time from its recorded episodes with the `standard` tier thresholds (at least 20 scored outcomes, Wilson lower bound $\ge 0.90$, and the gate's other conditions); no assessment is stored, and the compiler never infers convergence. Only low-authority policies qualify, because only they have learned values; a candidate that is full authority, has no `role_map`, or fails the gate is excluded from the family and named with its reason in the validation report (FDD-019 H1, H5).
Each member's action ids are mapped to roles through its declared `role_map`, which must be a bijection onto $R$ (no two actions of one policy share a role). The compiled prior is indexed by role.
Softmax is invariant to adding a constant to every logit, so each member's logits are zero-centred before pooling, which makes the mean and the diagnostic independent of that arbitrary offset:
$$\tilde{\theta}_{k,r} = \theta_{k,r} - \frac{1}{|R|}\sum_{q \in R} \theta_{k,q}$$
The pooled estimates are the family mean and the per-role variance:
$$\hat{\boldsymbol{\mu}}_{\text{meta}} = \frac{1}{K} \sum_{k=1}^K \tilde{\boldsymbol{\theta}}_k, \qquad \hat{\sigma}^2_r = \frac{1}{K-1} \sum_{k=1}^K (\tilde{\theta}_{k,r} - \hat{\mu}_r)^2$$
The variance is a **heterogeneity diagnostic**, not a prior covariance: if $\max_r \hat{\sigma}_r > \sigma_{\text{het}}$ (a required value declared at compile time, with no default, and recorded in the prior's provenance), the family is too dissimilar to pool and compilation fails with a reason. Pooling the mean across $K \ge 4$ members is the shrinkage this ADR provides; a per-member James-Stein factor is not computed.

### 4.2 Initializing Target Policies from the Meta-Prior
When a new policy $P_{\text{new}}$ is initialized within family $\mathcal{F}$:
- **Softmax policies:** its initial logits are $\boldsymbol{\theta}_{\text{new}, 0} = \hat{\boldsymbol{\mu}}_{\text{meta}}$, mapped from roles back to the new policy's own action ids through its own `role_map`.
- **Thompson policies (ADR-015):** the prior is compiled in the same representation, never converted from logits. The family prior is the pooled, strength-capped count per role:
  $$\alpha_r = 1 + \kappa_{\text{prior}} \cdot \bar{p}_r, \quad \beta_r = 1 + \kappa_{\text{prior}} \cdot (1 - \bar{p}_r), \quad \bar{p}_r = \frac{\sum_k (\alpha_{k,r} - 1)}{\sum_k (\alpha_{k,r} + \beta_{k,r} - 2)}$$
  The denominator is nonzero only if every member has at least one observation for the role ($\alpha_{k,r} + \beta_{k,r} > 2$); a family with an unconverged member is rejected before this formula is evaluated (§4.4). For a Thompson family the heterogeneity diagnostic is computed over the members' payoff rates $p_{k,r} = (\alpha_{k,r} - 1)/(\alpha_{k,r} + \beta_{k,r} - 2)$ around their mean, with the same $\sigma_{\text{het}}$ test. Here $\kappa_{\text{prior}} \le 10$ is the effective pseudo-count strength. Softmax logits and Beta payoff rates are different quantities, so a family is compiled in one representation only.
- **Evidence gate:** pseudo-counts and initial logits from a meta-prior are not scored outcomes. They do not count towards the ADR-003 gate (at least 20 outcomes, Wilson lower bound $\ge 0.90$).

### 4.3 Tooling & Storage Architecture
Meta-compilation is executed via an offline CLI utility:
```powershell
python -m agent_learning.cli task-policy-meta-compile \
  --agent-id agent-learning-governance \
  --family pmbok_advisory_learners \
  --output-prior-name meta_pmbok_learner_v1 \
  --sigma-het 0.25
```
`--sigma-het` is required and has no default; `--kappa-prior` is optional (default 10, at most 10) and applies only to Beta counts (FDD-019 H4).
The compiled meta-prior is stored as a template snapshot in `LearningStore`: a `PolicySnapshot` with one `Action` per role, saved under the output name as its task id, never made the active policy of any task, and left out of member discovery by `is_family_meta_prior` (FDD-019 H6). A human declares a policy's `family` and `role_map` with `task-policy-family-set` (FDD-019 H2). The command that applies a prior to a new policy is the `task-policy-warm-start` of ADR-020 and is decided there (FDD-019 H7):
- `PolicySnapshot.metadata["is_family_meta_prior"] = True`
- `PolicySnapshot.metadata["family_member_count"] = K`
- Provenance, as in ADR-020: `PolicySnapshot.metadata["compiled_from"]` (each member's task id and snapshot version), `compile_time`, `sigma_het`, `kappa_prior`, `representation`, and the validation report (family size, rejected members with reasons, per-role variance).
- A defective prior is superseded by compiling a new one; the old snapshot is kept, marked `superseded_by`, and no longer offered for seeding. Policies already seeded from it are unaffected (Invariant 2) and keep a record of which prior seeded them.
- Individual active policies remain completely independent; updates never propagate backward to mutate the compiled meta-prior.

### 4.4 Code design and test data
Design only: nothing below is built, and the signatures are the contract an FDD must confirm or change.
Module `src/agent_learning/meta_prior.py`, pure and standard library only; the CLI wiring (`task-policy-meta-compile`) lives in `cli.py` and does the storage reads.

```python
@dataclass(frozen=True)
class FamilyMember:
    task_id: str
    version: int                      # the active snapshot version, for provenance
    role_map: Mapping[str, str]       # action id -> role ("approve", "reject", "revise"); identity when ids already match
    params: Mapping[str, float | tuple[float, float]]   # logit (softmax) or (alpha, beta) pair (Thompson), keyed by action id
    gate_passed: bool                 # `assess_autonomy(...).eligible` for the active version, computed by the CLI wiring

def compile_meta_prior(members: Sequence[FamilyMember], *, representation: str,
                       sigma_het: float, kappa_prior: float = 10.0) -> MetaPrior: ...
# raises ValueError: K < 4; a member has not passed the ADR-003 gate; a role_map is not a bijection; the role sets differ; max sigma_a > sigma_het;
#   kappa_prior <= 0 or > 10; or (Thompson) any member with alpha + beta <= 2 for an action (not converged,
#   which would also make the pooled-rate denominator zero)
```

The module also provides `MetaPrior`, `seed_values(prior, role_map, action_ids)` and `seed_record(prior_snapshot, seeded_at)`, the pure seeding functions (FDD-019 H3, H7).

Tests (`tests/test_meta_prior_softmax.py`, `tests/test_meta_prior_thompson.py`, `tests/test_meta_prior_refusals.py`, `tests/test_meta_prior_members.py`, `tests/test_meta_prior_store.py`, `tests/test_meta_prior_seed.py`, `tests/test_meta_prior_real_data.py`, split by story in Epic 19): the mean over $K$ members, two members that differ only by a constant logit offset show zero heterogeneity, a non-bijective `role_map` is rejected, a member that has not passed the gate is rejected, the Thompson heterogeneity uses payoff rates, the provenance keys are present, rejection when $K < 4$, rejection when the role sets differ or the family is heterogeneous, rejection of `kappa_prior` above 10 or not positive, rejection of an unconverged Thompson member (no zero denominator), the same family compiles when ids differ but `role_map` agrees, the Thompson prior counts follow the §4.2 formula, the compiled prior has `is_family_meta_prior=True` and no member snapshot is changed, and the prior does not count towards the ADR-003 gate.

**Test data.** *Real:* no suitable family exists today. The `approve-*` tasks share action roles, but they are `full` authority (ADR-001 §4.2) and pinned there (ADR-021 Invariant 5), so they have no learned logits by design and can never be converged donors. The intended family is the nine advisory knowledge-area learners (`planning-redesign-notes.md` §4.12, `low` authority), which are not built. *Gap:* $K \ge 4$ converged same-family policies with real episodes, and a `role_map` for each, written by a human. *Oracle tests:* hand-computed pooled means on small vectors, as arithmetic.

**Walkthrough.** [Methodology 14 in the walkthroughs](../learning-methodology-walkthroughs.md#14-hierarchical-meta-prior-adr-019-44). It runs the sketch today; it must be rewritten against the real module once this is built.

## 5. Alternatives Considered

| Alternative | Rationale for Rejection |
|---|---|
| **1-to-1 Transfer Only (ADR-020)** | Lacks statistical pooling; highly sensitive to noise in the chosen donor policy. |
| **Model-Agnostic Meta-Learning (MAML)** | Requires computing second-order Hessian gradients through training trajectories, violating the CPU-bound, lightweight runtime requirement. |
| **Global Pooled Learning** | Training one shared policy across multiple tasks conflates task-specific nuances and destroys localized error attribution. |

## 6. Consequences

### Positive
- Solves the cold-start bottleneck across large governance task clusters (e.g. PMBOK 8 subsidiary plans).
- Empirical Bayes shrinkage eliminates donor-selection bias.
- Fully offline compilation with zero runtime inference overhead.

### Negative
- Requires a minimum family size ($K \ge 4$ converged policies) to produce meaningful meta-priors.
- Assumes exchangeability across family members; if one policy is radically different, it can distort the family mean.

## 7. Architectural Invariants

1. **Read-Only Aggregation:** Meta-compilation is strictly a read-only batch aggregation over historical snapshots; it never alters active policies.
2. **Decoupled Local Execution:** Once a policy is seeded from a meta-prior, its runtime updates are 100% localized to its own snapshot.
3. **Action Space Identity:** All policies included in a family compilation must possess identical action spaces after each member's action ids are mapped through its declared `role_map`. The map is declared by a human; the compiler never infers it.
4. **Storage Law (ADR-002):** Meta-priors reside within standard `PolicySnapshot` records.
5. **Evidence Gate Separation:** A meta-prior never counts as scored outcomes for the ADR-003 autonomy gate.
6. **Single Representation:** A family is compiled either in logits or in Beta counts, never a mix.
7. **Defined Convergence:** A member qualifies as a donor only through the recorded ADR-003 gate result, and a bijective, human-declared `role_map` is required.
8. **Reproducible Provenance:** Every compiled prior records its members and versions, compile time and parameters; a superseded prior is kept, not deleted.

## 8. Amendment Log

| Date | Change | Why |
|---|---|---|
| 2026-10-25 | Initial Draft | Candidate derived from Ideation Document §2.1 (Methodology #14). |
| 2026-10-28 | Review fix | The draft claimed James-Stein shrinkage but computed a plain mean and an unused covariance. Now a pooled mean plus a heterogeneity check, $K \ge 4$. Removed the sigmoid conversion from softmax logits to Beta counts (different quantities). Added the ADR-003 gate separation and the human-declared `family` field. |
| 2026-10-28 | Code design | Added §4.4: module layout, signatures, tests, and which real data exists and which is missing. |
| 2026-10-28 | Amazon Q review (PR #36) | Added `role_map` to `FamilyMember` and Invariant 3 (the real `approve-*` family could not otherwise satisfy it); `kappa_prior` bounds and the unconverged-member (zero denominator) case added to the raises contract and tests; dataclass fields on separate lines. |
| 2026-10-28 | Amazon Q review, round 2 | The zero-denominator precondition is stated at the formula; `FamilyMember.logits` renamed `params` because it also holds Beta counts. |
| 2026-10-28 | Amazon Q review, round 5 | The Thompson pooled-rate formula is indexed by role ($r$), like the softmax formula and the role-indexed prior in §4.1. |
| 2026-10-28 | External review triage | Family example corrected: ADR-013 §5 rejected nine per-plan policies and the `approve-*` gates are `full` authority, so the family is the nine advisory learners (planning-redesign-notes §4.12). Logits are zero-centred before pooling; Thompson heterogeneity defined over payoff rates; priors indexed by role with a bijective `role_map`; `params` can hold an (alpha, beta) pair; converged defined by the ADR-003 gate; provenance and supersession added (Invariants 7 and 8). Declined: a family registry with invented owners, a re-compilation cadence, a drift parameter, and a claimed missing minus sign (the formula is correct). |
| 2026-10-28 | Accepted | Approved by Menno through `approve-adr`: robust utility 0.677, expected utility 0.757; Episode `f3a99dcf-b62b-4810-b043-1c1c0dfb0289`. Design only. |
| 2026-10-29 | FDD alignment | Menno confirmed FDD-019 H1 to H7: convergence computed at compile time by `assess_autonomy` with the `standard` tier thresholds and low authority only, with non-qualifying candidates excluded and reported; family and role map declared with a new `task-policy-family-set` command; `FamilyMember` gains `version` and the result type `MetaPrior` is defined; `sigma_het` required with no default; the prior stored as an ordinary snapshot per role under the output name, never active and excluded from discovery; the command that applies a prior left to ADR-020, with pure seeding functions here. §4.1, §4.3 and §4.4 amended to match. Re-approved 2026-10-29 under `approve-adr` (adjudicated accept, robust utility 0.694 vs. 0.044 reject and 0.110 revise, episode `e0cda2d2-7f5c-4c3c-aff0-cbcc4baa4dd6`). The ADR-005 comparison with the original approval (0.677) classifies as **progression**: margin 0.514 to 0.584, expected utility 0.757 to 0.771, uncertainty 0.798 to 0.772, no criterion lower (soundness +0.029, gap disclosure +0.020, consequences +0.009, alternatives 0.000; the alternatives section did not change). The inputs are the same reader's scoring both times, so this is not independent evidence. Result: `docs/policy-shapes/results/adr-019-reapproval-comparison.json`. |

## 9. References
- `docs/project-docs/Ideation-Document.md` §2.1 (Methodology #14)
- `ADR-001`: Decision Authority Model
- `ADR-002`: Storage Backend Strategy
- `ADR-020`: Explicit Policy Prior Warm-Starting
