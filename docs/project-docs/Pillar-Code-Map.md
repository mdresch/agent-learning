---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope (architectural strategy: code to pillar traceability)"
lifecycle_stage: "Stage 5 (Pillars & Architecture)"
governance_policy: "approve-project-pillars (amendment; not yet run)"
artifact_id: "pillar-code-map"
version: "0.1 (Draft)"
owner: "Menno Drescher"
last_updated: "2026-11-04"
---

# Pillar Code Map: original `microsoft/agent-learning` code

> **Status: Draft, not approved.** It assigns every source file that came from `microsoft/agent-learning` (upstream `476f367`) to one of the nine approved pillars in `Project-Pillars.md`, and records what cover each file has today. It does not change the approved pillars; an amendment to `Project-Pillars.md` and a prospective `approve-project-pillars` run are still needed before this is baselined.

## What this is not yet

Not a claim that the original code is governed. The columns below show the opposite: the original code has Microsoft's own tests but no story, ADR, BRD or FDD behind them, and much of it has no component skill. Closing that is the catch-up this map starts.

## Method

- **Files:** the 54 `src/**/*.py` files (excluding `__init__.py`) present at upstream `476f367`, plus `scripts/estimate_learning_cost.py`. The top-level `pmbok/` package is not upstream code (fork origin, decommission under ADR-034) and is out of scope here.
- **Pillar:** assigned by what the module does, from the pillar statements in `Project-Pillars.md`. Judgment, not measurement.
- **Coverage:** line coverage from running only the 26 test files Microsoft ships (`pytest --cov=agent_learning`, 2026-11-04). Point-in-time; rerun to refresh.
- **Component skill:** a `.claude/skills/*/SKILL.md` that names the file or module. `none` means no skill names it.

## Pillars with no original code

`Critique becomes evidence`, `A new policy inherits a similar policy's prior`, and `A repair path for a stuck low-authority decision` are served only by code this fork added (Epics 14 to 20, ADR-014 to ADR-020). `A hosted layer someone would pay for` has no code anywhere (HYP-AL-011). `An honest place against SFT, RLVR, and ERL` is documentation, not code (`docs/experiential-reinforcement-learning-comparison.md`). The original code therefore lands in four pillars.

## Map

| File | Pillar | Coverage from shipped tests | Component skill |
|---|---|---|---|
| `src/agent_learning/_version.py` | Frozen-model, in-process learning | 100% | none |
| `src/agent_learning/audit.py` | Earned, auditable autonomy | 97% | learner |
| `src/agent_learning/autonomy.py` | Earned, auditable autonomy | 92% | autonomy |
| `src/agent_learning/capture.py` | Earned, auditable autonomy | 76% | none |
| `src/agent_learning/classifiers/base.py` | Frozen-model, in-process learning | 57% | none |
| `src/agent_learning/classifiers/router.py` | Frozen-model, in-process learning | 26% | none |
| `src/agent_learning/classifiers/scorers/_base.py` | Frozen-model, in-process learning | 91% | none |
| `src/agent_learning/classifiers/scorers/adherence.py` | Frozen-model, in-process learning | 71% | none |
| `src/agent_learning/classifiers/scorers/completion.py` | Frozen-model, in-process learning | 71% | none |
| `src/agent_learning/classifiers/scorers/intent.py` | Frozen-model, in-process learning | 71% | none |
| `src/agent_learning/cli.py` | One TaskPolicy for statistical and reasoned resolution | 54% | autonomy, comparison, meta-prior, warm-start |
| `src/agent_learning/config.py` | Earned, auditable autonomy | 95% | autonomy |
| `src/agent_learning/decision.py` | One TaskPolicy for statistical and reasoned resolution | 85% | autonomy |
| `src/agent_learning/learners/base.py` | Frozen-model, in-process learning | 100% | none |
| `src/agent_learning/learners/reinforce.py` | Frozen-model, in-process learning | 99% | learner |
| `src/agent_learning/metrics/base.py` | Frozen-model, in-process learning | 51% | none |
| `src/agent_learning/metrics/intent_resolution.py` | Frozen-model, in-process learning | 45% | none |
| `src/agent_learning/metrics/local.py` | Frozen-model, in-process learning | 80% | none |
| `src/agent_learning/metrics/registry.py` | Frozen-model, in-process learning | 100% | none |
| `src/agent_learning/metrics/task_adherence.py` | Frozen-model, in-process learning | 56% | none |
| `src/agent_learning/metrics/task_completion.py` | Frozen-model, in-process learning | 45% | none |
| `src/agent_learning/policy/base.py` | Frozen-model, in-process learning | 100% | none |
| `src/agent_learning/policy/contextual_softmax.py` | Packaged contextual learning | 85% | none |
| `src/agent_learning/policy/softmax_bandit.py` | Frozen-model, in-process learning | 97% | none |
| `src/agent_learning/rewards/shaping.py` | Frozen-model, in-process learning | 100% | none |
| `src/agent_learning/rewards/writer.py` | Frozen-model, in-process learning | 88% | none |
| `src/agent_learning/scorers/base.py` | Frozen-model, in-process learning | 100% | none |
| `src/agent_learning/scorers/llm/_base.py` | Frozen-model, in-process learning | 98% | none |
| `src/agent_learning/scorers/llm/adherence.py` | Frozen-model, in-process learning | 100% | none |
| `src/agent_learning/scorers/llm/completion.py` | Frozen-model, in-process learning | 100% | none |
| `src/agent_learning/scorers/llm/intent.py` | Frozen-model, in-process learning | 100% | none |
| `src/agent_learning/scorers/nlp/_base.py` | Frozen-model, in-process learning | 100% | none |
| `src/agent_learning/scorers/nlp/adherence.py` | Frozen-model, in-process learning | 100% | none |
| `src/agent_learning/scorers/nlp/completion.py` | Frozen-model, in-process learning | 100% | none |
| `src/agent_learning/scorers/nlp/intent.py` | Frozen-model, in-process learning | 100% | none |
| `src/agent_learning/scorers/nlp_text/_base.py` | Frozen-model, in-process learning | 96% | none |
| `src/agent_learning/scorers/nlp_text/adherence.py` | Frozen-model, in-process learning | 100% | none |
| `src/agent_learning/scorers/nlp_text/completion.py` | Frozen-model, in-process learning | 90% | none |
| `src/agent_learning/scorers/nlp_text/intent.py` | Frozen-model, in-process learning | 100% | none |
| `src/agent_learning/scorers/slm/_base.py` | Frozen-model, in-process learning | 70% | none |
| `src/agent_learning/scorers/slm/adherence.py` | Frozen-model, in-process learning | 93% | none |
| `src/agent_learning/scorers/slm/completion.py` | Frozen-model, in-process learning | 100% | none |
| `src/agent_learning/scorers/slm/intent.py` | Frozen-model, in-process learning | 100% | none |
| `src/agent_learning/scorers/stdlib/_text.py` | Frozen-model, in-process learning | 100% | none |
| `src/agent_learning/scorers/stdlib/adherence.py` | Frozen-model, in-process learning | 100% | none |
| `src/agent_learning/scorers/stdlib/completion.py` | Frozen-model, in-process learning | 96% | none |
| `src/agent_learning/scorers/stdlib/intent.py` | Frozen-model, in-process learning | 100% | none |
| `src/agent_learning/spark.py` | Frozen-model, in-process learning | 46% | none |
| `src/agent_learning/storage/base.py` | Frozen-model, in-process learning | 100% | none |
| `src/agent_learning/storage/cosmos.py` | Frozen-model, in-process learning | 29% | storage |
| `src/agent_learning/storage/local.py` | Frozen-model, in-process learning | 84% | none |
| `src/agent_learning/storage/memory.py` | Frozen-model, in-process learning | 87% | none |
| `src/agent_learning/training/runner.py` | Frozen-model, in-process learning | 99% | learner |
| `src/agent_learning/types.py` | Frozen-model, in-process learning | 100% | thompson |
| `scripts/estimate_learning_cost.py` | Frozen-model, in-process learning | not measured | none |

## Count by pillar

| Pillar | Original files |
|---|---|
| Frozen-model, in-process learning | 48 |
| Earned, auditable autonomy | 4 |
| One TaskPolicy for statistical and reasoned resolution | 2 |
| Packaged contextual learning | 1 |

## Catch-up still needed (not done by this draft)

1. **Governed documents** for the original code: ADR, BRD, FDD and Stories (work packages) written and approved prospectively, one per pillar area. No backdating.
2. **Component skills** for areas where the column says `none`.
3. **Governed contracts** (Story and ADR headed, one test per acceptance criterion) for the original code, starting with files under 60% coverage.
4. **Amendment** of `Project-Pillars.md` and a prospective `approve-project-pillars` run.
