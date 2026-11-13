---
artifact_type: "methodology_guide"
stage: "5"
stage_name: "Pillars & Architecture"
pmbok_process: "Pillars Exercise (post-Charter decomposition)"
version: "1.6"
date: "2026-11-12"
owner: "Menno Drescher"
governance_policy: "approve-project-pillars (FULL authority); approve-adr (FULL authority)"
---

# Stage 5: Pillars & Architecture — Methodology Guide

> **Purpose:** Decompose the approved Charter into a fixed set of broad, durable topic pillars, each wide enough to provide full coverage of its concern across the entire project's life — not a one-shot decision point. A pillar accumulates its grounding over time through however many ADRs its concern actually needs; most end up with several, some with many (`Project-Pillars.md`'s current table assigns about twenty ADRs to "Earned, auditable autonomy" alone).

> **Alignment:** PMBOK 8 Planning — the Pillars Exercise, a post-Charter decomposition step this repository's governance chain adds ahead of 5.2/5.3 Requirement work.

> **Authority:** FULL authority via `approve-project-pillars` (3 actions: `approve_project_pillars`, `reject_project_pillars`, `request_revision_before_decision`) for the pillar document itself, and `approve-adr` (also FULL, 3 actions) for each grounding ADR.

> **Authority in this repository:** the Sponsor decides both gates. `approve-project-pillars` checks that every pillar is grounded in the Spark, Ideation, Business Case, and Benefits sources, and that the primary-ADR assignment table is complete — it does not itself judge each ADR's architectural soundness; that is `approve-adr`'s job, run per ADR.

---

## 1. Overview

### 1.1 Position in the Chain

```
Stage 4 (Objective) — the approved Charter
    ↓
Stage 5 (Pillars & Architecture) — this stage
    ↓
Stage 6 (Requirement) — BRD/FDD/User Stories trace to the ADRs this stage grounds
```

### 1.2 Inputs

| Input | Source | Mandatory |
|---|---|---|
| Project Charter | `docs/project-docs/Project-Charter.md` | Yes |
| Ideation Document, Business Case, Benefits Management Plan | `docs/project-docs/` | Yes |
| Current codebase — the upstream fork boundary and all code not decided through an ADR | `src/agent_learning/` (including the legacy `pmbok/` orchestration engine still pending its ADR-034 decommission), `scripts/`, `.claude/skills/`, `_infra/`, `packaging/`, `examples/`, `animiations/` | Yes, for the coverage check (§2 Step 5) |

### 1.3 Outputs

| Output | Destination | Governed |
|---|---|---|
| Project Pillars | `docs/project-docs/Project-Pillars.md` | Yes (via `approve-project-pillars`) |
| High-level ADRs, one or more per pillar | `docs/adr/ADR-NNN-*.md` | Yes (via `approve-adr`, per ADR) |

### 1.4 Success Criteria

Stage 5 is complete when:
- [ ] Every pillar in `Project-Pillars.md` traces to the Spark, Ideation, Business Case, or Benefits sources — none is invented
- [ ] `Project-Pillars.md`'s "Primary assignment" table names at least one ADR per pillar — commonly many, since a pillar's criterion is meant to be satisfied repeatedly over the project's life, not once — with no pillar left unassigned
- [ ] Each named ADR has itself been approved via `approve-adr`
- [ ] `approve-project-pillars` has run and the decision is recorded

---

## 2. Process

### Step 1: Decompose the Charter into pillars

`Project-Pillars.md` holds a fixed small set of named pillars (the current baseline has nine, for example "Frozen-model, in-process learning" and "Earned, auditable autonomy"), each with its own `### ` heading, plus a "Primary assignment" table and a "Not a pillar" section naming things deliberately excluded. A pillar is a broad, durable topic meant to cover its concern for the whole project, not a single decision: it earns its place only when a real Charter-level concern is broad enough to need its own standing criterion — each pillar states one in its "An ADR addresses this pillar when..." line — that many separate ADRs can each independently satisfy over the project's life. A pillar is never sized to exactly one ADR's content, and a pillar that has accumulated many ADRs is working as intended, not overgrown.

### Step 2: Assign each ADR's primary pillar — expect many ADRs per pillar, not one

Draft or point to the ADR(s) that ground each pillar architecturally, and for every new ADR, name the single pillar it primarily belongs to in the "Primary assignment" table. This is a per-ADR assignment, not a per-pillar slot: a pillar is satisfied by its standing "An ADR addresses this pillar when" criterion being met, and that criterion is designed to be met again and again as the project grows — `Project-Pillars.md`'s own table already assigns roughly twenty ADRs to "Earned, auditable autonomy" alone, and several more each to "Frozen-model, in-process learning" and "Critique becomes evidence." The pillar document's own approval checks 100% assignment coverage — no pillar without at least one ADR, no ADR claiming a pillar it does not actually ground — not an exact count per pillar.

### Step 3: Submit each ADR for `approve-adr`, then the pillar document for `approve-project-pillars`

Run each ADR's recommendation and decision first (an ADR must exist and be approved before it can be cited as a pillar's grounding). Then submit `Project-Pillars.md` itself. Both follow the same pattern: `task-policy-decide`, Sponsor's words, `task-policy-adjudicate`, `task-episode-register`.

### Step 4: Amend, never silently re-author

A later pillar addition or ADR reassignment is an amendment to an already-approved document: record it in `Project-Pillars.md`'s own "Amendment log" section with its date and rationale, same discipline as any other approved document (ADR-007 route via `scripts/stage16_amend.py` for the ADRs themselves).

### Step 5: Check codebase coverage

Walk the actual repository, not just the ADR list, and classify every top-level area as one of: (a) decided through an approved ADR, and therefore already carrying a pillar via the Primary assignment table; (b) the upstream fork's own code, kept a pristine mirror by charter and deliberately outside pillar scope; or (c) process/tooling code that was never meant to go through Stage 6 at all — this project's own Stage 16 triage explicitly routes a tooling-only change around the ADR/pillar process ("Tooling (automation only) → No governance change required, direct fix," Stage 16 Methodology §2, Step 2d). Category (c) is not a defect by itself; it is the methodology working as designed. It becomes a real finding only when a piece of (c) has quietly grown real decision weight — a standard, an invariant, a policy — that nothing names a pillar for.

### Step 6: Evaluate an incoming fork sync or a serious dependency bump (proposed 2026-11-12, methodology-level — not yet a binding ADR invariant)

Category (b)'s "pristine mirror" status is not permanent immunity: the mirror itself changes every time `scripts/refresh_upstream_manifest.py` moves the pin to a new `upstream/main` commit, and `pyproject.toml`'s own dependencies change over time. Two kinds of incoming change get a pillar check before anything else happens to them:

1. **An upstream fork sync** that changes the public interface or behavior of a module this project's own code, `src/agent_learning_ext/`, or the fork rule's `known_edited` debt list depends on — not a purely internal Microsoft refactor with no observable behavior change.
2. **A dependency version bump** that changes a public API this codebase calls, drops a Python version this project targets, crosses a semver major boundary, or pulls in anything ADR-034 Invariant 1 would reject for a brand-new dependency (a relational ORM, a web framework, a CLI framework, a retry library, OCR tooling). A patch-level bump with no such effect does not meet this bar.

Either kind that meets the bar is evaluated exactly like a new design concern, not patched in place:

1. **Pillar check (this stage).** Does an existing pillar in `Project-Pillars.md` already cover it (same walk as §4's audit)? If yes, the ADR that follows is a daughter ADR or an amendment under that pillar's existing Primary assignment — no new pillar. If no, `Project-Pillars.md` itself needs an amendment (Step 4) — a widened pillar statement, or a new one — before drafting the ADR, following `approve-project-pillars` same as any other pillar change.
2. **ADR → BRD → FDD → User Stories (Stage 6).** The ADR records the actual decision (why this fork change or dependency bump is accepted, and what, if anything, has to change on our side to absorb it); BRD/FDD/Stories follow normally.
3. **Scheduled as a Task (Stage 7, ADR-026 §4.2.1).** The resulting epic's stories get a Milestone and Task entry in the Schedule Management Plan, exactly as any other epic's stories do — the real `epic.story` WBS package id, not a special case.
4. **Governed by a contract test.** Each story's acceptance criteria becomes a contract test (ADR-012 Definition of Done, LL-012) — this is what actually governs the resulting code, whether it arrived through the fork sync or through adapting to the new dependency version, going forward.

A bump or sync that does **not** meet the bar above stays a Stage 16 "Dependency Diff" at Project-Manager authority (Stage 16 Methodology §3, Diff Type Taxonomy #4) — it does not need a pillar, a new ADR, or a Schedule Task.

**Status:** this step is drafted as methodology guidance only. It is not yet a binding Invariant the way ADR-034 Invariant 1 is for a brand-new dependency; making it one would need its own ADR-034 amendment (or a new ADR), approved the normal way, not asserted here.

### Step 7: Phase-close retrospective (triggered by Stage 18, not a one-off)

At every phase's close, after Stage 16 (Governance Change) and Stage 17 (Adaptation Plan) have run and before Stage 18 (Intent Refinement) seeds the next phase, loop back through this stage once:

1. Walk every governance-change item (`GC-NNN` / `GC-P<phase>-NN`) Stage 16 produced that phase. For each: does it imply a genuinely new architectural concern — one no existing pillar's "An ADR addresses this pillar when" criterion covers — or is it operationalizing a decision an existing ADR/pillar already covers (the common case: a tooling fix, a text backfill, a documentation correction)? Only the former needs a new or widened pillar and a fresh ADR; Stage 16's own triage already keeps most items out of this category (§2d), so most phases should find nothing here.
2. Walk what the phase's Intent Refinement Proposal (Stage 18) carries forward into the next phase — a carried hypothesis, a deferred governance item. The same question: does any of it, now that it is being carried rather than closed, imply a pillar nothing names?
3. Record the result, even when it is "nothing found" — a retrospective that is never written down cannot be told apart from one that was never run. `Project-Pillars.md`'s own Amendment log is the record; an empty retrospective still gets a dated log line saying so.
4. If something is found, it amends `Project-Pillars.md` (`approve-project-pillars`) before the next phase's Stage 6 work begins — the same route Step 4 already names, just triggered by the retrospective instead of a fresh pillars-authoring exercise.

**Status:** proposed 2026-11-12 (methodology-level, same caveat as Step 6). Neither Phase 1's close (2026-11-06) nor Phase 2's close (2026-11-11) ever ran this check — `Project-Pillars.md`'s Amendment log has exactly one entry, its original 2026-10-30 approval, despite two full phase closes since. Run retroactively below (§5) for both.

---

## 3. Current Instance (as of 2026-11-12)

`Project-Pillars.md` was approved for baseline `PMP-BL-v1.0.0` (Phase 1) — the policy's own action description names that baseline explicitly. It carries an "Amendment log" section recording later pillar changes rather than a silent rewrite. Phase 3's Pillars work, if any new pillar is needed, has not yet started; Project-Status-Register.md's Phase 3 plan starts at the Charter and the Requirement artifacts, not a pillar rewrite.

---

## 4. Codebase Coverage Audit (2026-11-12)

A walk of the repository against `Project-Pillars.md`'s nine pillars and its Primary-assignment table (ADR-001 through ADR-038, all 38 assigned, no gap inside that table itself) finds:

**Fully covered.** Every approved ADR has a primary pillar, and most of `src/agent_learning/`'s own subpackages (`policy/`, `learners/`, `rewards/`, `scorers/`, `storage/`, `training/`, `classifiers/`, `tailoring.py`, `autonomy.py`, `comparison.py`, `meta_prior.py`, `warm_start.py`, `methodology_catalog.py`, `review_triage.py`) implement a specific ADR's decision and so inherit that ADR's pillar. Most of `.claude/skills/` (`thompson`, `ucb`, `pairwise-preference`, `contextual-learning`, `contextual-cli`, `critique-evidence`, `warm-start`, `routing`, `autonomy`, `comparison`, `storage`, `tailoring`, `weight-compiler`, `learning-methodology-selection`, `meta-prior`) is the same code, one layer up.

**Deliberately outside pillar scope.** Pillars are sourced from Spark, Ideation, Business Case, and the Benefits plan (`Project-Pillars.md` header) — product and research concerns. They do not, and should not, cover: build/release infrastructure (`_infra/`, `packaging/`), demo and illustration code (`examples/`, `animiations/`), or the parts of `src/agent_learning/` that are a pristine upstream mirror by charter (Scope-Management-Plan.md §1.3, "Upstream files remain a pristine mirror of `microsoft/agent-learning`"). This is correct, not a gap.

**Covered only through routing around the pillar process — by design, not by accident.** A real and growing share of the codebase was never meant to go through Stage 5/6 at all: `scripts/` (`stage16_amend.py`, `governance_baseline.py`, `phase_rollup.py`, `pr_gate.py`, `pmbok_write_guard.py`, `execute_stage_18.py`, `update_stage_18_docs.py`, `update_story_status.py`, `spec_gate.py`, `shadow_effort.py`, `estimate_learning_cost.py`), the process-only `.claude/skills/` (`pmbok-planning`, `plan-lint`, `plan-approval-gate`, `phase-rollup`, `governance`, `stage-18`, `intent-refinement`), and the Methodology guides this folder holds — all trace to a Lesson Learned or an `IMP` entry, not an ADR. Stage 16's own triage table calls a tooling-only change "automation only... direct fix, traced," explicitly routing it around Stage 5/6 (Stage 16 Methodology §2, Step 2d). None of these carry a pillar, and under the current rule none are required to.

**An open finding, with a resolution already tracked — not one this audit needs to invent.** The legacy `pmbok/` directory (`agents/`, `api/`, `engines/`, `orchestrator/`, `playbooks/`, `processors/`, `registry/`, `schemas/`, `storage/`) is assigned to ADR-034, which decided to *decommission* it (pillar: "Frozen-model, in-process learning," by inheritance) through a named four-phase migration (ADR-034 §6.1, Epic 34). Checked 2026-11-12: `scripts/orchestrate_pmbok.py` still imports the legacy package directly (`pmbok.models.enums`, `pmbok.storage.state_store`, `pmbok.orchestrator.orchestrator`, …), so ADR-034 §6.2 completion criterion 1 ("zero files import from the legacy top-level `pmbok` package") is not yet met — but Epic 34's own tracking already says so honestly: Stories 34.1–34.3 are Completed, and **Story 34.4** ("One CLI dispatches draft, approve, formalize, and adapt") and **Story 34.5** ("The legacy tree is gone and the suite collects") are correctly Draft/blocked, not misreported as done. The resolution is: implement Stories 34.4 and 34.5 per ADR-034 §6.1 Phase 2 and Phase 4 — a separate, already-scoped engineering task, not a pillar fix and not something to attempt inside this audit.

**Resolved.** `src/agent_learning_ext/` (confirmed on disk: `critique_evidence.py`, `routing.py`, `learners/pairwise.py`, `weight_compiler.py`, `training/`, etc., plus `tests/test_agent_learning_ext.py`) *does* implement Phase 2's custom-extension isolation exactly as the Scope Management Plan intends — the plan just named it wrong. `Scope-Management-Plan.md` and `Schedule-Management-Plan.md` said `agent-training-ext/`, a path that never existed; both have been corrected (2026-11-12, pending `approve-subsidiary-plan` re-approval) to the real path, and two stale filenames (`dpo_preference.py`, `ensemble_router.py`) were corrected to the real ones (`learners/pairwise.py`, `routing.py`). This was a naming error, not an architectural gap.

**Conclusion:** the pillars cover 100% of the ADR-governed decision layer (38/38 ADRs assigned) and correctly exclude pure infrastructure and the upstream mirror. They do not cover, and are not meant to cover, the growing body of tooling/process code that Stage 16 routes around Stage 5/6 by design. The Scope/Schedule Plan path-naming error is now corrected. The one remaining item, the legacy `pmbok/` engine, already has an owned, sequenced resolution (Epic 34 Stories 34.4–34.5); it does not need a new plan from this audit.

---

## 5. Phase-Close Retrospective (run 2026-11-12, retroactively for Phase 1 and Phase 2)

**Phase 1 (closed 2026-11-06).** Governance changes: GC-001 (Stage 18 tooling migration, LL-043) operationalizes the already-approved ADR-034 decommissioning mandate — no new ADR was needed, and a Baseline Revision Package (`BRP-20261106-001`) correctly sufficed. GC-002 (evidence management sync, LL-046), GC-003 (external evidence dependency, LL-044), and GC-004 (single source of truth, LL-045) are all process/tooling fixes under Stage 16's own "direct fix, traced" category, none architectural. **Finding: nothing missed.**

**Phase 2 (closed 2026-11-11).** Governance changes GC-P2-01 through GC-P2-07 (`Stage-16-Governance-Change-Phase2.md`): skill-text backfills, register corrections, a change-request-governed tooling set, a Tier 2 text backfill, and three items deferred to Phase 3. **Finding: nothing missed at the pillar/ADR level** — none imply a new architectural concern. **But GC-P2-05 is a live, undone action this retrospective surfaces concretely:** "replace `agent-training-ext/` with `src/agent_learning_ext/` in the Charter, Business Case and Benefits Management Plan" — the exact same correction this guide's own §4 audit already made to the Scope and Schedule Management Plans — still outstanding on three more Sponsor-approved documents, deferred to Phase 3 "once the documents are made available" (Sponsor, 2026-11-11). GC-P2-05's own text requires each document's edit to be individually accepted by the Sponsor, so this is reported here, not applied.

**Phase 3 hypothesis carry-forward (`IRP-20261111-001`, 19 carried hypotheses plus the newly registered `HYP-AL-028`).** Spot-checked, not walked exhaustively line by line: `HYP-AL-028` (DPO sample efficiency, repointing `HYP-AL-018`) inherits ADR-018's existing "Critique becomes evidence" pillar coverage — no new pillar implied. No carried hypothesis was found claiming a concern outside the nine existing pillars' stated scope.

**Conclusion:** running this retrospective for the first time, two phases late, found no missed ADR and no pillar gap — but it did surface a concrete, already-decided, still-undone action (GC-P2-05) that this methodology guide's own earlier audit (§4) had independently reached by a different route. That convergence is itself evidence the retrospective is worth running going forward, not just this once.

---

## 6. Validation

```bash
grep -n "^### \|^## Primary assignment\|^## Not a pillar\|^## Amendment log" docs/project-docs/Project-Pillars.md
```
No dedicated schema-validation script exists for the pillar document; review against `docs/policy-shapes/approve-project-pillars.actions.json`.

---

## 7. Common Pitfalls

| Pitfall | Mitigation |
|---|---|
| A pillar with no ADR assigned | `approve-project-pillars` checks for a complete primary-assignment table; fix the gap before submitting |
| An invented pillar not traceable to Spark/Ideation/Business Case/Benefits | Every pillar's grounding is checked against those four sources |
| Rewriting the pillar document instead of amending it | Use the "Amendment log" section; never silently restate the pillar set |

---

## 8. References

- [Intent-to-Outcome Chain Coverage](../../intent-to-outcome-chain-coverage.md) — §2 row 5, §4 `approve-project-pillars`
- [Project-Pillars.md](../Project-Pillars.md)
- [Stage 4: Objective Methodology](./Stage-4-Objective-Methodology.md) — renamed 2026-11-12 (was Stage 2)
- [Stage 6: Requirement Methodology](./Stage-6-Requirement-Methodology.md)

---

## Change Log

| Date | Version | Change |
|---|---|---|
| 2026-11-12 | 1.0 | Initial version, grounded in the real `docs/project-docs/Project-Pillars.md` structure (nine pillars, Primary assignment, Not a pillar, Amendment log) and `docs/policy-shapes/approve-project-pillars.actions.json`. |
| 2026-11-12 | 1.1 | Added the current codebase (fork boundary and code not decided through an ADR) as an input (§1.2), a new Step 5 codebase-coverage check (§2), and §4 Codebase Coverage Audit — a real walk of the repository finding 38/38 ADRs pillar-assigned, infrastructure/upstream-mirror code correctly out of scope, a large and growing body of tooling code deliberately routed around Stage 5/6 by Stage 16's own triage rule, the legacy `pmbok/` engine as the one real open (not-yet-covered) item pending its ADR-034 decommission, and a separately flagged discrepancy: `agent-training-ext/` does not exist on disk despite the Scope Management Plan naming it as where Phase 2 custom code lives. |
| 2026-11-12 | 1.2 | Resolved two of §4's findings: corrected `Scope-Management-Plan.md` and `Schedule-Management-Plan.md`'s `agent-training-ext/` path (which never existed) to the real `src/agent_learning_ext/` package, plus two stale filenames, pending `approve-subsidiary-plan` re-approval; and confirmed the legacy `pmbok/` item already has an owned resolution path (ADR-034 Epic 34, Stories 34.4–34.5, correctly tracked as not-yet-done), so no new plan was invented for it. |
| 2026-11-12 | 1.3 | Added Step 6: an incoming upstream fork-sync change or a dependency bump with real consequences (public-API change, major version boundary, or anything ADR-034 Invariant 1 would reject as new) gets a pillar check before anything else, then flows ADR → BRD → FDD → User Stories → a Schedule Task (ADR-026 §4.2.1) → a contract test. Explicitly marked as methodology-level guidance only, not yet a binding ADR invariant — that would need its own ADR-034 amendment or a new ADR. |
| 2026-11-12 | 1.4 | Added Step 7: a phase-close retrospective, triggered by Stage 18, that walks that phase's Stage 16 governance changes and Stage 18 carry-forwards for any pillar/ADR gap. Ran it retroactively (new §5) for Phase 1 and Phase 2: no missed ADR or pillar gap in either phase, but it surfaced GC-P2-05 (the same `agent-training-ext/` → `src/agent_learning_ext/` correction already made to the Scope/Schedule plans) as still outstanding on the Charter, Business Case, and Benefits Management Plan. |
| 2026-11-12 | 1.5 | Corrected a one-ADR-per-pillar implication in the Purpose line, Step 1, Step 2 (retitled from "Assign a primary ADR per pillar"), and §1.4: a pillar is a broad, durable topic whose standing "An ADR addresses this pillar when" criterion is meant to be satisfied repeatedly over the project's life, not a one-shot slot. `Project-Pillars.md`'s own table already assigns roughly twenty ADRs to "Earned, auditable autonomy" alone — a pillar with many ADRs is working as intended, not overgrown. |
| 2026-11-12 | 1.6 | Updated the §1.1 and §8 references to the Objective stage from "Stage 2" to "Stage 4" following the Sponsor's 2026-11-12 renumbering of the Initiating group. Stage 5 itself is unchanged. |
