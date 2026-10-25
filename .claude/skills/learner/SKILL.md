---
name: learner
description: ReinforceLearner policy update and authority boundary enforcement (Stage 18/ADR-001 §4.5).
---

# Component: learner (`agent_learning.learners`)

**Governing:** ADR-001 §4.5, BRD-001, FDD-001, Story 1.1 (`docs/user-stories/epic-1-decision-authority-enforcement.md`).
**Contract:** `tests/test_learner.py`, `tests/test_audit.py`.

## Load-bearing constraints

- **Strict Authority Exclusion (ADR-001 §4.5 / BRU-001-01):**
  - Any episode with `action_logprob is None` is a `full`-authority (reasoned, non-sampled) decision.
  - `ReinforceLearner.update()` MUST exclude such episodes inside its own per-episode loop, rather than reweighting them via fallback importance weight.
  - Excluded episodes do NOT increment `episodes_used`, do NOT enter `consumed_inputs`, and contribute zero gradient delta to policy logits.
- **Auditable Exclusion Accounting (FDD-001 / AC1):**
  - `LearnerResult.extra["full_authority_excluded"]` reports the count of full-authority episodes excluded on every call (including `0`).
- **Preserved Low-Authority Importance Sampling (BRU-001-04 / AC2):**
  - Episodes with `action_logprob` set (e.g., decisions logged under an older policy version) continue to be reweighted via importance-sampling ratio $\pi_{\text{target}} / \pi_{\text{behaviour}}$, clipped to `config.importance_clip`.
- **Learner-Level Boundary Enforcement (BRU-001-02 / AC4):**
  - The check is placed inside `ReinforceLearner.update()`, protecting all callers at once: `LearningRunner.run_offline_batch()`, `audit.py:444` (replay reconstruction), and `audit.py:503` (per-episode attribution).
- **Audit Warning Alignment (FDD-001 / AC3):**
  - When `audit.py` encounters episodes with `action_logprob is None`, it emits:
    `"One or more full-authority episodes (action_logprob is None) were present in this batch and excluded from the REINFORCE update, not reweighted — see ADR-001 §4.5."`
- **Zero Schema Expansion (ADR-002 Invariant #2 / BRU-001-03):**
  - No new fields added to `Episode`; `action_logprob is None` is the sole and unambiguous indicator.

## Call sites

- `src/agent_learning/learners/reinforce.py`: `ReinforceLearner.update()`.
- `src/agent_learning/training/runner.py`: `LearningRunner.run_offline_batch()`.
- `src/agent_learning/audit.py`: `audit_run()` lines 444 and 503.
