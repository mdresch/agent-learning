---
name: weight-compiler
description: Guidance for scored-search decision configuration compilation (ADR-022, Epic 22, Story 22.2).
---

# Skill: weight-compiler (agent-learning)

## Overview
Scored-search decision configuration compilation optimizes criteria weights offline against a labeled validation suite of past decision episodes, then freezes the compiled configuration for zero-overhead runtime deployment. This skill covers `src/agent_learning_ext/weight_compiler.py` and related CLI commands and tests.

## Governing Specifications & Contracts
- **Architecture:** [`docs/adr/ADR-022-scored-search-decision-compilation.md`](../../docs/adr/ADR-022-scored-search-decision-compilation.md)
- **Business Requirements:** [`docs/project-docs/Business-Requirements/BRD-022-scored-search-decision-configuration-compilation.md`](../../docs/project-docs/Business-Requirements/BRD-022-scored-search-decision-configuration-compilation.md)
- **Functional Design:** [`docs/project-docs/Functional-Design/FDD-022-scored-search-decision-configuration-compilation.md`](../../docs/project-docs/Functional-Design/FDD-022-scored-search-decision-configuration-compilation.md)
- **User Stories:** [`docs/user-stories/epic-22-scored-search-decision-configuration-compilation.md`](../../docs/user-stories/epic-22-scored-search-decision-configuration-compilation.md)
- **Test Contracts:**
  - `tests/test_weight_split.py` (Story 22.2: Hold-out splitting and label timing rule)

## Load-Bearing Constraints & Invariants
1. **Invariant 6 (Upstream Fork Purity):** All implementations reside under `src/agent_learning_ext/weight_compiler.py` and are exported via `src/agent_learning_ext/__init__.py`. Upstream `src/agent_learning/` remains untouched.
2. **Storage Decoupling [I2]:** `weight_compiler.py` imports nothing from `agent_learning.storage` and performs no file I/O.
3. **Reproducible Hold-Out (AC_0):** `split_holdout(items, *, fraction=0.3, seed)` returns reproducible disjoint partitions that sum to the input collection across calls and fresh Python processes.
4. **Split Sizes & Validation (AC_1):** `split_holdout` requires `0.3 <= fraction <= 0.5`, an integer seed, and ensures at least `MIN_PART` (5) items in both training and held-out partitions, raising `ValueError` otherwise.
5. **Order Independence (AC_2):** `split_holdout` deterministically sorts items prior to shuffling with `random.Random(seed)`, guaranteeing that input list permutations do not alter the resulting partitions.
6. **Label Timing Validation (AC_3):** `validate_label_timing(items, proposed_at)` validates that every item's `labeled_at` is strictly earlier than `proposed_at`. If `labeled_at >= proposed_at`, it raises `ValueError` naming the item.
7. **Held-Out Untouched (AC_4):** Offline training search and evaluations run exclusively on the training partition without invoking the resolver on held-out items.
