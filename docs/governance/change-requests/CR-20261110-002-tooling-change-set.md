---
artifact_type: "manual_change_request"
change_request_id: "CR-20261110-002"
stage: "16"
evidence_basis: "execution"
current_baseline: "PMP-BL-v1.1.0"
status: "dispositions_approved_implementation_pending"
date: "2026-11-10"
requested_by: "Menno Drescher"
drafted_by: "assistant (draft; no code is changed by this request)"
---

# Manual Change Request: The In-Flight Tooling Change Set

> **Status:** The Sponsor approved the disposition of these 15 improvements on 2026-11-10 (section 4). This request fixes their scope and order. Each change below is built and merged through its own PR (or story), and none is applied by this request.

## 1. Request

Stage 16 checked the 24 `In-Flight Candidate` improvements against the code (Stage 16 note, Step 2c). Fifteen are tooling, process or skill changes that the accepted lessons keep naming. They are grouped here so that they are evaluated once, not left open since Epic 14.

## 2. The change set

| IMP | Change | Touches | Lessons | Needs |
|---|---|---|---|---|
| 062 | `stage16_amend.py` prints the store path, file count and the `agent-learning-governance` partition count; refuses a path outside the repository unless a flag allows it | `scripts/stage16_amend.py` | LL-040, LL-067 | contract test, inside and outside |
| 063 | Tests use a temporary store; a test proves the suite leaves the configured store unchanged | `tests/`, `conftest.py` | LL-067 | the test itself |
| 045 | Read `gh` output as UTF-8 in the gate, `spec_gate.py` and `stage16_amend.py` | `scripts/pr_gate.py` and two more | LL-059 | contract test with a non-cp1252 character |
| 052 | Skip the release when the version is not bumped, instead of failing | `.github/workflows/publish.yaml` | none | workflow run on a no-bump push |
| 030 | Check review-triage lines inside the PR gate | `scripts/pr_gate.py` | LL-049 | contract test |
| 017 | Wire `triage_replay` into the gate | `scripts/pr_gate.py` | LL-049 | contract test |
| 015 | Export PR review threads to committed fixtures | new script | none | contract test |
| 021 | Spec gate flags a discrete primitive widened to a continuous domain | `scripts/spec_gate.py` | LL-046 | contract test |
| 024 | Spec gate flags `abs_tol` without `rel_tol=0.0` | `scripts/spec_gate.py` | LL-047 | contract test |
| 001 | `complete_story.py` gains `worktree` and `triage --none`, and the `Co-Authored-By` trailer | `scripts/complete_story.py` | LL-033, LL-034 | contract test |
| 007 | One `approve.py` for an approval run (frame, decide, compare, register), printing the store path | new script | LL-040 | contract test |
| 043 | Union merge driver (or script) for `implementation-log.md` | `.gitattributes` | LL-054 | a merge test that an older-entry conflict is not hidden |
| 044 | Step 0 and Step 6 of `implement-story` match the whole-suite rule | `implement-story` skill | LL-013, LL-055 | **delivered by PR #187; the maintainer confirms by reading the merged skill** |
| 050 | A Step 8 checklist with the literal command strings in `implement-story` | `implement-story` skill | LL-004, LL-058 | **not delivered by PR #187** |
| 031 | Backfill the Tier 2 targets for the lessons the skill still lacks and script the LL-041 check | skills, new script | LL-041, 045 to 048 | the script, with a test |

## 3. Order and route

1. **First:** IMP-062 and IMP-063. They stop the two ways a governance run can write to the wrong place, and the rest depends on a trustworthy store.
2. **Second:** IMP-045 and IMP-052, which unblock the gate and the release workflow.
3. **Third:** the spec-gate and gate-check changes (030, 017, 021, 024), then the helper scripts (001, 007, 015, 043).
4. **Fourth:** 050 and 031, which edit skills and need a Sponsor decision on the exact text, as CR-20261110-001 did.

Each change is a story (or an `IMP` PR with a contract test written first and seen failing), merged through `scripts/pr_gate.py` with every required workflow concluded (LL-060) and with the whole suite run. Scripts under `scripts/` are not covered by ADR-007; skills follow the route of CR-20261110-001.

## 4. Decision record

| Role | Decision | Date |
|---|---|---|
| Project Sponsor | Approved: proposal A of the Stage 16 note, Step 5 (15 improvements in-flight as this change set; IMP-002, 006, 019, 025, 027, 028, 039 rolled into Phase Next; IMP-004, 016, 020, 022 marked as the code shows) | 2026-11-10 |

Given by Menno Drescher in the working session of 2026-11-10 ("Approve both A and B proposals") and recorded here from that statement. The approval fixes the dispositions; it does not approve the text of a skill edit (IMP-031, IMP-050) or any code, which are decided with their own PR.
