---
artifact_type: "methodology_guide"
stage: "8"
stage_name: "Implementation Readiness"
pmbok_process: "5.4 WBS & Execution Authorization Gate"
version: "1.0"
date: "2026-11-12"
owner: "Menno Drescher"
governance_policy: "validate-intent-foundation (FULL authority)"
---

# Stage 8: Implementation Readiness — Methodology Guide

> **Purpose:** Gate the boundary between Planning and Executing: certify that a named ADR/BRD/FDD/Story chain is grounded enough — real traceability, testable acceptance criteria, no unresolved prerequisite — before `implement-story` opens a worktree for it.

> **Alignment:** PMBOK 8 Process 5.4, a Planning → Executing execution-authorization gate this chain adds ahead of 4.3 Direct & Manage Project Work.

> **Authority:** FULL authority via `validate-intent-foundation` (3 actions: `accept_foundation_proceed`, `reject_needs_rework`, `flag_for_human_review`).

> **Authority in this repository:** this gate does not judge architectural soundness (that already happened at Stage 6) — it judges whether the chain is *actually ready to build against*: can the acceptance criteria really be contract-tested, does the traceability actually resolve, is there an unresolved blocker. `flag_for_human_review` exists for genuine ambiguity about readiness itself.

---

## 1. Overview

### 1.1 Position in the Chain

```
Stage 7 (Project/PMP) — the formalized baseline
    ↓
Stage 8 (Implementation Readiness) — this stage
    ↓
Stage 9 (Deliverable) — implement-story opens the worktree only after this gate accepts
```

### 1.2 Inputs

| Input | Source | Mandatory |
|---|---|---|
| The story's own ADR/BRD/FDD/epic chain, approved | `docs/adr/`, `docs/project-docs/Business-Requirements/`, `docs/project-docs/Functional-Design/`, `docs/user-stories/` | Yes |
| The formalized PMP baseline | `docs/project-docs/Project-Management-Plan.md` | Yes |
| The story's acceptance criteria | The epic's user-stories file | Yes |

### 1.3 Outputs

| Output | Destination | Governed |
|---|---|---|
| Implementation Authorization Notice | `docs/project-docs/Status-Reports/Stage-8-Implementation-Authorization-Notice.md` (or phase-specific equivalent) | Yes (via `validate-intent-foundation`) |
| Authorization to open an `implement-story` worktree for the named story | n/a (a go/no-go decision, not a new file per story) | Yes |

### 1.4 Success Criteria

Stage 8 is complete, per story, when:
- [ ] The chain's traceability actually resolves (the cited ADR/BRD/FDD/epic exist and are approved)
- [ ] The story's acceptance criteria can really be contract-tested, not just plausible-sounding
- [ ] No named prerequisite blocks it
- [ ] `validate-intent-foundation` has run and accepted, or any rework it required has been done and it was resubmitted

---

## 2. Process

### Step 1: Name the chain

For the story about to enter `implement-story`, name its ADR, BRD, FDD, and epic/story id explicitly. A chain with a broken or missing link cannot be validated.

### Step 2: Run `validate-intent-foundation`

- `accept_foundation_proceed` — real traceability, testable acceptance criteria, no unresolved prerequisite: the story enters the pipeline (worktree → contract RED → `SKILL.md` → implement GREEN → validate → log → PR).
- `reject_needs_rework` — a real, fixable gap exists (untestable acceptance criteria, broken traceability). Name the gap; fix it at the source document, not by working around it in the worktree.
- `flag_for_human_review` — whether the grounding is actually sufficient is itself ambiguous; the Sponsor decides directly.

### Step 3: Record and hand off

Record the decision (and, for an `accept`, the authorization) in the Stage 8 status report and in Project-Status-Register.md. Only then does Stage 9 begin for that story.

---

## 3. Current Instance (as of 2026-11-12)

Phase 1's gate produced `docs/project-docs/Status-Reports/Stage-8-Implementation-Authorization-Notice.md`. Phase 2 and Phase 3 run the same gate per story as each enters `implement-story`; there is no single once-per-phase Stage 8 artifact beyond that first notice — later phases' authorizations are tracked per story in `implementation-log.md` and the epic files' own Status lines, not as a separate Stage 8 document each time.

---

## 4. Validation

```bash
uv run pytest --ignore=tests/test_spark.py --ignore=tests/pmbok -q --tb=no
```
No separate readiness-validation script exists beyond `validate-intent-foundation` itself and the whole test suite.

---

## 5. Common Pitfalls

| Pitfall | Mitigation |
|---|---|
| Treating Stage 8 as re-judging architectural soundness | That already happened at Stage 6; Stage 8 judges build-readiness only |
| Working around an untestable acceptance criterion inside the worktree | `reject_needs_rework` and fix the story file itself |
| Opening a worktree before the gate accepts | No story enters `implement-story` without this gate's acceptance |

---

## 6. References

- [Intent-to-Outcome Chain Coverage](../../intent-to-outcome-chain-coverage.md) — §2 row 8, §4 `validate-intent-foundation`
- [Stage-8-Implementation-Authorization-Notice.md](../Status-Reports/Stage-8-Implementation-Authorization-Notice.md)
- [Stage 7: Project (PMP & Baselines) Methodology](./Stage-7-Project-PMP-and-Baselines-Methodology.md)
- [Stage 9: Deliverable Methodology](./Stage-9-Deliverable-Methodology.md)
- `.claude/skills/implement-story/SKILL.md`

---

## Change Log

| Date | Version | Change |
|---|---|---|
| 2026-11-12 | 1.0 | Initial version, grounded in `docs/policy-shapes/validate-intent-foundation.actions.json` and the real Stage 8 notice in `docs/project-docs/Status-Reports/`. |
