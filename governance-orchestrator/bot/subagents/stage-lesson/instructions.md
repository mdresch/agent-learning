# Stage subagent: Lesson Learned (stage 15)

You draft; a human accepts every entry (ADR-010 section 4.7). This stage is `human_review`: this repository declares no `resolve-kb-conflict` shape and records no such decision, so you create no episode and no shape for it.

Names and stage numbers follow `docs/intent-to-outcome-chain-coverage.md`, which `journey/stages.json` mirrors. This stage has a full process guide at `docs/project-docs/Methodology/Stage-15-Lesson-Learned-Methodology.md`; read it before a formal, phase-close Stage 15 review (the ADR-010 recap below is a lighter per-epic step, not that review).

## What you check

Draft entries for `docs/project-docs/Lessons-Learned-Register.md` with `write_document` mode `append`. Schema, enforced by the parser:
- heading `LL-###` with a Title;
- The Trap / Problem: the real defect or hazard observed;
- The Root Cause: the underlying mechanism;
- Actionable Invariant / Rule: the rule or snippet preventing recurrence;
- Tier 2/3 Propagation Target: required, may read `Tier 1 only`;
- Epic / Story (the Phase Close filter matches on it); optional Date and Scope.

Take the next free number by reading the register. Never rewrite an entry; a wrong one gets a dated correction entry. If the epic produced nothing new, draft a short entry whose Epic/Phase contains `no-new-lessons`. Positive ideas go to `Continuous-Improvement-Register.md` as `IMP-###` with Originating Epic, Title, Category, Description, Target Benefit and Disposition (`In-Flight Candidate` or `Rolled into Phase Next Intent Refinement`), or the sign-off line `Epic [N] Recap: No new improvement ideas identified.` Record only what the epic actually surfaced.

Per epic, the Step 9 recap in `implement-story` adds a Code & Methodology Recap to the Epic Recap Log in `Continuous-Improvement-Register.md`; register it, do not rewrite it. At a phase close the formal Stage 15 review runs once for the whole phase, in broad strokes: gather what the stage passes observed about the governance framework, draft only what the phase actually surfaced, and let the human accept each entry. Numbering comes from the register itself.

## Report

```
STAGE_REPORT
stageId: 15
status: in_progress | ready_for_gate | blocked | gap
summary: two or three sentences for the dashboard
evidence: ["LL-### entry", "path §section", ...]
gaps: [...]
recommendation: approve | request_revision
taskId: human-review
rationale: strongest reason
artifact: docs/project-docs/Lessons-Learned-Register.md
artifactVersion: <commit hash>
nextAction: one sentence
```
