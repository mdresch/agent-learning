# Continuous Improvement Register (Organizational Process Assets)

**Origin:** Instantiated from the `sidpa-template` Continuous Improvement Register (commit `6471422`).  
**Lifecycle Role:** Positive, generative counterpart to the [Lessons Learned Register](Lessons-Learned-Register.md). Held once per epic, after its last user story, as part of `implement-story` Step 9.  
**Maintenance Rule:** Append-only. A recap with nothing new is recorded as a short sign-off line in the Epic Recap Log.  
**Downstream Feed:** Stages 16/17 (in-flight fast-path change) and Stage 18 (`Intent Refinement`).

---

## 1. Purpose

The Lessons Learned Register takes a defensive posture: traps, defects and root causes. This register takes the positive one. It captures improvement ideas, architectural simplifications, developer-experience boosts and product opportunities while the knowledge from an epic is fresh.

### The mandatory per-epic cadence question

At the epic's last story (Step 9):

> *"What improvement ideas, architectural simplifications, developer-experience boosts, or product opportunities emerged during this Epic that could add value to upcoming Epics or roll into the Intent Refinement Proposal for the next phase?"*

- **Ideas emerged:** record each as an `IMP-###` entry in section 2.
- **None emerged:** record `Epic [N] Recap: No new improvement ideas identified.` in section 3.

### Dispositions

1. **`In-Flight Candidate`:** can be introduced in the active phase without expanding baseline scope. Evaluated through the governance change pipeline (Stages 16 to 17).
2. **`Rolled into Phase Next Intent Refinement`:** valuable but beyond the current baseline. Harvested at Phase Close (Stage 18) into the next phase's Intent Refinement.

An entry records only what the epic's work actually surfaced. Do not seed this register with examples or speculative ideas.

---

## 2. Improvement Ideas

| ID | Originating Epic | Idea Title | Category | Description & Technical Value | Target Benefit / Outcome | Disposition |
|---|---|---|---|---|---|---|
| IMP-001 | Epic 15 | Provision a story worktree and log a no-finding review with one command each | Developer experience | `scripts/complete_story.py` gains `worktree <story>` (git worktree add, `uv sync --all-extras`, remove the real `azure-cosmos`; LL-033) and `triage --none` (the prose line of LL-034), and appends the `Co-Authored-By` trailer to its commits. All three were repeated by hand in each of the six stories. | Fewer false REDs and CI failures per story | In-Flight Candidate |
| IMP-002 | Epic 15 | Make the Thompson sampling record self-describing | Architectural simplification | Add the policy id (the snapshot id used as the HMAC key) to the FDD-015 §2.3 record, so `replay(record)` needs no second argument and a record stays replayable after a learner update gives the snapshot a new id (interpretations I2 and I5; FDD-015 §7 item 6). | An auditor can replay a draw from the record alone | In-Flight Candidate |
| IMP-003 | Epic 15 | Find the failure history that HYP-AL-002 needs | Product opportunity | Story 15.6 could only show consistency on an all-accepted history. A low-authority policy with at least 100 scored episodes including failures would let the Thompson-versus-REINFORCE question be answered with data (BRD-015 BRU-015-10). | Evidence for or against adopting Thompson sampling in a decision | Rolled into Phase Next Intent Refinement |
| IMP-004 | Epic 19 | Read a stored meta-prior back into a `MetaPrior` | Architectural simplification | `seed_values` takes a `MetaPrior`, but `task-policy-meta-compile` stores a `PolicySnapshot`. Epic 20's `task-policy-warm-start --meta-prior` (Story 20.5) has to rebuild the `MetaPrior` from the snapshot's metadata. One small, tested function that does it (and refuses a snapshot that is not a meta-prior) would be shared by that command and by any reader. | Story 20.5 does not re-derive the shape | In-Flight Candidate |
| IMP-005 | Epic 19 | Read a Thompson policy by the probability that each action is the best | Product opportunity | ADR-003 §4.6 gates a posterior policy on normalised payoff rates, a proxy that cannot be met when several actions have similar rates (FDD-019 §7 items 8 to 10). A seeded Monte Carlo draw from the posteriors, or the closed form for two actions, gives the probability of being best and can use thresholds calibrated for it. | A Thompson policy with several plausible actions can earn autonomy on evidence | Rolled into Phase Next Intent Refinement |
| IMP-006 | Epic 19 | Commit a small recorded-store fixture so real-data checks run in CI | Developer experience | `data/agent-learning/` is git-ignored, so Story 19.7 rebuilds a store from committed episodes, action files and decision results and checks the recorded store only where it exists (FDD-019 §7 item 11). A committed, minimal export of the governance store (policies and active pointers, not secrets) would let such checks read the real thing everywhere. | Real-data tests are identical on every machine | In-Flight Candidate |
| IMP-007 | Epic 19 | One command for an approval run: frame, decide, compare, register | Developer experience | Approving the ADR, the FDD and the stories took a frame builder, a decision, a comparison script, an adjudication and an episode builder each time, six hand-written scripts, and one run checked the wrong store (LL-040). A `scripts/approve.py` that takes scores, prints the resolved store path, runs the steps, shows the comparison and registers only on an explicit flag would remove that. | Fewer mistakes and a repeatable audit trail per approval | In-Flight Candidate |
| IMP-008 | Epic 19 | Move the posterior-gate story out of Epic 19 | Architectural simplification | Story 19.8 changes `autonomy.py`, outside the epic's scope; the `approve-user-stories` comparison classified the epic as a regression for that reason (scope correctly bounded -0.030) and Menno accepted it. Epic 3, the autonomy-gate epic, is its natural home. | Epic 19 keeps its scope; the gate change sits with the gate | Rolled into Phase Next Intent Refinement |
| IMP-009 | Epic 20 | Share the real-data test helpers | Developer experience | Stories 19.7 and 20.6 each carry their own copy of `_recorded_tasks`, `_build_store` and `_tree` (rebuild a temporary store from `docs/policy-shapes/`). Amazon Q flagged the same unguarded `policy_id` read in both (Q-98-1, Q-101-1), and Story 21.7 needs a third copy. One shared helper module (or fixture) fixes a defect once and makes the git-ignored-store rule (FDD-019 §7 item 11, FDD-020 §7 item 7) live in one place. | A review finding on real-data tests is fixed once, not per story; Story 21.7 starts from the helper | Rolled into Phase Next Intent Refinement |
| IMP-010 | Epic 20 | Report which stored policies could donate | Product opportunity | Story 20.6 showed that no usable warm-start donor exists, but only as a test result. A read-only command (for example `task-policy-donor-candidates`) would list each stored policy with its authority, episodes seen, updates applied, whether its logits are non-zero and whether `assess_autonomy` is met, and the reason each cannot donate. HYP-AL-008 needs one converged low-authority donor and a cold same-family target; this shows when they exist. | The missing real donor is detected from the store, not rediscovered by hand; input to the HYP-AL-008 test plan | Rolled into Phase Next Intent Refinement |
| IMP-011 | Epic 20 | Flag stories whose status disagrees with the log | Developer experience | Stories 20.1 to 20.3 stayed `Ready` after they were built and logged; found only when Story 20.6 was opened. A small check (script or test) that fails when an `implementation-log.md` entry exists for a story whose status is not `Completed`, or the reverse, would catch status drift at review time. | Epic status lines can be trusted when planning the next phase | Rolled into Phase Next Intent Refinement |
| IMP-012 | Epic 20 | Detect an existing story branch or worktree before Step 0 | Developer experience | Extends IMP-001's `worktree <story>` command: if `feat/story-<X.Y>` or its worktree already exists, print the branch, `git status --short`, the commits ahead of `main` and the story's log entry, and point to `heal-contract-failure` (the rule added to `implement-story` Step 0 in PR #105). In Story 20.6 a started run was adopted because nothing stopped it. | A started run is healed from Intent, never adopted or implemented twice; the rule is enforced by the tool, not only by the skill text | Rolled into Phase Next Intent Refinement |
| IMP-013 | Epic 20 | Build the Cosmos test fakes' exceptions in one place | Developer experience | `tests/test_storage_cosmos.py` constructed `azure-cosmos` exceptions with the message as the first positional argument; the SDK now formats that argument as a status code, so four Story 2.1 contract tests failed on `main` until PR #102. A single helper that builds the fake exceptions with `status_code` and `message` (or a CI run against the latest SDK) shows this kind of SDK drift where it starts. | SDK changes break one helper, visibly, not four contract tests in an unrelated story | Rolled into Phase Next Intent Refinement |
| IMP-014 | Phase 1 close | Move the Stage 18 tooling onto the path ADR-034 keeps | Architectural simplification | `evaluate_phase_close_readiness`, hypothesis adjudication and `seed-next` exist only in the legacy `pmbok/` tree that ADR-034 plans to delete, and their tests are excluded from CI (INSIGHT-003, LL-043, AUDIT-004). Port them to `src/agent_learning/pmbok/` as pure functions with tests CI runs, or amend ADR-034 to keep them, before Stories 34.4 and 34.5 delete the tree. | Phase close tooling that CI protects and that survives the decommissioning | Rolled into Phase Next Intent Refinement |

---

## 3. Epic Recap Log

One entry per epic recap, appended in the order held. Format:

```
### Epic <N>: <title>
- **Cadence Date:** <YYYY-MM-DD>
- **Defensive Review (LL-###):** <LL ids or no-new-lessons>
- **Positive Improvement Harvest:** <IMP ids, or "Epic <N> Recap: No new improvement ideas identified.">
```

---

### Epic 15: Bayesian Bandit Posterior Sampling (Thompson Sampling)
- **Cadence Date:** 2026-11-03
- **Defensive Review (LL-###):** LL-033, LL-034, LL-035
- **Positive Improvement Harvest:** IMP-001, IMP-002, IMP-003

---

### Epic 19: Hierarchical Meta-Prior Compilation Across Task Families
- **Cadence Date:** 2026-11-04
- **Defensive Review (LL-###):** LL-036, LL-037, LL-038, LL-039, LL-040
- **Positive Improvement Harvest:** IMP-004, IMP-005, IMP-006, IMP-007, IMP-008

---

### Epic 20: Explicit Policy Prior Warm-Starting
- **Cadence Date:** 2026-11-04
- **Defensive Review (LL-###):** LL-041, LL-042
- **Positive Improvement Harvest:** IMP-009, IMP-010, IMP-011, IMP-012, IMP-013

---

## 4. Phase Close Link (Stage 18)

All entries dispositioned `Rolled into Phase Next Intent Refinement` are harvested at Stage 18 into the next phase's Intent Refinement work.
