---
artifact_type: "methodology_guide"
stage: "6"
stage_name: "Requirement"
pmbok_process: "5.2 Collect Requirements & 5.3 Define Scope"
version: "1.0"
date: "2026-11-12"
owner: "Menno Drescher"
governance_policy: "approve-adr, approve-brd, approve-fdd, approve-user-stories (each FULL authority)"
---

# Stage 6: Requirement — Methodology Guide

> **Purpose:** Specify a change fully — architecture (ADR), business rules (BRD), interface/implementation design (FDD), and testable acceptance criteria (User Stories) — before any of it is built, and amend that specification correctly if it is already approved and needs to change.

> **Alignment:** PMBOK 8 Process 5.2 Collect Requirements and 5.3 Define Scope.

> **Authority:** FULL authority on each of `approve-adr`, `approve-brd`, `approve-fdd`, `approve-user-stories` (3 actions each: approve, reject, request revision).

> **Authority in this repository:** the Sponsor decides each gate. There are **two different routes** depending on whether the document already exists and is approved: a brand-new ADR/BRD/FDD/Story goes through its policy's normal approval; an edit to an **already-approved** one goes through the Stage 16 amendment tooling (`scripts/stage16_amend.py propose` then `accept`), never a silent hand-edit — see Step 3 below.

---

## 1. Overview

### 1.1 Position in the Chain

```
Stage 5 (Pillars & Architecture) — the grounding ADRs
    ↓
Stage 6 (Requirement) — this stage — BRD, FDD, User Stories, and further ADRs
    ↓
Stage 7 (Project/PMP) — subsidiary plans and the PMP trace to this epic's WBS
```

### 1.2 Inputs

| Input | Source | Mandatory |
|---|---|---|
| Project Charter and Project Pillars | `docs/project-docs/` | Yes |
| The grounding ADR for the epic (if one already exists) | `docs/adr/` | If amending |
| `Scope-WBS-Dictionary.md` (the canonical `epic.story` id list) | `docs/project-docs/management-plans/scope-baseline/foundation/Scope-WBS-Dictionary.md` | Yes, for any story |

### 1.3 Outputs

| Output | Destination | Governed |
|---|---|---|
| Architecture Decision Record | `docs/adr/ADR-NNN-*.md` | Yes (via `approve-adr`) |
| Business Requirements Document | `docs/project-docs/Business-Requirements/BRD-NNN-*.md` | Yes (via `approve-brd`) |
| Functional Design Document | `docs/project-docs/Functional-Design/FDD-NNN-*.md` | Yes (via `approve-fdd`) |
| User Stories | `docs/user-stories/epic-NNN-*.md` | Yes (via `approve-user-stories`) |

### 1.4 Success Criteria

Stage 6 is complete when:
- [ ] The ADR, BRD, and FDD for the epic are each individually approved
- [ ] Every story in the epic file has testable acceptance criteria and a real `epic.story` id matching `Scope-WBS-Dictionary.md`
- [ ] Any edit to an already-approved one of these four documents went through `scripts/stage16_amend.py`, not a hand-edit
- [ ] `tests/test_governance_baseline.py` and the whole suite pass

---

## 2. Process

### Step 1: Draft the chain in order

ADR first (the architectural decision and its alternatives), then BRD (the business rules it implies), then FDD (the interface/implementation detail), then User Stories (testable acceptance criteria, each a real `epic.story` pair). Each is its own approval; do not bundle all four into one submission.

### Step 2: Submit each for its own approval

For a **brand-new** document: run `task-policy-decide` for the matching policy (`approve-adr`, `approve-brd`, `approve-fdd`, or `approve-user-stories`), show the Sponsor the recommendation, and on their explicit instruction run `task-policy-adjudicate` then `task-episode-register`.

### Step 3: For an edit to an already-approved document, amend — never hand-edit

This is the route this project learned the hard way (ADR-026's WBS/Task amendment is a live worked example of it):
1. Make the edit, uncommitted.
2. `uv run python scripts/stage16_amend.py propose <doc>` — this classifies the diff (`new_superseding_adr`, `amendment_log_entry`, `correction_note`, `clarification_section`, `provenance_note`, `pending_supersession_note`, or `supersession_update`) and writes the decision-frame to `docs/policy-shapes/`. It registers nothing by itself.
3. A human reads the classification. If the top-ranked action disagrees with the edit's own framing, or the result is `needs_user_tie_break`, resolve that with the Sponsor before proceeding — do not accept past a disagreement silently.
4. On the Sponsor's explicit instruction, `accept <doc> --by "<name>" --summary "..."`.
5. Commit the document, the manifest, and the `docs/policy-shapes/` files together. Run `tests/test_governance_baseline.py`.

A classifier result naming `new_superseding_adr`, `pending_supersession_note`, or `supersession_update` means the change is more than an amendment — stop and consider a new ADR instead of forcing it through the amendment route.

### Step 4: Hand off to Stage 7

Once the epic's ADR/BRD/FDD/Stories are approved (or correctly amended), Stage 7's subsidiary plans and PMP can cite its WBS.

---

## 3. Validation

```bash
uv run pytest tests/test_governance_baseline.py tests/test_stage16_amend.py -v
grep -n "^epic\." docs/project-docs/management-plans/scope-baseline/foundation/Scope-WBS-Dictionary.md | head -10
```

---

## 4. Common Pitfalls

| Pitfall | Mitigation |
|---|---|
| Hand-editing an approved ADR/BRD/FDD/Story | Always `stage16_amend.py propose` then `accept`; never a silent edit |
| Accepting past a classifier disagreement or tie | Resolve with the Sponsor first; a tie or disagreement is a signal, not noise |
| Inventing a flattened story ordinal instead of the real `epic.story` pair | Use the id verbatim from `Scope-WBS-Dictionary.md` — never renumber |
| Treating a `new_superseding_adr`/`pending_supersession_note`/`supersession_update` result as "just accept it" | These mean the change is bigger than an amendment; consider a new ADR |

---

## 5. References

- [ADR-007: Governance Change Paired Diff Classification and Escalation](../../adr/ADR-007-governance-change-paired-diff-classification-and-escalation.md)
- [Stage 16: Governance Change Methodology](./Stage-16-Governance-Change-Methodology.md) — Step 3's routing table, route 1
- [Scope-WBS-Dictionary.md](../management-plans/scope-baseline/foundation/Scope-WBS-Dictionary.md)
- [Intent-to-Outcome Chain Coverage](../../intent-to-outcome-chain-coverage.md) — §2 row 6, §4

---

## Change Log

| Date | Version | Change |
|---|---|---|
| 2026-11-12 | 1.0 | Initial version, grounded in `scripts/stage16_amend.py`'s real propose/accept mechanics (as exercised this session on ADR-026) and `docs/intent-to-outcome-chain-coverage.md` §2 row 6. |
