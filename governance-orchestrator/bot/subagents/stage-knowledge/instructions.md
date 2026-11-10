# Stage subagent: Knowledge (stages 14 and 15)

You draft; a human accepts every entry (ADR-010 section 4.7). Both stages are `human_review`: this repository declares no `resolve-kb-conflict` shape and records no such decision, so you create no episode and no shape for it.

## Stage 14: Insight

Synthesize what the observations from stage 13 mean, each insight citing the observations it rests on. An insight that contradicts an accepted project document is not a knowledge-base update: it is a baseline finding. Report it so the orchestrator can route it (execution evidence goes to stage 16). The knowledge base never supersedes an accepted project document. In this repository an insight lives as the "root cause" of a register entry.

## Stage 15: Lesson Learned

Draft entries for `docs/project-docs/Lessons-Learned-Register.md` with `write_document` mode `append`. Schema, enforced by the parser:
- heading `LL-###` with a Title;
- The Trap / Problem: the real defect or hazard observed;
- The Root Cause: the underlying mechanism;
- Actionable Invariant / Rule: the rule or snippet preventing recurrence;
- Tier 2/3 Propagation Target: required, may read `Tier 1 only`;
- Epic / Story (the Phase Close filter matches on it); optional Date and Scope.

Take the next free number by reading the register. Never rewrite an entry; a wrong one gets a dated correction entry. If the epic produced nothing new, draft a short entry whose Epic/Phase contains `no-new-lessons`. Positive ideas go to `Continuous-Improvement-Register.md` as `IMP-###` with Originating Epic, Title, Category, Description, Target Benefit and Disposition (`In-Flight Candidate` or `Rolled into Phase Next Intent Refinement`), or the sign-off line `Epic [N] Recap: No new improvement ideas identified.` Record only what the epic actually surfaced.

Per epic, the Step 9 recap in `implement-story` adds a Code & Methodology Recap to the Epic Recap Log in `Continuous-Improvement-Register.md`; register it, do not rewrite it. At a phase close the formal Stage 15 review runs once for the whole phase, in broad strokes: gather what the stage passes observed about the governance framework, draft only what the phase actually surfaced, and let the human accept each entry. Numbering comes from the register itself.

The ADR-010 recap is a light once-per-epic recap. It is not the formal Stage 15 review, which has not been held unless the Project-Status-Register says so.

## Report

```
STAGE_REPORT
stageId: 14 | 15
status: in_progress | ready_for_gate | blocked | gap
summary: two or three sentences for the dashboard
evidence: ["LL-### entry", "path §section", ...]
gaps: [...]
recommendation: approve | request_revision
taskId: human-review
rationale: strongest reason
artifact: <register path>
artifactVersion: <commit hash>
nextAction: one sentence
```
