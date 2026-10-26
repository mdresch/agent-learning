# ADR 019: Hierarchical Meta-Prior Compilation Across Task Families

## 1. Executive Brief
As autonomous governance expands across the 18-stage lifecycle (ADR-008, ADR-009, ADR-011), the repository deploys clusters of structurally similar task policies—such as the nine PMBOK subsidiary plan approval gates, multi-stage document classification gates, and tier-specific escalation handlers. While ADR-020 provides direct 1-to-1 prior transfer between a single donor and recipient, scaling to complex task families requires synthesizing collective statistical experience from across *all* previously converged peer policies.

This ADR introduces **Hierarchical Meta-Prior Compilation Across Task Families** (Methodology #14 from `Ideation-Document.md` §2.1). Grounded in Empirical Bayes hierarchical modeling, this offline compilation utility aggregates parameter vectors across family members into a robust meta-prior distribution, providing accelerated cold-start convergence for newly instantiated family members without cross-task contamination.

## 2. Status
**Proposed (2026-10-25)** — Derived from `Ideation-Document.md` §2.1 (Methodology #14). Ready for multi-criteria evaluation under `approve-adr`.

## 3. Context & Problem Statement
- **The Limits of 1-to-1 Transfer (ADR-020):** 1-to-1 prior transfer is vulnerable to donor-specific idiosyncrasies or localized overfitting. If the selected donor policy converged on a skewed distribution, that bias is transferred directly to the target.
- **Shared Family Structure:** Policies within a common governance family (e.g., `family = "pmbok_subsidiary_gates"`) share identical action semantics (`approve`, `reject`, `request_revision`) and experience similar baseline rejection rates.
- **Statistical Shrinkage:** Hierarchical Bayesian modeling provides James-Stein shrinkage, borrowing statistical strength across multiple sparse policies to produce a more robust prior than any single policy could generate alone.

## 4. Technical Decision

### 4.1 Empirical Bayes Hierarchical Formulation
Let a policy family $\mathcal{F} = \{P_1, \dots, P_K\}$ consist of $K$ converged policies sharing action space $A$.
Each policy $k$ has converged logit vector $\boldsymbol{\theta}_k \in \mathbb{R}^{|A|}$.
We model the parameters as exchangeable draws from a family-level Gaussian meta-prior:
$$\boldsymbol{\theta}_k \sim \mathcal{N}(\boldsymbol{\mu}_{\text{meta}}, \boldsymbol{\Sigma}_{\text{meta}})$$

The Empirical Bayes estimators are computed in closed form:
$$\hat{\boldsymbol{\mu}}_{\text{meta}} = \frac{1}{K} \sum_{k=1}^K \boldsymbol{\theta}_k$$
$$\hat{\boldsymbol{\Sigma}}_{\text{meta}} = \text{diag}\left( \frac{1}{K} \sum_{k=1}^K (\boldsymbol{\theta}_k - \hat{\boldsymbol{\mu}}_{\text{meta}})^2 + \gamma \mathbf{I} \right)$$
Where $\gamma > 0$ is a variance floor preventing singularity on unvaried actions.

### 4.2 Initializing Target Policies via Shrinkage
When a new policy $P_{\text{new}}$ is initialized within family $\mathcal{F}$:
- Its initial action logits $\boldsymbol{\theta}_{\text{new}, 0}$ are set to $\hat{\boldsymbol{\mu}}_{\text{meta}}$.
- If Thompson sampling (ADR-015) is used, the conjugate prior counts are set to:
  $$\alpha_a = \kappa_{\text{prior}} \cdot \sigma(\mu_{\text{meta}, a}), \quad \beta_a = \kappa_{\text{prior}} \cdot (1 - \sigma(\mu_{\text{meta}, a}))$$
  Where $\kappa_{\text{prior}}$ represents the effective pseudo-count strength of the meta-prior.

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
- Requires a minimum family size ($K \ge 3$ converged policies) to produce meaningful meta-priors.
- Assumes exchangeability across family members; if one policy is radically different, it can distort the family mean.

## 7. Architectural Invariants

1. **Read-Only Aggregation:** Meta-compilation is strictly a read-only batch aggregation over historical snapshots; it never alters active policies.
2. **Decoupled Local Execution:** Once a policy is seeded from a meta-prior, its runtime updates are 100% localized to its own snapshot.
3. **Action Space Identity:** All policies included in a family compilation must possess identical action spaces.
4. **Storage Law (ADR-002):** Meta-priors reside within standard `PolicySnapshot` records.

## 8. References
- `docs/project-docs/Ideation-Document.md` §2.1 (Methodology #14)
- `ADR-001`: Decision Authority Model
- `ADR-002`: Storage Backend Strategy
- `ADR-020`: Explicit Policy Prior Warm-Starting

