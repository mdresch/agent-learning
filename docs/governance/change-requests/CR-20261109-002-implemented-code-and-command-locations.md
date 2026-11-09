---
artifact_type: "manual_change_request"
change_request_id: "CR-20261109-002"
stage: "16"
evidence_basis: "design_time"
current_baseline: "PMP-BL-v1.1.0"
status: "draft_pending_sponsor_decision"
date: "2026-11-09"
requested_by: "Menno Drescher"
---

# Manual Change Request: Align Approved Documents With Where Implemented Code and Commands Live

> **Status:** Draft for sponsor decision. This request bundles 26 corrections into one change request. It does not edit an approved document by itself; each document is amended through `scripts/stage16_amend.py`, one at a time, and accepted by a human.

## 1. Request

26 approved documents (9 ADRs, 8 FDDs and 9 epic story files) say something about implemented code that is no longer true. The fork rule (`tests/test_upstream_untouched.py`) puts everything we add in `src/agent_learning_ext/` and reaches our commands through `agent-learn-ext`. The same two traps were corrected for ADR-038 and FDD-038 in PR #152 (LL-050, LL-053). This request corrects the rest in one decision instead of 26.

Two kinds of correction, both wording only:

1. **Module path (18 documents).** The document names `src/agent_learning/<file>.py` for a module that is tracked as `src/agent_learning_ext/<file>.py`. A path is replaced only when the old path is not a tracked file and the new one is.
2. **CLI location or name (11 documents).** The document says a command lives in `cli.py` or `src/agent_learning/cli.py`, or names the binary `agent-learn`, for a command that exists only in `src/agent_learning_ext/cli.py`, reached with `agent-learn-ext` (checked command by command: `task-policy-meta-compile`, `task-policy-family-set`, `task-policy-warm-start`, `policy-compile-weights`, `task-policy-routing-set` and `task-policy-compare` each appear in the extension CLI and not in Microsoft's).

## 2. Baseline and authority

Approved ADRs, BRDs, FDDs and user stories change only through Stage 16 (ADR-007, `tests/test_governance_baseline.py`). `PMP-BL-v1.1.0` is not revised: no scope, schedule or cost line changes, and no behaviour changes.

## 3. Manual Stage 16 assessment

| Assessment field | Assessment |
|---|---|
| Trigger | The path and wording audit of 2026-11-09 against the tracked files; follows LL-050 and LL-053 |
| Evidence basis | `design_time` |
| Primary diff type | `correction_note` for all 26 documents (measured by `classify-diff-type` through `stage16_amend.py propose`, margin 0.089 to 0.101; evidence under `docs/policy-shapes/` with the tag `cr002b`) |
| Overall impact | Low: wording only, no requirement, interface or baseline change |
| Proposed escalation | Project Sponsor |
| Decision status | Pending; no acceptance or governance episode recorded |

## 4. The documents

| Document | File | Kind | Correction | Proposed classification (margin) |
|---|---|---|---|---|
| ADR-005 | `docs/adr/ADR-005-decision-progress-comparison.md` | CLI location or name | "agent-learn task-policy-compare" to "agent-learn-ext task-policy-compare" | correction_note (0.101) |
| ADR-014 | `docs/adr/ADR-014-critique-to-evidence-ingestion.md` | module path | `src/agent_learning/critique_evidence.py` to `src/agent_learning_ext/critique_evidence.py` | correction_note (0.089) |
| ADR-016 | `docs/adr/ADR-016-deterministic-ucb-decision-policy.md` | module path | `src/agent_learning/policy/ucb.py` to `src/agent_learning_ext/policy/ucb.py` | correction_note (0.089) |
| ADR-017 | `docs/adr/ADR-017-scheduled-epsilon-greedy-policy.md` | module path | `src/agent_learning/policy/epsilon_greedy.py` to `src/agent_learning_ext/policy/epsilon_greedy.py` | correction_note (0.101) |
| ADR-018 | `docs/adr/ADR-018-pairwise-preference-optimization.md` | module path | `src/agent_learning/learners/pairwise.py` to `src/agent_learning_ext/learners/pairwise.py` | correction_note (0.089) |
| ADR-019 | `docs/adr/ADR-019-hierarchical-meta-prior-compilation.md` | CLI location or name | "lives in cli.py and does the storage reads" to "lives in src/agent_learning_ext/cli.py and does the storage reads" | correction_note (0.101) |
| ADR-020 | `docs/adr/ADR-020-explicit-policy-prior-warm-starting.md` | CLI location or name | "task-policy-warm-start in cli.py does the reads and writes" to "task-policy-warm-start in src/agent_learning_ext/cli.py does the reads and writes" | correction_note (0.101) |
| ADR-021 | `docs/adr/ADR-021-contextual-authority-ensemble-routing.md` | module path | `src/agent_learning/routing.py` to `src/agent_learning_ext/routing.py` | correction_note (0.089) |
| ADR-022 | `docs/adr/ADR-022-scored-search-decision-compilation.md` | CLI location or name and module path | `src/agent_learning/weight_compiler.py` to `src/agent_learning_ext/weight_compiler.py`; "policy-compile-weights in cli.py does the file" to "policy-compile-weights in src/agent_learning_ext/cli.py does the file" | correction_note (0.089) |
| FDD-014 | `docs/project-docs/Functional-Design/FDD-014-critique-to-evidence-ingestion.md` | module path | `src/agent_learning/critique_evidence.py` to `src/agent_learning_ext/critique_evidence.py` | correction_note (0.101) |
| FDD-016 | `docs/project-docs/Functional-Design/FDD-016-deterministic-ucb-decision-policy.md` | module path | `src/agent_learning/policy/ucb.py` to `src/agent_learning_ext/policy/ucb.py`; `src/agent_learning/learners/ucb.py` to `src/agent_learning_ext/learners/ucb.py`; `src/agent_learning/policy/action_statistics.py` to `src/agent_learning_ext/policy/action_statistics.py` | correction_note (0.101) |
| FDD-017 | `docs/project-docs/Functional-Design/FDD-017-scheduled-epsilon-greedy-policy.md` | module path | `src/agent_learning/policy/epsilon_greedy.py` to `src/agent_learning_ext/policy/epsilon_greedy.py`; `src/agent_learning/learners/epsilon_greedy.py` to `src/agent_learning_ext/learners/epsilon_greedy.py`; `src/agent_learning/policy/action_statistics.py` to `src/agent_learning_ext/policy/action_statistics.py` | correction_note (0.101) |
| FDD-018 | `docs/project-docs/Functional-Design/FDD-018-pairwise-preference-optimization.md` | module path | `src/agent_learning/learners/pairwise.py` to `src/agent_learning_ext/learners/pairwise.py` | correction_note (0.101) |
| FDD-019 | `docs/project-docs/Functional-Design/FDD-019-hierarchical-meta-prior-compilation.md` | CLI location or name | "CLI wiring in src/agent_learning/cli.py:" to "CLI wiring in src/agent_learning_ext/cli.py:" | correction_note (0.101) |
| FDD-020 | `docs/project-docs/Functional-Design/FDD-020-explicit-policy-prior-warm-starting.md` | CLI location or name | "CLI wiring in src/agent_learning/cli.py:" to "CLI wiring in src/agent_learning_ext/cli.py:" | correction_note (0.101) |
| FDD-021 | `docs/project-docs/Functional-Design/FDD-021-contextual-authority-ensemble-routing.md` | CLI location or name and module path | `src/agent_learning/routing.py` to `src/agent_learning_ext/routing.py`; "One command in cli.py:" to "One command in src/agent_learning_ext/cli.py:" | correction_note (0.101) |
| FDD-022 | `docs/project-docs/Functional-Design/FDD-022-scored-search-decision-configuration-compilation.md` | CLI location or name and module path | `src/agent_learning/weight_compiler.py` to `src/agent_learning_ext/weight_compiler.py`; "Two commands in cli.py:" to "Two commands in src/agent_learning_ext/cli.py:" | correction_note (0.101) |
| Epic 5 | `docs/user-stories/epic-5-decision-progress-comparison.md` | CLI location or name | "agent-learn task-policy-compare --sequence" to "agent-learn-ext task-policy-compare --sequence" | correction_note (0.101) |
| Epic 14 | `docs/user-stories/epic-14-critique-to-evidence-ingestion.md` | module path | `src/agent_learning/critique_evidence.py` to `src/agent_learning_ext/critique_evidence.py` | correction_note (0.101) |
| Epic 16 | `docs/user-stories/epic-16-deterministic-ucb-decision-policy.md` | module path | `src/agent_learning/policy/ucb.py` to `src/agent_learning_ext/policy/ucb.py`; `src/agent_learning/learners/ucb.py` to `src/agent_learning_ext/learners/ucb.py`; `src/agent_learning/policy/action_statistics.py` to `src/agent_learning_ext/policy/action_statistics.py` | correction_note (0.089) |
| Epic 17 | `docs/user-stories/epic-17-scheduled-epsilon-greedy-policy.md` | module path | `src/agent_learning/policy/epsilon_greedy.py` to `src/agent_learning_ext/policy/epsilon_greedy.py`; `src/agent_learning/learners/epsilon_greedy.py` to `src/agent_learning_ext/learners/epsilon_greedy.py`; `src/agent_learning/policy/action_statistics.py` to `src/agent_learning_ext/policy/action_statistics.py` | correction_note (0.089) |
| Epic 18 | `docs/user-stories/epic-18-pairwise-preference-optimization.md` | module path | `src/agent_learning/learners/pairwise.py` to `src/agent_learning_ext/learners/pairwise.py` | correction_note (0.101) |
| Epic 19 | `docs/user-stories/epic-19-hierarchical-meta-prior-compilation.md` | CLI location or name | "in cli.py; Story 19.8" to "in src/agent_learning_ext/cli.py; Story 19.8" | correction_note (0.101) |
| Epic 20 | `docs/user-stories/epic-20-explicit-policy-prior-warm-starting.md` | CLI location or name | "task-policy-warm-start in cli.py. Each rule" to "task-policy-warm-start in src/agent_learning_ext/cli.py. Each rule" | correction_note (0.101) |
| Epic 21 | `docs/user-stories/epic-21-contextual-authority-ensemble-routing.md` | module path | `src/agent_learning/routing.py` to `src/agent_learning_ext/routing.py` | correction_note (0.101) |
| Epic 22 | `docs/user-stories/epic-22-scored-search-decision-configuration-compilation.md` | module path | `src/agent_learning/weight_compiler.py` to `src/agent_learning_ext/weight_compiler.py` | correction_note (0.101) |

## 5. Checked and left unchanged

- **All BRDs.** No BRD names a wrong code path. BRD-013 and BRD-034 mention `agent-learning pmbok` commands that are not built (section 6).
- **Dotted module names.** No ADR, BRD, FDD or epic names an `agent_learning.<module>` that exists only in `agent_learning_ext`.
- **Modules that are correctly in `agent_learning/`.** `meta_prior.py`, `warm_start.py`, `review_triage.py`, `methodology_catalog.py` and the `pmbok/` files are our own files in that package, not Microsoft's, so their paths stand.
- **Citations of Microsoft's own code.** ADR-003 and FDD-004 cite lines of Microsoft's `src/agent_learning/cli.py` as it was; that file still exists.
- **History lines.** The `**Status:**` lines of the Epic 14 and Epic 5 stories keep "completed in agent-training-ext" and `agent-learn task-policy-compare` as history.
- **Generated plans.** The PMP and the generated plan documents that still name `agent-training-ext/` are regenerated from the tooling, not edited by hand.

## 6. Held until the epic is implemented

- **Modules not built yet.** FDD-024, FDD-026 to FDD-033, FDD-035, FDD-037 and Epic 24 name paths that do not exist. They are decided when each epic is implemented.
- **The `agent-learn pmbok` commands (ADR-013, ADR-034, BRD-013, BRD-034, FDD-013, FDD-034, Epics 13 and 34).** The commands are not built (Stories 34.4 and 34.5 are Draft). ADR-034 Invariant 5 ("CLI Singularity") and BRU-034-05 say the one entry point is `agent-learn` in `src/agent_learning/cli.py`, which is a Microsoft file and may not be edited. That conflict is decided before Story 34.4 starts, by amending ADR-034, BRD-034 and FDD-034 together.
- **Epic 23.** ADR-023, FDD-023 and Epic 23 name `dueling.py` in both packages and quote the `agent-training-ext/` boundary; they stay with CR-20261109-001, whose Stage 17 package resolves the boundary.

## 7. Procedure after the decision

For each document in section 4, in order: apply the correction, run `stage16_amend.py propose`, run `stage16_amend.py accept` on the Sponsor's explicit instruction with a summary that cites this request, commit the document with its manifest line and evidence files, then take the next document. The governance baseline is refreshed by the script and `tests/test_governance_baseline.py` must pass after every document. No agent accepts on its own.

## 8. Decision record

| Role | Decision | Date |
|---|---|---|
| Project Sponsor | Pending | — |

Until the Sponsor decides, the 26 documents are unchanged.
