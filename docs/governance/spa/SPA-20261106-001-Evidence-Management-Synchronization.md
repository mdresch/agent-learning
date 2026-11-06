---
artifact_type: "subsidiary_plan_amendment"
amendment_id: "SPA-20261106-001"
plan: "Governance-Management-Plan"
version: "v1.1.0"
date: "2026-11-06"
prepared_by: "Vibe Code (on behalf of Project Manager)"
status: "prepared"
submission_date: "2026-11-06"
related_lesson: "LL-046"
related_insight: "INSIGHT-004"
related_episodes:
  - "classify-diff-type-LL-046-20261106.json"
  - "escalate-diff-response-LL-046-20261106.json"
governance_policy: "classify-diff-type, escalate-diff-response"
escalation_level: "project_manager"
---

# Subsidiary Plan Amendment: SPA-20261106-001

## Evidence Management and Synchronization Strategy

> **Purpose:** Address LL-046 by establishing a single authoritative source for governance evidence and implementing automated synchronization with conflict detection.

> **Status:** Prepared for Project Manager Review

> **Authority:** Project Manager Approval Required

---

## Executive Summary

| Field | Value |
|---|---|
| **Amendment ID** | SPA-20261106-001 |
| **Plan** | Governance-Management-Plan |
| **Version** | v1.1.0 |
| **Submission Date** | 2026-11-06 |
| **Related Lesson** | [LL-046](../project-docs/Lessons-Learned-Register.md#ll-046) |
| **Related Insight** | [INSIGHT-004](../insights/INSIGHT-004.md) |
| **Escalation Level** | Project Manager |
| **Status** | **Prepared** |

---

## 1. Problem Statement

### Root Cause (from LL-046)

Gate evidence is currently split between two locations with no reconciliation mechanism:
1. **External Store** (`AGENT_LEARNING_LOCAL_STORE_DIR`) - Primary location for governance episodes
2. **Repository Copies** (`docs/policy-shapes/episodes/`) - Local copies for reference

**Issues:**
- No automated comparison between the two sources
- Upstream gates (approve-charter, approve-business-case) lack episodes entirely
- Incomplete audit trail for governance decisions
- Risk of divergence between sources

### Current State

- External store contains episodes from recent gates (approve-audit-record, etc.)
- Repository contains copies of some episodes
- No synchronization mechanism exists
- Manual copying creates potential for errors and omissions

### Impact

- **Audit trail integrity** - Incomplete record of governance decisions
- **Compliance risk** - Cannot guarantee all gates are properly documented
- **Operational inefficiency** - Manual reconciliation required
- **Traceability gap** - Difficult to trace decisions across systems

---

## 2. Proposed Solution

### 2.1 Evidence Management Strategy

**Designate Repository as Authoritative Source**

Rationale:
- Repository is version-controlled and auditable
- All team members have access
- Changes are tracked and reviewable
- Aligns with ADR-010 (documentation in repository)

**Synchronization Architecture:**
```
┌─────────────────────────┐
│   Governance Decision    │
└─────────────┬───────────┘
              │ writes to
              ▼
┌─────────────────────────┐
│  Repository (Authoritative) │ ◄─────────────────┐
│  docs/policy-shapes/episodes/ │                  │
└─────────────┬───────────┘                  │
              │ sync to                     │
              ▼                            │
┌─────────────────────────┐                  │
│   External Store          │ ◄─────────────────┘
│   (Read-Only Copy)        │
└─────────────────────────┘
```

### 2.2 Implementation Components

#### Component 1: Evidence Writer
- **Purpose:** Ensure all governance decisions write to repository first
- **Implementation:** Update `governance.py` to write episodes to repository
- **Location:** `src/agent_learning/governance.py`

#### Component 2: Synchronization Script
- **Purpose:** Sync repository episodes to external store
- **Implementation:** Python script to copy and validate episodes
- **Location:** `scripts/sync_governance_episodes.py`

#### Component 3: Validation Script
- **Purpose:** Detect conflicts and missing episodes
- **Implementation:** Compare repository and external store
- **Location:** `scripts/validate_governance_episodes.py`

#### Component 4: Backfill Script
- **Purpose:** Create missing episodes for upstream gates
- **Implementation:** Generate episodes for approve-charter, approve-business-case
- **Location:** `scripts/backfill_governance_episodes.py`

---

## 3. Changes to Governance-Management-Plan

### 3.1 New Policies

#### Policy 1: Authoritative Source
```
Policy: Evidence-Authoritative-Source
Description: All governance evidence must be written to the repository first
Applies to: All governance policies (approve-*, classify-*, escalate-*)
Enforcement: governance.py validation
Violation: Warning logged, but operation continues
```

#### Policy 2: Synchronization Requirement
```
Policy: Evidence-Synchronization
Description: All repository episodes must be synchronized to external store
Frequency: After each governance operation
Enforcement: CI/CD pipeline
Violation: Build failure if sync fails
```

#### Policy 3: Episode Validation
```
Policy: Episode-Validation
Description: All episodes must be valid JSON with required fields
Validation: schema validation before write
Enforcement: governance.py
Violation: Operation rejected
```

### 3.2 Updated Procedures

#### Procedure: Governance Decision Recording

**Before:**
1. Policy executes decision
2. Episode written to external store (if configured)
3. Manual copy to repository (optional)

**After:**
1. Policy executes decision
2. Episode written to repository (`docs/policy-shapes/episodes/`)
3. Automatic synchronization to external store
4. Validation of both copies

#### Procedure: Audit Trail Verification

**Before:**
1. Manual check of external store
2. Manual check of repository
3. Manual comparison (rarely done)

**After:**
1. Run `scripts/validate_governance_episodes.py`
2. Automated report of discrepancies
3. Automated flagging of missing episodes

---

## 4. Implementation Plan

### Phase 1: Preparation (Day 1)

1. **Create feature branch**
   ```bash
   git checkout -b feature/evidence-management-sync
   ```

2. **Create scripts directory**
   ```bash
   mkdir -p scripts/governance
   ```

3. **Create documentation**
   - Update Governance-Management-Plan.md
   - Create implementation guide

### Phase 2: Development (Days 2-5)

4. **Update governance.py**
   - Modify to write episodes to repository first
   - Add validation for episode schema
   - Add synchronization call

5. **Create sync script**
   - Implement `scripts/governance/sync_episodes.py`
   - Handle file copying
   - Handle error cases

6. **Create validation script**
   - Implement `scripts/governance/validate_episodes.py`
   - Compare repository vs external store
   - Generate discrepancy report

7. **Create backfill script**
   - Implement `scripts/governance/backfill_episodes.py`
   - Generate missing episodes for approve-charter, approve-business-case
   - Validate generated episodes

### Phase 3: Testing (Days 6-7)

8. **Unit tests**
   - Test governance.py changes
   - Test sync script
   - Test validation script
   - Test backfill script

9. **Integration tests**
   - Test full workflow: decision → write → sync → validate
   - Test error handling
   - Test edge cases

10. **CI/CD integration**
    - Add validation to CI pipeline
    - Add sync verification to CI pipeline

### Phase 4: Backfill (Days 8-9)

11. **Generate missing episodes**
    - Run backfill script for approve-charter
    - Run backfill script for approve-business-case
    - Verify generated episodes

12. **Sync existing episodes**
    - Run sync script to copy all existing episodes
    - Verify synchronization

13. **Validate all episodes**
    - Run validation script
    - Fix any issues
    - Verify 0 discrepancies

### Phase 5: Review and Approval (Days 10-12)

14. **Submit for review**
    - Create PR with all changes
    - Request Project Manager review

15. **Address feedback**
    - Incorporate review comments
    - Update documents as needed

16. **Final approval**
    - Project Manager approval
    - Merge to main branch

---

## 5. File Changes

### 5.1 New Files

```
scripts/governance/__init__.py
scripts/governance/sync_episodes.py
scripts/governance/validate_episodes.py
scripts/governance/backfill_episodes.py
docs/governance/spa/SPA-20261106-001-Evidence-Management-Synchronization.md
```

### 5.2 Modified Files

```
src/agent_learning/governance.py
.github/workflows/ci.yml
docs/project-docs/management-plans/Governance-Management-Plan.md
```

### 5.3 Generated Files (during backfill)

```
docs/policy-shapes/episodes/approve-charter-[timestamp].json
docs/policy-shapes/episodes/approve-business-case-[timestamp].json
```

---

## 6. Verification Criteria

### 6.1 Technical Verification

- [ ] All governance policies write episodes to repository
- [ ] Synchronization script successfully copies episodes to external store
- [ ] Validation script detects discrepancies between sources
- [ ] Backfill script generates valid episodes for missing gates
- [ ] All tests pass
- [ ] CI pipeline passes with new validation

### 6.2 Process Verification

- [ ] All new governance decisions are recorded in repository
- [ ] All repository episodes are synchronized to external store
- [ ] No discrepancies between repository and external store
- [ ] All upstream gates have episodes
- [ ] Validation script runs successfully in CI

### 6.3 Documentation Verification

- [ ] Governance-Management-Plan.md updated with new policies
- [ ] All scripts are documented
- [ ] All changes are recorded in SPA
- [ ] No broken links or references

---

## 7. Rollback Plan

### 7.1 Rollback Conditions

- Synchronization causes data loss
- Validation fails consistently
- Performance issues with new workflow
- Project Manager rejects the SPA

### 7.2 Rollback Steps

1. **Revert code changes**
   ```bash
   git revert <amendment-commit>
   ```

2. **Restore old governance.py**
   - Revert to previous version
   - Restore old behavior

3. **Remove new scripts**
   - Delete `scripts/governance/` directory
   - Remove from CI configuration

4. **Verify rollback**
   - Run old validation process
   - Verify governance still works

5. **Document rollback**
   - Record rollback decision and rationale
   - Update SPA status to "rolled back"

---

## 8. Risk Assessment

### 8.1 Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Data loss during sync | Low | High | Backup before sync, dry-run mode |
| Episode schema changes | Low | Medium | Validate all existing episodes first |
| Performance degradation | Low | Low | Optimize sync script, run async |
| External store unavailable | Low | Medium | Queue sync, retry later |

### 8.2 Process Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Manual intervention still needed | Medium | Medium | Automate as much as possible |
| Team resistance to change | Low | Medium | Communicate benefits, provide training |
| Backfill errors | Medium | Medium | Validate all backfilled episodes |

### 8.3 Business Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Audit findings due to incomplete history | Low | High | Complete backfill before go-live |
| Compliance issues | Low | High | Ensure all gates have episodes |

---

## 9. Resource Requirements

### 9.1 Human Resources

| Role | Time Required | Responsibility |
|---|---|---|
| Developer | 7 days | Script development and testing |
| QA Engineer | 2 days | Test verification |
| Technical Writer | 1 day | Documentation updates |
| Project Manager | 1 day | Coordination and review |

### 9.2 Tooling Resources

- Development environment with Python 3.12
- Access to repository and external store
- Code review tools
- CI/CD system

---

## 10. Approval Workflow

### 10.1 Required Approvals

1. **Technical Review**
   - [ ] Code review by senior developer
   - [ ] Test review by QA engineer
   - [ ] Architecture review by technical lead

2. **Project Management Review**
   - [ ] Governance policy review by Project Manager
   - [ ] Process impact review by Project Manager
   - [ ] Resource review by Project Manager

3. **Final Approval**
   - [ ] Project Manager approval

### 10.2 Approval Timeline

| Step | Duration | Target Date |
|---|---|---|
| Preparation | 1 day | 2026-11-06 |
| Development | 4 days | 2026-11-10 |
| Testing | 2 days | 2026-11-12 |
| Backfill | 2 days | 2026-11-14 |
| Technical Review | 2 days | 2026-11-16 |
| Project Management Review | 2 days | 2026-11-18 |
| Final Approval | 1 day | 2026-11-19 |
| **Total** | **14 days** | **2026-11-19** |

---

## 11. Success Metrics

### 11.1 Completion Metrics

- [ ] SPA submitted on time (2026-11-06)
- [ ] All development completed within 4 days
- [ ] All testing completed within 2 days
- [ ] Backfill completed within 2 days
- [ ] All reviews completed within 4 days
- [ ] Project Manager approval received within 2 days

### 11.2 Quality Metrics

- [ ] 100% of governance decisions recorded in repository
- [ ] 0 discrepancies between repository and external store
- [ ] 100% of upstream gates have episodes
- [ ] 0 critical bugs in synchronization
- [ ] All documentation updated and accurate

---

## 12. Handoff to Stage 17

### 12.1 Inputs for Stage 17

Once this SPA is approved and implemented, the following inputs will be available for Stage 17 (Adaptation Plan):

1. **Operationalized Governance Changes**
   - Updated governance.py with repository-first evidence writing
   - Synchronization scripts for evidence management
   - Validation scripts for audit trail integrity

2. **Documentation**
   - Updated Governance-Management-Plan.md
   - Implementation guides for new workflows
   - Training materials for team members

3. **Process Improvements**
   - Automated evidence recording
   - Automated synchronization
   - Automated validation

4. **Compliance Assurance**
   - Complete audit trail for all governance decisions
   - Single authoritative source for evidence
   - Automated discrepancy detection

### 12.2 Stage 17 Preparation

The following artifacts should be prepared for Stage 17:

1. **Adaptation Plan Document**
   - Reference this SPA (SPA-20261106-001)
   - Reference BRP-20261106-001 (for LL-043)
   - Document operationalization steps

2. **Skills and Workflows**
   - Update `.claude/skills/governance/SKILL.md` with new procedures
   - Update any other affected skills

3. **Validation**
   - Verify all changes integrated into baseline
   - Verify no regressions in governance operations

---

## 13. References

### 13.1 Related Documents

- [LL-046: Dual Evidence Storage Requires Reconciliation](../project-docs/Lessons-Learned-Register.md#ll-046)
- [INSIGHT-004: Gate evidence is split between the repository and an external store](../insights/INSIGHT-004.md)
- [ADR-010: Lessons Learned Crystallization and Register](../adr/ADR-010-lessons-learned-crystallization-and-register.md)
- [Governance-Management-Plan](../project-docs/management-plans/Governance-Management-Plan.md)
- [Stage 16 Governance Change Assessment](../project-docs/Status-Reports/Stage-16-Governance-Change-Assessment.md)
- [Stage 16 Methodology](../project-docs/Methodology/Stage-16-Governance-Change-Methodology.md)

### 13.2 Governance Episodes

- [Classification Episode: classify-diff-type-LL-046-20261106.json](../policy-shapes/episodes/classify-diff-type-LL-046-20261106.json)
- [Escalation Episode: escalate-diff-response-LL-046-20261106.json](../policy-shapes/episodes/escalate-diff-response-LL-046-20261106.json)

### 13.3 Related Lessons and Insights

- [OBS-001: Store outside repository](../observations/OBS-001.md)
- [OBS-007: Upstream gates missing episodes](../observations/OBS-007.md)
- [OBS-008: Registering episode writes to external store](../observations/OBS-008.md)

---

## 14. Appendix

### 14.1 Episode Schema

All governance episodes must conform to the following schema:

```json
{
  "episode_id": "UUID v4",
  "timestamp": "ISO8601",
  "policy": "string",
  "action": "string",
  "lesson_id": "string (optional)",
  "decision": "string",
  "decision_maker": "string",
  "evidence": {
    "basis": "execution|design_time",
    "artifacts": ["array of strings"]
  },
  "related_episodes": ["array of UUIDs"]
}
```

### 14.2 Backfill Episode Template

```json
{
  "episode_id": "[generated UUID]",
  "timestamp": "[actual decision timestamp]",
  "policy": "approve-charter|approve-business-case",
  "action": "approve",
  "decision": "[decision text from gate record]",
  "decision_maker": "[actual decision maker]",
  "evidence": {
    "basis": "design_time",
    "artifacts": [
      "[related documents]"
    ]
  },
  "related_episodes": []
}
```

### 14.3 Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-11-06 | Vibe Code | Initial version |
