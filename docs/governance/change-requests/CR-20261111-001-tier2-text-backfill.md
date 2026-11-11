---
artifact_type: "manual_change_request"
change_request_id: "CR-20261111-001"
stage: "16"
evidence_basis: "execution"
current_baseline: "PMP-BL-v1.1.0"
status: "draft_awaiting_sponsor_decision"
date: "2026-11-11"
requested_by: "Menno Drescher"
drafted_by: "assistant (draft only; nothing in section 4 is applied)"
---

# Manual Change Request: Tier 2 Text Backfill (GC-P2-04), the Step 8 Checklist (IMP-050) and the Tier 2 Check (IMP-031)

> **Status:** Draft. The Sponsor decides the wording of section 4 (accept, change or strike each row). On approval one PR applies it. Same route as CR-20261110-001.

## 1. Request

Three items of the approved Phase 2 Close Adaptation Plan (`ADP-20261110-002`) put new text into Tier 2 files, and the Sponsor decides that text:

- **GC-P2-04:** the rule of LL-014, 015, 046, 047, 065, 066 and 067 is not in the Tier 2 target the lesson names.
- **IMP-050:** Step 8 of `implement-story` is nine sub-steps in dense prose; Story 21.6 posted a bare `/q confirm`, which Q answered with "too ambiguous to act on", and recorded no triage lines over six review rounds.
- **IMP-031:** LL-045 and LL-048 are in no Tier 2 target (LL-046 and LL-047 are covered by GC-P2-04), and the LL-041 check is still a grep done by hand.

## 2. Why a change request

None of the files below is an approved ADR, BRD, FDD or story, so ADR-007 and `scripts/stage16_amend.py` do not cover them. The route is the one of CR-20261110-001: a change request, a human decision, then one PR that carries the edits and cites each lesson id in the changed text (LL-041).

## 3. Manual Stage 16 assessment

| Assessment field | Assessment |
|---|---|
| Trigger | Stage 16 Step 2d (buckets B and C) and the approved ADP-20261110-002 |
| Evidence basis | `execution` |
| Primary diff type | process (skill text); one comment-only edit in `scripts/spec_gate.py`; no requirement, interface or baseline change |
| Overall impact | Low to medium: it changes what agents read, not what the code does |
| Proposed escalation | Project Sponsor |

## 4. Proposed text (draft for the Sponsor to change)

Each row says where the text goes and gives it in full. The lesson id is part of the text, so the Step 9 check finds it.

### 4a. GC-P2-04: lessons whose rule is not in the named target

| # | File and place | Text to add | Lesson |
|---|---|---|---|
| 1 | `.claude/skills/tailoring/SKILL.md`, Load-bearing constraints, after "Charter prevails" | **Blank is defined once.** Any `Any`-typed input is checked by one helper that treats `None`, blank strings and every empty container (list, tuple, set, frozenset, dict) as blank, and a contract test covers each type. One condition per error message, so the message names what is missing. | LL-014 |
| 2 | `.claude/skills/learning-methodology-selection/SKILL.md`, Load-bearing constraints, last bullet | **Gate the components before the composite.** A methodology that generates several components for one baseline document (for example nine subsidiary plans into the PMP) needs an individual, hash-verified, route-aware gate per component before the composite is formed. A component defect is governed at its gate; only a cross-component conflict is governed at the composite gate. Synthesis asserts that every component meets its route contract (hash match, not a stub) and has no active staleness flag. | LL-015 |
| 3 | `.claude/skills/ucb/SKILL.md`, Load-Bearing Constraints, new item | **Continuous widening is deliberate.** The Wilson and UCB bounds take fractional pseudo-successes ($r = (\text{value}+1)/2 \in [0,1]$, FDD-016 §3 E3). Do not add integer guards to `cumulative_reward`: a reviewer urged this on PR #126 and it would have broken partial-reward accumulation. A widening is documented in the docstring and this skill, covered by a symmetry test on a continuous grid ($1 - \text{wilson\_lower\_bound}(N-k, N) = \text{wilson\_upper\_bound}(k, N)$), and listed as an interpretation by `scripts/spec_gate.py` so triage can cite it. | LL-046 |
| 4 | `.claude/skills/pairwise-preference/SKILL.md`, Load-bearing constraints, new item | **Tight contracts use explicit tolerances.** Where a contract is $10^{-12}$, write `abs(a - b) <= 1e-12` or `math.isclose(a, b, rel_tol=0.0, abs_tol=1e-12)`; the default `rel_tol=1e-9` is 1,000 times looser. Assert against runtime state (`result.episodes_used`, `result.extra['pairs']`, `policy.snapshot().logits`), never against a string the test built itself. | LL-047 |
| 5 | `scripts/spec_gate.py`, the comments at the IMP-024 and IMP-021 rules (about lines 298 and 306) | Comment only, no behaviour change: add "LL-047" to the IMP-024 comment and "LL-046" to the IMP-021 comment. | LL-046, 047 |
| 6 | `.claude/skills/implement-story/SKILL.md`, Step 0, after the worktree sentence | **Data dependencies.** For a story that validates a hypothesis, list each external data source it needs (a donor policy, a failure history) and check the test environment can reach it or a stand-in that meets the hypothesis's preconditions. If it cannot, record the story as blocked on data in the log; do not build more code in its place. | LL-065 |
| 7 | `.claude/skills/implement-story/SKILL.md`, Step 9, after the Status register wording | **One home for story status.** A story's status is kept in `implementation-log.md` only; the epic file's Status line and every roll-up are derived from it (`phase-rollup`). Do not edit a Status line by hand in a story PR. | LL-066 |
| 8 | `.claude/skills/governance/SKILL.md`, section 2.5, new bullet | **One home for gate evidence.** The store at `AGENT_LEARNING_LOCAL_STORE_DIR` (this repository's `data/agent-learning/store`) is the authoritative record; `docs/policy-shapes/episodes/` holds committed copies of it. Before a phase close, list the episode ids in both and report any present in only one. Every gate writes its episode to the store. | LL-067 |

**Open question for the Sponsor (row 7):** LL-066 asks for one canonical location and does not name it. The text above names `implementation-log.md`, because `phase-rollup` already derives "implemented" from it and the story file's Status line is the copy that drifted. If you want the epic file to be canonical instead, row 7 changes and so does the roll-up.

### 4b. IMP-050: a checklist in Step 8

Add under Step 8 of `implement-story`, as a fenced block the agent copies per round. It repeats nothing new; it only puts the literal strings in one place.

````
Step 8 round checklist (copy per round; fill the <>)
[ ] push the fix commit; head commit = <sha>
[ ] review request, first characters of its own comment:
      MSYS_NO_PATHCONV=1 gh pr comment <n> --repo mdresch/agent-learning --body "/q review"
    read it back: it starts with /q (LL-016, LL-021)
[ ] Q's reply is on <sha>; findings read with:
      gh api repos/mdresch/agent-learning/pulls/<n>/comments
[ ] one triage line per finding, in implementation-log.md:
      Q-<n>-<k> | <logic error|crash risk|test gap|documentation|style> | verified: <yes|no|partial|unknown> | decision: <accepted|declined|deferred> | <reason> | fix: <sha|none>
[ ] uv run pytest tests/test_review_triage.py tests/test_critique_replay.py
[ ] final round only, as its own comment (not the last line of another):
      MSYS_NO_PATHCONV=1 gh pr comment <n> --repo mdresch/agent-learning --body "/q confirm whether every earlier finding is resolved in this commit and list anything remaining"
[ ] uv run python scripts/pr_gate.py <n>
[ ] uv run python scripts/pr_gate.py <n> --merge
Round log: <round> | <sha> | <findings> | <verdict>
````

Two facts in it are new to the skill and are checked against the repository: the gate command is `scripts/pr_gate.py` (Step 8.8, 8.9), and the register entry names `/q confirm` as the text that failed when bare. A halt that remains after fixes is not a checklist item; it goes to the Sponsor (waiver route of `## IMP-007` and `## IMP-015` in the log, IMP-065).

### 4c. IMP-031: LL-045 and LL-048, and the LL-041 check

| # | File and place | Text to add | Lesson |
|---|---|---|---|
| 9 | `.claude/skills/implement-story/SKILL.md`, Step 1b, after the "If the gate passes" bullet | The gate also surfaces unstated empty-collection and `None`-handling contracts for replay and parsing code; those become interpretations in the RED docstring (LL-045). | LL-045 |
| 10 | `.claude/skills/implement-story/SKILL.md`, Step 3, at the end | **Subclassing an upstream `Policy`:** `snapshot()` and `actions()` are called by the runner and read as attributes by users, so return `CallableSnapshot` and `CallableActionList` (`agent_learning_ext/policy/epsilon_greedy.py`). When the safe set is empty, assert $\epsilon_t = 0.0$ for all $t$ and document lock-in onto positive-reward actions as the stated price of the mask (BRU-017-03), not as a dead-lock. | LL-048 |

**The LL-041 check as a script (a code change, not text).** Proposed: `scripts/check_tier2_propagation.py` reads the `Tier 2/3 Propagation Target` line of each `LL-###` entry, takes the files named after `Tier 2:`, and lists every id missing from its file; exit 1 if any. Tests with a fake register. It is a separate improvement with its own PR, because section 4a and 4c are text and this is code. After the text lands it should report nothing for the lessons of this request; it will still list older entries (the Step 2d "not applied" ones outside this request), which is its purpose.

### 4d. Story Execution Register: put it into the loop

`docs/registers/Story-Execution-Register.md` has a column per step (0 to 8) and no rows. Nothing writes to it; only `tests/test_project_status_register.py` reads it, to check it exists and still holds the "first real row gets added" marker. Its own text says rows are added prospectively and never backfilled (Stories 1.1 to 20.6 stay in `implementation-log.md`).

| # | File and place | Change |
|---|---|---|
| 11 | `.claude/skills/implement-story/SKILL.md`, Step 7, after "Audit log" | New bullet: **Execution row.** In the same follow-up commit as the log entry, add the story's row to `docs/registers/Story-Execution-Register.md`: for each of Steps 0 to 8, `done` with the evidence (commit, test output, PR number), `skipped` with the reason, or `not recorded`. Never fill a cell from memory or mark a step done that did not happen (LL-028). Step 8 is completed in the row when the PR merges. |
| 12 | `scripts/complete_story.py done` | Writes the row's cells that the script itself saw: Step 0 (branch `feat/story-<X.Y>`), 5 and 6 (contract and full-suite results it ran), 7 (the log commit). Leaves Steps 1 to 4 as `not recorded` unless passed with `--attest "1=<evidence>"`, because the script cannot see that the spec was read or RED was observed. `triage` and the merge fill Step 8. Test with a fake register. |
| 13 | `tests/test_project_status_register.py::test_story_execution_register_exists_and_is_empty` | Today it requires the "first real row gets added" marker, so the first row would break it. Change it to: the file exists, and either holds the marker or every row has all nine step cells filled (`done`, `skipped` or `not recorded`). |
| 14 | The register's "Status" line | "Active, empty" becomes "Active" when the first row lands; the "Trigger for building that TaskPolicy" section stays as written. |

Rows 12 and 13 are code and tests, so they follow section 4c's script as a separate improvement; rows 11 and 14 are text and go with the PR of this request. Recommendation: start with the rows by hand under row 11 for the next story, and add the script only after one real row shows which cells are worth automating. That matches the register's own rule that nothing is built before a real case exists.

### 4e. Future: a Task Ownership Register for a swarm of agents (noted, not built)

Sponsor direction, 2026-11-11: when several agents work in parallel they will need a register where they bid on the tasks to be done, and where the win assigns ownership to one agent. Nothing exists for this and no case has run, so this request only records the need and its relation to 4d.

- It is a separate register from the Story Execution Register: that one records which steps of a story completed; this one would record who owns which task (task id, bids, the awarded agent, status, who decided).
- The Story Execution Register would gain an `Owner` column once ownership exists, so 4d should not hard-code a single actor.
- Open design points, to settle with a real multi-agent case first: how a bid is scored (this repository's own decision machinery is the obvious candidate), whether a human approves each award or only above a risk tier, how an abandoned or stalled task is released, and how two agents are kept from claiming the same worktree (LL-042: an existing story branch means a run was already started).
- Same rule as the Story Execution Register: no TaskPolicy and no invented bids until a real case shows the decision shape.
- Proposed route: register it as an `IMP-###` for the next phase (Continuous Improvement Register) so it reaches the Stage 18 input; not part of this PR.

## 5. Out of scope

- Any Tier 3 (`sidpa-template`) change; each stays "proposed, needs human approval before any cross-repo change".
- LL-017, 027 to 036, 038, 039, 051, 061: covered by CR-20261110-001 or already applied (Step 2d).
- Changing the gate rule behind IMP-065 and IMP-066.

## 6. Decision record

| Role | Decision | Date |
|---|---|---|
| Project Sponsor | Pending: per row of section 4 (accept, change, strike); the row 7 question; whether to build the script of section 4c; hand-filled rows first or the script of section 4d | |

## 7. Procedure after approval

1. One branch, one PR: apply the approved rows; the PR cites this request and each lesson id appears in the changed text.
2. `uv run pytest` (whole suite; `tests/test_project_status_register.py` reads `implement-story`) and `scripts/pr_gate.py`.
3. Mark GC-P2-04, IMP-050 and IMP-031 in `ADP-20261110-002` and the Continuous Improvement Register as applied, through their own record, not by editing this request.
4. If approved, the script of section 4c follows as its own improvement.
