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

## 4. Phase Close Link (Stage 18)

All entries dispositioned `Rolled into Phase Next Intent Refinement` are harvested at Stage 18 into the next phase's Intent Refinement work.
