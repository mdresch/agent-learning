# Learning Methodologies Landscape: 32-Methodology Taxonomy & Evaluation

> **Library:** Spark & Ideation Research Library (`docs/research/ideation/`)  
> **Source Investigation:** Phase 1 Exploration & Methodology Survey  
> **Author:** Project Contributors & Research Authors  
> **Target System:** `agent-learning` lightweight in-process decision & learning layer

---

## 1. Executive Summary & Evaluation Boundaries

This study documents a comprehensive step-back survey of learning and resolution methodologies from the machine learning and reinforcement learning literature. Rather than assessing whether a technique is academically interesting in the abstract, each methodology was assessed against the core operational constraints of `agent-learning`:
- **Frozen Foundation Model:** Zero GPU training jobs, no hidden prompt rewrites, no model parameter fine-tuning.
- **In-Process & CPU-Only:** Sub-millisecond latency, zero GPU infrastructure overhead.
- **Mathematically Auditable:** Explicit confidence bounds, provable regret or error guarantees, and inspectable criteria tables.
- **Small Discrete Action Spaces:** Decisions among 2 to $N$ explicit executable alternatives.

---

## 2. Comprehensive 32-Methodology Taxonomy

| # | Methodology | Implementable Here? | Categorization & Architectural Assessment |
|---|---|---|---|
| **1** | Supervised Fine-Tuning (SFT) | **No** | Requires updating model weights to copy an example. Contradicts the frozen-model premise outright. Reopens only if a hosted fine-tuning pipeline enters scope. |
| **2** | RLVR / Policy-Gradient Bandit (REINFORCE-with-baseline) | **Yes** | Implemented in production: `SoftmaxPolicy` + `ReinforceLearner` (HYP-AL-001). Stable for contrastive feedback; stalls on positive-only history (HYP-AL-002). |
| **3** | Bayesian / Evidence-Based Reasoned Resolution | **Yes** | Implemented in production: `DecisionResolver` (HYP-AL-003). Non-gradient, multi-criteria decision analysis with Pareto dominance and robust utility. Zero training required. |
| **4** | Contextual Bandit | **Yes, proven feasible** | Example-only (`ContextualSoftmaxPolicy` / `ContextualReinforceLearner`), demonstrated in `examples/next_best_action.py` (HYP-AL-004). |
| **5** | Pluggable Reward Shaping | **Yes** | Implemented in production: Local stdlib metrics and optional Azure AI evaluators feeding scalar rewards into #2. |
| **6** | Durable Explicit Human Override | **Yes** | Implemented in production: Non-gradient, granted trust disposition that pins an action and bypasses statistical gates entirely. |
| **7** | Experiential RL (ERL) — Experience, Reflection, Retry | **No, in full form** | Requires the policy itself to generate and internalize textual reflections into its own weights. Reopens if replayable, resettable agent environments exist. |
| **8** | Lightweight Critique-to-Evidence (ERL-inspired) | **Yes** | Candidate for Phase 2 (Option B): Converts textual review critiques into `DecisionFrame` evidence adjustments without touching model weights (ADR-014, HYP-AL-005). |
| **9** | Thompson Sampling / Bayesian Bandits | **Yes** | Candidate: Computes posterior beta/normal distributions over actions (ADR-015, HYP-AL-002/009). Stochastic sampling requires RNG-seed logging for replayability. |
| **10** | Upper Confidence Bound (UCB) | **Yes** | Implemented in Phase 1 (Option C): Deterministic Wilson-bound bandit (ADR-016, HYP-AL-009). Crosses autonomy gates under positive-only evidence where REINFORCE stalls. |
| **11** | Epsilon-Greedy Bandit | **Yes** | Simpler alternative to #9–10 with scheduled exploration decay (ADR-017). |
| **12** | Active Evidence-Seeking (Information-Gain-Driven) | **Partially** | `InformationNeed` and `estimated_information_gain_bits` implemented on `DecisionResolver`'s `NEEDS_EVIDENCE` path; automated active loop unbuilt. |
| **13** | DPO-Style Pairwise Preference Learning | **Yes** | Candidate for Phase 2 (Option B): Fits Bradley-Terry preference model over paired contrastive decisions (ADR-018). |
| **14** | Meta-Learning Across Structurally Similar TaskPolicies | **Yes** | Candidate: Hierarchical meta-prior compilation across policies sharing action space topology (ADR-019). |
| **15** | Warm-Start / Transfer of Priors | **Yes** | Implemented in Phase 1 (Option A): Seeds a new policy's initial state from a converged donor policy's state, eliminating cold-start volatility (ADR-020, HYP-AL-008). |
| **16** | Model-Based RL | **No** | Contradicts model-free simplicity philosophy for acting. Reopens as off-policy evaluation only (see #29). |
| **17** | Ensemble Routing Across Authority Modes | **Yes** | Candidate: Meta-decision choosing `low` vs `full` authority per-instance based on input entropy and margin (ADR-021). |
| **18** | Federated / Multi-Agent Learning | **Not applicable** | Each `TaskPolicy` is single-agent, single-tenant by design. |
| **19** | Adversarial / Red-Team Example Generation | **Yes** | Practiced as validation testing; converts contrastive failures into training signals. |
| **20** | Diff/Baseline Classification + Scoped Verification | **Yes** | Implemented and validated: `classify-diff-type` correctly classifies artifact changes and tie-breaks cosmetic vs structural changes (HYP-AL-006). |
| **21** | Category-Level Escalation Learning | **Yes** | Implemented (`escalate-diff-response`): Learns human escalation preferences across categories of semantic diffs (HYP-AL-007). |
| **22** | Offline Scored-Search Configuration Compilation (DSPy-style) | **Yes** | Candidate: Optimize `DecisionResolver`'s criteria weights against labeled validation sets via derivative-free search (ADR-022, HYP-AL-010). |
| **23** | Dueling-Bandit / Active-Ranking Pairwise Comparison | **Yes** | Candidate: Adaptively queries pairwise comparisons to rank items with fewer queries than exhaustive $O(n^2)$ matrices (ADR-023, HYP-AL-015). |
| **24** | Linear Contextual Bandit (LinUCB / LinTS) | **Yes** | Candidate: Principled closed-form contextual bandit updating weight vectors per feature row (ADR-038, HYP-AL-018). |
| **25** | Multi-Stage Credit Assignment Across Chains | **Yes, blocked** | Candidate: Propagates reward across sequential decision chains; blocked on `trace_id` serialization standards. |
| **26** | Outcome-Conditioned Exemplar Selection | **Yes** | Candidate: Dynamically selects past episodes as in-context exemplars, logged in metadata (HYP-AL-024). |
| **27** | Prioritized Experience Replay | **Declined** | Overhead exceeds value at low episode volume; revisit only if volume scales $> 100\times$. |
| **28** | Conformal Prediction / Abstention | **Yes** | Candidate: Calibrated statistical trigger to defer to a human when prediction sets exceed threshold size (HYP-AL-019). |
| **29** | Off-Policy Evaluation (OPE / Doubly Robust) | **Yes** | Candidate: Evaluates candidate policies offline against historical logged action probabilities without executing them live (HYP-AL-020). |
| **30** | Non-Stationarity & Change-Point Handling | **Yes** | Candidate: Discounted or sliding-window update rules to adapt to drifting reward distributions (HYP-AL-021). |
| **31** | Constrained Bandits with Hard Action Masking | **Yes** | Candidate: Enforces floors, caps, and safety bounds as zero-probability action masks rather than soft penalties (HYP-AL-022). |
| **32** | Active-Learning Triage for Human Review | **Yes** | Candidate: Prioritizes which autonomous decisions receive scarce human audit budget based on predictive uncertainty (HYP-AL-023). |

---

## 3. Mathematical Distribution & Synthesis

Across the 32 surveyed methodologies:
- **7 Implemented in Packaged Core:** #2, #3, #5, #6, #10, #15, #20.
- **2 Implemented in Examples / Initialized:** #4, #21.
- **3 Structurally Incompatible with Frozen Model:** #1, #7, #16.
- **2 Inapplicable / Declined:** #18, #27.
- **18 Prioritized Candidates:** Staged across Phase 1 and Phase 2 backlogs.
