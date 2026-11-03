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

## 4. Phase Close Link (Stage 18)

All entries dispositioned `Rolled into Phase Next Intent Refinement` are harvested at Stage 18 into the next phase's Intent Refinement work.
