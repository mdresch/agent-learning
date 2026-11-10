# Critique Evidence Ingestion Example — Summary

## Purpose
Demonstrates **Structured Critique-to-Evidence Ingestion** (ADR-014 / Epic 14). Agents making high-stakes decisions evaluate options against multiple criteria. While quantitative metrics provide baseline scores, human code reviews or architectural critiques deliver rich qualitative findings. This example demonstrates parsing markdown critique bullets into structured deltas, updating `DecisionFrame` evidence via Bayesian log-odds pooling and doubt inflation ($\kappa$), and observing how `DecisionResolver` shifts recommendations.

File: [critique_evidence_demo.py](critique_evidence_demo.py)

## Problem Setup
An automated release manager selects a deployment architecture for a high-throughput settlement engine.

| Element | Definition |
|---|---|
| **Actions** | Option A (`async_batch`: high-throughput async pipeline) vs. Option B (`sync_atomic`: conservative 2PC sync pipeline) |
| **Criteria** | `reliability` (weight = 0.60, crash resilience) and `throughput` (weight = 0.40, peak speed) |
| **Critique Input** | Markdown text containing tagged review findings: `[criterion: ...]`, `[claim: ...]`, `[verified: ...]`, or explicit numeric deltas |
| **Rubric Table** | Calibrated delta lookup mapping claim types (`crash risk`, `test gap`, `style`, `confirmation`) to support adjustments |
| **Doubt Updating** | Uncertainty multiplier $\kappa = 0.20$ inflates doubt upon defect discovery: $u_{\text{after}} = \min(1.0, u + \kappa \cdot \text{defect})$ |

## Core Building Blocks
| Object | How the example uses it |
|---|---|
| **`parse_critique`** | Parses bullet findings from Markdown text using tag grammar into structured `CritiqueDelta` records. |
| **`apply_critique`** | Pools log-odds of existing evidence points, calculates target support, inflates doubt, and appends synthetic `EvidencePoint`s. |
| **`DecisionResolver`** | Resolves `DecisionFrame` under a `PolicySnapshot`, evaluating feasibility, robust utility, and margins. |
| **`to_episode_metadata`** | Formats critique adjustments into JSON-serializable dictionaries for episode storage and downstream auditing. |

## Flow
1. **Initial Decision State**: Option A leads initially due to high claimed throughput and benchmark reliability:
   - Option A (`async_batch`): robust utility = +0.7552 (**Selected**)
   - Option B (`sync_atomic`): robust utility = +0.5762
2. **Reviewer Markdown Critique**: Security reviewers inspect Option A and submit four findings:
   - Crash risk on timeout (`claim: crash risk`, `verified: yes` $\to -0.30$)
   - Test coverage gap (`claim: test gap`, `verified: partial` $\to -0.08$)
   - Adversarial cache eviction penalty (explicit $-0.15$)
   - Backwards-compatible schema (`claim: confirmation`, `verified: yes` $\to +0.10$)
3. **Structured Ingestion & Doubt Penalty**: `apply_critique` adjusts support and raises uncertainty on Option A using $\kappa = 0.20$.
4. **Resolution Shift**: Re-evaluating with `DecisionResolver` shows Option A's robust utility dropping from +0.7552 to +0.5000, causing a clean **decision flip** to Option B (+0.5762).
5. **Episode Metadata Serialization**: Serializes adjustment audit trails.

## Results (deterministic, seed-fixed)
```
Decision Resolution BEFORE Critique:
  Status: RESOLVED
  Selected Action: 'async_batch'
  - Option 'async_batch': robust_utility = +0.7552
  - Option 'sync_atomic': robust_utility = +0.5762

Parsed Critique Findings:
  [REV-4089#1] Criterion: reliability  Delta: -0.30 (rubric: crash risk / yes)
  [REV-4089#2] Criterion: reliability  Delta: -0.08 (rubric: test gap / partial)
  [REV-4089#3] Criterion: throughput   Delta: -0.15 (explicit delta)
  [confirmation-01] Criterion: reliability Delta: +0.10 (rubric: confirmation / yes)

Decision Resolution AFTER Critique:
  Status: RESOLVED
  Selected Action: 'sync_atomic' (Decision Flipped!)
  - Option 'async_batch': robust_utility = +0.5000
  - Option 'sync_atomic': robust_utility = +0.5762
```

## Key Learnings
1. **Unstructured reviews become formal evidence:** The tag grammar bridges natural-language code critiques and mathematical decision theory.
2. **Doubt inflation is asymmetric:** Negative defect findings not only reduce support but increase uncertainty via $\kappa$, penalizing robust utility more heavily.
3. **Full audit lineage:** Every synthetic evidence point points back to `critique:<finding_id>`, enabling complete decision auditability and explainability.

## How It Differs From the Other Examples
| | [critique_evidence_demo.py](critique_evidence_demo.py) | [weight_compiler_demo.py](weight_compiler_demo.py) | [quickstart.py](quickstart.py) |
|---|---|---|---|
| Input Format | Markdown review bullets | Historical labeled frames | Scalar rewards |
| Mechanism | Evidence point appending & doubt inflation | Simplex criteria weight tuning | Policy gradient update |
| Decision Engine | Multi-criteria `DecisionResolver` | Multi-criteria `DecisionResolver` | Softmax bandit sampling |

## Run It
```powershell
uv run python examples/critique_evidence_demo.py
```
