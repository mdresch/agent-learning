# ADR 014: Lightweight Critique-to-Evidence Ingestion

## 1. Executive Brief
In the `agent-learning` governance lifecycle, human code reviews, retrospective breakout sessions (Stage 15, ADR-010), and automated Red Team audits produce rich natural language critiques and review findings. However, because the repository enforces a strictly frozen foundation model and CPU-only execution, traditional Supervised Fine-Tuning (SFT) or full Experiential Reinforcement Learning (ERL) with self-reflection cannot update model weights. Furthermore, gradient-based reinforcement learning (REINFORCE, ADR-001) operates only over discrete scalar rewards and cannot absorb semantic diagnostic text.

This ADR introduces **Lightweight Critique-to-Evidence Ingestion** (Methodology #8 from `Ideation-Document.md` §2.1, addressing `HYP-AL-005`). It establishes a deterministic mechanism that parses structured textual critique into numeric criteria support deltas ($\Delta s_c$) and uncertainty adjustments ($u_c$) within an instance-specific `DecisionFrame`. This closes the cognitive loop between textual review findings and Bayesian decision adjudication without modifying foundation model weights or expanding storage schemas.

## 2. Status
**Accepted (2026-10-28, Menno)** — Derived from `Ideation-Document.md` §2.1 (Methodology #8) and `HYP-AL-005`. Approved as a design through `approve-adr` (robust utility 0.662, expected utility 0.744; Episode `22072e4f-1024-48b5-a32d-b5c0a2d48e8b`). Amazon Q reviewed this text in PR #37. Nothing is built; the gaps named in the code-design section stay open.

## 3. Context & Problem Statement
- **The Frozen Model Constraint:** Foundation models in this repository are strictly frozen. Techniques that require backpropagating loss through weights (SFT) are permanently ruled out.
- **The Qualitative-to-Quantitative Semantic Gap:** When an automated reviewer (e.g. Amazon Q) or a human reviewer flags a defect (e.g. "missing boundary validation on negative inputs"), current policies cannot consume this critique directly. The author must manually adjust JSON decision frames or re-draft the entire document.
- **External Precedent:** Microsoft's AutoGen implements Task-Centric Memory, where failed tests trigger an LLM to phrase advice that is appended to future retry prompts. ADR-014 adopts the underlying critique-driven insight while grounding it in mathematically bounded Bayesian criteria adjustments rather than non-deterministic prompt bloating.

## 4. Technical Decision

### 4.1 Critique Mapping Formulation
Let a `DecisionFrame` contain a set of evaluation criteria $C = \{c_1, \dots, c_m\}$.
A textual critique $T$ consists of discrete finding statements. A deterministic parser extracts the criterion tag and the reviewer-supplied delta from each finding. The parser is the only deterministic part: $f_{\text{critique}}$ is the identity on the tagged number, which the reviewer chooses against an explicit rubric (see Negative consequences), and the parser rejects any untagged finding rather than guessing a delta:
$$\Delta s_c = f_{\text{critique}}(T, c), \quad \Delta s_c \in [-1.0, 1.0]$$
The delta moves the criterion's **pooled** support, the value the resolver itself computes, $s_c = \sigma\big(\sum_i c_i \,\text{logit}(p_i)\big)$ over the evidence points $(p_i, c_i)$ of that criterion. The target is clipped away from the edges so the log-odds stay finite:
$$s_c^{*} = \text{clip}(s_c + \Delta s_c, \varepsilon, 1 - \varepsilon), \quad \varepsilon = 10^{-6}$$
The finding is added as one evidence point $(p, c_{\text{new}})$ chosen so that the pooled log-odds land on the target, $c_{\text{new}} \cdot \text{logit}(p) = \text{logit}(s_c^{*}) - \text{logit}(s_c)$, which gives
$$p = \sigma\!\left(\frac{\text{logit}(s_c^{*}) - \text{logit}(s_c)}{c_{\text{new}}}\right)$$
so the pooled support becomes $s_c^{*}$ for any $c_{\text{new}}$. A defect (negative delta) therefore never raises the pooled support, and a confirmation (positive delta) never lowers it.

Only a defect finding adds doubt; a confirming finding leaves the uncertainty unchanged. With $u_c$ equal to one minus the mean confidence of the criterion's points at that step:
$$u_c' = \min(1.0, u_c + \kappa \cdot \max(0, -\Delta s_c)), \quad \kappa \in [0.1, 0.5], \qquad c_{\text{new}} = \max(1 - u_c', 0.05)$$
The resolver measures an option's uncertainty as the entropy of the pooled support, so a defect adds doubt by moving the support toward 0.5; $u_c'$ sets the weight of the appended point and is recorded, and it does not by itself change the option's uncertainty.

### 4.2 Ingestion Interfaces & Tag Schema
Critiques are supplied as structured markdown bullet points or parsed via token extraction:
```markdown
- [criterion: architectural_soundness] -0.20: Unchecked concurrency race on active pointer replace
- [criterion: consequences_honest] +0.10: Explicit disclosure of negative performance trade-offs
```
This section fixes the tag grammar only. The interface (`CritiqueDelta`, which carries a `finding_id`, `parse_critique` and `apply_critique`) is specified once, in section 4.4, so that the evidence source of every change can be traced to its finding (Invariant 3).

### 4.3 Authority & Persistence
- **Authority:** Evaluated strictly under `DecisionAuthority.FULL` via `DecisionResolver`.
- **Storage Boundary (ADR-002 Invariant #2):** The applied critique deltas and raw review findings are persisted strictly within `Episode.metadata["critique_adjustments"]`. Zero new database containers or record types.

### 4.4 Code design and test data
Design only: nothing below is built, and the signatures are the contract an FDD must confirm or change.
Module `src/agent_learning/critique_evidence.py`, standard library only and no file I/O, like `review_triage.py`; callers pass text in and get dataclasses or dicts out.

```python
@dataclass(frozen=True)
class CritiqueDelta:
    criterion_id: str
    support_delta: float     # [-1.0, 1.0]
    rationale: str
    finding_id: str          # e.g. "Q-34-1"; becomes the evidence source

def parse_critique(text: str, source_id: str) -> list[CritiqueDelta]: ...   # ValueError on an untagged or out-of-range line
def apply_critique(frame: DecisionFrame, option_id: str,
                   deltas: Sequence[CritiqueDelta], *, kappa: float = 0.2) -> AppliedCritique: ...
def to_episode_metadata(applied: AppliedCritique) -> dict[str, object]: ...  # {"critique_adjustments": [...]}
```

`DecisionFrame` and `EvidencePoint` are frozen, so `apply_critique` returns an `AppliedCritique` holding a new frame and one adjustment record per delta (with the support and uncertainty before and after). For each delta, in order, it appends an `EvidencePoint(criterion_id, source=f"critique:{finding_id}", support=p, confidence=c)` where $p$ and $c$ come from §4.1, computed against the pooled state left by the previous delta. Appending, rather than editing an existing point, is what makes Invariant 3 (every change cites its finding) hold. A criterion with no evidence on the option raises `ValueError`, since there is nothing to adjust and no prior is invented. A finding without a `[finding: ...]` tag gets the id `<source_id>#<n>`, counting bullets from 1. The full algorithm is in FDD-014 §3.

Tests (`tests/test_critique_evidence.py`): the pooled support after a finding equals the clipped target when measured through `DecisionResolver.resolve()`, a defect never raises and a confirmation never lowers the pooled support, bounds and clipping, uncertainty does not rise on a positive delta, an untagged line is rejected, each changed criterion cites its finding, the input frame is not mutated, metadata round-trips. The Epic 14 stories split these across `tests/test_critique_parse.py`, `tests/test_critique_apply.py` and `tests/test_critique_metadata.py`.

**Test data.** *Real:* the 30 review-triage records in `implementation-log.md` (read with `review_triage.find_triage_lines`): real Amazon Q findings with claim type, verification result and the human decision. A person tags each with a criterion and a delta, recording who tagged it; the check is directional (a finding the human declined should not lower support on the criterion it names). *Gap:* the log keeps the human's one-line reason, not the reviewer's original comment; the originals are in the PR threads and must be exported before tagging. *Oracle tests:* hand-computed expected values for the §4.1 formulas, labeled as arithmetic checks and not as evidence.

**Walkthrough.** [Methodology 8 in the walkthroughs](../learning-methodology-walkthroughs.md#8-critique-to-evidence-adr-014-44). It runs the sketch today; it must be rewritten against the real module once this is built.

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
2. **Deterministic Bounding:** All criteria adjustments $\Delta s_c$ must be bounded in $[-1.0, 1.0]$, and the pooled-support target is clipped to $[\varepsilon, 1 - \varepsilon]$ with $\varepsilon = 10^{-6}$, so the log-odds stay finite.
3. **Audit Traceability:** Every modified criterion in a `DecisionFrame` must cite its triggering critique finding in its evidence source.
4. **Zero Storage Sprawl:** Persisted exclusively in `Episode.metadata["critique_adjustments"]` under ADR-002 Invariant #2.
5. **Direction:** A defect finding never raises the pooled support of the criterion it names, and a confirming finding never lowers it; the pooled support moves by the clipped delta.

## 8. Amendment Log

| Date | Change | Why |
|---|---|---|
| 2026-10-25 | Initial Draft | Candidate derived from Ideation Document §2.1 (Methodology #8). |
| 2026-10-28 | Review fix | The mapper is a parser of reviewer-supplied deltas, not an inference step; uncertainty now rises only on negative deltas, because a confirming finding must not add doubt. |
| 2026-10-28 | Code design | Added §4.4: module layout, signatures, tests, and which real data exists and which is missing. |
| 2026-10-28 | Amazon Q review (PR #37) | Section 4.2 kept a second, older interface (`CritiqueEvidenceMapper`, `CritiqueDelta` without `finding_id`) that contradicted section 4.4. Section 4.2 now fixes only the tag grammar and points to section 4.4 as the single interface. |
| 2026-10-28 | Accepted | Approved by Menno through `approve-adr`: robust utility 0.662, expected utility 0.744; Episode `22072e4f-1024-48b5-a32d-b5c0a2d48e8b`. Design only. |
| 2026-10-28 | Amendment after FDD-014 | Menno confirmed FDD-014 §4 (D1 to D5). Appending a point that carries the adjusted support does not move the pooled support by the delta, because the resolver adds confidence-weighted log-odds: tested on the real resolver, a -0.20 defect finding raised the pooled support from 0.8666 to 0.9188. §4.1 and §4.4 now append a point chosen so the pooled log-odds land on the target (exact for any confidence); `parse_critique` takes a `source_id`; `apply_critique` returns an `AppliedCritique`; a criterion with no evidence raises; Invariant 5 (Direction) added. The role of `u'` is stated as it is in the resolver. |

## 9. References
- `docs/project-docs/Ideation-Document.md` §2.1 (Methodology #8)
- `HYP-AL-005`: Critique-to-evidence Bayesian resolution
- `ADR-001`: Decision Authority Model
- `ADR-002`: Storage Backend Strategy
- `ADR-005`: Decision Progress Comparison

