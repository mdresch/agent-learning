---
artifact_type: "methodology_guide"
stage: "17"
stage_name: "Adaptation Plan"
pmbok_process: "4.6 Perform Integrated Change Control (Tailoring)"
version: "1.1"
date: "2026-11-10"
owner: "Menno Drescher"
governance_policy: "approve-adaptation-plan (FULL authority)"
---

# Stage 17: Adaptation Plan Methodology

> **Purpose:** This document provides a comprehensive methodology for Stage 17 (Adaptation Plan) of the Intent-to-Outcome chain. Stage 17 operationalizes governance changes from Stage 16 into executable skills, workflows, and tailored project management plan updates.

> **Alignment:** PMBOK 8 Process 4.6 Perform Integrated Change Control (Tailoring)

> **Authority:** FULL authority via `approve-adaptation-plan` policy (3 actions: approve, reject, request revision)

> **Authority in this repository:** the policy's gate computes a recommendation; the decision of record is the Project Sponsor's, given in words and registered with `task-policy-adjudicate` and `task-episode-register`. An agent drafts the plan and runs the steps; it never adjudicates, registers an approval, or edits a generated plan by hand. There is no separate technical-review or project-manager sign-off beyond the Sponsor (the Charter names one decision-maker).

> **One adaptation per phase.** A phase runs Stage 16 and Stage 17 once, at its close (Sponsor, 2026-11-10: "close Phase 2 once instead of multiple times"). Stage 17 therefore carries everything Stage 16 approved plus what it deferred; a standalone package for one change is kept as an input, not run on its own.

---

## 1. Stage 17 Overview

### 1.1 Purpose and Position in the Chain

Stage 17 is the **operationalization gate** that transforms approved governance changes into actionable adaptations. It sits at the boundary between **Monitoring & Controlling** (Stage 16) and **Closing / Strategic Feedback** (Stage 18).

```
Stage 16 (Governance Change)
    \u2193
Stage 17 (Adaptation Plan) \u0014 Operationalize
    \u2193
Stage 18 (Intent Refinement) \u0014 Strategic Feedback
```

**Key Responsibility:** Take validated governance changes and make them operational through skills updates, workflow modifications, and tailored PMP updates.

### 1.2 Inputs

| Input | Source | Mandatory |
|---|---|---|
| Approved Governance Changes | Stage 16 output | Yes |
| Baseline Revision Packages (BRPs) | Stage 16 output | If applicable |
| Subsidiary Plan Amendments (SPAs) | Stage 16 output | If applicable |
| Current Skills | `.claude/skills/` | Yes |
| Current Workflows | `.claude/skills/` | Yes |
| Current PMP | Project-Management-Plan.md | Yes |
| Governance Episodes | `docs/policy-shapes/episodes/` and the governance store (`data/agent-learning/store/`) | Yes |
| Stage 16 assessment | `docs/project-docs/Status-Reports/Stage-16-Governance-Change-*.md`, approved | Yes |
| Change requests and their decisions | `docs/governance/change-requests/` | Yes |
| Earlier change packages kept as inputs | `docs/project-docs/Adaptation-Plans/` | If any |
| Registers | Lessons Learned and Continuous Improvement, for the dispositions Stage 16 set | Yes |

### 1.3 Outputs

| Output | Destination | Governed |
|---|---|---|
| Updated Skills | `.claude/skills/` | No (but version controlled) |
| Updated Workflows | `.claude/skills/` | No (but version controlled) |
| Tailored PMP | Project-Management-Plan.md | Yes (via approve-adaptation-plan) |
| Adaptation Plan Document | `docs/project-docs/Adaptation-Plans/ADP-YYYYMMDD-NNN-<title>.md` (the integrated `docs/project-docs/Adaptation-Plan.md` is produced by the planning tooling after approval) | Yes |
| Updated Governance Episodes | `docs/policy-shapes/episodes/` | Yes |

### 1.4 Success Criteria

Stage 17 is complete when:
- [ ] All Stage 16 governance changes are operationalized
- [ ] All skills and workflows are updated
- [ ] All PMP tailoring is complete
- [ ] Adaptation Plan document is approved via `approve-adaptation-plan`
- [ ] All changes are committed and pushed
- [ ] Project-Status-Register.md is updated

---

## 2. Adaptation Plan Process (8-Step)

### Step 1: Input Validation

**Purpose:** Ensure all required inputs from Stage 16 are available and valid.

**Actions:**
1. Verify Stage 16 assessment is complete and marked COMPLETED
2. Confirm all BRPs and SPAs are prepared and approved
3. Verify current skills and workflows are accessible
4. Confirm current PMP baseline is accessible
5. Verify governance episodes from Stage 16 are recorded

**Checklist:**
- [ ] Stage 16 assessment exists and is marked COMPLETED
- [ ] All BRPs have required approvals (or are in review)
- [ ] All SPAs have required approvals (or are in review)
- [ ] Current skills directory exists and is valid
- [ ] Current PMP is accessible and valid
- [ ] All Stage 16 episodes are recorded

**Validation Commands** (the Stage 16 assessment is marked `APPROVED` in its frontmatter status; Stage 16 writes no per-lesson episode files named `classify-diff-type-LL-*.json`):
```bash
# Stage 16 assessment approved
grep -n "^status:" docs/project-docs/Status-Reports/Stage-16-Governance-Change-*.md

# Change requests exist and record their decisions
ls docs/governance/change-requests/ && grep -n "Decision status\|Project Sponsor |" docs/governance/change-requests/CR-*.md

# Skills and the PMP
ls .claude/skills/ && head -30 docs/project-docs/Project-Management-Plan.md | grep "PMP-BL-v"

# The store the approval will be registered in (LL-040): print it, count its files
echo "${AGENT_LEARNING_LOCAL_STORE_DIR:-./data/agent-learning/store}"
```
Open items that Stage 16 deferred (for example F3 and F4) are carried as deferrals in the plan; they are not silently dropped.

---

### Step 2: Change Inventory

**Purpose:** Create a complete inventory of all governance changes that need to be operationalized.

**Inventory Template:**
```markdown
## Governance Change Inventory

### From Stage 16 Assessment: [REP-GC-...]

| Change ID | Source | Type | Status | Priority | Owner |
|---|---|---|---|---|---|
| GC-001 | LL-043 | Structural | BRP Approved | High | [Name] |
| GC-002 | LL-046 | Process | SPA Approved | High | [Name] |
| GC-003 | LL-044 | Process | Direct | Medium | [Name] |
| GC-004 | LL-045 | Process | Direct | Medium | [Name] |

### Detailed Changes

#### GC-001: [Change Name]
- **Source:** LL-043
- **Type:** Structural/Architectural
- **BRP:** BRP-20261106-001
- **Description:** [Detailed description]
- **Affected Components:** [List]
- **Operationalization Requirements:** [List]
- **Success Criteria:** [List]
```

**Inventory for Current Stage:**
| Change ID | Source | Type | Document | Status | Priority |
|---|---|---|---|---|---|
| GC-001 | LL-043 | Structural | BRP-20261106-001 | Prepared | High |
| GC-002 | LL-046 | Process | SPA-20261106-001 | Prepared | High |
| GC-003 | LL-044 | Process | N/A | Direct | Medium |
| GC-004 | LL-045 | Process | N/A | Direct | Medium |

---

### Step 3: Impact Mapping

**Purpose:** Map each governance change to the specific skills, workflows, and PMP sections that need to be updated.

**Impact Mapping Template:**
```yaml
change_id: GC-001
source: LL-043
change_type: structural
affected_skills:
  - .claude/skills/implement-story/SKILL.md
  - .claude/skills/governance/SKILL.md
affected_workflows:
  - workflows/stage-18.yml
affected_pmp_sections:
  - Scope Management Plan
  - Schedule Management Plan
  - Quality Management Plan
operationalization_steps:
  - Step 1: [description]
  - Step 2: [description]
success_criteria:
  - Criterion 1: [description]
  - Criterion 2: [description]
validation_methods:
  - Test 1: [description]
  - Test 2: [description]
```

**Current Impact Mapping:**

#### GC-001: Stage 18 Tooling Migration (from LL-043)
```yaml
change_id: GC-001
source: LL-043
change_type: structural
affected_skills:
  - .claude/skills/implement-story/SKILL.md
  - .claude/skills/governance/SKILL.md
affected_workflows:
  - .claude/skills/stage-18/SKILL.md (new)
affected_pmp_sections:
  - Project-Management-Plan.md (baseline update)
  - Scope-Management-Plan.md
  - Schedule-Management-Plan.md
  - Quality-Management-Plan.md
operationalization_steps:
  - Update implement-story to reference new tooling location
  - Create new stage-18 skill for intent refinement
  - Update governance skill to handle new module structure
  - Update PMP baseline to PMP-BL-v1.0.1
success_criteria:
  - All Stage 18 functionality works in new location
  - All tests pass
  - CI pipeline includes new tests
validation_methods:
  - Run Stage 18 tooling in new location
  - Verify CI passes with new tests
  - Validate governance episodes are created correctly
```

#### GC-002: Evidence Management Synchronization (from LL-046)
```yaml
change_id: GC-002
source: LL-046
change_type: process
affected_skills:
  - .claude/skills/governance/SKILL.md
affected_workflows:
  - N/A
associated_scripts:
  - scripts/governance/sync_episodes.py
  - scripts/governance/validate_episodes.py
  - scripts/governance/backfill_episodes.py
affected_pmp_sections:
  - Governance-Management-Plan.md
operationalization_steps:
  - Update governance skill to write episodes to repository first
  - Create sync script to copy episodes to external store
  - Create validation script to check for discrepancies
  - Create backfill script for missing episodes
  - Update Governance-Management-Plan.md with new policies
success_criteria:
  - All governance decisions recorded in repository
  - All repository episodes synchronized to external store
  - No discrepancies between sources
  - All upstream gates have episodes
validation_methods:
  - Run validation script
  - Verify all episodes exist in both locations
  - Check for missing episodes
```

#### GC-003: External Evidence Dependency (from LL-044)
```yaml
change_id: GC-003
source: LL-044
change_type: process
affected_skills:
  - .claude/skills/implement-story/SKILL.md
affected_documentation:
  - sidpa-template/testing/data-dependencies.md
operationalization_steps:
  - Add data dependency check to implement-story Step 0
  - Create guidance document for hypothesis validation
  - Update testing template with data dependency section
success_criteria:
  - All hypotheses have documented data dependencies
  - Test environment has mock data for validation
  - No hypotheses blocked by missing data
validation_methods:
  - Check hypothesis tracking for data dependencies
  - Verify mock data exists for all test scenarios
```

#### GC-004: Single Source of Truth for Story Status (from LL-045)
```yaml
change_id: GC-004
source: LL-045
change_type: process
affected_skills:
  - .claude/skills/implement-story/SKILL.md
affected_scripts:
  - scripts/phase_rollup.py
  - scripts/update_story_status.py (new)
affected_documentation:
  - sidpa-template/governance/story-status-management.md
operationalization_steps:
  - Automate story status updates in implementation-log.md
  - Derive epic file status from implementation-log.md
  - Add validation to detect and flag drift
  - Update phase_rollup.py to enforce single source
  - Create automation script for status synchronization
success_criteria:
  - Story status maintained in single canonical location
  - All other representations derived from canonical source
  - No drift between epic files and implementation-log.md
validation_methods:
  - Run phase_rollup.py with --check
  - Verify no status-drift rows
  - Check that all status updates are automated
```

---

### Step 4: Skill and Workflow Updates

**Purpose:** Update the actual skills and workflows to implement the governance changes.

**Update Process:**

#### For Each Skill Update:

1. **Create feature branch**
   ```bash
   git checkout -b feature/adaptation-[change-id]
   ```

2. **Identify specific changes**
   - Review the impact mapping for the change
   - Identify exact lines/sections to modify
   - Document current state

3. **Implement changes**
   - Make minimal, focused changes
   - Follow existing patterns and conventions
   - Add comments explaining changes (if necessary)

4. **Update tests**
   - Update existing tests for modified behavior
   - Add new tests for new functionality
   - Ensure all tests pass

5. **Document changes**
   - Update skill documentation
   - Add change log entry
   - Update cross-references

**Skill Update Template:**
```markdown
## Skill Update: [Skill Name]

**Change ID:** GC-XXX
**Source:** LL-XXX
**Date:** YYYY-MM-DD
**Author:** [Name]

### Changes Made

1. **Section [X]** - [Description of change]
   - **Before:** [old code/text]
   - **After:** [new code/text]
   - **Rationale:** [why this change was made]

2. **Section [Y]** - [Description of change]
   - **Before:** [old code/text]
   - **After:** [new code/text]
   - **Rationale:** [why this change was made]

### Tests Updated

- [ ] test_1.py - Updated to test new behavior
- [ ] test_2.py - Added new test for feature X

### Validation

- [ ] All existing tests pass
- [ ] All new tests pass
- [ ] Manual testing completed
- [ ] Code review completed
```

**Current Skill Updates Required:**

1. **implement-story/SKILL.md**
   - Add data dependency check (GC-003)
   - Automate story status updates (GC-004)

2. **governance/SKILL.md**
   - Update to write episodes to repository first (GC-002)
   - Add evidence sync check (GC-002)

3. **New: stage-18/SKILL.md**
   - Create new skill for intent refinement (GC-001)

---

### Step 5: PMP Tailoring

**Purpose:** Update the Project Management Plan and subsidiary plans to reflect the operationalized changes.

**Generated plans are regenerated, never hand-edited.** The PMP and the nine subsidiary plans come from `scripts/orchestrate_pmbok.py` (`--mode adapt --adaptation-plan <plan>`) and the `pmbok-planning` skill. A standard that must hold in every run goes in the template, then the plans are regenerated. Hand-authored approved documents named by the plan (the Charter, Business Case, Benefits Management Plan, Ideation Document) change through their own approved amendment, accepted by the Sponsor, and are listed in the plan with that route. **Baseline versioning** follows ADR-008 §4.6.1 and ADR-037: an execution adaptation is a minor increment (`PMP-BL-v1.1.0` to `PMP-BL-v1.2.0`); the numbers in the example below are from Phase 1.

**PMP Update Process:**

1. **Update baseline version**
   - From: PMP-BL-v1.0.0
   - To: PMP-BL-v1.0.1 (for BRP-20261106-001)
   - Or: PMP-BL-v1.1.0 (if major changes)

2. **Update affected subsidiary plans**
   - Scope-Management-Plan.md
   - Schedule-Management-Plan.md
   - Quality-Management-Plan.md
   - Governance-Management-Plan.md

3. **Document changes**
   - Add change log entry
   - Update version history
   - Update cross-references

**PMP Tailoring Template:**
```markdown
## PMP Tailoring: [Change ID]

**BRP/SPA:** [Document ID]
**From Version:** PMP-BL-vX.Y.Z
**To Version:** PMP-BL-vA.B.C
**Date:** YYYY-MM-DD
**Author:** [Name]

### Changes to Project-Management-Plan.md

| Section | Change | Rationale |
|---|---|---|
| Baseline Version | Updated from vX.Y.Z to vA.B.C | Reflects approved changes |
| Scope | [Description] | [Rationale] |
| Schedule | [Description] | [Rationale] |

### Changes to Subsidiary Plans

#### Scope-Management-Plan.md
- [Change 1 description]
- [Change 2 description]

#### Schedule-Management-Plan.md
- [Change 1 description]
- [Change 2 description]

### Validation

- [ ] All cross-references updated
- [ ] All version numbers consistent
- [ ] All changes approved
```

**Current PMP Tailoring:**

1. **From BRP-20261106-001:**
   - Update baseline from PMP-BL-v1.0.0 to PMP-BL-v1.0.1
   - Update Scope-Management-Plan.md with new work packages
   - Update Schedule-Management-Plan.md with migration timeline
   - Update Quality-Management-Plan.md with test coverage requirements

2. **From SPA-20261106-001:**
   - Update Governance-Management-Plan.md with new policies
   - Add evidence management procedures
   - Add synchronization requirements

---

### Step 6: Adaptation Plan Document

**Purpose:** Create the formal Adaptation Plan document that consolidates all changes and serves as the input for approval.

**Adaptation Plan Template:**
```markdown
---
artifact_type: "adaptation_plan"
plan_id: "ADP-[PROJECT]-[DATE]"
baseline_from: "PMP-BL-vX.Y.Z"
baseline_to: "PMP-BL-vA.B.C"
version: "1.0"
date: "YYYY-MM-DD"
prepared_by: "[Name]"
status: "[draft|in_review|approved|rejected]"
related_changes:
  - "GC-001"
  - "GC-002"
  - "GC-003"
  - "GC-004"
---

# Adaptation Plan: [Plan ID]

> **Purpose:** [Brief purpose statement]
>
> **Status:** [draft|in_review|approved|rejected]

---

## Executive Summary

| Field | Value |
|---|---|
| **Plan ID** | ADP-[PROJECT]-[DATE] |
| **From Baseline** | PMP-BL-vX.Y.Z |
| **To Baseline** | PMP-BL-vA.B.C |
| **Changes Included** | [Number] |
| **Status** | [Status] |

---

## 1. Change Inventory

[Include the inventory from Step 2]

---

## 2. Impact Mapping

[Include the impact mapping from Step 3]

---

## 3. Skill and Workflow Updates

### [Skill Name]
- **Changes:** [List of changes]
- **Files Modified:** [List]
- **Tests Updated:** [List]
- **Validation:** [Status]

---

## 4. PMP Tailoring

[Include the PMP tailoring from Step 5]

---

## 5. Implementation Plan

### Phase 1: [Phase Name]
- [ ] Task 1
- [ ] Task 2

### Phase 2: [Phase Name]
- [ ] Task 1
- [ ] Task 2

---

## 6. Validation Plan

### Validation Criteria
- [ ] Criterion 1
- [ ] Criterion 2

### Validation Methods
- [ ] Method 1
- [ ] Method 2

---

## 7. Rollback Plan

### Rollback Conditions
- [ ] Condition 1
- [ ] Condition 2

### Rollback Steps
1. [Step 1]
2. [Step 2]

---

## 8. Approval

- [ ] Technical Review: _______________ Date: _______
- [ ] Project Manager Review: _______________ Date: _______
- [ ] Steering Committee Review (if required): _______________ Date: _______
- [ ] Final Approval via approve-adaptation-plan: _______________ Date: _______
```

---

### Step 7: Validation

**Purpose:** Validate that all changes are correctly implemented and working as expected.

**Validation Checklist:**

#### Skill Validation
- [ ] All skill updates are committed
- [ ] All skill tests pass
- [ ] All skill changes are documented
- [ ] All cross-references are valid

#### Workflow Validation
- [ ] All workflow updates are committed
- [ ] All workflow tests pass
- [ ] All workflow changes are documented

#### PMP Validation
- [ ] All PMP updates are committed
- [ ] All version numbers are consistent
- [ ] All cross-references are valid
- [ ] All changes are approved

#### Integration Validation
- [ ] All skills work together correctly
- [ ] All workflows execute properly
- [ ] All PMP changes are reflected in operations

**Validation Commands** (the scripts `validate_pmp.py`, `validate_links.py` and `validate_episodes.py` do not exist in this repository):
```bash
uv run pytest                                  # the whole suite, no --ignore
uv run pytest tests/test_governance_baseline.py tests/test_stage16_amend.py tests/test_lessons_learned.py
# plan consistency: the plan-lint and plan-approval-gate skills, run by the planning tooling
python scripts/orchestrate_pmbok.py --mode adapt --adaptation-plan <plan>   # only after approval
```
Run the suite with `AGENT_LEARNING_LOCAL_STORE_DIR` pointing at a temporary directory until IMP-063 lands: the suite writes fixture episodes into the configured store.

---

### Step 8: Approval and Completion

**Purpose:** Submit the Adaptation Plan for approval and complete Stage 17.

**Approval Process:**

1. **Merge the plan as a draft.** The plan document is committed with `status: draft`. Implementation work it lists is done in separate PRs, each merged through `scripts/pr_gate.py` after every required workflow has concluded (LL-060) and the whole suite has passed.
2. **Decision.** The Sponsor reads the plan. Run `task-policy-decide` for `approve-adaptation-plan`, show the gate's recommendation, and wait. On the Sponsor's explicit words run `task-policy-adjudicate` and `task-episode-register`, after printing the store path and its file count before and after (LL-040).
3. **Record.** Put the decision, its date and the episode id in the plan and in the Project-Status-Register. A gate that was missed is not approved afterwards; record the gap and run the gate going forward.
4. **Finalize.** Regenerate the PMP and plans with the tooling, commit, and mark Stage 17 COMPLETED only when the work the plan authorizes is merged.

**Completion Checklist:**
- [ ] All skill and workflow updates are committed
- [ ] All PMP updates are committed
- [ ] Adaptation Plan document is approved
- [ ] All validation tests pass
- [ ] Project-Status-Register.md is updated
- [ ] All artifacts are pushed to repository

---

## 3. Templates

### 3.1 Adaptation Plan Template

```markdown
---
artifact_type: "adaptation_plan"
plan_id: "ADP-[PROJECT]-[DATE]"
baseline_from: "PMP-BL-vX.Y.Z"
baseline_to: "PMP-BL-vA.B.C"
version: "1.0"
date: "YYYY-MM-DD"
prepared_by: "[Name]"
status: "draft"
related_changes:
  - "GC-001"
  - "GC-002"
  - "GC-003"
  - "GC-004"
governance_policy: "approve-adaptation-plan"
---

# Adaptation Plan: [Plan ID]

> **Purpose:** Operationalize governance changes from Stage 16 into skills, workflows, and tailored PMP updates.
>
> **Authority:** FULL authority via `approve-adaptation-plan` policy
>
> **Status:** [draft|in_review|approved|rejected]

---

## Executive Summary

| Field | Value |
|---|---|
| **Plan ID** | ADP-[PROJECT]-[DATE] |
| **From Baseline** | PMP-BL-vX.Y.Z |
| **To Baseline** | PMP-BL-vA.B.C |
| **Changes Included** | [Number] |
| **Status** | [Status] |

---

## 1. Introduction

### Purpose
[Brief description of the purpose of this adaptation plan]

### Scope
[Description of what is included in this plan]

### Out of Scope
[Description of what is not included in this plan]

---

## 2. Change Inventory

### Governance Changes from Stage 16

| Change ID | Source Lesson | Type | Document | Status |
|---|---|---|---|---|
| GC-001 | LL-043 | Structural | BRP-20261106-001 | Approved |
| GC-002 | LL-046 | Process | SPA-20261106-001 | Approved |
| GC-003 | LL-044 | Process | N/A | Direct |
| GC-004 | LL-045 | Process | N/A | Direct |

### Detailed Change Descriptions

#### GC-001: [Change Name]
- **Source:** LL-043
- **Type:** Structural
- **Document:** BRP-20261106-001
- **Description:** [Detailed description]
- **Status:** Approved

#### GC-002: [Change Name]
- **Source:** LL-046
- **Type:** Process
- **Document:** SPA-20261106-001
- **Description:** [Detailed description]
- **Status:** Approved

---

## 3. Impact Mapping

### GC-001: Stage 18 Tooling Migration

**Affected Components:**
- Skills: implement-story, governance, stage-18 (new)
- Workflows: stage-18 workflow
- PMP: Project-Management-Plan, Scope-Management-Plan, Schedule-Management-Plan, Quality-Management-Plan

**Operationalization Steps:**
1. [Step 1]
2. [Step 2]

**Success Criteria:**
- [ ] All Stage 18 functionality works in new location
- [ ] All tests pass
- [ ] CI pipeline includes new tests

---

## 4. Implementation

### Skill Updates

#### implement-story/SKILL.md
- **Changes:** [List of changes]
- **Files Modified:** implement-story/SKILL.md
- **Tests Updated:** [List]
- **Validation:** [Status]

#### governance/SKILL.md
- **Changes:** [List of changes]
- **Files Modified:** governance/SKILL.md
- **Tests Updated:** [List]
- **Validation:** [Status]

#### stage-18/SKILL.md (New)
- **Changes:** New skill created
- **Files Created:** stage-18/SKILL.md
- **Tests Created:** tests/test_stage_18.py
- **Validation:** [Status]

### Workflow Updates

[List workflow updates]

### PMP Updates

[List PMP updates]

---

## 5. Validation

### Validation Criteria

- [ ] All skills updated and tested
- [ ] All workflows updated and tested
- [ ] All PMP updates committed
- [ ] All cross-references valid
- [ ] All validation tests pass

### Validation Methods

1. **Skill Validation**
   ```bash
   uv run pytest .claude/skills/ -v
   ```

2. **PMP Validation**
   ```bash
   python scripts/validate_pmp.py
   ```

3. **Link Validation**
   ```bash
   python scripts/validate_links.py docs/
   ```

---

## 6. Rollback Plan

### Rollback Conditions

- [ ] Critical bugs in updated skills
- [ ] PMP inconsistencies detected
- [ ] Validation tests fail
- [ ] Approval rejected

### Rollback Steps

1. **Revert all changes**
   ```bash
   git revert <adaptation-commit>
   ```

2. **Restore previous state**
   - Revert skill changes
   - Revert PMP changes
   - Revert workflow changes

3. **Verify rollback**
   - Run all tests
   - Verify PMP consistency
   - Check all cross-references

---

## 7. Approval

### Approval Workflow

1. **Technical Review**
   - [ ] Senior Developer: _______________ Date: _______
   - [ ] QA Engineer: _______________ Date: _______

2. **Project Management Review**
   - [ ] Project Manager: _______________ Date: _______

3. **Governance Approval**
   - [ ] approve-adaptation-plan: _______________ Date: _______
   - [ ] Episode ID: _______________

### Approval Status

- [ ] Draft
- [ ] In Review
- [ ] Approved
- [ ] Rejected

---

## 8. References

### Related Documents

- [Stage 16 Assessment](../Status-Reports/Stage-16-Governance-Change-Assessment.md)
- [Stage 16 Methodology](../Methodology/Stage-16-Governance-Change-Methodology.md)
- [BRP-20261106-001](../../governance/brp/BRP-20261106-001-Stage-18-Tooling-Migration.md)
- [SPA-20261106-001](../../governance/spa/SPA-20261106-001-Evidence-Management-Synchronization.md)
- [Project-Status-Register](../Project-Status-Register.md)

### Governance Episodes

- [classify-diff-type-LL-043-20261106](../../policy-shapes/episodes/classify-diff-type-LL-043-20261106.json)
- [escalate-diff-response-LL-043-20261106](../../policy-shapes/episodes/escalate-diff-response-LL-043-20261106.json)
- [classify-diff-type-LL-046-20261106](../../policy-shapes/episodes/classify-diff-type-LL-046-20261106.json)
- [escalate-diff-response-LL-046-20261106](../../policy-shapes/episodes/escalate-diff-response-LL-046-20261106.json)

---

## 9. Appendix

### Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | YYYY-MM-DD | [Name] | Initial version |
```

### 3.2 Skill Update Template

```markdown
## Skill Update: [Skill Name]

**Change ID:** GC-XXX
**Source:** LL-XXX
**Date:** YYYY-MM-DD
**Author:** [Name]
**Status:** [draft|in_review|approved|rejected]

### Changes

| Section | Type | Description | Before | After |
|---|---|---|---|---|
| Section 1 | modification | [Description] | [Old] | [New] |
| Section 2 | addition | [Description] | N/A | [New] |

### Files Modified

- [ ] .claude/skills/[skill-name]/SKILL.md
- [ ] .claude/skills/[skill-name]/[other-file]

### Tests Updated

- [ ] tests/test_[skill-name].py

### Validation

- [ ] All tests pass
- [ ] Manual testing completed
- [ ] Code review completed

### Approval

- [ ] Technical Review: _______________ Date: _______
- [ ] Project Manager Review: _______________ Date: _______
```

### 3.3 PMP Update Template

```markdown
## PMP Update: [Plan Name]

**Change ID:** GC-XXX
**Source:** LL-XXX
**Date:** YYYY-MM-DD
**Author:** [Name]
**Status:** [draft|in_review|approved|rejected]

### Changes

| Section | Field | Old Value | New Value | Rationale |
|---|---|---|---|---|
| Baseline | Version | PMP-BL-vX.Y.Z | PMP-BL-vA.B.C | Reflects changes |
| Scope | [Field] | [Old] | [New] | [Rationale] |

### Files Modified

- [ ] docs/project-docs/Project-Management-Plan.md
- [ ] docs/project-docs/management-plans/[Plan-Name].md

### Validation

- [ ] All cross-references updated
- [ ] All version numbers consistent
- [ ] All changes approved

### Approval

- [ ] Project Manager Review: _______________ Date: _______
- [ ] Steering Committee Review (if required): _______________ Date: _______
```

---

## 4. Quality Assurance

### 4.1 Validation Checklist

**Before Submitting Adaptation Plan:**
- [ ] All inputs are valid and accessible
- [ ] All changes are inventoryed and mapped
- [ ] All skills and workflows are updated
- [ ] All PMP sections are updated
- [ ] All tests pass
- [ ] All documentation is updated
- [ ] All cross-references are valid
- [ ] All templates are properly filled
- [ ] Document passes validation scripts

**Validation Commands:**
```bash
# Check for broken links
python scripts/validate_links.py docs/project-docs/Adaptation-Plans/

# Check YAML frontmatter
python scripts/validate_frontmatter.py docs/project-docs/Adaptation-Plans/

# Check PMP consistency
python scripts/validate_pmp.py

# Run all tests
uv run pytest --ignore=tests/test_spark.py --ignore=tests/pmbok -v
```

### 4.2 Review Criteria

**Content Review:**
- [ ] Executive summary is accurate and complete
- [ ] All changes are properly inventoryed
- [ ] All impacts are correctly mapped
- [ ] All updates are clearly defined
- [ ] All dependencies are identified
- [ ] All risks are assessed

**Process Review:**
- [ ] Stage 17 methodology was followed
- [ ] All steps were completed
- [ ] All templates were used correctly
- [ ] All decisions are traceable
- [ ] All evidence is cited

**Compliance Review:**
- [ ] Follows PMBOK 8 standards
- [ ] Follows repository governance policies
- [ ] Follows ADR-037 for versioning
- [ ] Follows template governance rules

---

## 5. Integration with Obsidian Brain

### 5.1 Knowledge Graph Entries

Each adaptation should be represented in the Obsidian knowledge graph:

**Node Types:**
- `AdaptationPlan` - The adaptation plan itself
- `GovernanceChange` - The change being adapted
- `SkillUpdate` - The skill update
- `WorkflowUpdate` - The workflow update
- `PMPUpdate` - The PMP update
- `AdaptationEpisode` - The recorded approval episode

**Relationships:**
- `adapts` - Adaptation plan adapts governance change
- `updates` - Adaptation plan updates skill/workflow/PMP
- `operationalizes` - Skill update operationalizes governance change
- `tailors` - PMP update tailors baseline
- `approves` - Policy approves adaptation plan
- `records` - Episode records approval

**Example Graph Entry:**
```markdown
- [[ADP-20261106-001]] adapts [[GC-001]]
- [[ADP-20261106-001]] adapts [[GC-002]]
- [[ADP-20261106-001]] updates [[implement-story/SKILL.md]]
- [[ADP-20261106-001]] updates [[governance/SKILL.md]]
- [[ADP-20261106-001]] updates [[Project-Management-Plan.md]]
- [[ADP-20261106-001]] tailors [[PMP-BL-v1.0.0]] to [[PMP-BL-v1.0.1]]
- [[approve-adaptation-plan]] approves [[ADP-20261106-001]]
- [[Episode-ADP-20261106-001]] records [[ADP-20261106-001]]
```

### 5.2 Ingestion Script

Update `obsidian-second-brain/scripts/ingest-agent-learning.mjs` to handle Stage 17 artifacts:

```javascript
// Stage 17 ingestion
if (filePath.includes('Adaptation-Plans') || filePath.includes('adaptation-plan')) {
  const stage17Data = parseAdaptationPlan(fileContent);
  
  // Create adaptation plan node
  createNode({
    id: stage17Data.plan_id,
    type: 'AdaptationPlan',
    properties: stage17Data,
    tags: ['stage-17', 'adaptation-plan']
  });
  
  // Create adaptation change nodes
  stage17Data.changes.forEach(change => {
    createNode({
      id: change.change_id,
      type: 'GovernanceChange',
      properties: change,
      tags: ['stage-17', 'governance-change']
    });
    
    createRelationship({
      from: stage17Data.plan_id,
      to: change.change_id,
      type: 'adapts'
    });
  });
  
  // Create skill update nodes
  stage17Data.skill_updates.forEach(update => {
    createNode({
      id: `SkillUpdate-${update.skill}-${stage17Data.plan_id}`,
      type: 'SkillUpdate',
      properties: update,
      tags: ['stage-17', 'skill-update']
    });
    
    createRelationship({
      from: stage17Data.plan_id,
      to: `SkillUpdate-${update.skill}-${stage17Data.plan_id}`,
      type: 'updates'
    });
  });
  
  // Create PMP update nodes
  stage17Data.pmp_updates.forEach(update => {
    createNode({
      id: `PMPUpdate-${update.plan}-${stage17Data.plan_id}`,
      type: 'PMPUpdate',
      properties: update,
      tags: ['stage-17', 'pmp-update']
    });
    
    createRelationship({
      from: stage17Data.plan_id,
      to: `PMPUpdate-${update.plan}-${stage17Data.plan_id}`,
      type: 'updates'
    });
    
    createRelationship({
      from: `PMPUpdate-${update.plan}-${stage17Data.plan_id}`,
      to: update.from_baseline,
      type: 'tailors'
    });
    
    createRelationship({
      from: `PMPUpdate-${update.plan}-${stage17Data.plan_id}`,
      to: update.to_baseline,
      type: 'results_in'
    });
  });
}
```

### 5.3 Cross-Reference Index

| Artifact | ID Pattern | Location | Cross-Reference |
|---|---|---|---|
| Adaptation Plan | ADP-[DATE]-[NUMBER] | docs/project-docs/Adaptation-Plans/ | [[ADP-...]] |
| Governance Change | GC-[NUMBER] | Knowledge Graph | [[GC-...]] |
| Skill Update | SkillUpdate-[SKILL]-[PLAN] | Knowledge Graph | [[SkillUpdate-...]] |
| PMP Update | PMPUpdate-[PLAN]-[ADP] | Knowledge Graph | [[PMPUpdate-...]] |
| Adaptation Episode | Episode-ADP-[ID] | docs/policy-shapes/episodes/ | [[Episode-...]] |

---

## 6. Success Metrics

### 6.1 Quality Metrics

| Metric | Target | Measurement |
|---|---|---|
| Operationalization Rate | 100% | Percentage of governance changes operationalized |
| Skill Update Success | 100% | Percentage of skill updates that pass all tests |
| PMP Consistency | 100% | Percentage of PMP updates that are consistent |
| Traceability | 100% | Percentage of changes that can be traced to source |
| Review Turnaround | < 24 hours | Time from submission to review completion |

### 6.2 Process Metrics

| Metric | Target | Measurement |
|---|---|---|
| Cycle Time | < 14 days | Time from Stage 16 completion to Stage 17 completion |
| Change Volume | Varies | Number of governance changes operationalized |
| Rework Rate | < 5% | Percentage of changes that require revision |
| Validation Pass Rate | 100% | Percentage of validation tests that pass |

### 6.3 Maturity Levels

**Level 1: Initial**
- Basic operationalization
- Manual skill updates
- Ad-hoc PMP updates

**Level 2: Managed**
- Standardized templates
- Automated validation
- Consistent documentation

**Level 3: Defined**
- Integrated with knowledge graph
- Automated change tracking
- Predictive impact assessment

**Level 4: Quantitatively Managed**
- Metrics-driven improvements
- Automated operationalization suggestions
- Historical analysis for better decisions

**Level 5: Optimizing**
- Continuous improvement
- Machine learning for impact prediction
- Automated adaptation (where appropriate)

---

## 7. Tools and Automation

### 7.1 Skill Update Assistant

```python
# update_skill.py - Assistant for skill updates

def update_skill(skill_path, change_id, changes):
    """
    Assist in updating a skill based on a governance change.
    """
    # Read current skill
    with open(skill_path) as f:
        skill_content = f.read()
    
    # Apply changes
    for change in changes:
        old_text = change['old']
        new_text = change['new']
        section = change['section']
        
        # Find and replace
        if old_text in skill_content:
            skill_content = skill_content.replace(old_text, new_text)
            print(f"Updated {section}: {old_text[:50]}... -> {new_text[:50]}...")
        else:
            print(f"Warning: Could not find text to replace in {section}")
    
    # Write updated skill
    with open(skill_path, 'w') as f:
        f.write(skill_content)
    
    # Return summary
    return {
        'skill_path': skill_path,
        'change_id': change_id,
        'changes_applied': len(changes),
        'warnings': []
    }
```

### 7.2 PMP Update Assistant

```python
# update_pmp.py - Assistant for PMP updates

def update_pmp(pmp_path, baseline_from, baseline_to, changes):
    """
    Assist in updating PMP based on governance changes.
    """
    # Read current PMP
    with open(pmp_path) as f:
        pmp_content = f.read()
    
    # Update baseline version
    pmp_content = pmp_content.replace(
        f"baseline_id: \"{baseline_from}\"",
        f"baseline_id: \"{baseline_to}\""
    )
    
    # Apply changes
    for change in changes:
        section = change['section']
        field = change['field']
        old_value = change['old']
        new_value = change['new']
        
        # Update field
        pattern = f"{field}: \"{old_value}\""
        replacement = f"{field}: \"{new_value}\""
        pmp_content = pmp_content.replace(pattern, replacement)
    
    # Write updated PMP
    with open(pmp_path, 'w') as f:
        f.write(pmp_content)
    
    # Return summary
    return {
        'pmp_path': pmp_path,
        'baseline_from': baseline_from,
        'baseline_to': baseline_to,
        'changes_applied': len(changes)
    }
```

### 7.3 Validation Script

```python
# validate_stage17.py - Validate Stage 17 artifacts

def validate_stage17(adaptation_plan_path, skills_dir, pmp_path):
    """
    Validate Stage 17 adaptation plan and related artifacts.
    """
    errors = []
    warnings = []
    
    # Check adaptation plan file exists
    if not os.path.exists(adaptation_plan_path):
        errors.append(f"Adaptation plan file not found: {adaptation_plan_path}")
        return errors, warnings
    
    # Parse adaptation plan
    with open(adaptation_plan_path) as f:
        adaptation_plan = parse_adaptation_plan(f.read())
    
    # Check all changes are inventoryed
    changes = adaptation_plan.get('changes', [])
    if not changes:
        errors.append("No changes found in adaptation plan")
    
    # Check all skills exist
    for skill_update in adaptation_plan.get('skill_updates', []):
        skill_path = os.path.join(skills_dir, skill_update['path'])
        if not os.path.exists(skill_path):
            errors.append(f"Skill file not found: {skill_path}")
    
    # Check PMP exists
    if not os.path.exists(pmp_path):
        errors.append(f"PMP file not found: {pmp_path}")
    
    # Check all cross-references
    with open(adaptation_plan_path) as f:
        content = f.read()
        for ref in find_markdown_links(content):
            if not os.path.exists(ref['path']):
                warnings.append(f"Broken link: {ref['path']}")
    
    return errors, warnings
```

---

## 8. Common Pitfalls and Mitigations

### 8.1 Pitfalls

| Pitfall | Description | Mitigation |
|---|---|---|
| Incomplete inventory | Missing some governance changes | Use Stage 16 assessment as source of truth |
| Incorrect impact mapping | Wrong skills/workflows identified | Review with technical lead, trace all dependencies |
| Breaking changes | Skill updates break existing functionality | Run all tests, validate before and after |
| Inconsistent PMP | Version numbers or references don't match | Use PMP validation script, manual review |
| Missing documentation | Changes not documented | Use templates, require documentation for all changes |
| Scope creep | Adding unrelated changes | Stick to governance changes from Stage 16 |
| Validation gaps | Not all scenarios tested | Use comprehensive test suite, manual testing |

### 8.2 Mitigation Strategies

1. **Use Templates:** Always use the provided templates for consistency
2. **Follow Checklists:** Complete all checklist items before submitting
3. **Automate Validation:** Run validation scripts before submission
4. **Peer Review:** Have another team member review changes
5. **Incremental Updates:** Make small, focused changes
6. **Document Everything:** Document all changes, no matter how small
7. **Test Thoroughly:** Run all tests, including edge cases
8. **Trace to Source:** Always link changes to specific governance changes

---

## 9. References

### 9.1 Internal References

- [Intent-to-Outcome Chain Coverage](../intent-to-outcome-chain-coverage.md)
- [Project Status Register](../Project-Status-Register.md)
- [Stage 16 Governance Change Assessment](../Status-Reports/Stage-16-Governance-Change-Assessment.md)
- [Stage 16 Methodology](../Methodology/Stage-16-Governance-Change-Methodology.md)
- [Stage 18 Methodology](Stage-18-Intent-Refinement-Methodology.md) (to be created)

### 9.2 External References

- PMBOK 8: Project Management Body of Knowledge, 8th Edition
- PMI: Project Management Institute standards
- ISO 21500: Guidance on Project Management

### 9.3 Related Methodologies

- [Stage 15 Methodology](../Methodology/Stage-15-Lesson-Learned-Methodology.md)
- [Stage 16 Methodology](../Methodology/Stage-16-Governance-Change-Methodology.md)

---

## 10. Appendix

### 10.1 Glossary

| Term | Definition |
|---|---|
| Adaptation Plan | A plan to operationalize governance changes into skills, workflows, and PMP updates |
| Baseline | The approved version of project documents against which changes are measured |
| BRP | Baseline Revision Package - A package of changes to the baseline |
| SPA | Subsidiary Plan Amendment - A change to a subsidiary management plan |
| Governance Change | A change to the project's governance baseline, architectural decisions, or process documentation |

### 10.2 Acronyms

| Acronym | Expansion |
|---|---|
| ADP | Adaptation Plan |
| BRP | Baseline Revision Package |
| CI | Continuous Integration |
| GC | Governance Change |
| LL | Lesson Learned |
| PMP | Project Management Plan |
| PMBOK | Project Management Body of Knowledge |
| SPA | Subsidiary Plan Amendment |

### 10.3 Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-11-06 | Vibe Code | Initial version |

---

## Change Log

| Date | Version | Change |
|---|---|---|
| 2026-11-06 | 1.0 | Phase 1 guide. |
| 2026-11-10 | 1.1 | Authority in this repository (Sponsor decides, agent never registers an approval); one adaptation per phase; inputs and output path corrected (`Adaptation-Plans/`, change requests, store); generated plans regenerated by the tooling and baseline versioning by ADR-008 and ADR-037; validation commands limited to what exists; approval process rewritten (gate recommendation, then the Sponsor's words, then adjudicate and register). Templates are unchanged. |
