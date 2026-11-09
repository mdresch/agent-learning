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

# Manual Change Request: Correct the Code Paths Named by Approved Documents for Implemented Modules

> **Status:** Draft for sponsor decision. This request bundles 18 path corrections into one change request. It does not edit an approved document by itself; each document is amended through `scripts/stage16_amend.py`, one at a time, and accepted by a human.

## 1. Request

Eighteen approved documents (six ADRs, six FDDs and six epic story files, for Epics 14, 16, 17, 18, 21 and 22) name the code of an implemented module as `src/agent_learning/...`. The module is in `src/agent_learning_ext/...`, where the fork rule requires it (`tests/test_upstream_untouched.py`). The same trap was corrected for ADR-038 and FDD-038 in PR #152 (LL-050, LL-053). This request corrects the remaining documents in one decision instead of eighteen.

Each correction replaces a wrong path with the path that exists on `main` and changes nothing else. A path is replaced only when the old path is not a tracked file and the new path is.

## 2. Baseline and authority

Approved ADRs, BRDs, FDDs and user stories change only through Stage 16 (ADR-007, `tests/test_governance_baseline.py`). `PMP-BL-v1.1.0` is not revised: no scope, schedule or cost line changes, and no behaviour changes.

## 3. Manual Stage 16 assessment

| Assessment field | Assessment |
|---|---|
| Trigger | The path audit of 2026-11-09 against the tracked files; follows LL-050 and LL-053 |
| Evidence basis | `design_time` |
| Primary diff type | `correction_note` for all 18 documents (measured by `classify-diff-type` through `stage16_amend.py propose`, margin 0.089 to 0.101; evidence under `docs/policy-shapes/` with the tag `cr002`) |
| Overall impact | Low: wording only, no requirement, interface or baseline change |
| Proposed escalation | Project Sponsor |
| Decision status | Pending; no acceptance or governance episode recorded |

## 4. The documents

| Document | File | Path corrected | Proposed classification (margin) |
|---|---|---|---|
| ADR-014 | `docs/adr\ADR-014-critique-to-evidence-ingestion.md` | `src/agent_learning/critique_evidence.py` to `src/agent_learning_ext/critique_evidence.py` | correction_note (0.089) |
| ADR-016 | `docs/adr\ADR-016-deterministic-ucb-decision-policy.md` | `src/agent_learning/policy/ucb.py` to `src/agent_learning_ext/policy/ucb.py` | correction_note (0.089) |
| ADR-017 | `docs/adr\ADR-017-scheduled-epsilon-greedy-policy.md` | `src/agent_learning/policy/epsilon_greedy.py` to `src/agent_learning_ext/policy/epsilon_greedy.py` | correction_note (0.101) |
| ADR-018 | `docs/adr\ADR-018-pairwise-preference-optimization.md` | `src/agent_learning/learners/pairwise.py` to `src/agent_learning_ext/learners/pairwise.py` | correction_note (0.089) |
| ADR-021 | `docs/adr\ADR-021-contextual-authority-ensemble-routing.md` | `src/agent_learning/routing.py` to `src/agent_learning_ext/routing.py` | correction_note (0.089) |
| ADR-022 | `docs/adr\ADR-022-scored-search-decision-compilation.md` | `src/agent_learning/weight_compiler.py` to `src/agent_learning_ext/weight_compiler.py` | correction_note (0.089) |
| FDD-014 | `docs/project-docs/Functional-Design\FDD-014-critique-to-evidence-ingestion.md` | `src/agent_learning/critique_evidence.py` to `src/agent_learning_ext/critique_evidence.py` | correction_note (0.101) |
| FDD-016 | `docs/project-docs/Functional-Design\FDD-016-deterministic-ucb-decision-policy.md` | `src/agent_learning/policy/ucb.py` to `src/agent_learning_ext/policy/ucb.py`; `src/agent_learning/learners/ucb.py` to `src/agent_learning_ext/learners/ucb.py`; `src/agent_learning/policy/action_statistics.py` to `src/agent_learning_ext/policy/action_statistics.py` | correction_note (0.101) |
| FDD-017 | `docs/project-docs/Functional-Design\FDD-017-scheduled-epsilon-greedy-policy.md` | `src/agent_learning/policy/epsilon_greedy.py` to `src/agent_learning_ext/policy/epsilon_greedy.py`; `src/agent_learning/learners/epsilon_greedy.py` to `src/agent_learning_ext/learners/epsilon_greedy.py`; `src/agent_learning/policy/action_statistics.py` to `src/agent_learning_ext/policy/action_statistics.py` | correction_note (0.101) |
| FDD-018 | `docs/project-docs/Functional-Design\FDD-018-pairwise-preference-optimization.md` | `src/agent_learning/learners/pairwise.py` to `src/agent_learning_ext/learners/pairwise.py` | correction_note (0.101) |
| FDD-021 | `docs/project-docs/Functional-Design\FDD-021-contextual-authority-ensemble-routing.md` | `src/agent_learning/routing.py` to `src/agent_learning_ext/routing.py` | correction_note (0.101) |
| FDD-022 | `docs/project-docs/Functional-Design\FDD-022-scored-search-decision-configuration-compilation.md` | `src/agent_learning/weight_compiler.py` to `src/agent_learning_ext/weight_compiler.py` | correction_note (0.101) |
| Epic 14 | `docs/user-stories\epic-14-critique-to-evidence-ingestion.md` | `src/agent_learning/critique_evidence.py` to `src/agent_learning_ext/critique_evidence.py` | correction_note (0.101) |
| Epic 16 | `docs/user-stories\epic-16-deterministic-ucb-decision-policy.md` | `src/agent_learning/policy/ucb.py` to `src/agent_learning_ext/policy/ucb.py`; `src/agent_learning/learners/ucb.py` to `src/agent_learning_ext/learners/ucb.py`; `src/agent_learning/policy/action_statistics.py` to `src/agent_learning_ext/policy/action_statistics.py` | correction_note (0.089) |
| Epic 17 | `docs/user-stories\epic-17-scheduled-epsilon-greedy-policy.md` | `src/agent_learning/policy/epsilon_greedy.py` to `src/agent_learning_ext/policy/epsilon_greedy.py`; `src/agent_learning/learners/epsilon_greedy.py` to `src/agent_learning_ext/learners/epsilon_greedy.py`; `src/agent_learning/policy/action_statistics.py` to `src/agent_learning_ext/policy/action_statistics.py` | correction_note (0.089) |
| Epic 18 | `docs/user-stories\epic-18-pairwise-preference-optimization.md` | `src/agent_learning/learners/pairwise.py` to `src/agent_learning_ext/learners/pairwise.py` | correction_note (0.101) |
| Epic 21 | `docs/user-stories\epic-21-contextual-authority-ensemble-routing.md` | `src/agent_learning/routing.py` to `src/agent_learning_ext/routing.py` | correction_note (0.101) |
| Epic 22 | `docs/user-stories\epic-22-scored-search-decision-configuration-compilation.md` | `src/agent_learning/weight_compiler.py` to `src/agent_learning_ext/weight_compiler.py` | correction_note (0.101) |

## 5. Not in this request

- **Modules that are not built yet.** The FDDs and epics for the plan standards and baseline loop (FDD-026 to FDD-033, FDD-035, FDD-037), and FDD-024, name paths that do not exist yet. Some of them may belong in `agent_learning/` beside the existing `pmbok/` and `review_triage.py`, so they are decided when each epic is implemented.
- **Epic 23.** ADR-023, FDD-023 and Epic 23 name `dueling.py` in both packages and quote the `agent-training-ext/` boundary. Their boundary is condition 2 of CR-20261109-001.
- **History lines.** The `**Status:**` lines of the Epic 14 stories keep "completed in agent-training-ext" as history.
- **Generated plans.** The PMP and the generated plan documents that still name `agent-training-ext/` are regenerated from the tooling, not edited by hand.
- **Import and export wording.** Phrases such as "exported from `agent_learning`" are not part of this correction unless they carry a file path.

## 6. Procedure after the decision

For each document in section 4, in order: apply the replacement, run `stage16_amend.py propose`, run `stage16_amend.py accept` on the Sponsor's explicit instruction with a summary that cites this request, commit the document with its manifest line and evidence files, then take the next document. The governance baseline is refreshed by the script and `tests/test_governance_baseline.py` must pass after every document. No agent accepts on its own.

## 7. Decision record

| Role | Decision | Date |
|---|---|---|
| Project Sponsor | Pending | — |

Until the Sponsor decides, the 18 documents are unchanged.
