---
artifact_type: "methodology_guide"
stage: "9"
stage_name: "Deliverable"
pmbok_process: "4.3 Direct & Manage Project Work"
version: "1.0"
date: "2026-11-12"
owner: "Menno Drescher"
governance_policy: "none — implement-story and heal-contract-failure skills (direct execution & review, no formal gate)"
---

# Stage 9: Deliverable — Methodology Guide

> **Purpose:** Build the code deliverable against an already-authorized story (Stage 8), contract-first, and recover cleanly when a contract test exposes a real defect — without any formal governance gate sitting inside the build loop itself.

> **Alignment:** PMBOK 8 Process 4.3 Direct & Manage Project Work.

> **Authority:** Direct execution and review. There is no `approve-*` TaskPolicy at this stage — `docs/intent-to-outcome-chain-coverage.md` §2 row 9 names the lifecycle role as "Direct Execution & Review," carried out by the `implement-story` and `heal-contract-failure` skills, not by a decision policy. Governance re-enters at Stage 11 (Audit Record) and at the PR merge gate (`scripts/pr_gate.py`), not inside this stage.

---

## 1. Overview

### 1.1 Position in the Chain

```
Stage 8 (Implementation Readiness) — accepted the story's foundation
    ↓
Stage 9 (Deliverable) — this stage — the implement-story loop
    ↓
Stage 10 (Verification Evidence) — the contract suite that proves the deliverable
```

### 1.2 Inputs

| Input | Source | Mandatory |
|---|---|---|
| Stage 8's acceptance for this story | `validate-intent-foundation`, `accept_foundation_proceed` | Yes |
| The story's acceptance criteria | The epic's user-stories file | Yes |
| The relevant component skill (if one exists for the module being touched) | `.claude/skills/*/SKILL.md` | If applicable |

### 1.3 Outputs

| Output | Destination | Governed |
|---|---|---|
| Source code and tests | The story's worktree, merged via PR | No (version-controlled; governed indirectly via Stage 6's acceptance criteria and the PR gate) |
| `implementation-log.md` entry | repository root `implementation-log.md` | No (but required by LL-045, single source of truth for story status) |

### 1.4 Success Criteria

Stage 9 is complete, per story, when:
- [ ] The contract test(s) named in the story's acceptance criteria were RED before implementation and are GREEN after
- [ ] The relevant `SKILL.md` was updated if the story changed how a component works
- [ ] `implementation-log.md` records the story's status (the single canonical source — LL-045; nothing else derives status independently)
- [ ] `scripts/pr_gate.py` has passed before merge

---

## 2. Process

### Step 1: Open the worktree

Follow the `implement-story` skill's own steps (0 through 9; Step 9 runs only for the epic's last story). This methodology does not restate that skill's steps — see `.claude/skills/implement-story/SKILL.md` for the authoritative sequence.

### Step 2: Contract-first build

Write the contract test RED, implement GREEN, run the whole suite, update the component's `SKILL.md` if the story changed its behavior.

### Step 3: Heal a contract failure, if one surfaces

If a contract test breaks or a PR review exposes a contract defect, use the bounded, intent-first diagnosis-and-repair loop in the `heal-contract-failure` skill rather than patching around the symptom.

### Step 4: Log and hand off

Record the story's completion in `implementation-log.md` (the single source of truth for story status — LL-045), not only in the epic file's own Status line; the epic file's status is derived from the log, never the reverse.

---

## 3. Current Instance (as of 2026-11-12)

Phase 2's deliverables closed out Milestones M6–M8 and Epics 14, 16, 17, 18, 21, 22, and 38 (Project-Status-Register.md §1). Phase 3 has not yet entered Stage 9 for any story — it is still at Stage 1-7 Planning per the register.

---

## 4. Validation

```bash
uv run pytest                 # the whole suite, no --ignore
python scripts/pr_gate.py     # before merge, after every required workflow has concluded (LL-060)
```

---

## 5. Common Pitfalls

| Pitfall | Mitigation |
|---|---|
| Treating story status in the epic file as canonical | `implementation-log.md` is the single source of truth (LL-045); the epic file derives from it |
| Patching around a contract failure instead of diagnosing its root cause | Use `heal-contract-failure`'s bounded diagnosis loop |
| Merging before every required workflow has concluded | `scripts/pr_gate.py` checks this (LL-060) |

---

## 6. References

- [Intent-to-Outcome Chain Coverage](../../intent-to-outcome-chain-coverage.md) — §2 row 9
- `.claude/skills/implement-story/SKILL.md`
- `.claude/skills/heal-contract-failure/SKILL.md`
- [Stage 15: Lesson Learned Methodology](./Stage-15-Lesson-Learned-Methodology.md) — LL-045, LL-060
- [Stage 8: Implementation Readiness Methodology](./Stage-8-Implementation-Readiness-Methodology.md)
- [Stage 10: Verification Evidence Methodology](./Stage-10-Verification-Evidence-Methodology.md)

---

## Change Log

| Date | Version | Change |
|---|---|---|
| 2026-11-12 | 1.0 | Initial version, grounded in `docs/intent-to-outcome-chain-coverage.md` §2 row 9 (no formal policy at this stage) and the real `implement-story`/`heal-contract-failure` skills. |
