---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Initiating"
pmbok_process: "Pre-Project / Strategic Need Identification"
lifecycle_stage: "Stage 1 (Intent)"
governance_policy: "approve-ideation"
inputs:
  - "Operational latency and cost friction of fine-tuning"
  - "Unreplayable agent prompt drift in multi-turn execution"
process: "Capture raw problem statement and motivation without premature solutioning"
outputs:
  - "Spark-Capture.md"
---

# Spark Capture — agent-learning

> **PMBOK 8 Process:** `Pre-Project / Strategic Need Identification` (Initiating)  
> **Governance Policy:** `approve-ideation` | **Lifecycle Stage:** `Stage 1 (Intent)`  
> **Inputs:** Operational latency and cost friction of fine-tuning, unreplayable agent prompt drift  
> **Process:** Capture raw problem statement and motivation without premature solutioning  
> **Outputs:** Spark-Capture.md (Source for Ideation-Document.md)

**Date:** 2026-10-20  
**Captured by:** Menno  

## The spark
Autonomous AI agents are repeatedly bottlenecked by heavy, non-deterministic LLM calls for recurring operational choices. Teams attempt to solve this either through expensive GPU fine-tuning (slow, irreversible, opaque) or brittle prompt hacks that drift over time and cannot be audited. 

What if agents had an in-process, lightweight, Bayesian decision-and-learning layer? Keep the foundation model frozen, and give recurring decisions an explicit, interpretable TaskPolicy with mathematically proven confidence bounds and reinforcement bandits.

## Why now
In production agentic loops (e.g. SocialEngage, ADPA, triage bots), agents make thousands of repeated discrete decisions daily. Fine-tuning takes hours to days and is unreplayable. A pure in-process policy layer with Thompson sampling and Softmax updates can learn from feedback in milliseconds with zero GPU overhead.

## What this is not yet
This is pre-Ideation. Don't draft Hypotheses or Objectives here — that belongs in `Ideation-Document.md` and `Project-Charter.md`.
