# ADR 019: Hierarchical Meta-Prior Compilation Across Task Families

## 1. Executive Brief
As autonomous governance expands across the 18-stage lifecycle (ADR-008, ADR-009, ADR-011), the repository deploys clusters of structurally similar task policies—such as the nine PMBOK subsidiary plan approval gates, multi-stage document classification gates, and tier-specific escalation handlers. While ADR-020 provides direct 1-to-1 prior transfer between a single donor and recipient, scaling to complex task families requires synthesizing collective statistical experience from across *all* previously converged peer policies.

This ADR introduces **Hierarchical Meta-Prior Compilation Across Task Families** (Methodology #14 from `Ideation-Document.md` §2.1). Grounded in Empirical Bayes hierarchical modeling, this offline compilation utility aggregates parameter vectors across family members into a robust meta-prior distribution, providing accelerated cold-start convergence for newly instantiated family members without cross-task contamination.

## 2. Status
**Proposed (2026-10-25)** — Derived from `Ideation-Document.md` §2.1 (Methodology #14). Ready for multi-criteria evaluation under `approve-adr`.

## 3. Context & Problem Statement
- **The Limits of 1-to-1 Transfer (ADR-020):** 1-to-1 prior transfer is vulnerable to donor-specific idiosyncrasies or localized overfitting. If the selected donor policy converged on a skewed distribution, that bias is transferred directly to the target.
- **Shared Family Structure:** Policies within a common governance family (e.g., `family = "pmbok_subsidiary_gates"`) share identical action semantics (`approve`, `reject`, `request_revision`) and experience similar baseline rejection rates.
- **Statistical Shrinkage:** Hierarchical Bayesian modeling provides pooled (empirical Bayes) estimation, borrowing statistical strength across multiple sparse policies to produce a more robust prior than any single policy could generate alone.

## 4. Technical Decision

### 4.1 Empirical Bayes Pooling
Let a policy family $\mathcal{F} = \{P_1, \dots, P_K\}$ consist of $K \ge 4$ converged policies sharing action space $A$ and a declared `family` value (a human-set field in the policy metadata; policies without it are never pooled).
Each policy $k$ has converged logit vector $\boldsymbol{\theta}_k \in \mathbb{R}^{|A|}$. The pooled estimates are the family mean and the per-action variance:
$$\hat{\boldsymbol{\mu}}_{\text{meta}} = \frac{1}{K} \sum_{k=1}^K \boldsymbol{\theta}_k, \qquad \hat{\sigma}^2_a = \frac{1}{K-1} \sum_{k=1}^K (\theta_{k,a} - \hat{\mu}_a)^2$$
The variance is a **heterogeneity diagnostic**, not a prior covariance: if $\max_a \hat{\sigma}_a > \sigma_{\text{het}}$ (declared at compile time), the family is too dissimilar to pool and compilation fails with a reason. Pooling the mean across $K \ge 4$ members is the shrinkage this ADR provides; a per-member James-Stein factor is not computed.

### 4.2 Initializing Target Policies from the Meta-Prior
When a new policy $P_{\text{new}}$ is initialized within family $\mathcal{F}$:
- **Softmax policies:** its initial logits are $\boldsymbol{\theta}_{\text{new}, 0} = \hat{\boldsymbol{\mu}}_{\text{meta}}$.
- **Thompson policies (ADR-015):** the prior is compiled in the same representation, never converted from logits. The family prior is the pooled, strength-capped count per action:
  $$\alpha_a = 1 + \kappa_{\text{prior}} \cdot \bar{p}_a, \quad \beta_a = 1 + \kappa_{\text{prior}} \cdot (1 - \bar{p}_a), \quad \bar{p}_a = \frac{\sum_k (\alpha_{k,a} - 1)}{\sum_k (\alpha_{k,a} + \beta_{k,a} - 2)}$$
  The denominator is nonzero only if every member has at least one observation for the action ($\alpha_{k,a} + \beta_{k,a} > 2$); a family with an unconverged member is rejected before this formula is evaluated (§4.4). Here $\kappa_{\text{prior}} \le 10$ is the effective pseudo-count strength. Softmax logits and Beta payoff rates are different quantities, so a family is compiled in one representation only.
- **Evidence gate:** pseudo-counts and initial logits from a meta-prior are not scored outcomes. They do not count towards the ADR-003 gate (at least 20 outcomes, Wilson lower bound $\ge 0.90$).

### 4.3 Tooling & Storage Architecture
Meta-compilation is executed via an offline CLI utility:
```powershell
python -m agent_learning.cli task-policy-meta-compile \
  --agent-id agent-learning-governance \
  --family pmbok_subsidiary_gates \
  --output-prior-name meta_pmbok_gate_v1
```
The compiled meta-prior is stored as a template snapshot in `LearningStore`:
- `PolicySnapshot.metadata["is_family_meta_prior"] = True`
- `PolicySnapshot.metadata["family_member_count"] = K`
- Individual active policies remain completely independent; updates never propagate backward to mutate the compiled meta-prior.

### 4.4 Code design and test data
Design only: nothing below is built, and the signatures are the contract an FDD must confirm or change.
Module `src/agent_learning/meta_prior.py`, pure and standard library only; the CLI wiring (`task-policy-meta-compile`) lives in `cli.py` and does the storage reads.

```python
@dataclass(frozen=True)
class FamilyMember:
    task_id: str
    role_map: Mapping[str, str]       # action id -> role ("approve", "reject", "revise"); identity when ids already match
    params: Mapping[str, float]       # logits (softmax) or alpha/beta counts (Thompson), keyed by action id

def compile_meta_prior(members: Sequence[FamilyMember], *, representation: str,
                       sigma_het: float, kappa_prior: float = 10.0) -> MetaPrior: ...
# raises ValueError: K < 4; the role sets differ; max sigma_a > sigma_het;
#   kappa_prior <= 0 or > 10; or (Thompson) any member with alpha + beta <= 2 for an action (not converged,
#   which would also make the pooled-rate denominator zero)
```

Tests (`tests/test_meta_prior.py`): the mean over $K$ members, rejection when $K < 4$, rejection when the role sets differ or the family is heterogeneous, rejection of `kappa_prior` above 10 or not positive, rejection of an unconverged Thompson member (no zero denominator), the same family compiles when ids differ but `role_map` agrees, the Thompson prior counts follow the §4.2 formula, the compiled prior has `is_family_meta_prior=True` and no member snapshot is changed, and the prior does not count towards the ADR-003 gate.

**Test data.** *Real:* the repository does have a real family, the `approve-*` tasks (`approve-adr`, `approve-brd`, `approve-fdd`, `approve-user-stories` and others). Their action ids differ by name (`approve_adr`, `approve_brd`, ...), so Invariant 3 is met through the declared `role_map` (approve, reject, revise); the map for the real `approve-*` tasks still has to be written by a human. *Gap:* none of these policies has learned logits (they are full authority at version 0), so no member is a converged donor, and $K \ge 4$ converged members do not exist. Needed: that role map written for the real tasks, and at least four low-authority policies of one family with real episodes. *Oracle tests:* hand-computed pooled means on small vectors, as arithmetic.

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

## 8. Amendment Log

| Date | Change | Why |
|---|---|---|
| 2026-10-25 | Initial Draft | Candidate derived from Ideation Document §2.1 (Methodology #14). |
| 2026-10-28 | Review fix | The draft claimed James-Stein shrinkage but computed a plain mean and an unused covariance. Now a pooled mean plus a heterogeneity check, $K \ge 4$. Removed the sigmoid conversion from softmax logits to Beta counts (different quantities). Added the ADR-003 gate separation and the human-declared `family` field. |
| 2026-10-28 | Code design | Added §4.4: module layout, signatures, tests, and which real data exists and which is missing. |
| 2026-10-28 | Amazon Q review (PR #36) | Added `role_map` to `FamilyMember` and Invariant 3 (the real `approve-*` family could not otherwise satisfy it); `kappa_prior` bounds and the unconverged-member (zero denominator) case added to the raises contract and tests; dataclass fields on separate lines. |
| 2026-10-28 | Amazon Q review, round 2 | The zero-denominator precondition is stated at the formula; `FamilyMember.logits` renamed `params` because it also holds Beta counts. |

## 9. References
- `docs/project-docs/Ideation-Document.md` §2.1 (Methodology #14)
- `ADR-001`: Decision Authority Model
- `ADR-002`: Storage Backend Strategy
- `ADR-020`: Explicit Policy Prior Warm-Starting

