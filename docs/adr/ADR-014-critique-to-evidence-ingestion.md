# ADR 014: Lightweight Critique-to-Evidence Ingestion

## 1. Executive Brief
In the `agent-learning` governance lifecycle, human code reviews, retrospective breakout sessions (Stage 15, ADR-010), and automated Red Team audits produce rich natural language critiques and review findings. However, because the repository enforces a strictly frozen foundation model and CPU-only execution, traditional Supervised Fine-Tuning (SFT) or full Experiential Reinforcement Learning (ERL) with self-reflection cannot update model weights. Furthermore, gradient-based reinforcement learning (REINFORCE, ADR-001) operates only over discrete scalar rewards and cannot absorb semantic diagnostic text.

This ADR introduces **Lightweight Critique-to-Evidence Ingestion** (Methodology #8 from `Ideation-Document.md` §2.1, addressing `HYP-AL-005`). It establishes a deterministic mechanism that parses structured textual critique into numeric criteria support deltas ($\Delta s_c$) and uncertainty adjustments ($u_c$) within an instance-specific `DecisionFrame`. This closes the cognitive loop between textual review findings and Bayesian decision adjudication without modifying foundation model weights or expanding storage schemas.

## 2. Status
**Proposed (2026-10-25)** — Derived from `Ideation-Document.md` §2.1 (Methodology #8) and `HYP-AL-005`. Ready for multi-criteria evaluation under `approve-adr`.

## 3. Context & Problem Statement
- **The Frozen Model Constraint:** Foundation models in this repository are strictly frozen. Techniques that require backpropagating loss through weights (SFT) are permanently ruled out.
- **The Qualitative-to-Quantitative Semantic Gap:** When an automated reviewer (e.g. Amazon Q) or a human reviewer flags a defect (e.g. "missing boundary validation on negative inputs"), current policies cannot consume this critique directly. The author must manually adjust JSON decision frames or re-draft the entire document.
- **External Precedent:** Microsoft's AutoGen implements Task-Centric Memory, where failed tests trigger an LLM to phrase advice that is appended to future retry prompts. ADR-014 adopts the underlying critique-driven insight while grounding it in mathematically bounded Bayesian criteria adjustments rather than non-deterministic prompt bloating.

## 4. Technical Decision

### 4.1 Critique Mapping Formulation
Let a `DecisionFrame` contain a set of evaluation criteria $C = \{c_1, \dots, c_m\}$.
A textual critique $T$ consists of discrete finding statements. A deterministic mapper parses target criteria tags:
$$\Delta s_c = f_{\text{critique}}(T, c), \quad \Delta s_c \in [-1.0, 1.0]$$
The updated support $s_c'$ is clipped to the unit interval:
$$s_c' = \text{clip}(s_c + \Delta s_c, 0.0, 1.0)$$
The epistemic uncertainty $u_c'$ expands proportionally to the magnitude of the delta, reflecting increased doubt:
$$u_c' = \min(1.0, u_c + \kappa \cdot |\Delta s_c|), \quad \kappa \in [0.1, 0.5]$$

### 4.2 Ingestion Interfaces & Tag Schema
Critiques are supplied as structured markdown bullet points or parsed via token extraction:
```markdown
- [criterion: architectural_soundness] -0.20: Unchecked concurrency race on active pointer replace
- [criterion: consequences_honest] +0.10: Explicit disclosure of negative performance trade-offs
```
The SDK provides `CritiqueEvidenceMapper`:
```python
@dataclass(frozen=True)
class CritiqueDelta:
    criterion_id: str
    support_delta: float
    rationale: str

class CritiqueEvidenceMapper:
    @staticmethod
    def apply_critique(
        frame: DecisionFrame,
        critiques: Sequence[CritiqueDelta],
        uncertainty_penalty_factor: float = 0.2
    ) -> DecisionFrame:
        ...
```

### 4.3 Authority & Persistence
- **Authority:** Evaluated strictly under `DecisionAuthority.FULL` via `DecisionResolver`.
- **Storage Boundary (ADR-002 Invariant #2):** The applied critique deltas and raw review findings are persisted strictly within `Episode.metadata["critique_adjustments"]`. Zero new database containers or record types.

## 5. Alternatives Considered

| Alternative | Rationale for Rejection |
|---|---|
| **Supervised Fine-Tuning (SFT) on Critique** | Contradicts the frozen foundation model invariant outright; requires GPU training infrastructure. |
| **Full Generative Reflection (ERL)** | Demands that the policy itself generate and internalize textual self-reflections, requiring generative LLM policies rather than discrete decision bandits. |
| **Ad-Hoc Prompt Concatenation** | Appending raw critique text to prompts increases token costs, induces context drift, and lacks quantitative reproducibility. |

## 6. Consequences

### Positive
- Converts natural language review feedback (from code reviews, PR comments, and retrospective breakout sessions) into quantitative decision evidence.
- Fully compatible with frozen models and CPU-only runtime execution.
- Enables automated iterative refinement loops with `task-policy-compare` (ADR-005).

### Negative
- Requires reviewers or parsing agents to tag critique findings with target criterion identifiers.
- Heuristic support deltas introduce subjective variance if not calibrated against explicit rubrics.

## 7. Architectural Invariants

1. **Frozen Model Invariance:** Critique ingestion never updates model weights or fine-tunes embeddings.
2. **Deterministic Bounding:** All criteria adjustments $\Delta s_c$ must be bounded in $[-1.0, 1.0]$ and clipped to $[0.0, 1.0]$.
3. **Audit Traceability:** Every modified criterion in a `DecisionFrame` must cite its triggering critique finding in its evidence source.
4. **Zero Storage Sprawl:** Persisted exclusively in `Episode.metadata["critique_adjustments"]` under ADR-002 Invariant #2.

## 8. References
- `docs/project-docs/Ideation-Document.md` §2.1 (Methodology #8)
- `HYP-AL-005`: Critique-to-evidence Bayesian resolution
- `ADR-001`: Decision Authority Model
- `ADR-002`: Storage Backend Strategy
- `ADR-005`: Decision Progress Comparison

