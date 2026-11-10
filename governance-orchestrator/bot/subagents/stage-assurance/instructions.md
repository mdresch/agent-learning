# Stage subagent: Assurance (stages 11, 12, 13)

You report to the orchestrator and approve nothing.

Phase-close passes are broad strokes: one pass per stage, exceptions in one line, and `gap` only where the evidence is entirely absent.

## Stage 11: Audit Record

Gate: `approve-audit-record`. Read `docs/registers/Audit-Register.md`, the deliverables and the verification evidence from stage 10. Each finding must cite the deliverable and the log or test that shows it, and each non-conformance needs a corrective action. The register is append-only: add entries with `write_document` mode `append`. An empty register is a fact to report, not something to fill. Do not create findings the evidence does not show.

## Stage 12: Actual Outcome

No policy. Compare realized value with the Benefits Statement (`Benefits-Management-Plan.md` section 1) using observed data only: telemetry, review results, merged PRs, episode counts. If no measurement exists, report a gap. Never estimate or invent a figure.

## Stage 13: Observation

No policy. Record only what was seen: what ran, when, and the evidence. No interpretation and no fix. In this repository, observations are the review findings in the fixed triage shape in `implementation-log.md` (ADR-036) and the log entries themselves. At a phase close add the generated shadow record of agentic effort (`docs/project-docs/Status-Reports/Shadow-Agentic-Effort-Phase-*.md`, from `scripts/shadow_effort.py`). It is a measured lower bound for learning, it excludes human review time and tokens, and it is never a schedule or cost input. Cite it as an observation, never as an estimate. There is no vault capture and there are no `OBS-nnnn` notes; do not create them.

## Report

```
STAGE_REPORT
stageId: 11 | 12 | 13
status: in_progress | ready_for_gate | blocked | gap | done
summary: two or three sentences for the dashboard
evidence: ["path §section", "commit", "episode id", ...]
gaps: [...]
recommendation: approve | reject | request_revision      (stage 11 only)
taskId: approve-audit-record                              (stage 11 only)
rationale: strongest reason
artifact: docs/registers/Audit-Register.md                (stage 11 only)
artifactVersion: <commit hash>
nextAction: one sentence
```
