---
artifact_type: "methodology_guide"
stage: "16"
stage_name: "Governance Change"
pmbok_process: "4.6 Perform Integrated Change Control"
version: "1.1"
date: "2026-11-10"
owner: "Menno Drescher"
governance_policy: "classify-diff-type (FULL), escalate-diff-response (LOW)"
---

# Stage 16: Governance Change Methodology

> **Purpose:** This document provides a comprehensive methodology for Stage 16 (Governance Change) of the Intent-to-Outcome chain. Stage 16 processes lessons learned and insights to identify, classify, and escalate necessary changes to the project's governance baseline, architectural decisions, and process documentation.

> **Alignment:** PMBOK 8 Process 4.6 Perform Integrated Change Control

> **Authority:** FULL authority for `classify-diff-type`, LOW authority for `escalate-diff-response`

> **Authority in this repository:** the Charter names one decision-maker, the Project Sponsor and Maintainer (Menno Drescher). There is no standing Steering Committee, so every "Steering Committee" or "Project Manager" approval below is given by the Sponsor and recorded as such (as in CR-20261109-001, CR-20261109-002 and CR-20261110-001). An agent classifies and drafts; it never accepts, approves or applies a governance change on its own, and it never backfills or re-scores a gate that was missed (record the gap; any exception is a dated human waiver).

> **Scope of a pass:** a Stage 16 pass covers the whole Lessons Learned Register and the whole Continuous Improvement Register, not only the lessons flagged in Stage 15. A lesson or improvement that earlier passes never triaged is triaged now (Step 2).

---

## 1. Stage 16 Overview

### 1.1 Purpose and Position in the Chain

Stage 16 sits at the **Monitoring & Controlling** process group, acting as the **gatekeeper for baseline evolution**. It receives input from Stage 15 (Lesson Learned) and produces outputs that feed into Stage 17 (Adaptation Plan).

```
Stage 15 (Lesson Learned)
    \u2193
Stage 16 (Governance Change)  Classify & Escalate
    \u2193
Stage 17 (Adaptation Plan)  Operationalize
```

**Key Responsibility:** Determine whether a lesson learned requires a change to the governed baseline, and if so, what type of change and at what authority level.

### 1.2 Inputs

| Input | Source | Mandatory |
|---|---|---|
| Approved Lessons Learned | Stage 15 output | Yes |
| Flagged Lessons | Stage 15 assessment | Yes |
| Current Baseline | PMP-BL-vX.Y.Z | Yes |
| Existing ADRs | docs/adr/ | Yes |
| Governance Episodes | docs/policy-shapes/episodes/ | Yes |
| Audit Register | docs/registers/Audit-Register.md | Yes |
| Project Charter | docs/project-docs/Project-Charter.md | Yes |
| Continuous Improvement Register | docs/project-docs/Continuous-Improvement-Register.md | Yes |
| Baseline findings from Stage 14 | the "Baseline findings" table of the Stage 14 note | Yes |
| Open change requests | docs/governance/change-requests/ | Yes |

### 1.3 Outputs

| Output | Destination | Governed |
|---|---|---|
| Classified Diffs | Stage 16 assessment | No |
| Escalation Decisions | Stage 16 assessment | No |
| Baseline Revision Package (BRP) | Stage 17 input | Yes (if Steering Committee) |
| Subsidiary Plan Amendments | Stage 17 input | Yes (if PM authority) |
| Updated Governance Episodes | docs/policy-shapes/episodes/ | Yes |

### 1.4 Success Criteria

Stage 16 is complete when:
- [ ] All flagged lessons from Stage 15 are classified
- [ ] All classified diffs have escalation decisions
- [ ] All required governance amendments are prepared
- [ ] All decisions are recorded as governance episodes
- [ ] Project-Status-Register.md is updated

---

## 2. Governance Change Process (8-Step)

### Step 1: Input Validation

**Purpose:** Ensure all required inputs are available and valid before processing.

**Actions:**
1. Verify Stage 15 assessment is complete and approved
2. Confirm all flagged lessons are documented in Lessons-Learned-Register.md
3. Verify current baseline (PMP-BL-vX.Y.Z) is accessible
4. Confirm Project Charter approval limits are documented
5. Verify governance policies (`classify-diff-type`, `escalate-diff-response`) are operational

**Checklist:**
- [ ] Stage 15 assessment exists and is marked COMPLETED
- [ ] All flagged lessons have complete entries in Lessons-Learned-Register.md
- [ ] Current baseline version is documented
- [ ] Charter approval limits are defined
- [ ] Governance policies are available and tested

**Validation Commands** (Stage 15 for Phase 1 ends in the words `STAGE 15 COMPLETE`; for Phase 2 the maintainer's acceptance is recorded in the Stage 15 note):
```bash
# Stage 15 is complete and accepted
grep -n "accepted\|COMPLETE" docs/project-docs/Status-Reports/Stage-15-*.md

# Every lesson parses, and the last id is the one expected
uv run python -c "from agent_learning.lessons_learned import load_lessons_learned_register as l; e=l(); print(len(e), e[-1].id)"

# Baseline and policies
head -30 docs/project-docs/Project-Management-Plan.md | grep "PMP-BL-v"
ls docs/policy-shapes/classify-diff-type.actions.json docs/policy-shapes/escalate-diff-response.actions.json

# The store the governance commands will write to (LL-040): print it, count its files
echo "${AGENT_LEARNING_LOCAL_STORE_DIR:-./data/agent-learning/store}"
```
Check that `AGENT_LEARNING_LOCAL_STORE_DIR` points at this repository's store before any command that registers an episode. `scripts/stage16_amend.py` does not print or check it yet.

---

### Step 2: Triage of the whole registers

**Purpose:** Separate lessons and improvements that need a governance change from those that need a direct fix or none, and find those no earlier pass triaged.

**2a. Coverage of the Lessons Learned Register.** For every `LL-###`, read its Tier 2/3 target and place it in one bucket:

| Bucket | Meaning |
|---|---|
| A. Tier 1 only | No propagation owed. |
| B. Tier 2/3 target, rule found there | Applied. Confirm by reading the target, not only by finding the id. |
| C. Tier 2/3 target, rule not found | Not applied. A finding, because LL-041 requires the Tier 2 edit in the same PR as the entry. |

An id search is a lead, not proof (a rule can sit in a skill without its id, an id in a test proves nothing). Read the named target. Tier 3 (`sidpa-template`) is outside the repository; list it as proposed, never as done.

**2b. Coverage of the Continuous Improvement Register.** For every `IMP-###` whose disposition is `In-Flight Candidate`, read the change it names in the code and mark it implemented, partly, or open. An entry that says it awaits Stage 16/17 and was never evaluated is a finding. Check the numbering for gaps and the dispositions for stale labels; do not change a status on the agent's reading alone.

**2c. Identifier integrity.** Check that each id cited in earlier stage documents (assessments, SPAs, BRPs, adaptation plans) names the lesson or improvement the register holds under that id. A mismatch is a baseline finding corrected through the amendment tooling; nothing is re-scored.

**2d. Classification of what needs a change.**

| Lesson or improvement impact | Requires governance change? | Action |
|---|---|---|
| Architectural (affects code structure) | Yes | Stage 16 |
| Process (affects how work is done) | Yes | Stage 16 |
| Documentation (clarification only) | No | Direct fix, traced |
| Tooling (automation only) | No | Direct fix, traced (a story or an `IMP`) |
| Scope (new features) | Yes | Stage 16 |
| Schedule (timeline changes) | Yes | Stage 16 |
| Cost (budget changes) | Yes | Stage 16 |
| Quality (standards changes) | Yes | Stage 16 |

**Triage Questions:**
1. Does this lesson require a change to the approved baseline?
2. Does it affect architectural decisions (ADRs)?
3. Does it require updates to governance policies, skills or templates?
4. Does it impact project scope, schedule, or cost?
5. Can it be resolved through documentation or tooling changes only?
6. Does the lesson conflict with a rule already in force (for example two skill steps that disagree)? Settle the conflict in the same change as the addition.

**Output:** Coverage table for both registers, and the list of items requiring Stage 16 processing, each with its route (Step 3).

---

### Step 3: Diff Classification (classify-diff-type)

**Purpose:** Classify each governance change by its structural type to determine the appropriate handling.

**Policy:** `classify-diff-type` (FULL authority)

**Two classifications, used for two different things.** The diff types below label a *proposed change* so that it can be routed and escalated. The `classify-diff-type` policy classifies an *edit to an approved document* into one of seven actions: `new_superseding_adr`, `amendment_log_entry`, `correction_note`, `clarification_section`, `provenance_note`, `pending_supersession_note`, `supersession_update`. Use the diff type here; use the policy's action only when an approved document is edited (route 1 below). The policy's lifecycle actions (`new_superseding_adr`, `pending_supersession_note`, `supersession_update`) mean the change is more than an amendment: stop and use the ADR route.

**Routes by artifact.** The artifact decides the tooling, not the diff type:

| # | Artifact changed | Route | Evidence it leaves |
|---|---|---|---|
| 1 | An approved ADR, BRD, FDD or user story | ADR-007: edit uncommitted, `uv run python scripts/stage16_amend.py propose <doc>`, a human reads the classification, then `accept <doc> --by "<name>" --summary "..."` on the human's explicit instruction; commit the document, the manifest and the `docs/policy-shapes/` files together. `tests/test_governance_baseline.py` must pass. | Episode in `docs/policy-shapes/episodes/`, the `Amended <date> at Stage 16 ...` line in the document, a refreshed manifest |
| 2 | A skill under `.claude/skills/` (Tier 2), a script, a workflow, a process document | A manual Change Request `CR-YYYYMMDD-NNN` under `docs/governance/change-requests/` with the exact proposed text, a Sponsor decision recorded in it, then one PR that applies the edit and cites the request (LL-041). The whole suite must pass. | The request, its decision record, the PR |
| 3 | The PMP and generated subsidiary plans | Regenerate from the `pmbok-planning` tooling and templates; never hand-edit a generated plan. A standard that must hold in every run belongs in the template. | The regenerated plan and its baseline id |
| 4 | The baseline itself (scope, schedule, cost, a new baseline id) | Baseline Revision Package (Step 6); versioning per ADR-008 §4.6.1 and ADR-037. | `BRP-...` document, new `PMP-BL` id |
| 5 | A register entry (`LL`, `IMP`) | Append-only. A correction is a new dated entry; an id is never reused or renumbered. | The register |
| 6 | A stage assessment or methodology note (a Status Report, this guide) | Direct edit with a change-log line; these are working documents. | Git history |

**Diff Type Taxonomy:**

#### 1. Structural Diffs (Architectural Changes)
- **Definition:** Changes that affect the project's architectural structure
- **Examples:** Adding/removing modules, changing package structure, migrating code
- **Authority:** Typically requires Steering Committee approval
- **Version Impact:** Minor or major version increment

#### 2. Process Diffs (Governance Procedure Changes)
- **Definition:** Changes to how governance is performed
- **Examples:** Evidence management, approval workflows, documentation standards
- **Authority:** Typically within PM authority
- **Version Impact:** Patch version or subsidiary plan update

#### 3. Content Diffs (Documentation Changes)
- **Definition:** Changes to documentation content only
- **Examples:** Clarifications, corrections, additions
- **Authority:** Typically within PM authority
- **Version Impact:** Patch version

#### 4. Dependency Diffs (External Package Changes)
- **Definition:** Changes to external dependencies
- **Examples:** Version bumps, package additions/removals
- **Authority:** Varies by impact
- **Version Impact:** Patch or minor version

#### 5. Configuration Diffs (Settings Changes)
- **Definition:** Changes to configuration files
- **Examples:** CI configuration, environment settings
- **Authority:** Typically within PM authority
- **Version Impact:** Patch version

#### 6. Scope Diffs (Feature Changes)
- **Definition:** Changes to project scope
- **Examples:** New features, removed features, changed requirements
- **Authority:** Typically requires Steering Committee approval
- **Version Impact:** Major version increment

#### 7. Schedule Diffs (Timeline Changes)
- **Definition:** Changes to project timeline
- **Examples:** Extended deadlines, accelerated delivery
- **Authority:** Varies by magnitude
- **Version Impact:** Typically no version change

**Classification Template:**
```yaml
lesson_id: LL-XXX
diff_type: [structural|process|content|dependency|configuration|scope|schedule]
subtype: [specific subtype]
evidence_basis: [execution|design_time]
affected_artifacts: [list of files/directories]
scope: [migration|update|addition|removal|refactoring]
impact: [low|medium|high]
confidence: [low|medium|high]
classification_timestamp: "YYYY-MM-DD"
classifier: classify-diff-type
rationale: "Detailed explanation of classification"
```

**Classification Rules:**
1. **Start with the most specific type** - If a change affects architecture, classify as structural even if it also affects process
2. **Consider evidence basis** - `execution` for changes derived from executed work, `design_time` for changes found during design review
3. **Assess impact** - High impact changes typically require higher authority
4. **Document rationale** - Always include clear reasoning for the classification

---

### Step 4: Impact Assessment

**Purpose:** Assess the impact of each classified diff to inform escalation decisions.

**Impact Dimensions:**

#### Technical Impact
- **Code Complexity:** Does it increase or decrease complexity?
- **Test Coverage:** Does it require new tests?
- **Performance:** Does it affect performance characteristics?
- **Security:** Does it introduce security considerations?
- **Maintainability:** Does it affect code maintainability?

#### Process Impact
- **Workflow Changes:** Does it change how work is performed?
- **Tooling Changes:** Does it require new or modified tools?
- **Training:** Does it require team training?
- **Documentation:** Does it require documentation updates?

#### Governance Impact
- **Policy Changes:** Does it require changes to governance policies?
- **Approval Authority:** Does it change who can approve what?
- **Audit Trail:** Does it affect auditability?
- **Compliance:** Does it affect compliance requirements?

#### Business Impact
- **Cost:** Does it have cost implications?
- **Schedule:** Does it affect timelines?
- **Scope:** Does it change project scope?
- **Risk:** Does it introduce new risks?

**Impact Assessment Template:**
```yaml
lesson_id: LL-XXX
diff_type: [from Step 3]
technical_impact:
  complexity: [increase|decrease|neutral]
  test_coverage: [new_tests_required|existing_sufficient|reduced]
  performance: [improved|degraded|neutral]
  security: [improved|degraded|neutral]
  maintainability: [improved|degraded|neutral]
process_impact:
  workflow: [changed|unchanged]
  tooling: [new_required|modified|unchanged]
  training: [required|not_required]
  documentation: [required|not_required]
governance_impact:
  policy_changes: [required|not_required]
  approval_authority: [changed|unchanged]
  audit_trail: [affected|unchanged]
  compliance: [affected|unchanged]
business_impact:
  cost: [increase|decrease|neutral]
  schedule: [extended|accelerated|neutral]
  scope: [changed|unchanged]
  risk: [new_risks|reduced_risks|neutral]
overall_impact: [low|medium|high]
```

---

### Step 5: Escalation Decision (escalate-diff-response)

**Purpose:** Determine the appropriate authority level for each classified diff.

**Policy:** `escalate-diff-response` (LOW authority, human decides)

**Escalation Matrix:**

| Diff Type | Impact | Authority Level | Action |
|---|---|---|---|
| Structural | High | Steering Committee | Baseline Revision Package |
| Structural | Medium | Steering Committee | Baseline Revision Package |
| Structural | Low | Project Manager | Subsidiary Plan Amendment |
| Process | High | Steering Committee | Baseline Revision Package |
| Process | Medium | Project Manager | Subsidiary Plan Amendment |
| Process | Low | Project Manager | Subsidiary Plan Amendment |
| Scope | Any | Steering Committee | Baseline Revision Package |
| Schedule | High | Steering Committee | Baseline Revision Package |
| Schedule | Medium/Low | Project Manager | Subsidiary Plan Amendment |
| Content | Any | Project Manager | Direct update or Subsidiary Plan |
| Dependency | High | Steering Committee | Baseline Revision Package |
| Dependency | Medium/Low | Project Manager | Subsidiary Plan Amendment |
| Configuration | Any | Project Manager | Direct update |

**Authority Limits (from Project Charter):**
- **Project Manager Authority:** Changes within approved scope, schedule, and budget
- **Steering Committee Authority:** Changes to scope, major schedule changes, budget changes > X%, architectural changes
- **Project Sponsor Authority:** Project charter changes, major scope changes

**Who decides here.** The matrix names roles from the PMBOK model. In this repository each of them is the Project Sponsor (see Authority above). The `escalate-diff-response` policy runs at LOW authority and its classifier's human-approval gate halts before it, so the human's decision is the decision of record. Write the decision into the request or the document it concerns; do not infer an approval from silence or from a later instruction.

**Escalation Template:**
```yaml
lesson_id: LL-XXX
diff_type: [from Step 3]
escalation_level: [project_manager|steering_committee|project_sponsor]
action: [direct_update|subsidiary_plan_amendment|baseline_revision_package]
evidence_basis: [execution|design_time]
threshold_exceeded: [true|false]
charter_approval_limit: [exceeded|within]
required_approvals: [list of roles]
decision_timestamp: "YYYY-MM-DD"
escalator: escalate-diff-response
rationale: "Detailed explanation of escalation decision"
```

**Escalation Decision Tree:**

```
Does the change exceed Charter approval limits?
  \u2192 Yes: Escalate to Steering Committee
  \u2192 No: Is it within PM authority?
    \u2192 Yes: Escalate to Project Manager
    \u2192 No: Escalate to Project Sponsor
```

**Charter Approval Limit Check:**
- Review Project Charter for specific limits
- Check ADR-037 for versioning rules
- Consult governance policies for thresholds

---

### Step 6: Governance Amendment Preparation

**Purpose:** Prepare the necessary documentation for approved governance changes.

Prepare the document that matches the route chosen in Step 3. Route 1 needs no separate package (the amendment tooling produces the evidence). Route 2 needs a Change Request. A BRP or an SPA is used only when the baseline or a subsidiary plan changes; existing examples are `docs/governance/brp/` and `docs/governance/spa/`. Prepare, do not apply: nothing here is applied before the decision is recorded.

#### Baseline Revision Package (BRP) - For Steering Committee

**Required Contents:**
1. **Revised PMP** - Updated Project Management Plan
2. **Changed Plans** - All affected subsidiary management plans
3. **Standard Set** - Core project documents:
   - Spark-Capture.md
   - Ideation-Document.md
   - Business-Case.md
   - Benefits-Statement.md
   - Stakeholder-Register.md
   - Project-Charter.md (if amended)
4. **Change Documentation** - Detailed description of changes
5. **Impact Assessment** - Technical, process, governance, business impacts
6. **Risk Assessment** - New risks introduced by changes
7. **Rollback Plan** - How to revert if issues arise

**Versioning Rules (ADR-037):**
- Design-time revisions: PMP-BL-v1.0.x (patch increment)
- Execution-time adaptations: PMP-BL-v1.1.0 (minor increment)
- Major architectural changes: PMP-BL-v2.0.0 (major increment)

**BRP Template:**
```markdown
# Baseline Revision Package: PMP-BL-vX.Y.Z

## Change Summary
- **Package ID:** BRP-YYYYMMDD-XXX
- **Date:** YYYY-MM-DD
- **Prepared by:** [Name]
- **Version:** PMP-BL-vX.Y.Z (from vA.B.C)

## Changes Included
1. [Change 1 description]
2. [Change 2 description]

## Affected Documents
- [ ] Project-Management-Plan.md
- [ ] docs/project-docs/management-plans/Scope-Management-Plan.md
- [ ] docs/project-docs/management-plans/Schedule-Management-Plan.md
- [ ] ...

## Approval Status
- [ ] Project Manager Review
- [ ] Steering Committee Approval
- [ ] Project Sponsor Approval (if required)

## Implementation Plan
1. [Step 1]
2. [Step 2]

## Rollback Plan
1. [Step 1]
2. [Step 2]
```

#### Subsidiary Plan Amendment - For Project Manager

**Required Contents:**
1. **Plan Identification** - Which subsidiary plan is being amended
2. **Change Description** - What is changing and why
3. **Impact Assessment** - How the change affects the plan
4. **Implementation Steps** - How to implement the change
5. **Verification** - How to verify the change is successful

**Subsidiary Plan Amendment Template:**
```markdown
# Subsidiary Plan Amendment: [Plan Name]

## Amendment Details
- **Amendment ID:** SPA-YYYYMMDD-XXX
- **Date:** YYYY-MM-DD
- **Prepared by:** [Name]
- **Plan:** [Plan Name]
- **Version:** vX.Y.Z

## Change Description
[Detailed description of the change]

## Rationale
[Why this change is necessary]

## Impact Assessment
- **Scope:** [Affected areas]
- **Schedule:** [Timeline impact]
- **Cost:** [Cost impact]
- **Risk:** [Risk assessment]

## Implementation
1. [Step 1]
2. [Step 2]

## Verification
- [ ] [Verification criterion 1]
- [ ] [Verification criterion 2]

## Approval
- [ ] Project Manager: _______________ Date: _______
```

---

### Step 7: Decision Recording

**Purpose:** Record every governance decision so it can be audited and replayed.

**Use the tooling; do not hand-write episodes.** Episodes are `Episode` records created by the commands, not JSON written by hand:

| Decision | How it is recorded |
|---|---|
| An edit to an approved ADR, BRD, FDD or story | `stage16_amend.py propose`, then `accept`: frame, result and measurements under `docs/policy-shapes/`, the episode in `docs/policy-shapes/episodes/` (for example `amend-adr-005-cr002b-episode.json`), the Status line in the document, and a refreshed governance baseline (`scripts/governance_baseline.py`) |
| A decision on a change request | The decision table inside the request, with the date and the words of the decision as given by the human |
| A classification by `classify-diff-type` or an escalation by `escalate-diff-response` outside the amendment route | `agent-learn-ext task-policy-decide`, then `task-policy-adjudicate`, then `task-episode-register`, in that order |

**Rules:**
1. Before any `task-policy-decide`, `task-policy-adjudicate` or `task-episode-register`, resolve and print the store path and count its files before and after (LL-040). Only `task-episode-register` writes a file.
2. An agent never runs `accept` and never registers an approval on a human's behalf.
3. A gate that was missed is not approved afterwards. Record the gap in the assessment; run the gate going forward; an exception is a dated human waiver.
4. Never edit `tests/governance_baseline.json` by hand.
5. Stages 13 to 15 have no episodes here (they are `human_review`); a Stage 16 decision on their output is the first episode.

**Recording order:** decide, record in the request or document, commit together with the evidence files, run `tests/test_governance_baseline.py` and the whole suite.

---

### Step 8: Stage Completion and Handoff

**Purpose:** Finalize Stage 16 and prepare for Stage 17.

**Completion Checklist:**
- [ ] Every lesson and every in-flight improvement has a coverage line (Step 2), not only the flagged ones
- [ ] Id mismatches in earlier documents are listed (Step 2c)
- [ ] All flagged lessons from Stage 15 are classified
- [ ] All classified diffs have escalation decisions
- [ ] Each change has a route (Step 3) and its evidence
- [ ] All required BRPs are prepared and submitted
- [ ] All required subsidiary plan amendments are prepared and submitted
- [ ] All decisions are recorded as the route requires (Step 7); none is recorded by an agent for a human
- [ ] Project-Status-Register.md is updated to mark Stage 16 as COMPLETED
- [ ] Stage 16 assessment document is complete and approved
- [ ] All artifacts are committed to repository

**One adaptation per phase.** The phase close runs Stage 16 and Stage 17 once, as one adaptation; Stage 17 receives everything Stage 16 approved, plus what it deferred to Phase Next.

**Handoff to Stage 17:**
1. Create Stage 17 assessment document
2. Reference all approved governance changes from Stage 16
3. Identify operationalization requirements
4. Prepare adaptation plan
5. Submit for approval via `approve-adaptation-plan`

**Stage 16 Completion Template:**
```markdown
## Stage 16 Completion Summary

### Processing Summary
- **Lessons Processed:** X
- **Flagged for Governance Change:** Y
- **Classified Diffs:** Y
- **Escalation Decisions:** Y
- **BRPs Created:** A
- **Subsidiary Plan Amendments:** B

### Decisions Made
| Lesson ID | Diff Type | Escalation Level | Action | Status |
|---|---|---|---|---|
| LL-XXX | structural | steering_committee | BRP | Approved/Pending |
| LL-YYY | process | project_manager | SPA | Approved/Pending |

### Next Steps
1. [Stage 17 action 1]
2. [Stage 17 action 2]

### Approval
- [ ] Stage 16 Assessment Approved
- [ ] Project-Status-Register.md Updated
- [ ] All artifacts committed
```

---

## 3. Templates

### 3.1 Stage 16 Assessment Template

```markdown
---
artifact_type: "governance_change_assessment"
report_id: "REP-GC-[PROJECT]-[DATE]"
baseline_id: "PMP-BL-vX.Y.Z"
lifecycle_stage: "Stage 16 (Governance Change) / Integrated Change Control"
pmbok_process: "4.6 Perform Integrated Change Control"
date: "YYYY-MM-DD"
governance_policy: "classify-diff-type (FULL), escalate-diff-response (LOW)"
evidence_commit: "[commit hash]"
related_documents:
  - "[Stage 15 assessment]"
  - "[Lessons Learned Register]"
  - "[Project Status Register]"
---

# Stage 16: Governance Change Assessment \u2014 [Project]

> **Purpose:** [Brief purpose statement]
>
> **Authority:** [Authority description]
>
> **Status:** [IN PROGRESS/COMPLETED]

---

## Executive Summary

| Field | Status |
|---|---|
| **Stage 15 Input** | [X lessons flagged] |
| **Classification Status** | [Y classified] |
| **Escalation Status** | [Z escalated] |
| **Overall Status** | **[STAGE 16 INITIATED/COMPLETED]** |

---

## 1. Input Analysis

### Lessons Learned Status
[Table of lessons from Stage 15]

### Flagged Items
[List of flagged lessons with reasons]

---

## 2. Classification Results

### [Lesson ID]
- **Diff Type:** [type]
- **Subtype:** [subtype]
- **Evidence Basis:** [execution|design_time]
- **Affected Artifacts:** [list]
- **Scope:** [scope]
- **Impact:** [low|medium|high]
- **Confidence:** [low|medium|high]
- **Rationale:** [detailed rationale]

---

## 3. Escalation Results

### [Lesson ID]
- **Escalation Level:** [level]
- **Action:** [action]
- **Threshold Exceeded:** [true|false]
- **Required Approvals:** [list]
- **Rationale:** [detailed rationale]

---

## 4. Governance Actions

### Immediate Actions
[List of actions to take]

### Short Term Actions
[List of follow-up actions]

---

## 5. Next Steps

### Stage 17 Preparation
[List of Stage 17 preparation items]
```

### 3.2 Governance Episode Template

```json
{
  "episode_id": "",
  "timestamp": "",
  "policy": "",
  "action": "",
  "lesson_id": "",
  "diff_type": "",
  "escalation_level": "",
  "decision": "",
  "decision_maker": "",
  "evidence": {
    "basis": "",
    "artifacts": []
  },
  "related_episodes": []
}
```

### 3.3 Classification Decision Template

```yaml
lesson_id: 
  diff_type: 
  subtype: 
  evidence_basis: 
  affected_artifacts: 
  scope: 
  impact: 
  confidence: 
  classification_timestamp: 
  classifier: 
  rationale: 
```

### 3.4 Escalation Decision Template

```yaml
lesson_id: 
  diff_type: 
  escalation_level: 
  action: 
  evidence_basis: 
  threshold_exceeded: 
  charter_approval_limit: 
  required_approvals: 
  decision_timestamp: 
  escalator: 
  rationale: 
```

---

## 4. Quality Assurance

### 4.1 Validation Checklist

**Before Submitting Stage 16 Assessment:**
- [ ] All inputs are valid and accessible
- [ ] All flagged lessons are processed
- [ ] All classifications are documented with rationale
- [ ] All escalation decisions are documented with rationale
- [ ] All governance amendments are prepared
- [ ] All decisions are recorded as episodes
- [ ] All artifacts are properly versioned
- [ ] All cross-references are valid
- [ ] All templates are properly filled
- [ ] Document passes validation scripts

**Validation Commands** (the scripts `validate_links.py`, `validate_frontmatter.py` and `validate_episodes.py` do not exist in this repository):
```bash
uv run pytest tests/test_governance_baseline.py tests/test_stage16_amend.py tests/test_lessons_learned.py
uv run pytest            # the whole suite, no --ignore
```

### 4.2 Review Criteria

**Content Review:**
- [ ] Executive summary is accurate and complete
- [ ] All classifications are logical and well-justified
- [ ] All escalation decisions are appropriate
- [ ] All actions are clearly defined
- [ ] All dependencies are identified
- [ ] All risks are assessed

**Process Review:**
- [ ] Stage 16 methodology was followed
- [ ] All steps were completed
- [ ] All templates were used correctly
- [ ] All decisions are traceable
- [ ] All evidence is cited

**Compliance Review:**
- [ ] Follows PMBOK 8 standards
- [ ] Follows repository governance policies
- [ ] Follows ADR-010 for lessons learned
- [ ] Follows ADR-037 for versioning
- [ ] Follows template governance rules

---

## 5. Integration with Obsidian Brain

### 5.1 Knowledge Graph Entries

Each governance change should be represented in the Obsidian knowledge graph:

**Node Types:**
- `GovernanceChange` - The change itself
- `LessonLearned` - The triggering lesson
- `DiffClassification` - The classification decision
- `EscalationDecision` - The escalation decision
- `GovernanceEpisode` - The recorded episode
- `BaselineRevision` - The BRP or SPA

**Relationships:**
- `triggers` - Lesson triggers governance change
- `classifies` - Policy classifies diff
- `escalates` - Policy escalates decision
- `records` - Episode records decision
- `amends` - Change amends baseline
- `requires` - Change requires approval
- `implements` - Change implements lesson

**Example Graph Entry:**
```markdown
- [[LL-043]] triggers [[GC-001]]
- [[classify-diff-type]] classifies [[GC-001]] as [[StructuralDiff]]
- [[escalate-diff-response]] escalates [[GC-001]] to [[SteeringCommittee]]
- [[Episode-GC-001-20261105]] records [[GC-001]]
- [[BRP-20261105-001]] amends [[PMP-BL-v1.0.0]]
- [[GC-001]] implements [[LL-043]]
```

### 5.2 Ingestion Script

Update `obsidian-second-brain/scripts/ingest-agent-learning.mjs` to handle Stage 16 artifacts:

```javascript
// Stage 16 ingestion
if (filePath.includes('Stage-16-')) {
  const stage16Data = parseStage16Assessment(fileContent);
  
  // Create governance change nodes
  stage16Data.classifications.forEach(classification => {
    createNode({
      id: `GC-${classification.lesson_id}`,
      type: 'GovernanceChange',
      properties: classification,
      tags: ['stage-16', 'governance-change']
    });
  });
  
  // Create classification nodes
  stage16Data.classifications.forEach(classification => {
    createNode({
      id: `DiffClass-${classification.lesson_id}`,
      type: 'DiffClassification',
      properties: {
        diff_type: classification.diff_type,
        subtype: classification.subtype,
        rationale: classification.rationale
      },
      tags: ['stage-16', 'classification']
    });
    
    createRelationship({
      from: `classify-diff-type`,
      to: `DiffClass-${classification.lesson_id}`,
      type: 'classifies'
    });
  });
  
  // Create escalation nodes
  stage16Data.escalations.forEach(escalation => {
    createNode({
      id: `Escalation-${escalation.lesson_id}`,
      type: 'EscalationDecision',
      properties: escalation,
      tags: ['stage-16', 'escalation']
    });
    
    createRelationship({
      from: `escalate-diff-response`,
      to: `Escalation-${escalation.lesson_id}`,
      type: 'escalates'
    });
  });
}
```

### 5.3 Cross-Reference Index

Maintain a cross-reference index for Stage 16 artifacts:

| Artifact | ID Pattern | Location | Cross-Reference |
|---|---|---|---|
| Stage 16 Assessment | REP-GC-[PROJECT]-[DATE] | docs/project-docs/Status-Reports/ | [[REP-GC-...]] |
| Governance Change | GC-[NUMBER] | Knowledge Graph | [[GC-...]] |
| Diff Classification | DiffClass-[LESSON_ID] | Knowledge Graph | [[DiffClass-LL-...]] |
| Escalation Decision | Escalation-[LESSON_ID] | Knowledge Graph | [[Escalation-LL-...]] |
| Governance Episode | Episode-[POLICY]-[ACTION]-[ID]-[DATE] | docs/policy-shapes/episodes/ | [[Episode-...]] |
| Baseline Revision Package | BRP-[DATE]-[NUMBER] | docs/governance/ | [[BRP-...]] |
| Subsidiary Plan Amendment | SPA-[DATE]-[NUMBER] | docs/project-docs/management-plans/ | [[SPA-...]] |

---

## 6. Success Metrics

### 6.1 Quality Metrics

| Metric | Target | Measurement |
|---|---|---|
| Classification Accuracy | 100% | Percentage of classifications that are logically consistent |
| Escalation Appropriateness | 100% | Percentage of escalations that match authority limits |
| Documentation Completeness | 100% | Percentage of required documents that are complete |
| Traceability | 100% | Percentage of decisions that can be traced to evidence |
| Review Turnaround | < 24 hours | Time from submission to review completion |

### 6.2 Process Metrics

| Metric | Target | Measurement |
|---|---|---|
| Cycle Time | < 48 hours | Time from Stage 15 completion to Stage 16 completion |
| Decision Velocity | > 5 decisions/day | Number of governance decisions made per day |
| Change Volume | Varies | Number of governance changes processed |
| Rework Rate | < 5% | Percentage of decisions that require revision |

### 6.3 Maturity Levels

**Level 1: Initial**
- Basic classification and escalation
- Manual documentation
- Ad-hoc decision recording

**Level 2: Managed**
- Standardized templates
- Automated validation
- Consistent decision recording

**Level 3: Defined**
- Integrated with knowledge graph
- Automated episode generation
- Predictive escalation

**Level 4: Quantitatively Managed**
- Metrics-driven improvements
- Automated classification suggestions
- Historical analysis for better decisions

**Level 5: Optimizing**
- Continuous improvement
- Machine learning for classification
- Automated decision making (where appropriate)

---

## 7. Tools and Automation

### 7.1 Classification Assistant

```python
# classify_diff.py - Assistant for diff classification

def classify_diff(lesson_text, affected_files, scope):
    """
    Assist in classifying a diff based on lesson text and affected files.
    """
    # Analyze lesson text for keywords
    keywords = {
        'structural': ['architecture', 'migrate', 'refactor', 'package', 'module', 'directory'],
        'process': ['governance', 'procedure', 'workflow', 'evidence', 'audit', 'policy'],
        'scope': ['feature', 'requirement', 'story', 'epic', 'deliverable'],
        'schedule': ['timeline', 'deadline', 'milestone', 'date', 'schedule'],
        'dependency': ['package', 'library', 'dependency', 'import', 'requirements'],
        'content': ['documentation', 'document', 'clarify', 'correct', 'update'],
        'configuration': ['config', 'setting', 'environment', '.yml', '.yaml', '.json']
    }
    
    # Score each category
    scores = {category: 0 for category in keywords}
    for category, terms in keywords.items():
        for term in terms:
            if term.lower() in lesson_text.lower():
                scores[category] += 1
    
    # Check affected files
    for file in affected_files:
        if file.startswith('src/') or file.startswith('tests/'):
            scores['structural'] += 2
        elif file.startswith('docs/'):
            scores['content'] += 2
            if 'governance' in file or 'policy' in file:
                scores['process'] += 2
        elif file.endswith('.yml') or file.endswith('.yaml') or file.endswith('.json'):
            scores['configuration'] += 2
    
    # Return top category
    return max(scores, key=scores.get)
```

### 7.2 Escalation Assistant

```python
# escalate_diff.py - Assistant for escalation decisions

def escalate_diff(diff_type, impact, charter_limits):
    """
    Assist in determining escalation level based on diff type, impact, and charter limits.
    """
    # Define escalation rules
    escalation_rules = {
        ('structural', 'high'): 'steering_committee',
        ('structural', 'medium'): 'steering_committee',
        ('structural', 'low'): 'project_manager',
        ('process', 'high'): 'steering_committee',
        ('process', 'medium'): 'project_manager',
        ('process', 'low'): 'project_manager',
        ('scope', 'any'): 'steering_committee',
        ('schedule', 'high'): 'steering_committee',
        ('schedule', 'medium'): 'project_manager',
        ('schedule', 'low'): 'project_manager',
        ('dependency', 'high'): 'steering_committee',
        ('dependency', 'medium'): 'project_manager',
        ('dependency', 'low'): 'project_manager',
        ('content', 'any'): 'project_manager',
        ('configuration', 'any'): 'project_manager'
    }
    
    # Get base escalation
    escalation = escalation_rules.get((diff_type, impact), 'project_manager')
    
    # Check against charter limits
    if charter_limits and charter_limits.get(diff_type, {}).get('requires_steering', False):
        escalation = 'steering_committee'
    
    return escalation
```

### 7.3 Validation Script

```python
# validate_stage16.py - Validate Stage 16 artifacts

def validate_stage16(assessment_path, register_path, episodes_dir):
    """
    Validate Stage 16 assessment and related artifacts.
    """
    errors = []
    warnings = []
    
    # Check assessment file exists
    if not os.path.exists(assessment_path):
        errors.append(f"Assessment file not found: {assessment_path}")
        return errors, warnings
    
    # Parse assessment
    with open(assessment_path) as f:
        assessment = parse_assessment(f.read())
    
    # Check all flagged lessons are processed
    flagged_lessons = assessment.get('flagged_lessons', [])
    classifications = assessment.get('classifications', [])
    
    for lesson in flagged_lessons:
        if lesson not in [c['lesson_id'] for c in classifications]:
            errors.append(f"Flagged lesson {lesson} not classified")
    
    # Check all classifications have escalations
    escalations = assessment.get('escalations', [])
    for classification in classifications:
        if classification['lesson_id'] not in [e['lesson_id'] for e in escalations]:
            errors.append(f"Classification for {classification['lesson_id']} has no escalation")
    
    # Check episodes are recorded
    for escalation in escalations:
        episode_pattern = f"*-{escalation['lesson_id']}-*.json"
        if not glob.glob(os.path.join(episodes_dir, episode_pattern)):
            warnings.append(f"No episode recorded for {escalation['lesson_id']}")
    
    # Check lessons exist in register
    with open(register_path) as f:
        register = f.read()
    
    for lesson in flagged_lessons:
        if f"LL-{lesson}" not in register:
            errors.append(f"Lesson {lesson} not found in register")
    
    return errors, warnings
```

---

## 8. Common Pitfalls and Mitigations

### 8.1 Pitfalls

| Pitfall | Description | Mitigation |
|---|---|---|
| Over-classification | Classifying everything as structural | Use the classification matrix, start with most specific type |
| Under-escalation | Not escalating high-impact changes | Always check charter approval limits |
| Incomplete documentation | Missing rationale for decisions | Use templates, require rationale for all decisions |
| Inconsistent versioning | Wrong version numbers | Follow ADR-037 versioning rules |
| Missing episodes | Decisions not recorded | Automate episode generation, validate before completion |
| Scope creep | Adding unrelated changes to BRP | Stick to the specific lesson being addressed |
| Analysis paralysis | Over-analyzing simple changes | Set time limits for classification and escalation |

### 8.2 Mitigation Strategies

1. **Use Templates:** Always use the provided templates for consistency
2. **Follow Checklists:** Complete all checklist items before submitting
3. **Automate Validation:** Run validation scripts before submission
4. **Peer Review:** Have another team member review classifications and escalations
5. **Timebox Decisions:** Set time limits for classification and escalation decisions
6. **Document Assumptions:** Clearly document any assumptions made during classification
7. **Trace to Evidence:** Always link decisions to specific evidence

---

## 9. References

### 9.1 Internal References

- [Intent-to-Outcome Chain Coverage](../intent-to-outcome-chain-coverage.md)
- [Project Status Register](../Project-Status-Register.md)
- [Lessons Learned Register](../Lessons-Learned-Register.md)
- [ADR-010: Lessons Learned Crystallization and Register](../adr/ADR-010-lessons-learned-crystallization-and-register.md)
- [ADR-034: Decommission pmbok/ Directory](../adr/ADR-034-decommission-pmbok-directory.md)
- [ADR-037: Design-Time vs Execution-Time Feedback Loops](../adr/ADR-037-design-time-vs-execution-time-feedback-loops.md)
- [Stage 15 Lesson Learned Methodology](./Stage-15-Lesson-Learned-Methodology.md)

### 9.2 External References

- PMBOK 8: Project Management Body of Knowledge, 8th Edition
- PMI: Project Management Institute standards
- ISO 21500: Guidance on Project Management

### 9.3 Related Methodologies

- [Stage 15 Methodology](./Stage-15-Lesson-Learned-Methodology.md)
- [Stage 17 Methodology](Stage-17-Adaptation-Plan-Methodology.md) (to be created)
- [Stage 18 Methodology](Stage-18-Intent-Refinement-Methodology.md) (to be created)

---

## 10. Appendix

### 10.1 Glossary

| Term | Definition |
|---|---|
| Baseline | The approved version of project documents against which changes are measured |
| BRP | Baseline Revision Package - A package of changes to the baseline |
| Diff | A difference between the current state and the baseline |
| Escalation | The process of routing a decision to the appropriate authority level |
| Episode | A recorded governance decision or action |
| SPA | Subsidiary Plan Amendment - A change to a subsidiary management plan |

### 10.2 Acronyms

| Acronym | Expansion |
|---|---|
| ADR | Architecture Decision Record |
| BRP | Baseline Revision Package |
| CI | Continuous Integration |
| LL | Lesson Learned |
| PMP | Project Management Plan |
| PMBOK | Project Management Body of Knowledge |
| SPA | Subsidiary Plan Amendment |

### 10.3 Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-11-05 | Vibe Code | Initial version |

---

## Change Log

| Date | Version | Change |
|---|---|---|
| 2026-11-05 | 1.0 | Phase 1 guide. |
| 2026-11-10 | 1.1 | Authority in this repository (one decision-maker, no agent approval); the pass covers both registers in full (Step 2a to 2d); two classifications distinguished and routes by artifact added (Step 3); who decides (Step 5); route-specific preparation (Step 6); decision recording through the tooling, with the store-path check and the no-retroactive-approval rule (Step 7); one adaptation per phase (Step 8); input list and validation commands corrected to what exists. Templates and the Obsidian section are unchanged. |
