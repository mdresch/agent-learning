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
