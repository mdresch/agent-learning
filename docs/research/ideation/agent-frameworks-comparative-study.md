# Agent Frameworks Comparative Study: Empirical Evaluation of "Agent Learning" Claims

> **Library:** Spark & Ideation Research Library (`docs/research/ideation/`)  
> **Source Investigation:** Phase 1 External Framework Validation  
> **Target Question:** *Do existing production agent frameworks actually implement outcome-driven learning, or is "learning" marketing for memory storage?*

---

## 1. Executive Summary

To establish an honest competitive baseline and ensure `agent-learning` is not reinventing existing wheels or overlooking shipping industry patterns, eight leading agent frameworks and platforms were audited against primary documentation, GitHub repositories, and package internals.

**Key Finding:** 
Of the eight platforms surveyed, **four ship no real learning mechanism at all**—their "learning" is pure retrieval-augmented generation (RAG) over vector memory. Of the remaining four, three independently validate architectural concepts pioneered in `agent-learning` (human override trust, reflection-to-critique, and model routing), while DSPy contributed the concept of offline compilation (#22).

---

## 2. Comparative Matrix

| Framework | Vendor | Does it Learn from Outcomes? | Primary Mechanism Audited | Architectural Takeaway for `agent-learning` |
|---|---|:---:|---|---|
| **LangGraph** | LangChain | **No** | Vector Store with embedding-similarity retrieval injected into prompts. Pure recall; no scoring, optimization, or behavior update based on execution success/failure. | Confirms vector memory is storage, not learning. `agent-learning` fills the missing decision-optimization layer. |
| **Semantic Kernel** | Microsoft | **No** | Semantic Memory recall pattern. Planners generate execution graphs, but plans do not update based on runtime success metrics. | Planners lack feedback loops; confirms need for lightweight bandit routing. |
| **OpenAI Agents SDK** | OpenAI | **No** (Textual self-journaling only) | Sandbox `Memory` summarizes and consolidates execution traces into `MEMORY.md` via LLM calls. No objective metrics, trainsets, or search. | Textual journaling accumulates context but does not optimize decision policy parameters. |
| **Haystack** | deepset | **No** | Pipelines support runtime loops, but evaluation components only output human-readable scores. No feedback loop updates execution choices. | Evaluation decoupled from policy adaptation. |
| **AutoGen** | Microsoft | **Yes (Experimental)** | **Task-Centric Memory:** Test $\to$ failure $\to$ LLM diagnoses and phrases advice $\to$ retry with advice appended $\to$ loop until reliable $\to$ persist insight. | **Direct validation of Methodology #8 (Critique-to-Evidence / HYP-AL-005).** Industry-recognized pattern for turning textual review into structured evidence. |
| **CrewAI** | CrewAI | **Yes** | **`crew.train()`:** Records human free-text feedback per agent role across iterations, persists it, and re-injects it into future prompts. | **Direct validation of Methodology #6 (Durable Human Override).** Independent confirmation that human-feedback-as-trust is an essential non-gradient mechanism. |
| **DSPy** | Stanford | **Yes (Offline Compilation)** | **Teleprompters (`BootstrapFewShot`, `MIPROv2`, `GEPA`):** Derivative-free search optimizing prompt/demo weights against a labeled validation set, then **freezes** the configuration. | **Inspired Methodology #22 (Scored-Search Compilation / HYP-AL-010).** Optimizing `DecisionResolver` criteria weights offline against past labeled decisions. |
| **GitHub Copilot Auto / Model Router** | Microsoft | **Yes (In Production)** | Scores prompts on code/reasoning complexity and real-time model availability, routing across cost/quality tiers via trained policy. | **Direct validation of Methodology #4 (Contextual Bandit) and #9–10 (UCB/Thompson).** Validates model routing at massive hyperscale. |

---

## 3. Analysis of Proposed Secondary Candidates

A secondary review round proposed five additional candidate learning mechanisms from industry marketing:
1. *Persistent Semantic Memory Learning*
2. *Agent Teachability*
3. *Memory Extraction / Consolidation*
4. *Iterative Human-Feedback Adaptation*
5. *Plan-Policy Learning*

### Verification & Disposition
- **Items 1 & 2 (Persistent Memory & Teachability):** Re-verified against LangGraph and AutoGen Teachability docs; both are embedding-based RAG recall. They alter context windows, not policy behavior.
- **Item 3 (Memory Extraction/Consolidation):** Verified against CrewAI docs; consolidation is write-time deduplication/merging via LLM similarity. It is ETL, not outcome-conditioned learning.
- **Item 4 (Iterative Adaptation):** Is identical to `crew.train()`, already cataloged under Methodology #6.
- **Item 5 (Plan-Policy Learning):** Semantic Kernel planners are static planning algorithms, not learned policies.

**Strategic Conclusion:** While competing agent frameworks invest almost exclusively in memory, recall, and personalization infrastructure, `agent-learning` focuses on **decision authority, mathematical evidence aggregation, and autonomy gating**. This confirms that `agent-learning` occupies a distinct, largely uncontested architectural space.
