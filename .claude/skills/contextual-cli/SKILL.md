---
name: contextual-cli
description: Guidance for the contextual-policy changes to agent-learn-ext (task-policy-init --feature-dim, task-policy-decide --features, the train and authority-set refusals) in agent-learning (ADR-038, Epic 38 Stories 38.4 to 38.6).
---

# Skill: contextual-cli (agent-learning)

## Overview
Lets an operator create, call and protect a `ContextualSoftmaxPolicy` snapshot from `agent-learn-ext` (`python -m agent_learning_ext`). The code lives in `src/agent_learning_ext/cli.py` (the fork rule: Microsoft's `src/agent_learning/` is not edited). The learner that trains these weight rows is a separate component (`contextual-learning` skill, Stories 38.1 to 38.3); nothing in the CLI depends on it.

## Governing Specifications & Contracts
- **Architecture:** `docs/adr/ADR-038-packaged-contextual-learning.md` (§4.3, Invariants 6 and 7)
- **Business Requirements:** `docs/project-docs/Business-Requirements/BRD-038-packaged-contextual-learning.md` (BRU-038-07 to 09, 11)
- **Functional Design:** `docs/project-docs/Functional-Design/FDD-038-packaged-contextual-learning.md` (§2.2, §2.3, §3.1 to §3.4, D1 to D5)
- **User Stories:** `docs/user-stories/epic-38-packaged-contextual-learning.md` (38.4, 38.5, 38.6)
- **Test Contract:** `tests/test_contextual_cli.py`

## Load-Bearing Constraints & Invariants
1. **Init (38.4):** `task-policy-init --feature-dim N` builds the snapshot with `ContextualSoftmaxPolicy.from_actions`, then the usual decision-metadata `update`, which must leave `policy_kind`, `feature_dim` and `context_weights` in place. Authority is `low`; `decision_authority_source` is `configured` only when `--decision-authority low` was passed.
2. **Refusals write nothing (38.4):** `--feature-dim` with `--decision-authority full`, and a value below 1, exit 2 before any `store_policy`. A non-integer is an argparse failure (also exit 2).
3. **Omitted flag is unchanged (38.4):** without `--feature-dim` the scalar `SoftmaxPolicy` path runs, including a full-authority init, and the metadata has no `context_weights`, `feature_dim` or `policy_kind`.
4. **Scalar logits stay present and unused:** the snapshot's `logits` map is `{id: 0.0}`. Nothing in the contextual path may read it for a decision (FDD-038 D3).
5. **Decide parses first (38.5):** on a snapshot with `policy_kind` `contextual_softmax`, `task-policy-decide` stores nothing and requires `--features`, an inline JSON list (not a path) of `feature_dim` finite `int` or `float` elements (`bool` refused). Any defect exits 2 with `--features` on stderr, before the shared `--decision-frame` and `capture_decision_evidence` refusals. `--features` on a scalar snapshot exits 2 too; it is never ignored. A contextual snapshot stored with `full` authority exits 2 (init cannot create it).
6. **No scalar gate (38.5, FDD-038 D3):** the contextual path calls `ContextualSoftmaxPolicy.probabilities(phi)` and never `assess_autonomy`, which reads the unused logits. `--greedy` takes the first maximum (a tie keeps the earlier action) and sets `logprob` from that probability; without it `choose(phi)` draws, seeded by `--seed` (the seed does not touch `--greedy`).
7. **Payload (38.5, FDD-038 2.3):** `feature_vector` (each element `float(x)`, for the caller to copy onto `Episode.metadata["feature_vector"]`), `selection_mode` (`sampled` or `greedy`), `selected_action` with `probability` and `logprob`, `action_probabilities`; no `autonomy` key. The command stores no episode and no new policy version (D1).
8. **Scalar commands leave the rows alone (38.6, FDD-038 D2/D4):** `train` skips a `contextual_softmax` snapshot right after the "no active policy" check, with a reason naming `ContextualReinforceLearner`, and builds neither a `SoftmaxPolicy` nor a `LearningRunner` from it (all tasks skipped keeps exit 2). `task-policy-authority-set --authority full` exits 2 naming `full` and `contextual` before any `migration_records` entry or write; `--authority low` stays the idempotent no-op.
9. **No distribution without a vector (38.6, FDD-038 D5):** `_policy_payload` returns `snapshot.to_dict()` for a contextual snapshot (`probabilities(None)` is uniform for any weights, so printing it would mislead); the scalar payload keeps `action_probabilities`. `_policy_difference` returns `None` when either snapshot is contextual, because it read the removed key.
10. **Known gaps (not in the criteria):** `task-policy` still prints an `autonomy` block computed from the unused logits for a contextual snapshot, and `task-policy-authority-set` from a hand-made `full` contextual snapshot to `low` would still record a migration distribution from the unused logits.
