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

## 4. Phase Close Link (Stage 18)

All entries dispositioned `Rolled into Phase Next Intent Refinement` are harvested at Stage 18 into the next phase's Intent Refinement work.
