# ADR 022: Scored-Search Decision Configuration Compilation

## 1. Executive Brief
In Bayesian multi-criteria decision reasoning (`DecisionResolver`, ADR-001), decisions are evaluated over structured `DecisionFrame` configurations containing criteria weights $\mathbf{w} \in \Delta^{|C|}$, evidence trust discounts, uncertainty penalties, and decision margin thresholds. Currently, these parameters are hand-tuned by software architects based on heuristic intuition (e.g. assigning weight $0.30$ to completeness and $0.20$ to consistency). Hand-tuning risks sub-optimal decision boundaries, vulnerability to adversarial boundary cases, and lack of empirical calibration.

This ADR introduces **Scored-Search Decision Configuration Compilation** (Methodology #22 from `Ideation-Document.md` §2.1, addressing `HYP-AL-010`). Inspired by DSPy's teleprompter compilers (BootstrapFewShot, MIPROv2) and grounded in derivative-free black-box optimization, this offline utility optimizes criteria weights and threshold parameters against a labeled validation suite of past decision episodes, then **freezes** the compiled configuration for zero-overhead runtime deployment.

## 2. Status
**Accepted (2026-10-28, Menno)** — Derived from `Ideation-Document.md` §2.1 (Methodology #22) and `HYP-AL-010`. Approved as a design through `approve-adr` (robust utility 0.650, expected utility 0.734; Episode `032469aa-a602-4ee5-a47c-df789986893f`). Amazon Q reviewed this text in PR #37. Nothing is built; the gaps named in the code-design section stay open.

## 3. Context & Problem Statement
- **The Heuristic Weight Trap:** In ADR-001 through ADR-011, criteria weights were set manually by authors. While transparent, manual weights cannot guarantee that the resulting decision margin $\Delta \mathcal{U}$ is maximized or that edge-case ties are properly resolved.
- **The Non-Differentiability of Decision Logic:** `DecisionResolver` includes non-differentiable operations: hard constraint rule-outs, Pareto dominance pruning, and entropy calculations. Standard gradient descent cannot be backpropagated through this logic.
- **External Framework Validation:** DSPy demonstrated that optimizing pipeline configurations via offline derivative-free search against an objective metric—and then deploying the resulting configuration frozen—is far more stable and auditable than online heuristic tuning.

## 4. Technical Decision

### 4.1 Optimization Formulation
Let $\mathcal{V} = \{(\text{Frame}_j, y_j^*)\}_{j=1}^M$ be a validation set of historical `DecisionFrame` instances paired with their ground-truth human adjudication dispositions $y_j^* \in A$.
Let $\boldsymbol{\phi} = (\mathbf{w}, \lambda_{\text{uncertainty}}, \epsilon_{\text{margin}})$ represent the configuration vector, where $\mathbf{w} \in \mathbb{R}^{|C|}$ satisfies $\sum_{i=1}^{|C|} w_i = 1.0$ and $w_i \ge 0$.

The compiler optimizes $\boldsymbol{\phi}$ to maximize a multi-objective loss:
$$\boldsymbol{\phi}^* = \arg\max_{\boldsymbol{\phi}} \sum_{j=1}^M \left[ \mathbb{I}[\hat{y}_j(\boldsymbol{\phi}) = y_j^*] + \beta \cdot \text{Margin}_j(\boldsymbol{\phi}) \right]$$
Where:
- $\hat{y}_j(\boldsymbol{\phi})$ is the action chosen by `DecisionResolver` under configuration $\boldsymbol{\phi}$.
- $\text{Margin}_j(\boldsymbol{\phi}) = \mathcal{U}(\text{leader}) - \mathcal{U}(\text{runner-up})$ rewards decisive, non-ambiguous separation, with utilities on $[0, 1]$ so the margin is on $[0, 1]$.
- $\beta = 0.1$ by default, so that one correct disposition always outweighs any margin gain.

**Train/holdout split.** The labeled set is split before the search: at least 30% is held out and never seen by the search (or $k$-fold with $k \ge 5$ for small sets). Reported accuracy is holdout accuracy only. The human weights in force today are scored on the same holdout as the baseline.

**Label independence.** Labels are human adjudications, and the same humans set the current weights, so agreement with labels partly measures agreement with the author. A label set is usable only if each label was recorded before the compiled weights were proposed.

### 4.2 Derivative-Free Optimization Engine
Because the objective function is non-differentiable, optimization is conducted via:
1. **Coordinate Ascent with Grid Restarts (primary):** Iteratively adjusts individual criteria weights in steps of $\Delta w = \pm 0.05$, renormalizing $\mathbf{w}$ after each step. It suits the objective, which is piecewise constant because the accuracy term only changes when a disposition flips.
2. **Nelder-Mead Simplex Search (secondary):** constrained to the probability simplex $\Delta^{|C|}$ and run only on a smoothed objective (the accuracy term replaced by a softmax-margin surrogate), because on the raw indicator it stalls on plateaus.
Execution runs on standard CPU hardware in $<10 \text{ seconds}$ for validation sets of $M \le 500$ frames.

### 4.3 Offline Freeze & Runtime Invariance
- Optimization is strictly an **offline batch compilation step** invoked via the CLI:
  ```powershell
  python -m agent_learning.cli policy-compile-weights \
    --task-id approve-adr \
    --validation-dataset tests/fixtures/governance/adr_validation_suite.json \
    --output-snapshot compiled_adr_approval_v2.json
  ```
- **Zero Runtime Overhead:** In production, `DecisionResolver` reads the frozen compiled weights from `PolicySnapshot.metadata["criteria_weights"]`. No search, exploration, or optimization runs during online request handling.

### 4.4 Code design and test data
Design only: nothing below is built, and the signatures are the contract an FDD must confirm or change.
Module `src/agent_learning/weight_compiler.py`, pure (frames and labels in, weights out); `policy-compile-weights` in `cli.py` does the file and snapshot work. It reuses `DecisionResolver` so the compiled weights are scored by the real resolver.

```python
@dataclass(frozen=True)
class LabeledFrame:
    frame: DecisionFrame; label: str; labeled_at: str

def split_holdout(items: Sequence[LabeledFrame], *, fraction: float = 0.3, seed: int) -> tuple[list, list]: ...
def objective(weights: Mapping[str, float], items, snapshot, *, beta: float = 0.1) -> float: ...
def coordinate_ascent(items, snapshot, *, step: float = 0.05, restarts: int = 5) -> CompiledWeights: ...
def propose(train, holdout, snapshot) -> CompiledWeights | NoImprovement: ...   # Invariant 5
```

Tests (`tests/test_weight_compiler.py`): weights stay on the simplex, no hard constraint is relaxed (a ruled-out option never wins), the same input gives the same output, the holdout set is untouched by the search, and `propose` returns `NoImprovement` when holdout accuracy does not beat the current weights.

**Test data.** *Real:* the repository holds 48 decision frames under `docs/policy-shapes/decision-frames/` with 97 stored results and the recorded adjudications, all real. They make a real regression set: compiled weights must not change a human-accepted outcome. *Gap:* every real label is the same class (approve accepted), so accuracy is trivially 100% and the set cannot show that compilation improves anything. Needed: frames where the human disagreed with the resolver. Labels were also recorded after the frames were scored, which satisfies the label-independence rule only if `labeled_at` precedes the proposal. *Oracle tests:* small hand-built frames with a known best weight vector, labeled as arithmetic.

**Walkthrough.** [Methodology 22 in the walkthroughs](../learning-methodology-walkthroughs.md#22-scored-search-compilation-adr-022-44). It runs the sketch today; it must be rewritten against the real module once this is built.

## 5. Alternatives Considered

| Alternative | Rationale for Rejection |
|---|---|
| **Manual Heuristic Tuning (Status Quo)** | Vulnerable to subjective bias, uncalibrated decision margins, and regression on boundary cases. |
| **Online Gradient Ascent** | Fails because `DecisionResolver`'s hard constraints and Pareto pruning are non-differentiable step functions. |
| **Full LLM Teleprompting (DSPy Prompts)** | Compiling natural language prompt text introduces non-deterministic model variance; compiling numeric criteria weights preserves exact mathematical auditability. |

## 6. Consequences

### Positive
- Replaces guesswork with empirical, reproducible criteria weight calibration.
- Maximizes robust decision margins, reducing ambiguous tie-breaks and unnecessary human escalations.
- Zero latency or CPU penalty at runtime; production policies remain purely deterministic and frozen.

### Negative
- Requires maintaining a curated, labeled validation set of historical decision frames.
- If the validation set lacks diversity, compiled weights can overfit to specific past examples.

## 7. Architectural Invariants

1. **Strict Offline Execution:** Configuration search must run exclusively in offline batch compilation; runtime execution is strictly read-only against frozen snapshots.
2. **Simplex Invariant:** Compiled criteria weights must sum to exactly $1.0$ ($\sum w_i = 1.0$) with all $w_i \ge 0.0$.
3. **Hard Constraint Inviolability:** Optimization cannot override or relax hard constraints (`ruled_out_by`).
4. **Storage Boundary (ADR-002):** Compiled configuration parameters are stored in `PolicySnapshot.metadata` with zero database changes.
5. **Holdout Acceptance:** Compiled weights are proposed only if their holdout accuracy is at least that of the weights in force; otherwise the compiler reports "no improvement" and changes nothing.
6. **Human Adoption:** A compiled snapshot is a proposal. Activating it needs an explicit human decision recorded as an episode.

## 8. References
- `docs/project-docs/Ideation-Document.md` §2.1 (Methodology #22)
- `HYP-AL-010`: Offline parameter compilation
- `ADR-001`: Decision Authority Model
- `ADR-002`: Storage Backend Strategy


## 9. Amendment Log

| Date | Change | Why |
|---|---|---|
| 2026-10-25 | Initial Draft | Candidate derived from Ideation Document §2.1 (Methodology #22). |
| 2026-10-28 | Review fix | Added the holdout split, a defined beta, the label-independence rule, holdout acceptance and human adoption (Invariants 5 and 6). Coordinate ascent is now primary and Nelder-Mead runs on a smoothed surrogate, because the raw objective is piecewise constant. |
| 2026-10-28 | Code design | Added §4.4: module layout, signatures, tests, and which real data exists and which is missing. |
| 2026-10-28 | Accepted | Approved by Menno through `approve-adr`: robust utility 0.650, expected utility 0.734; Episode `032469aa-a602-4ee5-a47c-df789986893f`. Design only. |