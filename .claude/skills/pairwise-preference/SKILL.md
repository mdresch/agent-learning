---
name: pairwise-preference
description: Guidance for Pairwise Preference Optimization for discrete action logits using the Bradley-Terry model (ADR-018, Epic 18).
---

# Skill: pairwise-preference (agent-learning)

## Overview
This skill governs the Pairwise Preference Optimization learner for discrete action logits (`src/agent_learning_ext/learners/pairwise.py`). It fits a policy's action logits directly to preference pairs (winner, loser) extracted from human override episodes using the Bradley-Terry model with convex L2 regularization anchored to frozen reference logits.

## Governing Specifications & Contracts
- **Architecture:** [`docs/adr/ADR-018-pairwise-preference-optimization.md`](../../docs/adr/ADR-018-pairwise-preference-optimization.md)
- **Business Requirements:** [`docs/project-docs/Business-Requirements/BRD-018-pairwise-preference-optimization.md`](../../docs/project-docs/Business-Requirements/BRD-018-pairwise-preference-optimization.md)
- **Functional Design:** [`docs/project-docs/Functional-Design/FDD-018-pairwise-preference-optimization.md`](../../docs/project-docs/Functional-Design/FDD-018-pairwise-preference-optimization.md)
- **User Stories:** [`docs/user-stories/epic-18-pairwise-preference-optimization.md`](../../docs/user-stories/epic-18-pairwise-preference-optimization.md)
- **Test Contracts:**
  - `tests/test_pairwise_pairs.py` (Story 18.1 — Pairs from episodes, override filter, deduplication, input purity)
  - `tests/test_pairwise_loss.py` (Story 18.2 — Bradley-Terry loss, finite difference gradient, aggregated matrix form)
  - `tests/test_pairwise_fit.py` (Story 18.3 — Projected gradient descent, monotonic step size, box clamp, convergence)
  - `tests/test_pairwise_learner.py` (Story 18.4 — `PairwiseLearner`, frozen reference anchor, storage boundary)
  - `tests/test_pairwise_runner.py` (Story 18.5 — Execution via `TrainingRunner`, idempotence, audit lineage)
  - `tests/test_pairwise_real_data.py` (Story 18.6 — Real-data check on committed episodes, zero pairs assertion)

## Load-Bearing Constraints & Invariants
1. **Upstream Fork Collision Protection (Invariant 6):**
   - Resides in `src/agent_learning_ext/learners/pairwise.py` and re-exported via `src/agent_learning_ext`.
   - `src/agent_learning/` remains 100% byte-for-byte identical to upstream Microsoft HEAD (0 lines diff).
2. **Standard Library Purity & Determinism (Invariant 4):**
   - Plain standard library and `numpy` (already a dependency of `SoftmaxPolicy`).
   - Zero random imports (`random`, `np.random` are forbidden in `fit_logits`).
   - Zero file, socket, or network I/O; zero imports from `agent_learning.storage`.
3. **Data Contract (FDD-018 §2):**
   - `PreferencePair(winner: str, loser: str, source_episode_id: str)`: frozen dataclass.
   - `FitResult(logits: dict[str, float], converged: bool, iterations: int, stationarity: float, step_size: float, loss: float)`: frozen dataclass.
   - Constants: `LAMBDA_MIN = 0.05`, `CLAMP = 8.0`, `LR_DEFAULT = 0.1`, `STEPS_DEFAULT = 2000`, `TOL_DEFAULT = 1e-8`.
4. **Extraction Rules (FDD-018 §3 item 1, G3, G5):**
   - `pairs_from_episodes(episodes, action_ids)` extracts pairs where `metadata["feedback_status"]` (trimmed, lowercased) is `"rejected"`, `metadata["correct_action_id"]` is a string in `action_ids`, `action_id` in `action_ids`, and `correct_action_id != action_id`.
   - Each episode ID yields at most one pair, preserving order of first appearance.
   - Episodes are never modified (`episodes == deepcopy(episodes)`).
5. **Loss, Gradient & Safe Step Size (FDD-018 §2.4, §3 item 2, G1):**
   - $\text{loss}(\theta) = \sum_{(w,l)} W[w][l] \ln(1 + e^{-(\theta_w - \theta_l)}) + \frac{\lambda}{2} \|\theta - \theta_{\text{ref}}\|^2$.
   - Step size $\gamma = \min(\text{lr}, \frac{1}{\lambda + 0.5 \cdot \text{max\_degree}})$ guarantees monotonic non-increasing loss on convex objective.
   - Stationarity stopping rule: $\max_a |\theta_a - \text{clip}(\theta_a - \gamma \cdot \text{grad}_a)| / \gamma < \text{tol}$.
6. **Learner Policy Contract (FDD-018 §3 item 3, G4, G6):**
   - Applies strictly to `SoftmaxPolicy` with `max_logit_abs >= 8.0`.
   - Reference logits $\theta_{\text{ref}}$ frozen into `metadata["pairwise_reference_logits"]` on first non-empty update and never overwritten.
   - `rewards` argument is ignored; returns `mean_reward = 0.0`, `baseline_after = baseline_before`, `consumed_inputs = None`.
7. **TrainingRunner Integration (Story 18.5, FDD-018 §7 item 2):**
   - Re-exported alias `TrainingRunner = LearningRunner` satisfies FDD naming while preserving upstream Invariant 6 fork purity.
   - Idempotent: repeated `run_offline_batch` calls on unchanged episodes leave logits invariant within $10^{-12}$.
   - Audit replay flags `AuditStatus.INSUFFICIENT_LINEAGE` without raising, reflecting external preference replay lineage.
8. **Real-Data Check & Preference Data Boundary (Story 18.6, BRU-018-12):**
   - Historical governance approval episodes (`docs/policy-shapes/episodes/`) are all accepted decisions with zero human override rejections.
   - `pairs_from_episodes` returns zero pairs on recorded history; learner execution leaves policy logits untouched, writes no reference, and returns `episodes_used = 0`.
   - Proves zero-pair historical boundary; makes no quality claim about the learner (missing real override adjudications and unbuilt Red Team pair set).
