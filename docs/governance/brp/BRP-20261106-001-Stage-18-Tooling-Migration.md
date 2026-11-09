---
artifact_type: "baseline_revision_package"
package_id: "BRP-20261106-001"
baseline_from: "PMP-BL-v1.0.0"
baseline_to: "PMP-BL-v1.0.1"
version_type: "patch"
justification: "Design-time revision per ADR-037 section 4.10 (patch increment for design-time revisions)"
date: "2026-11-06"
prepared_by: "Vibe Code (on behalf of Project Manager)"
status: "prepared"
submission_date: "2026-11-06"
related_lesson: "LL-043"
related_insight: "INSIGHT-003"
related_episodes:
  - "classify-diff-type-LL-043-20261106.json"
  - "escalate-diff-response-LL-043-20261106.json"
governance_policy: "classify-diff-type, escalate-diff-response"
escalation_level: "steering_committee"
---

# Baseline Revision Package: BRP-20261106-001

## Stage 18 Tooling Migration & ADR-034 Amendment

> **Purpose:** Address LL-043 by migrating Stage 18 tooling from legacy `pmbok/` directory to maintained `src/agent_learning/pmbok/` location and amending ADR-034 to preserve critical path functionality.

> **Status:** Prepared for Steering Committee Review

> **Authority:** Steering Committee Approval Required

---

## Executive Summary

| Field | Value |
|---|---|
| **Package ID** | BRP-20261106-001 |
| **From Baseline** | PMP-BL-v1.0.0 |
| **To Baseline** | PMP-BL-v1.0.1 |
| **Version Type** | Patch (design-time revision) |
| **Submission Date** | 2026-11-06 |
| **Related Lesson** | [LL-043](../project-docs/Lessons-Learned-Register.md#ll-043) |
| **Related Insight** | [INSIGHT-003](../insights/INSIGHT-003.md) |
| **Escalation Level** | Steering Committee |
| **Status** | **Prepared** |

---

## 1. Problem Statement

### Root Cause (from LL-043)

The Stage 18 tooling (required for Phase 1 closure) currently exists only in the legacy `pmbok/` package directory, which is:
1. **Excluded from CI** - Tests in `tests/pmbok/` are not run by CI
2. **Scheduled for deletion** - ADR-034 plans to decommission the entire `pmbok/` directory
3. **Critical path dependency** - Without this tooling, Stage 18 (Intent Refinement) cannot be executed

### Current State

- `pmbok/evaluate_phase_close_readiness.py` - Phase closure readiness check
- `pmbok/seed-next.py` - Next phase seeding functionality
- `scripts/orchestrate_pmbok.py` - Orchestration script
- `tests/pmbok/` - Test suite (excluded from CI)
- `src/agent_learning/pmbok/` - **Empty** (no intent_refinement module)

### Impact

- **Phase 1 cannot close** without Stage 18 execution
- **ADR-034 cannot be fully executed** without migrating Stage 18 tooling
- **CI coverage gap** - Stage 18 code not tested in CI pipeline
- **Technical debt** - Legacy code not maintained in current architecture

---

## 2. Proposed Changes

### 2.1 Migration Plan

#### Step 1: Create New Module Structure
```
src/agent_learning/pmbok/
├── __init__.py
├── intent_refinement/
│   ├── __init__.py
│   ├── evaluate_phase_close_readiness.py  # Migrated from pmbok/
│   ├── seed_next.py                         # Migrated from pmbok/
│   └── orchestrate.py                      # New orchestration
└── tests/
    └── test_intent_refinement/
        ├── __init__.py
        ├── test_evaluate_phase_close_readiness.py
        └── test_seed_next.py
```

#### Step 2: Code Migration
- Migrate `pmbok/evaluate_phase_close_readiness.py` → `src/agent_learning/pmbok/intent_refinement/evaluate_phase_close_readiness.py`
- Migrate `pmbok/seed-next.py` → `src/agent_learning/pmbok/intent_refinement/seed_next.py`
- Create new `orchestrate.py` to replace `scripts/orchestrate_pmbok.py`
- Update all imports to use new module structure

#### Step 3: Test Migration
- Migrate `tests/pmbok/test_*.py` → `src/agent_learning/pmbok/tests/test_intent_refinement/`
- Update test imports
- Ensure all tests pass in new location

#### Step 4: CI Configuration Update
- Remove `tests/pmbok/` from CI exclusion list
- Add `src/agent_learning/pmbok/tests/` to CI test suite
- Verify all tests pass in CI pipeline

#### Step 5: ADR-034 Amendment
- Update ADR-034 to exclude Stage 18 tooling from deletion
- Add clause: "Stage 18 tooling (intent_refinement module) must be migrated before pmbok/ deletion"
- Update decommissioning timeline to include migration completion

---

## 3. Affected Documents

### 3.1 Project Management Plan Updates

| Document | Change | Rationale |
|---|---|---|
| Project-Management-Plan.md | Update baseline version to PMP-BL-v1.0.1 | Version increment per ADR-037 |
| Scope-Management-Plan.md | Add Stage 18 tooling migration work package | New scope |
| Schedule-Management-Plan.md | Add migration timeline (2 weeks) | Timeline adjustment |
| Quality-Management-Plan.md | Add test coverage requirements for migrated code | Quality assurance |

### 3.2 Standard Set (Unchanged)

- [ ] Spark-Capture.md - No changes
- [ ] Ideation-Document.md - No changes
- [ ] Business-Case.md - No changes
- [ ] Benefits-Statement.md - No changes
- [ ] Stakeholder-Register.md - No changes
- [ ] Project-Charter.md - No changes (authority limits unchanged)

### 3.3 Architectural Decisions

| ADR | Change | Status |
|---|---|---|
| ADR-034 | Amend to exclude Stage 18 tooling from deletion | **Required** |
| ADR-037 | Reference for versioning rules | Unchanged |

---

## 4. Implementation Steps

### Phase 1: Preparation (Week 1)

1. **Create migration branch**
   ```bash
   git checkout -b feature/migrate-stage-18-tooling
   ```

2. **Create new module structure**
   ```bash
   mkdir -p src/agent_learning/pmbok/intent_refinement
   mkdir -p src/agent_learning/pmbok/tests/test_intent_refinement
   ```

3. **Migrate source code**
   - Copy and refactor `pmbok/evaluate_phase_close_readiness.py`
   - Copy and refactor `pmbok/seed-next.py`
   - Create new `orchestrate.py`

4. **Migrate tests**
   - Copy and update `tests/pmbok/test_*.py`
   - Update imports to use new module structure

5. **Update imports**
   - Update any references to old `pmbok/` location
   - Ensure backward compatibility where needed

### Phase 2: Testing (Week 1-2)

6. **Run local tests**
   ```bash
   uv run pytest src/agent_learning/pmbok/tests/ -v
   ```

7. **Update CI configuration**
   - Remove `tests/pmbok/` from `.github/workflows/ci.yml` exclusions
   - Add new test paths to CI configuration

8. **Verify CI tests**
   - Push to branch and verify CI passes
   - Fix any CI-specific issues

### Phase 3: Documentation (Week 2)

9. **Update ADR-034**
   - Add amendment section
   - Update decommissioning timeline

10. **Update documentation**
    - Update `docs/adr/ADR-034-decommission-pmbok-directory.md`
    - Update any references to old tooling location

11. **Create migration guide**
    - Document migration process
    - Update README if needed

### Phase 4: Review and Approval (Week 2-3)

12. **Submit for review**
    - Create PR with all changes
    - Request Steering Committee review

13. **Address feedback**
    - Incorporate review comments
    - Update documents as needed

14. **Final approval**
    - Steering Committee approval
    - Project Sponsor sign-off (if required)

---

## 5. Verification Criteria

### 5.1 Code Verification

- [ ] All migrated code compiles without errors
- [ ] All migrated tests pass locally
- [ ] All migrated tests pass in CI pipeline
- [ ] No breaking changes to existing functionality
- [ ] Backward compatibility maintained where required

### 5.2 Documentation Verification

- [ ] ADR-034 amendment is complete and accurate
- [ ] All documentation references updated
- [ ] Migration guide is clear and comprehensive
- [ ] No broken links or references

### 5.3 Process Verification

- [ ] CI pipeline updated and passing
- [ ] All Stage 18 functionality works in new location
- [ ] Old tooling can be safely deleted (after verification)
- [ ] No dependencies on legacy `pmbok/` directory

---

## 6. Rollback Plan

### 6.1 Rollback Conditions

- Migration causes breaking changes
- Critical bugs discovered after migration
- Steering Committee rejects the BRP
- CI pipeline fails consistently

### 6.2 Rollback Steps

1. **Revert code changes**
   ```bash
   git revert <migration-commit>
   ```

2. **Restore old configuration**
   - Revert CI configuration changes
   - Restore any modified files

3. **Verify rollback**
   - Run tests to ensure old code still works
   - Verify CI pipeline passes

4. **Document rollback**
   - Record rollback decision and rationale
   - Update BRP status to "rolled back"

---

## 7. Risk Assessment

### 7.1 Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Breaking changes during migration | Medium | High | Comprehensive testing, incremental migration |
| CI configuration issues | Medium | Medium | Test CI changes in branch before merging |
| Import path conflicts | Low | Medium | Use unique module names, test imports |
| Performance degradation | Low | Low | Performance testing before/after |

### 7.2 Schedule Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Delay in Steering Committee approval | Medium | Medium | Prepare complete package, address concerns proactively |
| Migration takes longer than estimated | Medium | Medium | Break into smaller PRs, parallelize work |
| Dependencies on other work | Low | Medium | Coordinate with other teams |

### 7.3 Business Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Phase 1 closure delayed | Medium | High | Prioritize this BRP, expedite review |
| ADR-034 execution blocked | Medium | Medium | Clearly communicate dependency |
| Resource contention | Low | Medium | Allocate dedicated resources |

---

## 8. Resource Requirements

### 8.1 Human Resources

| Role | Time Required | Responsibility |
|---|---|---|
| Developer | 10 days | Code migration and testing |
| QA Engineer | 3 days | Test verification |
| Technical Writer | 2 days | Documentation updates |
| Project Manager | 2 days | Coordination and review |
| Steering Committee | 1 day | Approval and oversight |

### 8.2 Tooling Resources

- Development environment with Python 3.12
- Access to repository and CI system
- Code review tools
- Documentation tools

---

## 9. Approval Workflow

### 9.1 Required Approvals

1. **Technical Review**
   - [ ] Code review by senior developer
   - [ ] Test review by QA engineer
   - [ ] Architecture review by technical lead

2. **Project Management Review**
   - [ ] Scope review by Project Manager
   - [ ] Schedule review by Project Manager
   - [ ] Resource review by Project Manager

3. **Steering Committee Review**
   - [ ] Business impact review
   - [ ] Strategic alignment review
   - [ ] Risk assessment review

4. **Final Approval**
   - [ ] Steering Committee approval
   - [ ] Project Sponsor sign-off (if required)

### 9.2 Approval Timeline

| Step | Duration | Target Date |
|---|---|---|
| Preparation | 1 day | 2026-11-06 |
| Technical Review | 3 days | 2026-11-09 |
| Project Management Review | 2 days | 2026-11-11 |
| Steering Committee Review | 5 days | 2026-11-16 |
| Final Approval | 1 day | 2026-11-17 |
| **Total** | **12 days** | **2026-11-17** |

---

## 10. Success Metrics

### 10.1 Completion Metrics

- [ ] BRP submitted on time (2026-11-06)
- [ ] All technical reviews completed within 3 days
- [ ] All management reviews completed within 2 days
- [ ] Steering Committee approval received within 5 days
- [ ] Migration completed within 2 weeks of approval

### 10.2 Quality Metrics

- [ ] 100% of migrated tests pass
- [ ] 0 critical bugs in migrated code
- [ ] 0 breaking changes to existing functionality
- [ ] All documentation updated and accurate

---

## 11. References

### 11.1 Related Documents

- [LL-043: A Closing Stage's Tooling May Sit Outside What CI Runs](../project-docs/Lessons-Learned-Register.md#ll-043)
- [INSIGHT-003: The Stage 18 tooling lives only in the legacy tree that CI skips](../insights/INSIGHT-003.md)
- [ADR-034: Decommission pmbok/ Directory](../adr/ADR-034-decommission-pmbok-directory.md)
- [ADR-037: Design-Time vs Execution-Time Feedback Loops](../adr/ADR-037-design-time-vs-execution-time-feedback-loops.md)
- [Stage 16 Governance Change Assessment](../project-docs/Status-Reports/Stage-16-Governance-Change-Assessment.md)
- [Stage 16 Methodology](../project-docs/Methodology/Stage-16-Governance-Change-Methodology.md)

### 11.2 Governance Episodes

- [Classification Episode: classify-diff-type-LL-043-20261106.json](../policy-shapes/episodes/classify-diff-type-LL-043-20261106.json)
- [Escalation Episode: escalate-diff-response-LL-043-20261106.json](../policy-shapes/episodes/escalate-diff-response-LL-043-20261106.json)

---

## 12. Appendix

### 12.1 File Inventory

**Files to be added:**
```
src/agent_learning/pmbok/__init__.py
src/agent_learning/pmbok/intent_refinement/__init__.py
src/agent_learning/pmbok/intent_refinement/evaluate_phase_close_readiness.py
src/agent_learning/pmbok/intent_refinement/seed_next.py
src/agent_learning/pmbok/intent_refinement/orchestrate.py
src/agent_learning/pmbok/tests/__init__.py
src/agent_learning/pmbok/tests/test_intent_refinement/__init__.py
src/agent_learning/pmbok/tests/test_intent_refinement/test_evaluate_phase_close_readiness.py
src/agent_learning/pmbok/tests/test_intent_refinement/test_seed_next.py
```

**Files to be modified:**
```
.github/workflows/ci.yml
pyproject.toml (if needed)
docs/adr/ADR-034-decommission-pmbok-directory.md
```

**Files to be deleted (after verification):**
```
pmbok/evaluate_phase_close_readiness.py
pmbok/seed-next.py
scripts/orchestrate_pmbok.py
tests/pmbok/*
```

### 12.2 Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-11-06 | Vibe Code | Initial version |
