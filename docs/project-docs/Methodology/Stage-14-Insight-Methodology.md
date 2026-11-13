---
artifact_type: "methodology_guide"
stage: "14"
stage_name: "Insight"
pmbok_process: "4.4 Manage Project Knowledge (Synthesis)"
version: "1.0"
date: "2026-11-12"
owner: "Menno Drescher"
governance_policy: "none declared — resolve-kb-conflict (LOW) is the idealized chain's policy; not built here, so human_review"
---

# Stage 14: Insight — Methodology Guide

> **Purpose:** Synthesize causal understanding from Stage 13's raw observations — why something happened, what it means — before Stage 15 crystallizes it into an actionable lesson.

> **Alignment:** PMBOK 8 Process 4.4 Manage Project Knowledge (Synthesis).

> **Authority:** the idealized Intent-to-Outcome chain designs this stage around a LOW-authority `resolve-kb-conflict` policy (`trust_existing`, `supersede`, or `flag`, deciding whether an insight contradicts an existing knowledge-base node). **This repository has recorded no such decision and declares no such shape** (confirmed: no `resolve-kb-conflict.actions.json` exists under `docs/policy-shapes/`). A policy here is built only once a real, repeating judgment exists to learn from — not speculatively. Until then, Stage 14 is `human_review`: the assistant drafts each insight, the maintainer accepts, changes, or drops it. No episode is created.

---

## 1. Overview

### 1.1 Position in the Chain

```
Stage 13 (Observation) — raw, uninterpreted facts
    ↓
Stage 14 (Insight) — this stage — synthesized causal understanding
    ↓
Stage 15 (Lesson Learned) — crystallizes verified insights into actionable invariants
```

### 1.2 Inputs

| Input | Source | Mandatory |
|---|---|---|
| Observations for the phase | `docs/observations/OBS-NNN.md` | Yes |
| The existing knowledge base (to check for contradiction) | `docs/project-docs/Lessons-Learned-Register.md`, prior insights, approved documents | Yes |

### 1.3 Outputs

| Output | Destination | Governed |
|---|---|---|
| Insight notes | `docs/insights/INSIGHT-NNN.md` (one file per insight) | No (human-reviewed, no episode) |
| Insights roll-up note (phase-level) | `docs/project-docs/Status-Reports/Stage-14-Insights*.md` | No |
| Baseline findings table (where an insight contradicts an approved document) | The phase's Stage 14 note | No, but feeds Stage 16 as a mandatory input |

### 1.4 Success Criteria

Stage 14 is complete, for a phase, when:
- [ ] Every observation that has causal significance has a corresponding insight naming which `OBS-NNN` files it rests on
- [ ] Each insight states the knowledge-base check result: trust existing, supersede, or flag — even without a formal policy, this judgment is made explicitly and recorded
- [ ] An insight that contradicts an approved document is listed as a baseline finding for Stage 16, not quietly folded into a lesson
- [ ] The maintainer has accepted, changed, or dropped each insight before Stage 15 drafts a lesson from it

---

## 2. Process

### Step 1: Group observations by cause

Read the phase's observations together; group the ones that share a root cause. An insight is the interpretation — "why" — behind one or more `OBS-NNN` facts, never a restatement of a single observation without added understanding.

### Step 2: Check against the existing knowledge base

Decide, for each insight: does it agree with what the Lessons Learned Register and approved documents already say (`trust_existing`), does it show an existing node is wrong and should be replaced (`supersede`), or is it genuinely ambiguous (`flag` for the maintainer)? **The knowledge base can never supersede an accepted project document** — if an insight contradicts an ADR/BRD/FDD/Charter, that is a baseline finding for Stage 16, not a knowledge-base supersession.

### Step 3: Submit for maintainer review

Since no policy is declared, this is a direct human review, not an episode. The maintainer accepts, edits, or drops the draft insight.

### Step 4: Hand off

Stage 15 drafts a lesson only from an insight the maintainer has already accepted (or accepted-with-changes). An insight the maintainer dropped does not become a lesson.

---

## 3. Current Instance (as of 2026-11-12)

Real insight files exist: `INSIGHT-001` through `INSIGHT-004` (Phase 1) and `INSIGHT-005` through `INSIGHT-011` (Phase 2, the Phase 2 note calls them `INSIGHT-P2-01` to `P2-07`), under `docs/insights/`. No `resolve-kb-conflict` episode has ever been created in this repository — every one of these was a direct human review, consistent with this methodology's authority statement.

---

## 4. Validation

```bash
ls docs/insights/INSIGHT-*.md | wc -l
grep -rn "resolve-kb-conflict" docs/policy-shapes/ 2>/dev/null   # expect no match: the shape is not declared here
```

---

## 5. Common Pitfalls

| Pitfall | Mitigation |
|---|---|
| Treating the idealized chain's `resolve-kb-conflict` policy as already operative here | It is not declared; this stage is `human_review` until a real repeating judgment justifies building it |
| Letting an insight silently override an approved document | That is a Stage 16 baseline finding, never a quiet knowledge-base supersession |
| Drafting a Stage 15 lesson from an insight the maintainer hasn't accepted yet | Wait for the maintainer's decision; Stage 15 only crystallizes accepted insights |

---

## 6. References

- [Intent-to-Outcome Chain Coverage](../../intent-to-outcome-chain-coverage.md) — §2 row 14, §3.2 ("What exists in this repository, as of 2026-10-27" — superseded for Stage 13/14 by real `OBS`/`INSIGHT` files now on disk; `resolve-kb-conflict` remains correctly undeclared)
- [Stage-14-Insights-Phase2.md](../Status-Reports/Stage-14-Insights-Phase2.md)
- [Stage 13: Observation Methodology](./Stage-13-Observation-Methodology.md)
- [Stage 15: Lesson Learned Methodology](./Stage-15-Lesson-Learned-Methodology.md) — states the same `human_review` authority finding for Stages 13-15

---

## Change Log

| Date | Version | Change |
|---|---|---|
| 2026-11-12 | 1.0 | Initial version, grounded in the real `docs/insights/INSIGHT-001.md` through `INSIGHT-011.md` and the confirmed absence of any `resolve-kb-conflict` policy shape, consistent with Stage 15's own 2026-11-10 authority correction. |
